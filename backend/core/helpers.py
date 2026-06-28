"""
Shared utility functions for the MEX API backend.
"""

import re
import json
import math
import logging
import hashlib
import zipfile
from pathlib import Path

from .config import STORAGE_PATH, OUTPUT_PATH
from .constants import VANILLA_COSTUME_COUNT
from .costume_files import find_costume_archive_name

logger = logging.getLogger(__name__)


# MexCLI import-iso markers that mean "this ISO just isn't a vanilla/m-ex build"
# (a custom build like 20XX) — an EXPECTED incompatibility, not a real failure.
_INCOMPAT_ISO_MARKERS = ('not vanilla', 'm-ex build', 'mxdt', 'dol patch')


def _mexcli_error_detail(raw_output: str) -> str:
    """Pull the last ``"error"`` value from MexCLI's output (it emits one or more
    pretty-printed JSON blocks), falling back to the raw text."""
    text = (raw_output or '').strip()
    matches = re.findall(r'"error"\s*:\s*"([^"]*)"', text)
    return (matches[-1].strip() if matches else text)


def is_incompatible_iso_error(raw_output: str) -> bool:
    """True when import-iso failed only because the ISO isn't a vanilla/m-ex
    build. Bulk scans skip these silently ("get what it can") instead of
    surfacing them as errors."""
    return any(k in _mexcli_error_detail(raw_output).lower() for k in _INCOMPAT_ISO_MARKERS)


def friendly_iso_open_error(raw_output: str) -> str:
    """Concise, user-facing message for a single-ISO import-iso failure."""
    detail = _mexcli_error_detail(raw_output)
    if is_incompatible_iso_error(raw_output):
        return ("This ISO isn't a vanilla or m-ex build, so custom characters / "
                "stages can't be extracted from it. Use the 'Character skins' "
                "or 'DAS stage variants' targets for builds like 20XX.")
    return (detail.splitlines()[0][:300] if detail else 'Failed to open ISO.')


def calculate_auto_compression(added_costume_count: int) -> float:
    """Recommended CSP compression based on ADDED costume count (total - vanilla).

    Derived empirically by crash-testing the ONLINE character-select screen
    (the worst case for memory -- it uses more than offline VS), exported with
    color-smash OFF == the Quick Export config. CSP textures are resized to
    (136*r x 188*r), so the CSP memory the CSS loads scales as
    (vanilla + added) * r^2; the heap left for it also SHRINKS as the costume
    tables grow. The online CSS freezes (hard hang) when that overflows.

    Measured crash boundaries (r at which it starts to freeze):
        added   0 -> stable at 1.0      added 125 -> ~0.735
        added  55 -> ~0.84              added 255 -> ~0.525
    These low/mid-count points fit a drooping budget:
        (128 + added) * r_crash^2 ~= 135 - 0.12*added.

    We keep ~15% memory margin below that and never exceed 1.0:
        r = sqrt( (135 - 0.12*added) * 0.85 / (128 + added) )
          = sqrt( (114.8 - 0.102*added) / (128 + added) )

    This REPLACES the old linear `1 - 0.003*added`, which was borderline-UNSAFE
    at low-mid counts (55 added -> 0.83 vs ~0.84 crash, ~1% margin) and massively
    OVER-compressed at high counts (255 added -> 0.25 when ~0.48 is safe).
    High-count ladders at the 0.1 floor are healthy through 1500 total costumes,
    so the floor remains conservative beyond the fitted range.
    """
    if added_costume_count <= 0:
        return 1.0
    vanilla = VANILLA_COSTUME_COUNT  # 128
    safe_budget = (135.0 - 0.12 * added_costume_count) * 0.85  # 15% margin
    ratio = math.sqrt(max(0.0, safe_budget) / (vanilla + added_costume_count))
    return max(0.1, min(1.0, ratio))


