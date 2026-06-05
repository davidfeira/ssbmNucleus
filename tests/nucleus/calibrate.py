"""
calibrate.py -- build the character -> cursor-coordinate map (grid.json).

Hovers each character once with the reliable timing selector (pipe.js char) and
records the cursor's resting coordinate read from RAM. Runtime selection then
uses closed-loop move_to against these coordinates, so positioning is robust to
cursor acceleration / frame timing. Re-run after a mod changes the CSS grid.

Run while on the character select screen (port 1 active, cursor unlocked).
"""

import json
import os
import subprocess
import time

from melee_mem import Dolphin
from melee_pipe import Pipe
from melee_css import Cursor

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE_JS = os.path.join(HERE, "..", "dolphin", "pipe.js")
GRID_PATH = os.path.join(HERE, "grid.json")

# One canonical name per cell. Aliases (sheik=zelda cell, etc.) resolve in select.
ROSTER = [
    "drmario", "mario", "luigi", "bowser", "peach", "yoshi", "dk", "falcon", "ganondorf",
    "falco", "fox", "ness", "iceclimbers", "kirby", "samus", "zelda", "link", "younglink",
    "pichu", "pikachu", "jigglypuff", "mewtwo", "gameandwatch", "marth", "roy",
]


def hover(name):
    subprocess.run(["node", PIPE_JS, "char", name, "--hover"],
                   cwd=HERE, capture_output=True, shell=True)
    time.sleep(0.35)


def stable_pos(c, tries=14):
    """Wait for the cursor to settle: two consecutive in-range reads that agree.
    Filters mid-animation transients and out-of-range garbage."""
    last = None
    for _ in range(tries):
        x, y = c.pos()
        if x is not None and abs(x) < 38 and abs(y) < 34:
            if last and abs(x - last[0]) < 0.4 and abs(y - last[1]) < 0.4:
                return (round((x + last[0]) / 2, 2), round((y + last[1]) / 2, 2))
            last = (x, y)
        time.sleep(0.12)
    return last


def main():
    d = Dolphin()
    p = Pipe()
    c = Cursor(d, p)
    # Unlock in case a character is locked in from a previous run (B once).
    p.neutral(); time.sleep(0.2)
    p.tap("B"); time.sleep(0.4)

    grid = {}
    for nm in ROSTER:
        pos = None
        for attempt in range(2):
            hover(nm)
            pos = stable_pos(c)
            if pos is not None:
                break
            print(f"{nm}: unstable read, retrying")
        if pos is None:
            print(f"{nm}: <no stable read>")
            continue
        grid[nm] = list(pos)
        print(f"{nm:14s} ({pos[0]:+6.1f},{pos[1]:+6.1f})")

    with open(GRID_PATH, "w", encoding="utf-8") as f:
        json.dump(grid, f, indent=2)
    print(f"\nwrote {len(grid)} cells -> {GRID_PATH}")


if __name__ == "__main__":
    main()
