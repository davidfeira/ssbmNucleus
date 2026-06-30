#!/usr/bin/env python3
"""
CSP Generator using HSDRawViewer headless CSP generation
Takes a DAT file and generates a CSP using the native 3D rendering pipeline
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from PIL import Image
from detect_character import DATParser

from logging_config import get_csp_logger

logger = get_csp_logger()


def get_windows_subprocess_args():
    """Hide subprocess windows on Windows while keeping stdout/stderr capturable."""
    if os.name != 'nt':
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {
        'startupinfo': startupinfo,
        'creationflags': subprocess.CREATE_NO_WINDOW,
    }

# HSDRawViewer CSP generator path - relative to this script.
SCRIPT_DIR = Path(__file__).parent
TOOLS_DIR = SCRIPT_DIR.parent

# csp_data is bundled next to this script (PyInstaller datas) in both dev and
# frozen builds, so it's always SCRIPT_DIR-relative.
CSP_BASE_PATH = str(SCRIPT_DIR / "csp_data")

def _resolve_hsdraw_dir() -> str:
    """Directory holding HSDRawViewer.exe.

    Packaged build: HSDRawViewer is shipped by electron-builder extraResources
    to <install>/resources/utility/HSDRawViewer — it is NOT inside the
    PyInstaller bundle, so resolving it relative to THIS script (_MEIPASS) gives
    a path that doesn't exist (the cause of mass CSP "preview failures" in the
    installed app). Resolve from the exe location instead; mirrors
    core.config.HSDRAW_EXE (RESOURCES_DIR = mex_backend.exe parent.parent)."""
    if getattr(sys, 'frozen', False):
        return str(Path(sys.executable).parent.parent / "utility" / "HSDRawViewer")
    return str(TOOLS_DIR / "HSDLib" / "HSDRawViewer" / "bin" / "Release" / "net6.0-windows")


HSDRAW_PATH = _resolve_hsdraw_dir()
HSDRAW_EXE = os.path.join(HSDRAW_PATH, "HSDRawViewer.exe")

# Character code mapping for folder structure
CHARACTER_CODES = {
    'Captain Falcon': 'Ca',
    'Donkey Kong': 'Dk',
    'Fox': 'Fx',
    'Mr. Game & Watch': 'Gw',
    'Kirby': 'Kb',
    'Bowser': 'Kp',
    'Giga Bowser': 'Gk',
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

# detect_character() returns a few names that aren't CHARACTER_CODES keys (the
# same variants CHARACTER_HEAD_BONES / CHARACTER_ARM_BONES alias inline below).
# Without these, char-code resolution silently no-ops for those fighters --
# dropping low-poly mesh hiding (_find_ftdata, used for both CSP and head-shot /
# stock renders) and the deformed-rig check (_vanilla_skeleton_ref). 'Ice
# Climbers (Nana)' already resolves via CHARACTER_CODES; it's kept here so this
# stays the single complete alias set.
_CHAR_CODE_ALIASES = {
    'C. Falcon': 'Ca',
    'DK': 'Dk',
    'Ice Climbers (Nana)': 'Nn',
    'Young Link (Girl)': 'Zd',
}


def _resolve_char_code(character):
    """The 2-letter Pl<XX> code for a character name, accepting both
    CHARACTER_CODES keys and the detect_character() name variants (e.g.
    'C. Falcon', 'DK', 'Young Link (Girl)'). None for unknown / custom names."""
    return CHARACTER_CODES.get(character) or _CHAR_CODE_ALIASES.get(character)


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

# TopOfHeadBone JOBJ index per character, extracted from the vanilla PlXx.dat
# fighter data (ModelLookupTables +0x12). Model imports keep the skeleton, so
# projecting this bone during the CSP render locates the head of ANY model --
# the .head.json sidecar drives stock-icon head cropping for model imports.
CHARACTER_HEAD_BONES = {
    'Captain Falcon': 39,
    'Donkey Kong': 44,
    'Fox': 41,
    'Mr. Game & Watch': 20,
    'Kirby': 11,
    'Bowser': 51,
    'Giga Bowser': 48,
    'Link': 40,
    'Luigi': 24,
    'Mario': 24,
    'Marth': 60,
    'Mewtwo': 44,
    'Ness': 25,
    'Peach': 87,
    'Pichu': 16,
    'Pikachu': 15,
    'Jigglypuff': 11,
    'Samus': 42,
    'Sheik': 36,
    'Yoshi': 43,
    'Zelda': 89,
    'Ice Climbers': 19,
    'Ice Climbers (Nana)': 19,
    'Young Link': 42,
    'Ganondorf': 54,
    'Roy': 62,
    'Falco': 39,
    'Dr. Mario': 24,
    # detect_character() name variants (it says 'C. Falcon'/'DK', the asset
    # folders agree) -- missing aliases silently disabled head shots
    'C. Falcon': 39,
    'DK': 44,
    'Young Link (Girl)': 89,
}

# RightArm/LeftArm (shoulder) JOBJ indexes per character, from the vanilla
# PlXx.dat FighterBoneTable (ftData +0x54, offsets 0x04/0x10). Head shots
# zero-scale these subtrees so T-pose arms can't pollute the head silhouette.
CHARACTER_ARM_BONES = {
    'Captain Falcon': (46, 24),
    'Donkey Kong': (52, 30),
    'Fox': (56, 26),
    'Mr. Game & Watch': (27, 12),
    'Kirby': (43, 38),
    'Bowser': (61, 34),
    'Giga Bowser': (61, 34),
    'Link': (54, 22),
    'Luigi': (32, 9),
    'Mario': (32, 9),
    'Marth': (71, 29),
    'Mewtwo': (55, 32),
    'Ness': (32, 10),
    'Peach': (98, 72),
    'Pichu': (26, 10),
    'Pikachu': (25, 9),
    'Jigglypuff': (34, 30),
    'Samus': (49, 27),
    'Sheik': (42, 22),
    'Yoshi': (57, 27),
    'Zelda': (101, 73),
    'Ice Climbers': (25, 10),
    'Ice Climbers (Nana)': (25, 10),
    'Young Link': (56, 22),
    'Ganondorf': (67, 23),
    'Roy': (73, 31),
    'Falco': (50, 24),
    'Dr. Mario': (32, 9),
    'C. Falcon': (46, 24),
    'DK': (52, 30),
    'Young Link (Girl)': (101, 73),
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
    'Giga Bowser',
    'Dr. Mario',
    'Peach',
    'Mewtwo',
    'Pichu',
    'Mario',
]

# Characters that pose with ANOTHER fighter's CSP scene (find_character_assets
# remaps the folder), so that scene's curated hiddenNodes describe the WRONG
# model. These fall back to the auto-derived low-poly hide set instead.
SCENE_BORROWERS = {'Giga Bowser'}


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
    # detect_character() says 'Mr. Game & Watch' but the asset folder is 'G&W'
    if character_name == 'Mr. Game & Watch':
        folder_name = 'G&W'
    # Giga Bowser is an internal Melee fighter without CSP setup assets of his
    # own. Pose him with Bowser's scene data while rendering the Giga model.
    if character_name == 'Giga Bowser':
        folder_name = 'Bowser'

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

def apply_character_specific_layers(csp_path, character_name, scale=1):
    """
    Apply character-specific overlay layers to CSPs.
    Currently supports Fox gun layer and Ness horizontal flip.

    Args:
        csp_path: Path to the generated CSP
        character_name: Name of the character
        scale: Resolution multiplier (1, 2, 4, 8, 16) - gun layer will be scaled to match

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
                # Mirror the head sidecar's x to match the flipped image
                head_json = csp_path + '.head.json'
                if os.path.exists(head_json):
                    try:
                        import json
                        with open(head_json) as f:
                            head = json.load(f)
                        head['x'] = head.get('width', 136) - head.get('x', 0)
                        with open(head_json, 'w') as f:
                            json.dump(head, f)
                    except Exception as e:
                        logger.warning(f"Failed to mirror Ness head sidecar: {e}")
                return True
            except Exception as e:
                logger.error(f"Failed to flip Ness CSP: {e}")
                return False

    # Fox gun: SUPERSEDED. The blaster is now rendered as the real 3D article
    # model during CSP generation (see generate_single_csp_internal -> the
    # `--gun` flags / _fox_gun_args), so it tracks the pose/lighting instead of
    # being a fixed 2D overlay. The old `gunlayer.png` composite is intentionally
    # no longer applied here (applying it too would double the gun).

    return False

