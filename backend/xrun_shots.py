"""xrun_shots.py -- boot the xrun-test ISO and screenshot each modded costume
in-game (solo, no CPU, no cursor). One boot per costume for reliability.

Run from backend/:  python xrun_shots.py
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.config import STORAGE_PATH, PROJECT_ROOT  # noqa: E402
from ingame.boot import DolphinBoot  # noqa: E402
from ingame.melee_mem import Dolphin  # noqa: E402
from ingame.melee_pipe import Pipe  # noqa: E402
from ingame.melee_css import Cursor  # noqa: E402
from ingame.melee_sss import StageCursor, INTERNAL_STAGE_ID  # noqa: E402
from ingame.observe import wait_in_game, wait_game_frames  # noqa: E402
from ingame import nav, match_setup  # noqa: E402
from ingame import screenshot as shot  # noqa: E402

ISO = PROJECT_ROOT / "output" / "xrun-test.iso"
OUT = Path(r"C:\Users\david\Downloads\xrunriot\_ingame")
RUNS_ROOT = STORAGE_PATH / "test-runs"

FOX = 0x02
MARTH = 0x09

# (label, ckind, color)
COSTUMES = [
    ("vader_black", MARTH, 5),
    ("vader_redeemed", MARTH, 6),
    ("link_fox", FOX, 4),
    ("tails", FOX, 5),
]


def log(m):
    print(m, flush=True)


def snap(boot, name):
    png = None
    try:
        png = shot.capture_via_printwindow(boot.pid, max_width=1100)
    except Exception:
        png = None
    if not png:
        try:
            png = shot.capture_png(boot.pid, max_width=1100)
        except Exception:
            png = None
    if png:
        (OUT / f"{name}.png").write_bytes(png)
        log(f"  shot -> {name}.png ({len(png)} bytes)")
    else:
        log(f"  shot FAILED for {name}")


def shoot_one(label, ckind, color):
    log(f"=== {label}: ckind=0x{ckind:02X} color={color} ===")
    boot = DolphinBoot(str(ISO), None, str(RUNS_ROOT), log=log)
    p = None
    try:
        boot.prepare()
        boot.launch()
        if not boot.wait_for_pipe(timeout=60):
            log("  pipe never appeared"); return
        d = Dolphin(boot.pid)
        t0 = time.time()
        while not d.locate() and time.time() - t0 < 25:
            if not d.alive():
                log("  dolphin died"); return
            time.sleep(0.4)
        if d.base is None:
            log("  could not locate MEM1"); return

        match_setup.patch_one_player(d, log=log)
        p = Pipe(boot.pipe_index)
        if not nav.nav_to_css(d, p, log=log):
            log("  never reached CSS"); return
        cur = Cursor(d, p)
        nav.wait_css_ready(d, cur, log=log)
        match_setup.force_time_infinite(d, log=log)

        match_setup.write_solo_player(d, ckind, color)
        match_setup.warp_to_stage_select(d)
        sc = StageCursor(d, p)
        if not sc.wait_for_stage_select(timeout=10.0):
            log("  CSS->SSS warp failed"); return
        match_setup.write_solo_player(d, ckind, color)
        if not sc.force_select(INTERNAL_STAGE_ID["battlefield"]):
            log("  match never started"); return

        wait_in_game(d, timeout=20.0)
        wait_game_frames(d, 140)   # settle past READY/GO, character standing
        snap(boot, f"{label}_live")
        # a couple more spaced frames to catch a clean idle pose
        wait_game_frames(d, 80)
        snap(boot, f"{label}_live2")
        # pause for a frozen, clean frame (no zoom: pause C-stick only pans)
        p.tap("START", 0.08)
        time.sleep(0.5)
        snap(boot, f"{label}_paused")
    finally:
        try:
            if p:
                p.close()
        except Exception:
            pass
        boot.cleanup()


def main():
    if not ISO.exists():
        raise SystemExit(f"ISO missing: {ISO}")
    OUT.mkdir(parents=True, exist_ok=True)
    only = sys.argv[1] if len(sys.argv) > 1 else None
    for label, ckind, color in COSTUMES:
        if only and only != label:
            continue
        try:
            shoot_one(label, ckind, color)
        except Exception as e:
            log(f"  {label} ERROR: {e}")
        time.sleep(1.0)
    log("done")


if __name__ == "__main__":
    main()
