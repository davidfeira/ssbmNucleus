#!/usr/bin/env python3
"""
CSP Generator using HSDRawViewer headless CSP generation
Takes a DAT file and generates a CSP using the native 3D rendering pipeline
"""

import os
import sys
import subprocess
from pathlib import Path
from PIL import Image
from detect_character import DATParser

# Add backend to path for imports
BACKEND_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.utils.logging_config import get_csp_logger

logger = get_csp_logger()

# HSDRawViewer CSP generator path - relative to this script
SCRIPT_DIR = Path(__file__).parent
TOOLS_DIR = SCRIPT_DIR.parent
BACKEND_DIR = TOOLS_DIR.parent

if os.name == 'nt':  # Windows
    HSDRAW_PATH = str(TOOLS_DIR / "HSDLib" / "HSDRawViewer" / "bin" / "Release" / "net6.0-windows")
    CSP_BASE_PATH = str(SCRIPT_DIR / "csp_data")
else:  # WSL/Linux
    HSDRAW_PATH = str(TOOLS_DIR / "HSDLib" / "HSDRawViewer" / "bin" / "Release" / "net6.0-windows")
    CSP_BASE_PATH = str(SCRIPT_DIR / "csp_data")

HSDRAW_EXE = os.path.join(HSDRAW_PATH, "HSDRawViewer.exe")

# Character code mapping for folder structure
CHARACTER_CODES = {
    'Captain Falcon': 'Ca',
    'Donkey Kong': 'Dk',
    'Fox': 'Fx',
    'Mr. Game & Watch': 'Gw',
    'Kirby': 'Kb',
    'Bowser': 'Kp',
    'Link': 'Lk',
    'Luigi': 'Lg',
    'Mario': 'Mr',
    'Marth': 'Ms',
    'Mewtwo': 'Mt',
    'Ness': 'Ns',
    'Peach': 'Pe',
    'Pichu': 'Pc',
    'Pikachu': 'Pk',
    'Jigglypuff': 'Pr',
    'Samus': 'Ss',
    'Sheik': 'Sk',
    'Yoshi': 'Ys',
    'Zelda': 'Zd',
    'Ice Climbers': 'Pp',  # Popo
    'Ice Climbers (Nana)': 'Nn',
    'Young Link': 'Cl',
    'Ganondorf': 'Gn',
    'Roy': 'Fe',
    'Falco': 'Fc',
    'Dr. Mario': 'Dr',
}

COLOR_CODES = {
    'Default': 'Nr',
    'Blue': 'Bu',
    'Red': 'Re',
    'Green': 'Gr',
    'Yellow': 'Ye',
    'Black': 'Bk',
    'White': 'Wh',
    'Pink': 'Pi',
    'Orange': 'Or',
    'Lavender': 'La',
    'Aqua/Light Blue': 'Aq',
    'Grey': 'Gy',
}

# Characters that use scene mode (only YML, no .anim file)
SCENE_MODE_CHARACTERS = [
    'Ganondorf',
    'Mr. Game & Watch',
    'Kirby',
    'Donkey Kong',
    'Luigi',
    'Jigglypuff',
    'Ice Climbers',
    'Ice Climbers (Nana)',
    'Captain Falcon',
    'Ness',
    'Bowser',
    'Dr. Mario',
    'Peach',
    'Mewtwo',
    'Pichu',
    'Mario',
]


def find_character_assets(character_name, dat_filepath=None):
    """Find animation and camera files for a character

    Scene mode characters (like Ganondorf) only use YML files for everything,
    no separate .anim file needed.

    Ice Climbers have separate folders for Popo and Nana, each with their own scene.yml.
    """
    # Ice Climbers (Nana) uses 'Ice Climbers (Nana)' folder
    # Ice Climbers (Popo) uses 'Ice Climbers (Popo)' folder
    folder_name = character_name
    if character_name == 'Ice Climbers':
        folder_name = 'Ice Climbers (Popo)'

    character_folder = os.path.join(CSP_BASE_PATH, folder_name)

    anim_file = None
    camera_file = None

    if os.path.exists(character_folder):
        # Scene mode characters only use YML, skip .anim file search
        use_scene_mode = character_name in SCENE_MODE_CHARACTERS

        if not use_scene_mode:
            # Look for any .anim file
            for file in os.listdir(character_folder):
                if file.endswith('.anim'):
                    anim_file = os.path.join(character_folder, file)
                    break

        # For scene mode, YML goes in anim_file slot
        if use_scene_mode:
            for file in os.listdir(character_folder):
                if file.endswith('.yml'):
                    anim_file = os.path.join(character_folder, file)
                    break
        else:
            # For non-scene mode, YML goes in camera_file slot
            for file in os.listdir(character_folder):
                if file.endswith('.yml'):
                    camera_file = os.path.join(character_folder, file)
                    break

    return anim_file, camera_file

