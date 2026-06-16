"""
cl_match.py -- one-process closed-loop match setup: lock the character, advance
to stage select, pick the stage. ALL on a single persistent pipe held open the
whole time, so there's no inter-process connection handoff -- which was racily
dropping the character lock (the lock flag needs ~0.4s to settle, and a second
process opening its own pipe read it before it had).

================================================================================
STOP if you are here to crash-test / move-test a fighter in-game. This path
drives the CSS cursor and ADDS A CPU (see pipe.js cpustep) to satisfy Melee's
2-player start gate. The CPU then attacks you and moves the camera, ruining
move/crash repros, and the cursor sweep is slow + per-build fragile.

Use the SOLO, no-CPU, no-cursor engine instead: backend/ingame/ (memory-loads
the match alone). Template: backend/fsm_crash_probe.py. Docs:
backend/ingame/README.md. This file is ONLY for testing the CSS/SSS UI itself.
================================================================================

Assumes the CSS already has a port-2 CPU (pipe.js cpustep) -- locking needs a
2nd player. Steers by memory feedback (no timing): character cell + costume via
melee_css.Cursor, stage via melee_sss.StageCursor.

    python cl_match.py <character> [costume] [stage]
    python cl_match.py <label> --icon <x>,<y>,<index> [stage]   # custom fighter

For a CUSTOM m-ex fighter (a new roster slot), pass its CSS icon coordinate +
grid index from the build manifest's `cssIcon` (the app's own grid placement):
the cursor target is (x, y - 3.5) and `index` is the in-game grid index to
confirm the hover -- so custom fighters are selected the same closed-loop way as
vanilla ones, without empirical calibration.

Exit 0 if the match started on the chosen character+stage, 1 otherwise.
"""

import sys
import time

from melee_mem import Dolphin
from melee_pipe import Pipe
from melee_css import Cursor
from melee_sss import StageCursor
import os
import subprocess

from char_select import load_grid, cell, css_index
from melee_sss import norm as norm_stage, STAGE_TARGET

CONTROL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dolphin", "control.js")


def perform_move(p, move, reps=6):
    """After a match starts, perform the in-game move that exercises an effect
    mod (so its model/data actually loads). Waits out the GO! countdown first.
    neutralb = the blaster (Fox/Falco gun/laser); sideb = the side special."""
    time.sleep(3.5)
    if move == "neutralb":
        for _ in range(reps):
            p.tap("B", 0.06)
            time.sleep(0.5)
    elif move == "sideb":
        for _ in range(reps):
            p.frame(["SET MAIN 1.000 0.500", "PRESS B", "FLUSH"])
            time.sleep(0.12)
            p.frame(["RELEASE B", "SET MAIN 0.500 0.500", "FLUSH"])
            time.sleep(0.6)
    p.center()


def screenshot(label):
    try:
        subprocess.run(["node", CONTROL, "shot", "--label", label],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    except Exception:
        pass


def lock_character(cur, name, costume):
    """Steer to the character cell + set the costume (lock=False), then press A
    EXACTLY ONCE to lock. A single, solid A press reliably drops the coin; the
    byte we used as a "locked" flag (0x804AA162) is actually noise, so don't
    gate on it -- and don't press A in a loop, because the loop count is then
    random and (since A toggles the coin) an even count silently leaves the
    character unlocked. The real lock check is downstream: START only advances
    to stage select if the character is locked."""
    grid = load_grid()
    x, y = cell(grid, name)
    cur.select(x, y, costume=costume, lock=False, css_index=css_index(name))
    cur.p.center()
    time.sleep(0.15)
    cur.p.tap("A", 0.08)           # single deliberate lock press
    time.sleep(0.35)
    return cur.hovered() == css_index(name)


def lock_at_icon(cur, x, y, index):
    """Lock a fighter by its CSS ICON coordinate (from the build manifest's
    cssIcon -- the app's grid placement). The cursor target is (x, y - 3.5)
    (the validated icon->cursor offset) and `index` is the grid index to
    confirm the hover. Same single-A lock as lock_character. Works for custom
    m-ex fighters (whose cell isn't in the vanilla grid.json)."""
    tx, ty = x, y - 3.5
    cur.unlock()
    cur.move_to(tx, ty)
    for _ in range(4):
        if cur.hovered() == index:
            break
        cur.move_to(tx, ty, tol=0.7)
        time.sleep(0.12)
    cur.p.center()
    time.sleep(0.15)
    cur.p.tap("A", 0.08)
    time.sleep(0.35)
    return cur.hovered() == index


def parse_icon(argv):
    if "--icon" in argv:
        spec = argv[argv.index("--icon") + 1]
        x, y, index = spec.split(",")
        return (float(x), float(y), int(index))
    return None


def parse_stage_icon(argv):
    """--stage-icon page,x,y -> (page, x, y) for a CUSTOM stage (off the main
    page), from the build manifest's sssIcon."""
    if "--stage-icon" in argv:
        spec = argv[argv.index("--stage-icon") + 1]
        page, x, y = spec.split(",")
        return (int(page), float(x), float(y))
    return None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    name = sys.argv[1]
    icon = parse_icon(sys.argv)
    stage_icon = parse_stage_icon(sys.argv)
    # --hold <button> keeps a button held through stage load -> the DAS trigger.
    hold = sys.argv[sys.argv.index("--hold") + 1].upper() if "--hold" in sys.argv else None
    # --move <name> performs an in-game move after the match starts (effect mods).
    move = sys.argv[sys.argv.index("--move") + 1] if "--move" in sys.argv else None
    costume = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 0
    stage = "battlefield"
    for a in sys.argv[2:]:
        if norm_stage(a) in STAGE_TARGET:
            stage = a
            break

    d = Dolphin()
    p = Pipe()
    cur = Cursor(d, p)
    sc = StageCursor(d, p)
    # Sacrificial neutral + settle: this persistent pipe opens right after the
    # node per-frame steps (gotocss/cpustep); the first write on a fresh
    # connection can be dropped on the handoff, so don't let it be a real input.
    p.neutral()
    time.sleep(0.4)

    if icon is not None:
        ix, iy, iidx = icon
        on_cell = lock_at_icon(cur, ix, iy, iidx)
        print(f"  custom fighter {name} @icon({ix},{iy}) idx {iidx}: "
              f"on_cell={on_cell} hovered_idx={cur.hovered()}")
    else:
        on_cell = lock_character(cur, name, costume)
        print(f"  char {name} costume {costume}: on_cell={on_cell} "
              f"hovered_idx={cur.hovered()} (want {css_index(name)}) "
              f"costume_read={cur.costume()}")

    # Same pipe: advance to stage select (START is also the functional lock
    # check -- it only transitions if the character actually locked) and pick
    # the stage. select()/select_at() returns True iff the match started.
    if stage_icon is not None:
        spage, sx, sy = stage_icon
        started = sc.select_at(sx, sy, page=spage, press=True)
        print(f"  custom stage @page{spage}({sx},{sy}): match_started={started}")
    else:
        started = sc.select(stage, press=True, hold=hold)
        tag = f" (hold {hold} -> DAS alt)" if hold else ""
        print(f"  stage {stage}{tag}: match_started={started}")

    # Effect mods: perform the move that exercises the effect in-game (so its
    # model/data actually loads), and screenshot it.
    if started and move:
        perform_move(p, move)
        screenshot(f"effect-{move}-{name}")
        print(f"  performed {move} (effect trigger)")

    p.center()
    p.close()
    time.sleep(0.3)
    return 0 if started else 1


if __name__ == "__main__":
    sys.exit(main())
