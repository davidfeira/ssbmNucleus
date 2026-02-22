"""
Slippi Blueprint - Slippi/Dolphin integration and texture pack endpoints.

Handles Slippi path verification, Dolphin configuration, and texture pack management.
"""

import os
import shutil
import configparser
import logging
from pathlib import Path
from flask import Blueprint, request, jsonify

from core.config import STORAGE_PATH, OUTPUT_PATH
from core.state import get_socketio
from core.helpers import convert_windows_to_wsl_path

logger = logging.getLogger(__name__)

slippi_bp = Blueprint('slippi', __name__)

# Global state for texture pack watcher
_active_texture_watcher = None
_active_texture_mapping = None
_active_slippi_path = None


def parse_dolphin_ini_iso_path(ini_path: str) -> str:
    """Parse Dolphin.ini to extract the ISO directory path."""
    try:
        config = configparser.ConfigParser()
        config.read(ini_path, encoding='utf-8')

        if 'General' in config:
            general = config['General']

            # Try ISOPath0, ISOPath1, etc.
            for i in range(10):
                key = f'ISOPath{i}'
                if key in general:
                    iso_dir = general[key]
                    if iso_dir and Path(iso_dir).is_dir():
                        logger.info(f"Found ISO directory from {key}: {iso_dir}")
                        return iso_dir

            # Also check DefaultISO
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


def get_dolphin_gfx_ini_path(slippi_path: str) -> Path:
    """Get path to Dolphin's GFX.ini configuration file."""
    return Path(slippi_path) / "User" / "Config" / "GFX.ini"


def get_dolphin_texture_settings(slippi_path: str) -> dict:
    """Read current texture settings from Dolphin's GFX.ini."""
    gfx_ini = get_dolphin_gfx_ini_path(slippi_path)

    result = {
        'dump_textures': None,
        'hires_textures': None
    }

    if not gfx_ini.exists():
        logger.warning(f"GFX.ini not found at {gfx_ini}")
        return result

    config = configparser.ConfigParser()
    config.optionxform = str  # Preserve case of keys

    try:
        config.read(gfx_ini)

        if 'Settings' in config:
            if 'DumpTextures' in config['Settings']:
                result['dump_textures'] = config['Settings']['DumpTextures'].lower() == 'true'
            if 'HiresTextures' in config['Settings']:
                result['hires_textures'] = config['Settings']['HiresTextures'].lower() == 'true'

    except Exception as e:
        logger.error(f"Error reading GFX.ini: {e}")

    return result


def set_dolphin_texture_settings(slippi_path: str, dump_textures: bool = None, hires_textures: bool = None) -> bool:
    """Modify texture settings in Dolphin's GFX.ini."""
    gfx_ini = get_dolphin_gfx_ini_path(slippi_path)

    # Ensure directory exists
    gfx_ini.parent.mkdir(parents=True, exist_ok=True)

    config = configparser.ConfigParser()
    config.optionxform = str  # Preserve case of keys

    try:
        # Read existing config if it exists
        if gfx_ini.exists():
            config.read(gfx_ini)

        # Ensure Settings section exists
        if 'Settings' not in config:
            config['Settings'] = {}

        # Update requested settings
        if dump_textures is not None:
            config['Settings']['DumpTextures'] = 'True' if dump_textures else 'False'
            logger.info(f"Set DumpTextures = {dump_textures}")

        if hires_textures is not None:
            config['Settings']['HiresTextures'] = 'True' if hires_textures else 'False'
            logger.info(f"Set HiresTextures = {hires_textures}")

        # Write back
        with open(gfx_ini, 'w') as f:
            config.write(f)

        logger.info(f"Updated GFX.ini at {gfx_ini}")
        return True

    except Exception as e:
        logger.error(f"Error writing GFX.ini: {e}")
        return False


