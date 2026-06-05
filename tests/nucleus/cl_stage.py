"""
cl_stage.py -- closed-loop (memory-feedback) stage selection, as a standalone
step for the match orchestrator. The stage analog of cl_select.py.

Assumes the CSS is locked (a character picked + a port-2 CPU). It advances to
the stage-select screen itself -- pressing START over its own persistent pipe
and verifying the scene changed (a separate per-frame `gotostage` step dropped
the START on the connection handoff) -- then steers the cursor to the target
stage by reading its live position (no timing) and presses A, which starts the
match on that stage.

    python cl_stage.py <stage>      # e.g. battlefield, fd, dreamland, yoshis,
                                    #      stadium, fountain, random

Exit 0 if the cursor reached the stage cell (and pressed A), 1 otherwise.
"""

import sys
import time

from melee_mem import Dolphin
from melee_pipe import Pipe
from melee_sss import StageCursor, norm, STAGE_TARGET


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    name = sys.argv[1]
    if norm(name) not in STAGE_TARGET:
        print(f"unknown stage '{name}' (known: {', '.join(sorted(STAGE_TARGET))})")
        return 2

    d = Dolphin()
    p = Pipe()
    sc = StageCursor(d, p)
    # Sacrificial neutral + settle: this persistent connection opens right after
    # the node per-frame step (gotostage), and the first write on a fresh
    # connection can be dropped on the handoff -- don't let it be a real input.
    p.neutral()
    time.sleep(0.4)
    p.main(0.5, 0.5)
    time.sleep(0.15)
    p.center()
    time.sleep(0.15)

    reached = sc.select(name, press=True)
    x, y = sc.pos()
    print(f"cl_stage {name}: reached={reached} pos=({x},{y})")
    # Release the persistent pipe cleanly so the next step's first input isn't
    # dropped on the connection handoff.
    p.center()
    p.close()
    time.sleep(0.3)
    return 0 if reached else 1


if __name__ == "__main__":
    sys.exit(main())