def cleanup_output_folder():
    """
    Clean up old files from the output folder on startup.
    The output folder should be treated as temp - files are deleted after download.
    This catches any files that weren't cleaned up properly.
    """
    try:
        cleaned_count = 0
        cleaned_size = 0

        for item in OUTPUT_PATH.iterdir():
            if item.is_dir():
                # Clean contents of mod_exports and vault_backups
                if item.name in ['mod_exports', 'vault_backups']:
                    for f in item.iterdir():
                        if f.is_file():
                            size = f.stat().st_size
                            f.unlink()
                            cleaned_count += 1
                            cleaned_size += size
                continue

            # Delete ISOs and other temp files
            if item.suffix.lower() in ['.iso', '.json', '.png']:
                size = item.stat().st_size
                item.unlink()
                cleaned_count += 1
                cleaned_size += size

        if cleaned_count > 0:
            logger.info(f"Startup cleanup: removed {cleaned_count} files ({cleaned_size / (1024*1024):.1f} MB)")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")


def get_folder_size(path):
    """Get total size of a folder in bytes"""
    total = 0
    try:
        for item in Path(path).rglob('*'):
            if item.is_file():
                total += item.stat().st_size
    except Exception:
        pass
    return total


def migrate_legacy_character_names():
    """
    Migrate old character names to MEX format.
    Renames:
    - "Captain Falcon" -> "C. Falcon"
    - "Donkey Kong" -> "DK"

    This affects both metadata.json and storage folder names.
    """
    migrations = {
        "Captain Falcon": "C. Falcon",
        "Donkey Kong": "DK"
    }

    metadata_file = STORAGE_PATH / 'metadata.json'
    if not metadata_file.exists():
        return

    try:
        # Load metadata
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        # Track if any changes were made
        changes_made = False

        # Migrate character names in metadata
        if 'characters' in metadata:
            old_chars = list(metadata['characters'].keys())
            for old_name, new_name in migrations.items():
                if old_name in old_chars:
                    logger.info(f"Migrating character metadata: {old_name} -> {new_name}")
                    metadata['characters'][new_name] = metadata['characters'].pop(old_name)
                    changes_made = True

        # Save updated metadata if changes were made
        if changes_made:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info("Updated metadata.json with migrated character names")

        # Rename storage folders
        for old_name, new_name in migrations.items():
            old_folder = STORAGE_PATH / old_name
            new_folder = STORAGE_PATH / new_name

            if old_folder.exists() and old_folder.is_dir():
                logger.info(f"Migrating storage folder: {old_name}/ -> {new_name}/")
                # If new folder already exists, we need to merge
                if new_folder.exists():
                    logger.warning(f"Target folder {new_name}/ already exists, skipping folder rename")
                else:
                    old_folder.rename(new_folder)
                    logger.info(f"Renamed storage folder: {old_name}/ -> {new_name}/")

    except Exception as e:
        logger.error(f"Error during character name migration: {e}", exc_info=True)


def convert_windows_to_wsl_path(windows_path: str) -> str:
    """Convert a Windows path to WSL path if running in WSL."""
    import os
    if os.name != 'nt' and windows_path and len(windows_path) >= 2:
        # Check if it looks like a Windows path (C:\... or C:/...)
        if windows_path[1] == ':':
            drive_letter = windows_path[0].lower()
            rest_of_path = windows_path[2:].replace('\\', '/')
            return f'/mnt/{drive_letter}{rest_of_path}'
    return windows_path


def backfill_dat_hashes():
    """
    Backfill dat_hash for any skins that are missing it.
    This ensures duplicate detection works properly for all skins.
    """
    metadata_file = STORAGE_PATH / 'metadata.json'
    if not metadata_file.exists():
        return

    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        updated = 0
        errors = 0

        for char, data in metadata.get('characters', {}).items():
            for skin in data.get('skins', []):
                if skin.get('dat_hash'):
                    continue  # Already has hash

                # Get filename
                filename = skin.get('filename')
                if not filename:
                    skin_id = skin.get('id')
                    if skin_id:
                        filename = f'{skin_id}.zip'
                    else:
                        continue

                zip_path = STORAGE_PATH / char / filename
                if not zip_path.exists():
                    errors += 1
                    continue

                try:
                    with zipfile.ZipFile(zip_path, 'r') as zf:
                        archive_name = find_costume_archive_name(zf.namelist())
                        if archive_name:
                            dat_data = zf.read(archive_name)
                            skin['dat_hash'] = hashlib.md5(dat_data).hexdigest()
                            updated += 1
                except Exception:
                    errors += 1

        # Save metadata if we made updates
        if updated > 0:
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"Backfilled {updated} dat_hash values ({errors} errors)")

    except Exception as e:
        logger.error(f"Error during dat_hash backfill: {e}", exc_info=True)
