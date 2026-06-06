"""
Test-in-game Blueprint -- boot a freshly-built ISO in an isolated throwaway
Dolphin, drive it to a real OFFLINE match, select the modded character/stage,
trigger effects, and report PASS / CRASH / HUNG with a screenshot.

Mirrors export.py's pattern: a REST kickoff endpoint that runs the work in a
background thread and streams progress over SocketIO
(test_progress / test_complete / test_error). All the actual driving lives in the
self-contained `ingame` engine (stdlib + Pillow, no extra installs); this
blueprint is just the HTTP/socket shell + input validation + a one-at-a-time
guard. It NEVER goes online -- the engine aborts if it ever sees the online
scene -- so it can't disrupt the user's Slippi or waste a real player's time.
"""

import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path

from flask import Blueprint, request, jsonify

from core.config import STORAGE_PATH
from core.state import get_socketio

logger = logging.getLogger(__name__)

test_in_game_bp = Blueprint('test_in_game', __name__)

# One test at a time: two Dolphins would fight over the screen + pipe.
_test_lock = threading.Lock()
_test_running = False


def _load_manifest(data):
    """Resolve the build manifest (what to drive) from the request, tolerating
    its absence -- without one we fall back to a boot-health check."""
    manifest = data.get('manifest')
    if isinstance(manifest, dict) and manifest:
        return manifest
    manifest_path = data.get('manifestPath')
    if manifest_path and os.path.exists(manifest_path):
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not read manifestPath {manifest_path}: {e}")
    return None


@test_in_game_bp.route('/api/mex/test-in-game/start', methods=['POST'])
def start_test_in_game():
    """
    Start an in-game test (async, with SocketIO progress).

    Body:
    {
        "isoPath": "...",            // required: the exported ISO to test
        "slippiDolphinPath": "...",  // required: the user's Slippi Dolphin path
        "manifest": { ... },         // optional: what mods to drive (see runner)
        "manifestPath": "...",       // optional: a JSON file with the manifest
        "observeSeconds": 9,         // optional: in-game watch window per check
        "hiresTextures": false,      // optional: pre-seed + enable HD textures
        "loadSeed": "..."            // optional: a Load/Textures dir to pre-seed
    }
    """
    global _test_running

    if os.name != 'nt':
        return jsonify({'success': False,
                        'error': 'In-game testing is only supported on Windows.'}), 400

    data = request.json or {}
    iso_path = data.get('isoPath')
    slippi_path = data.get('slippiDolphinPath')

    if not iso_path or not os.path.exists(iso_path):
        return jsonify({'success': False,
                        'error': f'ISO not found: {iso_path}'}), 400
    if not slippi_path:
        return jsonify({'success': False,
                        'error': 'slippiDolphinPath is required (set the Slippi path in Settings).'}), 400

    manifest = _load_manifest(data)
    observe_seconds = int(data.get('observeSeconds', 9) or 9)
    hires_textures = bool(data.get('hiresTextures', False))
    load_seed = data.get('loadSeed')

    with _test_lock:
        if _test_running:
            return jsonify({'success': False,
                            'error': 'A test is already running. Please wait for it to finish.'}), 409
        _test_running = True

    runs_root = STORAGE_PATH / 'test-runs'
    runs_root.mkdir(parents=True, exist_ok=True)

    def test_with_progress():
        global _test_running
        socketio = get_socketio()

        def emit(stage, percentage, message):
            socketio.emit('test_progress', {
                'stage': stage, 'percentage': percentage, 'message': message,
            })

        try:
            # Imported lazily so the blueprint stays importable on non-Windows
            # dev machines (the engine binds kernel32 at import time).
            from ingame.runner import run_test

            emit('starting', 1, 'Starting in-game test…')
            result = run_test(
                iso_path=iso_path,
                slippi_path=slippi_path,
                runs_root=str(runs_root),
                manifest=manifest,
                emit=emit,
                log=lambda m: logger.info(f"[test-in-game] {m}"),
                observe_seconds=observe_seconds,
                hires_textures=hires_textures,
                load_seed=load_seed,
            )

            socketio.emit('test_complete', {
                'success': bool(result.get('pass')),
                'verdict': result.get('verdict'),
                'reason': result.get('reason'),
                'checks': result.get('checks', []),
                'screenshot': result.get('screenshot'),
                'drove': result.get('drove', []),
                'onlineAborted': result.get('online_aborted', False),
            })
            logger.info(f"[test-in-game] done: verdict={result.get('verdict')} pass={result.get('pass')}")
        except Exception as e:
            logger.exception("[test-in-game] failed")
            socketio.emit('test_error', {'success': False, 'error': str(e)})
        finally:
            with _test_lock:
                _test_running = False

    thread = threading.Thread(target=test_with_progress, daemon=True)
    thread.start()

    return jsonify({'success': True, 'message': 'In-game test started',
                    'mode': 'manifest' if manifest else 'boot-health'})


