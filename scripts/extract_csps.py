#!/usr/bin/env python3
"""
DEPRECATED: This script is no longer needed as of the single-source-of-truth refactor.

Previously extracted CSP and stock images from storage zips to viewer/public/storage.
Now the frontend uses a Vite proxy to fetch images directly from the Flask backend,
which serves files from the storage/ folder via the /storage/* endpoint.

No file duplication is needed - the backend serves images on demand.

This file is kept for reference only and should not be used.
"""

import os
import sys
import zipfile
import logging
import traceback
from pathlib import Path
import json

SCRIPT_DIR = Path(__file__).parent
STORAGE_DIR = SCRIPT_DIR / "storage"
VIEWER_PUBLIC = SCRIPT_DIR / "viewer" / "public" / "storage"
LOGS_DIR = SCRIPT_DIR / "logs"
METADATA_FILE = STORAGE_DIR / "metadata.json"
LOG_FILE = LOGS_DIR / "extract_csps.log"

# Setup logging
def setup_logging():
    """Configure logging with both file and console output"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # File handler - captures everything
    file_handler = logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
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

logger = setup_logging()


def extract_images_from_storage():
    """
    Extract CSP and stock images from all zips in storage
    """
    logger.info("Extracting CSP and stock images from storage...")
    logger.info("="*60)
    logger.debug(f"Storage directory: {STORAGE_DIR}")
    logger.debug(f"Viewer public directory: {VIEWER_PUBLIC}")
    logger.debug(f"Metadata file: {METADATA_FILE}")

    # Load metadata
    if not METADATA_FILE.exists():
        logger.error(f"Error: Metadata not found at {METADATA_FILE}")
        return

    logger.debug(f"Loading metadata from {METADATA_FILE}")
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)

    logger.debug(f"Metadata contains {len(metadata['characters'])} characters")

    # Ensure viewer storage exists
    VIEWER_PUBLIC.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Created viewer public directory: {VIEWER_PUBLIC}")

    total_extracted = 0
    total_skins = 0

    # Process each character
    for character, char_data in metadata['characters'].items():
        logger.debug(f"\n{'='*60}")
        logger.debug(f"Processing character: {character}")
        logger.debug(f"{'='*60}")

        char_folder = STORAGE_DIR / character
        viewer_char_folder = VIEWER_PUBLIC / character

        logger.debug(f"Character folder: {char_folder}")
        logger.debug(f"Viewer character folder: {viewer_char_folder}")
        logger.debug(f"Character folder exists: {char_folder.exists()}")

        if not char_folder.exists():
            logger.warning(f"Warning: Character folder not found: {char_folder}")
            continue

        viewer_char_folder.mkdir(exist_ok=True)
        logger.debug(f"Created viewer character folder: {viewer_char_folder}")

        num_skins = len(char_data.get('skins', []))
        logger.debug(f"Character has {num_skins} skins")

        # Process each skin
        for skin in char_data.get('skins', []):
            total_skins += 1
            logger.debug(f"\nProcessing skin: {skin['id']}")

            zip_path = char_folder / skin['filename']
            logger.debug(f"Zip path: {zip_path}")
            logger.debug(f"Zip exists: {zip_path.exists()}")

            if not zip_path.exists():
                logger.info(f"  [SKIP] Zip not found: {skin['filename']}")
                continue

            skin_id = skin['id']
            extracted = 0

            try:
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zip_contents = zf.namelist()
                    logger.debug(f"Zip contents: {zip_contents}")

                    # Extract CSP if it exists
                    if 'csp.png' in zip_contents:
                        csp_dest = viewer_char_folder / f"{skin_id}_csp.png"
                        logger.debug(f"Extracting CSP to: {csp_dest}")
                        with zf.open('csp.png') as source:
                            with open(csp_dest, 'wb') as dest:
                                dest.write(source.read())
                        logger.debug(f"CSP extracted successfully")
                        extracted += 1
                    else:
                        logger.debug(f"No CSP found in zip")

                    # Extract stock if it exists
                    if 'stc.png' in zip_contents:
                        stock_dest = viewer_char_folder / f"{skin_id}_stc.png"
                        logger.debug(f"Extracting stock to: {stock_dest}")
                        with zf.open('stc.png') as source:
                            with open(stock_dest, 'wb') as dest:
                                dest.write(source.read())
                        logger.debug(f"Stock extracted successfully")
                        extracted += 1
                    else:
                        logger.debug(f"No stock found in zip")

                if extracted > 0:
                    logger.info(f"  [OK] {character}/{skin_id}: Extracted {extracted} image(s)")
                    total_extracted += extracted
                else:
                    logger.debug(f"No images extracted for {skin_id}")

            except Exception as e:
                logger.error(f"  [ERROR] Error extracting {skin['filename']}: {e}")
                logger.debug(f"  Full traceback:\n{traceback.format_exc()}")

    logger.info("\n" + "="*60)
    logger.info(f"Extracted {total_extracted} images from {total_skins} skins")
    logger.info(f"Images available at: {VIEWER_PUBLIC}")
    logger.info("="*60)
    logger.info(f"\nDetailed logs written to: {LOG_FILE}")


if __name__ == "__main__":
    extract_images_from_storage()
