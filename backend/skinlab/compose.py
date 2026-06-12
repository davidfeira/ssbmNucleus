"""
compose.py -- deterministic texture compositing for the skin lab.

These are the operations the AI skin experiments converged on, promoted into
a parameterized engine so a UI or a *small* planner model can drive them with
JSON instead of writing code:

  * build_mask    -- select pixels by hue range (wrap-aware) / saturation /
                     lightness, opaque only
  * composite     -- lay a material image over the masked pixels, modulated by
                     the texture's ORIGINAL lightness so folds/seams/shading
                     survive (a "re-fabric", not a paste)
  * hue_shift     -- rotate hue / push saturation on the masked pixels only
                     (lightness untouched, shading survives)

All functions take/return HxWx4 uint8 numpy arrays and never mutate inputs.
"""

import numpy as np

from .palette import hsl_to_rgb, rgb_to_hsl


def build_mask(rgba, hue_min=None, hue_max=None, sat_min=None, sat_max=None,
               lum_min=None, lum_max=None):
    """Boolean pixel mask. Hue in degrees (hue_min > hue_max wraps through 0,
    e.g. 330..30 selects reds), sat/lum in 0..100. Omitted bounds don't
    constrain. Transparent pixels are never selected."""
    h, s, l = rgb_to_hsl(rgba[..., :3].astype(np.float64))
    mask = rgba[..., 3] >= 128
    if hue_min is not None and hue_max is not None:
        if hue_min <= hue_max:
            mask &= (h >= hue_min) & (h <= hue_max)
        else:  # wraps around 0/360
            mask &= (h >= hue_min) | (h <= hue_max)
    elif hue_min is not None:
        mask &= h >= hue_min
    elif hue_max is not None:
        mask &= h <= hue_max
    if sat_min is not None:
        mask &= s >= sat_min
    if sat_max is not None:
        mask &= s <= sat_max
    if lum_min is not None:
        mask &= l >= lum_min
    if lum_max is not None:
        mask &= l <= lum_max
    return mask


def tile_to(material_rgb, shape):
    """Tile/crop a material (HxWx3) to cover `shape` (HxWx...)."""
    th, tw = shape[:2]
    reps = (int(np.ceil(th / material_rgb.shape[0])),
            int(np.ceil(tw / material_rgb.shape[1])), 1)
    return np.tile(material_rgb, reps)[:th, :tw]


def fit_to(material_rgb, shape):
    """Stretch a material (HxWx3) to exactly cover `shape` (HxWx...).
    Right for panorama/backdrop textures, where tiling a small swatch reads
    as a crusty repeat instead of one coherent image."""
    from PIL import Image
    th, tw = shape[:2]
    img = Image.fromarray(material_rgb.astype(np.uint8), 'RGB')
    return np.asarray(img.resize((tw, th), Image.LANCZOS), dtype=np.float64)


def composite(rgba, material_rgb, mask, lum_lo=0.3, lum_hi=1.6, mode='tile'):
    """Replace masked pixels with the material, shaded by the original
    lightness relative to the masked region's mean (so highlights stay
    highlights and creases stay dark). mode='tile' repeats the swatch;
    mode='fit' stretches it to the texture (backdrops). Returns a new array,
    or None if the mask selects nothing."""
    if not mask.any():
        return None
    _, _, l = rgb_to_hsl(rgba[..., :3].astype(np.float64))
    lum = l / 100.0
    ref = float(lum[mask].mean()) or 0.5
    shade = np.clip(lum / ref, lum_lo, lum_hi)
    out = rgba.copy()
    cover = fit_to if mode == 'fit' else tile_to
    mat = cover(material_rgb.astype(np.float64), rgba.shape)
    out[..., :3][mask] = np.clip(mat[mask] * shade[mask][:, None], 0, 255).astype(np.uint8)
    return out


# --------------------------------------------------------------------------- #
# UV-projected compositing
#
# tile/fit composites lay the material into each texture INDEPENDENTLY in
# pixel space, so two textures meeting on the model (e.g. an eye-decal quad
# over the head) get unrelated pattern scale/orientation -- the UV boundary
# shows as a hard seam. Projection mode fixes that: the viewer exports each
# texture's UV triangles with posed world-space corner positions
# (getUVLayout), we bake a per-texel world-position map, and sample the
# material in SHARED model space (triplanar projection). Adjacent textures
# then agree on the pattern at every seam.
# --------------------------------------------------------------------------- #

# GXWrapMode values (matches HSDRaw.GX.GXWrapMode)
WRAP_CLAMP, WRAP_REPEAT, WRAP_MIRROR = 0, 1, 2


