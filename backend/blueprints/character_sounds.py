"""
Character Sounds Blueprint - sound packs for vanilla characters.

A character can have any number of alternate sound packs in the vault;
each pack is a full copy of the character's voice/SFX bank
(audio/us/*.ssm) with per-sound replacements:

    storage/<Character>/sounds/
        original.ssm        (pristine bank, seeded from a project once;
                             the base for new packs and per-sound revert)
        names.json          (sound names captured from project data)
        packs/<pack-id>/
            pack.json       ({"name": ..., "created": ...})
            sound_mods.json (per-sound manifest: which indices were replaced)
            bank.ssm        (original + this pack's replacements)
            cache/          (decoded wav previews)

Packs are NOT applied automatically — installation is an explicit per-
project action (like importing a costume): the pack's bank is imported
into the open project through MexCLI's import-ssm (mexLib path) and the
choice is recorded in <project_dir>/nucleus_sounds.json. A raw file drop
into files/audio/us/ would not survive: mexLib regenerates every .ssm
from project data on workspace save, and the MxDt SSM table's recorded
buffer size would go stale (the game allocates that many bytes for the
bank).

Zelda and Sheik share one bank (zs.ssm); Sheik resolves to Zelda's vault
sounds folder so both characters see the same packs.
"""

import json
import re
import shutil
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

from core.config import STORAGE_PATH
from core.state import get_current_project_path

logger = logging.getLogger(__name__)

character_sounds_bp = Blueprint('character_sounds', __name__)

# vanilla vault character -> fighter sound bank (project files/audio/us/)
CHAR_BANKS = {
    'Bowser': 'koopa.ssm',
    'C. Falcon': 'captain.ssm',
    'DK': 'dk.ssm',
    'Dr. Mario': 'drmario.ssm',
    'Falco': 'falco.ssm',
    'Fox': 'fox.ssm',
    'Ganondorf': 'ganon.ssm',
    'Ice Climbers': 'ice.ssm',
    'Jigglypuff': 'purin.ssm',
    'Kirby': 'kirby.ssm',
    'Link': 'link.ssm',
    'Luigi': 'luigi.ssm',
    'Mario': 'mario.ssm',
    'Marth': 'mars.ssm',
    'Mewtwo': 'mewtwo.ssm',
    'Mr. Game & Watch': 'gw.ssm',
    'Ness': 'ness.ssm',
    'Peach': 'peach.ssm',
    'Pichu': 'pichu.ssm',
    'Pikachu': 'pikachu.ssm',
    'Roy': 'emblem.ssm',
    'Samus': 'samus.ssm',
    'Yoshi': 'yoshi.ssm',
    'Young Link': 'clink.ssm',
    'Zelda': 'zs.ssm',
}

# alternate fighter names (project fighter lists, older vault names) and
# shared-bank characters, mapped onto the canonical vault folder above
CHAR_ALIASES = {
    'Sheik': 'Zelda',                 # zs.ssm holds both
    'Captain Falcon': 'C. Falcon',
    'Donkey Kong': 'DK',
    'Game & Watch': 'Mr. Game & Watch',
    'Mr. Game and Watch': 'Mr. Game & Watch',
    'GameWatch': 'Mr. Game & Watch',
    'Popo': 'Ice Climbers',
    'Nana': 'Ice Climbers',
}


def _norm(name):
    n = (name or '').lower().replace(' and ', ' & ')
    return re.sub(r'[^a-z0-9&]', '', n)


_LOOKUP = {_norm(k): k for k in CHAR_BANKS}
_LOOKUP.update({_norm(k): v for k, v in CHAR_ALIASES.items()})


def resolve_character(character):
    """Map a character name (vault folder or fighter alias) to its
    canonical vault folder + bank filename. Returns (folder, bank) or
    (None, None) for non-vanilla names."""
    canonical = _LOOKUP.get(_norm(character))
    if canonical is None:
        return None, None
    return canonical, CHAR_BANKS[canonical]


