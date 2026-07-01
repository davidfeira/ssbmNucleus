"""Tests for the vault backup/restore/clear blueprint.

Focus is the *merge* restore mode, which previously let ``zipf.extractall``
overwrite ``metadata.json`` -- wiping the current vault index instead of merging.
These tests pin the merge semantics (current items kept, backup items added,
no duplicates) and cover backup, replace-restore, and clear for good measure.

All filesystem state is redirected to ``tmp_path`` via monkeypatch, so the real
vault under ``storage/`` is never touched.
"""

import io
import json
import sys
import zipfile
from pathlib import Path

import pytest
from flask import Flask


BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from blueprints import vault_backup  # noqa: E402
import core.config as core_config  # noqa: E402
import core.vault as vaultmod  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

class _RecordingSocket:
    """Captures socketio.emit calls so tests can assert progress/complete events."""
    def __init__(self):
        self.events = []

    def emit(self, event, data=None):
        self.events.append((event, data))


class _SyncThread:
    """Stand-in for threading.Thread that runs the target inline on start(), so
    the restore worker completes synchronously within the request under test."""
    def __init__(self, target=None, args=(), kwargs=None, daemon=None):
        self._target, self._args, self._kwargs = target, args, kwargs or {}

    def start(self):
        if self._target:
            self._target(*self._args, **self._kwargs)


@pytest.fixture
def vault_env(tmp_path, monkeypatch):
    """Redirect the blueprint's storage/project/logs paths into tmp_path and
    return a Flask test client plus the patched paths. The restore worker thread
    is run synchronously and its socketio events are captured."""
    project_root = tmp_path / 'project'
    storage_path = project_root / 'storage'
    logs_path = project_root / 'logs'
    for p in (storage_path, logs_path):
        p.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(vault_backup, 'PROJECT_ROOT', project_root)
    monkeypatch.setattr(vault_backup, 'STORAGE_PATH', storage_path)
    monkeypatch.setattr(vault_backup, 'LOGS_PATH', logs_path)

    sock = _RecordingSocket()
    monkeypatch.setattr(vault_backup, 'get_socketio', lambda: sock)
    monkeypatch.setattr(vault_backup.threading, 'Thread', _SyncThread)

    app = Flask(__name__)
    app.register_blueprint(vault_backup.vault_backup_bp)
    client = app.test_client()

    return type('VaultEnv', (), {
        'client': client,
        'project_root': project_root,
        'storage_path': storage_path,
        'logs_path': logs_path,
        'socket': sock,
    })


def _restore_event(env, name):
    """Return the payload of the most recent captured restore event of ``name``."""
    return next((d for e, d in reversed(env.socket.events) if e == name), None)


def _write_metadata(storage_path, metadata):
    (storage_path / 'metadata.json').write_text(json.dumps(metadata), encoding='utf-8')


def _read_metadata(storage_path):
    return json.loads((storage_path / 'metadata.json').read_text(encoding='utf-8'))


def _make_backup_zip(metadata, extra_files=None):
    """Build an in-memory backup zip with metadata.json + optional data files.

    ``extra_files`` maps archive-relative posix paths to bytes.
    """
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('metadata.json', json.dumps(metadata))
        for arcname, content in (extra_files or {}).items():
            zf.writestr(arcname, content)
    buf.seek(0)
    return buf


def _skin(skin_id, color=None):
    return {'id': skin_id, 'color': color or skin_id, 'filename': f'{skin_id}.zip'}


def _variant(variant_id, name=None):
    return {'id': variant_id, 'name': name or variant_id, 'filename': f'{variant_id}.zip'}


# ---------------------------------------------------------------------------
# Pure merge function: merge_vault_metadata
# ---------------------------------------------------------------------------

