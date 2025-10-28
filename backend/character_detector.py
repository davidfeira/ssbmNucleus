"""
Character Detector - Detects character and costume info from DAT files
"""
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Tuple, List
import zipfile

# Try to import py7zr for 7z support
try:
    import py7zr
    HAS_7Z_SUPPORT = True
except ImportError:
    HAS_7Z_SUPPORT = False

# Add utility scripts to path
SCRIPT_DIR = Path(__file__).parent.parent
UTILITY_DIR = SCRIPT_DIR / "utility" / "website" / "backend" / "tools" / "processor"
sys.path.insert(0, str(UTILITY_DIR))

try:
    from detect_character import DATParser
except ImportError:
    print(f"Warning: Could not import DATParser from {UTILITY_DIR}")
    DATParser = None


def build_image_indexes(filenames: list) -> tuple:
    """
    Build dual indexes for CSPs and stocks from ZIP file list.

    Args:
        filenames: List of all filenames in ZIP

    Returns:
        Tuple of (csps_by_name, csps_by_path, stocks_by_name, stocks_by_path)
        Each is a dict mapping to file info
    """
    csps_by_name = {}
    csps_by_path = {}
    stocks_by_name = {}
    stocks_by_path = {}

    image_extensions = {'.png', '.jpg', '.jpeg'}

    for filename in filenames:
        ext = os.path.splitext(filename)[1].lower()
        if ext not in image_extensions:
            continue

        basename = os.path.splitext(os.path.basename(filename))[0].lower()
        folder = os.path.dirname(filename)

        info = {
            'filename': filename,
            'folder': folder,
            'basename': basename
        }

        # Determine if CSP or stock by filename patterns
        basename_lower = basename.lower()
        if any(pattern in basename_lower for pattern in ['csp', 'portrait', 'icon']) and 'stock' not in basename_lower:
            csps_by_name[basename] = info
            csps_by_path[filename] = info
        elif any(pattern in basename_lower for pattern in ['stc', 'stock']):
            stocks_by_name[basename] = info
            stocks_by_path[filename] = info
        else:
            # Default: treat as potential CSP if no clear stock indicator
            csps_by_name[basename] = info
            csps_by_path[filename] = info

    return csps_by_name, csps_by_path, stocks_by_name, stocks_by_path


