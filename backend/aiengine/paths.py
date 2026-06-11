"""On-disk layout for the AI engine.

Everything writable lives under PROJECT_ROOT (which is %LOCALAPPDATA%\\SSBM
Nucleus when packaged), mirroring how the rest of the backend handles user
data. Model weights default to the STANDARD HuggingFace cache so an existing
cache (assetFarm, other HF apps) is reused with zero migration; an override
lives in storage/ai_studio.json ('hfCacheDir').
"""
import os
import sys
from pathlib import Path

from core.config import BACKEND_DIR, PROJECT_ROOT, STORAGE_PATH

ENGINE_ROOT = PROJECT_ROOT / 'aiengine'
RUNTIME_DIR = ENGINE_ROOT / 'python'          # managed CPython lands here
INSTALL_STATE = ENGINE_ROOT / 'install_state.json'

CONFIG_PATH = STORAGE_PATH / 'ai_studio.json'
RUNS_LEDGER = STORAGE_PATH / 'ai_runs.jsonl'

ENGINE_REQUIREMENTS = Path(__file__).parent / 'engine_requirements.txt'

if os.name == 'nt':
    RUNTIME_PYTHON = RUNTIME_DIR / 'python.exe'
else:
    RUNTIME_PYTHON = RUNTIME_DIR / 'bin' / 'python3'

# The worker script is EXECUTED by an external interpreter, not imported, so
# in a frozen build it must ship as a data file (see the PyInstaller spec).
if getattr(sys, 'frozen', False):
    WORKER_SCRIPT = Path(sys._MEIPASS) / 'aiengine' / 'generate_worker.py'
else:
    WORKER_SCRIPT = BACKEND_DIR / 'aiengine' / 'worker' / 'generate_worker.py'


def engine_python():
    """The interpreter that runs the worker: NUCLEUS_AIENGINE_PYTHON when set
    (dev escape hatch — e.g. an existing torch venv), else the managed
    runtime. Returns a Path; existence is the caller's problem."""
    override = os.environ.get('NUCLEUS_AIENGINE_PYTHON', '').strip()
    if override:
        return Path(override)
    return RUNTIME_PYTHON


def engine_available():
    """True when something can run the worker (managed runtime installed or
    a dev interpreter override that exists)."""
    return engine_python().exists()


def hf_cache_env():
    """Extra environment for subprocesses that touch the HF cache. Empty when
    the standard cache is used (the default — reuses any existing cache)."""
    from aiengine.settings_store import load_settings
    cache_dir = load_settings().get('hfCacheDir')
    if cache_dir:
        return {'HF_HOME': str(Path(cache_dir))}
    return {}


def hf_cache_dir():
    """The directory model weights live in (for disk-usage display)."""
    from aiengine.settings_store import load_settings
    cache_dir = load_settings().get('hfCacheDir')
    if cache_dir:
        return Path(cache_dir) / 'hub'
    return Path(os.environ.get('HF_HOME', str(Path.home() / '.cache' / 'huggingface'))) / 'hub'
