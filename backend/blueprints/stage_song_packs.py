"""
Stage Song Packs Blueprint - alternate music playlists for DAS stages.

Each DAS stage (the six tournament stages) can have any number of song
packs in the vault; a pack is a playlist of tracks:

    storage/das/<stage_folder>/song_packs/<pack-id>/
        pack.json       ({"name", "created", "tracks": [{"name", "chance"}]})
        music_N.hps     (one per track, index-aligned with tracks)
        cache/          (decoded wav previews)

Packs are NOT applied automatically — installation is an explicit per-
project action: each track is added to the open project via MexCLI
add-music (content-aware dedupe reuses identical songs) and the stage's
playlist is pointed at them with set-stage-playlist. The choice is
recorded in <project_dir>/nucleus_songs.json. Uninstall sets an EMPTY
playlist, which is exactly the vanilla state (vanilla stage playlists are
empty in project data — the game falls back to the stage's default song).
"""

import json
import re
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

from core.config import STORAGE_PATH, MEXCLI_PATH, PROJECT_ROOT, get_subprocess_args
from core.state import get_current_project_path, mexcli_lock

logger = logging.getLogger(__name__)

stage_song_packs_bp = Blueprint('stage_song_packs', __name__)

# DAS stage code -> (vault folder, project stage name for set-stage-playlist)
DAS_SONG_STAGES = {
    'GrNBa': ('battlefield', 'Battlefield'),
    'GrNLa': ('final_destination', 'Final Destination'),
    'GrSt': ('yoshis_story', "Yoshi's Story"),
    'GrOp': ('dreamland', 'Dream Land N64'),
    'GrPs': ('pokemon_stadium', 'Pokemon Stadium'),
    'GrIz': ('fountain_of_dreams', 'Fountain of Dreams'),
}

# formats MeleeMedia's DSP.FromFile actually reads — the viewer converts
# everything else (mp3 etc.) to WAV client-side before uploading
MUSIC_IMPORT_EXTS = {'.wav', '.hps', '.brstm', '.dsp'}

INSTALL_RECORD = 'nucleus_songs.json'


def _run_mexcli(*cli_args):
    from blueprints.custom_characters import _run_mexcli as run
    return run(*cli_args)


def resolve_stage(stage):
    """Map a DAS stage code (or vault folder name) to (code, folder,
    project stage name). Returns (None, None, None) for unknown stages."""
    for code, (folder, name) in DAS_SONG_STAGES.items():
        if stage == code or stage == folder:
            return code, folder, name
    return None, None, None


def _packs_dir(folder):
    return STORAGE_PATH / 'das' / folder / 'song_packs'


def _pack_dir(folder, pack_id):
    """Pack folder, validated against traversal. None when missing."""
    if not re.fullmatch(r'[a-z0-9][a-z0-9\-_]*', pack_id or ''):
        return None
    d = _packs_dir(folder) / pack_id
    return d if (d / 'pack.json').exists() else None


