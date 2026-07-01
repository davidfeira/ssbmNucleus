"""
Custom Stages Blueprint - Manage m-ex custom stages in the vault.

Custom stages are entirely new stages (not DAS texture variants). They are
imported from MexManager-exported ZIP packages or scanned from an open m-ex
project. Each stage is stored as:

    storage/custom_stages/<slug>/
        stage.zip       (original ZIP preserved for re-export)
        icon.png        (extracted for fast serving)
        banner.png      (extracted for detail view)
        stage.json      (extracted metadata)

Metadata is tracked under metadata.json["custom_stages"] (list of objects).
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import uuid
import zipfile
import logging
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

from core.config import STORAGE_PATH, MEXCLI_PATH, PROJECT_ROOT, get_subprocess_args
from core.helpers import friendly_iso_open_error
from core.metadata import load_metadata, save_metadata, metadata_transaction
from core.state import metadata_lock
from core.state import get_current_project_path, reload_mex_manager, get_socketio, mexcli_lock

logger = logging.getLogger(__name__)

custom_stages_bp = Blueprint('custom_stages', __name__)

CUSTOM_STAGES_PATH = STORAGE_PATH / 'custom_stages'
CUSTOM_STAGES_PATH.mkdir(parents=True, exist_ok=True)

METADATA_FILE = STORAGE_PATH / 'metadata.json'


def _sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


def _make_slug(name):
    slug = _sanitize_filename(name).lower().replace(' ', '-')
    slug = re.sub(r'-+', '-', slug).strip('-')
    if not slug:
        slug = 'custom-stage'
    return slug


def _dedupe_slug(slug):
    if not (CUSTOM_STAGES_PATH / slug).exists():
        return slug
    counter = 2
    while (CUSTOM_STAGES_PATH / f"{slug}-{counter}").exists():
        counter += 1
    return f"{slug}-{counter}"


# Default vault shape this module expects from a missing/empty metadata file.
_DEFAULT_META = {'characters': {}, 'stages': {}, 'custom_stages': []}


def _read_metadata():
    # Delegates to the core.metadata DAL (the single seam the SQLite migration
    # swaps behind); keeps this module's historical 'custom_stages' default.
    data = load_metadata(default=dict(_DEFAULT_META))
    data.setdefault('custom_stages', [])
    return data


def _write_metadata(data):
    # DAL write is atomic (temp + os.replace); pairs with metadata_lock /
    # metadata_transaction at the mutation sites to prevent lost updates.
    save_metadata(data)


def _is_folder(item):
    return isinstance(item, dict) and item.get('type') == 'folder'


def _find_folder(items, folder_id):
    for i, item in enumerate(items):
        if _is_folder(item) and item.get('id') == folder_id:
            return item, i
    return None, -1


def _folder_id_at_position(items, position):
    """Determine folder membership for a stage placed at `position`.

    Mirrors get_folder_id_at_position from storage_costumes: look backwards
    until we find either a folder header (we're in it) or a root-level stage
    (we're at root).
    """
    for i in range(position - 1, -1, -1):
        item = items[i]
        if _is_folder(item):
            return item['id']
        if item.get('folder_id'):
            return item['folder_id']
        return None
    return None


@custom_stages_bp.route('/api/mex/custom-stages/list', methods=['GET'])
def list_custom_stages():
    try:
        metadata = _read_metadata()
        items = metadata.get('custom_stages', [])
        for item in items:
            if _is_folder(item):
                continue
            # Stages keep slug as their stable identifier, but the frontend
            # drag/drop code uses `id` uniformly. Mirror slug → id.
            item['id'] = item.get('slug')
            item['icon_url'] = f"/api/mex/custom-stages/{item['slug']}/icon"
        return jsonify({'success': True, 'stages': items})
    except Exception as e:
        logger.error(f"List custom stages error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def import_custom_stage_zip_bytes(zip_data, fallback_name):
    """Import a custom stage package (zip bytes) into the vault.
    Returns the metadata entry. Raises ValueError on an invalid package.
    Shared by the dedicated route and the unified /import/file dispatcher."""
    import io
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        names = zf.namelist()

        stage_json_path = None
        dat_files = []
        icon_path = None
        banner_path = None

        for name in names:
            basename = name.split('/')[-1].lower()
            if basename == 'stage.json':
                stage_json_path = name
            elif basename.endswith('.dat'):
                dat_files.append(name)
            elif basename == 'icon.png':
                icon_path = name
            elif basename == 'banner.png':
                banner_path = name

        if not stage_json_path:
            raise ValueError('ZIP must contain a stage.json file')
        if not dat_files:
            raise ValueError('ZIP must contain at least one .dat file')

        stage_meta = json.loads(zf.read(stage_json_path))
        stage_name = stage_meta.get('name', fallback_name)

        slug = _dedupe_slug(_make_slug(stage_name))
        stage_dir = CUSTOM_STAGES_PATH / slug
        stage_dir.mkdir(parents=True, exist_ok=True)

        (stage_dir / 'stage.zip').write_bytes(zip_data)

        with open(stage_dir / 'stage.json', 'w') as f:
            json.dump(stage_meta, f, indent=2)

        has_icon = False
        if icon_path:
            (stage_dir / 'icon.png').write_bytes(zf.read(icon_path))
            has_icon = True

        has_banner = False
        if banner_path:
            (stage_dir / 'banner.png').write_bytes(zf.read(banner_path))
            has_banner = True

    entry = {
        'slug': slug,
        'name': stage_name,
        'source': 'zip',
        'date_added': datetime.now().isoformat(),
        'series_id': stage_meta.get('seriesID', 0),
        'sound_bank': stage_meta.get('soundBank', None),
        'dat_files': [n.split('/')[-1] for n in dat_files],
        'has_banner': has_banner,
        'has_icon': has_icon
    }

    # Locked read-append-write (see custom_characters import) — concurrent
    # multi-file imports otherwise race on the shared vault metadata.
    with metadata_transaction(default=dict(_DEFAULT_META)) as metadata:
        metadata.setdefault('custom_stages', []).append(entry)

    logger.info(f"[OK] Imported custom stage '{stage_name}' as {slug}")
    return entry


@custom_stages_bp.route('/api/mex/custom-stages/import-zip', methods=['POST'])
def import_custom_stage_zip():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        uploaded = request.files['file']
        if not uploaded.filename or not uploaded.filename.lower().endswith('.zip'):
            return jsonify({'success': False, 'error': 'File must be a .zip'}), 400

        entry = import_custom_stage_zip_bytes(
            uploaded.read(), uploaded.filename.rsplit('.', 1)[0])
        return jsonify({'success': True, 'stage': entry})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except zipfile.BadZipFile:
        return jsonify({'success': False, 'error': 'Invalid or corrupted ZIP file'}), 400
    except Exception as e:
        logger.error(f"Import custom stage ZIP error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/in-project', methods=['GET'])
def list_custom_stages_in_project():
    """List custom stages currently installed in the open project (index > 70)."""
    try:
        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': True, 'stages': []})

        project_dir = project_path.parent
        stages_dir = project_dir / 'data' / 'stages'

        if not stages_dir.exists() or not project_path.exists():
            return jsonify({'success': True, 'stages': []})

        with open(project_path, 'r') as f:
            proj_data = json.load(f)

        stage_files = proj_data.get('stageSaveMap', {}).get('filePaths', [])
        assets_dir = project_dir / 'assets'
        stages = []

        for i, stage_file in enumerate(stage_files):
            if i <= 70:
                continue
            stage_json_path = stages_dir / stage_file
            if not stage_json_path.exists():
                continue
            try:
                with open(stage_json_path, 'r') as f:
                    stage_data = json.load(f)
                name = stage_data.get('name', f'Stage {i}')
                icon_ref = stage_data.get('assets', {}).get('icon')
                icon_url = None
                if icon_ref:
                    icon_url = f"/assets/{icon_ref.replace(chr(92), '/')}.png"
                stages.append({
                    'index': i,
                    'name': name,
                    'icon_url': icon_url,
                })
            except (json.JSONDecodeError, KeyError):
                continue

        return jsonify({'success': True, 'stages': stages})
    except Exception as e:
        logger.error(f"List project custom stages error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


VANILLA_STAGE_NAMES = {
    'Null', 'Test Stage', "Princess Peach's Castle", 'Rainbow Cruise',
    'Kongo Jungle', 'Jungle Japes', 'Great Bay', 'Temple', 'Brinstar',
    'Brinstar Depths', "Yoshi's Story", "Yoshi's Island",
    'Fountain of Dreams', 'Green Greens', 'Corneria', 'Venom',
    'Pokemon Stadium', 'Poke Floats', 'Mute City', 'Big Blue', 'Onett',
    'Fourside', 'Icicle Mountain', 'Ice Top', 'Kingdom', 'Kingdom II',
    'Akaneia', 'Flat Zone', 'Dream Land N64', "Yoshi's Island N64",
    'Kongo Jungle N64', 'Mushroom Kingdom (Adventure)', 'Underground Maze',
    'Brinstar Escape Shaft', 'F-Zero Grand Prix', 'Battlefield',
    'Final Destination', 'Trophy Collector', 'Race to the Finish',
    'Targets!Mario', 'Targets!C. Falcon', 'Targets!Young Link',
    'Targets!DK', 'Targets!Dr. Mario', 'Targets!Falco', 'Targets!Fox',
    'Targets!Ice Climbers', 'Targets!Kirby', 'Targets!Bowser',
    'Targets!Link', 'Targets!Luigi', 'Targets!Marth', 'Targets!Mewtwo',
    'Targets!Ness', 'Targets!Peach', 'Targets!Pichu', 'Targets!Pikachu',
    'Targets!Jigglypuff', 'Targets!Samus', 'Targets!Sheik',
    'Targets!Yoshi', 'Targets!Zelda', 'Targets!Game and Watch',
    'Targets!Roy', 'Targets!Ganon', 'All-Star Rest Area',
    'Home-Run Stadium', 'Trophy (Goomba)', 'Trophy (Entei)',
    "Trophy (Majora's Mask)",
}


def _resolve_asset_png(assets_dir, asset_ref):
    """Resolve an asset reference like 'sss\\icon_048' to a .png file path."""
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


def _extract_stage_playlist(project_dir, stage_data, stage_dir):
    """Copy a custom stage's playlist music (.hps files + names) into the
    vault. MexStage.FromPackage resets the playlist on install, so the
    vault carries the actual tracks to port them. Returns entry updates."""
    entries = ((stage_data.get('playlist') or {}).get('entries')) or []
    if not entries:
        return {}

    music_json = project_dir / 'data' / 'music.json'
    if not music_json.exists():
        return {}
    try:
        with open(music_json, 'r', encoding='utf-8') as f:
            music = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}

    playlist = []
    for e in entries:
        mid = e.get('musicID')
        chance = e.get('chanceToPlay', 50)
        if not (isinstance(mid, int) and 0 <= mid < len(music)):
            continue
        m = music[mid] or {}
        fname = m.get('fileName')
        src = (project_dir / 'files' / 'audio' / fname) if fname else None
        if not (src and src.exists()):
            continue
        i = len(playlist)
        shutil.copy2(src, stage_dir / f'music_{i}.hps')
        cache = stage_dir / 'audio_cache' / f'track_{i}.wav'
        if cache.exists():
            cache.unlink()
        playlist.append({
            'name': (m.get('name') or '').strip() or Path(fname).stem,
            'chance': chance,
        })

    return {'playlist': playlist} if playlist else {}


def _extract_custom_stages_from_project(project_dir, source_label):
    """Extract custom stages from a MEX project directory into the vault.
    Returns (imported, skipped) name lists."""
    files_dir = project_dir / 'files'
    stages_dir = project_dir / 'data' / 'stages'
    assets_dir = project_dir / 'assets'
    project_path = project_dir / 'project.mexproj'

    if not stages_dir.exists():
        raise FileNotFoundError('Project data/stages/ directory not found')

    with open(project_path, 'r') as f:
        proj_data = json.load(f)

    stage_files = proj_data.get('stageSaveMap', {}).get('filePaths', [])
    if not stage_files:
        return [], []

    metadata = _read_metadata()
    existing_names = {
        s['name'].lower()
        for s in metadata.get('custom_stages', [])
        if not _is_folder(s) and s.get('name')
    }

    imported = []
    skipped = []

    mexcli_path = str(MEXCLI_PATH)

    for stage_index, stage_file in enumerate(stage_files):
        stage_json_path = stages_dir / stage_file
        if not stage_json_path.exists():
            continue

        try:
            with open(stage_json_path, 'r') as f:
                stage_data = json.load(f)

            stage_name = stage_data.get('name', '')
            if not stage_name or stage_name in VANILLA_STAGE_NAMES:
                continue

            if stage_name.lower() in existing_names:
                # backfill playlist music for stages scanned before audio
                # extraction existed
                existing = next((s for s in metadata.get('custom_stages', [])
                                 if not _is_folder(s) and (s.get('name') or '').lower() == stage_name.lower()), None)
                if existing is not None:
                    existing_dir = CUSTOM_STAGES_PATH / existing['slug']
                    if existing_dir.exists():
                        playlist_updates = _extract_stage_playlist(project_dir, stage_data, existing_dir)
                        if playlist_updates:
                            existing.update(playlist_updates)
                            _write_metadata(metadata)
                skipped.append(stage_name)
                continue

            slug = _dedupe_slug(_make_slug(stage_name))
            stage_dir = CUSTOM_STAGES_PATH / slug
            stage_dir.mkdir(parents=True, exist_ok=True)

            # Export full stage ZIP via MexCLI
            zip_path = stage_dir / 'stage.zip'
            if Path(mexcli_path).exists():
                export_cmd = [mexcli_path, 'export-stage', str(project_path), str(stage_index), str(zip_path)]
                export_result = subprocess.run(
                    export_cmd, capture_output=True, text=True,
                    cwd=str(PROJECT_ROOT), **get_subprocess_args()
                )
                if export_result.returncode != 0:
                    logger.warning(f"Failed to export stage ZIP for '{stage_name}': {export_result.stderr or export_result.stdout}")

            with open(stage_dir / 'stage.json', 'w') as f:
                json.dump(stage_data, f, indent=2)

            assets_obj = stage_data.get('assets', {})
            has_icon = False
            icon_ref = assets_obj.get('icon')
            icon_file = _resolve_asset_png(assets_dir, icon_ref)
            if icon_file:
                shutil.copy2(icon_file, stage_dir / 'icon.png')
                has_icon = True

            has_banner = False
            banner_ref = assets_obj.get('banner')
            banner_file = _resolve_asset_png(assets_dir, banner_ref)
            if banner_file:
                shutil.copy2(banner_file, stage_dir / 'banner.png')
                has_banner = True

            file_name = stage_data.get('fileName') or ''
            dat_files_found = []
            if file_name and files_dir.exists():
                clean = file_name.lstrip('/')
                if not clean.endswith('.dat'):
                    clean += '.dat'
                main_dat = files_dir / clean
                if main_dat.exists():
                    dat_files_found.append(main_dat.name)
                for extra in stage_data.get('additionalFiles', []):
                    extra_path = files_dir / extra.lstrip('/')
                    if extra_path.exists():
                        dat_files_found.append(extra_path.name)

            entry = {
                'slug': slug,
                'name': stage_name,
                'source': source_label,
                'date_added': datetime.now().isoformat(),
                'series_id': stage_data.get('seriesID', 0),
                'sound_bank': stage_data.get('soundBank', None),
                'dat_files': dat_files_found,
                'has_banner': has_banner,
                'has_icon': has_icon
            }

            entry.update(_extract_stage_playlist(project_dir, stage_data, stage_dir))

            metadata['custom_stages'].append(entry)
            existing_names.add(stage_name.lower())
            imported.append(stage_name)

        except (json.JSONDecodeError, KeyError):
            continue

    if imported:
        _write_metadata(metadata)

    return imported, skipped


@custom_stages_bp.route('/api/mex/custom-stages/scan-iso', methods=['POST'])
def scan_iso_for_custom_stages():
    """Create a temp MEX project from an ISO, extract custom stages, clean up."""
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
        if '.nkit' in iso_file.name.lower():
            logger.info(f"Skipping NKit ISO for custom stage scan: {iso_path}")
            return jsonify({
                'success': True,
                'imported': [],
                'skipped': [iso_file.name],
                'message': 'Skipped NKit ISO (not supported)'
            })

        mexcli_path = str(MEXCLI_PATH)
        if not Path(mexcli_path).exists():
            return jsonify({'success': False, 'error': 'MexCLI not found. Build MexCLI first.'}), 500

        temp_dir = tempfile.mkdtemp(prefix='nucleus_stage_scan_')
        try:
            logger.info(f"Scanning ISO for custom stages: {iso_path}")
            logger.info(f"Temp project dir: {temp_dir}")

            cmd = [mexcli_path, 'import-iso', str(iso_file), temp_dir, 'temp_scan']
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                cwd=str(PROJECT_ROOT), **get_subprocess_args()
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or 'Unknown error'
                logger.error(f"MexCLI create failed: {error_msg}")
                return jsonify({'success': False, 'error': friendly_iso_open_error(error_msg)}), 500

            project_dir = Path(temp_dir)
            if not (project_dir / 'project.mexproj').exists():
                return jsonify({'success': False, 'error': 'MexCLI created project but .mexproj not found'}), 500

            imported, skipped = _extract_custom_stages_from_project(project_dir, 'iso-scan')

            logger.info(f"[OK] ISO scan: imported {len(imported)}, skipped {len(skipped)}")
            return jsonify({
                'success': True,
                'imported': imported,
                'skipped': skipped,
                'message': f"Imported {len(imported)} custom stage(s), skipped {len(skipped)} duplicate(s)"
            })
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logger.error(f"Scan ISO for custom stages error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/<slug>/icon', methods=['GET'])
def get_custom_stage_icon(slug):
    icon_path = CUSTOM_STAGES_PATH / slug / 'icon.png'
    if icon_path.exists():
        return send_file(icon_path, mimetype='image/png')
    return jsonify({'success': False, 'error': 'Icon not found'}), 404


@custom_stages_bp.route('/api/mex/custom-stages/<slug>/banner', methods=['GET'])
def get_custom_stage_banner(slug):
    banner_path = CUSTOM_STAGES_PATH / slug / 'banner.png'
    if banner_path.exists():
        return send_file(banner_path, mimetype='image/png')
    return jsonify({'success': False, 'error': 'Banner not found'}), 404


@custom_stages_bp.route('/api/mex/custom-stages/<slug>/audio/track/<int:index>', methods=['GET'])
def get_stage_track_audio(slug, index):
    """Decode a stage playlist track (extracted at scan) to WAV."""
    stage_dir = CUSTOM_STAGES_PATH / slug
    cache = stage_dir / 'audio_cache' / f'track_{index}.wav'
    if not cache.exists():
        hps = stage_dir / f'music_{index}.hps'
        if not hps.exists():
            return jsonify({'success': False, 'error': 'Track not extracted — rescan the source ISO'}), 404
        from blueprints.custom_characters import _run_mexcli
        cache.parent.mkdir(exist_ok=True)
        out = _run_mexcli('hps-to-wav', hps, cache)
        if not out.get('success') or not cache.exists():
            return jsonify({'success': False, 'error': out.get('error', 'HPS decode failed')}), 500
    return send_file(cache, mimetype='audio/wav')


# ============= Playlist editing (vault-level; ported on install) =============

# formats MeleeMedia's DSP.FromFile actually reads — the viewer converts
# everything else (mp3 etc.) to WAV client-side before uploading
MUSIC_IMPORT_EXTS = {'.wav', '.hps', '.brstm', '.dsp'}


def _find_stage_entry(metadata, slug):
    return next((s for s in metadata.get('custom_stages', [])
                 if not _is_folder(s) and s.get('slug') == slug), None)


def _invalidate_track_cache(stage_dir):
    cache_dir = stage_dir / 'audio_cache'
    if cache_dir.exists():
        for f in cache_dir.glob('track_*.wav'):
            f.unlink(missing_ok=True)


@custom_stages_bp.route('/api/mex/custom-stages/<slug>/playlist', methods=['GET'])
def get_stage_playlist(slug):
    """List the stage's vault playlist (what install ports into a build)."""
    metadata = _read_metadata()
    entry = _find_stage_entry(metadata, slug)
    if entry is None:
        return jsonify({'success': False, 'error': 'Stage not found'}), 404
    stage_dir = CUSTOM_STAGES_PATH / slug
    tracks = []
    for i, t in enumerate(entry.get('playlist') or []):
        tracks.append({
            'index': i,
            'name': t.get('name') or f'track_{i}',
            'chance': t.get('chance', 50),
            'has_file': (stage_dir / f'music_{i}.hps').exists(),
            'url': f"/api/mex/custom-stages/{slug}/audio/track/{i}",
        })
    return jsonify({'success': True, 'tracks': tracks})


@custom_stages_bp.route('/api/mex/custom-stages/<slug>/playlist/add', methods=['POST'])
def add_stage_track(slug):
    """Add a song to the stage's playlist. Non-HPS uploads are converted to
    HPS via MexCLI (mono sources are mirrored to stereo)."""
    try:
        metadata = _read_metadata()
        entry = _find_stage_entry(metadata, slug)
        if entry is None:
            return jsonify({'success': False, 'error': 'Stage not found'}), 404
        stage_dir = CUSTOM_STAGES_PATH / slug
        stage_dir.mkdir(parents=True, exist_ok=True)

        file = request.files.get('file')
        if file is None or not file.filename:
            return jsonify({'success': False, 'error': 'No audio file uploaded'}), 400
        ext = Path(file.filename).suffix.lower()
        if ext not in MUSIC_IMPORT_EXTS:
            return jsonify({'success': False,
                            'error': f"Unsupported format '{ext}' — use one of: "
                                     + ', '.join(sorted(MUSIC_IMPORT_EXTS))}), 400

        name = (request.form.get('name') or '').strip() or Path(file.filename).stem
        try:
            chance = max(0, min(100, int(request.form.get('chance', 50))))
        except ValueError:
            chance = 50

        playlist = entry.setdefault('playlist', [])
        index = len(playlist)
        hps_path = stage_dir / f'music_{index}.hps'

        if ext == '.hps':
            file.save(hps_path)
        else:
            from blueprints.custom_characters import _run_mexcli
            with tempfile.TemporaryDirectory() as td:
                upload = Path(td) / f'upload{ext}'
                file.save(upload)
                out = _run_mexcli('audio-to-hps', upload, hps_path)
            if not out.get('success') or not hps_path.exists():
                return jsonify({'success': False, 'error': out.get('error', 'HPS conversion failed')}), 500

        playlist.append({'name': name, 'chance': chance})
        _write_metadata(metadata)

        logger.info(f"[OK] Added track '{name}' to custom stage '{slug}'")
        return jsonify({'success': True, 'track': {
            'index': index, 'name': name, 'chance': chance, 'has_file': True,
            'url': f"/api/mex/custom-stages/{slug}/audio/track/{index}",
        }})
    except Exception as e:
        logger.error(f"Add stage track error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/<slug>/playlist/<int:index>/update', methods=['POST'])
def update_stage_track(slug, index):
    """Update a track's name and/or play chance (%)."""
    try:
        metadata = _read_metadata()
        entry = _find_stage_entry(metadata, slug)
        if entry is None:
            return jsonify({'success': False, 'error': 'Stage not found'}), 404
        playlist = entry.get('playlist') or []
        if not (0 <= index < len(playlist)):
            return jsonify({'success': False, 'error': f'Track {index} out of range'}), 404

        data = request.get_json(silent=True) or {}
        if 'chance' in data:
            try:
                playlist[index]['chance'] = max(0, min(100, int(data['chance'])))
            except (TypeError, ValueError):
                return jsonify({'success': False, 'error': 'chance must be a number 0..100'}), 400
        if isinstance(data.get('name'), str) and data['name'].strip():
            playlist[index]['name'] = data['name'].strip()

        _write_metadata(metadata)
        return jsonify({'success': True, 'track': {'index': index, **playlist[index]}})
    except Exception as e:
        logger.error(f"Update stage track error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/<slug>/playlist/<int:index>/remove', methods=['POST'])
def remove_stage_track(slug, index):
    """Remove a track and renumber the music_N.hps files after it."""
    try:
        metadata = _read_metadata()
        entry = _find_stage_entry(metadata, slug)
        if entry is None:
            return jsonify({'success': False, 'error': 'Stage not found'}), 404
        playlist = entry.get('playlist') or []
        if not (0 <= index < len(playlist)):
            return jsonify({'success': False, 'error': f'Track {index} out of range'}), 404

        stage_dir = CUSTOM_STAGES_PATH / slug
        (stage_dir / f'music_{index}.hps').unlink(missing_ok=True)
        for j in range(index + 1, len(playlist)):
            src = stage_dir / f'music_{j}.hps'
            if src.exists():
                src.rename(stage_dir / f'music_{j - 1}.hps')

        playlist.pop(index)
        _write_metadata(metadata)
        _invalidate_track_cache(stage_dir)

        logger.info(f"[OK] Removed track {index} from custom stage '{slug}'")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Remove stage track error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= Stage assets (vault editing) =============

# fixed entry names + canonical sizes from MexStageAssets
STAGE_ASSET_SPECS = {
    'icon': ('icon.png', (64, 56)),
    'banner': ('banner.png', (224, 56)),
}


def _set_stage_zip_entry(zip_path, entry_name, new_bytes):
    """Replace the stage.zip entry whose basename matches, or add it at the
    root if absent. add-stage (MexStage.FromPackage) reads assets by these
    fixed names, so vault-side asset edits must land here to survive install."""
    tmp = zip_path.with_suffix('.tmp')
    matched = False
    with zipfile.ZipFile(zip_path) as zin, \
            zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename.split('/')[-1].lower() == entry_name:
                zout.writestr(item, new_bytes)
                matched = True
            else:
                zout.writestr(item, zin.read(item.filename))
        if not matched:
            zout.writestr(entry_name, new_bytes)
    tmp.replace(zip_path)


@custom_stages_bp.route('/api/mex/custom-stages/<slug>/replace-asset/<which>', methods=['POST'])
def replace_stage_asset(slug, which):
    """Replace the SSS icon or banner with an uploaded image. Writes both the
    vault display copy and the stage.zip entry (what installs read)."""
    try:
        spec = STAGE_ASSET_SPECS.get(which)
        if spec is None:
            return jsonify({'success': False, 'error': f'Unknown asset {which}'}), 400
        entry_name, size = spec

        metadata = _read_metadata()
        entry = _find_stage_entry(metadata, slug)
        if entry is None:
            return jsonify({'success': False, 'error': 'Stage not found'}), 404
        stage_dir = CUSTOM_STAGES_PATH / slug
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        raw = request.files['file'].read()
        from blueprints.custom_characters import _normalized_png
        try:
            png = _normalized_png(raw, size)
        except Exception:
            return jsonify({'success': False, 'error': 'File is not a valid image'}), 400

        stage_dir.mkdir(parents=True, exist_ok=True)
        (stage_dir / entry_name).write_bytes(png)
        zip_path = stage_dir / 'stage.zip'
        if zip_path.exists():
            _set_stage_zip_entry(zip_path, entry_name, png)

        entry[f'has_{which}'] = True
        _write_metadata(metadata)

        logger.info(f"[OK] Replaced {which} asset for custom stage '{slug}'")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Replace stage asset error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/<slug>/delete', methods=['POST'])
def delete_custom_stage(slug):
    try:
        stage_dir = CUSTOM_STAGES_PATH / slug
        if stage_dir.exists():
            shutil.rmtree(stage_dir)

        metadata = _read_metadata()
        metadata['custom_stages'] = [
            s for s in metadata.get('custom_stages', []) if s.get('slug') != slug
        ]
        _write_metadata(metadata)

        logger.info(f"[OK] Deleted custom stage '{slug}'")
        return jsonify({'success': True, 'message': f'Deleted {slug}'})
    except Exception as e:
        logger.error(f"Delete custom stage error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/<slug>/rename', methods=['POST'])
def rename_custom_stage(slug):
    try:
        data = request.json
        new_name = data.get('newName', '').strip()
        if not new_name:
            return jsonify({'success': False, 'error': 'New name is required'}), 400

        metadata = _read_metadata()

        for existing in metadata.get('custom_stages', []):
            if _is_folder(existing):
                continue
            if existing.get('slug') != slug and existing.get('name', '').lower() == new_name.lower():
                return jsonify({'success': False, 'error': f"A stage named '{existing['name']}' already exists"}), 400

        stage_entry = None
        for s in metadata.get('custom_stages', []):
            if _is_folder(s):
                continue
            if s.get('slug') == slug:
                s['name'] = new_name
                stage_entry = s
                break

        if not stage_entry:
            return jsonify({'success': False, 'error': f'Stage {slug} not found'}), 404

        stage_json_path = CUSTOM_STAGES_PATH / slug / 'stage.json'
        if stage_json_path.exists():
            with open(stage_json_path, 'r') as f:
                stage_data = json.load(f)
            stage_data['name'] = new_name
            with open(stage_json_path, 'w') as f:
                json.dump(stage_data, f, indent=2)

        _write_metadata(metadata)

        logger.info(f"[OK] Renamed custom stage '{slug}' to '{new_name}'")
        return jsonify({'success': True, 'stage': stage_entry})
    except Exception as e:
        logger.error(f"Rename custom stage error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/<slug>/export', methods=['GET'])
def export_custom_stage(slug):
    zip_path = CUSTOM_STAGES_PATH / slug / 'stage.zip'
    if zip_path.exists():
        return send_file(zip_path, as_attachment=True, download_name=f'{slug}.zip')

    return jsonify({'success': False, 'error': 'Stage ZIP not found (imported from project scan?)'}), 404


@custom_stages_bp.route('/api/mex/custom-stages/install', methods=['POST'])
def install_custom_stage():
    """Install a custom stage from the vault into the currently open project."""
    try:
        data = request.json or {}
        slug = data.get('slug', '').strip()
        if not slug:
            return jsonify({'success': False, 'error': 'Missing slug parameter'}), 400

        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No project loaded. Open a project first.'}), 400

        zip_path = CUSTOM_STAGES_PATH / slug / 'stage.zip'
        if not zip_path.exists():
            return jsonify({'success': False, 'error': f'Stage ZIP not found for "{slug}". Re-scan the ISO to generate it.'}), 404

        mexcli_path = str(MEXCLI_PATH)
        if not Path(mexcli_path).exists():
            return jsonify({'success': False, 'error': 'MexCLI not found'}), 500

        cmd = [mexcli_path, 'add-stage', str(project_path), str(zip_path)]
        logger.info(f"Installing custom stage '{slug}': {' '.join(cmd)}")

        # Workspace-mutating MexCLI call -- hold the project lock so it can't run
        # concurrently with a background costume reorder / export.
        with mexcli_lock:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                cwd=str(PROJECT_ROOT), **get_subprocess_args()
            )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or 'Unknown error'
            logger.error(f"add-stage failed: {error_msg}")
            return jsonify({'success': False, 'error': f'Failed to add stage: {error_msg}'}), 500

        from blueprints.custom_characters import _parse_cli_json, _run_mexcli
        cli_output = _parse_cli_json(result.stdout)
        stage_name = cli_output.get('name', slug)

        # Port the stage's music playlist: add each track to the target
        # project (reusing same-named ones), then point the stage at them —
        # add-stage itself resets the playlist to a single default track
        warnings = []
        playlist_ported = 0
        metadata = _read_metadata()
        entry = next((s for s in metadata.get('custom_stages', [])
                      if not _is_folder(s) and s.get('slug') == slug), None)
        playlist = (entry or {}).get('playlist') or []
        if playlist:
            stage_dir = CUSTOM_STAGES_PATH / slug
            cli_entries = []
            for i, track in enumerate(playlist):
                hps = stage_dir / f'music_{i}.hps'
                if not hps.exists() or not track.get('name'):
                    warnings.append(f"Track '{track.get('name')}' file missing, skipped")
                    continue
                with mexcli_lock:
                    music_out = _run_mexcli('add-music', project_path, hps, track['name'])
                if music_out.get('success') and 'musicId' in music_out:
                    cli_entries.append({'musicId': music_out['musicId'],
                                        'chance': track.get('chance', 50)})
                else:
                    warnings.append(f"Track '{track['name']}' could not be added")
            if cli_entries:
                with mexcli_lock:
                    pl_result = subprocess.run(
                        [str(MEXCLI_PATH), 'set-stage-playlist', str(project_path), stage_name],
                        input=json.dumps(cli_entries),
                        capture_output=True, text=True,
                        cwd=str(PROJECT_ROOT), **get_subprocess_args()
                    )
                if pl_result.returncode == 0 and _parse_cli_json(pl_result.stdout).get('success'):
                    playlist_ported = len(cli_entries)
                    logger.info(f"Ported {playlist_ported} playlist track(s) for stage '{stage_name}'")
                else:
                    warnings.append('Stage playlist could not be set')
                    logger.warning(f"set-stage-playlist failed: {pl_result.stdout or pl_result.stderr}")

        import time
        time.sleep(0.15)
        reload_mex_manager()

        message = f"Added {stage_name} to project"
        if playlist_ported:
            message += f" with {playlist_ported} music track(s)"
        logger.info(f"[OK] Installed custom stage '{slug}' into project")
        return jsonify({
            'success': True,
            'message': message,
            'name': stage_name,
            'playlistPorted': playlist_ported,
            'warnings': warnings,
        })
    except Exception as e:
        logger.error(f"Install custom stage error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def _stage_manifest_entry(slug):
    """Build the add-stages manifest entry for a vault stage: the raw stage.zip plus
    its playlist (hps path + name + chance per track), mirroring install_custom_stage.
    Returns (entry_dict, warnings) or (None, [error])."""
    zip_path = CUSTOM_STAGES_PATH / slug / 'stage.zip'
    if not zip_path.exists():
        return None, [f'Stage ZIP not found for "{slug}". Re-scan the ISO to generate it.']

    e = {'zip': str(zip_path)}
    warnings = []
    metadata = _read_metadata()
    entry = next((s for s in metadata.get('custom_stages', [])
                  if not _is_folder(s) and s.get('slug') == slug), None)
    playlist = (entry or {}).get('playlist') or []
    if playlist:
        stage_dir = CUSTOM_STAGES_PATH / slug
        tracks = []
        for i, track in enumerate(playlist):
            hps = stage_dir / f'music_{i}.hps'
            if not hps.exists() or not track.get('name'):
                warnings.append(f"{slug}: track '{track.get('name')}' file missing, skipped")
                continue
            tracks.append({'hps': str(hps), 'name': track['name'],
                           'chance': track.get('chance', 50)})
        if tracks:
            e['playlist'] = tracks
    return e, warnings


@custom_stages_bp.route('/api/mex/custom-stages/install-batch', methods=['POST'])
def install_custom_stages_batch():
    """Bulk-install several vault custom stages in ONE `add-stages` call -- one
    workspace Save instead of add-stage + (one add-music per track) + set-stage-playlist
    PER stage. Byte-identical to N sequential installs (validated full-tree).

    Body: { "slugs": ["awakening-wood-2", ...] }
    """
    try:
        data = request.json or {}
        slugs = [s.strip() for s in (data.get('slugs') or []) if s and s.strip()]
        if not slugs:
            return jsonify({'success': False, 'error': 'No slugs provided'}), 400

        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No project loaded. Open a project first.'}), 400
        mexcli_path = str(MEXCLI_PATH)
        if not Path(mexcli_path).exists():
            return jsonify({'success': False, 'error': 'MexCLI not found'}), 500

        from blueprints.custom_characters import _parse_cli_json

        # Stream progress so the UI doesn't sit at 0/N (same as the character
        # batch). Stages prepare fast, but the compile is one step — show it.
        socketio = get_socketio()
        total = len(slugs)

        def _emit(current, phase, name=None, message=None):
            try:
                socketio.emit('custom_stage_install_progress', {
                    'current': current, 'total': total,
                    'phase': phase, 'name': name, 'message': message})
            except Exception:
                pass

        manifest_stages, failed, warnings = [], [], []
        for i, slug in enumerate(slugs):
            _emit(i + 1, 'preparing', name=slug)
            entry, warns = _stage_manifest_entry(slug)
            if entry is None:
                failed.append({'slug': slug, 'error': warns[0] if warns else 'prepare failed'})
                continue
            manifest_stages.append(entry)
            warnings += warns

        if not manifest_stages:
            return jsonify({'success': False, 'error': 'No installable stages', 'failed': failed}), 400

        logger.info(f"=== BATCH STAGE INSTALL ({len(manifest_stages)} stages) ===")
        _emit(total, 'compiling', message='Building project…')
        fd, manifest_path = tempfile.mkstemp(suffix='.json', prefix='nucleus_stages_batch_')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump({'stages': manifest_stages}, f)
            with mexcli_lock:
                result = subprocess.run(
                    [mexcli_path, 'add-stages', str(project_path), manifest_path],
                    capture_output=True, text=True, cwd=str(PROJECT_ROOT), **get_subprocess_args())
        finally:
            try:
                os.unlink(manifest_path)
            except OSError:
                pass

        if result.returncode != 0:
            err = result.stderr or result.stdout or 'Unknown error'
            logger.error(f"add-stages batch failed: {err}")
            return jsonify({'success': False, 'error': f'Batch add failed: {err}'}), 500

        cli = _parse_cli_json(result.stdout)
        for sr in cli.get('stages', []):
            for w in (sr.get('warnings') or []):
                warnings.append(f"{sr.get('name', '?')}: {w}")

        import time
        time.sleep(0.15)
        reload_mex_manager()

        added = cli.get('totalAdded', 0)
        logger.info(f"[OK] Batch-installed {added} custom stage(s)")
        _emit(total, 'done')
        return jsonify({
            'success': True,
            'message': f"Added {added} stage(s) to project",
            'totalAdded': added,
            'totalFailed': cli.get('totalFailed', 0) + len(failed),
            'totalTracks': cli.get('totalTracks', 0),
            'stages': cli.get('stages', []),
            'failed': failed,
            'warnings': warnings,
        })
    except Exception as e:
        logger.error(f"Batch stage install error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/remove-from-project', methods=['POST'])
def remove_custom_stage_from_project():
    """Remove a custom stage from the currently open project."""
    try:
        data = request.json or {}
        stage_name = data.get('name', '').strip()
        if not stage_name:
            return jsonify({'success': False, 'error': 'Missing name parameter'}), 400

        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No project loaded.'}), 400

        mexcli_path = str(MEXCLI_PATH)
        cmd = [mexcli_path, 'remove-stage', str(project_path), stage_name]
        logger.info(f"Removing stage '{stage_name}': {' '.join(cmd)}")

        with mexcli_lock:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                cwd=str(PROJECT_ROOT), **get_subprocess_args()
            )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or 'Unknown error'
            return jsonify({'success': False, 'error': f'Failed to remove stage: {error_msg}'}), 500

        import time
        time.sleep(0.15)
        reload_mex_manager()

        logger.info(f"[OK] Removed stage '{stage_name}' from project")
        return jsonify({'success': True, 'message': f'Removed {stage_name}'})
    except Exception as e:
        logger.error(f"Remove stage error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/remove-batch', methods=['POST'])
def remove_custom_stages_batch():
    """Bulk-remove several custom stages in ONE `remove-stages` call -- one workspace
    Save instead of one per stage. Byte-identical to N sequential removes (the live
    project matches; only a stale, never-loaded orphan stage json can differ).

    Body: { "names": ["My Stage", ...] }
    """
    try:
        data = request.json or {}
        names = [n.strip() for n in (data.get('names') or []) if n and n.strip()]
        if not names:
            return jsonify({'success': False, 'error': 'No names provided'}), 400

        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No project loaded.'}), 400
        mexcli_path = str(MEXCLI_PATH)
        if not Path(mexcli_path).exists():
            return jsonify({'success': False, 'error': 'MexCLI not found'}), 500

        from blueprints.custom_characters import _parse_cli_json
        logger.info(f"=== BATCH STAGE REMOVE ({len(names)} stages) ===")
        fd, manifest_path = tempfile.mkstemp(suffix='.json', prefix='nucleus_stages_rm_')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump({'stages': names}, f)
            with mexcli_lock:
                result = subprocess.run(
                    [mexcli_path, 'remove-stages', str(project_path), manifest_path],
                    capture_output=True, text=True, cwd=str(PROJECT_ROOT), **get_subprocess_args())
        finally:
            try:
                os.unlink(manifest_path)
            except OSError:
                pass

        if result.returncode != 0:
            err = result.stderr or result.stdout or 'Unknown error'
            logger.error(f"remove-stages batch failed: {err}")
            return jsonify({'success': False, 'error': f'Batch remove failed: {err}'}), 500

        cli = _parse_cli_json(result.stdout)
        import time
        time.sleep(0.15)
        reload_mex_manager()

        removed = cli.get('totalRemoved', 0)
        logger.info(f"[OK] Batch-removed {removed} custom stage(s)")
        return jsonify({
            'success': True,
            'message': f'Removed {removed} stage(s)',
            'totalRemoved': removed,
            'totalFailed': cli.get('totalFailed', 0),
            'stages': cli.get('stages', []),
        })
    except Exception as e:
        logger.error(f"Batch stage remove error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ============= Reorder + Folder Endpoints =============

@custom_stages_bp.route('/api/mex/custom-stages/reorder', methods=['POST'])
def reorder_custom_stages():
    """Reorder items (stages or folders) in the custom_stages list."""
    try:
        data = request.json or {}
        from_index = data.get('fromIndex')
        to_index = data.get('toIndex')

        if from_index is None or to_index is None:
            return jsonify({'success': False, 'error': 'Missing fromIndex or toIndex'}), 400

        metadata = _read_metadata()
        items = metadata.get('custom_stages', [])

        if from_index < 0 or from_index >= len(items) or to_index < 0 or to_index >= len(items):
            return jsonify({'success': False, 'error': 'Invalid fromIndex or toIndex'}), 400

        item = items.pop(from_index)
        items.insert(to_index, item)

        # Update folder membership for stages (not folders)
        if not _is_folder(item):
            new_folder_id = _folder_id_at_position(items, to_index)
            if new_folder_id:
                item['folder_id'] = new_folder_id
            elif 'folder_id' in item:
                del item['folder_id']

        metadata['custom_stages'] = items
        _write_metadata(metadata)

        logger.info(f"[OK] Reordered custom stages: {from_index} -> {to_index}")
        return jsonify({'success': True, 'stages': items})
    except Exception as e:
        logger.error(f"Reorder custom stages error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/folders/create', methods=['POST'])
def create_custom_stage_folder():
    try:
        data = request.json or {}
        name = data.get('name', 'New Folder')

        metadata = _read_metadata()
        items = metadata.setdefault('custom_stages', [])

        folder_id = f"folder_{uuid.uuid4().hex[:8]}"
        new_folder = {'type': 'folder', 'id': folder_id, 'name': name, 'expanded': True}
        items.append(new_folder)

        _write_metadata(metadata)
        logger.info(f"[OK] Created custom-stage folder '{name}'")
        return jsonify({'success': True, 'folder': new_folder})
    except Exception as e:
        logger.error(f"Create custom-stage folder error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/folders/rename', methods=['POST'])
def rename_custom_stage_folder():
    try:
        data = request.json or {}
        folder_id = data.get('folderId')
        new_name = data.get('newName')

        if not folder_id or not new_name:
            return jsonify({'success': False, 'error': 'Missing folderId or newName'}), 400

        metadata = _read_metadata()
        items = metadata.get('custom_stages', [])

        folder, _idx = _find_folder(items, folder_id)
        if not folder:
            return jsonify({'success': False, 'error': f'Folder {folder_id} not found'}), 404

        folder['name'] = new_name
        _write_metadata(metadata)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Rename custom-stage folder error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/folders/delete', methods=['POST'])
def delete_custom_stage_folder():
    """Delete a folder. Stages inside lose their folder_id but are kept."""
    try:
        data = request.json or {}
        folder_id = data.get('folderId')
        if not folder_id:
            return jsonify({'success': False, 'error': 'Missing folderId'}), 400

        metadata = _read_metadata()
        items = metadata.get('custom_stages', [])

        folder, folder_idx = _find_folder(items, folder_id)
        if not folder:
            return jsonify({'success': False, 'error': f'Folder {folder_id} not found'}), 404

        for it in items:
            if not _is_folder(it) and it.get('folder_id') == folder_id:
                del it['folder_id']

        items.pop(folder_idx)
        _write_metadata(metadata)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Delete custom-stage folder error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/set-folder', methods=['POST'])
def set_custom_stage_folder():
    """Assign or unassign a custom stage to a folder (drag-into-folder)."""
    try:
        data = request.json or {}
        stage_id = data.get('stageId')
        folder_id = data.get('folderId')

        if not stage_id:
            return jsonify({'success': False, 'error': 'Missing stageId'}), 400

        metadata = _read_metadata()
        items = metadata.get('custom_stages', [])

        # Custom-stage entries are keyed by 'slug' (no 'id' field); the grid
        # sends the slug as stageId. Match either so drag-into-folder works.
        stage = next((it for it in items if not _is_folder(it)
                      and (it.get('slug') == stage_id or it.get('id') == stage_id)), None)
        if not stage:
            return jsonify({'success': False, 'error': f'Stage {stage_id} not found'}), 404

        if folder_id:
            folder, _idx = _find_folder(items, folder_id)
            if not folder:
                return jsonify({'success': False, 'error': f'Folder {folder_id} not found'}), 404
            stage['folder_id'] = folder_id
        elif 'folder_id' in stage:
            del stage['folder_id']

        _write_metadata(metadata)
        logger.info(f"[OK] Set custom stage {stage_id} folder to {folder_id}")
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Set custom-stage folder error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/folders/toggle', methods=['POST'])
def toggle_custom_stage_folder():
    try:
        data = request.json or {}
        folder_id = data.get('folderId')
        if not folder_id:
            return jsonify({'success': False, 'error': 'Missing folderId'}), 400

        metadata = _read_metadata()
        items = metadata.get('custom_stages', [])
        folder, _idx = _find_folder(items, folder_id)
        if not folder:
            return jsonify({'success': False, 'error': f'Folder {folder_id} not found'}), 404

        folder['expanded'] = not folder.get('expanded', True)
        _write_metadata(metadata)
        return jsonify({'success': True, 'expanded': folder['expanded']})
    except Exception as e:
        logger.error(f"Toggle custom-stage folder error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