def _fold_indices(idx, n, wrap):
    """Fold unwrapped texel indices into [0, n) per GX wrap mode."""
    if wrap == WRAP_CLAMP:
        return np.clip(idx, 0, n - 1)
    if wrap == WRAP_MIRROR:
        m = np.mod(idx, 2 * n)
        return np.where(m < n, m, 2 * n - 1 - m)
    return np.mod(idx, n)


def rasterize_uv_layout(triangles, width, height, wrap_s=WRAP_REPEAT,
                        wrap_t=WRAP_REPEAT, max_bbox_texels=4_000_000):
    """Bake per-texel world positions + face normals from a texture's UV
    triangles (each: [u0,v0,u1,v1,u2,v2, x0,y0,z0, x1,y1,z1, x2,y2,z2], UVs
    in wrap units where [0,1] is one tile). Triangles are written in order,
    so callers should put the geometry that must win overlaps LAST.
    Returns (pos HxWx3, nrm HxWx3, covered HxW bool)."""
    pos = np.zeros((height, width, 3), np.float64)
    nrm = np.zeros((height, width, 3), np.float64)
    covered = np.zeros((height, width), dtype=bool)
    for tri in triangles:
        u = np.array([tri[0], tri[2], tri[4]], np.float64) * width
        v = np.array([tri[1], tri[3], tri[5]], np.float64) * height
        p = np.asarray(tri[6:15], np.float64).reshape(3, 3)
        n = np.cross(p[1] - p[0], p[2] - p[0])
        ln = np.linalg.norm(n)
        if ln < 1e-12:
            continue
        n = n / ln
        x0, x1 = int(np.floor(u.min())), int(np.ceil(u.max())) + 1
        y0, y1 = int(np.floor(v.min())), int(np.ceil(v.max())) + 1
        if (x1 - x0) * (y1 - y0) > max_bbox_texels:
            continue   # runaway repeat counts; nothing sane to bake
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        denom = (v[1] - v[2]) * (u[0] - u[2]) + (u[2] - u[1]) * (v[0] - v[2])
        if abs(denom) < 1e-12:
            continue
        w0 = ((v[1] - v[2]) * (gx - u[2]) + (u[2] - u[1]) * (gy - v[2])) / denom
        w1 = ((v[2] - v[0]) * (gx - u[2]) + (u[0] - u[2]) * (gy - v[2])) / denom
        w2 = 1.0 - w0 - w1
        # slight outset so texels straddling an edge still get a position
        eps = -0.02
        inside = (w0 >= eps) & (w1 >= eps) & (w2 >= eps)
        if not inside.any():
            continue
        iy, ix = np.nonzero(inside)
        px = _fold_indices(ix + x0, width, wrap_s)
        py = _fold_indices(iy + y0, height, wrap_t)
        world = (w0[inside][:, None] * p[0] + w1[inside][:, None] * p[1]
                 + w2[inside][:, None] * p[2])
        pos[py, px] = world
        nrm[py, px] = n
        covered[py, px] = True
    return pos, nrm, covered


def fill_uncovered(pos, nrm, covered, iters=12):
    """Propagate baked positions into neighboring un-baked texels (UV-island
    padding) so masks slightly larger than the islands still sample sensibly."""
    pos = pos.copy()
    nrm = nrm.copy()
    covered = covered.copy()
    for _ in range(iters):
        if covered.all():
            break
        grew = False
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sc = np.roll(covered, (dy, dx), (0, 1))
            take = (~covered) & sc
            if not take.any():
                continue
            pos[take] = np.roll(pos, (dy, dx), (0, 1))[take]
            nrm[take] = np.roll(nrm, (dy, dx), (0, 1))[take]
            covered |= take
            grew = True
        if not grew:
            break
    return pos, nrm, covered


def _bilinear_wrap(mat, x, y):
    """Bilinear sample HxWx3 `mat` at float pixel coords, tiling at borders."""
    mh, mw = mat.shape[:2]
    x = x - 0.5
    y = y - 0.5
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    fx = (x - x0)[..., None]
    fy = (y - y0)[..., None]
    x0m, x1m = np.mod(x0, mw), np.mod(x0 + 1, mw)
    y0m, y1m = np.mod(y0, mh), np.mod(y0 + 1, mh)
    return (mat[y0m, x0m] * (1 - fx) * (1 - fy) + mat[y0m, x1m] * fx * (1 - fy)
            + mat[y1m, x0m] * (1 - fx) * fy + mat[y1m, x1m] * fx * fy)


