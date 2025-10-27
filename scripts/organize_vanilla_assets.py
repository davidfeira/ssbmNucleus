#!/usr/bin/env python3
"""
Organize Vanilla Assets Script

Copies all vanilla CSPs and stock icons from build/assets into an organized
structure in utility/assets, organized by character and color.

The organized structure will be:
utility/assets/vanilla/{character}/{costume_code}/csp.png
utility/assets/vanilla/{character}/{costume_code}/stock.png
"""

import json
import shutil
from pathlib import Path

# Directories
SCRIPT_DIR = Path(__file__).parent
FIGHTERS_DIR = SCRIPT_DIR / "build" / "data" / "fighters"
CSP_DIR = SCRIPT_DIR / "build" / "assets" / "csp"
ICONS_DIR = SCRIPT_DIR / "build" / "assets" / "icons"
OUTPUT_DIR = SCRIPT_DIR / "utility" / "assets" / "vanilla"

def main():
    print("="*60)
    print("Organizing Vanilla Melee Assets")
    print("="*60)
    print()

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Process each fighter JSON
    for json_file in sorted(FIGHTERS_DIR.glob("*.json")):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                fighter_data = json.load(f)

            character_name = fighter_data.get('name', 'Unknown')

            # Skip unknown characters
            if character_name == 'Unknown':
                continue

            print(f"Processing {character_name}...")

            # Create character directory
            char_dir = OUTPUT_DIR / character_name
            char_dir.mkdir(parents=True, exist_ok=True)

            # Process each costume
            costumes = fighter_data.get('costumes', [])
            for costume in costumes:
                # Get costume details
                file_info = costume.get('file', {})
                filename = file_info.get('fileName', '')

                if not filename:
                    continue

                # Extract costume code (e.g., PlFxNr -> PlFxNr)
                costume_code = filename.replace('.dat', '')

                # Get CSP and stock icon paths
                csp_path_str = costume.get('csp', '')
                icon_path_str = costume.get('icon', '')

                if not csp_path_str or not icon_path_str:
                    continue

                # Extract asset numbers (e.g., "csp\\csp_007" -> "007")
                csp_num = csp_path_str.split('_')[-1]
                icon_num = icon_path_str.split('_')[-1]

                # Source files
                csp_src = CSP_DIR / f"csp_{csp_num}.png"
                stock_src = ICONS_DIR / f"ft_{icon_num}.png"

                # Create costume directory
                costume_dir = char_dir / costume_code
                costume_dir.mkdir(parents=True, exist_ok=True)

                # Copy CSP
                if csp_src.exists():
                    csp_dst = costume_dir / "csp.png"
                    shutil.copy2(csp_src, csp_dst)
                    print(f"  + {costume_code}/csp.png")
                else:
                    print(f"  - {costume_code}/csp.png (source not found: {csp_src})")

                # Copy stock icon
                if stock_src.exists():
                    stock_dst = costume_dir / "stock.png"
                    shutil.copy2(stock_src, stock_dst)
                    print(f"  + {costume_code}/stock.png")
                else:
                    print(f"  - {costume_code}/stock.png (source not found: {stock_src})")

            print()

        except Exception as e:
            print(f"Error processing {json_file}: {e}")
            print()

    print("="*60)
    print(f"Vanilla assets organized in: {OUTPUT_DIR}")
    print("="*60)

if __name__ == "__main__":
    main()
