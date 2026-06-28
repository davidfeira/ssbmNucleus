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

import base64
import json
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

from flask import Blueprint, request, jsonify

from core.config import STORAGE_PATH
from core.metadata import load_metadata
from core.state import get_socketio

logger = logging.getLogger(__name__)

test_in_game_bp = Blueprint('test_in_game', __name__)

# One test at a time: two Dolphins would fight over the screen + pipe.
_test_lock = threading.Lock()
_test_running = False

# In a bulk capture, if a packed ISO's boot leaves shots missing (Dolphin
# crashed/hung), reboot the SAME ISO this many more times before giving up.
# We never rebuild a per-variant ISO — that was slow and is what the user hated.
MAX_DOLPHIN_RETRIES = 2


def try_acquire_test_slot():
    """Non-blocking claim of the one-Dolphin-at-a-time slot. Returns True if
    claimed; caller must release_test_slot() when done. Used by background
    jobs (screenshot backfill) so they never fight a user-started test."""
    global _test_running
    with _test_lock:
        if _test_running:
            return False
        _test_running = True
        return True


def release_test_slot():
    global _test_running
    with _test_lock:
        _test_running = False


# NOTE: an already-open user Dolphin no longer 409s test starts here — the
# engine (runner.run_test / capture_*) WAITS for the user to close it, telling
# them why via the progress channel, then continues automatically.


def _paired_nana_zip(character, skin_id):
    """The paired Nana zip path (str) for an Ice Climbers Popo skin, or None.
    Mirrors the frontend's pairing (useCostumes.js): the selected skin's
    `paired_nana_id` names a hidden Nana skin entry whose zip lives in storage."""
    try:
        chars = (load_metadata() or {}).get('characters', {})
        skin = next((s for s in chars.get(character, {}).get('skins', [])
                     if s.get('id') == skin_id), None)
        pair_id = (skin or {}).get('paired_nana_id')
        if not pair_id:
            return None
        for char_name, char_data in chars.items():
            nana = next((s for s in char_data.get('skins', [])
                         if s.get('id') == pair_id), None)
            if nana and nana.get('filename'):
                return str(STORAGE_PATH / char_name / nana['filename'])
        logger.warning(f"paired Nana skin {pair_id} not found in storage metadata")
    except Exception:
        logger.warning("could not resolve a paired Nana costume", exc_info=True)
    return None


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

    # Ice Climbers skins are a Popo/Nana PAIR of zips linked in the storage
    # metadata; importing only the selected (Popo) zip would leave Nana vanilla
    # in the test ISO. Resolve the paired Nana zip so the build installs both.
    nana_zip = _paired_nana_zip(character, skin_id)

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
                out_iso=str(out_iso), nana_zip=nana_zip,
                progress_cb=build_progress, log=build_log,
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


