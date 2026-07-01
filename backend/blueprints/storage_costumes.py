"""
Storage Costumes Blueprint - Storage vault costume operations.

Handles listing, deleting, renaming, CSP management, stock icons,
Slippi testing, reordering, and folder management for stored costumes.
"""

import os
import time
import json
import uuid
import re
import shutil
import zipfile
import tempfile
import threading
import logging
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify

from core.config import PROJECT_ROOT, STORAGE_PATH, VANILLA_ASSETS_DIR, PROCESSOR_DIR, SERVICES_DIR
from core.constants import get_char_prefix
from core.costume_files import find_costume_archive_name, find_extracted_costume_archive
from core.metadata import load_metadata, save_metadata, get_char_data

import sys
sys.path.insert(0, str(PROCESSOR_DIR))
from generate_csp import generate_csp, generate_single_csp_internal, find_character_assets, apply_character_specific_layers

sys.path.insert(0, str(SERVICES_DIR))
from dat_processor import validate_for_slippi

logger = logging.getLogger(__name__)

storage_costumes_bp = Blueprint('storage_costumes', __name__)

# Vanilla CSP texture size; HD previews are capped at 4x that
CSP_SD_SIZE = (136, 188)
CSP_HD_SIZE = (544, 752)


def derive_csp_versions(image_bytes):
    """Derive (sd_png_bytes, hd_png_bytes_or_None) from one uploaded image.

    SD is the image shrunk to fit the vanilla 136x188 CSP texture (never
    enlarged). The HD preview is kept only when the source is at least ~2x
    the SD size -- upscaling a small image would just make a blurry "HD" --
    and is capped at 4x.
    """
    from io import BytesIO
    from PIL import Image

    with Image.open(BytesIO(image_bytes)) as src:
        img = src.convert('RGBA')

    width, height = img.size

    sd = img.copy()
    if width > CSP_SD_SIZE[0] or height > CSP_SD_SIZE[1]:
        sd.thumbnail(CSP_SD_SIZE, Image.LANCZOS)
    sd_buf = BytesIO()
    sd.save(sd_buf, format='PNG')

    hd_bytes = None
    if width >= CSP_SD_SIZE[0] * 2 or height >= CSP_SD_SIZE[1] * 2:
        hd = img.copy()
        if width > CSP_HD_SIZE[0] or height > CSP_HD_SIZE[1]:
            hd.thumbnail(CSP_HD_SIZE, Image.LANCZOS)
        hd_buf = BytesIO()
        hd.save(hd_buf, format='PNG')
        hd_bytes = hd_buf.getvalue()

    return sd_buf.getvalue(), hd_bytes


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


def order_skins_like_vault(skins):
    """Return the non-folder skins in the SAME visual order the vault shows them.

    The vault (viewer buildDisplayList) pulls every foldered skin *under* its
    folder entry -- which can sit anywhere in the array -- so grouped skins
    display together, while the raw ``skins`` list leaves those members
    scattered at their original positions. The install page's "Available to
    Import" list is flat (it shows no folders), so we flatten to a plain list
    but keep the vault's order, which is what makes the two screens agree.

    Folder headers are dropped; every real skin is returned exactly once, in
    vault order. Skins the vault never shows (hidden Nana entries, or members
    whose folder was deleted) are appended afterward in raw order so the
    returned SET is identical to a plain folder-skipping walk -- no skin is
    silently dropped (the Ice Climbers pairing lookup depends on that).
    """
    folder_members = {}  # folder_id -> [skins, in array order]
    for s in skins:
        if not isinstance(s, dict):
            continue
        if s.get('type') == 'folder':
            folder_members.setdefault(s.get('id'), [])
        elif s.get('folder_id'):
            folder_members.setdefault(s.get('folder_id'), []).append(s)

    ordered = []
    placed = set()  # id() of skins already emitted
    for s in skins:
        if not isinstance(s, dict):
            continue
        if s.get('type') == 'folder':
            for member in folder_members.get(s.get('id'), []):
                if id(member) not in placed:
                    ordered.append(member)
                    placed.add(id(member))
        elif not s.get('folder_id'):
            ordered.append(s)
            placed.add(id(s))
        # else: folder member -- emitted under its folder above

    # Hidden / orphaned skins (never shown by the vault) still have to be
    # returned; append them in raw order after the vault-ordered skins.
    for s in skins:
        if isinstance(s, dict) and s.get('type') != 'folder' and id(s) not in placed:
            ordered.append(s)
            placed.add(id(s))

    return ordered


