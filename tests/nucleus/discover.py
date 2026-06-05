"""
discover.py -- empirically locate Melee CSS memory addresses by correlating
controller inputs with RAM changes. Robust to game version and mods because it
finds addresses by cause-and-effect, not a hardcoded table.

Method: pin the cursor to a wall (deterministic start), then nudge it across the
screen in several small steps, snapshotting RAM after each. The cursor
coordinate is the float that moves MONOTONICALLY across every step (animation
noise won't track a controlled multi-step trajectory).

Run while sitting on the character select screen (port 1 cursor active).
"""

import os
import subprocess
import sys
import time

import numpy as np

from melee_mem import Dolphin, GC_BASE
from melee_pipe import Pipe

HERE = os.path.dirname(os.path.abspath(__file__))
PIPE_JS = os.path.join(HERE, "..", "dolphin", "pipe.js")


def hover(name):
    """Move the port-1 cursor onto a character via the timing-based selector."""
    subprocess.run(["node", PIPE_JS, "char", name, "--hover"],
                   cwd=HERE, capture_output=True, shell=True)
    time.sleep(0.4)


def f32(buf):
    n = (len(buf) // 4) * 4
    return np.frombuffer(buf[:n], ">f4").astype(np.float64)


def u8(buf):
    return np.frombuffer(buf, np.uint8).astype(np.int16)


def settle(t=0.12):
    time.sleep(t)


def trajectory(d, p, pin, step, n_steps=6, dwell=0.18):
    """Pin to a wall, then step across; return RAM snapshots after each step."""
    p.main(*pin); time.sleep(0.8); p.center(); settle(0.25)
    samples = [d.snapshot()]
    for _ in range(n_steps):
        p.main(*step); time.sleep(dwell); p.center(); settle()
        samples.append(d.snapshot())
    return samples


def monotonic_floats(samples, min_span=8.0, rng=80.0, min_steps=3):
    n = min(len(s) for s in samples) // 4
    raw = np.stack([f32(s)[:n] for s in samples])  # (steps+1, nfloats)
    finite = np.isfinite(raw).all(0)
    S = np.nan_to_num(raw, nan=1e30, posinf=1e30, neginf=-1e30)
    inrange = (np.abs(S) <= rng).all(0)
    diffs = np.diff(S, axis=0)
    gradual = (np.abs(diffs) > 0.5).sum(0) >= min_steps  # moved on >=3 steps
    up = (diffs >= -0.5).all(0) & ((S[-1] - S[0]) > min_span)
    down = (diffs <= 0.5).all(0) & ((S[0] - S[-1]) > min_span)
    idx = np.where((up | down) & finite & inrange & gradual)[0]
    idx = sorted(idx, key=lambda i: -abs(S[-1, i] - S[0, i]))
    return [(GC_BASE + int(i) * 4, raw[:, i]) for i in idx]


def find_axis(d, p, pin, step, label):
    hits = monotonic_floats(trajectory(d, p, pin, step))
    print(f"[{label}] {len(hits)} monotonic float(s):")
    for addr, traj in hits:
        print(f"  0x{addr:08x}: " + " ".join(f"{v:+.1f}" for v in traj))
    return [a for a, _ in hits]


def find_costume(d, p):
    snaps = [u8(d.snapshot())]
    for _ in range(3):
        p.tap("X", 0.05); time.sleep(0.4)
        snaps.append(u8(d.snapshot()))
    n = min(len(s) for s in snaps)
    snaps = [s[:n] for s in snaps]
    inc = np.ones(n, dtype=bool)
    for i in range(3):
        inc &= (snaps[i + 1] - snaps[i]) == 1
    inc &= snaps[0] < 8
    idx = np.where(inc)[0]
    print(f"[costume] {len(idx)} candidate(s):")
    for i in idx:
        print(f"  0x{GC_BASE + int(i):08x}: " + " ".join(str(int(s[i])) for s in snaps))
    return [GC_BASE + int(i) for i in idx]


# Melee character ids in two known orderings; whichever the CSS stores, the
# hovered-character byte will exactly equal one of these fingerprints.
EXTERNAL = {"fox": 2, "falco": 20, "ganondorf": 25, "marth": 9, "mario": 8}
INTERNAL = {"fox": 1, "falco": 22, "ganondorf": 25, "marth": 18, "mario": 0}


def find_character(d):
    """Find the 'character under cursor' byte by hovering known characters and
    matching the values against Melee's character-id orderings."""
    seq = ["fox", "falco", "fox", "ganondorf", "fox", "marth"]
    snaps = []
    for nm in seq:
        hover(nm)
        snaps.append(u8(d.snapshot()))
    n = min(len(s) for s in snaps)
    s = [x[:n] for x in snaps]
    for name, ids in (("external", EXTERNAL), ("internal", INTERNAL)):
        want = np.array([ids[nm] for nm in seq], dtype=np.int16)
        match = np.ones(n, dtype=bool)
        for k in range(len(seq)):
            match &= s[k] == want[k]
        idx = np.where(match)[0]
        print(f"[character/{name}] expect {list(want)} -> {len(idx)} exact match(es):")
        for i in idx:
            print(f"  0x{GC_BASE + int(i):08x}")
    return None


def main():
    d = Dolphin()
    p = Pipe()
    print(f"attached pid {d.pid}, MEM1 base 0x{d.base:012x}")
    what = sys.argv[1] if len(sys.argv) > 1 else "cursor"

    if what in ("cursor", "all"):
        find_axis(d, p, (0.0, 0.5), (1.0, 0.5), "cursor.X (right)")
        find_axis(d, p, (0.5, 0.0), (0.5, 1.0), "cursor.Y (down)")
    if what in ("costume", "all"):
        find_costume(d, p)
    if what in ("character", "char", "all"):
        find_character(d)


if __name__ == "__main__":
    main()
