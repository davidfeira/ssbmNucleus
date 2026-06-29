"""
melee_pipe.py -- send controller input to Slippi Dolphin's named pipe from
Python, for closed-loop (memory-feedback) control.

Holds ONE persistent connection open (libmelee's model). Dolphin reads every
FLUSH batch from a live connection and HOLDS the last input until the next, so
a held tilt/press persists until you change it. This is essential for
closed-loop control: a fresh connection per frame churns connect/close and
desyncs Dolphin's controller -- inputs stop registering. A single open
connection avoids that.

Ported from tests/nucleus/melee_pipe.py, but the original used pywin32
(win32file) for the pipe handle. To ship inside the packaged backend with NO
extra installs, this version opens/writes/closes the named pipe with raw
kernel32 via ctypes (CreateFileW / WriteFile / CloseHandle) -- the same surface
melee_mem.py already uses. No pywin32, no other dependencies.

Buttons: A B X Y Z L R START D_UP D_DOWN D_LEFT D_RIGHT. Sticks 0.0-1.0, 0.5
center; control stick y=0.0 DOWN, y=1.0 UP (libmelee's convention -- verified
in-match: y=1.0 + B is an UP-B), x=0.0 LEFT, x=1.0 RIGHT. The closed-loop
cursor code (melee_css/melee_sss) is unaffected by the labels -- it steers by
feedback -- but open-loop in-match inputs MUST use this mapping.
"""

import ctypes
import ctypes.wintypes as wt
import time

BUTTONS = ["A", "B", "X", "Y", "Z", "L", "R", "START",
           "D_UP", "D_DOWN", "D_LEFT", "D_RIGHT"]

GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

# CreateFile error codes seen while Slippi Dolphin is (re-)arming the pipe.
ERROR_FILE_NOT_FOUND = 2     # the pipe isn't present this instant (being recreated)
ERROR_PIPE_BUSY = 231        # the pipe exists but every instance is busy

_k32 = ctypes.WinDLL("kernel32", use_last_error=True)
_k32.CreateFileW.restype = wt.HANDLE
_k32.CreateFileW.argtypes = [
    wt.LPCWSTR, wt.DWORD, wt.DWORD, wt.LPVOID, wt.DWORD, wt.DWORD, wt.HANDLE,
]
_k32.WriteFile.restype = wt.BOOL
_k32.WriteFile.argtypes = [
    wt.HANDLE, wt.LPCVOID, wt.DWORD, ctypes.POINTER(wt.DWORD), wt.LPVOID,
]
_k32.CloseHandle.restype = wt.BOOL
_k32.CloseHandle.argtypes = [wt.HANDLE]
_k32.WaitNamedPipeW.restype = wt.BOOL
_k32.WaitNamedPipeW.argtypes = [wt.LPCWSTR, wt.DWORD]


def pipe_open(port=1):
    """Try to open the slippibot<port> pipe for writing ONCE (non-blocking).
    Returns a handle, or None if the pipe doesn't exist this instant (Dolphin's
    input plugin not up, or mid re-arm). Used by the boot code to probe
    pipe-readiness / pick a free pipe index without creating a Pipe object. To
    actually open a pipe for driving, prefer pipe_open_wait (it rides over the
    transient gaps)."""
    path = rf"\\.\pipe\slippibot{port}"
    h = _k32.CreateFileW(path, GENERIC_WRITE, 0, None, OPEN_EXISTING, 0, None)
    if not h or h == INVALID_HANDLE_VALUE:
        return None
    return h


