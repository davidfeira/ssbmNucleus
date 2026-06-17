"""
count_bisect.py -- pin the TOTAL-costume-count CSS-hang limit. Strips video (so ISO
size is NOT a factor), then imports costumes round-robin across 6 characters,
exporting a checkpoint ISO at total costume counts 450/500/550/600. Boot each
(fps_check) to find where the character-select screen flips from healthy to hung.

Vanilla base = 133 total costumes; we add to reach each checkpoint total.

Run from backend/:  python count_bisect.py
"""
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH  # noqa: E402
from stress_build import run_mexcli, parse_json, smallest_zip, TEST_BASE  # noqa: E402

CHARS = ["Fox", "Falco", "Marth", "C. Falcon", "Roy", "Sheik"]
VANILLA_TOTAL = 133
CHECKPOINT_TOTALS = [450, 500, 550, 600]


def log(m):
    print(m, flush=True)


def main():
    work = (STORAGE_PATH / "test-builds" / "countbisect_proj").resolve()
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    log(f"copying base -> {work}")
    shutil.copytree(TEST_BASE, work)

    freed = 0
    for p in (work / "files").rglob("*"):
        if p.is_file() and p.name.lower().startswith("mv"):
            freed += p.stat().st_size
            p.unlink()
    log(f"stripped video: freed {freed/1024/1024:.0f} MiB")

    proj = str((work / "project.mexproj").resolve())
    zips = {c: smallest_zip(c) for c in CHARS}
    missing = [c for c, z in zips.items() if z is None]
    if missing:
        raise SystemExit(f"no vault zip for {missing}")

    added = 0
    t0 = time.time()
    for total in CHECKPOINT_TOTALS:
        target_added = total - VANILLA_TOTAL
        while added < target_added:
            c = CHARS[added % len(CHARS)]
            cp = run_mexcli(["import-costume", proj, c, str(zips[c])], timeout=300)
            data = parse_json(cp.stdout) or {}
            if not data.get("success"):
                log(f"  import FAILED at added={added} ({c}): {data.get('error') or cp.stderr[:160]}")
                return 1
            added += 1
            if added % 50 == 0:
                log(f"  added {added} (total~{VANILLA_TOTAL+added}) elapsed={time.time()-t0:.0f}s")
        iso = (STORAGE_PATH.parent / "output" / f"count-{total}.iso").resolve()
        iso.parent.mkdir(parents=True, exist_ok=True)
        log(f"== checkpoint total~{total} (added {added}): exporting {iso.name} ==")
        cp = run_mexcli(["export", proj, str(iso), "1.0", "false", "false"], timeout=1800)
        res = parse_json(cp.stdout) or {}
        sz = f"{iso.stat().st_size/1024/1024:.0f} MiB" if iso.exists() else "NO ISO"
        log(f"   export success={res.get('success')} size={sz}")

    shutil.rmtree(work, ignore_errors=True)
    log("DONE — now boot output/count-450/500/550/600.iso with fps_check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