def find_ice_climbers_pair(dat_filepath, explicit_pair_filepath=None):
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

    dat_path = Path(dat_filepath)
    filename = dat_path.name
    dat_dir = dat_path.parent

    # Parse this file to get the actual color
    parser = DATParser(dat_filepath)
    try:
        parser.read_dat()
        character, symbol = parser.detect_character()
        my_color = parser.detect_costume_color()
    except Exception as e:
        logger.error(f"Failed to parse Ice Climbers file {dat_filepath}: {e}")
        return (None, None, None, None)

    # Determine if this is Popo or Nana. Prefer the parsed character (set by
    # DATParser.detect_character above) so imports work with renamed temp files
    # like `tmpXXXX.dat` — the filename loses the PlPp/PlNn signal once a DAT
    # is copied into a tempdir, and without char_type generate_csp can't fire
    # its "skip solo Nana" branch and we end up rendering an orphaned Nana.
    if character == 'Ice Climbers' or 'PlPp' in filename:
        char_type = 'popo'
        popo_color = my_color
        nana_color = POPO_TO_NANA.get(popo_color)
        # Search for PlNn files
        search_pattern = 'PlNn'
    elif character == 'Ice Climbers (Nana)' or 'PlNn' in filename:
        char_type = 'nana'
        nana_color = my_color
        popo_color = NANA_TO_POPO.get(nana_color)
        # Search for PlPp files
        search_pattern = 'PlPp'
    else:
        return (None, None, None, None)

    if explicit_pair_filepath:
        explicit_pair = Path(explicit_pair_filepath)
        if explicit_pair.exists() and explicit_pair.resolve() != dat_path.resolve():
            try:
                pair_parser = DATParser(str(explicit_pair))
                pair_parser.read_dat()
                pair_character, _pair_symbol = pair_parser.detect_character()
                pair_color = pair_parser.detect_costume_color()
            except Exception as e:
                logger.warning(f"Explicit Ice Climbers pair is not readable: {explicit_pair} ({e})")
            else:
                expected_character = 'Ice Climbers (Nana)' if char_type == 'popo' else 'Ice Climbers'
                expected_prefix = 'PlNn' if char_type == 'popo' else 'PlPp'
                if pair_character == expected_character or expected_prefix in explicit_pair.name:
                    if char_type == 'popo':
                        nana_color = pair_color
                    else:
                        popo_color = pair_color
                    logger.info(
                        f"Using explicit Ice Climbers pair: {filename} + "
                        f"{explicit_pair.name} ({pair_character} - {pair_color})"
                    )
                    return (char_type, str(explicit_pair), popo_color, nana_color)
                logger.warning(
                    f"Explicit Ice Climbers pair has unexpected character: "
                    f"{explicit_pair.name} parsed as {pair_character}"
                )

    # Strategy 0: Filename slot suffix in the SAME directory.
    # Custom MEX color slots (e.g. Popo Blue + Nana Blue) aren't in the vanilla
    # POPO_TO_NANA color table, so the color-name strategies below give up. But
    # iso_scanner deliberately stages both halves of an IC pair into the same
    # skin folder before invoking generate_csp specifically so a filename match
    # works here — no DAT parsing needed.
    stem = os.path.splitext(filename)[0]
    if len(stem) >= 6:
        my_suffix = stem[4:6]  # 2-char slot code, e.g. "Bu"
        candidate = dat_dir / f"{search_pattern}{my_suffix}.dat"
        if candidate.exists() and candidate.resolve() != Path(dat_filepath).resolve():
            logger.info(
                f"Found Ice Climbers pair in same directory by filename suffix: "
                f"{candidate.name} (suffix '{my_suffix}')"
            )
            return (char_type, str(candidate), popo_color, nana_color)

    # Strategy 0b: A caller may stage exactly one opposite climber beside this
    # DAT even when the slot suffixes do not match. Treat that as an explicit
    # local pair before any color-table or tree-search heuristics.
    local_opposites = [
        p for p in dat_dir.glob(f'*{search_pattern}*.dat')
        if p.resolve() != dat_path.resolve()
    ]
    if len(local_opposites) == 1:
        pair = local_opposites[0]
        try:
            pair_parser = DATParser(str(pair))
            pair_parser.read_dat()
            pair_color = pair_parser.detect_costume_color()
        except Exception:
            pair_color = None
        if char_type == 'popo':
            nana_color = pair_color
        else:
            popo_color = pair_color
        logger.info(
            f"Found Ice Climbers pair in same directory by single opposite DAT: "
            f"{pair.name}"
        )
        return (char_type, str(pair), popo_color, nana_color)

    # If the vanilla color table doesn't cover this slot, we can't fall back
    # on color-based matching below — bail out so the caller renders solo.
    if char_type == 'popo' and not nana_color:
        logger.warning(f"No color mapping defined for Popo {popo_color}")
        return (char_type, None, popo_color, None)
    if char_type == 'nana' and not popo_color:
        logger.warning(f"No color mapping defined for Nana {nana_color}")
        return (char_type, None, None, nana_color)

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

    # Strategy 4: Search entire extracted folder tree. Do not climb out of a
    # temporary render/staging directory into the repo root; that caused ISO
    # scans to pair custom Popo DATs with utility/assets/vanilla/Nana DATs.
    search_root = dat_dir
    found_extract_root = False
    for _ in range(5):  # Max 5 levels up
        root_name = search_root.name.lower()
        if root_name == 'extracted' or root_name.startswith('extracted_'):
            found_extract_root = True
            break
        if search_root.parent == search_root:
            break
        search_root = search_root.parent

    if found_extract_root:
        for dat_file in search_root.rglob(f'*{search_pattern}*.dat'):
            if check_color_match(dat_file, target_color):
                logger.info(f"Found Ice Climbers pair in tree: {dat_file.relative_to(search_root)} (color: {target_color})")
                return (char_type, str(dat_file), popo_color, nana_color)
    else:
        logger.info(f"Strategy 4 SKIPPED: no extracted root above {dat_dir}")

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

