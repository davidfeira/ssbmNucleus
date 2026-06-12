"""
skinlab_inspiration_gauntlet.py -- test how each AI-studio planner uses an
INSPIRATION IMAGE, end to end through the REAL /ai-create endpoint (vision
plan call + referenceImage image-to-image materials + review pass).

The theme is deliberately empty (image runs) or the bare server default
(control run), so any monarch-butterfly palette/motif in a plan can ONLY
have come from the image.

Usage:
  python scripts/skinlab_inspiration_gauntlet.py --port <fresh backend port>
      [--models id1,id2,...] [--character Fox]
  Results -> ../gauntlet_out/inspiration/ (sheets, results.json, compare.html)
"""
import argparse
import base64
import html
import json
import re
import threading
import time
from pathlib import Path

import requests
import socketio

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO.parent / 'gauntlet_out' / 'inspiration'
INSPIRATION = OUT_DIR / 'inspiration.png'

# (label, planner model, send the image?)  '' theme = server default
RUNS = [
    ('control-no-image', 'openai/gpt-5-mini', False),
    ('gpt-5-mini', 'openai/gpt-5-mini', True),
    ('gemini-3-flash', 'google/gemini-3-flash-preview', True),
    ('claude-haiku-4.5', 'anthropic/claude-haiku-4.5', True),
    ('gemma3-4b-local', 'ollama:gemma3:4b', True),
    ('qwen3-8b-local', 'ollama:qwen3:8b', True),
]

# evidence the plan came from the image, not the theme text
IMAGE_WORDS = ['butterfly', 'monarch', 'wing', 'orange', 'black', 'amber',
               'vein', 'white spot', 'spotted']


def image_evidence(steps):
    """Which image-derived words appear in the plan's material prompts, and
    which tint/hue-shift hues land in the monarch orange band (20-45)."""
    words = set()
    orange_ops = 0
    for s in steps or []:
        text = (s.get('material_prompt') or '').lower()
        words.update(w for w in IMAGE_WORDS if w in text)
        if s.get('op') == 'tint' and s.get('hue') is not None:
            if 10 <= float(s['hue']) <= 50:
                orange_ops += 1
    return sorted(words), orange_ops


def run_one(base, label, model, with_image, insp_uri, timeout=1200):
    api = f'{base}/api/mex/skin-lab'
    state = {'progress': [], 'done': threading.Event(), 'result': None,
             'error': None}

    sio = socketio.Client()

    @sio.on('ailab_progress')
    def _prog(d):
        msg = d.get('message') or ''
        if not state['progress'] or state['progress'][-1] != msg:
            state['progress'].append(msg)
            print(f'    [{label}] {msg}')

    @sio.on('ailab_complete')
    def _done(d):
        state['result'] = d
        state['done'].set()

    @sio.on('ailab_error')
    def _err(d):
        state['error'] = d.get('error') or 'unknown error'
        state['done'].set()

    sio.connect(base)
    t0 = time.time()
    try:
        body = {'character': 'Fox',
                'theme': '' if with_image
                         else 'a costume inspired by the attached image',
                'plannerModel': model,
                'imageProvider': 'openrouter',
                'imageModel': 'google/gemini-2.5-flash-image',
                'reviewPass': True}
        if with_image:
            body['inspirationImage'] = insp_uri
        r = requests.post(f'{api}/ai-create', json=body, timeout=60).json()
        if not r.get('success'):
            return {'label': label, 'model': model, 'error': r.get('error')}
        if not state['done'].wait(timeout):
            return {'label': label, 'model': model, 'error': 'timed out'}
        elapsed = round(time.time() - t0, 1)
        if state['error']:
            return {'label': label, 'model': model, 'error': state['error'],
                    'elapsed_s': elapsed}
        d = state['result']
        sheet_file = f'{label}_sheet.jpg'
        (OUT_DIR / sheet_file).write_bytes(
            base64.b64decode(d['sheet'].split('base64,', 1)[1]))
        steps = (d.get('planSteps') or []) + (d.get('fixSteps') or [])
        words, orange_ops = image_evidence(steps)
        return {
            'label': label, 'model': model, 'withImage': with_image,
            'elapsed_s': elapsed, 'skinName': d.get('skinName'),
            'planSteps': d.get('planSteps'), 'fixSteps': d.get('fixSteps'),
            'assessment': d.get('assessment'), 'review': d.get('review'),
            'generation': d.get('generation'), 'planning': d.get('planning'),
            'estCostUsd': d.get('estCostUsd'), 'sheet': sheet_file,
            'imageEvidence': {'promptWords': words, 'orangeTints': orange_ops},
        }
    finally:
        try:
            requests.post(f'{api}/close', timeout=30)
        except requests.RequestException:
            pass
        sio.disconnect()


