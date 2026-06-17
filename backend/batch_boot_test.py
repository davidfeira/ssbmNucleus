"""
batch_boot_test.py -- build a small ISO using the BATCH import command and export it,
so it can be booted (fps_batch) to confirm a batch-built project loads in-game. The
final in-game safety check for batch import before adopting it in the app.

Run from backend/:  python batch_boot_test.py   (then: python fps_batch.py ../output/batch-boot.iso)
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH  # noqa: E402
from stress_build import run_mexcli, parse_json, TEST_BASE  # noqa: E402


def log(m):
    print(m, flush=True)


def main():
    work = (STORAGE_PATH / "test-builds" / "batchboot_proj").resolve()
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(TEST_BASE, work)
    # Strip video to match the proven-healthy count-ladder recipe (full base + added
    # costumes can exceed the disc and place costumes past the boundary).
    freed = 0
    for p in (work / "files").rglob("*"):
        if p.is_file() and p.name.lower().startswith("mv"):
            freed += p.stat().st_size
            p.unlink()
    log(f"stripped video: freed {freed/1024/1024:.0f} MiB")
    proj = str((work / "project.mexproj").resolve())

    plan = {f: [str(z.resolve()) for z in sorted((STORAGE_PATH / f).glob("*.zip"))[:8]]
            for f in ["Ganondorf", "Samus", "Jigglypuff"]}
    man = work / "manifest.json"
    man.write_text(json.dumps(plan))
    r = parse_json(run_mexcli(["import-costumes", proj, str(man)]).stdout) or {}
    log(f"batch import: success={r.get('success')} totalImported={r.get('totalImported')} "
        f"perFighter={r.get('perFighter')}")
    if not r.get("success"):
        raise SystemExit("batch import failed")

    iso = (STORAGE_PATH.parent / "output" / "batch-boot.iso").resolve()
    iso.parent.mkdir(parents=True, exist_ok=True)
    cp = run_mexcli(["export", proj, str(iso), "0.5", "false", "false"], timeout=1800)
    res = parse_json(cp.stdout) or {}
    sz = f"{iso.stat().st_size/1024/1024:.0f} MiB" if iso.exists() else "NO ISO"
    log(f"export: success={res.get('success')} size={sz}  -> {iso}")
    shutil.rmtree(work, ignore_errors=True)
    log("now boot: python fps_batch.py ../output/batch-boot.iso")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
