import builtins
import hashlib
import os
import shutil
import sys
import uuid
from pathlib import Path

import pytest


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