@test_in_game_bp.route('/api/mex/test-in-game/custom-character-skin', methods=['POST'])
def start_custom_character_skin_test():
    """Test ONE specific skin of a custom (m-ex) fighter in game: build a temp
    ISO with that fighter, import the chosen vault custom skin onto it (or pick a
    bundled costume slot), select that exact costume on the CSS, play a short
    match. Body: { slug, skinId? | costumeIndex?, colorName?, vanillaIsoPath,
    slippiDolphinPath, observeSeconds? }."""
    global _test_running
    if os.name != 'nt':
        return jsonify({'success': False, 'error': 'In-game testing is only supported on Windows.'}), 400
    data = request.json or {}
    slug = data.get('slug')
    skin_id = data.get('skinId')
    costume_index = data.get('costumeIndex')
    color_name = data.get('colorName') or ''
    if not slug:
        return jsonify({'success': False, 'error': 'slug is required.'}), 400
    if not skin_id and costume_index is None:
        return jsonify({'success': False, 'error': 'skinId or costumeIndex is required.'}), 400
    vanilla, slippi, obs, err = _common_inputs(data)
    if err:
        return jsonify({'success': False, 'error': err}), 400

    skin_zip = None
    if skin_id:
        skin_zip = STORAGE_PATH / 'custom_characters' / slug / 'skins' / f'{skin_id}.zip'
        if not skin_zip.exists():
            return jsonify({'success': False,
                            'error': f'Custom skin archive not found: {skin_zip}'}), 400

    with _test_lock:
        if _test_running:
            return jsonify({'success': False, 'error': 'A test is already running.'}), 409
        _test_running = True

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_iso = (STORAGE_PATH / 'test-builds' / f'test_charskin_{slug}_{stamp}.iso')

    def build(progress_cb, log):
        from test_build import build_custom_character_iso
        r = build_custom_character_iso(
            vanilla, slug, str(out_iso),
            skin_zip=str(skin_zip) if skin_zip else None,
            costume_index=int(costume_index) if costume_index is not None else None,
            progress_cb=progress_cb, log=log)
        mod_name = f"{r['name']} — {color_name}" if color_name else r['name']
        return ({'character': {'name': r['name'], 'cssIcon': r['cssIcon'],
                               'colorIndex': r['colorIndex']}},
                {'modName': mod_name, 'cssIcon': r['cssIcon'],
                 'colorIndex': r['colorIndex']})

    _start_build_test_job(out_iso, slippi, obs, build)
    return jsonify({'success': True, 'message': 'Custom character skin test started'})


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


@test_in_game_bp.route('/api/mex/test-in-game/capture-stage-screenshot', methods=['POST'])
def start_capture_stage_screenshot():
    """Capture a clean in-game SCREENSHOT of a DAS stage variant (like a CSP for a
    stage) and save it as the variant's preview. Builds the one-skin ISO, boots it
    in the throwaway Dolphin, loads the stage ALONE (1-player, no timer) with the
    DAS button held, poses a deterministic whole-stage camera, and grabs the
    frame. The image is RETURNED (not saved) so the user can review it and choose
    whether to replace the variant's current screenshot (the frontend then saves
    via /storage/stages/update-screenshot). Streams capture_progress /
    capture_complete (with the image) / capture_error over SocketIO.
    Body: { stageCode, stageFolder, variantId, button?, vanillaIsoPath,
    slippiDolphinPath }."""
    global _test_running
    if os.name != 'nt':
        return jsonify({'success': False,
                        'error': 'In-game capture is only supported on Windows.'}), 400
    data = request.json or {}
    stage_code = data.get('stageCode')
    stage_folder = data.get('stageFolder')
    variant_id = data.get('variantId')
    button = (data.get('button') or 'X').upper()
    if not stage_code or not stage_folder or not variant_id:
        return jsonify({'success': False,
                        'error': 'stageCode, stageFolder and variantId are required.'}), 400
    vanilla, slippi, _obs, err = _common_inputs(data)
    if err:
        return jsonify({'success': False, 'error': err}), 400

    with _test_lock:
        if _test_running:
            return jsonify({'success': False, 'error': 'A test is already running.'}), 409
        _test_running = True

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_iso = (STORAGE_PATH / 'test-builds' / f'cap_{stage_code}_{stamp}.iso')
    runs_root = STORAGE_PATH / 'test-runs'
    runs_root.mkdir(parents=True, exist_ok=True)

    def run():
        global _test_running
        socketio = get_socketio()

        def emit(stage, percentage, message):
            socketio.emit('capture_progress', {
                'stage': stage, 'percentage': percentage, 'message': message})

        try:
            from test_build import build_stage_skin_iso
            from ingame.capture import capture_stage
            from ingame.melee_sss import INTERNAL_STAGE_ID

            emit('building', 3, 'Building a one-skin test ISO…')
            r = build_stage_skin_iso(
                vanilla, stage_code, stage_folder, variant_id, str(out_iso),
                button=button,
                progress_cb=lambda p, m: emit('building', 6 + int(p * 0.30), m),
                log=lambda m: logger.info(f"[capture] {m}"))

            stage_name = r['stage']
            internal_id = INTERNAL_STAGE_ID.get(stage_name)
            res = capture_stage(
                str(out_iso), slippi, str(runs_root),
                internal_id=internal_id, hold=r['button'], framing_key=stage_name,
                emit=lambda s, p, m: emit(s, 40 + int(p * 0.6), m),
                log=lambda m: logger.info(f"[capture] {m}"))

            if not res.get('ok') or not res.get('png'):
                socketio.emit('capture_error', {
                    'success': False,
                    'error': res.get('reason') or 'screenshot capture failed'})
                return

            # Don't save yet -- hand the captured image back so the user can review
            # it and choose whether to replace the variant's current screenshot.
            data_uri = "data:image/png;base64," + base64.b64encode(res['png']).decode('ascii')
            socketio.emit('capture_complete', {
                'success': True, 'screenshot': data_uri,
                'stageFolder': stage_folder, 'variantId': variant_id})
            logger.info(f"[capture] captured {stage_folder}/{variant_id} (awaiting replace confirmation)")
        except Exception as e:
            logger.exception("[capture] failed")
            socketio.emit('capture_error', {'success': False, 'error': str(e)})
        finally:
            try:
                if out_iso.exists():
                    out_iso.unlink()
            except Exception:
                pass
            with _test_lock:
                _test_running = False

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'message': 'Stage screenshot capture started'})


