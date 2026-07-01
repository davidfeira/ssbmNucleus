"""
Color extras - character effect color modifications (lasers, side-B, shine, etc.).

The /api/mex/storage/extras/* routes plus apply_extras_patches() used at export time.
"""

import json
import uuid
import logging
import shutil
from datetime import datetime
from flask import request, jsonify

from core.metadata import load_metadata, save_metadata
from extra_types import get_extra_types, get_extra_type, has_extras, get_storage_character

from . import extras_bp
from . import helpers
from .helpers import (
    find_dat_file,
    get_dynamic_offsets,
    patch_matrix_colors,
    read_shine_gradient_colors,
    read_current_colors,
    apply_hex_patches,
)
from .textures import ensure_vanilla_texture, shift_texture_hue, import_texture

logger = logging.getLogger(__name__)


def apply_extras_patches(project_path):
    """Apply all selected extras to character .dat files before ISO export.

    Args:
        project_path: Path to MEX project directory

    Returns:
        Dict with patching results
    """
    results = {
        'patched': [],
        'skipped': [],
        'errors': []
    }

    # Load metadata (via the core.metadata DAL)
    metadata = load_metadata()
    if not metadata:
        logger.info("No vault metadata found, skipping extras patching")
        return results

    # Get MEX build files directory
    files_dir = project_path / "build" / "files"
    if not files_dir.exists():
        logger.warning(f"Build files directory not found: {files_dir}")
        results['errors'].append(f"Build files directory not found: {files_dir}")
        return results

    # Iterate through all characters with extras
    for character, char_data in metadata.get('characters', {}).items():
        extras = char_data.get('extras', {})
        if not extras:
            continue

        # Get extra type configs for this character
        char_extra_types = get_extra_types(character)
        if not char_extra_types:
            continue

        for extra_type_config in char_extra_types:
            type_id = extra_type_config['id']
            target_file = extra_type_config['target_file']
            fallback_offsets = extra_type_config['offsets']

            # Get mods for this type
            mods = extras.get(type_id, [])
            if not mods:
                continue

            # Find the active mod (one with active: True)
            active_mod = None
            for mod in mods:
                if mod.get('active'):
                    active_mod = mod
                    break

            # Skip if no active mod (vanilla)
            if not active_mod:
                logger.debug(f"No active {type_id} mod for {character}, using vanilla")
                continue

            modifications = active_mod.get('modifications', {})

            if not modifications:
                logger.debug(f"No modifications in {type_id} mod for {character}, skipping")
                results['skipped'].append(f"{character}/{type_id}: no modifications")
                continue

            # Find the target .dat file in build/files
            dat_path = find_dat_file(files_dir, target_file)
            if not dat_path or not dat_path.exists():
                logger.warning(f"Could not find {target_file} for {character}")
                results['skipped'].append(f"{character}/{type_id}: {target_file} not found")
                continue

            # Use dynamic offset detection for laser/sideb, fallback to hardcoded
            offsets = get_dynamic_offsets(dat_path, type_id, fallback_offsets)

            try:
                # Special handling for shine_gradient format (two-color gradient + optional flash)
                if extra_type_config.get('format') == 'shine_gradient':
                    hex_offset = offsets.get('hex', {})

                    # Read CURRENT colors from the file (might be vanilla or from a previous build)
                    current_colors = read_shine_gradient_colors(dat_path, hex_offset)
                    current_primary = current_colors.get('primary', '621F')
                    current_secondary = current_colors.get('secondary', 'AB9F')

                    # Get new colors from modifications
                    vanilla = extra_type_config.get('vanilla', {})
                    new_primary = modifications.get('primary', {}).get('color', vanilla.get('primary', '621F'))
                    new_secondary = modifications.get('secondary', {}).get('color', vanilla.get('secondary', 'AB9F'))

                    # Build color_map from current to new (works whether file is vanilla or modified)
                    color_map = {
                        current_primary: new_primary,
                        current_secondary: new_secondary
                    }

                    # Patch the hex region with the color_map
                    start = hex_offset.get('start', 0)
                    end = hex_offset.get('end', start)

                    with open(dat_path, 'r+b') as f:
                        f.seek(start)
                        data = f.read(end - start)
                        modified = patch_matrix_colors(data, color_format='RGBY', color_map=color_map)
                        f.seek(start)
                        f.write(modified)

                    # Patch flash colors if provided (startup glow effect - two colors)
                    flash1_mod = modifications.get('flash1', {}).get('color')
                    flash2_mod = modifications.get('flash2', {}).get('color')

                    if flash1_mod or flash2_mod:
                        vanilla_flash1 = vanilla.get('flash1', '63FF')
                        vanilla_flash2 = vanilla.get('flash2', 'FFFF')
                        flash_offsets = extra_type_config.get('flash_offsets', {})
                        flash_ranges = flash_offsets.get('ranges', [])

                        # Build flash color map
                        flash_map = {}
                        if flash1_mod:
                            flash_map[vanilla_flash1] = flash1_mod
                        if flash2_mod:
                            flash_map[vanilla_flash2] = flash2_mod

                        if flash_map and flash_ranges:
                            with open(dat_path, 'r+b') as f:
                                for range_info in flash_ranges:
                                    range_start = range_info['start']
                                    range_end = range_info['end']
                                    f.seek(range_start)
                                    data = f.read(range_end - range_start)
                                    modified = patch_matrix_colors(data, color_format='RGBY', color_map=flash_map)
                                    f.seek(range_start)
                                    f.write(modified)

                            logger.info(f"[OK] Applied shine flash colors: {flash_map}")

                    logger.info(f"[OK] Applied shine gradient to {character}: {current_primary}->{new_primary}, {current_secondary}->{new_secondary}")
                    results['patched'].append(f"{character}/{type_id}")
                    continue

                # Apply hex patches (standard format)
                apply_hex_patches(dat_path, offsets, modifications)
                logger.info(f"[OK] Applied {type_id} extras to {character} ({target_file})")
                results['patched'].append(f"{character}/{type_id}")
            except Exception as e:
                logger.error(f"Failed to patch {character}/{type_id}: {e}", exc_info=True)
                results['errors'].append(f"{character}/{type_id}: {e}")

    return results


