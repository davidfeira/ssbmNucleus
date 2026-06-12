"""Boot an ISO, start a solo Fox match (costume index 4), move around, PAUSE,
and grab a close-up screenshot (the pause camera zooms onto the character).
The model-lab visual QA loop, driven entirely by the in-app engine.

usage: pause_capture.py <iso> <out.png> [css_costume_index]
"""
import os
import sys
import time
from pathlib import Path

BACKEND = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

from ingame.boot import DolphinBoot, wait_until_no_dolphin  # noqa: E402
from ingame.melee_mem import Dolphin  # noqa: E402
from ingame.melee_pipe import Pipe  # noqa: E402
from ingame.melee_css import Cursor  # noqa: E402
from ingame.melee_sss import StageCursor  # noqa: E402
from ingame.observe import wait_in_game, wait_game_frames  # noqa: E402
from ingame import nav, match_setup, screenshot as shot  # noqa: E402
from ingame.char_select import ckind as char_ckind  # noqa: E402
from ingame.runner import _memory_select_to_sss, _select_stage  # noqa: E402

SLIPPI = os.path.join(os.environ["APPDATA"], "Slippi Launcher", "netplay")
RUNS = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\storage\test-runs")

iso = sys.argv[1]
out_png = Path(sys.argv[2])
color = int(sys.argv[3]) if len(sys.argv) > 3 else 4
char = sys.argv[5] if len(sys.argv) > 5 else "fox"

log = lambda m: print(f"  {m}")  # noqa: E731

assert wait_until_no_dolphin(lambda *a, **k: None, log=log), "close Dolphin first"
boot = DolphinBoot(iso, SLIPPI, str(RUNS), log=log)
try:
    boot.prepare()
    boot.launch()
    assert boot.wait_for_pipe(timeout=45), "no input pipe"
    d = Dolphin(boot.pid)
    t0 = time.time()
    while not d.locate() and time.time() - t0 < 20:
        time.sleep(0.4)
    assert d.base is not None, "no MEM1"

    solo = match_setup.patch_one_player(d, log=log)
    p = Pipe(boot.pipe_index)
    assert nav.nav_to_css(d, p, log=log), "CSS nav failed"
    cur = Cursor(d, p)
    sc = StageCursor(d, p)
    nav.wait_css_ready(d, cur, log=log)
    if solo:
        match_setup.force_time_infinite(d, log=log)

    ck = char_ckind(char)
    assert _memory_select_to_sss(d, sc, ck, color, log), "memory select failed"
    assert _select_stage(sc, {"kind": "name", "name": "battlefield"}, None), \
        "stage select failed"

    log("waiting for match…")
    wait_in_game(d, timeout=25.0)
    wait_game_frames(d, 200)          # past READY/GO

    still = len(sys.argv) > 4 and "still" in sys.argv[4]
    if not still:
        # move around so the model deforms: walk right, jump, walk left
        log("moving…")
        p.frame(["SET MAIN 1.000 0.500", "FLUSH"]); time.sleep(0.8)
        p.frame(["SET MAIN 0.500 0.500", "FLUSH"]); time.sleep(0.2)
        p.tap("Y", 0.08); time.sleep(0.7)
        p.frame(["SET MAIN 0.000 0.500", "FLUSH"]); time.sleep(0.6)
        p.frame(["SET MAIN 0.500 0.500", "FLUSH"]); time.sleep(0.4)

        # mid-animation freeze: attack then pause quickly
        p.tap("A", 0.06); time.sleep(0.25)
    if len(sys.argv) > 4 and "strip" in sys.argv[4]:
        # animation strip: frames while moving/attacking (no pause)
        out_png.parent.mkdir(parents=True, exist_ok=True)
        moves = [["SET MAIN 1.000 0.500"], ["PRESS A"], ["RELEASE A"],
                 ["PRESS Y"], ["RELEASE Y"], ["SET MAIN 0.500 0.500"]]
        for n in range(6):
            p.frame(moves[n % len(moves)] + ["FLUSH"])
            time.sleep(0.45)
            png = shot.capture_via_printwindow(boot.pid, max_width=1100) or \
                shot.capture_png(boot.pid, max_width=1100)
            if png:
                f = out_png.with_name(out_png.stem + f"_{n}.png")
                f.write_bytes(png)
                print(f"saved {f}")
        sys.exit(0)

    if not (len(sys.argv) > 4 and "nopause" in sys.argv[4]):
        log("pausing…")
        p.tap("START", 0.1)
        time.sleep(1.2)

    png = shot.capture_via_printwindow(boot.pid, max_width=1100) or \
        shot.capture_png(boot.pid, max_width=1100)
    assert png, "screenshot failed"
    out_png.parent.mkdir(parents=True, exist_ok=True)
    out_png.write_bytes(png)
    print(f"saved {out_png}")
finally:
    try:
        p.close()
    except Exception:
        pass
    boot.cleanup()
