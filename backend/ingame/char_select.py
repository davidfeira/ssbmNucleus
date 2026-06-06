"""
char_select.py -- character name resolution + the calibrated CSS cursor grid
(grid.json) for closed-loop selection. Ported from tests/nucleus/char_select.py
(the dev CLI main() and its Dolphin/Pipe imports dropped -- the runner only
needs the lookups here).
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def _grid_path():
    """Resolve grid.json in dev (next to this module) and frozen (PyInstaller
    bundles it under <_MEIPASS>/ingame/grid.json) layouts."""
    candidates = [os.path.join(HERE, "grid.json")]
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, "ingame", "grid.json"))
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]


GRID_PATH = _grid_path()

ALIASES = {
    "doc": "drmario", "doctormario": "drmario",
    "ganon": "ganondorf", "dk3": "dk", "donkeykong": "dk",
    "cf": "falcon", "captainfalcon": "falcon", "cfalcon": "falcon",
    "sheik": "zelda",  # same cell; sheik is reached by toggling after select
    "gnw": "gameandwatch", "gw": "gameandwatch", "mrgameandwatch": "gameandwatch",
    "mrgamewatch": "gameandwatch", "gamewatch": "gameandwatch",
    "puff": "jigglypuff", "jiggs": "jigglypuff",
    "pika": "pikachu", "mew2": "mewtwo",
    "ics": "iceclimbers", "icies": "iceclimbers", "popo": "iceclimbers",
    "yl": "younglink", "yink": "younglink",
}

# CSS grid index (Dr.Mario=0 ... Fox=10 ... Roy=24) -- the value at 0x803F0E0A.
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
    key = "".join(ch for ch in str(name).lower() if ch.isalnum())
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