def apply_character_specific_layers(csp_path, character_name):
    """
    Apply character-specific overlay layers to CSPs.
    Currently supports Fox gun layer and Ness horizontal flip.

    Args:
        csp_path: Path to the generated CSP
        character_name: Name of the character

    Returns:
        True if a layer was applied, False otherwise
    """
    # Ness - flip horizontally
    if character_name == 'Ness':
        if os.path.exists(csp_path):
            try:
                with Image.open(csp_path) as img:
                    # Flip the image horizontally (left-right)
                    flipped = img.transpose(Image.FLIP_LEFT_RIGHT)
                    flipped.save(csp_path)
                    logger.info(f"Flipped Ness CSP horizontally")
                    return True
            except Exception as e:
                logger.error(f"Failed to flip Ness CSP: {e}")
                return False

    # Fox gun layer
    if character_name == 'Fox':
        gun_layer_path = os.path.join(CSP_BASE_PATH, 'Fox', 'gunlayer.png')

        if os.path.exists(gun_layer_path) and os.path.exists(csp_path):
            try:
                # Open the base CSP and the gun layer
                with Image.open(csp_path) as base_csp:
                    with Image.open(gun_layer_path) as gun_layer:
                        # Ensure both images are in RGBA mode
                        if base_csp.mode != 'RGBA':
                            base_csp = base_csp.convert('RGBA')
                        if gun_layer.mode != 'RGBA':
                            gun_layer = gun_layer.convert('RGBA')

                        # Composite the gun layer on top of the CSP
                        # The gun layer should have transparency where Fox's body should show through
                        result = Image.alpha_composite(base_csp, gun_layer)

                        # Save the result back to the same path
                        result.save(csp_path)
                        return True
            except Exception as e:
                # If compositing fails, just continue without the layer
                # print(f"Failed to apply Fox gun layer: {e}")
                return False

    return False

