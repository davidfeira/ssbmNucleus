"""
Import Unified Blueprint - Unified file import endpoint.

Handles importing both character costumes and stage mods from ZIP/7z files,
with auto-detection and slippi safety validation.
"""

import os
import re
import json
import zipfile
import tempfile
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify

from core.config import STORAGE_PATH, VANILLA_ASSETS_DIR
from character_detector import detect_character_from_zip
from stage_detector import detect_stage_from_zip
from dat_processor import validate_for_slippi
from generate_csp import generate_csp

logger = logging.getLogger(__name__)

import_bp = Blueprint('import', __name__)


def sanitize_filename(name):
    """Sanitize filename by removing/replacing invalid characters."""
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


def compute_dat_hash(dat_data: bytes) -> str:
    """Compute MD5 hash of DAT file data."""
    return hashlib.md5(dat_data).hexdigest()


def compute_hash_from_stored_skin(character: str, skin: dict) -> str:
    """
    Extract DAT from stored zip and compute its hash.
    Used to backfill hashes for skins imported before this feature.
    """
    try:
        zip_path = STORAGE_PATH / character / skin['filename']
        if not zip_path.exists():
            logger.warning(f"Zip file not found for hash computation: {zip_path}")
            return None

        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Find the .dat file in the zip
            for name in zf.namelist():
                if name.lower().endswith('.dat'):
                    dat_data = zf.read(name)
                    computed_hash = compute_dat_hash(dat_data)
                    logger.info(f"Computed hash for existing skin {skin['id']}: {computed_hash}")
                    return computed_hash
        logger.warning(f"No DAT file found in zip for {skin['id']}")
        return None
    except Exception as e:
        logger.warning(f"Failed to compute hash for {skin['id']}: {e}")
        return None


def check_duplicate_skin(character: str, dat_hash: str, metadata: dict) -> dict:
    """
    Check if a skin with this DAT hash already exists for the character.
    Computes hash on-demand for skins missing dat_hash (backfill).

    Returns the existing skin entry if found, None otherwise.
    """
    char_data = metadata.get('characters', {}).get(character, {})
    for skin in char_data.get('skins', []):
        existing_hash = skin.get('dat_hash')

        # If skin doesn't have hash, compute it from stored zip (backfill)
        if existing_hash is None:
            existing_hash = compute_hash_from_stored_skin(character, skin)
            if existing_hash:
                # Cache the computed hash in metadata (will be saved later)
                skin['dat_hash'] = existing_hash

        if existing_hash == dat_hash:
            return skin
    return None


def extract_custom_name_from_filename(filename: str, character_name: str) -> str:
    """
    Extract a custom name from the zip filename to use in costume ID.

    Args:
        filename: Original zip filename (e.g., "Villager Climbers (2).zip")
        character_name: Detected character name (e.g., "Ice Climbers")

    Returns:
        Custom name string, or None if no meaningful name could be extracted

    Examples:
        "Villager Climbers (2).zip" -> "villager-climbers"
        "Fox - Shadow Link.zip" -> "shadow-link"
        "Ice Climbers_CustomSkin.zip" -> "customskin"
        "costume.zip" -> None (too generic)
    """
    # Remove file extension
    base_name = Path(filename).stem

    # Remove numbers in parentheses: "(2)", "(1)", etc.
    base_name = re.sub(r'\s*\(\d+\)\s*$', '', base_name)

    # Try to remove character name prefix if present
    # Handle patterns like "Fox - CustomName" or "Ice Climbers - CustomName"
    char_pattern = re.escape(character_name)
    base_name = re.sub(rf'^{char_pattern}\s*[-_:]\s*', '', base_name, flags=re.IGNORECASE)

    # Remove common version patterns: v1, v2, V1.0, etc.
    base_name = re.sub(r'\s*[vV]\d+(\.\d+)?\s*$', '', base_name)

    # Clean up: convert to lowercase, replace spaces/underscores with hyphens
    base_name = base_name.lower()
    base_name = re.sub(r'[_\s]+', '-', base_name)

    # Remove special characters except hyphens
    base_name = re.sub(r'[^a-z0-9-]', '', base_name)

    # Remove multiple consecutive hyphens
    base_name = re.sub(r'-+', '-', base_name)

    # Remove leading/trailing hyphens
    base_name = base_name.strip('-')

    # Check if result is too generic or empty
    generic_names = {'costume', 'skin', 'mod', 'custom', 'default', 'new', 'import'}
    if not base_name or base_name in generic_names or len(base_name) < 2:
        return None

    return base_name