@test_in_game_bp.route('/api/mex/test-in-game/costume', methods=['POST'])
def start_costume_test():
    """
    Test ONE character costume in game: build a minimal temp ISO (vanilla + just
    this costume), boot it, select that character + costume, play a short match,
    and report PASS / CRASH with a screenshot. Streams the same SocketIO events
    as /start (test_progress / test_complete / test_error).

    Body:
    {
        "character": "Fox",          // required: storage character (display name)
        "skinId": "<id>",            // required: storage skin id
        "colorName": "...",          // optional: for the result label
        "vanillaIsoPath": "...",     // required: the user's vanilla Melee ISO
        "slippiDolphinPath": "...",  // required: the user's Slippi Dolphin path
        "observeSeconds": 9          // optional
    }
    """
    global _test_running

    if os.name != 'nt':
        return jsonify({'success': False,
                        'error': 'In-game testing is only supported on Windows.'}), 400

    data = request.json or {}
    character = data.get('character')
    skin_id = data.get('skinId')
    color_name = data.get('colorName') or ''
    vanilla_iso = data.get('vanillaIsoPath')
    slippi_path = data.get('slippiDolphinPath')
    observe_seconds = int(data.get('observeSeconds', 9) or 9)

    if not character or not skin_id:
        return jsonify({'success': False, 'error': 'character and skinId are required.'}), 400
    if not vanilla_iso or not os.path.exists(vanilla_iso):
        return jsonify({'success': False,
                        'error': f'Vanilla Melee ISO not found: {vanilla_iso}. Set it in Settings.'}), 400
    if not slippi_path:
        return jsonify({'success': False,
                        'error': 'slippiDolphinPath is required (set the Slippi path in Settings).'}), 400

    skin_zip = STORAGE_PATH / character / f"{skin_id}.zip"
    if not skin_zip.exists():
        return jsonify({'success': False,
                        'error': f'Costume archive not found: {skin_zip}'}), 400

    with _test_lock:
        if _test_running:
            return jsonify({'success': False,
                            'error': 'A test is already running. Please wait for it to finish.'}), 409
        _test_running = True

    runs_root = STORAGE_PATH / 'test-runs'
    runs_root.mkdir(parents=True, exist_ok=True)
    build_dir = STORAGE_PATH / 'test-builds'
    build_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_iso = build_dir / f'test_{character}_{stamp}.iso'.replace(' ', '_')

    def run():
        global _test_running
        socketio = get_socketio()

        def build_log(msg):
            socketio.emit('test_progress', {'stage': 'building', 'percentage': 6, 'message': msg})

        def build_progress(percentage, message):
            # export progress 0-100 -> 6-40% of the overall bar
            socketio.emit('test_progress', {
                'stage': 'building', 'percentage': 6 + int(percentage * 0.34), 'message': message,
            })

        def test_emit(stage, percentage, message):
            # in-game test 1-96 -> 40-100% of the overall bar
            socketio.emit('test_progress', {
                'stage': stage, 'percentage': 40 + int(percentage * 0.6), 'message': message,
            })

        try:
            from test_build import build_single_costume_iso
            from ingame.runner import run_test

            socketio.emit('test_progress', {'stage': 'building', 'percentage': 3,
                                            'message': 'Building a one-costume test ISO…'})
            index = build_single_costume_iso(
                vanilla_iso=vanilla_iso, character=character, skin_zip=str(skin_zip),
                out_iso=str(out_iso), progress_cb=build_progress, log=build_log,
            )

            manifest = {'costume': {'fighter': character, 'colorIndex': index,
                                    'name': color_name}}
            result = run_test(
                iso_path=str(out_iso), slippi_path=slippi_path, runs_root=str(runs_root),
                manifest=manifest, emit=test_emit,
                log=lambda m: logger.info(f"[test-in-game costume] {m}"),
                observe_seconds=observe_seconds,
            )

            socketio.emit('test_complete', {
                'success': bool(result.get('pass')),
                'verdict': result.get('verdict'),
                'reason': result.get('reason'),
                'checks': result.get('checks', []),
                'screenshot': result.get('screenshot'),
                'drove': result.get('drove', []),
                'onlineAborted': result.get('online_aborted', False),
                'costumeIndex': index,
                'character': character,
                'colorName': color_name,
            })
            logger.info(f"[test-in-game costume] done: {character} verdict={result.get('verdict')}")
        except Exception as e:
            logger.exception("[test-in-game costume] failed")
            socketio.emit('test_error', {'success': False, 'error': str(e)})
        finally:
            try:
                if out_iso.exists():
                    out_iso.unlink()
            except Exception:
                pass
            with _test_lock:
                _test_running = False

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'message': 'Costume test started'})


