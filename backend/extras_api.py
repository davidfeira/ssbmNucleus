"""
Extras API - Character effect color modifications (lasers, side-B, shine, etc.)
Extracted from mex_api.py for better organization.
"""

import json
import uuid
import logging
import subprocess
import shutil
import os
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from extra_types import get_extra_types, get_extra_type, has_extras, get_storage_character

logger = logging.getLogger(__name__)

# Blueprint for extras routes
extras_bp = Blueprint('extras', __name__)

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
        fallback_offsets = type_config['offsets']
        dat_path = find_dat_file(files_dir, target_file)

        if not dat_path or not dat_path.exists():
            return jsonify({
                'success': False,
                'error': f'Could not find {target_file} in MEX project'
            }), 404

        # Use dynamic offset detection for laser/sideb, fallback to hardcoded
        offsets = get_dynamic_offsets(dat_path, extra_type, fallback_offsets)

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
                            textures_dir = STORAGE_PATH / storage_char / 'textures'
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
            files_dir = get_project_files_dir()
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


# =============================================================================
# MODEL EXTRAS - For 3D model replacements (gun, etc.)
# =============================================================================

def extract_model_from_dat(dat_path, jobj_path, output_dae_path):
    """Extract a model from a DAT file using HSDRawViewer CLI.

    Args:
        dat_path: Path to the source .dat file
        jobj_path: Path within the DAT to the JOBJ (e.g., "ftDataFalco/Articles/Articles_1/Model_/RootModelJoint")
        output_dae_path: Path to save the exported .dae file

    Returns:
        True if successful, raises exception on failure
    """
    if not HSDRAW_VIEWER_PATH:
        raise RuntimeError("HSDRawViewer path not configured")

    cmd = [
        str(HSDRAW_VIEWER_PATH),
        '--model', 'export',
        str(dat_path),
        jobj_path,
        str(output_dae_path)
    ]

    logger.info(f"Running model export: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        logger.error(f"Model export failed: {result.stderr}")
        raise RuntimeError(f"Model export failed: {result.stderr}")

    logger.info(f"Model export output: {result.stdout}")
    return True


def import_model_to_dat(dat_path, jobj_path, model_dae_path, output_dat_path):
    """Import a model into a DAT file using HSDRawViewer CLI.

    Args:
        dat_path: Path to the source .dat file
        jobj_path: Path within the DAT to the JOBJ
        model_dae_path: Path to the .dae model file to import
        output_dat_path: Path to save the modified .dat file

    Returns:
        True if successful, raises exception on failure
    """
    if not HSDRAW_VIEWER_PATH:
        raise RuntimeError("HSDRawViewer path not configured")

    cmd = [
        str(HSDRAW_VIEWER_PATH),
        '--model', 'import',
        str(dat_path),
        jobj_path,
        str(model_dae_path),
        str(output_dat_path)
    ]

    logger.info(f"Running model import: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        logger.error(f"Model import failed: {result.stderr}")
        raise RuntimeError(f"Model import failed: {result.stderr}")

    logger.info(f"Model import output: {result.stdout}")
    return True


@extras_bp.route('/api/mex/storage/models/create', methods=['POST'])
def create_model_extra():
    """Create a new model extra from an uploaded .dae or .dat file.

    For .dat files, extracts the model as .dae first.
    Stores the .dae in storage/[Character]/models/[uuid].dae

    Request: multipart/form-data with:
        - character: Character name (e.g., "Falco")
        - extraType: Extra type ID (e.g., "gun")
        - name: Display name for the mod
        - file: The .dae or .dat file
    """
    try:
        character = request.form.get('character')
        extra_type = request.form.get('extraType')
        name = request.form.get('name', 'Custom Model')

        if not character or not extra_type:
            return jsonify({
                'success': False,
                'error': 'Missing character or extraType parameter'
            }), 400

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

        # Verify this extra type exists and is a model type
        type_config = get_extra_type(character, extra_type)
        if not type_config:
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" not defined for {character}'
            }), 400

        if type_config.get('type') != 'model':
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" is not a model type'
            }), 400

        # Get storage character
        storage_char = get_storage_character(character, extra_type)

        # Create models directory if needed
        models_dir = STORAGE_PATH / storage_char / 'models'
        models_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique ID
        mod_id = f"{extra_type}_{uuid.uuid4().hex[:8]}"

        # Determine file type and process
        filename = secure_filename(file.filename)
        file_ext = Path(filename).suffix.lower()

        if file_ext == '.dae':
            # Direct .dae upload - save directly
            dae_path = models_dir / f"{mod_id}.dae"
            file.save(str(dae_path))
            logger.info(f"Saved .dae model to {dae_path}")

        elif file_ext == '.dat':
            # .dat upload - need to extract the model
            # Save the .dat temporarily
            temp_dat = models_dir / f"{mod_id}_temp.dat"
            file.save(str(temp_dat))

            try:
                # Extract model from the .dat
                dae_path = models_dir / f"{mod_id}.dae"
                jobj_path = type_config.get('model_path')

                if not jobj_path:
                    return jsonify({
                        'success': False,
                        'error': 'Model path not configured for this extra type'
                    }), 400

                extract_model_from_dat(temp_dat, jobj_path, dae_path)
                logger.info(f"Extracted model from .dat to {dae_path}")

            finally:
                # Clean up temp .dat
                if temp_dat.exists():
                    temp_dat.unlink()
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported file type: {file_ext}. Use .dae or .dat'
            }), 400

        # Load metadata
        metadata_file = STORAGE_PATH / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {'characters': {}}

        # Ensure character structure exists
        if storage_char not in metadata.get('characters', {}):
            metadata['characters'][storage_char] = {'skins': [], 'extras': {}}

        char_data = metadata['characters'][storage_char]
        if 'extras' not in char_data:
            char_data['extras'] = {}
        if extra_type not in char_data['extras']:
            char_data['extras'][extra_type] = []

        # Create mod entry
        new_mod = {
            'id': mod_id,
            'name': name,
            'type': 'model',
            'date_added': datetime.now().isoformat(),
            'source': 'uploaded',
            'model_file': f"models/{mod_id}.dae"
        }

        char_data['extras'][extra_type].append(new_mod)

        # Save metadata
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Created model extra '{name}' ({extra_type}) for {storage_char}")

        return jsonify({
            'success': True,
            'mod': new_mod
        })

    except Exception as e:
        logger.error(f"Create model extra error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@extras_bp.route('/api/mex/storage/models/install', methods=['POST'])
def install_model_extra():
    """Install a model extra by importing the .dae into the target .dat file.

    Request body:
    {
        "character": "Falco",
        "extraType": "gun",
        "modId": "gun_abc123"
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

        if type_config.get('type') != 'model':
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" is not a model type'
            }), 400

        # Get storage character
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
        jobj_path = type_config.get('model_path')

        if not jobj_path:
            return jsonify({
                'success': False,
                'error': 'Model path not configured for this extra type'
            }), 400

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

        # Find the mod
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

        # Get the .dae file path
        model_file = found_mod.get('model_file')
        if not model_file:
            return jsonify({
                'success': False,
                'error': 'Model file not found in mod metadata'
            }), 400

        dae_path = STORAGE_PATH / storage_char / model_file
        if not dae_path.exists():
            return jsonify({
                'success': False,
                'error': f'Model file not found: {dae_path}'
            }), 404

        # Import the model into the .dat file (in place)
        # We'll write to a temp file then replace the original
        temp_output = dat_path.parent / f"{dat_path.stem}_temp{dat_path.suffix}"

        try:
            import_model_to_dat(dat_path, jobj_path, dae_path, temp_output)

            # Replace original with modified
            shutil.move(str(temp_output), str(dat_path))
            logger.info(f"[OK] Installed model '{found_mod['name']}' to {target_file}")

        except Exception as e:
            # Clean up temp file on failure
            if temp_output.exists():
                temp_output.unlink()
            raise

        return jsonify({
            'success': True
        })

    except Exception as e:
        logger.error(f"Install model extra error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# =============================================================================
# TEXTURE EXTRAS - For hue-shifted textures (Up-B fire, etc.)
# =============================================================================

def shift_texture_hue(input_png, output_png, hue_degrees):
    """Shift hue of texture, preserving alpha and luminance.

    Args:
        input_png: Path to input PNG file
        output_png: Path to save hue-shifted PNG
        hue_degrees: Hue shift amount in degrees (0-360)

    Returns:
        True if successful
    """
    from PIL import Image
    import colorsys

    img = Image.open(input_png).convert('RGBA')
    pixels = img.load()

    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]
            # Convert to HLS (hue, lightness, saturation)
            h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
            # Shift hue
            h = (h + hue_degrees/360) % 1.0
            # Convert back to RGB
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            pixels[x, y] = (int(r*255), int(g*255), int(b*255), a)

    img.save(output_png)
    logger.info(f"Hue shifted texture saved to {output_png}")
    return True


def export_texture(dat_path, node_path, tex_index, output_png):
    """Export texture from DAT using HSDRaw CLI.

    Args:
        dat_path: Path to the .dat file
        node_path: Path within DAT to JOBJ containing texture
        tex_index: Index of texture to export
        output_png: Path to save exported PNG

    Returns:
        True if successful, raises exception on failure
    """
    if not HSDRAW_VIEWER_PATH:
        raise RuntimeError("HSDRawViewer path not configured")

    cmd = [
        str(HSDRAW_VIEWER_PATH),
        '--texture', 'export',
        str(dat_path),
        node_path,
        str(tex_index),
        str(output_png)
    ]

    logger.info(f"Running texture export: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        logger.error(f"Texture export failed: {result.stderr}")
        raise RuntimeError(f"Texture export failed: {result.stderr}")

    logger.info(f"Texture export output: {result.stdout}")
    return True


def import_texture(dat_path, node_path, tex_index, input_png, output_dat):
    """Import texture into DAT using HSDRaw CLI.

    Args:
        dat_path: Path to the source .dat file
        node_path: Path within DAT to JOBJ containing texture
        tex_index: Index of texture to replace
        input_png: Path to the PNG file to import
        output_dat: Path to save the modified .dat file

    Returns:
        True if successful, raises exception on failure
    """
    if not HSDRAW_VIEWER_PATH:
        raise RuntimeError("HSDRawViewer path not configured")

    cmd = [
        str(HSDRAW_VIEWER_PATH),
        '--texture', 'import',
        str(dat_path),
        node_path,
        str(tex_index),
        str(input_png),
        str(output_dat)
    ]

    logger.info(f"Running texture import: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        logger.error(f"Texture import failed: {result.stderr}")
        raise RuntimeError(f"Texture import failed: {result.stderr}")

    logger.info(f"Texture import output: {result.stdout}")
    return True


def ensure_vanilla_texture(character, extra_type, type_config):
    """Ensure vanilla reference texture exists, exporting if necessary.

    Args:
        character: Character name
        extra_type: Extra type ID (e.g., 'upb_texture')
        type_config: Extra type configuration

    Returns:
        Path to vanilla texture PNG, or None on failure
    """
    # Get storage character
    storage_char = get_storage_character(character, extra_type)

    # Create textures directory
    textures_dir = STORAGE_PATH / storage_char / 'textures'
    textures_dir.mkdir(parents=True, exist_ok=True)

    vanilla_png = textures_dir / f"{extra_type}_vanilla.png"

    # If vanilla already exists, return it
    if vanilla_png.exists():
        logger.info(f"Using existing vanilla texture: {vanilla_png}")
        return vanilla_png

    # Export vanilla texture from MEX project
    try:
        files_dir = get_project_files_dir()
    except Exception as e:
        logger.error(f"Cannot get project files dir: {e}")
        return None

    target_file = type_config['target_file']
    dat_path = find_dat_file(files_dir, target_file)

    if not dat_path or not dat_path.exists():
        logger.error(f"Could not find {target_file} to export vanilla texture")
        return None

    try:
        node_path = type_config['texture_path']
        tex_index = type_config['texture_index']
        export_texture(dat_path, node_path, tex_index, vanilla_png)
        logger.info(f"Exported vanilla texture to {vanilla_png}")
        return vanilla_png
    except Exception as e:
        logger.error(f"Failed to export vanilla texture: {e}")
        return None


def detect_texture_hue(png_path):
    """Analyze a texture and detect its dominant hue.

    Args:
        png_path: Path to PNG file

    Returns:
        Dominant hue in degrees (0-360), or None if detection fails
    """
    from PIL import Image
    import colorsys

    try:
        img = Image.open(png_path).convert('RGBA')
        pixels = img.load()

        # Collect hues from non-transparent, saturated pixels
        hue_votes = {}

        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                if a < 32:  # Skip mostly transparent pixels
                    continue

                h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)

                # Only count pixels with decent saturation and not too dark/light
                if s > 0.2 and 0.1 < l < 0.9:
                    # Round hue to nearest 5 degrees for binning
                    hue_deg = int(round(h * 360 / 5) * 5) % 360
                    hue_votes[hue_deg] = hue_votes.get(hue_deg, 0) + 1

        if not hue_votes:
            logger.warning(f"No saturated pixels found in {png_path}")
            return None

        # Return the most common hue
        dominant_hue = max(hue_votes, key=hue_votes.get)
        logger.info(f"Detected dominant hue: {dominant_hue} degrees from {png_path}")
        return dominant_hue

    except Exception as e:
        logger.error(f"Failed to detect hue from {png_path}: {e}")
        return None


@extras_bp.route('/api/mex/storage/textures/current/<character>/<extra_type>', methods=['GET'])
def get_current_texture_hue(character, extra_type):
    """Get the current hue of a texture extra by exporting and analyzing it.

    This is lazy-loaded - only called when user views the extra panel.
    """
    try:
        # Get extra type config
        type_config = get_extra_type(character, extra_type)
        if not type_config:
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" not defined for {character}'
            }), 400

        if type_config.get('type') != 'texture':
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" is not a texture type'
            }), 400

        # Find the target DAT file
        try:
            files_dir = get_project_files_dir()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        target_file = type_config['target_file']
        dat_path = find_dat_file(files_dir, target_file)

        if not dat_path or not dat_path.exists():
            return jsonify({
                'success': False,
                'error': f'Could not find {target_file} in MEX project'
            }), 404

        # Get storage character for cache directory
        storage_char = get_storage_character(character, extra_type)
        textures_dir = STORAGE_PATH / storage_char / 'textures'
        textures_dir.mkdir(parents=True, exist_ok=True)

        # Check if we have a cached export that's still valid
        current_png = textures_dir / f"{extra_type}_current.png"
        cache_valid = False

        if current_png.exists():
            # Check if DAT is newer than our cached export
            dat_mtime = dat_path.stat().st_mtime
            cache_mtime = current_png.stat().st_mtime
            cache_valid = cache_mtime > dat_mtime

        if not cache_valid:
            # Export current texture from DAT
            node_path = type_config['texture_path']
            tex_index = type_config['texture_index']

            try:
                export_texture(dat_path, node_path, tex_index, current_png)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to export texture: {e}'
                }), 500

        # Detect the hue
        current_hue = detect_texture_hue(str(current_png))
        vanilla_hue = type_config.get('vanilla_hue', 30)

        return jsonify({
            'success': True,
            'hue': current_hue,
            'vanillaHue': vanilla_hue,
            'isVanilla': current_hue is not None and abs(current_hue - vanilla_hue) < 10
        })

    except Exception as e:
        logger.error(f"Get current texture hue error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@extras_bp.route('/api/mex/storage/textures/install', methods=['POST'])
def install_texture_extra():
    """Install a texture extra by applying hue shift and importing into DAT.

    For texture extras, the hue value is applied to the vanilla reference texture
    and the result is imported into the target DAT file.

    Request body:
    {
        "character": "Fox",
        "extraType": "upb_texture",
        "hue": 180  // Hue shift in degrees (0-360)
    }
    """
    try:
        data = request.json
        character = data.get('character')
        extra_type = data.get('extraType')
        hue = data.get('hue', 0)

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

        if type_config.get('type') != 'texture':
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" is not a texture type'
            }), 400

        # Ensure vanilla texture exists
        vanilla_png = ensure_vanilla_texture(character, extra_type, type_config)
        if not vanilla_png:
            return jsonify({
                'success': False,
                'error': 'Could not get vanilla reference texture'
            }), 500

        # Get storage character for temp files
        storage_char = get_storage_character(character, extra_type)
        textures_dir = STORAGE_PATH / storage_char / 'textures'

        # Create hue-shifted texture
        hue_shifted_png = textures_dir / f"{extra_type}_hue_{int(hue)}.png"

        # Calculate hue shift from vanilla
        vanilla_hue = type_config.get('vanilla_hue', 30)  # Default orange ~30 degrees
        hue_shift = hue - vanilla_hue

        if abs(hue_shift) < 1:
            # No shift needed, use vanilla directly
            hue_shifted_png = vanilla_png
            logger.info("No hue shift needed, using vanilla texture")
        else:
            shift_texture_hue(str(vanilla_png), str(hue_shifted_png), hue_shift)
            logger.info(f"Created hue-shifted texture: {hue_shifted_png}")

        # Find the target DAT file
        try:
            files_dir = get_project_files_dir()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        target_file = type_config['target_file']
        dat_path = find_dat_file(files_dir, target_file)

        if not dat_path or not dat_path.exists():
            return jsonify({
                'success': False,
                'error': f'Could not find {target_file} in MEX project'
            }), 404

        # Import the hue-shifted texture into the DAT
        node_path = type_config['texture_path']
        tex_index = type_config['texture_index']

        # Write to a temp file then replace original
        temp_dat = dat_path.parent / f"{dat_path.stem}_temp{dat_path.suffix}"

        try:
            import_texture(dat_path, node_path, tex_index, hue_shifted_png, temp_dat)
            # Replace original with modified
            shutil.move(str(temp_dat), str(dat_path))
            logger.info(f"[OK] Installed texture with hue {hue} to {target_file}")
        except Exception as e:
            if temp_dat.exists():
                temp_dat.unlink()
            raise

        return jsonify({
            'success': True,
            'hue': hue
        })

    except Exception as e:
        logger.error(f"Install texture extra error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@extras_bp.route('/api/mex/storage/textures/restore-vanilla', methods=['POST'])
def restore_vanilla_texture():
    """Restore vanilla texture.

    Request body:
    {
        "character": "Fox",
        "extraType": "upb_texture"
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

        # Ensure vanilla texture exists
        vanilla_png = ensure_vanilla_texture(character, extra_type, type_config)
        if not vanilla_png:
            return jsonify({
                'success': False,
                'error': 'Could not get vanilla reference texture'
            }), 500

        # Find the target DAT file
        try:
            files_dir = get_project_files_dir()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        target_file = type_config['target_file']
        dat_path = find_dat_file(files_dir, target_file)

        if not dat_path or not dat_path.exists():
            return jsonify({
                'success': False,
                'error': f'Could not find {target_file} in MEX project'
            }), 404

        # Import the vanilla texture
        node_path = type_config['texture_path']
        tex_index = type_config['texture_index']
        temp_dat = dat_path.parent / f"{dat_path.stem}_temp{dat_path.suffix}"

        try:
            import_texture(dat_path, node_path, tex_index, vanilla_png, temp_dat)
            shutil.move(str(temp_dat), str(dat_path))
            logger.info(f"[OK] Restored vanilla texture for {character}/{extra_type}")
        except Exception as e:
            if temp_dat.exists():
                temp_dat.unlink()
            raise

        return jsonify({
            'success': True
        })

    except Exception as e:
        logger.error(f"Restore vanilla texture error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@extras_bp.route('/api/mex/storage/models/delete', methods=['POST'])
def delete_model_extra():
    """Delete a model extra and its .dae file.

    Request body:
    {
        "character": "Falco",
        "extraType": "gun",
        "modId": "gun_abc123"
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

        # Get storage character
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

        # Find the mod
        char_data = metadata.get('characters', {}).get(storage_char, {})
        extras = char_data.get('extras', {})
        mods = extras.get(extra_type, [])

        # Find and remove the mod
        found_mod = None
        new_mods = []
        for mod in mods:
            if mod.get('id') == mod_id:
                found_mod = mod
            else:
                new_mods.append(mod)

        if not found_mod:
            return jsonify({
                'success': False,
                'error': f'Mod {mod_id} not found'
            }), 404

        # Delete the model file if it exists
        model_file = found_mod.get('model_file')
        if model_file:
            dae_path = STORAGE_PATH / storage_char / model_file
            if dae_path.exists():
                dae_path.unlink()
                logger.info(f"Deleted model file: {dae_path}")

        # Update metadata
        extras[extra_type] = new_mods

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Deleted model extra {mod_id} from {storage_char}")

        return jsonify({
            'success': True
        })

    except Exception as e:
        logger.error(f"Delete model extra error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