@test_in_game_bp.route('/api/mex/test-in-game/capture-pause-screenshot', methods=['POST'])
def start_capture_pause_screenshot():
    """Capture a LIVE in-game screenshot of a pause screen mod. Builds a
    vanilla+mod ISO (the mod applied to GmPause.usd), boots it in the throwaway
    Dolphin, loads Battlefield alone (invisible fighter, no timer), PAUSES the
    match, and grabs the pause overlay. The shot is saved as the mod's preview
    screenshot and also returned in capture_complete. Streams capture_progress /
    capture_complete / capture_error over SocketIO.
    Body: { modId, vanillaIsoPath, slippiDolphinPath }."""
    global _test_running
    if os.name != 'nt':
        return jsonify({'success': False,
                        'error': 'In-game capture is only supported on Windows.'}), 400
    data = request.json or {}
    mod_id = data.get('modId')
    if not mod_id:
        return jsonify({'success': False, 'error': 'modId is required.'}), 400
    vanilla, slippi, _obs, err = _common_inputs(data)
    if err:
        return jsonify({'success': False, 'error': err}), 400

    with _test_lock:
        if _test_running:
            return jsonify({'success': False, 'error': 'A test is already running.'}), 409
        _test_running = True

    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_iso = (STORAGE_PATH / 'test-builds' / f'cap_pause_{stamp}.iso')
    runs_root = STORAGE_PATH / 'test-runs'
    runs_root.mkdir(parents=True, exist_ok=True)

    def run():
        global _test_running
        socketio = get_socketio()

        def emit(stage, percentage, message):
            socketio.emit('capture_progress', {
                'stage': stage, 'percentage': percentage, 'message': message})

        try:
            from test_build import build_pause_mod_iso
            from ingame.capture import capture_pause
            from blueprints.menus.pause import set_mod_screenshot

            emit('building', 3, 'Building a test ISO with the pause mod…')
            build_pause_mod_iso(
                vanilla, mod_id, str(out_iso),
                progress_cb=lambda p, m: emit('building', 6 + int(p * 0.30), m),
                log=lambda m: logger.info(f"[capture] {m}"))

            res = capture_pause(
                str(out_iso), slippi, str(runs_root),
                emit=lambda s, p, m: emit(s, 40 + int(p * 0.6), m),
                log=lambda m: logger.info(f"[capture] {m}"))

            if not res.get('ok') or not res.get('png'):
                socketio.emit('capture_error', {
                    'success': False,
                    'error': res.get('reason') or 'screenshot capture failed'})
                return

            # The live pause shot IS the mod's best preview -- save it directly.
            set_mod_screenshot(mod_id, res['png'])
            data_uri = "data:image/png;base64," + base64.b64encode(res['png']).decode('ascii')
            socketio.emit('capture_complete', {
                'success': True, 'screenshot': data_uri, 'modId': mod_id})
            logger.info(f"[capture] captured pause screenshot for mod {mod_id}")
        except Exception as e:
            logger.exception("[capture] pause capture failed")
            socketio.emit('capture_error', {'success': False, 'error': str(e)})
        finally:
            try:
                if out_iso.exists():
                    out_iso.unlink()
            except Exception:
                pass
            with _test_lock:
                _test_running = False

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'message': 'Pause screenshot capture started'})


