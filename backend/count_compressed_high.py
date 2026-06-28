"""
count_compressed_high.py -- build high-count costume ladders with the app's auto
CSP compression. count_compressed proved 512/513 distinct costumes are healthy WITH
compression (so there is NO hard 511/512 count cap). The binding limit is the CSS
texture-RAM budget, and it must be probed separately for offline VS CSS and Slippi
online CSS.

The current Slippi online CSS ladder is healthy through 1500 total costumes; the
ceiling has not been found yet.

Draws DISTINCT costumes across a broad vault roster (char by char) so the data is
genuinely unique (worst case for memory); exports each checkpoint at its own auto
compression. When the ladder exhausts distinct vault costumes it reuses them
round-robin, while keeping every fighter at or below the 255 byte cap.

Run from backend/:  python count_compressed_high.py            # checkpoints 800, 1000
Then probe the exported ladder with:
  python fps_batch.py --mode both ../output/count-comp-800.iso ../output/count-comp-1000.iso
"""
import json
import argparse
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


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("checkpoints", nargs="*", type=int, help="total costume counts to build")
    ap.add_argument(
        "--repeat-smallest",
        action="store_true",
        help="reuse each fighter's smallest zip round-robin instead of consuming all distinct zips first",
    )
    ap.add_argument(
        "--keep-work",
        action="store_true",
        help="leave the temporary project in storage/test-builds/countcomphigh_proj",
    )
    return ap.parse_args()


def main():
    args = parse_args()
    checkpoints = sorted(set(args.checkpoints)) or DEFAULT_CHECKPOINTS

    zips_by_char = {}
    for c in CHARS:
        zips = sorted((STORAGE_PATH / c).glob("*.zip"), key=lambda p: p.stat().st_size)
        zips_by_char[c] = zips[:1] if args.repeat_smallest else sorted(zips)
    distinct_count = sum(len(v) for v in zips_by_char.values())
    mode = "repeat-smallest" if args.repeat_smallest else "distinct-first"
    log(f"{distinct_count} costume zip source(s) across {len(CHARS)} fighters; "
        f"mode={mode}; checkpoints={checkpoints}")
    need = max(checkpoints) - VANILLA_TOTAL
    if not args.repeat_smallest and need > distinct_count:
        log(f"  NOTE: need {need} added but only {distinct_count} distinct; "
            "the rest will cycle round-robin (dup)")

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
    cp = run_mexcli(["list-fighters", proj], timeout=120)
    base_info = parse_json(cp.stdout) or {}
    if not base_info.get("success"):
        log(f"list-fighters FAILED: {base_info.get('error') or cp.stderr[:500]}")
        return 1
    counts = {f["name"]: int(f["costumeCount"]) for f in base_info.get("fighters", [])}
    missing = [c for c in CHARS if c not in counts]
    if missing:
        log(f"missing fighters from project: {missing}")
        return 1
    max_total = sum(counts.values()) + sum(max(0, 255 - counts[c]) for c in CHARS)
    if max(checkpoints) > max_total:
        log(f"  NOTE: max valid total with this roster is {max_total}; "
            "higher checkpoints will stop there")

    dup = 0
    added = 0
    distinct_pos = {c: 0 for c in CHARS}
    dup_pos = {c: 0 for c in CHARS}
    rr = 0

    def next_import():
        nonlocal dup, rr
        # First consume distinct zips, balanced across the roster.
        if not args.repeat_smallest:
            for _ in range(len(CHARS)):
                c = CHARS[rr % len(CHARS)]
                rr += 1
                pos = distinct_pos[c]
                if counts[c] < 255 and pos < len(zips_by_char[c]):
                    distinct_pos[c] += 1
                    counts[c] += 1
                    return c, zips_by_char[c][pos]
        # Then reuse existing zips, still balanced and still respecting 255.
        for _ in range(len(CHARS)):
            c = CHARS[rr % len(CHARS)]
            rr += 1
            pool = zips_by_char[c]
            if counts[c] < 255 and pool:
                z = pool[dup_pos[c] % len(pool)]
                dup_pos[c] += 1
                counts[c] += 1
                dup += 1
                return c, z
        return None

    t0 = time.time()
    for total in checkpoints:
        target = total - VANILLA_TOTAL
        manifest = {}
        while added < target:
            pick = next_import()
            if pick is None:
                log(f"  no valid fighter slots remain at total~{VANILLA_TOTAL+added}; "
                    "all configured fighters reached 255 or have no zips")
                return 1
            c, z = pick
            manifest.setdefault(c, []).append(str(z.resolve()))
            added += 1
        if manifest:
            manifest_path = work / f"import-{total}.json"
            manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            batch_count = sum(len(v) for v in manifest.values())
            log(f"  batch importing {batch_count} -> total~{VANILLA_TOTAL+added} "
                f"elapsed={time.time()-t0:.0f}s dup={dup}")
            cp = run_mexcli(["import-costumes", proj, str(manifest_path)], timeout=7200)
            d = parse_json(cp.stdout) or {}
            if not d.get("success"):
                log(f"  batch import FAILED total={total}: {d.get('error') or cp.stderr[:500]}")
                return 1
        csp = round(calculate_auto_compression(added), 3)
        prefix = "count-rep" if args.repeat_smallest else "count-comp"
        iso = (STORAGE_PATH.parent / "output" / f"{prefix}-{total}.iso").resolve()
        iso.parent.mkdir(parents=True, exist_ok=True)
        log(f"== total~{total} (added {added}, dup={dup}): export csp={csp} (auto) -> {iso.name} ==")
        cp = run_mexcli(["export", proj, str(iso), str(csp), "false", "false"], timeout=3600)
        r = parse_json(cp.stdout) or {}
        sz = f"{iso.stat().st_size/1024/1024:.0f} MiB" if iso.exists() else "NO ISO"
        log(f"   export success={r.get('success')} size={sz}")

    if not args.keep_work:
        shutil.rmtree(work, ignore_errors=True)
    prefix = "count-rep" if args.repeat_smallest else "count-comp"
    log("DONE -- boot: python fps_batch.py --mode both "
        + " ".join(f"../output/{prefix}-{t}.iso" for t in checkpoints))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
