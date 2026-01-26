"""
Bundles Blueprint - .ssbm mod bundle management.

Handles creating, importing, installing, and managing .ssbm mod bundles.
"""

import os
import re
import sys
import json
import time
import uuid
import shutil
import zipfile
import tempfile
import subprocess
import threading
import configparser
import logging
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

from core.config import PROJECT_ROOT, RESOURCES_DIR, STORAGE_PATH, OUTPUT_PATH, get_subprocess_args
from core.state import get_socketio

logger = logging.getLogger(__name__)

bundles_bp = Blueprint('bundles', __name__)

# Bundle storage path
BUNDLE_PATH = STORAGE_PATH / "bundles"
BUNDLE_PATH.mkdir(parents=True, exist_ok=True)


def load_bundle_metadata():
    """Load bundle metadata from metadata.json"""
    metadata_file = STORAGE_PATH / 'metadata.json'
    if not metadata_file.exists():
        return []

    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    return metadata.get('bundles', [])


def save_bundle_metadata(bundles_list):
    """Save bundle metadata to metadata.json"""
    metadata_file = STORAGE_PATH / 'metadata.json'

    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    else:
        metadata = {'version': '1.0', 'characters': {}, 'stages': {}}

    metadata['bundles'] = bundles_list

    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved {len(bundles_list)} bundles to metadata.json")


def parse_dolphin_ini_iso_path(ini_path: str) -> str:
    """Parse Dolphin.ini to extract the ISO directory path."""
    try:
        config = configparser.ConfigParser()
        config.read(ini_path, encoding='utf-8')

        if 'General' in config:
            general = config['General']
            for i in range(10):
                key = f'ISOPath{i}'
                if key in general:
                    iso_dir = general[key]
                    if iso_dir and Path(iso_dir).is_dir():
                        return iso_dir

            if 'DefaultISO' in general:
                default_iso = general['DefaultISO']
                if default_iso:
                    iso_dir = str(Path(default_iso).parent)
                    if Path(iso_dir).is_dir():
                        return iso_dir

        return None
    except Exception as e:
        logger.warning(f"Error parsing Dolphin.ini: {e}")
        return None


def set_dolphin_texture_settings(slippi_path, dump_textures=False, hires_textures=True):
    """Set Dolphin texture settings in GFX.ini"""
    try:
        gfx_ini = Path(slippi_path) / 'User' / 'Config' / 'GFX.ini'

        config = configparser.ConfigParser()
        if gfx_ini.exists():
            config.read(gfx_ini, encoding='utf-8')

        if 'Settings' not in config:
            config['Settings'] = {}

        config['Settings']['DumpTextures'] = 'True' if dump_textures else 'False'
        config['Settings']['HiresTextures'] = 'True' if hires_textures else 'False'

        with open(gfx_ini, 'w') as f:
            config.write(f)

        logger.info(f"Updated GFX.ini: DumpTextures={dump_textures}, HiresTextures={hires_textures}")
    except Exception as e:
        logger.error(f"Failed to update GFX.ini: {e}")


