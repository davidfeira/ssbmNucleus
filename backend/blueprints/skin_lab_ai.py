"""AI Skin Studio orchestration -- the one-call flow behind the viewer UI.

POST /api/mex/skin-lab/ai-create {character, costumeCode, theme,
    plannerModel?, openrouterKey?}
  -> background thread: open session -> plan (OpenRouter text model) ->
     execute steps (self-HTTP against the existing skin-lab endpoints) ->
     render a front/back/CSP review sheet -> emit it as a data URI.
     The session is LEFT OPEN so the UI's Save button can POST /save.

Events: ailab_progress {stage, percentage, message},
        ailab_complete {success, sheet, skinName, steps},
        ailab_error {error}.

GET /api/mex/skin-lab/ai-status -> {enabled, hasKey} (feature gate probe).
"""
import base64
import io
import json
import os
import re
import threading
import time

import requests
from flask import Blueprint, jsonify, request
from PIL import Image, ImageDraw

import logging

logger = logging.getLogger(__name__)

skin_lab_ai_bp = Blueprint('skin_lab_ai', __name__)

# Feature gate: default ON in dev; a packaged release can set
# NUCLEUS_AI_LAB=0 to hide the studio everywhere (the /ai-status probe).
AI_LAB_ENABLED = os.environ.get('NUCLEUS_AI_LAB', '1') != '0'

DEFAULT_PLANNER = 'openai/gpt-5-mini'
OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'

PLAN_PROMPT = """You are designing a Super Smash Bros. Melee costume transformation
for {character} using a texture-compositing API. The theme is:

  "{theme}"

The costume's textures are grouped into named regions:
{region_summary}

The CURRENT costume colors (measured from its pixels):
{color_facts}
A great themed skin usually transforms ALL of it -- anything you don't touch
stays stock and looks out of place.

You can emit three kinds of steps:
1. {{"op": "composite", "region": "<name>", "material_prompt": "<a text-to-image
   prompt for a seamless material/fabric tile>", "modulate": {{"lo": 0.3-0.5,
   "hi": 1.4-1.9}}}}
2. {{"op": "hue-shift", "region": "<name>", "hueShift": -180..180,
   "saturationShift": -100..100}} -- rotates existing colors, keeps patterns.
   Does nothing on white/gray pixels.
3. {{"op": "tint", "region": "<name>", "hue": 0-360, "saturation": 0-100}} --
   colorizes outright (works on grays), keeps lightness.

Rules:
- 3 to 6 steps total. At most 3 composite steps.
- Cover the whole costume: EVERY region listed above should get a step unless
  the theme truly calls for leaving it stock (small detail regions are fine to
  skip or just tint).
- The "eyes" region may be hue-shifted or tinted but NEVER composited.

Reply with ONLY JSON: {{"skin_name": "<short name>", "steps": [...]}}"""

REVIEW_PROMPT = """You previously designed a Melee costume for the theme
"{theme}" and your plan was executed. The attached image is the ACTUAL result
rendered on the 3D model (front, back, and the character-select framing).

Critique it against the theme. Look specifically for: parts that still look
STOCK/untouched (original colors: {color_facts}), regions whose color clashes
with the theme, and anything too subtle to read. Check ALL three views.

If it already reads well, reply {{"assessment": "<one sentence>", "steps": []}}.
Otherwise reply with up to 3 FIX steps using the same ops:
  {{"op": "composite", "region": "<name>", "material_prompt": "...",
    "modulate": {{"lo": .., "hi": ..}}}}
  {{"op": "tint", "region": "<name>", "hue": 0-360, "saturation": 0-100}}
  {{"op": "hue-shift", "region": "<name>", "hueShift": -180..180,
    "saturationShift": -100..100}}

Reply with ONLY JSON: {{"assessment": "<one sentence>", "steps": [...]}}"""

HUE_NAMES = [(15, 'red'), (40, 'orange'), (65, 'yellow'), (95, 'olive'),
             (150, 'green'), (185, 'teal'), (250, 'blue'), (290, 'purple'),
             (330, 'magenta'), (360, 'red')]


