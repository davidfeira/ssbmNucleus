"""
Export Blueprint - ISO export routes with progress tracking.

Handles ISO export with WebSocket progress updates and download.
"""

import os
import shutil
import threading
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, after_this_request

from core.config import OUTPUT_PATH
from core.state import get_mex_manager, get_socketio, get_current_project_path

logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__)


@export_bp.route('/api/mex/export/start', methods=['POST'])
def start_export():
    """
    Start ISO export (async operation with WebSocket progress)

    Body:
    {
        "filename": "modded_game.iso",  // optional
        "cspCompression": 1.0,  // optional, 0.1-1.0, default 1.0
        "useColorSmash": false,  // optional, boolean, default false
        "texturePackMode": false,  // optional, boolean, default false
        "slippiDolphinPath": "..."  // required if texturePackMode is true
    }
    """
    try:
        data = request.json or {}
        filename = data.get('filename', f'game_{datetime.now().strftime("%Y%m%d_%H%M%S")}.iso')
        csp_compression = data.get('cspCompression', 1.0)
        use_color_smash = data.get('useColorSmash', False)
        texture_pack_mode = data.get('texturePackMode', False)
        slippi_dolphin_path = data.get('slippiDolphinPath')

        # Validate compression range
        if not isinstance(csp_compression, (int, float)) or csp_compression < 0.1 or csp_compression > 1.0:
            return jsonify({
                'success': False,
                'error': 'cspCompression must be a number between 0.1 and 1.0'
            }), 400

        # Validate useColorSmash
        if not isinstance(use_color_smash, bool):
            return jsonify({
                'success': False,
                'error': 'useColorSmash must be a boolean'
            }), 400

        # Validate texture pack mode requirements
        if texture_pack_mode:
            if not slippi_dolphin_path:
                return jsonify({
                    'success': False,
                    'error': 'slippiDolphinPath is required when texturePackMode is enabled'
                }), 400

        output_file = OUTPUT_PATH / filename
        build_id = f"build_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"=== ISO EXPORT START ===")
        logger.info(f"Filename: {filename}")
        logger.info(f"CSP Compression: {csp_compression}")
        logger.info(f"Use Color Smash: {use_color_smash}")
        logger.info(f"Texture Pack Mode: {texture_pack_mode}")

        def export_with_progress():
            """Export ISO in background thread with WebSocket progress updates"""
            from pathlib import Path
            backup_dir = None
            mapping = None
            socketio = get_socketio()
            current_project_path = get_current_project_path()

            try:
                def progress_callback(percentage, message):
                    socketio.emit('export_progress', {
                        'percentage': percentage,
                        'message': message
                    })

                mex = get_mex_manager()

                # If texture pack mode, replace CSPs with placeholders
                if texture_pack_mode:
                    from texture_pack import (
                        save_encoded_placeholder,
                        TexturePackMapping,
                        CostumeMapping
                    )

                    # Clear the DUMP folder to prevent old placeholders from confusing the scanner
                    if slippi_dolphin_path:
                        dump_path = Path(slippi_dolphin_path) / "User" / "Dump" / "Textures" / "GALE01"
                        if dump_path.exists():
                            shutil.rmtree(dump_path)
                            dump_path.mkdir(parents=True)
                            logger.info(f"Cleared dump folder: {dump_path}")

                    project_dir = current_project_path.parent
                    csp_dir = project_dir / "assets" / "csp"
                    backup_dir = project_dir / "assets" / "csp_backup"

                    # Backup original CSPs
                    if backup_dir.exists():
                        shutil.rmtree(backup_dir)
                    if csp_dir.exists():
                        shutil.copytree(csp_dir, backup_dir)
                        logger.info(f"Backed up CSPs to {backup_dir}")

                    # Create mapping
                    build_name = filename.replace('.iso', '')
                    mapping = TexturePackMapping(
                        build_id=build_id,
                        build_name=build_name,
                        created_at=datetime.now().isoformat()
                    )

                    # Get all fighters and their costumes
                    fighters = mex.list_fighters()
                    global_index = 0

                    for fighter in fighters:
                        try:
                            result = mex._run_command("get-costumes", str(mex.project_path), fighter['name'])
                            costumes = result.get('costumes', [])

                            for costume_idx, costume in enumerate(costumes):
                                if costume.get('csp'):
                                    csp_ref = costume['csp'].replace('\\', '/')
                                    csp_path = csp_dir / f"{csp_ref.split('/')[-1]}.png"

                                    if csp_path.exists():
                                        # Store original CSP path (from backup for restoration)
                                        backup_csp_path = backup_dir / f"{csp_ref.split('/')[-1]}.png"

                                        # Add to mapping
                                        mapping.add_costume(CostumeMapping(
                                            index=global_index,
                                            character=fighter['name'],
                                            costume_index=costume_idx,
                                            skin_id=costume.get('name', f"costume_{costume_idx}"),
                                            real_csp_path=str(backup_csp_path)
                                        ))

                                        # Replace CSP with base-4 encoded placeholder (16x16)
                                        save_encoded_placeholder(global_index, csp_path)
                                        logger.debug(f"Replaced CSP {csp_path.name} with encoded placeholder index={global_index}")

                                        global_index += 1

                        except Exception as e:
                            logger.warning(f"Error processing {fighter['name']}: {e}")
                            continue

                    logger.info(f"Created {global_index} placeholder CSPs")

                    # Save a debug sample so user can verify the placeholder format
                    debug_placeholder = OUTPUT_PATH / "debug_placeholder_sample.png"
                    save_encoded_placeholder(12345, debug_placeholder)  # Test index to verify encoding
                    logger.info(f"Saved debug placeholder sample to {debug_placeholder}")

                    # Save mapping
                    mapping_file = OUTPUT_PATH / f"{build_id}_texture_mapping.json"
                    mapping.save(mapping_file)
                    logger.info(f"Saved texture mapping to {mapping_file}")

                    # CRITICAL: Recompile CSPs from PNG sources
                    # This regenerates the .tex files from the placeholder PNGs we just wrote.
                    # Without this step, MexCLI would use the old cached .tex files instead
                    # of the new placeholder images.
                    logger.info("Recompiling CSPs from placeholder PNGs...")
                    recompile_result = mex.recompile_csps()
                    logger.info(f"CSP recompile complete: {recompile_result.get('message', 'done')}")

                # Note: Extras are patched immediately on import, not at export time

                # Run the actual export
                # When using texture pack mode, skip compression entirely
                # because placeholders must stay at fixed 16x16 size
                skip_compression = texture_pack_mode
                result = mex.export_iso(str(output_file), progress_callback, csp_compression, use_color_smash, skip_compression)

                # Restore original CSPs if texture pack mode
                if texture_pack_mode and backup_dir and backup_dir.exists():
                    if csp_dir.exists():
                        shutil.rmtree(csp_dir)
                    # Copy back (not move) - keep backup for texture pack listening
                    shutil.copytree(backup_dir, csp_dir)
                    logger.info("Restored original CSPs (kept backup for texture pack)")

                socketio.emit('export_complete', {
                    'success': True,
                    'filename': filename,
                    'path': str(output_file),
                    'texturePackMode': texture_pack_mode,
                    'buildId': build_id if texture_pack_mode else None,
                    'totalCostumes': len(mapping.costumes) if mapping else 0
                })

            except Exception as e:
                # Restore CSPs on error
                if texture_pack_mode and backup_dir and backup_dir.exists():
                    try:
                        project_dir = current_project_path.parent
                        csp_dir = project_dir / "assets" / "csp"
                        if csp_dir.exists():
                            shutil.rmtree(csp_dir)
                        shutil.move(str(backup_dir), str(csp_dir))
                        logger.info("Restored original CSPs after error")
                    except Exception as restore_error:
                        logger.error(f"Failed to restore CSPs: {restore_error}")

                socketio.emit('export_error', {
                    'success': False,
                    'error': str(e)
                })

        # Start export in background thread
        thread = threading.Thread(target=export_with_progress)
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Export started',
            'filename': filename,
            'buildId': build_id if texture_pack_mode else None
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@export_bp.route('/api/mex/export/download/<filename>', methods=['GET'])
def download_iso(filename):
    """Download exported ISO file"""
    try:
        file_path = OUTPUT_PATH / filename

        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404

        @after_this_request
        def remove_file(response):
            try:
                os.remove(file_path)
                logger.info(f"Deleted ISO file after download: {filename}")
            except Exception as error:
                logger.error(f"Error deleting ISO file {filename}: {str(error)}")
            return response

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
