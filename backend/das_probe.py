"""
das_probe.py -- boot DAS-ladder ISOs and check whether a NO-BUTTON (random pool)
DAS pick LOADS INTO A MATCH or breaks. Costumes hang the CSS, but DAS runs at
STAGE LOAD, so we must drive into a match on the DAS stage. Uses the solo engine:
memory-warp CSS->SSS, force-select the DAS stage (no cursor), then watch in-match
health.

Verdict per ISO (from observe.Observer.watch):
  HEALTHY        -> a variant loaded and the match ran (DAS fine at this count)
  HUNG           -> frame counter froze in-game
  NEVER_STARTED  -> never reached in-game within the window (stage load hung)
  CRASHED/ENDED  -> process died / soft-crashed out
A low-count ISO is the control: if even das-64 fails to load, it's the probe/fighter,
not a DAS limit.

Run from backend/ (no other Dolphin emulator open):
  python das_probe.py --stage dreamland                 # globs output/das-dreamland-*.iso
  python das_probe.py --stage dreamland ../output/das-dreamland-512.iso
"""
import argparse
import glob
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH  # noqa: E402
from ingame.boot import DolphinBoot, dolphin_running  # noqa: E402
from ingame.melee_mem import Dolphin  # noqa: E402
from ingame.melee_pipe import Pipe  # noqa: E402
from ingame.melee_css import Cursor  # noqa: E402
from ingame.melee_sss import StageCursor, INTERNAL_STAGE_ID, norm  # noqa: E402
from ingame.observe import Observer  # noqa: E402
from ingame import nav, match_setup  # noqa: E402

RUNS = STORAGE_PATH / "test-runs"
RESULTS = (STORAGE_PATH.parent / "output" / "das-probe-results.txt").resolve()
CKIND = 0x00  # vanilla fighter (DAS stage load is fighter-independent)


def log(m):
    print(m, flush=True)


def probe(iso, stage, hold=None):
    res = {"iso": Path(iso).name, "verdict": "ERROR", "reason": ""}
    # Absolute path: Dolphin's cwd is its exe dir, so a relative ISO would not be
    # found ("died during boot").
    boot = DolphinBoot(str(Path(iso).resolve()), None, str(RUNS), log=log)
    p = None
    try:
        boot.prepare()
        boot.launch()
        if not boot.wait_for_pipe(timeout=60):
            res["verdict"] = "NO-BOOT"
            res["reason"] = "pipe never appeared"
            return res
        d = Dolphin(boot.pid)
        t0 = time.time()
        while not d.locate() and time.time() - t0 < 30:
            if not d.alive():
                res["verdict"] = "CRASH"
                res["reason"] = "died during boot"
                return res
            time.sleep(0.4)
        if d.base is None:
            res["verdict"] = "NO-MEM1"
            return res

        match_setup.patch_one_player(d, log=log)
        p = Pipe(boot.pipe_index)
        if not nav.nav_to_css(d, p, log=log):
            res["verdict"] = "NAV-FAIL"
            res["reason"] = "couldn't reach CSS"
            return res
        nav.wait_css_ready(d, Cursor(d, p), log=log)
        match_setup.force_time_infinite(d)
        match_setup.write_solo_player(d, CKIND, 0)
        match_setup.warp_to_stage_select(d)
        sc = StageCursor(d, p)
        if not sc.wait_for_stage_select(timeout=8):
            res["verdict"] = "SSS-FAIL"
            res["reason"] = "never reached stage select"
            return res
        match_setup.write_solo_player(d, CKIND, 0)  # re-assert after the warp
        sid = INTERNAL_STAGE_ID[norm(stage)]
        if not sc.force_select(sid, hold=hold):
            res["verdict"] = "NO-START"
            res["reason"] = "force_select didn't start the match"
            return res
        verdict, reason, _ = Observer(d).watch(seconds=25.0, min_ingame=4.0)
        res["verdict"] = verdict.upper()
        res["reason"] = reason
        return res
    except Exception as e:  # noqa: BLE001
        res["verdict"] = "EXC"
        res["reason"] = f"{type(e).__name__}: {e}"
        return res
    finally:
        try:
            if p:
                p.close()
        except Exception:
            pass
        boot.cleanup()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="dreamland")
    ap.add_argument("--hold", default=None,
                    help="optional DAS button to hold (default: none = random pool)")
    ap.add_argument("isos", nargs="*")
    args = ap.parse_args()

    isos = args.isos
    if not isos:
        pat = str(STORAGE_PATH.parent / "output" / f"das-{args.stage}-*.iso")
        isos = sorted(glob.glob(pat), key=lambda s: int(Path(s).stem.split("-")[-1]))
    if not isos:
        raise SystemExit(f"no DAS ISOs for stage '{args.stage}'")

    open_dolphins = dolphin_running()
    if open_dolphins:
        log(f"WARNING: a Dolphin EMULATOR is open (pids {open_dolphins}); close it.")

    log(f"probing {len(isos)} DAS ISO(s) on {args.stage} (hold={args.hold or 'none/random'}):")
    results = []
    for iso in isos:
        log("")
        log(f"################ {Path(iso).name} ################")
        r = probe(iso, args.stage, hold=args.hold)
        results.append(r)
        log(f"  -> {r['verdict']}  {r['reason']}")
        time.sleep(4)

    log("")
    log("==================== SUMMARY ====================")
    lines = [f"  {'ISO':<28} {'VERDICT':<14} reason"]
    for r in results:
        lines.append(f"  {r['iso']:<28} {r['verdict']:<14} {r['reason']}")
    table = "\n".join(lines)
    log(table)
    try:
        RESULTS.parent.mkdir(parents=True, exist_ok=True)
        RESULTS.write_text("DAS variant-count probe\n" + table + "\n", encoding="utf-8")
        log(f"\nwrote {RESULTS}")
    except Exception as e:  # noqa: BLE001
        log(f"(could not write results file: {e})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
