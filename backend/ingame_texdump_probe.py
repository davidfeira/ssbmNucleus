"""ingame_texdump_probe.py -- boot the scrambled Ryu costume (corrupt plcagr01 on
Captain Falcon, costume 6) and DUMP every texture the game actually uploads, so we
can see whether the gi-atlas/face are used and (next step) which geometry samples
them. Solo memory-load, no CPU, no cursor (backend/ingame). Run from backend/.

Copies Dolphin's Dump/Textures out to scratch BEFORE the throwaway User dir is
wiped, and grabs an in-game screenshot.
"""
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.config import STORAGE_PATH, PROJECT_ROOT  # noqa: E402
from ingame.boot import DolphinBoot, _patch_gfx_textures  # noqa: E402
from ingame.melee_mem import Dolphin  # noqa: E402
from ingame.melee_pipe import Pipe  # noqa: E402
from ingame.melee_css import Cursor  # noqa: E402
from ingame.melee_sss import StageCursor, INTERNAL_STAGE_ID  # noqa: E402
from ingame.observe import wait_in_game, wait_game_frames  # noqa: E402
from ingame import nav, match_setup  # noqa: E402
from ingame import screenshot as shot  # noqa: E402

SCRATCH = Path(r"C:\Users\david\AppData\Local\Temp\claude\C--Users-david-projects-ssbmNucleus-master\c80120d9-81bd-4edc-ab41-8ba35bf4665a\scratchpad")
OUT = SCRATCH / "texdump"
RUNS_ROOT = STORAGE_PATH / "test-runs"
DEFAULT_ISO = PROJECT_ROOT / "output" / "harness-test.iso"

FALCON_CKIND = 0x00
COSTUME = 6


def log(m):
    print(m, flush=True)


def main():
    iso = DEFAULT_ISO
    if "--iso" in sys.argv:
        iso = Path(sys.argv[sys.argv.index("--iso") + 1])
    if not iso.exists():
        raise SystemExit(f"ISO missing: {iso}")
    OUT.mkdir(parents=True, exist_ok=True)
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)

    # optional pre-seeded Load/Textures dir for the magenta-swap stage
    load_seed = None
    if "--load-seed" in sys.argv:
        load_seed = sys.argv[sys.argv.index("--load-seed") + 1]

    boot = DolphinBoot(str(iso), None, str(RUNS_ROOT), hires_textures=bool(load_seed),
                       load_seed=load_seed, clean_osd=True, log=log)
    p = None
    try:
        boot.prepare()
        # turn ON texture dumping in the throwaway GFX.ini (and keep hires on so a
        # seeded Load/Textures swap is honoured)
        _patch_gfx_textures(str(boot.user_dir), dump=True, hires=True)
        log(f"DumpTextures=True in {boot.user_dir}\\Config\\GFX.ini")

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
            raise SystemExit("never reached the offline CSS")
        cur = Cursor(d, p)
        nav.wait_css_ready(d, cur, log=log)
        match_setup.force_time_infinite(d, log=log)

        log(f"memory-select Falcon (ckind=0x{FALCON_CKIND:02X}) costume {COSTUME} solo...")
        match_setup.write_solo_player(d, FALCON_CKIND, COSTUME)
        match_setup.warp_to_stage_select(d)
        sc = StageCursor(d, p)
        if not sc.wait_for_stage_select(timeout=8.0):
            raise SystemExit("CSS->SSS warp did not land")
        match_setup.write_solo_player(d, FALCON_CKIND, COSTUME)
        if not sc.force_select(INTERNAL_STAGE_ID["battlefield"]):
            raise SystemExit("match never started")
        log("match started on Battlefield")

        wait_in_game(d, timeout=20.0)
        wait_game_frames(d, 240)   # past READY/GO; let textures upload+dump
        # readback player to confirm
        try:
            blk = match_setup.CSS_PLAYERS if hasattr(match_setup, "CSS_PLAYERS") else None
        except Exception:
            blk = None
        # hold a bit more so all costume textures get dumped
        time.sleep(4.0)
        png = shot.capture_via_printwindow(boot.pid, max_width=1100) or shot.capture_png(boot.pid, max_width=1100)
        if png:
            (OUT / "ingame.png").write_bytes(png)
            log(f"shot -> {OUT}\\ingame.png")

        # copy the dumped textures OUT before cleanup wipes the throwaway User dir
        dump_dir = boot.user_dir / "Dump" / "Textures"
        if dump_dir.is_dir():
            dest = OUT / "Dump_Textures"
            if dest.exists():
                shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(dump_dir, dest)
            n = len(list(dest.rglob("*.png")))
            log(f"copied {n} dumped textures -> {dest}")
        else:
            log(f"NO dump dir at {dump_dir}")
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
