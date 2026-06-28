import builtins
import hashlib
import io
import os
import shutil
import sys
import uuid
import zipfile
from pathlib import Path

import pytest
from flask import Flask


BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import importlib.util


def _load_setup_module():
    module_name = 'nucleus_setup_blueprint_test'
    module_path = BACKEND_DIR / 'blueprints' / 'setup.py'
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def setup_module():
    module = _load_setup_module()
    module.clear_iso_verification_cache()
    yield module
    module.clear_iso_verification_cache()


@pytest.fixture
def workspace_iso_dir():
    temp_dir = BACKEND_DIR.parent / 'storage' / 'pytest_setup_blueprint' / uuid.uuid4().hex
    temp_dir.mkdir(parents=True, exist_ok=True)
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_verify_iso_file_uses_cache_until_metadata_changes(workspace_iso_dir, monkeypatch, setup_module):
    iso_bytes = b'nucleus-test-iso'
    iso_path = workspace_iso_dir / 'GALE01.iso'
    iso_path.write_bytes(iso_bytes)
    monkeypatch.setattr(setup_module, 'VANILLA_ISO_MD5', hashlib.md5(iso_bytes).hexdigest())

    real_open = builtins.open
    open_calls = {'count': 0}

    def counting_open(file, mode='r', *args, **kwargs):
        if 'rb' in mode and Path(file).resolve() == iso_path.resolve():
            open_calls['count'] += 1
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, 'open', counting_open)

    first = setup_module.verify_iso_file(iso_path)
    second = setup_module.verify_iso_file(iso_path)

    assert first['valid'] is True
    assert first['cached'] is False
    assert second['valid'] is True
    assert second['cached'] is True
    assert open_calls['count'] == 1

    stat = iso_path.stat()
    os.utime(iso_path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    third = setup_module.verify_iso_file(iso_path)

    assert third['valid'] is True
    assert third['cached'] is False
    assert open_calls['count'] == 2


def _write_fake_iso(path, size, game_id=b'GALE01', version=0x02):
    """A file whose 8-byte disc header matches Melee, padded to `size`."""
    header = bytearray(8)
    header[:6] = game_id
    header[7] = version
    with open(path, 'wb') as f:
        f.write(header)
        if size > 8:
            f.seek(size - 1)
            f.write(b'\x00')


def test_name_score_prefers_vanilla_over_mod_names(setup_module):
    score = setup_module._vanilla_name_score
    assert score(Path('Melee.iso')) > score(Path('acebuild.iso'))
    assert score(Path('vanilla.iso')) > score(Path('z20XX 4.05 Corona Beginnings.iso'))
    assert score(Path('SSBM.iso')) > score(Path('Akaneia Build.iso'))


def test_finds_vanilla_among_mods_and_hashes_likely_one_first(workspace_iso_dir, monkeypatch, setup_module):
    """A modded build shares vanilla's header+size, so we must MD5 — but the
    vanilla-looking name is hashed FIRST and we early-exit, so the modded
    acebuild.iso is never hashed (the bug: header-only picked the mod)."""
    size = 4096
    monkeypatch.setattr(setup_module, 'VANILLA_ISO_EXPECTED_SIZE', size)

    vanilla = workspace_iso_dir / 'Melee.iso'
    mod = workspace_iso_dir / 'acebuild.iso'
    _write_fake_iso(vanilla, size)
    # give the mod distinct bytes so its md5 differs from vanilla's
    _write_fake_iso(mod, size)
    with open(mod, 'r+b') as f:
        f.seek(16)
        f.write(b'MODDEDBYTES')

    monkeypatch.setattr(setup_module, 'VANILLA_ISO_MD5',
                        hashlib.md5(vanilla.read_bytes()).hexdigest())

    hashed = []
    real_verify = setup_module.verify_iso_file

    def tracking_verify(p):
        hashed.append(Path(p).name)
        return real_verify(p)

    monkeypatch.setattr(setup_module, 'verify_iso_file', tracking_verify)

    found = setup_module.find_vanilla_melee_iso(str(workspace_iso_dir))
    assert found == str(vanilla)
    assert hashed == ['Melee.iso']  # early-exit: mod never hashed


def test_scan_skips_non_melee_header(workspace_iso_dir, monkeypatch, setup_module):
    size = 4096
    monkeypatch.setattr(setup_module, 'VANILLA_ISO_EXPECTED_SIZE', size)
    # Right size, wrong game id -> must be ignored before any hashing.
    _write_fake_iso(workspace_iso_dir / 'OtherGame.iso', size, game_id=b'GZLE01')

    found = setup_module.find_vanilla_melee_iso(str(workspace_iso_dir))
    assert found is None


def test_logs_zip_bundles_logs_and_diagnostics(tmp_path, monkeypatch, setup_module):
    logs = tmp_path / 'logs'
    logs.mkdir()
    (logs / 'mex_api.log').write_text('hello log', encoding='utf-8')
    (logs / 'csp_generation.log').write_text('csp log', encoding='utf-8')
    monkeypatch.setattr(setup_module, 'LOGS_PATH', logs)

    app = Flask(__name__)
    app.register_blueprint(setup_module.setup_bp)
    resp = app.test_client().get('/api/mex/logs/download')

    assert resp.status_code == 200
    assert resp.mimetype == 'application/zip'
    with zipfile.ZipFile(io.BytesIO(resp.data)) as zf:
        names = set(zf.namelist())
        assert 'diagnostics.txt' in names
        assert 'logs/mex_api.log' in names
        assert 'logs/csp_generation.log' in names
        assert zf.read('logs/mex_api.log') == b'hello log'


def test_logs_zip_ok_when_logs_dir_missing(tmp_path, monkeypatch, setup_module):
    """Even with no logs folder the zip still builds (carries diagnostics)."""
    monkeypatch.setattr(setup_module, 'LOGS_PATH', tmp_path / 'nonexistent')
    app = Flask(__name__)
    app.register_blueprint(setup_module.setup_bp)
    resp = app.test_client().get('/api/mex/logs/download')

    assert resp.status_code == 200
    with zipfile.ZipFile(io.BytesIO(resp.data)) as zf:
        assert 'diagnostics.txt' in zf.namelist()


def test_logs_zip_includes_slippi_dolphin_logs(tmp_path, monkeypatch, setup_module):
    """When a slippiPath is given, Dolphin's logs + crash dumps come along, but
    replays/ISOs in the User tree are NOT swept in."""
    monkeypatch.setattr(setup_module, 'LOGS_PATH', tmp_path / 'applogs')

    slippi = tmp_path / 'Slippi Launcher' / 'netplay'
    (slippi / 'User' / 'Logs').mkdir(parents=True)
    (slippi / 'User' / 'Slippi').mkdir(parents=True)  # replays — must be ignored
    (slippi / 'User' / 'Logs' / 'dolphin.log').write_text('dolphin crashed', encoding='utf-8')
    (slippi / 'User' / 'exception.dmp').write_bytes(b'DMP')
    (slippi / 'User' / 'Slippi' / 'Game_20260101.slp').write_bytes(b'REPLAY')
    (slippi.parent / 'launcher.log').write_text('launcher', encoding='utf-8')

    app = Flask(__name__)
    app.register_blueprint(setup_module.setup_bp)
    resp = app.test_client().get(f'/api/mex/logs/download?slippiPath={slippi}')

    assert resp.status_code == 200
    with zipfile.ZipFile(io.BytesIO(resp.data)) as zf:
        names = set(zf.namelist())
        assert 'slippi-dolphin/Logs/dolphin.log' in names
        assert 'slippi-dolphin/User/exception.dmp' in names
        assert 'slippi-dolphin/launcher/launcher.log' in names
        # the replay must NOT be in the zip
        assert not any(n.endswith('.slp') for n in names)