def _pack_meta(pdir):
    try:
        return json.loads((pdir / 'pack.json').read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_pack_meta(pdir, meta):
    (pdir / 'pack.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')


def _invalidate_cache(pdir, index=None):
    cache = pdir / 'cache'
    if not cache.exists():
        return
    pattern = f'track_{index}.wav' if index is not None else 'track_*.wav'
    for f in cache.glob(pattern):
        f.unlink(missing_ok=True)


def _make_pack_id(folder, name):
    slug = re.sub(r'-+', '-', re.sub(r'[^a-z0-9\-_]', '-', (name or '').lower())).strip('-_')
    slug = slug or 'pack'
    base, n = slug, 2
    while (_packs_dir(folder) / slug).exists():
        slug = f'{base}-{n}'
        n += 1
    return slug


def _project_dir():
    project = get_current_project_path()
    return None if project is None else Path(project).parent


def _install_record(project_dir):
    p = project_dir / INSTALL_RECORD
    if p.exists():
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_install_record(project_dir, record):
    p = project_dir / INSTALL_RECORD
    if record:
        p.write_text(json.dumps(record, indent=2), encoding='utf-8')
    elif p.exists():
        p.unlink()


def _set_stage_playlist(project_file, stage_name, entries):
    """Run set-stage-playlist (entries JSON on stdin). Empty list clears
    the playlist, restoring vanilla default music."""
    from blueprints.custom_characters import _parse_cli_json
    # Workspace-mutating MexCLI call -- hold the project lock (shared with the
    # background costume reorder / export) so two MexCLI processes can't run at once.
    with mexcli_lock:
        result = subprocess.run(
            [str(MEXCLI_PATH), 'set-stage-playlist', str(project_file), stage_name],
            input=json.dumps(entries),
            capture_output=True, text=True,
            cwd=str(PROJECT_ROOT), **get_subprocess_args()
        )
    out = _parse_cli_json(result.stdout)
    out['_returncode'] = result.returncode
    return out


# ============= Pack management =============

@stage_song_packs_bp.route('/api/mex/das/<stage>/song-packs', methods=['GET'])
def list_song_packs(stage):
    code, folder, _name = resolve_stage(stage)
    if code is None:
        return jsonify({'success': False, 'error': f'Not a DAS stage: {stage}'}), 404

    packs = []
    pk_root = _packs_dir(folder)
    if pk_root.exists():
        for d in sorted(pk_root.iterdir()):
            if not (d / 'pack.json').exists():
                continue
            meta = _pack_meta(d)
            packs.append({
                'id': d.name,
                'name': meta.get('name') or d.name,
                'created': meta.get('created'),
                'track_count': len(meta.get('tracks') or []),
            })

    installed = None
    project_open = False
    pdir = _project_dir()
    if pdir is not None:
        project_open = True
        entry = _install_record(pdir).get(code)
        if entry:
            installed = entry.get('pack')

    return jsonify({
        'success': True,
        'stage': code,
        'packs': packs,
        'installed': installed,
        'project_open': project_open,
    })


@stage_song_packs_bp.route('/api/mex/das/<stage>/song-packs/create', methods=['POST'])
def create_song_pack(stage):
    code, folder, _name = resolve_stage(stage)
    if code is None:
        return jsonify({'success': False, 'error': f'Not a DAS stage: {stage}'}), 404
    name = ((request.json or {}).get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Pack name required'}), 400

    pack_id = _make_pack_id(folder, name)
    pdir = _packs_dir(folder) / pack_id
    pdir.mkdir(parents=True, exist_ok=True)
    _save_pack_meta(pdir, {
        'name': name,
        'created': datetime.now().isoformat(),
        'tracks': [],
    })
    return jsonify({'success': True, 'id': pack_id, 'name': name})


@stage_song_packs_bp.route('/api/mex/das/<stage>/song-packs/<pack_id>/rename', methods=['POST'])
def rename_song_pack(stage, pack_id):
    code, folder, _name = resolve_stage(stage)
    pdir = _pack_dir(folder, pack_id) if code else None
    if pdir is None:
        return jsonify({'success': False, 'error': 'Song pack not found'}), 404
    name = ((request.json or {}).get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Pack name required'}), 400
    meta = _pack_meta(pdir)
    meta['name'] = name
    _save_pack_meta(pdir, meta)
    return jsonify({'success': True, 'id': pack_id, 'name': name})


@stage_song_packs_bp.route('/api/mex/das/<stage>/song-packs/<pack_id>/delete', methods=['POST'])
def delete_song_pack(stage, pack_id):
    code, folder, _name = resolve_stage(stage)
    pdir = _pack_dir(folder, pack_id) if code else None
    if pdir is None:
        return jsonify({'success': False, 'error': 'Song pack not found'}), 404
    shutil.rmtree(pdir)
    return jsonify({'success': True})


# ============= Track editing =============

@stage_song_packs_bp.route('/api/mex/das/<stage>/song-packs/<pack_id>/tracks', methods=['GET'])
def list_pack_tracks(stage, pack_id):
    code, folder, _name = resolve_stage(stage)
    pdir = _pack_dir(folder, pack_id) if code else None
    if pdir is None:
        return jsonify({'success': False, 'error': 'Song pack not found'}), 404
    meta = _pack_meta(pdir)
    tracks = []
    for i, t in enumerate(meta.get('tracks') or []):
        tracks.append({
            'index': i,
            'name': t.get('name') or f'track_{i}',
            'chance': t.get('chance', 50),
            'has_file': (pdir / f'music_{i}.hps').exists(),
        })
    return jsonify({'success': True, 'name': meta.get('name'), 'tracks': tracks})


@stage_song_packs_bp.route('/api/mex/das/<stage>/song-packs/<pack_id>/tracks/add', methods=['POST'])
def add_pack_track(stage, pack_id):
    """Add a song to the pack. Non-HPS uploads are converted to HPS via
    MexCLI (mono sources are mirrored to stereo)."""
    code, folder, _name = resolve_stage(stage)
    pdir = _pack_dir(folder, pack_id) if code else None
    if pdir is None:
        return jsonify({'success': False, 'error': 'Song pack not found'}), 404

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

    meta = _pack_meta(pdir)
    tracks = meta.setdefault('tracks', [])
    index = len(tracks)
    hps_path = pdir / f'music_{index}.hps'

    if ext == '.hps':
        file.save(hps_path)
    else:
        with tempfile.TemporaryDirectory() as td:
            upload = Path(td) / f'upload{ext}'
            file.save(upload)
            out = _run_mexcli('audio-to-hps', upload, hps_path)
        if not out.get('success') or not hps_path.exists():
            return jsonify({'success': False, 'error': out.get('error', 'HPS conversion failed')}), 500

    tracks.append({'name': name, 'chance': chance})
    _save_pack_meta(pdir, meta)

    logger.info(f"[OK] Added track '{name}' to song pack '{pack_id}' ({code})")
    return jsonify({'success': True, 'track': {
        'index': index, 'name': name, 'chance': chance, 'has_file': True,
    }})


@stage_song_packs_bp.route('/api/mex/das/<stage>/song-packs/<pack_id>/tracks/<int:index>/update', methods=['POST'])
def update_pack_track(stage, pack_id, index):
    code, folder, _name = resolve_stage(stage)
    pdir = _pack_dir(folder, pack_id) if code else None
    if pdir is None:
        return jsonify({'success': False, 'error': 'Song pack not found'}), 404
    meta = _pack_meta(pdir)
    tracks = meta.get('tracks') or []
    if not (0 <= index < len(tracks)):
        return jsonify({'success': False, 'error': f'Track {index} out of range'}), 404

    data = request.get_json(silent=True) or {}
    if 'chance' in data:
        try:
            tracks[index]['chance'] = max(0, min(100, int(data['chance'])))
        except (TypeError, ValueError):
            return jsonify({'success': False, 'error': 'chance must be a number 0..100'}), 400
    if isinstance(data.get('name'), str) and data['name'].strip():
        tracks[index]['name'] = data['name'].strip()

    _save_pack_meta(pdir, meta)
    return jsonify({'success': True, 'track': {'index': index, **tracks[index]}})


@stage_song_packs_bp.route('/api/mex/das/<stage>/song-packs/<pack_id>/tracks/<int:index>/remove', methods=['POST'])
def remove_pack_track(stage, pack_id, index):
    """Remove a track and renumber the music_N.hps files after it."""
    code, folder, _name = resolve_stage(stage)
    pdir = _pack_dir(folder, pack_id) if code else None
    if pdir is None:
        return jsonify({'success': False, 'error': 'Song pack not found'}), 404
    meta = _pack_meta(pdir)
    tracks = meta.get('tracks') or []
    if not (0 <= index < len(tracks)):
        return jsonify({'success': False, 'error': f'Track {index} out of range'}), 404

    (pdir / f'music_{index}.hps').unlink(missing_ok=True)
    for j in range(index + 1, len(tracks)):
        src = pdir / f'music_{j}.hps'
        if src.exists():
            src.rename(pdir / f'music_{j - 1}.hps')

    tracks.pop(index)
    _save_pack_meta(pdir, meta)
    _invalidate_cache(pdir)
    return jsonify({'success': True})


@stage_song_packs_bp.route('/api/mex/das/<stage>/song-packs/<pack_id>/track/<int:index>', methods=['GET'])
def get_pack_track(stage, pack_id, index):
    """Decode a track to WAV for preview."""
    code, folder, _name = resolve_stage(stage)
    pdir = _pack_dir(folder, pack_id) if code else None
    if pdir is None:
        return jsonify({'success': False, 'error': 'Song pack not found'}), 404
    cache = pdir / 'cache' / f'track_{index}.wav'
    if not cache.exists():
        hps = pdir / f'music_{index}.hps'
        if not hps.exists():
            return jsonify({'success': False, 'error': 'Track file missing'}), 404
        cache.parent.mkdir(exist_ok=True)
        out = _run_mexcli('hps-to-wav', hps, cache)
        if not out.get('success') or not cache.exists():
            return jsonify({'success': False, 'error': out.get('error', 'HPS decode failed')}), 500
    return send_file(cache, mimetype='audio/wav')


# ============= Per-project install =============

@stage_song_packs_bp.route('/api/mex/das/<stage>/song-packs/<pack_id>/install', methods=['POST'])
def install_song_pack(stage, pack_id):
    """Install the pack into the currently open project: add each track's
    music (content-aware dedupe) and point the stage's playlist at them."""
    code, folder, stage_name = resolve_stage(stage)
    pdir = _pack_dir(folder, pack_id) if code else None
    if pdir is None:
        return jsonify({'success': False, 'error': 'Song pack not found'}), 404
    project_dir = _project_dir()
    if project_dir is None:
        return jsonify({'success': False, 'error': 'No project open'}), 409

    meta = _pack_meta(pdir)
    tracks = meta.get('tracks') or []
    if not tracks:
        return jsonify({'success': False, 'error': 'This pack has no songs yet'}), 400

    project_file = get_current_project_path()
    warnings = []
    cli_entries = []
    for i, track in enumerate(tracks):
        hps = pdir / f'music_{i}.hps'
        if not hps.exists() or not track.get('name'):
            warnings.append(f"Track '{track.get('name') or i}' file missing, skipped")
            continue
        music_out = _run_mexcli('add-music', project_file, hps, track['name'])
        if music_out.get('success') and 'musicId' in music_out:
            cli_entries.append({'musicId': music_out['musicId'],
                                'chance': track.get('chance', 50)})
        else:
            warnings.append(f"Track '{track['name']}' could not be added")

    if not cli_entries:
        return jsonify({'success': False,
                        'error': 'No tracks could be added to the project',
                        'warnings': warnings}), 500

    out = _set_stage_playlist(project_file, stage_name, cli_entries)
    if not out.get('success'):
        return jsonify({'success': False,
                        'error': out.get('error', 'Failed to set stage playlist'),
                        'warnings': warnings}), 500

    record = _install_record(project_dir)
    record[code] = {
        'pack': pack_id,
        'stage': stage_name,
        'installed_at': datetime.now().isoformat(),
    }
    _save_install_record(project_dir, record)

    logger.info(f"Song pack '{pack_id}' installed on {stage_name} "
                f"in {project_dir.name} ({len(cli_entries)} tracks)")
    return jsonify({'success': True, 'installed': pack_id,
                    'tracks': len(cli_entries), 'warnings': warnings})


@stage_song_packs_bp.route('/api/mex/das/<stage>/song-packs/uninstall', methods=['POST'])
def uninstall_song_pack(stage):
    """Restore the stage's vanilla music in the open project (clears the
    playlist — vanilla stage playlists are empty)."""
    code, _folder, stage_name = resolve_stage(stage)
    if code is None:
        return jsonify({'success': False, 'error': f'Not a DAS stage: {stage}'}), 404
    project_dir = _project_dir()
    if project_dir is None:
        return jsonify({'success': False, 'error': 'No project open'}), 409

    out = _set_stage_playlist(get_current_project_path(), stage_name, [])
    if not out.get('success'):
        return jsonify({'success': False,
                        'error': out.get('error', 'Failed to clear stage playlist')}), 500

    record = _install_record(project_dir)
    record.pop(code, None)
    _save_install_record(project_dir, record)

    return jsonify({'success': True, 'installed': None})
