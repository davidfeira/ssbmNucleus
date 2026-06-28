"""
Percent font (IfAll HUD) mod endpoints.

The in-game damage percent font lives in IfAll.dat/.usd (`.usd` = English,
the file a US 1.02 build reads). Digits 0-9 are 32x36 IA4 texture-swap
animation frames under the `DmgNum_scene_models` root (3 banks of 32 frames:
digits 0-9 three times + the 32x24 "%" and "HP" glyphs); the faded franchise
emblem behind the percent is `DmgMrk_scene_models`. Typeface mods often also
retouch the other HUD roots (timer, READY/GO, P1-P4 badges), so a mod stores
*every* slot that differs from vanilla, not just the digits.

Mods arrive in two flavors and are normalized on import:

  1. Compiled IfAll.dat/.usd (alone or in a zip) — exported with
     HSDRawViewer --hud-textures and diffed against the committed vanilla
     manifest (raw-buffer md5 per slot); only differing slots are stored.
     Slots are keyed (root, kind, ordinal) so a mod built from the Japanese
     IfAll.dat still lands on the right slots in the project's IfAll.usd
     (the only structural difference between regions is the usd-only
     Eblm_matanim_joint root).
  2. A glyph pack — loose images named per glyph (`0zero.png`, `7.png`,
     `percent.png`, `HP.png`, ...). Each glyph maps to every DmgNum slot
     whose vanilla pixels show that glyph, and installs as RGB5A3 so color
     survives (vanilla glyphs are grayscale IA4).

    storage/menus/percent/
        metadata.json                   # catalog of installed mods
        <mod_id>/
            mod.json                    # manifest (source + slot list)
            screenshot.png              # optional preview from the zip
            preview.png                 # composed 0-9% strip
            textures/s<n>.png           # one PNG per stored slot

Install runs HSDRawViewer --hud-textures import against the loaded project's
IfAll.usd with a spec.json of index→png replacements.
"""

import json
import re
import shutil
import tempfile
import uuid
import zipfile
import logging
from pathlib import Path
from datetime import datetime
from flask import request, jsonify, send_file

from core.config import HSDRAW_EXE, BACKEND_ASSETS_DIR
from core.state import get_project_files_dir, get_current_project_path

from . import menus_bp
from .helpers import (
    PERCENT_PATH, PERCENT_METADATA,
    load_catalog, save_catalog, load_mod_json, save_mod_json,
    _run_hsd_cli, _safe_extract_zip, _find_screenshot, send_mod_zip,
)

logger = logging.getLogger(__name__)

IMAGE_SUFFIXES = ('.png', '.jpg', '.jpeg', '.webp')

# Vanilla IfAll slot manifests (exported once from clean 1.02 files with
# --hud-textures; includes a raw-buffer md5 per slot for diffing).
VANILLA_MANIFEST_DIR = BACKEND_ASSETS_DIR / 'hud_vanilla'

# Source formats that carry color; injecting them into a grayscale vanilla
# slot as "original" would discard the color, so they re-encode as RGB5A3.
COLOR_FORMATS = {'RGB5A3', 'RGB565', 'RGBA8', 'CMP', 'CI8', 'CI4', 'CI14X2'}

GLYPH_KEYS = [str(d) for d in range(10)] + ['percent', 'hp']

# READY/GO!/GAME! word banners: ScInfCnt mat slot ordinals in vanilla IfAll
# (identified visually; "Time!" is stored three times, hash-identical).
WORD_MAT_ORDINALS = {
    'time': [0, 1, 2],
    'death': [3],
    'sudden': [4],
    'success': [8],
    'ready': [13],
    'go': [14],
    'game': [15],
    'failure': [16],
    'complete': [17],
}
WORD_KEYS = ['ready', 'go', 'game', 'time', 'sudden', 'death',
             'success', 'failure', 'complete']
# Words identifiable by texture dimensions alone — lets Dolphin-hash-named
# packs (tex1_<w>x<h>_<hash>.png) map without semantic filenames. Sudden and
# Death share 448x124 and are excluded.
UNIQUE_WORD_DIMS = {
    (280, 84): 'ready',
    (376, 188): 'go',
    (528, 144): 'game',
    (528, 164): 'time',
    (532, 172): 'success',
    (464, 136): 'failure',
    (536, 184): 'complete',
}
ALL_EDIT_KEYS = GLYPH_KEYS + WORD_KEYS


def _load_vanilla_manifest(region):
    """region: 'usd' or 'dat'. Returns the texture entry list or []."""
    try:
        with open(VANILLA_MANIFEST_DIR / f'manifest_{region}.json', 'r', encoding='utf-8') as f:
            return json.load(f).get('textures', [])
    except Exception as e:
        logger.warning(f'Vanilla HUD manifest ({region}) unavailable: {e}')
        return []


def _structure_seq(entries):
    # Only the slot skeleton — mods legitimately change texture formats
    # (grayscale → RGB5A3 for color) and occasionally dimensions.
    return [(e['root'], e['kind']) for e in entries]


def _detect_region(entries):
    """Match an exported mod's slot structure against the vanilla manifests.
    Returns ('usd'|'dat', vanilla_entries) or (None, None)."""
    seq = _structure_seq(entries)
    for region in ('usd', 'dat'):
        vanilla = _load_vanilla_manifest(region)
        if vanilla and _structure_seq(vanilla) == seq:
            return region, vanilla
    return None, None