def step_line(s):
    extra = ''
    if s.get('material_prompt'):
        extra = f" — “{s['material_prompt']}”"
    elif s.get('op') == 'tint':
        extra = f" hue={s.get('hue')} sat={s.get('saturation')}"
    elif s.get('op') == 'hue-shift':
        extra = f" Δhue={s.get('hueShift')} Δsat={s.get('saturationShift')}"
    return f"{s['op']}:{s['region']}{extra}"


def make_compare(results):
    rows = []
    for r in results:
        if r.get('error'):
            body = f"<p class='err'>ERROR: {html.escape(r['error'])}</p>"
        else:
            steps = ''.join(f'<li>{html.escape(step_line(s))}</li>'
                            for s in (r.get('planSteps') or []))
            fixes = ''.join(f'<li class="fix">{html.escape(step_line(s))}</li>'
                            for s in (r.get('fixSteps') or []))
            ev = r.get('imageEvidence') or {}
            body = (
                f"<img src='{r['sheet']}'>"
                f"<p><b>{html.escape(r.get('skinName') or '')}</b>"
                f" · {r['elapsed_s']}s · ~${r.get('estCostUsd') or 0:.3f}</p>"
                f"<ul>{steps}{fixes}</ul>"
                f"<p class='ev'>image words: {', '.join(ev.get('promptWords') or []) or '—'}"
                f" · orange tints: {ev.get('orangeTints', 0)}</p>"
                + (f"<p class='asmt'>“{html.escape(r['assessment'])}”</p>"
                   if r.get('assessment') else ''))
        rows.append(f"<div class='card'><h3>{html.escape(r['label'])}"
                    f" <small>{html.escape(r['model'])}</small></h3>{body}</div>")
    page = f"""<!doctype html><meta charset="utf-8"><title>inspiration gauntlet</title>
<style>
 body {{ background:#11141c; color:#e6e8ee; font:14px system-ui; margin:24px }}
 .card {{ background:#1a1f2b; border-radius:10px; padding:14px; margin:14px 0 }}
 .card img {{ max-width:100%; border-radius:6px }}
 h3 small {{ color:#8b93a7; font-weight:normal }}
 .fix {{ color:#ffd479 }} .err {{ color:#f87171 }}
 .ev {{ color:#7ee787 }} .asmt {{ color:#8b93a7; font-style:italic }}
 .ref img {{ width:220px; border-radius:8px }}
</style>
<h2>Inspiration-image planner gauntlet — Fox, monarch wing reference</h2>
<div class='ref'><img src='inspiration.png'>
<p>theme sent: <i>(empty — “a costume inspired by the attached image”)</i></p></div>
{''.join(rows)}"""
    (OUT_DIR / 'compare.html').write_text(page, encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', required=True)
    ap.add_argument('--models', default=None,
                    help='comma list of run labels to include (default: all)')
    args = ap.parse_args()

    base = f'http://127.0.0.1:{args.port}'
    insp_uri = ('data:image/png;base64,'
                + base64.b64encode(INSPIRATION.read_bytes()).decode('ascii'))

    runs = RUNS
    if args.models:
        wanted = {m.strip() for m in args.models.split(',')}
        runs = [r for r in RUNS if r[0] in wanted]

    results = []
    for label, model, with_image in runs:
        print(f'\n=== {label} ({model}, image={with_image}) ===')
        try:
            r = run_one(base, label, model, with_image, insp_uri)
        except Exception as e:
            r = {'label': label, 'model': model, 'error': str(e)[:500]}
        if r.get('error'):
            print(f'  -> ERROR: {r["error"]}')
        else:
            ev = r['imageEvidence']
            print(f"  -> ok in {r['elapsed_s']}s, ~${r.get('estCostUsd') or 0:.3f}"
                  f" | words={ev['promptWords']} orangeTints={ev['orangeTints']}")
        results.append(r)
        (OUT_DIR / 'results.json').write_text(
            json.dumps(results, indent=2), encoding='utf-8')
        make_compare(results)

    print(f'\nresults -> {OUT_DIR}')


if __name__ == '__main__':
    main()
