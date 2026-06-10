"""
Pause screen (GmPause) mod endpoints.

A pause mod replaces textures in the in-game pause overlay (GmPause.usd).
Mods arrive in two flavors and are normalized on import:

  1. Compiled GmPause.dat/.usd (alone or in a zip) — every texture is dumped
     to PNG via HSDRawViewer --pause-screen export and stored by index. A zip
     can ship several GmPause variants (e.g. white/black/silver controller
     colors); each becomes its own mod.
  2. A plain picture (png/jpg/webp) — stored as-is. On install it replaces
     the central 88x72 pause graphic (the camera-control icon), re-encoded
     as RGB5A3 so color survives (the vanilla texture is grayscale IA4).

    storage/menus/pause/
        metadata.json                   # catalog of installed mods
        <mod_id>/
            mod.json                    # manifest (source + texture list)
            screenshot.png              # optional preview from the zip
            picture.png                 # image-sourced mods
            textures/t<index>.png       # dat-sourced mods

Install runs HSDRawViewer --pause-screen import against the loaded project's
GmPause.usd with a spec.json describing the replacements.
"""

import json
import shutil
import tempfile
import uuid
import zipfile
import logging
from pathlib import Path
from datetime import datetime
from flask import request, jsonify, send_file

from core.config import HSDRAW_EXE
from core.state import get_project_files_dir, get_current_project_path

from . import menus_bp
from .helpers import (
    PAUSE_PATH, PAUSE_METADATA,
    load_catalog, save_catalog, load_mod_json, save_mod_json,
    _run_hsd_cli, _safe_extract_zip, _find_screenshot,
)

logger = logging.getLogger(__name__)

IMAGE_SUFFIXES = ('.png', '.jpg', '.jpeg', '.webp')

# Vanilla GmPause textures (exported once from a clean 1.02 GmPause.usd) —
# the base set for per-texture editing of mods that didn't ship a full dat.
VANILLA_TEX_DIR = Path(__file__).resolve().parent.parent.parent / 'assets' / 'pause_vanilla'


def _load_vanilla_manifest():
    try:
        with open(VANILLA_TEX_DIR / 'manifest.json', 'r', encoding='utf-8') as f:
            return json.load(f).get('textures', [])
    except Exception as e:
        logger.warning(f'Vanilla pause texture manifest unavailable: {e}')
        return []


def _load_pause_catalog():
    return load_catalog(PAUSE_METADATA, '1.0')


def _save_pause_catalog(data):
    save_catalog(PAUSE_METADATA, data)


def _attach_pause_urls(mod):
    out = dict(mod)
    if mod.get('id'):
        out['imageUrl'] = f"/api/mex/menus/pause/image/{mod['id']}"
    return out


def _find_gmpause_files(directory):
    """All GmPause*.dat/.usd files in an extracted directory, sorted by name."""
    found = []
    for p in sorted(Path(directory).rglob('*')):
        if not p.is_file():
            continue
        name_lower = p.name.lower()
        if name_lower.startswith('gmpause') and name_lower.endswith(('.dat', '.usd')):
            found.append(p)
    return found