def _with_ordinals(entries):
    """Tag each entry with its ordinal position within its (root, kind) group —
    the region-independent slot key."""
    counters = {}
    out = []
    for e in entries:
        key = (e['root'], e['kind'])
        ordinal = counters.get(key, 0)
        counters[key] = ordinal + 1
        out.append({**e, 'ordinal': ordinal})
    return out


def _glyph_slots(vanilla_entries):
    """Map glyph key ('0'..'9', 'percent', 'hp') → list of vanilla DmgNum
    slot entries (with ordinals) whose pixels show that glyph. Derived from
    the manifest itself: bank 1 frames 0-9 are digits 0-9 in order, and the
    32x24 frames alternate % / HP; mat slots are matched by md5."""
    entries = _with_ordinals(vanilla_entries)
    dn = [e for e in entries if e['root'] == 'DmgNum_scene_models']
    anim36 = [e for e in dn if e['kind'] == 'anim' and e['height'] == 36]
    anim24 = [e for e in dn if e['kind'] == 'anim' and e['height'] == 24]
    if len(anim36) < 10 or len(anim24) < 2:
        return {}

    md5_to_glyph = {anim36[i]['md5']: str(i) for i in range(10)}
    md5_to_glyph.setdefault(anim24[0]['md5'], 'percent')
    md5_to_glyph.setdefault(anim24[1]['md5'], 'hp')

    groups = {}
    for e in dn:
        glyph = md5_to_glyph.get(e['md5'])
        if glyph:
            groups.setdefault(glyph, []).append(e)
    return groups


def _word_slots(vanilla_entries):
    """Map word key ('ready', 'go', 'game', ...) → list of vanilla ScInfCnt
    slot entries (with ordinals). md5 expansion catches buffer-aliased
    duplicates (vanilla stores "Time!" three times as one shared buffer —
    a partial replace would leave stale copies on screen)."""
    entries = _with_ordinals(vanilla_entries)
    mats = [e for e in entries
            if e['root'] == 'ScInfCnt_scene_models' and e['kind'] == 'mat']
    by_ordinal = {e['ordinal']: e for e in mats}

    groups = {}
    for word, ordinals in WORD_MAT_ORDINALS.items():
        md5s = {by_ordinal[o]['md5'] for o in ordinals if o in by_ordinal}
        group = [e for e in mats
                 if e['ordinal'] in ordinals or e['md5'] in md5s]
        if group:
            groups[word] = group
    return groups


def _group_slots(vanilla_entries):
    """All editable slot groups: digit/percent glyphs + word banners."""
    groups = _glyph_slots(vanilla_entries)
    groups.update(_word_slots(vanilla_entries))
    return groups


def _mod_categories(mod):
    """Which HUD sub-categories a mod belongs to, derived from its slots:
    'percent' (damage digits / emblem) and/or 'readygo' (word banners).
    Empty custom mods fall back to the category they were created from."""
    vanilla = _load_vanilla_manifest('usd')
    word_keys = set()
    for word, entries in _word_slots(vanilla).items():
        for e in entries:
            word_keys.add((e['root'], e['kind'], e['ordinal']))

    cats = set()
    for s in mod.get('slots', []):
        if s['root'] in ('DmgNum_scene_models', 'DmgMrk_scene_models'):
            cats.add('percent')
        elif (s['root'], s['kind'], s['ordinal']) in word_keys:
            cats.add('readygo')
        else:
            # other HUD roots (timer, P badges...) ride along with percent
            cats.add('percent')
    if not cats and mod.get('origin_category'):
        cats.add(mod['origin_category'])
    return sorted(cats) or ['percent']


def _load_percent_catalog():
    return load_catalog(PERCENT_METADATA, '1.0')


def _update_catalog_categories(mod):
    """Refresh a mod's category tags in the catalog after its slots change
    (glyph/word edits can move a custom mod between HUD sub-categories)."""
    catalog = _load_percent_catalog()
    entry = next((m for m in catalog.get('mods', []) if m.get('id') == mod['id']), None)
    if entry is not None:
        entry['categories'] = _mod_categories(mod)
        _save_percent_catalog(catalog)


def _save_percent_catalog(data):
    save_catalog(PERCENT_METADATA, data)


def _attach_percent_urls(mod):
    out = dict(mod)
    if mod.get('id'):
        out['imageUrl'] = f"/api/mex/menus/percent/image/{mod['id']}"
    return out


def _find_ifall_files(directory):
    """All IfAll*.dat/.usd files in an extracted directory, sorted by name."""
    found = []
    for p in sorted(Path(directory).rglob('*')):
        if not p.is_file():
            continue
        name_lower = p.name.lower()
        if name_lower.startswith('ifall') and name_lower.endswith(('.dat', '.usd')):
            found.append(p)
    return found


def _find_glyph_images(directory):
    """Map glyph key → image path for loose glyph-pack files (`0zero.png`,
    `7.png`, `percent.png`, `HP.png`...). Ambiguous names are skipped;
    first match per glyph wins."""
    glyphs = {}
    for p in sorted(Path(directory).rglob('*')):
        if not p.is_file() or p.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if '__MACOSX' in p.parts:
            continue
        stem = p.stem.lower().strip()
        key = None
        if stem and stem[0].isdigit() and (len(stem) == 1 or not stem[1].isdigit()):
            key = stem[0]
        elif 'percent' in stem or stem == '%':
            key = 'percent'
        elif stem == 'hp' or stem.startswith('hp'):
            key = 'hp'
        if key and key not in glyphs:
            glyphs[key] = p
    return glyphs