# --------------------------------------------------------------------------- #
# Low-poly DObj hiding for portrait renders                                     #
# --------------------------------------------------------------------------- #
# Portrait renders (--csp / --head-shot) draw EVERY DObj, including the
# off-screen low-poly (magnifier/shadow) mesh, which then pokes through the
# image. Each fighter's ftData (Pl<XX>.dat) carries a visibility table whose
# costume-0 LowPoly set is exactly that mesh — read it and pass --hide-dobjs.
# This is the same DObj-index space the engine and HSDRawViewer use, and works
# for ANY character (vanilla, recolor, custom) because each ships its own
# Pl<XX>.dat. It beats the hand-authored per-scene `hiddenNodes`, which are
# calibrated for one model and don't transfer to a borrowed scene (Giga Bowser
# posed with Bowser's scene). See docs/CSP_LOWPOLY_HIDING.md.
def _test_base_files_dirs():
    """Candidate `test-base/files` dirs holding the vanilla Pl<XX>.dat fighter
    data + costume DATs, most-correct first.

    The installed/frozen app keeps these in the WRITABLE vault
    (`core.config.STORAGE_PATH` = %LOCALAPPDATA%\\SSBM Nucleus\\storage). Resolving
    via `SCRIPT_DIR.parents[2]` instead points into the PyInstaller _MEIPASS temp
    in a frozen build (which has no `storage/`) -- that's why low-poly hiding
    silently logged "no ftData found" and skipped `--hide-dobjs` in the PACKAGED
    app only, so CSP low-poly cheeks were never hidden there. Try the frozen-aware
    path first, then the dev/repo path."""
    dirs = []
    try:
        backend = str(SCRIPT_DIR.parents[2] / "backend")
        if backend not in sys.path:
            sys.path.insert(0, backend)
        from core.config import STORAGE_PATH  # installed vault when frozen
        dirs.append(Path(STORAGE_PATH) / "test-base" / "files")
    except Exception:
        pass
    dirs.append(SCRIPT_DIR.parents[2] / "storage" / "test-base" / "files")
    return dirs


def _find_ftdata(dat_filepath, character):
    """Locate the fighter ftData (Pl<XX>.dat) for a costume model dat: a sibling
    Pl<XX>.dat next to the model, else the vanilla copy in test-base/files."""
    p = Path(dat_filepath)
    stem = p.stem
    if len(stem) >= 6 and stem.startswith('Pl'):
        cand = p.parent / f"{stem[:4]}.dat"
        if cand.exists() and cand.resolve() != p.resolve():
            return cand
    code = _resolve_char_code(character)
    if code:
        for base in _test_base_files_dirs():
            vb = base / f"Pl{code}.dat"
            if vb.exists():
                return vb
    return None


# Vanilla CSS costume color order is authoritative for mapping a costume's color
# to its slot index (slot 0 = default). Pulled from core.constants so there's one
# source of truth; the embedded fallback covers exactly the fighters whose ALT
# costumes use a different visibility config (so the fix still works if the
# import ever fails -- everyone else has a single config and the slot is moot).
_COLOR_ORDER_CACHE = None
_FALLBACK_COLOR_ORDER = {
    'Pikachu': ['Nr', 'Re', 'Bu', 'Gr'],
    'Pichu':   ['Nr', 'Re', 'Bu', 'Gr'],
    'Peach':   ['Nr', 'Ye', 'Wh', 'Bu', 'Gr'],
}


def _vanilla_color_order(character):
    """Ordered list of color codes for a character's vanilla costumes, or None."""
    global _COLOR_ORDER_CACHE
    if _COLOR_ORDER_CACHE is None:
        order = None
        for attempt in (1, 2):
            try:
                from core.constants import VANILLA_CSS_COLOR_ORDER
                order = dict(VANILLA_CSS_COLOR_ORDER)
                break
            except Exception as e:
                if attempt == 1:
                    backend = str(SCRIPT_DIR.parents[2] / "backend")
                    if backend not in sys.path:
                        sys.path.insert(0, backend)
                    continue
                logger.info(f"vanilla color order: using fallback ({e})")
        _COLOR_ORDER_CACHE = order or dict(_FALLBACK_COLOR_ORDER)
    return _COLOR_ORDER_CACHE.get(character)


