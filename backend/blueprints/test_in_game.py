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


@test_in_game_bp.before_request
def _guard_dolphin_already_open():
    """Every test-start endpoint launches its OWN throwaway Dolphin and drives it
    over a pipe. If the user already has a Slippi/Dolphin window open, the second
    one steals the foreground and the test just sits on the menu (never pressing a
    button) -- so refuse early with a clear message. Skipped for GETs (e.g.
    /status) and while a test is already running (the per-endpoint one-at-a-time
    guard answers that case, and our own harness Dolphin would be running)."""
    if request.method != 'POST' or os.name != 'nt' or _test_running:
        return None
    try:
        from ingame.boot import dolphin_running
        open_pids = dolphin_running()
    except Exception:
        return None
    if open_pids:
        return jsonify({
            'success': False,
            'dolphinOpen': True,
            'error': ('A Dolphin window is already open. Close any running Slippi '
                      'Dolphin first — the in-game test launches its own Dolphin, '
                      'and a second one steals focus so the test just sits on the '
                      'menu.'),
        }), 409
    return None


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

    def run():
        global _test_running
        socketio = get_socketio()

        def emit(stage, percentage, message):
            socketio.emit('capture_progress', {
                'stage': stage, 'percentage': percentage, 'message': message})

        results = []  # one entry per requested variant, in input order
        try:
            from test_build import build_stage_skin_multibatch_iso, BATCH_BUTTONS, DAS_STAGES
            from ingame.capture import capture_stage_batch
            from ingame.melee_sss import INTERNAL_STAGE_ID

            total = len(variants)

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

            # One ISO per ROUND packs up to BATCH_BUTTONS (6) variants of EACH base
            # stage (the DAS framework loads all six stages), so a whole selection
            # usually needs just ONE build + ONE boot -- a stage with >6 selected
            # spills into extra rounds. Far fewer ISOs than one-per-stage.
            chunk = max(1, len(BATCH_BUTTONS))
            rounds = max(((len(vs) + chunk - 1) // chunk for vs in groups.values()), default=0)
            shots_by_id = {}   # "<stageCode>:<variantId>" -> png

            for k in range(rounds):
                round_groups = []
                for (stage_code, stage_folder), vs in groups.items():
                    sub = vs[k * chunk:(k + 1) * chunk]
                    if sub:
                        round_groups.append({'stageCode': stage_code, 'stageFolder': stage_folder,
                                             'variantIds': [v['variantId'] for v in sub]})
                if not round_groups:
                    continue
                base = 4 + int(90 * k / max(1, rounds))
                n_round = sum(len(g['variantIds']) for g in round_groups)
                emit('building', base,
                     f'Building ISO {k + 1}/{rounds} ({n_round} variants across '
                     f'{len(round_groups)} stage{"s" if len(round_groups) != 1 else ""})…')
                out_iso = (STORAGE_PATH / 'test-builds'
                           / f'capbatch_{datetime.now().strftime("%Y%m%d_%H%M%S_%f")}.iso')
                try:
                    placed = build_stage_skin_multibatch_iso(
                        vanilla, round_groups, str(out_iso),
                        log=lambda m: logger.info(f"[capture-batch] {m}"))
                    cap_variants = []
                    for pv in placed:
                        stage_name = DAS_STAGES[pv['stageCode']][1]
                        cap_variants.append({
                            'id': f"{pv['stageCode']}:{pv['variantId']}",
                            'button': pv['button'],
                            'internal_id': INTERNAL_STAGE_ID.get(stage_name),
                            'framing_key': stage_name,
                        })
                    span = 90.0 / max(1, rounds)
                    res = capture_stage_batch(
                        str(out_iso), slippi, str(runs_root), cap_variants,
                        emit=lambda s, p, m: emit(s, base + int(span * (p / 100.0)), m),
                        log=lambda m: logger.info(f"[capture-batch] {m}"))
                    for shot in res.get('shots', []):
                        shots_by_id[shot['id']] = shot['png']
                except Exception:
                    logger.exception("[capture-batch] round failed")
                finally:
                    try:
                        if out_iso.exists():
                            out_iso.unlink()
                    except Exception:
                        pass

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
                    results.append({**_vmeta(v), 'ok': False, 'reason': 'capture failed'})

            ok_n = sum(1 for r in results if r.get('ok'))
            socketio.emit('capture_batch_complete', {
                'success': ok_n > 0, 'results': results,
                'captured': ok_n, 'total': total})
            logger.info(f"[capture-batch] done: {ok_n}/{total} captured")
        except Exception as e:
            logger.exception("[capture-batch] failed")
            socketio.emit('capture_error', {'success': False, 'error': str(e)})
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


@test_in_game_bp.route('/api/mex/test-in-game/status', methods=['GET'])
def test_in_game_status():
    return jsonify({'success': True, 'running': _test_running})