def run_bundle_export(export_id, name, description, build_name, vanilla_iso_path, exported_iso_path, texture_pack_path, image_path=None):
    """Background thread function to create .ssbm bundle and save to storage"""
    socketio = get_socketio()
    try:
        socketio.emit('bundle_export_progress', {
            'export_id': export_id,
            'percentage': 0,
            'message': 'Creating xdelta patch...'
        })

        # Create temp directory for bundle contents
        temp_dir = Path(tempfile.mkdtemp(prefix='bundle_'))
        bundle_dir = temp_dir / 'bundle'
        bundle_dir.mkdir()

        # 1. Create xdelta patch
        patch_path = bundle_dir / 'patch.xdelta'

        # Find xdelta executable
        if os.name == 'nt':
            if getattr(sys, 'frozen', False):
                xdelta_exe = RESOURCES_DIR / "utility" / "xdelta" / "xdelta3.exe"
            else:
                xdelta_exe = PROJECT_ROOT / "utility" / "xdelta" / "xdelta3.exe"
            if not xdelta_exe.exists():
                xdelta_exe = "xdelta3"
        else:
            xdelta_exe = "xdelta3"

        cmd = [
            str(xdelta_exe),
            '-e',  # Encode (create patch)
            '-1',  # Fast compression
            '-s', str(vanilla_iso_path),
            str(exported_iso_path),
            str(patch_path)
        ]

        logger.info(f"Creating xdelta patch for bundle: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **get_subprocess_args()
        )

        # Monitor progress
        last_size_mb = 0
        while process.poll() is None:
            time.sleep(1)
            try:
                if patch_path.exists():
                    current_size = patch_path.stat().st_size
                    current_size_mb = current_size / (1024 * 1024)
                    if int(current_size_mb) != int(last_size_mb):
                        socketio.emit('bundle_export_progress', {
                            'export_id': export_id,
                            'percentage': 30,
                            'message': f'Creating patch... ({current_size_mb:.1f} MB)'
                        })
                        last_size_mb = current_size_mb
            except:
                pass

        stdout, stderr = process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else stdout.decode() if stdout else 'Unknown xdelta error'
            logger.error(f"xdelta3 failed: {error_msg}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            socketio.emit('bundle_export_error', {
                'export_id': export_id,
                'error': f'Failed to create patch: {error_msg}'
            })
            return

        socketio.emit('bundle_export_progress', {
            'export_id': export_id,
            'percentage': 50,
            'message': 'Copying textures...'
        })

        # 2. Copy textures
        textures_dir = bundle_dir / 'textures'
        texture_count = 0

        if texture_pack_path and Path(texture_pack_path).exists():
            texture_src = Path(texture_pack_path)
            textures_dir.mkdir()

            # Copy all PNG files
            png_files = list(texture_src.glob('*.png'))
            total_textures = len(png_files)

            for i, png_file in enumerate(png_files):
                shutil.copy2(png_file, textures_dir / png_file.name)
                texture_count += 1

                if i % 20 == 0:
                    progress = 50 + int((i / max(total_textures, 1)) * 30)
                    socketio.emit('bundle_export_progress', {
                        'export_id': export_id,
                        'percentage': progress,
                        'message': f'Copying textures... ({i}/{total_textures})'
                    })

        socketio.emit('bundle_export_progress', {
            'export_id': export_id,
            'percentage': 85,
            'message': 'Creating manifest...'
        })

        # 3. Copy image if provided (include in bundle)
        if image_path and Path(image_path).exists():
            shutil.copy(image_path, bundle_dir / 'image.png')

        # 4. Create manifest.json
        manifest = {
            'version': '1.0',
            'name': name,
            'description': description,
            'build_name': build_name,
            'created': datetime.now().isoformat(),
            'texture_count': texture_count,
            'has_image': image_path and Path(image_path).exists()
        }

        with open(bundle_dir / 'manifest.json', 'w') as f:
            json.dump(manifest, f, indent=2)

        socketio.emit('bundle_export_progress', {
            'export_id': export_id,
            'percentage': 90,
            'message': 'Packaging bundle...'
        })

        # 5. Create .ssbm ZIP - use export_id as the bundle ID for storage
        bundle_id = export_id
        bundle_filename = f"{bundle_id}.ssbm"
        bundle_path = BUNDLE_PATH / bundle_filename

        with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in bundle_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(bundle_dir)
                    zf.write(file_path, arcname)

        # Cleanup temp
        shutil.rmtree(temp_dir, ignore_errors=True)

        bundle_size = bundle_path.stat().st_size
        bundle_size_mb = bundle_size / (1024 * 1024)

        # 6. Also save image separately for display in UI
        if image_path and Path(image_path).exists():
            image_dest = BUNDLE_PATH / f"{bundle_id}.png"
            shutil.copy(image_path, image_dest)
            # Delete temp image
            os.remove(image_path)

        # 7. Save to metadata
        bundles = load_bundle_metadata()
        bundles.append({
            'id': bundle_id,
            'name': name,
            'description': description,
            'build_name': build_name,
            'filename': bundle_filename,
            'size': bundle_size,
            'size_mb': round(bundle_size_mb, 2),
            'texture_count': texture_count,
            'created': datetime.now().isoformat()
        })
        save_bundle_metadata(bundles)

        # Create user-friendly filename for download
        safe_name = re.sub(r'[^\w\-_]', '_', name)
        download_filename = f"{safe_name}.ssbm"

        logger.info(f"[OK] Created bundle: {bundle_filename} ({bundle_size_mb:.2f} MB)")
        logger.info(f"  Bundle saved to: {bundle_path}")
        logger.info(f"  Bundle ID: {bundle_id}")

        socketio.emit('bundle_export_complete', {
            'export_id': export_id,
            'bundle_id': bundle_id,
            'filename': download_filename,
            'size': bundle_size,
            'size_mb': round(bundle_size_mb, 2),
            'texture_count': texture_count
        })

    except Exception as e:
        logger.error(f"Bundle export thread error: {str(e)}", exc_info=True)
        socketio.emit('bundle_export_error', {
            'export_id': export_id,
            'error': str(e)
        })