def looks_like_pause_zip(zip_path):
    """Returns True if the zip contains a GmPause dat/usd file."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for n in zf.namelist():
                if n.startswith('__MACOSX'):
                    continue
                base = Path(n).name.lower()
                if base.startswith('gmpause') and base.endswith(('.dat', '.usd')):
                    return True
        return False
    except zipfile.BadZipFile:
        return False


def _variant_label(dat_path, base_name):
    """Derive a per-variant mod name from the GmPause filename.

    `GmPause(white).dat` → `<base_name> (white)`; a bare `GmPause.dat`
    just keeps base_name.
    """
    stem = dat_path.stem
    suffix = stem[len('gmpause'):].strip(' _-()') if stem.lower().startswith('gmpause') else stem
    return f'{base_name} ({suffix})' if suffix else base_name


def _import_pause_dat(dat_path, name, description, screenshot_src, catalog):
    """Dump a compiled GmPause's textures into a new mod. Returns the mod dict
    (without URLs) or raises RuntimeError."""
    with tempfile.TemporaryDirectory(prefix='pause_export_') as tmp:
        export_dir = Path(tmp) / 'dump'
        export_dir.mkdir()
        result = _run_hsd_cli(['--pause-screen', 'export', str(dat_path), str(export_dir)])
        if result is None:
            raise RuntimeError(f'Failed to extract textures from {dat_path.name}')

        manifest_path = export_dir / 'manifest.json'
        if not manifest_path.exists():
            raise RuntimeError('HSDRawViewer did not produce a texture manifest')
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)

        entries = manifest.get('textures', [])
        if not entries:
            raise RuntimeError(f'No textures found in {dat_path.name}')

        mod_id = str(uuid.uuid4())[:8]
        mod_dir = PAUSE_PATH / mod_id
        tex_dir = mod_dir / 'textures'
        tex_dir.mkdir(parents=True, exist_ok=True)

        textures = []
        for entry in entries:
            src = export_dir / entry['filename']
            if not src.exists():
                continue
            tex_name = f"t{entry['index']}.png"
            shutil.copy(str(src), str(tex_dir / tex_name))
            textures.append({
                'index': entry['index'],
                'width': entry['width'],
                'height': entry['height'],
                'format': entry['format'],
                'file': tex_name,
            })

        screenshot_filename = None
        if screenshot_src is not None and screenshot_src.exists():
            screenshot_filename = f'screenshot{screenshot_src.suffix.lower()}'
            shutil.copy(str(screenshot_src), str(mod_dir / screenshot_filename))

        mod = {
            'id': mod_id,
            'name': name,
            'description': description,
            'source': 'dat',
            'screenshot': screenshot_filename,
            'textures': textures,
            'created': datetime.now().isoformat(),
        }
        save_mod_json(PAUSE_PATH, mod_id, mod)
        catalog.setdefault('mods', []).append({
            'id': mod_id,
            'name': name,
            'description': description,
            'source': 'dat',
            'created': mod['created'],
        })
        logger.info(f'[OK] Imported pause mod: {name} ({mod_id}) — {len(textures)} textures')
        return mod


def install_pause_mods_from_zip(zip_path, name=None, description=''):
    """Import every GmPause variant in a zip. Returns list of mod dicts with
    URLs attached. Raises RuntimeError when nothing recognizable is found."""
    zip_path = Path(zip_path)
    base_name = (name or zip_path.stem).strip() or zip_path.stem

    with tempfile.TemporaryDirectory(prefix='pause_import_') as tmp:
        extract_dir = Path(tmp) / 'extracted'
        extract_dir.mkdir()
        _safe_extract_zip(zip_path, extract_dir)

        dats = _find_gmpause_files(extract_dir)
        if not dats:
            raise RuntimeError('No GmPause .dat/.usd found in archive')

        screenshot_src = _find_screenshot(extract_dir)
        multi = len(dats) > 1

        catalog = _load_pause_catalog()
        installed = []
        for dat in dats:
            mod_name = _variant_label(dat, base_name) if multi else base_name
            mod = _import_pause_dat(dat, mod_name, description, screenshot_src, catalog)
            installed.append(_attach_pause_urls(mod))
        _save_pause_catalog(catalog)
        return installed


@menus_bp.route('/api/mex/menus/pause/list', methods=['GET'])
def list_pause_mods():
    try:
        catalog = _load_pause_catalog()
        mods = [_attach_pause_urls(m) for m in catalog.get('mods', []) if m.get('id')]
        return jsonify({'success': True, 'mods': mods})
    except Exception as e:
        logger.error(f'List pause mods error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/pause/image/<mod_id>', methods=['GET'])
def get_pause_image(mod_id):
    """Serve the best preview for a pause mod: zip screenshot, uploaded
    picture, or the main (largest) extracted texture."""
    try:
        mod = load_mod_json(PAUSE_PATH, mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404
        mod_dir = PAUSE_PATH / mod_id

        candidates = []
        if mod.get('screenshot'):
            candidates.append(mod_dir / mod['screenshot'])
        candidates.append(mod_dir / 'picture.png')
        for tex in sorted(mod.get('textures', []),
                          key=lambda t: t.get('width', 0) * t.get('height', 0),
                          reverse=True):
            candidates.append(mod_dir / 'textures' / tex['file'])

        for path in candidates:
            if path.exists():
                return send_file(str(path), max_age=0)
        return jsonify({'success': False, 'error': 'No preview available'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/pause/import', methods=['POST'])
def import_pause_mod():
    """Import a pause screen mod. Accepts .zip (containing GmPause dat/usd),
    a raw GmPause .dat/.usd, or a plain picture (png/jpg/webp)."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        fname_lower = file.filename.lower()
        name = (request.form.get('name') or '').strip() or Path(file.filename).stem
        description = (request.form.get('description') or '').strip()

        # Plain picture → stored as-is, replaces the main pause graphic on install
        if fname_lower.endswith(IMAGE_SUFFIXES):
            mod_id = str(uuid.uuid4())[:8]
            mod_dir = PAUSE_PATH / mod_id
            mod_dir.mkdir(parents=True, exist_ok=True)
            file.save(str(mod_dir / 'picture.png'))

            mod = {
                'id': mod_id,
                'name': name,
                'description': description,
                'source': 'image',
                'created': datetime.now().isoformat(),
            }
            save_mod_json(PAUSE_PATH, mod_id, mod)
            catalog = _load_pause_catalog()
            catalog.setdefault('mods', []).append({
                'id': mod_id,
                'name': name,
                'description': description,
                'source': 'image',
                'created': mod['created'],
            })
            _save_pause_catalog(catalog)
            logger.info(f'[OK] Imported pause picture mod: {name} ({mod_id})')
            return jsonify({'success': True, 'mods': [_attach_pause_urls(mod)], 'imported_count': 1})

        is_zip = fname_lower.endswith('.zip')
        is_dat = fname_lower.endswith(('.dat', '.usd'))
        if not (is_zip or is_dat):
            return jsonify({'success': False,
                            'error': 'File must be .zip, .dat, .usd, or an image (.png/.jpg/.webp)'}), 400

        with tempfile.TemporaryDirectory(prefix='pause_upload_') as tmp:
            # Wrap a raw dat in a zip so one code path handles both
            zip_path = Path(tmp) / 'upload.zip'
            if is_zip:
                file.save(str(zip_path))
            else:
                raw = file.read()
                with zipfile.ZipFile(zip_path, 'w') as zf:
                    zf.writestr(file.filename, raw)
            try:
                mods = install_pause_mods_from_zip(zip_path, name=name, description=description)
            except zipfile.BadZipFile:
                return jsonify({'success': False, 'error': 'Invalid or corrupt zip file'}), 400
            except RuntimeError as e:
                return jsonify({'success': False, 'error': str(e)}), 400

        return jsonify({'success': True, 'mods': mods, 'imported_count': len(mods)})
    except Exception as e:
        logger.error(f'Import pause mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/pause/create', methods=['POST'])
