"""Build MY stage skins for the DAS vault: apply each plan, import to a variant
dat, zip into storage/das/<folder>/<variant>.zip, capture an in-game shot, and
save it as <variant>_screenshot.png next to the zip (the DAS vault layout).

Resumable: skips variants whose zip + screenshot both exist.

Usage:
  python scripts/skinlab_stage_mine.py --plans <my_stage_plans.json> \
      --vanilla <iso> --slippi <exe> [--only GrNLa,GrIz]
"""
import argparse
import json
import subprocess
import sys
import zipfile
from pathlib import Path

SCRIPTS = Path(__file__).parent
REPO = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / 'backend'))

from skinlab_stage_lab import DEFAULT_DATS, DEFAULT_EXPORTS, DEFAULT_HSDCLI, apply_plan  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plans', required=True)
    ap.add_argument('--vanilla', required=True)
    ap.add_argument('--slippi', required=True)
    ap.add_argument('--only', default='')
    args = ap.parse_args()

    import test_build
    from core.config import STORAGE_PATH
    from ingame.capture import capture_stage
    from ingame.melee_sss import INTERNAL_STAGE_ID
    from skinlab.stage_ops import stage_file_name

    plans = json.loads(Path(args.plans).read_text(encoding='utf-8'))
    only = {s.strip() for s in args.only.split(',') if s.strip()}
    failures = []

    for code, plan in plans.items():
        if only and code not in only:
            continue
        variant = plan['variant']
        folder, framing_key = test_build.DAS_STAGES[code]
        das_dir = REPO / 'storage' / 'das' / folder
        das_dir.mkdir(parents=True, exist_ok=True)
        zip_path = das_dir / f'{variant}.zip'
        shot_path = das_dir / f'{variant}_screenshot.png'
        if zip_path.exists() and shot_path.exists():
            print(f'{code}/{variant}: already in the vault, skipping', flush=True)
            continue
        print(f'=== {code} -> {variant} ("{plan["skin_name"]}")', flush=True)
        try:
            work = DEFAULT_EXPORTS / code / variant
            out_dat = work / stage_file_name(code)
            if plan['steps'] or plan.get('materialTints'):
                outputs = apply_plan(code, plan, DEFAULT_EXPORTS / code / 'textures',
                                     work / 'pngs')
                spec = {'replacements': [{'index': i, 'png': str(p)}
                                         for i, p in outputs.items()]}
                if plan.get('materialTints'):
                    spec['materialTints'] = plan['materialTints']
                (work / 'spec.json').write_text(json.dumps(spec, indent=1),
                                                encoding='utf-8')
                subprocess.run([str(DEFAULT_HSDCLI), '--stage-textures', 'import',
                                str(Path(DEFAULT_DATS) / stage_file_name(code)),
                                str(work / 'spec.json'), str(out_dat)],
                               capture_output=True, text=True, timeout=300)
            if not out_dat.exists():
                raise RuntimeError('variant dat missing (steps empty or import failed)')
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
                z.write(out_dat, stage_file_name(code))

            iso = STORAGE_PATH / 'test-builds' / f'mine_{code}.iso'
            try:
                test_build.build_stage_skin_iso(args.vanilla, code, folder, variant,
                                                str(iso), button='X',
                                                log=lambda m: None)
                res = capture_stage(str(iso), args.slippi,
                                    str(STORAGE_PATH / 'test-runs'),
                                    internal_id=INTERNAL_STAGE_ID[framing_key],
                                    hold='X', framing_key=framing_key,
                                    log=lambda m: None, settle=4.0)
                if not res.get('png'):
                    raise RuntimeError(f"capture failed: {res.get('reason')}")
                shot_path.write_bytes(res['png'])
            finally:
                iso.unlink(missing_ok=True)
            print(f'  vaulted: {zip_path.name} + screenshot', flush=True)
        except Exception as e:
            failures.append(code)
            print(f'  FAILED {code}: {e}', flush=True)
    print('done. failures:', failures or 'none', flush=True)


if __name__ == '__main__':
    main()
