"""TEMP: extract the 6 legal stages' vanilla .dat files for the stage skin lab.

Creates one temp project from the vanilla ISO, copies the Gr*.dat files into
storage/skinlab_stages/, and cleans up.

Usage (from backend/): python _extract_stage_dats.py "<vanilla.iso>"
"""
import shutil
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND))

from core.config import STORAGE_PATH  # noqa: E402
from test_build import DAS_STAGES, create_temp_project  # noqa: E402

OUT = STORAGE_PATH / "skinlab_stages"


def main():
    vanilla = sys.argv[1]
    OUT.mkdir(parents=True, exist_ok=True)
    proj_dir, _proj = create_temp_project(vanilla, log=lambda m: print(" ", m, flush=True))
    try:
        files_dir = proj_dir / "files"
        for code in DAS_STAGES:
            src = files_dir / f"{code}.dat"
            if not src.exists():
                print(f"MISSING {code}.dat", flush=True)
                continue
            dst = OUT / f"{code}.dat"
            shutil.copy2(src, dst)
            print(f"{code}.dat -> {dst} ({dst.stat().st_size:,} bytes)", flush=True)
    finally:
        shutil.rmtree(proj_dir, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