def _sounds_dir(canonical):
    return STORAGE_PATH / canonical / 'sounds'


def _packs_dir(canonical):
    return _sounds_dir(canonical) / 'packs'


def _run_mexcli(*cli_args):
    from blueprints.custom_characters import _run_mexcli as run
    return run(*cli_args)


def _project_dir():
    project = get_current_project_path()
    return None if project is None else Path(project).parent


def _capture_names(bank, sdir):
    """Snapshot the bank's sound names out of the open project's data
    (vanilla banks carry real names like v_mars_atk1)."""
    pdir = _project_dir()
    if pdir is None:
        return
    sounds_data = pdir / 'data' / 'sounds'
    if not sounds_data.exists():
        return
    for gpath in sorted(sounds_data.glob('*.json')):
        try:
            g = json.loads(gpath.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            continue
        if (g.get('fileName') or '').lower() == bank.lower():
            names = [s.get('name') for s in (g.get('sounds') or [])]
            (sdir / 'names.json').write_text(
                json.dumps(names, indent=2), encoding='utf-8')
            return


def _ensure_original(canonical, bank):
    """Materialize the character's pristine bank, seeding it from the
    open project on first use. Returns the path or an error string."""
    sdir = _sounds_dir(canonical)
    original = sdir / 'original.ssm'
    if original.exists():
        return original
    pdir = _project_dir()
    if pdir is None:
        return 'Open a project first — the original sound bank is loaded from your build'
    src = pdir / 'files' / 'audio' / 'us' / bank
    if not src.exists():
        return f'Sound bank {bank} not found in the current project'
    sdir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, original)
    _capture_names(bank, sdir)
    return original


def _load_names(canonical):
    p = _sounds_dir(canonical) / 'names.json'
    if p.exists():
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            pass
    return []


def _pack_dir(canonical, pack_id):
    """Pack folder, validated against traversal. None when missing."""
    if not re.fullmatch(r'[a-z0-9][a-z0-9\-_]*', pack_id or ''):
        return None
    d = _packs_dir(canonical) / pack_id
    return d if (d / 'pack.json').exists() else None


def _pack_meta(pdir):
    try:
        return json.loads((pdir / 'pack.json').read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError):
        return {}


def _sound_mods(pdir):
    p = pdir / 'sound_mods.json'
    if p.exists():
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_sound_mods(pdir, mods):
    (pdir / 'sound_mods.json').write_text(
        json.dumps(mods, indent=2), encoding='utf-8')


def _invalidate_cache(pdir, index=None):
    cache = pdir / 'cache'
    if not cache.exists():
        return
    pattern = f'sound_{index}.wav' if index is not None else 'sound_*.wav'
    for f in cache.glob(pattern):
        f.unlink(missing_ok=True)


def _make_pack_id(canonical, name):
    slug = re.sub(r'-+', '-', re.sub(r'[^a-z0-9\-_]', '-', (name or '').lower())).strip('-_')
    slug = slug or 'pack'
    base, n = slug, 2
    while (_packs_dir(canonical) / slug).exists():
        slug = f'{base}-{n}'
        n += 1
    return slug


# ============= Per-project install record =============

INSTALL_RECORD = 'nucleus_sounds.json'


def _install_record(pdir):
    p = pdir / INSTALL_RECORD
    if p.exists():
        try:
            return json.loads(p.read_text(encoding='utf-8'))
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_install_record(pdir, record):
    p = pdir / INSTALL_RECORD
    if record:
        p.write_text(json.dumps(record, indent=2), encoding='utf-8')
    elif p.exists():
        p.unlink()


# ============= Pack management =============

