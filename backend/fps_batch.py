"""
fps_batch.py -- boot a LIST of ISOs in sequence, measure the emulated frame-rate
on the character-select screen of each, and print a HEALTHY / DEGRADED / HUNG
verdict + a summary table. This is the tool that pins the total-costume-count
CSS-hang threshold: boot count-450/500/550/600 and find where CSS fps -> 0.

Every nav step has an internal timeout (nav_to_css 35s, wait_css_ready 10s), so a
hung build can't stall the batch -- it just scores HUNG and we move to the next.

Run from backend/:
  python fps_batch.py ../output/count-450.iso ../output/count-500.iso ...
  python fps_batch.py            # no args -> all output/count-*.iso, ascending
"""
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
from ingame import nav, match_setup  # noqa: E402

RUNS = STORAGE_PATH / "test-runs"
FRAME_COUNTER = 0x80479D60
RESULTS = (STORAGE_PATH.parent / "output" / "count-fps-results.txt").resolve()


def log(m):
    print(m, flush=True)


def measure(d, secs):
    """(fps, (f0, f1)) over `secs` wall-clock; fps None if counter unreadable."""
    f0 = d.u32(FRAME_COUNTER)
    t0 = time.time()
    time.sleep(secs)
    f1 = d.u32(FRAME_COUNTER)
    t1 = time.time()
    if f0 is None or f1 is None:
        return None, (f0, f1)
    df = (f1 - f0) & 0xFFFFFFFF
    return df / (t1 - t0), (f0, f1)


def classify(css_fps):
    if css_fps is None:
        return "HUNG"
    if css_fps < 5:
        return "HUNG"
    if css_fps < 40:
        return "DEGRADED"
    return "HEALTHY"


def probe(iso):
    """Boot one ISO, navigate to the CSS, measure fps there. Returns a result dict."""
    res = {"iso": Path(iso).name, "menu_fps": None, "css_fps": None,
           "verdict": "ERROR", "note": ""}
    # Absolute: Dolphin launches with cwd=<exe dir>, so a relative ISO path would
    # resolve against the Slippi folder and "die during boot" (file not found).
    p_iso = Path(iso).resolve()
    if not p_iso.exists():
        # Don't hand Dolphin a missing file (it exits ~4s with code 3, which looks
        # exactly like a crash). output/ is auto-cleaned, so ISOs can vanish.
        res["verdict"] = "MISSING"
        res["note"] = "ISO file not found (output/ is auto-cleaned?)"
        return res
    boot = DolphinBoot(str(p_iso), None, str(RUNS), log=log)
    p = None
    try:
        boot.prepare()
        boot.launch()
        if not boot.wait_for_pipe(timeout=60):
            res["verdict"] = "NO-BOOT"
            res["note"] = "pipe never appeared (crash/abort during disc load)"
            return res
        d = Dolphin(boot.pid)
        t0 = time.time()
        while not d.locate() and time.time() - t0 < 30:
            if not d.alive():
                res["verdict"] = "CRASH"
                res["note"] = "process died during boot"
                return res
            time.sleep(0.4)
        if d.base is None:
            res["verdict"] = "NO-MEM1"
            res["note"] = "MEM1 base never resolved"
            return res

        mfps, _ = measure(d, 3.0)
        res["menu_fps"] = round(mfps, 1) if mfps is not None else None

        match_setup.patch_one_player(d, log=log)
        p = Pipe(boot.pipe_index)
        reached = nav.nav_to_css(d, p, log=log)
        if not reached:
            # The menu->CSS hop advances the frame counter; a hang before/at the
            # transition shows up as a frozen counter here too.
            cfps, ctr = measure(d, 4.0)
            res["css_fps"] = round(cfps, 1) if cfps is not None else None
            res["verdict"] = "HUNG" if (cfps is not None and cfps < 5) else "NAV-FAIL"
            res["note"] = f"nav_to_css failed; counter {ctr}"
            return res

        nav.wait_css_ready(d, Cursor(d, p), log=log)
        # The costume preload is what hangs; give the CSS a moment to either reach
        # steady 60 fps or freeze, then measure a clean 5 s window.
        time.sleep(2.0)
        cfps, ctr = measure(d, 5.0)
        res["css_fps"] = round(cfps, 1) if cfps is not None else None
        res["verdict"] = classify(cfps)
        if cfps is None:
            res["note"] = f"counter unreadable {ctr}"
        return res
    except Exception as e:  # noqa: BLE001 - want the batch to survive any single ISO
        res["verdict"] = "EXC"
        res["note"] = f"{type(e).__name__}: {e}"
        return res
    finally:
        try:
            if p:
                p.close()
        except Exception:
            pass
        boot.cleanup()


def main():
    isos = sys.argv[1:]
    if not isos:
        out = STORAGE_PATH.parent / "output"
        isos = sorted(glob.glob(str(out / "count-*.iso")))
    if not isos:
        raise SystemExit("no ISOs given and no output/count-*.iso found")

    open_dolphins = dolphin_running()
    if open_dolphins:
        log(f"WARNING: a Dolphin EMULATOR is already open (pids {open_dolphins}). "
            f"It steals input focus -- close it or results are unreliable.")

    log(f"probing {len(isos)} ISO(s):")
    for i in isos:
        log(f"  - {Path(i).name}")

    results = []
    for iso in isos:
        log("")
        log(f"################ {Path(iso).name} ################")
        r = probe(iso)
        results.append(r)
        log(f"  -> {r['verdict']}  (menu={r['menu_fps']} css={r['css_fps']})  {r['note']}")
        time.sleep(4)

    log("")
    log("==================== SUMMARY ====================")
    lines = [f"  {'ISO':<22} {'VERDICT':<9} {'CSS fps':>8} {'MENU fps':>9}  note"]
    for r in results:
        lines.append(f"  {r['iso']:<22} {r['verdict']:<9} "
                     f"{str(r['css_fps']):>8} {str(r['menu_fps']):>9}  {r['note']}")
    table = "\n".join(lines)
    log(table)

    try:
        RESULTS.parent.mkdir(parents=True, exist_ok=True)
        with open(RESULTS, "w", encoding="utf-8") as f:
            f.write("count-limit CSS fps probe\n")
            f.write(table + "\n")
        log(f"\nwrote {RESULTS}")
    except Exception as e:  # noqa: BLE001
        log(f"(could not write results file: {e})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
