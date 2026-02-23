"""
Storage Costumes Blueprint - Storage vault costume operations.

Handles listing, deleting, renaming, CSP management, stock icons,
Slippi testing, reordering, and folder management for stored costumes.
"""

import os
import json
import time
import uuid
import re
import shutil
import zipfile
import tempfile
import logging
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify

from core.config import PROJECT_ROOT, STORAGE_PATH, VANILLA_ASSETS_DIR, PROCESSOR_DIR, SERVICES_DIR
from core.constants import get_char_prefix

import sys
sys.path.insert(0, str(PROCESSOR_DIR))
from generate_csp import generate_csp, generate_single_csp_internal, find_character_assets, apply_character_specific_layers

sys.path.insert(0, str(SERVICES_DIR))
from dat_processor import validate_for_slippi

logger = logging.getLogger(__name__)

storage_costumes_bp = Blueprint('storage_costumes', __name__)


def find_folder_in_skins(skins, folder_id):
    """Find a folder by ID in the skins array."""
    for i, item in enumerate(skins):
        if item.get('type') == 'folder' and item.get('id') == folder_id:
            return item, i
    return None, -1


def get_folder_id_at_position(skins, position):
    """Determine folder membership based on position."""
    for i in range(position - 1, -1, -1):
        item = skins[i]
        if item.get('type') == 'folder':
            return item['id']
        if item.get('folder_id'):
            return item['folder_id']
        return None
    return None