def _hue_name(h):
    for limit, name in HUE_NAMES:
        if h <= limit:
            return name
    return 'red'


def _color_facts(hints):
    facts = []
    for region, hint in (hints or {}).items():
        if hint.get('hueMin') is not None and hint.get('hueMax') is not None:
            lo, hi = hint['hueMin'], hint['hueMax']
            mid = (lo + hi) / 2 if lo <= hi else ((lo + hi + 360) / 2) % 360
            facts.append(f'- {region}: {_hue_name(mid)} (hue ~{lo}-{hi})')
        elif hint.get('satMax') is not None:
            facts.append(f'- {region}: white/gray surfaces')
    return '\n'.join(facts) or '- (no color data)'


def _extract_json(text):
    text = re.sub(r'^```(?:json)?|```$', '', (text or '').strip(),
                  flags=re.MULTILINE).strip()
    depth, start = 0, None
    for i, ch in enumerate(text):
        if ch == '{':
            if depth == 0:
                start = i
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0 and start is not None:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    start = None
    return None


def _validate(plan, regions):
    if not isinstance(plan, dict) or not isinstance(plan.get('steps'), list):
        return None, 'the model returned no steps'
    steps, composites = [], 0
    for s in plan['steps'][:6]:
        if not isinstance(s, dict):
            continue
        op = s.get('op')
        region = s.get('region')
        if region not in regions:
            continue
        if op == 'composite':
            if not (s.get('material_prompt') or '').strip():
                continue
            composites += 1
            if composites > 3:
                continue
        elif op == 'tint':
            if s.get('hue') is None:
                continue
        elif op == 'hue-shift':
            if not s.get('hueShift') and not s.get('saturationShift'):
                continue
        else:
            continue
        steps.append(s)
    if not steps:
        return None, 'the model returned no usable steps'
    return steps, None


def _vanilla_nr_code(character):
    """The character's neutral vanilla costume code (PlXxNr), discovered from
    the vanilla assets folder. None if the character has no vanilla assets
    (e.g. custom characters -- those open via skinId instead)."""
    from core.config import VANILLA_ASSETS_DIR
    char_dir = VANILLA_ASSETS_DIR / character
    if not char_dir.exists():
        return None
    for entry in sorted(char_dir.iterdir()):
        stem = entry.name.split('.')[0]
        if stem.startswith('Pl') and stem.endswith('Nr'):
            return stem
    return None


def _call_planner(model, prompt, key, image_jpeg=None):
    """Text call, or vision call when image_jpeg bytes are provided."""
    if image_jpeg is not None:
        content = [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {
                'url': 'data:image/jpeg;base64,'
                       + base64.b64encode(image_jpeg).decode('ascii')}},
        ]
    else:
        content = prompt
    r = requests.post(OPENROUTER_URL, timeout=180, json={
        'model': model,
        'messages': [{'role': 'user', 'content': content}],
        'max_tokens': 2000,
    }, headers={'Authorization': f'Bearer {key}'})
    body = r.json()
    if 'error' in body:
        raise RuntimeError(f"planner failed: {body['error'].get('message', body['error'])}")
    return body['choices'][0]['message']['content']


