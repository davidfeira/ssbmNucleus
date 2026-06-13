"""Rig a foreign mesh (GLB/OBJ from the AI path) onto ANY target character's
skeleton, preview it, and optionally import + render the textured DAT.

Generalizes rig_cross's GLB path off Fox: a realistic human rigs FAR better onto
a human-proportioned target (Captain Falcon) than onto Fox's stocky cartoon
build (huge head, short limbs) where the joints can't line up.

usage: rig_glb.py <glb> <target_slug> <PlCode> [tag] [--rot-y N]
                  [--rig-only | --textured]
   ex: rig_glb.py modellab/foxtest-pilot.glb falcon PlCa v1
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
EXE = ROOT / ("utility/tools/HSDLib/HSDRawViewer/bin/Release/"
              "net6.0-windows/HSDRawViewer.exe")
FILES = ROOT / "storage/test-base/files"
ML = ROOT / "modellab"
RK = ML / "rigkits"

args = [a for a in sys.argv[1:] if not a.startswith("--")]
glb, slug, plcode = args[0], args[1], args[2]
tag = args[3] if len(args) > 3 else "v1"
rot_y = float(sys.argv[sys.argv.index("--rot-y") + 1]) if "--rot-y" in sys.argv else 0.0
rig_only = "--rig-only" in sys.argv
textured = "--textured" in sys.argv


def joint_symbol(dat_path):
    for m in re.findall(rb"[\x20-\x7e]{8,}", Path(dat_path).read_bytes()):
        s = m.decode("ascii", "replace")
        if s.endswith("_joint") and "matanim" not in s:
            return s
    raise RuntimeError(f"no joint symbol in {dat_path}")


# rig kit (export from the vanilla costume once)
kit = RK / slug / f"{slug}_vanilla.smd"
base = FILES / f"{plcode}Nr.dat"
if not kit.exists():
    kit.parent.mkdir(parents=True, exist_ok=True)
    print(f"exporting {slug} rig kit...")
    subprocess.run([str(EXE), "--model", "export", str(base),
                    joint_symbol(base), str(kit)],
                   capture_output=True, text=True, timeout=300)
    if not kit.exists():
        sys.exit("rig kit export failed")

from modellab.rig import rig_mesh  # noqa: E402

out_dir = ML / "out" / f"{slug}_glb"
out_dir.mkdir(parents=True, exist_ok=True)
out_smd = out_dir / f"{slug}_{tag}.smd"
rig_mesh(str(kit), glb, str(out_smd), rot_y=rot_y,
         char_code=plcode, src_char_code=None)
print(f"rigged -> {out_smd}")

# wait-pose preview (the rig kit's own Wait1)
wait = RK / slug / f"{slug}_wait1.json"
if wait.exists():
    subprocess.run([sys.executable, str(ML / "preview_rigged.py"), str(out_smd),
                    str(wait), str(ML / "shots" / f"{slug}_{tag}_wait.png")],
                   timeout=180)
    print(f"wait preview -> shots/{slug}_{tag}_wait.png")

if rig_only:
    sys.exit(0)

# import onto the vanilla costume (skeleton preserved) + textured render
out_dat = out_dir / f"{plcode}{slug.capitalize()}{tag.upper()}.dat"
r = subprocess.run([str(EXE), "--model", "import", str(base), joint_symbol(base),
                    str(out_smd), str(out_dat), "--strip-matanim"],
                   capture_output=True, text=True, timeout=600)
if not out_dat.exists():
    sys.exit(f"import failed:\n{r.stdout[-800:]}\n{r.stderr[-600:]}")
print(f"imported {out_dat.name} ({out_dat.stat().st_size} bytes)")

from render_dat import render_dat  # noqa: E402

csp = ML / "shots" / f"{slug}_{tag}_textured.png"
if render_dat(out_dat, csp):
    print(f"textured render -> {csp}")
