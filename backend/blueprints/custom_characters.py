"""
Custom Characters Blueprint - Manage m-ex custom fighters in the vault.

Custom characters are entirely new fighters added via m-ex. They are
imported from MexManager-exported ZIP packages or scanned from an ISO.
Each fighter is stored as:

    storage/custom_characters/<slug>/
        fighter.zip     (original ZIP preserved for re-export)
        fighter.json    (extracted metadata)
        css_icon.png    (CSS icon for grid display)
        csp_0.png ...   (per-costume CSP portraits)

Metadata is tracked under metadata.json["custom_characters"] (list of objects).
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
import logging
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

from core.config import STORAGE_PATH, MEXCLI_PATH, PROJECT_ROOT, get_subprocess_args
from core.state import get_current_project_path, reload_mex_manager

logger = logging.getLogger(__name__)

custom_characters_bp = Blueprint('custom_characters', __name__)

CUSTOM_CHARACTERS_PATH = STORAGE_PATH / 'custom_characters'
CUSTOM_CHARACTERS_PATH.mkdir(parents=True, exist_ok=True)

METADATA_FILE = STORAGE_PATH / 'metadata.json'

# Vanilla m-ex series list (index = seriesID in a fresh project).
# Icons exported from a vanilla project live in backend/assets/series/.
SERIES_NAMES = [
    'F-Zero', 'Donkey Kong', 'Star Fox', 'Game & Watch', 'Ice Climber',
    'Kirby', 'Super Mario', 'Fire Emblem', 'EarthBound', 'Pokémon',
    'Metroid', 'Smash Bros.', 'Yoshi', 'The Legend of Zelda',
    'Master Hand', 'Crazy Hand', 'Special Stages',
]
SERIES_ASSETS_DIR = Path(__file__).resolve().parent.parent / 'assets' / 'series'

VANILLA_FIGHTER_NAMES = {
    'C. Falcon', 'Captain Falcon', 'DK', 'Donkey Kong', 'Fox',
    'Mr. Game & Watch', 'Game & Watch', 'Kirby', 'Bowser',
    'Link', 'Luigi', 'Mario', 'Marth', 'Mewtwo', 'Ness', 'Peach',
    'Pikachu', 'Ice Climbers', 'Jigglypuff', 'Samus', 'Yoshi', 'Zelda',
    'Sheik', 'Falco', 'Young Link', 'Dr. Mario', 'Roy', 'Pichu',
    'Ganondorf', 'Master Hand', 'Wireframe Male', 'Wireframe Female',
    'Giga Bowser', 'Crazy Hand', 'Sandbag', 'Nana',
    'NONE', 'Popo',
}


def _norm_fighter_name(name):
    """Normalize a fighter name for comparison: case, punctuation, and
    '&'-vs-'and' (some builds rename e.g. 'Mr. Game and Watch')."""
    n = (name or '').lower().replace(' and ', ' & ')
    return re.sub(r'[^a-z0-9&]', '', n)


VANILLA_FIGHTER_NAMES_NORM = {_norm_fighter_name(n) for n in VANILLA_FIGHTER_NAMES}


def _sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


def _make_slug(name):
    slug = _sanitize_filename(name).lower().replace(' ', '-')
    slug = re.sub(r'-+', '-', slug).strip('-')
    if not slug:
        slug = 'custom-character'
    return slug


def _dedupe_slug(slug):
    if not (CUSTOM_CHARACTERS_PATH / slug).exists():
        return slug
    counter = 2
    while (CUSTOM_CHARACTERS_PATH / f"{slug}-{counter}").exists():
        counter += 1
    return f"{slug}-{counter}"


def _read_metadata():
    if not METADATA_FILE.exists():
        return {'characters': {}, 'stages': {}, 'custom_stages': [], 'custom_characters': []}
    with open(METADATA_FILE, 'r') as f:
        data = json.load(f)
    if 'custom_characters' not in data:
        data['custom_characters'] = []
    return data


def _write_metadata(data):
    with open(METADATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def _resolve_asset_png(assets_dir, asset_ref):
    """Resolve an asset reference like 'css\\icon' to a .png file path."""
    if not asset_ref or not assets_dir.exists():
        return None
    normalized = asset_ref.replace('\\', '/').replace('/', os.sep)
    png_path = assets_dir / f"{normalized}.png"
    if png_path.exists():
        return png_path
    basename = Path(normalized).name
    candidate = assets_dir / f"{basename}.png"
    if candidate.exists():
        return candidate
    return None


def _parse_cli_json(stdout):
    """Extract the trailing JSON object from MexCLI output. MexCLI prints
    indented JSON (often after progress noise like 'Trimmed Image ...'),
    so naive last-line parsing yields '}' and silently fails."""
    s = (stdout or '').strip()
    idx = s.rfind('\n{')
    candidate = s[idx + 1:] if idx != -1 else (s if s.startswith('{') else None)
    if candidate is None:
        return {}
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        return {}


def _find_entry(metadata, slug):
    for c in metadata.get('custom_characters', []):
        if c['slug'] == slug:
            return c
    return None


def _series_icon_path(series_id):
    p = SERIES_ASSETS_DIR / f'icon_{series_id}.png'
    return p if p.exists() else None


def _series_name(series_id):
    if isinstance(series_id, int) and 0 <= series_id < len(SERIES_NAMES):
        return SERIES_NAMES[series_id]
    return None


def _rewrite_zip_fighter_json(zip_path, out_path, mutate_json=None, drop_entries=None,
                              replace_entries=None):
    """Copy a fighter zip to out_path, optionally mutating the embedded
    fighter.json, dropping entries by name, and/or replacing entry contents
    (replace_entries: {basename: bytes}; missing entries are appended)."""
    drop = {n.lower() for n in (drop_entries or [])}
    replace = {n.lower(): b for n, b in (replace_entries or {}).items()}
    replaced = set()
    with zipfile.ZipFile(zip_path, 'r') as src, \
            zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            basename = item.filename.split('/')[-1]
            if basename.lower() in drop:
                continue
            data = src.read(item.filename)
            if mutate_json and basename.lower() == 'fighter.json':
                meta = json.loads(data)
                meta = mutate_json(meta) or meta
                data = json.dumps(meta, indent=2).encode('utf-8')
            if basename.lower() in replace:
                data = replace[basename.lower()]
                replaced.add(basename.lower())
            dst.writestr(item, data)
        for name, data in (replace_entries or {}).items():
            if name.lower() not in replaced:
                dst.writestr(name, data)


def _rewrite_fighter_zip(char_dir, mutate_json=None, drop_entries=None, replace_entries=None):
    """Rewrite fighter.zip in place: optionally mutate the embedded
    fighter.json (mutate_json receives and returns the parsed dict), drop
    entries by name, and/or replace entry contents. add-fighter reads the
    zip's own fighter.json and assets, so any vault-side change must be
    mirrored here to survive install.
    """
    zip_path = char_dir / 'fighter.zip'
    if not zip_path.exists():
        return False
    tmp_path = zip_path.with_suffix('.zip.tmp')
    _rewrite_zip_fighter_json(zip_path, tmp_path, mutate_json, drop_entries, replace_entries)
    tmp_path.replace(zip_path)
    return True


def _update_fighter_json_everywhere(char_dir, mutate):
    """Apply `mutate(fighter_dict)` to BOTH the storage fighter.json and the
    one embedded in fighter.zip."""
    fighter_json_path = char_dir / 'fighter.json'
    with open(fighter_json_path, 'r') as f:
        fighter_data = json.load(f)
    mutate(fighter_data)
    with open(fighter_json_path, 'w') as f:
        json.dump(fighter_data, f, indent=2)
    _rewrite_fighter_zip(char_dir, mutate_json=lambda m: (mutate(m), m)[1])
    return fighter_data


def _normalized_png(raw, size):
    """Decode an uploaded image and return PNG bytes resized to `size`."""
    import io
    from PIL import Image
    img = Image.open(io.BytesIO(raw))
    img.load()
    img = img.convert('RGBA')
    if img.size != size:
        img = img.resize(size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


# fixed entry names + canonical sizes from MexFighterAssets
FIGHTER_ASSET_SPECS = {
    'icon': ('icon.png', (64, 56)),
    'big_banner': ('big_banner.png', (256, 28)),
    'small_banner': ('small_banner.png', (120, 24)),
}


def _sync_costume_meta(entry, char_dir, fighter_data):
    """Mirror the bundled costumes into entry['costume_meta'] + materialized
    per-costume zips under char_dir/costumes/, keyed by DAT stem.

    This is what lets the shared skin-edit stack (EditModal, CSP manager,
    3D viewer) open a bundled costume directly via the pseudo-character
    'custom_characters/<slug>/costumes'. Edits land in the materialized
    zips/meta and are folded back into fighter.zip at install time.
    Returns True if anything changed.
    """
    fighter_zip = char_dir / 'fighter.zip'
    if not fighter_zip.exists():
        return False

    costumes_dir = char_dir / 'costumes'
    meta_list = entry.setdefault('costume_meta', [])
    by_id = {m['id']: m for m in meta_list}
    changed = False
    current_ids = []

    with zipfile.ZipFile(fighter_zip) as zf:
        inner_names = {n.split('/')[-1].lower(): n for n in zf.namelist()}
        for i, costume in enumerate(fighter_data.get('costumes', [])):
            dat = (costume.get('file') or {}).get('fileName') or ''
            stem = Path(dat).stem
            if not stem:
                continue
            current_ids.append(stem)
            costumes_dir.mkdir(exist_ok=True)

            zip_dest = costumes_dir / f'{stem}.zip'
            if not zip_dest.exists():
                inner = inner_names.get(f'{stem}.zip'.lower())
                if inner is None:
                    continue
                zip_dest.write_bytes(zf.read(inner))
                changed = True

            if not (costumes_dir / f'{stem}_csp.png').exists() and (char_dir / f'csp_{i}.png').exists():
                shutil.copy2(char_dir / f'csp_{i}.png', costumes_dir / f'{stem}_csp.png')
                changed = True
            if not (costumes_dir / f'{stem}_stc.png').exists() and (char_dir / f'stock_{i}.png').exists():
                shutil.copy2(char_dir / f'stock_{i}.png', costumes_dir / f'{stem}_stc.png')
                changed = True

            m = by_id.get(stem)
            if m is None:
                m = {
                    'id': stem,
                    'color': costume.get('name') or stem,
                    'filename': f'{stem}.zip',
                    'dat_name': dat,
                }
                meta_list.append(m)
                by_id[stem] = m
                changed = True
            has_csp = (costumes_dir / f'{stem}_csp.png').exists()
            has_stock = (costumes_dir / f'{stem}_stc.png').exists()
            if m.get('has_csp') != has_csp or m.get('has_stock') != has_stock:
                m['has_csp'] = has_csp
                m['has_stock'] = has_stock
                changed = True

    stale = [m for m in meta_list if m['id'] not in current_ids]
    for m in stale:
        meta_list.remove(m)
        changed = True
        if costumes_dir.exists():
            for p in costumes_dir.glob(f"{m['id']}*"):
                p.unlink()

    return changed


def _run_mexcli(*cli_args):
    """Run a MexCLI command, returning the parsed JSON output (or {})."""
    result = subprocess.run(
        [str(MEXCLI_PATH), *[str(a) for a in cli_args]],
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT), **get_subprocess_args()
    )
    out = _parse_cli_json(result.stdout)
    out['_returncode'] = result.returncode
    return out


def _build_ssm_index(project_dir):
    """Index every sound bank of a scanned build: [(ssm_path, startIndex,
    count)]. Built once per scan — announcer calls are absolute sound IDs
    that can live in ANY bank (usually a global announcer bank, not the
    fighter's own)."""
    index = []
    us_dir = project_dir / 'files' / 'audio' / 'us'
    if not us_dir.exists():
        return index
    for ssm_path in sorted(us_dir.glob('*.ssm')):
        info = _run_mexcli('ssm-info', ssm_path)
        if info.get('success'):
            index.append((ssm_path, info['startIndex'], info['count']))
    return index


def _extract_audio_meta(project_dir, fighter_data, char_dir, ssm_index=None):
    """Pull portable audio out of a scanned build for a fighter:

    - victory theme: the .hps file + track name (MexFighter.FromPackage
      resets victoryTheme on install, so the vault must carry the music
      itself to port it)
    - announcer call: located across the build's sound banks and decoded
      straight to announcer.wav (absolute sound IDs only mean something
      inside the source build)

    Returns a dict of metadata-entry updates.
    """
    updates = {}

    # victory theme
    vt = fighter_data.get('victoryTheme')
    music_json = project_dir / 'data' / 'music.json'
    if isinstance(vt, int) and music_json.exists():
        try:
            with open(music_json, 'r', encoding='utf-8') as f:
                music = json.load(f)
        except (json.JSONDecodeError, OSError):
            music = []
        if 0 <= vt < len(music):
            m = music[vt] or {}
            fname = m.get('fileName')
            src = (project_dir / 'files' / 'audio' / fname) if fname else None
            if src and src.exists():
                shutil.copy2(src, char_dir / 'victory_theme.hps')
                # stale decoded cache, if any
                cache = char_dir / 'audio_cache' / 'victory_theme.wav'
                if cache.exists():
                    cache.unlink()
                updates['victory_theme'] = {
                    'name': (m.get('name') or '').strip() or Path(fname).stem,
                }

    # announcer call: a SEM script id (bank*10000 + script) → resolve to
    # the script's SFX id, then decode from whichever bank's SSM holds it
    call = fighter_data.get('announcerCall')
    if isinstance(call, int) and ssm_index and not (char_dir / 'announcer.wav').exists():
        sem_files = sorted((project_dir / 'files' / 'audio' / 'us').glob('*.sem'))
        if sem_files:
            resolved = _run_mexcli('sem-resolve', sem_files[0], call)
            sfx_id = resolved.get('sfxId')
            if resolved.get('success') and isinstance(sfx_id, int):
                for ssm_path, start, count in ssm_index:
                    idx = sfx_id - start
                    if 0 <= idx < count:
                        out = _run_mexcli('ssm-to-wav', ssm_path, idx, char_dir / 'announcer.wav')
                        if out.get('success'):
                            updates['has_announcer'] = True
                        break

    return updates


def _extract_fighter_ssm(char_dir):
    """Materialize the fighter's sound bank (.ssm from sound.zip inside
    fighter.zip) into audio_cache/bank.ssm. Returns the path or None."""
    cache_dir = char_dir / 'audio_cache'
    bank = cache_dir / 'bank.ssm'
    if bank.exists():
        return bank
    fighter_zip = char_dir / 'fighter.zip'
    if not fighter_zip.exists():
        return None
    import io
    try:
        with zipfile.ZipFile(fighter_zip) as zf:
            sound_entry = next((n for n in zf.namelist()
                                if n.split('/')[-1].lower() == 'sound.zip'), None)
            if sound_entry is None:
                return None
            with zipfile.ZipFile(io.BytesIO(zf.read(sound_entry))) as sz:
                ssm_entry = next((n for n in sz.namelist()
                                  if n.lower().endswith('.ssm')), None)
                if ssm_entry is None:
                    return None
                cache_dir.mkdir(exist_ok=True)
                bank.write_bytes(sz.read(ssm_entry))
                return bank
    except (zipfile.BadZipFile, KeyError):
        return None


def _based_on_from_joint(fighter_data):
    """Derive the donor skeleton from a costume joint symbol, e.g.
    'PlyZelda5K_Share_joint' -> 'Zelda'."""
    for costume in fighter_data.get('costumes', []):
        joint = (costume.get('file') or {}).get('jointSymbol') or ''
        m = re.match(r'Ply(.+?)5K', joint)
        if m:
            return m.group(1)
    return None


def _extract_custom_series(project_dir, series_id, char_dir):
    """Pull a custom series (beyond the vanilla 17) out of a scanned
    project: its icon texture, emblem model, and name. Returns the
    custom_series metadata dict, or None.
    """
    if not isinstance(series_id, int) or series_id < len(SERIES_NAMES):
        return None
    series_json = project_dir / 'data' / 'series.json'
    if not series_json.exists():
        return None
    try:
        with open(series_json, 'r', encoding='utf-8') as f:
            series_list = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
    if series_id >= len(series_list):
        return None

    src = series_list[series_id] or {}
    assets_dir = project_dir / 'assets'

    icon_file = _resolve_asset_png(assets_dir, src.get('icon'))
    if icon_file:
        shutil.copy2(icon_file, char_dir / 'series_icon.png')

    model_ref = src.get('model')
    if model_ref:
        model_file = assets_dir / (model_ref.replace('\\', '/') + '.obj')
        if model_file.exists():
            shutil.copy2(model_file, char_dir / 'series_emblem.obj')

    name = (src.get('name') or '').strip()
    return {
        'name': name or None,
        'source_id': series_id,
        'active': True,
        'has_icon': icon_file is not None,
    }


def _validate_costume_zip(zip_bytes):
    """Check a costume zip has a usable DAT. Returns (dat_name, error)."""
    import io
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            dats = [n for n in zf.namelist()
                    if n.lower().endswith(('.dat', '.usd')) and not n.endswith('/')]
    except zipfile.BadZipFile:
        return None, 'Invalid or corrupted ZIP file'
    if not dats:
        return None, 'ZIP contains no costume .dat file'
    dat_name = Path(dats[0]).name
    # MexCostume.FromZip derives the costume key from stem[4:6]
    if len(Path(dat_name).stem) < 6:
        return None, f'Costume DAT name "{dat_name}" is too short (expected PlXxYy style)'
    return dat_name, None


def _extract_skin_previews(skins_dir, skin_id, zip_bytes):
    """Pull csp/stock PNGs out of a costume zip for vault display.
    Uses the canonical vault naming (_csp.png / _stc.png) so the shared
    skin-editing stack finds them."""
    import io
    has_csp = has_stock = False
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for n in zf.namelist():
            base = n.split('/')[-1].lower()
            if base in ('csp.png', 'portrait.png', 'select.png') and not has_csp:
                (skins_dir / f'{skin_id}_csp.png').write_bytes(zf.read(n))
                has_csp = True
            elif base in ('stc.png', 'stock.png', 'icon.png') and not has_stock:
                (skins_dir / f'{skin_id}_stc.png').write_bytes(zf.read(n))
                has_stock = True
    return has_csp, has_stock


@custom_characters_bp.route('/api/mex/custom-characters/list', methods=['GET'])
def list_custom_characters():
    try:
        metadata = _read_metadata()
        characters = metadata.get('custom_characters', [])
        for char in characters:
            char['icon_url'] = f"/api/mex/custom-characters/{char['slug']}/icon"
        return jsonify({'success': True, 'characters': characters})
    except Exception as e:
        logger.error(f"List custom characters error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def import_custom_character_zip_bytes(zip_data, fallback_name):
    """Import a custom character fighter package (zip bytes) into the vault.
    Returns the metadata entry. Raises ValueError on an invalid package.
    Shared by the dedicated route and the unified /import/file dispatcher."""
    import io
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        names = zf.namelist()

        fighter_json_path = None
        icon_path = None

        for name in names:
            basename = name.split('/')[-1].lower()
            if basename == 'fighter.json':
                fighter_json_path = name
            elif basename == 'icon.png':
                icon_path = name

        if not fighter_json_path:
            raise ValueError('ZIP must contain a fighter.json file')

        fighter_meta = json.loads(zf.read(fighter_json_path))
        fighter_name = fighter_meta.get('name', fallback_name)

        slug = _dedupe_slug(_make_slug(fighter_name))
        char_dir = CUSTOM_CHARACTERS_PATH / slug
        char_dir.mkdir(parents=True, exist_ok=True)

        (char_dir / 'fighter.zip').write_bytes(zip_data)

        with open(char_dir / 'fighter.json', 'w') as f:
            json.dump(fighter_meta, f, indent=2)

        has_css_icon = False
        if icon_path:
            (char_dir / 'css_icon.png').write_bytes(zf.read(icon_path))
            has_css_icon = True

        costume_count = len(fighter_meta.get('costumes', []))

    entry = {
        'slug': slug,
        'name': fighter_name,
        'source': 'zip',
        'date_added': datetime.now().isoformat(),
        'series_id': fighter_meta.get('seriesID', 0),
        'costume_count': costume_count,
        'has_css_icon': has_css_icon
    }

    metadata = _read_metadata()
    metadata['custom_characters'].append(entry)
    _write_metadata(metadata)

    logger.info(f"[OK] Imported custom character '{fighter_name}' as {slug}")
    return entry


@custom_characters_bp.route('/api/mex/custom-characters/import-zip', methods=['POST'])
def import_custom_character_zip():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        uploaded = request.files['file']
        if not uploaded.filename or not uploaded.filename.lower().endswith('.zip'):
            return jsonify({'success': False, 'error': 'File must be a .zip'}), 400

        entry = import_custom_character_zip_bytes(
            uploaded.read(), uploaded.filename.rsplit('.', 1)[0])
        return jsonify({'success': True, 'character': entry})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except zipfile.BadZipFile:
        return jsonify({'success': False, 'error': 'Invalid or corrupted ZIP file'}), 400
    except Exception as e:
        logger.error(f"Import custom character ZIP error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def _extract_custom_characters_from_project(project_dir, source_label):
    """Extract custom characters from a MEX project directory into the vault.
    Returns (imported, skipped) name lists."""
    fighters_dir = project_dir / 'data' / 'fighters'
    assets_dir = project_dir / 'assets'
    project_path = project_dir / 'project.mexproj'

    if not fighters_dir.exists():
        raise FileNotFoundError('Project data/fighters/ directory not found')

    with open(project_path, 'r') as f:
        proj_data = json.load(f)

    fighter_files = proj_data.get('fighterSaveMap', {}).get('filePaths', [])
    if not fighter_files:
        return [], []

    metadata = _read_metadata()
    existing_names = {c['name'].lower() for c in metadata.get('custom_characters', [])}

    # one pass over the build's sound banks for announcer-call resolution
    ssm_index = _build_ssm_index(project_dir)

    imported = []
    skipped = []

    mexcli_path = str(MEXCLI_PATH)

    for fighter_index, fighter_file in enumerate(fighter_files):
        fighter_json_path = fighters_dir / fighter_file
        if not fighter_json_path.exists():
            continue

        try:
            with open(fighter_json_path, 'r') as f:
                fighter_data = json.load(f)

            fighter_name = fighter_data.get('name', '')
            if not fighter_name or _norm_fighter_name(fighter_name) in VANILLA_FIGHTER_NAMES_NORM:
                continue

            if fighter_name.lower() in existing_names:
                existing = next((c for c in metadata.get('custom_characters', [])
                                 if c['name'].lower() == fighter_name.lower()), None)
                existing_dir = CUSTOM_CHARACTERS_PATH / existing['slug'] if existing else None
                if existing is not None and existing_dir.exists():
                    # Backfill custom series for characters scanned before
                    # series extraction existed (e.g. Chun-Li's series 19)
                    if not existing.get('custom_series'):
                        cs = _extract_custom_series(
                            project_dir, fighter_data.get('seriesID', 0), existing_dir)
                        if cs:
                            existing['custom_series'] = cs
                            _write_metadata(metadata)
                            logger.info(f"Backfilled custom series for '{fighter_name}': {cs}")

                    # Refresh result banners + CSS icon inside fighter.zip —
                    # an old importer bug assigned every custom fighter its
                    # neighbour's banner (Wolf showed SHEIK etc.)
                    assets_obj = fighter_data.get('assets', {})
                    replace = {}
                    for ref_key, entry_name in (('resultBannerBig', 'big_banner.png'),
                                                ('resultSmallBig', 'small_banner.png'),
                                                ('cssIcon', 'icon.png')):
                        asset_file = _resolve_asset_png(assets_dir, assets_obj.get(ref_key))
                        if asset_file:
                            replace[entry_name] = asset_file.read_bytes()
                    if replace and (existing_dir / 'fighter.zip').exists():
                        _rewrite_fighter_zip(existing_dir, replace_entries=replace)
                        if 'icon.png' in replace:
                            (existing_dir / 'css_icon.png').write_bytes(replace['icon.png'])
                        logger.info(f"Refreshed {sorted(replace)} for '{fighter_name}'")

                    # backfill portable audio (victory theme, announcer call)
                    audio_updates = _extract_audio_meta(project_dir, fighter_data, existing_dir, ssm_index)
                    if audio_updates:
                        existing.update(audio_updates)
                        _write_metadata(metadata)
                skipped.append(fighter_name)
                continue

            slug = _dedupe_slug(_make_slug(fighter_name))
            char_dir = CUSTOM_CHARACTERS_PATH / slug
            char_dir.mkdir(parents=True, exist_ok=True)

            # Export full fighter ZIP via MexCLI
            zip_path = char_dir / 'fighter.zip'
            if Path(mexcli_path).exists():
                export_cmd = [mexcli_path, 'export-fighter', str(project_path), str(fighter_index), str(zip_path)]
                export_result = subprocess.run(
                    export_cmd, capture_output=True, text=True,
                    cwd=str(PROJECT_ROOT), **get_subprocess_args()
                )
                if export_result.returncode != 0:
                    logger.warning(f"Failed to export fighter ZIP for '{fighter_name}': {export_result.stderr or export_result.stdout}")

            with open(char_dir / 'fighter.json', 'w') as f:
                json.dump(fighter_data, f, indent=2)

            assets_obj = fighter_data.get('assets', {})
            has_css_icon = False
            icon_ref = assets_obj.get('cssIcon')
            icon_file = _resolve_asset_png(assets_dir, icon_ref)
            if icon_file:
                shutil.copy2(icon_file, char_dir / 'css_icon.png')
                has_css_icon = True

            costumes = fighter_data.get('costumes', [])
            for i, costume in enumerate(costumes):
                csp_ref = costume.get('csp')
                csp_file = _resolve_asset_png(assets_dir, csp_ref)
                if csp_file:
                    shutil.copy2(csp_file, char_dir / f'csp_{i}.png')
                stock_ref = costume.get('icon')
                stock_file = _resolve_asset_png(assets_dir, stock_ref)
                if stock_file:
                    shutil.copy2(stock_file, char_dir / f'stock_{i}.png')

            entry = {
                'slug': slug,
                'name': fighter_name,
                'source': source_label,
                'date_added': datetime.now().isoformat(),
                'series_id': fighter_data.get('seriesID', 0),
                'costume_count': len(costumes),
                'has_css_icon': has_css_icon
            }

            custom_series = _extract_custom_series(
                project_dir, fighter_data.get('seriesID', 0), char_dir)
            if custom_series:
                entry['custom_series'] = custom_series

            entry.update(_extract_audio_meta(project_dir, fighter_data, char_dir, ssm_index))

            metadata['custom_characters'].append(entry)
            existing_names.add(fighter_name.lower())
            imported.append(fighter_name)

        except (json.JSONDecodeError, KeyError):
            continue

    if imported:
        _write_metadata(metadata)

    return imported, skipped


@custom_characters_bp.route('/api/mex/custom-characters/scan-iso', methods=['POST'])
def scan_iso_for_custom_characters():
    """Create a temp MEX project from an ISO, extract custom characters, clean up."""
    try:
        data = request.json or {}
        iso_path = data.get('isoPath', '').strip()
        if not iso_path:
            return jsonify({'success': False, 'error': 'Missing isoPath parameter'}), 400

        iso_file = Path(iso_path)
        if not iso_file.exists():
            return jsonify({'success': False, 'error': f'ISO not found: {iso_path}'}), 404
        if iso_file.suffix.lower() not in ('.iso', '.gcm'):
            return jsonify({'success': False, 'error': 'File must be an .iso or .gcm'}), 400

        mexcli_path = str(MEXCLI_PATH)
        if not Path(mexcli_path).exists():
            return jsonify({'success': False, 'error': 'MexCLI not found. Build MexCLI first.'}), 500

        temp_dir = tempfile.mkdtemp(prefix='nucleus_char_scan_')
        try:
            logger.info(f"Scanning ISO for custom characters: {iso_path}")

            cmd = [mexcli_path, 'import-iso', str(iso_file), temp_dir, 'temp_scan']
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                cwd=str(PROJECT_ROOT), **get_subprocess_args()
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or 'Unknown error'
                logger.error(f"MexCLI import-iso failed: {error_msg}")
                return jsonify({'success': False, 'error': f'Failed to open ISO: {error_msg}'}), 500

            project_dir = Path(temp_dir)
            if not (project_dir / 'project.mexproj').exists():
                return jsonify({'success': False, 'error': 'MexCLI created project but .mexproj not found'}), 500

            imported, skipped = _extract_custom_characters_from_project(project_dir, 'iso-scan')

            logger.info(f"[OK] ISO character scan: imported {len(imported)}, skipped {len(skipped)}")
            return jsonify({
                'success': True,
                'imported': imported,
                'skipped': skipped,
                'message': f"Imported {len(imported)} custom character(s), skipped {len(skipped)} duplicate(s)"
            })
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logger.error(f"Scan ISO for custom characters error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/icon', methods=['GET'])
def get_custom_character_icon(slug):
    icon_path = CUSTOM_CHARACTERS_PATH / slug / 'css_icon.png'
    if icon_path.exists():
        return send_file(icon_path, mimetype='image/png')
    return jsonify({'success': False, 'error': 'Icon not found'}), 404


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/detail', methods=['GET'])
def get_custom_character_detail(slug):
    """Return full character detail including costume info with image URLs."""
    try:
        char_dir = CUSTOM_CHARACTERS_PATH / slug
        fighter_json_path = char_dir / 'fighter.json'
        if not fighter_json_path.exists():
            return jsonify({'success': False, 'error': 'Character not found'}), 404

        with open(fighter_json_path, 'r') as f:
            fighter_data = json.load(f)

        metadata = _read_metadata()
        entry = _find_entry(metadata, slug) or {}

        # Keep the costume mirror (costume_meta + materialized zips) in sync
        # so the shared edit stack can open bundled costumes directly
        if entry and _sync_costume_meta(entry, char_dir, fighter_data):
            _write_metadata(metadata)
        meta_by_id = {m['id']: m for m in entry.get('costume_meta', [])}

        costumes = []
        for i, costume in enumerate(fighter_data.get('costumes', [])):
            dat = (costume.get('file') or {}).get('fileName')
            stem = Path(dat).stem if dat else None
            meta = meta_by_id.get(stem, {})
            # prefer the materialized (editable) preview over the scan-time one
            if stem and (char_dir / 'costumes' / f'{stem}_csp.png').exists():
                csp_url = f"/storage/custom_characters/{slug}/costumes/{stem}_csp.png"
            elif (char_dir / f'csp_{i}.png').exists():
                csp_url = f"/api/mex/custom-characters/{slug}/csp/{i}"
            else:
                csp_url = None
            if stem and (char_dir / 'costumes' / f'{stem}_stc.png').exists():
                stock_url = f"/storage/custom_characters/{slug}/costumes/{stem}_stc.png"
            elif (char_dir / f'stock_{i}.png').exists():
                stock_url = f"/api/mex/custom-characters/{slug}/stock/{i}"
            else:
                stock_url = None
            costumes.append({
                **meta,
                'index': i,
                'edit_id': stem,
                'name': meta.get('color') or costume.get('name', f'Costume {i}'),
                'dat': dat,
                'csp_url': csp_url,
                'stock_url': stock_url,
            })

        # which fixed-name assets exist in fighter.zip (banners are only
        # in the zip; the css icon also has a vault display copy)
        zip_assets = {}
        basenames = set()
        zip_path = char_dir / 'fighter.zip'
        if zip_path.exists():
            with zipfile.ZipFile(zip_path) as zf:
                basenames = {n.split('/')[-1].lower() for n in zf.namelist()}
            for key, (entry_name, size) in FIGHTER_ASSET_SPECS.items():
                if entry_name in basenames:
                    zip_assets[key] = {
                        'url': f"/api/mex/custom-characters/{slug}/zip-asset/{key}",
                        'width': size[0],
                        'height': size[1],
                    }

        added_skins = []
        for skin in entry.get('added_skins', []):
            sid = skin['id']
            # full entry (canonical skin fields) so the shared EditModal /
            # CSP manager stack can drive it, plus display conveniences
            added_skins.append({
                **skin,
                'name': skin.get('color') or skin.get('name') or 'Custom Skin',
                'csp_url': f"/api/mex/custom-characters/{slug}/skins/{sid}/csp" if skin.get('has_csp') else None,
                'stock_url': f"/api/mex/custom-characters/{slug}/skins/{sid}/stock" if skin.get('has_stock') else None,
            })

        cs = entry.get('custom_series')
        custom_series = None
        if cs:
            custom_series = {
                'name': cs.get('name'),
                'active': bool(cs.get('active')),
                'source_id': cs.get('source_id'),
                'icon_url': (f"/api/mex/custom-characters/{slug}/custom-series-icon"
                             if (char_dir / 'series_icon.png').exists() else None),
            }

        series_id = fighter_data.get('seriesID', 0)
        detail = {
            'name': fighter_data.get('name', ''),
            'series_id': series_id,
            'series_name': _series_name(series_id),
            'series_icon_url': (f"/api/mex/custom-characters/series-icon/{series_id}"
                                if isinstance(series_id, int) and _series_icon_path(series_id) else None),
            'custom_series': custom_series,
            'can_wall_jump': fighter_data.get('canWallJump', False),
            'sound_bank': fighter_data.get('soundBank'),
            'victory_theme': fighter_data.get('victoryTheme'),
            'victory_theme_info': ({
                'name': (entry.get('victory_theme') or {}).get('name'),
                'available': (char_dir / 'victory_theme.hps').exists(),
            } if entry.get('victory_theme') else None),
            'announcer_available': (char_dir / 'announcer.wav').exists(),
            'announcer_call': fighter_data.get('announcerCall'),
            'target_test_stage': fighter_data.get('targetTestStage'),
            'based_on': _based_on_from_joint(fighter_data),
            'anim_count': (fighter_data.get('files') or {}).get('animCount'),
            'has_kirby_cap': bool((fighter_data.get('files') or {}).get('kirbyCapFileName')),
            'has_sound_pack': 'sound.zip' in basenames,
            'ending_movies': sum(1 for v in (fighter_data.get('media') or {}).values() if v),
            'costumes': costumes,
            'added_skins': added_skins,
            'has_css_icon': (char_dir / 'css_icon.png').exists(),
            'icon_url': f"/api/mex/custom-characters/{slug}/icon",
            'zip_assets': zip_assets,
            'files': fighter_data.get('files', {}),
        }

        return jsonify({'success': True, 'detail': detail})
    except Exception as e:
        logger.error(f"Get custom character detail error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/csp/<int:index>', methods=['GET'])
def get_custom_character_csp(slug, index):
    csp_path = CUSTOM_CHARACTERS_PATH / slug / f'csp_{index}.png'
    if csp_path.exists():
        return send_file(csp_path, mimetype='image/png')
    return jsonify({'success': False, 'error': 'CSP not found'}), 404


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/stock/<int:index>', methods=['GET'])
def get_custom_character_stock(slug, index):
    stock_path = CUSTOM_CHARACTERS_PATH / slug / f'stock_{index}.png'
    if stock_path.exists():
        return send_file(stock_path, mimetype='image/png')
    return jsonify({'success': False, 'error': 'Stock icon not found'}), 404


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/delete', methods=['POST'])
def delete_custom_character(slug):
    try:
        char_dir = CUSTOM_CHARACTERS_PATH / slug
        if char_dir.exists():
            shutil.rmtree(char_dir)

        metadata = _read_metadata()
        metadata['custom_characters'] = [
            c for c in metadata.get('custom_characters', []) if c['slug'] != slug
        ]
        _write_metadata(metadata)

        logger.info(f"[OK] Deleted custom character '{slug}'")
        return jsonify({'success': True, 'message': f'Deleted {slug}'})
    except Exception as e:
        logger.error(f"Delete custom character error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/rename', methods=['POST'])
def rename_custom_character(slug):
    try:
        data = request.json
        new_name = data.get('newName', '').strip()
        if not new_name:
            return jsonify({'success': False, 'error': 'New name is required'}), 400

        metadata = _read_metadata()

        for existing in metadata.get('custom_characters', []):
            if existing['slug'] != slug and existing['name'].lower() == new_name.lower():
                return jsonify({'success': False, 'error': f"A character named '{existing['name']}' already exists"}), 400

        char_entry = None
        for c in metadata.get('custom_characters', []):
            if c['slug'] == slug:
                c['name'] = new_name
                char_entry = c
                break

        if not char_entry:
            return jsonify({'success': False, 'error': f'Character {slug} not found'}), 404

        fighter_json_path = CUSTOM_CHARACTERS_PATH / slug / 'fighter.json'
        if fighter_json_path.exists():
            with open(fighter_json_path, 'r') as f:
                fighter_data = json.load(f)
            fighter_data['name'] = new_name
            with open(fighter_json_path, 'w') as f:
                json.dump(fighter_data, f, indent=2)

        # add-fighter reads the zip's own fighter.json — keep it in sync so
        # the rename survives install
        def _set_name(meta):
            meta['name'] = new_name
            return meta
        _rewrite_fighter_zip(CUSTOM_CHARACTERS_PATH / slug, mutate_json=_set_name)

        _write_metadata(metadata)

        logger.info(f"[OK] Renamed custom character '{slug}' to '{new_name}'")
        return jsonify({'success': True, 'character': char_entry})
    except Exception as e:
        logger.error(f"Rename custom character error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/export', methods=['GET'])
def export_custom_character(slug):
    zip_path = CUSTOM_CHARACTERS_PATH / slug / 'fighter.zip'
    if zip_path.exists():
        return send_file(zip_path, as_attachment=True, download_name=f'{slug}.zip')

    return jsonify({'success': False, 'error': 'Fighter ZIP not found (imported from project scan?)'}), 404


def _resolve_install_series(entry, char_dir, project_path, mexcli_path):
    """Work out what seriesID the fighter should use in the TARGET project.

    Returns (series_id_or_None, warnings). None means "leave fighter.json
    as-is". A custom series (extracted from the source build) is matched by
    name in the target project or created there via `mexcli add-series`.
    A dangling seriesID (points past the target's series list) falls back
    to Smash Bros. so the install never references a missing series.
    """
    warnings = []
    project_dir = Path(project_path).parent
    series_json = project_dir / 'data' / 'series.json'
    target_series = None
    if series_json.exists():
        try:
            with open(series_json, 'r', encoding='utf-8') as f:
                target_series = json.load(f)
        except (json.JSONDecodeError, OSError):
            target_series = None
    target_count = len(target_series) if target_series is not None else len(SERIES_NAMES)

    cs = entry.get('custom_series')
    icon = char_dir / 'series_icon.png'
    if cs and cs.get('active') and icon.exists():
        name = (cs.get('name') or '').strip() or f"Series {cs.get('source_id', '?')}"

        if target_series is not None:
            for i, s in enumerate(target_series):
                if (s.get('name') or '').strip().lower() == name.lower():
                    return i, warnings

        cmd = [mexcli_path, 'add-series', str(project_path), name, str(icon)]
        emblem = char_dir / 'series_emblem.obj'
        if emblem.exists():
            cmd.append(str(emblem))
        logger.info(f"Creating series '{name}' in project: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            cwd=str(PROJECT_ROOT), **get_subprocess_args()
        )
        if result.returncode == 0:
            out = _parse_cli_json(result.stdout)
            if 'seriesId' in out:
                return out['seriesId'], warnings
        warnings.append(f"Could not create series '{name}' in project; franchise icon skipped")
        logger.warning(f"add-series failed: {result.stderr or result.stdout}")

    # No (usable) custom series — make sure the fighter's seriesID isn't dangling
    sid = entry.get('series_id', 0)
    if isinstance(sid, int) and sid >= target_count:
        warnings.append(f"Series {sid} does not exist in this project; defaulted to Smash Bros.")
        return 11, warnings
    return None, warnings


@custom_characters_bp.route('/api/mex/custom-characters/install', methods=['POST'])
def install_custom_character():
    """Install a custom character from the vault into the currently open project."""
    temp_zip = None
    try:
        data = request.json or {}
        slug = data.get('slug', '').strip()
        if not slug:
            return jsonify({'success': False, 'error': 'Missing slug parameter'}), 400

        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No project loaded. Open a project first.'}), 400

        char_dir = CUSTOM_CHARACTERS_PATH / slug
        zip_path = char_dir / 'fighter.zip'
        if not zip_path.exists():
            return jsonify({'success': False, 'error': f'Fighter ZIP not found for "{slug}". Re-scan the ISO to generate it.'}), 404

        mexcli_path = str(MEXCLI_PATH)
        if not Path(mexcli_path).exists():
            return jsonify({'success': False, 'error': 'MexCLI not found'}), 500

        metadata = _read_metadata()
        entry = _find_entry(metadata, slug) or {}

        # Custom franchise: re-create the series in the target project (or
        # match an existing one by name) and point the fighter at it
        series_id, series_warnings = _resolve_install_series(
            entry, char_dir, project_path, mexcli_path)

        # Fold costume edits back into the fighter zip: CSP/stock changes
        # live in the materialized per-costume zips (costumes/<stem>.zip),
        # renames in costume_meta — installs must carry both
        costumes_dir = char_dir / 'costumes'
        meta_by_id = {m['id']: m for m in entry.get('costume_meta', [])}
        replace_entries = {}
        if costumes_dir.exists():
            for f in costumes_dir.glob('*.zip'):
                if Path(f.name).stem in meta_by_id:
                    replace_entries[f.name] = f.read_bytes()

        def _mutate_install_json(meta):
            if series_id is not None:
                meta['seriesID'] = series_id
            for costume in meta.get('costumes', []):
                stem = Path((costume.get('file') or {}).get('fileName') or '').stem
                m = meta_by_id.get(stem)
                if m and m.get('color'):
                    costume['name'] = m['color']
            return meta

        install_zip = zip_path
        if series_id is not None or replace_entries:
            temp_zip = Path(tempfile.mktemp(suffix='.zip', prefix='nucleus_fighter_'))
            _rewrite_zip_fighter_json(zip_path, temp_zip,
                                      mutate_json=_mutate_install_json,
                                      replace_entries=replace_entries)
            install_zip = temp_zip

        cmd = [mexcli_path, 'add-fighter', str(project_path), str(install_zip)]
        logger.info(f"Installing custom character '{slug}': {' '.join(cmd)}")

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            cwd=str(PROJECT_ROOT), **get_subprocess_args()
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or 'Unknown error'
            logger.error(f"add-fighter failed: {error_msg}")
            return jsonify({'success': False, 'error': f'Failed to add fighter: {error_msg}'}), 500

        cli_output = _parse_cli_json(result.stdout)
        fighter_name = cli_output.get('name', slug)

        # Bring along any custom skins added to this character in the vault
        skins_dir = CUSTOM_CHARACTERS_PATH / slug / 'skins'
        skins_installed = 0
        skin_warnings = []
        for skin in entry.get('added_skins', []):
            skin_zip = skins_dir / skin['filename']
            if not skin_zip.exists():
                skin_warnings.append(f"Skin '{skin.get('color') or skin.get('name')}' file missing, skipped")
                continue
            skin_cmd = [mexcli_path, 'import-costume', str(project_path), fighter_name, str(skin_zip)]
            skin_result = subprocess.run(
                skin_cmd, capture_output=True, text=True,
                cwd=str(PROJECT_ROOT), **get_subprocess_args()
            )
            if skin_result.returncode == 0:
                skins_installed += 1
            else:
                err = skin_result.stderr or skin_result.stdout or 'unknown error'
                logger.warning(f"import-costume failed for skin '{skin.get('color') or skin.get('name')}': {err}")
                skin_warnings.append(f"Skin '{skin.get('color') or skin.get('name')}' failed to import")

        # Port the victory theme: add the track to the target project (or
        # reuse a same-named one) and point the fighter at it — add-fighter
        # itself resets victoryTheme to the default
        victory_ported = False
        vt_file = char_dir / 'victory_theme.hps'
        vt_meta = entry.get('victory_theme') or {}
        if vt_file.exists() and vt_meta.get('name'):
            music_out = _run_mexcli('add-music', project_path, vt_file, vt_meta['name'])
            if music_out.get('success') and 'musicId' in music_out:
                set_out = _run_mexcli('set-fighter-music', project_path,
                                      fighter_name, music_out['musicId'])
                victory_ported = bool(set_out.get('success'))
            if not victory_ported:
                skin_warnings.append(f"Victory theme '{vt_meta['name']}' could not be ported")
                logger.warning(f"Victory theme port failed for {slug}")
            else:
                logger.info(f"Ported victory theme '{vt_meta['name']}' "
                            f"(musicId {music_out['musicId']}) for {fighter_name}")

        import time
        time.sleep(0.15)
        reload_mex_manager()

        logger.info(f"[OK] Installed custom character '{slug}' into project "
                    f"(+{skins_installed} custom skin(s))")
        message = f"Added {fighter_name} to project"
        if skins_installed:
            message += f" with {skins_installed} custom skin(s)"
        if victory_ported:
            message += f", victory theme '{vt_meta['name']}'"
        return jsonify({
            'success': True,
            'message': message,
            'name': fighter_name,
            'costumeCount': cli_output.get('costumeCount', 0),
            'customSkinsInstalled': skins_installed,
            'seriesId': series_id,
            'victoryThemePorted': victory_ported,
            'warnings': series_warnings + skin_warnings,
        })
    except Exception as e:
        logger.error(f"Install custom character error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if temp_zip is not None and temp_zip.exists():
            temp_zip.unlink()


@custom_characters_bp.route('/api/mex/custom-characters/remove-from-project', methods=['POST'])
def remove_custom_character_from_project():
    """Remove a custom character from the currently open project."""
    try:
        data = request.json or {}
        fighter_name = data.get('name', '').strip()
        if not fighter_name:
            return jsonify({'success': False, 'error': 'Missing name parameter'}), 400

        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No project loaded.'}), 400

        mexcli_path = str(MEXCLI_PATH)
        cmd = [mexcli_path, 'remove-fighter', str(project_path), fighter_name]
        logger.info(f"Removing fighter '{fighter_name}': {' '.join(cmd)}")

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            cwd=str(PROJECT_ROOT), **get_subprocess_args()
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or 'Unknown error'
            return jsonify({'success': False, 'error': f'Failed to remove fighter: {error_msg}'}), 500

        import time
        time.sleep(0.15)
        reload_mex_manager()

        logger.info(f"[OK] Removed fighter '{fighter_name}' from project")
        return jsonify({'success': True, 'message': f'Removed {fighter_name}'})
    except Exception as e:
        logger.error(f"Remove fighter error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= Custom skins (vault, per custom character) =============

@custom_characters_bp.route('/api/mex/custom-characters/<slug>/skins/add', methods=['POST'])
def add_custom_character_skin(slug):
    """Add a custom skin to a vault custom character.

    Accepts either:
      - multipart upload: 'file' = costume .zip (PlXxYy.dat + csp.png/stc.png)
        or a bare .dat, optional 'name' field
      - JSON {character, skinId}: copy a canonical skin from the vault
        (used by drag-and-drop from a canonical character)
    """
    try:
        char_dir = CUSTOM_CHARACTERS_PATH / slug
        if not (char_dir / 'fighter.json').exists():
            return jsonify({'success': False, 'error': 'Character not found'}), 404

        metadata = _read_metadata()
        entry = _find_entry(metadata, slug)
        if entry is None:
            return jsonify({'success': False, 'error': 'Character not found in metadata'}), 404

        skin_name = None
        source_character = None
        src_skin = None

        if 'file' in request.files:
            uploaded = request.files['file']
            fname = (uploaded.filename or '').lower()
            raw = uploaded.read()
            skin_name = (request.form.get('name') or Path(uploaded.filename).stem).strip()
            if fname.endswith(('.dat', '.usd')):
                # wrap a bare DAT into a costume zip
                import io
                buf = io.BytesIO()
                with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
                    zf.writestr(Path(uploaded.filename).name, raw)
                zip_bytes = buf.getvalue()
            elif fname.endswith('.zip'):
                zip_bytes = raw
            else:
                return jsonify({'success': False, 'error': 'File must be a .zip or .dat costume'}), 400
        else:
            data = request.get_json(silent=True) or {}
            source_character = (data.get('character') or '').strip()
            skin_id_src = (data.get('skinId') or '').strip()
            if not source_character or not skin_id_src:
                return jsonify({'success': False, 'error': 'Provide a file or {character, skinId}'}), 400

            char_meta = metadata.get('characters', {}).get(source_character)
            if not char_meta:
                return jsonify({'success': False, 'error': f'Character {source_character} not found'}), 404
            src_skin = next((s for s in char_meta.get('skins', [])
                             if s.get('id') == skin_id_src and s.get('type') != 'folder'), None)
            if not src_skin:
                return jsonify({'success': False, 'error': f'Skin {skin_id_src} not found'}), 404
            src_zip = STORAGE_PATH / source_character / src_skin['filename']
            if not src_zip.exists():
                return jsonify({'success': False, 'error': f'Skin zip missing: {src_skin["filename"]}'}), 404
            zip_bytes = src_zip.read_bytes()
            skin_name = src_skin.get('color') or Path(src_skin['filename']).stem

        dat_name, err = _validate_costume_zip(zip_bytes)
        if err:
            return jsonify({'success': False, 'error': err}), 400

        import uuid
        skin_id = uuid.uuid4().hex[:8]
        skins_dir = char_dir / 'skins'
        skins_dir.mkdir(exist_ok=True)
        (skins_dir / f'{skin_id}.zip').write_bytes(zip_bytes)
        has_csp, has_stock = _extract_skin_previews(skins_dir, skin_id, zip_bytes)

        skin_entry = {
            'id': skin_id,
            # canonical field name so the shared skin-edit stack works on it
            'color': skin_name or Path(dat_name).stem,
            'filename': f'{skin_id}.zip',
            'dat_name': dat_name,
            'has_csp': has_csp,
            'has_stock': has_stock,
            'source_character': source_character,
            'date_added': datetime.now().isoformat(),
        }
        if src_skin is not None:
            # carry slippi status over from the canonical source skin
            for field in ('slippi_safe', 'slippi_tested', 'slippi_test_date', 'slippi_manual_override'):
                if field in src_skin:
                    skin_entry[field] = src_skin[field]
        entry.setdefault('added_skins', []).append(skin_entry)
        _write_metadata(metadata)

        logger.info(f"[OK] Added custom skin '{skin_entry['color']}' to {slug}")
        return jsonify({'success': True, 'skin': {
            **skin_entry,
            'name': skin_entry['color'],
            'csp_url': f"/api/mex/custom-characters/{slug}/skins/{skin_id}/csp" if has_csp else None,
            'stock_url': f"/api/mex/custom-characters/{slug}/skins/{skin_id}/stock" if has_stock else None,
        }})
    except Exception as e:
        logger.error(f"Add custom skin error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/skins/<skin_id>/remove', methods=['POST'])
def remove_custom_character_skin(slug, skin_id):
    try:
        metadata = _read_metadata()
        entry = _find_entry(metadata, slug)
        if entry is None:
            return jsonify({'success': False, 'error': 'Character not found'}), 404

        skins = entry.get('added_skins', [])
        skin = next((s for s in skins if s['id'] == skin_id), None)
        if skin is None:
            return jsonify({'success': False, 'error': 'Skin not found'}), 404

        # remove the zip + every derived file (csp/stc/HD/alt csps)
        skins_dir = CUSTOM_CHARACTERS_PATH / slug / 'skins'
        if skins_dir.exists():
            for p in skins_dir.glob(f'{skin_id}*'):
                p.unlink()

        entry['added_skins'] = [s for s in skins if s['id'] != skin_id]
        _write_metadata(metadata)

        logger.info(f"[OK] Removed custom skin '{skin.get('color') or skin.get('name')}' from {slug}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Remove custom skin error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/skins/<skin_id>/csp', methods=['GET'])
def get_custom_character_skin_csp(slug, skin_id):
    p = CUSTOM_CHARACTERS_PATH / slug / 'skins' / f'{skin_id}_csp.png'
    if p.exists():
        return send_file(p, mimetype='image/png')
    return jsonify({'success': False, 'error': 'CSP not found'}), 404


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/skins/<skin_id>/stock', methods=['GET'])
def get_custom_character_skin_stock(slug, skin_id):
    for fname in (f'{skin_id}_stc.png', f'{skin_id}_stock.png'):
        p = CUSTOM_CHARACTERS_PATH / slug / 'skins' / fname
        if p.exists():
            return send_file(p, mimetype='image/png')
    return jsonify({'success': False, 'error': 'Stock icon not found'}), 404


def _drop_bundled_costume(char_dir, fighter_data, index):
    """Remove costume `index` from storage fighter.json, the fighter.zip
    (embedded fighter.json + inner costume zip — add-fighter re-reads both)
    and shift csp_N/stock_N previews. Returns the removed costume dict."""
    removed = fighter_data['costumes'].pop(index)
    dat_name = (removed.get('file') or {}).get('fileName', '')
    inner_zip = f"{Path(dat_name).stem}.zip" if dat_name else None

    with open(char_dir / 'fighter.json', 'w') as f:
        json.dump(fighter_data, f, indent=2)

    def _drop_costume(meta):
        zcost = meta.get('costumes', [])
        if index < len(zcost):
            zcost.pop(index)
        return meta
    _rewrite_fighter_zip(char_dir, mutate_json=_drop_costume,
                         drop_entries=[inner_zip] if inner_zip else None)

    for prefix in ('csp', 'stock'):
        removed_png = char_dir / f'{prefix}_{index}.png'
        if removed_png.exists():
            removed_png.unlink()
        i = index + 1
        while (char_dir / f'{prefix}_{i}.png').exists():
            (char_dir / f'{prefix}_{i}.png').rename(char_dir / f'{prefix}_{i - 1}.png')
            i += 1

    return removed


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/costumes/<int:index>/remove', methods=['POST'])
def remove_bundled_costume(slug, index):
    """Remove one of the costumes bundled in fighter.zip."""
    try:
        char_dir = CUSTOM_CHARACTERS_PATH / slug
        fighter_json_path = char_dir / 'fighter.json'
        if not fighter_json_path.exists():
            return jsonify({'success': False, 'error': 'Character not found'}), 404

        with open(fighter_json_path, 'r') as f:
            fighter_data = json.load(f)

        costumes = fighter_data.get('costumes', [])
        if index < 0 or index >= len(costumes):
            return jsonify({'success': False, 'error': f'Invalid costume index {index}'}), 400
        if len(costumes) <= 1:
            return jsonify({'success': False, 'error': 'A fighter needs at least one costume'}), 400

        removed = _drop_bundled_costume(char_dir, fighter_data, index)

        metadata = _read_metadata()
        entry = _find_entry(metadata, slug)
        if entry is not None:
            entry['costume_count'] = len(costumes)
            _write_metadata(metadata)

        dat_name = (removed.get('file') or {}).get('fileName', '')
        logger.info(f"[OK] Removed bundled costume {index} ({dat_name}) from {slug}")
        return jsonify({'success': True, 'costume_count': len(costumes)})
    except Exception as e:
        logger.error(f"Remove bundled costume error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/costumes/<int:index>/to-skin', methods=['POST'])
def bundled_costume_to_skin(slug, index):
    """Move a bundled costume into the Custom Skins area (drag-down in the
    UI). The costume's inner zip is lifted out of fighter.zip into skins/;
    on install it comes back via import-costume like any added skin."""
    try:
        char_dir = CUSTOM_CHARACTERS_PATH / slug
        fighter_json_path = char_dir / 'fighter.json'
        if not fighter_json_path.exists():
            return jsonify({'success': False, 'error': 'Character not found'}), 404

        metadata = _read_metadata()
        entry = _find_entry(metadata, slug)
        if entry is None:
            return jsonify({'success': False, 'error': 'Character not found in metadata'}), 404

        with open(fighter_json_path, 'r') as f:
            fighter_data = json.load(f)

        costumes = fighter_data.get('costumes', [])
        if index < 0 or index >= len(costumes):
            return jsonify({'success': False, 'error': f'Invalid costume index {index}'}), 400
        if len(costumes) <= 1:
            return jsonify({'success': False, 'error': 'A fighter needs at least one bundled costume'}), 400

        costume = costumes[index]
        dat_name = (costume.get('file') or {}).get('fileName', '')
        if not dat_name:
            return jsonify({'success': False, 'error': 'Costume has no DAT file'}), 400
        inner_name = f"{Path(dat_name).stem}.zip"

        zip_bytes = None
        with zipfile.ZipFile(char_dir / 'fighter.zip') as zf:
            for n in zf.namelist():
                if n.split('/')[-1].lower() == inner_name.lower():
                    zip_bytes = zf.read(n)
                    break
        if zip_bytes is None:
            return jsonify({'success': False, 'error': f'Costume zip {inner_name} not found in fighter.zip'}), 404

        _, err = _validate_costume_zip(zip_bytes)
        if err:
            return jsonify({'success': False, 'error': err}), 400

        import uuid
        skin_id = uuid.uuid4().hex[:8]
        skins_dir = char_dir / 'skins'
        skins_dir.mkdir(exist_ok=True)
        (skins_dir / f'{skin_id}.zip').write_bytes(zip_bytes)
        has_csp, has_stock = _extract_skin_previews(skins_dir, skin_id, zip_bytes)

        # Inner costume zips usually carry csp/stc, but fall back to the
        # character-dir previews before they get shifted by the removal
        if not has_csp and (char_dir / f'csp_{index}.png').exists():
            shutil.copy2(char_dir / f'csp_{index}.png', skins_dir / f'{skin_id}_csp.png')
            has_csp = True
        if not has_stock and (char_dir / f'stock_{index}.png').exists():
            shutil.copy2(char_dir / f'stock_{index}.png', skins_dir / f'{skin_id}_stc.png')
            has_stock = True

        skin_entry = {
            'id': skin_id,
            'color': costume.get('name') or Path(dat_name).stem,
            'filename': f'{skin_id}.zip',
            'dat_name': dat_name,
            'has_csp': has_csp,
            'has_stock': has_stock,
            'source_character': None,
            'date_added': datetime.now().isoformat(),
        }

        _drop_bundled_costume(char_dir, fighter_data, index)

        entry.setdefault('added_skins', []).append(skin_entry)
        entry['costume_count'] = len(fighter_data.get('costumes', []))
        _write_metadata(metadata)

        logger.info(f"[OK] Moved bundled costume {index} ({dat_name}) of {slug} to custom skins")
        return jsonify({'success': True, 'skin': {
            **skin_entry,
            'name': skin_entry['color'],
            'csp_url': f"/api/mex/custom-characters/{slug}/skins/{skin_id}/csp" if has_csp else None,
            'stock_url': f"/api/mex/custom-characters/{slug}/skins/{skin_id}/stock" if has_stock else None,
        }, 'costume_count': len(fighter_data.get('costumes', []))})
    except Exception as e:
        logger.error(f"Costume to skin error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= Audio (victory theme / announcer / sound bank) =============

@custom_characters_bp.route('/api/mex/custom-characters/<slug>/audio/victory-theme', methods=['GET'])
def get_victory_theme_audio(slug):
    """Decode the character's victory theme (extracted at scan) to WAV."""
    char_dir = CUSTOM_CHARACTERS_PATH / slug
    cache = char_dir / 'audio_cache' / 'victory_theme.wav'
    if not cache.exists():
        hps = char_dir / 'victory_theme.hps'
        if not hps.exists():
            return jsonify({'success': False, 'error': 'No victory theme extracted — rescan the source ISO'}), 404
        cache.parent.mkdir(exist_ok=True)
        out = _run_mexcli('hps-to-wav', hps, cache)
        if not out.get('success') or not cache.exists():
            return jsonify({'success': False, 'error': out.get('error', 'HPS decode failed')}), 500
    return send_file(cache, mimetype='audio/wav')


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/audio/announcer', methods=['GET'])
def get_announcer_audio(slug):
    """Serve the character's announcer call (decoded at scan time)."""
    wav = CUSTOM_CHARACTERS_PATH / slug / 'announcer.wav'
    if not wav.exists():
        return jsonify({'success': False, 'error': 'No announcer call extracted — rescan the source ISO'}), 404
    return send_file(wav, mimetype='audio/wav')


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/audio/sounds', methods=['GET'])
def list_fighter_sounds(slug):
    """List the fighter's sound bank (groundwork for a future sounds menu)."""
    char_dir = CUSTOM_CHARACTERS_PATH / slug
    bank = _extract_fighter_ssm(char_dir)
    if bank is None:
        return jsonify({'success': False, 'error': 'No sound bank in fighter.zip'}), 404
    info = _run_mexcli('ssm-info', bank)
    if not info.get('success'):
        return jsonify({'success': False, 'error': info.get('error', 'SSM read failed')}), 500

    # sound names live in the packed group.json
    names = []
    import io
    try:
        with zipfile.ZipFile(char_dir / 'fighter.zip') as zf:
            sound_entry = next((n for n in zf.namelist()
                                if n.split('/')[-1].lower() == 'sound.zip'), None)
            if sound_entry:
                with zipfile.ZipFile(io.BytesIO(zf.read(sound_entry))) as sz:
                    group_entry = next((n for n in sz.namelist()
                                        if n.split('/')[-1].lower() == 'group.json'), None)
                    if group_entry:
                        names = [s.get('name') for s in json.loads(sz.read(group_entry)).get('sounds', [])]
    except (zipfile.BadZipFile, json.JSONDecodeError, KeyError):
        pass

    sounds = []
    for s in info.get('sounds', []):
        i = s['index']
        sounds.append({
            'index': i,
            'name': names[i] if i < len(names) else f'sound_{i}',
            'durationMs': s.get('durationMs'),
            'url': f"/api/mex/custom-characters/{slug}/audio/sound/{i}",
        })
    return jsonify({'success': True, 'count': len(sounds), 'sounds': sounds})


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/audio/sound/<int:index>', methods=['GET'])
def get_fighter_sound(slug, index):
    char_dir = CUSTOM_CHARACTERS_PATH / slug
    cache = char_dir / 'audio_cache' / f'sound_{index}.wav'
    if not cache.exists():
        bank = _extract_fighter_ssm(char_dir)
        if bank is None:
            return jsonify({'success': False, 'error': 'No sound bank in fighter.zip'}), 404
        out = _run_mexcli('ssm-to-wav', bank, index, cache)
        if not out.get('success') or not cache.exists():
            return jsonify({'success': False, 'error': out.get('error', 'SSM decode failed')}), 500
    return send_file(cache, mimetype='audio/wav')


# ============= Franchise / series =============

@custom_characters_bp.route('/api/mex/custom-characters/series-list', methods=['GET'])
def list_series():
    series = []
    for i, name in enumerate(SERIES_NAMES):
        series.append({
            'id': i,
            'name': name,
            'icon_url': f"/api/mex/custom-characters/series-icon/{i}" if _series_icon_path(i) else None,
        })
    return jsonify({'success': True, 'series': series})


@custom_characters_bp.route('/api/mex/custom-characters/series-icon/<int:series_id>', methods=['GET'])
def get_series_icon(series_id):
    p = _series_icon_path(series_id)
    if p:
        return send_file(p, mimetype='image/png')
    return jsonify({'success': False, 'error': 'Series icon not found'}), 404


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/set-series', methods=['POST'])
def set_custom_character_series(slug):
    """Change a custom character's franchise (seriesID)."""
    try:
        data = request.json or {}
        series_id = data.get('seriesId')
        if not isinstance(series_id, int) or not (0 <= series_id < len(SERIES_NAMES)):
            return jsonify({'success': False, 'error': f'seriesId must be 0..{len(SERIES_NAMES) - 1}'}), 400

        char_dir = CUSTOM_CHARACTERS_PATH / slug
        fighter_json_path = char_dir / 'fighter.json'
        if not fighter_json_path.exists():
            return jsonify({'success': False, 'error': 'Character not found'}), 404

        with open(fighter_json_path, 'r') as f:
            fighter_data = json.load(f)
        fighter_data['seriesID'] = series_id
        with open(fighter_json_path, 'w') as f:
            json.dump(fighter_data, f, indent=2)

        def _set_series(meta):
            meta['seriesID'] = series_id
            return meta
        _rewrite_fighter_zip(char_dir, mutate_json=_set_series)

        metadata = _read_metadata()
        entry = _find_entry(metadata, slug)
        if entry is not None:
            entry['series_id'] = series_id
            # Picking a vanilla franchise turns the custom one off (it can
            # be reactivated from the picker without rescanning)
            if entry.get('custom_series'):
                entry['custom_series']['active'] = False
            _write_metadata(metadata)

        logger.info(f"[OK] Set {slug} series to {series_id} ({SERIES_NAMES[series_id]})")
        return jsonify({
            'success': True,
            'series_id': series_id,
            'series_name': SERIES_NAMES[series_id],
            'series_icon_url': f"/api/mex/custom-characters/series-icon/{series_id}" if _series_icon_path(series_id) else None,
        })
    except Exception as e:
        logger.error(f"Set series error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= Fighter assets + properties (vault editing) =============

@custom_characters_bp.route('/api/mex/custom-characters/<slug>/zip-asset/<which>', methods=['GET'])
def get_fighter_zip_asset(slug, which):
    """Serve a fixed-name asset (result banners) straight out of fighter.zip."""
    spec = FIGHTER_ASSET_SPECS.get(which)
    if spec is None:
        return jsonify({'success': False, 'error': f'Unknown asset {which}'}), 400
    entry_name = spec[0]
    zip_path = CUSTOM_CHARACTERS_PATH / slug / 'fighter.zip'
    if not zip_path.exists():
        return jsonify({'success': False, 'error': 'fighter.zip not found'}), 404
    with zipfile.ZipFile(zip_path) as zf:
        for n in zf.namelist():
            if n.split('/')[-1].lower() == entry_name:
                import io
                from flask import Response
                return Response(zf.read(n), mimetype='image/png')
    return jsonify({'success': False, 'error': f'{entry_name} not in fighter.zip'}), 404


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/replace-asset/<which>', methods=['POST'])
def replace_fighter_asset(slug, which):
    """Replace the CSS icon or a result banner with an uploaded image.
    Writes the fighter.zip entry (what installs read) and, for the icon,
    the vault display copy css_icon.png."""
    try:
        spec = FIGHTER_ASSET_SPECS.get(which)
        if spec is None:
            return jsonify({'success': False, 'error': f'Unknown asset {which}'}), 400
        entry_name, size = spec

        char_dir = CUSTOM_CHARACTERS_PATH / slug
        if not (char_dir / 'fighter.zip').exists():
            return jsonify({'success': False, 'error': 'Character not found'}), 404
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        raw = request.files['file'].read()
        try:
            png = _normalized_png(raw, size)
        except Exception:
            return jsonify({'success': False, 'error': 'File is not a valid image'}), 400

        _rewrite_fighter_zip(char_dir, replace_entries={entry_name: png})
        if which == 'icon':
            (char_dir / 'css_icon.png').write_bytes(png)
            metadata = _read_metadata()
            entry = _find_entry(metadata, slug)
            if entry is not None:
                entry['has_css_icon'] = True
                _write_metadata(metadata)

        logger.info(f"[OK] Replaced {which} asset for {slug}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Replace fighter asset error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/set-wall-jump', methods=['POST'])
def set_wall_jump(slug):
    try:
        char_dir = CUSTOM_CHARACTERS_PATH / slug
        if not (char_dir / 'fighter.json').exists():
            return jsonify({'success': False, 'error': 'Character not found'}), 404
        data = request.get_json(silent=True) or {}
        value = bool(data.get('canWallJump'))

        def _set(meta):
            meta['canWallJump'] = value
        _update_fighter_json_everywhere(char_dir, _set)

        logger.info(f"[OK] Set {slug} canWallJump = {value}")
        return jsonify({'success': True, 'can_wall_jump': value})
    except Exception as e:
        logger.error(f"Set wall jump error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/costumes/<int:index>/rename', methods=['POST'])
def rename_bundled_costume(slug, index):
    try:
        char_dir = CUSTOM_CHARACTERS_PATH / slug
        if not (char_dir / 'fighter.json').exists():
            return jsonify({'success': False, 'error': 'Character not found'}), 404
        data = request.get_json(silent=True) or {}
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({'success': False, 'error': 'Name is required'}), 400

        with open(char_dir / 'fighter.json', 'r') as f:
            fighter_data = json.load(f)
        costumes = fighter_data.get('costumes', [])
        if index < 0 or index >= len(costumes):
            return jsonify({'success': False, 'error': f'Invalid costume index {index}'}), 400

        def _set(meta):
            metac = meta.get('costumes', [])
            if index < len(metac):
                metac[index]['name'] = name
        _update_fighter_json_everywhere(char_dir, _set)

        # keep the costume mirror's display name in sync
        dat = (costumes[index].get('file') or {}).get('fileName') or ''
        stem = Path(dat).stem
        metadata = _read_metadata()
        entry = _find_entry(metadata, slug)
        if entry is not None:
            for m in entry.get('costume_meta', []):
                if m['id'] == stem:
                    m['color'] = name
                    _write_metadata(metadata)
                    break

        logger.info(f"[OK] Renamed {slug} costume {index} to '{name}'")
        return jsonify({'success': True, 'name': name})
    except Exception as e:
        logger.error(f"Rename costume error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/custom-series-icon', methods=['GET'])
def get_custom_series_icon(slug):
    p = CUSTOM_CHARACTERS_PATH / slug / 'series_icon.png'
    if p.exists():
        return send_file(p, mimetype='image/png')
    return jsonify({'success': False, 'error': 'Custom series icon not found'}), 404


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/replace-series-icon', methods=['POST'])
def replace_series_icon(slug):
    """Upload a PNG as this character's franchise icon. Creates/activates a
    custom series; at install it is added to the target project."""
    try:
        char_dir = CUSTOM_CHARACTERS_PATH / slug
        if not (char_dir / 'fighter.json').exists():
            return jsonify({'success': False, 'error': 'Character not found'}), 404
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        uploaded = request.files['file']
        raw = uploaded.read()
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(raw))
            img.load()
        except Exception:
            return jsonify({'success': False, 'error': 'File is not a valid image'}), 400
        # The in-game asset is an 80x64 I4 texture — normalize so it encodes well
        if img.size != (80, 64):
            img = img.convert('RGBA').resize((80, 64), Image.LANCZOS)
        img.save(char_dir / 'series_icon.png')

        metadata = _read_metadata()
        entry = _find_entry(metadata, slug)
        if entry is None:
            return jsonify({'success': False, 'error': 'Character not found in metadata'}), 404

        cs = entry.get('custom_series') or {'source_id': entry.get('series_id')}
        name = (request.form.get('name') or '').strip()
        if name:
            cs['name'] = name
        elif not cs.get('name'):
            cs['name'] = f"{entry.get('name', slug)} Series"
        cs['active'] = True
        cs['has_icon'] = True
        entry['custom_series'] = cs
        _write_metadata(metadata)

        logger.info(f"[OK] Replaced franchise icon for {slug} (series '{cs['name']}')")
        return jsonify({'success': True, 'custom_series': {
            'name': cs.get('name'),
            'active': True,
            'source_id': cs.get('source_id'),
            'icon_url': f"/api/mex/custom-characters/{slug}/custom-series-icon",
        }})
    except Exception as e:
        logger.error(f"Replace series icon error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/set-series-custom', methods=['POST'])
def set_series_custom(slug):
    """Activate (or rename) the character's custom franchise."""
    try:
        metadata = _read_metadata()
        entry = _find_entry(metadata, slug)
        if entry is None:
            return jsonify({'success': False, 'error': 'Character not found'}), 404

        cs = entry.get('custom_series')
        icon_exists = (CUSTOM_CHARACTERS_PATH / slug / 'series_icon.png').exists()
        if not cs and not icon_exists:
            return jsonify({'success': False,
                            'error': 'No custom series available — upload a franchise icon first'}), 400

        cs = cs or {'source_id': entry.get('series_id')}
        data = request.get_json(silent=True) or {}
        name = (data.get('name') or '').strip()
        if name:
            cs['name'] = name
        elif not cs.get('name'):
            cs['name'] = f"{entry.get('name', slug)} Series"
        cs['active'] = True
        entry['custom_series'] = cs
        _write_metadata(metadata)

        logger.info(f"[OK] Activated custom series '{cs['name']}' for {slug}")
        return jsonify({'success': True, 'custom_series': {
            'name': cs.get('name'),
            'active': True,
            'source_id': cs.get('source_id'),
            'icon_url': (f"/api/mex/custom-characters/{slug}/custom-series-icon"
                         if icon_exists else None),
        }})
    except Exception as e:
        logger.error(f"Set custom series error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