def create_pause_mod():
    """Create a fresh pause mod seeded with the vanilla textures — a blank
    canvas for the per-texture editor. Body: {name?}."""
    try:
        payload = request.get_json(silent=True) or {}
        name = (payload.get('name') or '').strip() or 'New Pause Mod'

        mod_id = str(uuid.uuid4())[:8]
        mod = {
            'id': mod_id,
            'name': name,
            'description': '',
            'source': 'custom',
            'created': datetime.now().isoformat(),
        }
        save_mod_json(PAUSE_PATH, mod_id, mod)
        try:
            mod = _ensure_textures(mod)   # seed the full vanilla set
        except RuntimeError as e:
            shutil.rmtree(str(PAUSE_PATH / mod_id), ignore_errors=True)
            return jsonify({'success': False, 'error': str(e)}), 500

        catalog = _load_pause_catalog()
        catalog.setdefault('mods', []).append({
            'id': mod_id,
            'name': name,
            'description': '',
            'source': 'custom',
            'created': mod['created'],
        })
        _save_pause_catalog(catalog)

        logger.info(f'[OK] Created blank pause mod: {name} ({mod_id})')
        return jsonify({'success': True, 'mod': _attach_pause_urls(mod)})
    except Exception as e:
        logger.error(f'Create pause mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/pause/<mod_id>/textures', methods=['GET'])
