"""
XDelta Blueprint - XDelta patch management.

Handles importing, building, creating, and downloading XDelta patches.
"""

import os
import re
import sys
import json
import time
import uuid
import shutil
import subprocess
import threading
import logging
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, after_this_request

from core.config import PROJECT_ROOT, RESOURCES_DIR, STORAGE_PATH, OUTPUT_PATH, get_subprocess_args
from core.state import get_socketio

logger = logging.getLogger(__name__)

xdelta_bp = Blueprint('xdelta', __name__)

# XDelta storage path
XDELTA_PATH = STORAGE_PATH / "xdelta"
XDELTA_PATH.mkdir(exist_ok=True)


def load_xdelta_metadata():
    """Load xdelta metadata from metadata.json"""
    metadata_file = STORAGE_PATH / 'metadata.json'
    if not metadata_file.exists():
        return []

    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    return metadata.get('xdelta', [])


def save_xdelta_metadata(xdelta_list):
    """Save xdelta metadata to metadata.json"""
    metadata_file = STORAGE_PATH / 'metadata.json'

    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {'version': '1.0', 'characters': {}, 'stages': {}}

    metadata['xdelta'] = xdelta_list

    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)


def get_xdelta_exe():
    """Get the path to xdelta3 executable."""
    if os.name == 'nt':
        if getattr(sys, 'frozen', False):
            xdelta_exe = RESOURCES_DIR / "utility" / "xdelta" / "xdelta3.exe"
        else:
            xdelta_exe = PROJECT_ROOT / "utility" / "xdelta" / "xdelta3.exe"
        if not xdelta_exe.exists():
            xdelta_exe = "xdelta3"
    else:
        xdelta_exe = "xdelta3"
    return xdelta_exe


def run_xdelta_build(patch_id, patch_name, vanilla_iso_path, xdelta_path, output_path, expected_size):
    """Background thread function to run xdelta and emit progress"""
    socketio = get_socketio()
    try:
        xdelta_exe = get_xdelta_exe()

        cmd = [
            str(xdelta_exe),
            '-d',  # Decode/decompress
            '-s', str(vanilla_iso_path),
            str(xdelta_path),
            str(output_path)
        ]

        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **get_subprocess_args()
        )

        # Monitor progress by checking output file size
        last_progress = 0
        while process.poll() is None:
            time.sleep(0.3)
            try:
                if output_path.exists():
                    current_size = output_path.stat().st_size
                    progress = min(int((current_size / expected_size) * 100), 99)
                    if progress != last_progress:
                        socketio.emit('xdelta_progress', {
                            'patch_id': patch_id,
                            'percentage': progress,
                            'message': f'Patching... {progress}%'
                        })
                        last_progress = progress
            except:
                pass

        # Process finished - check result
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else stdout.decode() if stdout else 'Unknown xdelta error'
            logger.error(f"xdelta3 failed: {error_msg}")
            socketio.emit('xdelta_error', {
                'patch_id': patch_id,
                'error': f'Failed to apply patch: {error_msg}'
            })
        else:
            logger.info(f"[OK] Successfully built ISO: {output_path.name}")
            socketio.emit('xdelta_complete', {
                'patch_id': patch_id,
                'filename': output_path.name,
                'path': str(output_path)
            })

    except Exception as e:
        logger.error(f"xdelta build thread error: {str(e)}", exc_info=True)
        socketio.emit('xdelta_error', {
            'patch_id': patch_id,
            'error': str(e)
        })


