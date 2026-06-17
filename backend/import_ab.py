"""
import_ab.py -- build the SAME costume plan two ways (sequential import-costume vs
batch import-costumes), export both, so we can boot both and see if the batch path
produces a broken (CSS-hang) build. Diagnostic for the batch-import bug.

Run from backend/:  python import_ab.py
  then: python fps_batch.py ../output/ab-seq.iso ../output/ab-batch.iso
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH  # noqa: E402
from stress_build import run_mexcli, parse_json, TEST_BASE  # noqa: E402

PLAN_COUNTS = {"Fox": 8, "Falco": 8, "Marth": 8}


def log(m):
    print(m, flush=True)


def fresh(name):
    w = (STORAGE_PATH / "test-builds" / name).resolve()
    if w.exists():
        shutil.rmtree(w, ignore_errors=True)
    shutil.copytree(TEST_BASE, w)
    return w


def export(proj, name):
    iso = (STORAGE_PATH.parent / "output" / name).resolve()
    iso.parent.mkdir(parents=True, exist_ok=True)
    cp = run_mexcli(["export", proj, str(iso), "1.0", "false", "false"], timeout=1800)
    ok = (parse_json(cp.stdout) or {}).get("success")
    log(f"  export {name}: success={ok} size={iso.stat().st_size/1024/1024:.0f} MiB")


def main():
    plan = {f: [str(z.resolve()) for z in sorted((STORAGE_PATH / f).glob("*.zip"))[:n]]
            for f, n in PLAN_COUNTS.items()}

    # A: sequential
    wA = fresh("ab_seq")
    pA = str((wA / "project.mexproj").resolve())
    for f, zs in plan.items():
        for z in zs:
            run_mexcli(["import-costume", pA, f, z])
    log("sequential imported")
    export(pA, "ab-seq.iso")

    # B: batch
    wB = fresh("ab_batch")
    pB = str((wB / "project.mexproj").resolve())
    man = wB / "manifest.json"
    man.write_text(json.dumps(plan))
    r = parse_json(run_mexcli(["import-costumes", pB, str(man)]).stdout) or {}
    log(f"batch imported: {r.get('totalImported')}")
    export(pB, "ab-batch.iso")

    # keep projects for file comparison
    log(f"projects kept: {wA}  |  {wB}")
    log("boot: python fps_batch.py ../output/ab-seq.iso ../output/ab-batch.iso")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