def pipe_open_wait(port=1, timeout=12.0, alive=None, poll=0.12):
    r"""Open \\.\pipe\slippibot<port> for writing, RETRYING across the brief
    windows where the pipe is momentarily unavailable.

    Slippi Dolphin tears the named pipe down and re-arms it whenever it refreshes
    controllers -- notably around game boot and stage load. A single-shot
    CreateFile that happens to land in that window fails with
    ERROR_FILE_NOT_FOUND(2) (pipe not present) or ERROR_PIPE_BUSY(231) (all
    instances busy) even though Dolphin is perfectly healthy -- which is why a
    screenshot/test would intermittently die with "CreateFile(...slippibot1)
    failed: 2". We instead retry with a short backoff until the pipe opens,
    `timeout` seconds elapse, or `alive()` (if given) reports Dolphin has exited.
    Returns a handle, or None on timeout / dead Dolphin."""
    path = rf"\\.\pipe\slippibot{port}"
    deadline = time.time() + timeout
    while True:
        h = _k32.CreateFileW(path, GENERIC_WRITE, 0, None, OPEN_EXISTING, 0, None)
        if h and h != INVALID_HANDLE_VALUE:
            return h
        err = ctypes.get_last_error()
        if alive is not None and not alive():
            return None                      # Dolphin died -- stop waiting
        if time.time() >= deadline:
            return None
        if err == ERROR_PIPE_BUSY:
            _k32.WaitNamedPipeW(path, 500)   # block (<=0.5s) for a free instance
        else:
            time.sleep(poll)                 # not up yet -- brief backoff, retry


def pipe_in_use(port):
    """True if a slippibot<port> pipe currently exists (another Dolphin owns
    it). Used to pick a pipe index that won't collide with the user's own
    running Slippi."""
    h = pipe_open(port)
    if h is None:
        return False
    _k32.CloseHandle(h)
    return True


class Pipe:
    def __init__(self, port=1, open_timeout=12.0, alive=None):
        """open_timeout: seconds to keep retrying the initial open across
        Dolphin's pipe re-arm windows (see pipe_open_wait). alive: optional
        callable -> bool; when it returns False the open/reconnect bails
        immediately instead of waiting out the timeout on a dead Dolphin."""
        self.port = port
        self.path = rf"\\.\pipe\slippibot{port}"
        self._open_timeout = open_timeout
        self._alive = alive
        self._h = None
        self._open()

    def _open(self, timeout=None):
        t = self._open_timeout if timeout is None else timeout
        h = pipe_open_wait(self.port, timeout=t, alive=self._alive)
        if h is None:
            raise OSError(f"CreateFile({self.path}) failed: {ctypes.get_last_error()}")
        self._h = h

    def _write(self, data):
        written = wt.DWORD(0)
        buf = ctypes.create_string_buffer(data, len(data))
        ok = _k32.WriteFile(self._h, buf, len(data), ctypes.byref(written), None)
        return bool(ok)

    def frame(self, lines):
        """Write one input frame to the persistent connection (reconnect if the
        handle has gone stale, e.g. Dolphin re-armed the pipe on a controller
        refresh). The reconnect retries briefly so a re-arm mid-run doesn't drop
        the frame, but stays bounded so a genuinely dead Dolphin fails fast."""
        data = ("\n".join(lines) + "\n").encode("ascii")
        try:
            if not self._write(data):
                raise OSError("WriteFile failed")
        except Exception:
            self._open(timeout=3.0)
            self._write(data)

    def close(self):
        if self._h is not None:
            try:
                _k32.CloseHandle(self._h)
            except Exception:
                pass
            self._h = None

    # --- buttons -------------------------------------------------------------
    def press(self, btn):
        self.frame([f"PRESS {btn}", "FLUSH"])

    def release(self, btn):
        self.frame([f"RELEASE {btn}", "FLUSH"])

    def tap(self, btn, hold=0.05):
        self.press(btn)
        time.sleep(hold)
        self.release(btn)

    # --- sticks --------------------------------------------------------------
    def main(self, x, y):
        self.frame([f"SET MAIN {x:.3f} {y:.3f}", "FLUSH"])

    def c(self, x, y):
        self.frame([f"SET C {x:.3f} {y:.3f}", "FLUSH"])

    def center(self):
        self.frame(["SET MAIN 0.5 0.5", "FLUSH"])

    def tilt(self, x, y, hold):
        """Tilt the control stick, hold, then re-center."""
        self.main(x, y)
        time.sleep(hold)
        self.center()

    def neutral(self):
        lines = [f"RELEASE {b}" for b in BUTTONS]
        lines += ["SET MAIN 0.5 0.5", "SET C 0.5 0.5", "SET L 0", "SET R 0", "FLUSH"]
        self.frame(lines)
