"""
cl_select.py -- closed-loop (memory-feedback) character + costume selection,
as a standalone step for the match orchestrator.

Assumes we're on the character-select screen with a 2nd player already set up
(a port-2 CPU) -- locking the coin requires it. Steers the cursor to the cell
by reading its live position (no timing), sets the costume by reading the
costume index, and locks with A, confirming via the lock flag.

    python cl_select.py <character> [costume]

Exit 0 if it locked the right character+costume, 1 otherwise.
"""

import sys

from melee_mem import Dolphin
from melee_pipe import Pipe
from melee_css import Cursor
from char_select import load_grid, cell, css_index


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    name = sys.argv[1]
    costume = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 0

    import time
    d = Dolphin()
    p = Pipe()
    c = Cursor(d, p)
    # Sacrificial neutral + settle: this persistent connection opens right after
    # the node per-frame steps (gotocss/cpustep), and the first write on a fresh
    # connection can be dropped on the handoff -- so don't let it be a real input.
    p.neutral()
    time.sleep(0.4)
    grid = load_grid()
    x, y = cell(grid, name)
    ok = c.select(x, y, costume=costume, lock=True, css_index=css_index(name))
    locked = c.locked()
    print(f"cl_select {name} costume {costume}: ok={ok} locked={locked} "
          f"hovered_idx={c.hovered()} (want {css_index(name)}) costume_read={c.costume()}")
    # Release the persistent pipe cleanly so the next (node, per-frame) step's
    # first input isn't dropped on the connection handoff.
    p.close()
    import time
    time.sleep(0.3)
    return 0 if (ok and locked) else 1


if __name__ == "__main__":
    sys.exit(main())
