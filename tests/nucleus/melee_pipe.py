"""
melee_pipe.py -- send controller input to Slippi Dolphin's named pipe from
Python, for closed-loop (memory-feedback) control.

Holds ONE persistent connection open (libmelee's model). Dolphin reads every
FLUSH batch from a live connection and HOLDS the last input until the next, so
a held tilt/press persists until you change it. This is essential for
closed-loop control: a fresh connection per frame (the pipe.js model) churns
connect/close at ~30 Hz and desyncs Dolphin's controller -- inputs stop
registering (notably A no longer locks). A single open connection avoids that.

Buttons: A B X Y Z L R START D_UP D_DOWN D_LEFT D_RIGHT. Sticks 0.0-1.0, 0.5
center; control stick y=0.0 UP, y=1.0 DOWN, x=0.0 LEFT, x=1.0 RIGHT.
"""

import time
import win32file

BUTTONS = ["A", "B", "X", "Y", "Z", "L", "R", "START",
           "D_UP", "D_DOWN", "D_LEFT", "D_RIGHT"]


class Pipe:
    def __init__(self, port=1):
        self.path = rf"\\.\pipe\slippibot{port}"
        self._h = None
        self._open()

    def _open(self):
        self._h = win32file.CreateFile(
            self.path, win32file.GENERIC_WRITE, 0, None,
            win32file.OPEN_EXISTING, 0, None,
        )

    def frame(self, lines):
        """Write one input frame to the persistent connection (reconnect once
        if the handle has gone stale, e.g. Dolphin restarted)."""
        data = ("\n".join(lines) + "\n").encode("ascii")
        try:
            win32file.WriteFile(self._h, data)
        except Exception:
            self._open()
            win32file.WriteFile(self._h, data)

    def close(self):
        if self._h is not None:
            try:
                win32file.CloseHandle(self._h)
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
