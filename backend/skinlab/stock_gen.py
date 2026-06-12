"""stock_gen.py -- deterministic stock-icon generation for recolored skins.

Vanilla stock icons are palette swaps of the same pixel art (Fox Nr->Gr is a
94% pure palette remap), so a recolored costume's icon can be derived instead
of drawn: measure how the costume's COLORS moved (vanilla DAT textures vs the
modded DAT's, pixel-aligned) and apply the same movement to the vanilla icon's
palette.

Transfer estimation is a hybrid tuned against the real vanilla colorways
(Fox/Pikachu/Marth/Falco ground truth, see _probe_out/stock_texdiff_test.py):

- SATURATED icon colors take a per-hue-group transform: vanilla texture pixels
  are hue-binned into color groups (same binning as palette.py), each group's
  median H/S/L shift is measured from the modded pixels, and an icon color
  joins a group BY HUE with tolerance. Robust to the icon art using different
  shades than the textures (Falco's stylized blue), and protects regions that
  did not change (Marth's face when only the cape recolors).
- NEUTRAL icon colors (low sat / extreme lightness) take a per-color KNN
  median delta over all sample pixels -- hue grouping is undefined for whites,
  and white-to-color recolors are real (Fox Gr's jacket is recolored WHITE
  texture). A spatial cleanup then resets isolated outlier pixels (lone
  anti-aliasing pixels picking up a foreign transform) to their original
  color, which is never jarring.

Both estimators only need (src_px, dst_px) sample pairs, so the same code
serves texture-diff (preferred: flat, unshaded, exactly aligned) and CSP-diff
(fallback: CSP renders share pose/camera, so they are pixel-aligned too).
"""

import io
import logging
from pathlib import Path

import numpy as np
from PIL import Image

from skinlab import datprobe
from skinlab.palette import rgb_to_hsl, hsl_to_rgb

logger = logging.getLogger(__name__)

HUE_TOL = 25.0          # degrees; same group tolerance as palette.py
SAT_NEUTRAL = 15.0      # s (0-100) below which a color is "neutral"
L_LO, L_HI = 10.0, 90.0
KNN_K = 600
MIN_SAMPLES = 5000      # below this a sample source is considered unusable


# --------------------------------------------------------------------------- #
# sample extraction                                                            #
# --------------------------------------------------------------------------- #
def _dat_textures(dat_path):
    """Decoded material textures of a DAT as HxWx4 uint8 arrays (None where
    decode fails), in JOBJ-tree walk order."""
    dat = datprobe.DatFile(dat_path)
    jobj_roots = [(n, o) for n, o in dat.roots
                  if n.endswith('_joint') and 'matanim' not in n
                  and 'shapeanim' not in n]
    out = []
    for _name, off in jobj_roots:
        for t in dat.jobj_textures(off):
            try:
                out.append(np.asarray(datprobe.decode_image(t.image, t.tlut),
                                      dtype=np.uint8))
            except Exception:
                out.append(None)
    return out


def _structure_corr(a, b):
    """Pearson correlation of two textures' downsampled grayscales -- a
    recolor keeps the image's spatial structure (hue moves, luminance
    pattern stays put), a different model's art does not."""
    ga = np.asarray(Image.fromarray(a).convert('L').resize((16, 16), Image.BOX),
                    dtype=np.float64).ravel()
    gb = np.asarray(Image.fromarray(b).convert('L').resize((16, 16), Image.BOX),
                    dtype=np.float64).ravel()
    sa, sb = ga.std(), gb.std()
    if sa < 1e-6 or sb < 1e-6:
        return None    # flat texture, no structure to compare
    return float(((ga - ga.mean()) * (gb - gb.mean())).mean() / (sa * sb))


