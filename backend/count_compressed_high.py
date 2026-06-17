"""
count_compressed_high.py -- pin the REAL high ceiling of the costume limit with the
app's auto CSP-compression. count_compressed proved 512/513 distinct costumes are
healthy WITH compression (so there is NO hard 511/512 count cap). The binding limit
is the CSS texture-RAM budget, which the app's auto-compression manages; the formula
(core.helpers.calculate_auto_compression) predicts the ceiling -- where even r=0.1
can't save it -- around total ~1150. This empirically checks high totals.

Draws DISTINCT costumes across a broad vault roster (char by char) so the data is
genuinely unique (worst case for memory); exports each checkpoint at its own auto
compression. Per-char counts stay well under the 255 byte cap.

Run from backend/:  python count_compressed_high.py            # checkpoints 800, 1000
"""
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH  # noqa: E402
from core.helpers import calculate_auto_compression  # noqa: E402
from stress_build import run_mexcli, parse_json, TEST_BASE  # noqa: E402

# Broad standard roster (excludes Kirby's special cap-costume handling, G&W, tiny pools).
CHARS = ["Falco", "C. Falcon", "Marth", "Fox", "Ganondorf", "Samus", "Roy",
         "Jigglypuff", "Sheik", "Ice Climbers", "Mario", "Zelda", "Yoshi", "DK",
         "Bowser", "Pichu", "Dr. Mario", "Peach", "Pikachu", "Link", "Ness",
         "Luigi", "Mewtwo", "Young Link"]
VANILLA_TOTAL = 133
DEFAULT_CHECKPOINTS = [800, 1000]


def log(m):
    print(m, flush=True)


def main():
    checkpoints = sorted(set(int(a) for a in sys.argv[1:])) or DEFAULT_CHECKPOINTS

    # Flat list of distinct costume zips, char by char (each tagged with its fighter).
    flat = []
    for c in CHARS:
        for z in sorted((STORAGE_PATH / c).glob("*.zip")):
            flat.append((c, z))
    log(f"{len(flat)} distinct costume zips across {len(CHARS)} fighters; checkpoints={checkpoints}")
    need = max(checkpoints) - VANILLA_TOTAL
    if need > len(flat):
        log(f"  NOTE: need {need} added but only {len(flat)} distinct; the rest will cycle (dup)")

    work = (STORAGE_PATH / "test-builds" / "countcomphigh_proj").resolve()
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

    dup = 0
    added = 0
    t0 = time.time()
    for total in checkpoints:
        target = total - VANILLA_TOTAL
        while added < target:
            if added < len(flat):
                c, z = flat[added]
            else:
                c, z = flat[added % len(flat)]
                dup += 1
            cp = run_mexcli(["import-costume", proj, c, str(z.resolve())], timeout=300)
            d = parse_json(cp.stdout) or {}
            if not d.get("success"):
                log(f"  import FAILED added={added} {c}: {d.get('error') or cp.stderr[:160]}")
                return 1
            added += 1
            if added % 100 == 0:
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