def costume_slot_for_color(character, color):
    """Vanilla CSS slot index (0 = default) for a costume color NAME (e.g.
    'Blue'), or 0 when unknown. Only fighters whose alt costumes add geometry
    (Pikachu/Pichu/Peach) actually depend on this; for everyone else every slot
    maps to the same single visibility config."""
    order = _vanilla_color_order(character)
    code = COLOR_CODES.get(color)
    if order and code and code in order:
        return order.index(code)
    return 0


def _low_poly_set(dat_filepath, character, costume_slot=0):
    """Set of LowPoly DObj indices to hide for the costume in `costume_slot`, or
    None if the fighter's visibility table can't be read.

    Melee stores a PER-COSTUME visibility table at ftData+0x08
    (`SBM_PlayerModelLookupTables`): an int Count followed by an array of
    `SBM_CostumeLookupTable` entries (0x10 bytes EACH), whose LowPoly accessor is
    at +0x04. The costume's config index is min(costume_slot, Count-1) -- the
    engine clamps the costume's VisibilityLookupIndex to the table length, so e.g.
    Pikachu has 4 costumes but only 2 configs and its hat costumes all use config
    1. Vanilla also leaves higher configs null when only one costume needs the
    extra geometry (Peach: only Daisy uses config 1, the rest reuse config 0); a
    null config means "reuse config 0"."""
    ft_dat = _find_ftdata(dat_filepath, character)
    if not ft_dat:
        logger.info(f"low-poly hide: no ftData found for {character}")
        return None
    try:
        backend = str(SCRIPT_DIR.parents[2] / "backend")
        if backend not in sys.path:
            sys.path.insert(0, backend)
        from skinlab.datprobe import DatFile

        d = DatFile(str(ft_dat))
        ft = next(o for n, o in d.roots if n.startswith('ftData'))
        lookups = d.ptr(ft + 0x08)
        if lookups is None:
            return None

        def rptr(off):
            # a pointer only if the field is itself relocated (vanilla dats pad
            # the lookup arrays with non-pointer garbage words)
            return d.u32(off) if off in d.relocs else None

        length = d.u32(lookups + 0x00)
        vis_arr = rptr(lookups + 0x04)
        if vis_arr is None or length < 1:
            return None

        def low_set(config):
            # SBM_CostumeLookupTable stride 0x10; LowPoly table at +0x04.
            table = rptr(vis_arr + config * 0x10 + 0x04)
            if table is None:
                return None
            count = d.u32(table + 0x00)
            arr = rptr(table + 0x04)
            if arr is None or count > 64:
                return None
            idx = set()
            for i in range(count):
                le = arr + i * 0x8
                n = d.u32(le + 0x00)
                data = rptr(le + 0x04)
                if data is not None and n <= 256:
                    idx.update(d.raw[0x20 + data:0x20 + data + n])
            return idx

        config = min(max(costume_slot, 0), length - 1)
        idx = low_set(config)
        if idx is None and config != 0:
            idx = low_set(0)            # null config -> reuse costume 0
        if not idx:
            return None
        logger.info(f"low-poly hide for {character} ({Path(ft_dat).name}) "
                    f"slot {costume_slot}->cfg {config}: {sorted(idx)}")
        return idx
    except Exception as e:
        logger.info(f"low-poly hide: derive failed for {character}: {e}")
        return None


def low_poly_dobjs(dat_filepath, character, costume_slot=0):
    """Comma-joined LowPoly DObj indices to hide for the costume in `costume_slot`
    (slot 0 = default), or None if the visibility table can't be read (then the
    caller falls back to whatever hiddenNodes the scene carries)."""
    idx = _low_poly_set(dat_filepath, character, costume_slot)
    if not idx:
        return None
    return ",".join(str(i) for i in sorted(idx))


def _scene_hidden_nodes(yml_path):
    """Parse the `hiddenNodes:` DObj-index list out of a curated CSP scene/pose
    YAML (same block Program.cs reads), or None if it can't be read."""
    try:
        nodes = set()
        parsing = False
        with open(yml_path, encoding='utf-8', errors='replace') as f:
            for line in f:
                s = line.rstrip('\n')
                if s.startswith('hiddenNodes:'):
                    parsing = True
                    continue
                if parsing:
                    m = re.match(r'\s*-\s*(\d+)\s*$', s)
                    if m:
                        nodes.add(int(m.group(1)))
                    elif s and not s[0].isspace():
                        break
        return nodes
    except Exception:
        return None


def curated_hide_override(dat_filepath, character, costume_slot, scene_yml):
    """For a curated-scene costume, return the `--hide-dobjs` CSV that swaps the
    costume-0 LowPoly set baked into the scene's `hiddenNodes` for the costume's
    OWN visibility-config LowPoly set, while KEEPING any extra curated hides the
    scene author added (e.g. Peach's parasol/dress parts that aren't in the
    visibility table). Returns None when nothing needs to change -- the default
    costume, a single-config fighter, an alt that reuses config 0, or an
    unreadable table -- so the scene's own hiddenNodes are used unchanged (no
    regression)."""
    slot_low = _low_poly_set(dat_filepath, character, costume_slot)
    base_low = _low_poly_set(dat_filepath, character, 0)
    if not slot_low or not base_low or slot_low == base_low:
        return None
    yml_hidden = _scene_hidden_nodes(scene_yml) if scene_yml else None
    extras = (yml_hidden - base_low) if yml_hidden else set()
    final = sorted(slot_low | extras)
    logger.info(f"curated hide override for {character} slot {costume_slot}: "
                f"{final}")
    return ",".join(str(i) for i in final)