def triplanar_sample(material_rgb, pos, nrm, world_scale, sharpness=4.0):
    """Sample the material at world positions: three axis-aligned planar
    projections blended by the surface normal. `world_scale` = world units
    covered by one material tile. Pure function of (pos, nrm), so any two
    texels at the same spot on the model get the same color -- seamless."""
    mat = material_rgb.astype(np.float64)
    mh, mw = mat.shape[:2]
    w = np.abs(nrm) ** sharpness
    s = w.sum(axis=-1, keepdims=True)
    s[s == 0] = 1.0
    w = w / s
    out = np.zeros(pos.shape[:2] + (3,), np.float64)
    for axis, (i, j) in enumerate(((1, 2), (0, 2), (0, 1))):
        uu = pos[..., i] / world_scale * mw
        vv = pos[..., j] / world_scale * mh
        out += w[..., axis:axis + 1] * _bilinear_wrap(mat, uu, vv)
    return out


def masked_lightness(rgba, mask):
    """Mean lightness (0..1) of the masked pixels; 0.0 when nothing matches.
    Used to build a shared shade_ref across textures for composite_project."""
    if not mask.any():
        return 0.0
    _, _, l = rgb_to_hsl(rgba[..., :3][mask].astype(np.float64))
    return float(l.mean()) / 100.0


def layout_world_scale(layouts, fraction=0.55):
    """Default world_scale (one material tile, world units) from the model's
    bounding box across the given layout entries."""
    mins = np.full(3, np.inf)
    maxs = np.full(3, -np.inf)
    for lay in layouts:
        tris = np.asarray(lay.get('triangles') or [], np.float64)
        if tris.size == 0:
            continue
        p = tris[:, 6:15].reshape(-1, 3)
        mins = np.minimum(mins, p.min(0))
        maxs = np.maximum(maxs, p.max(0))
    if not np.isfinite(mins).all():
        return 1.0
    return max(float(np.linalg.norm(maxs - mins)) * fraction, 1e-6)


def composite_project(rgba, material_rgb, mask, layout, world_scale,
                      lum_lo=0.3, lum_hi=1.6, fill_iters=12, shade_ref=None):
    """UV-aware composite: replace masked pixels with the material sampled in
    shared model space (see module note above), shaded by the original
    lightness like composite(). `layout` is one getUVLayout entry
    {triangles, wrapS, wrapT}. `shade_ref` is the lightness (0..1) treated as
    "no shading" -- pass one value for ALL textures of an op, or each texture
    exposes the material differently and the shared pattern still shows a
    brightness step at the seam. Returns a new array, or None if the mask
    selects nothing bake-able."""
    if not mask.any():
        return None
    h, w = rgba.shape[:2]
    pos, nrm, covered = rasterize_uv_layout(
        layout['triangles'], w, h,
        layout.get('wrapS', WRAP_REPEAT), layout.get('wrapT', WRAP_REPEAT))
    if not covered.any():
        return None
    pos, nrm, covered = fill_uncovered(pos, nrm, covered, fill_iters)
    target = mask & covered
    if not target.any():
        return None
    mat = triplanar_sample(material_rgb, pos, nrm, world_scale)
    _, _, l = rgb_to_hsl(rgba[..., :3].astype(np.float64))
    lum = l / 100.0
    ref = float(shade_ref) if shade_ref else (float(lum[target].mean()) or 0.5)
    shade = np.clip(lum / ref, lum_lo, lum_hi)
    out = rgba.copy()
    out[..., :3][target] = np.clip(mat[target] * shade[target][:, None],
                                   0, 255).astype(np.uint8)
    return out


def hue_shift(rgba, mask, hue_delta=0.0, sat_delta=0.0):
    """Rotate hue / push saturation on the masked pixels (lightness kept).
    Returns a new array, or None if nothing matched / nothing to do."""
    if (not mask.any()) or (not hue_delta and not sat_delta):
        return None
    out = rgba.copy()
    flat = out.reshape(-1, 4)
    sel = mask.ravel()
    h, s, l = rgb_to_hsl(flat[sel, :3].astype(np.float64))
    flat[sel, :3] = hsl_to_rgb((h + hue_delta) % 360.0,
                               np.clip(s + sat_delta, 0, 100), l)
    return out


def tint(rgba, mask, hue, saturation=60.0):
    """COLORIZE the masked pixels: set hue + saturation outright, keep each
    pixel's lightness. Unlike hue_shift this works on whites/grays (which have
    no hue to rotate) -- e.g. white armor -> green armor. Returns a new array,
    or None if nothing matched."""
    if not mask.any():
        return None
    out = rgba.copy()
    flat = out.reshape(-1, 4)
    sel = mask.ravel()
    _, _, l = rgb_to_hsl(flat[sel, :3].astype(np.float64))
    n = int(sel.sum())
    flat[sel, :3] = hsl_to_rgb(np.full(n, float(hue) % 360.0),
                               np.full(n, np.clip(float(saturation), 0, 100)), l)
    return out
