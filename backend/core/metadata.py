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


def custom_character_slug(character):
    """Slug for custom-character pseudo keys.

    Custom characters expose their skins to the canonical skin-editing stack
    under 'custom_characters/<slug>/skins' (added skins) and
    'custom_characters/<slug>/costumes' (bundled costumes, mirrored into a
    costume_meta list + materialized zips). STORAGE_PATH / key is the
    matching directory, so every path-join in the canonical endpoints works
    unchanged.
    """
    if character and character.startswith('custom_characters/') and \
            (character.endswith('/skins') or character.endswith('/costumes')):
        parts = character.split('/')
        if len(parts) == 3 and parts[1]:
            return parts[1]
    return None


def get_char_data(metadata, character):
    """Resolve a character's skins container.

    Canonical characters come from metadata['characters']. Custom-character
    pseudo keys resolve to a view over that character's added_skins or
    costume_meta — the SAME list object, so in-place skin mutations +
    save_metadata persist into the custom character entry.
    """
    if not isinstance(metadata, dict) or not character:
        return None
    chars = metadata.get('characters', {})
    if character in chars:
        return chars[character]
    slug = custom_character_slug(character)
    if slug:
        field = 'costume_meta' if character.endswith('/costumes') else 'added_skins'
        for entry in metadata.get('custom_characters', []):
            if entry.get('slug') == slug:
                return {'skins': entry.setdefault(field, [])}
    return None