# --------------------------------------------------------------------------- #
# Replaced-model detection (suppress low-poly hiding for full model imports)   #
# --------------------------------------------------------------------------- #
# Low-poly hiding -- whether from the scene's baked hiddenNodes or the ftData
# visibility table -- is a list of DObj INDICES into the fighter's stock model.
# A recolor reuses that model, so the indices still point at the off-screen
# magnifier/LowPoly mesh. A full model import (Sonic over Mario, Rayman, Sans...)
# swaps in geometry with a DIFFERENT DObj layout, so those same indices land on
# real visible parts -- e.g. Sonic-over-Mario hides DObjs 37-52, which in Mario
# are the LowPoly body but in Sonic are the EYES (the costume only looked fine
# in-game because the engine hides that set only in the magnifier/far view).
#
# Detect it by comparing the costume's body-model DObj count to the counts of
# the fighter's vanilla color costumes. A recolor (any slot, incl. alt-geometry
# ones like Peach's Daisy or Pikachu's hats) matches one of those counts; a
# replaced model matches none. When replaced, pass `--hide-dobjs none` so the
# renderer drops the (now-wrong) hide entirely -- nothing valid to hide, and
# hiding does active harm. Any read failure -> not flagged (no behavior change).
def _body_root_offset(d):
    """Offset of the costume's main body JOBJ root (the *_Share_joint the
    renderer selects), skipping matanim/shapeanim roots. None if absent."""
    roots = [(nm, o) for nm, o in d.roots if nm.endswith('_joint')
             and 'matanim' not in nm and 'shapeanim' not in nm]
    if not roots:
        return None
    for nm, o in roots:
        if 'Share_joint' in nm:
            return o
    return roots[0][1]


def _model_dobj_count(dat_path):
    """Global render DObj count of a costume's body model -- matches
    RenderJObj.DObjCount: walk the JOBJ tree (child @0x08 / next @0x0C) and sum
    each JOBJ's DObj chain (linked by next @0x04). Returns None if unreadable.

    NOTE: count every JOBJ's DObjs -- do NOT skip SPLINE/PTCL-flagged JOBJs; the
    renderer counts those too, and some imports park real geometry under them
    (Sonic's extra 15 DObjs), which is exactly the layout change we detect."""
    try:
        backend = str(SCRIPT_DIR.parents[2] / "backend")
        if backend not in sys.path:
            sys.path.insert(0, backend)
        from skinlab.datprobe import DatFile

        d = DatFile(str(dat_path))
        root = _body_root_offset(d)
        if root is None:
            return None
        seen = set()
        stack = [root]
        total = 0
        while stack:
            node = stack.pop()
            if node is None or node in seen:
                continue
            seen.add(node)
            stack.append(d.ptr(node + 0x0C))   # next sibling
            stack.append(d.ptr(node + 0x08))   # first child
            dobj = d.ptr(node + 0x10)
            dseen = set()
            while dobj is not None and dobj not in dseen:
                dseen.add(dobj)
                total += 1
                dobj = d.ptr(dobj + 0x04)
        return total
    except Exception as e:
        logger.info(f"dobj count failed for {Path(dat_path).name}: {e}")
        return None


_VANILLA_DOBJ_COUNTS = {}


def _vanilla_dobj_counts(character):
    """Set of body-model DObj counts across this fighter's vanilla color
    costumes (Pl<code><cc>.dat in test-base/files), cached per character. A
    costume whose count matches none of these has a replaced model. Empty set
    (no vanilla costumes found) disables the check for that fighter."""
    if character in _VANILLA_DOBJ_COUNTS:
        return _VANILLA_DOBJ_COUNTS[character]
    counts = set()
    code = _resolve_char_code(character)
    if code:
        for base in _test_base_files_dirs():
            hits = sorted(base.glob(f"Pl{code}??.dat"))
            for p in hits:
                c = _model_dobj_count(p)   # AJ/anim files have no body root -> None
                if c:
                    counts.add(c)
            if counts:
                break
    _VANILLA_DOBJ_COUNTS[character] = counts
    return counts


def model_is_replacement(dat_filepath, character):
    """True when the costume swaps in a model whose DObj layout differs from
    every vanilla color costume of this fighter (a full import, not a recolor),
    so the fighter's low-poly DObj indices no longer line up. Conservative: any
    failure or no vanilla reference -> False (keep existing hide behavior)."""
    van = _vanilla_dobj_counts(character)
    if not van:
        return False
    cnt = _model_dobj_count(dat_filepath)
    if cnt is None:
        return False
    return cnt not in van


# --------------------------------------------------------------------------- #
# Deformed-skeleton detection (render such costumes at their own bind pose)    #
# --------------------------------------------------------------------------- #
# A normal recolor/reskin -- even a full model import (Rayman, Sans) -- reuses
# the fighter's vanilla skeleton with byte-identical bind transforms, because
# the shared fighter animations require it. A handful of "joke" costumes instead
# EDIT the bind transforms (stretched / displaced bones) while keeping the same
# bone COUNT. Under the curated CSP pose those edits are invisible: the pose's
# per-bone tracks overwrite the costume's own rotation/scale/translation
# (LiveJObj.ApplyAnimation resets to the costume's SRT then applies each track),
# so the portrait looks like a clean vanilla pose and HIDES the custom rig.
# Detect that case by comparing the costume's per-bone bind transforms against
# the vanilla skeleton; when it deviates, pass --bind-pose so HSDRawViewer
# renders the costume's OWN rig (keeping the scene camera + low-poly hide).
#
# Two things make a NAIVE comparison false-positive on normal costumes, so we
# guard against both (verified against all ~1600 vault costumes -> only the
# joke rigs flag):
#   * Rotation must be compared as a MATRIX, not raw RX/RY/RZ: HSDRaw re-export
#     canonicalizes Euler angles via the double-cover (x,y,z)==(x+pi, pi-y, z+pi),
#     so a re-exported costume's raw components differ by ~pi from the raw-ISO
#     vanilla while the actual orientation is identical.
#   * Vanilla color SLOTS aren't byte-identical skeletons (Captain Falcon slots
#     differ by ~0.2 translation, Pikachu's by ~0.19 scale), so thresholds sit
#     well above that per-slot variation. The joke rigs deviate by whole units
#     (4-7 translation, 1.0 scale), an order of magnitude clear of the noise.
# Any detection failure returns False -> normal posed render (no regression).