# --------------------------------------------------------------------------- #
# Shared build->test job for the single-mod testers (custom character / custom  #
# stage / stage skin). `build_callable(progress_cb, log)` builds the temp ISO   #
# at out_iso and returns (manifest, extra) -- the manifest tells the runner what #
# to drive, extra is merged into the test_complete payload.                     #
# --------------------------------------------------------------------------- #
def _common_inputs(data):
    vanilla = data.get('vanillaIsoPath')
    slippi = data.get('slippiDolphinPath')
    obs = int(data.get('observeSeconds', 9) or 9)
    if not vanilla or not os.path.exists(vanilla):
        return None, None, None, f'Vanilla Melee ISO not found: {vanilla}. Set it in Settings.'
    if not slippi:
        return None, None, None, 'slippiDolphinPath is required (set the Slippi path in Settings).'
    return vanilla, slippi, obs, None


def _start_build_test_job(out_iso, slippi_path, observe_seconds, build_callable):
    """Run a build->test job in a background thread (build the temp ISO, then
    drive it in-game), streaming the same SocketIO events as the costume test."""
    global _test_running
    runs_root = STORAGE_PATH / 'test-runs'
    runs_root.mkdir(parents=True, exist_ok=True)

    def run():
        global _test_running
        socketio = get_socketio()

        def build_log(msg):
            socketio.emit('test_progress', {'stage': 'building', 'percentage': 6, 'message': msg})

        def build_progress(percentage, message):
            socketio.emit('test_progress', {
                'stage': 'building', 'percentage': 6 + int(percentage * 0.34), 'message': message})

        def test_emit(stage, percentage, message):
            socketio.emit('test_progress', {
                'stage': stage, 'percentage': 40 + int(percentage * 0.6), 'message': message})

        try:
            from ingame.runner import run_test

            socketio.emit('test_progress', {'stage': 'building', 'percentage': 3,
                                            'message': 'Building a one-mod test ISO…'})
            manifest, extra = build_callable(build_progress, build_log)

            result = run_test(
                iso_path=str(out_iso), slippi_path=slippi_path, runs_root=str(runs_root),
                manifest=manifest, emit=test_emit,
                log=lambda m: logger.info(f"[test-in-game] {m}"),
                observe_seconds=observe_seconds,
            )
            payload = {
                'success': bool(result.get('pass')),
                'verdict': result.get('verdict'),
                'reason': result.get('reason'),
                'checks': result.get('checks', []),
                'screenshot': result.get('screenshot'),
                'drove': result.get('drove', []),
                'onlineAborted': result.get('online_aborted', False),
            }
            if extra:
                payload.update(extra)
            socketio.emit('test_complete', payload)
            logger.info(f"[test-in-game] done: verdict={result.get('verdict')} pass={result.get('pass')}")
        except Exception as e:
            logger.exception("[test-in-game] build/test failed")
            socketio.emit('test_error', {'success': False, 'error': str(e)})
        finally:
            try:
                if Path(out_iso).exists():
                    Path(out_iso).unlink()
            except Exception:
                pass
            with _test_lock:
                _test_running = False

    threading.Thread(target=run, daemon=True).start()


