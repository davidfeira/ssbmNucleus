"""
Extras API - Character effect color modifications (lasers, side-B, shine, etc.)
Extracted from mex_api.py for better organization.
"""

import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify

from extra_types import get_extra_types, get_extra_type, has_extras, get_storage_character

logger = logging.getLogger(__name__)

# Blueprint for extras routes
extras_bp = Blueprint('extras', __name__)

# These will be set by init_extras_api()
STORAGE_PATH = None
get_project_files_dir = None


def init_extras_api(storage_path, project_files_dir_func):
    """Initialize the extras API with required dependencies from mex_api."""
    global STORAGE_PATH, get_project_files_dir
    STORAGE_PATH = storage_path
    get_project_files_dir = project_files_dir_func


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def find_dat_file(files_dir, target_file):
    """Find a .dat file in the MEX build files directory.

    Args:
        files_dir: Path to MEX build/files directory
        target_file: Target filename (e.g., 'PlFc.dat')

    Returns:
        Path to the file if found, None otherwise
    """
    # Check common locations
    possible_paths = [
        files_dir / target_file,
        files_dir / "PlCo" / target_file,  # Character data folder
        files_dir / "fighter" / target_file,
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # Search recursively if not found in common locations
    matches = list(files_dir.rglob(target_file))
    return matches[0] if matches else None


def patch_matrix_colors(data, new_color, color_format="RGBY"):
    """Replace colors in 98 matrix format data.

    The 98 matrix format has:
    - Header: 98 00 NN (3 bytes) where NN is index count
    - Then repeating entries, each 4 bytes:
      - 1 byte: vertex index
      - 2 or 3 bytes: color (RGBY or RGB)
      - 1 or 0 bytes: coordinate (if RGBY) or none (if RGB)

    RGBY format (2-byte colors, 4-byte entries):
    98 00 17 22 FC 00 03 23 FC 00 05 21 FC 00 ...
              ^^ ^^^^    ^^ ^^^^    ^^^^
              |  color   |  color   color

    RGB format (3-byte colors, 4-byte entries):
    98 00 12 05 FF FF FF 04 FF FF FF 03 FF FF FF ...
              ^^ ^^^^^^    ^^^^^^    ^^^^^^
              |  color     color     color

    Args:
        data: Bytes data from the offset range
        new_color: 2-byte RGBY or 3-byte RGB color value
        color_format: "RGBY" for 2-byte colors, "RGB" for 3-byte colors

    Returns:
        Patched bytes data
    """
    result = bytearray(data)
    color_len = 3 if color_format == "RGB" else 2

    # Header is 3 bytes (98 00 NN), first entry starts at position 3
    # Each entry: 1 byte vertex + color bytes + remaining bytes = 4 bytes total
    # First color at position 4 (3 header + 1 vertex)
    pos = 4  # First color position
    while pos + color_len - 1 < len(result):
        for i in range(color_len):
            result[pos + i] = new_color[i]
        pos += 4  # Move to next color (4 bytes per entry)

    return bytes(result)


def patch_cf_colors(dat_path, offsets_list, color_bytes):
    """Patch multiple CF format offsets with the same color.

    CF format (5 bytes): CF XX RR GG BB
    - CF is the header byte
    - XX is a flag (00, 08, 18)
    - RR GG BB is the RGB color (3 bytes starting at offset+2)

    Args:
        dat_path: Path to the .dat file
        offsets_list: List of offset integers where CF headers are located
        color_bytes: 3-byte RGB color value
    """
    with open(dat_path, 'r+b') as f:
        for offset in offsets_list:
            # Color starts at offset+2 (after CF XX)
            f.seek(offset + 2)
            f.write(color_bytes)


def patch_070707_colors(dat_path, offsets_list, color_bytes):
    """Patch multiple 070707 format offsets with the same color.

    070707 format (11 bytes): 07 07 07 04 RR GG BB 00 RR GG BB
    - 07 07 07 04 is the marker (4 bytes)
    - First color at offset+4 (3 bytes RGB)
    - 00 separator byte
    - Second color at offset+8 (3 bytes RGB)

    Args:
        dat_path: Path to the .dat file
        offsets_list: List of offset integers (marker positions)
        color_bytes: 3-byte RGB color value
    """
    with open(dat_path, 'r+b') as f:
        for offset in offsets_list:
            # First color at offset+4 (after 07 07 07 04)
            f.seek(offset + 4)
            f.write(color_bytes)
            # Second color at offset+8 (after first color + 00)
            f.seek(offset + 8)
            f.write(color_bytes)


def read_current_colors(dat_path, offsets):
    """Read current colors from a .dat file.

    Args:
        dat_path: Path to the .dat file
        offsets: Dict of layer_id -> {start, end/size, format, ...} offset info

    Returns:
        Dict of layer_id -> color hex string

    Supports multiple formats:
    - Matrix format (has 'end'): Reads from 98 00 ## ## format (offset +4 for header)
    - Direct format (has 'size'): Reads bytes directly at offset (for 42_48 RGBA)
    - CF format (format='CF'): Reads 3-byte RGB at offset+2
    - 070707 format (format='070707'): Reads 3-byte RGB at offset+4
    - Multi format (has 'offsets' list): Reads from first offset in the list
    - 98_multi format (has 'ranges' list): Reads from first range's first color
    - 42_48 format: Reads 12 bytes (3x RGBA) directly
    """
    colors = {}
    with open(dat_path, 'rb') as f:
        for layer_id, offset_info in offsets.items():
            fmt = offset_info.get('format', 'RGBY')

            # Handle multi-offset format (CF or 070707 with list of offsets)
            if 'offsets' in offset_info:
                first_offset = offset_info['offsets'][0]
                if fmt == 'CF':
                    # CF format: color at offset+2
                    f.seek(first_offset + 2)
                    color_bytes = f.read(3)
                elif fmt == '070707':
                    # 070707 format: color at offset+4 (after 07 07 07 04 marker)
                    f.seek(first_offset + 4)
                    color_bytes = f.read(3)
                else:
                    continue
                colors[layer_id] = color_bytes.hex().upper()
                continue

            # Handle 98_multi format (multiple 98 matrix ranges)
            if 'ranges' in offset_info:
                first_range = offset_info['ranges'][0]
                start = first_range['start']
                # Read first color in the matrix (at position 4 from start)
                f.seek(start + 4)
                color_bytes = f.read(2)  # RGBY format
                colors[layer_id] = color_bytes.hex().upper()
                continue

            start = offset_info.get('start', 0)

            if fmt == '42_48':
                # 42_48 format: 3x RGBA colors (12 bytes)
                size = offset_info.get('size', 12)
                f.seek(start)
                color_bytes = f.read(size)
                colors[layer_id] = color_bytes.hex().upper()
            elif 'size' in offset_info:
                # Direct read mode - for RGBA format
                size = offset_info['size']
                f.seek(start)
                color_bytes = f.read(size)
                colors[layer_id] = color_bytes.hex().upper()
            elif fmt == 'CF':
                # CF format: color at offset+2
                f.seek(start + 2)
                color_bytes = f.read(3)
                colors[layer_id] = color_bytes.hex().upper()
            elif fmt == '070707':
                # 070707 format: color at offset+4 (after 07 07 07 04 marker)
                f.seek(start + 4)
                color_bytes = f.read(3)
                colors[layer_id] = color_bytes.hex().upper()
            else:
                # Matrix read mode - for 98 00 ## ## format
                color_format = fmt
                color_len = 3 if color_format == 'RGB' else 2
                # Read first color in the matrix (at position 4 from start)
                # Header is 3 bytes (98 00 NN), then 1 byte vertex, then color bytes
                f.seek(start + 4)
                color_bytes = f.read(color_len)
                colors[layer_id] = color_bytes.hex().upper()
    return colors


def apply_hex_patches(dat_path, offsets, modifications):
    """Apply color patches to a .dat file.

    Args:
        dat_path: Path to the .dat file
        offsets: Dict of layer_id -> {start, end/size, format, offsets} offset info
        modifications: Dict of layer_id -> {color: "FC00" or "FFFFFFFF"} modifications

    Supports multiple formats:
    - Matrix format (has 'end'): Uses patch_matrix_colors for 98 00 ## ## format
    - Direct format (has 'size'): Writes color bytes directly at offset (for 42_48 RGBA)
    - CF format (format='CF'): Writes 3-byte RGB at offset+2, supports 'offsets' list
    - 070707 format (format='070707'): Writes 3-byte RGB at offset+1 and offset+5
    """
    with open(dat_path, 'r+b') as f:
        for layer_id, layer_mods in modifications.items():
            if layer_id not in offsets:
                logger.warning(f"Unknown layer '{layer_id}' in modifications, skipping")
                continue

            offset_info = offsets[layer_id]
            color_format = offset_info.get('format', 'RGBY')  # Default to RGBY for backwards compat
            color_hex = layer_mods.get('color', '')

            # Handle multi-offset formats (CF or 070707 with 'offsets' list)
            if 'offsets' in offset_info:
                offsets_list = offset_info['offsets']
                try:
                    color_bytes = bytes.fromhex(color_hex)
                    if len(color_bytes) != 3:
                        logger.warning(f"Invalid color length for {layer_id}: {color_hex}, expected 3 bytes (RGB)")
                        continue
                except ValueError:
                    logger.warning(f"Invalid hex color for {layer_id}: {color_hex}")
                    continue

                if color_format == 'CF':
                    # CF format: color at each offset+2
                    for offset in offsets_list:
                        f.seek(offset + 2)
                        f.write(color_bytes)
                    logger.debug(f"Patched CF {layer_id} at {len(offsets_list)} offsets with color {color_hex}")
                elif color_format == '070707':
                    # 070707 format: color at offset+4 and offset+8 (after 07 07 07 04 marker)
                    for offset in offsets_list:
                        f.seek(offset + 4)
                        f.write(color_bytes)
                        f.seek(offset + 8)
                        f.write(color_bytes)
                    logger.debug(f"Patched 070707 {layer_id} at {len(offsets_list)} offsets with color {color_hex}")
                continue

            # Handle 98_multi format (multiple 98 matrix ranges with same color)
            if 'ranges' in offset_info:
                ranges_list = offset_info['ranges']
                if not color_hex:
                    color_hex = 'FC00'  # Default RGBY
                try:
                    color_bytes = bytes.fromhex(color_hex)
                    if len(color_bytes) != 2:
                        logger.warning(f"Invalid color length for {layer_id}: {color_hex}, expected 2 bytes (RGBY)")
                        continue
                except ValueError:
                    logger.warning(f"Invalid hex color for {layer_id}: {color_hex}")
                    continue

                # Patch each range
                for range_info in ranges_list:
                    start = range_info['start']
                    end = range_info['end']
                    f.seek(start)
                    data = f.read(end - start)
                    modified = patch_matrix_colors(data, color_bytes, 'RGBY')
                    f.seek(start)
                    f.write(modified)
                logger.debug(f"Patched 98_multi {layer_id} at {len(ranges_list)} ranges with color {color_hex}")
                continue

            start = offset_info.get('start', 0)

            # Handle 42_48 format (3x RGBA colors)
            if color_format == '42_48':
                size = offset_info.get('size', 12)
                if not color_hex:
                    color_hex = '808080FFFFFFFFFFFFFFFFFF'  # Default gray/white
                try:
                    color_bytes = bytes.fromhex(color_hex)
                    if len(color_bytes) != size:
                        logger.warning(f"Invalid color length for {layer_id}: {color_hex}, expected {size} bytes")
                        continue
                except ValueError:
                    logger.warning(f"Invalid hex color for {layer_id}: {color_hex}")
                    continue
                f.seek(start)
                f.write(color_bytes)
                logger.debug(f"Patched 42_48 {layer_id} at 0x{start:X} with color {color_hex}")
                continue

            # Determine patch mode based on offset_info structure
            if 'size' in offset_info:
                # Direct write mode - for 42_48 RGBA format
                size = offset_info['size']
                if not color_hex:
                    color_hex = '0099FFFF'  # Default blue RGBA

                try:
                    color_bytes = bytes.fromhex(color_hex)
                    if len(color_bytes) != size:
                        logger.warning(f"Invalid color length for {layer_id}: {color_hex}, expected {size} bytes")
                        continue
                except ValueError:
                    logger.warning(f"Invalid hex color for {layer_id}: {color_hex}")
                    continue

                # Write directly at offset
                f.seek(start)
                f.write(color_bytes)
                logger.debug(f"Direct write {layer_id} at 0x{start:X} with color {color_hex}")

            elif color_format == 'CF':
                # Single CF offset: color at offset+2
                if not color_hex:
                    color_hex = 'FFFFFF'
                try:
                    color_bytes = bytes.fromhex(color_hex)
                    if len(color_bytes) != 3:
                        logger.warning(f"Invalid color length for {layer_id}: {color_hex}, expected 3 bytes")
                        continue
                except ValueError:
                    logger.warning(f"Invalid hex color for {layer_id}: {color_hex}")
                    continue
                f.seek(start + 2)
                f.write(color_bytes)
                logger.debug(f"Patched CF {layer_id} at 0x{start:X} with color {color_hex}")

            elif color_format == '070707':
                # Single 070707 offset: color at offset+4 and offset+8 (after 07 07 07 04 marker)
                if not color_hex:
                    color_hex = 'FFFFFF'
                try:
                    color_bytes = bytes.fromhex(color_hex)
                    if len(color_bytes) != 3:
                        logger.warning(f"Invalid color length for {layer_id}: {color_hex}, expected 3 bytes")
                        continue
                except ValueError:
                    logger.warning(f"Invalid hex color for {layer_id}: {color_hex}")
                    continue
                f.seek(start + 4)
                f.write(color_bytes)
                f.seek(start + 8)
                f.write(color_bytes)
                logger.debug(f"Patched 070707 {layer_id} at 0x{start:X} with color {color_hex}")

            elif 'end' in offset_info:
                # Matrix patch mode - for 98 00 ## ## format
                end = offset_info['end']
                if not color_hex:
                    color_hex = 'FC00' if color_format == 'RGBY' else 'FFFFFF'

                # Determine expected color byte length based on format
                expected_len = 3 if color_format == 'RGB' else 2

                # Parse color bytes
                try:
                    color_bytes = bytes.fromhex(color_hex)
                    if len(color_bytes) != expected_len:
                        logger.warning(f"Invalid color length for {layer_id} ({color_format}): {color_hex}, expected {expected_len} bytes")
                        continue
                except ValueError:
                    logger.warning(f"Invalid hex color for {layer_id}: {color_hex}")
                    continue

                # Read the section
                f.seek(start)
                data = f.read(end - start)

                # Patch colors in the matrix format
                modified = patch_matrix_colors(data, color_bytes, color_format)

                # Write back
                f.seek(start)
                f.write(modified)

                logger.debug(f"Patched {layer_id} ({color_format}) at 0x{start:X}-0x{end:X} with color {color_hex}")


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

    # Load metadata
    metadata_file = STORAGE_PATH / 'metadata.json'
    if not metadata_file.exists():
        logger.info("No metadata.json found, skipping extras patching")
        return results

    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load metadata for extras patching: {e}")
        results['errors'].append(f"Failed to load metadata: {e}")
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
            offsets = extra_type_config['offsets']

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

            try:
                # Apply hex patches
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

        # Load metadata
        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({
                'success': True,
                'extras': {}
            })

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

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
            files_dir = get_project_files_dir()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        target_file = type_config['target_file']
        offsets = type_config['offsets']
        vanilla = type_config.get('vanilla', {})
        dat_path = find_dat_file(files_dir, target_file)

        if not dat_path or not dat_path.exists():
            return jsonify({
                'success': False,
                'error': f'Could not find {target_file} in MEX project'
            }), 404

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

        # Load metadata
        metadata_file = STORAGE_PATH / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {'characters': {}}

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

        # Save metadata
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

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

        # Load metadata
        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({
                'success': False,
                'error': 'Metadata file not found'
            }), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

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

        # Save metadata
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

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
            files_dir = get_project_files_dir()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        target_file = type_config['target_file']
        offsets = type_config['offsets']
        dat_path = find_dat_file(files_dir, target_file)

        if not dat_path or not dat_path.exists():
            return jsonify({
                'success': False,
                'error': f'Could not find {target_file} in MEX project'
            }), 404

        # Load metadata to find the mod
        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({
                'success': False,
                'error': 'Metadata file not found'
            }), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

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
        if modifications:
            apply_hex_patches(dat_path, offsets, modifications)
            logger.info(f"[OK] Installed {found_mod['name']} to {target_file}")

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
            files_dir = get_project_files_dir()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        target_file = type_config['target_file']
        offsets = type_config['offsets']
        dat_path = find_dat_file(files_dir, target_file)

        if not dat_path or not dat_path.exists():
            return jsonify({
                'success': False,
                'error': f'Could not find {target_file} in MEX project'
            }), 404

        # Apply vanilla colors
        vanilla_mods = {layer: {'color': color} for layer, color in vanilla.items()}
        apply_hex_patches(dat_path, offsets, vanilla_mods)
        logger.info(f"[OK] Restored vanilla colors for {character}/{extra_type}")

        return jsonify({
            'success': True
        })

    except Exception as e:
        logger.error(f"Restore vanilla error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
