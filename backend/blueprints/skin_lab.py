"""
Skin Lab Blueprint -- a REST surface over the Skin Creator's machinery so an
AI agent (or any script) can create skins: open a costume in a live
HSDRawViewer, fetch/replace textures, run the color-palette tool, reposition
the 3D camera and grab rendered frames, pose animations, and save the result
back to the vault as a new skin.

This drives the SAME HSDRawViewer --stream WebSocket protocol the UI uses
(skinlab.session.ViewerSession), and the SAME palette algorithm
(skinlab.palette, a numpy port of colorUtils.js). Saving dispatches
internally to the existing intake (/import/file) for canonical characters or
to /custom-characters/<slug>/skins/add for custom-character pseudo keys, so
every downstream behavior (classification, previews, metadata) is identical
to a hand-made skin.

One session at a time -- it owns a real OpenGL window.
"""

import io
import json
import logging
import os
import shutil
import threading
import time
from pathlib import Path

import numpy as np
from flask import Blueprint, current_app, jsonify, request, send_file
from PIL import Image

from core.config import HSDRAW_EXE, LOGS_PATH, STORAGE_PATH, get_subprocess_args
from skinlab import compose as compose_mod
from skinlab import palette as palette_mod
from skinlab.session import ViewerSession, ViewerSessionError

TEXTURE_REGIONS_DIR = Path(__file__).parent.parent / 'assets' / 'texture_regions'

logger = logging.getLogger(__name__)

skin_lab_bp = Blueprint('skin_lab', __name__)

_lock = threading.Lock()
_session = None      # ViewerSession
_meta = None         # {character, skinId, datName, tempDir, name}
_edited = {}         # texture index -> PNG bytes (latest pushed)
_palette = None      # {'groups':…, 'pixel_maps':…, 'originals':…, 'adjustments':…}


def _close_session_locked():
    global _session, _meta, _edited, _palette
    if _session is not None:
        try:
            _session.close()
        except Exception:
            pass
    if _meta and _meta.get('tempDir'):
        shutil.rmtree(_meta['tempDir'], ignore_errors=True)
    _session = None
    _meta = None
    _edited = {}
    _palette = None


def _require_session():
    if _session is None or not _session.alive():
        return None, (jsonify({'success': False,
                               'error': 'No skin-lab session is open (or the viewer died). '
                                        'POST /api/mex/skin-lab/open first.'}), 409)
    return _session, None


def _resolve_open_target(data):
    """Resolve {character, skinId} / {character, costumeCode} / {datPath} to
    (dat_path, scene_path, aj_path, temp_dir, dat_name). Mirrors viewer.py's
    paths-vault / paths-vanilla resolution including custom-character pseudo
    keys (custom_characters/<slug>/skins|costumes)."""
    from blueprints.viewer import (custom_character_based_on,
                                   extract_costume_archive,
                                   extract_custom_character_aj, find_aj_file,
                                   find_scene_file, find_vanilla_costume_file)
    from core.metadata import custom_character_slug

    character = (data.get('character') or '').strip()
    skin_id = (data.get('skinId') or '').strip()
    costume_code = (data.get('costumeCode') or '').strip()
    dat_path_arg = (data.get('datPath') or '').strip()

    temp_dir = None
    if dat_path_arg:
        dat_path = Path(dat_path_arg)
        if not dat_path.exists():
            raise FileNotFoundError(f'DAT not found: {dat_path}')
        scene_path = find_scene_file(character) if character else None
        aj_path = find_aj_file(character) if character else None
    elif character and skin_id:
        zip_path = STORAGE_PATH / character / f'{skin_id}.zip'
        if not zip_path.exists():
            raise FileNotFoundError(f'Costume not found in vault: {zip_path}')
        temp_dir, dat_path = extract_costume_archive(zip_path, 'skinlab_')
        if not dat_path or not dat_path.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise FileNotFoundError('No costume archive inside the vault zip')
        scene_path = find_scene_file(character)
        aj_path = find_aj_file(character)
    elif character and costume_code:
        dat_path = find_vanilla_costume_file(character, costume_code)
        if not dat_path or not dat_path.exists():
            raise FileNotFoundError(f'Vanilla costume not found: {character} {costume_code}')
        scene_path = find_scene_file(character)
        aj_path = find_aj_file(character)
    else:
        raise ValueError('Provide {character, skinId}, {character, costumeCode}, or {datPath}')

    # custom characters: their own AJ + the donor skeleton's scene
    slug = custom_character_slug(character) if character else None
    if slug:
        if aj_path is None:
            aj_path = extract_custom_character_aj(slug)
        if scene_path is None:
            based_on = custom_character_based_on(slug)
            if based_on:
                scene_path = find_scene_file(based_on)

    return dat_path, scene_path, aj_path, temp_dir, Path(dat_path).name


