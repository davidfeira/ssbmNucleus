"""
count_compressed.py -- the REALISTIC count-cap test: distinct costumes, 8 different
characters, exported WITH the app's auto CSP-compression (core.helpers.
calculate_auto_compression), around the suspected 511 cap. count_xcheck used csp=1.0
(no compression) so it crashed early on CSP texture RAM -- but real exports always
auto-compress. With CSPs compressed, the CSP-RAM limit is handled, so this isolates
the COUNT/table cap: if it flips 511->512 here, the hard cap is real for real builds.

Exports each checkpoint at its own auto-compression ratio (~0.39 at these counts).

Run from backend/:  python count_compressed.py            # checkpoints 509..513
"""
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH  # noqa: E402
from core.helpers import calculate_auto_compression  # noqa: E402
from stress_build import run_mexcli, parse_json, TEST_BASE  # noqa: E402

CHARS = ["Ganondorf", "Samus", "Jigglypuff", "Ice Climbers", "Mario", "Zelda", "Yoshi", "DK"]
VANILLA_TOTAL = 133
DEFAULT_CHECKPOINTS = [509, 510, 511, 512, 513]


def log(m):
    print(m, flush=True)


def main():
    checkpoints = sorted(set(int(a) for a in sys.argv[1:])) or DEFAULT_CHECKPOINTS

    zips = {c: sorted((STORAGE_PATH / c).glob("*.zip")) for c in CHARS}
    for c in CHARS:
        if not zips[c]:
            raise SystemExit(f"no vault zips for {c}")

    work = (STORAGE_PATH / "test-builds" / "countcomp_proj").resolve()
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
    dup = 0
    added = 0
    t0 = time.time()
    for total in checkpoints:
        target = total - VANILLA_TOTAL
        while added < target:
            c = CHARS[added % len(CHARS)]
            zl = zips[c]
            if idx[c] >= len(zl):
                dup += 1
            z = zl[idx[c] % len(zl)]
            idx[c] += 1
            cp = run_mexcli(["import-costume", proj, c, str(z.resolve())], timeout=300)
            d = parse_json(cp.stdout) or {}
            if not d.get("success"):
                log(f"  import FAILED added={added} {c}: {d.get('error') or cp.stderr[:160]}")
                return 1
            added += 1
            if added % 50 == 0:
                log(f"  added {added} (total~{VANILLA_TOTAL+added}) elapsed={time.time()-t0:.0f}s dup={dup}")
        csp = round(calculate_auto_compression(added), 3)
        iso = (STORAGE_PATH.parent / "output" / f"count-comp-{total}.iso").resolve()
        iso.parent.mkdir(parents=True, exist_ok=True)
        log(f"== total~{total} (added {added}, dup={dup}): export csp={csp} (auto) -> {iso.name} ==")
        cp = run_mexcli(["export", proj, str(iso), str(csp), "false", "false"], timeout=1800)
        r = parse_json(cp.stdout) or {}
        sz = f"{iso.stat().st_size/1024/1024:.0f} MiB" if iso.exists() else "NO ISO"
        log(f"   export success={r.get('success')} size={sz}")

    shutil.rmtree(work, ignore_errors=True)
    log("DONE -- boot: python fps_batch.py "
        + " ".join(f"../output/count-comp-{t}.iso" for t in checkpoints))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
