"""
Settings Blueprint - User-configurable application settings.

Handles reading and writing persistent settings (user_settings.json),
including the custom vault storage path and vault file migration.
"""

import json
import shutil
import logging
from pathlib import Path
from flask import Blueprint, request, jsonify

from core.config import STORAGE_PATH, USER_SETTINGS_PATH

logger = logging.getLogger(__name__)

settings_bp = Blueprint('settings', __name__)


def _read_user_settings() -> dict:
    """Read user_settings.json, returning empty dict on any error."""
    if USER_SETTINGS_PATH.exists():
        try:
            return json.loads(USER_SETTINGS_PATH.read_text())
        except Exception:
            pass
    return {}


def _write_user_settings(data: dict) -> None:
    """Write data to user_settings.json."""
    USER_SETTINGS_PATH.write_text(json.dumps(data, indent=2))


@settings_bp.route('/api/mex/settings', methods=['GET'])
def get_settings():
    """Return current runtime storage path and any pending (unsaved) path."""
    user_settings = _read_user_settings()
    pending = user_settings.get('storage_path')

    # If the persisted path matches the runtime path there is nothing pending
    if pending and Path(pending) == STORAGE_PATH:
        pending = None

    return jsonify({
        'success': True,
        'storage_path': str(STORAGE_PATH),
        'pending_storage_path': pending,
    })


@settings_bp.route('/api/mex/settings', methods=['POST'])
def save_settings():
    """Persist a new storage path to user_settings.json.

    Body: { "storage_path": "/absolute/path" }
    The change takes effect on next restart.
    """
    data = request.json or {}
    new_path_str = data.get('storage_path', '').strip()

    if not new_path_str:
        return jsonify({'success': False, 'error': 'storage_path is required'}), 400

    new_path = Path(new_path_str)

    # Basic validation: try to create the directory if it doesn't exist yet
    try:
        new_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        return jsonify({'success': False, 'error': f'Cannot use path: {e}'}), 400

    user_settings = _read_user_settings()
    user_settings['storage_path'] = str(new_path)
    _write_user_settings(user_settings)

    logger.info(f"Storage path saved to user_settings.json: {new_path}")
    return jsonify({'success': True, 'requires_restart': True})


@settings_bp.route('/api/mex/settings/move-storage', methods=['POST'])
def move_storage():
    """Copy all vault files to a new location and save the path.

    Body: { "storage_path": "/absolute/path" }
    The destination must be empty or not exist.
    Returns: { "success": true, "requires_restart": true, "files_copied": N }
    """
    data = request.json or {}
    dest_str = data.get('storage_path', '').strip()

    if not dest_str:
        return jsonify({'success': False, 'error': 'storage_path is required'}), 400

    dest = Path(dest_str)

    # Refuse to overwrite a non-empty destination
    if dest.exists() and any(dest.iterdir()):
        return jsonify({
            'success': False,
            'error': 'Destination directory is not empty. Please choose an empty folder.'
        }), 400

    logger.info(f"Moving vault from {STORAGE_PATH} -> {dest}")

    try:
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copytree(str(STORAGE_PATH), str(dest), dirs_exist_ok=True)
        shutil.rmtree(str(STORAGE_PATH))
    except Exception as e:
        logger.error(f"Vault move failed: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

    # Count copied files
    files_copied = sum(1 for f in dest.rglob('*') if f.is_file())

    # Persist the new path
    user_settings = _read_user_settings()
    user_settings['storage_path'] = str(dest)
    _write_user_settings(user_settings)

    logger.info(f"Vault move complete: {files_copied} files copied")
    return jsonify({'success': True, 'requires_restart': True, 'files_copied': files_copied})
