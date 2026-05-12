"""
Menus Blueprint - Menu mod management (CSS / SSS).

Currently supports CSS Icon Grid mods. A mod can arrive in two flavors:
  1. Loose PNGs named after characters
  2. Compiled CSS dat files (`MnSlChr.dat/.usd`, `mexSelectChr.dat`, optional `MxDt.dat`)

Regardless of source, on import we normalize to a tiny per-mod payload:

    storage/menus/css/icon_grid/
        metadata.json                       # catalog of installed mods
        <mod_id>/
            mod.json                        # per-mod manifest (icons + names + screenshot)
            screenshot.png                  # optional preview
            icons/
                <Character>.png             # one labeled icon per character

Anything else from the source archive is discarded. Some zips ship two packs
in one archive (e.g. both `mario.png` and `=mario.png`); we keep only the last
write per character — the user can split the zip if they want both variants.
"""

import json
import re
import shutil
import subprocess
import tempfile
import uuid
import zipfile
import logging
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify

from core.config import STORAGE_PATH, HSDRAW_EXE, MEXCLI_PATH, get_subprocess_args
from core.state import get_project_files_dir, get_current_project_path

logger = logging.getLogger(__name__)

menus_bp = Blueprint('menus', __name__)

MENUS_PATH = STORAGE_PATH / 'menus'
CSS_PATH = MENUS_PATH / 'css'
ICON_GRID_PATH = CSS_PATH / 'icon_grid'
ICON_GRID_PATH.mkdir(parents=True, exist_ok=True)

ICON_GRID_METADATA = ICON_GRID_PATH / 'metadata.json'

BG_PATH = CSS_PATH / 'background'
BG_PATH.mkdir(parents=True, exist_ok=True)
BG_METADATA = BG_PATH / 'metadata.json'

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

# Normalize MEX NameText values (which vary between projects) to our canonical
# character names (matching CHARACTER_ALIASES keys / ROSTER_ORDER).
NAMETEXT_NORMALIZE = {
    'c. falcon': 'C. Falcon',
    'cfalcon': 'C. Falcon',
    'captain falcon': 'C. Falcon',
    'dk': 'DK',
    'donkey kong': 'DK',
    'ice climbers': 'Ice Climbers',
    'iceclimbers': 'Ice Climbers',
    'popo': 'Ice Climbers',
    'nana': 'Ice Climbers',
    'jigglypuff': 'Jigglypuff',
    'puff': 'Jigglypuff',
    'mr. game & watch': 'Mr. Game & Watch',
    'mr. game and watch': 'Mr. Game & Watch',
    'mr game and watch': 'Mr. Game & Watch',
    'game and watch': 'Mr. Game & Watch',
    'game & watch': 'Mr. Game & Watch',
    'g&w': 'Mr. Game & Watch',
    'gw': 'Mr. Game & Watch',
    'dr. mario': 'Dr. Mario',
    'dr mario': 'Dr. Mario',
    'doc': 'Dr. Mario',
    'young link': 'Young Link',
    'ylink': 'Young Link',
    'mario': 'Mario',
    'fox': 'Fox',
    'kirby': 'Kirby',
    'bowser': 'Bowser',
    'link': 'Link',
    'sheik': 'Sheik',
    'ness': 'Ness',
    'peach': 'Peach',
    'pikachu': 'Pikachu',
    'samus': 'Samus',
    'yoshi': 'Yoshi',
    'mewtwo': 'Mewtwo',
    'luigi': 'Luigi',
    'marth': 'Marth',
    'zelda': 'Zelda',
    'falco': 'Falco',
    'pichu': 'Pichu',
    'ganondorf': 'Ganondorf',
    'ganon': 'Ganondorf',
    'roy': 'Roy',
}


def _normalize_mex_name(raw):
    """Map a MEX NameText string to a canonical character name. Returns the
    canonical name when recognized, otherwise the trimmed raw string (so custom
    fighters like 'Wolf' or 'Diddy Kong' keep their MEX-defined names)."""
    if not raw:
        return None
    trimmed = raw.strip()
    if not trimmed:
        return None
    return NAMETEXT_NORMALIZE.get(trimmed.lower(), trimmed)


# Standard Melee External Char ID → canonical character name (fallback when
# MEX NameText isn't available, e.g. mexSelectChr.dat without a sibling MxDt.dat).
EXTERNAL_ID_TO_CHARACTER = {
    0x00: 'C. Falcon',
    0x01: 'DK',
    0x02: 'Fox',
    0x03: 'Mr. Game & Watch',
    0x04: 'Kirby',
    0x05: 'Bowser',
    0x06: 'Link',
    0x07: 'Luigi',
    0x08: 'Mario',
    0x09: 'Marth',
    0x0A: 'Mewtwo',
    0x0B: 'Ness',
    0x0C: 'Peach',
    0x0D: 'Pikachu',
    0x0E: 'Ice Climbers',
    0x0F: 'Jigglypuff',
    0x10: 'Samus',
    0x11: 'Yoshi',
    0x12: 'Zelda',
    0x13: 'Sheik',
    0x14: 'Falco',
    0x15: 'Young Link',
    0x16: 'Dr. Mario',
    0x17: 'Roy',
    0x18: 'Pichu',
    0x19: 'Ganondorf',
}

