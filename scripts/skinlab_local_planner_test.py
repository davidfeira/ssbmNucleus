"""Can a LOCAL LLM (via Ollama) do the AI Studio planner's job?

Runs the REAL planner prompts (PLAN_PROMPT / STAGE_PLAN_PROMPT from the
backend) against local models and scores the replies with the REAL
validators (_extract_json + _validate / _validate_stage). Also measures
per-call latency and verifies the keep_alive=0 VRAM unload story (the
planner must vacate the GPU before the diffusion model loads).

Usage:
  python scripts/skinlab_local_planner_test.py [--models m1,m2] [--themes N]

Requires the Ollama server running (it is, as a service). Models that are
not pulled yet are skipped with a note (pull with `ollama pull <model>`).
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).parent
BACKEND = HERE.parent / 'backend'
sys.path.insert(0, str(BACKEND))

from blueprints.skin_lab_ai import (PLAN_PROMPT, _color_facts, _extract_json,
                                    _validate)
from blueprints.stage_lab_ai import STAGE_PLAN_PROMPT, _validate_stage

OLLAMA = 'http://127.0.0.1:11434'

CHAR_THEMES = [
    'royal crusader: polished steel plate armor, deep crimson cloth, gold trim',
    'toxic swamp monster: dripping algae fur, sickly green hide',
    'synthwave: neon magenta and cyan, chrome accents, retro grid',
    'desert nomad: sun-bleached linen, turquoise jewelry, sand-worn leather',
]
STAGE_THEMES = [
    'molten core: volcanic basalt, glowing lava cracks, apocalyptic ember sky',
    'frozen ruins: blue ice, snow drifts, aurora night sky',
    'candy land: pastel frosting, sprinkles, cotton-candy clouds',
]


def char_prompt():
    rm = json.loads((BACKEND / 'assets' / 'texture_regions' / 'Fox.json')
                    .read_text(encoding='utf-8'))
    region_summary = '\n'.join(f'- {name}: {len(idxs)} textures'
                               for name, idxs in rm['regions'].items())
    color_facts = _color_facts(rm.get('maskHints'))
    return rm, region_summary, color_facts


def stage_prompt():
    stages_dir = BACKEND / 'assets' / 'texture_regions' / 'stages'
    path = sorted(stages_dir.glob('*.json'))[0]
    rm = json.loads(path.read_text(encoding='utf-8'))
    notes = rm.get('notes') or {}
    region_summary = '\n'.join(
        f"- {name}: {len(idxs)} textures"
        + (f" ({notes[name]})" if name in notes else '')
        for name, idxs in rm['regions'].items())
    return rm, region_summary, path.stem


def vram_used_mb():
    try:
        out = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5).stdout.strip()
        return int(out.splitlines()[0])
    except Exception:
        return -1


def model_available(model):
    try:
        tags = requests.get(f'{OLLAMA}/api/tags', timeout=5).json()
        names = {m['name'] for m in tags.get('models', [])}
        return model in names or f'{model}:latest' in names
    except Exception:
        return False


def call_ollama(model, prompt, keep_alive='2m'):
    """One planner call. format=json forces valid JSON output framing
    (the integration would do the same). Returns (text, seconds)."""
    t0 = time.time()
    r = requests.post(f'{OLLAMA}/api/chat', timeout=600, json={
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'format': 'json',
        'stream': False,
        'think': False,
        'keep_alive': keep_alive,
        'options': {'temperature': 0.7, 'num_ctx': 8192},
    })
    body = r.json()
    if 'error' in body:
        raise RuntimeError(body['error'])
    return body['message']['content'], time.time() - t0


def unload(model):
    """keep_alive=0 with an empty prompt unloads the model immediately."""
    try:
        requests.post(f'{OLLAMA}/api/generate', timeout=60, json={
            'model': model, 'prompt': '', 'keep_alive': 0, 'stream': False})
    except Exception:
        pass


def score_char(reply, rm):
    plan = _extract_json(reply)
    if not plan:
        return {'ok': False, 'why': 'no JSON'}
    steps, err = _validate(plan, set(rm['regions']))
    if err:
        return {'ok': False, 'why': err}
    composites = [s for s in steps if s['op'] == 'composite']
    covered = {s['region'] for s in steps}
    return {'ok': True, 'steps': len(steps), 'composites': len(composites),
            'coverage': f"{len(covered)}/{len(rm['regions'])}",
            'name': (plan.get('skin_name') or '')[:30],
            'sample_prompt': (composites[0]['material_prompt'][:60]
                              if composites else '')}


def score_stage(reply, rm):
    plan = _extract_json(reply)
    if not plan:
        return {'ok': False, 'why': 'no JSON'}
    steps, tints, err = _validate_stage(plan, set(rm['regions']))
    if err:
        return {'ok': False, 'why': err}
    composites = [s for s in steps if s['op'] == 'composite']
    return {'ok': True, 'steps': len(steps) + len(tints),
            'composites': len(composites),
            'coverage': f"{len({s['region'] for s in steps})}/{len(rm['regions'])}",
            'name': (plan.get('skin_name') or '')[:30],
            'sample_prompt': (composites[0]['material_prompt'][:60]
                              if composites else '')}


def review_test(model):
    """Vision REVIEW pass: critique a real in-game stage screenshot against
    a theme. Needs a vision-capable model (text-only models fail here)."""
    import base64
    from blueprints.stage_lab_ai import STAGE_REVIEW_PROMPT

    shot = (HERE.parent / 'storage' / 'das' / 'battlefield'
            / 'art-deco-b_screenshot.png')
    if not shot.exists():
        print('  review: no screenshot available, skipped')
        return None
    rm = json.loads((BACKEND / 'assets' / 'texture_regions' / 'stages'
                     / 'GrNBa.json').read_text(encoding='utf-8'))
    region_summary = '\n'.join(f"- {name}: {len(idxs)} textures"
                               for name, idxs in rm['regions'].items())
    prompt = STAGE_REVIEW_PROMPT.format(
        theme='art deco: brass, marble, geometric gold trim',
        region_summary=region_summary)
    t0 = time.time()
    try:
        r = requests.post(f'{OLLAMA}/api/chat', timeout=600, json={
            'model': model,
            'messages': [{'role': 'user', 'content': prompt,
                          'images': [base64.b64encode(shot.read_bytes())
                                     .decode('ascii')]}],
            'format': 'json', 'stream': False, 'think': False,
            'keep_alive': 0,
            'options': {'temperature': 0.7, 'num_ctx': 8192},
        }).json()
        if 'error' in r:
            raise RuntimeError(r['error'])
        reply = r['message']['content']
    except Exception as e:
        print(f'  review FAIL ({str(e)[:80]})')
        return {'ok': False, 'why': str(e)[:80]}
    secs = round(time.time() - t0, 1)
    review = _extract_json(reply) or {}
    assessment = (review.get('assessment') or '')[:120]
    steps, tints, err = _validate_stage(review, set(rm['regions']))
    n_fixes = len(steps or []) + len(tints or [])
    looked = bool(assessment)
    print(f'  review {secs:>5}s  '
          + ('OK' if looked else 'FAIL')
          + f'  fixes={n_fixes}  assessment="{assessment}"')
    return {'ok': looked, 'secs': secs, 'fixes': n_fixes,
            'assessment': assessment}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--models', default='gemma3:1b,'
                    'huihui_ai/qwen3.5-abliterated:0.8B,qwen3:8b')
    ap.add_argument('--themes', type=int, default=3,
                    help='themes per scenario per model')
    ap.add_argument('--review', action='store_true',
                    help='also test the vision review pass (needs a VLM)')
    args = ap.parse_args()

    char_rm, char_summary, char_colors = char_prompt()
    stage_rm, stage_summary, stage_name = stage_prompt()
    print(f'character map: Fox ({len(char_rm["regions"])} regions) | '
          f'stage map: {stage_name} ({len(stage_rm["regions"])} regions)\n')

    results = {}
    for model in [m.strip() for m in args.models.split(',') if m.strip()]:
        if not model_available(model):
            print(f'== {model}: NOT PULLED (ollama pull {model}) — skipping\n')
            continue
        print(f'== {model}')
        rows = []
        vram_before = vram_used_mb()

        for theme in CHAR_THEMES[:args.themes]:
            prompt = PLAN_PROMPT.format(character='Fox', theme=theme,
                                        region_summary=char_summary,
                                        color_facts=char_colors)
            try:
                reply, secs = call_ollama(model, prompt)
                s = score_char(reply, char_rm)
            except Exception as e:
                s, secs = {'ok': False, 'why': str(e)[:80]}, 0
            s.update(kind='char', theme=theme[:28], secs=round(secs, 1))
            rows.append(s)
            print(f"  char  {s['secs']:>6}s  "
                  + (f"OK steps={s['steps']} comp={s['composites']} "
                     f"cover={s['coverage']}  \"{s['name']}\""
                     if s['ok'] else f"FAIL ({s['why']})")
                  + f"  [{s['theme']}]")

        for theme in STAGE_THEMES[:args.themes]:
            prompt = STAGE_PLAN_PROMPT.format(
                stage_name=stage_rm.get('stage', stage_name), theme=theme,
                region_summary=stage_summary, extra_notes='')
            try:
                reply, secs = call_ollama(model, prompt)
                s = score_stage(reply, stage_rm)
            except Exception as e:
                s, secs = {'ok': False, 'why': str(e)[:80]}, 0
            s.update(kind='stage', theme=theme[:28], secs=round(secs, 1))
            rows.append(s)
            print(f"  stage {s['secs']:>6}s  "
                  + (f"OK steps={s['steps']} comp={s['composites']} "
                     f"cover={s['coverage']}  \"{s['name']}\""
                     if s['ok'] else f"FAIL ({s['why']})")
                  + f"  [{s['theme']}]")

        review = review_test(model) if args.review else None

        vram_loaded = vram_used_mb()
        unload(model)
        time.sleep(3)
        vram_after = vram_used_mb()
        ok = sum(1 for r in rows if r['ok'])
        avg = (sum(r['secs'] for r in rows if r['ok']) / ok) if ok else 0
        print(f'  -> {ok}/{len(rows)} valid plans, avg {avg:.1f}s/plan | '
              f'VRAM idle {vram_before}MB -> loaded {vram_loaded}MB -> '
              f'unloaded {vram_after}MB\n')
        results[model] = {'rows': rows, 'valid': ok, 'total': len(rows),
                          'avgSecs': round(avg, 1), 'review': review,
                          'vram': {'before': vram_before,
                                   'loaded': vram_loaded,
                                   'after': vram_after}}

    out = HERE.parent / 'storage' / 'local_planner_results.json'
    out.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(f'results -> {out}')


if __name__ == '__main__':
    main()
