#!/usr/bin/env python3
"""
Costume Packaging Script
Packages loose DAT and CSP files into importable zip files with proper stock icons.

Usage: python scripts/migration/package_costumes.py <input_folder>
Example: python scripts/migration/package_costumes.py PlFxNr-sm4sh-fox
"""

import os
import sys
import json
import re
import zipfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Base paths
SCRIPT_DIR = Path(__file__).parent
FIGHTERS_DIR = SCRIPT_DIR / "build" / "data" / "fighters"
ASSETS_DIR = SCRIPT_DIR / "build" / "assets" / "icons"
FILES_DIR = SCRIPT_DIR / "build" / "files"


def build_character_mapping() -> Dict[str, Tuple[Path, str]]:
    """
    Scan all fighter JSON files and build a mapping of character prefixes to JSON files.

    Returns:
        Dict mapping character prefix (e.g., 'PlFx') to (json_path, character_name)
    """
    mapping = {}

    if not FIGHTERS_DIR.exists():
        print(f"Error: Fighters directory not found at {FIGHTERS_DIR}")
        return mapping

    for json_file in FIGHTERS_DIR.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Get character name and first costume to extract prefix
            char_name = data.get('name', 'Unknown')
            costumes = data.get('costumes', [])

            if costumes and 'file' in costumes[0]:
                filename = costumes[0]['file'].get('fileName', '')
                # Extract prefix (first 4 characters, e.g., 'PlFx', 'PlFc')
                if len(filename) >= 4:
                    prefix = filename[:4]
                    mapping[prefix] = (json_file, char_name)
                    print(f"Mapped {prefix} -> {char_name} ({json_file.name})")

        except Exception as e:
            print(f"Warning: Error reading {json_file}: {e}")

    return mapping


def extract_costume_code(filename: str) -> Optional[str]:
    """
    Extract costume code from filename.

    Examples:
        'PlFxGr sm4sh fox (green).dat' -> 'PlFxGr'
        'csp_PlFxgr sm4sh fox (green).png' -> 'PlFxGr'

    Returns:
        Costume code (e.g., 'PlFxGr') or None if not found
    """
    # Match PlXxYy pattern (case insensitive)
    match = re.search(r'(Pl[A-Za-z]{2}[A-Za-z]{2})', filename, re.IGNORECASE)
    if match:
        # Normalize to proper case (PlXxYy format)
        code = match.group(1)
        # Ensure first 4 chars are uppercase, last 2 are capitalized
        return code[:2] + code[2:4].capitalize() + code[4:].capitalize()
    return None


def find_matching_csp(costume_code: str, dat_filename: str, input_dir: Path) -> Optional[Path]:
    """
    Find CSP file matching the costume code and filename pattern.

    Args:
        costume_code: Costume code like 'PlFxGr'
        dat_filename: Original DAT filename for better matching
        input_dir: Directory to search in

    Returns:
        Path to matching CSP file or None
    """
    matches = []

    # Find all CSPs with matching costume code
    for file in input_dir.glob("*.png"):
        if file.name.lower().startswith("csp"):
            file_code = extract_costume_code(file.name)
            if file_code and file_code.lower() == costume_code.lower():
                matches.append(file)

    if not matches:
        return None

    if len(matches) == 1:
        return matches[0]

    # Multiple matches - try to find best match based on filename similarity
    # Extract descriptive parts from DAT filename (e.g., "(green)", "(black)")
    dat_desc = dat_filename.lower()

    for csp_file in matches:
        csp_desc = csp_file.name.lower()
        # Check if CSP filename contains similar descriptors
        # For exact match of base name (without descriptors), prioritize
        if dat_desc.replace('.dat', '').replace('_', ' ') in csp_desc.replace('.png', '').replace('_', ' '):
            return csp_file

    # If no perfect match, return the first one
    return matches[0]


