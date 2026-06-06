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
center; control stick y=0.0 UP, y=1.0 DOWN, x=0.0 LEFT, x=1.0 RIGHT.
"""

import ctypes
import ctypes.wintypes as wt
import time

BUTTONS = ["A", "B", "X", "Y", "Z", "L", "R", "START",
           "D_UP", "D_DOWN", "D_LEFT", "D_RIGHT"]

GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

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


def pipe_open(port=1):
    """Try to open the slippibot<port> pipe for writing. Returns a handle, or
    None if the pipe doesn't exist yet (Dolphin's input plugin not up). Used
    both by Pipe and by the boot code to probe pipe-readiness / pick a free
    pipe index without creating a Pipe object."""
    path = rf"\\.\pipe\slippibot{port}"
    h = _k32.CreateFileW(path, GENERIC_WRITE, 0, None, OPEN_EXISTING, 0, None)
    if not h or h == INVALID_HANDLE_VALUE:
        return None
    return h


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
    def __init__(self, port=1):
        self.port = port
        self.path = rf"\\.\pipe\slippibot{port}"
        self._h = None
        self._open()

    def _open(self):
        h = pipe_open(self.port)
        if h is None:
            raise OSError(f"CreateFile({self.path}) failed: {ctypes.get_last_error()}")
        self._h = h

    def _write(self, data):
        written = wt.DWORD(0)
        buf = ctypes.create_string_buffer(data, len(data))
        ok = _k32.WriteFile(self._h, buf, len(data), ctypes.byref(written), None)
        return bool(ok)

    def frame(self, lines):
        """Write one input frame to the persistent connection (reconnect once
        if the handle has gone stale, e.g. Dolphin restarted)."""
        data = ("\n".join(lines) + "\n").encode("ascii")
        try:
            if not self._write(data):
                raise OSError("WriteFile failed")
        except Exception:
            self._open()
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