def run_xdelta_create(create_id, name, description, vanilla_iso_path, modded_iso_path, output_path, image_path=None):
    """Background thread function to create xdelta patch and emit progress"""
    socketio = get_socketio()
    try:
        xdelta_exe = get_xdelta_exe()

        # Get modded ISO size for progress estimation
        modded_size = Path(modded_iso_path).stat().st_size

        cmd = [
            str(xdelta_exe),
            '-e',  # Encode (create patch)
            '-1',  # Fast compression
            '-s', str(vanilla_iso_path),
            str(modded_iso_path),
            str(output_path)
        ]

        logger.info(f"Creating xdelta patch: {' '.join(cmd)}")

        # Start the process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **get_subprocess_args()
        )

        # xdelta3 doesn't output progress, so we just show current output size
        last_size_mb = 0

        while process.poll() is None:
            time.sleep(1)
            try:
                if output_path.exists():
                    current_size = output_path.stat().st_size
                    current_size_mb = current_size / (1024 * 1024)
                    if int(current_size_mb) != int(last_size_mb):
                        socketio.emit('xdelta_create_progress', {
                            'create_id': create_id,
                            'percentage': -1,  # -1 means indeterminate
                            'message': f'Creating patch... ({current_size_mb:.1f} MB so far)'
                        })
                        last_size_mb = current_size_mb
            except:
                pass

        # Process finished - check result
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else stdout.decode() if stdout else 'Unknown xdelta error'
            logger.error(f"xdelta3 create failed: {error_msg}")
            # Clean up failed output
            if output_path.exists():
                os.remove(output_path)
            socketio.emit('xdelta_create_error', {
                'create_id': create_id,
                'error': f'Failed to create patch: {error_msg}'
            })
        else:
            # Success - save to storage
            patch_id = str(uuid.uuid4())[:8]

            # Move to storage
            final_path = XDELTA_PATH / f"{patch_id}.xdelta"
            shutil.move(str(output_path), str(final_path))

            # Copy image if provided
            if image_path and Path(image_path).exists():
                image_dest = XDELTA_PATH / f"{patch_id}.png"
                shutil.copy(str(image_path), str(image_dest))

            # Get patch file size for display
            patch_size = final_path.stat().st_size
            patch_size_mb = patch_size / (1024 * 1024)

            # Add to metadata
            patches = load_xdelta_metadata()
            patches.append({
                'id': patch_id,
                'name': name,
                'description': description,
                'filename': f"{name}.xdelta",
                'size': patch_size,
                'created': datetime.now().isoformat()
            })
            save_xdelta_metadata(patches)

            logger.info(f"[OK] Created xdelta patch: {name} ({patch_id}) - {patch_size_mb:.2f} MB")
            socketio.emit('xdelta_create_complete', {
                'create_id': create_id,
                'patch_id': patch_id,
                'name': name,
                'size': patch_size,
                'size_mb': round(patch_size_mb, 2)
            })

    except Exception as e:
        logger.error(f"xdelta create thread error: {str(e)}", exc_info=True)
        socketio.emit('xdelta_create_error', {
            'create_id': create_id,
            'error': str(e)
        })


