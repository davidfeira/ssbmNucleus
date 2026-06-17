"""
charrem_diff_build.py -- prove the BATCH remove commands (remove-costumes,
remove-stages) are byte-identical to the per-item sequential remove loops. Core-feature
safety gate for bulk removal, mirroring the import diff harnesses.

For each case: build ONE starting project, copy it to two dirs, remove the SAME set
sequentially (A) vs batched (B), then proj_diff. Every generated file must match.

Run from backend/:  python charrem_diff_build.py
"""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH  # noqa: E402
from stress_build import run_mexcli, parse_json, TEST_BASE  # noqa: E402

VAULT_STAGES = STORAGE_PATH / "custom_stages"
STAGE_SLUGS = ["awakening-wood-2", "distant-planet", "edo-town-2", "fichina-2"]


def log(m):
    print(m, flush=True)


def cli(args):
    return parse_json(run_mexcli(args, timeout=1800).stdout) or {}


def mk(name, src=None):
    w = (STORAGE_PATH / "test-builds" / name).resolve()
    if w.exists():
        shutil.rmtree(w, ignore_errors=True)
    shutil.copytree(src or TEST_BASE, w)
    return w


def proj_of(w):
    return str((w / "project.mexproj").resolve())


def diff(a, b, label):
    log(f"\n# {label} proj_diff:")
    cp = subprocess.run([sys.executable, "proj_diff.py", str(a), str(b)],
                        capture_output=True, text=True)
    print(cp.stdout)
    return "byte-identical" in cp.stdout


def test_costumes():
    log("==== COSTUMES ====")
    tmpl = mk("rem_cos_tmpl")
    proj = proj_of(tmpl)
    lf = cli(["list-fighters", proj])
    counts = {f["name"]: f["costumeCount"] for f in lf.get("fighters", [])}
    # pick two fighters with >=4 costumes; remove two non-adjacent indices each
    plan = {}
    for name in ["Fox", "Marth", "Falco", "Captain Falcon"]:
        c = counts.get(name, 0)
        if c >= 4 and len(plan) < 2:
            plan[name] = [c - 1, c - 3]
    if len(plan) < 2:
        raise SystemExit(f"not enough costumes to test: {counts}")
    log(f"plan: {plan}")

    workA = mk("rem_cos_seq", tmpl)
    projA = proj_of(workA)
    for name, idxs in plan.items():
        for idx in sorted(idxs, reverse=True):
            r = cli(["remove-costume", projA, name, str(idx)])
            if not r.get("success"):
                raise SystemExit(f"[seq] remove {name}[{idx}] FAILED: {r.get('error')}")

    workB = mk("rem_cos_batch", tmpl)
    projB = proj_of(workB)
    man = workB / "rm.json"
    man.write_text(json.dumps(plan))
    t0 = time.time()
    r = cli(["remove-costumes", projB, str(man)])
    tB = time.time() - t0
    man.unlink()
    if not r.get("success"):
        raise SystemExit(f"[batch] remove-costumes FAILED: {r}")
    log(f"batch removed {r.get('totalRemoved')} in {tB:.1f}s")
    ok = diff(workA, workB, "costumes")
    for w in (tmpl, workA, workB):
        shutil.rmtree(w, ignore_errors=True)
    return ok


def test_stages():
    log("\n==== STAGES ====")
    tmpl = mk("rem_stg_tmpl")
    proj = proj_of(tmpl)
    entries = []
    for s in STAGE_SLUGS:
        zp = VAULT_STAGES / s / "stage.zip"
        if zp.exists():
            entries.append({"zip": str(zp.resolve())})
    man = tmpl / "add.json"
    man.write_text(json.dumps({"stages": entries}))
    r = cli(["add-stages", proj, str(man)])
    man.unlink()
    if not r.get("success"):
        raise SystemExit(f"add-stages (setup) FAILED: {r}")
    names = [st["name"] for st in r.get("stages", []) if st.get("success")]
    log(f"added stages: {names}")
    # remove a subset (2 of them)
    to_remove = names[:2]
    log(f"removing: {to_remove}")

    workA = mk("rem_stg_seq", tmpl)
    projA = proj_of(workA)
    for nm in to_remove:
        r = cli(["remove-stage", projA, nm])
        if not r.get("success"):
            raise SystemExit(f"[seq] remove-stage {nm} FAILED: {r.get('error')}")

    workB = mk("rem_stg_batch", tmpl)
    projB = proj_of(workB)
    man = workB / "rm.json"
    man.write_text(json.dumps({"stages": to_remove}))
    t0 = time.time()
    r = cli(["remove-stages", projB, str(man)])
    tB = time.time() - t0
    man.unlink()
    if not r.get("success"):
        raise SystemExit(f"[batch] remove-stages FAILED: {r}")
    log(f"batch removed {r.get('totalRemoved')} in {tB:.1f}s")
    ok = diff(workA, workB, "stages")
    for w in (tmpl, workA, workB):
        shutil.rmtree(w, ignore_errors=True)
    return ok


def main():
    c_ok = test_costumes()
    s_ok = test_stages()
    log("\n==================== RESULT ====================")
    log(f"  costumes: {'PASS' if c_ok else 'FAIL'}")
    log(f"  stages:   {'PASS' if s_ok else 'FAIL'}")
    return 0 if (c_ok and s_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