@storage_costumes_bp.route('/api/mex/storage/metadata', methods=['GET'])
def get_storage_metadata():
    """Get storage metadata.json"""
    try:
        metadata = load_metadata(default={'characters': {}})

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

        metadata = load_metadata()
        if metadata is None:
            return jsonify({'success': True, 'costumes': []})

        characters_data = metadata.get('characters', {})
        if character:
            if character in characters_data:
                characters_data = {character: characters_data[character]}
            else:
                # custom-character pseudo keys (.../skins, .../costumes)
                characters_data = {character: get_char_data(metadata, character) or {}}

        for char_name, char_data in characters_data.items():
            skins = char_data.get('skins', [])

            # Present skins in the SAME order the vault (storage tab) shows them
            # -- folder members grouped at their folder's position -- so the flat
            # "Available to Import" list and the vault don't disagree on order.
            # order_skins_like_vault drops folder entries and returns every real
            # skin exactly once, so no `type == 'folder'` guard is needed here.
            for skin in order_skins_like_vault(skins):
                # NOTE: We do NOT filter `visible: False` here. The frontend
                # (CharacterMode.jsx) already filters `!c.isNana` for the
                # displayed costume grid, so hidden Nana entries don't appear
                # as separate tiles — but they DO need to be in the array so
                # the IC install path can find them via
                # `storageCostumes.find(c => c.folder === pairedNanaId)`.
                # Filtering them out here is what was causing "Paired Nana
                # costume not found" → batch-install fail with no HTTP request
                # ever leaving the renderer.

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
                    active_csp_id = skin.get('active_csp_id')
                    active_alt = next((a for a in alternate_csps if a.get('id') == active_csp_id), None)
                    if active_alt and active_alt.get('is_hd'):
                        active_alt = next((a for a in alternate_csps
                                           if a.get('pose_name') == active_alt.get('pose_name')
                                           and not a.get('is_hd')), None)
                    csp_url = f"/storage/{char_name}/{skin['id']}_csp.png" if skin.get('has_csp') else None
                    if active_alt and active_alt.get('url'):
                        csp_url = active_alt['url']

                    costume_data = {
                        'character': char_name,
                        'name': f"{char_name} - {skin.get('color', 'Custom')}",
                        'folder': skin['id'],
                        # custom-character skins have no costume_code; fall back
                        # to the DAT stem so the UI still shows something useful
                        'costumeCode': skin.get('costume_code') or Path(skin.get('dat_name', '')).stem,
                        'zipPath': str(zip_path.relative_to(PROJECT_ROOT)),
                        'cspUrl': csp_url,
                        'stockUrl': f"/storage/{char_name}/{skin['id']}_stc.png" if skin.get('has_stock') else None,
                        'alternateCsps': alternate_csps,
                        'activeCspId': skin.get('active_csp_id'),
                        'isPopo': skin.get('is_popo', False),
                        'isNana': skin.get('is_nana', False),
                        'pairedNanaId': skin.get('paired_nana_id'),
                        'pairedPopoId': skin.get('paired_popo_id'),
                        'slippiSafe': skin.get('slippi_safe', False)
                    }
                    costumes.append(costume_data)

        # Custom-character added skins surface here too, so an installed custom
        # fighter shows its extra skins in the same "Available to Import" list
        # as vanilla characters (chosen per-skin instead of force-installed).
        custom_root = STORAGE_PATH / 'custom_characters'
        for cc in metadata.get('custom_characters', []):
            cc_name = cc.get('name')
            cc_slug = cc.get('slug')
            if character and character not in (cc_name, cc_slug):
                continue
            skins_dir = custom_root / cc_slug / 'skins'
            for skin in cc.get('added_skins', []):
                sid = skin.get('id')
                zp = skins_dir / skin.get('filename', f"{sid}.zip")
                if not zp.exists():
                    continue
                alternate_csps = []
                for alt in skin.get('alternate_csps', []):
                    alternate_csps.append({
                        'id': alt.get('id'),
                        'url': f"/storage/custom_characters/{cc_slug}/skins/{alt.get('filename')}",
                        'pose_name': alt.get('pose_name'),
                        'is_hd': alt.get('is_hd', False),
                        'timestamp': alt.get('timestamp')
                    })
                active_csp_id = skin.get('active_csp_id')
                active_alt = next((a for a in alternate_csps if a.get('id') == active_csp_id), None)
                if active_alt and active_alt.get('is_hd'):
                    active_alt = next((a for a in alternate_csps
                                       if a.get('pose_name') == active_alt.get('pose_name')
                                       and not a.get('is_hd')), None)
                csp_url = f"/api/mex/custom-characters/{cc_slug}/skins/{sid}/csp" if skin.get('has_csp') else None
                if active_alt and active_alt.get('url'):
                    csp_url = active_alt['url']
                costumes.append({
                    'character': cc_name,
                    'name': f"{cc_name} - {skin.get('color') or skin.get('name') or 'Custom Skin'}",
                    'folder': sid,
                    'costumeCode': '',
                    'zipPath': str(zp.relative_to(PROJECT_ROOT)),
                    'cspUrl': csp_url,
                    'stockUrl': f"/api/mex/custom-characters/{cc_slug}/skins/{sid}/stock" if skin.get('has_stock') else None,
                    'alternateCsps': alternate_csps,
                    'activeCspId': active_csp_id,
                    'isPopo': False,
                    'isNana': False,
                    'pairedNanaId': None,
                    'pairedPopoId': None,
                    'slippiSafe': False,
                    # routing markers: these import via MexCLI import-costume,
                    # not the vanilla /import path
                    'isCustomCharSkin': True,
                    'customSlug': cc_slug,
                    'skinId': sid,
                })

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

        metadata = load_metadata()
        if metadata is None:
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        char_data = get_char_data(metadata, character)
        if char_data is None:
            return jsonify({'success': False, 'error': f'Character {character} not found in metadata'}), 404

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

        # Every on-disk file this skin owns: the costume zip plus ALL derived
        # portraits — SD CSP, HD CSP, stock, and every alternate-pose CSP.
        # Older deletes only removed _csp.png/_stc.png, which orphaned the HD
        # and alternate PNGs in the character folder; collect them all here.
        names = {
            skin_to_delete.get('filename') or f"{skin_id}.zip",
            skin_to_delete.get('csp_filename') or f"{skin_id}_csp.png",
            skin_to_delete.get('hd_csp_filename') or f"{skin_id}_csp_hd.png",
            f"{skin_id}_csp.png",
            f"{skin_id}_csp_hd.png",
            f"{skin_id}_stc.png",
        }
        for alt in skin_to_delete.get('alternate_csps', []):
            if alt.get('filename'):
                names.add(alt['filename'])

        deleted_files = []
        for name in names:
            f = char_folder / name
            if f.exists():
                f.unlink()
                deleted_files.append(str(f))

        # Belt-and-suspenders: sweep any alternate CSP PNGs that match this
        # skin's id but weren't tracked in metadata. The literal `_csp_alt_`
        # anchor keeps it from matching a longer sibling id; glob.escape guards
        # ids containing glob specials (e.g. "plmrbu[mrsonic]").
        import glob as _glob
        for p in _glob.glob(_glob.escape(str(char_folder / skin_id)) + '_csp_alt_*.png'):
            if p not in deleted_files:
                os.unlink(p)
                deleted_files.append(p)

        skins.pop(skin_index)

        save_metadata(metadata)

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

        metadata = load_metadata()
        if metadata is None:
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        char_data = get_char_data(metadata, character)
        if char_data is None:
            return jsonify({'success': False, 'error': f'Character {character} not found in metadata'}), 404

        skins = char_data.get('skins', [])
        skin_found = False

        for skin in skins:
            if skin['id'] == skin_id:
                skin['color'] = new_name
                skin_found = True
                break

        if not skin_found:
            return jsonify({'success': False, 'error': f'Skin {skin_id} not found for {character}'}), 404

        save_metadata(metadata)

        logger.info(f"[OK] Renamed costume {skin_id} to '{new_name}'")
        return jsonify({'success': True, 'message': f'Successfully renamed to {new_name}'})
    except Exception as e:
        logger.error(f"Rename costume error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/costumes/update-csp', methods=['POST'])
def update_costume_csp():
    """Update CSP image for a character costume.

    With auto=true, one uploaded image is split into both versions: shrunk to
    the in-game 136x188 texture, and kept (up to 4x) as the HD vault preview.
    The legacy isHd flag updates just one of the two files.
    """
    try:
        character = request.form.get('character')
        skin_id = request.form.get('skinId')
        is_hd = request.form.get('isHd', '').lower() == 'true'
        auto = request.form.get('auto', '').lower() == 'true'

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

        # Auto mode: derive both SD (in-game) and HD (preview) from one image.
        # Animated GIFs fall through to the legacy as-is path.
        if auto and csp_file.content_type != 'image/gif':
            sd_data, hd_data = derive_csp_versions(csp_data)

            csp_filename = f"{skin_id}_csp.png"
            (char_folder / csp_filename).write_bytes(sd_data)

            temp_zip = char_folder / f"{skin_id}_temp.zip"
            with zipfile.ZipFile(zip_path, 'r') as source_zip:
                with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as dest_zip:
                    for item in source_zip.infolist():
                        if item.filename.lower() not in ['csp.png', 'csp']:
                            dest_zip.writestr(item, source_zip.read(item.filename))
                    dest_zip.writestr('csp.png', sd_data)
            zip_path.unlink()
            temp_zip.rename(zip_path)

            hd_filename = None
            hd_size = None
            if hd_data:
                hd_filename = f"{skin_id}_csp_hd.png"
                (char_folder / hd_filename).write_bytes(hd_data)
                from PIL import Image
                from io import BytesIO
                with Image.open(BytesIO(hd_data)) as img:
                    hd_size = f"{img.size[0]}x{img.size[1]}"

            metadata = load_metadata()
            if metadata is not None:
                char_data = get_char_data(metadata, character)
                if char_data is not None:
                    for skin in char_data.get('skins', []):
                        if skin['id'] == skin_id:
                            skin['has_csp'] = True
                            skin['csp_source'] = 'custom'
                            skin['csp_filename'] = csp_filename
                            skin.pop('csp_pose_name', None)
                            if hd_filename:
                                skin['has_hd_csp'] = True
                                skin['hd_csp_source'] = 'custom'
                                skin['hd_csp_filename'] = hd_filename
                                skin['hd_csp_resolution'] = 'custom'
                                skin['hd_csp_size'] = hd_size
                            break
                    save_metadata(metadata)

            logger.info(f"[OK] Updated CSP for {character} - {skin_id} (auto, hd={'yes' if hd_data else 'no'})")
            return jsonify({'success': True, 'message': 'CSP updated successfully', 'hasHd': bool(hd_data)})

        if is_hd:
            hd_csp_filename = f"{skin_id}_csp_hd{ext}"
            standalone_hd_csp = char_folder / hd_csp_filename
            with open(standalone_hd_csp, 'wb') as f:
                f.write(csp_data)

            metadata = load_metadata()
            if metadata is not None:
                char_data = get_char_data(metadata, character)
                if char_data is not None:
                    for skin in char_data.get('skins', []):
                        if skin['id'] == skin_id:
                            skin['has_hd_csp'] = True
                            skin['hd_csp_source'] = 'custom'
                            skin['hd_csp_filename'] = hd_csp_filename
                            break

                    save_metadata(metadata)

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

            metadata = load_metadata()
            if metadata is not None:
                char_data = get_char_data(metadata, character)
                if char_data is not None:
                    for skin in char_data.get('skins', []):
                        if skin['id'] == skin_id:
                            skin['has_csp'] = True
                            skin['csp_source'] = 'custom'
                            skin['csp_filename'] = csp_filename
                            skin.pop('csp_pose_name', None)
                            break

                    save_metadata(metadata)

            logger.info(f"[OK] Updated CSP for {character} - {skin_id}")

        return jsonify({'success': True, 'message': 'CSP updated successfully', 'isHd': is_hd})
    except Exception as e:
        logger.error(f"Update CSP error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/costumes/<path:character>/<skin_id>/csp/capture-hd', methods=['POST'])
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

            dat_file = find_extracted_costume_archive(temp_path)
            if not dat_file:
                return jsonify({'success': False, 'error': 'No costume archive found in costume zip'}), 400

            hd_csp_path = generate_csp(str(dat_file), scale=scale)

            if not hd_csp_path or not Path(hd_csp_path).exists():
                return jsonify({'success': False, 'error': 'Failed to generate HD CSP'}), 500

            final_hd_csp = char_folder / f"{skin_id}_csp_hd.png"
            shutil.copy2(hd_csp_path, final_hd_csp)

            from PIL import Image
            with Image.open(final_hd_csp) as img:
                width, height = img.size

            metadata = load_metadata()
            if metadata is not None:
                char_data = get_char_data(metadata, character)
                if char_data is not None:
                    for skin in char_data.get('skins', []):
                        if skin['id'] == skin_id:
                            skin['has_hd_csp'] = True
                            skin['hd_csp_resolution'] = f"{scale}x"
                            skin['hd_csp_size'] = f"{width}x{height}"
                            break

                    save_metadata(metadata)

            logger.info(f"[OK] Generated HD CSP for {character}/{skin_id} at {scale}x ({width}x{height})")
            return jsonify({'success': True, 'message': f'HD CSP generated at {scale}x', 'resolution': f"{scale}x", 'size': f"{width}x{height}"})

    except Exception as e:
        logger.error(f"Capture HD CSP error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/costumes/<path:character>/<skin_id>/csp/manage', methods=['POST', 'OPTIONS'])
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

        metadata = load_metadata()
        if metadata is None:
            return jsonify({'success': False, 'error': 'Metadata not found'}), 404

        char_data = get_char_data(metadata, character) or {}
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

            save_metadata(metadata)

            logger.info(f"[OK] Set active CSP to: {skin['active_csp_id']}")
            return jsonify({'success': True, 'message': 'Active CSP updated', 'activeCspId': skin['active_csp_id']})

        elif action == 'reset':
            skin['active_csp_id'] = None
            save_metadata(metadata)
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

            save_metadata(metadata)

            return jsonify({'success': True, 'message': 'Alt CSP removed'})

        elif action == 'add':
            if not file:
                return jsonify({'success': False, 'error': 'No file provided'}), 400

            is_hd_upload = request.form.get('isHd', '').lower() == 'true'
            auto = request.form.get('auto', '').lower() == 'true'
            alt_csps = skin.get('alternate_csps', [])

            # Auto mode: one image becomes an SD + HD pair, grouped by a name
            # derived from the uploaded filename (animated GIFs stay as-is below)
            if auto and file.content_type != 'image/gif':
                if 'alternate_csps' not in skin:
                    skin['alternate_csps'] = []
                    alt_csps = skin['alternate_csps']

                sd_data, hd_data = derive_csp_versions(file.read())

                stem = re.sub(r'[^\w\- ]', '', Path(file.filename or '').stem).strip() or 'custom'
                existing_names = {a.get('pose_name') for a in alt_csps}
                group_name = stem
                suffix = 2
                while group_name in existing_names:
                    group_name = f"{stem} {suffix}"
                    suffix += 1

                ts = int(time.time())
                n = len(alt_csps) + 1
                now = datetime.now().isoformat()

                sd_id = f"alt_{ts}"
                sd_filename = f"{skin_id}_csp_alt_{n}.png"
                (STORAGE_PATH / character / sd_filename).write_bytes(sd_data)
                skin['alternate_csps'].append({
                    'id': sd_id,
                    'filename': sd_filename,
                    'pose_name': group_name,
                    'is_hd': False,
                    'timestamp': now
                })

                if hd_data:
                    hd_filename = f"{skin_id}_csp_alt_{n}_hd.png"
                    (STORAGE_PATH / character / hd_filename).write_bytes(hd_data)
                    skin['alternate_csps'].append({
                        'id': f"alt_{ts}_hd",
                        'filename': hd_filename,
                        'pose_name': group_name,
                        'is_hd': True,
                        'timestamp': now
                    })

                save_metadata(metadata)

                return jsonify({
                    'success': True,
                    'message': 'Alt CSP added',
                    'altId': sd_id,
                    'url': f"/storage/{character}/{sd_filename}",
                    'isHd': False,
                    'hasHd': bool(hd_data),
                    'poseName': group_name
                })

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

            save_metadata(metadata)

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

                dat_file = find_extracted_costume_archive(Path(temp_dir))
                if not dat_file:
                    return jsonify({'success': False, 'error': 'No costume archive found in ZIP'}), 400

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

                save_metadata(metadata)

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

        metadata = load_metadata()
        if metadata is not None:
            char_data = get_char_data(metadata, character)
            if char_data is not None:
                for skin in char_data.get('skins', []):
                    if skin['id'] == skin_id:
                        skin['has_stock'] = True
                        skin['stock_source'] = 'custom'
                        break

                save_metadata(metadata)

        logger.info(f"[OK] Updated stock icon for {character} - {skin_id}")
        return jsonify({'success': True, 'message': 'Stock icon updated successfully'})
    except Exception as e:
        logger.error(f"Update stock error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/costumes/generate-stock', methods=['POST'])
def generate_costume_stock():
    """Derive a stock icon for a vault costume from its DAT's color movement
    vs the vanilla costume (skinlab.stock_gen).

    Two-step flow so nothing is replaced without the user's say-so:
      {character, skinId}                      -> preview: {dataUri, method},
                                                  nothing written
      {character, skinId, apply, imageData}    -> writes the previewed icon to
                                                  the zip/standalone/metadata
    """
    try:
        import base64

        data = request.json
        character = data.get('character')
        skin_id = data.get('skinId')

        if not character or not skin_id:
            return jsonify({'success': False, 'error': 'Missing character or skinId parameter'}), 400

        char_folder = STORAGE_PATH / character
        zip_path = char_folder / f"{skin_id}.zip"
        if not zip_path.exists():
            return jsonify({'success': False, 'error': f'Costume zip not found: {skin_id}'}), 404

        metadata = load_metadata()
        skin_meta = None
        if metadata is not None:
            char_data = get_char_data(metadata, character)
            if char_data is not None:
                skin_meta = next((s for s in char_data.get('skins', [])
                                  if s['id'] == skin_id), None)

        if data.get('apply'):
            image_data = data.get('imageData') or ''
            if ',' in image_data:
                image_data = image_data.split(',', 1)[1]
            try:
                stock_data = base64.b64decode(image_data)
            except Exception:
                stock_data = b''
            if not stock_data:
                return jsonify({'success': False, 'error': 'No previewed icon to apply'}), 400

            (char_folder / f"{skin_id}_stc.png").write_bytes(stock_data)
            temp_zip = char_folder / f"{skin_id}_temp.zip"
            with zipfile.ZipFile(zip_path, 'r') as source_zip:
                with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as dest_zip:
                    for item in source_zip.infolist():
                        if item.filename.lower() not in ['stc.png', 'stock.png', 'stock']:
                            dest_zip.writestr(item, source_zip.read(item.filename))
                    dest_zip.writestr('stc.png', stock_data)
            zip_path.unlink()
            temp_zip.rename(zip_path)

            if metadata is not None and skin_meta is not None:
                skin_meta['has_stock'] = True
                skin_meta['stock_source'] = 'generated'
                save_metadata(metadata)

            logger.info(f"[OK] Applied generated stock icon for {character} - {skin_id}")
            return jsonify({'success': True,
                            'stockUrl': f"/storage/{character}/{skin_id}_stc.png"})

        # preview: generate (generated-only, no vanilla fallback) via the shared
        # canonical builder; nothing is written here.
        from skinlab.costume_assets import build_stock

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            dat_filename = find_costume_archive_name(zip_ref.namelist())
            if not dat_filename:
                return jsonify({'success': False, 'error': 'No costume archive found in costume ZIP'}), 400
            dat_data = zip_ref.read(dat_filename)

        # Import names the archive '<costume_code>Mod.<ext>'
        stem = Path(dat_filename).stem
        costume_code = stem[:-3] if stem.endswith('Mod') else stem

        # only our own stored render (vanilla pose) may feed the csp-diff path
        csp_bytes = None
        if skin_meta and skin_meta.get('csp_source') == 'generated':
            csp_path = char_folder / f"{skin_id}_csp.png"
            if csp_path.exists():
                csp_bytes = csp_path.read_bytes()

        stock_data, _source, method = build_stock(
            character, costume_code, dat_data,
            aligned_csp=csp_bytes, vanilla_fallback=False)

        if stock_data is None:
            return jsonify({
                'success': False,
                'error': 'Could not derive a stock icon for this skin (no vanilla '
                         'reference lines up with its DAT or CSP)'}), 422

        logger.info(f"[OK] Previewed generated stock for {character} - {skin_id} via {method}")
        return jsonify({'success': True, 'method': method,
                        'dataUri': 'data:image/png;base64,'
                                   + base64.b64encode(stock_data).decode('ascii')})
    except Exception as e:
        logger.error(f"Generate stock error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def _resolve_active_portrait(skin_meta):
    """Resolve the costume's currently active portrait from metadata.

    Returns (active_alt, pose_name): the active alternate dict (None when the
    original/default CSP is active) and its pose name (None = default pose). A
    swap stores active_csp_id pointing at the SD member of a pose group, but we
    fold an HD pointer back to its SD sibling just in case.
    """
    skin_meta = skin_meta or {}
    alt_csps = skin_meta.get('alternate_csps', [])
    active_csp_id = skin_meta.get('active_csp_id')
    if not active_csp_id:
        return None, None
    active_alt = next((a for a in alt_csps if a.get('id') == active_csp_id), None)
    if active_alt and active_alt.get('is_hd'):
        active_alt = next((a for a in alt_csps
                           if a.get('pose_name') == active_alt.get('pose_name')
                           and not a.get('is_hd')), active_alt)
    pose_name = active_alt.get('pose_name') if active_alt else None
    return active_alt, pose_name


def _render_costume_preview(character, zip_path, pose_name):
    """Render a costume's HD portrait for the given active pose (pose_name=None =>
    default) and return (png_bytes, pose_label). Writes nothing. Shared by the
    single retake (generate_costume_csp) and the per-character bulk retake so both
    use the identical render path -- and both flow through the CSP render pool
    when one is active. Raises on a missing DAT / failed render."""
    with tempfile.TemporaryDirectory() as temp_dir:
        tdir = Path(temp_dir)
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(tdir)
        dat_file = find_extracted_costume_archive(tdir)
        if not dat_file:
            raise ValueError('No costume archive found in costume ZIP')

        scale = 4  # render HD; the in-game SD is derived from it on apply

        # A custom pose drives the render through its saved scene YAML + the
        # character's AJ animations (same path the CSP manager's HD regen uses);
        # the default portrait goes through the canonical generator (character
        # auto-detect, per-costume low-poly slot, Fox gun, ICs).
        csp_output = None
        if pose_name:
            pose_path = VANILLA_ASSETS_DIR / 'custom_poses' / character / f"{pose_name}.yml"
            if pose_path.exists():
                camera_file = None
                char_prefix = get_char_prefix(character)
                if char_prefix:
                    aj_file = VANILLA_ASSETS_DIR / character / f"{char_prefix}AJ.dat"
                    if aj_file.exists():
                        camera_file = str(aj_file)
                csp_output = generate_single_csp_internal(
                    str(dat_file), character, str(pose_path), camera_file, scale)
                if csp_output and Path(csp_output).exists():
                    apply_character_specific_layers(csp_output, character, scale)
        if not csp_output:
            # default pose, or pose YAML missing -> fall back to default
            csp_output = generate_csp(str(dat_file), scale=scale)

        if not csp_output or not Path(csp_output).exists():
            raise RuntimeError('Failed to render a portrait for this costume')

        return Path(csp_output).read_bytes(), (pose_name or 'Default')


@storage_costumes_bp.route('/api/mex/storage/costumes/generate-csp', methods=['POST'])
def generate_costume_csp():
    """Re-render ("retake") a vault costume's character-select portrait with the
    headless HSDRaw renderer, using whichever pose is currently active for the
    skin -- the original/default pose unless a custom-pose alternate is the
    active portrait in the CSP manager.

    Two-step flow so nothing is overwritten without the user's say-so (mirrors
    generate-stock):
      {character, skinId}                   -> preview: {dataUri, poseName};
                                               nothing is written
      {character, skinId, apply, imageData} -> writes the previewed portrait to
                                               the active portrait (original CSP
                                               + HD, or the active pose alternate)
    """
    try:
        import base64

        data = request.json or {}
        character = data.get('character')
        skin_id = data.get('skinId')

        if not character or not skin_id:
            return jsonify({'success': False, 'error': 'Missing character or skinId parameter'}), 400

        char_folder = STORAGE_PATH / character
        zip_path = char_folder / f"{skin_id}.zip"
        if not zip_path.exists():
            return jsonify({'success': False, 'error': f'Costume zip not found: {skin_id}'}), 404

        metadata = load_metadata()
        skin_meta = None
        if metadata is not None:
            char_data = get_char_data(metadata, character)
            if char_data is not None:
                skin_meta = next((s for s in char_data.get('skins', [])
                                  if s['id'] == skin_id), None)

        active_alt, pose_name = _resolve_active_portrait(skin_meta)

        # ---- apply: write the render the user already previewed -------------
        if data.get('apply'):
            image_data = data.get('imageData') or ''
            if ',' in image_data:
                image_data = image_data.split(',', 1)[1]
            try:
                raw = base64.b64decode(image_data)
            except Exception:
                raw = b''
            if not raw:
                return jsonify({'success': False, 'error': 'No previewed portrait to apply'}), 400

            # The preview is the HD render; split it into the in-game SD texture
            # and the (capped) HD vault preview, exactly like a manual upload.
            sd_data, hd_data = derive_csp_versions(raw)
            alt_csps = (skin_meta or {}).get('alternate_csps', [])

            if active_alt:
                # Active custom-pose alternate: overwrite its SD (+ HD) in place.
                sd_filename = active_alt.get('filename')
                (char_folder / sd_filename).write_bytes(sd_data)
                active_alt['timestamp'] = datetime.now().isoformat()
                if hd_data:
                    hd_alt = next((a for a in alt_csps
                                   if a.get('pose_name') == pose_name and a.get('is_hd')), None)
                    if hd_alt:
                        (char_folder / hd_alt.get('filename')).write_bytes(hd_data)
                        hd_alt['timestamp'] = datetime.now().isoformat()
                    else:
                        hd_filename = f"{skin_id}_csp_alt_{len(alt_csps) + 1}_hd.png"
                        (char_folder / hd_filename).write_bytes(hd_data)
                        alt_csps.append({
                            'id': f"alt_{int(time.time())}_hd",
                            'filename': hd_filename,
                            'pose_name': pose_name,
                            'is_hd': True,
                            'timestamp': datetime.now().isoformat()
                        })
                if metadata is not None:
                    save_metadata(metadata)
                logger.info(f"[OK] Retook CSP for {character} - {skin_id} (pose '{pose_name}')")
                return jsonify({'success': True,
                                'cspUrl': f"/storage/{character}/{sd_filename}"})

            # Original/default portrait: SD into standalone + zip, HD standalone.
            csp_filename = f"{skin_id}_csp.png"
            (char_folder / csp_filename).write_bytes(sd_data)
            temp_zip = char_folder / f"{skin_id}_temp.zip"
            with zipfile.ZipFile(zip_path, 'r') as source_zip:
                with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as dest_zip:
                    for item in source_zip.infolist():
                        if item.filename.lower() not in ['csp.png', 'csp']:
                            dest_zip.writestr(item, source_zip.read(item.filename))
                    dest_zip.writestr('csp.png', sd_data)
            zip_path.unlink()
            temp_zip.rename(zip_path)

            hd_filename = None
            hd_size = None
            if hd_data:
                hd_filename = f"{skin_id}_csp_hd.png"
                (char_folder / hd_filename).write_bytes(hd_data)
                from PIL import Image
                from io import BytesIO
                with Image.open(BytesIO(hd_data)) as img:
                    hd_size = f"{img.size[0]}x{img.size[1]}"

            if metadata is not None and skin_meta is not None:
                skin_meta['has_csp'] = True
                skin_meta['csp_source'] = 'generated'
                skin_meta['csp_filename'] = csp_filename
                skin_meta.pop('csp_pose_name', None)
                if hd_filename:
                    skin_meta['has_hd_csp'] = True
                    skin_meta['hd_csp_source'] = 'generated'
                    skin_meta['hd_csp_filename'] = hd_filename
                    skin_meta['hd_csp_resolution'] = '4x'
                    skin_meta['hd_csp_size'] = hd_size
                save_metadata(metadata)

            logger.info(f"[OK] Retook CSP for {character} - {skin_id} (default pose)")
            return jsonify({'success': True,
                            'cspUrl': f"/storage/{character}/{csp_filename}",
                            'hasHd': bool(hd_data)})

        # ---- preview: render now at HD, return a data URI, write nothing ----
        png_bytes, pose_label = _render_costume_preview(character, zip_path, pose_name)
        logger.info(f"[OK] Previewed retaken CSP for {character} - {skin_id} (pose '{pose_label}')")
        return jsonify({'success': True, 'poseName': pose_label,
                        'dataUri': 'data:image/png;base64,'
                                   + base64.b64encode(png_bytes).decode('ascii')})
    except Exception as e:
        logger.error(f"Generate CSP error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# One bulk retake at a time: active_pool installs a process-global CSP pool, so
# two concurrent batches would clobber each other's pool.
_batch_retake_lock = threading.Lock()
_batch_retake_running = False


@storage_costumes_bp.route('/api/mex/storage/costumes/batch-retake-csp', methods=['POST'])
def batch_retake_csp():
    """Bulk-retake every selected costume's portrait for ONE character, each with
    its OWN active pose, through the persistent CSP render pool. Renders only --
    nothing is written; the frontend reviews the before/after grid and applies the
    kept ones via /generate-csp (apply). Mirrors the stage bulk-capture flow.

    Streams over socket.io: `csp_retake_item` per costume
    ({skinId, ok, dataUri|error, poseName, done, total}) and a final
    `csp_retake_complete` ({total, rendered}); `csp_retake_error` on a fatal error.
    Body: {character, skinIds}. Returns immediately; work runs in a bg thread."""
    global _batch_retake_running
    import base64

    data = request.json or {}
    character = data.get('character')
    skin_ids = data.get('skinIds') or []
    if not character or not skin_ids:
        return jsonify({'success': False, 'error': 'Missing character or skinIds'}), 400

    with _batch_retake_lock:
        if _batch_retake_running:
            return jsonify({'success': False,
                            'error': 'A bulk CSP retake is already running.'}), 409
        _batch_retake_running = True

    # Snapshot the skins' metadata on the request thread (don't touch Flask state
    # from the worker); each costume keeps its own active-portrait/pose.
    metadata = load_metadata()
    char_data = get_char_data(metadata, character) if metadata else None
    skins = (char_data or {}).get('skins', [])
    skin_lookup = {s['id']: s for s in skins if s.get('type') != 'folder'}
    jobs = [(sid, skin_lookup.get(sid)) for sid in skin_ids]

    def run():
        global _batch_retake_running
        from core.state import get_socketio
        from skinlab.csp_pool import active_pool
        from skinlab.csp_concurrency import csp_workers
        socketio = get_socketio()
        total = len(jobs)
        rendered = 0
        try:
            # One warm pool for the whole batch (bounded to the job count).
            with active_pool(workers=max(1, min(csp_workers(), total))):
                for i, (sid, skin_meta) in enumerate(jobs):
                    item = {'skinId': sid, 'done': i + 1, 'total': total}
                    try:
                        if skin_meta is None:
                            raise ValueError('Skin not found')
                        zip_path = STORAGE_PATH / character / f"{sid}.zip"
                        if not zip_path.exists():
                            raise FileNotFoundError('Costume zip not found')
                        _active_alt, pose_name = _resolve_active_portrait(skin_meta)
                        png_bytes, pose_label = _render_costume_preview(
                            character, zip_path, pose_name)
                        item.update({
                            'ok': True, 'poseName': pose_label,
                            'dataUri': 'data:image/png;base64,'
                                       + base64.b64encode(png_bytes).decode('ascii')})
                        rendered += 1
                    except Exception as e:  # noqa: BLE001 - one bad costume mustn't stop the batch
                        item.update({'ok': False, 'error': str(e)})
                        logger.warning(f"Batch retake: {character}/{sid} failed: {e}")
                    socketio.emit('csp_retake_item', item)
            socketio.emit('csp_retake_complete',
                          {'character': character, 'total': total, 'rendered': rendered})
            logger.info(f"[OK] Batch retake for {character}: {rendered}/{total} rendered")
        except Exception as e:
            logger.error(f"Batch retake error: {e}", exc_info=True)
            socketio.emit('csp_retake_error', {'error': str(e)})
        finally:
            _batch_retake_running = False

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'message': f'Retaking {len(jobs)} costume(s)'})


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
            dat_filename = find_costume_archive_name(zip_ref.namelist())
            if not dat_filename:
                return jsonify({'success': False, 'error': 'No costume archive found in costume ZIP'}), 400

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
                            if item.filename == dat_filename:
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

        metadata = load_metadata()
        if metadata is not None:
            char_data = get_char_data(metadata, character)
            if char_data is not None:
                for skin in char_data.get('skins', []):
                    if skin['id'] == skin_id:
                        skin['slippi_safe'] = validation['slippi_safe']
                        skin['slippi_tested'] = True
                        skin['slippi_test_date'] = datetime.now().isoformat()
                        skin['slippi_manual_override'] = None
                        break

                save_metadata(metadata)

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

        metadata = load_metadata()
        if metadata is None:
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        char_data = get_char_data(metadata, character)
        if char_data is None:
            return jsonify({'success': False, 'error': f'Character {character} not found in metadata'}), 404

        skin_found = False
        for skin in char_data.get('skins', []):
            if skin['id'] == skin_id:
                skin['slippi_safe'] = slippi_safe
                skin['slippi_manual_override'] = True
                skin['slippi_test_date'] = datetime.now().isoformat()
                skin_found = True
                break

        if not skin_found:
            return jsonify({'success': False, 'error': f'Skin {skin_id} not found for {character}'}), 404

        save_metadata(metadata)

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

        metadata = load_metadata()
        if metadata is None:
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

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

        save_metadata(metadata)

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

        metadata = load_metadata()
        if metadata is None:
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

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
            save_metadata(metadata)
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

        metadata = load_metadata()
        if metadata is None:
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

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
            save_metadata(metadata)
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

        STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        metadata = load_metadata(default={'characters': {}})

        characters = metadata.setdefault('characters', {})
        character_data = characters.setdefault(character, {})
        skins = character_data.setdefault('skins', [])

        folder_id = f"folder_{uuid.uuid4().hex[:8]}"
        new_folder = {'type': 'folder', 'id': folder_id, 'name': name, 'expanded': True}

        skins.append(new_folder)

        save_metadata(metadata)

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

        metadata = load_metadata()
        if metadata is None:
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        if character not in metadata.get('characters', {}):
            return jsonify({'success': False, 'error': f'Character {character} not found in metadata'}), 404

        character_data = metadata['characters'][character]
        skins = character_data.get('skins', [])

        folder, idx = find_folder_in_skins(skins, folder_id)
        if not folder:
            return jsonify({'success': False, 'error': f'Folder {folder_id} not found'}), 404

        folder['name'] = new_name

        save_metadata(metadata)

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

        metadata = load_metadata()
        if metadata is None:
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

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

        save_metadata(metadata)

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

        metadata = load_metadata()
        if metadata is None:
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        if character not in metadata.get('characters', {}):
            return jsonify({'success': False, 'error': f'Character {character} not found in metadata'}), 404

        character_data = metadata['characters'][character]
        skins = character_data.get('skins', [])

        folder, idx = find_folder_in_skins(skins, folder_id)
        if not folder:
            return jsonify({'success': False, 'error': f'Folder {folder_id} not found'}), 404

        folder['expanded'] = not folder.get('expanded', True)

        save_metadata(metadata)

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

        metadata = load_metadata()
        if metadata is None:
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

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

        save_metadata(metadata)

        logger.info(f"[OK] Set skin {skin_id} folder to {folder_id}")
        return jsonify({'success': True, 'skins': skins})
    except Exception as e:
        logger.error(f"Set skin folder error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ---------------------------------------------------------------------------
# Animelee detection — find costumes with the inverted-hull outline effect via
# the MexCLI geometry detector (detect-outline), grouped by body-geometry
# fingerprint so colour variants of the same skin cluster together. Vanilla
# geometry is excluded (defensive; vanilla's small intrinsic outline is already
# below the detector's threshold). See memory animelee-detection.
# ---------------------------------------------------------------------------

_VANILLA_GEOM_HASHES = None

# Animelee verdict applied here (not in C#) so it's tunable without a rebuild.
# A real inverted-hull outline needs >=2 cull-asymmetric concentric duplicate
# pairs and a substantial largest duplicated part. Threshold 120 sits above the
# retail-vanilla ceiling (max asymDupMax across all 273 vanilla DATs = 112) and
# below genuine Animelee (e.g. Breloom-Yoshi = 137), so vanilla never trips it.
ANIMELEE_CULLASYM_MIN = 2
ANIMELEE_ASYMMAX_MIN = 120


def _load_vanilla_geom_hashes():
    """Body-geometry fingerprints of retail vanilla costumes (cached)."""
    global _VANILLA_GEOM_HASHES
    if _VANILLA_GEOM_HASHES is None:
        try:
            from core.config import BACKEND_DATA_DIR
            doc = json.loads((BACKEND_DATA_DIR / 'vanilla_geom_hashes.json').read_text(encoding='utf-8'))
            _VANILLA_GEOM_HASHES = set(doc.get('hashes', []))
        except Exception:
            _VANILLA_GEOM_HASHES = set()
    return _VANILLA_GEOM_HASHES


@storage_costumes_bp.route('/api/mex/storage/animelee/detect', methods=['POST'])
def detect_animelee():
    """Detect Animelee (inverted-hull outline) costumes for a character.

    Runs the MexCLI geometry detector over the character's costume zips, drops
    vanilla geometry, and groups hits by geomHash (same fingerprint = same model
    in different colours). A group is 'known' when its geometry already appears
    inside an Animelee folder — propagating your existing labels to colour
    variants you haven't foldered yet.
    """
    try:
        from blueprints.custom_characters import _run_mexcli
        from collections import defaultdict

        data = request.json or {}
        character = data.get('character')
        if not character:
            return jsonify({'success': False, 'error': 'Missing character parameter'}), 400

        metadata = load_metadata()
        char_data = get_char_data(metadata, character) if metadata else None
        if not char_data:
            return jsonify({'success': False, 'error': f'Character {character} not found'}), 404
        skins = char_data.get('skins', [])

        folder_names = {s['id']: s.get('name', '') for s in skins if s.get('type') == 'folder'}
        anime_fids = {fid for fid, nm in folder_names.items() if 'anim' in nm.lower()}

        char_folder = STORAGE_PATH / character
        id_to_skin = {}
        items = []
        for s in skins:
            if s.get('type') == 'folder':
                continue
            fn = s.get('filename')
            if not fn:
                continue
            zp = char_folder / fn
            if not zp.exists():
                continue
            id_to_skin[s['id']] = s
            items.append({'key': s['id'], 'path': str(zp)})

        if not items:
            return jsonify({'success': True, 'character': character, 'groups': [], 'totalNew': 0,
                            'animeFolders': [{'id': f, 'name': folder_names[f]} for f in anime_fids]})

        manifest_path = None
        try:
            with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False, encoding='utf-8') as mf:
                json.dump({'items': items}, mf)
                manifest_path = mf.name
            out = _run_mexcli('detect-outline', '--batch', manifest_path)
        finally:
            if manifest_path:
                try:
                    os.unlink(manifest_path)
                except OSError:
                    pass

        results = out.get('results', []) if isinstance(out, dict) else []
        res_by_id = {r.get('key'): r for r in results}
        vanilla = _load_vanilla_geom_hashes()

        # geometry fingerprints already confirmed Animelee (foldered members)
        confirmed_geom = set()
        for s in skins:
            if s.get('type') == 'folder' or s.get('folder_id') not in anime_fids:
                continue
            r = res_by_id.get(s.get('id'))
            if r and r.get('success') and r.get('geomHash'):
                confirmed_geom.add(r['geomHash'])

        groups_map = defaultdict(list)
        for r in results:
            if not r.get('success'):
                continue
            if (r.get('dupCullAsym', 0) < ANIMELEE_CULLASYM_MIN
                    or r.get('asymDupMax', 0) < ANIMELEE_ASYMMAX_MIN):
                continue
            gh = r.get('geomHash') or ''
            if gh and gh in vanilla:
                continue   # vanilla/recolor geometry, never Animelee
            s = id_to_skin.get(r.get('key'))
            if not s:
                continue
            groups_map[gh].append({
                'id': s.get('id'),
                'name': s.get('name') or s.get('id'),
                'alreadyFoldered': bool(s.get('folder_id') in anime_fids),
                'folderId': s.get('folder_id'),
                'asymMax': r.get('asymDupMax', 0),
            })

        groups = []
        for gh, members in groups_map.items():
            unfoldered = sum(1 for m in members if not m['alreadyFoldered'])
            groups.append({
                'geomHash': gh,
                'known': gh in confirmed_geom,
                'skins': members,
                'unfolderedCount': unfoldered,
            })
        groups.sort(key=lambda g: (-g['unfolderedCount'], not g['known']))

        return jsonify({
            'success': True,
            'character': character,
            'groups': groups,
            'totalNew': sum(g['unfolderedCount'] for g in groups),
            'animeFolders': [{'id': f, 'name': folder_names[f]} for f in anime_fids],
        })
    except Exception as e:
        logger.error(f"Detect animelee error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/animelee/apply', methods=['POST'])
def apply_animelee():
    """Move the given skins into an Animelee folder (reusing one if it exists,
    else creating it). Atomic: one metadata write."""
    try:
        data = request.json or {}
        character = data.get('character')
        skin_ids = data.get('skinIds') or []
        folder_id = data.get('folderId')
        folder_name = data.get('folderName') or 'Animelee'

        if not character or not skin_ids:
            return jsonify({'success': False, 'error': 'Missing character or skinIds'}), 400

        metadata = load_metadata(default={'characters': {}})
        characters = metadata.setdefault('characters', {})
        character_data = characters.setdefault(character, {})
        skins = character_data.setdefault('skins', [])

        if folder_id:
            folder, _ = find_folder_in_skins(skins, folder_id)
            if not folder:
                return jsonify({'success': False, 'error': f'Folder {folder_id} not found'}), 404
        else:
            folder_id = f"folder_{uuid.uuid4().hex[:8]}"
            skins.append({'type': 'folder', 'id': folder_id, 'name': folder_name, 'expanded': True})

        wanted = set(skin_ids)
        moved = 0
        for s in skins:
            if s.get('type') != 'folder' and s.get('id') in wanted:
                s['folder_id'] = folder_id
                moved += 1

        save_metadata(metadata)
        logger.info(f"[OK] Animelee: moved {moved} skin(s) into {folder_id} for {character}")
        return jsonify({'success': True, 'folderId': folder_id, 'moved': moved, 'skins': skins})
    except Exception as e:
        logger.error(f"Apply animelee error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_costumes_bp.route('/api/mex/storage/animelee/convert', methods=['POST'])
def convert_animelee():
    """Make a COPY of a costume with the Animelee inverted-hull outline added or
    removed; the original is never touched.

    {character, skinId, mode: 'add'|'remove'} -> a new vault costume.

    'add' generates a black, front-culled, normal-offset duplicate of every body
    mesh (MexCLI convert-outline --mode generate); 'remove' deletes the outline
    shells. The new DAT's CSP/stock are re-rendered through the canonical asset
    path so the copy looks right. See memory animelee-detection.
    """
    try:
        # Gated behind the AI Studio flag (NUCLEUS_AI_LAB) — off in packaged builds,
        # on in dev — so the converter stays unshipped for now. See skin_lab_ai.
        try:
            from blueprints.skin_lab_ai import AI_LAB_ENABLED
        except Exception:
            AI_LAB_ENABLED = os.environ.get('NUCLEUS_AI_LAB', '1') != '0'
        if not AI_LAB_ENABLED:
            return jsonify({'success': False, 'error': 'The Animelee converter is not enabled'}), 403

        from blueprints.custom_characters import _run_mexcli
        from blueprints.import_unified.helpers import compute_dat_hash
        from skinlab.costume_assets import build_csp_and_stock

        data = request.json or {}
        character = data.get('character')
        skin_id = data.get('skinId')
        mode = (data.get('mode') or 'add').lower()
        if mode not in ('add', 'remove'):
            return jsonify({'success': False, 'error': "mode must be 'add' or 'remove'"}), 400
        if not character or not skin_id:
            return jsonify({'success': False, 'error': 'Missing character or skinId'}), 400

        cli_mode = 'generate' if mode == 'add' else 'remove'

        metadata = load_metadata()
        char_data = get_char_data(metadata, character) if metadata else None
        if not char_data:
            return jsonify({'success': False, 'error': f'Character {character} not found'}), 404
        skins = char_data.get('skins', [])
        src = next((s for s in skins
                    if s.get('type') != 'folder' and s.get('id') == skin_id), None)
        if not src:
            return jsonify({'success': False, 'error': f'Costume {skin_id} not found'}), 404

        char_folder = STORAGE_PATH / character
        src_zip = char_folder / (src.get('filename') or f"{skin_id}.zip")
        if not src_zip.exists():
            return jsonify({'success': False, 'error': f'Costume zip not found: {skin_id}'}), 404

        # ---- extract the primary DAT and run the geometry conversion -----------
        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            with zipfile.ZipFile(src_zip, 'r') as zf:
                zf.extractall(tdir)
            dat_path = find_extracted_costume_archive(tdir)
            if not dat_path or not os.path.exists(dat_path):
                return jsonify({'success': False, 'error': 'No DAT found inside the costume'}), 400
            dat_name = os.path.basename(dat_path)

            # Is the SOURCE a vanilla-based recolor? If so, its low-poly hide
            # indices are valid, and since we only APPEND outline DObjs they stay
            # valid for the copy too — but the CSP renderer's replaced-model guard
            # keys on DObj count and would wrongly drop hiding. Remember this so we
            # can keep the hide for the render below. A genuinely custom source
            # stays under the guard (vanilla indices wouldn't match its geometry).
            source_vanilla_based = False
            try:
                from generate_csp import model_is_replacement
                source_vanilla_based = not model_is_replacement(str(dat_path), character)
            except Exception:
                source_vanilla_based = False

            out_dat = tdir / 'converted.dat'
            res = _run_mexcli('convert-outline', '--mode', cli_mode,
                              '--in', str(dat_path), '--out', str(out_dat))
            if not res.get('success') or res.get('_returncode', 1) != 0 or not out_dat.exists():
                return jsonify({'success': False,
                                'error': res.get('error') or 'Geometry conversion failed'}), 500
            changed = res.get('dobjsAdded', res.get('dobjsRemoved', 0)) or 0
            if changed == 0:
                msg = ('This costume has no body geometry to outline.' if mode == 'add'
                       else 'No Animelee outline was found on this costume to remove.')
                return jsonify({'success': False, 'error': msg}), 400
            dat_data = out_dat.read_bytes()

        # ---- name + unique id for the copy ------------------------------------
        suffix = 'Animelee' if mode == 'add' else 'No Outline'
        base_name = src.get('color') or src.get('name') or skin_id
        display_name = f"{base_name} ({suffix})"
        costume_code = src.get('costume_code') or get_char_prefix(character)

        existing_ids = {s.get('id') for s in skins}
        slug = 'animelee' if mode == 'add' else 'nooutline'
        new_id = f"{skin_id}-{slug}"
        while new_id in existing_ids or (char_folder / f"{new_id}.zip").exists():
            new_id = f"{skin_id}-{slug}-{uuid.uuid4().hex[:4]}"

        # ---- render CSP + stock for the converted geometry --------------------
        # For a vanilla-based source, keep the low-poly hide (the appended outline
        # DObjs don't shift the original indices) so the off-screen magnifier mesh
        # stays hidden in the portrait.
        prev_fix = os.environ.get('CSP_DISABLE_REPLACEMENT_FIX')
        if source_vanilla_based:
            os.environ['CSP_DISABLE_REPLACEMENT_FIX'] = '1'
        try:
            assets = build_csp_and_stock(character, costume_code, dat_data, log=logger)
        finally:
            if prev_fix is None:
                os.environ.pop('CSP_DISABLE_REPLACEMENT_FIX', None)
            else:
                os.environ['CSP_DISABLE_REPLACEMENT_FIX'] = prev_fix
        csp_data, csp_source = assets.get('csp'), assets.get('csp_source')
        stock_data, stock_source = assets.get('stock'), assets.get('stock_source')

        # ---- write the new costume zip (source files, DAT swapped, fresh CSP) --
        new_zip = char_folder / f"{new_id}.zip"
        drop = {'csp.png', 'csp', 'stc.png', 'stock.png', 'stock'}
        with zipfile.ZipFile(src_zip, 'r') as sz, \
                zipfile.ZipFile(new_zip, 'w', zipfile.ZIP_DEFLATED) as dz:
            for item in sz.infolist():
                if item.filename.lower() in drop:
                    continue
                if os.path.basename(item.filename) == dat_name:
                    dz.writestr(item, dat_data)
                else:
                    dz.writestr(item, sz.read(item.filename))
            if csp_data:
                dz.writestr('csp.png', csp_data)
            if stock_data:
                dz.writestr('stc.png', stock_data)

        if csp_data:
            (char_folder / f"{new_id}_csp.png").write_bytes(csp_data)
        if stock_data:
            (char_folder / f"{new_id}_stc.png").write_bytes(stock_data)

        new_skin = {
            'id': new_id,
            'color': display_name,
            'costume_code': costume_code,
            'filename': f"{new_id}.zip",
            'has_csp': csp_data is not None,
            'has_stock': stock_data is not None,
            'csp_source': csp_source,
            'stock_source': stock_source if stock_data else None,
            'date_added': datetime.now().isoformat(),
            'dat_hash': compute_dat_hash(dat_data),
            'slippi_safe': src.get('slippi_safe', False),
            'slippi_tested': src.get('slippi_tested', False),
            'slippi_test_date': src.get('slippi_test_date'),
            'slippi_manual_override': src.get('slippi_manual_override'),
            'converted_from': skin_id,
            'animelee_converted': mode,
        }

        idx = next((i for i, s in enumerate(skins) if s.get('id') == skin_id), len(skins) - 1)
        skins.insert(idx + 1, new_skin)
        save_metadata(metadata)

        logger.info(f"[OK] Animelee convert ({mode}): {character}/{skin_id} -> {new_id} "
                    f"({changed} DObjs)")
        return jsonify({'success': True, 'character': character, 'mode': mode,
                        'changed': changed, 'skin': new_skin})
    except Exception as e:
        logger.error(f"Convert animelee error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
