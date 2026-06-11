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


def composite(rgba, material_rgb, mask, lum_lo=0.3, lum_hi=1.6):
    """Replace masked pixels with the material, shaded by the original
    lightness relative to the masked region's mean (so highlights stay
    highlights and creases stay dark). Returns a new array, or None if the
    mask selects nothing."""
    if not mask.any():
        return None
    _, _, l = rgb_to_hsl(rgba[..., :3].astype(np.float64))
    lum = l / 100.0
    ref = float(lum[mask].mean()) or 0.5
    shade = np.clip(lum / ref, lum_lo, lum_hi)
    out = rgba.copy()
    mat = tile_to(material_rgb.astype(np.float64), rgba.shape)
    out[..., :3][mask] = np.clip(mat[mask] * shade[mask][:, None], 0, 255).astype(np.uint8)
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
