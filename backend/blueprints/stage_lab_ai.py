"""AI Stage Studio -- themed DAS-alt generation behind the viewer UI.

POST /api/mex/stage-lab/ai-create {stageCode, theme, plannerModel?,
    openrouterKey?, vanillaIsoPath, slippiDolphinPath}
  -> background thread: plan (OpenRouter text model over the stage's region
     map) -> offline texture ops -> variant dat -> one-skin test ISO ->
     in-game capture (calibrated framing) -> emit the screenshot. The built
     variant is held PENDING until /save or /discard.

POST /api/mex/stage-lab/save {name}  -> writes <slug>.zip + screenshot into
     storage/das/<folder>/ (the DAS vault layout).
POST /api/mex/stage-lab/discard
GET  /api/mex/stage-lab/ai-status    -> {enabled, hasKey, stages: [codes]}

Events: stagelab_progress / stagelab_complete / stagelab_error.
"""
import base64
import json
import logging
import os
import re
import shutil
import tempfile
import threading
import time
import zipfile
from pathlib import Path

from flask import Blueprint, jsonify, request

from blueprints.skin_lab_ai import (AI_LAB_ENABLED, DEFAULT_PLANNER,
                                    _call_planner, _extract_json,
                                    is_local_planner)
from core.config import STORAGE_PATH

logger = logging.getLogger(__name__)

stage_lab_ai_bp = Blueprint('stage_lab_ai', __name__)

_pending = {}          # {'dat': Path, 'png': bytes, 'code': str, 'name': str}
_pending_lock = threading.Lock()

STAGE_PLAN_PROMPT = """You are designing a Super Smash Bros. Melee STAGE reskin (a
"DAS alternate") for {stage_name} using a texture-compositing API. The theme:

  "{theme}"

The stage's textures are grouped into named regions:
{region_summary}

You can emit four kinds of steps:
1. {{"op": "composite", "region": "<name>", "material_prompt": "<text-to-image
   prompt for a seamless material tile>", "modulate": {{"lo": 0.3-0.5,
   "hi": 1.4-1.9}}}} -- re-surfaces the region, keeping original shading.
2. {{"op": "hue-shift", "region": "<name>", "hueShift": -180..180,
   "saturationShift": -100..100}} -- rotates existing colors, keeps patterns.
3. {{"op": "tint", "region": "<name>", "hue": 0-360, "saturation": 0-100}} --
   colorizes outright (works on grays), keeps lightness.
4. {{"op": "material-tint", "hueShift": -180..180}} -- rotates ALL of the
   stage's non-texture colors: material colors (glow rims, light accents),
   animated material colors, TEV constants, and vertex colors (e.g. Pokemon
   Stadium's green deck light strips). At most one of these; powerful,
   affects the whole stage's accent palette.

Rules:
- 3 to 6 steps total. At most 3 composite steps.
- A great stage alt transforms the PLAYFIELD and the BACKGROUND -- untouched
  regions look stock.
- Keep gameplay readability: surfaces players stand on must stay visually
  distinct from the background.
{extra_notes}
Reply with ONLY JSON: {{"skin_name": "<short name>", "steps": [...]}}"""


STAGE_REVIEW_PROMPT = """You previously designed a Melee STAGE reskin for the
theme "{theme}" and your plan was executed. The attached image is the ACTUAL
in-game screenshot of the result.

Critique it against the theme. Look for: regions that still look STOCK,
surfaces whose color clashes with the theme, muddy/crusty textures, and
readability problems (the playfield must stay distinct from the background).

Regions you can target:
{region_summary}

If it already reads well, reply {{"assessment": "<one sentence>", "steps": []}}.
Otherwise reply with up to 3 FIX steps using the same ops (composite /
tint / hue-shift / material-tint) as before.

Reply with ONLY JSON: {{"assessment": "<one sentence>", "steps": [...]}}"""


def _validate_stage(plan, regions):
    if not isinstance(plan, dict) or not isinstance(plan.get('steps'), list):
        return None, None, 'the model returned no steps'
    steps, tints, composites = [], [], 0
    for s in plan['steps'][:6]:
        if not isinstance(s, dict):
            continue
        op = s.get('op')
        if op == 'material-tint':
            if s.get('hueShift') and len(tints) < 1:
                tints.append({'hueShift': float(s['hueShift'])})
            continue
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
    if not steps and not tints:
        return None, None, 'the model returned no usable steps'
    return steps, tints, None


@stage_lab_ai_bp.route('/api/mex/stage-lab/ai-status', methods=['GET'])
def stage_ai_status():
    from skinlab.stage_ops import STAGE_REGIONS_DIR
    stages = sorted(p.stem for p in STAGE_REGIONS_DIR.glob('*.json')) \
        if STAGE_REGIONS_DIR.exists() else []
    from aiengine import keystore
    from blueprints.ai_engine import _local_model_ready
    return jsonify({'success': True, 'enabled': AI_LAB_ENABLED,
                    'hasKey': bool(keystore.get_openrouter_key()),
                    'localModelReady': _local_model_ready(),
                    'stages': stages})


