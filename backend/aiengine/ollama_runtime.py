"""Bundled portable Ollama — the last external install, made self-contained.

Resolution order for the local-LLM server:
  1. the user's OWN Ollama (NUCLEUS_OLLAMA_URL, default localhost:11434)
  2. the BUNDLED portable Ollama under PROJECT_ROOT/aiengine/ollama,
     spawned on demand as `ollama serve` on port 11435 (so it never fights
     a user install) and terminated when the backend exits.

Models pulled through either server land in the standard ~/.ollama store,
so bundled and user installs share downloads. Windows-only (Ollama ships a
portable zip only for win-amd64); elsewhere the user installs Ollama.
"""
import atexit
import logging
import os
import subprocess
import threading
import time
import zipfile

import requests

from core.config import get_subprocess_args

from aiengine.paths import ENGINE_ROOT

logger = logging.getLogger(__name__)

OLLAMA_DIR = ENGINE_ROOT / 'ollama'
OLLAMA_EXE = OLLAMA_DIR / 'ollama.exe'
BUNDLED_PORT = 11435
BUNDLED_URL = f'http://127.0.0.1:{BUNDLED_PORT}'
EXTERNAL_URL = os.environ.get('NUCLEUS_OLLAMA_URL', 'http://127.0.0.1:11434')

ZIP_URL = os.environ.get(
    'NUCLEUS_OLLAMA_ZIP_URL',
    'https://github.com/ollama/ollama/releases/latest/download/'
    'ollama-windows-amd64.zip')

_proc = None
_start_lock = threading.Lock()
_install_lock = threading.Lock()
_installing = False


def is_supported():
    return os.name == 'nt'


def bundled_installed():
    return OLLAMA_EXE.exists()


def is_installing():
    return _installing


def _reachable(url, timeout=2):
    try:
        requests.get(f'{url}/api/tags', timeout=timeout)
        return True
    except Exception:
        return False


def _start_bundled():
    global _proc
    with _start_lock:
        if _reachable(BUNDLED_URL, timeout=1):
            return BUNDLED_URL
        env = dict(os.environ)
        env['OLLAMA_HOST'] = f'127.0.0.1:{BUNDLED_PORT}'
        try:
            logger.info('[ai-engine] starting bundled ollama serve')
            _proc = subprocess.Popen(
                [str(OLLAMA_EXE), 'serve'], env=env,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                **get_subprocess_args())
        except OSError as e:
            logger.warning(f'[ai-engine] bundled ollama failed to start: {e}')
            return None
    for _ in range(40):
        if _reachable(BUNDLED_URL, timeout=1):
            return BUNDLED_URL
        time.sleep(0.5)
    logger.warning('[ai-engine] bundled ollama never became reachable')
    return None


@atexit.register
def _shutdown():
    if _proc is not None and _proc.poll() is None:
        try:
            _proc.terminate()
        except Exception:
            pass


def effective_url(start=True):
    """The URL of a reachable Ollama server: the user's own install first,
    then the bundled one (spawned on demand when `start`). None when
    neither is available."""
    if _reachable(EXTERNAL_URL):
        return EXTERNAL_URL
    if not bundled_installed():
        return None
    if _reachable(BUNDLED_URL, timeout=1):
        return BUNDLED_URL
    return _start_bundled() if start else None


def install_bundled(socketio):
    """Download + extract the portable Ollama zip (~1.2GB) in a daemon
    thread, streaming aiengine_ollama_progress / _complete / _error.
    Returns (started, error)."""
    global _installing
    if not is_supported():
        return False, 'bundled Ollama is Windows-only — install from ollama.com'
    with _install_lock:
        if _installing:
            return False, 'the Ollama install is already running'
        _installing = True

    def emit(message, percentage=None):
        socketio.emit('aiengine_ollama_progress',
                      {'message': message, 'percentage': percentage})

    def run():
        global _installing
        archive = ENGINE_ROOT / 'ollama-portable.zip'
        try:
            OLLAMA_DIR.mkdir(parents=True, exist_ok=True)
            emit('downloading portable Ollama…', 0)
            with requests.get(ZIP_URL, stream=True, timeout=120) as r:
                r.raise_for_status()
                total = int(r.headers.get('content-length') or 0)
                done = 0
                with archive.open('wb') as f:
                    for chunk in r.iter_content(chunk_size=1 << 20):
                        f.write(chunk)
                        done += len(chunk)
                        if total:
                            emit(f'downloading portable Ollama… '
                                 f'{done // (1 << 20)} / {total // (1 << 20)} MB',
                                 int(100 * done / total))
            emit('extracting…', 100)
            with zipfile.ZipFile(archive) as z:
                z.extractall(OLLAMA_DIR)
            archive.unlink(missing_ok=True)
            if not OLLAMA_EXE.exists():
                raise RuntimeError(f'extraction produced no {OLLAMA_EXE}')
            emit('starting the server…', None)
            if not _start_bundled():
                raise RuntimeError('installed, but the server did not start')
            socketio.emit('aiengine_ollama_complete', {})
        except Exception as e:
            logger.error(f'[ai-engine] ollama install failed: {e}', exc_info=True)
            archive.unlink(missing_ok=True)
            socketio.emit('aiengine_ollama_error', {'error': str(e)})
        finally:
            _installing = False

    threading.Thread(target=run, daemon=True).start()
    return True, None
