"""
Launcher for the Nucleus dev backend, used by the test harness.

mex_api.py calls socketio.run(debug=True) without allow_unsafe_werkzeug, and
flask-socketio aborts the dev server when stdin is not a TTY (its production
guard, flask_socketio/__init__.py:638). When the backend is spawned by a
non-interactive parent (Node child_process), stdin is a pipe, not a TTY, so the
guard fires. We present a fake-TTY stdin to satisfy it, then run the real
mex_api.py unchanged as __main__. use_reloader is False, so this only lets the
existing dev server bind -- no behaviour change, no edits to app code.
"""

import os
import sys
import runpy

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(HERE, "..", "..", "backend"))
# mex_api.py is normally run as `python backend/mex_api.py`, which puts
# backend/ on sys.path[0]; replicate that so its `from core...`/`from
# blueprints...` imports resolve.
sys.path.insert(0, BACKEND_DIR)


class _FakeTty:
    """Minimal stand-in so sys.stdin.isatty() returns True."""

    def isatty(self):
        return True

    def fileno(self):
        return 0

    def readline(self, *_):
        return ""


sys.stdin = _FakeTty()

runpy.run_path(os.path.join(BACKEND_DIR, "mex_api.py"), run_name="__main__")
