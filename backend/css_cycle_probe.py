"""
css_cycle_probe.py -- on the real character-select screen, hover a character and
press X over and over, reading the costume index (0x80480823) each time, to find
how many costumes are actually SELECTABLE via the CSS cycler (vs merely loadable
by memory write). The m-ex cycler is cyclic: costume = (costume+1) % count, so the
peak value before it wraps back to 0 == count-1. If it instead CAPS (sticks at a
max and never wraps) we report that too.

Run from backend/:
  python css_cycle_probe.py --iso ../output/stress-fox-255.iso --char fox --presses 300
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH  # noqa: E402
from ingame.boot import DolphinBoot  # noqa: E402
from ingame.melee_mem import Dolphin  # noqa: E402
from ingame.melee_pipe import Pipe  # noqa: E402
from ingame.melee_css import Cursor  # noqa: E402
from ingame import nav, match_setup, char_select  # noqa: E402

RUNS_ROOT = STORAGE_PATH / "test-runs"


def log(m):
    print(m, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", required=True)
    ap.add_argument("--char", default="fox")
    ap.add_argument("--presses", type=int, default=300)
    args = ap.parse_args()

    iso = Path(args.iso)
    if not iso.exists():
        raise SystemExit(f"ISO missing: {iso}")
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)

    boot = DolphinBoot(str(iso), None, str(RUNS_ROOT), log=log)
    p = None
    try:
        boot.prepare()
        boot.launch()
        if not boot.wait_for_pipe(timeout=45):
            raise SystemExit("input pipe never appeared")
        d = Dolphin(boot.pid)
        t0 = time.time()
        while not d.locate() and time.time() - t0 < 20:
            if not d.alive():
                raise SystemExit("Dolphin died during boot")
            time.sleep(0.4)
        if d.base is None:
            raise SystemExit("could not locate MEM1")

        match_setup.patch_one_player(d, log=log)
        p = Pipe(boot.pipe_index)
        if not nav.nav_to_css(d, p, log=log):
            raise SystemExit("never reached offline CSS")
        cur = Cursor(d, p)
        nav.wait_css_ready(d, cur, log=log)

        grid = char_select.load_grid()
        x, y = char_select.cell(grid, args.char)
        idx = char_select.css_index(args.char)
        cur.unlock()
        cur.move_to(x, y)
        for _ in range(6):
            time.sleep(0.15)
            if cur.hovered() == idx:
                break
            cur.move_to(x, y, tol=0.6)
        log(f"hovered index={cur.hovered()} (want {idx}); start costume={cur.costume()}")

        seen = []
        peak = -1
        wrapped_at = None
        stuck = 0
        prev = cur.costume()
        for i in range(args.presses):
            before = cur.costume()
            # tap X; retry a couple times if the input was dropped (value
            # unchanged AND we're not at a genuine cap yet)
            changed = False
            for _ in range(3):
                p.tap("X", 0.05)
                time.sleep(0.16)
                now = cur.costume()
                if now != before:
                    changed = True
                    break
            now = cur.costume()
            seen.append(now)
            if now > peak:
                peak = now
            if not changed:
                stuck += 1
            else:
                stuck = 0
            if now < before and wrapped_at is None:
                wrapped_at = before  # the value just before it dropped == count-1
                log(f"  WRAP: {before} -> {now} at press {i+1}  => count={before+1}")
            if wrapped_at is not None and now == peak:
                pass
            if stuck >= 6:
                log(f"  CAP: stuck at {now} for 6 presses (press {i+1})")
                break
            if wrapped_at is not None and i > 0 and now >= 3:
                # we've confirmed the wrap and cycled a few past 0; stop early
                if now == seen[0] or now == 3:
                    pass
            prev = now
        # summarize
        distinct = sorted(set(seen))
        result = {
            "char": args.char,
            "hovered": cur.hovered(),
            "peak_costume": peak,
            "selectable_count": (wrapped_at + 1) if wrapped_at is not None else None,
            "wrapped": wrapped_at is not None,
            "capped_at": (peak if (wrapped_at is None and stuck >= 6) else None),
            "n_distinct": len(distinct),
            "first_20": seen[:20],
            "max_distinct": distinct[-5:] if distinct else [],
        }
        log("CSS_RESULT " + json.dumps(result))
        return 0
    finally:
        try:
            if p:
                p.close()
        except Exception:
            pass
        boot.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
