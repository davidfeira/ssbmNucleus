"""
desync_check.py -- diff the live game state of TWO Slippi Dolphin instances to
detect and localize desyncs. This is the observability foundation for the
netplay desync debugger (the user's idea): in a netplay match the two clients
run the same game in lockstep, so their game-relevant RAM should be identical
each frame -- wherever it diverges is the desync, and the differing addresses
point at what diverged.

Reads each instance's MEM1 via melee_mem (attach by PID) -- no libmelee, no
Slippi stream, version-independent. The netplay CONNECTION between the two
clients (matchmaking / direct-connect) is SEPARATE setup that this does not do;
this is the read+diff half. Until that's wired up you can sanity-check the diff
mechanism against two instances of the same ISO (they will differ everywhere
since they aren't synced -- that just exercises the plumbing).

    python desync_check.py <pid1> <pid2>            # one snapshot diff
    python desync_check.py <pid1> <pid2> --watch 30 # poll, report divergence

Notes / TODO for the full debugger:
  - Some MEM1 regions legitimately differ even in sync (audio mixer, HID/
    controller buffers, some RNG-seed scratch). Those belong in IGNORE so they
    don't mask the real desync. Refine IGNORE empirically once two synced
    clients are available.
  - The cleanest signal is usually the player blocks (position/state/RNG) and
    the global RNG seed; a frame-aligned diff there localizes the desync fast.
"""

import sys
import time

import numpy as np

from melee_mem import Dolphin, GC_BASE, MEM1_VALID

FRAME_COUNTER = 0x80479D60

# GC address ranges that may differ between synced clients (NOT desyncs).
# Placeholder -- refine once we can observe two genuinely-synced clients.
IGNORE = [
    # (start_gc, end_gc),
]


def snapshot(d):
    buf = d.snapshot(MEM1_VALID)
    return np.frombuffer(buf, np.uint8) if buf else None


def apply_ignore(mask):
    for start, end in IGNORE:
        s = start - GC_BASE
        e = end - GC_BASE
        mask[s:e] = False
    return mask


def diff(a, b, max_report=20):
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    ne = a != b
    apply_ignore(ne)
    idx = np.nonzero(ne)[0]
    runs = []
    if len(idx):
        # group contiguous differing bytes into runs for readable output
        breaks = np.nonzero(np.diff(idx) > 4)[0]
        starts = np.concatenate(([idx[0]], idx[breaks + 1]))
        ends = np.concatenate((idx[breaks], [idx[-1]]))
        for s, e in zip(starts[:max_report], ends[:max_report]):
            runs.append((GC_BASE + int(s), GC_BASE + int(e),
                         bytes(a[s:e + 1][:8]), bytes(b[s:e + 1][:8])))
    return int(ne.sum()), runs


def report(da, db):
    fa, fb = da.u32(FRAME_COUNTER), db.u32(FRAME_COUNTER)
    print(f"frame: pid{da.pid}={fa}  pid{db.pid}={fb}  {'(aligned)' if fa == fb else '(NOT aligned!)'}")
    a, b = snapshot(da), snapshot(db)
    if a is None or b is None:
        print("  could not read one instance's RAM")
        return None
    count, runs = diff(a, b)
    print(f"  {count:,} differing bytes across MEM1")
    for s, e, av, bv in runs:
        print(f"    0x{s:08x}-0x{e:08x}: A={av.hex()} B={bv.hex()}")
    return count


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 2
    pid1, pid2 = int(args[0]), int(args[1])
    da, db = Dolphin(pid1), Dolphin(pid2)
    print(f"attached: pid{pid1} base 0x{da.base:012x}, pid{pid2} base 0x{db.base:012x}")

    if "--watch" in args:
        seconds = float(args[args.index("--watch") + 1])
        start = time.time()
        baseline = None
        while time.time() - start < seconds:
            count = report(da, db)
            if count is None:
                print("VERDICT: a client became unreadable (crash?)")
                return 1
            # In a real synced session, baseline≈0 and a jump up = the desync.
            if baseline is not None and count > baseline * 3 + 100:
                print(f"VERDICT: divergence grew {baseline} -> {count} (likely desync frame)")
                return 1
            baseline = count if baseline is None else min(baseline, count)
            time.sleep(0.25)
        print("VERDICT: no growing divergence observed")
        return 0

    report(da, db)
    return 0


if __name__ == "__main__":
    sys.exit(main())
