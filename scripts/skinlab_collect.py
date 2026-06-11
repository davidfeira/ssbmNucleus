"""Mapping-campaign data collector: everything needed to classify a character's
texture regions, gathered automatically per fighter.

Per character it saves into <out>/<char-slug>/:
  baseline.jpg   -- front + back + CSP review sheet of the stock costume
  contact.png    -- numbered texture-thumbnail grid
  atlas.json     -- per-index on-model visibility (solid push -> diff -> restore)
  stats.json     -- per-index size + alpha coverage + hue/sat/lum summary

Usage:
  python scripts/skinlab_collect.py --port 56199 --out C:/path/mapping
  python scripts/skinlab_collect.py --port 56199 --out ... --only Falco,Marth
"""
import argparse
import io
import json
import re
import sys
import traceback
from pathlib import Path

import numpy as np
import requests
from PIL import Image

from skinlab_atlas import CAMS, MAGENTA, grab
from skinlab_gauntlet import Lab, capture_review_sheet, contact_sheet

ROSTER = [
    ('Bowser', 'PlKpNr'), ('C. Falcon', 'PlCaNr'), ('DK', 'PlDkNr'),
    ('Dr. Mario', 'PlDrNr'), ('Falco', 'PlFcNr'), ('Fox', 'PlFxNr'),
    ('Ganondorf', 'PlGnNr'), ('Ice Climbers', 'PlPpNr'),
    ('Jigglypuff', 'PlPrNr'), ('Kirby', 'PlKbNr'), ('Link', 'PlLkNr'),
    ('Luigi', 'PlLgNr'), ('Mario', 'PlMrNr'), ('Marth', 'PlMsNr'),
    ('Mewtwo', 'PlMtNr'), ('Nana', 'PlNnNr'), ('Ness', 'PlNsNr'),
    ('Peach', 'PlPeNr'), ('Pichu', 'PlPcNr'), ('Pikachu', 'PlPkNr'),
    ('Roy', 'PlFeNr'), ('Samus', 'PlSsNr'), ('Sheik', 'PlSkNr'),
    ('Yoshi', 'PlYsNr'), ('Young Link', 'PlClNr'), ('Zelda', 'PlZdNr'),
]


def slugify(name):
    return re.sub(r'[^\w]+', '_', name).strip('_')


def rgb_to_hsl(rgb):
    r, g, b = rgb[..., 0] / 255.0, rgb[..., 1] / 255.0, rgb[..., 2] / 255.0
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    l = (mx + mn) / 2
    d = mx - mn
    s = np.where(d == 0, 0, d / (1 - np.abs(2 * l - 1) + 1e-9))
    h = np.zeros_like(l)
    m = (mx == r) & (d > 0)
    h[m] = ((g[m] - b[m]) / d[m]) % 6
    m = (mx == g) & (d > 0)
    h[m] = (b[m] - r[m]) / d[m] + 2
    m = (mx == b) & (d > 0)
    h[m] = (r[m] - g[m]) / d[m] + 4
    return h * 60, s * 100, l * 100


def texture_stats(img):
    arr = np.asarray(img.convert('RGBA'), dtype=np.float64)
    alpha = arr[..., 3] >= 128
    out = {'size': list(img.size), 'opaquePct': round(float(alpha.mean()) * 100, 1)}
    if not alpha.any():
        return out
    h, s, l = rgb_to_hsl(arr[..., :3])
    hs, ss, ls = h[alpha], s[alpha], l[alpha]
    out['meanSat'] = round(float(ss.mean()), 1)
    out['meanLum'] = round(float(ls.mean()), 1)
    sat = ss >= 20
    out['saturatedPct'] = round(float(sat.mean()) * 100, 1)
    if sat.any():
        bins = np.bincount(np.floor(hs[sat]).astype(int) % 360, minlength=360)
        # top 2 hue bands, 30-degree smoothing
        smooth = np.convolve(np.concatenate([bins, bins[:30]]),
                             np.ones(30), mode='valid')[:360]
        top = int(smooth.argmax())
        out['topHueBands'] = [{'center': (top + 15) % 360,
                               'share': round(float(bins[(np.arange(top, top + 30) % 360)].sum()
                                                    / max(1, bins.sum())), 2)}]
        bins2 = bins.copy()
        bins2[(np.arange(top - 20, top + 50) % 360)] = 0
        if bins2.sum() > bins.sum() * 0.15:
            t2 = int(np.convolve(np.concatenate([bins2, bins2[:30]]),
                                 np.ones(30), mode='valid')[:360].argmax())
            out['topHueBands'].append({'center': (t2 + 15) % 360,
                                       'share': round(float(bins2[(np.arange(t2, t2 + 30) % 360)].sum()
                                                            / max(1, bins.sum())), 2)})
    return out


def collect(lab, character, code, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    lab.session = lab.open(character, code)
    try:
        n = len(lab.session['textures'])
        print(f'{character} ({code}): {n} textures', flush=True)

        sheet_bytes, _ = capture_review_sheet(lab)
        (out_dir / 'baseline.jpg').write_bytes(sheet_bytes)

        _, sheet_img = contact_sheet(lab, list(range(n)))
        sheet_img.save(out_dir / 'contact.png')

        stats = {}
        originals = {}
        for idx in range(n):
            img = lab.texture(idx)
            stats[idx] = texture_stats(img)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            originals[idx] = buf.getvalue()

        # visibility atlas: solid push -> diff vs baseline -> restore
        base = {name: grab(lab, cam) for name, cam in CAMS.items()}
        for idx in range(n):
            size = Image.open(io.BytesIO(originals[idx])).size
            solid = Image.new('RGBA', size, MAGENTA + (255,))
            buf = io.BytesIO()
            solid.save(buf, format='PNG')
            requests.post(f'{lab.base}/texture/{idx}', timeout=60,
                          files={'file': ('t.png', buf.getvalue(), 'image/png')})
            for name, cam in CAMS.items():
                diff = (np.abs(grab(lab, cam) - base[name]).sum(axis=2) > 40)
                count = int(diff.sum())
                stats[idx][f'visible_{name}'] = count
                if count > 30:
                    ys, xs = np.nonzero(diff)
                    stats[idx][f'bbox_{name}'] = [int(xs.min()), int(ys.min()),
                                                  int(xs.max()), int(ys.max())]
            requests.post(f'{lab.base}/texture/{idx}', timeout=60,
                          files={'file': ('t.png', originals[idx], 'image/png')})

        (out_dir / 'stats.json').write_text(json.dumps(stats, indent=1),
                                            encoding='utf-8')
        print(f'  -> {out_dir}', flush=True)
    finally:
        lab.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--only', default='')
    args = ap.parse_args()

    only = {s.strip() for s in args.only.split(',') if s.strip()}
    failures = []
    for character, code in ROSTER:
        if only and character not in only:
            continue
        out_dir = Path(args.out) / slugify(character)
        if (out_dir / 'stats.json').exists():
            print(f'{character}: already collected, skipping', flush=True)
            continue
        lab = Lab(args.port)
        try:
            collect(lab, character, code, out_dir)
        except Exception:
            failures.append(character)
            print(f'FAILED {character}:', flush=True)
            traceback.print_exc()
            try:
                lab.close()
            except Exception:
                pass
    print('done. failures:', failures or 'none', flush=True)
    sys.exit(1 if failures else 0)


if __name__ == '__main__':
    main()
