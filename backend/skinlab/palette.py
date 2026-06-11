"""
palette.py -- server-side port of the Skin Creator's color palette tool
(viewer/src/components/skincreator/colorUtils.js), vectorized with numpy.

Same semantics as the UI: pool every texture's opaque, non-gray, mid-lightness
pixels into 1-degree hue bins, merge adjacent bins (gap <= 25 degrees) into
color groups, fit to the requested group count (merge closest / split widest),
then apply per-group hue/saturation shifts back onto the ORIGINAL pixels.
Lightness is never touched, so shading survives recolors.
"""

import numpy as np

HUE_TOLERANCE = 25
MIN_GROUP_PIXELS = 100


# --------------------------------------------------------------------------- #
# vectorized HSL <-> RGB (matches the JS math: h in [0,360), s/l in [0,100])   #
# --------------------------------------------------------------------------- #
def rgb_to_hsl(rgb):
    """rgb: float array (..., 3) in 0..255 -> (h, s, l) arrays."""
    r, g, b = rgb[..., 0] / 255.0, rgb[..., 1] / 255.0, rgb[..., 2] / 255.0
    cmax = np.maximum(np.maximum(r, g), b)
    cmin = np.minimum(np.minimum(r, g), b)
    l = (cmax + cmin) / 2.0
    d = cmax - cmin
    with np.errstate(divide='ignore', invalid='ignore'):
        s = np.where(d == 0, 0.0,
                     np.where(l > 0.5, d / (2.0 - cmax - cmin), d / (cmax + cmin)))
        h_r = ((g - b) / d + np.where(g < b, 6.0, 0.0)) / 6.0
        h_g = ((b - r) / d + 2.0) / 6.0
        h_b = ((r - g) / d + 4.0) / 6.0
    # JS switch picks the FIRST channel equal to max: r, then g, then b
    h = np.select([d == 0, cmax == r, cmax == g], [0.0, h_r, h_g], default=h_b)
    h = np.nan_to_num(h, nan=0.0)
    s = np.nan_to_num(s, nan=0.0)
    return h * 360.0, s * 100.0, l * 100.0


def hsl_to_rgb(h, s, l):
    """h in degrees, s/l in 0..100 -> uint8 array (..., 3)."""
    h = (h % 360.0) / 360.0
    s = np.clip(s, 0, 100) / 100.0
    l = np.clip(l, 0, 100) / 100.0

    def hue2rgb(p, q, t):
        t = np.mod(t, 1.0)
        return np.select(
            [t < 1 / 6, t < 1 / 2, t < 2 / 3],
            [p + (q - p) * 6 * t, q, p + (q - p) * (2 / 3 - t) * 6],
            default=p)

    q = np.where(l < 0.5, l * (1 + s), l + s - l * s)
    p = 2 * l - q
    r = np.where(s == 0, l, hue2rgb(p, q, h + 1 / 3))
    g = np.where(s == 0, l, hue2rgb(p, q, h))
    b = np.where(s == 0, l, hue2rgb(p, q, h - 1 / 3))
    return np.stack([np.round(r * 255), np.round(g * 255), np.round(b * 255)],
                    axis=-1).astype(np.uint8)


def _valid_mask(rgba):
    """The pixels the palette tool considers: opaque enough, not near
    black/white, not gray."""
    h, s, l = rgb_to_hsl(rgba[..., :3].astype(np.float64))
    mask = (rgba[..., 3] >= 128) & (l >= 10) & (l <= 90) & (s >= 15)
    return mask, h, s, l