def texture_pixel_pairs(vanilla_dat_path, modded_dat_path):
    """Aligned (src_px, dst_px) Nx3 float arrays from two costume DATs, or
    None if this is a different model: texture lists that don't line up, OR
    same-shaped textures whose CONTENT doesn't correlate (model imports that
    reuse the vanilla texture dimensions)."""
    try:
        van = _dat_textures(vanilla_dat_path)
        mod = _dat_textures(modded_dat_path)
    except Exception as e:
        logger.info(f"stock_gen: DAT decode failed: {e}")
        return None
    if not van or not mod:
        return None
    n = min(len(van), len(mod))
    matched = 0
    src, dst = [], []
    corrs = []
    for i in range(n):
        a, b = van[i], mod[i]
        if a is None or b is None or a.shape != b.shape:
            continue
        matched += 1
        c = _structure_corr(a, b)
        if c is not None:
            corrs.append(c)
        op = (a[..., 3] > 128) & (b[..., 3] > 128)
        src.append(a[op][:, :3].astype(np.float64))
        dst.append(b[op][:, :3].astype(np.float64))
    # a recolor keeps the texture list; lots of shape mismatches mean a
    # different model and index-pairing would produce garbage transforms
    if matched < max(n, 1) * 0.7:
        return None
    if corrs and float(np.median(corrs)) < 0.3:
        logger.info(f"stock_gen: textures align but content does not "
                    f"(median corr {np.median(corrs):.2f}) -> model import")
        return None
    if not src:
        return None
    src_px, dst_px = np.concatenate(src), np.concatenate(dst)
    if len(src_px) < MIN_SAMPLES:
        return None
    return src_px, dst_px


def csp_pixel_pairs(vanilla_csp, modded_csp):
    """Aligned (src_px, dst_px) from two CSP renders (same pose/camera =>
    pixel-aligned). Inputs are paths or PNG bytes."""
    try:
        a = _load_rgba(vanilla_csp)
        b = _load_rgba(modded_csp)
    except Exception as e:
        logger.info(f"stock_gen: CSP load failed: {e}")
        return None
    if a.shape != b.shape:
        return None
    op = (a[..., 3] > 200) & (b[..., 3] > 200)
    src_px = a[op][:, :3].astype(np.float64)
    dst_px = b[op][:, :3].astype(np.float64)
    if len(src_px) < MIN_SAMPLES:
        return None
    return src_px, dst_px


def _load_rgba(source):
    if isinstance(source, (bytes, bytearray)):
        img = Image.open(io.BytesIO(source))
    else:
        img = Image.open(source)
    return np.asarray(img.convert('RGBA'), dtype=np.float64)


# --------------------------------------------------------------------------- #
# transfer estimation + application                                            #
# --------------------------------------------------------------------------- #
def _circ_median_deg(d):
    d = (d + 180.0) % 360.0 - 180.0
    return float(np.median(d))


def _rgb_to_hsv(rgb):
    """rgb 0-255 (...,3) -> h(0-360), s(0-1), v(0-1). HSV saturation stays
    near 0 for whites (unlike HSL, where a barely-tinted white has s=100),
    which is what nearest-neighbor distances need."""
    rgb = rgb / 255.0
    mx = rgb.max(-1)
    mn = rgb.min(-1)
    diff = mx - mn
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.zeros_like(mx)
    mask = diff > 0
    rmax = mask & (mx == r)
    gmax = mask & (mx == g) & ~rmax
    bmax = mask & ~rmax & ~gmax
    with np.errstate(divide='ignore', invalid='ignore'):
        h[rmax] = ((g - b)[rmax] / diff[rmax]) % 6
        h[gmax] = ((b - r)[gmax] / diff[gmax]) + 2
        h[bmax] = ((r - g)[bmax] / diff[bmax]) + 4
    s = np.where(mx > 0, diff / np.where(mx > 0, mx, 1), 0)
    return h * 60.0, s, mx


def _hue_groups(sh, valid):
    """palette.py-style hue groups [(lo, hi)] over the valid sample pixels;
    lo may be negative for the wrap-around group."""
    bins = np.bincount(np.floor(sh[valid]).astype(int) % 360, minlength=360)
    min_px = max(200, int(valid.sum() * 0.002))
    groups, cur = [], None
    for deg in range(360):
        if bins[deg] > 0:
            if cur is None:
                cur = [deg, deg, int(bins[deg])]
            elif deg - cur[1] <= HUE_TOL:
                cur[1] = deg
                cur[2] += int(bins[deg])
            else:
                if cur[2] >= min_px:
                    groups.append(cur)
                cur = [deg, deg, int(bins[deg])]
    if cur is not None and cur[2] >= min_px:
        groups.append(cur)
    if len(groups) >= 2 and groups[0][0] < HUE_TOL and groups[-1][1] > 360 - HUE_TOL:
        first = groups.pop(0)
        groups[-1] = [groups[-1][0] - 360, first[1], groups[-1][2] + first[2]]
    return [(lo, hi) for lo, hi, _n in groups]


