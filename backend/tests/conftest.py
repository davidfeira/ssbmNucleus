"""
Shared pytest fixtures for backend tests.

The headline fixture is `vault`, a temp-directory stand-in for the user's
`storage/` folder wired into the REAL `core.metadata` load/save path. Tests that
use it exercise actual metadata file IO (not monkeypatched lambdas), so the SAME
test will keep working when the storage backend swaps from metadata.json to
SQLite — that backend-agnostic property is the whole point of the Phase 0 safety
net for the vault-storage migration (see docs/VAULT_SQLITE_MIGRATION.md).

Usage:

    def test_something(vault):
        vault.write({'characters': {'Fox': {'skins': []}}})
        client = vault.client(storage_costumes, 'storage_costumes_bp')
        resp = client.post('/api/mex/storage/...', json={...})
        assert vault.read()['characters']['Fox']['skins'] == [...]
"""
import sys
from pathlib import Path

import pytest
from flask import Flask

# Every test module historically inserts BACKEND_DIR itself; doing it here once
# (conftest imports before test collection) makes `import core.*` / `blueprints.*`
# work without each test repeating the boilerplate.
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import core.metadata as core_metadata  # noqa: E402
import core.config as core_config      # noqa: E402


class VaultHarness:
    """A temp vault: real metadata IO + filesystem helpers + a wired Flask client."""

    def __init__(self, storage: Path, monkeypatch):
        self.storage = storage
        self.project_root = storage.parent
        self._mp = monkeypatch

    # ---- metadata IO (goes through the real core.metadata, redirected to tmp) ----
    def write(self, metadata: dict) -> dict:
        core_metadata.save_metadata(metadata)
        return metadata

    def read(self):
        return core_metadata.load_metadata()

    # ---- filesystem helpers ----
    def path(self, *parts) -> Path:
        p = self.storage.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def touch(self, *parts, data: bytes = b'x') -> Path:
        p = self.path(*parts)
        p.write_bytes(data)
        return p

    def add_costume_files(self, character, skin_id, *, csp=False, stock=False, hd=False):
        """Create the on-disk footprint that list_storage_costumes checks for."""
        self.touch(character, f'{skin_id}.zip')
        if csp:
            self.touch(character, f'{skin_id}_csp.png')
        if stock:
            self.touch(character, f'{skin_id}_stc.png')
        if hd:
            self.touch(character, f'{skin_id}_csp_hd.png')

    def add_stage_variant_zip(self, stage, variant_id):
        """Stage variant zips live at storage/das/<stage>/<id>.zip."""
        self.touch('das', stage, f'{variant_id}.zip')

    # ---- Flask client wired to this vault ----
    def client(self, module, bp_attr: str):
        """Build a test client for one blueprint, repointing its module-level
        STORAGE_PATH / PROJECT_ROOT at this temp vault. (Blueprints bind those
        names at import time, so patching core.config alone is not enough.)"""
        if hasattr(module, 'STORAGE_PATH'):
            self._mp.setattr(module, 'STORAGE_PATH', self.storage)
        if hasattr(module, 'PROJECT_ROOT'):
            self._mp.setattr(module, 'PROJECT_ROOT', self.project_root)
        app = Flask(__name__)
        app.register_blueprint(getattr(module, bp_attr))
        return app.test_client()


@pytest.fixture
def vault(tmp_path, monkeypatch):
    storage = tmp_path / 'storage'
    storage.mkdir()
    # Redirect the canonical metadata file at the temp vault. core.metadata
    # resolves METADATA_FILE at call time, and every blueprint's load_metadata/
    # save_metadata is the same function object, so this one patch covers them all.
    monkeypatch.setattr(core_metadata, 'METADATA_FILE', storage / 'metadata.json')
    monkeypatch.setattr(core_config, 'STORAGE_PATH', storage, raising=False)
    # Default to the JSON backend (existing tests assert JSON-specific behavior).
    monkeypatch.setattr(core_config, 'VAULT_BACKEND', 'json', raising=False)
    monkeypatch.setattr(core_config, 'VAULT_DB_PATH', storage / 'vault.db', raising=False)
    return VaultHarness(storage, monkeypatch)


@pytest.fixture(params=['json', 'db'])
def dual_backend(request, tmp_path, monkeypatch):
    """Like `vault`, but parametrized over BOTH storage backends so a single
    test asserts identical behavior on JSON and SQLite — the equivalence proof
    for the metadata.json -> DB migration."""
    storage = tmp_path / 'storage'
    storage.mkdir()
    monkeypatch.setattr(core_metadata, 'METADATA_FILE', storage / 'metadata.json')
    monkeypatch.setattr(core_config, 'STORAGE_PATH', storage, raising=False)
    monkeypatch.setattr(core_config, 'VAULT_DB_PATH', storage / 'vault.db', raising=False)
    monkeypatch.setattr(core_config, 'VAULT_BACKEND', request.param, raising=False)
    harness = VaultHarness(storage, monkeypatch)
    harness.backend = request.param
    return harness
