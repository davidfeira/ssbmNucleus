"""
Setup Blueprint - First-run setup and auto-detection.

Handles first-run setup process, auto-detection of Slippi/ISO paths.
"""

import io
import os
import sys
import zipfile
import platform
import hashlib
import threading
import configparser
import logging
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file

from core.config import PROJECT_ROOT, MEXCLI_PATH, LOGS_PATH
from core.constants import VANILLA_ISO_MD5
from core.state import get_socketio
from first_run_setup import FirstRunSetup

logger = logging.getLogger(__name__)

setup_bp = Blueprint('setup', __name__)

# Global state for setup process
_setup_in_progress = False
_setup_instance = None
_iso_verification_cache = {}


# Vanilla Melee 1.02 disc size in bytes.
VANILLA_ISO_EXPECTED_SIZE = 1459978240

# Cache a small number of recent ISO verifications so auto-detect and setup/start
# do not re-hash the same unchanged file back-to-back.
ISO_VERIFICATION_CACHE_LIMIT = 16


def _get_iso_cache_key(iso_path: str | Path) -> tuple[str, int, int, int]:
    """Build a cache key from the resolved path plus file metadata."""
    iso_file = Path(iso_path).resolve()
    stat = iso_file.stat()
    return (
        str(iso_file).lower(),
        stat.st_size,
        stat.st_mtime_ns,
        stat.st_ctime_ns,
    )


def clear_iso_verification_cache():
    """Clear the in-memory ISO verification cache."""
    _iso_verification_cache.clear()


def verify_iso_file(iso_path: str | Path) -> dict:
    """Verify a Melee ISO, reusing cached results when the file is unchanged."""
    iso_file = Path(iso_path).resolve()
    cache_key = _get_iso_cache_key(iso_file)
    cached_result = _iso_verification_cache.get(cache_key)
    if cached_result is not None:
        logger.info(f"Using cached ISO verification: {iso_file}")
        return {
            **cached_result,
            'cached': True
        }

    logger.info(f"Calculating MD5 for: {iso_file}")
    md5_hash = hashlib.md5()

    with open(iso_file, 'rb') as f:
        for chunk in iter(lambda: f.read(8192 * 1024), b''):
            md5_hash.update(chunk)

    calculated_md5 = md5_hash.hexdigest()
    result = {
        'valid': calculated_md5.lower() == VANILLA_ISO_MD5.lower(),
        'md5': calculated_md5,
        'expected': VANILLA_ISO_MD5
    }

    _iso_verification_cache[cache_key] = result
    while len(_iso_verification_cache) > ISO_VERIFICATION_CACHE_LIMIT:
        _iso_verification_cache.pop(next(iter(_iso_verification_cache)))

    return {
        **result,
        'cached': False
    }


def verify_slippi_structure(slippi_path: str) -> bool:
    """Verify that a path has the expected Slippi Dolphin structure."""
    slippi_dir = Path(slippi_path)
    user_dir = slippi_dir / 'User'

    # Must have a User folder
    if not user_dir.exists() or not user_dir.is_dir():
        return False

    # Should have Config folder (Dolphin creates this)
    config_dir = user_dir / 'Config'
    if not config_dir.exists():
        return False

    return True


def parse_dolphin_ini_iso_path(ini_path: str) -> str:
    """Parse Dolphin.ini to extract the ISO directory path.

    Looks for ISOPath0, ISOPath1, etc. or DefaultISO in the [General] section.
    Returns the first valid directory found.
    """
    try:
        # Dolphin.ini uses a Windows INI format
        config = configparser.ConfigParser()
        config.read(ini_path, encoding='utf-8')

        # Check [General] section for ISO paths
        if 'General' in config:
            general = config['General']

            # Try ISOPath0, ISOPath1, etc.
            for i in range(10):  # Check up to 10 paths
                key = f'ISOPath{i}'
                if key in general:
                    iso_dir = general[key]
                    if iso_dir and Path(iso_dir).is_dir():
                        logger.info(f"Found ISO directory from {key}: {iso_dir}")
                        return iso_dir

            # Also check DefaultISO (this is a file path, so get its directory)
            if 'DefaultISO' in general:
                default_iso = general['DefaultISO']
                if default_iso:
                    iso_dir = str(Path(default_iso).parent)
                    if Path(iso_dir).is_dir():
                        logger.info(f"Found ISO directory from DefaultISO: {iso_dir}")
                        return iso_dir

        return None
    except Exception as e:
        logger.warning(f"Error parsing Dolphin.ini: {e}")
        return None