def lookup_stock_icon(costume_code: str, json_path: Path) -> Optional[str]:
    """
    Look up stock icon path from character JSON.

    Args:
        costume_code: Costume code like 'PlFxGr'
        json_path: Path to character JSON file

    Returns:
        Stock icon filename (e.g., 'ft_010.png') or None
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Look for costume with matching fileName
        dat_filename = f"{costume_code}.dat"
        for costume in data.get('costumes', []):
            if 'file' in costume and costume['file'].get('fileName', '') == dat_filename:
                icon_path = costume.get('icon')
                if icon_path:
                    # Extract filename from path like "icons\\ft_010" or "icons/ft_010"
                    # Use os.path.basename for cross-platform compatibility
                    icon_name = os.path.basename(icon_path.replace('\\', '/'))
                    return f"{icon_name}.png"

        print(f"Warning: Could not find costume {dat_filename} in {json_path.name}")
        return None

    except Exception as e:
        print(f"Error looking up stock icon: {e}")
        return None


def generate_unique_dat_name(prefix: str, json_path: Path, used_names: set) -> str:
    """
    Generate a unique DAT filename that doesn't exist in build/files or character JSON.

    Args:
        prefix: Character prefix like 'PlFx'
        json_path: Path to character JSON file to check for existing costumes
        used_names: Set of names already used in this run

    Returns:
        Unique filename like 'PlFx4A.dat'
    """
    # Get existing files from build/files directory
    existing_files = set(f.name for f in FILES_DIR.glob("*.dat"))

    # Get existing costumes from character JSON
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for costume in data.get('costumes', []):
            if 'file' in costume:
                filename = costume['file'].get('fileName')
                if filename:
                    existing_files.add(filename)
    except Exception as e:
        print(f"  Warning: Could not read character JSON: {e}")

    # Combine with names used in this run
    existing_files.update(used_names)

    # Try pattern PlXx4YY where YY goes from A-Z, then AA-ZZ
    # Try single letters first (A-Z)
    for char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        name = f"{prefix}4{char}.dat"
        if name not in existing_files:
            return name

    # Try double letters (AA-ZZ)
    for char1 in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
        for char2 in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
            name = f"{prefix}4{char1}{char2}.dat"
            if name not in existing_files:
                return name

    # Fallback to timestamp-based name
    import time
    timestamp = int(time.time()) % 10000
    return f"{prefix}4X{timestamp}.dat"


def package_costume(dat_file: Path, csp_file: Path, stock_icon: Optional[Path],
                    output_dir: Path, new_dat_name: str) -> bool:
    """
    Package costume files into a zip.

    Args:
        dat_file: Original DAT file
        csp_file: CSP file
        stock_icon: Stock icon file (or None if not found)
        output_dir: Output directory for zip
        new_dat_name: New name for the DAT file

    Returns:
        True if successful
    """
    # Create descriptive zip name from original DAT filename
    base_name = dat_file.stem  # Remove .dat extension
    zip_name = f"{base_name}.zip"
    zip_path = output_dir / zip_name

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add DAT file with new name
            zf.write(dat_file, new_dat_name)

            # Add CSP as csp.png
            zf.write(csp_file, 'csp.png')

            # Add stock icon as stc.png if available
            if stock_icon and stock_icon.exists():
                zf.write(stock_icon, 'stc.png')
            else:
                print(f"  Warning: No stock icon found, zip will not include stc.png")

        print(f"  [OK] Created {zip_name}")
        return True

    except Exception as e:
        print(f"  [ERROR] Error creating zip: {e}")
        return False


def process_folder(input_folder: Path):
    """
    Process a folder containing DAT and CSP files.

    Args:
        input_folder: Path to folder with costume files
    """
    if not input_folder.exists():
        print(f"Error: Input folder not found: {input_folder}")
        return

    print(f"\n{'='*60}")
    print(f"Processing folder: {input_folder.name}")
    print(f"{'='*60}\n")

    # Build character mapping
    print("Building character mapping...")
    char_mapping = build_character_mapping()
    print(f"Found {len(char_mapping)} characters\n")

    if not char_mapping:
        print("Error: No character mappings found. Check that build/data/fighters/ exists.")
        return

    # Find all DAT files
    dat_files = list(input_folder.glob("*.dat"))
    if not dat_files:
        print(f"No DAT files found in {input_folder}")
        return

    print(f"Found {len(dat_files)} DAT file(s)\n")

    # Process each DAT file
    processed = 0
    skipped = 0
    used_names = set()  # Track DAT names used in this run

    for dat_file in dat_files:
        print(f"Processing: {dat_file.name}")

        # Extract costume code
        costume_code = extract_costume_code(dat_file.name)
        if not costume_code:
            print(f"  [SKIP] Could not extract costume code from filename")
            skipped += 1
            continue

        print(f"  Costume code: {costume_code}")

        # Get character prefix
        char_prefix = costume_code[:4]
        if char_prefix not in char_mapping:
            print(f"  [SKIP] Unknown character prefix: {char_prefix}")
            skipped += 1
            continue

        json_path, char_name = char_mapping[char_prefix]
        print(f"  Character: {char_name}")

        # Find matching CSP
        csp_file = find_matching_csp(costume_code, dat_file.name, input_folder)
        if not csp_file:
            print(f"  [SKIP] No matching CSP file found")
            skipped += 1
            continue

        print(f"  CSP: {csp_file.name}")

        # Look up stock icon
        stock_icon_name = lookup_stock_icon(costume_code, json_path)
        stock_icon_path = None
        if stock_icon_name:
            stock_icon_path = ASSETS_DIR / stock_icon_name
            if stock_icon_path.exists():
                print(f"  Stock: {stock_icon_name}")
            else:
                print(f"  Warning: Stock icon not found: {stock_icon_name}")
                stock_icon_path = None

        # Generate unique DAT name
        new_dat_name = generate_unique_dat_name(char_prefix, json_path, used_names)
        used_names.add(new_dat_name)  # Track this name as used
        print(f"  New DAT name: {new_dat_name}")

        # Package into zip
        if package_costume(dat_file, csp_file, stock_icon_path, input_folder, new_dat_name):
            processed += 1
        else:
            skipped += 1

        print()  # Blank line between entries

    # Summary
    print(f"{'='*60}")
    print(f"Summary: {processed} packaged, {skipped} skipped")
    print(f"{'='*60}\n")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/migration/package_costumes.py <input_folder>")
        print("Example: python scripts/migration/package_costumes.py PlFxNr-sm4sh-fox")
        sys.exit(1)

    input_folder = SCRIPT_DIR / sys.argv[1]
    process_folder(input_folder)


if __name__ == "__main__":
    main()
