"""DAT file processing service - wraps existing processor tools."""
import sys
import logging
from pathlib import Path
from PIL import Image

# Add tools to path
TOOLS_DIR = Path(__file__).parent.parent.parent / 'tools' / 'processor'
sys.path.insert(0, str(TOOLS_DIR))

from detect_character import DATParser
from validate_costume import validate_dat_file
from generate_csp import generate_csp as generate_csp_internal
from generate_stock_icon import generate_stock_icon as generate_stock_internal

logger = logging.getLogger(__name__)

# Image type detection constants
CSP_ASPECT_RATIO = 136 / 188  # ~0.723
STOCK_ASPECT_RATIO = 1.0  # Square
ASPECT_RATIO_TOLERANCE = 0.05


def detect_character(file_path):
    """
    Detect character from .dat file.
    Returns: dict with character info or None

    Distinguishes between:
    - Character costume files (PlXxYy with Ply symbols and known colors) - is_costume=True
    - Data/effect mods (PlXx with only ftData symbols OR unknown colors) - is_costume=False
    """
    try:
        parser = DATParser(file_path)
        parser.read_dat()
        character, symbol = parser.detect_character()
        color = parser.detect_costume_color()
        is_costume = parser.is_character_costume()

        if not character:
            return None

        # Treat unknown colors as data mods (not character costumes)
        # These are custom colors like Ti (Teal) for Kirby or Fox that aren't standard Melee colors
        if color == 'Unknown Color':
            logger.info(f"Unknown color detected for {file_path} - treating as data mod")
            is_costume = False

        return {
            'character': character,
            'color': color,
            'symbol': symbol,
            'is_costume': is_costume
        }
    except Exception as e:
        logger.error(f"Character detection failed for {file_path}: {e}")
        return None


def validate_for_slippi(file_path, auto_fix=False):
    """
    Validate .dat file for Slippi compatibility using copy→test→replace workflow.

    Args:
        file_path: Path to the .dat file
        auto_fix: If True, apply fixes to the original file. If False, only check.

    Returns: dict with validation results
    """
    import shutil
    import os

    try:
        import hashlib
        file_path = Path(file_path)

        # Get hash of original file BEFORE any processing
        with open(file_path, 'rb') as f:
            original_hash = hashlib.md5(f.read()).hexdigest()

        # CRITICAL: Validator needs proper Melee character filename (e.g., PlFxGr.dat)
        # Get the proper filename based on detected character + color
        parser = DATParser(str(file_path))
        parser.read_dat()
        proper_filename = parser.get_character_filename()

        if not proper_filename:
            return {
                'is_valid': False,
                'needs_fix': False,
                'fix_applied': False,
                'slippi_safe': False,
                'output': 'Could not determine proper character filename for validation'
            }

        # Always use copy→test workflow with proper character code filename
        temp_check_file = file_path.parent / f"{proper_filename}.dat"

        # If file already has proper name, use a temp name to avoid copying to itself
        if temp_check_file.resolve() == file_path.resolve():
            temp_check_file = file_path.parent / f"_temp_{proper_filename}.dat"

        shutil.copy2(file_path, temp_check_file)

        try:
            # Check the temp file
            result = validate_dat_file(temp_check_file, auto_fix=False, create_backup=False)

            is_valid = result.get('is_valid', False)
            needs_fix = result.get('needs_fix', False)

            # Verify original was not modified
            with open(file_path, 'rb') as f:
                original_hash_after = hashlib.md5(f.read()).hexdigest()

            if original_hash != original_hash_after:
                logger.error(f"ORIGINAL FILE WAS MODIFIED! Before: {original_hash}, After: {original_hash_after}")
                return {
                    'is_valid': False,
                    'needs_fix': False,
                    'fix_applied': False,
                    'slippi_safe': False,
                    'output': f"ERROR: Original file was modified during validation!\nBefore: {original_hash}\nAfter: {original_hash_after}"
                }

            # If auto_fix is True and file needs fixing, apply the fix
            if auto_fix and needs_fix:
                # The temp_check_file was already fixed by the validator
                # Copy the fixed version back to the original file
                shutil.copy2(temp_check_file, file_path)
                logger.info(f"Copied fixed DAT from {temp_check_file} to {file_path}")

                return {
                    'is_valid': True,  # It's now valid after fixing
                    'needs_fix': needs_fix,  # It did need fixes
                    'fix_applied': True,
                    'slippi_safe': True,
                    'output': result.get('output', '')
                }
            else:
                # Just return check results without modifying original
                return {
                    'is_valid': is_valid,
                    'needs_fix': needs_fix,
                    'fix_applied': False,
                    'slippi_safe': is_valid and not needs_fix,
                    'output': result.get('output', '')
                }
        finally:
            # Clean up temp check file
            if temp_check_file.exists():
                os.remove(temp_check_file)

    except Exception as e:
        logger.error(f"Slippi validation failed for {file_path}: {e}")
        return {
            'is_valid': False,
            'needs_fix': False,
            'fix_applied': False,
            'slippi_safe': False,
            'output': str(e)
        }


