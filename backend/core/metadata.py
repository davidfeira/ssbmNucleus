"""
Shared access to the vault's storage/metadata.json.

Every blueprint that reads or writes vault metadata should go through
load_metadata()/save_metadata() instead of hand-rolling the open/json
boilerplate.
"""

import json
import logging
from pathlib import Path

from .config import STORAGE_PATH

logger = logging.getLogger(__name__)

METADATA_FILE = STORAGE_PATH / 'metadata.json'


def load_metadata(default=None, path: Path = None):
    """Load a metadata JSON file (the vault's metadata.json by default).

    Returns `default` when the file is missing or unreadable. Pass e.g.
    default={'characters': {}} to match the shape callers expect.
    """
    file = path or METADATA_FILE
    if not file.exists():
        return default
    try:
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Failed to read {file}: {e}")
        return default


def save_metadata(metadata, path: Path = None):
    """Write a metadata JSON file (the vault's metadata.json by default)."""
    file = path or METADATA_FILE
    file.parent.mkdir(parents=True, exist_ok=True)
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
