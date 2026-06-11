"""Managed-runtime installer: a private CPython + torch + diffusers under
PROJECT_ROOT/aiengine, so local generation needs no dev tooling on the
user's machine.

Phases (each persisted to install_state.json so a refresh/restart can show
partial or failed installs, and re-running resumes — completed phases are
skipped):
  python  download python-build-standalone (~35MB) and extract
  torch   pip install torch from the cuda/cpu wheel index (~2.5GB cuda)
  deps    pip install -r engine_requirements.txt
  verify  run the worker's --check probe

Progress streams over SocketIO: aiengine_install_progress {phase, message,
percentage?}, then aiengine_install_complete {check} / aiengine_install_error
{phase, error}. One install at a time (module lock).
"""
import json
import logging
import os
import subprocess
import tarfile
import threading
import time

import requests

from core.config import get_subprocess_args

from aiengine.paths import (ENGINE_REQUIREMENTS, ENGINE_ROOT, INSTALL_STATE,
                            RUNTIME_DIR, RUNTIME_PYTHON)

logger = logging.getLogger(__name__)

# install_only archives extract to a top-level `python/` dir = RUNTIME_DIR.
# Override with NUCLEUS_AIENGINE_PYTHON_URL if this release ever 404s.
PYTHON_BUILD_URL = (
    'https://github.com/astral-sh/python-build-standalone/releases/download/'
    '20250409/cpython-3.12.10%2B20250409-x86_64-pc-windows-msvc-install_only.tar.gz')

# cu128+ required for Blackwell GPUs (RTX 50xx, sm_120) — cu124 torch has no
# kernels for them and dies at generation time with 'no kernel image'.
TORCH_INDEX = {
    'cuda': 'https://download.pytorch.org/whl/cu128',
    'cpu': 'https://download.pytorch.org/whl/cpu',
}
MIN_FREE_BYTES = 8 * 1024**3   # torch + deps need real room

_install_lock = threading.Lock()
_installing = False


def read_state():
    try:
        return json.loads(INSTALL_STATE.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {}


def _write_state(**updates):
    state = read_state()
    state.update(updates)
    INSTALL_STATE.parent.mkdir(parents=True, exist_ok=True)
    INSTALL_STATE.write_text(json.dumps(state, indent=2), encoding='utf-8')
    return state


def is_installed():
    return RUNTIME_PYTHON.exists() and read_state().get('finishedAt') is not None


def is_installing():
    return _installing


def _download_python(emit):
    if RUNTIME_PYTHON.exists():
        emit('python', 'runtime already present', 100)
        return
    url = os.environ.get('NUCLEUS_AIENGINE_PYTHON_URL', PYTHON_BUILD_URL)
    archive = ENGINE_ROOT / 'python-runtime.tar.gz'
    ENGINE_ROOT.mkdir(parents=True, exist_ok=True)
    emit('python', 'downloading Python runtime…', 0)
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get('content-length') or 0)
        done = 0
        with archive.open('wb') as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                done += len(chunk)
                if total:
                    emit('python', f'downloading Python runtime… '
                         f'{done // (1 << 20)} / {total // (1 << 20)} MB',
                         int(100 * done / total))
    emit('python', 'extracting Python runtime…', 100)
    with tarfile.open(archive, 'r:gz') as tar:
        tar.extractall(ENGINE_ROOT)
    archive.unlink(missing_ok=True)
    if not RUNTIME_PYTHON.exists():
        raise RuntimeError(f'extraction produced no {RUNTIME_PYTHON}')


def _pip(args, phase, emit, timeout=3600):
    cmd = [str(RUNTIME_PYTHON), '-m', 'pip'] + args + \
          ['--no-warn-script-location', '--disable-pip-version-check']
    logger.info(f'[ai-engine] {phase}: {" ".join(cmd)}')
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True,
                            encoding='utf-8', errors='replace',
                            **get_subprocess_args())
    deadline = time.time() + timeout
    tail = []
    for line in proc.stdout:
        if time.time() > deadline:
            proc.kill()
            raise RuntimeError(f'{phase} timed out')
        line = line.strip()
        if not line:
            continue
        tail.append(line)
        tail[:] = tail[-30:]
        # pip has no clean global %; relay the interesting lines as messages
        if line.startswith(('Collecting', 'Downloading', 'Installing',
                            'Successfully')):
            emit(phase, line[:160], None)
    proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f'pip failed ({phase}): ' + ' | '.join(tail[-5:]))


def start_install(socketio, variant=None):
    """Kick off the install in a daemon thread. Returns (started, error)."""
    global _installing
    with _install_lock:
        if _installing:
            return False, 'an install is already running'
        _installing = True

    from aiengine import hardware
    hw = hardware.detect(force=True)
    if not variant:
        variant = 'cuda' if hw.get('gpu') else 'cpu'
    if hw.get('diskFreeBytes', 0) < MIN_FREE_BYTES:
        with _install_lock:
            _installing = False
        return False, ('not enough free disk space for the engine '
                       f'(need ~{MIN_FREE_BYTES // 1024**3}GB)')

    def emit(phase, message, percentage):
        socketio.emit('aiengine_install_progress',
                      {'phase': phase, 'message': message,
                       'percentage': percentage})

    def run():
        global _installing
        state = read_state()
        try:
            _write_state(torchVariant=variant, error=None, finishedAt=None)

            _download_python(emit)
            _write_state(phase='python')

            # reinstall torch when the phase never completed, the variant
            # changed, OR the wheel index changed (e.g. cu124 -> cu128)
            if state.get('phase') not in ('torch', 'deps', 'verify') \
                    or state.get('torchVariant') != variant \
                    or state.get('torchIndex') != TORCH_INDEX[variant]:
                emit('torch', f'installing torch ({variant})… '
                     'this is a ~2.5GB download', None)
                _pip(['install', '--upgrade', 'torch',
                      '--index-url', TORCH_INDEX[variant]], 'torch', emit)
            _write_state(phase='torch', torchIndex=TORCH_INDEX[variant])

            emit('deps', 'installing diffusers and friends…', None)
            _pip(['install', '-r', str(ENGINE_REQUIREMENTS)], 'deps', emit)
            _write_state(phase='deps')

            emit('verify', 'verifying the engine…', None)
            from aiengine import runner
            report = runner.check(force=True)
            if not report or not report.get('ok'):
                raise RuntimeError('verification failed: '
                                   + str((report or {}).get('error') or report))
            _write_state(phase='verify', check=report,
                         finishedAt=round(time.time(), 1))
            socketio.emit('aiengine_install_complete', {'check': report})
        except Exception as e:
            logger.error(f'[ai-engine] install failed: {e}', exc_info=True)
            _write_state(error=str(e))
            socketio.emit('aiengine_install_error',
                          {'phase': read_state().get('phase'), 'error': str(e)})
        finally:
            with _install_lock:
                _installing = False

    threading.Thread(target=run, daemon=True).start()
    return True, None