def generate_csp(file_path):
    """
    Generate CSP from .dat file.
    Returns: path to generated CSP or None
    """
    try:
        csp_path = generate_csp_internal(file_path)
        return csp_path
    except Exception as e:
        logger.error(f"CSP generation failed for {file_path}: {e}")
        return None


def generate_stock(csp_path, character):
    """
    Generate stock icon from CSP.
    Returns: path to generated stock icon or None
    """
    try:
        # Generate stock icon filename based on CSP path
        csp_file = Path(csp_path)
        stock_output = csp_file.parent / f"{csp_file.stem.replace('_csp', '')}_stock.png"

        stock_path = generate_stock_internal(csp_path, character, str(stock_output))
        return stock_path
    except Exception as e:
        logger.error(f"Stock generation failed for {csp_path}: {e}")
        return None


def process_dat_file(file_path, steps=None):
    """
    Process a .dat file through the full pipeline or selected steps.

    Args:
        file_path: Path to the .dat file
        steps: List of steps to run ['detect', 'validate', 'csp', 'stock'] or None for all

    Returns:
        dict with processing results
    """
    if steps is None:
        steps = ['detect', 'validate', 'csp', 'stock']

    result = {
        'file': file_path,
        'success': False,
        'character': None,
        'color': None,
        'symbol': None,
        'slippi_safe': None,
        'csp_path': None,
        'stock_path': None
    }

    # Step 1: Detect character
    if 'detect' in steps:
        char_info = detect_character(file_path)
        if not char_info:
            logger.warning(f"Not a character .dat file: {file_path}")
            return result

        result.update(char_info)

        # Check if this is a data mod (not a costume)
        # Data mods have character info but no Ply symbols (e.g., PlMsPastelSword.dat)
        if not char_info.get('is_costume', False):
            logger.info(f"Data/effect mod detected (not a costume): {file_path}")
            result['is_data_mod'] = True
            # Don't validate, generate CSP, or generate stock for data mods
            # Just return character info for tagging purposes
            result['success'] = True
            return result

        # Mark Nana files for Ice Climbers (they get composited with Popo at post creation)
        filename = Path(file_path).name
        character = char_info['character']
        is_ice_climbers = character in ['Ice Climbers', 'Ice Climbers (Nana)']
        is_nana = is_ice_climbers and 'PlNn' in filename
        if is_nana:
            logger.info(f"Detected Nana file (will be composited with Popo at post creation): {filename}")
            result['is_ice_climbers_nana'] = True

    # Step 2: Validate for Slippi (for all costumes including Nana)
    if 'validate' in steps:
        validation = validate_for_slippi(file_path, auto_fix=False)
        result['slippi_safe'] = validation['slippi_safe']
        result['needs_fix'] = validation['needs_fix']
        result['fix_applied'] = validation.get('fix_applied', False)
        result['backup_path'] = validation.get('backup_path')
        result['validation_output'] = validation.get('output', '')

    # Step 3: Generate CSP
    if 'csp' in steps:
        csp_path = generate_csp(file_path)
        if csp_path:
            result['csp_path'] = csp_path
            result['csp_generated'] = True
        else:
            result['csp_generated'] = False

    # Step 4: Generate Stock Icon (skip for Nana - only Popo gets a stock)
    if 'stock' in steps and result.get('csp_path') and result.get('character') and not result.get('is_ice_climbers_nana'):
        stock_path = generate_stock(result['csp_path'], result['character'])
        if stock_path:
            result['stock_path'] = stock_path
            result['stock_generated'] = True
        else:
            result['stock_generated'] = False

    result['success'] = result.get('csp_path') is not None or 'csp' not in steps

    return result