@skin_lab_bp.route('/api/mex/skin-lab/open', methods=['POST'])
def open_session():
    """Open a costume in a live viewer. Body: {character, skinId} (vault skin,
    incl. custom_characters/<slug>/skins|costumes pseudo keys) OR
    {character, costumeCode} (vanilla, e.g. "PlFxNr") OR {datPath}."""
    global _session, _meta
    data = request.get_json(silent=True) or {}
    if not Path(HSDRAW_EXE).exists():
        return jsonify({'success': False,
                        'error': f'HSDRawViewer not found at {HSDRAW_EXE}'}), 500
    with _lock:
        _close_session_locked()
        try:
            dat_path, scene_path, aj_path, temp_dir, dat_name = _resolve_open_target(data)
        except (FileNotFoundError, ValueError) as e:
            return jsonify({'success': False, 'error': str(e)}), 400

        from blueprints.viewer import find_available_port
        port = find_available_port()
        try:
            _session = ViewerSession(
                HSDRAW_EXE, port, dat_path, logs_path=LOGS_PATH,
                scene_file=scene_path, aj_file=aj_path,
                subprocess_kwargs=get_subprocess_args())
        except Exception as e:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
            logger.error(f'skin-lab open failed: {e}', exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500

        _meta = {
            'character': data.get('character'),
            'skinId': data.get('skinId'),
            'costumeCode': data.get('costumeCode'),
            'datName': dat_name,
            'tempDir': str(temp_dir) if temp_dir else None,
        }
        logger.info(f"[skin-lab] opened {_meta['character']} ({dat_name}) on port {port}")
        return jsonify({'success': True, 'session': _status_payload()})


def _status_payload():
    anim = (_session.info or {}).get('animation') or {}
    return {
        'character': _meta.get('character'),
        'skinId': _meta.get('skinId'),
        'costumeCode': _meta.get('costumeCode'),
        'datName': _meta.get('datName'),
        'textures': _session.textures,
        'editedTextures': sorted(_edited.keys()),
        'camera': _session.camera,
        'animation': {'frameCount': anim.get('frameCount'),
                      'playing': anim.get('playing')},
        'paletteAnalyzed': _palette is not None,
    }


@skin_lab_bp.route('/api/mex/skin-lab/status', methods=['GET'])
def status():
    with _lock:
        if _session is None or not _session.alive():
            return jsonify({'success': True, 'open': False})
        return jsonify({'success': True, 'open': True, 'session': _status_payload()})


@skin_lab_bp.route('/api/mex/skin-lab/close', methods=['POST'])
def close_session():
    with _lock:
        _close_session_locked()
    return jsonify({'success': True})


# --------------------------------------------------------------------------- #
# textures                                                                      #
# --------------------------------------------------------------------------- #
@skin_lab_bp.route('/api/mex/skin-lab/textures', methods=['GET'])
def list_textures():
    with _lock:
        session, err = _require_session()
        if err:
            return err
        return jsonify({'success': True, 'textures': session.textures,
                        'editedTextures': sorted(_edited.keys())})


@skin_lab_bp.route('/api/mex/skin-lab/texture/<int:index>', methods=['GET'])
def get_texture(index):
    """The texture as PNG -- the edited version if one was pushed, else the
    original from the DAT."""
    with _lock:
        session, err = _require_session()
        if err:
            return err
        try:
            png = _edited.get(index) or session.get_full_texture(index)
        except ViewerSessionError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        return send_file(io.BytesIO(png), mimetype='image/png',
                         download_name=f'texture_{index}.png')


@skin_lab_bp.route('/api/mex/skin-lab/texture/<int:index>', methods=['POST'])
def set_texture(index):
    """Replace a texture. Multipart 'file' or JSON {data: <base64 png>}.
    The image is resampled to the texture's native size if it differs."""
    with _lock:
        session, err = _require_session()
        if err:
            return err
        tex = next((t for t in session.textures if t['index'] == index), None)
        if tex is None:
            return jsonify({'success': False, 'error': f'No texture {index}'}), 404

        if 'file' in request.files:
            raw = request.files['file'].read()
        else:
            data = request.get_json(silent=True) or {}
            b64 = data.get('data') or ''
            if not b64:
                return jsonify({'success': False,
                                'error': "Provide multipart 'file' or JSON {data: base64}"}), 400
            import base64 as _b64
            raw = _b64.b64decode(b64)

        try:
            img = Image.open(io.BytesIO(raw)).convert('RGBA')
        except Exception as e:
            return jsonify({'success': False, 'error': f'Bad image: {e}'}), 400
        if img.size != (tex['width'], tex['height']):
            img = img.resize((tex['width'], tex['height']), Image.NEAREST)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        png = buf.getvalue()

        try:
            session.update_texture(index, png)
        except ViewerSessionError as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        _edited[index] = png
        return jsonify({'success': True, 'index': index,
                        'width': tex['width'], 'height': tex['height']})


# --------------------------------------------------------------------------- #
# camera / view / animation                                                    #
# --------------------------------------------------------------------------- #
@skin_lab_bp.route('/api/mex/skin-lab/camera', methods=['POST'])
def set_camera():
    """Absolute: {rotX?, rotY?, scale?, x?, y?} (degrees / zoom / pan) --
    or relative: {deltaRotX?, deltaRotY?, deltaZoom?, deltaX?, deltaY?}."""
    with _lock:
        session, err = _require_session()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        if any(k in data for k in ('deltaRotX', 'deltaRotY', 'deltaZoom', 'deltaX', 'deltaY')):
            cam = session.nudge_camera(
                delta_rot_x=float(data.get('deltaRotX', 0) or 0),
                delta_rot_y=float(data.get('deltaRotY', 0) or 0),
                delta_zoom=float(data.get('deltaZoom', 0) or 0),
                delta_x=float(data.get('deltaX', 0) or 0),
                delta_y=float(data.get('deltaY', 0) or 0))
        else:
            cam = session.set_camera(
                rot_x=data.get('rotX'), rot_y=data.get('rotY'),
                scale=data.get('scale'), x=data.get('x'), y=data.get('y'))
        return jsonify({'success': True, 'camera': cam})


@skin_lab_bp.route('/api/mex/skin-lab/frame', methods=['GET'])
def get_frame():
    """The current rendered 3D view as a JPEG. Waits for fresh frames so
    recent camera/texture changes are visible. ?width=&height= resizes the
    render target first."""
    with _lock:
        session, err = _require_session()
        if err:
            return err
        w, h = request.args.get('width'), request.args.get('height')
        if w and h:
            session.resize(int(w), int(h))
        try:
            jpeg = session.grab_frame(fresh=int(request.args.get('fresh', 2)))
        except ViewerSessionError as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        return send_file(io.BytesIO(jpeg), mimetype='image/jpeg',
                         download_name='view.jpg')


@skin_lab_bp.route('/api/mex/skin-lab/anims', methods=['GET'])
def list_anims():
    with _lock:
        session, err = _require_session()
        if err:
            return err
        try:
            return jsonify({'success': True, 'symbols': session.get_anim_list()})
        except ViewerSessionError as e:
            return jsonify({'success': False, 'error': str(e)}), 500


@skin_lab_bp.route('/api/mex/skin-lab/anim', methods=['POST'])
def set_anim():
    """{symbol?} load an animation; {frame?} jump to a frame;
    {playing?} play/pause. Fields combine (load -> pause -> frame)."""
    with _lock:
        session, err = _require_session()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        result = {}
        try:
            if data.get('symbol'):
                result = session.load_anim(data['symbol'])
            if 'playing' in data:
                session.set_anim_playing(bool(data['playing']))
            if 'frame' in data:
                session.set_anim_playing(False)
                session.set_anim_frame(float(data['frame']))
        except ViewerSessionError as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        return jsonify({'success': True, 'loaded': result.get('symbol'),
                        'frameCount': result.get('frameCount')})


# --------------------------------------------------------------------------- #
# color palette tool                                                           #
# --------------------------------------------------------------------------- #
def _texture_array(session, index):
    png = _edited.get(index) or session.get_full_texture(index)
    img = Image.open(io.BytesIO(png)).convert('RGBA')
    return np.array(img)


@skin_lab_bp.route('/api/mex/skin-lab/palette/analyze', methods=['POST'])
def palette_analyze():
    """Detect color groups across ALL textures (same algorithm as the UI's
    palette tool, but on full-resolution pixels). Body: {maxGroups?: 8}.
    Snapshots the current textures -- later /palette/apply calls recolor from
    this snapshot, so shifts are absolute, not cumulative."""
    global _palette
    with _lock:
        session, err = _require_session()
        if err:
            return err
        max_groups = int((request.get_json(silent=True) or {}).get('maxGroups', 8))
        originals = {}
        for t in session.textures:
            try:
                originals[t['index']] = _texture_array(session, t['index'])
            except ViewerSessionError:
                continue
        groups, pixel_maps = palette_mod.analyze(originals, max_groups)
        _palette = {'groups': groups, 'pixel_maps': pixel_maps,
                    'originals': originals}
        return jsonify({'success': True, 'groups': groups})


@skin_lab_bp.route('/api/mex/skin-lab/palette/apply', methods=['POST'])
def palette_apply():
    """Recolor by group. Body: {adjustments: [{index, hueShift?, saturationShift?}]}.
    Shifts are ABSOLUTE relative to the analyze-time snapshot (calling again
    with smaller values undoes). Pushes every changed texture to the viewer."""
    with _lock:
        session, err = _require_session()
        if err:
            return err
        if _palette is None:
            return jsonify({'success': False,
                            'error': 'Run /palette/analyze first.'}), 409
        adjustments = {}
        for adj in (request.get_json(silent=True) or {}).get('adjustments', []):
            adjustments[int(adj['index'])] = (
                float(adj.get('hueShift', 0) or 0),
                float(adj.get('saturationShift', 0) or 0))
        if not adjustments:
            return jsonify({'success': False, 'error': 'No adjustments given.'}), 400

        changed = []
        for tex_index, original in _palette['originals'].items():
            result = palette_mod.apply_adjustments(
                original, _palette['pixel_maps'][tex_index], adjustments)
            if result is None:
                continue
            img = Image.fromarray(result, 'RGBA')
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            png = buf.getvalue()
            try:
                session.update_texture(tex_index, png)
            except ViewerSessionError as e:
                return jsonify({'success': False, 'error': str(e),
                                'changed': changed}), 500
            _edited[tex_index] = png
            changed.append(tex_index)
        return jsonify({'success': True, 'changed': changed})


@skin_lab_bp.route('/api/mex/skin-lab/palette/reset', methods=['POST'])
def palette_reset():
    """Push the analyze-time snapshot back (undo palette recolors)."""
    global _palette
    with _lock:
        session, err = _require_session()
        if err:
            return err
        if _palette is None:
            return jsonify({'success': False, 'error': 'Nothing to reset.'}), 409
        restored = []
        for tex_index, original in _palette['originals'].items():
            img = Image.fromarray(original, 'RGBA')
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            png = buf.getvalue()
            try:
                session.update_texture(tex_index, png)
            except ViewerSessionError as e:
                return jsonify({'success': False, 'error': str(e)}), 500
            _edited[tex_index] = png
            restored.append(tex_index)
        return jsonify({'success': True, 'restored': restored})


# --------------------------------------------------------------------------- #
# image generation -- the vendored AI engine (local diffusion) or OpenRouter,  #
# picked by the task-tier resolver; optionally applied straight onto a         #
# texture in the open session.                                                 #
# --------------------------------------------------------------------------- #
class GenerationError(RuntimeError):
    pass


def _openrouter_generate(params, model=None, key=None):
    """Generate a texture image via an OpenRouter image-output model (e.g.
    google/gemini-2.5-flash-image). Key: explicit arg (threaded from the
    request) or OPENROUTER_API_KEY. Returns (absolute_image_path, result_info)."""
    import base64 as _b64
    import hashlib
    import os

    import requests as _rq

    from aiengine import keystore
    key = (key or params.get('openrouterKey')
           or keystore.get_openrouter_key() or '').strip()
    if not key:
        raise GenerationError('No OpenRouter key (set it in Settings)')
    prompt = (params.get('prompt') or '').strip()
    if not prompt:
        raise GenerationError('prompt is required')
    model = model or params.get('model') or 'google/gemini-2.5-flash-image'

    if (params.get('style') or '') == 'scene':
        # backdrop/panorama use -- one coherent image, stretched (not tiled)
        full_prompt = ('Generate a wide painted GAME BACKGROUND scene, no '
                       'text, no borders, cohesive single image filling the '
                       f'frame: {prompt}')
    else:
        full_prompt = ('Generate a seamless tileable TEXTURE swatch, square, '
                       'repeating pattern, no borders, no text, fills the whole '
                       f'image edge to edge: {prompt}')
    logger.info(f'[skin-lab] openrouter generate ({model}): {prompt!r}')
    res = _rq.post('https://openrouter.ai/api/v1/chat/completions', timeout=180, json={
        'model': model,
        'messages': [{'role': 'user', 'content': full_prompt}],
        'modalities': ['image', 'text'],
    }, headers={'Authorization': f'Bearer {key}'})
    body = res.json()
    if 'error' in body:
        raise GenerationError(f'openrouter generation failed: {body["error"]}')
    msg = (body.get('choices') or [{}])[0].get('message') or {}
    images = msg.get('images') or []
    if not images:
        raise GenerationError('openrouter returned no image: '
                              + str(msg.get('content') or body)[:300])
    url = (images[0].get('image_url') or {}).get('url') or ''
    if 'base64,' not in url:
        raise GenerationError('unexpected image payload from openrouter')
    raw = _b64.b64decode(url.split('base64,', 1)[1])

    out_dir = STORAGE_PATH / 'skinlab_materials'
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = (params.get('name') or hashlib.sha1(prompt.encode()).hexdigest()[:10])
    path = out_dir / f'{stem}.png'
    path.write_bytes(raw)
    return path, {'model': model}


def _generate_material(params):
    """Route a {generate: ...} request through the task-tier resolver.

    params: {prompt, name?, seed?, width?, height?, style?: 'scene',
             tier?: 'standard'|'strong', kind?: 'material'|'ailab'|'stage',
             provider?, model?, openrouterKey?}
    Material cache first (keyed by name/prompt hash); then the resolved
    provider — OpenRouter falls back to a local model on failure (e.g. key
    out of credits). Every attempt lands in the telemetry ledger."""
    import hashlib
    import time as _time

    from aiengine import routing, telemetry
    from aiengine.routing import RoutingError
    from aiengine.runner import EngineError

    prompt = (params.get('prompt') or '').strip()
    stem = (params.get('name') or hashlib.sha1(prompt.encode()).hexdigest()[:10])
    cache = STORAGE_PATH / 'skinlab_materials' / f'{stem}.png'

    tier = params.get('tier') or \
        ('strong' if (params.get('style') or '') == 'scene' else 'standard')
    kind = params.get('kind') or 'material'
    client_key = bool(params.get('openrouterKey'))

    # NUCLEUS_IMAGE_PROVIDER=local (alias: assetfarm) forces local generation
    # everywhere (batch runs / cost control); requests can still name a
    # provider/model when unset.
    forced = os.environ.get('NUCLEUS_IMAGE_PROVIDER', '').strip().lower()
    provider = forced if forced in ('local', 'assetfarm') \
        else (params.get('provider') or '').strip().lower()
    model = params.get('model') or None
    if provider in ('local', 'assetfarm') and model and '/' in str(model):
        model = None   # API slug leaked into a forced-local request

    try:
        resolved = routing.resolve(tier, override_provider=provider,
                                   override_model=model, client_key=client_key)
    except RoutingError as e:
        raise GenerationError(str(e))

    if cache.exists():
        telemetry.record_run(resolved['provider'], resolved['model'], tier,
                             kind, 0.0, True, cached=True)
        return cache, {'cached': True, 'tier': tier,
                       'escalated': resolved['escalated'],
                       'provider': resolved['provider'],
                       'model': resolved['model'], 'label': resolved['label'],
                       'estCostUsd': 0.0}

    if resolved['provider'] == 'openrouter':
        t0 = _time.time()
        try:
            image_path, result = _openrouter_generate(
                params, model=resolved['model'],
                key=params.get('openrouterKey'))
            telemetry.record_run('openrouter', resolved['model'], tier, kind,
                                 _time.time() - t0, True,
                                 est_cost_usd=resolved['estCostUsd'])
            result.update(tier=tier, escalated=resolved['escalated'],
                          provider='openrouter', label=resolved['label'],
                          estCostUsd=resolved['estCostUsd'],
                          seconds=round(_time.time() - t0, 1))
            return image_path, result
        except GenerationError as e:
            telemetry.record_run('openrouter', resolved['model'], tier, kind,
                                 _time.time() - t0, False)
            logger.warning(f'[skin-lab] openrouter generation failed ({e}); '
                           'falling back to a local model')
            try:
                resolved = routing.resolve(tier, override_provider='local',
                                           client_key=client_key)
            except RoutingError:
                raise e   # nothing local to fall back to

    from aiengine import runner as _runner
    cache.parent.mkdir(parents=True, exist_ok=True)
    style = 'scene' if (params.get('style') or '') == 'scene' else 'tile'

    # The local worker reports model load + denoise progress ("loading X…",
    # "step 3/4 | …"); with a progressEvent the caller (AI studio run thread)
    # gets those on its socket channel instead of silence. Message-only —
    # the orchestrator owns the overall percentage.
    on_progress = None
    progress_event = (params.get('progressEvent') or '').strip()
    if progress_event:
        from core.state import get_socketio
        _socketio = get_socketio()
        _label = resolved['label'] or resolved['model']

        def on_progress(_pct, desc):
            if desc:
                _socketio.emit(progress_event, {'message': f'{_label}: {desc}'})

    t0 = _time.time()
    try:
        _, seconds = _runner.generate(
            prompt, resolved['model'], cache, style=style,
            seed=params.get('seed'),
            width=int(params['width']) if params.get('width') else None,
            height=int(params['height']) if params.get('height') else None,
            on_progress=on_progress)
    except EngineError as e:
        telemetry.record_run('local', resolved['model'], tier, kind,
                             _time.time() - t0, False)
        raise GenerationError(str(e))
    telemetry.record_run('local', resolved['model'], tier, kind, seconds, True)
    return cache, {'model': resolved['model'], 'tier': tier,
                   'escalated': resolved['escalated'], 'provider': 'local',
                   'label': resolved['label'], 'estCostUsd': 0.0,
                   'seconds': seconds}


@skin_lab_bp.route('/api/mex/skin-lab/generate-texture', methods=['POST'])
def generate_texture():
    """Generate an image via the AI engine and optionally apply it to a
    texture. Body: {prompt, index?, style?: 'scene', tier?, model?, seed?,
    width?, height?, name?}. With `index`, the result is resized to that
    texture and pushed into the open session; without it, the image is just
    generated and its path returned. First call may be slow (model load)."""
    data = request.get_json(silent=True) or {}
    if not (data.get('prompt') or '').strip():
        return jsonify({'success': False, 'error': 'prompt is required'}), 400
    try:
        image_path, result = _generate_material(data)
    except GenerationError as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    payload = {'success': True, 'imagePath': str(image_path),
               'model': result.get('model'), 'tier': result.get('tier'),
               'escalated': result.get('escalated'),
               'seconds': result.get('seconds')}

    index = data.get('index')
    if index is not None:
        with _lock:
            session, err = _require_session()
            if err:
                payload['applied'] = False
                payload['applyError'] = 'no open session'
                return jsonify(payload)
            tex = next((t for t in session.textures if t['index'] == int(index)), None)
            if tex is None:
                payload['applied'] = False
                payload['applyError'] = f'no texture {index}'
                return jsonify(payload)
            img = Image.open(image_path).convert('RGBA')
            if img.size != (tex['width'], tex['height']):
                img = img.resize((tex['width'], tex['height']), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            png = buf.getvalue()
            try:
                session.update_texture(int(index), png)
            except ViewerSessionError as e:
                payload['applied'] = False
                payload['applyError'] = str(e)
                return jsonify(payload)
            _edited[int(index)] = png
            payload['applied'] = True
            payload['index'] = int(index)
    return jsonify(payload)


# --------------------------------------------------------------------------- #
# regions + deterministic compositing -- the structured ops a UI or a small    #
# planner model drives with JSON (no code, no agent).                          #
# --------------------------------------------------------------------------- #
def _load_region_map():
    """The texture-region map for the open session's character (canonical name
    or a custom character's donor), or None. Flags 'approximate' when the open
    DAT's texture count differs from the map's basis.

    MatAnim swap frames (blink textures etc.) are folded in dynamically: each
    frame inherits the region/protection of the material texture its bank
    animates, so region ops (tint/composite/hue-shift) and pad masks cover
    them without per-character map changes. Maps stay authored against the
    material textures only -- basis counts ignore matanim entries."""
    character = (_meta or {}).get('character') or ''
    name = character
    if character.startswith('custom_characters/'):
        from blueprints.viewer import custom_character_based_on
        from core.metadata import custom_character_slug
        slug = custom_character_slug(character)
        name = custom_character_based_on(slug) if slug else ''
    path = TEXTURE_REGIONS_DIR / f'{name}.json'
    if not name or not path.exists():
        return None
    region_map = json.loads(path.read_text(encoding='utf-8'))
    material_count = sum(1 for t in _session.textures if not t.get('matAnim'))
    basis_count = (region_map.get('basis') or {}).get('textureCount')
    region_map['approximate'] = (basis_count is not None
                                 and basis_count != material_count)

    links = {}   # material texture index -> [matanim swap-frame indexes]
    for t in _session.textures:
        animates = t.get('animates')
        if t.get('matAnim') and isinstance(animates, int) and animates >= 0:
            links.setdefault(animates, []).append(t['index'])
    if links:
        regions = region_map.get('regions') or {}
        for region, idxs in regions.items():
            extra = [m for base in idxs for m in links.get(base, [])]
            if extra:
                regions[region] = list(idxs) + extra
        protected = region_map.get('protected') or []
        extra = [m for base in protected for m in links.get(base, [])]
        if extra:
            region_map['protected'] = list(protected) + extra
    return region_map


def _hue_histogram(session, idxs):
    """360-bin hue histogram over the saturated, mid-lightness pixels of a
    set of textures."""
    bins = np.zeros(360, dtype=np.int64)
    for index in idxs:
        try:
            arr = _texture_png_array(session, index)
        except Exception:
            continue
        h, s, l = palette_mod.rgb_to_hsl(arr[..., :3].astype(np.float64))
        mask = (arr[..., 3] >= 128) & (s >= 25) & (l >= 15) & (l <= 90)
        if mask.any():
            bins += np.bincount(np.floor(h[mask]).astype(np.int64) % 360,
                                minlength=360)
    return bins


def _band_from_bins(bins):
    """Dominant hue band: walk out from the peak until bins drop below 3%."""
    peak = int(bins.argmax())
    floor = max(1, bins[peak] * 0.03)
    lo = peak
    while bins[(lo - 1) % 360] >= floor and (peak - lo) % 360 < 100:
        lo = (lo - 1) % 360
    hi = peak
    while bins[(hi + 1) % 360] >= floor and (hi - peak) % 360 < 100:
        hi = (hi + 1) % 360
    return {'hueMin': int(lo), 'hueMax': int(hi), 'satMin': 18}


def _compute_live_hints(session, region_map):
    """Per-COSTUME mask hints, computed from the open DAT's actual pixels.
    Shipped hints describe the basis costume's colors (e.g. a blue jacket),
    but every costume color differs -- so for hue-defined regions we histogram
    the region's saturated pixels and take the dominant hue band. The armor
    hint (low-sat whites) is costume-independent and kept as shipped."""
    hints = dict((region_map.get('maskHints') or {}))
    # maps can opt regions out of live recomputation ("liveHints" key): regions
    # whose textures are single-purpose work best with NO mask (all opaque
    # pixels), and a computed hue band would wrongly narrow them.
    live_regions = region_map.get('liveHints')
    if live_regions is None:
        live_regions = ('fur', 'cloth', 'eyes')
    for region in live_regions:
        idxs = (region_map.get('regions') or {}).get(region) or []
        bins = _hue_histogram(session, idxs)
        if bins.sum() < 200:
            continue
        if region == 'eyes':
            # the eye texture is mostly the SKIN around the iris (fur-toned);
            # suppress the fur band so the iris cluster wins the peak
            fur_hint = hints.get('fur') or {}
            lo_f, hi_f = fur_hint.get('hueMin'), fur_hint.get('hueMax')
            if lo_f is not None and hi_f is not None:
                pad = 15
                for hdeg in range(360):
                    if lo_f <= hi_f:
                        inside = (lo_f - pad) <= hdeg <= (hi_f + pad)
                    else:
                        inside = hdeg >= (lo_f - pad) or hdeg <= (hi_f + pad)
                    if inside:
                        bins[hdeg] = 0
            if bins.sum() < 50:
                continue
        hints[region] = _band_from_bins(bins)
    return hints


def _region_hints():
    """Live hints for the open session, computed once and cached in _meta."""
    if _meta is None:
        return {}
    if 'liveHints' not in _meta:
        region_map = _load_region_map()
        if region_map is None:
            _meta['liveHints'] = {}
        else:
            try:
                _meta['liveHints'] = _compute_live_hints(_session, region_map)
            except Exception:
                logger.warning('live hint computation failed', exc_info=True)
                _meta['liveHints'] = dict(region_map.get('maskHints') or {})
    return _meta['liveHints']


# Regions whose color defines the character's BODY — feature textures
# (eyes/cheeks/mouth) carry padding pixels in this color around the feature.
BODY_REGIONS = ('fur', 'cloth')


def _body_band(region_map):
    """(region, hue band) for the BODY region, cached per session. Uses the
    live hint when present; maps that OPT OUT of live hints (single-purpose
    textures, e.g. Pikachu) still get a band computed ad hoc here — the
    opt-out is about op masks, but pad masks always need the body color."""
    if _meta is None:
        return None, None
    if 'bodyBand' not in _meta:
        result = (None, None)
        hints = _region_hints()
        for region in BODY_REGIONS:
            idxs = (region_map.get('regions') or {}).get(region)
            if not idxs:
                continue
            band = hints.get(region)
            if not band:
                bins = _hue_histogram(_session, idxs)
                band = _band_from_bins(bins) if bins.sum() >= 200 else None
            if band:
                result = (region, band)
                break
        _meta['bodyBand'] = result
    return _meta['bodyBand']


def _body_region(region_map):
    """The region whose color band represents the body, or None."""
    return _body_band(region_map)[0]


def _dilate(mask, iters=2):
    """Grow a boolean mask by `iters` pixels (4-neighborhood) — swallows the
    anti-aliased fringe between a feature and its padding."""
    for _ in range(iters):
        grown = mask.copy()
        grown[1:, :] |= mask[:-1, :]
        grown[:-1, :] |= mask[1:, :]
        grown[:, 1:] |= mask[:, :-1]
        grown[:, :-1] |= mask[:, 1:]
        mask = grown
    return mask


def _feature_pad_masks():
    """{index: bool mask} of BODY-COLORED PADDING inside each protected
    feature texture (eye/cheek/mouth textures carry fur-colored pixels
    around the feature). Computed ONCE from the pristine DAT pixels — later
    recolors can't shift it. Powers two fixes for the face-square problem:
    spillover (body ops also treat this padding, so features don't sit on
    stock-colored squares) and feature confinement (eye/face ops subtract
    the padding, so a tint can't flood the whole texture)."""
    if _meta is None:
        return {}
    if 'featurePadMasks' not in _meta:
        masks = {}
        region_map = _load_region_map()
        _, band = _body_band(region_map) if region_map else (None, None)
        if band:
            # widen the band: feature borders anti-alias toward neighboring
            # hues (yellow fur -> orange ring around a red cheek) and at
            # lower saturation than the body proper
            band = {'hueMin': (band['hueMin'] - 10) % 360,
                    'hueMax': (band['hueMax'] + 10) % 360,
                    'satMin': max(10, band.get('satMin', 18) - 8)}
            for index in (region_map.get('protected') or []):
                try:
                    # get_full_texture is always the ORIGINAL (edits live in
                    # the _edited overlay), so this is pristine by definition
                    png = _session.get_full_texture(index)
                    arr = np.array(Image.open(io.BytesIO(png)).convert('RGBA'))
                    m = compose_mod.build_mask(arr, **_mask_kwargs(band))
                    if m.any():
                        masks[index] = _dilate(m) & (arr[..., 3] >= 128)
                except Exception:
                    continue
        _meta['featurePadMasks'] = masks
    return _meta['featurePadMasks']


def _pad_mask_for(index, shape):
    """The padding mask for a texture, resized (nearest) when the working
    array's resolution differs (composite upscales tiny canvases)."""
    m = _feature_pad_masks().get(index)
    if m is None:
        return None
    if m.shape != tuple(shape[:2]):
        img = Image.fromarray(m.astype(np.uint8) * 255, 'L')
        img = img.resize((shape[1], shape[0]), Image.NEAREST)
        m = np.asarray(img) >= 128
    return m


def _resolve_targets(data, region_map):
    """The texture indexes + default mask for a request that names either
    explicit {textures: [...]} or a {region: "fur"}. Returns
    (indexes, default_mask, protected, error)."""
    protected = set((region_map or {}).get('protected') or [])
    if data.get('textures') is not None:
        try:
            indexes = [int(i) for i in data['textures']]
        except (TypeError, ValueError):
            return None, None, None, 'textures must be a list of indexes'
        return indexes, None, protected, None
    region = (data.get('region') or '').strip()
    if not region:
        return None, None, None, 'Provide textures: [indexes] or region: "<name>"'
    if region_map is None:
        return None, None, None, ('No texture-region map for this character -- '
                                  'use explicit textures + mask')
    indexes = (region_map.get('regions') or {}).get(region)
    if not indexes:
        known = ', '.join((region_map.get('regions') or {}).keys())
        return None, None, None, f'Unknown region "{region}" (known: {known})'
    # live hints follow the OPEN costume's actual colors (shipped hints only
    # describe the basis costume)
    default_mask = _region_hints().get(region) \
        or (region_map.get('maskHints') or {}).get(region)
    return list(indexes), default_mask, protected, None


def _mask_kwargs(mask):
    mask = mask or {}
    return {
        'hue_min': mask.get('hueMin'), 'hue_max': mask.get('hueMax'),
        'sat_min': mask.get('satMin'), 'sat_max': mask.get('satMax'),
        'lum_min': mask.get('lumMin'), 'lum_max': mask.get('lumMax'),
    }


def _texture_png_array(session, index):
    png = _edited.get(index) or session.get_full_texture(index)
    return np.array(Image.open(io.BytesIO(png)).convert('RGBA'))


# Some fighters keep almost no texture real estate -- Pichu's whole body is an
# 8x8 solid-yellow swatch, and Pikachu/Jigglypuff are similar. A material
# composited into that can only average to one mushy color (and on 64px ear
# textures it shows as giant pattern chunks). UVs are normalized, so pushing a
# LARGER texture maps onto the model identically -- the viewer re-encodes the
# TOBJ at the pushed size. Blow tiny canvases up before compositing.
MIN_COMPOSITE_RES = 128


def _upscale_for_composite(arr):
    h, w = arr.shape[:2]
    longest = max(w, h)
    if longest >= MIN_COMPOSITE_RES:
        return arr
    k = 1
    while longest * k < MIN_COMPOSITE_RES:
        k *= 2
    img = Image.fromarray(arr, 'RGBA').resize((w * k, h * k), Image.LANCZOS)
    return np.array(img)


def _push_array(session, index, arr):
    buf = io.BytesIO()
    Image.fromarray(arr, 'RGBA').save(buf, format='PNG')
    png = buf.getvalue()
    session.update_texture(index, png)
    _edited[index] = png


@skin_lab_bp.route('/api/mex/skin-lab/regions', methods=['GET'])
def get_regions():
    """The open character's texture-region map (roles per texture index,
    protected indexes, default masks per region). 404 when no map is shipped
    for this character -- callers then work with explicit textures + masks."""
    with _lock:
        session, err = _require_session()
        if err:
            return err
        region_map = _load_region_map()
        if region_map is None:
            return jsonify({'success': False,
                            'error': 'No texture-region map for this character'}), 404
        # hints recomputed from the OPEN costume's pixels (colors vary per costume)
        region_map['liveMaskHints'] = _region_hints()
        return jsonify({'success': True, 'regionMap': region_map})


@skin_lab_bp.route('/api/mex/skin-lab/composite', methods=['POST'])
def composite_textures():
    """Re-fabric textures: lay a material over the masked pixels, shaded by
    the texture's original lightness (folds/seams survive). Body:
    {region: "fur" | textures: [i...],
     material: {path} | {data: b64} | {generate: {prompt, tier?, kind?, ...}},
     mask?: {hueMin,hueMax,satMin,satMax,lumMin,lumMax}   (default: the
            region's mask hint; REQUIRED with explicit textures),
     modulate?: {lo: 0.3, hi: 1.6},
     force?: false}   -- protected textures (eyes/mouth) are skipped unless forced."""
    data = request.get_json(silent=True) or {}

    # Resolve the material image first (generation can be slow; no lock held)
    material = data.get('material') or {}
    generated = None
    try:
        if material.get('generate'):
            image_path, generated = _generate_material(material['generate'])
            mat_img = Image.open(image_path).convert('RGB')
        elif material.get('path'):
            mat_img = Image.open(material['path']).convert('RGB')
        elif material.get('data'):
            import base64 as _b64
            mat_img = Image.open(io.BytesIO(_b64.b64decode(material['data']))).convert('RGB')
        else:
            return jsonify({'success': False,
                            'error': 'material must be {path}, {data} or {generate}'}), 400
    except GenerationError as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'Bad material image: {e}'}), 400
    mat_arr = np.array(mat_img)

    with _lock:
        session, err = _require_session()
        if err:
            return err
        region_map = _load_region_map()
        indexes, default_mask, protected, rerr = _resolve_targets(data, region_map)
        if rerr:
            return jsonify({'success': False, 'error': rerr}), 400
        mask_spec = data.get('mask') or default_mask
        if mask_spec is None:
            if (data.get('region') or '').strip():
                mask_spec = {}   # region without a mask hint: every opaque pixel
            else:
                return jsonify({'success': False,
                                'error': 'mask is required with explicit textures'}), 400
        modulate = data.get('modulate') or {}
        lum_lo = float(modulate.get('lo', 0.3))
        lum_hi = float(modulate.get('hi', 1.6))
        force = bool(data.get('force'))

        valid = {t['index'] for t in session.textures}
        changed, skipped = [], []
        for index in indexes:
            if index not in valid:
                skipped.append({'index': index, 'reason': 'no such texture'})
                continue
            if index in protected and not force:
                skipped.append({'index': index, 'reason': 'protected'})
                continue
            try:
                arr = _upscale_for_composite(_texture_png_array(session, index))
                mask = compose_mod.build_mask(arr, **_mask_kwargs(mask_spec))
                pad = None if force else _pad_mask_for(index, arr.shape)
                if pad is not None:
                    mask &= ~pad   # never flood a feature texture's padding
                result = compose_mod.composite(arr, mat_arr, mask,
                                               lum_lo=lum_lo, lum_hi=lum_hi)
                if result is None:
                    skipped.append({'index': index, 'reason': 'mask matched nothing'})
                    continue
                _push_array(session, index, result)
                changed.append(index)
            except ViewerSessionError as e:
                return jsonify({'success': False, 'error': str(e),
                                'changed': changed, 'skipped': skipped}), 500

        # SPILLOVER: a body-region op also treats the body-colored padding
        # INSIDE the protected feature textures (eye/cheek/mouth canvases),
        # so the new look runs right up to the feature instead of leaving
        # stock-colored squares around it.
        if (data.get('region') or '').strip() == _body_region(region_map) \
                and data.get('spillover', True):
            for index in sorted(set(protected) - set(indexes)):
                if index not in valid:
                    continue
                try:
                    arr = _upscale_for_composite(_texture_png_array(session, index))
                    pad = _pad_mask_for(index, arr.shape)
                    if pad is None or not pad.any():
                        continue
                    result = compose_mod.composite(arr, mat_arr, pad,
                                                   lum_lo=lum_lo, lum_hi=lum_hi)
                    if result is not None:
                        _push_array(session, index, result)
                        changed.append(index)
                except Exception:
                    logger.warning(f'[skin-lab] composite spillover failed on '
                                   f'{index}', exc_info=True)
        return jsonify({'success': True, 'changed': changed,
                        'skipped': skipped, 'generated': generated})


