"""GPU + disk detection for spec recommendations.

nvidia-smi is the source of truth for the GPU (name + total VRAM); any
failure — no NVIDIA driver, no GPU, timeout — degrades to gpu=None and the
UI steers the user toward API models. Results are cached briefly: the
settings hub polls this alongside model statuses.
"""
import shutil
import subprocess
import time

from core.config import get_subprocess_args

_cache = {'at': 0.0, 'value': None}
_CACHE_SECONDS = 60


def _query_gpu():
    try:
        proc = subprocess.run(
            ['nvidia-smi', '--query-gpu=name,memory.total',
             '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5, **get_subprocess_args())
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    line = (proc.stdout or '').strip().splitlines()
    if not line:
        return None
    # first GPU only: "NVIDIA GeForce RTX 3080, 10240"
    parts = line[0].rsplit(',', 1)
    if len(parts) != 2:
        return None
    try:
        return {'name': parts[0].strip(), 'vramMb': int(float(parts[1].strip()))}
    except ValueError:
        return None


def detect(force=False):
    """{'gpu': {'name', 'vramMb'} | None, 'diskFreeBytes': int}"""
    now = time.time()
    if not force and _cache['value'] and now - _cache['at'] < _CACHE_SECONDS:
        return _cache['value']

    from aiengine.paths import hf_cache_dir
    cache_dir = hf_cache_dir()
    probe = cache_dir
    while not probe.exists() and probe.parent != probe:
        probe = probe.parent
    try:
        disk_free = shutil.disk_usage(probe).free
    except OSError:
        disk_free = 0

    value = {'gpu': _query_gpu(), 'diskFreeBytes': disk_free}
    _cache.update(at=now, value=value)
    return value


def model_fit(spec, hw=None):
    """How a local model suits the detected hardware:
    'good' | 'slow' | 'insufficient_vram' | 'no_gpu'. API models are 'good'."""
    if spec.kind == 'api':
        return 'good'
    hw = hw or detect()
    gpu = hw.get('gpu')
    if not gpu:
        return 'no_gpu'
    vram_gb = gpu['vramMb'] / 1024
    if spec.vram_estimate_gb > vram_gb * 1.05:
        return 'insufficient_vram'
    if spec.vram_estimate_gb > vram_gb * 0.8:
        return 'slow'
    return 'good'
