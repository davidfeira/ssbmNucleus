"""Spawn the generate worker and speak its NDJSON protocol.

One job per process (cold model load each call — parity with the old
assetFarm bridge; the protocol permits a keep-warm loop later). Local
generations are serialized with a module lock: one GPU.
"""
import json
import logging
import os
import subprocess
import threading

from core.config import get_subprocess_args

from aiengine.paths import WORKER_SCRIPT, engine_python, hf_cache_env
from aiengine.registry import find

logger = logging.getLogger(__name__)

_gen_lock = threading.Lock()
_check_cache = {'python': None, 'report': None}


class EngineError(RuntimeError):
    pass


def _worker_env(offline=True):
    env = dict(os.environ)
    env.update(hf_cache_env())
    if offline:
        # weights must already be downloaded; fail fast instead of fetching
        env['HF_HUB_OFFLINE'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    return env


def check(force=False):
    """Run the worker's --check probe: {ok, torch, cuda, cudaDeviceName,
    diffusersVersion, pipelines} or None when no interpreter is available.
    Cached per interpreter path (a torch import costs seconds)."""
    python = engine_python()
    if not python.exists():
        return None
    key = str(python)
    if not force and _check_cache['python'] == key and _check_cache['report']:
        return _check_cache['report']
    try:
        proc = subprocess.run(
            [str(python), str(WORKER_SCRIPT), '--check'],
            capture_output=True, text=True, timeout=120,
            env=_worker_env(offline=False), **get_subprocess_args())
    except (OSError, subprocess.TimeoutExpired) as e:
        return {'ok': False, 'error': str(e)}
    report = None
    for line in reversed((proc.stdout or '').strip().splitlines()):
        try:
            report = json.loads(line)
            break
        except json.JSONDecodeError:
            continue
    if report is None:
        report = {'ok': False,
                  'error': (proc.stderr or proc.stdout or 'no output')[-500:]}
    _check_cache.update(python=key, report=report)
    return report


def generate(prompt, model_id, out_path, style=None, seed=None,
             width=None, height=None, on_progress=None, timeout=1800):
    """Generate an image with a local model. Returns (out_path, seconds).
    Raises EngineError with a readable message on any failure."""
    spec = find(model_id)
    if spec is None or spec.kind != 'local':
        raise EngineError(f'unknown local model: {model_id}')
    python = engine_python()
    if not python.exists():
        raise EngineError('local engine is not installed '
                          '(Settings → AI Studio → Install)')

    job = {
        'prompt': prompt,
        'style': style,
        'width': width,
        'height': height,
        'seed': seed,
        'out_path': str(out_path),
        'spec': {
            'repo_id': spec.repo_id,
            'pipeline_class': spec.pipeline_class,
            'dtype': spec.dtype,
            'num_inference_steps': spec.num_inference_steps,
            'guidance_scale': spec.guidance_scale,
        },
    }

    with _gen_lock:
        logger.info(f'[ai-engine] generate ({model_id}): {prompt!r}')
        proc = subprocess.Popen(
            [str(python), str(WORKER_SCRIPT)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding='utf-8',
            env=_worker_env(), **get_subprocess_args())

        def _kill_on_timeout():
            try:
                proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()

        watchdog = threading.Thread(target=_kill_on_timeout, daemon=True)
        watchdog.start()

        # Drain stderr concurrently: diffusers/HF write tqdm bars there, and
        # an undrained pipe fills its buffer and DEADLOCKS the worker.
        stderr_tail = []

        def _drain_stderr():
            for line in proc.stderr:
                stderr_tail.append(line.rstrip())
                del stderr_tail[:-30]

        threading.Thread(target=_drain_stderr, daemon=True).start()

        try:
            proc.stdin.write(json.dumps(job) + '\n')
            proc.stdin.close()
        except OSError as e:
            proc.kill()
            raise EngineError(f'could not start the generate worker: {e}')

        result = None
        for line in proc.stdout:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get('event') == 'progress' and on_progress:
                try:
                    on_progress(event.get('pct'), event.get('desc') or '')
                except Exception:
                    pass
            elif event.get('event') == 'result':
                result = event
        proc.wait()

    if result is None:
        stderr = ' | '.join(stderr_tail[-5:])
        raise EngineError('generate worker died without a result'
                          + (f': {stderr}' if stderr else ''))
    if not result.get('ok'):
        raise EngineError(f'generation failed: {result.get("error")}')
    return result['path'], result.get('seconds') or 0.0