SAT_NEUTRAL_V = 0.15    # HSV saturation below which a color is "neutral"
V_BLACK = 0.10
IDENTITY_EPS = 0.02     # mean squared weighted-HSV movement = "unchanged"
RAMP_KEEP = 0.5         # how much of the icon's own shading offset survives


def recolor_stock(stock_rgba, src_px, dst_px):
    """Recolor a stock icon (HxWx4) by DIRECT COLOR LOOKUP: for each icon
    color, find the texture pixels of that color family in the vanilla skin
    (hue-group gated for saturated colors) and take the color those pixels
    actually BECAME in the modded skin. Outputs always come from the modded
    skin's real palette, so drastic recolors (yellow -> near-black) cannot
    leave stray out-of-gamut colors the way hue/sat deltas did. A fraction
    of the icon's own lightness offset is kept so pixel-art shading ramps
    survive, and colors whose matched pixels did not move keep their exact
    original value."""
    sh, ss, sl = rgb_to_hsl(src_px)
    dh, ds, dl = rgb_to_hsl(dst_px)
    # classification + distances use HSV: HSL saturation explodes near white
    # (a pale pink reads s=100, l=92), which mis-routes light colored pixels
    svh, svs, svv = _rgb_to_hsv(src_px)
    dvh, dvs, dvv = _rgb_to_hsv(dst_px)
    valid = (svs >= SAT_NEUTRAL_V) & (svv >= V_BLACK)

    # hue groups over the vanilla pixels; saturated icon colors only sample
    # within their own group so an unrelated region can't dilute the lookup
    groups = []
    for lo, hi in _hue_groups(sh, valid):
        if lo < 0:
            in_g = valid & ((sh >= lo + 360.0) | (sh <= hi))
        else:
            in_g = valid & (sh >= lo) & (sh <= hi)
        if in_g.sum() >= 50:
            groups.append((lo, hi, np.where(in_g)[0]))

    def group_pool(ch):
        best = None
        for lo, hi, idx_pool in groups:
            center = ((lo + hi) / 2.0) % 360.0
            dist = abs(((ch - center) + 180.0) % 360.0 - 180.0)
            span = (hi - lo) / 2.0 + HUE_TOL
            if dist <= span and (best is None or dist < best[0]):
                best = (dist, idx_pool)
        return best[1] if best is not None else None

    def lookup(rgb_key, pool):
        """Match the icon color to vanilla pixels -> (new_rgb or None).

        Saturated colors: KNN inside their hue group's pool. Neutral colors
        (pool=None): the whole near-neutral FAMILY in a sat/value band --
        a k-nearest selection would lock onto the unmoved pure whites and
        never see a recolored off-white region (the Fox Gr jacket)."""
        cv = _rgb_to_hsv(np.array(rgb_key, dtype=np.float64)[None, :])
        ch_v, cs_v, cv_v = (float(v[0]) for v in cv)
        if pool is None:
            # tight band: a mid-gray must not inherit the movement of light
            # khakis two value-steps away (the Fox headset-stripe artifact)
            fam = (np.abs(svs - cs_v) <= 0.15) & (svs <= 0.35) \
                & (np.abs(svv - cv_v) <= 0.15)
            idx = np.where(fam)[0]
            if len(idx) < 50:
                return None
        else:
            hue_d = np.abs(svh[pool] - ch_v)
            hue_d = np.minimum(hue_d, 360.0 - hue_d) / 360.0
            sat_w = np.minimum(svs[pool], cs_v)
            dist = (hue_d * sat_w * 4) ** 2 + ((svs[pool] - cs_v) * 2) ** 2 \
                + (svv[pool] - cv_v) ** 2
            k = min(KNN_K, len(dist) - 1)
            if k < 20:
                return None
            idx = pool[np.argpartition(dist, k)[:k]]

        # how far did each matched pixel actually move? Matched sets can be
        # mixed (Fox Gr recolors the jacket's WHITE pixels while the muzzle
        # whites stay), so identity is decided by the moved FRACTION and the
        # destination is read from the moved subset only.
        m_h = np.abs(dvh[idx] - svh[idx])
        m_h = np.minimum(m_h, 360.0 - m_h) / 360.0
        m_sat = np.minimum(svs[idx], dvs[idx])
        movement = ((m_h * m_sat * 4) ** 2
                    + ((dvs[idx] - svs[idx]) * 2) ** 2
                    + (dvv[idx] - svv[idx]) ** 2)
        moved = movement > IDENTITY_EPS
        if moved.mean() < 0.3:
            return None    # region untouched -> keep the icon's exact pixel
        idx = idx[moved]

        # destination color: medians of where those pixels landed
        d_hue = np.deg2rad(dh[idx])
        med_h = np.degrees(np.arctan2(np.median(np.sin(d_hue)),
                                      np.median(np.cos(d_hue)))) % 360.0
        med_s = float(np.median(ds[idx]))
        med_l = float(np.median(dl[idx]))
        # keep part of the icon's own shading: offset from the matched
        # source lightness, damped, so ramps don't collapse to one flat tone
        chsl = rgb_to_hsl(np.array(rgb_key, dtype=np.float64)[None, :])
        cl = float(chsl[2][0])
        src_l = float(np.median(sl[idx]))
        new_l = np.clip(med_l + RAMP_KEEP * (cl - src_l), 0, 100)
        return hsl_to_rgb(np.array([med_h]), np.array([med_s]),
                          np.array([new_l]))[0].astype(np.float64)

    h_img, w_img = stock_rgba.shape[:2]
    opaque = stock_rgba[..., 3] > 0
    out = stock_rgba.astype(np.float64).copy()

    # per palette color: new color (None = unchanged)
    color_new = {}
    is_neutral = {}
    for y in range(h_img):
        for x in range(w_img):
            if not opaque[y, x]:
                continue
            key = tuple(int(v) for v in stock_rgba[y, x, :3])
            if key in color_new:
                continue
            cv = _rgb_to_hsv(np.array(key, dtype=np.float64)[None, :])
            ch_v, cs_v, cv_v = (float(v[0]) for v in cv)
            neutral = cs_v < SAT_NEUTRAL_V or cv_v < V_BLACK
            is_neutral[key] = neutral
            pool = None if neutral else group_pool(ch_v)
            if not neutral and pool is None:
                color_new[key] = None   # saturated but matches no group
            else:
                color_new[key] = lookup(key, pool)

    # express results as HSL deltas for the speckle-cleanup pass below
    ph, ps, pl = rgb_to_hsl(stock_rgba[..., :3].astype(np.float64))
    pvh, pvs, pvv = _rgb_to_hsv(stock_rgba[..., :3].astype(np.float64))
    delta_of = {}
    for key, new_rgb in color_new.items():
        if new_rgb is None:
            delta_of[key] = (0.0, 0.0, 0.0)
            continue
        chsl = rgb_to_hsl(np.array(key, dtype=np.float64)[None, :])
        nhsl = rgb_to_hsl(new_rgb[None, :])
        d_hue = (float(nhsl[0][0]) - float(chsl[0][0]) + 180.0) % 360.0 - 180.0
        delta_of[key] = (d_hue,
                         float(nhsl[1][0]) - float(chsl[1][0]),
                         float(nhsl[2][0]) - float(chsl[2][0]))

    field = np.zeros((h_img, w_img, 3))
    for y in range(h_img):
        for x in range(w_img):
            if opaque[y, x]:
                field[y, x] = delta_of[tuple(int(v) for v in stock_rgba[y, x, :3])]

    # isolated-speckle cleanup (neutral pixels only -- group transforms are
    # uniform per ramp already): a lone pixel with no similar-colored
    # neighbor whose transform disagrees with the neighborhood keeps its
    # original color
    ph, ps, pl = rgb_to_hsl(stock_rgba[..., :3].astype(np.float64))
    pvh, pvs, pvv = _rgb_to_hsv(stock_rgba[..., :3].astype(np.float64))

    def color_close(y1, x1, y2, x2):
        dh_ = abs(pvh[y1, x1] - pvh[y2, x2])
        dh_ = min(dh_, 360.0 - dh_) / 360.0
        sat_w = min(pvs[y1, x1], pvs[y2, x2])
        return (dh_ * sat_w * 4) ** 2 + ((pvs[y1, x1] - pvs[y2, x2]) * 2) ** 2 \
            + (pvv[y1, x1] - pvv[y2, x2]) ** 2 < 0.08

    cleaned = field.copy()
    for y in range(h_img):
        for x in range(w_img):
            if not opaque[y, x]:
                continue
            key = tuple(int(v) for v in stock_rgba[y, x, :3])
            if not is_neutral.get(key, False):
                continue
            neigh, similar = [], 0
            for ny in range(max(0, y - 1), min(h_img, y + 2)):
                for nx in range(max(0, x - 1), min(w_img, x + 2)):
                    if (ny, nx) == (y, x) or not opaque[ny, nx]:
                        continue
                    neigh.append(field[ny, nx])
                    if color_close(y, x, ny, nx):
                        similar += 1
            if similar == 0 and len(neigh) >= 4:
                med = np.median(np.array(neigh), axis=0)
                hue_dev = abs(field[y, x, 0] - med[0])
                hue_dev = min(hue_dev, 360.0 - hue_dev)
                if hue_dev > 30.0 or abs(field[y, x, 1] - med[1]) > 30.0:
                    cleaned[y, x] = 0.0
    field = cleaned

    for y in range(h_img):
        for x in range(w_img):
            if not opaque[y, x]:
                continue
            d = field[y, x]
            if not d.any():
                continue
            nh = (ph[y, x] + d[0]) % 360.0
            ns = np.clip(ps[y, x] + d[1], 0, 100)
            nl = np.clip(pl[y, x] + d[2], 0, 100)
            out[y, x, :3] = hsl_to_rgb(np.array([nh]), np.array([ns]),
                                       np.array([nl]))[0]
    return out