@xdelta_bp.route('/api/mex/xdelta/list', methods=['GET'])
def list_xdelta_patches():
    """List all xdelta patches in storage"""
    try:
        patches = load_xdelta_metadata()

        # Add image URLs
        for patch in patches:
            patch_id = patch.get('id')
            if patch_id:
                image_path = XDELTA_PATH / f"{patch_id}.png"
                if image_path.exists():
                    patch['imageUrl'] = f"/storage/xdelta/{patch_id}.png"
                else:
                    patch['imageUrl'] = None

        return jsonify({
            'success': True,
            'patches': patches
        })
    except Exception as e:
        logger.error(f"List xdelta patches error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@xdelta_bp.route('/api/mex/xdelta/import', methods=['POST'])
def import_xdelta_patch():
    """Import a new xdelta patch"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No xdelta file uploaded'
            }), 400

        file = request.files['file']
        name = request.form.get('name', 'Unnamed Patch')
        description = request.form.get('description', '')

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Validate file extension
        if not file.filename.lower().endswith('.xdelta'):
            return jsonify({
                'success': False,
                'error': 'File must be an .xdelta file'
            }), 400

        # Generate unique ID
        patch_id = str(uuid.uuid4())[:8]

        # Save xdelta file
        xdelta_filename = f"{patch_id}.xdelta"
        xdelta_path = XDELTA_PATH / xdelta_filename
        file.save(str(xdelta_path))

        # Save image if provided
        if 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename:
                image_path = XDELTA_PATH / f"{patch_id}.png"
                image_file.save(str(image_path))

        # Add to metadata
        patches = load_xdelta_metadata()
        patches.append({
            'id': patch_id,
            'name': name,
            'description': description,
            'filename': file.filename,
            'created': datetime.now().isoformat()
        })
        save_xdelta_metadata(patches)

        logger.info(f"[OK] Imported xdelta patch: {name} ({patch_id})")

        return jsonify({
            'success': True,
            'patch': {
                'id': patch_id,
                'name': name,
                'description': description
            }
        })
    except Exception as e:
        logger.error(f"Import xdelta patch error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@xdelta_bp.route('/api/mex/xdelta/update/<patch_id>', methods=['POST'])
def update_xdelta_patch(patch_id):
    """Update an xdelta patch's metadata"""
    try:
        data = request.json or {}
        name = data.get('name')
        description = data.get('description')

        patches = load_xdelta_metadata()
        patch = next((p for p in patches if p['id'] == patch_id), None)

        if not patch:
            return jsonify({
                'success': False,
                'error': 'Patch not found'
            }), 404

        if name is not None:
            patch['name'] = name
        if description is not None:
            patch['description'] = description

        save_xdelta_metadata(patches)

        return jsonify({
            'success': True,
            'patch': patch
        })
    except Exception as e:
        logger.error(f"Update xdelta patch error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@xdelta_bp.route('/api/mex/xdelta/update-image/<patch_id>', methods=['POST'])
def update_xdelta_image(patch_id):
    """Update an xdelta patch's image"""
    try:
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file uploaded'
            }), 400

        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Verify patch exists
        patches = load_xdelta_metadata()
        patch = next((p for p in patches if p['id'] == patch_id), None)

        if not patch:
            return jsonify({
                'success': False,
                'error': 'Patch not found'
            }), 404

        # Save image
        image_path = XDELTA_PATH / f"{patch_id}.png"
        image_file.save(str(image_path))

        return jsonify({
            'success': True,
            'imageUrl': f"/storage/xdelta/{patch_id}.png"
        })
    except Exception as e:
        logger.error(f"Update xdelta image error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@xdelta_bp.route('/api/mex/xdelta/delete/<patch_id>', methods=['POST'])
def delete_xdelta_patch(patch_id):
    """Delete an xdelta patch"""
    try:
        # Remove from metadata
        patches = load_xdelta_metadata()
        patches = [p for p in patches if p['id'] != patch_id]
        save_xdelta_metadata(patches)

        # Delete files
        xdelta_path = XDELTA_PATH / f"{patch_id}.xdelta"
        image_path = XDELTA_PATH / f"{patch_id}.png"

        if xdelta_path.exists():
            os.remove(xdelta_path)
        if image_path.exists():
            os.remove(image_path)

        logger.info(f"[OK] Deleted xdelta patch: {patch_id}")

        return jsonify({
            'success': True
        })
    except Exception as e:
        logger.error(f"Delete xdelta patch error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@xdelta_bp.route('/api/mex/xdelta/build/<patch_id>', methods=['POST'])
def build_xdelta_iso(patch_id):
    """Build an ISO from an xdelta patch using the vanilla ISO"""
    try:
        data = request.json or {}
        vanilla_iso_path = data.get('vanillaIsoPath')

        if not vanilla_iso_path:
            return jsonify({
                'success': False,
                'error': 'No vanilla ISO path provided. Please set it in Settings.'
            }), 400

        vanilla_iso = Path(vanilla_iso_path)
        if not vanilla_iso.exists():
            return jsonify({
                'success': False,
                'error': f'Vanilla ISO not found: {vanilla_iso_path}'
            }), 404

        # Get expected output size from vanilla ISO
        expected_size = vanilla_iso.stat().st_size

        # Get patch info
        patches = load_xdelta_metadata()
        patch = next((p for p in patches if p['id'] == patch_id), None)

        if not patch:
            return jsonify({
                'success': False,
                'error': 'Patch not found'
            }), 404

        xdelta_path = XDELTA_PATH / f"{patch_id}.xdelta"
        if not xdelta_path.exists():
            return jsonify({
                'success': False,
                'error': 'Xdelta file not found'
            }), 404

        # Create output filename
        safe_name = re.sub(r'[^\w\-_]', '_', patch['name'])
        output_filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.iso"
        output_path = OUTPUT_PATH / output_filename

        logger.info(f"Building ISO from xdelta patch: {patch['name']}")
        logger.info(f"  Vanilla ISO: {vanilla_iso_path} ({expected_size} bytes)")
        logger.info(f"  Patch: {xdelta_path}")
        logger.info(f"  Output: {output_path}")

        # Run in background thread
        thread = threading.Thread(
            target=run_xdelta_build,
            args=(patch_id, patch['name'], vanilla_iso_path, xdelta_path, output_path, expected_size)
        )
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Build started',
            'filename': output_filename
        })
    except Exception as e:
        logger.error(f"Build xdelta ISO error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@xdelta_bp.route('/api/mex/xdelta/download/<filename>', methods=['GET'])
def download_xdelta_iso(filename):
    """Download a built xdelta ISO"""
    try:
        file_path = OUTPUT_PATH / filename

        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'ISO file not found'
            }), 404

        # Delete after download
        @after_this_request
        def cleanup(response):
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
        logger.error(f"Download xdelta ISO error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@xdelta_bp.route('/api/mex/xdelta/create', methods=['POST'])
def create_xdelta_patch():
    """Create a new xdelta patch from a modded ISO"""
    try:
        data = request.json or {}
        vanilla_iso_path = data.get('vanillaIsoPath')
        modded_iso_path = data.get('moddedIsoPath')
        name = data.get('name', 'New Patch')
        description = data.get('description', '')

        if not vanilla_iso_path:
            return jsonify({
                'success': False,
                'error': 'No vanilla ISO path provided. Please set it in Settings.'
            }), 400

        if not modded_iso_path:
            return jsonify({
                'success': False,
                'error': 'No modded ISO path provided.'
            }), 400

        vanilla_iso = Path(vanilla_iso_path)
        modded_iso = Path(modded_iso_path)

        if not vanilla_iso.exists():
            return jsonify({
                'success': False,
                'error': f'Vanilla ISO not found: {vanilla_iso_path}'
            }), 404

        if not modded_iso.exists():
            return jsonify({
                'success': False,
                'error': f'Modded ISO not found: {modded_iso_path}'
            }), 404

        # Generate unique ID for this creation session
        create_id = str(uuid.uuid4())[:8]

        # Create temporary output path
        safe_name = re.sub(r'[^\w\-_]', '_', name)
        temp_filename = f"temp_patch_{create_id}.xdelta"
        temp_output_path = OUTPUT_PATH / temp_filename

        logger.info(f"Creating xdelta patch: {name}")
        logger.info(f"  Vanilla ISO: {vanilla_iso_path}")
        logger.info(f"  Modded ISO: {modded_iso_path}")
        logger.info(f"  Temp output: {temp_output_path}")

        # Run in background thread
        thread = threading.Thread(
            target=run_xdelta_create,
            args=(create_id, name, description, vanilla_iso_path, modded_iso_path, temp_output_path)
        )
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Patch creation started',
            'create_id': create_id
        })
    except Exception as e:
        logger.error(f"Create xdelta patch error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@xdelta_bp.route('/api/mex/xdelta/download-patch/<patch_id>', methods=['GET'])
def download_xdelta_patch(patch_id):
    """Download an xdelta patch file"""
    try:
        # Get patch info
        patches = load_xdelta_metadata()
        patch = next((p for p in patches if p['id'] == patch_id), None)

        if not patch:
            return jsonify({
                'success': False,
                'error': 'Patch not found'
            }), 404

        file_path = XDELTA_PATH / f"{patch_id}.xdelta"

        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'Patch file not found'
            }), 404

        # Use the original name for the download
        download_name = f"{patch['name']}.xdelta"

        return send_file(
            file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        logger.error(f"Download xdelta patch error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
