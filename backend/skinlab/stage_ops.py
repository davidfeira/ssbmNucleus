"""Stage texture operations -- offline plan execution for the Stage AI Studio.

Stages can't render in the streaming viewer (map_head models), so the flow is
file-based: exported texture PNGs -> compose ops -> spec.json -> the
HSDRawViewer --stage-textures CLI rebuilds a variant .dat. Verification is an
in-game capture (ingame.capture), not a viewer frame.
"""
import json
import logging
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

from core.config import HSDRAW_EXE, STORAGE_PATH, get_subprocess_args
from skinlab import compose as compose_mod

logger = logging.getLogger(__name__)

STAGE_DATS_DIR = STORAGE_PATH / 'skinlab_stages'
STAGE_REGIONS_DIR = Path(__file__).resolve().parents[1] / 'assets' / 'texture_regions' / 'stages'


class StageOpsError(Exception):
    pass


def stage_region_map(code):
    path = STAGE_REGIONS_DIR / f'{code}.json'
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def ensure_exports(code):
    """Export the vanilla stage's textures via the CLI if not already done.
    Returns the export directory (with manifest.json)."""
    dat = STAGE_DATS_DIR / f'{code}.dat'
    if not dat.exists():
        raise StageOpsError(
            f'Vanilla stage dat missing: {dat} (run the stage extraction once)')
    out_dir = STAGE_DATS_DIR / f'{code}_textures'
    if (out_dir / 'manifest.json').exists():
        return out_dir
    r = subprocess.run([str(HSDRAW_EXE), '--stage-textures', 'export',
                        str(dat), str(out_dir)],
                       capture_output=True, text=True, timeout=300,
                       **get_subprocess_args())
    if not (out_dir / 'manifest.json').exists():
        raise StageOpsError('stage texture export failed: '
                            + (r.stdout or r.stderr or '')[-300:])
    return out_dir


def apply_stage_plan(code, steps, material_tints, work_dir, generate_material,
                     on_step=None):
    """Apply plan steps to the exported PNGs and build the variant dat.
    generate_material(prompt) -> path to a material PNG.
    Returns the output dat path."""
    region_map = stage_region_map(code)
    if region_map is None:
        raise StageOpsError(f'No region map for stage {code}')
    exports_dir = ensure_exports(code)
    manifest = json.loads((exports_dir / 'manifest.json').read_text(encoding='utf-8'))
    by_index = {e['index']: e for e in manifest['textures']}
    protected = set(region_map.get('protected') or [])
    work_dir = Path(work_dir)
    (work_dir / 'pngs').mkdir(parents=True, exist_ok=True)

    current = {}

    def load(idx):
        if idx not in current:
            img = Image.open(exports_dir / by_index[idx]['filename']).convert('RGBA')
            current[idx] = np.asarray(img, dtype=np.uint8).copy()
        return current[idx]

    for i, s in enumerate(steps):
        region = s.get('region')
        indexes = (region_map['regions'].get(region) or [])
        op = s.get('op')
        if on_step:
            on_step(i, f'{op} {region}')
        if not indexes:
            continue
        mat = None
        if op == 'composite':
            mat_path = generate_material(s['material_prompt'])
            mat = np.asarray(Image.open(mat_path).convert('RGB'), dtype=np.uint8)
        changed = []
        for idx in indexes:
            if op == 'composite' and idx in protected:
                continue
            arr = load(idx)
            mask = compose_mod.build_mask(arr)
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
                continue
            current[idx] = result
            changed.append(idx)
        logger.info(f'[stage-ops] {op}:{region} changed={changed}')

    spec = {'replacements': []}
    for idx, arr in current.items():
        p = work_dir / 'pngs' / f't{idx}.png'
        Image.fromarray(arr, 'RGBA').save(p)
        spec['replacements'].append({'index': idx, 'png': str(p)})
    if material_tints:
        spec['materialTints'] = material_tints
    spec_path = work_dir / 'spec.json'
    spec_path.write_text(json.dumps(spec, indent=1), encoding='utf-8')

    out_dat = work_dir / f'{code}.dat'
    r = subprocess.run([str(HSDRAW_EXE), '--stage-textures', 'import',
                        str(STAGE_DATS_DIR / f'{code}.dat'),
                        str(spec_path), str(out_dat)],
                       capture_output=True, text=True, timeout=300,
                       **get_subprocess_args())
    if not out_dat.exists():
        raise StageOpsError('variant dat import failed: '
                            + (r.stdout or r.stderr or '')[-300:])
    return out_dat
