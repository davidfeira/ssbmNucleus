"""Stage-skin gauntlet: cheap models plan a themed DAS alt, executed offline,
verified with an in-game capture.

Per model: plan (text, cheap) -> apply_plan -> variant dat -> DAS zip ->
test ISO -> capture_stage (calibrated framing) -> shot saved for comparison.
A hand-written plan can join the round via --claude-plan.

Usage:
  python scripts/skinlab_stage_gauntlet.py --code GrNBa \
      --theme "molten core: ..." --vanilla <iso> --slippi <exe> \
      [--models m1,m2] [--claude-plan plan.json] [--out dir]
"""
import argparse
import base64
import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

SCRIPTS = Path(__file__).parent
REPO = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(REPO / 'backend'))

from skinlab_gauntlet import call_model, extract_json, validate_plan  # noqa: E402
from skinlab_stage_lab import (DEFAULT_DATS, DEFAULT_EXPORTS, DEFAULT_HSDCLI,  # noqa: E402
                               REGION_DIR, apply_plan)

DEFAULT_MODELS = ['google/gemini-3-flash-preview', 'openai/gpt-5-mini']

PLAN_PROMPT = """You are designing a Super Smash Bros. Melee STAGE reskin (a
"DAS alternate") for {stage_name} using a texture-compositing API. The theme:

  "{theme}"

The stage's textures are grouped into named regions:
{region_summary}

You can emit three kinds of steps:
1. {{"op": "composite", "region": "<name>", "material_prompt": "<text-to-image
   prompt for a seamless material tile>", "modulate": {{"lo": 0.3-0.5,
   "hi": 1.4-1.9}}}} -- re-surfaces the region with a generated material,
   keeping the original shading.
2. {{"op": "hue-shift", "region": "<name>", "hueShift": -180..180,
   "saturationShift": -100..100}} -- rotates existing colors, keeps patterns.
   Does nothing on gray pixels.
3. {{"op": "tint", "region": "<name>", "hue": 0-360, "saturation": 0-100}} --
   colorizes the region outright (works on grays), keeps lightness.

Rules:
- 3 to 6 steps total. At most 3 composite steps.
- A great stage alt transforms the PLAYFIELD (deck/platforms) and the
  BACKGROUND -- untouched regions look stock.
- Keep gameplay readability: the deck surface should stay visually distinct
  from the background.

Reply with ONLY JSON: {{"skin_name": "<short name>", "steps": [...]}}"""


def region_summary(code):
    rm = json.loads((REGION_DIR / f'{code}.json').read_text(encoding='utf-8'))
    notes = rm.get('notes') or {}
    lines = []
    for name, idxs in rm['regions'].items():
        note = notes.get(name, '')
        lines.append(f'- {name}: {len(idxs)} textures' + (f' ({note})' if note else ''))
    return rm, '\n'.join(lines)


def make_das_zip(code, dat_path, variant_id):
    from test_build import DAS_STAGES
    folder = DAS_STAGES[code][0]
    das_dir = REPO / 'storage' / 'das' / folder
    das_dir.mkdir(parents=True, exist_ok=True)
    zip_path = das_dir / f'{variant_id}.zip'
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(dat_path, f'{code}.dat')
    return zip_path, folder


def capture_variant(code, folder, variant_id, vanilla, slippi, out_png):
    import test_build
    from core.config import STORAGE_PATH
    from ingame.capture import capture_stage
    from ingame.melee_sss import INTERNAL_STAGE_ID
    framing_key = test_build.DAS_STAGES[code][1]
    iso = STORAGE_PATH / 'test-builds' / f'stage_gauntlet_{code}.iso'
    try:
        test_build.build_stage_skin_iso(vanilla, code, folder, variant_id,
                                        str(iso), button='X',
                                        log=lambda m: print('   ', m, flush=True))
        res = capture_stage(str(iso), slippi, str(STORAGE_PATH / 'test-runs'),
                            internal_id=INTERNAL_STAGE_ID[framing_key], hold='X',
                            framing_key=framing_key,
                            log=lambda m: None, settle=4.0)
        if res.get('png'):
            out_png.write_bytes(res['png'])
            return True, 'captured'
        return False, res.get('reason')
    finally:
        iso.unlink(missing_ok=True)


