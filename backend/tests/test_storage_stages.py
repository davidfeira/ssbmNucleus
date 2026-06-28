"""
Regression test for the DAS vault delete bug: variants imported via ISO scan
have no 'filename' key, so delete_storage_stage KeyError'd with
"Delete failed: 'filename'". Delete must fall back to the <id>.zip convention.
"""
import sys
from pathlib import Path

from flask import Flask

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import blueprints.storage_stages as ss


def _client():
    app = Flask(__name__)
    app.register_blueprint(ss.storage_stages_bp)
    return app.test_client()


def test_delete_variant_without_filename_key(tmp_path, monkeypatch):
    # ISO-scan-style entry: id/name/source/md5 but NO 'filename'
    meta = {'stages': {'battlefield': {'variants': [
        {'id': 'bf0', 'name': 'BF 0', 'source': 'iso-scan:20xx', 'md5': 'abc'},
    ]}}}
    monkeypatch.setattr(ss, 'load_metadata', lambda: meta)
    monkeypatch.setattr(ss, 'save_metadata', lambda m: None)
    monkeypatch.setattr(ss, 'STORAGE_PATH', tmp_path)

    das = tmp_path / 'das' / 'battlefield'
    das.mkdir(parents=True)
    (das / 'bf0.zip').write_bytes(b'ZIP')               # <id>.zip convention
    (das / 'bf0_screenshot.png').write_bytes(b'PNG')

    resp = _client().post('/api/mex/storage/stages/delete',
                          json={'stageFolder': 'battlefield', 'variantId': 'bf0'})

    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
    assert not (das / 'bf0.zip').exists()
    assert not (das / 'bf0_screenshot.png').exists()
    assert meta['stages']['battlefield']['variants'] == []


def test_delete_variant_with_filename_key(tmp_path, monkeypatch):
    """The normal path (entry has 'filename') still works."""
    meta = {'stages': {'yoshisstory': {'variants': [
        {'id': 'ys1', 'name': 'YS 1', 'filename': 'custom_name.zip'},
    ]}}}
    monkeypatch.setattr(ss, 'load_metadata', lambda: meta)
    monkeypatch.setattr(ss, 'save_metadata', lambda m: None)
    monkeypatch.setattr(ss, 'STORAGE_PATH', tmp_path)

    das = tmp_path / 'das' / 'yoshisstory'
    das.mkdir(parents=True)
    (das / 'custom_name.zip').write_bytes(b'ZIP')

    resp = _client().post('/api/mex/storage/stages/delete',
                          json={'stageFolder': 'yoshisstory', 'variantId': 'ys1'})

    assert resp.status_code == 200
    assert resp.get_json()['success'] is True
    assert not (das / 'custom_name.zip').exists()
