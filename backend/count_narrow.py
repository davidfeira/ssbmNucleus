"""
count_narrow.py -- narrow the total-costume-count CSS-hang threshold inside the
500 (healthy) .. 550 (hung) bracket found by count_bisect/fps_batch. Same method:
strip video (size out of the picture), import round-robin across 6 chars, export a
checkpoint ISO at each total in CHECKPOINT_TOTALS. 512 is bracketed directly (it's
a suspiciously round, table-sized number). Boot each with fps_batch to find the
lowest total that hangs.

Run from backend/:
  python count_narrow.py                 # default checkpoints (around 512)
  python count_narrow.py 505 510 515 ...  # custom totals
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
DEFAULT_CHECKPOINTS = [505, 510, 512, 515, 520, 525, 530]


def log(m):
    print(m, flush=True)


def main():
    checkpoints = [int(a) for a in sys.argv[1:]] or DEFAULT_CHECKPOINTS
    checkpoints = sorted(set(checkpoints))
    log(f"checkpoints (total costumes): {checkpoints}")

    work = (STORAGE_PATH / "test-builds" / "countnarrow_proj").resolve()
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
    for total in checkpoints:
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
    log(f"DONE -- now: python fps_batch.py " +
        " ".join(f"../output/count-{t}.iso" for t in checkpoints))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