@test_in_game_bp.route('/api/mex/test-in-game/custom-character', methods=['POST'])
def start_custom_character_test():
    """Test ONE custom (m-ex) fighter in game: build a temp ISO with just that
    fighter (placed in the CSS grid), boot it, select it, play a short match.
    Body: { slug, name?, vanillaIsoPath, slippiDolphinPath, observeSeconds? }."""
    global _test_running
    if os.name != 'nt':
        return jsonify({'success': False, 'error': 'In-game testing is only supported on Windows.'}), 400
    data = request.json or {}
    slug = data.get('slug')
    if not slug:
        return jsonify({'success': False, 'error': 'slug is required.'}), 400
    vanilla, slippi, obs, err = _common_inputs(data)
    if err:
        return jsonify({'success': False, 'error': err}), 400

    with _test_lock:
        if _test_running:
            return jsonify({'success': False, 'error': 'A test is already running.'}), 409
        _test_running = True

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_iso = (STORAGE_PATH / 'test-builds' / f'test_char_{slug}_{stamp}.iso')

    def build(progress_cb, log):
        from test_build import build_custom_character_iso
        r = build_custom_character_iso(vanilla, slug, str(out_iso), progress_cb=progress_cb, log=log)
        return ({'character': {'name': r['name'], 'cssIcon': r['cssIcon']}},
                {'modName': r['name'], 'cssIcon': r['cssIcon']})

    _start_build_test_job(out_iso, slippi, obs, build)
    return jsonify({'success': True, 'message': 'Custom character test started'})


@test_in_game_bp.route('/api/mex/test-in-game/custom-stage', methods=['POST'])
def start_custom_stage_test():
    """Test ONE custom (m-ex) stage in game: build a temp ISO with just that stage
    (placed on the SSS), boot it, select it, play a short match.
    Body: { slug, name?, vanillaIsoPath, slippiDolphinPath, observeSeconds? }."""
    global _test_running
    if os.name != 'nt':
        return jsonify({'success': False, 'error': 'In-game testing is only supported on Windows.'}), 400
    data = request.json or {}
    slug = data.get('slug')
    if not slug:
        return jsonify({'success': False, 'error': 'slug is required.'}), 400
    vanilla, slippi, obs, err = _common_inputs(data)
    if err:
        return jsonify({'success': False, 'error': err}), 400

    with _test_lock:
        if _test_running:
            return jsonify({'success': False, 'error': 'A test is already running.'}), 409
        _test_running = True

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_iso = (STORAGE_PATH / 'test-builds' / f'test_stage_{slug}_{stamp}.iso')

    def build(progress_cb, log):
        from test_build import build_custom_stage_iso
        r = build_custom_stage_iso(vanilla, slug, str(out_iso), progress_cb=progress_cb, log=log)
        return ({'customStage': {'name': r['name'], 'sssIcon': r['sssIcon']}},
                {'modName': r['name'], 'sssIcon': r['sssIcon']})

    _start_build_test_job(out_iso, slippi, obs, build)
    return jsonify({'success': True, 'message': 'Custom stage test started'})


@test_in_game_bp.route('/api/mex/test-in-game/stage-skin', methods=['POST'])
def start_stage_skin_test():
    """Test ONE stage skin (DAS variant) in game: build a temp ISO with the DAS
    framework + that skin behind a hold button, boot it, select the base stage
    holding the button, play a short match.
    Body: { stageCode, stageFolder, variantId, name?, button?, vanillaIsoPath,
    slippiDolphinPath, observeSeconds? }."""
    global _test_running
    if os.name != 'nt':
        return jsonify({'success': False, 'error': 'In-game testing is only supported on Windows.'}), 400
    data = request.json or {}
    stage_code = data.get('stageCode')
    stage_folder = data.get('stageFolder')
    variant_id = data.get('variantId')
    button = (data.get('button') or 'X').upper()
    variant_name = data.get('name') or variant_id
    if not stage_code or not stage_folder or not variant_id:
        return jsonify({'success': False,
                        'error': 'stageCode, stageFolder and variantId are required.'}), 400
    vanilla, slippi, obs, err = _common_inputs(data)
    if err:
        return jsonify({'success': False, 'error': err}), 400

    with _test_lock:
        if _test_running:
            return jsonify({'success': False, 'error': 'A test is already running.'}), 409
        _test_running = True

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_iso = (STORAGE_PATH / 'test-builds' / f'test_skin_{stage_code}_{stamp}.iso')

    def build(progress_cb, log):
        from test_build import build_stage_skin_iso
        r = build_stage_skin_iso(vanilla, stage_code, stage_folder, variant_id, str(out_iso),
                                 button=button, progress_cb=progress_cb, log=log)
        return ({'das': {'stage': r['stage'], 'button': r['button']}},
                {'modName': variant_name, 'das': r})

    _start_build_test_job(out_iso, slippi, obs, build)
    return jsonify({'success': True, 'message': 'Stage skin test started'})


@test_in_game_bp.route('/api/mex/test-in-game/status', methods=['GET'])
def test_in_game_status():
    return jsonify({'success': True, 'running': _test_running})
