"""
Effect/model mod import - routes website-tagged effect mods through the
extras model system.
"""

import zipfile
import logging
import uuid
from pathlib import Path
from datetime import datetime

from core.config import STORAGE_PATH
from core.metadata import load_metadata, save_metadata
from extra_types import get_extra_type, get_extra_types, get_storage_character
from blueprints.extras import extract_model_from_dat

from .helpers import sanitize_filename, compute_dat_hash

logger = logging.getLogger(__name__)


def _import_effect_mod(zip_path, zip_filename, effect_type, custom_title=None):
    """Import an effect/model mod using website-provided type info.

    Routes through the existing extras model system so the effect
    shows up in the Extras/Effects tab.

    Args:
        zip_path: Path to the uploaded ZIP file
        zip_filename: Original filename of the uploaded ZIP
        effect_type: Effect type ID from website tags (e.g. 'gun', 'laser')
        custom_title: Optional display name

    Returns:
        dict with success/error info, or None if ZIP has no .dat files
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            dat_files = [n for n in zf.namelist()
                         if n.lower().endswith('.dat')
                         and not n.startswith('__MACOSX')]
            image_exts = {'.png', '.jpg', '.jpeg', '.gif'}
            image_files = [n for n in zf.namelist()
                           if Path(n).suffix.lower() in image_exts
                           and not n.startswith('__MACOSX')]

            if not dat_files:
                return None  # No .dat files, let normal detection handle it

            # Use first .dat file
            dat_name = dat_files[0]
            dat_data = zf.read(dat_name)

            # Derive character from ZIP filename (format: "Character_Color.zip")
            # e.g. "Fox_Default.zip" -> "Fox"
            name_stem = Path(zip_filename).stem
            character = name_stem.split('_')[0] if '_' in name_stem else name_stem

            # Normalize effect_type to lowercase (website tags are "Gun", desktop IDs are "gun")
            effect_type = effect_type.lower()
            # Normalize separators (website sends "shadow ball", IDs use "shadow_ball")
            effect_type = effect_type.replace(' ', '_').replace('-', '_')

            # Validate effect type exists for this character
            type_config = get_extra_type(character, effect_type)

            # Fallback: match by name (website often sends the display name, not the ID)
            if not type_config:
                for t in get_extra_types(character):
                    normalized_name = t["name"].lower().replace(' ', '_').replace('-', '_')
                    if normalized_name == effect_type:
                        effect_type = t["id"]
                        type_config = t
                        break

            if not type_config:
                logger.warning(f"Effect type '{effect_type}' not defined for {character}")
                return {
                    'success': False,
                    'error': f'Effect type "{effect_type}" not defined for {character}'
                }

            storage_char = get_storage_character(character, effect_type)
            mod_id = f"{effect_type}_{uuid.uuid4().hex[:8]}"
            effect_name = custom_title or Path(zip_filename).stem
            effect_name = sanitize_filename(effect_name)

            if type_config.get('type') == 'model':
                # Model-type effect (e.g. gun) - extract .dae from .dat
                models_dir = STORAGE_PATH / storage_char / 'models'
                models_dir.mkdir(parents=True, exist_ok=True)

                # Save .dat temporarily for model extraction
                temp_dat = models_dir / f"{mod_id}_temp.dat"
                temp_dat.write_bytes(dat_data)

                try:
                    dae_path = models_dir / f"{mod_id}.dae"
                    jobj_path = type_config.get('model_path')
                    if not jobj_path:
                        return {
                            'success': False,
                            'error': f'Model path not configured for {effect_type}'
                        }

                    extract_model_from_dat(temp_dat, jobj_path, dae_path)
                    logger.info(f"Extracted model from .dat to {dae_path}")
                finally:
                    if temp_dat.exists():
                        temp_dat.unlink()

                model_file = f"models/{mod_id}.dae"
            else:
                # Non-model effect (color patches etc.) - store the .dat directly
                models_dir = STORAGE_PATH / storage_char / 'models'
                models_dir.mkdir(parents=True, exist_ok=True)
                dat_path = models_dir / f"{mod_id}.dat"
                dat_path.write_bytes(dat_data)
                model_file = f"models/{mod_id}.dat"

            # Save screenshot if present
            screenshot_file = None
            if image_files:
                screenshots_dir = STORAGE_PATH / storage_char / 'models'
                screenshots_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = screenshots_dir / f"{mod_id}_preview.png"
                screenshot_path.write_bytes(zf.read(image_files[0]))
                screenshot_file = f"models/{mod_id}_preview.png"

            # Update metadata
            metadata = load_metadata(default={'characters': {}})

            if storage_char not in metadata.get('characters', {}):
                metadata['characters'][storage_char] = {'skins': [], 'extras': {}}

            char_data = metadata['characters'][storage_char]
            if 'extras' not in char_data:
                char_data['extras'] = {}
            if effect_type not in char_data['extras']:
                char_data['extras'][effect_type] = []

            new_mod = {
                'id': mod_id,
                'name': effect_name,
                'type': type_config.get('type', 'model'),
                'date_added': datetime.now().isoformat(),
                'source': 'nucleus',
                'model_file': model_file,
                'file_hash': compute_dat_hash(dat_data)
            }
            if screenshot_file:
                new_mod['screenshot'] = screenshot_file

            char_data['extras'][effect_type].append(new_mod)

            save_metadata(metadata)

            logger.info(f"[OK] Imported effect '{effect_name}' ({effect_type}) for {storage_char}")

            return {
                'success': True,
                'type': 'effect',
                'imported_count': 1,
                'character': storage_char,
                'effect_type': effect_type,
                'message': f"Imported {effect_name} ({effect_type} for {storage_char})"
            }

    except zipfile.BadZipFile:
        return None  # Not a valid zip
    except Exception as e:
        logger.error(f"Effect import error: {e}", exc_info=True)
        return {
            'success': False,
            'error': f'Effect import error: {str(e)}'
        }
