"""
Character costume import - vault storage, CSP/stock handling, Ice Climbers
pairing.
"""

import os
import re
import zipfile
import tempfile
import logging
from datetime import datetime

from core.config import STORAGE_PATH, VANILLA_ASSETS_DIR
from core.costume_files import get_costume_archive_extension
from core.metadata import load_metadata, save_metadata
from dat_processor import validate_for_slippi
from generate_csp import generate_csp

from .helpers import compute_dat_hash, extract_custom_name_from_filename

logger = logging.getLogger(__name__)


def fix_ice_climbers_pairing(character_infos: list, imported_skin_ids: dict):
    """
    Fix Ice Climbers pairing after import using actual skin IDs.

    Args:
        character_infos: List of character info dicts with pairing metadata
        imported_skin_ids: Dict mapping costume_code -> actual skin_id created
    """
    try:
        # Load metadata
        metadata = load_metadata()
        if metadata is None:
            return

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
            save_metadata(metadata)
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
        metadata = load_metadata(default={'characters': {}, 'stages': {}})

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
        archive_ext = get_costume_archive_extension(char_info['dat_file'])

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
                logger.info(f"Slippi validation: slippi_safe={slippi_validation['slippi_safe']}, auto_fix={auto_fix}, output={slippi_validation.get('output', '')[:200]}")

                # If auto_fix was applied, read the fixed DAT
                if auto_fix and slippi_validation.get('fix_applied'):
                    with open(tmp_dat_path, 'rb') as f:
                        dat_data = f.read()
                    logger.info("Using slippi-fixed DAT file")
            finally:
                os.unlink(tmp_dat_path)

        with zipfile.ZipFile(zip_path, 'r') as source_zip:
            with zipfile.ZipFile(final_zip, 'w') as dest_zip:
                # Copy the costume archive (potentially fixed version), preserving .usd when present.
                dest_zip.writestr(f"{char_info['costume_code']}Mod{archive_ext}", dat_data)

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
                    if char_info.get('is_popo') and char_info.get('pair_dat_file'):
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
                    else:
                        # Custom MEX color slots (e.g. PlPpBr) have no matching
                        # vanilla folder, so fall back to the character's default
                        # color (Nr) stock. Better an arbitrary but on-brand icon
                        # than no icon — empty stock is the most reported "import
                        # looks broken" symptom.
                        costume_code = char_info.get('costume_code') or ''
                        if len(costume_code) >= 4:
                            default_costume_code = costume_code[:4] + 'Nr'
                            default_stock_path = VANILLA_ASSETS_DIR / character / default_costume_code / "stock.png"
                            if default_stock_path.exists():
                                with open(default_stock_path, 'rb') as f:
                                    stock_data = f.read()
                                stock_source = 'vanilla_default'
                                logger.info(
                                    f"No stock found for {costume_code}, falling back to "
                                    f"vanilla default {default_costume_code}/stock.png"
                                )

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
        save_metadata(metadata)

        logger.info(f"[OK] Saved character costume: {final_zip}")

        return {
            'success': True,
            'type': 'character',
            'character': character,
            'color': dat_name_clean,  # Use descriptive name
            'skin_id': skin_id,  # Return the actual skin ID for pairing
            'csp_source': csp_source,
            'camera_sound': csp_source == 'generated',
            'message': f"Imported {character} - {dat_name_clean} costume"
        }

    except Exception as e:
        logger.error(f"Character import error: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
