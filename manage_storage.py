#!/usr/bin/env python3
"""
Costume Storage Management System

Processes DAT files from intake folder, detects character/color, finds or generates
CSP and stock icons, then packages into organized storage with metadata tracking.

Usage: python manage_storage.py [--dry-run]
"""

import os
import sys
import json
import zipfile
import shutil
import logging
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re

# Add utility scripts to path
SCRIPT_DIR = Path(__file__).parent
UTILITY_DIR = SCRIPT_DIR / "utility" / "website" / "backend" / "tools" / "processor"
sys.path.insert(0, str(UTILITY_DIR))

from detect_character import DATParser

# Directories
INTAKE_DIR = SCRIPT_DIR / "intake"
STORAGE_DIR = SCRIPT_DIR / "storage"
BUILD_ASSETS_DIR = SCRIPT_DIR / "build" / "assets" / "icons"
VANILLA_ASSETS_DIR = SCRIPT_DIR / "utility" / "assets" / "vanilla"
LOGS_DIR = SCRIPT_DIR / "logs"
METADATA_FILE = STORAGE_DIR / "metadata.json"
LOG_FILE = LOGS_DIR / "storage_manager.log"

# Character name normalization
CHARACTER_NAME_MAP = {
    'Ice Climbers (Nana)': 'Ice Climbers',
    'Ice Climbers (Popo)': 'Ice Climbers',
}

# Setup logging
def setup_logging():
    """Configure logging with both file and console output"""
    # Create logs directory if needed
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # File handler - captures everything
    file_handler = logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler - shows info and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    return logger

# Initialize logger
logger = setup_logging()