@skin_lab_bp.route('/api/mex/skin-lab/tint', methods=['POST'])
def tint_textures():
    """COLORIZE masked pixels: set hue + saturation outright, keep lightness.
    Works on whites/grays where hue-shift is a no-op (e.g. white armor ->
    green armor). Body: {region | textures, mask?, hue (0-360),
    saturation?: 60, force?} -- same target/mask semantics as /composite."""
    data = request.get_json(silent=True) or {}
    if data.get('hue') is None:
        return jsonify({'success': False, 'error': 'hue is required (0-360)'}), 400
    hue = float(data['hue'])
    saturation = float(data.get('saturation', 60) or 60)

    with _lock:
        session, err = _require_session()
        if err:
            return err
        region_map = _load_region_map()
        indexes, default_mask, protected, rerr = _resolve_targets(data, region_map)
        if rerr:
            return jsonify({'success': False, 'error': rerr}), 400
        mask_spec = data.get('mask') or default_mask
        if mask_spec is None:
            if (data.get('region') or '').strip():
                mask_spec = {}   # region without a mask hint: every opaque pixel
            else:
                return jsonify({'success': False,
                                'error': 'mask is required with explicit textures'}), 400
        valid = {t['index'] for t in session.textures}
        changed, skipped = [], []
        for index in indexes:
            if index not in valid:
                skipped.append({'index': index, 'reason': 'no such texture'})
                continue
            # tint preserves structure -- protected (eyes/mouth) stays allowed;
            # recoloring eyes is its primary use
            try:
                arr = _texture_png_array(session, index)
                mask = compose_mod.build_mask(arr, **_mask_kwargs(mask_spec))
                # an eye/cheek tint must hit the FEATURE, not the texture's
                # body-colored padding (Pikachu's green-box-eyes bug)
                pad = None if data.get('force') else _pad_mask_for(index, arr.shape)
                if pad is not None:
                    mask &= ~pad
                result = compose_mod.tint(arr, mask, hue, saturation)
                if result is None:
                    skipped.append({'index': index, 'reason': 'mask matched nothing'})
                    continue
                _push_array(session, index, result)
                changed.append(index)
            except ViewerSessionError as e:
                return jsonify({'success': False, 'error': str(e),
                                'changed': changed, 'skipped': skipped}), 500

        # spillover: body-region tints recolor the feature textures' padding
        if (data.get('region') or '').strip() == _body_region(region_map) \
                and data.get('spillover', True):
            for index in sorted(set(protected) - set(indexes)):
                if index not in valid:
                    continue
                try:
                    arr = _texture_png_array(session, index)
                    pad = _pad_mask_for(index, arr.shape)
                    if pad is None or not pad.any():
                        continue
                    result = compose_mod.tint(arr, pad, hue, saturation)
                    if result is not None:
                        _push_array(session, index, result)
                        changed.append(index)
                except Exception:
                    logger.warning(f'[skin-lab] tint spillover failed on '
                                   f'{index}', exc_info=True)
        return jsonify({'success': True, 'changed': changed, 'skipped': skipped})


