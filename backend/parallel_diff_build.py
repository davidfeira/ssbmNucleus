"""
parallel_diff_build.py -- build a SEQUENTIAL (single-import, inline decode) project
and a PARALLEL BATCH (import-costumes, parallel decode) project into KEPT dirs, then
run proj_diff to prove the parallel batch output is byte-identical across EVERY
generated file (not just Pl*): CSP .tex/.png, MnSlChr, IfAll, MxDt, PlCo, codes...

Run from backend/:  python parallel_diff_build.py
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH  # noqa: E402
from stress_build import run_mexcli, parse_json, TEST_BASE  # noqa: E402

PLAN_COUNTS = {"Fox": 6, "Falco": 6, "Marth": 6, "Ice Climbers": 4}


def log(m):
    print(m, flush=True)


def fresh(name):
    w = (STORAGE_PATH / "test-builds" / name).resolve()
    if w.exists():
        shutil.rmtree(w, ignore_errors=True)
    shutil.copytree(TEST_BASE, w)
    return w


def main():
    plan = {f: [str(z.resolve()) for z in sorted((STORAGE_PATH / f).glob("*.zip"))[:n]]
            for f, n in PLAN_COUNTS.items()}

    workA = fresh("pdiff_seq")
    projA = str((workA / "project.mexproj").resolve())
    for f, zs in plan.items():
        for z in zs:
            r = parse_json(run_mexcli(["import-costume", projA, f, z]).stdout) or {}
            if not r.get("success"):
                raise SystemExit(f"seq import FAILED {f}: {r.get('error')}")
    log(f"sequential built -> {workA}")

    workB = fresh("pdiff_batch")
    projB = str((workB / "project.mexproj").resolve())
    man = workB / "manifest.json"
    man.write_text(json.dumps(plan))
    r = parse_json(run_mexcli(["import-costumes", projB, str(man)]).stdout) or {}
    if not r.get("success"):
        raise SystemExit(f"batch import FAILED: {r}")
    man.unlink()  # manifest.json is a batch-only artifact; exclude from diff
    log(f"parallel batch built -> {workB}")

    log("\n# proj_diff:")
    import subprocess
    cp = subprocess.run([sys.executable, "proj_diff.py", str(workA), str(workB)],
                        capture_output=True, text=True)
    print(cp.stdout)
    if cp.stderr:
        print(cp.stderr)
    # leave dirs for inspection; caller can rmtree test-builds/pdiff_* after
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