def test_merge_keeps_current_and_adds_new_skins():
    current = {'characters': {'Fox': {'skins': [_skin('fox-red')]}}}
    incoming = {'characters': {'Fox': {'skins': [_skin('fox-blue')]}}}

    merged, stats = vault_backup.merge_vault_metadata(current, incoming)

    ids = [s['id'] for s in merged['characters']['Fox']['skins']]
    assert ids == ['fox-red', 'fox-blue']  # current first, backup appended
    assert stats['characters'] == 1


def test_merge_does_not_duplicate_shared_skins():
    current = {'characters': {'Fox': {'skins': [_skin('fox-red'), _skin('fox-blue')]}}}
    incoming = {'characters': {'Fox': {'skins': [_skin('fox-blue'), _skin('fox-green')]}}}

    merged, stats = vault_backup.merge_vault_metadata(current, incoming)

    ids = [s['id'] for s in merged['characters']['Fox']['skins']]
    assert ids == ['fox-red', 'fox-blue', 'fox-green']  # blue not duplicated
    assert stats['characters'] == 1


def test_merge_adds_character_absent_from_current():
    current = {'characters': {'Fox': {'skins': [_skin('fox-red')]}}}
    incoming = {'characters': {'Marth': {'skins': [_skin('marth-black'), _skin('marth-white')]}}}

    merged, stats = vault_backup.merge_vault_metadata(current, incoming)

    assert set(merged['characters']) == {'Fox', 'Marth'}
    assert [s['id'] for s in merged['characters']['Marth']['skins']] == ['marth-black', 'marth-white']
    assert stats['characters'] == 2  # whole new character's skins counted


def test_merge_handles_stage_variants():
    current = {'stages': {'battlefield': {'variants': [_variant('bf-a')]}}}
    incoming = {'stages': {
        'battlefield': {'variants': [_variant('bf-a'), _variant('bf-b')]},
        'dreamland': {'variants': [_variant('dl-a')]},
    }}

    merged, stats = vault_backup.merge_vault_metadata(current, incoming)

    assert [v['id'] for v in merged['stages']['battlefield']['variants']] == ['bf-a', 'bf-b']
    assert [v['id'] for v in merged['stages']['dreamland']['variants']] == ['dl-a']
    assert stats['stages'] == 2  # bf-b + dreamland's dl-a


def test_merge_dedupes_skin_folder_markers_by_id():
    folder = {'type': 'folder', 'id': 'folder_abc', 'name': 'Animelee', 'expanded': True}
    current = {'characters': {'Peach': {'skins': [folder, _skin('peach-a')]}}}
    incoming = {'characters': {'Peach': {'skins': [folder, _skin('peach-b')]}}}

    merged, stats = vault_backup.merge_vault_metadata(current, incoming)

    ids = [s['id'] for s in merged['characters']['Peach']['skins']]
    assert ids == ['folder_abc', 'peach-a', 'peach-b']  # folder not duplicated
    assert stats['characters'] == 1


def test_merge_top_level_lists_by_identity_key():
    current = {
        'xdelta': [{'id': 'x1', 'name': 'patch one'}],
        'custom_characters': [{'slug': 'wolf-2', 'name': 'Wolf'}],
        'bundles': [{'id': 'b1', 'name': 'Bundle One'}],
    }
    incoming = {
        'xdelta': [{'id': 'x1', 'name': 'patch one'}, {'id': 'x2', 'name': 'patch two'}],
        'custom_characters': [{'slug': 'roy-2', 'name': 'Roy'}],
        'custom_stages': [{'slug': 'castle-64', 'name': "Peach's Castle"}],
        'bundles': [{'id': 'b1', 'name': 'Bundle One'}],
    }

    merged, stats = vault_backup.merge_vault_metadata(current, incoming)

    assert [x['id'] for x in merged['xdelta']] == ['x1', 'x2']
    assert {c['slug'] for c in merged['custom_characters']} == {'wolf-2', 'roy-2'}
    assert [s['slug'] for s in merged['custom_stages']] == ['castle-64']
    assert [b['id'] for b in merged['bundles']] == ['b1']  # no dupe
    assert stats == {'characters': 0, 'stages': 0, 'xdelta': 1,
                     'custom_characters': 1, 'custom_stages': 1, 'bundles': 0}


