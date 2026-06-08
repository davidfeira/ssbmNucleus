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

# External character id (the match player block's "c_kind") -- what the cursor-free
# memory selection writes to pick a fighter without steering. DISTINCT from the
# CSS grid index above: this is the engine's character id (Fox=0x02, Marth=0x09
# verified live; "no pick"/Master Hand = 0x1A). Sheik shares Zelda's slot (0x12).
CKIND = {
    "falcon": 0x00, "dk": 0x01, "fox": 0x02, "gameandwatch": 0x03, "kirby": 0x04,
    "bowser": 0x05, "link": 0x06, "luigi": 0x07, "mario": 0x08, "marth": 0x09,
    "mewtwo": 0x0A, "ness": 0x0B, "peach": 0x0C, "pikachu": 0x0D, "iceclimbers": 0x0E,
    "jigglypuff": 0x0F, "samus": 0x10, "yoshi": 0x11, "zelda": 0x12, "falco": 0x14,
    "younglink": 0x15, "drmario": 0x16, "roy": 0x17, "pichu": 0x18, "ganondorf": 0x19,
}


def load_grid():
    with open(GRID_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def norm(name):
    key = "".join(ch for ch in str(name).lower() if ch.isalnum())
    return ALIASES.get(key, key)


def css_index(name):
    return CSS_INDEX.get(norm(name))


def ckind(name):
    """External character id for the cursor-free memory selection, or None for an
    unknown / custom fighter (caller should fall back to the cursor)."""
    return CKIND.get(norm(name))


def cell(grid, name):
    key = norm(name)
    if key not in grid:
        raise KeyError(f"no grid cell for '{name}' (known: {', '.join(sorted(grid))})")
    return grid[key]


def select(cur, grid, name, costume=0, lock=True):
    x, y = cell(grid, name)
    return cur.select(x, y, costume=costume, lock=lock)