def run_bundle_import(import_id, bundle_path, slippi_path, vanilla_iso_path, delete_on_complete=True):
    """Background thread function to import .ssbm bundle"""
    socketio = get_socketio()
    try:
        socketio.emit('bundle_import_progress', {
            'import_id': import_id,
            'percentage': 0,
            'message': 'Extracting bundle...'
        })

        # 1. Extract ZIP to temp
        temp_dir = Path(tempfile.mkdtemp(prefix='bundle_import_'))

        with zipfile.ZipFile(bundle_path, 'r') as zf:
            zf.extractall(temp_dir)

        # 2. Validate manifest.json and patch.xdelta exist
        manifest_path = temp_dir / 'manifest.json'
        patch_path = temp_dir / 'patch.xdelta'

        if not manifest_path.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            socketio.emit('bundle_import_error', {
                'import_id': import_id,
                'error': 'Invalid bundle: manifest.json not found'
            })
            return

        if not patch_path.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            socketio.emit('bundle_import_error', {
                'import_id': import_id,
                'error': 'Invalid bundle: patch.xdelta not found'
            })
            return

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        build_name = manifest.get('build_name', 'imported-mod')
        mod_name = manifest.get('name', 'Imported Mod')

        socketio.emit('bundle_import_progress', {
            'import_id': import_id,
            'percentage': 10,
            'message': 'Building ISO from patch...'
        })

        # 3. Run xdelta3 to build ISO
        dolphin_ini = os.path.join(slippi_path, 'User', 'Config', 'Dolphin.ini')
        iso_folder = parse_dolphin_ini_iso_path(dolphin_ini)

        if not iso_folder:
            # Fallback: use a default location
            iso_folder = os.path.join(slippi_path, 'User', 'Games')
            os.makedirs(iso_folder, exist_ok=True)

        # Output ISO path
        safe_name = re.sub(r'[^\w\-_]', '_', mod_name)
        output_iso_path = Path(iso_folder) / f"{safe_name}.iso"

        # Find xdelta executable
        if os.name == 'nt':
            if getattr(sys, 'frozen', False):
                xdelta_exe = RESOURCES_DIR / "utility" / "xdelta" / "xdelta3.exe"
            else:
                xdelta_exe = PROJECT_ROOT / "utility" / "xdelta" / "xdelta3.exe"
            if not xdelta_exe.exists():
                xdelta_exe = "xdelta3"
        else:
            xdelta_exe = "xdelta3"

        cmd = [
            str(xdelta_exe),
            '-d',  # Decode/decompress
            '-f',  # Force overwrite
            '-s', str(vanilla_iso_path),
            str(patch_path),
            str(output_iso_path)
        ]

        logger.info(f"Building ISO from bundle: {' '.join(cmd)}")

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **get_subprocess_args()
        )

        # Monitor progress by checking output file size
        expected_size = Path(vanilla_iso_path).stat().st_size
        last_progress = 0

        while process.poll() is None:
            time.sleep(0.3)
            try:
                if output_iso_path.exists():
                    current_size = output_iso_path.stat().st_size
                    progress = min(int((current_size / expected_size) * 60) + 10, 69)
                    if progress != last_progress:
                        socketio.emit('bundle_import_progress', {
                            'import_id': import_id,
                            'percentage': progress,
                            'message': f'Building ISO... {progress - 10}%'
                        })
                        last_progress = progress
            except:
                pass

        stdout, stderr = process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else stdout.decode() if stdout else 'Unknown xdelta error'
            logger.error(f"xdelta3 failed: {error_msg}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            socketio.emit('bundle_import_error', {
                'import_id': import_id,
                'error': f'Failed to build ISO: {error_msg}'
            })
            return

        socketio.emit('bundle_import_progress', {
            'import_id': import_id,
            'percentage': 70,
            'message': 'Copying textures...'
        })

        # 4. Copy textures to Load folder
        textures_src = temp_dir / 'textures'
        texture_count = 0

        if textures_src.exists():
            load_path = Path(slippi_path) / 'User' / 'Load' / 'Textures' / 'GALE01' / build_name
            load_path.mkdir(parents=True, exist_ok=True)

            png_files = list(textures_src.glob('*.png'))
            total_textures = len(png_files)

            for i, png_file in enumerate(png_files):
                shutil.copy2(png_file, load_path / png_file.name)
                texture_count += 1

                if i % 20 == 0:
                    progress = 70 + int((i / max(total_textures, 1)) * 20)
                    socketio.emit('bundle_import_progress', {
                        'import_id': import_id,
                        'percentage': progress,
                        'message': f'Copying textures... ({i}/{total_textures})'
                    })

        socketio.emit('bundle_import_progress', {
            'import_id': import_id,
            'percentage': 95,
            'message': 'Enabling hi-res textures...'
        })

        # 5. Enable HiresTextures=True in GFX.ini
        set_dolphin_texture_settings(slippi_path, dump_textures=False, hires_textures=True)

        # Cleanup temp extraction directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        # Delete temp bundle file (only if it's an uploaded file, not from storage)
        if delete_on_complete and bundle_path.exists():
            os.remove(bundle_path)

        logger.info(f"[OK] Imported bundle: {mod_name}")
        logger.info(f"  ISO: {output_iso_path}")
        logger.info(f"  Textures: {texture_count}")

        socketio.emit('bundle_import_complete', {
            'import_id': import_id,
            'name': mod_name,
            'iso_path': str(output_iso_path),
            'texture_count': texture_count
        })

    except Exception as e:
        logger.error(f"Bundle import thread error: {str(e)}", exc_info=True)
        # Cleanup temp bundle on error (only if it's a temp file)
        if delete_on_complete and bundle_path.exists():
            os.remove(bundle_path)
        socketio.emit('bundle_import_error', {
            'import_id': import_id,
            'error': str(e)
        })


