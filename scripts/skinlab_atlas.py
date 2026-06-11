"""Per-index visibility atlas: which texture indexes actually show on the model.

For each texture index: push a solid magenta, render front + back, measure the
changed pixels vs the baseline render, then restore the original texture.
Output: atlas.json (per-index visible pixel counts + bboxes) and a contact
sheet of diff crops. This is the ground truth for building region maps.

Usage:
  python scripts/skinlab_atlas.py --port 56199 --character Fox --costume PlFxNr \
      --out C:/path/atlas_fox
"""
import argparse
import io
import json
from pathlib import Path

import numpy as np
import requests
from PIL import Image

from skinlab_gauntlet import Lab

CAMS = {
    'front': {'rotX': 0, 'rotY': 0, 'scale': 0.75, 'x': 0, 'y': 10},
    'back': {'rotX': 0, 'rotY': 180, 'scale': 0.75, 'x': 0, 'y': 10},
}
MAGENTA = (255, 0, 255)


def grab(lab, cam):
    lab.camera(**cam)
    img = Image.open(io.BytesIO(lab.frame())).convert('RGB')
    return np.asarray(img, dtype=np.int16)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', required=True)
    ap.add_argument('--character', default='Fox')
    ap.add_argument('--costume', default='PlFxNr')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    lab = Lab(args.port)
    lab.session = lab.open(args.character, args.costume)
    try:
        n = len(lab.session['textures'])
        print(f'{args.character} {args.costume}: {n} textures')
        base = {name: grab(lab, cam) for name, cam in CAMS.items()}

        atlas = {}
        for idx in range(n):
            r = requests.get(f'{lab.base}/texture/{idx}', timeout=30)
            orig = r.content
            size = Image.open(io.BytesIO(orig)).size
            solid = Image.new('RGBA', size, MAGENTA + (255,))
            buf = io.BytesIO()
            solid.save(buf, format='PNG')
            requests.post(f'{lab.base}/texture/{idx}', timeout=60,
                          files={'file': ('t.png', buf.getvalue(), 'image/png')})

            entry = {'size': list(size)}
            for name, cam in CAMS.items():
                diff = (np.abs(grab(lab, cam) - base[name]).sum(axis=2) > 40)
                count = int(diff.sum())
                entry[name] = {'pixels': count}
                if count > 30:
                    ys, xs = np.nonzero(diff)
                    entry[name]['bbox'] = [int(xs.min()), int(ys.min()),
                                           int(xs.max()), int(ys.max())]
            atlas[idx] = entry
            vis = {k: v['pixels'] for k, v in entry.items() if k != 'size'}
            print(f'  [{idx:2}] {size[0]}x{size[1]} visible={vis}')

            # restore the original so later indexes diff cleanly
            requests.post(f'{lab.base}/texture/{idx}', timeout=60,
                          files={'file': ('t.png', orig, 'image/png')})

        (out_dir / 'atlas.json').write_text(json.dumps(atlas, indent=1),
                                            encoding='utf-8')
        print('atlas ->', out_dir / 'atlas.json')
    finally:
        lab.close()


if __name__ == '__main__':
    main()
