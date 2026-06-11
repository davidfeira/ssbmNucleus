"""Stage texture lab: execute a plan (composite/tint/hue-shift on stage regions)
entirely offline -- no viewer session.

Pipeline per run:
  1. textures already exported via `HSDRawViewer.exe --stage-textures export`
  2. apply plan steps to the PNGs (same compose engine as the fighter lab)
  3. write modified PNGs + spec.json, `--stage-textures import` -> variant .dat
  4. (separately) zip as DAS variant / build test ISO / in-game capture

Usage:
  python scripts/skinlab_stage_lab.py --code GrNBa --plan plan.json --name lava-bf
Optional: --exports <dir> --dats <dir> --out <dir> --hsdcli <exe>
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

SCRIPTS = Path(__file__).parent
REPO = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / 'backend'))

from skinlab import compose as compose_mod  # noqa: E402

DEFAULT_EXPORTS = REPO.parent / 'gauntlet_out' / 'stages'
DEFAULT_DATS = REPO / 'storage' / 'skinlab_stages'
DEFAULT_HSDCLI = REPO.parent / 'tmp_skinlab' / 'hsdcli' / 'HSDRawViewer.exe'
REGION_DIR = REPO / 'backend' / 'assets' / 'texture_regions' / 'stages'
MATERIAL_DIR = REPO / 'storage' / 'skinlab_materials'


def _assetfarm_generate(prompt, out):
    """Local fallback via assetFarm (free; sd-turbo = ~16s/tile incl. cold start)."""
    farm = Path(os.environ.get('NUCLEUS_ASSETFARM_DIR',
                               str(Path.home() / 'projects' / 'assetFarm')))
    model = os.environ.get('NUCLEUS_ASSETFARM_MODEL', 'sd-turbo')
    py = farm / '.venv' / 'Scripts' / 'python.exe'
    r = subprocess.run([str(py), '-m', 'assetfarm', 'generate', 'tileset_tile',
                        '-p', prompt, '--model', model, '--json'],
                       cwd=str(farm), capture_output=True, text=True, timeout=900)
    info = json.loads(r.stdout.strip().splitlines()[-1])
    src = Path(info['output_paths'][0])
    if not src.is_absolute():
        src = farm / src
    out.write_bytes(src.read_bytes())
    return out


def generate_material(prompt, name):
    """OpenRouter image generation, assetFarm local FLUX as the fallback.
    NUCLEUS_IMAGE_PROVIDER=assetfarm forces local (cost control for batches)."""
    import base64
    import requests
    out = MATERIAL_DIR / f'{name}.png'
    if out.exists():
        return out
    MATERIAL_DIR.mkdir(parents=True, exist_ok=True)
    forced = os.environ.get('NUCLEUS_IMAGE_PROVIDER', '').strip().lower()
    key = os.environ.get('OPENROUTER_API_KEY')
    if key and forced != 'assetfarm':
        full = ('Generate a seamless tileable TEXTURE swatch, square, repeating '
                'pattern, no borders, no text, fills the whole image edge to '
                f'edge: {prompt}')
        r = requests.post('https://openrouter.ai/api/v1/chat/completions', timeout=180, json={
            'model': 'google/gemini-2.5-flash-image',
            'messages': [{'role': 'user', 'content': full}],
            'modalities': ['image', 'text'],
        }, headers={'Authorization': f'Bearer {key}'}).json()
        images = (r.get('choices') or [{}])[0].get('message', {}).get('images') or []
        if images:
            url = images[0]['image_url']['url']
            out.write_bytes(base64.b64decode(url.split('base64,', 1)[1]))
            return out
        print(f'  openrouter image gen unavailable ({str(r)[:120]}); using local flux')
    return _assetfarm_generate(prompt, out)


def apply_plan(code, plan, exports_dir, work_dir):
    """Apply plan steps to exported PNGs; returns {index: out_path} changed."""
    region_map = json.loads((REGION_DIR / f'{code}.json').read_text(encoding='utf-8'))
    manifest = json.loads((exports_dir / 'manifest.json').read_text(encoding='utf-8'))
    by_index = {e['index']: e for e in manifest['textures']}
    protected = set(region_map.get('protected') or [])
    work_dir.mkdir(parents=True, exist_ok=True)

    current = {}   # index -> np array (lazily loaded)

    def load(idx):
        if idx not in current:
            img = Image.open(exports_dir / by_index[idx]['filename']).convert('RGBA')
            current[idx] = np.asarray(img, dtype=np.uint8).copy()
        return current[idx]

    for s in plan['steps']:
        region = s['region']
        indexes = (region_map['regions'].get(region) or [])
        if not indexes:
            print(f'  SKIP unknown region {region}')
            continue
        op = s['op']
        mat = None
        if op == 'composite':
            mat_path = generate_material(s['material_prompt'],
                                         f"stage_{abs(hash(s['material_prompt'])) % 10**10}")
            mat = np.asarray(Image.open(mat_path).convert('RGB'), dtype=np.uint8)
        changed, skipped = [], []
        for idx in indexes:
            if op == 'composite' and idx in protected:
                skipped.append((idx, 'protected'))
                continue
            arr = load(idx)
            mask = compose_mod.build_mask(arr)   # all opaque pixels
            if op == 'composite':
                mod = s.get('modulate') or {}
                result = compose_mod.composite(arr, mat, mask,
                                               lum_lo=float(mod.get('lo', 0.4)),
                                               lum_hi=float(mod.get('hi', 1.6)))
            elif op == 'tint':
                result = compose_mod.tint(arr, mask, float(s['hue']),
                                          float(s.get('saturation', 60)))
            else:
                result = compose_mod.hue_shift(arr, mask,
                                               float(s.get('hueShift', 0)),
                                               float(s.get('saturationShift', 0)))
            if result is None:
                skipped.append((idx, 'mask matched nothing'))
                continue
            current[idx] = result
            changed.append(idx)
        print(f'  {op}:{region} changed={changed}'
              + (f' skipped={skipped}' if skipped else ''))

    outputs = {}
    for idx, arr in current.items():
        out_path = work_dir / f't{idx}.png'
        Image.fromarray(arr, 'RGBA').save(out_path)
        outputs[idx] = out_path
    return outputs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--code', required=True)
    ap.add_argument('--plan', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--exports', default=None)
    ap.add_argument('--dats', default=str(DEFAULT_DATS))
    ap.add_argument('--out', default=None)
    ap.add_argument('--hsdcli', default=str(DEFAULT_HSDCLI))
    args = ap.parse_args()

    exports_dir = Path(args.exports) if args.exports \
        else DEFAULT_EXPORTS / args.code / 'textures'
    out_dir = Path(args.out) if args.out else DEFAULT_EXPORTS / args.code / args.name
    plan = json.loads(Path(args.plan).read_text(encoding='utf-8'))

    outputs = apply_plan(args.code, plan, exports_dir, out_dir / 'pngs')
    spec = {'replacements': [{'index': i, 'png': str(p)} for i, p in outputs.items()]}
    if plan.get('materialTints'):
        spec['materialTints'] = plan['materialTints']
    spec_path = out_dir / 'spec.json'
    spec_path.write_text(json.dumps(spec, indent=1), encoding='utf-8')

    src_dat = Path(args.dats) / f'{args.code}.dat'
    out_dat = out_dir / f'{args.code}.dat'
    r = subprocess.run([args.hsdcli, '--stage-textures', 'import',
                        str(src_dat), str(spec_path), str(out_dat)],
                       capture_output=True, text=True, timeout=300)
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[:400])
    if not out_dat.exists():
        raise SystemExit('import failed')
    print('variant dat ->', out_dat)


if __name__ == '__main__':
    main()