def _word_key_for_name(name):
    """Match an image filename to a word key: semantic stems with optional
    trailing digits ('ready3.png', 'go21.png'), or Dolphin-hash names
    (tex1_<w>x<h>_<hash>.png) whose dimensions identify the word."""
    stem = Path(name).stem.lower().strip()
    m = re.match(r'^tex1_(\d+)x(\d+)_', stem)
    if m:
        return UNIQUE_WORD_DIMS.get((int(m.group(1)), int(m.group(2))))
    base = re.sub(r'[\s_\-]*\d+$', '', stem).rstrip('!').strip()
    return base if base in WORD_KEYS else None


def _find_word_images(directory):
    """Map word key → image path for loose word-banner files. First match
    per word wins (multi-variant packs keep their first folder)."""
    words = {}
    for p in sorted(Path(directory).rglob('*')):
        if not p.is_file() or p.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        if '__MACOSX' in p.parts:
            continue
        key = _word_key_for_name(p.name)
        if key and key not in words:
            words[key] = p
    return words


def looks_like_percent_zip(zip_path):
    """True if the zip contains an IfAll dat/usd, a full digit glyph pack,
    or a Ready/Go/Game word pack (3+ recognizable banners)."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            digit_stems = set()
            word_keys = set()
            for n in zf.namelist():
                if n.startswith('__MACOSX'):
                    continue
                base = Path(n).name.lower()
                if base.startswith('ifall') and base.endswith(('.dat', '.usd')):
                    return True
                if not base.endswith(IMAGE_SUFFIXES):
                    continue
                stem = Path(base).stem
                if stem and stem[0].isdigit() and (len(stem) == 1 or not stem[1].isdigit()):
                    digit_stems.add(stem[0])
                key = _word_key_for_name(base)
                if key:
                    word_keys.add(key)
            return len(digit_stems) == 10 or len(word_keys) >= 3
    except zipfile.BadZipFile:
        return False


def _variant_label(dat_path, base_name):
    """`IfAll(white).dat` → `<base_name> (white)`; bare names keep base_name."""
    stem = dat_path.stem
    suffix = stem[len('ifall'):].strip(' _-()') if stem.lower().startswith('ifall') else stem
    return f'{base_name} ({suffix})' if suffix else base_name


def _store_slots(mod_dir, slot_sources):
    """Copy slot source PNGs into <mod_dir>/textures/s<n>.png. slot_sources is
    a list of (vanilla_entry_with_ordinal, src_path, replaced[, glyph_key]).
    Returns the mod.json slot list."""
    tex_dir = mod_dir / 'textures'
    tex_dir.mkdir(parents=True, exist_ok=True)
    slots = []
    for n, source in enumerate(slot_sources):
        entry, src, replaced = source[:3]
        glyph = source[3] if len(source) > 3 else None
        fname = f's{n}.png'
        shutil.copy(str(src), str(tex_dir / fname))
        slot = {
            'root': entry['root'],
            'kind': entry['kind'],
            'ordinal': entry['ordinal'],
            'width': entry['width'],
            'height': entry['height'],
            'format': entry['format'],
            'file': fname,
            'replaced': bool(replaced),
        }
        if glyph:
            # lets the glyph/word editor revert pack-imported slots
            slot['glyph'] = glyph
        slots.append(slot)
    return slots


def _compose_preview(mod_dir, slots):
    """Compose a 0-9 + % glyph strip from the mod's stored DmgNum textures.
    Best-effort: returns True if preview.png was written."""
    try:
        from PIL import Image
    except ImportError:
        return False

    # vanilla bank 1: anim ordinals 0..9 are digits 0..9, the first 32x24
    # anim ordinal is the % sign
    wanted = [('anim', 36, i) for i in range(10)]
    by_key = {}
    digit_seen = {}
    for s in slots:
        if s['root'] != 'DmgNum_scene_models':
            continue
        key = (s['kind'], s['height'], s['ordinal'])
        by_key[key] = s
    # locate % slot: smallest 32x24 anim ordinal stored
    pct = sorted([s for s in slots if s['root'] == 'DmgNum_scene_models'
                  and s['kind'] == 'anim' and s['height'] == 24],
                 key=lambda s: s['ordinal'])
    picks = [by_key.get(k) for k in wanted]
    picks.append(pct[0] if pct else None)
    picks = [p for p in picks if p]
    if len(picks) < 3:
        return False

    images = []
    for s in picks:
        p = mod_dir / 'textures' / s['file']
        if p.exists():
            images.append(Image.open(p).convert('RGBA'))
    if len(images) < 3:
        return False

    w = sum(im.width for im in images)
    h = max(im.height for im in images)
    strip = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    x = 0
    for im in images:
        strip.paste(im, (x, h - im.height), im)
        x += im.width
    strip = strip.resize((w * 3, h * 3), Image.NEAREST)
    strip.save(mod_dir / 'preview.png')
    return True


def _import_percent_dat(dat_path, name, description, screenshot_src, catalog):
    """Diff a compiled IfAll against vanilla and store the changed slots as a
    new mod. Returns the mod dict (without URLs) or raises RuntimeError."""
    with tempfile.TemporaryDirectory(prefix='percent_export_') as tmp:
        export_dir = Path(tmp) / 'dump'
        export_dir.mkdir()
        result = _run_hsd_cli(['--hud-textures', 'export', str(dat_path), str(export_dir)],
                              timeout=300)
        if result is None:
            raise RuntimeError(f'Failed to extract textures from {dat_path.name}')

        manifest_path = export_dir / 'manifest.json'
        if not manifest_path.exists():
            raise RuntimeError('HSDRawViewer did not produce a texture manifest')
        with open(manifest_path, 'r', encoding='utf-8') as f:
            mod_entries = json.load(f).get('textures', [])
        if not mod_entries:
            raise RuntimeError(f'No textures found in {dat_path.name}')

        region, vanilla = _detect_region(mod_entries)
        if region is None:
            raise RuntimeError(f'{dat_path.name} does not match the vanilla IfAll '
                               'structure (not an IfAll file, or heavily restructured)')

        mod_entries = _with_ordinals(mod_entries)
        vanilla = _with_ordinals(vanilla)
        # Modders often build a "JP" IfAll.dat from US textures (or vice
        # versa); slots that are stock art from EITHER region are
        # localization noise, not edits — e.g. the US "Time!"/"Game!"
        # banners showing up as diffs against the JP baseline.
        other_region = 'dat' if region == 'usd' else 'usd'
        other_md5 = {(e['root'], e['kind'], e['ordinal']): e['md5']
                     for e in _with_ordinals(_load_vanilla_manifest(other_region))}
        slot_sources = []
        for me, ve in zip(mod_entries, vanilla):
            if me['md5'] == ve['md5']:
                continue
            if me['md5'] == other_md5.get((ve['root'], ve['kind'], ve['ordinal'])):
                continue
            # Colored source pixels need a color format in the (grayscale)
            # target slot; matching formats reinject as the target original.
            replaced = me['format'] != ve['format'] and me['format'] in COLOR_FORMATS
            slot_sources.append((ve, export_dir / me['filename'], replaced))

        if not slot_sources:
            raise RuntimeError(f'{dat_path.name} is identical to vanilla — nothing to import')

        mod_id = str(uuid.uuid4())[:8]
        mod_dir = PERCENT_PATH / mod_id
        slots = _store_slots(mod_dir, slot_sources)

        screenshot_filename = None
        if screenshot_src is not None and screenshot_src.exists():
            screenshot_filename = f'screenshot{screenshot_src.suffix.lower()}'
            shutil.copy(str(screenshot_src), str(mod_dir / screenshot_filename))
        _compose_preview(mod_dir, slots)

        mod = {
            'id': mod_id,
            'name': name,
            'description': description,
            'source': 'dat',
            'region': region,
            'screenshot': screenshot_filename,
            'slots': slots,
            'created': datetime.now().isoformat(),
        }
        save_mod_json(PERCENT_PATH, mod_id, mod)
        catalog.setdefault('mods', []).append({
            'id': mod_id,
            'name': name,
            'description': description,
            'source': 'dat',
            'categories': _mod_categories(mod),
            'created': mod['created'],
        })
        logger.info(f'[OK] Imported percent font mod: {name} ({mod_id}) — '
                    f'{len(slots)} changed slots from {dat_path.name} [{region}]')
        return mod


def _import_glyph_pack(glyphs, name, description, screenshot_src, catalog):
    """Build a mod from loose glyph/word images: each image lands on every
    slot showing that glyph (digits/percent/HP) or word banner (READY/GO!/
    GAME!...). Returns the mod dict or raises."""
    vanilla = _load_vanilla_manifest('usd')
    groups = _group_slots(vanilla)
    if not groups:
        raise RuntimeError('Vanilla HUD manifest unavailable; cannot import glyph packs')

    slot_sources = []
    for key, img_path in glyphs.items():
        for entry in groups.get(key, []):
            slot_sources.append((entry, img_path, True, key))
    if not slot_sources:
        raise RuntimeError('No recognizable glyph (0-9, percent, HP) or word '
                           '(ready/go/game/...) images found')

    mod_id = str(uuid.uuid4())[:8]
    mod_dir = PERCENT_PATH / mod_id
    slots = _store_slots(mod_dir, slot_sources)

    screenshot_filename = None
    if screenshot_src is not None and screenshot_src.exists():
        screenshot_filename = f'screenshot{screenshot_src.suffix.lower()}'
        shutil.copy(str(screenshot_src), str(mod_dir / screenshot_filename))
    _compose_preview(mod_dir, slots)

    mod = {
        'id': mod_id,
        'name': name,
        'description': description,
        'source': 'glyphs',
        'region': 'usd',
        'screenshot': screenshot_filename,
        'slots': slots,
        'created': datetime.now().isoformat(),
    }
    save_mod_json(PERCENT_PATH, mod_id, mod)
    catalog.setdefault('mods', []).append({
        'id': mod_id,
        'name': name,
        'description': description,
        'source': 'glyphs',
        'categories': _mod_categories(mod),
        'created': mod['created'],
    })
    logger.info(f'[OK] Imported percent glyph pack: {name} ({mod_id}) — '
                f'{len(glyphs)} glyphs over {len(slots)} slots')
    return mod


def install_percent_mods_from_zip(zip_path, name=None, description=''):
    """Import every IfAll variant (or a glyph pack) from a zip. Returns list of
    mod dicts with URLs attached. Raises RuntimeError when nothing is found."""
    zip_path = Path(zip_path)
    base_name = (name or zip_path.stem).strip() or zip_path.stem

    with tempfile.TemporaryDirectory(prefix='percent_import_') as tmp:
        extract_dir = Path(tmp) / 'extracted'
        extract_dir.mkdir()
        _safe_extract_zip(zip_path, extract_dir)

        dats = _find_ifall_files(extract_dir)
        screenshot_src = _find_screenshot(extract_dir)
        catalog = _load_percent_catalog()
        installed = []
        dat_errors = []

        multi = len(dats) > 1
        for dat in dats:
            mod_name = _variant_label(dat, base_name) if multi else base_name
            try:
                mod = _import_percent_dat(dat, mod_name, description, screenshot_src, catalog)
                installed.append(_attach_percent_urls(mod))
            except RuntimeError as e:
                dat_errors.append(str(e))

        if not installed:
            # No usable compiled IfAll — some archives ship a non-vanilla dat
            # (e.g. SD Remix IfAl1 renamed) alongside perfectly good glyph PNGs.
            glyphs = _find_glyph_images(extract_dir)
            if len([k for k in glyphs if k.isdigit()]) < 10:
                glyphs = {}   # partial digit sets are too ambiguous to trust
            words = _find_word_images(extract_dir)
            pack = {**glyphs, **words}
            if pack:
                mod = _import_glyph_pack(pack, base_name, description, screenshot_src, catalog)
                installed.append(_attach_percent_urls(mod))
            elif dat_errors:
                raise RuntimeError('; '.join(dat_errors))
            else:
                raise RuntimeError('No IfAll .dat/.usd, digit glyph pack (0-9), or '
                                   'Ready/Go/Game word pack found in archive')

        _save_percent_catalog(catalog)
        return installed


@menus_bp.route('/api/mex/menus/percent/list', methods=['GET'])
def list_percent_mods():
    """List HUD typeface mods. ?category=percent|readygo filters to mods
    touching that sub-category (a full typeface mod can be in both)."""
    try:
        category = (request.args.get('category') or '').strip().lower()
        catalog = _load_percent_catalog()
        dirty = False
        mods = []
        for m in catalog.get('mods', []):
            if not m.get('id'):
                continue
            if 'categories' not in m:
                full = load_mod_json(PERCENT_PATH, m['id'])
                m['categories'] = _mod_categories(full or {})
                dirty = True
            if category and category not in m['categories']:
                continue
            mods.append(_attach_percent_urls(m))
        if dirty:
            _save_percent_catalog(catalog)
        return jsonify({'success': True, 'mods': mods})
    except Exception as e:
        logger.error(f'List percent mods error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/percent/image/<mod_id>', methods=['GET'])
def get_percent_image(mod_id):
    """Serve the best preview for a percent mod: zip screenshot, composed
    glyph strip, or the largest stored texture."""
    try:
        mod = load_mod_json(PERCENT_PATH, mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404
        mod_dir = PERCENT_PATH / mod_id

        candidates = []
        if mod.get('screenshot'):
            candidates.append(mod_dir / mod['screenshot'])
        candidates.append(mod_dir / 'preview.png')
        for slot in sorted(mod.get('slots', []),
                           key=lambda s: s.get('width', 0) * s.get('height', 0),
                           reverse=True):
            candidates.append(mod_dir / 'textures' / slot['file'])

        for path in candidates:
            if path.exists():
                return send_file(str(path), max_age=0)
        return jsonify({'success': False, 'error': 'No preview available'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/percent/import', methods=['POST'])
def import_percent_mod():
    """Import a percent font mod. Accepts .zip (IfAll dat/usd or a digit glyph
    pack) or a raw IfAll .dat/.usd."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        fname_lower = file.filename.lower()
        name = (request.form.get('name') or '').strip() or Path(file.filename).stem
        description = (request.form.get('description') or '').strip()

        is_zip = fname_lower.endswith('.zip')
        is_dat = fname_lower.endswith(('.dat', '.usd'))
        if not (is_zip or is_dat):
            return jsonify({'success': False,
                            'error': 'File must be .zip or an IfAll .dat/.usd'}), 400

        with tempfile.TemporaryDirectory(prefix='percent_upload_') as tmp:
            # Wrap a raw dat in a zip so one code path handles both
            zip_path = Path(tmp) / 'upload.zip'
            if is_zip:
                file.save(str(zip_path))
            else:
                raw = file.read()
                with zipfile.ZipFile(zip_path, 'w') as zf:
                    zf.writestr(file.filename, raw)
            try:
                mods = install_percent_mods_from_zip(zip_path, name=name, description=description)
            except zipfile.BadZipFile:
                return jsonify({'success': False, 'error': 'Invalid or corrupt zip file'}), 400
            except RuntimeError as e:
                return jsonify({'success': False, 'error': str(e)}), 400

        return jsonify({'success': True, 'mods': mods, 'imported_count': len(mods)})
    except Exception as e:
        logger.error(f'Import percent mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/percent/create', methods=['POST'])