def test_merge_does_not_mutate_inputs():
    current = {'characters': {'Fox': {'skins': [_skin('fox-red')]}}}
    incoming = {'characters': {'Fox': {'skins': [_skin('fox-blue')]}}}

    vault_backup.merge_vault_metadata(current, incoming)

    assert [s['id'] for s in current['characters']['Fox']['skins']] == ['fox-red']
    assert [s['id'] for s in incoming['characters']['Fox']['skins']] == ['fox-blue']


def test_merge_preserves_unknown_top_level_keys():
    current = {'version': '1.0', 'characters': {}}
    incoming = {'version': '1.0', 'menus': {'foo': 'bar'}, 'characters': {}}

    merged, _ = vault_backup.merge_vault_metadata(current, incoming)

    assert merged['version'] == '1.0'
    assert merged['menus'] == {'foo': 'bar'}  # carried over from incoming


def test_merge_into_empty_current():
    incoming = {'characters': {'Fox': {'skins': [_skin('fox-red')]}}}

    merged, stats = vault_backup.merge_vault_metadata({}, incoming)

    assert [s['id'] for s in merged['characters']['Fox']['skins']] == ['fox-red']
    assert stats['characters'] == 1


# ---------------------------------------------------------------------------
# Restore endpoint -- merge mode (the regression under test)
# ---------------------------------------------------------------------------

def test_restore_merge_keeps_current_vault_items(vault_env):
    # Current vault has Fox; backup has Marth + an extra Fox skin.
    _write_metadata(vault_env.storage_path, {
        'characters': {'Fox': {'skins': [_skin('fox-red')]}},
    })
    backup = _make_backup_zip({
        'characters': {
            'Fox': {'skins': [_skin('fox-blue')]},
            'Marth': {'skins': [_skin('marth-black')]},
        },
    }, extra_files={'Marth/marth-black.zip': b'marth-data'})

    resp = vault_env.client.post(
        '/api/mex/storage/restore',
        data={'mode': 'merge', 'file': (backup, 'backup.zip')},
        content_type='multipart/form-data',
    )

    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True
    assert body['mode'] == 'merge'

    meta = _read_metadata(vault_env.storage_path)
    # Current Fox skin is NOT wiped; backup items added.
    assert [s['id'] for s in meta['characters']['Fox']['skins']] == ['fox-red', 'fox-blue']
    assert 'Marth' in meta['characters']
    # Backup data file landed on disk.
    assert (vault_env.storage_path / 'Marth' / 'marth-black.zip').read_bytes() == b'marth-data'


def test_restore_merge_does_not_overwrite_existing_data_files(vault_env):
    _write_metadata(vault_env.storage_path, {'characters': {'Fox': {'skins': [_skin('fox-red')]}}})
    (vault_env.storage_path / 'Fox').mkdir()
    (vault_env.storage_path / 'Fox' / 'fox-red.zip').write_bytes(b'current-data')

    backup = _make_backup_zip(
        {'characters': {'Fox': {'skins': [_skin('fox-red')]}}},
        extra_files={'Fox/fox-red.zip': b'backup-data'},
    )

    resp = vault_env.client.post(
        '/api/mex/storage/restore',
        data={'mode': 'merge', 'file': (backup, 'backup.zip')},
        content_type='multipart/form-data',
    )

    assert resp.status_code == 200
    # Existing file preserved (current wins), not clobbered by the backup copy.
    assert (vault_env.storage_path / 'Fox' / 'fox-red.zip').read_bytes() == b'current-data'


