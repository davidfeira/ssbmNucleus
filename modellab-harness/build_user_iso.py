"""Build a persistent test ISO from the current roundtrip-test costume zip."""
import os
import sys

BACKEND = r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend"
sys.path.insert(0, BACKEND)
os.chdir(BACKEND)

from test_build import build_single_costume_iso  # noqa: E402

out = sys.argv[1] if len(sys.argv) > 1 else \
    r"C:\Users\david\projects\ssbmNucleus-master\modellab\modellab-bottle-v2.iso"
index = build_single_costume_iso(
    vanilla_iso=r"C:\Users\david\projects\melee\working\melee-vanilla-v1.02-working.iso",
    character="Fox",
    skin_zip=r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\storage\Fox\roundtrip-test-plfxrt.zip",
    out_iso=out,
    progress_cb=lambda p, m: None,
    log=lambda m: None,
)
print("ISO:", out, "| costume index:", index)