def create_percent_mod():
    """Create a fresh HUD typeface mod — a blank canvas for the glyph/word
    editor. Starts with no slots (= vanilla everywhere); edits add slots.
    Body: {name?, category?: 'percent'|'readygo', draft?}.

    When `draft` is true the mod folder is created but NOT added to the catalog,
    so it stays invisible in the vault until the editor commits it via /save."""
    try:
        payload = request.get_json(silent=True) or {}
        category = (payload.get('category') or 'percent').strip().lower()
        if category not in ('percent', 'readygo'):
            category = 'percent'
        default_name = 'New Ready/Go Pack' if category == 'readygo' else 'New Percent Font'
        name = (payload.get('name') or '').strip() or default_name
        is_draft = bool(payload.get('draft'))

        mod_id = str(uuid.uuid4())[:8]
        mod = {
            'id': mod_id,
            'name': name,
            'description': '',
            'source': 'custom',
            'region': 'usd',
            'origin_category': category,
            'slots': [],
            'created': datetime.now().isoformat(),
        }
        if is_draft:
            mod['draft'] = True
        save_mod_json(PERCENT_PATH, mod_id, mod)
        if not is_draft:
            catalog = _load_percent_catalog()
            catalog.setdefault('mods', []).append({
                'id': mod_id,
                'name': name,
                'description': '',
                'source': 'custom',
                'categories': [category],
                'created': mod['created'],
            })
            _save_percent_catalog(catalog)

        logger.info(f'[OK] Created {"draft " if is_draft else ""}percent font mod: {name} ({mod_id})')
        return jsonify({'success': True, 'mod': _attach_percent_urls(mod), 'draft': is_draft})
    except Exception as e:
        logger.error(f'Create percent mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/percent/<mod_id>/save', methods=['POST'])