# --------------------------------------------------------------------------- #
# analysis                                                                     #
# --------------------------------------------------------------------------- #
def analyze(textures, max_groups=8):
    """textures: {index: HxWx4 uint8 array}. Returns (groups, pixel_maps):
    groups is a list of dicts (ordered by pixel count), pixel_maps maps each
    texture index to a flat uint8 array (255 = unassigned)."""
    bins_count = np.zeros(360, dtype=np.int64)
    bins_s = np.zeros(360, dtype=np.float64)
    bins_l = np.zeros(360, dtype=np.float64)

    per_tex = {}
    for idx, rgba in textures.items():
        mask, h, s, l = _valid_mask(rgba)
        per_tex[idx] = (mask, h)
        hv = np.floor(h[mask]).astype(np.int64) % 360
        bins_count += np.bincount(hv, minlength=360)
        bins_s += np.bincount(hv, weights=s[mask], minlength=360)
        bins_l += np.bincount(hv, weights=l[mask], minlength=360)

    # merge adjacent occupied bins (gap <= tolerance) into raw groups
    raw = []
    current = None
    for hdeg in range(360):
        if bins_count[hdeg] > 0:
            if current is None:
                current = {'start': hdeg, 'end': hdeg, 'count': int(bins_count[hdeg]),
                           'total_s': float(bins_s[hdeg]), 'total_l': float(bins_l[hdeg])}
            elif hdeg - current['end'] <= HUE_TOLERANCE:
                current['end'] = hdeg
                current['count'] += int(bins_count[hdeg])
                current['total_s'] += float(bins_s[hdeg])
                current['total_l'] += float(bins_l[hdeg])
            else:
                if current['count'] >= MIN_GROUP_PIXELS:
                    raw.append(current)
                current = {'start': hdeg, 'end': hdeg, 'count': int(bins_count[hdeg]),
                           'total_s': float(bins_s[hdeg]), 'total_l': float(bins_l[hdeg])}
    if current and current['count'] >= MIN_GROUP_PIXELS:
        raw.append(current)

    # red wraps around 0/360
    if len(raw) >= 2:
        first, last = raw[0], raw[-1]
        if first['start'] < HUE_TOLERANCE and last['end'] > 360 - HUE_TOLERANCE:
            first['start'] = last['start'] - 360
            first['count'] += last['count']
            first['total_s'] += last['total_s']
            first['total_l'] += last['total_l']
            raw.pop()

    # merge closest pairs down to max_groups
    while len(raw) > max_groups:
        min_dist, mi, mj = float('inf'), 0, 1
        for i in range(len(raw)):
            for j in range(i + 1, len(raw)):
                h1 = ((raw[i]['start'] + raw[i]['end']) / 2 + 360) % 360
                h2 = ((raw[j]['start'] + raw[j]['end']) / 2 + 360) % 360
                dist = abs(h1 - h2)
                if dist > 180:
                    dist = 360 - dist
                if dist < min_dist:
                    min_dist, mi, mj = dist, i, j
        gi, gj = raw[mi], raw[mj]
        gi['start'] = min(gi['start'], gj['start'])
        gi['end'] = max(gi['end'], gj['end'])
        gi['count'] += gj['count']
        gi['total_s'] += gj['total_s']
        gi['total_l'] += gj['total_l']
        raw.pop(mj)

    # split widest groups up to max_groups
    while 0 < len(raw) < max_groups:
        widest = max(range(len(raw)), key=lambda i: raw[i]['end'] - raw[i]['start'])
        g = raw[widest]
        if g['end'] - g['start'] < 2:
            break
        mid = (g['start'] + g['end']) // 2
        g1 = {'start': g['start'], 'end': mid, 'count': g['count'] // 2,
              'total_s': g['total_s'] / 2, 'total_l': g['total_l'] / 2}
        g2 = {'start': mid + 1, 'end': g['end'], 'count': g['count'] - g['count'] // 2,
              'total_s': g['total_s'] / 2, 'total_l': g['total_l'] / 2}
        raw[widest:widest + 1] = [g1, g2]

    raw.sort(key=lambda g: -g['count'])

    groups = []
    for i, g in enumerate(raw):
        avg_s = g['total_s'] / g['count'] if g['count'] else 0
        avg_l = g['total_l'] / g['count'] if g['count'] else 0
        center = ((g['start'] + g['end']) / 2 + 360) % 360
        rgb = hsl_to_rgb(np.array([center]), np.array([avg_s]), np.array([avg_l]))[0]
        groups.append({
            'index': i,
            'centerHue': round(center, 1),
            'hueRange': [(g['start'] + 360) % 360, g['end'] % 360],
            'pixelCount': int(g['count']),
            'avgSaturation': round(avg_s, 1),
            'avgLightness': round(avg_l, 1),
            'displayColor': '#%02x%02x%02x' % tuple(int(v) for v in rgb),
        })

    # per-texture pixel -> group map (first matching group wins, like the UI)
    pixel_maps = {}
    for idx, (mask, h) in per_tex.items():
        flat_mask = mask.ravel()
        flat_h = h.ravel()
        gmap = np.full(flat_mask.shape, 255, dtype=np.uint8)
        unassigned = flat_mask.copy()
        for gi, g in enumerate(groups):
            lo, hi = g['hueRange']
            if lo <= hi:
                in_range = (flat_h >= lo - HUE_TOLERANCE) & (flat_h <= hi + HUE_TOLERANCE)
            else:  # wraps 0
                in_range = (flat_h >= lo - HUE_TOLERANCE) | (flat_h <= hi + HUE_TOLERANCE)
            sel = unassigned & in_range
            gmap[sel] = gi
            unassigned &= ~sel
        pixel_maps[idx] = gmap

    return groups, pixel_maps


def apply_adjustments(original_rgba, pixel_map, adjustments):
    """Apply per-group {index: (hue_shift, sat_shift)} to a texture's ORIGINAL
    pixels. Returns a new HxWx4 uint8 array (or None if nothing changed)."""
    active = {gi: (hs, ss) for gi, (hs, ss) in adjustments.items() if hs or ss}
    if not active:
        return None
    out = original_rgba.copy()
    flat = out.reshape(-1, 4)
    changed = False
    for gi, (hue_shift, sat_shift) in active.items():
        sel = pixel_map == gi
        if not sel.any():
            continue
        changed = True
        px = flat[sel]
        h, s, l = rgb_to_hsl(px[:, :3].astype(np.float64))
        h = (h + hue_shift) % 360.0
        s = np.clip(s + sat_shift, 0, 100)
        px[:, :3] = hsl_to_rgb(h, s, l)
        flat[sel] = px
    return out if changed else None