# GameCube disc header: bytes 0x00-0x05 = 6-char game ID, byte 0x07 = disc
# version. Vanilla Melee NTSC 1.02 is "GALE01" with version byte 0x02.
MELEE_GAME_ID = b'GALE01'
MELEE_102_VERSION = 0x02


def _is_melee_102_header(iso_file: Path) -> bool:
    """Cheaply test a disc's 8-byte header for Melee NTSC 1.02 (GALE01 v1.02).

    Reads only 8 bytes, so it rejects unrelated GameCube ISOs before any
    full-file MD5. This matters because every uncompressed GC ISO shares the
    same disc size, so the size pre-filter alone never narrows the candidates.
    """
    try:
        with open(iso_file, 'rb') as f:
            header = f.read(8)
    except OSError:
        return False
    return (len(header) == 8
            and header[:6] == MELEE_GAME_ID
            and header[7] == MELEE_102_VERSION)


# Filename hints. Vanilla dumps are usually named plainly (Melee / SSBM /
# vanilla / 1.02); mod builds carry a tell in the name (20XX, m-ex, Akaneia,
# Ace, training, etc.). We can't tell vanilla from a mod by the disc header
# (both are GALE01 v1.02, same size), so we MD5 — but ordering candidates by
# these hints means the real vanilla is almost always hashed FIRST and we
# early-exit, instead of hashing a modded build (e.g. acebuild.iso) first.
_VANILLA_NAME_HINTS = ('vanilla', 'melee', 'ssbm', 'smashmelee', '1.02', 'v1.02',
                       'ntsc', 'gale01')
_MOD_NAME_HINTS = ('mod', 'ace', '20xx', 'mex', 'm-ex', 'akaneia', 'training',
                   'tournament', 'beyond', 'diet', 'widescreen', 'netplay',
                   'build', 'mango', 'uncle', 'hax', 'crazy', 'summit', 'slippi')


def _vanilla_name_score(iso_path: Path) -> int:
    """Higher = more likely to be the plain vanilla dump (hash it sooner)."""
    name = iso_path.stem.lower()
    score = 0
    if name in ('melee', 'vanilla', 'ssbm', 'ssbm melee', 'super smash bros melee'):
        score += 100
    for hint in _VANILLA_NAME_HINTS:
        if hint in name:
            score += 10
    for hint in _MOD_NAME_HINTS:
        if hint in name:
            score -= 25
    # plain/short names (e.g. "Melee.iso") lean vanilla; long descriptive names
    # are usually mods ("z20XX 4.05 Corona Beginnings").
    score -= len(name) // 12
    return score