# =============================================================================
# API ROUTES
# =============================================================================

@extras_bp.route('/api/mex/storage/extras/list/<character>', methods=['GET'])
def list_extras(character):
    """List all extras for a character from metadata.json.

    For shared extras, retrieves mods from the owner character's storage.
    """
    try:
        # Check if character has extras defined
        if not has_extras(character):
            return jsonify({
                'success': True,
                'extras': {},
                'message': f'No extras defined for {character}'
            })

        # Load metadata (via the core.metadata DAL)
        metadata = load_metadata()
        if not metadata:
            return jsonify({
                'success': True,
                'extras': {}
            })

        # Build extras dict, pulling shared extras from owner characters
        extras = {}
        char_extra_types = get_extra_types(character)

        for extra_type in char_extra_types:
            type_id = extra_type['id']
            # Get the storage character (owner for shared extras)
            storage_char = get_storage_character(character, type_id)

            # Get mods from the appropriate character's storage
            char_data = metadata.get('characters', {}).get(storage_char, {})
            type_mods = char_data.get('extras', {}).get(type_id, [])

            if type_mods:
                extras[type_id] = type_mods

        return jsonify({
            'success': True,
            'extras': extras
        })

    except Exception as e:
        logger.error(f"List extras error for {character}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@extras_bp.route('/api/mex/storage/extras/current/<character>/<extra_type>', methods=['GET'])
def get_current_extra(character, extra_type):
    """Read current colors from the .dat file in MEX project.

    Returns the actual colors currently in the build.
    """
    try:
        # Get extra type config
        type_config = get_extra_type(character, extra_type)
        if not type_config:
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" not defined for {character}'
            }), 400

        # Find the .dat file in MEX project
        try:
            files_dir = helpers.get_project_files_dir()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        target_file = type_config['target_file']
        fallback_offsets = type_config['offsets']
        vanilla = type_config.get('vanilla', {})
        dat_path = find_dat_file(files_dir, target_file)

        if not dat_path or not dat_path.exists():
            return jsonify({
                'success': False,
                'error': f'Could not find {target_file} in MEX project'
            }), 404

        # Use dynamic offset detection for laser/sideb, fallback to hardcoded
        offsets = get_dynamic_offsets(dat_path, extra_type, fallback_offsets)

        # Special handling for shine_gradient format (two-color gradient)
        if type_config.get('format') == 'shine_gradient':
            hex_offset = offsets.get('hex', {})
            current_colors = read_shine_gradient_colors(dat_path, hex_offset)

            # Check if current colors match vanilla
            is_vanilla = (
                current_colors.get('primary', '').upper() == vanilla.get('primary', '').upper() and
                current_colors.get('secondary', '').upper() == vanilla.get('secondary', '').upper()
            )

            return jsonify({
                'success': True,
                'colors': current_colors,
                'isVanilla': is_vanilla,
                'vanilla': vanilla
            })

        # Read current colors from the .dat file
        current_colors = read_current_colors(dat_path, offsets)

        # Check if current colors match vanilla
        is_vanilla = all(
            current_colors.get(layer, '').upper() == vanilla.get(layer, '').upper()
            for layer in vanilla.keys()
        )

        return jsonify({
            'success': True,
            'colors': current_colors,
            'isVanilla': is_vanilla,
            'vanilla': vanilla
        })

    except Exception as e:
        logger.error(f"Get current extra error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@extras_bp.route('/api/mex/storage/extras/create', methods=['POST'])
def create_extra():
    """Create a new extra mod from color picker values.

    For shared extras, stores under the owner character.

    Request body:
    {
        "character": "Falco",
        "extraType": "laser",
        "name": "Red Laser",
        "modifications": {
            "wide": { "color": "FC00" },
            "thin": { "color": "FC00" },
            "outline": { "color": "FC00" }
        }
    }
    """
    try:
        data = request.json
        character = data.get('character')
        extra_type = data.get('extraType')
        name = data.get('name', 'New Extra')
        modifications = data.get('modifications', {})

        if not character or not extra_type:
            return jsonify({
                'success': False,
                'error': 'Missing character or extraType parameter'
            }), 400

        # Verify this extra type exists for the character
        type_config = get_extra_type(character, extra_type)
        if not type_config:
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" not defined for {character}'
            }), 400

        # Get the storage character (owner for shared extras)
        storage_char = get_storage_character(character, extra_type)

        # Load metadata (via the core.metadata DAL)
        metadata = load_metadata(default={'characters': {}})

        # Ensure storage character exists in metadata
        if storage_char not in metadata.get('characters', {}):
            metadata['characters'][storage_char] = {'skins': [], 'extras': {}}

        char_data = metadata['characters'][storage_char]

        # Ensure extras structure exists
        if 'extras' not in char_data:
            char_data['extras'] = {}

        if extra_type not in char_data['extras']:
            char_data['extras'][extra_type] = []

        # Generate unique ID
        mod_id = f"{extra_type}_{uuid.uuid4().hex[:8]}"

        # Create new mod entry
        new_mod = {
            'id': mod_id,
            'name': name,
            'date_added': datetime.now().isoformat(),
            'source': 'created',
            'modifications': modifications
        }

        # Add to list
        char_data['extras'][extra_type].append(new_mod)

        # Save metadata (atomic, via the DAL)
        save_metadata(metadata)

        logger.info(f"[OK] Created extra mod '{name}' ({extra_type}) for {storage_char}" +
                   (f" (shared from {character})" if storage_char != character else ""))

        return jsonify({
            'success': True,
            'mod': new_mod
        })

    except Exception as e:
        logger.error(f"Create extra error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@extras_bp.route('/api/mex/storage/extras/delete', methods=['POST'])
def delete_extra():
    """Delete an extra mod.

    For shared extras, deletes from the owner character's storage.

    Request body:
    {
        "character": "Falco",
        "extraType": "laser",
        "modId": "laser_abc12345"
    }
    """
    try:
        data = request.json
        character = data.get('character')
        extra_type = data.get('extraType')
        mod_id = data.get('modId')

        if not character or not extra_type or not mod_id:
            return jsonify({
                'success': False,
                'error': 'Missing character, extraType, or modId parameter'
            }), 400

        # Get the storage character (owner for shared extras)
        storage_char = get_storage_character(character, extra_type)

        # Load metadata (via the core.metadata DAL)
        metadata = load_metadata()
        if metadata is None:
            return jsonify({
                'success': False,
                'error': 'Metadata file not found'
            }), 404

        # Get storage character extras
        char_data = metadata.get('characters', {}).get(storage_char, {})
        extras = char_data.get('extras', {})
        mods = extras.get(extra_type, [])

        # Find and remove the mod
        original_count = len(mods)
        mods = [m for m in mods if m.get('id') != mod_id]

        if len(mods) == original_count:
            return jsonify({
                'success': False,
                'error': f'Mod {mod_id} not found'
            }), 404

        # Update metadata
        extras[extra_type] = mods

        # Save metadata (atomic, via the DAL)
        save_metadata(metadata)

        logger.info(f"[OK] Deleted extra mod {mod_id} ({extra_type}) from {storage_char}")

        return jsonify({
            'success': True
        })

    except Exception as e:
        logger.error(f"Delete extra error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@extras_bp.route('/api/mex/storage/extras/install', methods=['POST'])
def install_extra():
    """Install an extra mod by patching the .dat file.

    For shared extras, retrieves mod from owner character's storage.

    Request body:
    {
        "character": "Falco",
        "extraType": "laser",
        "modId": "laser_abc123"
    }
    """
    try:
        data = request.json
        character = data.get('character')
        extra_type = data.get('extraType')
        mod_id = data.get('modId')

        if not character or not extra_type or not mod_id:
            return jsonify({
                'success': False,
                'error': 'Missing character, extraType, or modId parameter'
            }), 400

        # Get extra type config
        type_config = get_extra_type(character, extra_type)
        if not type_config:
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" not defined for {character}'
            }), 400

        # Get the storage character (owner for shared extras)
        storage_char = get_storage_character(character, extra_type)

        # Find the .dat file in MEX project
        try:
            files_dir = helpers.get_project_files_dir()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        target_file = type_config['target_file']
        fallback_offsets = type_config['offsets']
        dat_path = find_dat_file(files_dir, target_file)

        if not dat_path or not dat_path.exists():
            return jsonify({
                'success': False,
                'error': f'Could not find {target_file} in MEX project'
            }), 404

        # Use dynamic offset detection for laser/sideb, fallback to hardcoded
        offsets = get_dynamic_offsets(dat_path, extra_type, fallback_offsets)

        # Load metadata to find the mod (via the core.metadata DAL)
        metadata = load_metadata()
        if metadata is None:
            return jsonify({
                'success': False,
                'error': 'Metadata file not found'
            }), 404

        # Find the mod (from storage character)
        char_data = metadata.get('characters', {}).get(storage_char, {})
        extras = char_data.get('extras', {})
        mods = extras.get(extra_type, [])

        found_mod = None
        for mod in mods:
            if mod.get('id') == mod_id:
                found_mod = mod
                break

        if not found_mod:
            return jsonify({
                'success': False,
                'error': f'Mod {mod_id} not found'
            }), 404

        # Apply the patch
        modifications = found_mod.get('modifications', {})
        logger.info(f"[Install] {extra_type} for {character}: offsets={offsets}, modifications={modifications}")
        if modifications:
            # Special handling for shine_gradient format (two-color gradient + optional flash)
            if type_config.get('format') == 'shine_gradient':
                hex_offset = offsets.get('hex', {})

                # Read CURRENT colors from the file (might be vanilla or from another mod)
                current_colors = read_shine_gradient_colors(dat_path, hex_offset)
                current_primary = current_colors.get('primary', '621F')
                current_secondary = current_colors.get('secondary', 'AB9F')

                # Get new colors from modifications
                vanilla = type_config.get('vanilla', {})
                new_primary = modifications.get('primary', {}).get('color', vanilla.get('primary', '621F'))
                new_secondary = modifications.get('secondary', {}).get('color', vanilla.get('secondary', 'AB9F'))

                # Build color_map from current to new (works whether file is vanilla or modified)
                color_map = {
                    current_primary: new_primary,
                    current_secondary: new_secondary
                }

                # Patch the hex region with the color_map
                start = hex_offset.get('start', 0)
                end = hex_offset.get('end', start)

                with open(dat_path, 'r+b') as f:
                    f.seek(start)
                    data = f.read(end - start)
                    modified = patch_matrix_colors(data, color_format='RGBY', color_map=color_map)
                    f.seek(start)
                    f.write(modified)

                # Patch flash colors if provided (startup glow effect - two colors)
                flash1_mod = modifications.get('flash1', {}).get('color')
                flash2_mod = modifications.get('flash2', {}).get('color')

                if flash1_mod or flash2_mod:
                    vanilla_flash1 = vanilla.get('flash1', '63FF')
                    vanilla_flash2 = vanilla.get('flash2', 'FFFF')
                    flash_offsets = type_config.get('flash_offsets', {})
                    flash_ranges = flash_offsets.get('ranges', [])

                    # Build flash color map
                    flash_map = {}
                    if flash1_mod:
                        flash_map[vanilla_flash1] = flash1_mod
                    if flash2_mod:
                        flash_map[vanilla_flash2] = flash2_mod

                    if flash_map and flash_ranges:
                        with open(dat_path, 'r+b') as f:
                            for range_info in flash_ranges:
                                range_start = range_info['start']
                                range_end = range_info['end']
                                f.seek(range_start)
                                data = f.read(range_end - range_start)
                                modified = patch_matrix_colors(data, color_format='RGBY', color_map=flash_map)
                                f.seek(range_start)
                                f.write(modified)

                        logger.info(f"[OK] Installed shine flash colors: {flash_map}")

                logger.info(f"[OK] Installed shine gradient {found_mod['name']}: {current_primary}->{new_primary}, {current_secondary}->{new_secondary}")
            else:
                apply_hex_patches(dat_path, offsets, modifications)
                logger.info(f"[OK] Installed {found_mod['name']} to {target_file} at {dat_path}")

            # Handle fire texture hue if present (for upb extra)
            if 'fire' in modifications and 'hue' in modifications['fire']:
                fire_hue = modifications['fire']['hue']
                logger.info(f"[Install] Applying fire texture hue: {fire_hue}")
                try:
                    # Get texture config for upb_texture
                    texture_config = get_extra_type(character, 'upb_texture')
                    if texture_config:
                        # Ensure vanilla texture exists
                        vanilla_png = ensure_vanilla_texture(character, 'upb_texture', texture_config)
                        if vanilla_png:
                            # Calculate hue shift from vanilla
                            vanilla_hue = texture_config.get('vanilla_hue', 15)
                            hue_shift = fire_hue - vanilla_hue

                            # Apply hue shift
                            textures_dir = helpers.STORAGE_PATH / storage_char / 'textures'
                            textures_dir.mkdir(parents=True, exist_ok=True)
                            hue_shifted_png = textures_dir / f"upb_texture_hue_{int(fire_hue)}.png"

                            if abs(hue_shift) >= 1:
                                shift_texture_hue(str(vanilla_png), str(hue_shifted_png), hue_shift)
                            else:
                                hue_shifted_png = vanilla_png

                            # Import into DAT
                            node_path = texture_config['texture_path']
                            tex_index = texture_config['texture_index']
                            temp_dat = dat_path.parent / f"{dat_path.stem}_temp{dat_path.suffix}"

                            import_texture(dat_path, node_path, tex_index, hue_shifted_png, temp_dat)
                            shutil.move(str(temp_dat), str(dat_path))
                            logger.info(f"[OK] Applied fire texture hue {fire_hue} to {target_file}")
                except Exception as tex_err:
                    logger.error(f"[Install] Fire texture hue failed: {tex_err}")
                    # Don't fail the whole install, just log the error
        else:
            logger.warning(f"[Install] No modifications found in mod {mod_id}")

        return jsonify({
            'success': True
        })

    except Exception as e:
        logger.error(f"Install extra error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@extras_bp.route('/api/mex/storage/extras/restore-vanilla', methods=['POST'])
def restore_vanilla_extra():
    """Restore vanilla colors from config.

    Request body:
    {
        "character": "Falco",
        "extraType": "laser"
    }
    """
    try:
        data = request.json
        character = data.get('character')
        extra_type = data.get('extraType')

        if not character or not extra_type:
            return jsonify({
                'success': False,
                'error': 'Missing character or extraType parameter'
            }), 400

        # Get extra type config
        type_config = get_extra_type(character, extra_type)
        if not type_config:
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" not defined for {character}'
            }), 400

        vanilla = type_config.get('vanilla', {})
        if not vanilla:
            return jsonify({
                'success': False,
                'error': f'No vanilla colors defined for {character}/{extra_type}'
            }), 400

        # Find the .dat file in MEX project
        try:
            files_dir = helpers.get_project_files_dir()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        target_file = type_config['target_file']
        fallback_offsets = type_config['offsets']
        dat_path = find_dat_file(files_dir, target_file)

        if not dat_path or not dat_path.exists():
            return jsonify({
                'success': False,
                'error': f'Could not find {target_file} in MEX project'
            }), 404

        # Use dynamic offset detection for laser/sideb, fallback to hardcoded
        offsets = get_dynamic_offsets(dat_path, extra_type, fallback_offsets)

        # Special handling for shine_gradient format (two-color gradient + flash)
        if type_config.get('format') == 'shine_gradient':
            # Read current colors to build the restoration map
            hex_offset = offsets.get('hex', {})
            current_colors = read_shine_gradient_colors(dat_path, hex_offset)

            # Build color_map to restore vanilla colors
            color_map = {
                current_colors['primary']: vanilla['primary'],
                current_colors['secondary']: vanilla['secondary']
            }

            # Patch back to vanilla
            start = hex_offset.get('start', 0)
            end = hex_offset.get('end', start)

            with open(dat_path, 'r+b') as f:
                f.seek(start)
                data = f.read(end - start)
                modified = patch_matrix_colors(data, color_format='RGBY', color_map=color_map)
                f.seek(start)
                f.write(modified)

            # Also restore flash colors to vanilla (two-color: 63FF and FFFF)
            vanilla_flash1 = vanilla.get('flash1', '63FF')
            vanilla_flash2 = vanilla.get('flash2', 'FFFF')
            flash_offsets = type_config.get('flash_offsets', {})
            flash_ranges = flash_offsets.get('ranges', [])

            if flash_ranges:
                with open(dat_path, 'r+b') as f:
                    for range_info in flash_ranges:
                        range_start = range_info['start']
                        range_end = range_info['end']
                        f.seek(range_start)
                        data = f.read(range_end - range_start)
                        # Find all non-vanilla colors and map them back
                        colors_in_range = {}
                        pos = 4
                        while pos + 1 < len(data):
                            c = data[pos:pos+2].hex().upper()
                            # Map any non-vanilla color to closest vanilla
                            if c != vanilla_flash1 and c != vanilla_flash2:
                                # Heuristic: if it's bright (FFFF-ish), map to flash2, else flash1
                                colors_in_range[c] = vanilla_flash1
                            pos += 4
                        if colors_in_range:
                            modified = patch_matrix_colors(data, color_format='RGBY', color_map=colors_in_range)
                            f.seek(range_start)
                            f.write(modified)

            logger.info(f"[OK] Restored vanilla shine gradient for {character}")
        else:
            # Apply vanilla colors (standard format)
            vanilla_mods = {layer: {'color': color} for layer, color in vanilla.items()}
            apply_hex_patches(dat_path, offsets, vanilla_mods)
            logger.info(f"[OK] Restored vanilla colors for {character}/{extra_type}")

        # Also restore fire texture for upb extra
        if extra_type == 'upb':
            try:
                texture_config = get_extra_type(character, 'upb_texture')
                if texture_config:
                    vanilla_png = ensure_vanilla_texture(character, 'upb_texture', texture_config)
                    if vanilla_png:
                        node_path = texture_config['texture_path']
                        tex_index = texture_config['texture_index']
                        temp_dat = dat_path.parent / f"{dat_path.stem}_temp{dat_path.suffix}"

                        import_texture(dat_path, node_path, tex_index, vanilla_png, temp_dat)
                        shutil.move(str(temp_dat), str(dat_path))
                        logger.info(f"[OK] Restored vanilla fire texture for {character}")
            except Exception as tex_err:
                logger.error(f"[RestoreVanilla] Fire texture restore failed: {tex_err}")
                # Don't fail, just log

        return jsonify({
            'success': True
        })

    except Exception as e:
        logger.error(f"Restore vanilla error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
