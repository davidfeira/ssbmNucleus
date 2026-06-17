"""
das_ladder.py -- build a ladder of ISOs with increasing DAS-variant counts on ONE
stage, to find whether DAS variants have a fixed COUNT cap analogous to the 512
costume table (docs/MEX_BUILD_LIMITS.md §2). Video is stripped so disc size is held
out of it (the same isolation count_narrow uses) — a break is then count-driven, not
size-driven. Boot each with das_probe.py.

Variant install layout matches das_test_setup.py / blueprints/das.py:
  files/<code>/vanilla.dat   files/<code>/varNNNN.dat ...   files/<code>{ext} = loader

Run from backend/ (when no other mexcli build is running):
  python das_ladder.py                                 # dreamland, default counts
  python das_ladder.py --stage dreamland 64 256 512 768 1024
"""
import argparse
import shutil
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH, BASE_PATH  # noqa: E402
from stress_build import run_mexcli, parse_json  # noqa: E402
from das_test_setup import TEST_BASE, DAS  # noqa: E402

DEFAULT_COUNTS = [64, 256, 512, 768, 1024]


def log(m):
    print(m, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="dreamland")
    ap.add_argument("counts", nargs="*", type=int)
    args = ap.parse_args()
    counts = sorted(set(args.counts or DEFAULT_COUNTS))

    if args.stage not in DAS:
        raise SystemExit(f"unknown stage '{args.stage}'; known: {', '.join(DAS)}")
    code, folder, ext = DAS[args.stage]
    vault = STORAGE_PATH / "das" / folder
    zips = sorted(vault.glob("*.zip"))
    if not zips:
        raise SystemExit(f"no DAS zips in {vault}")

    # Preload the variant .dat payloads once; cycle through them to hit each count.
    payloads = []
    for z in zips:
        try:
            with zipfile.ZipFile(z) as zf:
                dats = [n for n in zf.namelist() if n.lower().endswith(".dat")]
                if dats:
                    payloads.append(zf.read(dats[0]))
        except Exception as e:  # noqa: BLE001
            log(f"  skip {z.name}: {e}")
    if not payloads:
        raise SystemExit("no .dat payloads in the vault zips")
    log(f"{len(payloads)} unique variant payloads (will cycle to reach each count); "
        f"checkpoints={counts}")

    work = (STORAGE_PATH / "test-builds" / "dasladder_proj").resolve()
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    log(f"copying base -> {work}")
    shutil.copytree(TEST_BASE, work)
    files = work / "files"
    proj = str((work / "project.mexproj").resolve())

    freed = 0
    for p in files.rglob("*"):
        if p.is_file() and p.name.lower().startswith("mv"):
            freed += p.stat().st_size
            p.unlink()
    log(f"stripped video: freed {freed/1024/1024:.0f} MiB")

    stage_folder = files / code
    stage_folder.mkdir(exist_ok=True)
    original = files / f"{code}{ext}"
    loader = BASE_PATH / "utility" / "DynamicAlternateStages" / f"{code}{ext}"
    if not loader.exists():
        raise SystemExit(f"DAS loader missing: {loader}")
    if original.exists():
        shutil.copy2(original, stage_folder / "vanilla.dat")  # vanilla variant
    shutil.copy2(loader, original)  # loader replaces the stage file

    placed = 0
    for count in counts:
        while placed < count:
            (stage_folder / f"var{placed:04d}.dat").write_bytes(payloads[placed % len(payloads)])
            placed += 1
        n_dat = len(list(stage_folder.glob("*.dat")))
        iso = (STORAGE_PATH.parent / "output" / f"das-{args.stage}-{count}.iso").resolve()
        iso.parent.mkdir(parents=True, exist_ok=True)
        log(f"== {count} variants (folder has {n_dat} .dat incl vanilla): exporting {iso.name} ==")
        cp = run_mexcli(["export", proj, str(iso), "1.0", "false", "false"], timeout=1800)
        res = parse_json(cp.stdout) or {}
        sz = f"{iso.stat().st_size/1024/1024:.0f} MiB" if iso.exists() else "NO ISO"
        log(f"   export success={res.get('success')} size={sz}")

    shutil.rmtree(work, ignore_errors=True)
    log(f"DONE -- boot with: python das_probe.py --stage {args.stage}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
