#!/usr/bin/env python3
"""
Clear Storage Script - Removes all storage data

This script will:
- Delete all character folders in storage/
- Delete storage metadata.json
- Optionally clear intake folder
- Optionally clear logs

Note: No longer clears viewer/public/storage/ as the frontend now uses
      a proxy to serve files directly from storage/ folder.

Usage:
    python clear_storage.py                # Clear storage only
    python clear_storage.py --clear-intake # Also clear intake folder
    python clear_storage.py --clear-logs   # Also clear logs
    python clear_storage.py --all          # Clear everything
"""

import sys
import shutil
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
STORAGE_DIR = SCRIPT_DIR / "storage"
INTAKE_DIR = SCRIPT_DIR / "intake"
LOGS_DIR = SCRIPT_DIR / "logs"
METADATA_FILE = STORAGE_DIR / "metadata.json"


def clear_storage():
    """Clear all storage data"""
    print("Clearing storage...")

    removed_count = 0

    # Remove character folders in storage
    if STORAGE_DIR.exists():
        for item in STORAGE_DIR.iterdir():
            if item.is_dir():
                print(f"  Removing: {item.name}/")
                shutil.rmtree(item)
                removed_count += 1

    # Remove metadata.json
    if METADATA_FILE.exists():
        print(f"  Removing: metadata.json")
        METADATA_FILE.unlink()
        removed_count += 1

    if removed_count > 0:
        print(f"[OK] Cleared {removed_count} items from storage")
    else:
        print("[INFO] Storage is already empty")


def clear_intake():
    """Clear all files in intake folder"""
    print("\nClearing intake...")

    removed_count = 0

    if INTAKE_DIR.exists():
        for item in INTAKE_DIR.iterdir():
            if item.is_file():
                print(f"  Removing: {item.name}")
                item.unlink()
                removed_count += 1

    if removed_count > 0:
        print(f"[OK] Cleared {removed_count} files from intake")
    else:
        print("[INFO] Intake is already empty")


def clear_logs():
    """Clear all log files"""
    print("\nClearing logs...")

    removed_count = 0

    if LOGS_DIR.exists():
        for item in LOGS_DIR.iterdir():
            if item.is_file() and item.suffix == '.log':
                print(f"  Removing: {item.name}")
                item.unlink()
                removed_count += 1

    if removed_count > 0:
        print(f"[OK] Cleared {removed_count} log files")
    else:
        print("[INFO] No log files to clear")


def main():
    print("="*60)
    print("Clear Storage Script")
    print("="*60)

    # Parse arguments
    clear_intake_flag = "--clear-intake" in sys.argv or "--all" in sys.argv
    clear_logs_flag = "--clear-logs" in sys.argv or "--all" in sys.argv

    # Always clear storage
    clear_storage()

    # Optionally clear intake
    if clear_intake_flag:
        clear_intake()

    # Optionally clear logs
    if clear_logs_flag:
        clear_logs()

    print("\n" + "="*60)
    print("Done!")
    print("="*60)

    if not clear_intake_flag:
        print("\nNote: Intake folder was not cleared.")
        print("      Use --clear-intake or --all to clear it.")


if __name__ == "__main__":
    main()
