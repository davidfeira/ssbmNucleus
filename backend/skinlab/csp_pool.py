"""CspRenderPool -- a pool of persistent HSDRawViewer `--csp-server` workers.

Bulk CSP generation otherwise spawns a fresh `HSDRawViewer.exe --csp` process
per costume; ~4s of every ~6s is fixed process + OpenGL startup, paid every time.
Each worker here keeps ONE process + GL context alive and renders costume after
costume off a shared queue, so that startup is paid once per worker instead of
once per costume (measured ~0.2s/job vs ~3.6s one-shot).

Crash-safe by design: a job that errors, times out, or a worker that dies makes
`render()` return False so the caller falls back to a one-shot `generate_csp`
(a single bad DAT never blocks the batch). Dead workers respawn on next use, and
every worker is recycled after N jobs to bound GPU/memory creep.

Protocol (see HSDRawViewer Program.cs RunCspServer): a worker prints "READY",
then per job we write a TAB-joined argv line ("--csp\t<dat>\t<output>\t...") and
read until "DONE\t<output>" / "ERR..." / "FATAL...".
"""
import contextlib
import logging
import os
import queue
import subprocess
import threading
import time

from skinlab.csp_concurrency import csp_workers, staggered_launch

_CREATE_NO_WINDOW = 0x08000000
_READY_TIMEOUT = 60.0
_DEFAULT_JOB_TIMEOUT = 90.0


class _Worker:
    def __init__(self, exe, idx):
        self.exe = str(exe)
        self.idx = idx
        self.proc = None
        self.jobs = 0
        self._spawn()

    def _spawn(self):
        flags = _CREATE_NO_WINDOW if os.name == "nt" else 0
        self.proc = subprocess.Popen(
            [self.exe, "--csp-server"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            text=True, bufsize=1, creationflags=flags,
        )
        deadline = time.time() + _READY_TIMEOUT
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError(f"csp worker {self.idx} exited during startup")
            if line.strip() == "READY":
                return
        raise RuntimeError(f"csp worker {self.idx} did not become READY in time")

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def render(self, job_args, timeout):
        """job_args = the argv `--csp` takes (['--csp', dat, output, ...]).
        Returns True on DONE, False on ERR/FATAL/timeout/dead worker."""
        if not self.alive():
            self._spawn()
        try:
            self.proc.stdin.write("\t".join(job_args) + "\n")
            self.proc.stdin.flush()
        except Exception:
            return False
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                return False  # worker died mid-job
            line = line.rstrip("\n")
            if line.startswith("DONE\t"):
                self.jobs += 1
                return True
            if line.startswith("ERR") or line.startswith("FATAL"):
                self.jobs += 1
                return False
            # ignore any stray line the worker might emit
        return False  # timed out

    def recycle(self):
        self.close()
        self.jobs = 0
        self._spawn()

    def close(self):
        try:
            if self.alive():
                self.proc.stdin.write("QUIT\n")
                self.proc.stdin.flush()
                self.proc.wait(timeout=3)
        except Exception:
            pass
        try:
            if self.alive():
                self.proc.kill()
        except Exception:
            pass


class CspRenderPool:
    def __init__(self, exe, workers=None, recycle_after=50,
                 job_timeout=_DEFAULT_JOB_TIMEOUT):
        self.exe = str(exe)
        self.recycle_after = recycle_after
        self.job_timeout = job_timeout
        n = workers or csp_workers()
        self._idle = queue.Queue()
        self._all = []
        for i in range(n):
            # Stagger worker startup so their GL-inits don't race (the same
            # blank/T-pose race the one-shot launch stagger guards). Only n
            # launches now, not one per costume.
            with staggered_launch():
                try:
                    w = _Worker(self.exe, i)
                except Exception:
                    continue
            self._all.append(w)
            self._idle.put(w)
        if not self._all:
            raise RuntimeError("CspRenderPool: no workers could start")

    @property
    def size(self):
        return len(self._all)

    def render(self, job_args) -> bool:
        """Render one costume. job_args is the argv `--csp` takes:
        ['--csp', <dat>, <output>, ...flags...]. Blocks until a worker is free
        (natural backpressure at `size` concurrent renders). Returns True only
        on a confirmed DONE; on any failure the caller should fall back."""
        w = self._idle.get()
        try:
            ok = w.render(list(job_args), self.job_timeout)
            if (not w.alive()) or w.jobs >= self.recycle_after:
                try:
                    w.recycle()
                except Exception:
                    pass
            return ok
        finally:
            self._idle.put(w)

    def close(self):
        for w in self._all:
            w.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


@contextlib.contextmanager
def active_pool(workers=None, enabled=None):
    """Stand up a CspRenderPool and install it as generate_csp's active pool for
    the duration of the block, so every costume rendered inside routes through a
    reused --csp-server worker instead of a one-shot process. Yields the pool (or
    None when disabled / unavailable -- callers then transparently get the
    one-shot path). Kill switch: MEX_CSP_SERVER=0.

    Wrap BATCH render loops in this (iso scan, texture-pack export, vanilla HD
    preseed). Do NOT wrap single-costume renders (Retake CSP, one pose, an install
    endpoint): the pool's one-time worker startup costs far more than one render.

    Pool workers are created BEFORE the pool is installed, so their launch still
    gets the csp_concurrency stagger; once installed, per-render staggers no-op.
    """
    # Lazy import: generate_csp pulls in the heavy HSDRaw stack, and it's on the
    # path in every backend caller of this module.
    import generate_csp

    if enabled is None:
        enabled = os.environ.get("MEX_CSP_SERVER", "1") != "0"

    pool = None
    if enabled:
        try:
            pool = CspRenderPool(generate_csp.HSDRAW_EXE, workers=workers)
            generate_csp.set_active_pool(pool)
        except Exception as e:
            logging.getLogger(__name__).warning(
                f"CSP render pool unavailable ({e}); using one-shot renders")
            pool = None
    try:
        yield pool
    finally:
        if pool is not None:
            try:
                generate_csp.set_active_pool(None)
            except Exception:
                pass
            pool.close()
