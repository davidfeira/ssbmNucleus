"""Build a single-costume test ISO from a rigged costume DAT, so it can be
checked in-game (low-poly magnifier, projected shadow, normal play). Packages
the DAT with placeholder csp/stc and drops it onto the named fighter in a fresh
throwaway project.

usage: build_test_iso.py <dat> <character> <out_tag>
   ex: build_test_iso.py modellab/out/falcon_glb/PlCaFalconV6LP.dat "Captain Falcon" falcon-lowpoly-v6lp
"""
import os
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
ML = ROOT / "modellab"
VANILLA_ISO = r"C:\Users\david\projects\melee\working\melee-vanilla-v1.02-working.iso"

dat = Path(sys.argv[1]).resolve()
character = sys.argv[2]
tag = sys.argv[3]

# placeholder CSS portrait + stock icon (the in-game model is what we test)
src_zip = ROOT / "storage" / "Fox" / "roundtrip-test-plfxrt.zip"
with zipfile.ZipFile(src_zip) as z:
    csp, stc = z.read("csp.png"), z.read("stc.png")

out_dir = ML / "out" / "iso"
out_dir.mkdir(parents=True, exist_ok=True)
test_zip = (out_dir / f"{tag}.zip").resolve()
with zipfile.ZipFile(test_zip, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr(dat.name, dat.read_bytes())        # PlCa* -> recognized as Falcon
    z.writestr("csp.png", csp)
    z.writestr("stc.png", stc)

out_iso = (ML / f"{tag}.iso").resolve()
os.chdir(BACKEND)
sys.path.insert(0, str(BACKEND))
from test_build import build_single_costume_iso  # noqa: E402

index = build_single_costume_iso(
    vanilla_iso=VANILLA_ISO, character=character, skin_zip=str(test_zip),
    out_iso=str(out_iso), progress_cb=lambda p, m: None, log=print)
print(f"\nISO: {out_iso}\ncostume index (color slot): {index}")
