"""
cl_das.py -- single-session DAS (Dynamic Alternate Stages) crash-test loop.

A DAS ISO holds many stage skins: each legal stage can carry several alternates,
each behind a different HOLD button (X/Y/Z/L -- not A/B/R, which select/back/
flip-page). This boots ONCE, locks a fighter, and tests EVERY (stage, button)
variant by: START -> stage select, steer to the stage while holding its button
(loads that alternate), watch it load+run, then quit back to the CSS with the
L+R+A+START combo (which returns to a still-"READY TO FIGHT" CSS) and do the
next -- so one build's worth of skins is tested with no relaunch between them.

    python cl_das.py '<variants-json>'
      variants-json = [{"stage":"dreamland","button":"X","variant":"cotton candy"}, ...]

Assumes the CSS already has a port-2 CPU (pipe.js cpustep). Prints one PASS/FAIL
line per variant and a summary; exit 0 iff every variant loaded + ran.
"""

import json
import os
import subprocess
import sys
import time

from melee_mem import Dolphin
from melee_pipe import Pipe
from melee_css import Cursor
from melee_sss import StageCursor
from char_select import load_grid, cell, css_index

HERE = os.path.dirname(os.path.abspath(__file__))
CONTROL = os.path.join(HERE, "..", "dolphin", "control.js")
FRAME_COUNTER = 0x80479D60
SCENE_MINOR = 0x80479D33


def lock_fighter(cur, name="fox"):
    grid = load_grid()
    x, y = cell(grid, name)
    cur.select(x, y, costume=0, lock=False, css_index=css_index(name))
    cur.p.center()
    time.sleep(0.15)
    cur.p.tap("A", 0.08)
    time.sleep(0.35)


def health(d, seconds=7.0):
    """In-game health: the frame counter must keep advancing while the scene
    stays in-game (sub 0x2) and the process/RAM stay alive. Returns True if the
    variant loaded and ran without a crash/hang/early-exit."""
    start = time.time()
    last = d.u32(FRAME_COUNTER)
    stuck = 0.0
    while time.time() - start < seconds:
        time.sleep(0.4)
        if not d.alive() or d.locate() is False:
            return False
        if d.u8(SCENE_MINOR) != 0x02:          # left in-game early (soft crash)
            return False
        f = d.u32(FRAME_COUNTER)
        if f is None or f == last:
            stuck += 0.4
            if stuck > 2.0:                     # frozen > 2s -> hung
                return False
        else:
            stuck = 0.0
            last = f
    return True


def reset_to_css(p):
    """Quit the running match back to the CSS: pause with START, then press
    L+R+A+START together (Melee's quit-to-CSS), which lands on a still-ready
    CSS (the fighter stays locked)."""
    p.tap("START", 0.08)
    time.sleep(0.7)
    p.frame(["PRESS L", "PRESS R", "PRESS A", "PRESS START", "FLUSH"])
    time.sleep(0.8)
    p.frame(["RELEASE L", "RELEASE R", "RELEASE A", "RELEASE START", "FLUSH"])
    time.sleep(1.3)


def screenshot(label):
    try:
        subprocess.run(["node", CONTROL, "shot", "--label", label],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=30)
    except Exception:
        pass


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    variants = json.loads(sys.argv[1])
    if not variants:
        print("no variants")
        return 2

    d = Dolphin()
    p = Pipe()
    cur = Cursor(d, p)
    sc = StageCursor(d, p)
    p.neutral()
    time.sleep(0.4)

    lock_fighter(cur, "fox")
    results = []
    for i, v in enumerate(variants):
        stage, button, name = v["stage"], v["button"], v.get("variant", "?")
        # From the ready CSS, select presses START -> stage select, steers to the
        # stage holding `button` (the DAS trigger), and starts the match. Prefer
        # the build's real SSS coordinate (accurate on any layout) over the
        # hardcoded vanilla target, which mis-hits non-bottom-row stages.
        if "x" in v and "y" in v:
            started = sc.select_at(v["x"], v["y"], page=v.get("page", 0),
                                   press=True, hold=button)
        else:
            started = sc.select(stage, press=True, hold=button)
        ok = bool(started) and health(d)
        screenshot(f"das-{stage}-{button}-{str(name).replace(' ', '-')[:16]}")
        results.append((stage, button, name, ok))
        print(f"  {'PASS' if ok else 'FAIL'}  {stage} hold {button} -> "
              f'"{name}" (started={started})')
        # Quit back to the CSS for the next variant (keep the fighter locked).
        reset_to_css(p)
        time.sleep(0.4)

    p.center()
    p.close()
    n_pass = sum(1 for *_, ok in results if ok)
    print(f"=== DAS: {n_pass}/{len(results)} variants loaded + ran ===")
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
