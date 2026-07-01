"""
Round-trip + migration tests for the SQLite vault backend (core.vault).

The headline guarantee: db_to_blob(blob_to_db(x)) == x for arbitrary vault
blobs, including the real dev metadata.json — this is what makes the migration
provably lossless (docs/VAULT_SQLITE_MIGRATION.md).
"""
import json
from pathlib import Path

import pytest

import core.vault as vault


def _roundtrip(tmp_path, blob):
    db = tmp_path / 'vault.db'
    vault.blob_to_db(blob, db)
    return vault.db_to_blob(db)


@pytest.mark.parametrize('blob', [
    {},
    {'version': '1.0'},
    {'characters': {}, 'stages': {}, 'xdelta': [],
     'custom_characters': [], 'custom_stages': [], 'bundles': []},
    # skins with an inline folder + folder_id membership + nested alternate_csps
    {'characters': {'Fox': {'skins': [
        {'type': 'folder', 'id': 'folder_1', 'name': 'F', 'expanded': True},
        {'id': 'a', 'color': 'Red', 'folder_id': 'folder_1'},
        {'id': 'b', 'color': 'Blue', 'alternate_csps': [{'id': 'x', 'pose_name': 'p'}]},
    ], 'extras': {'laser': [{'id': 'l1', 'modifications': {'wide': {'color': 'FC00'}}}],
                  'shine': []}}}},
    # character present with NO skins/extras keys (presence must be preserved)
    {'characters': {'Kirby': {}}},
    # empty-but-present lists/dicts (empty != absent)
    {'characters': {'Fox': {'skins': [], 'extras': {}}}, 'bundles': []},
    # stage variants incl. an ISO-scan entry with no filename
    {'stages': {'battlefield': {'variants': [
        {'id': 'v1', 'name': 'BF'}, {'id': 'v2', 'source': 'iso-scan', 'md5': 'abc'}]}}},
    # unicode payload (real data has mojibake like this)
    {'custom_stages': [{'slug': 'x', 'name': 'Peach�s Castle 64',
                        'playlist': [{'name': 'A', 'chance': 100}]}]},
    # nested ordered lists inside a custom_characters entry (kept verbatim)
    {'custom_characters': [{'slug': 'wolf', 'name': 'Wolf',
                            'costume_meta': [{'id': '1'}, {'id': '2'}], 'added_skins': []}]},
    # unknown top-level key routes to the catch-all and still round-trips
    {'mystery': {'weird': [1, 2, 3]}, 'version': '2.0'},
])
def test_roundtrip_exact(tmp_path, blob):
    assert _roundtrip(tmp_path, blob) == blob


def test_roundtrip_real_dev_metadata(tmp_path):
    """Strongest fixture: the actual dev vault, if present on this machine."""
    real = Path(__file__).resolve().parents[2] / 'storage' / 'metadata.json'
    if not real.exists():
        pytest.skip('no dev storage/metadata.json to validate against')
    source = json.loads(real.read_text(encoding='utf-8'))
    assert _roundtrip(tmp_path, source) == source


def test_blob_to_db_is_full_replace(tmp_path):
    db = tmp_path / 'vault.db'
    vault.blob_to_db({'bundles': [{'id': 'a'}]}, db)
    vault.blob_to_db({'bundles': [{'id': 'b'}]}, db)
    assert vault.db_to_blob(db) == {'bundles': [{'id': 'b'}]}


def test_db_to_blob_none_when_uninitialized(tmp_path):
    assert vault.db_to_blob(tmp_path / 'absent.db') is None


def test_migrate_backs_up_and_validates(tmp_path):
    j = tmp_path / 'metadata.json'
    src = {'characters': {'Fox': {'skins': [{'id': 'a'}]}}, 'version': '1.0'}
    j.write_text(json.dumps(src), encoding='utf-8')
    db = tmp_path / 'vault.db'

    res = vault.migrate_json_to_db(j, db)

    assert res['migrated'] is True
    assert Path(res['backup']).exists()                 # original JSON preserved
    assert json.loads(Path(res['backup']).read_text(encoding='utf-8')) == src
    assert vault.db_to_blob(db) == src                  # DB reproduces the source


def test_migrate_missing_json_initializes_empty_db(tmp_path):
    db = tmp_path / 'vault.db'
    res = vault.migrate_json_to_db(tmp_path / 'nope.json', db)
    assert res['migrated'] is False
    assert vault.is_initialized(db) is False            # no skeleton written yet


def test_export_db_to_json_roundtrips(tmp_path):
    db = tmp_path / 'vault.db'
    src = {'stages': {'battlefield': {'variants': [{'id': 'v1'}]}}}
    vault.blob_to_db(src, db)

    out = tmp_path / 'out.json'
    assert vault.export_db_to_json(out, db) is True
    assert json.loads(out.read_text(encoding='utf-8')) == src


def test_ensure_migrated_builds_then_noops(tmp_path, monkeypatch):
    import core.metadata as cm
    j = tmp_path / 'metadata.json'
    src = {'bundles': [{'id': 'a'}]}
    j.write_text(json.dumps(src), encoding='utf-8')
    db = tmp_path / 'vault.db'
    monkeypatch.setattr(cm, 'METADATA_FILE', j)

    first = vault.ensure_migrated(db=db)          # builds from JSON
    assert first['migrated'] is True
    assert vault.db_to_blob(db) == src

    second = vault.ensure_migrated(db=db)         # idempotent no-op
    assert second['migrated'] is False