def test_restore_merge_reports_added_count(vault_env):
    _write_metadata(vault_env.storage_path, {'characters': {'Fox': {'skins': [_skin('fox-red')]}}})
    backup = _make_backup_zip({'characters': {'Fox': {'skins': [_skin('fox-blue'), _skin('fox-green')]}}})

    resp = vault_env.client.post(
        '/api/mex/storage/restore',
        data={'mode': 'merge', 'file': (backup, 'backup.zip')},
        content_type='multipart/form-data',
    )

    # The route returns a restore_id immediately; the added count + message land
    # in the vault_restore_complete socket event.
    assert resp.status_code == 200
    assert resp.get_json()['restore_id']
    done = _restore_event(vault_env, 'vault_restore_complete')
    assert done['added']['characters'] == 2
    assert '2 new item' in done['message']


def test_restore_merge_does_not_leak_backup_files_into_kept_custom_character(vault_env):
    # The vault has custom character 'wolf' with 2 costumes; the backup has a
    # DIFFERENT 'wolf' build with extra costume files. Merge must keep ours
    # ATOMICALLY -- the backup's extra files must NOT leak into wolf's folder.
    _write_metadata(vault_env.storage_path, {
        'characters': {}, 'stages': {},
        'custom_characters': [{'slug': 'wolf', 'name': 'Wolf', 'costume_count': 2}],
    })
    wolf = vault_env.storage_path / 'custom_characters' / 'wolf'
    (wolf / 'costumes').mkdir(parents=True)
    (wolf / 'fighter.dat').write_bytes(b'CURRENT')
    (wolf / 'costumes' / 'red.png').write_bytes(b'cur-red')

    backup = _make_backup_zip(
        {'custom_characters': [
            {'slug': 'wolf', 'name': 'Wolf', 'costume_count': 4},
            {'slug': 'fawful', 'name': 'Fawful'},
        ]},
        extra_files={
            'custom_characters/wolf/fighter.dat': b'BACKUP',         # conflict -> skip
            'custom_characters/wolf/costumes/green.png': b'bak-green',  # would leak
            'custom_characters/wolf/costumes/yellow.png': b'bak-yel',   # would leak
            'custom_characters/fawful/fighter.dat': b'new-fawful',      # new -> copy
        },
    )

    resp = vault_env.client.post(
        '/api/mex/storage/restore',
        data={'mode': 'merge', 'file': (backup, 'backup.zip')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 200

    # Wolf is untouched: original files only, no backup leakage.
    assert (wolf / 'fighter.dat').read_bytes() == b'CURRENT'
    assert sorted(p.name for p in (wolf / 'costumes').iterdir()) == ['red.png']
    # The genuinely-new character came in whole.
    assert (vault_env.storage_path / 'custom_characters' / 'fawful' / 'fighter.dat').exists()

    done = _restore_event(vault_env, 'vault_restore_complete')
    assert done['report']['kept']['custom_characters'] == ['Wolf']
    assert done['report']['added']['custom_characters'] == ['Fawful']


def test_merge_plan_classifies_added_vs_kept_per_type():
    current = {
        'custom_characters': [{'slug': 'wolf', 'name': 'Wolf'}],
        'characters': {'Fox': {'skins': [{'id': 'fox-a', 'color': 'red'}]}},
        'stages': {'dreamland': {'variants': [{'id': 'dl-a', 'name': 'Cotton'}]}},
    }
    incoming = {
        'custom_characters': [{'slug': 'wolf', 'name': 'Wolf'},
                              {'slug': 'geno', 'name': 'Geno'}],
        'characters': {'Fox': {'skins': [{'id': 'fox-a', 'color': 'red'}, {'id': 'fox-b', 'color': 'blue'}]}},
        'stages': {'dreamland': {'variants': [{'id': 'dl-a', 'name': 'Cotton'}, {'id': 'dl-b', 'name': 'Neon'}]}},
    }

    report, skip = vault_backup.merge_plan(current, incoming)

    assert report['added']['custom_characters'] == ['Geno']
    assert report['kept']['custom_characters'] == ['Wolf']
    assert report['added']['skins'] == ['Fox blue']
    assert report['kept']['skins'] == ['Fox red']
    assert report['added']['variants'] == ['dreamland: Neon']
    assert report['kept']['variants'] == ['dreamland: Cotton']
    # Conflicting items contribute skip prefixes; new ones do not.
    assert 'custom_characters/wolf/' in skip
    assert 'custom_characters/geno/' not in skip
    assert 'Fox/fox-a.' in skip and 'Fox/fox-a_' in skip
    assert 'das/dreamland/dl-a.' in skip


def test_restore_emits_progress_and_completion_events(vault_env):
    _write_metadata(vault_env.storage_path, {'characters': {'Marth': {'skins': [_skin('marth-black')]}}})
    backup = _make_backup_zip(
        {'characters': {'Fox': {'skins': [_skin('fox-red')]}}},
        extra_files={f'Fox/file{i}.bin': b'x' * 8 for i in range(5)},
    )

    resp = vault_env.client.post(
        '/api/mex/storage/restore',
        data={'mode': 'replace', 'file': (backup, 'backup.zip')},
        content_type='multipart/form-data',
    )

    assert resp.status_code == 200
    events = vault_env.socket.events
    progress = [d for e, d in events if e == 'vault_restore_progress']
    assert progress, 'expected progress events'
    # Percentages are non-decreasing and bounded.
    pcts = [p['percentage'] for p in progress]
    assert pcts == sorted(pcts)
    assert all(0 <= p <= 100 for p in pcts)
    assert all(p.get('message') for p in progress)
    # Finishes with a single completion event, no error.
    assert [e for e, _ in events].count('vault_restore_complete') == 1
    assert not [e for e, _ in events if e == 'vault_restore_error']


# ---------------------------------------------------------------------------
# Restore endpoint -- replace mode
# ---------------------------------------------------------------------------

def test_restore_replace_wipes_current_and_extracts_backup(vault_env):
    _write_metadata(vault_env.storage_path, {'characters': {'Fox': {'skins': [_skin('fox-red')]}}})
    (vault_env.storage_path / 'Fox').mkdir()
    (vault_env.storage_path / 'Fox' / 'fox-red.zip').write_bytes(b'current-data')

    backup = _make_backup_zip(
        {'characters': {'Marth': {'skins': [_skin('marth-black')]}}},
        extra_files={'Marth/marth-black.zip': b'marth-data'},
    )

    resp = vault_env.client.post(
        '/api/mex/storage/restore',
        data={'mode': 'replace', 'file': (backup, 'backup.zip')},
        content_type='multipart/form-data',
    )

    assert resp.status_code == 200
    meta = _read_metadata(vault_env.storage_path)
    assert 'Fox' not in meta['characters']  # wiped
    assert 'Marth' in meta['characters']
    assert not (vault_env.storage_path / 'Fox').exists()
    assert (vault_env.storage_path / 'Marth' / 'marth-black.zip').exists()


def test_restore_defaults_to_replace_mode(vault_env):
    _write_metadata(vault_env.storage_path, {'characters': {'Fox': {'skins': [_skin('fox-red')]}}})
    backup = _make_backup_zip({'characters': {'Marth': {'skins': [_skin('marth-black')]}}})

    resp = vault_env.client.post(
        '/api/mex/storage/restore',
        data={'file': (backup, 'backup.zip')},  # no mode -> replace
        content_type='multipart/form-data',
    )

    assert resp.status_code == 200
    assert resp.get_json()['mode'] == 'replace'
    meta = _read_metadata(vault_env.storage_path)
    assert 'Fox' not in meta['characters']


# ---------------------------------------------------------------------------
# Restore endpoint -- validation / error paths
# ---------------------------------------------------------------------------

def test_restore_rejects_missing_file(vault_env):
    resp = vault_env.client.post(
        '/api/mex/storage/restore',
        data={'mode': 'merge'},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 400
    assert resp.get_json()['success'] is False


def test_restore_rejects_non_zip(vault_env):
    resp = vault_env.client.post(
        '/api/mex/storage/restore',
        data={'mode': 'merge', 'file': (io.BytesIO(b'nope'), 'backup.txt')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 400
    assert 'ZIP' in resp.get_json()['error']


def test_restore_rejects_zip_without_metadata(vault_env):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr('Fox/fox-red.zip', b'data')  # no metadata.json
    buf.seek(0)

    resp = vault_env.client.post(
        '/api/mex/storage/restore',
        data={'mode': 'merge', 'file': (buf, 'backup.zip')},
        content_type='multipart/form-data',
    )
    assert resp.status_code == 400
    assert 'metadata.json' in resp.get_json()['error']


def test_restore_merge_leaves_vault_intact_when_backup_invalid(vault_env):
    # An invalid backup must not have already wiped/altered the vault.
    _write_metadata(vault_env.storage_path, {'characters': {'Fox': {'skins': [_skin('fox-red')]}}})

    resp = vault_env.client.post(
        '/api/mex/storage/restore',
        data={'mode': 'merge', 'file': (io.BytesIO(b'not a zip'), 'backup.txt')},
        content_type='multipart/form-data',
    )

    assert resp.status_code == 400
    meta = _read_metadata(vault_env.storage_path)
    assert [s['id'] for s in meta['characters']['Fox']['skins']] == ['fox-red']


# ---------------------------------------------------------------------------
# Backup endpoint + round-trip
# ---------------------------------------------------------------------------

def test_backup_creates_zip_with_all_files(vault_env):
    _write_metadata(vault_env.storage_path, {'characters': {'Fox': {'skins': [_skin('fox-red')]}}})
    (vault_env.storage_path / 'Fox').mkdir()
    (vault_env.storage_path / 'Fox' / 'fox-red.zip').write_bytes(b'fox-data')

    resp = vault_env.client.post('/api/mex/storage/backup')

    assert resp.status_code == 200
    body = resp.get_json()
    assert body['success'] is True

    backup_path = Path(body['path'])
    assert backup_path.exists()
    with zipfile.ZipFile(backup_path, 'r') as zf:
        names = set(zf.namelist())
    # Paths are stored relative to STORAGE_PATH (posix separators in zip).
    assert 'metadata.json' in names
    assert 'Fox/fox-red.zip' in names


def test_backup_then_restore_merge_round_trip(vault_env):
    # Build a vault, back it up, mutate, then merge the backup back in.
    _write_metadata(vault_env.storage_path, {'characters': {'Fox': {'skins': [_skin('fox-red')]}}})
    (vault_env.storage_path / 'Fox').mkdir()
    (vault_env.storage_path / 'Fox' / 'fox-red.zip').write_bytes(b'fox-data')

    backup_resp = vault_env.client.post('/api/mex/storage/backup').get_json()
    backup_path = Path(backup_resp['path'])

    # Replace current vault with a different character.
    _write_metadata(vault_env.storage_path, {'characters': {'Marth': {'skins': [_skin('marth-black')]}}})

    with open(backup_path, 'rb') as f:
        backup_bytes = io.BytesIO(f.read())

    resp = vault_env.client.post(
        '/api/mex/storage/restore',
        data={'mode': 'merge', 'file': (backup_bytes, 'backup.zip')},
        content_type='multipart/form-data',
    )

    assert resp.status_code == 200
    meta = _read_metadata(vault_env.storage_path)
    # Both the current Marth and the restored Fox are present.
    assert set(meta['characters']) == {'Fox', 'Marth'}
    assert (vault_env.storage_path / 'Fox' / 'fox-red.zip').read_bytes() == b'fox-data'


# ---------------------------------------------------------------------------
# Clear endpoint
# ---------------------------------------------------------------------------

def test_clear_storage_removes_character_folders_and_resets_metadata(vault_env):
    _write_metadata(vault_env.storage_path, {'characters': {'Fox': {'skins': [_skin('fox-red')]}}})
    (vault_env.storage_path / 'Fox').mkdir()
    (vault_env.storage_path / 'Fox' / 'fox-red.zip').write_bytes(b'fox-data')
    # 'das' folder should be preserved structurally (stage root), its variants cleared.
    das = vault_env.storage_path / 'das'
    das.mkdir()

    resp = vault_env.client.post('/api/mex/storage/clear', json={})

    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
    assert not (vault_env.storage_path / 'Fox').exists()
    assert das.exists()  # das root kept
    meta = _read_metadata(vault_env.storage_path)
    assert meta == {'version': '1.0', 'characters': {}, 'stages': {}}


def test_clear_storage_optionally_clears_logs(vault_env):
    (vault_env.logs_path / 'app.log').write_text('log line', encoding='utf-8')
    (vault_env.logs_path / 'keep.txt').write_text('keep', encoding='utf-8')

    resp = vault_env.client.post('/api/mex/storage/clear', json={'clearLogs': True})

    assert resp.status_code == 200
    assert not (vault_env.logs_path / 'app.log').exists()  # .log removed
    assert (vault_env.logs_path / 'keep.txt').exists()      # non-log kept


# ---------------------------------------------------------------------------
# SQLite backend interaction: vault.db is a rebuildable cache, excluded from
# backups and rebuilt from the restored metadata.json (docs/VAULT_SQLITE_MIGRATION.md)
# ---------------------------------------------------------------------------

def _use_db(monkeypatch, storage_path):
    monkeypatch.setattr(core_config, 'VAULT_BACKEND', 'db')
    monkeypatch.setattr(core_config, 'VAULT_DB_PATH', storage_path / 'vault.db')
    monkeypatch.setattr(core_config, 'VAULT_DUAL_WRITE', False)


def test_backup_excludes_vault_db(vault_env):
    _write_metadata(vault_env.storage_path, {'bundles': [{'id': 'a'}]})
    # a stray SQLite cache + its WAL sidecars must NOT be in the portable backup
    (vault_env.storage_path / 'vault.db').write_bytes(b'SQLITECACHE')
    (vault_env.storage_path / 'vault.db-wal').write_bytes(b'WAL')

    resp = vault_env.client.post('/api/mex/storage/backup')

    assert resp.status_code == 200
    with zipfile.ZipFile(Path(resp.get_json()['path'])) as zf:
        names = set(zf.namelist())
    assert 'metadata.json' in names
    assert 'vault.db' not in names and 'vault.db-wal' not in names


def test_replace_restore_rebuilds_db(vault_env, monkeypatch):
    _use_db(monkeypatch, vault_env.storage_path)
    backup = _make_backup_zip({'bundles': [{'id': 'restored'}]})

    resp = vault_env.client.post(
        '/api/mex/storage/restore',
        data={'mode': 'replace', 'file': (backup, 'backup.zip')},
        content_type='multipart/form-data',
    )

    assert resp.status_code == 200
    # DB rebuilt from the restored metadata.json, so DB-mode reads see the restore
    assert vaultmod.db_to_blob(vault_env.storage_path / 'vault.db') == {'bundles': [{'id': 'restored'}]}


def test_merge_restore_rebuilds_db(vault_env, monkeypatch):
    _write_metadata(vault_env.storage_path, {'characters': {'Fox': {'skins': [_skin('fox-red')]}}})
    _use_db(monkeypatch, vault_env.storage_path)
    backup = _make_backup_zip({'characters': {'Fox': {'skins': [_skin('fox-blue')]}}})

    resp = vault_env.client.post(
        '/api/mex/storage/restore',
        data={'mode': 'merge', 'file': (backup, 'backup.zip')},
        content_type='multipart/form-data',
    )

    assert resp.status_code == 200
    rebuilt = vaultmod.db_to_blob(vault_env.storage_path / 'vault.db')
    ids = {s['id'] for s in rebuilt['characters']['Fox']['skins']}
    assert ids == {'fox-red', 'fox-blue'}      # DB reflects the merged catalog