ROSTER_ORDER = [
    'Dr. Mario', 'Mario', 'Luigi', 'Bowser', 'Peach', 'Yoshi', 'DK', 'C. Falcon',
    'Ganondorf', 'Falco', 'Fox', 'Ness', 'Ice Climbers', 'Kirby', 'Samus', 'Zelda',
    'Sheik', 'Link', 'Young Link', 'Pichu', 'Pikachu', 'Jigglypuff', 'Mewtwo',
    'Mr. Game & Watch', 'Marth', 'Roy',
]

# Vanilla MenuModel JOBJ index → character name. The icon-grid tiles (64x56)
# are static textures on these joints (DOBJ 1 = foreground icon). This mapping
# is a fixed constant for all vanilla-format CSS dats — it's the hardcoded
# layout of MnSlChr.dat's MenuModel.
VANILLA_ICON_JOINT_TO_CHARACTER = {
    4:  'Dr. Mario',
    6:  'Ganondorf',
    8:  'Falco',
    10: 'Young Link',
    12: 'Pichu',
    14: 'Roy',
    16: 'Mario',
    17: 'Luigi',
    18: 'Bowser',
    19: 'Peach',
    20: 'Yoshi',
    21: 'DK',
    22: 'C. Falcon',
    23: 'Fox',
    24: 'Ness',
    25: 'Ice Climbers',
    26: 'Kirby',
    27: 'Samus',
    28: 'Sheik',
    29: 'Link',
    30: 'Pikachu',
    31: 'Jigglypuff',
    32: 'Mewtwo',
    33: 'Mr. Game & Watch',
    34: 'Marth',
}


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
# Catalog persistence
# ─────────────────────────────────────────────────────────────────────────────

def _load_catalog():
    if not ICON_GRID_METADATA.exists():
        return {'version': '2.0', 'mods': []}
    try:
        with open(ICON_GRID_METADATA, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'version': '2.0', 'mods': []}


def _save_catalog(data):
    ICON_GRID_METADATA.parent.mkdir(parents=True, exist_ok=True)
    with open(ICON_GRID_METADATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def _catalog_entry(mod_full):
    """Trim a mod.json to the fields the catalog needs (list view)."""
    return {
        'id': mod_full['id'],
        'name': mod_full['name'],
        'description': mod_full.get('description', ''),
        'screenshot': mod_full.get('screenshot'),
        'icon_count': len(mod_full.get('icons', [])),
        'created': mod_full.get('created'),
    }


def _attach_urls(mod):
    """Add screenshot/icon URLs (absolute under /storage) to a mod dict."""
    out = dict(mod)
    mod_id = mod.get('id')
    if not mod_id:
        return out
    base = f'/storage/menus/css/icon_grid/{mod_id}'
    if mod.get('screenshot'):
        out['screenshotUrl'] = f"{base}/{mod['screenshot']}"
    icons_out = []
    for entry in mod.get('icons', []):
        e = dict(entry)
        if e.get('icon'):
            e['iconUrl'] = f"{base}/icons/{e['icon']}"
        icons_out.append(e)
    out['icons'] = icons_out
    return out


def _load_mod_json(mod_id):
    mod_dir = ICON_GRID_PATH / mod_id
    mod_path = mod_dir / 'mod.json'
    if not mod_path.exists():
        return None
    try:
        with open(mod_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f'Failed to read mod.json for {mod_id}: {e}')
        return None


def _save_mod_json(mod_id, mod):
    mod_dir = ICON_GRID_PATH / mod_id
    mod_dir.mkdir(parents=True, exist_ok=True)
    with open(mod_dir / 'mod.json', 'w', encoding='utf-8') as f:
        json.dump(mod, f, indent=2)


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


def looks_like_icon_grid_zip(zip_path):
    """Returns True if zip looks like a CSS icon grid mod (loose PNGs or compiled DAT)."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = [n for n in zf.namelist() if not n.startswith('__MACOSX')]
        equals_pngs = [n for n in names if Path(n).name.startswith('=') and n.lower().endswith('.png')]
        if len(equals_pngs) >= 2:
            return True
        for n in names:
            base = Path(n).name.lower()
            if base.startswith('mnslchr') or base == 'mexselectchr.dat':
                return True
        return False
    except zipfile.BadZipFile:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# HSDRawViewer CLI wrappers
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


def _dump_dat_icons(dat_path, out_dir):
    """Returns parsed CSS icons manifest dict or None."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if _run_hsd_cli(['--css-icons', 'export', str(dat_path), str(out_dir)]) is None:
        return None
    manifest_path = out_dir / 'manifest.json'
    if not manifest_path.exists():
        return None
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f'Failed to parse css-icons manifest: {e}')
        return None


