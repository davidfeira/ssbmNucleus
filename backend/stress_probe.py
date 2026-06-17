"""
stress_probe.py -- boot a built ISO, load a SOLO match as (ckind, color) via the
backend/ingame engine (no CPU, no cursor), and report whether the costume id
loaded healthy / crashed / hung. Also reads the costume id BACK out of RAM so we
can detect a silent 6-bit wrap (id>=64 -> reads back id & 0x3F) even when the
spammed costumes are visually identical.

One (ckind,color) per process for crash isolation. Exit codes:
  0 healthy   1 crashed   2 hung   3 ended-early   4 setup-fail/never-started

Run from backend/:
  python stress_probe.py --iso ../output/stress-fox-200.iso --ckind 2 --color 64
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH, OUTPUT_PATH  # noqa: E402
from ingame.boot import DolphinBoot  # noqa: E402
from ingame.melee_mem import Dolphin  # noqa: E402
from ingame.melee_pipe import Pipe  # noqa: E402
from ingame.melee_css import Cursor  # noqa: E402
from ingame.melee_sss import StageCursor, INTERNAL_STAGE_ID  # noqa: E402
from ingame.observe import Observer, wait_in_game, wait_game_frames  # noqa: E402
from ingame import nav, match_setup  # noqa: E402
from ingame import screenshot as shot  # noqa: E402

RUNS_ROOT = STORAGE_PATH / "test-runs"
SHOTS = OUTPUT_PATH / "stress-shots"

STATIC_PLAYER = 0x80453080
STATIC_STRIDE = 0xE90
CSS_PLAYERS = 0x80480820


def log(m):
    print(m, flush=True)


def read_costume(d, port=0):
    """Read candidate runtime costume fields. ft+0x44 = Fighter.costume (the
    in-engine costume index). Returns a dict of what each candidate holds."""
    out = {"gobj": None, "ft": None, "ft+0x44": None, "ft+0x619": None,
           "css+0x03": d.u8(CSS_PLAYERS + 0x03)}
    gobj = d.u32(STATIC_PLAYER + STATIC_STRIDE * port + 0xB0)
    out["gobj"] = gobj
    if gobj and 0x80000000 <= gobj < 0x81800000:
        ft = d.u32(gobj + 0x2C)
        out["ft"] = ft
        if ft and 0x80000000 <= ft < 0x81800000:
            out["ft+0x44"] = d.u8(ft + 0x44)
            out["ft+0x619"] = d.u8(ft + 0x619)
    return out


def snap(boot, name):
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
        SHOTS.mkdir(parents=True, exist_ok=True)
        (SHOTS / f"{name}.png").write_bytes(png)
        log(f"  shot -> stress-shots/{name}.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iso", required=True)
    ap.add_argument("--ckind", type=lambda x: int(x, 0), default=2)  # Fox external id
    ap.add_argument("--color", type=lambda x: int(x, 0), required=True)
    ap.add_argument("--stage", default="battlefield")
    ap.add_argument("--hold", default=None, help="DAS button to hold during stage load (e.g. X)")
    ap.add_argument("--watch", type=float, default=12.0)
    ap.add_argument("--shot", action="store_true")
    args = ap.parse_args()

    iso = Path(args.iso)
    if not iso.exists():
        raise SystemExit(f"ISO missing: {iso}")
    RUNS_ROOT.mkdir(parents=True, exist_ok=True)

    result = {"color": args.color, "ckind": args.ckind, "verdict": "setup_fail",
              "reason": "", "costume_read": None}
    code = {"healthy": 0, "crashed": 1, "hung": 2, "ended": 3,
            "never_started": 4, "setup_fail": 4}

    boot = DolphinBoot(str(iso), None, str(RUNS_ROOT), log=log)
    p = None
    try:
        boot.prepare()
        boot.launch()
        if not boot.wait_for_pipe(timeout=45):
            result["reason"] = "input pipe never appeared"
            log("RESULT " + json.dumps(result))
            return code[result["verdict"]]
        d = Dolphin(boot.pid)
        t0 = time.time()
        while not d.locate() and time.time() - t0 < 20:
            if not d.alive():
                result["verdict"] = "crashed"
                result["reason"] = "Dolphin died during boot"
                log("RESULT " + json.dumps(result))
                return code[result["verdict"]]
            time.sleep(0.4)
        if d.base is None:
            result["reason"] = "could not locate MEM1"
            log("RESULT " + json.dumps(result))
            return code[result["verdict"]]

        match_setup.patch_one_player(d, log=log)
        p = Pipe(boot.pipe_index)
        if not nav.nav_to_css(d, p, log=log):
            result["reason"] = "never reached offline CSS"
            log("RESULT " + json.dumps(result))
            return code[result["verdict"]]
        cur = Cursor(d, p)
        nav.wait_css_ready(d, cur, log=log)
        match_setup.force_time_infinite(d, log=log)

        log(f"memory-select ckind=0x{args.ckind:02X} color={args.color} solo...")
        match_setup.write_solo_player(d, args.ckind, args.color)
        sc = StageCursor(d, p)
        landed = False
        for _ in range(8):
            match_setup.warp_to_stage_select(d)
            if sc.wait_for_stage_select(timeout=2.5):
                landed = True
                break
            if not d.alive():
                result["verdict"] = "crashed"
                result["reason"] = "Dolphin died during CSS->SSS warp"
                log("RESULT " + json.dumps(result))
                return code[result["verdict"]]
        if not landed:
            result["reason"] = "CSS->SSS warp did not land (8 tries)"
            log("RESULT " + json.dumps(result))
            return code[result["verdict"]]
        match_setup.write_solo_player(d, args.ckind, args.color)
        if args.stage not in INTERNAL_STAGE_ID:
            args.stage = "battlefield"
        if not sc.force_select(INTERNAL_STAGE_ID[args.stage], hold=args.hold):
            result["reason"] = "force_select returned false"
            log("RESULT " + json.dumps(result))
            return code[result["verdict"]]

        ig = wait_in_game(d, timeout=20.0, log=log)
        if ig:
            wait_game_frames(d, 180)  # past READY/GO
            result["costume_read"] = read_costume(d)
            log(f"costume read-back: {result['costume_read']}")
            if args.shot:
                snap(boot, f"c{args.color:03d}-spawn")
            verdict, reason, _ = Observer(d).watch(seconds=args.watch, require_ingame=True, log=log)
            result["verdict"] = verdict
            result["reason"] = reason
        else:
            # Never reached in-game: distinguish a load-time crash/hang from a
            # navigation failure.
            if not d.alive():
                result["verdict"] = "crashed"
                result["reason"] = "process died during stage load"
            else:
                verdict, reason, _ = Observer(d).watch_health(seconds=6.0, log=log)
                if verdict in ("crashed", "hung"):
                    result["verdict"] = verdict
                    result["reason"] = "during load: " + reason
                else:
                    result["verdict"] = "never_started"
                    result["reason"] = "alive but never reached in-game (load stuck or nav)"
            if args.shot:
                snap(boot, f"c{args.color:03d}-noig")
        log("RESULT " + json.dumps(result))
        return code.get(result["verdict"], 4)
    finally:
        try:
            if p:
                p.close()
        except Exception:
            pass
        boot.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