def _sheet_from_session(base_url):
    """Front/back/CSP review sheet via the live session endpoints."""
    session = requests.get(f'{base_url}/status', timeout=30).json().get('session') or {}
    csp_cam = session.get('camera') or {}
    panels = []
    for label, cam in (
            ('front', {'rotX': 0, 'rotY': 0, 'scale': 0.75, 'x': 0, 'y': 10}),
            ('back', {'rotX': 0, 'rotY': 180, 'scale': 0.75, 'x': 0, 'y': 10}),
            ('CSP view', {k: csp_cam.get(k) for k in ('rotX', 'rotY', 'scale', 'x', 'y')
                          if csp_cam.get(k) is not None})):
        requests.post(f'{base_url}/camera', json=cam, timeout=15)
        fr = requests.get(f'{base_url}/frame?fresh=6', timeout=30)
        img = Image.open(io.BytesIO(fr.content)).convert('RGB')
        w, h = img.size
        img = img.crop((int(w * 0.2), 0, int(w * 0.8), h))
        img = img.resize((420, int(420 * img.height / img.width)))
        ImageDraw.Draw(img).text((8, 6), label, fill=(255, 255, 120))
        panels.append(img)
    sheet = Image.new('RGB', (sum(p.width for p in panels),
                              max(p.height for p in panels)), (0, 0, 0))
    x = 0
    for p in panels:
        sheet.paste(p, (x, 0))
        x += p.width
    buf = io.BytesIO()
    sheet.save(buf, format='JPEG', quality=88)
    return buf.getvalue()


@skin_lab_ai_bp.route('/api/mex/skin-lab/ai-status', methods=['GET'])
def ai_status():
    return jsonify({
        'success': True,
        'enabled': AI_LAB_ENABLED,
        'hasKey': bool(os.environ.get('OPENROUTER_API_KEY')),
    })