def find_ice_climbers_pair(dat_filepath):
    """Find matching Popo/Nana pair using color mapping

    Color pairing scheme (based on actual DAT color detection):
    - Popo Default ↔ Nana Default
    - Popo Red ↔ Nana White
    - Popo Orange ↔ Nana Aqua/Light Blue
    - Popo Green ↔ Nana Yellow

    Matching strategies (in order of priority):
    1. Same directory - try all PlPp/PlNn files and check colors via DATParser
    2. Parent directory search
    3. Sibling directories (POPO/ ↔ NANA/)
    4. Extracted folder tree search

    Returns: (character_type, pair_filepath, popo_color, nana_color)
        character_type: 'popo' or 'nana'
        pair_filepath: path to the matching pair file
        popo_color: Popo's actual color name (from DAT)
        nana_color: Nana's actual color name (from DAT)
    """
    # Color mapping: Popo color name -> Nana color name
    POPO_TO_NANA = {
        'Default': 'Default',
        'Red': 'White',
        'Orange': 'Aqua/Light Blue',
        'Green': 'Yellow',
    }

    # Reverse mapping: Nana color -> Popo color
    NANA_TO_POPO = {v: k for k, v in POPO_TO_NANA.items()}

    filename = Path(dat_filepath).name
    dat_dir = Path(dat_filepath).parent

    # Parse this file to get the actual color
    parser = DATParser(dat_filepath)
    try:
        parser.read_dat()
        character, symbol = parser.detect_character()
        my_color = parser.detect_costume_color()
    except Exception as e:
        logger.error(f"Failed to parse Ice Climbers file {dat_filepath}: {e}")
        return (None, None, None, None)

    # Determine if this is Popo or Nana based on filename pattern (for finding pair)
    if 'PlPp' in filename:
        char_type = 'popo'
        popo_color = my_color
        nana_color = POPO_TO_NANA.get(popo_color)

        if not nana_color:
            logger.warning(f"No color mapping defined for Popo {popo_color}")
            return (char_type, None, popo_color, None)

        # Search for PlNn files
        search_pattern = 'PlNn'

    elif 'PlNn' in filename:
        char_type = 'nana'
        nana_color = my_color
        popo_color = NANA_TO_POPO.get(nana_color)

        if not popo_color:
            logger.warning(f"No color mapping defined for Nana {nana_color}")
            return (char_type, None, None, nana_color)

        # Search for PlPp files
        search_pattern = 'PlPp'
    else:
        return (None, None, None, None)

    # Helper function to check if a file matches the expected color
    def check_color_match(filepath, expected_color):
        """Parse a DAT file and check if its color matches expected_color"""
        try:
            p = DATParser(str(filepath))
            p.read_dat()
            file_color = p.detect_costume_color()
            return file_color == expected_color
        except:
            return False

    # Strategy 1: Same directory - find all PlPp/PlNn files and check colors
    target_color = nana_color if char_type == 'popo' else popo_color
    for dat_file in dat_dir.glob(f'*{search_pattern}*.dat'):
        if check_color_match(dat_file, target_color):
            logger.info(f"Found Ice Climbers pair in same directory: {dat_file.name} (color: {target_color})")
            return (char_type, str(dat_file), popo_color, nana_color)

    # Strategy 2: Parent directory
    for dat_file in dat_dir.parent.glob(f'*{search_pattern}*.dat'):
        if check_color_match(dat_file, target_color):
            logger.info(f"Found Ice Climbers pair in parent directory: {dat_file.name} (color: {target_color})")
            return (char_type, str(dat_file), popo_color, nana_color)

    # Strategy 3: Sibling directories (search all siblings that might contain pairs)
    # Check if current directory contains "popo" or "nana" in name (case-insensitive)
    dir_name_lower = dat_dir.name.lower()
    logger.info(f"Strategy 3: Checking sibling directories. Current dir: {dat_dir.name}, lowercase: {dir_name_lower}")
    if 'popo' in dir_name_lower or 'nana' in dir_name_lower or 'pp' in dir_name_lower or 'nn' in dir_name_lower:
        logger.info(f"Directory name contains popo/nana keyword, searching siblings...")
        # Search all sibling directories
        for sibling_dir in dat_dir.parent.iterdir():
            if sibling_dir.is_dir() and sibling_dir != dat_dir:
                logger.info(f"Checking sibling: {sibling_dir.name}")
                for dat_file in sibling_dir.glob(f'*{search_pattern}*.dat'):
                    logger.info(f"Found {search_pattern} file: {dat_file.name}, checking if color matches {target_color}...")
                    if check_color_match(dat_file, target_color):
                        logger.info(f"Found Ice Climbers pair in sibling directory: {sibling_dir.name}/{dat_file.name} (color: {target_color})")
                        return (char_type, str(dat_file), popo_color, nana_color)
    else:
        logger.info(f"Strategy 3 SKIPPED: Directory name '{dir_name_lower}' doesn't contain popo/nana/pp/nn")

    # Strategy 4: Search entire extracted folder tree
    search_root = dat_dir
    for _ in range(5):  # Max 5 levels up
        if 'extracted_' in str(search_root) or search_root.parent == search_root:
            break
        search_root = search_root.parent

    for dat_file in search_root.rglob(f'*{search_pattern}*.dat'):
        if check_color_match(dat_file, target_color):
            logger.info(f"Found Ice Climbers pair in tree: {dat_file.relative_to(search_root)} (color: {target_color})")
            return (char_type, str(dat_file), popo_color, nana_color)

    logger.warning(f"No Ice Climbers pair found for {filename} (Popo: {popo_color if char_type == 'popo' else 'N/A'}, Nana: {nana_color if char_type == 'nana' else 'N/A'})")
    return (char_type, None, popo_color, nana_color)

