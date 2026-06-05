"""
melee_pipe.py -- send controller input to Slippi Dolphin's named pipe from
Python, for closed-loop (memory-feedback) control.

Same per-frame model as ../dolphin/pipe.js: Dolphin reads one FLUSH batch per
pipe connection then closes it, and HOLDS the last input until the next batch.
So each call opens a fresh connection, writes its lines + FLUSH, and closes;
a held tilt/press persists until you send a new value (e.g. recenter/release).
That hold-until-next is what makes closed-loop work: tilt toward a target, poll
the target's position from RAM, then recenter when it arrives.

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

    def frame(self, lines):
        """One input frame: fresh connection, write all lines + close."""
        h = win32file.CreateFile(
            self.path, win32file.GENERIC_WRITE, 0, None,
            win32file.OPEN_EXISTING, 0, None,
        )
        try:
            win32file.WriteFile(h, ("\n".join(lines) + "\n").encode("ascii"))
        finally:
            win32file.CloseHandle(h)

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
