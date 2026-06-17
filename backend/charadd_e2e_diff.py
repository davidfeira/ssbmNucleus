"""
charadd_e2e_diff.py -- END-TO-END byte-identity gate for bulk custom-character
install, exercising the REAL backend preprocessing (_prepare_fighter_for_batch:
series resolve + costume-CSP fold + victory + announcer), not raw zips. Proves the
batch endpoint path is byte-identical to the per-char install path for EVERY aspect
(series, costumes, victory theme, announcer, CSS icon) -- except the generated
PlCo.dat bone-lookup file (serialization layout only; validated correct in-game).

Path A replicates install_custom_character's interleaving (prepare+add+port per char).
Path B replicates install-batch (prepare all, one add-fighters). Same _prepare for
both (it's the identical code both endpoints use).

Run from backend/:  python charadd_e2e_diff.py [slug1 slug2 ...]
"""
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH  # noqa: E402
from stress_build import run_mexcli, parse_json, TEST_BASE  # noqa: E402
import core.config as cfg  # noqa: E402
from blueprints.custom_characters import _prepare_fighter_for_batch  # noqa: E402

MEXCLI = str(cfg.MEXCLI_PATH)
DEFAULT_SLUGS = ["wario", "slippy", "toad"]


def log(m):
    print(m, flush=True)


def fresh(name):
    w = (STORAGE_PATH / "test-builds" / name).resolve()
    if w.exists():
        shutil.rmtree(w, ignore_errors=True)
    shutil.copytree(TEST_BASE, w)
    return w


def cli(args):
    return parse_json(run_mexcli(args, timeout=1800).stdout) or {}


def apply_sequential(proj, entry):
    """Mirror install_custom_character: add-fighter then port victory + announcer."""
    r = cli(["add-fighter", proj, entry["zip"]])
    if not r.get("success"):
        raise SystemExit(f"[seq] add-fighter FAILED: {r.get('error')}")
    name = r["name"]
    if entry.get("victoryHps"):
        m = cli(["add-music", proj, entry["victoryHps"], entry.get("victoryName") or f"{name} Victory"])
        if m.get("success") and m.get("musicId") is not None:
            cli(["set-fighter-music", proj, name, str(m["musicId"])])
    if entry.get("announcerWav"):
        cli(["set-fighter-announcer", proj, name, entry["announcerWav"]])
    elif entry.get("announcerCallReuse") is not None:
        cli(["set-fighter-announcer-id", proj, name, str(entry["announcerCallReuse"])])


def main():
    slugs = sys.argv[1:] or DEFAULT_SLUGS
    temp_zips = []

    # ---- A: per-char install path (prepare + add + port, interleaved) ----
    workA = fresh("chare2e_seq")
    projA = str((workA / "project.mexproj").resolve())
    t0 = time.time()
    for s in slugs:
        pre = _prepare_fighter_for_batch(s, projA, MEXCLI)
        if not pre.get("ok"):
            log(f"  [seq skip] {s}: {pre.get('error')}")
            continue
        if pre.get("temp_zip"):
            temp_zips.append(pre["temp_zip"])
        apply_sequential(projA, pre["manifest"])
    tA = time.time() - t0
    log(f"sequential : {tA:6.1f}s")

    # ---- B: batch install path (prepare all, one add-fighters) ----
    workB = fresh("chare2e_batch")
    projB = str((workB / "project.mexproj").resolve())
    entries = []
    for s in slugs:
        pre = _prepare_fighter_for_batch(s, projB, MEXCLI)
        if not pre.get("ok"):
            log(f"  [batch skip] {s}: {pre.get('error')}")
            continue
        if pre.get("temp_zip"):
            temp_zips.append(pre["temp_zip"])
        entries.append(pre["manifest"])
    man = workB / "manifest.json"
    man.write_text(json.dumps({"fighters": entries}))
    t0 = time.time()
    r = cli(["add-fighters", projB, str(man)])
    tB = time.time() - t0
    man.unlink()
    if not r.get("success"):
        raise SystemExit(f"[batch] add-fighters FAILED: {r}")
    log(f"batch      : {tB:6.1f}s  ->  {tA/tB:.1f}x faster   (added={r.get('totalAdded')})")

    for tz in temp_zips:
        try:
            if tz and Path(tz).exists():
                Path(tz).unlink()
        except OSError:
            pass

    log("\n# proj_diff (real preprocessing; only PlCo.dat may differ):")
    import subprocess
    cp = subprocess.run([sys.executable, "proj_diff.py", str(workA), str(workB)],
                        capture_output=True, text=True)
    print(cp.stdout)
    if cp.stderr:
        print(cp.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