@character_sounds_bp.route('/api/mex/storage/characters/<path:character>/sound-packs', methods=['GET'])
def list_sound_packs(character):
    canonical, bank = resolve_character(character)
    if canonical is None:
        return jsonify({'success': False, 'error': f'No sound bank for character: {character}'}), 404

    packs = []
    pk_root = _packs_dir(canonical)
    if pk_root.exists():
        for d in sorted(pk_root.iterdir()):
            if not (d / 'pack.json').exists():
                continue
            meta = _pack_meta(d)
            packs.append({
                'id': d.name,
                'name': meta.get('name') or d.name,
                'created': meta.get('created'),
                'modified_count': len(_sound_mods(d)),
            })

    # which pack (if any) is installed in the currently open project
    installed = None
    project_open = False
    pdir = _project_dir()
    if pdir is not None:
        project_open = True
        entry = _install_record(pdir).get(bank)
        if entry:
            installed = entry.get('pack')

    return jsonify({
        'success': True,
        'character': canonical,
        'bank': bank,
        'shared_with': ['Zelda', 'Sheik'] if bank == 'zs.ssm' else None,
        'packs': packs,
        'installed': installed,
        'project_open': project_open,
    })


@character_sounds_bp.route('/api/mex/storage/characters/<path:character>/sound-packs/create', methods=['POST'])
def create_sound_pack(character):
    canonical, bank = resolve_character(character)
    if canonical is None:
        return jsonify({'success': False, 'error': f'No sound bank for character: {character}'}), 404
    name = ((request.json or {}).get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Pack name required'}), 400

    original = _ensure_original(canonical, bank)
    if isinstance(original, str):
        return jsonify({'success': False, 'error': original}), 409

    pack_id = _make_pack_id(canonical, name)
    pdir = _packs_dir(canonical) / pack_id
    pdir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(original, pdir / 'bank.ssm')
    (pdir / 'pack.json').write_text(json.dumps({
        'name': name,
        'created': datetime.now().isoformat(),
    }, indent=2), encoding='utf-8')
    _save_sound_mods(pdir, {})

    return jsonify({'success': True, 'id': pack_id, 'name': name})


@character_sounds_bp.route('/api/mex/storage/characters/<path:character>/sound-packs/<pack_id>/rename', methods=['POST'])
def rename_sound_pack(character, pack_id):
    canonical, _bank = resolve_character(character)
    pdir = _pack_dir(canonical, pack_id) if canonical else None
    if pdir is None:
        return jsonify({'success': False, 'error': 'Sound pack not found'}), 404
    name = ((request.json or {}).get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Pack name required'}), 400
    meta = _pack_meta(pdir)
    meta['name'] = name
    (pdir / 'pack.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    return jsonify({'success': True, 'id': pack_id, 'name': name})


@character_sounds_bp.route('/api/mex/storage/characters/<path:character>/sound-packs/<pack_id>/delete', methods=['POST'])
def delete_sound_pack(character, pack_id):
    canonical, _bank = resolve_character(character)
    pdir = _pack_dir(canonical, pack_id) if canonical else None
    if pdir is None:
        return jsonify({'success': False, 'error': 'Sound pack not found'}), 404
    shutil.rmtree(pdir)
    return jsonify({'success': True})


# ============= Pack sound browser =============

# formats MeleeMedia's DSP.FromFile actually reads — the viewer converts
# everything else (mp3, ogg, flac...) to WAV client-side before uploading
SOUND_IMPORT_EXTS = {'.wav', '.brstm', '.dsp', '.hps'}


@character_sounds_bp.route('/api/mex/storage/characters/<path:character>/sound-packs/<pack_id>/audio/sounds', methods=['GET'])
def list_pack_sounds(character, pack_id):
    canonical, bank = resolve_character(character)
    pdir = _pack_dir(canonical, pack_id) if canonical else None
    if pdir is None:
        return jsonify({'success': False, 'error': 'Sound pack not found'}), 404

    info = _run_mexcli('ssm-info', pdir / 'bank.ssm')
    if not info.get('success'):
        return jsonify({'success': False, 'error': info.get('error', 'SSM read failed')}), 500

    names = _load_names(canonical)
    mods = _sound_mods(pdir)
    sounds = []
    for s in info.get('sounds', []):
        i = s['index']
        sounds.append({
            'index': i,
            'name': names[i] if i < len(names) and names[i] else f'sound_{i}',
            'durationMs': s.get('durationMs'),
            'frequency': s.get('frequency'),
            'modified': str(i) in mods,
            'source': (mods.get(str(i)) or {}).get('source'),
        })
    return jsonify({
        'success': True,
        'character': canonical,
        'bank': bank,
        'count': len(sounds),
        'sounds': sounds,
        'has_original_backup': (_sounds_dir(canonical) / 'original.ssm').exists(),
    })


@character_sounds_bp.route('/api/mex/storage/characters/<path:character>/sound-packs/<pack_id>/audio/sound/<int:index>', methods=['GET'])
def get_pack_sound(character, pack_id, index):
    canonical, _bank = resolve_character(character)
    pdir = _pack_dir(canonical, pack_id) if canonical else None
    if pdir is None:
        return jsonify({'success': False, 'error': 'Sound pack not found'}), 404
    cache = pdir / 'cache' / f'sound_{index}.wav'
    if not cache.exists():
        cache.parent.mkdir(exist_ok=True)
        out = _run_mexcli('ssm-to-wav', pdir / 'bank.ssm', index, cache)
        if not out.get('success') or not cache.exists():
            return jsonify({'success': False, 'error': out.get('error', 'SSM decode failed')}), 500
    return send_file(cache, mimetype='audio/wav')


@character_sounds_bp.route('/api/mex/storage/characters/<path:character>/sound-packs/<pack_id>/audio/sound/<int:index>/replace', methods=['POST'])
def replace_pack_sound(character, pack_id, index):
    """Replace one sound in the pack with an uploaded audio file."""
    canonical, _bank = resolve_character(character)
    pdir = _pack_dir(canonical, pack_id) if canonical else None
    if pdir is None:
        return jsonify({'success': False, 'error': 'Sound pack not found'}), 404

    file = request.files.get('file')
    if file is None or not file.filename:
        return jsonify({'success': False, 'error': 'No audio file uploaded'}), 400
    ext = Path(file.filename).suffix.lower()
    if ext not in SOUND_IMPORT_EXTS:
        return jsonify({'success': False,
                        'error': f"Unsupported format '{ext}' — use one of: "
                                 + ', '.join(sorted(SOUND_IMPORT_EXTS))}), 400

    bank_path = pdir / 'bank.ssm'
    with tempfile.TemporaryDirectory() as td:
        upload = Path(td) / f'upload{ext}'
        file.save(upload)
        new_bank = Path(td) / 'bank_new.ssm'
        out = _run_mexcli('ssm-replace', bank_path, index, upload, new_bank)
        if not out.get('success') or not new_bank.exists():
            return jsonify({'success': False, 'error': out.get('error', 'SSM replace failed')}), 500
        bank_path.write_bytes(new_bank.read_bytes())

    _invalidate_cache(pdir, index)
    mods = _sound_mods(pdir)
    mods[str(index)] = {'source': file.filename, 'date': datetime.now().isoformat()}
    _save_sound_mods(pdir, mods)

    return jsonify({'success': True, 'index': index,
                    'durationMs': out.get('durationMs'),
                    'frequency': out.get('frequency')})


@character_sounds_bp.route('/api/mex/storage/characters/<path:character>/sound-packs/<pack_id>/audio/sound/<int:index>/revert', methods=['POST'])
def revert_pack_sound(character, pack_id, index):
    """Restore one sound from the pristine bank (lossless copy)."""
    canonical, _bank = resolve_character(character)
    pdir = _pack_dir(canonical, pack_id) if canonical else None
    if pdir is None:
        return jsonify({'success': False, 'error': 'Sound pack not found'}), 404
    original = _sounds_dir(canonical) / 'original.ssm'
    if not original.exists():
        return jsonify({'success': False, 'error': 'No original bank — nothing to revert'}), 404

    bank_path = pdir / 'bank.ssm'
    with tempfile.TemporaryDirectory() as td:
        new_bank = Path(td) / 'bank_new.ssm'
        out = _run_mexcli('ssm-copy', original, index, bank_path, index, new_bank)
        if not out.get('success') or not new_bank.exists():
            return jsonify({'success': False, 'error': out.get('error', 'SSM copy failed')}), 500
        bank_path.write_bytes(new_bank.read_bytes())

    _invalidate_cache(pdir, index)
    mods = _sound_mods(pdir)
    mods.pop(str(index), None)
    _save_sound_mods(pdir, mods)

    return jsonify({'success': True, 'index': index,
                    'durationMs': out.get('durationMs'),
                    'frequency': out.get('frequency')})


@character_sounds_bp.route('/api/mex/storage/characters/<path:character>/sound-packs/<pack_id>/audio/sounds/revert-all', methods=['POST'])
def revert_all_pack_sounds(character, pack_id):
    canonical, _bank = resolve_character(character)
    pdir = _pack_dir(canonical, pack_id) if canonical else None
    if pdir is None:
        return jsonify({'success': False, 'error': 'Sound pack not found'}), 404
    original = _sounds_dir(canonical) / 'original.ssm'
    if not original.exists():
        return jsonify({'success': False, 'error': 'No original bank — nothing to revert'}), 404

    shutil.copy2(original, pdir / 'bank.ssm')
    _invalidate_cache(pdir)
    _save_sound_mods(pdir, {})
    return jsonify({'success': True})


# ============= Per-project install =============

@character_sounds_bp.route('/api/mex/storage/characters/<path:character>/sound-packs/<pack_id>/install', methods=['POST'])
def install_sound_pack(character, pack_id):
    """Install the pack's bank into the currently open project (explicit
    per-project action, like importing a costume)."""
    canonical, bank = resolve_character(character)
    pdir = _pack_dir(canonical, pack_id) if canonical else None
    if pdir is None:
        return jsonify({'success': False, 'error': 'Sound pack not found'}), 404
    project_dir = _project_dir()
    if project_dir is None:
        return jsonify({'success': False, 'error': 'No project open'}), 409

    project_file = get_current_project_path()
    out = _run_mexcli('import-ssm', project_file, bank, pdir / 'bank.ssm')
    if not out.get('success'):
        return jsonify({'success': False, 'error': out.get('error', 'Sound bank install failed')}), 500

    record = _install_record(project_dir)
    record[bank] = {
        'pack': pack_id,
        'character': canonical,
        'installed_at': datetime.now().isoformat(),
    }
    _save_install_record(project_dir, record)

    logger.info(f"Sound pack '{pack_id}' installed into {project_dir.name} ({bank})")
    return jsonify({'success': True, 'installed': pack_id, 'bank': bank})


@character_sounds_bp.route('/api/mex/storage/characters/<path:character>/sound-packs/uninstall', methods=['POST'])
def uninstall_sound_pack(character):
    """Restore the character's original sounds in the open project."""
    canonical, bank = resolve_character(character)
    if canonical is None:
        return jsonify({'success': False, 'error': f'No sound bank for character: {character}'}), 404
    project_dir = _project_dir()
    if project_dir is None:
        return jsonify({'success': False, 'error': 'No project open'}), 409
    original = _sounds_dir(canonical) / 'original.ssm'
    if not original.exists():
        return jsonify({'success': False, 'error': 'No original bank stored — nothing to restore'}), 404

    project_file = get_current_project_path()
    out = _run_mexcli('import-ssm', project_file, bank, original)
    if not out.get('success'):
        return jsonify({'success': False, 'error': out.get('error', 'Sound bank restore failed')}), 500

    record = _install_record(project_dir)
    record.pop(bank, None)
    _save_install_record(project_dir, record)

    return jsonify({'success': True, 'installed': None, 'bank': bank})
