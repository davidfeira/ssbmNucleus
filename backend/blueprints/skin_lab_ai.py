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

# Local planner LLMs run through Ollama: planner model ids prefixed
# 'ollama:' (e.g. 'ollama:qwen3:8b') need no API key — combined with local
# image models the studios are fully offline. The server is resolved by
# aiengine.ollama_runtime: the user's own install first, else the BUNDLED
# portable Ollama (spawned on demand) — see that module.


def is_local_planner(model):
    return (model or '').startswith('ollama:')


def _call_ollama_planner(model, prompt, image_jpeg=None):
    """Planner call against a local Ollama model. format=json forces valid
    JSON framing; keep_alive=0 unloads the LLM IMMEDIATELY after the reply so
    the diffusion model gets the GPU to itself (16GB can't hold both)."""
    from aiengine import ollama_runtime
    base = ollama_runtime.effective_url()
    if not base:
        raise RuntimeError('no local Ollama available — install it in '
                           'Settings → AI Studio, or pick an API planner')
    name = model.split(':', 1)[1]
    message = {'role': 'user', 'content': prompt}
    if image_jpeg is not None:
        message['images'] = [base64.b64encode(image_jpeg).decode('ascii')]
    r = requests.post(f'{base}/api/chat', timeout=600, json={
        'model': name,
        'messages': [message],
        'format': 'json',
        'stream': False,
        'think': False,
        'keep_alive': 0,
        'options': {'temperature': 0.7, 'num_ctx': 8192},
    })
    body = r.json()
    if 'error' in body:
        raise RuntimeError(f"local planner failed: {body['error']} "
                           f"(is '{name}' pulled in Ollama?)")
    return body['message']['content']


def _ollama_model_loaded(model):
    """True when the local planner's weights are already resident in Ollama
    (GET /api/ps). keep_alive=0 unloads after every call, so this is usually
    False — and the reload takes long enough that the UI should say so."""
    from aiengine import ollama_runtime
    base = ollama_runtime.effective_url()
    if not base:
        return False
    try:
        ps = requests.get(f'{base}/api/ps', timeout=3).json()
        name = model.split(':', 1)[1]
        return any(m.get('name') == name or m.get('model') == name
                   for m in ps.get('models') or [])
    except Exception:
        return False


def planner_call_message(model, doing):
    """Progress message for a planner call. A local model that isn't resident
    yet spends most of the call loading into memory — say that instead of
    pretending the model is already thinking."""
    if is_local_planner(model) and not _ollama_model_loaded(model):
        return f'Loading {model.split(":", 1)[1]} planner into memory…'
    return f'Asking {model.split("/")[-1]} {doing}…'


def call_with_pulse(emit, stage, percentage, message, fn, interval=3):
    """Run fn() while re-emitting `message (Ns)` every few seconds so a long
    silent call (model load, slow API) never reads as a hang."""
    done = threading.Event()
    t0 = time.time()

    def pulse():
        while not done.wait(interval):
            emit(stage, percentage, f'{message} ({int(time.time() - t0)}s)')

    threading.Thread(target=pulse, daemon=True).start()
    try:
        return fn()
    finally:
        done.set()


def list_local_planners():
    """Installed Ollama models as planner options, [] when Ollama is absent."""
    from aiengine import ollama_runtime
    base = ollama_runtime.effective_url()
    if not base:
        return []
    try:
        tags = requests.get(f'{base}/api/tags', timeout=3).json()
        return sorted(m['name'] for m in tags.get('models', []))
    except Exception:
        return []

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
  the theme truly calls for leaving it stock.
- Face features (face_detail: cheeks/mouth/nose) are small but read STRONGLY
  against a recolored body -- give them a tint or hue-shift that fits the
  theme. Only leave them stock when the theme keeps the character's natural
  face colors.
- The "eyes" region may be hue-shifted or tinted but NEVER composited.

Reply with ONLY JSON: {{"skin_name": "<short name>", "steps": [...]}}"""

REVIEW_PROMPT = """You previously designed a Melee costume for the theme
"{theme}" and your plan was executed. The attached image is the ACTUAL result
rendered on the 3D model (front, back, and the character-select framing).

Critique it against the theme. Look specifically for: parts that still look
STOCK/untouched (original colors: {color_facts}) -- INCLUDING small face
features like cheeks and mouth -- regions whose color clashes with the theme,
and anything too subtle to read. Check ALL three views.

