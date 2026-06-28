"""
Regression test for HSDRawViewer path resolution in generate_csp.

In a packaged build HSDRawViewer ships via electron-builder extraResources to
<install>/resources/utility/HSDRawViewer — NOT inside the PyInstaller bundle.
generate_csp must resolve it from the exe location, not relative to its own
(_MEIPASS) path, or every CSP render fails (the "230 preview failures" bug).
"""
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).parent.parent
PROCESSOR_DIR = BACKEND_DIR.parent / 'utility' / 'tools' / 'processor'
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(PROCESSOR_DIR))

generate_csp = pytest.importorskip('generate_csp')


def test_frozen_resolves_to_resources_not_meipass(monkeypatch, tmp_path):
    # Simulate the packaged layout: resources/backend/mex_backend.exe
    exe = tmp_path / 'resources' / 'backend' / 'mex_backend.exe'
    exe.parent.mkdir(parents=True)
    monkeypatch.setattr(sys, 'frozen', True, raising=False)
    monkeypatch.setattr(sys, 'executable', str(exe))

    resolved = Path(generate_csp._resolve_hsdraw_dir())
    # -> resources/utility/HSDRawViewer  (sibling of backend/, under resources/)
    assert resolved == tmp_path / 'resources' / 'utility' / 'HSDRawViewer'
    # must NOT be relative to the bundled script dir
    assert 'tools' not in resolved.parts or 'HSDLib' not in resolved.parts


def test_dev_resolves_to_source_tree(monkeypatch):
    monkeypatch.setattr(sys, 'frozen', False, raising=False)
    resolved = Path(generate_csp._resolve_hsdraw_dir())
    assert resolved.name == 'net6.0-windows'
    assert 'HSDLib' in resolved.parts
