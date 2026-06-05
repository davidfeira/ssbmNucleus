"""
select.py -- closed-loop character + costume selection by name, using the
calibrated grid (grid.json) and memory-feedback control (melee_css.Cursor).

    python select.py <character> [costume] [--hover]
"""

import json
import os
import sys

from melee_mem import Dolphin
from melee_pipe import Pipe
from melee_css import Cursor

HERE = os.path.dirname(os.path.abspath(__file__))
GRID_PATH = os.path.join(HERE, "grid.json")

ALIASES = {
    "doc": "drmario", "doctormario": "drmario",
    "ganon": "ganondorf", "dk3": "dk", "donkeykong": "dk",
    "cf": "falcon", "captainfalcon": "falcon",
    "sheik": "zelda",  # same cell; sheik is reached by toggling after select
    "gnw": "gameandwatch", "gw": "gameandwatch", "mrgameandwatch": "gameandwatch",
    "puff": "jigglypuff", "jiggs": "jigglypuff",
    "pika": "pikachu", "mew2": "mewtwo",
    "ics": "iceclimbers", "icies": "iceclimbers", "popo": "iceclimbers",
    "yl": "younglink", "yink": "younglink",
}


# CSS grid index (Dr.Mario=0 ... Fox=10 ... Roy=24) -- the value at 0x803F0E0A,
# used to CONFIRM the cursor is on the right character (grid-layout-independent,
# verified 10/10 against libmelee's menu-info gecko encoding).
CSS_INDEX = {
    "drmario": 0, "mario": 1, "luigi": 2, "bowser": 3, "peach": 4, "yoshi": 5,
    "dk": 6, "falcon": 7, "ganondorf": 8,
    "falco": 9, "fox": 10, "ness": 11, "iceclimbers": 12, "kirby": 13,
    "samus": 14, "zelda": 15, "link": 16, "younglink": 17,
    "pichu": 18, "pikachu": 19, "jigglypuff": 20, "mewtwo": 21,
    "gameandwatch": 22, "marth": 23, "roy": 24,
}


def load_grid():
    with open(GRID_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def norm(name):
    key = "".join(ch for ch in name.lower() if ch.isalnum())
    return ALIASES.get(key, key)


def css_index(name):
    return CSS_INDEX.get(norm(name))


def cell(grid, name):
    key = norm(name)
    if key not in grid:
        raise KeyError(f"no grid cell for '{name}' (known: {', '.join(sorted(grid))})")
    return grid[key]


def select(cur, grid, name, costume=0, lock=True):
    x, y = cell(grid, name)
    return cur.select(x, y, costume=costume, lock=lock)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    name = sys.argv[1]
    costume = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 0
    lock = "--hover" not in sys.argv
    d = Dolphin()
    cur = Cursor(d, Pipe())
    grid = load_grid()
    ok = select(cur, grid, name, costume=costume, lock=lock)
    x, y = cur.pos()
    print(f"{name} costume {costume}: ok={ok} pos=({x:+.1f},{y:+.1f}) costume_read={cur.costume()}")


if __name__ == "__main__":
    main()
