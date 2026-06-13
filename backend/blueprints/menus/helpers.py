"""
Shared constants and helpers for the menus blueprint package.

Everything that more than one submodule (icons / backgrounds / doors / ...)
needs lives here: storage path constants, the character alias table, zip
extraction, screenshot discovery, the HSDRawViewer CLI wrapper, and the
parameterized catalog / mod.json persistence helpers.
"""

import io
import re
import shutil
import subprocess
import zipfile
import logging
from pathlib import Path

from flask import send_file

from core.config import STORAGE_PATH, HSDRAW_EXE, get_subprocess_args
from core.metadata import load_metadata, save_metadata

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Storage paths
# ─────────────────────────────────────────────────────────────────────────────

MENUS_PATH = STORAGE_PATH / 'menus'
CSS_PATH = MENUS_PATH / 'css'

ICON_GRID_PATH = CSS_PATH / 'icon_grid'
ICON_GRID_PATH.mkdir(parents=True, exist_ok=True)
ICON_GRID_METADATA = ICON_GRID_PATH / 'metadata.json'

BG_PATH = CSS_PATH / 'background'
BG_PATH.mkdir(parents=True, exist_ok=True)
BG_METADATA = BG_PATH / 'metadata.json'

DOORS_PATH = CSS_PATH / 'doors'
DOORS_PATH.mkdir(parents=True, exist_ok=True)
DOORS_METADATA = DOORS_PATH / 'metadata.json'

PAUSE_PATH = MENUS_PATH / 'pause'
PAUSE_PATH.mkdir(parents=True, exist_ok=True)
PAUSE_METADATA = PAUSE_PATH / 'metadata.json'

PERCENT_PATH = MENUS_PATH / 'percent'
PERCENT_PATH.mkdir(parents=True, exist_ok=True)
PERCENT_METADATA = PERCENT_PATH / 'metadata.json'

SCREENSHOT_CANDIDATES = ['screenshot_0.png', 'screenshot.png', 'preview.png']

# Canonical Melee character → list of accepted filename stems (lowercase).
CHARACTER_ALIASES = {
    'Mario':            ['mario', 'mr'],
    'Fox':              ['fox', 'fx'],
    'C. Falcon':        ['falcon', 'falc', 'cfalcon', 'captainfalcon', 'ca', 'capt'],
    'DK':               ['dk', 'donkey', 'donkeykong', 'dkong'],
    'Kirby':            ['kirby', 'kieby', 'kby', 'kb'],
    'Bowser':           ['bowser', 'bows', 'kp', 'koopa'],
    'Link':             ['link', 'lk'],
    'Sheik':            ['sheik', 'sk', 'shelda', 'shiek'],
    'Ness':             ['ness', 'ns'],
    'Peach':            ['peach', 'pe'],
    'Ice Climbers':     ['ics', 'iceclimbers', 'ic', 'popo', 'nana', 'pp', 'climbers'],
    'Pikachu':          ['pika', 'pikachu', 'pk'],
    'Samus':            ['samus', 'sams', 'ss'],
    'Yoshi':            ['yoshi', 'yosh', 'ys'],
    'Jigglypuff':       ['jiggly', 'jigglypuff', 'puff', 'pr'],
    'Mewtwo':           ['mewtwo', 'm2', 'mt'],
    'Luigi':            ['luigi', 'lugi', 'lg'],
    'Marth':            ['marth', 'mars', 'ms'],
    'Zelda':            ['zelda', 'zd'],
    'Young Link':       ['younglink', 'yink', 'ylink', 'cl', 'ylk'],
    'Dr. Mario':        ['drmario', 'doc', 'dr', 'docmario'],
    'Falco':            ['falco', 'fc'],
    'Pichu':            ['pichu', 'pc'],
    'Mr. Game & Watch': ['gw', 'gnw', 'mrgw', 'mrgameandwatch', 'gameandwatch', 'gamewatch'],
    'Ganondorf':        ['ganon', 'ganondorf', 'gn'],
    'Roy':              ['roy', 'fe'],
}
_ALIAS_TO_CHARACTER = {alias: char for char, aliases in CHARACTER_ALIASES.items() for alias in aliases}