def _read_mxdt_icon_info(mxdt_path, out_dir):
    """Returns parsed {icons: [{joint_id, external_char_id, ...}]} or None."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / 'mxdt_info.json'
    if _run_hsd_cli(['--mex-css-info', 'export', str(mxdt_path), str(out_json)]) is None:
        return None
    try:
        with open(out_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f'Failed to parse mxdt info: {e}')
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Source extraction → labeled icons (the work)
# ─────────────────────────────────────────────────────────────────────────────

def _find_css_dat(directory):
    """Pick the best CSS data file to feed to --css-icons. Returns Path or None."""
    candidates = list(Path(directory).rglob('*'))
    for p in candidates:
        if p.is_file() and p.name.lower() == 'mexselectchr.dat':
            return p
    for p in candidates:
        if p.is_file() and p.name.lower().startswith('mnslchr') and p.suffix.lower() == '.usd':
            return p
    for p in candidates:
        if p.is_file() and p.name.lower().startswith('mnslchr') and p.suffix.lower() == '.dat':
            return p
    return None


def _find_mxdt(directory):
    for p in Path(directory).rglob('*'):
        if p.is_file() and p.name.lower() == 'mxdt.dat':
            return p
    return None


def _label_loose_png(temp_dir):
    """Walk PNGs in temp_dir, alias-match to characters, return one or more packs.

    A "pack" is a list of {character, icon_path} dicts. When a zip contains
    multiple icons per character (e.g. `mario.png` AND `=mario.png`), each
    distinct candidate becomes its own pack. Pack ordering follows the sorted
    file order, so e.g. `=`-prefixed names land in pack 0 (lexicographically
    earlier).
    """
    by_char = {}  # character → list[Path]
    for path in sorted(Path(temp_dir).rglob('*')):
        if not path.is_file() or path.suffix.lower() != '.png':
            continue
        if path.name.lower() in (n.lower() for n in SCREENSHOT_CANDIDATES):
            continue
        stem = path.stem.lstrip('=')
        character = _stem_to_character(stem)
        if not character:
            continue
        by_char.setdefault(character, []).append(path)

    if not by_char:
        return []

    pack_count = max(len(paths) for paths in by_char.values())
    packs = []
    for pack_idx in range(pack_count):
        pack = []
        for character, paths in by_char.items():
            if pack_idx < len(paths):
                pack.append({'character': character, 'icon_path': paths[pack_idx]})
        if pack:
            packs.append(pack)
    return packs


def _label_dat_mod(temp_dir, work_dir):
    """Run HSDRawViewer to extract icons from a CSS dat, returning labeled-icon list.

    work_dir is a scratch directory we can write extraction output into.
    Returns same shape as _label_loose_png: list of {character, icon_path}.
    Discards unlabeled icons.
    """
    dat = _find_css_dat(temp_dir)
    if dat is None:
        return [], None

    css_dump_dir = Path(work_dir) / 'css_dump'
    manifest = _dump_dat_icons(dat, css_dump_dir)
    if not manifest:
        return [], None

    fmt = manifest.get('format')
    by_char = {}

    if fmt == 'mex':
        # MxDt.dat's MEX_CSSIcon[] is positional: entry N corresponds to
        # IconModel child N. Use its external_char_id to label the slot,
        # preferring the project's own NameText table when present (catches
        # custom MEX fighters like Wolf with their MEX-defined display names).
        slot_external_ids = []
        ext_id_to_name = {}  # external_char_id → display name (from MEX project)
        mxdt = _find_mxdt(temp_dir)
        if mxdt is not None:
            mxdt_info = _read_mxdt_icon_info(mxdt, work_dir)
            if mxdt_info:
                for entry in mxdt_info.get('icons', []):
                    eid = entry.get('external_char_id')
                    slot_external_ids.append(int(eid) if eid is not None else None)
                # NameText is indexed by external_char_id in the MEX project.
                for f in mxdt_info.get('fighters', []):
                    ext_id = f.get('internal_id')  # array position == ext_id for NameText
                    name = _normalize_mex_name(f.get('name'))
                    if ext_id is not None and name:
                        ext_id_to_name[int(ext_id)] = name

        # Repair pass: some MEX mods (e.g. Diamond) ship a MxDt with duplicate
        # ext_ids and missing-but-visually-present vanilla characters. When the
        # number of duplicates exactly matches the number of missing vanilla
        # ext_ids, reassign each duplicate to a missing id (in slot order).
        # We skip Sheik (0x13) because she typically shares Zelda's slot.
        VANILLA_EXTIDS = set(range(0x00, 0x1A))  # 0x00..0x19
        seen_first = {}
        dup_slots = []
        for i, eid in enumerate(slot_external_ids):
            if eid is None or eid not in VANILLA_EXTIDS:
                continue
            if eid in seen_first:
                dup_slots.append(i)
            else:
                seen_first[eid] = i
        missing_ids = sorted((VANILLA_EXTIDS - {0x13}) - set(seen_first.keys()))
        if dup_slots and len(dup_slots) == len(missing_ids):
            logger.info(
                f"  MEX: MxDt has {len(dup_slots)} duplicate vanilla ext_id(s); "
                f"reassigning to missing {[hex(x) for x in missing_ids]}"
            )
            for slot_idx, new_eid in zip(dup_slots, missing_ids):
                slot_external_ids[slot_idx] = new_eid

        for entry in manifest.get('icons', []):
            slot_index = entry.get('index')
            if slot_index is None:
                continue
            if slot_index >= len(slot_external_ids):
                continue
            external_id = slot_external_ids[slot_index]
            if external_id is None:
                continue
            # Prefer the MEX project's NameText (catches custom fighters like
            # Wolf); fall back to the standard vanilla ext_id table.
            character = ext_id_to_name.get(external_id) or EXTERNAL_ID_TO_CHARACTER.get(external_id)
            if not character:
                continue
            fg = entry.get('foreground')
            if not fg:
                continue
            src = css_dump_dir / fg
            if not src.exists():
                continue
            by_char[character] = src

    elif fmt == 'vanilla':
        # Vanilla icon grid: 64x56 static textures on fixed MenuModel joints.
        # The manifest's `icons` bucket contains these (one per joint), and
        # joint_index maps to a character via VANILLA_ICON_JOINT_TO_CHARACTER.
        for entry in manifest.get('icons', []):
            ji = entry.get('joint_index')
            if ji is None:
                continue
            character = VANILLA_ICON_JOINT_TO_CHARACTER.get(ji)
            if not character:
                continue
            filename = entry.get('filename')
            if not filename:
                continue
            src = css_dump_dir / filename
            if not src.exists():
                continue
            by_char[character] = src
        logger.info(f'  vanilla: matched {len(by_char)} characters via joint table')

    icons = [{'character': c, 'icon_path': p} for c, p in by_char.items()]
    return icons, fmt


# ─────────────────────────────────────────────────────────────────────────────
# Install (normalized output)
# ─────────────────────────────────────────────────────────────────────────────

def install_icon_grid_mod(zip_path, name=None, description=''):
    """Import an icon grid mod from a zip, persisting only the normalized payload.

    Returns a list of mod metadata dicts (with URLs attached). Most zips
    produce one mod, but zips bundling multiple packs (e.g. `name.png` and
    `=name.png` sets) produce one mod per pack.
    Raises on critical failure (bad zip, no icons extracted).
    """
    zip_path = Path(zip_path)
    if not zip_path.exists():
        raise FileNotFoundError(f'Zip not found: {zip_path}')

    default_name = zip_path.stem
    base_name = (name or default_name).strip() or default_name

    with tempfile.TemporaryDirectory(prefix='icongrid_') as tmp:
        temp_root = Path(tmp)
        extract_dir = temp_root / 'extracted'
        extract_dir.mkdir()
        work_dir = temp_root / 'work'
        work_dir.mkdir()

        _safe_extract_zip(zip_path, extract_dir)

        source_format = None
        packs = []  # list[list[{character, icon_path}]]

        # Loose-PNG first; falls back to DAT pipeline.
        packs = _label_loose_png(extract_dir)
        if packs:
            source_format = 'loose_png'
        else:
            dat_pack, fmt = _label_dat_mod(extract_dir, work_dir)
            if dat_pack:
                packs = [dat_pack]
                source_format = f'dat_{fmt}' if fmt else 'dat'

        if not packs:
            raise RuntimeError('No recognizable icons found in archive')

        screenshot_src = _find_screenshot(extract_dir)
        multi = len(packs) > 1

        def _sort_key(e):
            try:
                return (0, ROSTER_ORDER.index(e['character']))
            except ValueError:
                return (1, e['character'])

        installed = []
        catalog = _load_catalog()

        for pack_idx, pack in enumerate(packs):
            mod_id = str(uuid.uuid4())[:8]
            mod_dir = ICON_GRID_PATH / mod_id
            icons_dir = mod_dir / 'icons'
            icons_dir.mkdir(parents=True, exist_ok=True)

            # Copy screenshot (shared across all packs from this zip)
            screenshot_filename = None
            if screenshot_src is not None:
                screenshot_filename = f'screenshot{screenshot_src.suffix.lower()}'
                shutil.copy(str(screenshot_src), str(mod_dir / screenshot_filename))

            icon_entries = []
            for entry in pack:
                character = entry['character']
                src = entry.get('icon_path')
                if src is None:
                    continue
                icon_name = f'{_safe_filename(character)}.png'
                shutil.copy(str(src), str(icons_dir / icon_name))
                icon_entries.append({'character': character, 'icon': icon_name})
            icon_entries.sort(key=_sort_key)

            final_name = f"{base_name} ({pack_idx + 1})" if multi else base_name

            mod = {
                'id': mod_id,
                'name': final_name,
                'description': description or '',
                'screenshot': screenshot_filename,
                'source_format': source_format,
                'icons': icon_entries,
                'created': datetime.now().isoformat(),
            }
            _save_mod_json(mod_id, mod)
            catalog.setdefault('mods', []).append(_catalog_entry(mod))

            logger.info(
                f"[OK] Imported icon grid mod: {final_name} ({mod_id}) — "
                f"{len(icon_entries)} labeled icons ({source_format})"
            )
            installed.append(_attach_urls(mod))

        _save_catalog(catalog)
        return installed


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@menus_bp.route('/api/mex/menus/css/icon_grid/list', methods=['GET'])
def list_icon_grid_mods():
    """List all installed CSS Icon Grid mods (catalog summaries)."""
    try:
        catalog = _load_catalog()
        mods = []
        for entry in catalog.get('mods', []):
            mod_id = entry.get('id')
            if not mod_id:
                continue
            # Re-attach URLs based on stored screenshot name
            out = dict(entry)
            if entry.get('screenshot'):
                out['screenshotUrl'] = f"/storage/menus/css/icon_grid/{mod_id}/{entry['screenshot']}"
            mods.append(out)
        return jsonify({'success': True, 'mods': mods})
    except Exception as e:
        logger.error(f'List icon grid mods error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/icon_grid/import', methods=['POST'])
def import_icon_grid_mod():
    """Import an icon grid mod. Accepts .zip (loose PNGs or DAT bundle) or a
    raw .dat/.usd compiled CSS file.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        fname_lower = file.filename.lower()
        is_zip = fname_lower.endswith('.zip')
        is_dat = fname_lower.endswith('.dat')
        is_usd = fname_lower.endswith('.usd')
        if not (is_zip or is_dat or is_usd):
            return jsonify({'success': False, 'error': 'File must be .zip, .dat, or .usd'}), 400

        name = (request.form.get('name') or '').strip() or Path(file.filename).stem
        description = (request.form.get('description') or '').strip()

        # Raw .dat/.usd: wrap in a temp zip so the installer's single code path
        # (extract → detect → label) handles it transparently. A raw CSS dat
        # encodes only one icon set, so the multi-pack case can't apply.
        if is_dat or is_usd:
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                tmp_path = Path(tmp.name)
            try:
                raw_bytes = file.read()
                with zipfile.ZipFile(tmp_path, 'w') as zf:
                    zf.writestr(file.filename, raw_bytes)
                try:
                    mods = install_icon_grid_mod(tmp_path, name=name, description=description)
                except RuntimeError as e:
                    return jsonify({'success': False, 'error': str(e)}), 400
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()
        else:
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                tmp_path = Path(tmp.name)
            try:
                file.save(str(tmp_path))
                try:
                    mods = install_icon_grid_mod(tmp_path, name=name, description=description)
                except zipfile.BadZipFile:
                    return jsonify({'success': False, 'error': 'Invalid or corrupt zip file'}), 400
                except RuntimeError as e:
                    return jsonify({'success': False, 'error': str(e)}), 400
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()

        return jsonify({'success': True, 'mods': mods, 'imported_count': len(mods)})
    except Exception as e:
        logger.error(f'Import icon grid mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/icon_grid/<mod_id>/icons', methods=['GET'])