@slippi_bp.route('/api/mex/settings/slippi-path/verify', methods=['POST'])
def verify_slippi_path():
    """Verify that a Slippi Dolphin path is valid."""
    try:
        data = request.json or {}
        slippi_path = data.get('slippiPath')

        if not slippi_path:
            return jsonify({
                'success': False,
                'error': 'No slippiPath provided'
            }), 400

        slippi_dir = Path(slippi_path)

        # Check if directory exists
        if not slippi_dir.exists():
            return jsonify({
                'success': False,
                'valid': False,
                'error': 'Directory does not exist'
            })

        # Check for User folder
        user_dir = slippi_dir / 'User'
        if not user_dir.exists() or not user_dir.is_dir():
            return jsonify({
                'success': False,
                'valid': False,
                'error': 'User folder not found'
            })

        # Check for Config folder
        config_dir = user_dir / 'Config'
        if not config_dir.exists():
            return jsonify({
                'success': False,
                'valid': False,
                'error': 'Config folder not found'
            })

        # Check for Dolphin.ini
        dolphin_ini = config_dir / 'Dolphin.ini'
        has_dolphin_ini = dolphin_ini.exists()

        return jsonify({
            'success': True,
            'valid': True,
            'hasDolphinIni': has_dolphin_ini
        })

    except Exception as e:
        logger.error(f"Verify Slippi path error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@slippi_bp.route('/api/dolphin/iso-folder', methods=['GET'])
def get_dolphin_iso_folder():
    """Get the ISO folder path from Dolphin.ini"""
    try:
        slippi_path = request.args.get('slippiPath')
        if not slippi_path:
            return jsonify({
                'success': False,
                'error': 'slippiPath query parameter is required'
            }), 400

        slippi_path = convert_windows_to_wsl_path(slippi_path)
        dolphin_ini = os.path.join(slippi_path, 'User', 'Config', 'Dolphin.ini')

        if not os.path.isfile(dolphin_ini):
            return jsonify({
                'success': False,
                'error': 'Dolphin.ini not found'
            }), 404

        iso_folder = parse_dolphin_ini_iso_path(dolphin_ini)

        return jsonify({
            'success': True,
            'isoFolder': iso_folder
        })
    except Exception as e:
        logger.error(f"Get ISO folder error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@slippi_bp.route('/api/mex/texture-pack/stats', methods=['GET'])
def get_texture_pack_stats():
    """Get texture pack folder statistics."""
    try:
        slippi_path = request.args.get('slippiPath', '')

        if not slippi_path:
            return jsonify({
                'success': True,
                'stats': {
                    'size': 0,
                    'fileCount': 0,
                    'path': '',
                    'exists': False
                }
            })

        # Texture pack folder is at <Slippi>/User/Load/Textures/GALE01/ssbm-nucleus
        texture_path = Path(slippi_path) / 'User' / 'Load' / 'Textures' / 'GALE01' / 'ssbm-nucleus'

        if not texture_path.exists():
            return jsonify({
                'success': True,
                'stats': {
                    'size': 0,
                    'fileCount': 0,
                    'path': str(texture_path),
                    'exists': False
                }
            })

        # Calculate size and file count
        total_size = 0
        file_count = 0
        for item in texture_path.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
                file_count += 1

        return jsonify({
            'success': True,
            'stats': {
                'size': total_size,
                'fileCount': file_count,
                'path': str(texture_path),
                'exists': True
            }
        })
    except Exception as e:
        logger.error(f"Error getting texture pack stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@slippi_bp.route('/api/mex/texture-pack/clear', methods=['POST'])
def clear_texture_pack():
    """Clear texture pack folder contents."""
    try:
        data = request.json or {}
        slippi_path = data.get('slippiPath', '')

        if not slippi_path:
            return jsonify({
                'success': False,
                'error': 'slippiPath is required'
            }), 400

        # Only clear our subfolder — leave other user textures untouched
        texture_path = Path(slippi_path) / 'User' / 'Load' / 'Textures' / 'GALE01' / 'ssbm-nucleus'

        if not texture_path.exists():
            return jsonify({
                'success': True,
                'deletedCount': 0,
                'message': 'Texture pack folder does not exist'
            })

        # Delete all contents
        deleted_count = 0
        for item in texture_path.iterdir():
            if item.is_file():
                item.unlink()
                deleted_count += 1
            elif item.is_dir():
                shutil.rmtree(item)
                deleted_count += 1

        logger.info(f"Cleared texture pack folder: {deleted_count} items deleted from {texture_path}")

        return jsonify({
            'success': True,
            'deletedCount': deleted_count,
            'message': f'Deleted {deleted_count} items from texture pack folder'
        })
    except Exception as e:
        logger.error(f"Error clearing texture pack: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@slippi_bp.route('/api/mex/texture-pack/start-listening', methods=['POST'])
def start_texture_listening():
    """Start watching for dumped textures after a texture pack mode export."""
    global _active_texture_watcher, _active_texture_mapping, _active_slippi_path

    try:
        data = request.json or {}
        build_id = data.get('buildId')
        slippi_path = data.get('slippiPath')

        if not build_id:
            return jsonify({
                'success': False,
                'error': 'buildId is required'
            }), 400

        if not slippi_path:
            return jsonify({
                'success': False,
                'error': 'slippiPath is required'
            }), 400

        # Convert Windows path to WSL path if needed
        slippi_path = convert_windows_to_wsl_path(slippi_path)
        logger.info(f"Slippi path (converted): {slippi_path}")

        # Enable texture dumping in Dolphin's GFX.ini
        set_dolphin_texture_settings(slippi_path, dump_textures=True, hires_textures=True)
        logger.info("Enabled DumpTextures in GFX.ini")

        # Store slippi path for use when stopping
        _active_slippi_path = slippi_path

        # Load the mapping file
        mapping_file = OUTPUT_PATH / f"{build_id}_texture_mapping.json"
        if not mapping_file.exists():
            return jsonify({
                'success': False,
                'error': f'Mapping file not found for build: {build_id}'
            }), 404

        from texture_pack import TexturePackMapping, TexturePackWatcher

        mapping = TexturePackMapping.load(mapping_file)
        _active_texture_mapping = mapping

        # Derive paths
        slippi_dir = Path(slippi_path)
        dump_path = slippi_dir / 'User' / 'Dump' / 'Textures' / 'GALE01'
        load_path = slippi_dir / 'User' / 'Load' / 'Textures' / 'GALE01' / 'ssbm-nucleus'

        # Ensure directories exist
        dump_path.mkdir(parents=True, exist_ok=True)
        load_path.mkdir(parents=True, exist_ok=True)

        # Stop any existing watcher
        if _active_texture_watcher:
            _active_texture_watcher.stop()

        # Create callbacks
        socketio = get_socketio()

        def on_match(costume):
            logger.info(f"[CALLBACK] on_match called: {costume['character']} costume {costume['costume_index']}")
            try:
                socketio.emit('texture_matched', {
                    'character': costume['character'],
                    'costumeIndex': costume['costume_index'],
                    'skinId': costume['skin_id'],
                    'filename': costume['dumped_filename']
                })
                logger.info("[CALLBACK] emitted texture_matched event")
            except Exception as e:
                logger.error(f"[CALLBACK] emit error: {e}", exc_info=True)

        def on_progress(matched, total):
            logger.info(f"[CALLBACK] on_progress called: {matched}/{total}")
            try:
                socketio.emit('texture_progress', {
                    'matched': matched,
                    'total': total,
                    'percentage': int(matched / total * 100) if total > 0 else 0
                })
                logger.info("[CALLBACK] emitted texture_progress event")
            except Exception as e:
                logger.error(f"[CALLBACK] emit error: {e}", exc_info=True)

        # Start watcher
        _active_texture_watcher = TexturePackWatcher(
            dump_path=dump_path,
            load_path=load_path,
            mapping=mapping,
            storage_path=STORAGE_PATH,
            on_match=on_match,
            on_progress=on_progress
        )
        _active_texture_watcher.start()

        logger.info(f"Started texture pack watcher for build {build_id}")
        logger.info(f"  Watching: {dump_path}")
        logger.info(f"  Output to: {load_path}")

        # Build character breakdown for UI
        characters = {}
        for costume in mapping.costumes:
            char_name = costume['character']
            if char_name not in characters:
                characters[char_name] = {'total': 0, 'matched': 0, 'costumes': []}
            characters[char_name]['total'] += 1
            if costume['matched']:
                characters[char_name]['matched'] += 1
            characters[char_name]['costumes'].append({
                'index': costume['costume_index'],
                'matched': costume['matched']
            })

        # Convert to list sorted by character name
        character_list = [
            {'name': name, **data}
            for name, data in sorted(characters.items())
        ]

        return jsonify({
            'success': True,
            'totalCostumes': len(mapping.costumes),
            'characters': character_list,
            'dumpPath': str(dump_path),
            'loadPath': str(load_path)
        })

    except Exception as e:
        logger.error(f"Start texture listening error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@slippi_bp.route('/api/mex/texture-pack/stop-listening', methods=['POST'])
def stop_texture_listening():
    """Stop watching and finalize the texture pack."""
    global _active_texture_watcher, _active_texture_mapping, _active_slippi_path

    try:
        if not _active_texture_watcher:
            return jsonify({
                'success': False,
                'error': 'No active texture watcher'
            }), 400

        # Disable texture dumping in Dolphin's GFX.ini (keep HiresTextures on for texture packs)
        if _active_slippi_path:
            set_dolphin_texture_settings(_active_slippi_path, dump_textures=False, hires_textures=True)
            logger.info("Disabled DumpTextures in GFX.ini (keeping HiresTextures on)")

        # Get status before stopping
        status = _active_texture_watcher.get_status()
        mapping = _active_texture_mapping

        # Stop the watcher
        _active_texture_watcher.stop()

        # Save updated mapping with matched filenames
        if mapping:
            mapping_file = OUTPUT_PATH / f"{mapping.build_id}_texture_mapping.json"
            mapping.save(mapping_file)
            logger.info(f"Saved final texture mapping to {mapping_file}")

        # Build texture pack path
        texture_pack_path = _active_texture_watcher.load_path / mapping.build_name if mapping else None

        result = {
            'success': True,
            'matchedCount': status['matched_count'],
            'totalCount': status['total_count'],
            'texturePackPath': str(texture_pack_path) if texture_pack_path else None
        }

        _active_texture_watcher = None
        _active_texture_mapping = None
        _active_slippi_path = None

        logger.info(f"Stopped texture pack watcher. Matched {result['matchedCount']}/{result['totalCount']} textures")

        return jsonify(result)

    except Exception as e:
        logger.error(f"Stop texture listening error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@slippi_bp.route('/api/dolphin/texture-settings', methods=['GET', 'POST'])
def dolphin_texture_settings():
    """GET: Read current texture settings. POST: Update texture settings."""
    try:
        if request.method == 'GET':
            slippi_path = request.args.get('slippiPath')
            if not slippi_path:
                return jsonify({
                    'success': False,
                    'error': 'slippiPath query parameter is required'
                }), 400

            # Convert Windows path to WSL path if needed
            slippi_path = convert_windows_to_wsl_path(slippi_path)

            settings = get_dolphin_texture_settings(slippi_path)
            return jsonify({
                'success': True,
                'dumpTextures': settings['dump_textures'],
                'hiresTextures': settings['hires_textures']
            })

        else:  # POST
            data = request.json or {}
            slippi_path = data.get('slippiPath')

            if not slippi_path:
                return jsonify({
                    'success': False,
                    'error': 'slippiPath is required'
                }), 400

            # Convert Windows path to WSL path if needed
            slippi_path = convert_windows_to_wsl_path(slippi_path)

            dump_textures = data.get('dumpTextures')
            hires_textures = data.get('hiresTextures')

            if dump_textures is None and hires_textures is None:
                return jsonify({
                    'success': False,
                    'error': 'At least one of dumpTextures or hiresTextures must be provided'
                }), 400

            success = set_dolphin_texture_settings(slippi_path, dump_textures, hires_textures)

            if success:
                # Read back the settings to confirm
                settings = get_dolphin_texture_settings(slippi_path)
                return jsonify({
                    'success': True,
                    'dumpTextures': settings['dump_textures'],
                    'hiresTextures': settings['hires_textures'],
                    'message': 'Settings updated. Restart Dolphin for changes to take effect.'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to update GFX.ini'
                }), 500

    except Exception as e:
        logger.error(f"Dolphin texture settings error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@slippi_bp.route('/api/mex/texture-pack/status', methods=['GET'])
def get_texture_listening_status():
    """Get the current status of the texture watcher."""
    global _active_texture_watcher

    try:
        if not _active_texture_watcher:
            return jsonify({
                'success': True,
                'active': False
            })

        status = _active_texture_watcher.get_status()
        return jsonify({
            'success': True,
            'active': True,
            **status
        })

    except Exception as e:
        logger.error(f"Texture status error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
