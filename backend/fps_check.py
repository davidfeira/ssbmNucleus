"""
fps_check.py -- boot an ISO and measure the emulated game frame-rate (the global
frame counter 0x80479D60 vs wall-clock) on the boot menu and on the CSS. Used to
tell whether a big/heavy build runs DEGRADED in Dolphin (low FPS / stalls) vs the
automation just timing out.

Run from backend/:  python fps_check.py --iso ../output/stress-roster-distinct.iso
"""
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH  # noqa: E402
from ingame.boot import DolphinBoot  # noqa: E402
from ingame.melee_mem import Dolphin  # noqa: E402
from ingame.melee_pipe import Pipe  # noqa: E402
from ingame.melee_css import Cursor  # noqa: E402
from ingame import nav, match_setup  # noqa: E402

RUNS = STORAGE_PATH / "test-runs"
FRAME_COUNTER = 0x80479D60


def log(m):
    print(m, flush=True)


def measure_fps(d, secs, label):
    f0 = d.u32(FRAME_COUNTER)
    t0 = time.time()
    time.sleep(secs)
    f1 = d.u32(FRAME_COUNTER)
    t1 = time.time()
    if f0 is None or f1 is None:
        log(f"  {label}: frame counter unreadable ({f0}->{f1})")
        return None
    df = (f1 - f0) & 0xFFFFFFFF
    fps = df / (t1 - t0)
    log(f"  {label}: {df} frames in {t1-t0:.1f}s = {fps:.1f} fps  (counter {f0}->{f1})")
    return fps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", required=True)
    args = ap.parse_args()
    iso = Path(args.iso)
    if not iso.exists():
        raise SystemExit(f"ISO missing: {iso}")
    RUNS.mkdir(parents=True, exist_ok=True)

    boot = DolphinBoot(str(iso), None, str(RUNS), log=log)
    p = None
    try:
        boot.prepare()
        boot.launch()
        if not boot.wait_for_pipe(timeout=45):
            raise SystemExit("pipe never appeared")
        d = Dolphin(boot.pid)
        t0 = time.time()
        while not d.locate() and time.time() - t0 < 25:
            if not d.alive():
                raise SystemExit("died during boot")
            time.sleep(0.4)
        if d.base is None:
            raise SystemExit("no MEM1")

        log("FPS at boot/menu:")
        measure_fps(d, 4.0, "menu")

        match_setup.patch_one_player(d, log=log)
        p = Pipe(boot.pipe_index)
        if nav.nav_to_css(d, p, log=log):
            cur = Cursor(d, p)
            nav.wait_css_ready(d, cur, log=log)
            log("FPS on CSS (idle):")
            measure_fps(d, 5.0, "css-idle")
            # try a cursor nudge and see if the cursor position changes at all
            x0, y0 = cur.read_pos()
            p.main(1.0, 0.5)  # full right
            time.sleep(1.0)
            p.center()
            x1, y1 = cur.read_pos()
            log(f"  cursor before nudge=({x0},{y0}) after full-right-1s=({x1},{y1})")
            log("FPS on CSS (after input):")
            measure_fps(d, 4.0, "css-post")
        else:
            log("nav_to_css failed; measuring FPS wherever we are:")
            measure_fps(d, 5.0, "post-nav-fail")
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