@bundles_bp.route('/api/mex/bundle/list', methods=['GET'])
def list_bundles():
    """List all bundles in storage"""
    try:
        bundles = load_bundle_metadata()

        # Add image URLs
        for bundle in bundles:
            bundle_id = bundle.get('id')
            if bundle_id:
                image_path = BUNDLE_PATH / f"{bundle_id}.png"
                if image_path.exists():
                    bundle['imageUrl'] = f"/storage/bundles/{bundle_id}.png"
                else:
                    bundle['imageUrl'] = None

        return jsonify({
            'success': True,
            'bundles': bundles
        })
    except Exception as e:
        logger.error(f"List bundles error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bundles_bp.route('/api/mex/bundle/delete/<bundle_id>', methods=['POST'])
def delete_bundle(bundle_id):
    """Delete a bundle"""
    try:
        # Remove from metadata
        bundles = load_bundle_metadata()
        bundles = [b for b in bundles if b['id'] != bundle_id]
        save_bundle_metadata(bundles)

        # Delete files
        bundle_path = BUNDLE_PATH / f"{bundle_id}.ssbm"
        image_path = BUNDLE_PATH / f"{bundle_id}.png"

        if bundle_path.exists():
            os.remove(bundle_path)
        if image_path.exists():
            os.remove(image_path)

        logger.info(f"[OK] Deleted bundle: {bundle_id}")

        return jsonify({
            'success': True
        })
    except Exception as e:
        logger.error(f"Delete bundle error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bundles_bp.route('/api/mex/bundle/update/<bundle_id>', methods=['POST'])
def update_bundle(bundle_id):
    """Update a bundle's name and description"""
    try:
        data = request.json
        name = data.get('name')
        description = data.get('description', '')

        if not name:
            return jsonify({
                'success': False,
                'error': 'Name is required'
            }), 400

        bundles = load_bundle_metadata()
        bundle = next((b for b in bundles if b['id'] == bundle_id), None)

        if not bundle:
            return jsonify({
                'success': False,
                'error': 'Bundle not found'
            }), 404

        bundle['name'] = name
        bundle['description'] = description
        save_bundle_metadata(bundles)

        logger.info(f"[OK] Updated bundle: {bundle_id}")

        return jsonify({
            'success': True
        })
    except Exception as e:
        logger.error(f"Update bundle error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bundles_bp.route('/api/mex/bundle/update-image/<bundle_id>', methods=['POST'])
def update_bundle_image(bundle_id):
    """Update a bundle's image"""
    try:
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400

        image_file = request.files['image']

        # Verify bundle exists
        bundles = load_bundle_metadata()
        bundle = next((b for b in bundles if b['id'] == bundle_id), None)

        if not bundle:
            return jsonify({
                'success': False,
                'error': 'Bundle not found'
            }), 404

        # Save image
        image_path = BUNDLE_PATH / f"{bundle_id}.png"
        image_file.save(str(image_path))

        return jsonify({
            'success': True,
            'imageUrl': f"/storage/bundles/{bundle_id}.png"
        })
    except Exception as e:
        logger.error(f"Update bundle image error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bundles_bp.route('/api/mex/bundle/export', methods=['POST'])
def export_bundle():
    """Export a .ssbm bundle (xdelta patch + texture pack)"""
    try:
        # Handle both JSON and FormData
        if request.content_type and 'multipart/form-data' in request.content_type:
            name = request.form.get('name', 'My Mod Pack')
            description = request.form.get('description', '')
            build_name = request.form.get('buildName', 'mod-pack')
            vanilla_iso_path = request.form.get('vanillaIsoPath')
            exported_iso_path = request.form.get('exportedIsoPath')
            texture_pack_path = request.form.get('texturePackPath') or None
            image_file = request.files.get('image')
        else:
            data = request.json or {}
            name = data.get('name', 'My Mod Pack')
            description = data.get('description', '')
            build_name = data.get('buildName', 'mod-pack')
            vanilla_iso_path = data.get('vanillaIsoPath')
            exported_iso_path = data.get('exportedIsoPath')
            texture_pack_path = data.get('texturePackPath') or None
            image_file = None

        if not vanilla_iso_path:
            return jsonify({
                'success': False,
                'error': 'No vanilla ISO path provided'
            }), 400

        if not exported_iso_path:
            return jsonify({
                'success': False,
                'error': 'No exported ISO path provided'
            }), 400

        vanilla_iso = Path(vanilla_iso_path)
        exported_iso = Path(exported_iso_path)

        if not vanilla_iso.exists():
            return jsonify({
                'success': False,
                'error': f'Vanilla ISO not found: {vanilla_iso_path}'
            }), 404

        if not exported_iso.exists():
            return jsonify({
                'success': False,
                'error': f'Exported ISO not found: {exported_iso_path}'
            }), 404

        # Generate unique ID for this export session (also used as bundle ID)
        export_id = str(uuid.uuid4())[:8]

        # Save image to temp if provided
        image_path = None
        if image_file and image_file.filename:
            image_path = OUTPUT_PATH / f"temp_bundle_image_{export_id}.png"
            image_file.save(str(image_path))

        logger.info(f"Exporting bundle: {name}")
        logger.info(f"  Vanilla ISO: {vanilla_iso_path}")
        logger.info(f"  Exported ISO: {exported_iso_path}")
        logger.info(f"  Texture pack: {texture_pack_path}")
        logger.info(f"  Image: {image_path}")

        # Run in background thread
        thread = threading.Thread(
            target=run_bundle_export,
            args=(export_id, name, description, build_name, vanilla_iso_path, exported_iso_path, texture_pack_path, str(image_path) if image_path else None)
        )
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Bundle export started',
            'export_id': export_id
        })
    except Exception as e:
        logger.error(f"Export bundle error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bundles_bp.route('/api/mex/bundle/download/<bundle_id>', methods=['GET'])
def download_bundle(bundle_id):
    """Download a .ssbm bundle file"""
    try:
        # Look up bundle in metadata to get the name for download
        bundles = load_bundle_metadata()
        bundle = next((b for b in bundles if b['id'] == bundle_id), None)

        # Try .ssbm extension
        file_path = BUNDLE_PATH / f"{bundle_id}.ssbm"

        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'Bundle file not found'
            }), 404

        # Use bundle name for download filename
        if bundle:
            safe_name = re.sub(r'[^\w\-_]', '_', bundle['name'])
            download_name = f"{safe_name}.ssbm"
        else:
            download_name = f"{bundle_id}.ssbm"

        return send_file(
            file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        logger.error(f"Download bundle error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bundles_bp.route('/api/mex/bundle/install/<bundle_id>', methods=['POST'])
def install_bundle_from_storage(bundle_id):
    """Install a bundle from storage (builds ISO + copies textures)"""
    try:
        data = request.json
        slippi_path = data.get('slippiPath')
        vanilla_iso_path = data.get('vanillaIsoPath')

        if not slippi_path:
            return jsonify({
                'success': False,
                'error': 'Slippi Dolphin path is required'
            }), 400

        if not vanilla_iso_path:
            return jsonify({
                'success': False,
                'error': 'Vanilla ISO path is required'
            }), 400

        if not Path(vanilla_iso_path).exists():
            return jsonify({
                'success': False,
                'error': f'Vanilla ISO not found: {vanilla_iso_path}'
            }), 404

        # Find bundle file
        bundle_path = BUNDLE_PATH / f"{bundle_id}.ssbm"

        if not bundle_path.exists():
            return jsonify({
                'success': False,
                'error': 'Bundle file not found'
            }), 404

        # Generate unique ID for tracking
        import_id = str(uuid.uuid4())[:8]

        logger.info(f"[BUNDLE INSTALL] Starting install from storage: {bundle_id}, import_id={import_id}")

        # Run import in background thread (don't delete stored bundle)
        thread = threading.Thread(
            target=run_bundle_import,
            args=(import_id, bundle_path, slippi_path, vanilla_iso_path, False)
        )
        thread.start()

        return jsonify({
            'success': True,
            'import_id': import_id
        })
    except Exception as e:
        logger.error(f"Install bundle error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bundles_bp.route('/api/mex/bundle/import', methods=['POST'])
def import_bundle():
    """Import a .ssbm bundle to storage (saves file + metadata, does NOT install)"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400

        file = request.files['file']

        if not file.filename:
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        if not file.filename.lower().endswith('.ssbm'):
            return jsonify({
                'success': False,
                'error': 'File must be a .ssbm bundle'
            }), 400

        # Generate unique ID for storage
        bundle_id = str(uuid.uuid4())[:8]

        # Save bundle file to storage
        bundle_path = BUNDLE_PATH / f"{bundle_id}.ssbm"
        file.save(str(bundle_path))

        # Extract manifest info from the bundle
        try:
            with zipfile.ZipFile(bundle_path, 'r') as zf:
                manifest_data = zf.read('manifest.json')
                manifest = json.loads(manifest_data)
        except Exception as e:
            # If we can't read manifest, delete the file and fail
            if bundle_path.exists():
                os.remove(bundle_path)
            return jsonify({
                'success': False,
                'error': f'Invalid bundle: {str(e)}'
            }), 400

        # Get file size
        file_size = bundle_path.stat().st_size

        # Count textures in bundle
        texture_count = 0
        try:
            with zipfile.ZipFile(bundle_path, 'r') as zf:
                texture_count = len([n for n in zf.namelist() if n.startswith('textures/') and n.endswith('.png')])
        except:
            pass

        # Extract image if present in bundle
        try:
            with zipfile.ZipFile(bundle_path, 'r') as zf:
                if 'image.png' in zf.namelist():
                    image_data = zf.read('image.png')
                    image_dest = BUNDLE_PATH / f"{bundle_id}.png"
                    with open(image_dest, 'wb') as f:
                        f.write(image_data)
                    logger.info(f"Extracted image from bundle: {image_dest}")
        except Exception as e:
            logger.warning(f"Failed to extract image from bundle: {e}")

        # Save to metadata
        bundles = load_bundle_metadata()
        bundles.append({
            'id': bundle_id,
            'name': manifest.get('name', file.filename.replace('.ssbm', '')),
            'description': manifest.get('description', ''),
            'size': file_size,
            'size_mb': round(file_size / (1024 * 1024), 2),
            'texture_count': texture_count,
            'created': datetime.now().isoformat()
        })
        save_bundle_metadata(bundles)

        logger.info(f"[OK] Imported bundle to storage: {bundle_id} - {manifest.get('name', 'Unknown')}")

        return jsonify({
            'success': True,
            'bundle_id': bundle_id,
            'name': manifest.get('name', file.filename.replace('.ssbm', '')),
            'message': 'Bundle saved to storage'
        })
    except Exception as e:
        logger.error(f"Import bundle error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bundles_bp.route('/api/mex/bundle/preview', methods=['POST'])
def preview_bundle():
    """Preview a .ssbm bundle without importing it"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400

        file = request.files['file']

        if not file.filename or not file.filename.lower().endswith('.ssbm'):
            return jsonify({
                'success': False,
                'error': 'File must be a .ssbm bundle'
            }), 400

        # Read manifest from ZIP without extracting
        try:
            with zipfile.ZipFile(file, 'r') as zf:
                if 'manifest.json' not in zf.namelist():
                    return jsonify({
                        'success': False,
                        'error': 'Invalid bundle: manifest.json not found'
                    }), 400

                with zf.open('manifest.json') as mf:
                    manifest = json.load(mf)

                # Check for patch.xdelta
                has_patch = 'patch.xdelta' in zf.namelist()

                # Count textures
                texture_count = len([n for n in zf.namelist() if n.startswith('textures/') and n.endswith('.png')])

            return jsonify({
                'success': True,
                'manifest': manifest,
                'has_patch': has_patch,
                'texture_count': texture_count
            })
        except zipfile.BadZipFile:
            return jsonify({
                'success': False,
                'error': 'Invalid bundle: not a valid ZIP file'
            }), 400

    except Exception as e:
        logger.error(f"Preview bundle error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
