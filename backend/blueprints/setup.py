"""
Setup Blueprint - First-run setup and auto-detection.

Handles first-run setup process, auto-detection of Slippi/ISO paths.
"""

import os
import hashlib
import threading
import configparser
import logging
from pathlib import Path
from flask import Blueprint, request, jsonify

from core.config import PROJECT_ROOT, MEXCLI_PATH
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


def find_vanilla_melee_iso(folder: str) -> str:
    """Scan a folder for a vanilla Melee 1.02 ISO.

    Checks .iso and .gcm files against the known MD5 hash.
    Returns the path to the first matching ISO found, or None.
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

    for iso_file in unique_files:
        try:
            # Check file size first (vanilla Melee is ~1.36GB)
            file_size = iso_file.stat().st_size
            if file_size != VANILLA_ISO_EXPECTED_SIZE:
                continue

            logger.info(f"Checking ISO: {iso_file}")

            verification = verify_iso_file(iso_file)
            if verification['valid']:
                logger.info(f"Found vanilla Melee ISO: {iso_file}")
                return str(iso_file)
        except Exception as e:
            logger.warning(f"Error checking ISO {iso_file}: {e}")
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

                    # 3. Scan folder for vanilla Melee ISO
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