@skin_lab_bp.route('/api/mex/skin-lab/hue-shift', methods=['POST'])
def hue_shift_textures():
    """Rotate hue / push saturation on masked pixels (lightness untouched).
    Body: {region | textures, mask?, hueShift?, saturationShift?, force?} --
    same target/mask semantics as /composite."""
    data = request.get_json(silent=True) or {}
    hue_delta = float(data.get('hueShift', 0) or 0)
    sat_delta = float(data.get('saturationShift', 0) or 0)
    if not hue_delta and not sat_delta:
        return jsonify({'success': False,
                        'error': 'hueShift or saturationShift is required'}), 400

    with _lock:
        session, err = _require_session()
        if err:
            return err
        region_map = _load_region_map()
        indexes, default_mask, protected, rerr = _resolve_targets(data, region_map)
        if rerr:
            return jsonify({'success': False, 'error': rerr}), 400
        mask_spec = data.get('mask') or default_mask
        if mask_spec is None:
            if (data.get('region') or '').strip():
                mask_spec = {}   # region without a mask hint: every opaque pixel
            else:
                return jsonify({'success': False,
                                'error': 'mask is required with explicit textures'}), 400
        valid = {t['index'] for t in session.textures}
        changed, skipped = [], []
        for index in indexes:
            if index not in valid:
                skipped.append({'index': index, 'reason': 'no such texture'})
                continue
            # hue-shift preserves structure -- protected (eyes/mouth) allowed
            try:
                arr = _texture_png_array(session, index)
                mask = compose_mod.build_mask(arr, **_mask_kwargs(mask_spec))
                pad = None if data.get('force') else _pad_mask_for(index, arr.shape)
                if pad is not None:
                    mask &= ~pad   # feature ops stay off the body padding
                result = compose_mod.hue_shift(arr, mask, hue_delta, sat_delta)
                if result is None:
                    skipped.append({'index': index, 'reason': 'mask matched nothing'})
                    continue
                _push_array(session, index, result)
                changed.append(index)
            except ViewerSessionError as e:
                return jsonify({'success': False, 'error': str(e),
                                'changed': changed, 'skipped': skipped}), 500

        # spillover: body-region hue-shifts rotate the feature padding too
        if (data.get('region') or '').strip() == _body_region(region_map) \
                and data.get('spillover', True):
            for index in sorted(set(protected) - set(indexes)):
                if index not in valid:
                    continue
                try:
                    arr = _texture_png_array(session, index)
                    pad = _pad_mask_for(index, arr.shape)
                    if pad is None or not pad.any():
                        continue
                    result = compose_mod.hue_shift(arr, pad, hue_delta, sat_delta)
                    if result is not None:
                        _push_array(session, index, result)
                        changed.append(index)
                except Exception:
                    logger.warning(f'[skin-lab] hue-shift spillover failed on '
                                   f'{index}', exc_info=True)
        return jsonify({'success': True, 'changed': changed, 'skipped': skipped})