# JOBJ bind-transform field offsets (HSD_JOBJ): R @0x14, S @0x20, T @0x2C.
_SRT_OFFSETS = (0x14, 0x18, 0x1C, 0x20, 0x24, 0x28, 0x2C, 0x30, 0x34)
# Deviation thresholds: rotation = max abs element of (Rmtx_a - Rmtx_b); scale
# and translation = max abs component delta. Above vanilla per-slot variation
# (<=0.033 rotMtx / 0.19 scale / 0.21 trans), below the joke rigs (>=1.0).
_ROT_EPS, _SCALE_EPS, _TRANS_EPS = 0.3, 0.5, 1.0


def _euler_rot_matrix(rx, ry, rz):
    """3x3 rotation matrix (Rz*Ry*Rx) for an Euler triple, as nested tuples.
    Comparing matrices instead of raw angles makes the deviation check immune to
    the Euler double-cover re-encoding HSDRaw applies on re-export."""
    import math
    cx, cy, cz = math.cos(rx), math.cos(ry), math.cos(rz)
    sx, sy, sz = math.sin(rx), math.sin(ry), math.sin(rz)
    return (
        (cz*cy, cz*sy*sx - sz*cx, cz*sy*cx + sz*sx),
        (sz*cy, sz*sy*sx + cz*cx, sz*sy*cx - cz*sx),
        (-sy,   cy*sx,            cy*cx),
    )


def _bind_srt_list(dat_path):
    """Depth-first per-bone (RX,RY,RZ,SX,SY,SZ,TX,TY,TZ) of the body JOBJ root,
    or None. Reuses the skinlab DAT reader (same one low-poly hiding uses)."""
    import struct
    try:
        backend = str(SCRIPT_DIR.parents[2] / "backend")
        if backend not in sys.path:
            sys.path.insert(0, backend)
        from skinlab.datprobe import DatFile, HEADER_SIZE

        d = DatFile(str(dat_path))
        roots = [(n, o) for n, o in d.roots if n.endswith('_joint')
                 and 'matanim' not in n and 'shapeanim' not in n]
        if not roots:
            return None
        # match the body root Program.cs selects for the render (Share_joint)
        root = next((o for n, o in roots if 'Share_joint' in n), roots[0][1])
        out = []
        for b in d._iter_tree(root, 0x08, 0x0C):   # JOBJ child @0x08, next @0x0C
            out.append(tuple(
                struct.unpack_from('>f', d.raw, HEADER_SIZE + b + off)[0]
                for off in _SRT_OFFSETS))
        return out
    except Exception as e:
        logger.info(f"bind-srt read failed for {Path(dat_path).name}: {e}")
        return None


def _vanilla_skeleton_ref(character):
    """A vanilla costume DAT for this character (the skeleton is identical across
    every color slot), used as the bind-pose reference. None if unavailable."""
    code = _resolve_char_code(character)
    if not code:
        return None
    slots = ['Nr', 'Re', 'Bu', 'Gr', 'Ye', 'Wh', 'Bk', 'Aq', 'Pi', 'La', 'Gy', 'Or']
    for base in _test_base_files_dirs():
        for slot in slots:
            p = base / f"Pl{code}{slot}.dat"
            if p.exists():
                return p
    return None


def skeleton_is_deformed(dat_filepath, character):
    """True when the costume's bind transforms deviate from the vanilla skeleton
    (same bone count, edited SRT) -- a deliberately deformed 'joke' rig that the
    curated CSP pose would otherwise hide. Any failure returns False so the
    normal posed render is used (no regression)."""
    ref = _vanilla_skeleton_ref(character)
    if not ref:
        return False
    van = _bind_srt_list(ref)
    cos = _bind_srt_list(dat_filepath)
    if not van or not cos or len(van) != len(cos):
        return False
    for a, b in zip(van, cos):
        ra = _euler_rot_matrix(a[0], a[1], a[2])
        rb = _euler_rot_matrix(b[0], b[1], b[2])
        rot = max(abs(ra[i][j] - rb[i][j]) for i in range(3) for j in range(3))
        scl = max(abs(a[i] - b[i]) for i in range(3, 6))
        trn = max(abs(a[i] - b[i]) for i in range(6, 9))
        if rot > _ROT_EPS or scl > _SCALE_EPS or trn > _TRANS_EPS:
            logger.info(
                f"deformed skeleton detected for {Path(dat_filepath).name} "
                f"({character}) -> rendering CSP at bind pose")
            return True
    return False


# Fox's blaster, rendered as the real 3D article model (from PlFx.dat) attached
# to the right-hand bone, replacing the old flat gunlayer.png composite. The
# orientation/offset were calibrated against the vanilla CSP with the interactive
# aligner; they're camera/world-space, so scale-independent (verified scale 1 == 4).
FOX_GUN = {
    "bone": "68",
    "view": "47,-47,-114",
    "offset": "-0.15,-0.8,0.05",
    "scale": "0.85",
}


def _fox_gun_args():
    """`--gun ...` CLI args that render Fox's 3D blaster, or [] if PlFx.dat is
    missing (then the portrait just renders without a gun rather than failing)."""
    def _winpath(p):
        return p.replace('/mnt/c/', 'C:\\').replace('/', '\\') if p.startswith('/mnt/c/') else p
    for d in _test_base_files_dirs():
        plfx = Path(d) / "PlFx.dat"
        if plfx.exists():
            return ["--gun", _winpath(str(plfx.resolve())),
                    "--gun-bone", FOX_GUN["bone"],
                    "--gun-view", FOX_GUN["view"],
                    "--gun-offset", FOX_GUN["offset"],
                    "--gun-scale", FOX_GUN["scale"]]
    logger.warning("Fox gun: PlFx.dat not found in test-base/files; rendering CSP without the 3D gun")
    return []


