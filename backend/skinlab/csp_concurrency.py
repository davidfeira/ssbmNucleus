"""Shared CSP-render concurrency policy.

How many parallel HSDRawViewer renders a given machine should run, and a
staggered-launch guard so those renders don't race HSDRawViewer's ~1.5s init
window (the blank / T-pose bug seen when several instances spin up at once).

This mirrors the policy the ISO scanner uses (see iso_scanner.py) so the
texture-pack export and the HD-CSP cache can share it without importing the
heavy scanner module. Tunable via the same env vars the scanner honors.
"""
import os
import time
import threading
from contextlib import contextmanager


def csp_workers() -> int:
    """Optimal number of parallel CSP renders for THIS machine.

    Detected from the machine's logical CPU count (HSDRawViewer renders are
    mostly GPU/CPU-swap bound, so threads scale well), clamped to [1, 16] to
    bound RAM on large boxes. Override with the MEX_CSP_PARALLELISM env var
    (clamped [1, 32]) for tuning. NOT a hardcoded worker count.
    """
    env = os.environ.get('MEX_CSP_PARALLELISM')
    if env and env.isdigit():
        return max(1, min(int(env), 32))
    return max(1, min(os.cpu_count() or 2, 16))


# Spacing between HSDRawViewer launches. 1.5s matches Program.cs's combined
# init Sleep budget; raise if you still see flaky renders, set 0 to disable.
CSP_LAUNCH_STAGGER_S = float(os.environ.get('MEX_CSP_LAUNCH_STAGGER', '1.5'))
_launch_lock = threading.Lock()


@contextmanager
def staggered_launch():
    """Serialize only the LAUNCH of each render so each HSDRawViewer gets a
    clean init window before the next starts; then release so renders overlap.

    Hold the lock for the stagger, release, then yield to run the actual render
    in parallel with others. A single, uncontended caller just pays the stagger
    once. Used by the HD-CSP cache so the texture-pack export can render in
    parallel safely (the lock is shared across all callers in this process).
    """
    if CSP_LAUNCH_STAGGER_S > 0:
        with _launch_lock:
            time.sleep(CSP_LAUNCH_STAGGER_S)
    yield