def fix_ice_climbers_pairing(character_infos: list, imported_skin_ids: dict):
    """
    Fix Ice Climbers pairing after import using actual skin IDs.

    Args:
        character_infos: List of character info dicts with pairing metadata
        imported_skin_ids: Dict mapping costume_code -> actual skin_id created
    """
    try:
        # Load metadata
        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if 'Ice Climbers' not in metadata.get('characters', {}):
            return

        # Build a mapping of costume_code -> character_info for easy lookup
        info_by_code = {ci['costume_code']: ci for ci in character_infos}

        # Update each Ice Climbers skin with actual paired IDs
        updated = False
        for skin in metadata['characters']['Ice Climbers']['skins']:
            # Skip if this specific skin wasn't just imported
            # Check by skin ID, not costume code, since multiple skins can share the same costume code
            if skin['id'] not in imported_skin_ids.values():
                continue

            costume_code = skin['costume_code']
            char_info = info_by_code.get(costume_code)
            if not char_info:
                continue

            # Update Popo with actual Nana ID
            if char_info.get('is_popo') and char_info.get('pair_costume_code'):
                nana_costume_code = char_info['pair_costume_code']
                actual_nana_id = imported_skin_ids.get(nana_costume_code)
                if actual_nana_id:
                    skin['paired_nana_id'] = actual_nana_id
                    logger.info(f"Linked Popo {skin['id']} -> Nana {actual_nana_id}")
                    updated = True

            # Update Nana with actual Popo ID
            elif char_info.get('is_nana') and char_info.get('pair_costume_code'):
                popo_costume_code = char_info['pair_costume_code']
                actual_popo_id = imported_skin_ids.get(popo_costume_code)
                if actual_popo_id:
                    skin['paired_popo_id'] = actual_popo_id
                    logger.info(f"Linked Nana {skin['id']} -> Popo {actual_popo_id}")
                    updated = True

        # Save metadata if we made changes
        if updated:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info("[OK] Updated Ice Climbers pairing with actual skin IDs")

    except Exception as e:
        logger.error(f"Failed to fix Ice Climbers pairing: {e}", exc_info=True)


