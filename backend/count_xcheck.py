"""
count_xcheck.py -- CROSS-CHECK the 511 total-costume cap with a DIFFERENT build
composition than count_narrow used, to kill the last confound. count_narrow spread
6 chars [Fox,Falco,Marth,C.Falcon,Roy,Sheik] and reused each char's smallest zip
(duplicate content). This uses:
  * 8 DIFFERENT characters,
  * DISTINCT costume files (each char's zips, in order; cycle only if exhausted),
  * a different distribution (8-way instead of 6-way).
Video stripped so disc size stays out of it. If the CSS-hang flip is STILL exactly
511->512 total, the global count cap is confirmed independent of composition.

Run from backend/:  python count_xcheck.py            # checkpoints 509..513
"""
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH  # noqa: E402
from stress_build import run_mexcli, parse_json, TEST_BASE  # noqa: E402

# Deliberately disjoint from count_narrow's roster:
CHARS = ["Ganondorf", "Samus", "Jigglypuff", "Ice Climbers", "Mario", "Zelda", "Yoshi", "DK"]
VANILLA_TOTAL = 133
DEFAULT_CHECKPOINTS = [509, 510, 511, 512, 513]


def log(m):
    print(m, flush=True)


def main():
    checkpoints = sorted(set(int(a) for a in sys.argv[1:])) or DEFAULT_CHECKPOINTS

    zips = {}
    for c in CHARS:
        zl = sorted((STORAGE_PATH / c).glob("*.zip"))
        if not zl:
            raise SystemExit(f"no vault zips for {c}")
        zips[c] = zl
    log("chars + distinct zips available: " + ", ".join(f"{c}:{len(zips[c])}" for c in CHARS))
    log(f"checkpoints={checkpoints}")

    work = (STORAGE_PATH / "test-builds" / "countxcheck_proj").resolve()
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

    idx = {c: 0 for c in CHARS}
    dup_used = 0
    added = 0
    t0 = time.time()
    for total in checkpoints:
        target = total - VANILLA_TOTAL
        while added < target:
            c = CHARS[added % len(CHARS)]
            zl = zips[c]
            if idx[c] >= len(zl):
                dup_used += 1
            z = zl[idx[c] % len(zl)]
            idx[c] += 1
            cp = run_mexcli(["import-costume", proj, c, str(z.resolve())], timeout=300)
            d = parse_json(cp.stdout) or {}
            if not d.get("success"):
                log(f"  import FAILED added={added} {c} {z.name}: {d.get('error') or cp.stderr[:160]}")
                return 1
            added += 1
            if added % 50 == 0:
                log(f"  added {added} (total~{VANILLA_TOTAL+added}) elapsed={time.time()-t0:.0f}s dup={dup_used}")
        iso = (STORAGE_PATH.parent / "output" / f"count-xcheck-{total}.iso").resolve()
        iso.parent.mkdir(parents=True, exist_ok=True)
        log(f"== total~{total} (added {added}, dup_used={dup_used}): exporting {iso.name} ==")
        cp = run_mexcli(["export", proj, str(iso), "1.0", "false", "false"], timeout=1800)
        r = parse_json(cp.stdout) or {}
        sz = f"{iso.stat().st_size/1024/1024:.0f} MiB" if iso.exists() else "NO ISO"
        log(f"   export success={r.get('success')} size={sz}")

    shutil.rmtree(work, ignore_errors=True)
    log("DONE -- boot: python fps_batch.py " +
        " ".join(f"../output/count-xcheck-{t}.iso" for t in checkpoints))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