def detect_character_from_zip(zip_path: str) -> List[Dict]:
    """
    Detect character information from a ZIP/7z file containing character costumes.
    Now supports multiple DATs in one archive and 7z files.

    Args:
        zip_path: Path to the ZIP or 7z file

    Returns:
        List of dicts with character info. Empty list if none detected.
        Each dict contains:
        {
            'character': 'Fox',
            'color': 'Green',
            'costume_code': 'PlFxGr',
            'dat_file': 'PlFxGr.dat',
            'csp_file': 'csp.png' or None,
            'stock_file': 'stc.png' or None,
            'folder': 'green_fox/' or ''
        }
    """
    if not DATParser:
        print("DATParser not available")
        return []

    # Detect archive type
    is_7z = zip_path.lower().endswith('.7z')

    if is_7z and not HAS_7Z_SUPPORT:
        print("7z file provided but py7zr not installed")
        return []

    try:
        # Open appropriate archive type
        if is_7z:
            archive = py7zr.SevenZipFile(zip_path, 'r')
            filenames = archive.getnames()
        else:
            archive = zipfile.ZipFile(zip_path, 'r')
            filenames = archive.namelist()

        # Find ALL .dat files
        dat_files = [f for f in filenames if f.endswith('.dat')]
        if not dat_files:
            if not is_7z:
                archive.close()
            return []

        # Build dual indexes for smart matching
        csps_by_name, csps_by_path, stocks_by_name, stocks_by_path = build_image_indexes(filenames)

        results = []
        import tempfile

        # Process each DAT file
        for dat_filename in dat_files:
            # Extract DAT to temp location for parsing
            with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as tmp:
                # Read file data from appropriate archive type
                if is_7z:
                    file_data = archive.read([dat_filename])
                    tmp.write(file_data[dat_filename].read())
                else:
                    tmp.write(archive.read(dat_filename))
                tmp_path = tmp.name

            try:
                # Parse DAT file
                parser = DATParser(tmp_path)
                parser.read_dat()

                character, symbol = parser.detect_character()
                if not character:
                    continue

                # Check if it's a costume (has Ply symbol) vs data mod (only ftData)
                has_ply_symbol = any('Ply' in node['symbol'] for node in parser.root_nodes)
                if not has_ply_symbol:
                    # This is a data/effect mod, not a costume
                    continue

                color_info = parser.detect_costume_color()
                costume_code = parser.get_character_filename()

                # Get folder context for this DAT
                dat_folder = os.path.dirname(dat_filename)
                dat_basename = os.path.splitext(os.path.basename(dat_filename))[0].lower()

                # THREE-TIER MATCHING for CSP
                csp_file = None

                # Tier 1: Exact filename match
                if dat_basename in csps_by_name:
                    csp_file = csps_by_name[dat_basename]['filename']

                # Tier 2: Same-folder match
                if not csp_file:
                    # Count DATs in this folder
                    dats_in_folder = sum(1 for d in dat_files if os.path.dirname(d) == dat_folder)

                    if dats_in_folder == 1:
                        # Only 1 DAT in this folder - match any CSP from same folder
                        for csp_path, csp_info in csps_by_path.items():
                            if csp_info['folder'] == dat_folder:
                                csp_file = csp_info['filename']
                                break

                # Tier 3: Global fallback (single DAT in entire ZIP)
                if not csp_file and len(dat_files) == 1 and csps_by_path:
                    # Take first available CSP
                    csp_file = next(iter(csps_by_path.values()))['filename']

                # Same matching for stock
                stock_file = None
                if dat_basename in stocks_by_name:
                    stock_file = stocks_by_name[dat_basename]['filename']
                elif not stock_file and len(dat_files) == 1 and dats_in_folder == 1:
                    # Same-folder or global fallback for stocks
                    for stock_path, stock_info in stocks_by_path.items():
                        if stock_info['folder'] == dat_folder:
                            stock_file = stock_info['filename']
                            break

                # Normalize character name
                if character in ['Ice Climbers (Nana)', 'Ice Climbers (Popo)']:
                    character = 'Ice Climbers'

                results.append({
                    'character': character,
                    'color': color_info if color_info else 'Custom',
                    'costume_code': costume_code,
                    'dat_file': dat_filename,
                    'csp_file': csp_file,
                    'stock_file': stock_file,
                    'symbol': symbol,
                    'folder': dat_folder
                })

            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass

        # Close archive before returning
        if not is_7z:
            archive.close()

        return results

    except Exception as e:
        print(f"Error detecting character from {zip_path}: {e}")
        return []


def find_image_in_zip(filenames: list, preferred_names: list, exclude: list = None) -> Optional[str]:
    """
    Find an image file in the ZIP based on preferred names.

    Args:
        filenames: List of filenames in ZIP
        preferred_names: List of preferred name patterns (e.g., ['csp', 'portrait'])
        exclude: List of patterns to exclude

    Returns:
        Filename of matched image, or None
    """
    image_extensions = {'.png', '.jpg', '.jpeg'}
    exclude = exclude or []

    # First pass: Look for preferred names
    for filename in filenames:
        basename = os.path.basename(filename).lower()
        name_without_ext = os.path.splitext(basename)[0]
        ext = os.path.splitext(basename)[1].lower()

        if ext in image_extensions:
            # Check exclusions
            if any(excl.lower() in basename for excl in exclude):
                continue

            # Check preferred names
            for preferred in preferred_names:
                if preferred.lower() in basename:
                    return filename

    # Second pass: Return first image not in exclusions
    for filename in filenames:
        ext = os.path.splitext(filename)[1].lower()
        basename = os.path.basename(filename).lower()

        if ext in image_extensions:
            if not any(excl.lower() in basename for excl in exclude):
                return filename

    return None


def is_character_costume(dat_path: str) -> bool:
    """
    Check if a DAT file is a character costume (vs data/effect mod).

    Args:
        dat_path: Path to DAT file

    Returns:
        True if it's a character costume file
    """
    if not DATParser:
        return False

    try:
        parser = DATParser(dat_path)
        parser.read_dat()

        # Check for Ply symbols (character costumes have these)
        has_ply_symbol = any('Ply' in node['symbol'] for node in parser.root_nodes)
        return has_ply_symbol

    except:
        return False