@test_in_game_bp.route('/api/mex/test-in-game/capture-stage-batch', methods=['POST'])
def start_capture_stage_batch():
    """BULK-capture clean in-game screenshots for many DAS variants at once. The
    selected variants are grouped by base stage and packed up to BATCH_BUTTONS
    (=4) per ISO, each behind its own HOLD button, so a single boot screenshots
    them all -- far fewer builds/boots than one ISO per variant. Images are
    RETURNED (not saved); the frontend shows a review grid and the user saves the
    ones they want via /storage/stages/update-screenshot. Streams capture_progress
    and a final capture_batch_complete carrying every result (with image or an
    error per variant); capture_error only on a fatal failure.
    Body: { variants: [{stageCode, stageFolder, variantId, name}], vanillaIsoPath,
    slippiDolphinPath }."""
    global _test_running
    if os.name != 'nt':
        return jsonify({'success': False,
                        'error': 'In-game capture is only supported on Windows.'}), 400
    data = request.json or {}
    variants = data.get('variants') or []
    variants = [v for v in variants
                if v.get('stageCode') and v.get('stageFolder') and v.get('variantId')]
    if not variants:
        return jsonify({'success': False, 'error': 'No valid variants selected.'}), 400
    vanilla, slippi, _obs, err = _common_inputs(data)
    if err:
        return jsonify({'success': False, 'error': err}), 400

    with _test_lock:
        if _test_running:
            return jsonify({'success': False, 'error': 'A test is already running.'}), 409
        _test_running = True

    runs_root = STORAGE_PATH / 'test-runs'
    runs_root.mkdir(parents=True, exist_ok=True)
    # Round ISOs are written here; ensure it exists or the very first build fails.
    (STORAGE_PATH / 'test-builds').mkdir(parents=True, exist_ok=True)

    def run():
        global _test_running
        socketio = get_socketio()

        def emit(stage, percentage, message):
            socketio.emit('capture_progress', {
                'stage': stage, 'percentage': percentage, 'message': message})

        results = []  # one entry per requested variant, in input order
        capture_log = []
        failure_attempts = []
        try:
            from test_build import build_stage_skin_multibatch_iso, BATCH_BUTTONS, DAS_STAGES
            from ingame.capture import capture_stage_batch
            from ingame.melee_sss import INTERNAL_STAGE_ID

            total = len(variants)
            missing_reason_by_id = {}
            max_log_lines = 300
            # A background build and the foreground capture both log now, so
            # guard the shared list (append + trim) against interleaving.
            log_guard = threading.Lock()

            def record_log(message):
                line = str(message or '').strip()
                if not line:
                    return
                logger.info("[capture-batch] %s", line)
                with log_guard:
                    capture_log.append(line[:500])
                    if len(capture_log) > max_log_lines:
                        del capture_log[:len(capture_log) - max_log_lines]

            def capture_id(stage_code, variant_id):
                return f"{stage_code}:{variant_id}"

            def group_ids(stage_groups):
                ids = []
                for g in stage_groups:
                    ids.extend(capture_id(g['stageCode'], vid)
                               for vid in g.get('variantIds', []))
                return ids

            def remember_missing(ids, reason):
                reason = reason or 'capture failed'
                for cid in ids:
                    if cid not in shots_by_id:
                        missing_reason_by_id[cid] = reason

            def log_tail(start, limit=28):
                return capture_log[start:][-limit:]

            def note_failed_attempt(label, ids, reason, log_start):
                failure_attempts.append({
                    'attempt': label,
                    'variantIds': ids,
                    'reason': reason or 'capture failed',
                    'log': log_tail(log_start),
                })

            shots_by_id = {}   # "<stageCode>:<variantId>" -> png

            def build_round_iso(round_groups, label):
                """Build ONE multibatch ISO for a round. Returns a dict with the
                ISO path + placement info, or {'error': ...}. Safe to run in a
                background thread (writes a uniquely-named ISO, no shared state
                except append-only logging)."""
                ids = group_ids(round_groups)
                out_iso = (STORAGE_PATH / 'test-builds'
                           / f'capbatch_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}.iso')
                try:
                    record_log(f"== {label}: building {len(ids)} variant(s) ==")
                    placed = build_stage_skin_multibatch_iso(
                        vanilla, round_groups, str(out_iso), log=record_log)
                    placed_ids = [capture_id(p['stageCode'], p['variantId']) for p in placed]
                    skipped_ids = [cid for cid in ids if cid not in placed_ids]
                    return {'iso': out_iso, 'placed': placed, 'placed_ids': placed_ids,
                            'skipped_ids': skipped_ids, 'ids': ids}
                except Exception as e:
                    reason = f"{type(e).__name__}: {e}"
                    logger.exception("[capture-batch] %s build failed", label)
                    record_log(f"{label}: build failed: {reason}")
                    try:
                        if out_iso.exists():
                            out_iso.unlink()
                    except Exception:
                        pass
                    return {'error': reason, 'ids': ids, 'iso': None}

            def capture_round(build, label, base, span):
                """Capture every placed variant from an ALREADY-BUILT ISO. If
                some shots are missing (Dolphin crashed/hung), reboot the SAME
                ISO up to MAX_DOLPHIN_RETRIES more times — we never rebuild a
                per-variant ISO. A variant that crashes Dolphin is moved to the
                end of the next boot so it can't block the ones queued behind
                it. Whatever is still missing after the retries is reported, so
                the user always gets what we did capture."""
                log_start = len(capture_log)
                if build.get('error'):
                    remember_missing(build['ids'], build['error'])
                    note_failed_attempt(label, build['ids'], build['error'], log_start)
                    return
                if build['skipped_ids']:
                    remember_missing(build['skipped_ids'], 'variant was not placed into the ISO')
                    record_log(f"{label}: {len(build['skipped_ids'])} variant(s) were not placed")
                if not build['placed_ids']:
                    remember_missing(build['ids'], 'no variants were placed into the ISO')
                    note_failed_attempt(label, build['ids'], 'no variants were placed into the ISO', log_start)
                    return

                out_iso = build['iso']
                cap_all = []
                for pv in build['placed']:
                    stage_name = DAS_STAGES[pv['stageCode']][1]
                    cap_all.append({
                        'id': capture_id(pv['stageCode'], pv['variantId']),
                        'button': pv['button'],
                        'internal_id': INTERNAL_STAGE_ID.get(stage_name),
                        'framing_key': stage_name,
                    })

                try:
                    crasher = None  # id that took Dolphin down last boot
                    attempts = MAX_DOLPHIN_RETRIES + 1
                    last_reason = ''
                    for attempt in range(attempts):
                        missing = [c for c in cap_all if c['id'] not in shots_by_id]
                        if not missing:
                            break
                        # Move a known crasher to the end so it can't stall the rest.
                        if crasher:
                            missing.sort(key=lambda c: c['id'] == crasher)
                        tag = '' if attempt == 0 else f' (retry {attempt}/{MAX_DOLPHIN_RETRIES})'
                        emit('capturing', base,
                             f'{label}{tag}: booting Dolphin ({len(missing)} variant(s))…')
                        record_log(f"{label}{tag}: capturing {len(missing)} variant(s) from the same ISO")
                        res = capture_stage_batch(
                            str(out_iso), slippi, str(runs_root), missing,
                            emit=lambda s, p, m: emit(s, base + int(span * (p / 100.0)), m),
                            log=record_log)
                        for shot in res.get('shots', []):
                            if shot.get('png'):
                                shots_by_id[shot['id']] = shot['png']
                        crasher = res.get('crashed_id')
                        last_reason = res.get('reason') or last_reason
                        still = [c['id'] for c in cap_all if c['id'] not in shots_by_id]
                        if not still:
                            record_log(f"{label}: captured all {len(cap_all)} placed variant(s)")
                            break
                        record_log(f"{label}{tag}: still missing {len(still)} of {len(cap_all)}")
                        if attempt == attempts - 1:
                            remember_missing(still, last_reason or 'capture failed')
                            for failure in res.get('failures', []):
                                fid = failure.get('id')
                                if fid:
                                    remember_missing([fid], failure.get('reason') or last_reason)
                            note_failed_attempt(label, still, last_reason, log_start)
                finally:
                    try:
                        if out_iso and out_iso.exists():
                            out_iso.unlink()
                    except Exception:
                        pass

            # Group by base stage (preserve input order within each).
            groups = {}
            for v in variants:
                groups.setdefault((v['stageCode'], v['stageFolder']), []).append(v)
            # Set aside variants on stages we can't drive.
            unknown = set()
            for key in list(groups):
                if key[0] not in DAS_STAGES:
                    for v in groups.pop(key):
                        unknown.add((v['stageCode'], v['variantId']))

            # One ISO per ROUND packs up to BATCH_BUTTONS variants of EACH base
            # stage (the DAS framework loads all six stages), so a whole selection
            # usually needs just ONE build + ONE boot -- a stage with >BATCH_BUTTONS
            # selected spills into extra rounds.
            chunk = max(1, len(BATCH_BUTTONS))
            round_specs = []
            for k in range(max(((len(vs) + chunk - 1) // chunk for vs in groups.values()), default=0)):
                round_groups = []
                for (stage_code, stage_folder), vs in groups.items():
                    sub = vs[k * chunk:(k + 1) * chunk]
                    if sub:
                        round_groups.append({'stageCode': stage_code, 'stageFolder': stage_folder,
                                             'variantIds': [v['variantId'] for v in sub]})
                if round_groups:
                    round_specs.append(round_groups)

            rounds = len(round_specs)
            span = 90.0 / max(1, rounds)
            # Pipeline: build the NEXT round's ISO in the background while the
            # current round is being screenshotted in Dolphin (build = CPU/disk,
            # capture = the GPU/Dolphin, so they don't contend). A single worker
            # keeps builds from overlapping each other.
            with ThreadPoolExecutor(max_workers=1) as build_pool:
                def _label(k):
                    return f"round {k + 1}/{rounds}"
                next_future = build_pool.submit(build_round_iso, round_specs[0], _label(0)) if rounds else None
                for k in range(rounds):
                    base = 4 + int(90 * k / max(1, rounds))
                    n_round = sum(len(g['variantIds']) for g in round_specs[k])
                    emit('building', base,
                         f'Round {k + 1}/{rounds} ({n_round} variants across '
                         f'{len(round_specs[k])} stage{"s" if len(round_specs[k]) != 1 else ""})…')
                    try:
                        build = next_future.result()
                    except Exception as e:  # belt-and-suspenders; build_round_iso catches its own
                        build = {'error': f"{type(e).__name__}: {e}",
                                 'ids': group_ids(round_specs[k]), 'iso': None}
                    # Kick off the next build now so it overlaps this capture.
                    next_future = (build_pool.submit(build_round_iso, round_specs[k + 1], _label(k + 1))
                                   if k + 1 < rounds else None)
                    try:
                        capture_round(build, _label(k), base, span)
                    except Exception:
                        logger.exception("[capture-batch] %s capture crashed", _label(k))
                        record_log(f"{_label(k)}: capture crashed; continuing with partial results")

            # Assemble a result for every requested variant, in input order.
            for v in variants:
                if (v['stageCode'], v['variantId']) in unknown:
                    results.append({**_vmeta(v), 'ok': False, 'reason': 'unsupported stage'})
                    continue
                png = shots_by_id.get(f"{v['stageCode']}:{v['variantId']}")
                if png:
                    results.append({**_vmeta(v), 'ok': True,
                                    'screenshot': "data:image/png;base64,"
                                    + base64.b64encode(png).decode('ascii')})
                else:
                    cid = f"{v['stageCode']}:{v['variantId']}"
                    results.append({**_vmeta(v), 'ok': False,
                                    'reason': missing_reason_by_id.get(cid) or 'capture failed'})

            ok_n = sum(1 for r in results if r.get('ok'))
            failures = [r for r in results if not r.get('ok')]
            socketio.emit('capture_batch_complete', {
                'success': ok_n > 0, 'results': results,
                'captured': ok_n, 'total': total,
                'failures': failures,
                'attempts': failure_attempts[-20:],
                'log': capture_log[-max_log_lines:]})
            logger.info("[capture-batch] done: %s/%s captured", ok_n, total)
        except Exception as e:
            logger.exception("[capture-batch] failed")
            socketio.emit('capture_error', {
                'success': False, 'error': str(e),
                'attempts': failure_attempts[-20:],
                'log': capture_log[-300:],
            })
        finally:
            with _test_lock:
                _test_running = False

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'message': 'Bulk stage screenshot capture started',
                    'count': len(variants)})


def _vmeta(v):
    """The identity fields echoed back for each variant in a batch result."""
    return {'stageCode': v.get('stageCode'), 'stageFolder': v.get('stageFolder'),
            'variantId': v.get('variantId'), 'name': v.get('name')}


@test_in_game_bp.route('/api/mex/test-in-game/window/position', methods=['POST'])
def position_test_window():
    """Pin the running test's Dolphin render window over the frontend's
    placeholder (ingame/embed.py): borderless, always-on-top, never activated.
    Body: { x, y, width, height } in PHYSICAL screen pixels. Returns
    found=false until Dolphin's render window exists -- the frontend keeps
    polling through the build/boot phase."""
    if os.name != 'nt':
        return jsonify({'success': False, 'found': False,
                        'error': 'Window embedding is only supported on Windows.'}), 400
    data = request.json or {}
    try:
        x, y = int(data['x']), int(data['y'])
        w, h = int(data['width']), int(data['height'])
    except (KeyError, TypeError, ValueError):
        return jsonify({'success': False, 'found': False,
                        'error': 'x, y, width and height (integers) are required.'}), 400
    from ingame import embed
    return jsonify({'success': True, **embed.position(x, y, w, h)})


@test_in_game_bp.route('/api/mex/test-in-game/window/park', methods=['POST'])
def park_test_window():
    """Move the test Dolphin's render window offscreen (the placeholder is
    hidden or the panel unmounted). Best-effort; no-op when nothing is active."""
    if os.name != 'nt':
        return jsonify({'success': True, 'found': False})
    from ingame import embed
    return jsonify({'success': True, **embed.park()})


@test_in_game_bp.route('/api/mex/test-in-game/status', methods=['GET'])
def test_in_game_status():
    return jsonify({'success': True, 'running': _test_running})