def detect_image_type(file_path):
    """
    Detect if an image is a CSP or Stock icon based on resolution.

    Args:
        file_path: Path to image file

    Returns:
        'csp', 'stock', or None
    """
    try:
        img = Image.open(file_path)
        width, height = img.size

        # Calculate aspect ratio
        aspect_ratio = width / height if height > 0 else 0

        # Check for CSP (136x188 or multiples with ~0.723 aspect ratio)
        if abs(aspect_ratio - CSP_ASPECT_RATIO) < ASPECT_RATIO_TOLERANCE:
            # Verify it's a multiple of base CSP dimensions
            if width % 136 == 0 and height % 188 == 0:
                return 'csp'

        # Check for Stock (24x24 or multiples, square)
        if abs(aspect_ratio - STOCK_ASPECT_RATIO) < ASPECT_RATIO_TOLERANCE:
            # Verify it's a multiple of base stock dimensions
            if width % 24 == 0 and height % 24 == 0 and width == height:
                return 'stock'

        return None

    except Exception as e:
        logger.error(f"Image type detection failed for {file_path}: {e}")
        return None


def extract_character_color_from_filename(filename):
    """
    Extract character and color from filename patterns.

    Examples:
        - fox_green.png -> (Fox, Green)
        - PlFxGr.png -> (Fox, Green)
        - marth_white_csp.png -> (Marth, White)
        - csp_PlFxgr sm4sh fox (green).png -> (Fox, Green)

    Returns:
        tuple: (character, color) or (None, None)
    """
    # Remove common prefixes/suffixes and extensions
    filename_lower = filename.lower()
    filename_lower = filename_lower.replace('_csp', '').replace('_stock', '')
    filename_lower = filename_lower.replace(' csp', '').replace(' stock', '')
    filename_lower = filename_lower.replace('csp_', '').replace('stock_', '')
    filename_lower = filename_lower.replace('.png', '').replace('.dat', '').replace('.jpg', '').replace('.jpeg', '')

    # Character code mapping (PlFxGr -> Fox Green)
    char_codes = {
        'fx': 'Fox', 'fc': 'Falcon', 'dk': 'Donkey Kong', 'dr': 'Dr. Mario',
        'fa': 'Falco', 'gn': 'Ganondorf', 'kb': 'Kirby', 'kp': 'Koopa',
        'lk': 'Link', 'lg': 'Luigi', 'mr': 'Mario', 'ms': 'Marth',
        'mt': 'Mewtwo', 'ns': 'Ness', 'pe': 'Peach', 'pc': 'Pichu',
        'pk': 'Pikachu', 'pr': 'Jigglypuff', 'fe': 'Roy', 'ss': 'Samus',
        'ys': 'Yoshi', 'ze': 'Zelda', 'cl': 'Young Link', 'gw': 'Mr. Game And Watch',
        'ca': 'Captain Falcon', 'nn': 'Ness', 'pp': 'Ice Climbers'
    }

    # Color codes
    color_codes = {
        'nr': 'Default', 're': 'Red', 'bu': 'Blue', 'gr': 'Green', 'wh': 'White',
        'ye': 'Yellow', 'bk': 'Black', 'pi': 'Pink', 'aq': 'Aqua', 'la': 'Lavender',
        'or': 'Orange', 'cy': 'Cyan', 'pu': 'Purple', 'vi': 'Violet', 'br': 'Brown',
        'gy': 'Grey', 'dg': 'Dark Green'
    }

    # Try PlXxYy pattern anywhere in the filename (character code + color code)
    import re
    pl_pattern = re.search(r'pl([a-z]{2})([a-z]{2})', filename_lower)
    if pl_pattern:
        char_code = pl_pattern.group(1)
        color_code = pl_pattern.group(2)

        character = char_codes.get(char_code)
        color = color_codes.get(color_code)

        if character and color:
            return (character, color)

    # Try word-based patterns (fox_green, marth_white, etc.)
    parts = filename_lower.split('_')
    if len(parts) >= 2:
        char_word = parts[0].capitalize()
        color_word = parts[1].capitalize()

        # Check if it matches known characters
        for code, char_name in char_codes.items():
            if char_name.lower().replace(' ', '') == char_word.lower():
                return (char_name, color_word)

    return (None, None)
