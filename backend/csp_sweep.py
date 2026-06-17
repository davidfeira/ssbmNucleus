"""
csp_sweep.py -- the realistic re-test of the costume limit WITH CSP compression.

count_xcheck showed uncompressed (csp=1.0) DISTINCT costumes hang the CSS well below
the 512 count cap: 380 full-size CSPs overflow CSS texture RAM. The app normally
AUTO-scales CSP compression with costume count (core.helpers.calculate_auto_compression)
precisely to avoid that. This builds ONE distinct-costume project at a high total, then
exports it at several CSP-compression levels and boots each, to find the level that
makes a high distinct count healthy again -- confirming compression is the real lever
and the ~511 count cap is reachable WITH it.

Exports go in DECREASING csp order on the same project, so each in-place CSP resize
lands at the correct size for that level (136*r x 188*r).

Run from backend/:  python csp_sweep.py            # total 511; csp 1.0 / 0.5 / auto / 0.3
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
TARGET_TOTAL = 511


def log(m):
    print(m, flush=True)


def main():
    target = int(sys.argv[1]) if len(sys.argv) > 1 else TARGET_TOTAL
    added = target - VANILLA_TOTAL
    auto = round(calculate_auto_compression(added), 3)
    csps = sorted({1.0, 0.5, auto, 0.3}, reverse=True)  # decreasing -> sequential resize is correct
    log(f"target total={target} (added {added}); app auto-compression={auto}; csp levels={csps}")

    zips = {c: sorted((STORAGE_PATH / c).glob("*.zip")) for c in CHARS}
    for c in CHARS:
        if not zips[c]:
            raise SystemExit(f"no vault zips for {c}")

    work = (STORAGE_PATH / "test-builds" / "cspsweep_proj").resolve()
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
    n = 0
    t0 = time.time()
    while n < added:
        c = CHARS[n % len(CHARS)]
        zl = zips[c]
        if idx[c] >= len(zl):
            dup += 1
        z = zl[idx[c] % len(zl)]
        idx[c] += 1
        cp = run_mexcli(["import-costume", proj, c, str(z.resolve())], timeout=300)
        d = parse_json(cp.stdout) or {}
        if not d.get("success"):
            log(f"  import FAILED n={n} {c}: {d.get('error') or cp.stderr[:160]}")
            return 1
        n += 1
        if n % 50 == 0:
            log(f"  added {n}/{added} (total~{VANILLA_TOTAL+n}) elapsed={time.time()-t0:.0f}s dup={dup}")
    log(f"imported {n} distinct costumes (dup={dup}) to total~{target}")

    for csp in csps:
        iso = (STORAGE_PATH.parent / "output" / f"cspsweep-{target}-csp{csp:.2f}.iso").resolve()
        iso.parent.mkdir(parents=True, exist_ok=True)
        tag = "  <-- app AUTO" if abs(csp - auto) < 1e-6 else ""
        log(f"== export csp={csp}{tag} -> {iso.name} ==")
        cp = run_mexcli(["export", proj, str(iso), str(csp), "false", "false"], timeout=1800)
        r = parse_json(cp.stdout) or {}
        sz = f"{iso.stat().st_size/1024/1024:.0f} MiB" if iso.exists() else "NO ISO"
        log(f"   export success={r.get('success')} size={sz}")

    shutil.rmtree(work, ignore_errors=True)
    log("DONE -- boot: python fps_batch.py "
        + " ".join(f"../output/cspsweep-{target}-csp{c:.2f}.iso" for c in csps))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