@storage_costumes_bp.route('/api/mex/storage/metadata', methods=['GET'])
def get_storage_metadata():
    """Get storage metadata.json"""
    try:
        metadata_file = STORAGE_PATH / 'metadata.json'

        if not metadata_file.exists():
            return jsonify({
                'success': True,
                'metadata': {'characters': {}}
            })

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        return jsonify({
            'success': True,
            'metadata': metadata
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@storage_costumes_bp.route('/api/mex/storage/costumes', methods=['GET'])
def list_storage_costumes():
    """List all costumes in storage with MEX-compatible ZIPs."""
    try:
        character = request.args.get('character')
        costumes = []

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': True, 'costumes': []})

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        characters_data = metadata.get('characters', {})
        if character:
            characters_data = {character: characters_data.get(character, {})}

        for char_name, char_data in characters_data.items():
            skins = char_data.get('skins', [])

            for skin in skins:
                if skin.get('type') == 'folder':
                    continue
                if skin.get('visible') is False:
                    continue

                zip_path = STORAGE_PATH / char_name / skin.get('filename', '')
                if zip_path.exists():
                    alternate_csps = []
                    for alt in skin.get('alternate_csps', []):
                        alternate_csps.append({
                            'id': alt.get('id'),
                            'url': f"/storage/{char_name}/{alt.get('filename')}",
                            'pose_name': alt.get('pose_name'),
                            'is_hd': alt.get('is_hd', False),
                            'timestamp': alt.get('timestamp')
                        })

                    costume_data = {
                        'character': char_name,
                        'name': f"{char_name} - {skin.get('color', 'Custom')}",
                        'folder': skin['id'],
                        'costumeCode': skin['costume_code'],
                        'zipPath': str(zip_path.relative_to(PROJECT_ROOT)),
                        'cspUrl': f"/storage/{char_name}/{skin['id']}_csp.png" if skin.get('has_csp') else None,
                        'stockUrl': f"/storage/{char_name}/{skin['id']}_stc.png" if skin.get('has_stock') else None,
                        'alternateCsps': alternate_csps,
                        'isPopo': skin.get('is_popo', False),
                        'isNana': skin.get('is_nana', False),
                        'pairedNanaId': skin.get('paired_nana_id'),
                        'pairedPopoId': skin.get('paired_popo_id'),
                        'slippiSafe': skin.get('slippi_safe', False)
                    }
                    costumes.append(costume_data)

        return jsonify({'success': True, 'costumes': costumes})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/costumes/delete', methods=['POST'])
def delete_storage_costume():
    """Delete character costume from storage"""
    try:
        data = request.json
        character = data.get('character')
        skin_id = data.get('skinId')

        if not character or not skin_id:
            return jsonify({'success': False, 'error': 'Missing character or skinId parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if character not in metadata.get('characters', {}):
            return jsonify({'success': False, 'error': f'Character {character} not found in metadata'}), 404

        char_data = metadata['characters'][character]
        skins = char_data.get('skins', [])
        skin_to_delete = None
        skin_index = None

        for idx, skin in enumerate(skins):
            if skin['id'] == skin_id:
                skin_to_delete = skin
                skin_index = idx
                break

        if not skin_to_delete:
            return jsonify({'success': False, 'error': f'Skin {skin_id} not found for {character}'}), 404

        char_folder = STORAGE_PATH / character
        zip_file = char_folder / skin_to_delete['filename']
        csp_file = char_folder / f"{skin_id}_csp.png"
        stc_file = char_folder / f"{skin_id}_stc.png"

        deleted_files = []
        if zip_file.exists():
            zip_file.unlink()
            deleted_files.append(str(zip_file))
        if csp_file.exists():
            csp_file.unlink()
            deleted_files.append(str(csp_file))
        if stc_file.exists():
            stc_file.unlink()
            deleted_files.append(str(stc_file))

        skins.pop(skin_index)

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Deleted costume {skin_id} for {character}")
        return jsonify({'success': True, 'message': f'Successfully deleted {skin_id}', 'deleted_files': deleted_files})
    except Exception as e:
        logger.error(f"Delete costume error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/costumes/rename', methods=['POST'])
def rename_storage_costume():
    """Rename character costume (update color field)"""
    try:
        data = request.json
        character = data.get('character')
        skin_id = data.get('skinId')
        new_name = data.get('newName')

        if not character or not skin_id or not new_name:
            return jsonify({'success': False, 'error': 'Missing character, skinId, or newName parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if character not in metadata.get('characters', {}):
            return jsonify({'success': False, 'error': f'Character {character} not found in metadata'}), 404

        char_data = metadata['characters'][character]
        skins = char_data.get('skins', [])
        skin_found = False

        for skin in skins:
            if skin['id'] == skin_id:
                skin['color'] = new_name
                skin_found = True
                break

        if not skin_found:
            return jsonify({'success': False, 'error': f'Skin {skin_id} not found for {character}'}), 404

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Renamed costume {skin_id} to '{new_name}'")
        return jsonify({'success': True, 'message': f'Successfully renamed to {new_name}'})
    except Exception as e:
        logger.error(f"Rename costume error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/costumes/update-csp', methods=['POST'])
def update_costume_csp():
    """Update CSP image for a character costume (normal or HD)"""
    try:
        character = request.form.get('character')
        skin_id = request.form.get('skinId')
        is_hd = request.form.get('isHd', '').lower() == 'true'

        if not character or not skin_id:
            return jsonify({'success': False, 'error': 'Missing character or skinId parameter'}), 400

        if 'csp' not in request.files:
            return jsonify({'success': False, 'error': 'No CSP file provided'}), 400

        csp_file = request.files['csp']
        if csp_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not csp_file.content_type.startswith('image/'):
            return jsonify({'success': False, 'error': 'File must be an image'}), 400

        csp_data = csp_file.read()
        char_folder = STORAGE_PATH / character
        zip_path = char_folder / f"{skin_id}.zip"

        if not zip_path.exists():
            return jsonify({'success': False, 'error': f'Costume zip not found: {skin_id}'}), 404

        # Derive file extension from MIME type to preserve original format (e.g. GIF)
        ext_map = {
            'image/gif': '.gif', 'image/png': '.png', 'image/jpeg': '.jpg',
            'image/webp': '.webp', 'image/bmp': '.bmp'
        }
        ext = ext_map.get(csp_file.content_type, '.png')

        if is_hd:
            hd_csp_filename = f"{skin_id}_csp_hd{ext}"
            standalone_hd_csp = char_folder / hd_csp_filename
            with open(standalone_hd_csp, 'wb') as f:
                f.write(csp_data)

            metadata_file = STORAGE_PATH / 'metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

                if character in metadata.get('characters', {}):
                    for skin in metadata['characters'][character].get('skins', []):
                        if skin['id'] == skin_id:
                            skin['has_hd_csp'] = True
                            skin['hd_csp_source'] = 'custom'
                            skin['hd_csp_filename'] = hd_csp_filename
                            break

                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)

            logger.info(f"[OK] Updated HD CSP for {character} - {skin_id}")
        else:
            csp_filename = f"{skin_id}_csp{ext}"
            standalone_csp = char_folder / csp_filename
            with open(standalone_csp, 'wb') as f:
                f.write(csp_data)

            temp_zip = char_folder / f"{skin_id}_temp.zip"
            with zipfile.ZipFile(zip_path, 'r') as source_zip:
                with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as dest_zip:
                    for item in source_zip.infolist():
                        if item.filename.lower() not in ['csp.png', 'csp']:
                            data = source_zip.read(item.filename)
                            dest_zip.writestr(item, data)
                    dest_zip.writestr('csp.png', csp_data)

            zip_path.unlink()
            temp_zip.rename(zip_path)

            metadata_file = STORAGE_PATH / 'metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

                if character in metadata.get('characters', {}):
                    for skin in metadata['characters'][character].get('skins', []):
                        if skin['id'] == skin_id:
                            skin['has_csp'] = True
                            skin['csp_source'] = 'custom'
                            skin['csp_filename'] = csp_filename
                            break

                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)

            logger.info(f"[OK] Updated CSP for {character} - {skin_id}")

        return jsonify({'success': True, 'message': 'CSP updated successfully', 'isHd': is_hd})
    except Exception as e:
        logger.error(f"Update CSP error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/costumes/<character>/<skin_id>/csp/capture-hd', methods=['POST'])
def capture_hd_csp(character, skin_id):
    """Generate HD CSP for a skin at specified resolution"""
    try:
        data = request.get_json() or {}
        scale = data.get('scale', 4)

        if scale not in [2, 4, 8, 16]:
            return jsonify({'success': False, 'error': 'Invalid scale. Must be 2, 4, 8, or 16'}), 400

        logger.info(f"Generating HD CSP for {character}/{skin_id} at {scale}x")

        char_folder = STORAGE_PATH / character
        zip_path = char_folder / f"{skin_id}.zip"

        if not zip_path.exists():
            return jsonify({'success': False, 'error': f'Costume zip not found: {skin_id}'}), 404

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(temp_path)

            dat_files = list(temp_path.glob('*.dat'))
            if not dat_files:
                return jsonify({'success': False, 'error': 'No DAT file found in costume zip'}), 400

            dat_file = dat_files[0]
            hd_csp_path = generate_csp(str(dat_file), scale=scale)

            if not hd_csp_path or not Path(hd_csp_path).exists():
                return jsonify({'success': False, 'error': 'Failed to generate HD CSP'}), 500

            final_hd_csp = char_folder / f"{skin_id}_csp_hd.png"
            shutil.copy2(hd_csp_path, final_hd_csp)

            from PIL import Image
            with Image.open(final_hd_csp) as img:
                width, height = img.size

            metadata_file = STORAGE_PATH / 'metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

                if character in metadata.get('characters', {}):
                    for skin in metadata['characters'][character].get('skins', []):
                        if skin['id'] == skin_id:
                            skin['has_hd_csp'] = True
                            skin['hd_csp_resolution'] = f"{scale}x"
                            skin['hd_csp_size'] = f"{width}x{height}"
                            break

                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)

            logger.info(f"[OK] Generated HD CSP for {character}/{skin_id} at {scale}x ({width}x{height})")
            return jsonify({'success': True, 'message': f'HD CSP generated at {scale}x', 'resolution': f"{scale}x", 'size': f"{width}x{height}"})

    except Exception as e:
        logger.error(f"Capture HD CSP error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/costumes/<character>/<skin_id>/csp/manage', methods=['POST', 'OPTIONS'])
def manage_csp(character, skin_id):
    """Manage CSPs for a skin - swap, remove, add alternatives, regenerate HD"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        if request.content_type and 'multipart/form-data' in request.content_type:
            action = request.form.get('action')
            alt_id = request.form.get('altId')
            scale = int(request.form.get('scale', 4))
            file = request.files.get('file')
        else:
            data = request.get_json() or {}
            action = data.get('action')
            alt_id = data.get('altId')
            scale = data.get('scale', 4)
            target = data.get('target')
            file = None

        logger.info(f"[CSP Manage] {character}/{skin_id} action={action} altId={alt_id}")

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        char_data = metadata.get('characters', {}).get(character, {})
        skins = char_data.get('skins', [])
        skin = next((s for s in skins if s.get('id') == skin_id), None)

        if not skin:
            return jsonify({'success': False, 'error': 'Skin not found'}), 404

        if action == 'swap':
            alt_csps = skin.get('alternate_csps', [])
            alt = next((a for a in alt_csps if a.get('id') == alt_id), None)
            if not alt:
                return jsonify({'success': False, 'error': 'Alt CSP not found'}), 404

            alt_pose = alt.get('pose_name')
            non_hd_alt = next((a for a in alt_csps if a.get('pose_name') == alt_pose and not a.get('is_hd', False)), None)

            if non_hd_alt:
                skin['active_csp_id'] = non_hd_alt.get('id')
            else:
                skin['active_csp_id'] = alt_id

            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"[OK] Set active CSP to: {skin['active_csp_id']}")
            return jsonify({'success': True, 'message': 'Active CSP updated', 'activeCspId': skin['active_csp_id']})

        elif action == 'reset':
            skin['active_csp_id'] = None
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            return jsonify({'success': True, 'message': 'Reset to original CSP', 'activeCspId': None})

        elif action == 'remove':
            alt_csps = skin.get('alternate_csps', [])
            alt = next((a for a in alt_csps if a.get('id') == alt_id), None)
            if not alt:
                return jsonify({'success': False, 'error': 'Alt CSP not found'}), 404

            alt_csp_path = STORAGE_PATH / character / alt.get('filename')
            if alt_csp_path.exists():
                alt_csp_path.unlink()

            skin['alternate_csps'] = [a for a in alt_csps if a.get('id') != alt_id]

            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            return jsonify({'success': True, 'message': 'Alt CSP removed'})

        elif action == 'add':
            if not file:
                return jsonify({'success': False, 'error': 'No file provided'}), 400

            is_hd_upload = request.form.get('isHd', '').lower() == 'true'
            alt_csps = skin.get('alternate_csps', [])
            new_alt_id = f"alt_{int(time.time())}{'_hd' if is_hd_upload else ''}"

            # Preserve original file extension (e.g. .gif for animated GIFs)
            alt_ext_map = {
                'image/gif': '.gif', 'image/png': '.png', 'image/jpeg': '.jpg',
                'image/webp': '.webp', 'image/bmp': '.bmp'
            }
            alt_ext = alt_ext_map.get(file.content_type, '.png')

            if is_hd_upload:
                new_alt_filename = f"{skin_id}_csp_alt_{len(alt_csps) + 1}_hd{alt_ext}"
            else:
                new_alt_filename = f"{skin_id}_csp_alt_{len(alt_csps) + 1}{alt_ext}"

            new_alt_path = STORAGE_PATH / character / new_alt_filename
            file.save(new_alt_path)

            if 'alternate_csps' not in skin:
                skin['alternate_csps'] = []

            skin['alternate_csps'].append({
                'id': new_alt_id,
                'filename': new_alt_filename,
                'pose_name': None,
                'is_hd': is_hd_upload,
                'timestamp': datetime.now().isoformat()
            })

            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            return jsonify({
                'success': True,
                'message': 'Alt CSP added',
                'altId': new_alt_id,
                'url': f"/storage/{character}/{new_alt_filename}",
                'isHd': is_hd_upload
            })

        elif action == 'regenerate-hd':
            zip_path = STORAGE_PATH / character / skin.get('filename', '')
            if not zip_path.exists():
                return jsonify({'success': False, 'error': 'Skin ZIP not found'}), 404

            pose_name = None
            is_main = target == 'main' or not alt_id

            if not is_main:
                alt_csps = skin.get('alternate_csps', [])
                alt = next((a for a in alt_csps if a.get('id') == alt_id), None)
                if not alt:
                    return jsonify({'success': False, 'error': 'Alt CSP not found'}), 404
                pose_name = alt.get('pose_name')

            anim_file = None
            camera_file = None

            if pose_name:
                pose_path = VANILLA_ASSETS_DIR / 'custom_poses' / character / f"{pose_name}.yml"
                if pose_path.exists():
                    anim_file = str(pose_path)
                    char_prefix = get_char_prefix(character)
                    if char_prefix:
                        aj_file = VANILLA_ASSETS_DIR / character / f"{char_prefix}AJ.dat"
                        if aj_file.exists():
                            camera_file = str(aj_file)

            if not anim_file:
                default_anim, default_camera = find_character_assets(character)
                if default_anim:
                    anim_file = default_anim
                if default_camera:
                    camera_file = default_camera

            temp_dir = tempfile.mkdtemp(prefix='csp_regen_')
            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(temp_dir)

                dat_file = None
                for root, dirs, files in os.walk(temp_dir):
                    for file_name in files:
                        if file_name.endswith('.dat') and file_name.startswith('Pl'):
                            dat_file = Path(root) / file_name
                            break
                    if dat_file:
                        break

                if not dat_file:
                    return jsonify({'success': False, 'error': 'No DAT file found in ZIP'}), 400

                csp_output = generate_single_csp_internal(str(dat_file), character, anim_file, camera_file, scale)

                if not csp_output or not Path(csp_output).exists():
                    return jsonify({'success': False, 'error': 'CSP generation failed'}), 500

                apply_character_specific_layers(csp_output, character, scale)

                if is_main:
                    output_path = STORAGE_PATH / character / f"{skin_id}_csp_hd.png"
                    from PIL import Image
                    with Image.open(csp_output) as img:
                        width, height = img.size
                    skin['has_hd_csp'] = True
                    skin['hd_csp_resolution'] = f"{scale}x"
                    skin['hd_csp_size'] = f"{width}x{height}"
                    shutil.move(csp_output, output_path)
                else:
                    alt_csps = skin.get('alternate_csps', [])
                    existing_hd = next((a for a in alt_csps if a.get('pose_name') == pose_name and a.get('is_hd', False)), None)

                    if existing_hd:
                        output_path = STORAGE_PATH / character / existing_hd.get('filename')
                        shutil.move(csp_output, output_path)
                    else:
                        new_hd_id = f"alt_{int(time.time())}_hd"
                        new_hd_filename = f"{skin_id}_csp_alt_{len(alt_csps) + 1}_hd.png"
                        output_path = STORAGE_PATH / character / new_hd_filename
                        shutil.move(csp_output, output_path)
                        alt_csps.append({
                            'id': new_hd_id,
                            'filename': new_hd_filename,
                            'pose_name': pose_name,
                            'is_hd': True,
                            'timestamp': datetime.now().isoformat()
                        })
                        skin['alternate_csps'] = alt_csps

                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)

                return jsonify({'success': True, 'message': f'HD CSP regenerated at {scale}x', 'isHd': True, 'isMain': is_main})

            finally:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)

        else:
            return jsonify({'success': False, 'error': f'Unknown action: {action}'}), 400

    except Exception as e:
        logger.error(f"CSP manage error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/costumes/update-stock', methods=['POST'])
def update_costume_stock():
    """Update stock icon for a character costume"""
    try:
        character = request.form.get('character')
        skin_id = request.form.get('skinId')

        if not character or not skin_id:
            return jsonify({'success': False, 'error': 'Missing character or skinId parameter'}), 400

        if 'stock' not in request.files:
            return jsonify({'success': False, 'error': 'No stock file provided'}), 400

        stock_file = request.files['stock']
        if stock_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not stock_file.content_type.startswith('image/'):
            return jsonify({'success': False, 'error': 'File must be an image'}), 400

        stock_data = stock_file.read()
        char_folder = STORAGE_PATH / character
        zip_path = char_folder / f"{skin_id}.zip"
        standalone_stock = char_folder / f"{skin_id}_stc.png"

        if not zip_path.exists():
            return jsonify({'success': False, 'error': f'Costume zip not found: {skin_id}'}), 404

        with open(standalone_stock, 'wb') as f:
            f.write(stock_data)

        temp_zip = char_folder / f"{skin_id}_temp.zip"
        with zipfile.ZipFile(zip_path, 'r') as source_zip:
            with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as dest_zip:
                for item in source_zip.infolist():
                    if item.filename.lower() not in ['stc.png', 'stock.png', 'stock']:
                        data = source_zip.read(item.filename)
                        dest_zip.writestr(item, data)
                dest_zip.writestr('stc.png', stock_data)

        zip_path.unlink()
        temp_zip.rename(zip_path)

        metadata_file = STORAGE_PATH / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            if character in metadata.get('characters', {}):
                for skin in metadata['characters'][character].get('skins', []):
                    if skin['id'] == skin_id:
                        skin['has_stock'] = True
                        skin['stock_source'] = 'custom'
                        break

                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Updated stock icon for {character} - {skin_id}")
        return jsonify({'success': True, 'message': 'Stock icon updated successfully'})
    except Exception as e:
        logger.error(f"Update stock error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/costumes/retest-slippi', methods=['POST'])
def retest_costume_slippi():
    """Retest a character costume for slippi safety and optionally apply fix"""
    try:
        data = request.json
        character = data.get('character')
        skin_id = data.get('skinId')
        auto_fix = data.get('autoFix', False)

        if not character or not skin_id:
            return jsonify({'success': False, 'error': 'Missing character or skinId parameter'}), 400

        char_folder = STORAGE_PATH / character
        zip_path = char_folder / f"{skin_id}.zip"

        if not zip_path.exists():
            return jsonify({'success': False, 'error': f'Costume zip not found: {skin_id}'}), 404

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            dat_files = [f for f in zip_ref.namelist() if f.lower().endswith('.dat')]
            if not dat_files:
                return jsonify({'success': False, 'error': 'No DAT file found in costume ZIP'}), 400

            dat_filename = dat_files[0]
            dat_data = zip_ref.read(dat_filename)

        with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as tmp_dat:
            tmp_dat.write(dat_data)
            tmp_dat_path = tmp_dat.name

        try:
            validation = validate_for_slippi(tmp_dat_path, auto_fix=auto_fix)

            if auto_fix and validation.get('fix_applied'):
                with open(tmp_dat_path, 'rb') as f:
                    fixed_dat_data = f.read()

                temp_zip = char_folder / f"{skin_id}_temp.zip"
                with zipfile.ZipFile(zip_path, 'r') as source_zip:
                    with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as dest_zip:
                        for item in source_zip.infolist():
                            if item.filename.lower().endswith('.dat'):
                                dest_zip.writestr(item.filename, fixed_dat_data)
                            else:
                                data = source_zip.read(item.filename)
                                dest_zip.writestr(item, data)

                zip_path.unlink()
                temp_zip.rename(zip_path)

        finally:
            try:
                os.unlink(tmp_dat_path)
            except:
                pass

        metadata_file = STORAGE_PATH / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            if character in metadata.get('characters', {}):
                for skin in metadata['characters'][character].get('skins', []):
                    if skin['id'] == skin_id:
                        skin['slippi_safe'] = validation['slippi_safe']
                        skin['slippi_tested'] = True
                        skin['slippi_test_date'] = datetime.now().isoformat()
                        skin['slippi_manual_override'] = None
                        break

                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Retested slippi for {character} - {skin_id}: {validation['slippi_safe']}")
        return jsonify({
            'success': True,
            'slippi_safe': validation['slippi_safe'],
            'message': 'Slippi Safe' if validation['slippi_safe'] else 'Not Slippi Safe'
        })
    except Exception as e:
        logger.error(f"Retest slippi error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/costumes/override-slippi', methods=['POST'])
def override_costume_slippi():
    """Manually override slippi safety status for a character costume"""
    try:
        data = request.json
        character = data.get('character')
        skin_id = data.get('skinId')
        slippi_safe = data.get('slippiSafe')

        if not character or not skin_id or slippi_safe is None:
            return jsonify({'success': False, 'error': 'Missing character, skinId, or slippiSafe parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if character not in metadata.get('characters', {}):
            return jsonify({'success': False, 'error': f'Character {character} not found in metadata'}), 404

        skin_found = False
        for skin in metadata['characters'][character].get('skins', []):
            if skin['id'] == skin_id:
                skin['slippi_safe'] = slippi_safe
                skin['slippi_manual_override'] = True
                skin['slippi_test_date'] = datetime.now().isoformat()
                skin_found = True
                break

        if not skin_found:
            return jsonify({'success': False, 'error': f'Skin {skin_id} not found for {character}'}), 404

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Manually set slippi status for {character} - {skin_id}: {slippi_safe}")
        return jsonify({
            'success': True,
            'slippi_safe': slippi_safe,
            'message': f"Manually set to {'Slippi Safe' if slippi_safe else 'Not Slippi Safe'}"
        })
    except Exception as e:
        logger.error(f"Override slippi error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/costumes/reorder', methods=['POST'])
def reorder_costumes():
    """Reorder character skins in storage."""
    try:
        data = request.json
        character = data.get('character')
        from_index = data.get('fromIndex')
        to_index = data.get('toIndex')

        if character is None or from_index is None or to_index is None:
            return jsonify({'success': False, 'error': 'Missing character, fromIndex, or toIndex parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if character not in metadata.get('characters', {}):
            return jsonify({'success': False, 'error': f'Character {character} not found in metadata'}), 404

        character_data = metadata['characters'][character]
        skins = character_data.get('skins', [])

        if from_index < 0 or from_index >= len(skins) or to_index < 0 or to_index >= len(skins):
            return jsonify({'success': False, 'error': 'Invalid fromIndex or toIndex'}), 400

        item = skins.pop(from_index)
        skins.insert(to_index, item)

        if item.get('type') != 'folder':
            new_folder_id = get_folder_id_at_position(skins, to_index)
            if new_folder_id:
                item['folder_id'] = new_folder_id
            elif 'folder_id' in item:
                del item['folder_id']

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Reordered {character} skins: moved index {from_index} to {to_index}")
        return jsonify({'success': True, 'skins': skins})
    except Exception as e:
        logger.error(f"Reorder costumes error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/costumes/move-to-top', methods=['POST'])
def move_costume_to_top():
    """Move a character skin to the top of the list"""
    try:
        data = request.json
        character = data.get('character')
        skin_id = data.get('skinId')

        if not character or not skin_id:
            return jsonify({'success': False, 'error': 'Missing character or skinId parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if character not in metadata.get('characters', {}):
            return jsonify({'success': False, 'error': f'Character {character} not found in metadata'}), 404

        character_data = metadata['characters'][character]
        skins = character_data.get('skins', [])

        skin_index = None
        for i, skin in enumerate(skins):
            if skin['id'] == skin_id:
                skin_index = i
                break

        if skin_index is None:
            return jsonify({'success': False, 'error': f'Skin {skin_id} not found'}), 404

        if skin_index > 0:
            skin = skins.pop(skin_index)
            skins.insert(0, skin)
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"[OK] Moved {character} skin {skin_id} to top")

        return jsonify({'success': True, 'skins': skins})
    except Exception as e:
        logger.error(f"Move costume to top error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/costumes/move-to-bottom', methods=['POST'])
def move_costume_to_bottom():
    """Move a character skin to the bottom of the list"""
    try:
        data = request.json
        character = data.get('character')
        skin_id = data.get('skinId')

        if not character or not skin_id:
            return jsonify({'success': False, 'error': 'Missing character or skinId parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if character not in metadata.get('characters', {}):
            return jsonify({'success': False, 'error': f'Character {character} not found in metadata'}), 404

        character_data = metadata['characters'][character]
        skins = character_data.get('skins', [])

        skin_index = None
        for i, skin in enumerate(skins):
            if skin['id'] == skin_id:
                skin_index = i
                break

        if skin_index is None:
            return jsonify({'success': False, 'error': f'Skin {skin_id} not found'}), 404

        if skin_index < len(skins) - 1:
            skin = skins.pop(skin_index)
            skins.append(skin)
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"[OK] Moved {character} skin {skin_id} to bottom")

        return jsonify({'success': True, 'skins': skins})
    except Exception as e:
        logger.error(f"Move costume to bottom error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= Folder Management Endpoints =============

@storage_costumes_bp.route('/api/mex/storage/folders/create', methods=['POST'])
def create_folder():
    """Create a new folder for organizing skins."""
    try:
        data = request.json
        character = data.get('character')
        name = data.get('name', 'New Folder')

        if not character:
            return jsonify({'success': False, 'error': 'Missing character parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if character not in metadata.get('characters', {}):
            return jsonify({'success': False, 'error': f'Character {character} not found in metadata'}), 404

        character_data = metadata['characters'][character]
        skins = character_data.get('skins', [])

        folder_id = f"folder_{uuid.uuid4().hex[:8]}"
        new_folder = {'type': 'folder', 'id': folder_id, 'name': name, 'expanded': True}

        skins.append(new_folder)
        character_data['skins'] = skins

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Created folder '{name}' for {character}")
        return jsonify({'success': True, 'folder': new_folder, 'skins': skins})
    except Exception as e:
        logger.error(f"Create folder error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/folders/rename', methods=['POST'])
def rename_folder():
    """Rename a folder"""
    try:
        data = request.json
        character = data.get('character')
        folder_id = data.get('folderId')
        new_name = data.get('newName')

        if not character or not folder_id or not new_name:
            return jsonify({'success': False, 'error': 'Missing character, folderId, or newName parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if character not in metadata.get('characters', {}):
            return jsonify({'success': False, 'error': f'Character {character} not found in metadata'}), 404

        character_data = metadata['characters'][character]
        skins = character_data.get('skins', [])

        folder, idx = find_folder_in_skins(skins, folder_id)
        if not folder:
            return jsonify({'success': False, 'error': f'Folder {folder_id} not found'}), 404

        folder['name'] = new_name

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Renamed folder {folder_id} to '{new_name}'")
        return jsonify({'success': True, 'skins': skins})
    except Exception as e:
        logger.error(f"Rename folder error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/folders/delete', methods=['POST'])
def delete_folder():
    """Delete a folder. Does NOT delete the skins themselves."""
    try:
        data = request.json
        character = data.get('character')
        folder_id = data.get('folderId')

        if not character or not folder_id:
            return jsonify({'success': False, 'error': 'Missing character or folderId parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if character not in metadata.get('characters', {}):
            return jsonify({'success': False, 'error': f'Character {character} not found in metadata'}), 404

        character_data = metadata['characters'][character]
        skins = character_data.get('skins', [])

        folder, folder_idx = find_folder_in_skins(skins, folder_id)
        if not folder:
            return jsonify({'success': False, 'error': f'Folder {folder_id} not found'}), 404

        for skin in skins:
            if skin.get('folder_id') == folder_id:
                del skin['folder_id']

        skins.pop(folder_idx)

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Deleted folder {folder_id}")
        return jsonify({'success': True, 'skins': skins})
    except Exception as e:
        logger.error(f"Delete folder error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/folders/toggle', methods=['POST'])
def toggle_folder():
    """Toggle folder expanded state"""
    try:
        data = request.json
        character = data.get('character')
        folder_id = data.get('folderId')

        if not character or not folder_id:
            return jsonify({'success': False, 'error': 'Missing character or folderId parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if character not in metadata.get('characters', {}):
            return jsonify({'success': False, 'error': f'Character {character} not found in metadata'}), 404

        character_data = metadata['characters'][character]
        skins = character_data.get('skins', [])

        folder, idx = find_folder_in_skins(skins, folder_id)
        if not folder:
            return jsonify({'success': False, 'error': f'Folder {folder_id} not found'}), 404

        folder['expanded'] = not folder.get('expanded', True)

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Toggled folder {folder_id} expanded: {folder['expanded']}")
        return jsonify({'success': True, 'expanded': folder['expanded'], 'skins': skins})
    except Exception as e:
        logger.error(f"Toggle folder error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/skins/set-folder', methods=['POST'])
def set_skin_folder():
    """Assign or unassign a skin to a folder"""
    try:
        data = request.json
        character = data.get('character')
        skin_id = data.get('skinId')
        folder_id = data.get('folderId')

        if not character or not skin_id:
            return jsonify({'success': False, 'error': 'Missing character or skinId parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if character not in metadata.get('characters', {}):
            return jsonify({'success': False, 'error': f'Character {character} not found in metadata'}), 404

        character_data = metadata['characters'][character]
        skins = character_data.get('skins', [])

        skin = None
        for s in skins:
            if s.get('id') == skin_id and s.get('type') != 'folder':
                skin = s
                break

        if not skin:
            return jsonify({'success': False, 'error': f'Skin {skin_id} not found'}), 404

        if folder_id:
            folder, _ = find_folder_in_skins(skins, folder_id)
            if not folder:
                return jsonify({'success': False, 'error': f'Folder {folder_id} not found'}), 404

        if folder_id:
            skin['folder_id'] = folder_id
        elif 'folder_id' in skin:
            del skin['folder_id']

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Set skin {skin_id} folder to {folder_id}")
        return jsonify({'success': True, 'skins': skins})
    except Exception as e:
        logger.error(f"Set skin folder error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