def save_percent_mod(mod_id):
    """Commit a draft to the vault and/or rename a mod. Body: {name?}."""
    try:
        mod = load_mod_json(PERCENT_PATH, mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        payload = request.get_json(silent=True) or {}
        name = (payload.get('name') or '').strip()
        if name:
            mod['name'] = name
        mod.pop('draft', None)
        save_mod_json(PERCENT_PATH, mod_id, mod)

        category = mod.get('origin_category', 'percent')
        catalog = _load_percent_catalog()
        mods = catalog.setdefault('mods', [])
        entry = next((m for m in mods if m.get('id') == mod_id), None)
        if entry is None:
            mods.append({
                'id': mod_id,
                'name': mod['name'],
                'description': mod.get('description', ''),
                'source': mod.get('source', 'custom'),
                'categories': [category],
                'created': mod.get('created'),
            })
        else:
            entry['name'] = mod['name']
        _save_percent_catalog(catalog)

        logger.info(f'[OK] Saved percent font mod: {mod["name"]} ({mod_id})')
        return jsonify({'success': True, 'mod': _attach_percent_urls(mod)})
    except Exception as e:
        logger.error(f'Save percent mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/percent/<mod_id>/discard', methods=['POST'])
def discard_percent_draft(mod_id):
    """Discard an uncommitted draft (delete its folder). No-op once committed."""
    try:
        catalog = _load_percent_catalog()
        if any(m.get('id') == mod_id for m in catalog.get('mods', [])):
            return jsonify({'success': True, 'committed': True})
        mod_dir = PERCENT_PATH / mod_id
        if mod_dir.exists():
            shutil.rmtree(str(mod_dir), ignore_errors=True)
        logger.info(f'[OK] Discarded percent draft: {mod_id}')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Discard percent draft error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def _mod_glyph_state(mod):
    """Per-glyph/word editor state for a mod: which keys have a stored
    texture. Returns {key: slot} using the first stored slot of each key's
    vanilla group (all slots in a group carry the same image)."""
    vanilla = _load_vanilla_manifest('usd')
    groups = _group_slots(vanilla)
    slot_index = {(s['root'], s['kind'], s['ordinal']): s for s in mod.get('slots', [])}
    state = {}
    for key, entries in groups.items():
        for e in entries:
            s = slot_index.get((e['root'], e['kind'], e['ordinal']))
            if s is not None:
                state[key] = s
                break
    return state


def _glyph_listing(mod_id, mod, keys):
    state = _mod_glyph_state(mod)
    out = []
    for key in keys:
        slot = state.get(key)
        out.append({
            'key': key,
            'replaced': bool(slot and slot.get('replaced')),
            'overridden': slot is not None,
            'url': f'/api/mex/menus/percent/glyph/{mod_id}/{key}',
        })
    return out


@menus_bp.route('/api/mex/menus/percent/<mod_id>/glyphs', methods=['GET'])
def list_percent_glyphs(mod_id):
    """Glyph listing for the percent editor: 0-9, percent, HP with current
    image URLs and whether the mod overrides them."""
    try:
        mod = load_mod_json(PERCENT_PATH, mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404
        return jsonify({'success': True,
                        'glyphs': _glyph_listing(mod_id, mod, GLYPH_KEYS),
                        'mod': _attach_percent_urls(mod)})
    except Exception as e:
        logger.error(f'List percent glyphs error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/percent/<mod_id>/words', methods=['GET'])
def list_percent_words(mod_id):
    """Word-banner listing for the Ready/Go/Game editor."""
    try:
        mod = load_mod_json(PERCENT_PATH, mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404
        return jsonify({'success': True,
                        'glyphs': _glyph_listing(mod_id, mod, WORD_KEYS),
                        'mod': _attach_percent_urls(mod)})
    except Exception as e:
        logger.error(f'List percent words error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/percent/glyph/<mod_id>/<key>', methods=['GET'])
def get_percent_glyph(mod_id, key):
    try:
        if key not in ALL_EDIT_KEYS:
            return jsonify({'success': False, 'error': 'Unknown glyph'}), 404
        mod = load_mod_json(PERCENT_PATH, mod_id)
        if mod:
            slot = _mod_glyph_state(mod).get(key)
            if slot:
                tex_path = PERCENT_PATH / mod_id / 'textures' / slot['file']
                if tex_path.exists():
                    return send_file(str(tex_path), mimetype='image/png', max_age=0)
        vanilla_glyph = VANILLA_MANIFEST_DIR / f'glyph_{key}.png'
        if vanilla_glyph.exists():
            return send_file(str(vanilla_glyph), mimetype='image/png', max_age=0)
        return jsonify({'success': False, 'error': 'Glyph not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/percent/<mod_id>/replace_glyph', methods=['POST'])
def replace_percent_glyph(mod_id):
    """Replace one glyph (0-9 / percent / hp) with an uploaded image — lands on
    every DmgNum slot showing that glyph. Multipart form: key + file. The first
    edit of a dat-sourced slot backs up its texture so it can be reverted."""
    try:
        mod = load_mod_json(PERCENT_PATH, mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        key = (request.form.get('key') or '').strip().lower()
        if key not in ALL_EDIT_KEYS:
            return jsonify({'success': False, 'error': f'key must be one of {ALL_EDIT_KEYS}'}), 400
        if 'file' not in request.files or not request.files['file'].filename:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400

        vanilla = _load_vanilla_manifest('usd')
        groups = _group_slots(vanilla)
        entries = groups.get(key, [])
        if not entries:
            return jsonify({'success': False, 'error': 'Vanilla HUD manifest unavailable'}), 500

        upload = request.files['file'].read()
        mod_dir = PERCENT_PATH / mod_id
        tex_dir = mod_dir / 'textures'
        tex_dir.mkdir(parents=True, exist_ok=True)
        slots = mod.setdefault('slots', [])
        slot_index = {(s['root'], s['kind'], s['ordinal']): s for s in slots}

        next_n = max([int(s['file'][1:-4]) for s in slots if s['file'][1:-4].isdigit()] or [-1]) + 1
        for e in entries:
            slot = slot_index.get((e['root'], e['kind'], e['ordinal']))
            if slot is None:
                slot = {
                    'root': e['root'],
                    'kind': e['kind'],
                    'ordinal': e['ordinal'],
                    'width': e['width'],
                    'height': e['height'],
                    'format': e['format'],
                    'file': f's{next_n}.png',
                    'added_by_glyph': True,
                }
                next_n += 1
                slots.append(slot)
            else:
                tex_path = tex_dir / slot['file']
                orig_path = tex_dir / f"{slot['file'][:-4]}.orig.png"
                if tex_path.exists() and not orig_path.exists() and not slot.get('added_by_glyph'):
                    shutil.copy(str(tex_path), str(orig_path))
                    slot['orig_replaced'] = bool(slot.get('replaced'))
            (tex_dir / slot['file']).write_bytes(upload)
            slot['replaced'] = True
            slot['glyph'] = key

        save_mod_json(PERCENT_PATH, mod_id, mod)
        _update_catalog_categories(mod)
        _compose_preview(mod_dir, slots)
        logger.info(f'[OK] Replaced percent glyph "{key}" on mod {mod_id} ({len(entries)} slots)')
        return jsonify({'success': True, 'key': key,
                        'url': f'/api/mex/menus/percent/glyph/{mod_id}/{key}'})
    except Exception as e:
        logger.error(f'Replace percent glyph error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/percent/<mod_id>/screenshot', methods=['POST'])
def upload_percent_screenshot(mod_id):
    """Replace a percent mod's preview screenshot with an uploaded image."""
    try:
        mod = load_mod_json(PERCENT_PATH, mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404
        f = request.files.get('screenshot') or request.files.get('file')
        if not f or not f.filename:
            return jsonify({'success': False, 'error': 'No image uploaded'}), 400

        mod_dir = PERCENT_PATH / mod_id
        mod_dir.mkdir(parents=True, exist_ok=True)
        f.save(str(mod_dir / 'screenshot.png'))
        mod['screenshot'] = 'screenshot.png'   # get_percent_image prefers this
        save_mod_json(PERCENT_PATH, mod_id, mod)
        return jsonify({'success': True, 'imageUrl': f'/api/mex/menus/percent/image/{mod_id}'})
    except Exception as e:
        logger.error(f'Upload percent screenshot error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/percent/<mod_id>/export', methods=['GET'])
def export_percent_mod(mod_id):
    """Download a percent mod's files as a zip."""
    try:
        mod = load_mod_json(PERCENT_PATH, mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404
        return send_mod_zip(PERCENT_PATH / mod_id, mod.get('name') or mod_id)
    except Exception as e:
        logger.error(f'Export percent mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/percent/<mod_id>/revert_glyph', methods=['POST'])
def revert_percent_glyph(mod_id):
    """Undo a glyph edit. Body: {key}. Slots created by the edit are removed
    (back to vanilla); dat-sourced slots restore their backed-up texture."""
    try:
        mod = load_mod_json(PERCENT_PATH, mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        payload = request.get_json(silent=True) or {}
        key = (payload.get('key') or '').strip().lower()
        if key not in ALL_EDIT_KEYS:
            return jsonify({'success': False, 'error': f'key must be one of {ALL_EDIT_KEYS}'}), 400

        mod_dir = PERCENT_PATH / mod_id
        tex_dir = mod_dir / 'textures'
        slots = mod.get('slots', [])
        keep = []
        reverted = 0
        for slot in slots:
            if slot.get('glyph') != key:
                keep.append(slot)
                continue
            tex_path = tex_dir / slot['file']
            orig_path = tex_dir / f"{slot['file'][:-4]}.orig.png"
            if orig_path.exists():
                shutil.move(str(orig_path), str(tex_path))
                slot['replaced'] = slot.pop('orig_replaced', False)
                slot.pop('glyph', None)
                keep.append(slot)
            else:
                tex_path.unlink(missing_ok=True)
            reverted += 1
        if not reverted:
            return jsonify({'success': False, 'error': 'Nothing to revert for this glyph'}), 400

        mod['slots'] = keep
        save_mod_json(PERCENT_PATH, mod_id, mod)
        _update_catalog_categories(mod)
        _compose_preview(mod_dir, keep)
        logger.info(f'[OK] Reverted percent glyph "{key}" on mod {mod_id}')
        return jsonify({'success': True, 'key': key,
                        'url': f'/api/mex/menus/percent/glyph/{mod_id}/{key}'})
    except Exception as e:
        logger.error(f'Revert percent glyph error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/percent/delete/<mod_id>', methods=['POST'])
def delete_percent_mod(mod_id):
    try:
        catalog = _load_percent_catalog()
        mods = catalog.get('mods', [])
        idx = next((i for i, m in enumerate(mods) if m.get('id') == mod_id), -1)
        if idx < 0:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        mod_dir = PERCENT_PATH / mod_id
        if mod_dir.exists():
            shutil.rmtree(str(mod_dir), ignore_errors=True)

        mods.pop(idx)
        _save_percent_catalog(catalog)
        logger.info(f'[OK] Deleted percent mod: {mod_id}')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Delete percent mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def _build_replacement_spec(mod, mod_dir, target_region='usd'):
    """Map a mod's stored (root, kind, ordinal) slots onto the target file's
    global texture indices. Returns the --hud-textures import replacement
    list; raises RuntimeError when payloads are missing."""
    vanilla = _with_ordinals(_load_vanilla_manifest(target_region))
    if not vanilla:
        raise RuntimeError('Vanilla HUD manifest unavailable')
    index_by_slot = {(e['root'], e['kind'], e['ordinal']): e['index'] for e in vanilla}

    replacements = []
    for slot in mod.get('slots', []):
        tex_path = mod_dir / 'textures' / slot['file']
        if not tex_path.exists():
            continue
        target_index = index_by_slot.get((slot['root'], slot['kind'], slot['ordinal']))
        if target_index is None:
            logger.warning(f"Slot {slot['root']}/{slot['kind']}/{slot['ordinal']} "
                           f'has no match in the {target_region} IfAll; skipping')
            continue
        fmt = 'rgb5a3' if slot.get('replaced') else 'original'
        replacements.append({'index': target_index, 'png': str(tex_path), 'format': fmt})
    if not replacements:
        raise RuntimeError('No textures stored for this mod')
    return replacements


def apply_percent_mod(mod_id, ifall_path):
    """Apply a stored percent mod to an IfAll.usd on disk (in place) via
    HSDRawViewer --hud-textures import. Raises on failure."""
    mod = load_mod_json(PERCENT_PATH, mod_id)
    if not mod:
        raise RuntimeError('Mod not found')
    ifall_path = Path(ifall_path)
    if not ifall_path.exists():
        raise RuntimeError(f'IfAll file not found at {ifall_path}')
    if not HSDRAW_EXE.exists():
        raise RuntimeError(f'HSDRawViewer not found at {HSDRAW_EXE}')

    target_region = 'usd' if ifall_path.suffix.lower() == '.usd' else 'dat'
    replacements = _build_replacement_spec(mod, PERCENT_PATH / mod_id, target_region)

    with tempfile.TemporaryDirectory(prefix='percent_install_') as tmp:
        spec_path = Path(tmp) / 'spec.json'
        with open(spec_path, 'w', encoding='utf-8') as f:
            json.dump({'replacements': replacements}, f)

        output = Path(tmp) / ifall_path.name
        result = _run_hsd_cli([
            '--hud-textures', 'import',
            str(ifall_path), str(spec_path), str(output)
        ], timeout=300)
        if result is None:
            raise RuntimeError('HSDRawViewer --hud-textures import failed')
        if not output.exists():
            raise RuntimeError('Import produced no output file')

        shutil.copy(str(output), str(ifall_path))
    return mod


@menus_bp.route('/api/mex/menus/percent/install/<mod_id>', methods=['POST'])
def install_percent_mod(mod_id):
    """Install a percent font mod into the loaded project's IfAll.usd."""
    try:
        mod = load_mod_json(PERCENT_PATH, mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No MEX project loaded'}), 400

        files_dir = get_project_files_dir()
        if files_dir is None:
            return jsonify({'success': False, 'error': 'No project files directory'}), 400

        try:
            apply_percent_mod(mod_id, Path(files_dir) / 'IfAll.usd')
        except RuntimeError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        logger.info('  Replaced IfAll.usd with modded HUD textures')

        msg = f'Installed percent font "{mod["name"]}". Rebuild ISO to apply.'
        logger.info(f'[OK] Installed percent mod {mod_id}')
        return jsonify({'success': True, 'message': msg})
    except Exception as e:
        logger.error(f'Install percent mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