def generate_single_csp_internal(dat_filepath, character, anim_file=None, camera_file=None, scale=1, no_shadow=False, costume_slot=None):
    """Internal function to generate a single CSP

    Used by both normal CSP generation and Ice Climbers composite generation.
    Returns the path to the generated CSP or None if failed.

    Args:
        dat_filepath: Path to the DAT file
        character: Character name
        anim_file: Optional animation file
        camera_file: Optional camera/scene YAML file
        scale: Resolution multiplier (1=136x188, 2=272x376, 4=544x752, etc.)
        costume_slot: Vanilla CSS slot index of this costume. Picks the
            per-costume low-poly visibility config; color slots that add or move
            geometry (Pichu's 4 configs, Pikachu hats, Peach's Daisy) need a
            different set. Leave None (the default) to AUTO-DERIVE it from the
            DAT's own detected color -- so callers that don't already know the
            slot (Retake CSP, Manage CSPs/Poses, pose re-render) still get the
            right config instead of silently falling back to slot 0.
    """
    # Generate output filename
    dat_dir = os.path.dirname(os.path.abspath(dat_filepath))
    dat_name = os.path.splitext(os.path.basename(dat_filepath))[0]
    # Add _hd suffix for scaled versions
    suffix = "_csp_hd.png" if scale > 1 else "_csp.png"
    output_csp = os.path.join(dat_dir, f"{dat_name}{suffix}")

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

    # Add scale argument if not 1x
    if scale > 1:
        cmd.extend(["--scale", str(scale)])

    if no_shadow:
        cmd.append("--no-shadow")

    # Project the head bone so stock generation can crop swapped-in models.
    # The renderer writes <output>.head.json next to the CSP.
    head_bone = CHARACTER_HEAD_BONES.get(character)
    if head_bone is not None:
        cmd.extend(["--head-bone", str(head_bone)])

    # Resolve the per-color low-poly visibility config. The canonical generate_csp
    # passes costume_slot explicitly; the Retake CSP / Manage CSPs / pose-render
    # paths call here directly and leave it None -- derive it from the DAT's own
    # color exactly like generate_csp does. (Defaulting to slot 0 here was the bug
    # behind "low-poly cheeks show on some skins": a non-default-color Pichu
    # re-rendered via those paths hid costume-0's dobjs -- the wrong indices for
    # its slot -- so its real low-poly cheek mesh leaked into the portrait.)
    if costume_slot is None:
        try:
            cs_parser = DATParser(dat_filepath)
            cs_parser.read_dat()
            costume_slot = costume_slot_for_color(
                character, cs_parser.detect_costume_color())
        except Exception as e:
            logger.info(f"costume_slot auto-derive failed for "
                        f"{Path(dat_filepath).name}: {e}")
            costume_slot = 0

    # Hiding the off-screen low-poly mesh.
    #
    # A character rendered with its OWN curated CSP scene/camera yml carries
    # hand-authored hiddenNodes (e.g. Kirby's copy-ability meshes, Peach's alt
    # parts). Those are baked from COSTUME 0's low-poly set, so they over/under-
    # hide on ALT costumes that use a different per-costume visibility config
    # (Pikachu/Pichu hats, Peach's Daisy). curated_hide_override() swaps in the
    # costume's OWN config low set while preserving the curated extras; it returns
    # None (-> keep the scene's hiddenNodes unchanged) for the default costume,
    # single-config fighters, and alts that reuse config 0, so the common path is
    # byte-identical to before.
    #
    # Without a curated yml (custom / model imports) or with a BORROWED scene
    # (Giga Bowser poses with Bowser's scene, whose hiddenNodes are wrong for the
    # Giga model) we apply the auto-derived per-costume low set directly.
    #
    # BUT a full model import (Sonic over Mario) replaces the geometry, so NO
    # index list -- baked or ftData-derived -- maps to its layout: hiding the
    # fighter's low-poly indices removes real visible parts (Sonic's eyes).
    # Detect the replaced model and pass `--hide-dobjs none` so the renderer
    # drops all hiding (including the scene's baked hiddenNodes) for it.
    # CSP_DISABLE_REPLACEMENT_FIX=1 reverts to the old behavior (escape hatch).
    if (os.environ.get('CSP_DISABLE_REPLACEMENT_FIX') != '1'
            and model_is_replacement(dat_filepath, character)):
        cmd.extend(["--hide-dobjs", "none"])
        logger.info(f"replaced model for {Path(dat_filepath).name} ({character}): "
                    f"suppressing low-poly hide (--hide-dobjs none)")
    else:
        has_curated_scene = bool(anim_file or camera_file) and character not in SCENE_BORROWERS
        if has_curated_scene:
            hide = curated_hide_override(dat_filepath, character, costume_slot,
                                         camera_file or anim_file)
        else:
            hide = low_poly_dobjs(dat_filepath, character, costume_slot)
        if hide:
            cmd.extend(["--hide-dobjs", hide])

    # Fox: render the real 3D blaster attached to his hand (replaces the old 2D
    # gunlayer.png composite). The renderer pulls the gun model from PlFx.dat and
    # pins it to the thumb bone; params are scale-independent (see FOX_GUN).
    if character == 'Fox':
        cmd.extend(_fox_gun_args())

    # Costumes with a deliberately deformed skeleton (edited bind transforms)
    # render normal under the curated pose because it overwrites their bone
    # transforms. Detect that and render the costume's OWN bind pose instead so
    # the custom rig shows (the scene camera + low-poly hide are still applied).
    if skeleton_is_deformed(dat_filepath, character):
        cmd.append("--bind-pose")

    if anim_file:
        cmd.append(to_windows_path(anim_file))

    if camera_file:
        cmd.append(to_windows_path(camera_file))

    logger.info(f"Running HSDRawViewer for {Path(dat_filepath).name}")
    logger.info(f"Command: {' '.join(cmd)}")

    # Run HSDRawViewer CSP generation.
    # IMPORTANT: HSDRawViewer.Program.Main opens a relative-path file
    # `csp_debug.log` for exclusive write at startup. If two instances share a
    # cwd they collide and the loser crashes before doing any work — that's
    # the "no_output / return code 3762504530" pattern that shows up under
    # iso_scanner's parallel ThreadPoolExecutor. Force the cwd to the DAT's
    # own folder so each parallel call isolates its debug log.
    try:
        # Run directly without PowerShell to avoid path quoting issues
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(dat_filepath)),
            **get_windows_subprocess_args(),
        )

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