def list_pause_textures(mod_id):
    """Full per-slot texture listing for the editor. Seeds picture-only mods
    with the vanilla texture set on first call."""
    try:
        mod = load_mod_json(PAUSE_PATH, mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404
        try:
            mod = _ensure_textures(mod)
        except RuntimeError as e:
            return jsonify({'success': False, 'error': str(e)}), 400

        out = []
        for tex in mod.get('textures', []):
            out.append({
                'index': tex['index'],
                'width': tex['width'],
                'height': tex['height'],
                'format': tex['format'],
                'replaced': bool(tex.get('replaced')),
                'url': f"/api/mex/menus/pause/texture/{mod_id}/{tex['index']}",
            })
        return jsonify({'success': True, 'textures': out, 'mod': _attach_pause_urls(mod)})
    except Exception as e:
        logger.error(f'List pause textures error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/pause/texture/<mod_id>/<int:index>', methods=['GET'])
def get_pause_texture(mod_id, index):
    try:
        tex_path = PAUSE_PATH / mod_id / 'textures' / f't{index}.png'
        if not tex_path.exists():
            # Not seeded yet (or never edited): fall back to the vanilla texture
            tex_path = VANILLA_TEX_DIR / f't{index}.png'
        if not tex_path.exists():
            return jsonify({'success': False, 'error': 'Texture not found'}), 404
        return send_file(str(tex_path), mimetype='image/png', max_age=0)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/pause/<mod_id>/replace_texture', methods=['POST'])
def replace_pause_texture(mod_id):
    """Replace a single texture slot with an uploaded image.
    Multipart form: index + file. The first replacement of a slot backs up the
    previous texture (t<i>.orig.png) so it can be reverted."""
    try:
        mod = load_mod_json(PAUSE_PATH, mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        try:
            index = int(request.form.get('index', ''))
        except ValueError:
            return jsonify({'success': False, 'error': 'index is required'}), 400
        if 'file' not in request.files or not request.files['file'].filename:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400

        try:
            mod = _ensure_textures(mod)
        except RuntimeError as e:
            return jsonify({'success': False, 'error': str(e)}), 400

        entry = next((t for t in mod['textures'] if t['index'] == index), None)
        if entry is None:
            return jsonify({'success': False, 'error': f'No texture slot {index}'}), 404

        tex_dir = PAUSE_PATH / mod_id / 'textures'
        tex_path = tex_dir / entry['file']
        orig_path = tex_dir / f't{index}.orig.png'
        if tex_path.exists() and not orig_path.exists():
            shutil.copy(str(tex_path), str(orig_path))
            entry['orig_replaced'] = bool(entry.get('replaced'))

        request.files['file'].save(str(tex_path))
        entry['replaced'] = True
        save_mod_json(PAUSE_PATH, mod_id, mod)

        logger.info(f'[OK] Replaced pause texture t{index} on mod {mod_id}')
        return jsonify({'success': True, 'index': index,
                        'url': f'/api/mex/menus/pause/texture/{mod_id}/{index}'})
    except Exception as e:
        logger.error(f'Replace pause texture error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/pause/<mod_id>/revert_texture', methods=['POST'])
def revert_pause_texture(mod_id):
    """Undo a user texture replacement. Body: {index}. Restores the backed-up
    original when one exists, otherwise the vanilla texture."""
    try:
        mod = load_mod_json(PAUSE_PATH, mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        payload = request.get_json(silent=True) or {}
        try:
            index = int(payload.get('index'))
        except (TypeError, ValueError):
            return jsonify({'success': False, 'error': 'index is required'}), 400

        entry = next((t for t in mod.get('textures', []) if t['index'] == index), None)
        if entry is None:
            return jsonify({'success': False, 'error': f'No texture slot {index}'}), 404

        tex_dir = PAUSE_PATH / mod_id / 'textures'
        tex_path = tex_dir / entry['file']
        orig_path = tex_dir / f't{index}.orig.png'

        if orig_path.exists():
            shutil.move(str(orig_path), str(tex_path))
            entry['replaced'] = entry.pop('orig_replaced', False)
        else:
            vanilla_tex = VANILLA_TEX_DIR / f't{index}.png'
            if not vanilla_tex.exists():
                return jsonify({'success': False, 'error': 'Nothing to revert to'}), 400
            shutil.copy(str(vanilla_tex), str(tex_path))
            entry['replaced'] = False
            entry.pop('orig_replaced', None)
        save_mod_json(PAUSE_PATH, mod_id, mod)

        logger.info(f'[OK] Reverted pause texture t{index} on mod {mod_id}')
        return jsonify({'success': True, 'index': index,
                        'url': f'/api/mex/menus/pause/texture/{mod_id}/{index}'})
    except Exception as e:
        logger.error(f'Revert pause texture error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/pause/delete/<mod_id>', methods=['POST'])
def delete_pause_mod(mod_id):
    try:
        catalog = _load_pause_catalog()
        mods = catalog.get('mods', [])
        idx = next((i for i, m in enumerate(mods) if m.get('id') == mod_id), -1)
        if idx < 0:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        mod_dir = PAUSE_PATH / mod_id
        if mod_dir.exists():
            shutil.rmtree(str(mod_dir), ignore_errors=True)

        mods.pop(idx)
        _save_pause_catalog(catalog)
        logger.info(f'[OK] Deleted pause mod: {mod_id}')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Delete pause mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def _build_replacement_spec(mod, mod_dir):
    """Build the --pause-screen import replacement list for a mod.
    Raises RuntimeError when the mod's payload files are missing."""
    replacements = []
    if mod.get('textures'):
        for tex in mod['textures']:
            tex_path = mod_dir / 'textures' / tex['file']
            if not tex_path.exists():
                continue
            # User-edited slots carry arbitrary color images → RGB5A3; textures
            # extracted from a compiled mod re-inject in their original format.
            fmt = 'rgb5a3' if tex.get('replaced') else 'original'
            replacements.append({'index': tex['index'], 'png': str(tex_path), 'format': fmt})
        if not replacements:
            raise RuntimeError('No textures stored for this mod')
    elif mod.get('source') == 'image':
        picture = mod_dir / 'picture.png'
        if not picture.exists():
            raise RuntimeError('picture.png missing from mod')
        replacements.append({'target': 'main', 'png': str(picture), 'format': 'rgb5a3'})
    else:
        raise RuntimeError('No textures stored for this mod')
    return replacements


def _ensure_textures(mod):
    """Give a mod a full per-index texture set so it can be edited slot-by-slot.

    Dat-sourced mods already have one. Picture mods get seeded from the vanilla
    texture assets, with the picture dropped into the two 88x72 "main" slots
    (marked replaced so install encodes them RGB5A3 — same as the picture
    install path). Returns the (possibly updated) mod, or raises RuntimeError."""
    if mod.get('textures'):
        return mod

    vanilla = _load_vanilla_manifest()
    if not vanilla:
        raise RuntimeError('Vanilla pause textures unavailable; cannot edit this mod')

    mod_dir = PAUSE_PATH / mod['id']
    tex_dir = mod_dir / 'textures'
    tex_dir.mkdir(parents=True, exist_ok=True)
    picture = mod_dir / 'picture.png'

    MAIN_SLOTS = {t['index'] for t in vanilla if t['width'] == 88 and t['height'] == 72}

    textures = []
    for t in vanilla:
        tex_name = f"t{t['index']}.png"
        entry = {
            'index': t['index'],
            'width': t['width'],
            'height': t['height'],
            'format': t['format'],
            'file': tex_name,
        }
        if t['index'] in MAIN_SLOTS and picture.exists():
            shutil.copy(str(picture), str(tex_dir / tex_name))
            entry['replaced'] = True
        else:
            shutil.copy(str(VANILLA_TEX_DIR / t['file']), str(tex_dir / tex_name))
        textures.append(entry)

    mod['textures'] = textures
    save_mod_json(PAUSE_PATH, mod['id'], mod)
    logger.info(f"[OK] Seeded per-texture set for pause mod {mod['id']} ({mod.get('source')})")
    return mod


def apply_pause_mod(mod_id, gmpause_path):
    """Apply a stored pause mod to a GmPause.usd on disk (in place) via
    HSDRawViewer --pause-screen import. Raises on failure. Also used by
    test_build.build_pause_mod_iso for the in-game capture flow."""
    mod = load_mod_json(PAUSE_PATH, mod_id)
    if not mod:
        raise RuntimeError('Mod not found')
    gmpause_path = Path(gmpause_path)
    if not gmpause_path.exists():
        raise RuntimeError(f'GmPause.usd not found at {gmpause_path}')
    if not HSDRAW_EXE.exists():
        raise RuntimeError(f'HSDRawViewer not found at {HSDRAW_EXE}')

    replacements = _build_replacement_spec(mod, PAUSE_PATH / mod_id)

    with tempfile.TemporaryDirectory(prefix='pause_install_') as tmp:
        spec_path = Path(tmp) / 'spec.json'
        with open(spec_path, 'w', encoding='utf-8') as f:
            json.dump({'replacements': replacements}, f)

        output_usd = Path(tmp) / 'GmPause.usd'
        result = _run_hsd_cli([
            '--pause-screen', 'import',
            str(gmpause_path), str(spec_path), str(output_usd)
        ])
        if result is None:
            raise RuntimeError('HSDRawViewer --pause-screen import failed')
        if not output_usd.exists():
            raise RuntimeError('Import produced no output file')

        shutil.copy(str(output_usd), str(gmpause_path))
    return mod


def set_mod_screenshot(mod_id, png_bytes):
    """Save captured PNG bytes as a pause mod's preview screenshot."""
    mod = load_mod_json(PAUSE_PATH, mod_id)
    if not mod:
        raise RuntimeError('Mod not found')
    mod_dir = PAUSE_PATH / mod_id
    mod_dir.mkdir(parents=True, exist_ok=True)
    (mod_dir / 'screenshot.png').write_bytes(png_bytes)
    mod['screenshot'] = 'screenshot.png'
    save_mod_json(PAUSE_PATH, mod_id, mod)
    return mod


@menus_bp.route('/api/mex/menus/pause/install/<mod_id>', methods=['POST'])
def install_pause_mod(mod_id):
    """Install a pause mod into the loaded project's GmPause.usd via
    HSDRawViewer --pause-screen import."""
    try:
        mod = load_mod_json(PAUSE_PATH, mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No MEX project loaded'}), 400

        files_dir = get_project_files_dir()
        if files_dir is None:
            return jsonify({'success': False, 'error': 'No project files directory'}), 400

        try:
            apply_pause_mod(mod_id, Path(files_dir) / 'GmPause.usd')
        except RuntimeError as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        logger.info('  Replaced GmPause.usd with modded pause screen')

        msg = f'Installed pause screen "{mod["name"]}". Rebuild ISO to apply.'
        logger.info(f'[OK] Installed pause mod {mod_id}')
        return jsonify({'success': True, 'message': msg})
    except Exception as e:
        logger.error(f'Install pause mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