@skin_lab_ai_bp.route('/api/mex/skin-lab/ai-create', methods=['POST'])
def ai_create():
    """Run the full AI skin flow for a character costume. Leaves the session
    open on success so the UI can preview further or POST /save."""
    from core.state import get_socketio
    socketio = get_socketio()

    if not AI_LAB_ENABLED:
        return jsonify({'success': False, 'error': 'AI Studio is disabled'}), 403

    data = request.get_json(silent=True) or {}
    character = (data.get('character') or '').strip()
    costume_code = (data.get('costumeCode') or '').strip()
    theme = (data.get('theme') or '').strip()
    model = (data.get('plannerModel') or DEFAULT_PLANNER).strip()
    image_provider = (data.get('imageProvider') or 'openrouter').strip().lower()
    image_model = (data.get('imageModel') or '').strip() or None
    review_pass = data.get('reviewPass', True)   # cheap for characters: default ON
    key = (data.get('openrouterKey') or os.environ.get('OPENROUTER_API_KEY') or '').strip()
    if not character or not theme:
        return jsonify({'success': False, 'error': 'character and theme are required'}), 400
    if not key:
        return jsonify({'success': False,
                        'error': 'No OpenRouter key (set it in Settings)'}), 400

    base_url = request.host_url.rstrip('/') + '/api/mex/skin-lab'

    def emit(stage, percentage, message):
        socketio.emit('ailab_progress', {'stage': stage, 'percentage': percentage,
                                         'message': message})

    def run():
        try:
            emit('opening', 5, f'Opening {character} in the lab…')
            body = {'character': character}
            if costume_code:
                body['costumeCode'] = costume_code
            elif data.get('skinId'):
                body['skinId'] = data['skinId']
            else:
                # default: build on the character's neutral vanilla costume
                nr = _vanilla_nr_code(character)
                if not nr:
                    raise RuntimeError(f'No vanilla costume found for {character}')
                body['costumeCode'] = nr
            r = requests.post(f'{base_url}/open', json=body, timeout=180).json()
            if not r.get('success'):
                raise RuntimeError(r.get('error') or 'could not open the costume')

            emit('planning', 15, 'Reading the costume regions…')
            rm = requests.get(f'{base_url}/regions', timeout=120).json().get('regionMap')
            if not rm:
                raise RuntimeError(f'No texture-region map for {character} yet')
            region_summary = '\n'.join(f'- {name}: {len(idxs)} textures'
                                       for name, idxs in rm['regions'].items())
            prompt = PLAN_PROMPT.format(
                character=character, theme=theme, region_summary=region_summary,
                color_facts=_color_facts(rm.get('liveMaskHints')))

            emit('planning', 25, f'Asking {model.split("/")[-1]} for a plan…')
            reply = _call_planner(model, prompt, key)
            plan = _extract_json(reply)
            steps, err = _validate(plan or {}, set(rm['regions']))
            if err:
                raise RuntimeError(err)
            skin_name = ((plan.get('skin_name') or theme)[:60])

            gen_log = []
            img_label = (image_model or ('nano banana' if image_provider == 'openrouter'
                                         else 'sd-turbo'))
            img_cost = 0.03 if image_provider == 'openrouter' else 0.0

            def run_steps(step_list, lo_pct, hi_pct, tag=''):
                n = len(step_list)
                for i, s in enumerate(step_list):
                    pct = lo_pct + int((hi_pct - lo_pct) * i / max(1, n))
                    label = s['op'] + ' ' + s['region']
                    emit('applying', pct, f'{tag}Step {i + 1}/{n}: {label}…')
                    if s['op'] == 'composite':
                        emit('applying', pct, f'{tag}Step {i + 1}/{n}: {label} — '
                             f'material via {img_label}'
                             + (f' (~{int(img_cost * 100)}¢)' if img_cost
                                else ' (local, free)'))
                        gen = {'prompt': s['material_prompt'],
                               'provider': image_provider}
                        if image_model:
                            gen['model'] = image_model
                        t0 = time.time()
                        rr = requests.post(f'{base_url}/composite', timeout=900, json={
                            'region': s['region'],
                            'material': {'generate': gen},
                            'modulate': s.get('modulate') or {}}).json()
                        gen_log.append({'model': img_label,
                                        'provider': image_provider,
                                        'seconds': round(time.time() - t0, 1),
                                        'estCostUsd': img_cost})
                    elif s['op'] == 'tint':
                        rr = requests.post(f'{base_url}/tint', timeout=120, json={
                            'region': s['region'], 'hue': s['hue'],
                            'saturation': s.get('saturation', 60)}).json()
                    else:
                        rr = requests.post(f'{base_url}/hue-shift', timeout=120, json={
                            'region': s['region'],
                            'hueShift': s.get('hueShift', 0),
                            'saturationShift': s.get('saturationShift', 0)}).json()
                    if not rr.get('success'):
                        raise RuntimeError(f"{label} failed: {rr.get('error')}")

            run_steps(steps, 30, 65)

            # Self-review round: the planner looks at its own render and emits
            # fix steps. Nearly free for characters (sheet renders in seconds).
            assessment = None
            fixes = []
            if review_pass:
                emit('reviewing', 70, 'Rendering for self-review…')
                sheet1 = _sheet_from_session(base_url)
                emit('reviewing', 75, f'{model.split("/")[-1]} is reviewing the result…')
                try:
                    reply = _call_planner(
                        model,
                        REVIEW_PROMPT.format(
                            theme=theme,
                            color_facts=_color_facts(rm.get('liveMaskHints'))),
                        key, image_jpeg=sheet1)
                    review = _extract_json(reply) or {}
                    assessment = (review.get('assessment') or '')[:200] or None
                    fixes, _err = _validate(review, set(rm['regions']))
                    fixes = fixes or []
                except Exception as e:
                    logger.warning(f'[ai-studio] review pass skipped: {e}')
                if fixes:
                    run_steps(fixes, 78, 88, tag='Fix ')

            emit('rendering', 90, 'Rendering the preview…')
            sheet = _sheet_from_session(base_url)
            socketio.emit('ailab_complete', {
                'success': True,
                'sheet': 'data:image/jpeg;base64,' + base64.b64encode(sheet).decode('ascii'),
                'skinName': skin_name,
                'steps': steps + fixes,
                'assessment': assessment,
                'generation': gen_log,
                'estCostUsd': round(sum(g['estCostUsd'] for g in gen_log), 3),
            })
        except Exception as e:
            logger.error(f'[ai-studio] failed: {e}', exc_info=True)
            try:
                requests.post(f'{base_url}/close', timeout=30)
            except Exception:
                pass
            socketio.emit('ailab_error', {'success': False, 'error': str(e)})

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'started': True})
