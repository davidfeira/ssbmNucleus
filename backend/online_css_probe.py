"""
online_css_probe.py -- does the Slippi ONLINE CSS show m-ex custom characters?

Boots a Nucleus build in an isolated Dolphin, presses A at the Slippi Online
Play boot menu to enter the online (unranked) CSS, screenshots it, and HOLDS B
back out before matchmaking can pair anyone (same safe envelope as
tests/nucleus/online_css_test.py). The screenshot shows whether added m-ex
fighters (e.g. Deoxys's icon) are present/selectable online.

Run from backend/:  python online_css_probe.py [--iso <path>]
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.config import STORAGE_PATH, PROJECT_ROOT  # noqa: E402

from ingame.boot import DolphinBoot  # noqa: E402
from ingame.melee_mem import Dolphin  # noqa: E402
from ingame.melee_pipe import Pipe  # noqa: E402
from ingame import screenshot as shot  # noqa: E402

ART = PROJECT_ROOT.parent / "tests" / "artifacts" / "fsm-probe"
RUNS_ROOT = STORAGE_PATH / "test-runs"
DEFAULT_ISO = Path(r"C:\Users\david\Downloads\deoxys_test_2026-06-12_16-07.iso")

SCENE_MAJOR = 0x80479D30
FRAME = 0x80479D60
ONLINE_CSS = 0x08
HOVER_BASE = 0x803F0E0A   # per-port +0x24: hovered CSS grid index


def log(m):
    print(m, flush=True)


def snap(boot, name):
    png = None
    try:
        png = shot.capture_via_printwindow(boot.pid, max_width=960)
    except Exception:
        png = None
    if not png:
        try:
            png = shot.capture_png(boot.pid, max_width=960)
        except Exception:
            png = None
    if png:
        (ART / f"{name}.png").write_bytes(png)
        log(f"  shot -> {name}.png")


def main():
    iso = DEFAULT_ISO
    if "--iso" in sys.argv:
        iso = Path(sys.argv[sys.argv.index("--iso") + 1])
    ART.mkdir(parents=True, exist_ok=True)

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
            time.sleep(0.4)
        if d.base is None:
            raise SystemExit("could not locate MEM1")
        p = Pipe(boot.pipe_index)

        # wait for the boot menu (Slippi Online Play, scene 0x01)
        t0 = time.time()
        while time.time() - t0 < 30 and d.u8(SCENE_MAJOR) != 0x01:
            time.sleep(0.4)
        log(f"boot menu scene=0x{d.u8(SCENE_MAJOR):02X}; entering online CSS...")
        time.sleep(2.0)
        p.tap("A", 0.08)

        # wait for the online CSS, then screenshot fast and leave
        t0 = time.time()
        while time.time() - t0 < 10 and d.u8(SCENE_MAJOR) != ONLINE_CSS:
            time.sleep(0.3)
        scene = d.u8(SCENE_MAJOR)
        log(f"scene now 0x{scene:02X} ({'ONLINE CSS' if scene == ONLINE_CSS else 'unexpected'})")
        if scene == ONLINE_CSS:
            time.sleep(2.5)          # let icons render
            snap(boot, "online-css")
            hov = d.u8(HOVER_BASE)
            log(f"p1 hovered grid index: {hov}")
        # HOLD B out before matchmaking pairs anyone
        log("holding B to exit...")
        p.frame(["PRESS B", "FLUSH"])
        time.sleep(1.2)
        p.frame(["RELEASE B", "FLUSH"])
        time.sleep(1.0)
        log(f"scene after exit: 0x{d.u8(SCENE_MAJOR):02X}")
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