def _stem_to_character(stem):
    """Map a filename stem (case-insensitive) to a canonical character, or None."""
    key = stem.lower().strip()
    if not key:
        return None
    if key in _ALIAS_TO_CHARACTER:
        return _ALIAS_TO_CHARACTER[key]
    stripped = re.sub(r'[\W_0-9]+$', '', key)
    if stripped and stripped != key and stripped in _ALIAS_TO_CHARACTER:
        return _ALIAS_TO_CHARACTER[stripped]
    return None


def _safe_filename(name):
    """Make a character name filesystem-safe (e.g. `Dr. Mario` → `Dr_Mario`)."""
    return re.sub(r'[^A-Za-z0-9]+', '_', name).strip('_')


# ─────────────────────────────────────────────────────────────────────────────
# Catalog / mod.json persistence (parameterized — shared by icons & backgrounds)
# ─────────────────────────────────────────────────────────────────────────────

def load_catalog(metadata_path, version):
    """Load a mod catalog ({'version': ..., 'mods': [...]}) from metadata_path.

    Returns a fresh empty catalog (with the given version string) when the
    file is missing or unreadable.
    """
    return load_metadata(default={'version': version, 'mods': []}, path=metadata_path)


def save_catalog(metadata_path, data):
    save_metadata(data, path=metadata_path)


def load_mod_json(base_path, mod_id):
    """Load <base_path>/<mod_id>/mod.json, or None if missing/unreadable."""
    return load_metadata(default=None, path=base_path / mod_id / 'mod.json')


def save_mod_json(base_path, mod_id, mod):
    save_metadata(mod, path=base_path / mod_id / 'mod.json')


# ─────────────────────────────────────────────────────────────────────────────
# Zip handling
# ─────────────────────────────────────────────────────────────────────────────

def _safe_extract_zip(zip_path, dest_dir):
    """Extract zip while blocking path traversal and absolute paths."""
    dest_dir = Path(dest_dir).resolve()
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.infolist():
            name = member.filename
            if not name or name.endswith('/'):
                continue
            target = (dest_dir / name).resolve()
            if not str(target).startswith(str(dest_dir)):
                logger.warning(f'Skipping unsafe zip member: {name}')
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(target, 'wb') as dst:
                shutil.copyfileobj(src, dst)


def send_mod_zip(mod_dir, name):
    """Zip every file in a mod's folder in-memory and return it as a download
    attachment named after the mod. Shared by the menu mods' Export action."""
    mod_dir = Path(mod_dir)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        if mod_dir.exists():
            for p in sorted(mod_dir.rglob('*')):
                if p.is_file() and p.name != 'mod.json':
                    zf.write(str(p), str(p.relative_to(mod_dir)))
    buf.seek(0)
    safe = re.sub(r'[^\w\-. ]+', '_', str(name)).strip() or 'mod'
    return send_file(buf, mimetype='application/zip', as_attachment=True,
                     download_name=f'{safe}.zip', max_age=0)


def _find_screenshot(directory):
    """Find a preview image in the extracted directory."""
    directory = Path(directory)
    for candidate in SCREENSHOT_CANDIDATES:
        # Search anywhere in the tree (zips sometimes nest in a folder)
        matches = list(directory.rglob(candidate))
        if matches:
            return matches[0]
    for path in sorted(directory.rglob('*')):
        if path.is_file() and path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp'):
            return path
    return None


# ─────────────────────────────────────────────────────────────────────────────
# HSDRawViewer CLI wrapper
# ─────────────────────────────────────────────────────────────────────────────

def _run_hsd_cli(args, timeout=120):
    if not HSDRAW_EXE.exists():
        logger.warning(f'HSDRawViewer not found at {HSDRAW_EXE}; skipping DAT processing')
        return None
    try:
        result = subprocess.run(
            [str(HSDRAW_EXE), *args],
            capture_output=True, text=True, timeout=timeout,
            **get_subprocess_args()
        )
    except subprocess.TimeoutExpired:
        logger.error(f'HSDRawViewer {args[0]} timed out')
        return None
    except Exception as e:
        logger.error(f'HSDRawViewer failed to start: {e}')
        return None

    if result.returncode != 0:
        logger.error(f'HSDRawViewer {args[0]} exit {result.returncode}: {result.stdout}\n{result.stderr}')
        return None
    return result
