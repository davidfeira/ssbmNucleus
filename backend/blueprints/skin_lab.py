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
import shutil
import threading
import time
from pathlib import Path

import numpy as np
from flask import Blueprint, current_app, jsonify, request, send_file
from PIL import Image

from core.config import HSDRAW_EXE, LOGS_PATH, STORAGE_PATH, get_subprocess_args
from skinlab import palette as palette_mod
from skinlab.session import ViewerSession, ViewerSessionError

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
# assetFarm bridge -- generate an image with local diffusion and (optionally)  #
# apply it straight onto a texture in the open session.                        #
# --------------------------------------------------------------------------- #
@skin_lab_bp.route('/api/mex/skin-lab/generate-texture', methods=['POST'])
def generate_texture():
    """Generate an image via the assetFarm project and optionally apply it to
    a texture. Body: {prompt, index?, recipe?: 'tileset_tile', model?, seed?,
    width?, height?, name?}. With `index`, the result is resized to that
    texture and pushed into the open session; without it, the image is just
    generated and its path returned. First call may be slow (model load)."""
    import subprocess

    from core.config import ASSETFARM_DIR

    data = request.get_json(silent=True) or {}
    prompt = (data.get('prompt') or '').strip()
    if not prompt:
        return jsonify({'success': False, 'error': 'prompt is required'}), 400

    farm_python = ASSETFARM_DIR / '.venv' / 'Scripts' / 'python.exe'
    if not farm_python.exists():
        return jsonify({'success': False,
                        'error': f'assetFarm not found at {ASSETFARM_DIR} '
                                 '(set NUCLEUS_ASSETFARM_DIR)'}), 500

    recipe = data.get('recipe') or 'tileset_tile'
    cmd = [str(farm_python), '-m', 'assetfarm', 'generate', recipe,
           '-p', prompt, '-n', (data.get('name') or 'skinlab').strip(),
           '--project', 'nucleus-skinlab', '--json']
    if data.get('model'):
        cmd += ['--model', str(data['model'])]
    if data.get('seed') is not None:
        cmd += ['--seed', str(int(data['seed']))]
    if data.get('width'):
        cmd += ['--width', str(int(data['width']))]
    if data.get('height'):
        cmd += ['--height', str(int(data['height']))]

    logger.info(f'[skin-lab] assetFarm generate: {prompt!r} (recipe={recipe})')
    try:
        proc = subprocess.run(cmd, cwd=str(ASSETFARM_DIR), capture_output=True,
                              text=True, timeout=900, **get_subprocess_args())
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'assetFarm generation timed out'}), 500

    # --json puts a machine-readable result on the LAST stdout line
    result = None
    for line in reversed((proc.stdout or '').strip().splitlines()):
        try:
            result = json.loads(line)
            break
        except json.JSONDecodeError:
            continue
    if not result or not result.get('ok') or not result.get('output_paths'):
        detail = (result or {}).get('error') or (proc.stderr or proc.stdout or '')[-2000:]
        return jsonify({'success': False,
                        'error': f'assetFarm generation failed: {detail}'}), 500

    # output_paths are relative to the assetFarm project directory
    image_path = Path(result['output_paths'][0])
    if not image_path.is_absolute():
        image_path = ASSETFARM_DIR / image_path
    payload = {'success': True, 'imagePath': str(image_path),
               'seed': result.get('seed'), 'recipe': result.get('recipe')}

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
