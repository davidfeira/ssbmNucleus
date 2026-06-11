"""Stage region diagnostic: push a LOUD solid color per region (or per texture
chunk), build + capture once, and see what actually changes on screen.

Usage:
  python scripts/skinlab_stage_diag.py --code GrNLa --vanilla <iso> --slippi <exe>
      [--chunks N]   split ALL textures into N chunks with distinct colors
                     (region mode if omitted: one color per mapped region)
"""
import argparse
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from PIL import Image

SCRIPTS = Path(__file__).parent
REPO = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / 'backend'))

from skinlab_stage_lab import DEFAULT_DATS, DEFAULT_EXPORTS, DEFAULT_HSDCLI, REGION_DIR  # noqa: E402

COLORS = [(255, 0, 0), (0, 255, 0), (0, 80, 255), (255, 255, 0),
          (255, 0, 255), (0, 255, 255), (255, 128, 0), (128, 0, 255)]
NAMES = ['RED', 'GREEN', 'BLUE', 'YELLOW', 'MAGENTA', 'CYAN', 'ORANGE', 'PURPLE']


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--code', required=True)
    ap.add_argument('--vanilla', required=True)
    ap.add_argument('--slippi', required=True)
    ap.add_argument('--chunks', type=int, default=0)
    ap.add_argument('--range', default=None,
                    help='limit chunking to an index range, e.g. "100-124"')
    args = ap.parse_args()

    import test_build
    from core.config import STORAGE_PATH
    from ingame.capture import capture_stage
    from ingame.melee_sss import INTERNAL_STAGE_ID

    exports = DEFAULT_EXPORTS / args.code / 'textures'
    manifest = json.loads((exports / 'manifest.json').read_text(encoding='utf-8'))
    by_index = {e['index']: e for e in manifest['textures']}
    work = DEFAULT_EXPORTS / args.code / 'diag'
    (work / 'pngs').mkdir(parents=True, exist_ok=True)

    if args.chunks:
        all_idx = sorted(by_index)
        if args.range:
            lo, hi = (int(x) for x in args.range.split('-'))
            all_idx = [i for i in all_idx if lo <= i <= hi]
        size = (len(all_idx) + args.chunks - 1) // args.chunks
        groups = [(NAMES[i % 8], COLORS[i % 8], all_idx[i * size:(i + 1) * size])
                  for i in range(args.chunks)]
    else:
        rm = json.loads((REGION_DIR / f'{args.code}.json').read_text(encoding='utf-8'))
        groups = [(f'{name}={NAMES[i % 8]}', COLORS[i % 8], idxs)
                  for i, (name, idxs) in enumerate(rm['regions'].items())]

    replacements = []
    for label, color, idxs in groups:
        print(f'  {label}: {idxs}', flush=True)
        for idx in idxs:
            e = by_index.get(idx)
            if not e:
                continue
            p = work / 'pngs' / f't{idx}.png'
            Image.new('RGBA', (e['width'], e['height']), color + (255,)).save(p)
            replacements.append({'index': idx, 'png': str(p)})

    spec_path = work / 'spec.json'
    spec_path.write_text(json.dumps({'replacements': replacements}, indent=1),
                         encoding='utf-8')
    out_dat = work / f'{args.code}.dat'
    subprocess.run([str(DEFAULT_HSDCLI), '--stage-textures', 'import',
                    str(Path(DEFAULT_DATS) / f'{args.code}.dat'),
                    str(spec_path), str(out_dat)],
                   capture_output=True, text=True, timeout=300)

    folder, framing_key = test_build.DAS_STAGES[args.code]
    das_dir = REPO / 'storage' / 'das' / folder
    das_dir.mkdir(parents=True, exist_ok=True)
    zip_path = das_dir / 'diag-tmp.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(out_dat, f'{args.code}.dat')
    iso = STORAGE_PATH / 'test-builds' / f'diag_{args.code}.iso'
    try:
        test_build.build_stage_skin_iso(args.vanilla, args.code, folder, 'diag-tmp',
                                        str(iso), button='X', log=lambda m: None)
        res = capture_stage(str(iso), args.slippi, str(STORAGE_PATH / 'test-runs'),
                            internal_id=INTERNAL_STAGE_ID[framing_key], hold='X',
                            framing_key=framing_key, log=lambda m: None, settle=4.0)
        shot = work / 'diag.png'
        if res.get('png'):
            shot.write_bytes(res['png'])
            print('diag shot ->', shot, flush=True)
        else:
            print('CAPTURE FAILED:', res.get('reason'), flush=True)
    finally:
        iso.unlink(missing_ok=True)
        zip_path.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