@stage_lab_ai_bp.route('/api/mex/stage-lab/ai-create', methods=['POST'])
def stage_ai_create():
    from core.state import get_socketio
    socketio = get_socketio()

    if not AI_LAB_ENABLED:
        return jsonify({'success': False, 'error': 'AI Studio is disabled'}), 403

    data = request.get_json(silent=True) or {}
    code = (data.get('stageCode') or '').strip()
    theme = (data.get('theme') or '').strip()
    model = (data.get('plannerModel') or DEFAULT_PLANNER).strip()
    # empty provider/model = 'Auto': the tier resolver picks per task
    image_provider = (data.get('imageProvider') or '').strip().lower()
    image_model = (data.get('imageModel') or '').strip() or None
    review_pass = bool(data.get('reviewPass'))   # opt-in: costs another ISO + boot
    from aiengine import keystore
    key = (data.get('openrouterKey') or keystore.get_openrouter_key() or '').strip()
    vanilla = (data.get('vanillaIsoPath') or '').strip()
    slippi = (data.get('slippiDolphinPath') or '').strip()
    if not code or not theme:
        return jsonify({'success': False, 'error': 'stageCode and theme are required'}), 400
    # a local (ollama:) planner needs no key (fully-local runs allowed)
    if not key and not is_local_planner(model):
        return jsonify({'success': False,
                        'error': 'No OpenRouter key (set it in Settings, or '
                                 'pick a local planner)'}), 400
    if not vanilla or not os.path.exists(vanilla):
        return jsonify({'success': False,
                        'error': 'Vanilla ISO path missing (set it in Settings)'}), 400
    if not slippi:
        return jsonify({'success': False,
                        'error': 'Slippi Dolphin path missing (set it in Settings)'}), 400

    from skinlab.stage_ops import (StageOpsError, apply_stage_plan,
                                   stage_file_name, stage_region_map)

    rm = stage_region_map(code)
    if rm is None:
        return jsonify({'success': False,
                        'error': f'No texture-region map for stage {code} yet'}), 404

    def emit(stage, percentage, message):
        socketio.emit('stagelab_progress', {'stage': stage, 'percentage': percentage,
                                            'message': message})

    def run():
        import test_build
        from blueprints.skin_lab import _generate_material
        from ingame.capture import capture_stage
        from ingame.melee_sss import INTERNAL_STAGE_ID

        work = Path(tempfile.mkdtemp(prefix='stagelab_'))
        try:
            emit('planning', 10, f'Asking {model.split("/")[-1]} for a plan…')
            notes = rm.get('notes') or {}
            region_summary = '\n'.join(
                f"- {name}: {len(idxs)} textures"
                + (f" ({notes[name]})" if name in notes else '')
                for name, idxs in rm['regions'].items())
            extra = notes.get('limitations')
            prompt = STAGE_PLAN_PROMPT.format(
                stage_name=rm.get('stage', code), theme=theme,
                region_summary=region_summary,
                extra_notes=(f'- NOTE: {extra}\n' if extra else ''))
            try:
                reply = _call_planner(model, prompt, key)
            except RuntimeError as e:
                raise StageOpsError(str(e))
            plan = _extract_json(reply)
            steps, tints, err = _validate_stage(plan or {}, set(rm['regions']))
            if err:
                raise StageOpsError(err)
            skin_name = ((plan.get('skin_name') or theme)[:60])

            n = max(1, len(steps))

            def on_step(i, label):
                emit('applying', 20 + int(35 * i / n), f'Step {i + 1}/{n}: {label}…')

            gen_log = []

            def gen(prompt_text, quality=False):
                # backdrops are 'strong' tier (coherent scene work); the
                # resolver picks the model — escalating past tile-only locals
                params = {'prompt': prompt_text, 'kind': 'stage',
                          'tier': 'strong' if quality else 'standard',
                          'openrouterKey': key}
                if quality:
                    params['style'] = 'scene'
                if image_model:
                    params['model'] = image_model
                elif image_provider:
                    params['provider'] = image_provider
                emit('applying', None, 'Generating material…')
                t0 = time.time()
                path, info = _generate_material(params)
                info = info or {}
                cached = bool(info.get('cached'))
                label = info.get('label') or info.get('model') or 'image model'
                escalated = bool(info.get('escalated'))
                emit('applying', None, f'Material via {label}'
                     + (' — escalated for scene quality' if escalated else ''))
                gen_log.append({'model': info.get('model') or label,
                                'provider': info.get('provider') or image_provider,
                                'tier': info.get('tier'),
                                'escalated': escalated,
                                'cached': cached,
                                'seconds': round(time.time() - t0, 1),
                                'estCostUsd': 0.0 if cached
                                else (info.get('estCostUsd') or 0.0)})
                return path

            out_dat = apply_stage_plan(code, steps, tints, work, gen, on_step=on_step)

            folder, framing_key = test_build.DAS_STAGES[code]

            def build_and_capture(dat_path, lo_pct):
                emit('building', lo_pct, 'Building the test ISO…')
                das_dir = STORAGE_PATH / 'das' / folder
                das_dir.mkdir(parents=True, exist_ok=True)
                tmp_zip = das_dir / '_ai-pending.zip'
                with zipfile.ZipFile(tmp_zip, 'w', zipfile.ZIP_DEFLATED) as z:
                    z.write(dat_path, stage_file_name(code))
                iso = STORAGE_PATH / 'test-builds' / f'stagelab_{code}.iso'
                try:
                    test_build.build_stage_skin_iso(vanilla, code, folder,
                                                    '_ai-pending', str(iso),
                                                    button='X', log=lambda m: None)
                    emit('capturing', lo_pct + 15, 'Capturing the in-game screenshot…')
                    return capture_stage(str(iso), slippi,
                                         str(STORAGE_PATH / 'test-runs'),
                                         internal_id=INTERNAL_STAGE_ID[framing_key],
                                         hold='X', framing_key=framing_key,
                                         log=lambda m: None, settle=4.0)
                finally:
                    iso.unlink(missing_ok=True)
                    tmp_zip.unlink(missing_ok=True)

            res = build_and_capture(out_dat, 55)
            if not res.get('png'):
                raise StageOpsError(f"capture failed: {res.get('reason')}")

            # Optional self-review round: the planner critiques the actual
            # in-game screenshot, then the FULL plan + fixes re-applies and a
            # second ISO/capture verifies (costs another ~2-3 minutes).
            assessment = None
            fixes, fix_tints = [], []
            if review_pass:
                emit('reviewing', 75, f'{model.split("/")[-1]} is reviewing the screenshot…')
                try:
                    from blueprints.skin_lab_ai import _call_planner
                    reply = _call_planner(
                        model,
                        STAGE_REVIEW_PROMPT.format(theme=theme,
                                                   region_summary=region_summary),
                        key, image_jpeg=res['png'])
                    review = _extract_json(reply) or {}
                    assessment = (review.get('assessment') or '')[:200] or None
                    fixes, fix_tints, _err = _validate_stage(review, set(rm['regions']))
                    fixes, fix_tints = fixes or [], fix_tints or []
                except Exception as e:
                    logger.warning(f'[stage-studio] review pass skipped: {e}')
                if fixes or fix_tints:
                    emit('applying', 80, f'Applying {len(fixes) + len(fix_tints)} fix step(s)…')
                    work2 = work / 'review'
                    out_dat = apply_stage_plan(code, steps + fixes,
                                               tints + fix_tints, work2, gen)
                    res = build_and_capture(out_dat, 85)
                    if not res.get('png'):
                        raise StageOpsError(f"re-capture failed: {res.get('reason')}")
                    steps = steps + fixes
                    tints = tints + fix_tints

            keep_dat = STORAGE_PATH / 'skinlab_stages' / f'_pending_{stage_file_name(code)}'
            shutil.copy2(out_dat, keep_dat)
            with _pending_lock:
                _pending.clear()
                _pending.update({'dat': keep_dat, 'png': res['png'],
                                 'code': code, 'folder': folder,
                                 'name': skin_name})
            socketio.emit('stagelab_complete', {
                'success': True,
                'screenshot': 'data:image/png;base64,'
                              + base64.b64encode(res['png']).decode('ascii'),
                'skinName': skin_name,
                'steps': steps + ([{'op': 'material-tint', **t} for t in tints]),
                'assessment': assessment,
                'generation': gen_log,
                'estCostUsd': round(sum(g['estCostUsd'] for g in gen_log), 3),
            })
        except Exception as e:
            logger.error(f'[stage-studio] failed: {e}', exc_info=True)
            socketio.emit('stagelab_error', {'success': False, 'error': str(e)})
        finally:
            shutil.rmtree(work, ignore_errors=True)

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'started': True})


