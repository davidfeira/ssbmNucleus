"""
Shared internals for the extras blueprint: module-level state set by
init_extras_api(), dynamic offset detection, and DAT color patching helpers.
"""

import os
import logging

logger = logging.getLogger(__name__)

# These will be set by init_extras_api()
STORAGE_PATH = None
get_project_files_dir = None
HSDRAW_VIEWER_PATH = None


def init_extras_api(storage_path, project_files_dir_func, hsdraw_viewer_path=None):
    """Initialize the extras API with required dependencies from mex_api."""
    global STORAGE_PATH, get_project_files_dir, HSDRAW_VIEWER_PATH
    STORAGE_PATH = storage_path
    get_project_files_dir = project_files_dir_func
    HSDRAW_VIEWER_PATH = hsdraw_viewer_path


# =============================================================================
# DYNAMIC OFFSET DETECTION
# =============================================================================

# Cache for dynamic offsets: (file_path, mtime) -> offsets dict
_dynamic_offset_cache = {}


def find_laser_offsets(dat_path):
    """Dynamically find laser color matrix offsets in a DAT file.

    Searches for three consecutive 98 00 17 matrices (23 entries each)
    that are exactly 0xA0 (160 bytes) apart. This pattern is consistent
    even when file structure changes due to model imports.

    Args:
        dat_path: Path to the .dat file (PlFc.dat or PlFx.dat)

    Returns:
        Dict with wide/thin/outline offset info, or None if not found
    """
    try:
        with open(dat_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        logger.error(f"Failed to read {dat_path} for laser detection: {e}")
        return None

    # Find all 98 00 17 matrices (23 entries = 0x17)
    candidates = []
    pattern = bytes([0x98, 0x00, 0x17])
    pos = 0
    while True:
        pos = data.find(pattern, pos)
        if pos == -1:
            break
        candidates.append(pos)
        pos += 1

    logger.debug(f"Found {len(candidates)} potential 98 00 17 matrices in {dat_path}")

    # Look for three consecutive matrices exactly 0xA0 apart
    candidate_set = set(candidates)
    for start in candidates:
        second = start + 0xA0
        third = start + 0x140
        if second in candidate_set and third in candidate_set:
            # Verify each matrix has uniform colors (same 2-byte color repeated)
            # Matrix structure: 98 00 17 [VV CC CC] * 23 entries
            # First color at offset 4 (after header + vertex byte)
            valid = True
            for matrix_start in [start, second, third]:
                if matrix_start + 0x60 > len(data):
                    valid = False
                    break
                first_color = data[matrix_start + 4:matrix_start + 6]
                # Check a few more entries to verify uniformity
                for i in range(1, 5):
                    entry_color = data[matrix_start + 4 + (i * 4):matrix_start + 6 + (i * 4)]
                    if entry_color != first_color:
                        valid = False
                        break
                if not valid:
                    break

            if valid:
                logger.info(f"Found laser offsets at 0x{start:X} (wide), 0x{second:X} (thin), 0x{third:X} (outline)")
                return {
                    'wide': {'start': start, 'end': start + 0x60, 'format': 'RGBY'},
                    'thin': {'start': second, 'end': second + 0x60, 'format': 'RGBY'},
                    'outline': {'start': third, 'end': third + 0x60, 'format': 'RGBY'}
                }

    logger.warning(f"Could not find laser pattern in {dat_path}")
    return None


def find_sideb_offsets(dat_path):
    """Dynamically find side-B RGBA color offsets in a DAT file.

    Searches for the unique marker pattern 3E 99 99 9A 42 48 00 00 that follows
    the side-B color data. The three 4-byte RGBA values are located
    12 bytes before this marker.

    Args:
        dat_path: Path to the .dat file (PlFc.dat or PlFx.dat)

    Returns:
        Dict with primary/secondary/tertiary offset info, or None if not found
    """
    try:
        with open(dat_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        logger.error(f"Failed to read {dat_path} for side-B detection: {e}")
        return None

    # Search for the unique marker that follows side-B colors
    # This pattern (3E99999A42480000) appears right after the 12 color bytes
    marker = bytes.fromhex('3E99999A42480000')
    pos = data.find(marker)

    if pos > 12:
        # Colors are 12 bytes before the marker
        color_start = pos - 12
        # Verify it looks like RGBA colors (check alpha bytes are reasonable)
        if (data[color_start + 3] == 0xFF and
            data[color_start + 7] == 0xFF and
            data[color_start + 11] == 0xFF):
            logger.info(f"Found side-B offsets at 0x{color_start:X} (marker at 0x{pos:X})")
            return {
                'primary': {'start': color_start, 'size': 4, 'format': 'RGBA'},
                'secondary': {'start': color_start + 4, 'size': 4, 'format': 'RGBA'},
                'tertiary': {'start': color_start + 8, 'size': 4, 'format': 'RGBA'}
            }

    logger.warning(f"Could not find side-B pattern in {dat_path}")
    return None


def find_upb_offsets(dat_path):
    """Dynamically find Up-B (Firefox/Firebird) color offsets in EfFxData.dat.

    Searches for unique patterns to locate:
    - tip: 98 00 20 (32 entries, unique count)
    - body: cluster of 98 00 0A (10-entry matrices)
    - rings: 07 07 07 04 markers (after tip region)
    - trail: kept hardcoded (CF format, complex, early in file)

    Args:
        dat_path: Path to EfFxData.dat

    Returns:
        Dict with detected offsets, or None if not found
    """
    try:
        with open(dat_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        logger.error(f"Failed to read {dat_path} for Up-B detection: {e}")
        return None

    result = {}

    # Find tip: unique 98 00 20 pattern (32 entries)
    tip_pattern = bytes([0x98, 0x00, 0x20])
    tip_pos = data.find(tip_pattern)
    if tip_pos != -1:
        # Tip matrix is 0x80 bytes (128 bytes): 3 header + 32 * 4 entries - 3 = 128
        result['tip'] = {
            'start': tip_pos,
            'end': tip_pos + 0x80,
            'format': 'RGBY',
            'vanilla': 'FE60'
        }
        logger.debug(f"Found Up-B tip at 0x{tip_pos:X}")
    else:
        logger.warning("Could not find Up-B tip pattern (98 00 20)")
        return None

    # Find body: cluster of 98 00 0A matrices (10 entries each)
    # Look for multiple 98 00 0A patterns close together, before the tip
    body_pattern = bytes([0x98, 0x00, 0x0A])
    body_candidates = []
    pos = 0
    while pos < tip_pos:  # Body is before tip
        pos = data.find(body_pattern, pos)
        if pos == -1 or pos >= tip_pos:
            break
        body_candidates.append(pos)
        pos += 1

    # Find a cluster of 98 00 0A matrices (RGB format, close together)
    # Body region spans multiple matrices with consistent spacing
    if len(body_candidates) >= 3:
        # Calculate actual spacing between matrices
        matrix_spacing = body_candidates[1] - body_candidates[0]

        # Find the cluster where matrices have consistent spacing
        cluster_start = None
        cluster_end = None
        for i in range(len(body_candidates) - 2):
            # Check if matrices have consistent spacing (within tolerance)
            spacing1 = body_candidates[i + 1] - body_candidates[i]
            spacing2 = body_candidates[i + 2] - body_candidates[i + 1]
            if abs(spacing1 - spacing2) < 5:  # Consistent spacing
                cluster_start = body_candidates[i]
                # Find the end of the cluster
                last_in_cluster = i
                for j in range(i + 1, len(body_candidates)):
                    if j + 1 < len(body_candidates):
                        next_spacing = body_candidates[j + 1] - body_candidates[j]
                        if abs(next_spacing - matrix_spacing) > 5:
                            break
                    last_in_cluster = j

                # End is last matrix + 0x28 (40 bytes = 10 RGB entries)
                # This matches the hardcoded value which excludes trailing padding
                cluster_end = body_candidates[last_in_cluster] + 0x28
                break

        if cluster_start is not None:
            result['body'] = {
                'start': cluster_start,
                'end': cluster_end,
                'format': 'RGB',
                'vanilla': 'FFFFFF'
            }
            logger.debug(f"Found Up-B body cluster at 0x{cluster_start:X}-0x{cluster_end:X}")

    # Find rings: 07 07 07 04 markers (after tip region)
    rings_pattern = bytes([0x07, 0x07, 0x07, 0x04])
    rings_offsets = []
    pos = tip_pos  # Rings are after tip
    while True:
        pos = data.find(rings_pattern, pos)
        if pos == -1:
            break
        rings_offsets.append(pos)
        pos += 1

    if len(rings_offsets) >= 2:
        # Use first two 07 07 07 04 markers after tip
        result['rings'] = {
            'format': '070707',
            'offsets': rings_offsets[:2]
        }
        logger.debug(f"Found Up-B rings at {[hex(o) for o in rings_offsets[:2]]}")

    # Trail: keep hardcoded (CF format early in file, complex structure)
    # These offsets are stable because they're at the beginning of the file
    result['trail'] = {
        'format': 'CF',
        'offsets': [0x2EE, 0x2F4, 0x324, 0x32B, 0x52E, 0x534]
    }

    if 'tip' in result:
        logger.info(f"Found Up-B offsets: tip=0x{result['tip']['start']:X}")
        return result

    return None


def find_shine_offsets(dat_path):
    """Dynamically find Shine (Reflector) color offsets in EfFxData.dat.

    Searches for unique patterns to locate:
    - hex: 98 00 2B (43 entries, unique count)
    - inner: 98 00 1B (27 entries, unique count)
    - outer: 3 consecutive 98 00 0F (15-entry matrices)
    - bubble: 12 bytes before 3E99999A42480000 marker

    Args:
        dat_path: Path to EfFxData.dat

    Returns:
        Dict with detected offsets, or None if not found
    """
    try:
        with open(dat_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        logger.error(f"Failed to read {dat_path} for Shine detection: {e}")
        return None

    result = {}

    # Find hex: unique 98 00 2B pattern (43 entries)
    hex_pattern = bytes([0x98, 0x00, 0x2B])
    hex_pos = data.find(hex_pattern)
    if hex_pos != -1:
        # 43 entries * 4 bytes each + 3 header = 175 bytes, round to 0xB0
        result['hex'] = {
            'start': hex_pos,
            'end': hex_pos + 0xB0,
            'format': 'RGBY'
        }
        logger.debug(f"Found Shine hex at 0x{hex_pos:X}")
    else:
        logger.warning("Could not find Shine hex pattern (98 00 2B)")
        return None

    # Find inner: 98 00 1B pattern (27 entries) - search AFTER hex
    # There are multiple 98 00 1B in the file, inner is the one after hex
    inner_pattern = bytes([0x98, 0x00, 0x1B])
    inner_pos = data.find(inner_pattern, hex_pos + 0xB0)  # Start after hex region
    if inner_pos != -1:
        # 27 entries * 4 bytes + 3 header = 111 bytes, round to 0x70
        result['inner'] = {
            'start': inner_pos,
            'end': inner_pos + 0x70,
            'format': 'RGBY'
        }
        logger.debug(f"Found Shine inner at 0x{inner_pos:X}")

    # Find outer: 3 consecutive 98 00 0F matrices (15 entries each)
    outer_pattern = bytes([0x98, 0x00, 0x0F])
    outer_candidates = []
    pos = hex_pos if hex_pos != -1 else 0  # Search after hex
    while True:
        pos = data.find(outer_pattern, pos)
        if pos == -1:
            break
        outer_candidates.append(pos)
        pos += 1

    # Look for 3 consecutive 98 00 0F matrices close together
    for i in range(len(outer_candidates) - 2):
        first = outer_candidates[i]
        second = outer_candidates[i + 1]
        third = outer_candidates[i + 2]
        # Each 15-entry matrix is about 0x3F bytes (63), with overlapping ends
        # Hardcoded uses 0x40, 0x41, 0x42 for the three ranges respectively
        if second - first < 0x50 and third - second < 0x50:
            result['outer'] = {
                'format': '98_multi',
                'ranges': [
                    {'start': first, 'end': first + 0x40},
                    {'start': second, 'end': second + 0x41},
                    {'start': third, 'end': third + 0x42}
                ]
            }
            logger.debug(f"Found Shine outer at 0x{first:X}, 0x{second:X}, 0x{third:X}")
            break

    # Find bubble: 12 bytes before 3E99999A42480000 marker (same as side-B)
    bubble_marker = bytes.fromhex('3E99999A42480000')
    bubble_pos = data.find(bubble_marker)
    if bubble_pos > 12:
        # The bubble colors are 12 bytes before the marker
        bubble_start = bubble_pos - 12
        result['bubble'] = {
            'start': bubble_start,
            'format': '42_48',
            'size': 12
        }
        logger.debug(f"Found Shine bubble at 0x{bubble_start:X}")

    if 'hex' in result:
        logger.info(f"Found Shine offsets: hex=0x{result['hex']['start']:X}")
        return result

    return None


def find_laser_ring_offsets(dat_path):
    """Dynamically find laser ring color offsets in EfFxData.dat.

    Searches for unique pattern 85 80 08 0f 07 07 07 07 which precedes the colors.
    Then calculates hue byte offsets relative to the color position.

    Structure at pattern:
    - 85 80 08 0f: prefix (4 bytes)
    - 07 07 07 07: marker (4 bytes)
    - RR GG BB 00: color1 (4 bytes) at prefix+8
    - RR GG BB 00: color2 (4 bytes) at prefix+12

    Hue bytes are at fixed offsets from color1:
    - hue1: color1 + 0x678
    - hue2: color1 + 0x68C
    - hue3: color1 + 0x6A0
    - hue4: color1 + 0x6B4
    - hue5: color1 + 0x6C8
    - hue6: color1 + 0x6DC

    Args:
        dat_path: Path to EfFxData.dat

    Returns:
        Dict with detected offsets, or None if not found
    """
    try:
        with open(dat_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        logger.error(f"Failed to read {dat_path} for laser ring detection: {e}")
        return None

    # Search for unique prefix pattern 85 80 08 0f 07 07 07 07
    prefix = bytes([0x85, 0x80, 0x08, 0x0f, 0x07, 0x07, 0x07, 0x07])
    prefix_pos = data.find(prefix)

    if prefix_pos == -1:
        logger.warning("Could not find laser ring pattern (85 80 08 0f 07 07 07 07)")
        return None

    # Color positions relative to prefix
    color1_pos = prefix_pos + 8   # After 85 80 08 0f 07 07 07 07
    color2_pos = prefix_pos + 12  # After color1 + separator

    logger.info(f"Found laser ring: color1=0x{color1_pos:X}, color2=0x{color2_pos:X}")

    # Hue byte offsets relative to color1
    hue_offsets = [0x678, 0x68C, 0x6A0, 0x6B4, 0x6C8, 0x6DC]

    result = {
        'color1': {'start': color1_pos, 'size': 3, 'format': 'RGB'},
        'color2': {'start': color2_pos, 'size': 3, 'format': 'RGB'},
    }

    for i, offset in enumerate(hue_offsets, 1):
        result[f'hue{i}'] = {'start': color1_pos + offset, 'size': 1, 'format': 'BYTE'}

    logger.info(f"Laser ring hue1 at 0x{color1_pos + 0x678:X}")

    return result


def get_dynamic_offsets(dat_path, extra_type_id, fallback_offsets):
    """Get offsets for an extra type, using dynamic detection if applicable.

    For laser, sideb, upb, shine, and laser_ring types, attempts dynamic detection first,
    falling back to hardcoded offsets if detection fails.

    Results are cached by (file_path, mtime) to avoid re-scanning.

    Args:
        dat_path: Path to the .dat file
        extra_type_id: The extra type ID (e.g., 'laser', 'sideb', 'upb', 'shine', 'laser_ring')
        fallback_offsets: Hardcoded offsets to use if detection fails

    Returns:
        Dict of offset info for each layer
    """
    # Check if this type needs dynamic detection
    if extra_type_id not in ('laser', 'sideb', 'upb', 'shine', 'laser_ring'):
        return fallback_offsets

    # Check cache
    try:
        mtime = os.path.getmtime(dat_path)
        cache_key = (str(dat_path), mtime, extra_type_id)
        if cache_key in _dynamic_offset_cache:
            logger.debug(f"Using cached offsets for {extra_type_id} in {dat_path}")
            return _dynamic_offset_cache[cache_key]
    except Exception:
        pass

    # Attempt dynamic detection
    detected = None
    if extra_type_id == 'laser':
        detected = find_laser_offsets(dat_path)
    elif extra_type_id == 'sideb':
        detected = find_sideb_offsets(dat_path)
    elif extra_type_id == 'upb':
        detected = find_upb_offsets(dat_path)
    elif extra_type_id == 'shine':
        detected = find_shine_offsets(dat_path)
    elif extra_type_id == 'laser_ring':
        detected = find_laser_ring_offsets(dat_path)

    if detected:
        logger.info(f"Using dynamically detected offsets for {extra_type_id}")
        # Cache the result
        try:
            _dynamic_offset_cache[cache_key] = detected
        except Exception:
            pass
        return detected
    else:
        logger.info(f"Dynamic detection failed for {extra_type_id}, using hardcoded offsets")
        return fallback_offsets


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


def patch_matrix_colors(data, new_color=None, color_format="RGBY", vanilla_color=None, color_map=None):
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

    Note: Some matrices have alternating color/position entries. When vanilla_color
    is provided, only entries matching that color are patched (safe mode).

    Args:
        data: Bytes data from the offset range
        new_color: 2-byte RGBY or 3-byte RGB color value (used if color_map not provided)
        color_format: "RGBY" for 2-byte colors, "RGB" for 3-byte colors
        vanilla_color: If provided, only patch entries matching this color (bytes)
        color_map: Dict mapping vanilla color hex strings to new color hex strings.
                   Example: {"621F": "0FF0", "AB9F": "0A45"}
                   If provided, replaces only colors matching map keys.

    Returns:
        Patched bytes data
    """
    result = bytearray(data)
    color_len = 3 if color_format == "RGB" else 2

    # Header is 3 bytes (98 00 NN), first entry starts at position 3
    # Each entry: 1 byte vertex + color bytes + remaining bytes = 4 bytes total
    # First color at position 4 (3 header + 1 vertex)
    pos = 4  # First color position
    patched_count = 0

    # If color_map provided, use targeted replacement
    if color_map:
        # Pre-convert map keys/values to bytes for efficiency
        byte_map = {}
        for vanilla_hex, new_hex in color_map.items():
            try:
                vanilla_bytes = bytes.fromhex(vanilla_hex)
                new_bytes = bytes.fromhex(new_hex)
                if len(vanilla_bytes) == color_len and len(new_bytes) == color_len:
                    byte_map[vanilla_bytes] = new_bytes
            except ValueError:
                continue

        while pos + color_len - 1 < len(result):
            current_color = bytes(result[pos:pos + color_len])
            if current_color in byte_map:
                new_bytes = byte_map[current_color]
                for i in range(color_len):
                    result[pos + i] = new_bytes[i]
                patched_count += 1
            pos += 4  # Move to next color (4 bytes per entry)
    else:
        # Original behavior: replace all/matching colors with single new_color
        while pos + color_len - 1 < len(result):
            current_color = bytes(result[pos:pos + color_len])
            # If vanilla_color specified, only patch matching entries (safe mode)
            # This prevents corrupting position data in mixed-format matrices
            should_patch = vanilla_color is None or current_color == vanilla_color
            if should_patch:
                for i in range(color_len):
                    result[pos + i] = new_color[i]
                patched_count += 1
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


def read_shine_gradient_colors(dat_path, hex_offset):
    """Read the two-color gradient from shine hex region.

    The shine hex region contains two alternating colors:
    - Primary (vanilla 621F): bright edge/outline vertices
    - Secondary (vanilla AB9F): fill/interior vertices

    We read all colors in the matrix and identify the two distinct values.

    Args:
        dat_path: Path to EfFxData.dat
        hex_offset: Dict with start/end for the hex region

    Returns:
        Dict with 'primary' and 'secondary' color hex strings
    """
    start = hex_offset.get('start', 0)
    end = hex_offset.get('end', start)

    with open(dat_path, 'rb') as f:
        f.seek(start)
        data = f.read(end - start)

    # Find all distinct 2-byte RGBY colors in the matrix
    # Header is 3 bytes (98 00 NN), entries are 4 bytes each (vertex + 2-byte color + coord)
    colors_found = {}
    pos = 4  # First color position (after header + vertex byte)
    while pos + 1 < len(data):
        color = data[pos:pos + 2].hex().upper()
        colors_found[color] = colors_found.get(color, 0) + 1
        pos += 4

    # Sort by frequency - secondary (fill) usually has more vertices
    sorted_colors = sorted(colors_found.items(), key=lambda x: x[1], reverse=True)

    if len(sorted_colors) >= 2:
        # Most common = secondary (fill), second = primary (edge)
        secondary = sorted_colors[0][0]
        primary = sorted_colors[1][0]
    elif len(sorted_colors) == 1:
        # Only one color found (already uniform)
        primary = secondary = sorted_colors[0][0]
    else:
        # Fallback to vanilla
        primary = '621F'
        secondary = 'AB9F'

    return {
        'primary': primary,
        'secondary': secondary
    }


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

                # Get vanilla color for safe mode if specified
                vanilla_hex = offset_info.get('vanilla')
                vanilla_bytes = bytes.fromhex(vanilla_hex) if vanilla_hex else None

                # Patch each range
                for range_info in ranges_list:
                    start = range_info['start']
                    end = range_info['end']
                    f.seek(start)
                    data = f.read(end - start)
                    modified = patch_matrix_colors(data, color_bytes, 'RGBY', vanilla_bytes)
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
                logger.info(f"[Patch] Direct write {layer_id} at 0x{start:X} with {color_hex} ({len(color_bytes)} bytes)")

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

                # Get vanilla color for safe mode (only patch matching entries)
                # This prevents corrupting position data in mixed-format matrices
                vanilla_hex = offset_info.get('vanilla')
                vanilla_bytes = bytes.fromhex(vanilla_hex) if vanilla_hex else None

                # Patch colors in the matrix format
                modified = patch_matrix_colors(data, color_bytes, color_format, vanilla_bytes)

                # Write back
                f.seek(start)
                f.write(modified)

                logger.debug(f"Patched {layer_id} ({color_format}) at 0x{start:X}-0x{end:X} with color {color_hex}")