def run_plan(code, plan, name, exports_dir, out_dir, vanilla, slippi, hsdcli):
    import subprocess
    work = out_dir / name
    outputs = apply_plan(code, plan, exports_dir, work / 'pngs')
    spec = {'replacements': [{'index': i, 'png': str(p)} for i, p in outputs.items()]}
    (work / 'spec.json').write_text(json.dumps(spec, indent=1), encoding='utf-8')
    out_dat = work / f'{code}.dat'
    subprocess.run([hsdcli, '--stage-textures', 'import',
                    str(Path(DEFAULT_DATS) / f'{code}.dat'),
                    str(work / 'spec.json'), str(out_dat)],
                   capture_output=True, text=True, timeout=300, check=False)
    if not out_dat.exists():
        return False, 'dat import failed'
    variant_id = f'ai-{name}'
    _zip, folder = make_das_zip(code, out_dat, variant_id)
    shot = out_dir / f'{name}.png'
    ok, reason = capture_variant(code, folder, variant_id, vanilla, slippi, shot)
    print(f'  {name}: {"shot -> " + shot.name if ok else "CAPTURE FAILED: " + str(reason)}',
          flush=True)
    return ok, reason


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--code', required=True)
    ap.add_argument('--theme', required=True)
    ap.add_argument('--vanilla', required=True)
    ap.add_argument('--slippi', required=True)
    ap.add_argument('--models', default=','.join(DEFAULT_MODELS))
    ap.add_argument('--claude-plan', default=None)
    ap.add_argument('--out', default=None)
    args = ap.parse_args()

    exports_dir = DEFAULT_EXPORTS / args.code / 'textures'
    out_dir = Path(args.out) if args.out else DEFAULT_EXPORTS / args.code / 'gauntlet'
    out_dir.mkdir(parents=True, exist_ok=True)
    rm, summary = region_summary(args.code)
    stage_name = rm.get('stage', args.code)
    prompt = PLAN_PROMPT.format(stage_name=stage_name, theme=args.theme,
                                region_summary=summary)
    results = {}

    for model in [m.strip() for m in args.models.split(',') if m.strip()]:
        slug = re.sub(r'[^\w.-]', '_', model)
        print(f'[stage] {model}: planning...', flush=True)
        try:
            reply, usage = call_model(model, prompt)
            plan = extract_json(reply)
            steps, err = validate_plan(plan or {}, set(rm['regions']))
            if err:
                print(f'  INVALID PLAN ({err})', flush=True)
                results[model] = {'valid': False, 'error': err}
                continue
            plan = {'skin_name': plan.get('skin_name'), 'steps': steps}
            (out_dir / f'{slug}_plan.json').write_text(json.dumps(plan, indent=1),
                                                       encoding='utf-8')
            print(f"  plan ok -- {'; '.join(s['op'] + ':' + s['region'] for s in steps)}",
                  flush=True)
            ok, reason = run_plan(args.code, plan, slug, exports_dir, out_dir,
                                  args.vanilla, args.slippi, str(DEFAULT_HSDCLI))
            results[model] = {'valid': True, 'plan': plan, 'captured': ok,
                              'reason': reason, 'usage': usage}
        except Exception as e:
            print(f'  FAILED: {e}', flush=True)
            results[model] = {'valid': False, 'error': str(e)}

    if args.claude_plan:
        plan = json.loads(Path(args.claude_plan).read_text(encoding='utf-8'))
        print('[stage] claude baseline...', flush=True)
        ok, reason = run_plan(args.code, plan, 'claude', exports_dir, out_dir,
                              args.vanilla, args.slippi, str(DEFAULT_HSDCLI))
        results['claude'] = {'valid': True, 'plan': plan, 'captured': ok,
                             'reason': reason}

    (out_dir / 'results.json').write_text(json.dumps(results, indent=1),
                                          encoding='utf-8')
    print('results ->', out_dir / 'results.json', flush=True)


if __name__ == '__main__':
    main()
