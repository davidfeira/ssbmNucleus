"""
batch_import_test.py -- prove the new `import-costumes` (batch, ONE Save) is
equivalent to N sequential `import-costume` calls, and measure the speedup. This is
the core-feature safety check before adopting batch import in the app: if the costume
tables / files / counts differ at all, batch is NOT safe to adopt.

Run from backend/:  python batch_import_test.py
"""
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH  # noqa: E402
from stress_build import run_mexcli, parse_json, TEST_BASE  # noqa: E402

# Distinct costumes across several fighters (a real mixed batch).
PLAN_COUNTS = {"Fox": 6, "Falco": 6, "Marth": 6, "Ice Climbers": 4}


def log(m):
    print(m, flush=True)


def zips_for(fighter, n):
    return [str(z.resolve()) for z in sorted((STORAGE_PATH / fighter).glob("*.zip"))[:n]]


def counts(proj):
    d = parse_json(run_mexcli(["list-fighters", proj]).stdout) or {}
    return {f["name"]: f["costumeCount"] for f in d.get("fighters", [])}


def costumes(proj, fighter):
    return parse_json(run_mexcli(["get-costumes", proj, fighter]).stdout) or {}


def pl_files(work):
    out = {}
    for p in (work / "files").rglob("Pl*"):
        if p.is_file():
            out[p.name] = p.stat().st_size
    return out


def fresh(name):
    w = (STORAGE_PATH / "test-builds" / name).resolve()
    if w.exists():
        shutil.rmtree(w, ignore_errors=True)
    shutil.copytree(TEST_BASE, w)
    return w


def main():
    plan = {f: zips_for(f, n) for f, n in PLAN_COUNTS.items()}
    for f, zs in plan.items():
        if len(zs) < PLAN_COUNTS[f]:
            raise SystemExit(f"only {len(zs)} zips for {f}, need {PLAN_COUNTS[f]}")
    total = sum(len(zs) for zs in plan.values())
    log(f"plan: {total} distinct costumes across {list(plan)}")

    # --- A: N sequential import-costume ---
    workA = fresh("batchtest_seq")
    projA = str((workA / "project.mexproj").resolve())
    t0 = time.time()
    for f, zs in plan.items():
        for z in zs:
            r = parse_json(run_mexcli(["import-costume", projA, f, z]).stdout) or {}
            if not r.get("success"):
                raise SystemExit(f"sequential import FAILED {f}: {r.get('error')}")
    tA = time.time() - t0
    log(f"sequential : {total} imports in {tA:6.1f}s  ({tA/total:.2f}s/ea)")

    # --- B: one batch import-costumes ---
    workB = fresh("batchtest_batch")
    projB = str((workB / "project.mexproj").resolve())
    manifest = workB / "manifest.json"
    manifest.write_text(json.dumps(plan))
    t0 = time.time()
    r = parse_json(run_mexcli(["import-costumes", projB, str(manifest)]).stdout) or {}
    tB = time.time() - t0
    if not r.get("success"):
        raise SystemExit(f"batch import FAILED: {r}")
    log(f"batch      : {total} imports in {tB:6.1f}s  ({tB/total:.2f}s/ea)  ->  {tA/tB:.1f}x faster")
    log("")

    # --- equivalence checks ---
    cA, cB = counts(projA), counts(projB)
    counts_ok = cA == cB
    log(f"[{'ok' if counts_ok else 'FAIL'}] per-fighter counts match")
    if not counts_ok:
        log(f"    A={cA}\n    B={cB}")

    cos_ok = True
    for f in plan:
        a = json.dumps(costumes(projA, f), sort_keys=True)
        b = json.dumps(costumes(projB, f), sort_keys=True)
        if a != b:
            cos_ok = False
            log(f"    costume-table MISMATCH for {f}")
    log(f"[{'ok' if cos_ok else 'FAIL'}] costume tables (get-costumes) match")

    fA, fB = pl_files(workA), pl_files(workB)
    files_ok = fA == fB
    log(f"[{'ok' if files_ok else 'FAIL'}] costume files in files/ match ({len(fA)} vs {len(fB)})")
    if not files_ok:
        onlyA, onlyB = sorted(set(fA) - set(fB)), sorted(set(fB) - set(fA))
        if onlyA:
            log(f"    only in sequential: {onlyA[:8]}")
        if onlyB:
            log(f"    only in batch:      {onlyB[:8]}")
        szdiff = [n for n in set(fA) & set(fB) if fA[n] != fB[n]]
        if szdiff:
            log(f"    size diffs:         {szdiff[:8]}")

    ok = counts_ok and cos_ok and files_ok
    log("")
    log(f"==> {'PASS — batch == sequential' if ok else 'FAIL — batch differs from sequential'}"
        f"   |   speedup {tA/tB:.1f}x ({tA:.0f}s -> {tB:.0f}s)")
    shutil.rmtree(workA, ignore_errors=True)
    shutil.rmtree(workB, ignore_errors=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