class StorageManager:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.metadata = self.load_metadata()

    def load_metadata(self) -> Dict:
        """Load master metadata file"""
        if METADATA_FILE.exists():
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "characters": {}
        }

    def save_metadata(self):
        """Save master metadata file"""
        if not self.dry_run:
            METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(METADATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2)

    def detect_character_from_dat(self, dat_path: Path) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Detect character, color, and costume code from DAT file.

        Returns:
            Tuple of (character_name, color, costume_code) or (None, None, None)
        """
        logger.debug(f"Detecting character from DAT: {dat_path}")

        try:
            parser = DATParser(str(dat_path))
            logger.debug(f"  Created DATParser for {dat_path.name}")

            parser.read_dat()
            logger.debug(f"  Successfully read DAT file")

            # Check if it's a character costume file
            is_costume = parser.is_character_costume()
            logger.debug(f"  is_character_costume() = {is_costume}")

            if not is_costume:
                logger.info(f"  [SKIP] Not a character costume file (no Ply symbols)")
                return None, None, None

            character, symbol = parser.detect_character()
            logger.debug(f"  detect_character() = {character}, symbol = {symbol}")

            color = parser.detect_costume_color()
            logger.debug(f"  detect_costume_color() = {color}")

            costume_code = parser.get_character_filename()
            logger.debug(f"  get_character_filename() = {costume_code}")

            if not character:
                logger.info(f"  [SKIP] Could not detect character")
                return None, None, None

            # Normalize character name
            original_character = character
            character = CHARACTER_NAME_MAP.get(character, character)
            if original_character != character:
                logger.debug(f"  Normalized character name: {original_character} -> {character}")

            logger.info(f"  Detected: {character} - {color} ({costume_code})")
            return character, color, costume_code

        except Exception as e:
            logger.error(f"  [ERROR] Failed to parse DAT: {e}")
            logger.debug(f"  Traceback:\n{traceback.format_exc()}")
            return None, None, None

    def find_matching_csp(self, dat_path: Path, costume_code: str, used_csps: set) -> Optional[Path]:
        """
        Find matching CSP file in intake folder.

        Uses filename similarity and descriptor matching to find best match.
        Avoids double-matching by tracking used CSPs.
        """
        logger.debug(f"Finding matching CSP for {dat_path.name} (costume_code={costume_code})")

        if not costume_code:
            logger.debug("  No costume code provided, cannot match CSP")
            return None

        dat_name = dat_path.stem.lower()  # e.g., "plfxor sm4sh fox (red)"
        logger.debug(f"  DAT stem: {dat_name}")

        # Find all candidate CSPs with matching costume code
        candidates = []
        all_pngs = list(INTAKE_DIR.glob("*.png"))
        logger.debug(f"  Found {len(all_pngs)} PNG files in intake")

        for file in all_pngs:
            if file in used_csps:
                logger.debug(f"    Skipping {file.name} (already matched)")
                continue  # Skip already matched CSPs

            if file.name.lower().startswith('csp'):
                # Check if costume code appears in filename (case insensitive)
                if costume_code.lower() in file.name.lower():
                    candidates.append(file)
                    logger.debug(f"    Candidate: {file.name}")

        logger.debug(f"  Found {len(candidates)} candidate CSPs")

        if not candidates:
            logger.debug("  No matching CSPs found")
            return None

        if len(candidates) == 1:
            logger.debug(f"  Single candidate found: {candidates[0].name}")
            return candidates[0]

        # Multiple candidates - find best match by filename similarity
        logger.debug("  Multiple candidates - scoring matches...")
        best_match = None
        best_score = 0

        # Extract descriptors from DAT filename (text in parentheses)
        dat_descriptors = re.findall(r'\(([^)]+)\)', dat_name)
        logger.debug(f"  DAT descriptors: {dat_descriptors}")

        for csp_file in candidates:
            csp_name = csp_file.stem.lower()
            score = 0

            # Check for matching descriptors
            csp_descriptors = re.findall(r'\(([^)]+)\)', csp_name)
            logger.debug(f"    {csp_file.name} descriptors: {csp_descriptors}")

            # Strong match if descriptors overlap
            for dat_desc in dat_descriptors:
                for csp_desc in csp_descriptors:
                    if dat_desc in csp_desc or csp_desc in dat_desc:
                        score += 10
                        logger.debug(f"      Descriptor match: '{dat_desc}' <-> '{csp_desc}' (+10)")

            # Check overall filename similarity (Levenshtein-like simple scoring)
            # Remove "csp_" prefix and ".png" suffix for comparison
            csp_base = csp_name.replace('csp_', '').replace('csp', '')

            # Count common words
            dat_words = set(dat_name.split())
            csp_words = set(csp_base.split())
            common_words = dat_words & csp_words
            score += len(common_words)
            logger.debug(f"      Common words: {common_words} (+{len(common_words)})")
            logger.debug(f"      Total score: {score}")

            if score > best_score:
                best_score = score
                best_match = csp_file

        result = best_match if best_score > 0 else candidates[0]
        logger.debug(f"  Best match: {result.name} (score={best_score})")
        return result

    def find_matching_stock(self, dat_path: Path, costume_code: str) -> Optional[Path]:
        """
        Find matching stock icon file in intake folder.

        Looks for small PNG files (stocks are typically 24x24)
        """
        if not costume_code:
            return None

        # Look for stock files with matching costume code
        for file in INTAKE_DIR.glob("*.png"):
            # Skip CSP files
            if file.name.lower().startswith('csp'):
                continue

            # Check if costume code appears in filename
            if costume_code.lower() in file.name.lower():
                # Verify it's a small image (stock icons are 24x24)
                try:
                    from PIL import Image
                    with Image.open(file) as img:
                        if img.size == (24, 24):
                            return file
                except:
                    pass

        return None

    def generate_csp(self, dat_path: Path, character: str) -> Optional[Path]:
        """
        Generate CSP from DAT file using utility scripts.

        Returns:
            Path to generated CSP or None if failed
        """
        logger.info(f"  Generating CSP from DAT...")
        logger.debug(f"    DAT file: {dat_path}")
        logger.debug(f"    Character: {character}")
        logger.debug(f"    UTILITY_DIR: {UTILITY_DIR}")

        try:
            # Check if utility directory exists
            if not UTILITY_DIR.exists():
                logger.error(f"    UTILITY_DIR does not exist: {UTILITY_DIR}")
                return None

            # Check for generate_csp module
            generate_csp_path = UTILITY_DIR / "generate_csp.py"
            logger.debug(f"    Looking for: {generate_csp_path}")
            logger.debug(f"    Exists: {generate_csp_path.exists()}")

            # Import the generation function
            sys.path.insert(0, str(UTILITY_DIR))
            logger.debug(f"    sys.path updated with {UTILITY_DIR}")

            try:
                from generate_csp import generate_csp
                logger.debug(f"    Successfully imported generate_csp")
            except ImportError as ie:
                logger.error(f"    Failed to import generate_csp: {ie}")
                logger.debug(f"    Available files in UTILITY_DIR:")
                for f in UTILITY_DIR.iterdir():
                    logger.debug(f"      {f.name}")
                return None

            # Generate CSP (it will be saved next to the DAT file with _csp.png suffix)
            logger.debug(f"    Calling generate_csp('{dat_path}')")

            result = generate_csp(str(dat_path))
            logger.debug(f"    generate_csp returned: {result}")

            if result:
                result_path = Path(result)
                if result_path.exists():
                    logger.info(f"  [OK] Generated CSP: {result_path.name}")
                    return result_path
                else:
                    logger.warning(f"  [WARNING] CSP generation returned path but file doesn't exist: {result}")
                    return None
            else:
                logger.warning(f"  [WARNING] CSP generation failed - no path returned")
                return None

        except Exception as e:
            logger.error(f"  [ERROR] CSP generation error: {e}")
            logger.debug(f"  Full traceback:\n{traceback.format_exc()}")
            return None

    def generate_stock(self, csp_path: Path, character: str) -> Optional[Path]:
        """
        Generate stock icon from CSP using utility scripts.

        Returns:
            Path to generated stock or None if failed
        """
        logger.info(f"  Generating stock icon from CSP...")
        logger.debug(f"    CSP file: {csp_path}")
        logger.debug(f"    Character: {character}")

        try:
            # Check for generate_stock_icon module
            stock_gen_path = UTILITY_DIR / "generate_stock_icon.py"
            logger.debug(f"    Looking for: {stock_gen_path}")
            logger.debug(f"    Exists: {stock_gen_path.exists()}")

            # Import the generation function
            sys.path.insert(0, str(UTILITY_DIR))
            from generate_stock_icon import generate_stock_icon
            logger.debug(f"    Successfully imported generate_stock_icon")

            # Generate stock (it will be saved next to the CSP file)
            output_path = csp_path.parent / f"stock_{csp_path.stem}.png"
            logger.debug(f"    Output path: {output_path}")
            logger.debug(f"    Calling generate_stock_icon('{csp_path}', '{character}', '{output_path}')")

            result = generate_stock_icon(str(csp_path), character, str(output_path))
            logger.debug(f"    generate_stock_icon returned: {result}")

            if result and output_path.exists():
                logger.info(f"  [OK] Generated stock: {output_path.name}")
                return output_path
            elif output_path.exists():
                logger.info(f"  [OK] Generated stock (returned {result}): {output_path.name}")
                return output_path
            else:
                logger.warning(f"  [WARNING] Stock generation failed - output file not created")
                logger.debug(f"    Result: {result}")
                logger.debug(f"    Output exists: {output_path.exists()}")
                return None

        except Exception as e:
            logger.error(f"  [ERROR] Stock generation error: {e}")
            logger.debug(f"  Full traceback:\n{traceback.format_exc()}")
            return None

    def get_default_stock(self, character: str) -> Optional[Path]:
        """
        Get default stock icon template from utility csp_data folder.
        """
        stock_template = UTILITY_DIR / "csp_data" / character / "stock.png"
        logger.debug(f"  Looking for default stock template: {stock_template}")

        if stock_template.exists():
            logger.debug(f"  Found default stock template")
            return stock_template

        logger.debug(f"  Default stock template not found")
        return None

    def get_vanilla_csp(self, character: str, costume_code: str) -> Optional[Path]:
        """
        Get vanilla CSP from organized vanilla assets directory.

        Args:
            character: Character name (e.g., 'Fox', 'Luigi')
            costume_code: Costume code (e.g., 'PlFxNr', 'PlLgNr')

        Returns:
            Path to vanilla CSP or None if not found
        """
        vanilla_csp = VANILLA_ASSETS_DIR / character / costume_code / "csp.png"
        logger.debug(f"  Looking for vanilla CSP: {vanilla_csp}")

        if vanilla_csp.exists():
            logger.debug(f"  Found vanilla CSP")
            return vanilla_csp

        logger.debug(f"  Vanilla CSP not found")
        return None

    def get_vanilla_stock(self, character: str, costume_code: str) -> Optional[Path]:
        """
        Get vanilla stock icon from organized vanilla assets directory.

        Args:
            character: Character name (e.g., 'Fox', 'Luigi')
            costume_code: Costume code (e.g., 'PlFxNr', 'PlLgNr')

        Returns:
            Path to vanilla stock or None if not found
        """
        vanilla_stock = VANILLA_ASSETS_DIR / character / costume_code / "stock.png"
        logger.debug(f"  Looking for vanilla stock: {vanilla_stock}")

        if vanilla_stock.exists():
            logger.debug(f"  Found vanilla stock")
            return vanilla_stock

        logger.debug(f"  Vanilla stock not found")
        return None

    def generate_unique_id(self, character: str, color: str) -> str:
        """
        Generate unique ID for a skin.

        Format: {character-slug}-{color-slug}-{counter}
        Example: fox-green-001
        """
        char_slug = character.lower().replace(' ', '-').replace('.', '')
        color_slug = color.lower().replace(' ', '-').replace('/', '-')
        base_id = f"{char_slug}-{color_slug}"

        # Check existing IDs in metadata
        existing_ids = set()
        if character in self.metadata['characters']:
            for skin in self.metadata['characters'][character].get('skins', []):
                existing_ids.add(skin['id'])

        # Find next available counter
        counter = 1
        while f"{base_id}-{counter:03d}" in existing_ids:
            counter += 1

        return f"{base_id}-{counter:03d}"

    def package_skin(self, dat_path: Path, csp_path: Optional[Path],
                    stock_path: Optional[Path], character: str, color: str,
                    costume_code: str) -> Optional[Dict]:
        """
        Package skin files into zip and move to storage.

        Returns:
            Metadata dict for the packaged skin, or None if failed
        """
        logger.debug(f"Packaging skin: {character} - {color} ({costume_code})")
        logger.debug(f"  DAT: {dat_path}")
        logger.debug(f"  CSP: {csp_path}")
        logger.debug(f"  Stock: {stock_path}")

        # Generate unique ID
        skin_id = self.generate_unique_id(character, color)
        zip_filename = f"{skin_id}.zip"
        logger.debug(f"  Generated skin ID: {skin_id}")

        # Create character folder in storage
        char_folder = STORAGE_DIR / character
        if not self.dry_run:
            char_folder.mkdir(parents=True, exist_ok=True)
            logger.debug(f"  Created character folder: {char_folder}")

        zip_path = char_folder / zip_filename

        # Determine new DAT name (simple increment system)
        dat_name = f"{costume_code}Mod.dat"
        logger.debug(f"  DAT will be renamed to: {dat_name}")

        logger.info(f"  Creating package: {zip_filename}")

        if not self.dry_run:
            try:
                # Create the zip
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                    # Add DAT file
                    zf.write(dat_path, dat_name)
                    logger.info(f"    + {dat_name}")
                    logger.debug(f"      Source: {dat_path}")

                    # Add CSP if available
                    if csp_path and csp_path.exists():
                        zf.write(csp_path, 'csp.png')
                        logger.info(f"    + csp.png")
                        logger.debug(f"      Source: {csp_path}")
                    else:
                        logger.debug(f"    No CSP to add (path={csp_path})")

                    # Add stock if available
                    if stock_path and stock_path.exists():
                        zf.write(stock_path, 'stc.png')
                        logger.info(f"    + stc.png")
                        logger.debug(f"      Source: {stock_path}")
                    else:
                        logger.debug(f"    No stock to add (path={stock_path})")

                logger.info(f"  [OK] Packaged to: {character}/{zip_filename}")

            except Exception as e:
                logger.error(f"  [ERROR] Failed to create package: {e}")
                logger.debug(f"  Full traceback:\n{traceback.format_exc()}")
                return None

        # Build metadata
        # Determine CSP source
        csp_source = "provided"
        if csp_path:
            csp_str = str(csp_path)
            if "vanilla" in csp_str:
                csp_source = "vanilla"
            elif "generated" in csp_str or "_csp.png" in csp_path.name:
                csp_source = "generated"

        # Determine stock source
        stock_source = "provided"
        if stock_path:
            stock_str = str(stock_path)
            if "vanilla" in stock_str:
                stock_source = "vanilla"
            elif "csp_data" in stock_str:
                stock_source = "default"
            # Only mark as generated if it was actually generated (not just starts with "stock_")
            # Generated stocks would be in intake folder and start with "stock_" prefix from generation
            elif "intake" in stock_str and stock_path.name.startswith("stock_") and "_csp.png" in stock_path.name:
                stock_source = "generated"

        metadata = {
            "id": skin_id,
            "filename": zip_filename,
            "character": character,
            "color": color,
            "dat_name": dat_name,
            "costume_code": costume_code,
            "has_csp": csp_path is not None,
            "has_stock": stock_path is not None,
            "csp_source": csp_source,
            "stock_source": stock_source,
            "date_added": datetime.now().isoformat(),
            "original_files": {
                "dat": dat_path.name,
                "csp": csp_path.name if csp_path else None,
                "stock": stock_path.name if stock_path else None
            }
        }

        return metadata

    def process_dat_file(self, dat_path: Path, used_csps: set):
        """Process a single DAT file from intake"""
        logger.info(f"\nProcessing: {dat_path.name}")
        logger.info("-" * 60)
        logger.debug(f"Full path: {dat_path}")
        logger.debug(f"File size: {dat_path.stat().st_size} bytes")

        # Detect character and color
        character, color, costume_code = self.detect_character_from_dat(dat_path)

        if not character:
            logger.info(f"Skipping {dat_path.name} - could not detect character")
            return False, None

        logger.info(f"  Character: {character}")
        logger.info(f"  Color: {color}")
        logger.info(f"  Costume Code: {costume_code}")

        # Find or generate CSP
        logger.debug("Starting CSP search/generation...")
        csp_path = self.find_matching_csp(dat_path, costume_code, used_csps)
        if csp_path:
            logger.info(f"  CSP: {csp_path.name} (matched)")
            used_csps.add(csp_path)  # Mark this CSP as used
            logger.debug(f"  Added {csp_path} to used_csps set")
        else:
            logger.info(f"  CSP: Not found, attempting to generate...")
            csp_path = self.generate_csp(dat_path, character)
            if csp_path:
                logger.debug(f"  CSP generation succeeded: {csp_path}")
            else:
                logger.info(f"  CSP generation failed, trying vanilla assets...")
                csp_path = self.get_vanilla_csp(character, costume_code)
                if csp_path:
                    logger.info(f"  CSP: {csp_path.name} (vanilla)")
                else:
                    logger.warning(f"  CSP: No vanilla CSP available - skin will have no CSP")

        # Find stock (prioritize vanilla over generation)
        logger.debug("Starting stock search...")
        stock_path = self.find_matching_stock(dat_path, costume_code)
        if stock_path:
            logger.info(f"  Stock: {stock_path.name} (matched)")
        else:
            logger.info(f"  Stock: Not found in intake, using vanilla stock...")
            stock_path = self.get_vanilla_stock(character, costume_code)
            if stock_path:
                logger.info(f"  Stock: {stock_path.name} (vanilla)")
            else:
                logger.info(f"  Stock: No vanilla stock found, trying default template...")
                stock_path = self.get_default_stock(character)
                if stock_path:
                    logger.info(f"  Stock: {stock_path.name} (default)")
                else:
                    logger.warning(f"  Stock: No stock available - skin will have no stock")

        # Package into zip
        logger.debug("Starting packaging...")
        metadata = self.package_skin(dat_path, csp_path, stock_path,
                                     character, color, costume_code)

        if metadata:
            logger.debug(f"Packaging succeeded, updating metadata")
            # Update master metadata
            if character not in self.metadata['characters']:
                self.metadata['characters'][character] = {"skins": []}
                logger.debug(f"Created new character entry for {character}")

            self.metadata['characters'][character]['skins'].append(metadata)
            logger.debug(f"Added skin metadata: {metadata['id']}")

            return True, csp_path

        logger.error(f"Packaging failed for {dat_path.name}")
        return False, None

    def process_intake_folder(self):
        """Process all DAT files in intake folder"""
        logger.info("="*60)
        logger.info("Costume Storage Management")
        logger.info("="*60)
        logger.debug(f"Script directory: {SCRIPT_DIR}")
        logger.debug(f"Intake directory: {INTAKE_DIR}")
        logger.debug(f"Storage directory: {STORAGE_DIR}")
        logger.debug(f"Utility directory: {UTILITY_DIR}")
        logger.debug(f"Log file: {LOG_FILE}")

        if self.dry_run:
            logger.info("[DRY RUN MODE - No files will be modified]")
            logger.info("")

        # Ensure directories exist
        INTAKE_DIR.mkdir(parents=True, exist_ok=True)
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directories exist")

        # Find all DAT files
        dat_files = list(INTAKE_DIR.glob("*.dat"))
        logger.debug(f"Glob search for *.dat in {INTAKE_DIR}")
        logger.debug(f"Found files: {[f.name for f in dat_files]}")

        if not dat_files:
            logger.info(f"\nNo DAT files found in {INTAKE_DIR}")
            return

        logger.info(f"\nFound {len(dat_files)} DAT file(s) in intake folder\n")

        # Process each DAT
        processed = 0
        skipped = 0
        used_csps = set()  # Track which CSPs have been matched

        for dat_file in dat_files:
            logger.debug(f"\n{'='*60}")
            logger.debug(f"Starting processing of {dat_file.name}")
            logger.debug(f"{'='*60}")

            success, csp_path = self.process_dat_file(dat_file, used_csps)
            if success:
                processed += 1
                logger.debug(f"Successfully processed {dat_file.name}")
            else:
                skipped += 1
                logger.debug(f"Skipped {dat_file.name}")

        # Save metadata
        if processed > 0:
            logger.debug(f"Saving metadata to {METADATA_FILE}")
            self.save_metadata()
            logger.info(f"\n[OK] Updated metadata: {METADATA_FILE}")

        # Summary
        logger.info("\n" + "="*60)
        logger.info(f"Summary: {processed} processed, {skipped} skipped")
        logger.info("="*60)

        if not self.dry_run and processed > 0:
            logger.info(f"\nSkins stored in: {STORAGE_DIR}")
            logger.info("You can now remove processed files from intake folder")

        logger.info(f"\nDetailed logs written to: {LOG_FILE}")


def main():
    dry_run = "--dry-run" in sys.argv

    manager = StorageManager(dry_run=dry_run)
    manager.process_intake_folder()


if __name__ == "__main__":
    main()