def composite_ice_climbers_csp(nana_csp_path, popo_csp_path, output_path):
    """Composite Popo CSP over Nana CSP with alpha blending

    Args:
        nana_csp_path: Path to Nana's CSP (background layer)
        popo_csp_path: Path to Popo's CSP (foreground layer)
        output_path: Where to save the composited result

    Returns:
        Path to composited CSP or None if failed
    """
    try:
        logger.info(f"DEBUG: Starting composite")
        logger.info(f"DEBUG: Nana CSP: {nana_csp_path}")
        logger.info(f"DEBUG: Popo CSP: {popo_csp_path}")
        logger.info(f"DEBUG: Output path: {output_path}")

        # Check files exist
        if not os.path.exists(nana_csp_path):
            logger.error(f"DEBUG: Nana CSP does not exist!")
            return None
        if not os.path.exists(popo_csp_path):
            logger.error(f"DEBUG: Popo CSP does not exist!")
            return None

        # Load both images
        logger.info(f"DEBUG: Loading Nana image...")
        nana = Image.open(nana_csp_path)
        logger.info(f"DEBUG: Nana image loaded - size: {nana.size}, mode: {nana.mode}")

        logger.info(f"DEBUG: Loading Popo image...")
        popo = Image.open(popo_csp_path)
        logger.info(f"DEBUG: Popo image loaded - size: {popo.size}, mode: {popo.mode}")

        # Ensure both images are in RGBA mode
        if nana.mode != 'RGBA':
            logger.info(f"DEBUG: Converting Nana to RGBA")
            nana = nana.convert('RGBA')
        if popo.mode != 'RGBA':
            logger.info(f"DEBUG: Converting Popo to RGBA")
            popo = popo.convert('RGBA')

        logger.info(f"DEBUG: Sizes match: {nana.size == popo.size}")

        # Composite Popo on top of Nana - use PIL's composite with proper alpha blending
        # We need to blend pixel by pixel based on alpha values
        logger.info(f"DEBUG: Creating composite using PIL composite...")

        # Start with Nana as the base
        result = nana.copy()

        # Use Image.composite but we need to extract alpha channel for mask
        # Split channels
        r, g, b, a = popo.split()
        logger.info(f"DEBUG: Extracted Popo alpha channel")

        # Use the alpha channel as the mask - this will blend based on transparency
        result = Image.composite(popo, result, a)
        logger.info(f"DEBUG: Composite created - size: {result.size}, mode: {result.mode}")

        logger.info(f"DEBUG: Saving to {output_path}")
        result.save(output_path)
        logger.info(f"DEBUG: Saved successfully")

        # Clean up
        nana.close()
        popo.close()

        logger.info(f"Composited Ice Climbers CSP: {Path(output_path).name}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to composite Ice Climbers CSP: {e}", exc_info=True)
        return None

