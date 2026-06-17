"""
charadd_diff_build.py -- prove the BATCH `add-fighters` CLI command is byte-identical
to the SEQUENTIAL per-char command sequence (add-fighter + add-music +
set-fighter-music + set-fighter-announcer). This is the core-feature safety gate for
bulk custom-character import, mirroring parallel_diff_build.py for costumes.

Uses the RAW vault fighter.zip for BOTH paths (no series/costume-zip rewrite -- that
backend logic is identical on both sides, so this isolates the C# fold). Builds into
KEPT dirs and runs proj_diff; every generated file must match.

Run from backend/:  python charadd_diff_build.py [slug1 slug2 ...]
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
DEFAULT_SLUGS = ["wario", "slippy", "toad"]


def log(m):
    print(m, flush=True)


def fresh(name):
    w = (STORAGE_PATH / "test-builds" / name).resolve()
    if w.exists():
        shutil.rmtree(w, ignore_errors=True)
    shutil.copytree(TEST_BASE, w)
    return w


def victory_name(cdir, slug):
    try:
        entry = json.loads((cdir / "fighter.json").read_text(encoding="utf-8"))
        return (entry.get("victoryTheme") or {}).get("name") or f"{slug} Victory"
    except Exception:
        return f"{slug} Victory"


def main():
    slugs = sys.argv[1:] or DEFAULT_SLUGS
    chars = []
    for s in slugs:
        cdir = VAULT / s
        zp = cdir / "fighter.zip"
        if not zp.exists():
            log(f"  [skip] {s}: no fighter.zip")
            continue
        chars.append((s, cdir, zp))
    if not chars:
        raise SystemExit("no usable chars")

    # ---- A: sequential per-char command sequence ----
    workA = fresh("chardiff_seq")
    projA = str((workA / "project.mexproj").resolve())
    t0 = time.time()
    for s, cdir, zp in chars:
        r = parse_json(run_mexcli(["add-fighter", projA, str(zp.resolve())], timeout=1800).stdout) or {}
        if not r.get("success"):
            raise SystemExit(f"[seq] add-fighter {s} FAILED: {r.get('error')}")
        fname = r["name"]
        vt = cdir / "victory_theme.hps"
        if vt.exists():
            m = parse_json(run_mexcli(["add-music", projA, str(vt.resolve()),
                                       victory_name(cdir, s)], timeout=1800).stdout) or {}
            if m.get("success") and m.get("musicId") is not None:
                run_mexcli(["set-fighter-music", projA, fname, str(m["musicId"])], timeout=1800)
        wav = cdir / "announcer.wav"
        if wav.exists():
            run_mexcli(["set-fighter-announcer", projA, fname, str(wav.resolve())], timeout=1800)
    tA = time.time() - t0
    log(f"sequential : {len(chars)} chars in {tA:6.1f}s  ({tA/len(chars):.1f}s/ea)")

    # ---- B: one batch add-fighters ----
    workB = fresh("chardiff_batch")
    projB = str((workB / "project.mexproj").resolve())
    entries = []
    for s, cdir, zp in chars:
        e = {"zip": str(zp.resolve())}
        vt = cdir / "victory_theme.hps"
        if vt.exists():
            e["victoryHps"] = str(vt.resolve())
            e["victoryName"] = victory_name(cdir, s)
        wav = cdir / "announcer.wav"
        if wav.exists():
            e["announcerWav"] = str(wav.resolve())
        entries.append(e)
    man = workB / "manifest.json"
    man.write_text(json.dumps({"fighters": entries}))
    t0 = time.time()
    r = parse_json(run_mexcli(["add-fighters", projB, str(man)], timeout=1800).stdout) or {}
    tB = time.time() - t0
    man.unlink()
    if not r.get("success"):
        raise SystemExit(f"[batch] add-fighters FAILED: {r}")
    log(f"batch      : {len(chars)} chars in {tB:6.1f}s  ({tB/len(chars):.1f}s/ea)  ->  {tA/tB:.1f}x faster")
    log(f"  added={r.get('totalAdded')} failed={r.get('totalFailed')}")

    log("\n# proj_diff (every generated file must match):")
    import subprocess
    cp = subprocess.run([sys.executable, "proj_diff.py", str(workA), str(workB)],
                        capture_output=True, text=True)
    print(cp.stdout)
    if cp.stderr:
        print(cp.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
