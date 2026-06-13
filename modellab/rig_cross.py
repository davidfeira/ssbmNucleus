"""Cross-character rig test: rig a vanilla character model onto Fox's
skeleton with the full v8 pipeline (source visibility drop + _SINGLE
conversion + pose-space retargeting), then import and build a test ISO.

usage: rig_cross.py <src_slug> <SrcCode> [tag]
   ex: rig_cross.py marth PlMs v1

Foreign (non-melee) meshes — GLB/OBJ from the AI path — have no source
skeleton, so no pose retargeting and no cape split; pass the mesh instead
of a source code:
   ex: rig_cross.py pilot --mesh path/to/model.glb v1 [--rot-y 180]
"""
import io
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

BACKEND = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
sys.path.insert(0, str(BACKEND))

EXE = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\utility\tools\HSDLib\HSDRawViewer\bin\Release\net6.0-windows\HSDRawViewer.exe")
FILES = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\storage\test-base\files")
ML = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\modellab")
RK = ML / "rigkits"
VANILLA_ISO = r"C:\Users\david\projects\melee\working\melee-vanilla-v1.02-working.iso"

args = [a for a in sys.argv[1:] if not a.startswith("--")]
src_slug = args[0]
mesh_override = None
rot_y = 0.0
if "--mesh" in sys.argv:
    mesh_override = sys.argv[sys.argv.index("--mesh") + 1]
    args = [a for a in args if a != mesh_override]
    src_code = None
else:
    src_code = args[1]
if "--rot-y" in sys.argv:
    rot_y = float(sys.argv[sys.argv.index("--rot-y") + 1])
    args = [a for a in args if a != sys.argv[sys.argv.index("--rot-y") + 1]]
tag = args[-1] if len(args) > (1 if mesh_override else 2) else "v1"
rig_only = "--rig-only" in sys.argv     # stop after the SMD (fast QA loop)


def joint_symbol(dat_path):
    raw = Path(dat_path).read_bytes()
    for m in re.findall(rb"[\x20-\x7e]{8,}", raw):
        s = m.decode("ascii", "replace")
        if s.endswith("_joint") and "matanim" not in s:
            return s
    raise RuntimeError(f"no joint symbol in {dat_path}")


# 1. source Wait1 pose (frame 0 = the rest pose the game actually shows);
# foreign meshes have no skeleton to repose — bind-vs-bind alignment only
wait = None
if mesh_override is None:
    wait = RK / src_slug / f"{src_slug}_wait1.json"
    if not wait.exists():
        r = subprocess.run(
            [str(EXE), "--dump-pose", str(FILES / f"{src_code}Nr.dat"),
             str(FILES / f"{src_code}AJ.dat"), "Wait1", str(wait), "0"],
            capture_output=True, text=True, timeout=300)
        if not wait.exists():
            sys.exit(f"pose dump failed:\n{r.stdout[-600:]}\n{r.stderr[-600:]}")
        print(f"dumped {wait.name}")

# 2. rig onto fox
from modellab.rig import rig_mesh  # noqa: E402

out_dir = ML / "out" / f"{src_slug}_on_fox"
out_dir.mkdir(parents=True, exist_ok=True)
out_smd = out_dir / f"{src_slug}_{tag}.smd"
acc_dir = out_dir / f"accessory_{tag}"
cape_dyn = RK / src_slug / f"{src_slug}_cape_dynamics.json"
rig_mesh(str(RK / "fox" / "fox_vanilla.smd"),
         mesh_override or str(RK / src_slug / f"{src_slug}_vanilla.smd"),
         str(out_smd), rot_y=rot_y,
         char_code="PlFx", src_char_code=src_code,
         target_pose=(str(RK / "fox" / "fox_wait1.json")
                      if mesh_override is None else None),
         src_pose=str(wait) if wait else None,
         accessory_dir=(str(acc_dir)
                        if cape_dyn.exists() and not mesh_override else None),
         cape_dynamics=(str(cape_dyn)
                        if cape_dyn.exists() and not mesh_override else None))

if rig_only:
    print(f"rig-only: wrote {out_smd}")
    sys.exit(0)

# 3. import over the vanilla Fox costume (skeleton preserved)
base = FILES / "PlFxNr.dat"
out_dat = out_dir / f"PlFx{src_slug.capitalize()}{tag.upper()}.dat"
r = subprocess.run(
    [str(EXE), "--model", "import", str(base), joint_symbol(base),
     str(out_smd), str(out_dat), "--strip-matanim"],
    capture_output=True, text=True, timeout=600)
if r.returncode != 0 or not out_dat.exists():
    sys.exit(f"import failed:\n{r.stdout[-900:]}\n{r.stderr[-900:]}")
print(f"imported {out_dat.name} ({out_dat.stat().st_size} bytes)")

# 3b. attach the mexCostume cloth accessory (real cape physics)
if (acc_dir / "cape.smd").exists():
    attach = json.loads((acc_dir / "attach.json").read_text())["attachBone"]
    acc_dat = out_dir / f"{out_dat.stem}_acc.dat"
    r = subprocess.run(
        [str(EXE), "--accessory", str(out_dat), str(acc_dir / "cape.smd"),
         str(attach), str(acc_dir / "dynamics_local.json"), str(acc_dat)],
        capture_output=True, text=True, timeout=600)
    if r.returncode == 0 and acc_dat.exists():
        out_dat = acc_dat
        print(f"accessory attached (bone {attach}) -> {out_dat.name} "
              f"({out_dat.stat().st_size} bytes)")
    else:
        print(f"WARNING accessory step failed, shipping without cape:\n"
              f"{r.stdout[-500:]}")

# 4. pack as a costume zip (placeholder csp/stc) and build the ISO
src_zip = BACKEND.parent / "storage" / "Fox" / "roundtrip-test-plfxrt.zip"
with zipfile.ZipFile(src_zip) as z:
    csp, stc = z.read("csp.png"), z.read("stc.png")
test_zip = out_dir / f"{src_slug}-{tag}-plfxrt.zip"
with zipfile.ZipFile(test_zip, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("PlFxRtMod.dat", out_dat.read_bytes())
    z.writestr("csp.png", csp)
    z.writestr("stc.png", stc)

os.chdir(BACKEND)
from test_build import build_single_costume_iso  # noqa: E402

out_iso = ML / f"{src_slug}-on-fox-{tag}.iso"
index = build_single_costume_iso(
    vanilla_iso=VANILLA_ISO, character="Fox", skin_zip=str(test_zip),
    out_iso=str(out_iso), progress_cb=lambda p, m: None, log=lambda m: None)
print(f"ISO: {out_iso} | costume index: {index}")