def generate_ice_climbers_composite_csp(popo_dat, nana_dat, scale=1):
    """Generate composite CSP for Ice Climbers (Popo + Nana)

    Args:
        popo_dat: Path to Popo .dat file
        nana_dat: Path to Nana .dat file
        scale: Resolution multiplier (1=136x188, 4=544x752). Both climber layers
            are rendered at this scale before compositing, so the composite is HD
            when scale>1 (the texture-pack/bundle HD path needs this).

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
    nana_csp = generate_single_csp_internal(nana_dat, 'Ice Climbers', nana_yml, None, scale)
    if not nana_csp:
        logger.error("Failed to generate Nana CSP")
        return None

    # Generate Popo CSP (foreground, no shadow) - YML in anim_file slot for scene mode
    logger.info("Generating Popo CSP (foreground layer, no shadow)")
    popo_csp = generate_single_csp_internal(popo_dat, 'Ice Climbers', popo_yml, None, scale, no_shadow=True)
    if not popo_csp:
        logger.error("Failed to generate Popo CSP")
        return None

    # Composite them - Popo over Nana (both at the requested scale)
    popo_dat_name = os.path.splitext(os.path.basename(popo_dat))[0]
    output_dir = os.path.dirname(popo_csp)
    suffix = "_csp_hd.png" if scale > 1 else "_csp.png"
    final_csp = os.path.join(output_dir, f"{popo_dat_name}{suffix}")

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

def generate_head_shot(dat_filepath):
    """Render a bind-pose, auto-framed, shadowless 'head shot' of a costume
    DAT plus the projected head-bone sidecar. Stock-icon generation crops the
    head of MODEL IMPORTS from this render: unlike the CSP action poses, the
    bind pose is consistent and can never put the head out of frame.

    Returns (png_path, head_info_dict) or (None, None).
    """
    parser = DATParser(dat_filepath)
    try:
        parser.read_dat()
        character, _symbol = parser.detect_character()
        color = parser.detect_costume_color()
    except Exception as e:
        logger.error(f"Head shot: failed to parse DAT: {e}")
        return None, None
    head_bone = CHARACTER_HEAD_BONES.get(character)
    if head_bone is None:
        logger.warning(f"Head shot: no head bone known for {character}")
        return None, None

    dat_dir = os.path.dirname(os.path.abspath(dat_filepath))
    dat_name = os.path.splitext(os.path.basename(dat_filepath))[0]
    output = os.path.join(dat_dir, f"{dat_name}_headshot.png")

    # scale 2 = 272x376: crop decisions get real pixel detail to work with;
    # the icon is downscaled at the very end anyway
    cmd = [HSDRAW_EXE, "--csp", os.path.abspath(dat_filepath), output,
           "--head-shot", "--scale", "2", "--head-bone", str(head_bone)]
    arm_bones = CHARACTER_ARM_BONES.get(character)
    if arm_bones:
        cmd.extend(["--collapse-bones", f"{arm_bones[0]},{arm_bones[1]}"])
    # Hide the low-poly mesh so it can't bleed into the head crop (the head-shot
    # has no scene yml, so this is the only way to hide it here). Use the
    # costume's own per-costume visibility config (slot from its color).
    hide = low_poly_dobjs(dat_filepath, character, costume_slot_for_color(character, color))
    if hide:
        cmd.extend(["--hide-dobjs", hide])
    if os.name != 'nt':
        cmd.insert(0, "wine")

    logger.info(f"Rendering head shot for {Path(dat_filepath).name} ({character})")
    result = None
    for attempt in (1, 2):   # transient GL/context crashes happen; retry once
        try:
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    cwd=dat_dir, **get_windows_subprocess_args())
        except Exception as e:
            logger.error(f"Head shot render error: {e}")
            return None, None
        if result.returncode == 0 and os.path.exists(output):
            break
        logger.warning(f"Head shot render attempt {attempt} failed "
                       f"(rc={result.returncode})")
    if result is None or result.returncode != 0 or not os.path.exists(output):
        logger.error("Head shot render failed")
        return None, None

    head_info = None
    head_json = output + '.head.json'
    if os.path.exists(head_json):
        try:
            import json
            with open(head_json) as f:
                head_info = json.load(f)
        except Exception:
            head_info = None
        try:
            os.unlink(head_json)
        except:
            pass
    return output, head_info


def generate_csp(dat_filepath, scale=1, paired_dat_filepath=None):
    """
    Generate CSP for a DAT file using HSDRawViewer headless CSP generation
    Returns path to generated CSP or None if failed

    Args:
        dat_filepath: Path to the DAT file
        scale: Resolution multiplier (1=136x188, 2=272x376, 4=544x752, etc.)
        paired_dat_filepath: Optional explicit Ice Climbers partner DAT.
    """

    logger.info(f"Starting CSP generation for: {dat_filepath} (scale={scale}x)")

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
        char_type, pair_file, popo_color, nana_color = find_ice_climbers_pair(
            dat_filepath,
            explicit_pair_filepath=paired_dat_filepath,
        )

        if char_type == 'nana':
            # Nana files are composited with Popo, skip individual generation
            logger.info(f"Skipping Nana {nana_color} - will be composited with Popo {popo_color}")
            return None
        elif char_type == 'popo' and pair_file:
            # Found a matching pair - generate composite CSP (at the requested scale)
            logger.info(f"Processing Ice Climbers pair: Popo {popo_color} + Nana {nana_color}")
            return generate_ice_climbers_composite_csp(dat_filepath, pair_file, scale)
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

    # 3. Generate CSP using internal function. The costume's vanilla CSS slot
    # selects its per-costume low-poly visibility config (matters for alt
    # costumes that add geometry -- Pikachu/Pichu hats, Peach's Daisy).
    costume_slot = costume_slot_for_color(character, color)
    output_csp = generate_single_csp_internal(dat_filepath, character, anim_file, camera_file, scale, costume_slot=costume_slot)

    if output_csp:
        # Apply character-specific layers (e.g., Fox gun layer)
        layer_applied = apply_character_specific_layers(output_csp, character, scale)
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
