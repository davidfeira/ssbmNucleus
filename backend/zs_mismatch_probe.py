"""
zs_mismatch_probe.py -- one-off probe: what does the engine actually DO when
Zelda and Sheik have DIFFERENT costume counts?

Build (fresh throwaway project from the vanilla ISO):
    Zelda  += Lilith (slot 5) += white Gardevoir (slot 6)   -> 7 costumes
    Sheik  += blue Chun-Li (slot 5)                          -> 6 costumes
Slot 6 exists for Zelda only (the "unpaired slot" the install UI warns about).
All three customs are visually unmistakable vs vanilla and vs each other.

Checks (one boot, memory-select each, screenshots before/after transform):
    A. Zelda costume 5  -> down-B    paired custom slot (expect Chun-Li Sheik)
    B. Zelda costume 6  -> down-B    UNPAIRED slot -- the actual question
    C. Sheik costume 6 direct        out-of-range costume index for Sheik
Run from backend/:  python zs_mismatch_probe.py [--skip-build]
"""
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.config import STORAGE_PATH, MEXCLI_PATH, PROJECT_ROOT  # noqa: E402
from test_build import create_temp_project, _export  # noqa: E402

sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "tools"))
from mex_bridge import MexManager  # noqa: E402

from ingame.boot import DolphinBoot  # noqa: E402
from ingame.melee_mem import Dolphin  # noqa: E402
from ingame.melee_pipe import Pipe  # noqa: E402
from ingame.melee_css import Cursor  # noqa: E402
from ingame.melee_sss import StageCursor, INTERNAL_STAGE_ID  # noqa: E402
from ingame.observe import Observer, wait_in_game, wait_game_frames  # noqa: E402
from ingame import nav, match_setup  # noqa: E402
from ingame import screenshot as shot  # noqa: E402
from ingame.char_select import ckind  # noqa: E402

ART = PROJECT_ROOT.parent / "tests" / "artifacts" / "zs-mismatch"
VANILLA = r"C:\Users\david\projects\melee\working\melee-vanilla-v1.02-working.iso"
OUT_ISO = STORAGE_PATH / "test-builds" / "zs-mismatch.iso"
RUNS_ROOT = STORAGE_PATH / "test-runs"

ZELDA_SKINS = ["mortecai-lilith.zip",                 # slot 5: red-haired Lilith
               "plzdwh-gardevoir-white-plzdgg.zip"]   # slot 6: white Gardevoir
SHEIK_SKINS = ["chun-plskbu-chunli.zip"]              # slot 5: blue Chun-Li


def log(m):
    print(m, flush=True)


def build():
    proj_dir, proj = create_temp_project(VANILLA, log=log)
    try:
        mex = MexManager(str(MEXCLI_PATH), str(proj))
        for name in ZELDA_SKINS:
            r = mex.import_costume("Zelda", str(STORAGE_PATH / "Zelda" / name))
            log(f"Zelda += {name} -> total {r.get('totalCostumes')}")
        for name in SHEIK_SKINS:
            r = mex.import_costume("Sheik", str(STORAGE_PATH / "Sheik" / name))
            log(f"Sheik += {name} -> total {r.get('totalCostumes')}")
        _export(mex, OUT_ISO, None, log)
        log(f"built {OUT_ISO}")
    finally:
        shutil.rmtree(proj_dir, ignore_errors=True)


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
    else:
        log(f"  shot FAILED for {name}")


def down_b(p):
    # Main-stick y: 0.0 = DOWN, 1.0 = UP (verified live).
    p.frame(["SET MAIN 0.500 0.000", "FLUSH"])
    time.sleep(0.1)
    p.frame(["PRESS B", "FLUSH"])
    time.sleep(0.15)
    p.frame(["RELEASE B", "SET MAIN 0.500 0.500", "FLUSH"])


def run_check(boot, d, p, sc, obs, name, ck, color, first):
    log(f"== {name} (ckind=0x{ck:02x} color={color})")
    if not first:
        if not nav.reset_to_css(d, p, log=log):
            log("  could not reset to the CSS; skipping")
            return
    match_setup.write_solo_player(d, ck, color)
    match_setup.warp_to_stage_select(d)
    if not sc.wait_for_stage_select(timeout=8.0):
        log("  CSS->SSS warp did not land; skipping")
        snap(boot, f"{name}-warpfail")
        return
    match_setup.write_solo_player(d, ck, color)  # re-assert after the scene flip
    started = sc.force_select(INTERNAL_STAGE_ID["battlefield"])
    log(f"  match started: {started}")
    if not started:
        snap(boot, f"{name}-nostart")
        return
    wait_in_game(d, timeout=20.0)
    wait_game_frames(d, 200)          # past READY/GO
    snap(boot, f"{name}-1-spawn")
    log("  down-B (transform)")
    down_b(p)
    wait_game_frames(d, 200)          # ride out the transform animation
    p.center()
    snap(boot, f"{name}-2-transformed")
    log("  down-B (transform back)")
    down_b(p)
    wait_game_frames(d, 200)
    p.center()
    snap(boot, f"{name}-3-back")
    v, reason, _ = obs.watch(seconds=6, require_ingame=True, log=log)
    log(f"  VERDICT: {v} -- {reason}")


def main():
    ART.mkdir(parents=True, exist_ok=True)
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    if "--skip-build" not in sys.argv:
        build()
    if not OUT_ISO.exists():
        raise SystemExit(f"test ISO missing: {OUT_ISO}")

    boot = DolphinBoot(str(OUT_ISO), None, str(RUNS_ROOT), log=log)
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

        solo = match_setup.patch_one_player(d, log=log)
        log(f"solo patch: {solo}")
        p = Pipe(boot.pipe_index)
        obs = Observer(d)
        if not nav.nav_to_css(d, p, log=log):
            raise SystemExit("never reached the offline CSS")
        cur = Cursor(d, p)
        nav.wait_css_ready(d, cur, log=log)
        if solo:
            match_setup.force_time_infinite(d, log=log)

        zk, sk = ckind("zelda"), ckind("sheik")
        run_check(boot, d, p, sc=StageCursor(d, p), obs=obs,
                  name="A-zelda5-paired", ck=zk, color=5, first=True)
        run_check(boot, d, p, sc=StageCursor(d, p), obs=obs,
                  name="B-zelda6-unpaired", ck=zk, color=6, first=False)
        run_check(boot, d, p, sc=StageCursor(d, p), obs=obs,
                  name="C-sheik6-direct", ck=sk, color=6, first=False)
        log("ALL CHECKS DONE")
    finally:
        try:
            if p:
                p.close()
        except Exception:
            pass
        boot.cleanup()


if __name__ == "__main__":
    main()