def get_icon_grid_icons(mod_id):
    """Return the full mod.json for a single mod, with URLs."""
    try:
        mod = _load_mod_json(mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404
        return jsonify({'success': True, 'mod': _attach_urls(mod)})
    except Exception as e:
        logger.error(f'Get icon grid icons error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/icon_grid/update/<mod_id>', methods=['POST'])
def update_icon_grid_mod(mod_id):
    """Update name/description of an icon grid mod."""
    try:
        mod = _load_mod_json(mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        payload = request.json or {}
        if 'name' in payload and payload['name'] is not None:
            new_name = str(payload['name']).strip()
            if new_name:
                mod['name'] = new_name
        if 'description' in payload and payload['description'] is not None:
            mod['description'] = str(payload['description'])

        _save_mod_json(mod_id, mod)

        # Update catalog summary too
        catalog = _load_catalog()
        for entry in catalog.get('mods', []):
            if entry.get('id') == mod_id:
                entry['name'] = mod['name']
                entry['description'] = mod.get('description', '')
                break
        _save_catalog(catalog)

        return jsonify({'success': True, 'mod': _attach_urls(mod)})
    except Exception as e:
        logger.error(f'Update icon grid mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/icon_grid/<mod_id>/relabel', methods=['POST'])
def relabel_icon(mod_id):
    """Change the character label on a single icon tile.

    Body: {old_character: "Mario", new_character: "Ganondorf"}
    Renames the file on disk + updates mod.json.
    """
    try:
        mod = _load_mod_json(mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        payload = request.json or {}
        old_char = (payload.get('old_character') or '').strip()
        new_char = (payload.get('new_character') or '').strip()
        if not old_char or not new_char:
            return jsonify({'success': False, 'error': 'old_character and new_character required'}), 400
        if old_char == new_char:
            return jsonify({'success': True, 'mod': _attach_urls(mod)})

        icons_dir = ICON_GRID_PATH / mod_id / 'icons'
        entry = next((e for e in mod.get('icons', []) if e.get('character') == old_char), None)
        if not entry:
            return jsonify({'success': False, 'error': f'No icon labeled "{old_char}"'}), 404

        old_file = icons_dir / entry['icon']
        new_file_name = f'{_safe_filename(new_char)}.png'
        new_file = icons_dir / new_file_name

        if old_file.exists():
            old_file.rename(new_file)

        entry['character'] = new_char
        entry['icon'] = new_file_name
        _save_mod_json(mod_id, mod)

        return jsonify({'success': True, 'mod': _attach_urls(mod)})
    except Exception as e:
        logger.error(f'Relabel icon error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/icon_grid/install/<mod_id>', methods=['POST'])
def install_icon_grid_to_mex(mod_id):
    """Install an icon grid mod into the currently loaded MEX project.

    Uses `mexcli set-css-icon` per fighter, which calls mexLib's
    SetFromImageFile — handles PNG→TEX conversion with correct color space
    and GX format natively.
    """
    try:
        mod = _load_mod_json(mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No MEX project loaded'}), 400

        if not MEXCLI_PATH.exists():
            return jsonify({'success': False, 'error': f'MexCLI not found at {MEXCLI_PATH}'}), 500

        icons_dir = ICON_GRID_PATH / mod_id / 'icons'
        installed = 0
        errors = []

        # Build the install list, handling the Zelda/Sheik shared-slot edge case:
        # if the mod only has one of them, use that icon for both.
        install_list = list(mod.get('icons', []))
        has_zelda = any(e.get('character') == 'Zelda' for e in install_list)
        has_sheik = any(e.get('character') == 'Sheik' for e in install_list)
        if has_zelda and not has_sheik:
            zelda_entry = next(e for e in install_list if e.get('character') == 'Zelda')
            install_list.append({'character': 'Sheik', 'icon': zelda_entry['icon']})
        elif has_sheik and not has_zelda:
            sheik_entry = next(e for e in install_list if e.get('character') == 'Sheik')
            install_list.append({'character': 'Zelda', 'icon': sheik_entry['icon']})

        for entry in install_list:
            character = entry.get('character')
            icon_file = entry.get('icon')
            if not character or not icon_file:
                continue
            src = icons_dir / icon_file
            if not src.exists():
                continue

            try:
                result = subprocess.run(
                    [str(MEXCLI_PATH), 'set-css-icon',
                     str(project_path), character, str(src)],
                    capture_output=True, text=True, timeout=30,
                    **get_subprocess_args()
                )
                if result.returncode == 0:
                    installed += 1
                    logger.info(f'  Set CSS icon: {character}')
                else:
                    err_msg = result.stdout.strip() or result.stderr.strip()
                    logger.warning(f'  Failed CSS icon for {character}: {err_msg}')
                    errors.append(character)
            except Exception as e:
                logger.warning(f'  Failed CSS icon for {character}: {e}')
                errors.append(character)

        if installed == 0:
            return jsonify({
                'success': False,
                'error': f'No icons installed. Errors: {", ".join(errors)}'
            }), 400

        msg = f'Installed {installed} icon(s). Rebuild ISO to apply.'
        if errors:
            msg += f' ({len(errors)} failed: {", ".join(errors)})'

        logger.info(f'[OK] Installed icon grid mod {mod_id} via MexCLI ({installed} icons)')
        return jsonify({'success': True, 'message': msg, 'matched': installed})
    except Exception as e:
        logger.error(f'Install icon grid mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/icon_grid/delete/<mod_id>', methods=['POST'])
def delete_icon_grid_mod(mod_id):
    """Delete an icon grid mod and its files."""
    try:
        catalog = _load_catalog()
        mods = catalog.get('mods', [])
        idx = next((i for i, m in enumerate(mods) if m.get('id') == mod_id), -1)
        if idx < 0:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        mod_dir = ICON_GRID_PATH / mod_id
        if mod_dir.exists():
            shutil.rmtree(mod_dir, ignore_errors=True)

        mods.pop(idx)
        _save_catalog(catalog)
        logger.info(f'[OK] Deleted icon grid mod: {mod_id}')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Delete icon grid mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# CSS Background mod catalog
# ─────────────────────────────────────────────────────────────────────────────

def _load_bg_catalog():
    if not BG_METADATA.exists():
        return {'version': '1.0', 'mods': []}
    try:
        with open(BG_METADATA, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'version': '1.0', 'mods': []}


def _save_bg_catalog(data):
    BG_METADATA.parent.mkdir(parents=True, exist_ok=True)
    with open(BG_METADATA, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def _load_bg_mod_json(mod_id):
    mod_path = BG_PATH / mod_id / 'mod.json'
    if not mod_path.exists():
        return None
    try:
        with open(mod_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f'Failed to read bg mod.json for {mod_id}: {e}')
        return None


def _save_bg_mod_json(mod_id, mod):
    mod_dir = BG_PATH / mod_id
    mod_dir.mkdir(parents=True, exist_ok=True)
    with open(mod_dir / 'mod.json', 'w', encoding='utf-8') as f:
        json.dump(mod, f, indent=2)


def _attach_bg_urls(mod):
    """Add screenshot URL to a background mod dict."""
    out = dict(mod)
    mod_id = mod.get('id')
    if not mod_id:
        return out
    base = f'/storage/menus/css/background/{mod_id}'
    if mod.get('screenshot'):
        out['screenshotUrl'] = f"{base}/{mod['screenshot']}"
    return out


def _find_mnslchr_dat(directory):
    """Find a MnSlChr dat/usd file in an extracted directory."""
    directory = Path(directory)
    for p in sorted(directory.rglob('*')):
        if not p.is_file():
            continue
        name_lower = p.name.lower()
        if name_lower.startswith('mnslchr') and name_lower.endswith(('.dat', '.usd')):
            return p
    return None


@menus_bp.route('/api/mex/menus/css/background/list', methods=['GET'])
def list_bg_mods():
    """List all installed CSS background mods."""
    try:
        catalog = _load_bg_catalog()
        mods = []
        for entry in catalog.get('mods', []):
            mod_id = entry.get('id')
            if not mod_id:
                continue
            out = dict(entry)
            if entry.get('screenshot'):
                out['screenshotUrl'] = f"/storage/menus/css/background/{mod_id}/{entry['screenshot']}"
            mods.append(out)
        return jsonify({'success': True, 'mods': mods})
    except Exception as e:
        logger.error(f'List bg mods error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/background/import', methods=['POST'])
def import_bg_mod():
    """Import a CSS background mod.

    Accepts .zip (containing MnSlChr.dat/.usd) or a raw .dat/.usd file.
    Extracts the background model/animation bundle via HSDRawViewer --css-bg export.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        fname_lower = file.filename.lower()
        is_zip = fname_lower.endswith('.zip')
        is_dat = fname_lower.endswith('.dat')
        is_usd = fname_lower.endswith('.usd')
        if not (is_zip or is_dat or is_usd):
            return jsonify({'success': False, 'error': 'File must be .zip, .dat, or .usd'}), 400

        name = (request.form.get('name') or '').strip() or Path(file.filename).stem
        description = (request.form.get('description') or '').strip()

        with tempfile.TemporaryDirectory(prefix='cssbg_') as tmp:
            temp_root = Path(tmp)

            if is_zip:
                zip_path = temp_root / 'upload.zip'
                file.save(str(zip_path))
                extract_dir = temp_root / 'extracted'
                extract_dir.mkdir()
                try:
                    _safe_extract_zip(zip_path, extract_dir)
                except zipfile.BadZipFile:
                    return jsonify({'success': False, 'error': 'Invalid or corrupt zip file'}), 400
                source_dat = _find_mnslchr_dat(extract_dir)
                screenshot_src = _find_screenshot(extract_dir)
            else:
                # Raw dat/usd
                source_dat = temp_root / file.filename
                file.save(str(source_dat))
                screenshot_src = None

            if source_dat is None or not source_dat.exists():
                return jsonify({'success': False, 'error': 'No MnSlChr .dat/.usd found in upload'}), 400

            # Run HSDRawViewer --css-bg export to extract background.dat
            export_dir = temp_root / 'bg_export'
            export_dir.mkdir()
            result = _run_hsd_cli(['--css-bg', 'export', str(source_dat), str(export_dir)])
            if result is None:
                return jsonify({'success': False, 'error': 'Failed to extract background from DAT'}), 500

            bg_dat = export_dir / 'background.dat'
            if not bg_dat.exists():
                return jsonify({'success': False, 'error': 'HSDRawViewer did not produce background.dat'}), 500

            # Create mod entry
            mod_id = str(uuid.uuid4())[:8]
            mod_dir = BG_PATH / mod_id
            mod_dir.mkdir(parents=True, exist_ok=True)

            # Copy background.dat
            shutil.copy(str(bg_dat), str(mod_dir / 'background.dat'))

            # Copy screenshot if available
            screenshot_filename = None
            if screenshot_src is not None and screenshot_src.exists():
                screenshot_filename = f'screenshot{screenshot_src.suffix.lower()}'
                shutil.copy(str(screenshot_src), str(mod_dir / screenshot_filename))

            mod = {
                'id': mod_id,
                'name': name,
                'description': description,
                'screenshot': screenshot_filename,
                'created': datetime.now().isoformat(),
            }
            _save_bg_mod_json(mod_id, mod)

            catalog = _load_bg_catalog()
            catalog.setdefault('mods', []).append({
                'id': mod_id,
                'name': name,
                'description': description,
                'screenshot': screenshot_filename,
                'created': mod['created'],
            })
            _save_bg_catalog(catalog)

            logger.info(f'[OK] Imported CSS background mod: {name} ({mod_id})')
            return jsonify({'success': True, 'mod': _attach_bg_urls(mod)})

    except Exception as e:
        logger.error(f'Import bg mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/background/install/<mod_id>', methods=['POST'])
def install_bg_to_mex(mod_id):
    """Install a CSS background mod into the currently loaded MEX project.

    1. Runs HSDRawViewer --css-bg import to swap the background in MnSlChr.usd
    2. Runs mexcli add-code to inject the Gecko code that disables the hardcoded
       CSS background animation, so the custom one is visible.
    """
    try:
        mod = _load_bg_mod_json(mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No MEX project loaded'}), 400

        files_dir = get_project_files_dir()
        if files_dir is None:
            return jsonify({'success': False, 'error': 'No project files directory'}), 400

        mnslchr_usd = Path(files_dir) / 'MnSlChr.usd'
        if not mnslchr_usd.exists():
            return jsonify({'success': False, 'error': f'MnSlChr.usd not found at {mnslchr_usd}'}), 400

        bg_dat = BG_PATH / mod_id / 'background.dat'
        if not bg_dat.exists():
            return jsonify({'success': False, 'error': 'background.dat missing from mod'}), 400

        if not HSDRAW_EXE.exists():
            return jsonify({'success': False, 'error': f'HSDRawViewer not found at {HSDRAW_EXE}'}), 500

        with tempfile.TemporaryDirectory(prefix='cssbg_install_') as tmp:
            output_usd = Path(tmp) / 'MnSlChr.usd'

            # Step 1: Import background into MnSlChr.usd
            result = _run_hsd_cli([
                '--css-bg', 'import',
                str(mnslchr_usd), str(bg_dat), str(output_usd)
            ])
            if result is None:
                return jsonify({'success': False, 'error': 'HSDRawViewer --css-bg import failed'}), 500

            if not output_usd.exists():
                return jsonify({'success': False, 'error': 'Import produced no output file'}), 500

            # Copy output back to project
            shutil.copy(str(output_usd), str(mnslchr_usd))
            logger.info(f'  Replaced MnSlChr.usd with custom background')

        # Step 2: Add Gecko code to disable hardcoded CSS BG animation
        logger.info(f'  MexCLI path: {MEXCLI_PATH} (exists={MEXCLI_PATH.exists()})')
        logger.info(f'  Project path: {project_path}')
        if MEXCLI_PATH.exists():
            try:
                cmd = [str(MEXCLI_PATH), 'add-code',
                       str(project_path),
                       'Disable Hardcoded CSS BG Anim',
                       '04263384 48000010']
                logger.info(f'  Running: {" ".join(cmd)}')
                code_result = subprocess.run(
                    cmd,
                    capture_output=True, text=True, timeout=60,
                    **get_subprocess_args()
                )
                logger.info(f'  add-code exit={code_result.returncode} stdout={code_result.stdout[:500]}')
                if code_result.stderr:
                    logger.info(f'  add-code stderr={code_result.stderr[:500]}')
            except Exception as e:
                logger.warning(f'  Failed to add Gecko code: {e}')
        else:
            logger.warning(f'  MexCLI not found at {MEXCLI_PATH}; skipping Gecko code injection')

        msg = f'Installed background "{mod["name"]}". Rebuild ISO to apply.'
        logger.info(f'[OK] Installed CSS background mod {mod_id}')
        return jsonify({'success': True, 'message': msg})

    except Exception as e:
        logger.error(f'Install bg mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/background/delete/<mod_id>', methods=['POST'])
def delete_bg_mod(mod_id):
    """Delete a CSS background mod and its files."""
    try:
        catalog = _load_bg_catalog()
        mods = catalog.get('mods', [])
        idx = next((i for i, m in enumerate(mods) if m.get('id') == mod_id), -1)
        if idx < 0:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        mod_dir = BG_PATH / mod_id
        if mod_dir.exists():
            shutil.rmtree(mod_dir, ignore_errors=True)

        mods.pop(idx)
        _save_bg_catalog(catalog)
        logger.info(f'[OK] Deleted CSS background mod: {mod_id}')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Delete bg mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