@stage_lab_ai_bp.route('/api/mex/stage-lab/save', methods=['POST'])
def stage_ai_save():
    from skinlab.stage_ops import stage_file_name
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    with _pending_lock:
        if not _pending:
            return jsonify({'success': False, 'error': 'nothing pending to save'}), 400
        p = dict(_pending)
        _pending.clear()
    name = name or p['name']
    slug = re.sub(r'[^\w-]+', '-', name.lower()).strip('-') or 'ai-stage'
    das_dir = STORAGE_PATH / 'das' / p['folder']
    das_dir.mkdir(parents=True, exist_ok=True)
    base = slug
    i = 1
    while (das_dir / f'{slug}.zip').exists():
        i += 1
        slug = f'{base}-{i}'
    with zipfile.ZipFile(das_dir / f'{slug}.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(p['dat'], stage_file_name(p['code']))
    (das_dir / f'{slug}_screenshot.png').write_bytes(p['png'])
    Path(p['dat']).unlink(missing_ok=True)
    return jsonify({'success': True, 'variantId': slug, 'folder': p['folder']})


@stage_lab_ai_bp.route('/api/mex/stage-lab/discard', methods=['POST'])
def stage_ai_discard():
    with _pending_lock:
        if _pending:
            Path(_pending['dat']).unlink(missing_ok=True)
            _pending.clear()
    return jsonify({'success': True})