# --------------------------------------------------------------------------- #
# head crop (model imports)                                                    #
# --------------------------------------------------------------------------- #
def _pixelize_icon(crop_img, out_size=24):
    """Crop -> 24x24 stock icon: NEAREST downscale (hard pixel edges -- BOX
    area-averaging looked fuzzy, not pixel art), quantize to a <=15 color
    palette, 1px melee-style dark outline."""
    inner = out_size - 2
    small = crop_img.resize((inner, inner), Image.NEAREST)
    alpha = np.asarray(small)[..., 3]
    quant = small.convert('RGB').quantize(colors=15, method=Image.MEDIANCUT)
    sq = np.asarray(quant.convert('RGBA')).copy()
    sq[..., 3] = np.where(alpha > 100, 255, 0)

    icon = np.zeros((out_size, out_size, 4), dtype=np.uint8)
    icon[1:1 + inner, 1:1 + inner] = sq
    opq = icon[..., 3] > 0
    outline = np.zeros_like(opq)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            outline |= np.roll(np.roll(opq, dy, 0), dx, 1)
    outline &= ~opq
    icon[outline] = (45, 30, 10, 255)
    return icon.astype(np.float64)


def csp_head_crop(csp_rgba, head_x, head_y, out_size=24, debug_out=None):
    """Stock icon for a MODEL IMPORT from a HEAD-SHOT render (bind pose,
    auto-framed, shadowless) + the projected head-bone position.

    The bone only anchors WHICH silhouette column is the head -- its height
    within the head varies by model (it is the vanilla skeleton's crown, and
    swapped meshes extend above or below it). The head region itself is found
    by silhouette profile: walk down the opaque run containing the head
    column (arms are separate runs in a T-pose, so they never pollute the
    width) and cut at the NECK = first sharp width minimum below the head's
    widest row. Models with no pinch (Kirby-likes) keep the whole silhouette,
    which is exactly right for them."""
    op = csp_rgba[..., 3] > 40
    if not op.any():
        return None
    H, W = op.shape
    hx = int(np.clip(head_x, 0, W - 1))

    def run_at(y, anchor, tol=3, near=10):
        """The opaque [x0, x1] run of row y containing anchor (+- tol), or
        the nearest run within `near` px (split features like ears would
        otherwise kill the walk at their gap)."""
        xs = np.where(op[y])[0]
        if len(xs) == 0:
            return None
        breaks = np.where(np.diff(xs) > 1)[0]
        starts = np.concatenate([[0], breaks + 1])
        ends = np.concatenate([breaks, [len(xs) - 1]])
        best = None
        for s, e in zip(starts, ends):
            if xs[s] - tol <= anchor <= xs[e] + tol:
                return int(xs[s]), int(xs[e])
            d = min(abs(anchor - int(xs[s])), abs(anchor - int(xs[e])))
            if d <= near and (best is None or d < best[0]):
                best = (d, int(xs[s]), int(xs[e]))
        return (best[1], best[2]) if best else None

    # start AT the bone row and walk both ways. Scanning from the image top
    # used to latch onto thin protrusions (Pichu-style ears/antennae), die at
    # the first gap, and emit a sliver icon.
    start = None
    for dy in range(0, H):
        for y in (int(head_y) - dy, int(head_y) + dy):
            if 0 <= y < H and run_at(y, hx) is not None:
                start = y
                break
        if start is not None:
            break
    if start is None:
        return None

    def walk(y_from, step, anchor):
        """Collect (y, x0, x1) rows from y_from in direction step. Heads and
        shoulders widen GRADUALLY and symmetrically; a sudden ONE-SIDED width
        jump is another part merging into the row (a tail or prop behind the
        model at the 3/4 angle) -- clip the merged side back to the previous
        row's extent so it can't hijack the profile or fake a neck cut."""
        out = []
        misses = 0
        prev = None   # previous (x0, x1)
        y = y_from
        while 0 <= y < H:
            r = run_at(y, anchor)
            if r is None:
                misses += 1
                if misses > 2:
                    break
                y += step
                continue
            misses = 0
            if prev is not None and (prev[1] - prev[0] + 1) >= 6:
                prev_w = prev[1] - prev[0] + 1
                w = r[1] - r[0] + 1
                if w > max(prev_w * 1.25, prev_w + 6):
                    lgrow = max(0, prev[0] - r[0])
                    rgrow = max(0, r[1] - prev[1])
                    grow = lgrow + rgrow
                    if grow > 0 and min(lgrow, rgrow) < 0.3 * grow:
                        # one-sided merge: clip the big side(s)
                        x0 = r[0] if lgrow <= 0.3 * grow else prev[0] - 2
                        x1 = r[1] if rgrow <= 0.3 * grow else prev[1] + 2
                        r = (max(r[0], x0), min(r[1], x1))
            out.append((y, r[0], r[1]))
            anchor = (r[0] + r[1]) // 2
            prev = r
            y += step
        return out

    start_run = run_at(start, hx)
    up = walk(start - 1, -1, (start_run[0] + start_run[1]) // 2)
    down = walk(start, +1, hx)
    profile = up[::-1] + down   # ordered top -> bottom

    # cut at the neck: either a hard width pinch below the head's widest row,
    # or the dip-then-regrowth where the torso/shoulders widen again. The
    # bone is the CROWN, so the face is still WIDENING just below it -- cuts
    # are forbidden until a face-height's worth of rows below the bone, or a
    # crown dip-then-cheek-regrowth reads as a neck (the Pikachu strip bug).
    ys_op, _ = np.where(op)
    bbox_h = float(ys_op.max() - ys_op.min() + 1) if len(ys_op) else H
    cut_floor = head_y + 0.10 * bbox_h
    widths = [x1 - x0 + 1 for _y, x0, x1 in profile]
    peak = 0
    dip = None
    cut = len(profile)
    for i in range(1, len(profile)):
        cuttable = profile[i][0] > cut_floor
        if dip is not None and cuttable and widths[i] > 1.35 * widths[dip]:
            cut = dip + 1
            break
        if cuttable and widths[i] < 0.5 * widths[peak]:
            cut = i + 1
            break
        if widths[i] >= widths[peak]:
            peak = i
            dip = None
        elif cuttable and (dip is None or widths[i] <= widths[dip]):
            dip = i   # only rows past the floor may become the neck cut
    profile = profile[:cut]
    if not profile:
        return None
    rows = {y: (x0, x1) for y, x0, x1 in profile}
    y_top = profile[0][0]
    y_end = profile[-1][0]
    x_left = min(r[0] for r in rows.values())
    x_right = max(r[1] for r in rows.values())

    # mask everything outside the per-row head runs (arms, other islands)
    mask = np.zeros_like(op)
    for y, (x0, x1) in rows.items():
        mask[y, x0:x1 + 1] = True

    width = x_right - x_left + 1
    height = y_end - y_top + 1
    side = max(width, height) * 1.08
    ctr_x = (x_left + x_right) / 2.0
    ctr_y = (y_top + y_end) / 2.0
    half = side / 2.0
    box = (int(max(0, ctr_x - half)), int(max(0, ctr_y - half)),
           int(min(W, ctr_x + half)), int(min(H, ctr_y + half)))

    masked = csp_rgba.astype(np.uint8).copy()
    masked[..., 3] = np.where(mask, masked[..., 3], 0)
    crop = Image.fromarray(masked).crop(box)
    if debug_out is not None:
        debug_out.update({'box': box, 'y_top': y_top, 'y_end': y_end,
                          'crop': crop.copy(), 'start': start})
    return _pixelize_icon(crop, out_size)


# --------------------------------------------------------------------------- #
# entry point                                                                  #
# --------------------------------------------------------------------------- #
def generate_stock(vanilla_dir, character, costume_code,
                   modded_dat_path=None, modded_csp=None,
                   head_shot_provider=None):
    """Generate a stock icon PNG for a modded costume.

    vanilla_dir: VANILLA_ASSETS_DIR (Path or str)
    costume_code: e.g. 'PlFxGr'; if its vanilla folder is missing (custom MEX
      slots) the character's Nr folder is used as the reference.
    modded_dat_path: path to the modded costume DAT (preferred source)
    modded_csp: path or PNG bytes of OUR generated CSP (csp-diff fallback)
    head_shot_provider: zero-arg callable -> (png_path_or_bytes, head_dict)
      from generate_csp.generate_head_shot. Called LAZILY, only when texture
      pairing fails (= model import), since the render costs a few seconds.

    Method order:
      texture-diff  recolors of the vanilla model (texture lists align)
      csp-crop      model imports: crop the new model's head from a bind-pose
                    head-shot render (consistent pose, head never out of frame)
      csp-diff      last resort: pixel-aligned CSP color transfer

    Returns (png_bytes, method) or None.
    """
    vanilla_dir = Path(vanilla_dir)
    ref = vanilla_dir / character / costume_code
    if not ref.is_dir() and len(costume_code) >= 4:
        ref = vanilla_dir / character / (costume_code[:4] + 'Nr')
    if not ref.is_dir() and len(costume_code) >= 4:
        # vault character names don't always match the vanilla folder names
        # (Nana skins live under 'Ice Climbers' but assets under 'Nana');
        # costume codes are globally unique, so search every character
        for cand in (costume_code, costume_code[:4] + 'Nr'):
            hits = [d for d in vanilla_dir.glob(f'*/{cand}') if d.is_dir()]
            if hits:
                ref = hits[0]
                break
    # the vanilla stock is only needed as the RECOLOR base; head-shot crops
    # draw the icon from scratch (Nana's vanilla folders ship no stock.png --
    # the IC pair shares Popo's icon -- yet her skins still deserve crops)
    stock_path = ref / 'stock.png'
    stock_exists = stock_path.exists()
    ref_dat = ref / f'{ref.name}.dat'

    pairs = None
    method = None
    if stock_exists and modded_dat_path is not None and ref_dat.exists():
        pairs = texture_pixel_pairs(ref_dat, modded_dat_path)
        method = 'texture-diff'

    # texture lists that don't align mean a DIFFERENT MODEL: color transfer
    # would repaint the wrong character's icon, so crop the real head instead
    if pairs is None and head_shot_provider is not None:
        icon = None
        try:
            shot, head = head_shot_provider()
            if shot is not None and head is not None:
                icon = csp_head_crop(_load_rgba(shot), head['x'], head['y'])
        except Exception as e:
            logger.info(f"stock_gen: head crop failed: {e}")
        if icon is not None:
            img = Image.fromarray(np.clip(icon, 0, 255).astype(np.uint8))
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            logger.info(f"stock_gen: generated {character}/{costume_code} via csp-crop")
            return buf.getvalue(), 'csp-crop'

    if pairs is None and stock_exists and modded_csp is not None:
        ref_csp = ref / 'csp.png'
        if ref_csp.exists():
            pairs = csp_pixel_pairs(ref_csp, modded_csp)
            method = 'csp-diff'
    if pairs is None:
        return None

    stock_rgba = _load_rgba(stock_path)
    result = recolor_stock(stock_rgba, pairs[0], pairs[1])
    img = Image.fromarray(np.clip(result, 0, 255).astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    logger.info(f"stock_gen: generated {character}/{costume_code} via {method}")
    return buf.getvalue(), method