def import_character_costume(zip_path: str, char_info: dict, original_filename: str, auto_fix: bool = False, custom_name: str = None) -> dict:
    """
    Import a character costume to storage.

    Args:
        zip_path: Path to the uploaded ZIP file
        char_info: Character detection info
        original_filename: Original filename of the upload
        auto_fix: If True, apply slippi fixes to the DAT file
        custom_name: Optional custom name to use instead of extracting from filename
    """
    try:
        # Load metadata
        metadata_file = STORAGE_PATH / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {'characters': {}, 'stages': {}}

        # Ensure 'stages' section exists
        if 'stages' not in metadata:
            metadata['stages'] = {}

        character = char_info['character']

        # Create character folder
        char_folder = STORAGE_PATH / character
        char_folder.mkdir(parents=True, exist_ok=True)

        # Generate unique ID for this skin
        char_data = metadata.get('characters', {}).get(character, {'skins': []})
        existing_ids = [skin['id'] for skin in char_data.get('skins', [])]

        logger.info(f"[DEBUG import_character_costume] custom_name parameter: '{custom_name}' (type: {type(custom_name).__name__})")
        logger.info(f"[DEBUG import_character_costume] original_filename: '{original_filename}'")

        # Use provided custom name, or extract from filename
        if not custom_name:
            logger.info(f"[DEBUG] custom_name is falsy, extracting from filename")
            custom_name = extract_custom_name_from_filename(original_filename, character)
            logger.info(f"[DEBUG] Extracted custom_name from filename: '{custom_name}'")

        # Extract descriptive name from DAT filename (remove .dat extension and clean up)
        dat_basename = os.path.splitext(os.path.basename(char_info['dat_file']))[0]
        # Clean and sanitize: lowercase, replace spaces/special chars with hyphens
        dat_name_clean = re.sub(r'[^\w\s-]', '', dat_basename)  # Remove special chars except space and hyphen
        dat_name_clean = re.sub(r'[\s_]+', '-', dat_name_clean)  # Replace spaces/underscores with hyphens
        dat_name_clean = dat_name_clean.lower().strip('-')  # Lowercase and remove leading/trailing hyphens

        # Generate base ID: use custom name if found, otherwise use DAT filename
        if custom_name:
            base_id = f"{custom_name}-{dat_name_clean}"
            logger.info(f"Using custom name from filename: '{custom_name}' -> '{base_id}'")
        else:
            base_id = dat_name_clean
            logger.info(f"Using DAT filename as name: '{base_id}'")

        # Handle duplicates: append 2-digit counter without dash (e.g., "name01", "name02")
        skin_id = base_id
        counter = 1
        while skin_id in existing_ids:
            skin_id = f"{base_id}{counter:02d}"
            counter += 1

        # Final paths
        final_zip = char_folder / f"{skin_id}.zip"

        # Copy files from uploaded ZIP to final ZIP with correct structure
        csp_source = 'imported'

        # SLIPPI VALIDATION: Validate DAT before importing
        slippi_validation = None
        dat_hash = None
        with zipfile.ZipFile(zip_path, 'r') as source_zip:
            # Extract DAT for validation
            dat_data = source_zip.read(char_info['dat_file'])

            # Compute hash of original DAT for duplicate detection
            dat_hash = compute_dat_hash(dat_data)
            logger.info(f"Computed DAT hash: {dat_hash}")

            with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as tmp_dat:
                tmp_dat.write(dat_data)
                tmp_dat_path = tmp_dat.name

            try:
                slippi_validation = validate_for_slippi(tmp_dat_path, auto_fix=auto_fix)
                logger.info(f"Slippi validation: slippi_safe={slippi_validation['slippi_safe']}, auto_fix={auto_fix}")

                # If auto_fix was applied, read the fixed DAT
                if auto_fix and slippi_validation.get('fix_applied'):
                    with open(tmp_dat_path, 'rb') as f:
                        dat_data = f.read()
                    logger.info("Using slippi-fixed DAT file")
            finally:
                os.unlink(tmp_dat_path)

        with zipfile.ZipFile(zip_path, 'r') as source_zip:
            with zipfile.ZipFile(final_zip, 'w') as dest_zip:
                # Copy DAT file (potentially fixed version)
                dest_zip.writestr(f"{char_info['costume_code']}Mod.dat", dat_data)

                # Handle CSP - copy if found, generate if missing
                csp_data = None
                if char_info['csp_file']:
                    # CSP found in ZIP - copy it
                    csp_data = source_zip.read(char_info['csp_file'])
                    logger.info(f"Using CSP from ZIP: {char_info['csp_file']}")
                else:
                    # No CSP in ZIP - generate one
                    logger.info("No CSP found in ZIP, generating...")

                    # Ice Climbers Popo: Extract both Popo and Nana DATs to same temp dir
                    # so generate_csp can find the pair and create composite CSP
                    if char_info.get('is_popo'):
                        logger.info("Ice Climbers Popo detected - extracting pair for composite CSP")
                        temp_dir = tempfile.mkdtemp()
                        try:
                            # Extract Popo DAT
                            popo_dat_name = os.path.basename(char_info['dat_file'])
                            tmp_dat_path = os.path.join(temp_dir, popo_dat_name)
                            with open(tmp_dat_path, 'wb') as f:
                                f.write(dat_data)

                            # Extract paired Nana DAT
                            nana_dat_name = os.path.basename(char_info['pair_dat_file'])
                            nana_dat_path = os.path.join(temp_dir, nana_dat_name)
                            nana_dat_data = source_zip.read(char_info['pair_dat_file'])
                            with open(nana_dat_path, 'wb') as f:
                                f.write(nana_dat_data)

                            # Generate composite CSP (generate_csp will detect pair)
                            generated_csp_path = generate_csp(tmp_dat_path)
                            if generated_csp_path and os.path.exists(generated_csp_path):
                                with open(generated_csp_path, 'rb') as f:
                                    csp_data = f.read()
                                logger.info("Successfully generated composite Ice Climbers CSP")
                                csp_source = 'generated'
                                # Clean up generated CSP
                                try:
                                    os.unlink(generated_csp_path)
                                except:
                                    pass
                            else:
                                logger.warning("Ice Climbers CSP generation failed")
                        finally:
                            # Clean up temp directory
                            try:
                                import shutil
                                shutil.rmtree(temp_dir)
                            except:
                                pass
                    else:
                        # Regular character or Nana - single DAT extraction
                        with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as tmp_dat:
                            tmp_dat.write(dat_data)
                            tmp_dat_path = tmp_dat.name

                        try:
                            generated_csp_path = generate_csp(tmp_dat_path)
                            if generated_csp_path and os.path.exists(generated_csp_path):
                                with open(generated_csp_path, 'rb') as f:
                                    csp_data = f.read()
                                logger.info("Successfully generated CSP")
                                csp_source = 'generated'
                                # Clean up generated CSP
                                try:
                                    os.unlink(generated_csp_path)
                                except:
                                    pass
                            else:
                                logger.warning("CSP generation failed")
                        finally:
                            # Clean up temp DAT
                            try:
                                os.unlink(tmp_dat_path)
                            except:
                                pass

                # Ice Climbers: Nana should copy composite CSP from Popo
                if char_info.get('is_nana') and not csp_data:
                    # Look for paired Popo in metadata
                    popo_color = char_info.get('pair_color')
                    if popo_color:
                        popo_id = f"{character.lower().replace(' ', '-')}-{popo_color.lower()}"

                        # Check if Popo already imported
                        if character in metadata.get('characters', {}):
                            for skin in metadata['characters'][character]['skins']:
                                if skin['id'] == popo_id:
                                    # Found Popo - copy its CSP
                                    popo_csp_path = STORAGE_PATH / character / f"{popo_id}_csp.png"
                                    if popo_csp_path.exists():
                                        csp_data = popo_csp_path.read_bytes()
                                        csp_source = 'copied_from_popo'
                                        logger.info(f"Copied composite CSP from Popo: {popo_id}")
                                    break

                # Save CSP to ZIP and storage if we have one
                if csp_data:
                    dest_zip.writestr('csp.png', csp_data)
                    # Save to storage for preview
                    storage_char_folder = STORAGE_PATH / character
                    storage_char_folder.mkdir(parents=True, exist_ok=True)
                    (storage_char_folder / f"{skin_id}_csp.png").write_bytes(csp_data)

                # Handle stock - copy if found, use vanilla if missing
                stock_data = None
                stock_source = 'imported'
                if char_info['stock_file']:
                    # Stock found in ZIP (using improved matching from character detector)
                    stock_data = source_zip.read(char_info['stock_file'])
                else:
                    # No stock in ZIP - try vanilla matching costume
                    vanilla_stock_path = VANILLA_ASSETS_DIR / character / char_info['costume_code'] / "stock.png"
                    if vanilla_stock_path.exists():
                        with open(vanilla_stock_path, 'rb') as f:
                            stock_data = f.read()
                        stock_source = 'vanilla'

                # Ice Climbers: Nana should copy stock from Popo
                if char_info.get('is_nana') and not stock_data:
                    # Look for paired Popo in metadata
                    popo_color = char_info.get('pair_color')
                    if popo_color:
                        popo_id = f"{character.lower().replace(' ', '-')}-{popo_color.lower()}"

                        # Check if Popo already imported
                        if character in metadata.get('characters', {}):
                            for skin in metadata['characters'][character]['skins']:
                                if skin['id'] == popo_id:
                                    # Found Popo - copy its stock
                                    popo_stock_path = STORAGE_PATH / character / f"{popo_id}_stc.png"
                                    if popo_stock_path.exists():
                                        stock_data = popo_stock_path.read_bytes()
                                        stock_source = 'copied_from_popo'
                                        logger.info(f"Copied stock from Popo: {popo_id}")
                                    break

                # Save stock if we have one
                if stock_data:
                    dest_zip.writestr('stc.png', stock_data)
                    storage_char_folder = STORAGE_PATH / character
                    (storage_char_folder / f"{skin_id}_stc.png").write_bytes(stock_data)

        # Update metadata
        if character not in metadata['characters']:
            metadata['characters'][character] = {'skins': []}

        # Determine display name: use custom_name if provided, otherwise use DAT filename
        display_name = custom_name if custom_name else dat_name_clean
        logger.info(f"[DEBUG] Final display_name: '{display_name}' (custom_name: '{custom_name}', dat_name_clean: '{dat_name_clean}')")

        # Build skin entry
        skin_entry = {
            'id': skin_id,
            'color': display_name,  # Display name shown in UI
            'costume_code': char_info['costume_code'],
            'filename': f"{skin_id}.zip",
            'has_csp': csp_data is not None,
            'has_stock': stock_data is not None,
            'csp_source': csp_source,
            'stock_source': stock_source if stock_data else None,
            'date_added': datetime.now().isoformat(),
            # DAT hash for duplicate detection
            'dat_hash': dat_hash,
            # Slippi safety metadata
            'slippi_safe': slippi_validation['slippi_safe'] if slippi_validation else False,
            'slippi_tested': True,
            'slippi_test_date': datetime.now().isoformat(),
            'slippi_manual_override': None
        }

        # Ice Climbers pairing metadata
        # Note: paired_nana_id/paired_popo_id will be set by fix_ice_climbers_pairing()
        # after both costumes are imported, using actual skin IDs
        if char_info.get('is_popo'):
            skin_entry['is_popo'] = True
            skin_entry['visible'] = True
            # Placeholder - will be updated with actual Nana ID after import
            skin_entry['paired_nana_id'] = None

        elif char_info.get('is_nana'):
            skin_entry['is_nana'] = True
            skin_entry['visible'] = False  # Hidden in UI
            # Placeholder - will be updated with actual Popo ID after import
            skin_entry['paired_popo_id'] = None

        metadata['characters'][character]['skins'].append(skin_entry)

        # Save metadata
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Saved character costume: {final_zip}")

        return {
            'success': True,
            'type': 'character',
            'character': character,
            'color': dat_name_clean,  # Use descriptive name
            'skin_id': skin_id,  # Return the actual skin ID for pairing
            'message': f"Imported {character} - {dat_name_clean} costume"
        }

    except Exception as e:
        logger.error(f"Character import error: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def import_stage_mod(zip_path: str, stage_info: dict, original_filename: str, custom_name: str = None) -> dict:
    """Import a stage mod to storage"""
    try:
        # Load metadata
        metadata_file = STORAGE_PATH / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {'characters': {}, 'stages': {}}

        # Ensure 'stages' section exists
        if 'stages' not in metadata:
            metadata['stages'] = {}

        stage_folder_name = stage_info['folder']
        stage_name = stage_info['stage_name']

        # Create stage folder in storage/das/
        das_folder = STORAGE_PATH / 'das' / stage_folder_name
        das_folder.mkdir(parents=True, exist_ok=True)

        # Generate unique ID for this variant
        stage_data = metadata.get('stages', {}).get(stage_folder_name, {'variants': []})
        existing_ids = [v['id'] for v in stage_data.get('variants', [])]

        # Generate sequential ID based on custom_name or original filename
        if custom_name:
            # Sanitize and limit stage names to 10 characters to prevent crashes
            base_name = sanitize_filename(custom_name)[:10].lower().replace(' ', '-')
        else:
            base_name = sanitize_filename(Path(original_filename).stem)[:10].lower().replace(' ', '-')

        variant_id = base_name
        counter = 1
        while variant_id in existing_ids:
            variant_id = f"{base_name}-{counter:03d}"
            counter += 1

        # Final paths
        final_zip = das_folder / f"{variant_id}.zip"

        # Create a new ZIP with only this stage's files
        with zipfile.ZipFile(zip_path, 'r') as source_zf:
            with zipfile.ZipFile(final_zip, 'w', zipfile.ZIP_DEFLATED) as dest_zf:
                # Add the specific stage DAT file
                stage_file_data = source_zf.read(stage_info['stage_file'])
                stage_file_basename = os.path.basename(stage_info['stage_file'])
                dest_zf.writestr(stage_file_basename, stage_file_data)
                logger.info(f"[OK] Added stage file to ZIP: {stage_file_basename}")

                # Add screenshot to ZIP if available
                if stage_info['screenshot']:
                    screenshot_data = source_zf.read(stage_info['screenshot'])
                    screenshot_basename = os.path.basename(stage_info['screenshot'])
                    dest_zf.writestr(screenshot_basename, screenshot_data)
                    logger.info(f"[OK] Added screenshot to ZIP: {screenshot_basename}")

        # Extract screenshot to storage folder for preview
        has_screenshot = False
        if stage_info['screenshot']:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                screenshot_data = zf.read(stage_info['screenshot'])
                screenshot_ext = os.path.splitext(stage_info['screenshot'])[1]

                # Save to storage folder
                screenshot_path = das_folder / f"{variant_id}_screenshot{screenshot_ext}"
                screenshot_path.write_bytes(screenshot_data)

                has_screenshot = True
                logger.info(f"[OK] Saved screenshot preview: {screenshot_path}")

        # Update metadata
        if stage_folder_name not in metadata['stages']:
            metadata['stages'][stage_folder_name] = {'variants': []}

        # Use variant_id as display name (it's already limited to 10 chars and uses custom_name if provided)
        display_name = variant_id

        metadata['stages'][stage_folder_name]['variants'].append({
            'id': variant_id,
            'name': display_name,
            'filename': f"{variant_id}.zip",
            'has_screenshot': has_screenshot,
            'date_added': datetime.now().isoformat()
            # No default slippi status - will show as "Unknown" until manually set
        })

        # Save metadata
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Saved stage mod: {final_zip}")

        return {
            'success': True,
            'type': 'stage',
            'stage': stage_name,
            'variant_id': variant_id,
            'message': f"Imported {stage_name} stage variant"
        }

    except Exception as e:
        logger.error(f"Stage import error: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


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

        # Check if file is a supported archive type
        is_zip = file.filename.lower().endswith('.zip')
        is_7z = file.filename.lower().endswith('.7z')

        if not (is_zip or is_7z):
            return jsonify({
                'success': False,
                'error': 'Only ZIP and 7z files are supported'
            }), 400

        # Get slippi_action parameter (can be "fix", "import_as_is", or None)
        slippi_action = request.form.get('slippi_action')

        # Get duplicate_action parameter (can be "import_anyway" or None)
        duplicate_action = request.form.get('duplicate_action')

        # Get custom_title parameter if provided (for nucleus:// imports)
        custom_title = request.form.get('custom_title')
        logger.info(f"[DEBUG] custom_title from form: '{custom_title}' (type: {type(custom_title).__name__})")

        # Save uploaded file to temp location with correct suffix
        suffix = '.zip' if is_zip else '.7z'
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            file.save(tmp.name)
            temp_zip_path = tmp.name

        try:
            logger.info(f"=== UNIFIED IMPORT: {file.filename} ===")

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
                    metadata_file = STORAGE_PATH / 'metadata.json'
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                    else:
                        metadata = {'characters': {}, 'stages': {}}

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
                    with open(metadata_file, 'w') as f:
                        json.dump(metadata, f, indent=2)

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
                for character_info in character_infos_sorted:
                    logger.info(f"  - Importing {character_info['character']} - {character_info['color']}")
                    logger.info(f"[DEBUG] Calling import_character_costume with custom_name='{custom_title}'")
                    result = import_character_costume(temp_zip_path, character_info, file.filename, auto_fix=auto_fix, custom_name=custom_title)
                    if result.get('success'):
                        results.append({
                            'character': character_info['character'],
                            'color': character_info['color']
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
                    'imported_count': len(results),
                    'costumes': results,
                    'message': f"Imported {len(results)} costume(s)"
                })

            # PHASE 2: Try stage detection
            logger.info("Phase 2: Attempting stage detection...")
            stage_infos = detect_stage_from_zip(temp_zip_path)

            if stage_infos:
                logger.info(f"[OK] Detected {len(stage_infos)} stage mod(s)")

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

            # PHASE 3: Detection failed
            logger.warning("Could not detect type - not a character costume or stage mod")
            return jsonify({
                'success': False,
                'error': 'Could not detect mod type. Make sure the ZIP contains a valid character costume (.dat with Ply symbols) or stage file (GrXx.dat/.usd)'
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