def find_vanilla_melee_iso(folder: str, deep_verify: bool = True) -> str:
    """Scan a folder for a vanilla Melee 1.02 ISO.

    Filters to .iso/.gcm files matching the exact disc size + 8-byte GALE01 v1.02
    header, then — because a modded 1.02 build shares both — confirms by MD5.
    Candidates are tried in filename-likelihood order (`_vanilla_name_score`) so
    the genuine vanilla dump is normally the FIRST (and only) file hashed; we
    early-exit on the first MD5 match. Results are cached, so /setup/start's
    re-verify is then instant.

    ``deep_verify=False`` returns the best-named size+header candidate WITHOUT
    hashing (used only where a cheap guess is acceptable). Auto-detect uses the
    default (True): an earlier header-only shortcut wrongly picked a modded
    acebuild.iso because it can't be distinguished from vanilla without the MD5.
    """
    folder_path = Path(folder)
    if not folder_path.is_dir():
        return None

    # Look for ISO and GCM files
    iso_files = list(folder_path.glob('*.iso')) + list(folder_path.glob('*.gcm'))
    iso_files += list(folder_path.glob('*.ISO')) + list(folder_path.glob('*.GCM'))

    # Remove duplicates (case-insensitive systems)
    seen = set()
    unique_files = []
    for f in iso_files:
        lower_path = str(f).lower()
        if lower_path not in seen:
            seen.add(lower_path)
            unique_files.append(f)

    # First narrow to real Melee-1.02 candidates by the cheap size + 8-byte
    # header check (rejects other games / non-1.02 instantly). All uncompressed
    # GC ISOs share the disc size, so the header is what does the filtering.
    candidates = []
    for iso_file in unique_files:
        try:
            if iso_file.stat().st_size != VANILLA_ISO_EXPECTED_SIZE:
                continue
            if not _is_melee_102_header(iso_file):
                logger.info(f"Skipping non-Melee-1.02 ISO (header): {iso_file}")
                continue
            candidates.append(iso_file)
        except OSError as e:
            logger.warning(f"Error checking ISO {iso_file}: {e}")

    if not candidates:
        return None

    # A modded build (acebuild.iso, 20XX, …) has the SAME header + size as
    # vanilla, so hash to confirm — but try the most vanilla-looking name first
    # so the genuine dump is normally the only file hashed (early-exit below).
    candidates.sort(key=_vanilla_name_score, reverse=True)

    if not deep_verify:
        logger.info(f"Best-named vanilla candidate (no hash): {candidates[0]}")
        return str(candidates[0])

    for iso_file in candidates:
        try:
            logger.info(f"Checking ISO: {iso_file}")
            if verify_iso_file(iso_file)['valid']:
                logger.info(f"Found vanilla Melee ISO: {iso_file}")
                return str(iso_file)
            logger.info(f"Not vanilla (modded build?): {iso_file}")
        except Exception as e:
            logger.warning(f"Error hashing ISO {iso_file}: {e}")
            continue

    return None