Valid regions (use these EXACT names): {region_names}

Decide a verdict:
- "good" -- the result reads well as-is. steps MUST be [].
- "needs_fixes" -- you see problems. You MUST then include a fix step for
  EVERY problem you name in the assessment (up to 3 steps). Never name a
  problem without a corresponding fix step.

Fix steps use the same ops:
  {{"op": "composite", "region": "<name>", "material_prompt": "...",
    "modulate": {{"lo": .., "hi": ..}}}}
  {{"op": "tint", "region": "<name>", "hue": 0-360, "saturation": 0-100}}
  {{"op": "hue-shift", "region": "<name>", "hueShift": -180..180,
    "saturationShift": -100..100}}
The "eyes" region may be hue-shifted or tinted but NEVER composited.

Reply with ONLY JSON:
{{"verdict": "good" | "needs_fixes", "assessment": "<one sentence>",
  "steps": [...]}}"""

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
        kind = hint.get('kind')
        if kind == 'dark':
            facts.append(f'- {region}: black / very dark')
        elif kind == 'graywhite':
            facts.append(f'- {region}: white/gray surfaces')
        elif hint.get('hueMin') is not None and hint.get('hueMax') is not None:
            lo, hi = hint['hueMin'], hint['hueMax']
            mid = (lo + hi) / 2 if lo <= hi else ((lo + hi + 360) / 2) % 360
            facts.append(f'- {region}: {_hue_name(mid)} (hue ~{lo}-{hi})')
        elif hint.get('satMax') is not None:
            facts.append(f'- {region}: white/gray surfaces')
    return '\n'.join(facts) or '- (no color data)'


def _facts_source(region_map):
    """Best color readout for the prompt: measured colorFacts (covers every
    region, pads excluded), falling back to mask hints for older payloads.
    Regions the colorFacts pass missed still get their mask-hint band."""
    merged = dict(region_map.get('liveMaskHints') or {})
    merged.update(region_map.get('colorFacts') or {})
    return merged


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


def _clean_step(s, regions, composites):
    """One step -> (step, None) when usable, (None, reason) when not.
    `composites` = composite steps already accepted."""
    if not isinstance(s, dict):
        return None, 'a step was not an object'
    op = s.get('op')
    region = s.get('region')
    if region not in regions:
        return None, f'unknown region "{region}"'
    if op == 'composite':
        if not (s.get('material_prompt') or '').strip():
            return None, f'composite on {region} had no material prompt'
        if composites >= 3:
            return None, f'composite on {region} was over the 3-composite limit'
    elif op == 'tint':
        if s.get('hue') is None:
            return None, f'tint on {region} had no hue'
    elif op == 'hue-shift':
        if not s.get('hueShift') and not s.get('saturationShift'):
            return None, f'hue-shift on {region} had no shift values'
    else:
        return None, f'unknown op "{op}"'
    return s, None


def _validate(plan, regions):
    if not isinstance(plan, dict) or not isinstance(plan.get('steps'), list):
        return None, 'the model returned no steps'
    steps, composites = [], 0
    for s in plan['steps'][:6]:
        step, _reason = _clean_step(s, regions, composites)
        if step is None:
            continue
        if step['op'] == 'composite':
            composites += 1
        steps.append(step)
    if not steps:
        return None, 'the model returned no usable steps'
    return steps, None


def _validate_review(review, regions):
    """Review-pass fixes: keep what's usable and report WHY the rest was
    dropped -- silently discarding them turns the review into commentary."""
    raw = review.get('steps') if isinstance(review, dict) else None
    if not isinstance(raw, list):
        return [], ['the review reply had no steps list']
    fixes, dropped, composites = [], [], 0
    for s in raw[:3]:
        step, reason = _clean_step(s, regions, composites)
        if step is None:
            dropped.append(reason)
            continue
        if step['op'] == 'composite':
            composites += 1
        fixes.append(step)
    if len(raw) > 3:
        dropped.append(f'{len(raw) - 3} step(s) over the 3-fix limit')
    return fixes, dropped


def _trim_assessment(text, limit=280):
    """Cap the assessment at a WORD boundary (the old hard [:200] slice cut
    sentences mid-word in the UI)."""
    text = (text or '').strip()
    if not text:
        return None
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(' ', 1)[0].rstrip(',;:. ') + '…'


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


def _record_planner_run(provider, model, t0, success, cost):
    """Planner calls go in the telemetry ledger too — they feed the stats
    table and the measured s/plan hints in the planner picker."""
    try:
        from aiengine import telemetry
        telemetry.record_run(provider, model, 'planner', 'planner',
                             time.time() - t0, success, est_cost_usd=cost)
    except Exception:
        logger.warning('planner telemetry failed', exc_info=True)


def _call_planner(model, prompt, key, image_jpeg=None, cost_log=None):
    """Text call, or vision call when image_jpeg bytes are provided.
    'ollama:<model>' routes to the local Ollama server (no key needed).
    When cost_log (a list) is given, the call's ACTUAL cost is appended as
    {'model', 'costUsd'} — OpenRouter reports it via usage accounting;
    local calls log 0 so the breakdown shows them as free."""
    t0 = time.time()
    if is_local_planner(model):
        try:
            reply = _call_ollama_planner(model, prompt, image_jpeg=image_jpeg)
        except Exception:
            _record_planner_run('ollama', model, t0, False, 0.0)
            raise
        _record_planner_run('ollama', model, t0, True, 0.0)
        if cost_log is not None:
            cost_log.append({'model': model, 'costUsd': 0.0})
        return reply
    if image_jpeg is not None:
        content = [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {
                'url': 'data:image/jpeg;base64,'
                       + base64.b64encode(image_jpeg).decode('ascii')}},
        ]
    else:
        content = prompt
    try:
        r = requests.post(OPENROUTER_URL, timeout=180, json={
            'model': model,
            'messages': [{'role': 'user', 'content': content}],
            'max_tokens': 2000,
            'usage': {'include': True},
        }, headers={'Authorization': f'Bearer {key}'})
        body = r.json()
        if 'error' in body:
            raise RuntimeError(
                f"planner failed: {body['error'].get('message', body['error'])}")
    except Exception:
        _record_planner_run('openrouter', model, t0, False, 0.0)
        raise
    cost = float((body.get('usage') or {}).get('cost') or 0)
    _record_planner_run('openrouter', model, t0, True, cost)
    if cost_log is not None:
        cost_log.append({'model': model, 'costUsd': cost})
    return body['choices'][0]['message']['content']


def _sheet_from_session(base_url):
    """Front/back/CSP review sheet via the live session endpoints."""
    session = requests.get(f'{base_url}/status', timeout=30).json().get('session') or {}
    csp_cam = session.get('camera') or {}
    # The GL texture rebuild after edits is lazy (next render), and a frame
    # grab silently falls back to the latest frame on timeout — so the very
    # first panel could capture a pre-update frame. Burn a settle grab first.
    requests.get(f'{base_url}/frame?fresh=8', timeout=30)
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
    from aiengine import keystore
    from blueprints.ai_engine import _local_model_ready
    return jsonify({
        'success': True,
        'enabled': AI_LAB_ENABLED,
        'hasKey': bool(keystore.get_openrouter_key()),
        # setup gate: studios unlock with a key OR a ready local model
        'localModelReady': _local_model_ready(),
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
    # empty provider/model = 'Auto': the tier resolver picks per task
    image_provider = (data.get('imageProvider') or '').strip().lower()
    image_model = (data.get('imageModel') or '').strip() or None
    review_pass = data.get('reviewPass', True)   # cheap for characters: default ON
    from aiengine import keystore
    key = (data.get('openrouterKey') or keystore.get_openrouter_key() or '').strip()
    if not character or not theme:
        return jsonify({'success': False, 'error': 'character and theme are required'}), 400
    # a local (ollama:) planner needs no key; image models resolve to local
    # ones without a key too -> fully offline runs are allowed
    if not key and not is_local_planner(model):
        return jsonify({'success': False,
                        'error': 'No OpenRouter key (set it in Settings, or '
                                 'pick a local planner)'}), 400

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
                color_facts=_color_facts(_facts_source(rm)))

            plan_msg = planner_call_message(model, 'for a plan')
            emit('planning', 25, plan_msg)
            planner_log = []
            reply = call_with_pulse(
                emit, 'planning', 25, plan_msg,
                lambda: _call_planner(model, prompt, key, cost_log=planner_log))
            plan = _extract_json(reply)
            steps, err = _validate(plan or {}, set(rm['regions']))
            if err:
                raise RuntimeError(err)
            skin_name = ((plan.get('skin_name') or theme)[:60])

            gen_log = []

            def run_steps(step_list, lo_pct, hi_pct, tag=''):
                n = len(step_list)
                for i, s in enumerate(step_list):
                    pct = lo_pct + int((hi_pct - lo_pct) * i / max(1, n))
                    label = s['op'] + ' ' + s['region']
                    emit('applying', pct, f'{tag}Step {i + 1}/{n}: {label}…')
                    if s['op'] == 'composite':
                        # costume materials are 'standard' tier tile swatches
                        gen = {'prompt': s['material_prompt'],
                               'kind': 'ailab', 'tier': 'standard',
                               # forward local-engine worker progress (model
                               # load, denoise steps) to the studio's bar
                               'progressEvent': 'ailab_progress',
                               'openrouterKey': key}
                        if image_model:
                            gen['model'] = image_model
                        elif image_provider:
                            gen['provider'] = image_provider
                        t0 = time.time()
                        rr = requests.post(f'{base_url}/composite', timeout=900, json={
                            'region': s['region'],
                            'material': {'generate': gen},
                            'modulate': s.get('modulate') or {}}).json()
                        info = rr.get('generated') or {}
                        img_label = info.get('label') or info.get('model') \
                            or image_model or 'image model'
                        emit('applying', pct, f'{tag}Step {i + 1}/{n}: {label} — '
                             f'material via {img_label}')
                        gen_log.append({'model': info.get('model') or img_label,
                                        'provider': info.get('provider')
                                        or image_provider,
                                        'tier': info.get('tier'),
                                        'escalated': bool(info.get('escalated')),
                                        'cached': bool(info.get('cached')),
                                        'seconds': round(time.time() - t0, 1),
                                        'estCostUsd': info.get('estCostUsd') or 0.0})
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
            # fix steps that are EXECUTED before the final render. Nearly free
            # for characters (sheet renders in seconds).
            assessment = None
            fixes = []
            review_info = {'ran': bool(review_pass)}
            if review_pass:
                emit('reviewing', 70, 'Rendering for self-review…')
                sheet1 = _sheet_from_session(base_url)
                review_msg = planner_call_message(model, 'to review the result')
                emit('reviewing', 75, review_msg)
                try:
                    reply = call_with_pulse(
                        emit, 'reviewing', 75, review_msg,
                        lambda: _call_planner(
                            model,
                            REVIEW_PROMPT.format(
                                theme=theme,
                                region_names=', '.join(rm['regions']),
                                color_facts=_color_facts(_facts_source(rm))),
                            key, image_jpeg=sheet1, cost_log=planner_log))
                    review = _extract_json(reply) or {}
                    assessment = _trim_assessment(review.get('assessment'))
                    fixes, dropped = _validate_review(review, set(rm['regions']))
                    verdict = (review.get('verdict') or '').strip().lower()
                    if verdict not in ('good', 'needs_fixes'):
                        # older/looser models: infer from whether fixes came back
                        verdict = 'needs_fixes' if (fixes or dropped) else 'good'
                    review_info.update(verdict=verdict,
                                       fixesApplied=len(fixes),
                                       fixesDropped=dropped)
                    if dropped:
                        logger.warning(f'[ai-studio] review fixes dropped: {dropped}')
                        emit('reviewing', 77,
                             f'Review proposed {len(fixes) + len(dropped)} fixes; '
                             f'{len(dropped)} unusable (dropped)')
                    if verdict == 'needs_fixes' and not fixes:
                        logger.warning('[ai-studio] review flagged issues but '
                                       'produced no usable fix steps')
                except Exception as e:
                    logger.warning(f'[ai-studio] review pass skipped: {e}')
                    review_info['error'] = str(e)
                if fixes:
                    run_steps(fixes, 78, 88, tag='Fix ')

            emit('rendering', 90, 'Rendering the preview…')
            sheet = _sheet_from_session(base_url)
            socketio.emit('ailab_complete', {
                'success': True,
                'sheet': 'data:image/jpeg;base64,' + base64.b64encode(sheet).decode('ascii'),
                'skinName': skin_name,
                'steps': steps + fixes,      # back-compat: full executed list
                'planSteps': steps,
                'fixSteps': fixes,
                'review': review_info,
                'assessment': assessment,
                'generation': gen_log,
                'planning': planner_log,
                'estCostUsd': round(sum(g['estCostUsd'] for g in gen_log)
                                    + sum(p['costUsd'] for p in planner_log), 4),
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