# --------------------------------------------------------------------------- #
# export / save                                                                #
# --------------------------------------------------------------------------- #
@skin_lab_bp.route('/api/mex/skin-lab/export-dat', methods=['GET'])
def export_dat():
    with _lock:
        session, err = _require_session()
        if err:
            return err
        time.sleep(0.5)   # let queued texture updates land on the UI thread
        try:
            dat = session.export_dat()
        except ViewerSessionError as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        return send_file(io.BytesIO(dat), mimetype='application/octet-stream',
                         download_name=_meta.get('datName') or 'skin.dat')


@skin_lab_bp.route('/api/mex/skin-lab/save', methods=['POST'])
def save_skin():
    """Export the edited DAT and save it to the vault as a NEW skin.
    Body: {name}. Routing matches the Skin Creator UI: a custom character's
    skin goes to that character's Custom Skins (original Pl* dat name kept);
    everything else goes through the unified intake (auto-classified)."""
    import zipfile

    with _lock:
        session, err = _require_session()
        if err:
            return err
        data = request.get_json(silent=True) or {}
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'success': False, 'error': 'name is required'}), 400

        time.sleep(0.5)   # let queued texture updates land on the UI thread
        try:
            dat = session.export_dat()
        except ViewerSessionError as e:
            return jsonify({'success': False, 'error': str(e)}), 500

        character = _meta.get('character') or ''
        is_custom = character.startswith('custom_characters/')
        # Keep the source's Pl* dat name: custom-character installs key costumes
        # by it, and the canonical intake only recognizes Pl*-stemmed DATs.
        dat_name = _meta.get('datName') or ''
        if not dat_name.lower().startswith('pl'):
            dat_name = f'{name}.dat'

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(dat_name, dat)
        zip_bytes = buf.getvalue()

    # Dispatch OUTSIDE the lock -- the nested request handlers are independent.
    client = current_app.test_client()
    if is_custom:
        slug = character.split('/')[1]
        res = client.post(f'/api/mex/custom-characters/{slug}/skins/add',
                          data={'file': (io.BytesIO(zip_bytes), f'{name}.zip'),
                                'name': name},
                          content_type='multipart/form-data')
    else:
        form = {'file': (io.BytesIO(zip_bytes), f'{name}.zip'),
                'custom_title': name}
        for passthrough in ('slippi_action', 'duplicate_action'):
            if data.get(passthrough):
                form[passthrough] = data[passthrough]
        res = client.post('/api/mex/import/file', data=form,
                          content_type='multipart/form-data')

    payload = res.get_json(silent=True) or {}
    payload.setdefault('success', res.status_code == 200)
    return jsonify(payload), res.status_code
