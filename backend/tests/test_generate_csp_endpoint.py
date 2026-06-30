"""
Tests for the "Retake CSP" endpoint (generate-csp): active-portrait resolution
and the apply (save) routing.

The headless render itself needs HSDRawViewer, so the preview render is verified
in-app; here we cover the pure metadata logic and the file/zip/metadata writes
the apply step performs (these mirror the proven update-csp / generate-stock
write paths).
"""
import base64
import io
import sys
import zipfile
from pathlib import Path

from flask import Flask
from PIL import Image

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import blueprints.storage_costumes as sc


def _client():
    app = Flask(__name__)
    app.register_blueprint(sc.storage_costumes_bp)
    return app.test_client()


def _png_data_uri(w, h, color=(200, 80, 80, 255)):
    img = Image.new('RGBA', (w, h), color)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')


def _make_costume_zip(path):
    with zipfile.ZipFile(path, 'w') as zf:
        zf.writestr('PlPkBkMod.dat', b'\x00' * 32)  # stand-in costume archive
        zf.writestr('csp.png', b'OLDCSP')


def _patch_meta(monkeypatch, tmp_path, meta):
    monkeypatch.setattr(sc, 'load_metadata', lambda: meta)
    monkeypatch.setattr(sc, 'save_metadata', lambda m: None)
    monkeypatch.setattr(sc, 'STORAGE_PATH', tmp_path)
    monkeypatch.setattr(sc, 'get_char_data', lambda m, c: m['characters'].get(c))


# ---- _resolve_active_portrait ------------------------------------------------

def test_resolve_default_when_no_active():
    assert sc._resolve_active_portrait({}) == (None, None)
    assert sc._resolve_active_portrait({'active_csp_id': None}) == (None, None)


def test_resolve_alt_pose():
    skin = {'active_csp_id': 'a1', 'alternate_csps': [
        {'id': 'a1', 'filename': 'x_csp_alt_1.png', 'pose_name': 'jump', 'is_hd': False},
        {'id': 'a1_hd', 'filename': 'x_csp_alt_1_hd.png', 'pose_name': 'jump', 'is_hd': True},
    ]}
    alt, pose = sc._resolve_active_portrait(skin)
    assert pose == 'jump'
    assert alt['id'] == 'a1'


def test_resolve_folds_hd_pointer_to_sd_sibling():
    skin = {'active_csp_id': 'a1_hd', 'alternate_csps': [
        {'id': 'a1', 'filename': 'x.png', 'pose_name': 'jump', 'is_hd': False},
        {'id': 'a1_hd', 'filename': 'x_hd.png', 'pose_name': 'jump', 'is_hd': True},
    ]}
    alt, pose = sc._resolve_active_portrait(skin)
    assert alt['id'] == 'a1'  # folded to the SD member
    assert pose == 'jump'


# ---- apply: original/default portrait ----------------------------------------

def test_apply_default_writes_csp_sd_hd_and_metadata(tmp_path, monkeypatch):
    character, skin_id = 'Pikachu', 'plpkbk'
    char_dir = tmp_path / character
    char_dir.mkdir(parents=True)
    zip_path = char_dir / f'{skin_id}.zip'
    _make_costume_zip(zip_path)

    meta = {'characters': {character: {'skins': [{'id': skin_id}]}}}
    _patch_meta(monkeypatch, tmp_path, meta)

    resp = _client().post('/api/mex/storage/costumes/generate-csp', json={
        'character': character, 'skinId': skin_id, 'apply': True,
        'imageData': _png_data_uri(544, 752),
    })
    data = resp.get_json()
    assert resp.status_code == 200 and data['success'] is True
    assert data['hasHd'] is True

    # SD standalone + HD standalone written; zip csp.png replaced; others kept
    assert (char_dir / f'{skin_id}_csp.png').exists()
    assert (char_dir / f'{skin_id}_csp_hd.png').exists()
    with zipfile.ZipFile(zip_path) as zf:
        assert zf.read('csp.png') != b'OLDCSP'
        assert 'PlPkBkMod.dat' in zf.namelist()

    skin = meta['characters'][character]['skins'][0]
    assert skin['has_csp'] and skin['csp_source'] == 'generated'
    assert skin['has_hd_csp'] and skin['hd_csp_source'] == 'generated'


# ---- apply: active pose alternate --------------------------------------------

def test_apply_alt_overwrites_alt_files_in_place(tmp_path, monkeypatch):
    character, skin_id = 'Pikachu', 'plpkbk'
    char_dir = tmp_path / character
    char_dir.mkdir(parents=True)
    _make_costume_zip(char_dir / f'{skin_id}.zip')
    sd_name = f'{skin_id}_csp_alt_1.png'
    hd_name = f'{skin_id}_csp_alt_1_hd.png'
    (char_dir / sd_name).write_bytes(b'OLDSD')
    (char_dir / hd_name).write_bytes(b'OLDHD')

    skin = {'id': skin_id, 'active_csp_id': 'a1', 'alternate_csps': [
        {'id': 'a1', 'filename': sd_name, 'pose_name': 'jump', 'is_hd': False},
        {'id': 'a1_hd', 'filename': hd_name, 'pose_name': 'jump', 'is_hd': True},
    ]}
    meta = {'characters': {character: {'skins': [skin]}}}
    _patch_meta(monkeypatch, tmp_path, meta)

    resp = _client().post('/api/mex/storage/costumes/generate-csp', json={
        'character': character, 'skinId': skin_id, 'apply': True,
        'imageData': _png_data_uri(544, 752),
    })
    data = resp.get_json()
    assert resp.status_code == 200 and data['success'] is True
    assert data['cspUrl'].endswith(sd_name)            # original CSP untouched
    assert not (char_dir / f'{skin_id}_csp.png').exists()
    assert (char_dir / sd_name).read_bytes() != b'OLDSD'   # alt SD overwritten
    assert (char_dir / hd_name).read_bytes() != b'OLDHD'   # alt HD overwritten


# ---- guards ------------------------------------------------------------------

def test_missing_params_400(tmp_path, monkeypatch):
    monkeypatch.setattr(sc, 'STORAGE_PATH', tmp_path)
    resp = _client().post('/api/mex/storage/costumes/generate-csp',
                          json={'character': 'Pikachu'})
    assert resp.status_code == 400


def test_missing_zip_404(tmp_path, monkeypatch):
    monkeypatch.setattr(sc, 'STORAGE_PATH', tmp_path)
    (tmp_path / 'Pikachu').mkdir()
    resp = _client().post('/api/mex/storage/costumes/generate-csp',
                          json={'character': 'Pikachu', 'skinId': 'nope'})
    assert resp.status_code == 404
