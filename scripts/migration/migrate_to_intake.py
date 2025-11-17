#!/usr/bin/env python3
"""
Migration Script - Copy costume zips/files into intake folder

Usage:
    python scripts/migration/migrate_to_intake.py <source_directory>
    python scripts/migration/migrate_to_intake.py --from-website  # Use website test imports
"""

import os
import sys
import shutil
import zipfile
import logging
import traceback
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
INTAKE_DIR = SCRIPT_DIR / "intake"
LOGS_DIR = SCRIPT_DIR / "logs"
WEBSITE_IMPORTS = SCRIPT_DIR / "utility" / "website" / "xxxTestImports"
LOG_FILE = LOGS_DIR / "migrate_to_intake.log"

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


def extract_and_migrate_zip(zip_path: Path):
    """
    Extract zip file and copy DAT/CSP/stock files to intake
    """
    logger.info(f"\nProcessing: {zip_path.name}")
    logger.debug(f"Full path: {zip_path}")

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Get list of files in zip
            files = zf.namelist()
            logger.debug(f"Files in zip: {files}")

            # Extract to temp location
            temp_dir = INTAKE_DIR / f"_temp_{zip_path.stem}"
            temp_dir.mkdir(exist_ok=True)
            logger.debug(f"Created temp directory: {temp_dir}")

            try:
                zf.extractall(temp_dir)
                logger.debug(f"Extracted all files to temp directory")

                # Find and copy DAT, CSP, and stock files
                copied = 0
                for root, dirs, filenames in os.walk(temp_dir):
                    logger.debug(f"Walking directory: {root}")
                    for filename in filenames:
                        file_path = Path(root) / filename

                        # Copy DAT files
                        if filename.lower().endswith('.dat'):
                            dest = INTAKE_DIR / filename
                            shutil.copy2(file_path, dest)
                            logger.info(f"  [OK] Copied DAT: {filename}")
                            logger.debug(f"    From: {file_path}")
                            logger.debug(f"    To: {dest}")
                            copied += 1

                        # Copy PNG files (CSP and stock icons)
                        elif filename.lower().endswith('.png'):
                            dest = INTAKE_DIR / filename
                            shutil.copy2(file_path, dest)
                            logger.info(f"  [OK] Copied PNG: {filename}")
                            logger.debug(f"    From: {file_path}")
                            logger.debug(f"    To: {dest}")
                            copied += 1

                if copied == 0:
                    logger.info(f"  [SKIP] No DAT or PNG files found in zip")
                else:
                    logger.info(f"  [OK] Copied {copied} files")

            finally:
                # Clean up temp directory
                logger.debug(f"Cleaning up temp directory: {temp_dir}")
                shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logger.error(f"  [ERROR] Failed to process zip: {e}")
        logger.debug(f"  Full traceback:\n{traceback.format_exc()}")


def migrate_directory(source_dir: Path):
    """
    Migrate files from a directory to intake
    """
    if not source_dir.exists():
        logger.error(f"Error: Directory not found: {source_dir}")
        return

    logger.info(f"Migrating from: {source_dir}")
    logger.info(f"To intake: {INTAKE_DIR}")
    logger.info("="*60)
    logger.debug(f"Source directory exists: {source_dir.exists()}")
    logger.debug(f"Source is directory: {source_dir.is_dir()}")

    # Ensure intake exists
    INTAKE_DIR.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Created intake directory: {INTAKE_DIR}")

    # Process zip files
    zip_files = list(source_dir.glob("*.zip"))
    logger.debug(f"Found zip files: {[f.name for f in zip_files]}")

    if zip_files:
        logger.info(f"\nFound {len(zip_files)} zip file(s)")
        for zip_file in zip_files:
            extract_and_migrate_zip(zip_file)

    # Copy loose DAT and PNG files
    logger.info("\nCopying loose files...")
    copied = 0

    for file in source_dir.glob("*"):
        if file.is_file() and file.suffix.lower() in ['.dat', '.png']:
            dest = INTAKE_DIR / file.name
            shutil.copy2(file, dest)
            logger.info(f"  [OK] Copied: {file.name}")
            logger.debug(f"    From: {file}")
            logger.debug(f"    To: {dest}")
            copied += 1

    if copied > 0:
        logger.info(f"\n[OK] Copied {copied} loose file(s)")
    else:
        logger.debug("No loose files to copy")

    logger.info("\n" + "="*60)
    logger.info("Migration complete!")
    logger.info(f"Files are now in: {INTAKE_DIR}")
    logger.info("\nNext steps:")
    logger.info("  1. Run: python scripts/tools/manage_storage.py")
    logger.info("  2. View in browser: cd viewer && npm run dev")
    logger.info(f"\nDetailed logs written to: {LOG_FILE}")


def main():
    if len(sys.argv) < 2:
        logger.info("Usage:")
        logger.info("  python scripts/migration/migrate_to_intake.py <source_directory>")
        logger.info("  python scripts/migration/migrate_to_intake.py --from-website")
        logger.info("\nExamples:")
        logger.info("  python scripts/migration/migrate_to_intake.py ~/Downloads/costume-pack")
        logger.info("  python scripts/migration/migrate_to_intake.py --from-website  # Use test imports")
        sys.exit(1)

    logger.debug(f"Command line arguments: {sys.argv}")

    if sys.argv[1] == "--from-website":
        logger.debug(f"Using website test imports from {WEBSITE_IMPORTS}")
        if not WEBSITE_IMPORTS.exists():
            logger.error(f"Error: Website test imports not found at {WEBSITE_IMPORTS}")
            sys.exit(1)
        source_dir = WEBSITE_IMPORTS
    else:
        source_dir = Path(sys.argv[1])
        logger.debug(f"Using provided directory: {source_dir}")

    migrate_directory(source_dir)


if __name__ == "__main__":
    main()
