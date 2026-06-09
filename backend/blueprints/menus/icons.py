"""
CSS Icon Grid mods.

A mod can arrive in two flavors:
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
import shutil
import subprocess
import tempfile
import uuid
import zipfile
import logging
from pathlib import Path
from datetime import datetime
from flask import request, jsonify

from core.config import MEXCLI_PATH, get_subprocess_args
from core.state import get_current_project_path

from . import menus_bp
from .helpers import (
    ICON_GRID_PATH, ICON_GRID_METADATA, SCREENSHOT_CANDIDATES,
    load_catalog, save_catalog, load_mod_json, save_mod_json,
    _stem_to_character, _safe_filename, _safe_extract_zip, _find_screenshot,
    _run_hsd_cli,
)

logger = logging.getLogger(__name__)

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


# ─────────────────────────────────────────────────────────────────────────────
# Catalog persistence (parameterized helpers live in .helpers)
# ─────────────────────────────────────────────────────────────────────────────

def _load_catalog():
    return load_catalog(ICON_GRID_METADATA, version='2.0')


def _save_catalog(data):
    save_catalog(ICON_GRID_METADATA, data)


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
    return load_mod_json(ICON_GRID_PATH, mod_id)


def _save_mod_json(mod_id, mod):
    save_mod_json(ICON_GRID_PATH, mod_id, mod)


# ─────────────────────────────────────────────────────────────────────────────
# Zip detection
# ─────────────────────────────────────────────────────────────────────────────

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


@menus_bp.route('/api/mex/menus/css/icon_grid/<mod_id>/replace_icon', methods=['POST'])
def replace_icon(mod_id):
    """Replace a single icon image. Multipart form: character + file (image)."""
    try:
        mod = _load_mod_json(mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        character = (request.form.get('character') or '').strip()
        if not character:
            return jsonify({'success': False, 'error': 'character is required'}), 400
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        img = request.files['file']
        if not img.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        entry = next((e for e in mod.get('icons', []) if e.get('character') == character), None)
        if not entry:
            return jsonify({'success': False, 'error': f'No icon labeled "{character}"'}), 404

        icons_dir = ICON_GRID_PATH / mod_id / 'icons'
        icon_name = entry['icon']
        dest = icons_dir / icon_name
        img.save(str(dest))

        _save_mod_json(mod_id, mod)
        return jsonify({'success': True, 'mod': _attach_urls(mod)})
    except Exception as e:
        logger.error(f'Replace icon error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/icon_grid/<mod_id>/delete_icon', methods=['POST'])
def delete_icon(mod_id):
    """Delete a single icon from the mod. Body: {character: "Mario"}."""
    try:
        mod = _load_mod_json(mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        payload = request.json or {}
        character = (payload.get('character') or '').strip()
        if not character:
            return jsonify({'success': False, 'error': 'character is required'}), 400

        icons = mod.get('icons', [])
        entry = next((e for e in icons if e.get('character') == character), None)
        if not entry:
            return jsonify({'success': False, 'error': f'No icon labeled "{character}"'}), 404

        icons_dir = ICON_GRID_PATH / mod_id / 'icons'
        icon_file = icons_dir / entry['icon']
        if icon_file.exists():
            icon_file.unlink()

        mod['icons'] = [e for e in icons if e.get('character') != character]
        _save_mod_json(mod_id, mod)

        catalog = _load_catalog()
        for cat_entry in catalog.get('mods', []):
            if cat_entry.get('id') == mod_id:
                cat_entry['icon_count'] = len(mod['icons'])
                break
        _save_catalog(catalog)

        return jsonify({'success': True, 'mod': _attach_urls(mod)})
    except Exception as e:
        logger.error(f'Delete icon error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/icon_grid/<mod_id>/add_icon', methods=['POST'])
def add_icon(mod_id):
    """Add a new icon to the mod. Multipart form: character + file (image)."""
    try:
        mod = _load_mod_json(mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        character = (request.form.get('character') or '').strip()
        if not character:
            return jsonify({'success': False, 'error': 'character is required'}), 400
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        img = request.files['file']
        if not img.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        existing = next((e for e in mod.get('icons', []) if e.get('character') == character), None)
        if existing:
            return jsonify({'success': False, 'error': f'Icon for "{character}" already exists. Use replace instead.'}), 400

        icons_dir = ICON_GRID_PATH / mod_id / 'icons'
        icons_dir.mkdir(parents=True, exist_ok=True)
        icon_name = f'{_safe_filename(character)}.png'
        dest = icons_dir / icon_name
        img.save(str(dest))

        mod.setdefault('icons', []).append({'character': character, 'icon': icon_name})
        _save_mod_json(mod_id, mod)

        catalog = _load_catalog()
        for cat_entry in catalog.get('mods', []):
            if cat_entry.get('id') == mod_id:
                cat_entry['icon_count'] = len(mod['icons'])
                break
        _save_catalog(catalog)

        return jsonify({'success': True, 'mod': _attach_urls(mod)})
    except Exception as e:
        logger.error(f'Add icon error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/icon_grid/install/<mod_id>', methods=['POST'])
def install_icon_grid_to_mex(mod_id):
    """Return the install plan (list of icons to install) without executing."""
    try:
        mod = _load_mod_json(mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        install_list = list(mod.get('icons', []))
        has_zelda = any(e.get('character') == 'Zelda' for e in install_list)
        has_sheik = any(e.get('character') == 'Sheik' for e in install_list)
        if has_zelda and not has_sheik:
            zelda_entry = next(e for e in install_list if e.get('character') == 'Zelda')
            install_list.append({'character': 'Sheik', 'icon': zelda_entry['icon']})
        elif has_sheik and not has_zelda:
            sheik_entry = next(e for e in install_list if e.get('character') == 'Sheik')
            install_list.append({'character': 'Zelda', 'icon': sheik_entry['icon']})

        valid = []
        icons_dir = ICON_GRID_PATH / mod_id / 'icons'
        for entry in install_list:
            character = entry.get('character')
            icon_file = entry.get('icon')
            if character and icon_file and (icons_dir / icon_file).exists():
                valid.append({'character': character, 'icon': icon_file})

        return jsonify({'success': True, 'icons': valid, 'total': len(valid)})
    except Exception as e:
        logger.error(f'Icon grid install plan error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/icon_grid/install/<mod_id>/icon', methods=['POST'])
def install_single_css_icon(mod_id):
    """Install a single CSS icon for one fighter."""
    try:
        data = request.get_json()
        character = data.get('character')
        icon_file = data.get('icon')
        if not character or not icon_file:
            return jsonify({'success': False, 'error': 'Missing character or icon'}), 400

        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No MEX project loaded'}), 400

        if not MEXCLI_PATH.exists():
            return jsonify({'success': False, 'error': 'MexCLI not found'}), 500

        icons_dir = ICON_GRID_PATH / mod_id / 'icons'
        src = icons_dir / icon_file
        if not src.exists():
            return jsonify({'success': False, 'error': f'Icon file not found: {icon_file}'}), 404

        result = subprocess.run(
            [str(MEXCLI_PATH), 'set-css-icon',
             str(project_path), character, str(src)],
            capture_output=True, text=True, timeout=30,
            **get_subprocess_args()
        )
        if result.returncode == 0:
            return jsonify({'success': True, 'character': character})
        else:
            err_msg = result.stdout.strip() or result.stderr.strip()
            return jsonify({'success': False, 'error': err_msg}), 500
    except Exception as e:
        logger.error(f'Install single CSS icon error: {e}', exc_info=True)
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