def generate_single_csp_internal(dat_filepath, character, anim_file=None, camera_file=None):
    """Internal function to generate a single CSP

    Used by both normal CSP generation and Ice Climbers composite generation.
    Returns the path to the generated CSP or None if failed.
    """
    # Generate output filename
    dat_dir = os.path.dirname(os.path.abspath(dat_filepath))
    dat_name = os.path.splitext(os.path.basename(dat_filepath))[0]
    output_csp = os.path.join(dat_dir, f"{dat_name}_csp.png")

    # Convert paths to Windows format for the .exe
    def to_windows_path(path):
        """Convert WSL path to Windows path"""
        if path.startswith('/mnt/c/'):
            return path.replace('/mnt/c/', 'C:\\').replace('/', '\\')
        return path

    # Build HSDRawViewer command with Windows paths
    windows_exe = to_windows_path(HSDRAW_EXE)
    windows_dat = to_windows_path(os.path.abspath(dat_filepath))
    windows_output = to_windows_path(output_csp)

    # On Linux, need to prepend 'wine' to run Windows executable
    if os.name != 'nt':
        cmd = ["wine", windows_exe, "--csp", windows_dat, windows_output]
    else:
        cmd = [windows_exe, "--csp", windows_dat, windows_output]

    if anim_file:
        cmd.append(to_windows_path(anim_file))

    if camera_file:
        cmd.append(to_windows_path(camera_file))

    logger.info(f"Running HSDRawViewer for {Path(dat_filepath).name}")
    logger.info(f"Command: {' '.join(cmd)}")

    # Run HSDRawViewer CSP generation
    try:
        # Run directly without PowerShell to avoid path quoting issues
        if os.name == 'nt':  # Windows
            # Use both CREATE_NO_WINDOW and DETACHED_PROCESS to hide console
            result = subprocess.run(cmd, capture_output=True, text=True,
                                   creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
        else:  # Linux - run with Wine
            result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            if os.path.exists(output_csp):
                logger.info(f"CSP generated successfully: {Path(output_csp).name}")
                return output_csp
            else:
                logger.error("HSDRawViewer completed but CSP file not found")
                return None
        else:
            logger.error(f"HSDRawViewer failed with return code: {result.returncode}")
            if result.stdout:
                logger.error(f"STDOUT: {result.stdout}")
            if result.stderr:
                logger.error(f"STDERR: {result.stderr}")
            return None

    except Exception as e:
        logger.error(f"Error running HSDRawViewer: {e}", exc_info=True)
        return None

def generate_ice_climbers_composite_csp(popo_dat, nana_dat):
    """Generate composite CSP for Ice Climbers (Popo + Nana)

    Args:
        popo_dat: Path to Popo .dat file
        nana_dat: Path to Nana .dat file

    Returns:
        Path to final composited CSP (associated with Popo) or None if failed
    """
    logger.info("Generating Ice Climbers composite CSP")

    # Get scene files for both (will be in anim_file slot for scene mode)
    popo_yml, _ = find_character_assets('Ice Climbers', popo_dat)  # Gets Popo's scene.yml
    nana_yml, _ = find_character_assets('Ice Climbers (Nana)', nana_dat)  # Gets Nana's scene.yml

    if not popo_yml or not nana_yml:
        logger.error("Failed to find Ice Climbers scene files")
        return None

    logger.info(f"Using Popo scene: {Path(popo_yml).name}, Nana scene: {Path(nana_yml).name}")

    # Generate Nana CSP (background) - YML in anim_file slot for scene mode
    logger.info("Generating Nana CSP (background layer)")
    nana_csp = generate_single_csp_internal(nana_dat, 'Ice Climbers', nana_yml, None)
    if not nana_csp:
        logger.error("Failed to generate Nana CSP")
        return None

    # Generate Popo CSP (foreground) - YML in anim_file slot for scene mode
    logger.info("Generating Popo CSP (foreground layer)")
    popo_csp = generate_single_csp_internal(popo_dat, 'Ice Climbers', popo_yml, None)
    if not popo_csp:
        logger.error("Failed to generate Popo CSP")
        return None

    # Composite them - Popo over Nana
    popo_dat_name = os.path.splitext(os.path.basename(popo_dat))[0]
    output_dir = os.path.dirname(popo_csp)
    final_csp = os.path.join(output_dir, f"{popo_dat_name}_csp.png")

    result = composite_ice_climbers_csp(nana_csp, popo_csp, final_csp)

    # Clean up temporary CSPs
    try:
        if os.path.exists(nana_csp) and nana_csp != final_csp:
            os.remove(nana_csp)
        if os.path.exists(popo_csp) and popo_csp != final_csp:
            os.remove(popo_csp)
    except Exception as e:
        logger.warning(f"Failed to clean up temp CSPs: {e}")

    return result

def generate_csp(dat_filepath):
    """
    Generate CSP for a DAT file using HSDRawViewer headless CSP generation
    Returns path to generated CSP or None if failed
    """

    logger.info(f"Starting CSP generation for: {dat_filepath}")

    # 1. Parse DAT to get character and color info
    parser = DATParser(dat_filepath)
    try:
        parser.read_dat()
        character, symbol = parser.detect_character()
        color = parser.detect_costume_color()
    except Exception as e:
        logger.error(f"Error parsing DAT file: {e}")
        return None

    if not character:
        logger.warning("Could not detect character from DAT file")
        return None

    logger.info(f"Detected character: {character} - {color}")

    # Special handling for Ice Climbers - match and composite pairs
    is_ice_climbers = character in ['Ice Climbers', 'Ice Climbers (Nana)']
    if is_ice_climbers:
        char_type, pair_file, popo_color, nana_color = find_ice_climbers_pair(dat_filepath)

        if char_type == 'nana':
            # Nana files are composited with Popo, skip individual generation
            logger.info(f"Skipping Nana {nana_color} - will be composited with Popo {popo_color}")
            return None
        elif char_type == 'popo' and pair_file:
            # Found a matching pair - generate composite CSP
            logger.info(f"Processing Ice Climbers pair: Popo {popo_color} + Nana {nana_color}")
            return generate_ice_climbers_composite_csp(dat_filepath, pair_file)
        elif char_type == 'popo' and not pair_file:
            # Popo without matching Nana - generate solo CSP
            logger.warning(f"No matching Nana found for Popo {popo_color}, generating solo CSP")
            # Continue to normal CSP generation below

    # 2. Find character assets (animation and camera files)
    anim_file, camera_file = find_character_assets(character, dat_filepath)

    if anim_file:
        logger.info(f"Found animation file: {Path(anim_file).name}")
    if camera_file:
        logger.info(f"Found camera file: {Path(camera_file).name}")

    # 3. Generate CSP using internal function
    output_csp = generate_single_csp_internal(dat_filepath, character, anim_file, camera_file)

    if output_csp:
        # Apply character-specific layers (e.g., Fox gun layer)
        layer_applied = apply_character_specific_layers(output_csp, character)
        if layer_applied:
            logger.info(f"Applied character-specific layer for {character}")

    return output_csp

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_csp.py <dat_file>")
        print("Example: python3 generate_csp.py 'pichu nr.dat'")
        sys.exit(1)

    dat_file = sys.argv[1]

    if not os.path.exists(dat_file):
        print(f"File not found: {dat_file}")
        sys.exit(1)

    if not os.path.exists(HSDRAW_EXE):
        print(f"HSDRawViewer not found at: {HSDRAW_EXE}")
        print("Please build HSDRawViewer first")
        sys.exit(1)

    csp_path = generate_csp(dat_file)

    if csp_path:
        print(f"Success! CSP generated at: {csp_path}")
    else:
        print("Failed to generate CSP")
        sys.exit(1)

if __name__ == "__main__":
    main()