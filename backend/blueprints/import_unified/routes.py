"""
The unified /api/mex/import/file endpoint - accepts ZIP/7z/DAT/USD uploads,
auto-detects mod type (character, stage, xdelta patch, CSS icon grid), and
dispatches to the matching import pipeline.
"""

import os
import zipfile
import tempfile
import logging
import uuid
from pathlib import Path
from datetime import datetime
from flask import request, jsonify

from core.config import STORAGE_PATH
from core.metadata import load_metadata, save_metadata
from character_detector import detect_character_from_zip
from stage_detector import detect_stage_from_zip
from dat_processor import validate_for_slippi
from blueprints.xdelta import load_xdelta_metadata, save_xdelta_metadata
from blueprints.menus import install_icon_grid_mod, looks_like_icon_grid_zip
from extra_types import get_storage_character

from . import import_bp
from .helpers import (
    sanitize_filename,
    compute_dat_hash,
    check_duplicate_skin,
    check_duplicate_stage,
    check_duplicate_patch,
    check_duplicate_effect,
)
from .characters import fix_ice_climbers_pairing, import_character_costume
from .stages import import_stage_mod
from .effects import _import_effect_mod

logger = logging.getLogger(__name__)


@import_bp.route('/api/mex/import/file', methods=['POST'])
def import_file():
    """
    Unified import endpoint for both character costumes and stage mods.

    Accepts ZIP file upload, auto-detects type, and processes accordingly.
    Includes slippi safety validation with user choice to fix or import as-is.
    """
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Check if file is a supported type
        fname_lower = file.filename.lower()
        is_zip = fname_lower.endswith('.zip')
        is_7z = fname_lower.endswith('.7z')
        is_dat = fname_lower.endswith('.dat')
        is_usd = fname_lower.endswith('.usd')

        if not (is_zip or is_7z or is_dat or is_usd):
            return jsonify({
                'success': False,
                'error': 'Only ZIP, 7z, DAT, and USD files are supported'
            }), 400

        # Get slippi_action parameter (can be "fix", "import_as_is", or None)
        slippi_action = request.form.get('slippi_action')

        # Get duplicate_action parameter (can be "import_anyway" or None)
        duplicate_action = request.form.get('duplicate_action')

        # Get custom_title parameter if provided (for nucleus:// imports)
        custom_title = request.form.get('custom_title')
        logger.info(f"[DEBUG] custom_title from form: '{custom_title}' (type: {type(custom_title).__name__})")

        # Get mod type hints from nucleus:// protocol (set by website tags)
        mod_type = request.form.get('mod_type')  # 'effect', 'patch', or None
        effect_type = request.form.get('effect_type')  # e.g. 'gun', 'laser', 'sword'
        logger.info(f"[DEBUG] mod_type: {mod_type}, effect_type: {effect_type}")

        if is_dat or is_usd:
            # Wrap raw costume archives in a temp zip so the rest of the pipeline runs unchanged.
            dat_bytes = file.read()
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                temp_zip_path = tmp.name
            with zipfile.ZipFile(temp_zip_path, 'w') as zf:
                zf.writestr(file.filename, dat_bytes)
        else:
            suffix = '.zip' if is_zip else '.7z'
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                file.save(tmp.name)
                temp_zip_path = tmp.name

        try:
            logger.info(f"=== UNIFIED IMPORT: {file.filename} ===")

            # EXPLICIT EFFECT ROUTING: If website told us this is an effect mod,
            # bypass auto-detection (which would misidentify the .dat as a costume)
            if mod_type == 'effect' and effect_type:
                logger.info(f"Explicit effect import: type={effect_type}")

                # DUPLICATE DETECTION for effects
                if duplicate_action is None:
                    try:
                        with zipfile.ZipFile(temp_zip_path, 'r') as zf:
                            dat_files = [n for n in zf.namelist()
                                         if n.lower().endswith('.dat')
                                         and not n.startswith('__MACOSX')]
                            if dat_files:
                                dat_data = zf.read(dat_files[0])
                                file_hash = compute_dat_hash(dat_data)
                                name_stem = Path(file.filename).stem
                                character = name_stem.split('_')[0] if '_' in name_stem else name_stem
                                effect_type_key = effect_type.lower()
                                storage_char = get_storage_character(character, effect_type_key)
                                metadata = load_metadata(default={'characters': {}})
                                existing = check_duplicate_effect(storage_char, effect_type_key, file_hash, metadata)
                                if existing:
                                    screenshot_url = (
                                        f"/storage/{storage_char}/{existing['screenshot']}"
                                        if existing.get('screenshot') else None
                                    )
                                    return jsonify({
                                        'success': False,
                                        'type': 'duplicate_dialog',
                                        'mod_type': 'effect',
                                        'duplicate_skins': [{
                                            'character': storage_char,
                                            'color': existing['name'],
                                            'existing_skin': {
                                                'id': existing['id'],
                                                'name': existing['name'],
                                                'csp_url': screenshot_url
                                            }
                                        }],
                                        'message': 'You already have this effect!'
                                    }), 200
                    except (zipfile.BadZipFile, KeyError):
                        pass

                result = _import_effect_mod(temp_zip_path, file.filename, effect_type, custom_title)
                if result:
                    return jsonify(result) if result.get('success') else (jsonify(result), 400)

            # EXPLICIT CSS ICON GRID ROUTING
            if mod_type == 'css_icon_grid':
                logger.info('Explicit CSS icon grid import')
                try:
                    icon_grid_name = custom_title or Path(file.filename).stem
                    mods = install_icon_grid_mod(temp_zip_path, name=icon_grid_name)
                    names = ', '.join(m.get('name', '?') for m in mods)
                    return jsonify({
                        'success': True,
                        'type': 'menu_mod',
                        'menu_mod_type': 'css_icon_grid',
                        'mods': mods,
                        'imported_count': len(mods),
                        'message': f"Imported {len(mods)} icon grid mod(s): {names}"
                    })
                except zipfile.BadZipFile:
                    return jsonify({'success': False, 'error': 'Invalid or corrupt zip file'}), 400

            # PHASE 1: Try character detection first
            logger.info("Phase 1: Attempting character detection...")
            character_infos = detect_character_from_zip(temp_zip_path)

            if character_infos:
                logger.info(f"[OK] Detected {len(character_infos)} character costume(s)")

                # SLIPPI VALIDATION: Check if any costume needs slippi validation dialog
                if slippi_action is None:
                    # First time upload - validate slippi safety
                    unsafe_costumes = []
                    with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                        for char_info in character_infos:
                            # Extract DAT to temp file for validation
                            dat_data = zip_ref.read(char_info['dat_file'])
                            with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as tmp_dat:
                                tmp_dat.write(dat_data)
                                tmp_dat_path = tmp_dat.name

                            try:
                                validation = validate_for_slippi(tmp_dat_path, auto_fix=False)
                                if not validation['slippi_safe']:
                                    unsafe_costumes.append({
                                        'character': char_info['character'],
                                        'color': char_info['color']
                                    })
                            finally:
                                os.unlink(tmp_dat_path)

                    # If any costume is not slippi safe, ask user what to do
                    if unsafe_costumes:
                        return jsonify({
                            'success': False,
                            'type': 'slippi_dialog',
                            'unsafe_costumes': unsafe_costumes,
                            'message': 'This costume is not Slippi safe. Choose an action:'
                        }), 200

                # DUPLICATE DETECTION: Check if any costume already exists (by DAT hash)
                if duplicate_action is None:
                    # Load metadata for duplicate checking
                    metadata = load_metadata(default={'characters': {}, 'stages': {}})

                    duplicate_skins = []
                    with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                        for char_info in character_infos:
                            dat_data = zip_ref.read(char_info['dat_file'])
                            dat_hash = compute_dat_hash(dat_data)

                            existing_skin = check_duplicate_skin(char_info['character'], dat_hash, metadata)
                            if existing_skin:
                                # Build CSP URL for preview
                                csp_url = f"/storage/{char_info['character']}/{existing_skin['id']}_csp.png"
                                duplicate_skins.append({
                                    'character': char_info['character'],
                                    'color': char_info['color'],
                                    'existing_skin': {
                                        'id': existing_skin['id'],
                                        'name': f"{char_info['character']} - {existing_skin.get('color', existing_skin['id'])}",
                                        'csp_url': csp_url
                                    }
                                })

                    # Save metadata to cache any computed dat_hash values (backfill)
                    save_metadata(metadata)

                    # If any costume is a duplicate, ask user what to do
                    if duplicate_skins:
                        return jsonify({
                            'success': False,
                            'type': 'duplicate_dialog',
                            'duplicate_skins': duplicate_skins,
                            'message': 'You already have this skin!'
                        }), 200

                # Sort Ice Climbers: Popo before Nana (Nana copies Popo's CSP)
                def ice_climbers_sort_key(char_info):
                    if char_info.get('is_popo'):
                        return 0  # Popo first
                    elif char_info.get('is_nana'):
                        return 1  # Nana second
                    else:
                        return 0  # Other characters

                character_infos_sorted = sorted(character_infos, key=ice_climbers_sort_key)

                # Determine auto_fix setting based on user choice
                auto_fix = (slippi_action == 'fix')

                # Import each detected costume
                results = []
                imported_skin_ids = {}  # Track actual skin IDs: costume_code -> skin_id
                should_play_camera_sound = False
                for character_info in character_infos_sorted:
                    logger.info(f"  - Importing {character_info['character']} - {character_info['color']}")
                    logger.info(f"[DEBUG] Calling import_character_costume with custom_name='{custom_title}'")
                    result = import_character_costume(temp_zip_path, character_info, file.filename, auto_fix=auto_fix, custom_name=custom_title)
                    if result.get('success'):
                        should_play_camera_sound = should_play_camera_sound or result.get('camera_sound', False)
                        results.append({
                            'character': character_info['character'],
                            'color': character_info['color'],
                            'csp_source': result.get('csp_source')
                        })
                        # Track the actual skin ID that was created
                        if result.get('skin_id'):
                            imported_skin_ids[character_info['costume_code']] = result['skin_id']

                # Post-process: Fix Ice Climbers pairing with actual skin IDs
                if any(ci.get('is_popo') or ci.get('is_nana') for ci in character_infos_sorted):
                    fix_ice_climbers_pairing(character_infos_sorted, imported_skin_ids)

                return jsonify({
                    'success': True,
                    'type': 'character',
                    'camera_sound': should_play_camera_sound,
                    'imported_count': len(results),
                    'costumes': results,
                    'message': f"Imported {len(results)} costume(s)"
                })

            # PHASE 2: Try stage detection
            logger.info("Phase 2: Attempting stage detection...")
            stage_infos = detect_stage_from_zip(temp_zip_path)

            if stage_infos:
                logger.info(f"[OK] Detected {len(stage_infos)} stage mod(s)")

                # DUPLICATE DETECTION for stages
                if duplicate_action is None:
                    stage_metadata = load_metadata(default={'characters': {}, 'stages': {}})

                    duplicate_skins = []
                    with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                        for stage_info in stage_infos:
                            dat_data = zip_ref.read(stage_info['stage_file'])
                            dat_hash = compute_dat_hash(dat_data)
                            existing = check_duplicate_stage(stage_info['folder'], dat_hash, stage_metadata)
                            if existing:
                                screenshot_url = (
                                    f"/storage/das/{stage_info['folder']}/{existing['screenshot_filename']}"
                                    if existing.get('screenshot_filename') else None
                                )
                                duplicate_skins.append({
                                    'character': stage_info['stage_name'],
                                    'color': existing['name'],
                                    'existing_skin': {
                                        'id': existing['id'],
                                        'name': f"{stage_info['stage_name']} - {existing['name']}",
                                        'csp_url': screenshot_url
                                    }
                                })
                    if duplicate_skins:
                        return jsonify({
                            'success': False,
                            'type': 'duplicate_dialog',
                            'mod_type': 'stage',
                            'duplicate_skins': duplicate_skins,
                            'message': 'You already have this stage!'
                        }), 200

                # Import each detected stage
                results = []
                for stage_info in stage_infos:
                    logger.info(f"  - Importing {stage_info['stage_name']}")
                    result = import_stage_mod(temp_zip_path, stage_info, file.filename, custom_name=custom_title)
                    if result.get('success'):
                        results.append({
                            'stage': stage_info['stage_name'],
                            'variant': result.get('variant_id')
                        })

                return jsonify({
                    'success': True,
                    'type': 'stage',
                    'imported_count': len(results),
                    'stages': results,
                    'message': f"Imported {len(results)} stage variant(s)"
                })

            # PHASE 3: Try patch (xdelta) detection
            logger.info("Phase 3: Attempting patch detection...")
            try:
                with zipfile.ZipFile(temp_zip_path, 'r') as zf:
                    xdelta_files = [n for n in zf.namelist() if n.lower().endswith('.xdelta')]
                    image_exts = {'.png', '.jpg', '.jpeg', '.gif'}
                    image_files = [n for n in zf.namelist()
                                   if Path(n).suffix.lower() in image_exts
                                   and not n.startswith('__MACOSX')]

                    if xdelta_files:
                        logger.info(f"[OK] Detected {len(xdelta_files)} xdelta patch(es)")
                        xdelta_dir = STORAGE_PATH / "xdelta"
                        xdelta_dir.mkdir(exist_ok=True)

                        patches = load_xdelta_metadata()
                        results = []

                        for xdelta_name in xdelta_files:
                            # Read data first for duplicate check and writing
                            xdelta_data = zf.read(xdelta_name)
                            file_hash = compute_dat_hash(xdelta_data)

                            # DUPLICATE DETECTION for patches
                            if duplicate_action is None:
                                existing = check_duplicate_patch(file_hash, patches)
                                if existing:
                                    screenshot_url = f"/storage/xdelta/{existing['id']}.png"
                                    return jsonify({
                                        'success': False,
                                        'type': 'duplicate_dialog',
                                        'mod_type': 'patch',
                                        'duplicate_skins': [{
                                            'character': 'Patch',
                                            'color': existing['name'],
                                            'existing_skin': {
                                                'id': existing['id'],
                                                'name': existing['name'],
                                                'csp_url': screenshot_url
                                            }
                                        }],
                                        'message': 'You already have this patch!'
                                    }), 200

                            patch_id = str(uuid.uuid4())[:8]

                            # Save xdelta file
                            xdelta_path = xdelta_dir / f"{patch_id}.xdelta"
                            xdelta_path.write_bytes(xdelta_data)

                            # Save first image as screenshot
                            if image_files:
                                img_data = zf.read(image_files[0])
                                img_path = xdelta_dir / f"{patch_id}.png"
                                img_path.write_bytes(img_data)

                            # Derive name from custom_title, xdelta filename, or zip filename
                            patch_name = custom_title or Path(xdelta_name).stem or Path(file.filename).stem
                            patch_name = sanitize_filename(patch_name)

                            patches.append({
                                'id': patch_id,
                                'name': patch_name,
                                'description': '',
                                'filename': Path(xdelta_name).name,
                                'created': datetime.now().isoformat(),
                                'file_hash': file_hash
                            })
                            results.append({'id': patch_id, 'name': patch_name})
                            logger.info(f"  - Imported patch: {patch_name} ({patch_id})")

                        save_xdelta_metadata(patches)

                        return jsonify({
                            'success': True,
                            'type': 'patch',
                            'imported_count': len(results),
                            'patches': results,
                            'message': f"Imported {len(results)} patch(es)"
                        })
            except zipfile.BadZipFile:
                pass  # Not a valid zip, fall through to error

            # PHASE 4: Try CSS icon grid detection
            logger.info('Phase 4: Attempting CSS icon grid detection...')
            if looks_like_icon_grid_zip(temp_zip_path):
                logger.info('[OK] Detected CSS icon grid mod')
                try:
                    icon_grid_name = custom_title or Path(file.filename).stem
                    mods = install_icon_grid_mod(temp_zip_path, name=icon_grid_name)
                    names = ', '.join(m.get('name', '?') for m in mods)
                    return jsonify({
                        'success': True,
                        'type': 'menu_mod',
                        'menu_mod_type': 'css_icon_grid',
                        'mods': mods,
                        'imported_count': len(mods),
                        'message': f"Imported {len(mods)} icon grid mod(s): {names}"
                    })
                except (zipfile.BadZipFile, RuntimeError):
                    pass

            # PHASE 5: Detection failed
            logger.warning("Could not detect mod type")
            return jsonify({
                'success': False,
                'error': 'Could not detect mod type. ZIP does not contain any recognized files (.dat, .xdelta, GrXx stage files)'
            }), 400

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_zip_path)
            except:
                pass

    except Exception as e:
        logger.error(f"Import error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Import error: {str(e)}'
        }), 500
