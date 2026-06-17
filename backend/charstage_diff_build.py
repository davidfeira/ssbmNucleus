"""
charstage_diff_build.py -- prove the BATCH `add-stages` CLI command is byte-identical
to the SEQUENTIAL per-stage sequence (add-stage + add-music per track +
set-stage-playlist). Core-feature safety gate for bulk custom-stage install, mirroring
charadd_diff_build.py for fighters.

Uses the RAW vault stage.zip + the metadata playlist for both paths. Builds into KEPT
dirs and runs proj_diff; every generated file must match (any divergence is flagged
for the same kind of read-mutate-write analysis we did for PlCo on fighters).

Run from backend/:  python charstage_diff_build.py [slug1 slug2 ...]
"""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH, MEXCLI_PATH  # noqa: E402
from stress_build import run_mexcli, parse_json, TEST_BASE  # noqa: E402

VAULT = STORAGE_PATH / "custom_stages"
MEX = str(Path(MEXCLI_PATH).resolve())
# stages that ship a playlist (exercise the add-music + set-stage-playlist path)
DEFAULT_SLUGS = ["awakening-wood-2", "distant-planet", "edo-town-2"]


def log(m):
    print(m, flush=True)


def fresh(name):
    w = (STORAGE_PATH / "test-builds" / name).resolve()
    if w.exists():
        shutil.rmtree(w, ignore_errors=True)
    shutil.copytree(TEST_BASE, w)
    return w


def metadata_playlist(slug):
    """Return [(hps_path, name, chance), ...] for a vault stage from metadata.json."""
    try:
        meta = json.loads((STORAGE_PATH / "metadata.json").read_text(encoding="utf-8"))
    except Exception:
        return []
    entry = next((s for s in meta.get("custom_stages", [])
                  if isinstance(s, dict) and s.get("slug") == slug), None)
    if not entry:
        return []
    out = []
    sdir = VAULT / slug
    for i, t in enumerate(entry.get("playlist") or []):
        hps = sdir / f"music_{i}.hps"
        if hps.exists() and t.get("name"):
            out.append((hps, t["name"], t.get("chance", 50)))
    return out


def cli(args):
    return parse_json(run_mexcli(args, timeout=1800).stdout) or {}


def main():
    slugs = sys.argv[1:] or DEFAULT_SLUGS
    stages = []
    for s in slugs:
        zp = VAULT / s / "stage.zip"
        if not zp.exists():
            log(f"  [skip] {s}: no stage.zip")
            continue
        stages.append((s, zp, metadata_playlist(s)))
    if not stages:
        raise SystemExit("no usable stages")
    for s, _, pl in stages:
        log(f"  {s}: {len(pl)} track(s)")

    # ---- A: sequential ----
    workA = fresh("stagediff_seq")
    projA = str((workA / "project.mexproj").resolve())
    t0 = time.time()
    for s, zp, pl in stages:
        r = cli(["add-stage", projA, str(zp.resolve())])
        if not r.get("success"):
            raise SystemExit(f"[seq] add-stage {s} FAILED: {r.get('error')}")
        name = r["name"]
        entries = []
        for hps, tname, chance in pl:
            m = cli(["add-music", projA, str(hps.resolve()), tname])
            if m.get("success") and m.get("musicId") is not None:
                entries.append({"musicId": m["musicId"], "chance": chance})
        if entries:
            subprocess.run([MEX, "set-stage-playlist", projA, name],
                           input=json.dumps(entries), capture_output=True, text=True, timeout=900)
    tA = time.time() - t0
    log(f"sequential : {tA:6.1f}s")

    # ---- B: one batch add-stages ----
    workB = fresh("stagediff_batch")
    projB = str((workB / "project.mexproj").resolve())
    man_stages = []
    for s, zp, pl in stages:
        e = {"zip": str(zp.resolve())}
        if pl:
            e["playlist"] = [{"hps": str(hps.resolve()), "name": tname, "chance": chance}
                             for hps, tname, chance in pl]
        man_stages.append(e)
    man = workB / "manifest.json"
    man.write_text(json.dumps({"stages": man_stages}))
    t0 = time.time()
    r = cli(["add-stages", projB, str(man)])
    tB = time.time() - t0
    man.unlink()
    if not r.get("success"):
        raise SystemExit(f"[batch] add-stages FAILED: {r}")
    log(f"batch      : {tB:6.1f}s  ->  {tA/tB:.1f}x faster   "
        f"(added={r.get('totalAdded')}, tracks={r.get('totalTracks')})")

    log("\n# proj_diff (every generated file must match):")
    cp = subprocess.run([sys.executable, "proj_diff.py", str(workA), str(workB)],
                        capture_output=True, text=True)
    print(cp.stdout)
    if cp.stderr:
        print(cp.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