@setup_bp.route('/api/mex/setup/status', methods=['GET'])
def check_setup_status():
    """Check if first-run setup is needed."""
    try:
        setup = FirstRunSetup(PROJECT_ROOT, MEXCLI_PATH)
        status = setup.check_setup_needed()
        logger.info(f"[Setup Status] complete={status.get('complete')}, reason={status.get('reason')}, details={status.get('details')}")
        return jsonify({
            'success': True,
            **status
        })
    except Exception as e:
        logger.error(f"Setup status check error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@setup_bp.route('/api/mex/setup/start', methods=['POST'])
def start_first_run_setup():
    """Start the first-run setup process."""
    global _setup_in_progress, _setup_instance

    if _setup_in_progress:
        return jsonify({
            'success': False,
            'error': 'Setup already in progress'
        }), 400

    try:
        data = request.json or {}
        iso_path = data.get('isoPath')

        if not iso_path:
            return jsonify({
                'success': False,
                'error': 'No ISO path provided'
            }), 400

        iso_file = Path(iso_path)
        if not iso_file.exists():
            return jsonify({
                'success': False,
                'error': 'ISO file not found'
            }), 404

        # Verify ISO hash first. This reuses the cached result from auto-detect
        # or /verify-iso when the file metadata has not changed.
        logger.info(f"Verifying ISO before setup: {iso_path}")
        verification = verify_iso_file(iso_file)
        if not verification['valid']:
            return jsonify({
                'success': False,
                'error': 'Invalid ISO file. Please provide a vanilla Melee 1.02 ISO.',
                'md5': verification['md5'],
                'expected': verification['expected']
            }), 400

        # Start setup in background thread
        _setup_in_progress = True
        _setup_instance = FirstRunSetup(PROJECT_ROOT, MEXCLI_PATH)
        socketio = get_socketio()

        def run_setup():
            global _setup_in_progress
            try:
                def progress_callback(phase, percentage, message, completed, total):
                    socketio.emit('setup_progress', {
                        'phase': phase,
                        'percentage': percentage,
                        'message': message,
                        'completed': completed,
                        'total': total
                    })

                result = _setup_instance.run_setup(iso_path, progress_callback)

                if result['success']:
                    socketio.emit('setup_complete', {
                        'success': True,
                        'message': result.get('message', 'Setup complete'),
                        'characters': result.get('characters', 0),
                        'stages': result.get('stages', 0),
                        'isoPath': iso_path
                    })
                else:
                    socketio.emit('setup_error', {
                        'error': result.get('error', 'Unknown error')
                    })
            except Exception as e:
                logger.error(f"Setup thread error: {e}", exc_info=True)
                socketio.emit('setup_error', {
                    'error': str(e)
                })
            finally:
                _setup_in_progress = False

        setup_thread = threading.Thread(target=run_setup, daemon=True)
        setup_thread.start()

        return jsonify({
            'success': True,
            'message': 'Setup started'
        })

    except Exception as e:
        _setup_in_progress = False
        logger.error(f"Start setup error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@setup_bp.route('/api/mex/setup/auto-detect', methods=['GET'])
def auto_detect_paths():
    """Auto-detect Slippi Dolphin path and vanilla Melee ISO."""
    result = {
        'slippiPath': None,
        'isoPath': None,
        'isoFolderPath': None
    }

    try:
        # 1. Check default Slippi path
        appdata = os.environ.get('APPDATA', '')
        if not appdata:
            # Fallback for non-Windows or missing APPDATA
            logger.info("APPDATA not found, cannot auto-detect Slippi path")
            return jsonify({'success': True, **result})

        default_slippi = os.path.join(appdata, 'Slippi Launcher', 'netplay')
        logger.info(f"Checking default Slippi path: {default_slippi}")

        if os.path.isdir(default_slippi):
            if verify_slippi_structure(default_slippi):
                result['slippiPath'] = default_slippi
                logger.info(f"Found valid Slippi installation: {default_slippi}")
            else:
                logger.info(f"Path exists but structure invalid: {default_slippi}")
        else:
            logger.info(f"Default Slippi path not found: {default_slippi}")

        # 2. Parse dolphin.ini for ISO path
        if result['slippiPath']:
            dolphin_ini = os.path.join(result['slippiPath'], 'User', 'Config', 'Dolphin.ini')
            logger.info(f"Checking Dolphin.ini: {dolphin_ini}")

            if os.path.isfile(dolphin_ini):
                iso_dir = parse_dolphin_ini_iso_path(dolphin_ini)
                if iso_dir:
                    result['isoFolderPath'] = iso_dir
                    logger.info(f"Found ISO folder: {iso_dir}")

                    # 3. Scan folder for the vanilla Melee ISO. Hash-confirmed
                    # (a modded build shares vanilla's header+size), but tried in
                    # filename-likelihood order so the real dump is normally the
                    # only file hashed — fast in the common case, correct always.
                    vanilla_iso = find_vanilla_melee_iso(iso_dir)
                    if vanilla_iso:
                        result['isoPath'] = vanilla_iso
                        logger.info(f"Found vanilla Melee ISO: {vanilla_iso}")
                    else:
                        logger.info(f"No vanilla Melee ISO found in: {iso_dir}")
                else:
                    logger.info("No ISO directory found in Dolphin.ini")
            else:
                logger.info(f"Dolphin.ini not found: {dolphin_ini}")

        return jsonify({'success': True, **result})

    except Exception as e:
        logger.error(f"Auto-detect error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@setup_bp.route('/api/mex/verify-iso', methods=['POST'])
def verify_vanilla_iso():
    """Verify that an ISO file is a valid vanilla Melee 1.02 ISO."""
    try:
        data = request.json or {}
        iso_path = data.get('isoPath')

        if not iso_path:
            return jsonify({
                'success': False,
                'error': 'No ISO path provided'
            }), 400

        iso_file = Path(iso_path)
        if not iso_file.exists():
            return jsonify({
                'success': False,
                'error': 'ISO file not found'
            }), 404

        verification = verify_iso_file(iso_file)
        logger.info(f"ISO MD5: {verification['md5']} (valid: {verification['valid']}, cached: {verification['cached']})")

        return jsonify({
            'success': True,
            'valid': verification['valid'],
            'md5': verification['md5'],
            'expected': verification['expected']
        })
    except Exception as e:
        logger.error(f"Verify ISO error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Caps so a logs zip can't balloon (Slippi crash .dmp files can be large, and the
# User tree also holds replays/ISOs we must NEVER sweep in).
_SLIPPI_LOG_MAX_FILE = 25 * 1024 * 1024     # 25 MB per file
_SLIPPI_LOG_MAX_TOTAL = 100 * 1024 * 1024   # 100 MB total


def _add_slippi_dolphin_logs(zf: zipfile.ZipFile, slippi_path: str) -> int:
    """Add the user's Slippi Dolphin logs + crash dumps to the zip under
    slippi-dolphin/. Only known log/dump locations are touched (Dolphin's Logs
    folder + .dmp/.log/.txt at known top levels) so we never pull in replays or
    ISOs. Size-capped. Returns the number of files added."""
    root = Path(slippi_path)
    if not root.is_dir():
        return 0
    user = root / 'User'
    added = 0
    total = 0

    def _add(p: Path, arc: str):
        nonlocal added, total
        try:
            sz = p.stat().st_size
        except OSError:
            return
        if sz > _SLIPPI_LOG_MAX_FILE or total + sz > _SLIPPI_LOG_MAX_TOTAL:
            return
        try:
            zf.write(p, arc)
        except OSError:
            return
        total += sz
        added += 1

    # Dolphin's Logs folder (recursive — small text logs).
    logs_dir = user / 'Logs'
    if logs_dir.is_dir():
        for p in sorted(logs_dir.rglob('*')):
            if p.is_file():
                _add(p, f"slippi-dolphin/Logs/{p.relative_to(logs_dir).as_posix()}")

    # Crash dumps / stray logs at known top levels (non-recursive so we don't
    # walk into Slippi/replays or Games/ISOs). Covers the netplay dir, its User
    # dir, and the Slippi Launcher dir above it.
    for base, prefix in ((root, 'netplay'), (user, 'User'), (root.parent, 'launcher')):
        if base.is_dir():
            for p in sorted(base.iterdir()):
                if p.is_file() and p.suffix.lower() in ('.dmp', '.log', '.txt'):
                    _add(p, f"slippi-dolphin/{prefix}/{p.name}")

    return added


def _build_diagnostics_text(slippi_path: str = '', app_logs: int = 0,
                            slippi_logs: int = 0) -> str:
    """A short system summary bundled alongside the logs so a bug report has
    context (app paths, OS, python, what was gathered) without the user having
    to describe it."""
    lines = [
        'SSBM Nucleus diagnostics',
        f'Generated: {datetime.now().isoformat()}',
        f'Platform: {platform.platform()}',
        f'Python: {sys.version.split()[0]}',
        f'Frozen build: {bool(getattr(sys, "frozen", False))}',
        f'Project root: {PROJECT_ROOT}',
        f'Logs path: {LOGS_PATH}',
        f'App log files: {app_logs}',
        f'Slippi Dolphin path: {slippi_path or "(not provided)"}',
        f'Slippi log/dump files: {slippi_logs}',
    ]
    return '\n'.join(lines) + '\n'


@setup_bp.route('/api/mex/logs/download', methods=['GET'])
def download_logs_zip():
    """Bundle the app's log files into a single zip the user can attach to a bug
    report. Built in-memory and streamed as a timestamped download. Includes a
    diagnostics.txt with basic system info. Safe even if the logs folder is empty
    (the zip still carries the diagnostics).

    If a `slippiPath` query param is given (the user's Slippi Dolphin folder), the
    zip also gathers Slippi Dolphin's own logs + crash dumps under slippi-dolphin/
    — so a crash playing a Nucleus-built ISO in their Slippi Dolphin is debuggable
    too, not just issues inside our app."""
    try:
        slippi_path = (request.args.get('slippiPath') or '').strip()
        buf = io.BytesIO()
        added = 0
        slippi_added = 0
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            if LOGS_PATH.is_dir():
                for log_file in sorted(LOGS_PATH.rglob('*')):
                    if log_file.is_file():
                        try:
                            zf.write(log_file, f'logs/{log_file.relative_to(LOGS_PATH).as_posix()}')
                            added += 1
                        except OSError as e:
                            logger.warning(f"Could not add log to zip: {log_file} ({e})")
            if slippi_path:
                slippi_added = _add_slippi_dolphin_logs(zf, slippi_path)
            # diagnostics written last so it can report what was gathered
            zf.writestr('diagnostics.txt',
                        _build_diagnostics_text(slippi_path, added, slippi_added))
        buf.seek(0)
        name = f"nucleus-logs-{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        logger.info(f"Built logs zip '{name}' ({added} app log(s), {slippi_added} Slippi log(s))")
        return send_file(buf, mimetype='application/zip',
                         as_attachment=True, download_name=name)
    except Exception as e:
        logger.error(f"Logs zip error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
