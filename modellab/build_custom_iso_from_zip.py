"""Build a test ISO from ARBITRARY custom-fighter fighter.zip files, without
touching the live storage/custom_characters vault (so a modified fighter.zip can
be verified in-game safely, and concurrent edits to the vault can't collide).

usage: build_custom_iso_from_zip.py <out.iso> <fighter1.zip> [<fighter2.zip> ...]
"""
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
VANILLA_ISO = r"C:\Users\david\projects\melee\working\melee-vanilla-v1.02-working.iso"

out_iso = str(Path(sys.argv[1]).resolve())
fighter_zips = [str(Path(a).resolve()) for a in sys.argv[2:]]

os.chdir(BACKEND)
sys.path.insert(0, str(BACKEND))
from test_build import (create_temp_project, MexManager, MEXCLI_PATH,  # noqa: E402
                        place_custom_fighter_icon, _export)

proj_dir, proj = create_temp_project(VANILLA_ISO, log=print)
try:
    mex = MexManager(str(MEXCLI_PATH), str(proj))
    for fz in fighter_zips:
        res = mex._run_command("add-fighter", str(proj), fz)
        name = res.get("name")
        print(f"added fighter: {name}  ({Path(fz).name})")
        place_custom_fighter_icon(mex, name)
    _export(mex, out_iso, None, print)
    print(f"\nISO: {out_iso}")
finally:
    shutil.rmtree(proj_dir, ignore_errors=True)
