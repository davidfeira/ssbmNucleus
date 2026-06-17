"""
charadd_timing.py -- Phase-0 timing probe for BULK custom-character import.

Replicates the mexcli command sequence that install_custom_character runs per
char (add-fighter + add-music + set-fighter-music + set-fighter-announcer), timing
EACH command, so we can see how much is the add-fighter recompile vs the porting
recompiles -- i.e. whether a fighter-only batch is enough or we need the full fold.

Run from backend/:  python charadd_timing.py [slug1 slug2 ...]
  (default: a few representative vault chars)
"""
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH  # noqa: E402
from stress_build import run_mexcli, parse_json, TEST_BASE  # noqa: E402

VAULT = STORAGE_PATH / "custom_characters"
DEFAULT_SLUGS = ["wario", "slippy", "toad"]  # all ship victory + announcer


def log(m):
    print(m, flush=True)


def timed(label, args):
    t0 = time.time()
    cp = run_mexcli(args, timeout=1800)
    dt = time.time() - t0
    out = parse_json(cp.stdout) or {}
    ok = out.get("success", False)
    log(f"    {label:<26} {dt:7.2f}s   success={ok}"
        + ("" if ok else f"   ERR={out.get('error') or cp.stderr[:120]}"))
    return dt, out


def main():
    slugs = sys.argv[1:] or DEFAULT_SLUGS
    work = (STORAGE_PATH / "test-builds" / "charadd_timing").resolve()
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(TEST_BASE, work)
    proj = str((work / "project.mexproj").resolve())

    totals = {"add-fighter": 0.0, "add-music": 0.0, "set-fighter-music": 0.0,
              "set-fighter-announcer": 0.0}
    grand = 0.0
    n_ok = 0

    for slug in slugs:
        cdir = VAULT / slug
        zipp = cdir / "fighter.zip"
        if not zipp.exists():
            log(f"  [skip] {slug}: no fighter.zip")
            continue
        log(f"\n  === {slug} ===")

        dt, out = timed("add-fighter", ["add-fighter", proj, str(zipp.resolve())])
        totals["add-fighter"] += dt
        grand += dt
        if not out.get("success"):
            log(f"  [skip rest of {slug}] add-fighter failed")
            continue
        fname = out.get("name", slug)
        n_ok += 1

        vt = cdir / "victory_theme.hps"
        vt_name = None
        try:
            entry = json.loads((cdir / "fighter.json").read_text(encoding="utf-8"))
            vt_name = (entry.get("victoryTheme") or {}).get("name")
        except Exception:
            pass
        if vt.exists():
            dt, mout = timed("add-music", ["add-music", proj, str(vt.resolve()),
                                           vt_name or f"{slug} Victory"])
            totals["add-music"] += dt
            grand += dt
            mid = mout.get("musicId")
            if mout.get("success") and mid is not None:
                dt, _ = timed("set-fighter-music",
                              ["set-fighter-music", proj, fname, str(mid)])
                totals["set-fighter-music"] += dt
                grand += dt

        wav = cdir / "announcer.wav"
        if wav.exists():
            dt, _ = timed("set-fighter-announcer",
                          ["set-fighter-announcer", proj, fname, str(wav.resolve())])
            totals["set-fighter-announcer"] += dt
            grand += dt

    log("\n==================== TOTALS ====================")
    log(f"  chars installed: {n_ok}")
    for k, v in totals.items():
        pct = (v / grand * 100) if grand else 0
        log(f"  {k:<26} {v:7.2f}s   {pct:4.0f}%")
    log(f"  {'GRAND TOTAL':<26} {grand:7.2f}s")
    if n_ok:
        log(f"  per-char avg:               {grand/n_ok:7.2f}s")
        porting = grand - totals["add-fighter"]
        log(f"\n  add-fighter   = {totals['add-fighter']/grand*100:.0f}% of time")
        log(f"  porting (3cmds)= {porting/grand*100:.0f}% of time")
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
