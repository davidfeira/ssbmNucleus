"""Replicate Lyn's ponytail physics accessory onto the 4 recolor costumes.

Same skeleton as the base (PlLyNr), so reuse the base bind-pose + Roy cape params;
per-recolor we only export that costume's mesh+atlas, strip the ponytail, and
attach a fresh accessory. Outputs PlLy<col>_hairacc.dat per recolor + a body
render for offline QA. Run from modellab/.
"""
import glob
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:/Users/david/projects/ssbmNucleus-master")
TMP = ROOT / "tmp_lyntrail"
EXE = ROOT / "ssbmNucleus/utility/tools/HSDLib/HSDRawViewer/bin/Release/net6.0-windows/HSDRawViewer.exe"
BIND = TMP / "lyn_bind.json"          # base skeleton bind pose (shared)
PARAMS = TMP / "roy_cape_params.json"  # Roy cape dyn params (shared)
HAIR_BONES = "46,47,48,49,50,56"
ATTACH = "24"

# costume -> joint root symbol
COSTUMES = {
    "Rd": "PlyEmblem5KRe_Share_joint",
    "Bu": "PlyEmblem5KBu_Share_joint",
    "Gr": "PlyEmblem5KGr_Share_joint",
    "Ye": "PlyEmblem5KYe_Share_joint",
}


def run(*args, **kw):
    r = subprocess.run([str(a) for a in args], capture_output=True, text=True,
                       timeout=600, **kw)
    return r


def main():
    for col, root_sym in COSTUMES.items():
        d = TMP / "recolors" / col
        dat = d / f"PlLy{col}.dat"
        smd = d / "lyn.smd"
        print(f"\n=== {col} ({root_sym}) ===")

        # 1. export mesh + atlas
        r = run(EXE, "--model", "export", dat, root_sym, smd)
        if "SUCCESS" not in r.stdout:
            print(f"  EXPORT FAILED:\n{r.stdout[-400:]}"); continue
        atlases = sorted(glob.glob(str(d / "Texture_*.png")),
                         key=lambda p: -Path(p).stat().st_size)
        if not atlases:
            print("  no atlas exported"); continue
        atlas = atlases[0]

        # 2. strip ponytail tris from the body (lossless re-encode)
        body = d / f"PlLy{col}_nohair.dat"
        r = run(EXE, "--remove-tris-by-bone", dat, root_sym, "0", HAIR_BONES, body)
        if "SUCCESS" not in r.stdout:
            print(f"  REMOVE FAILED:\n{r.stdout[-400:]}"); continue
        print(f"  {r.stdout.strip().splitlines()[-1]}")

        # 3. build accessory (reuse base bind + params; this recolor's mesh+atlas)
        accdir = d / "acc_hair"
        r = run(sys.executable, ROOT / "ssbmNucleus/modellab/build_lyn_hair_accessory.py",
                smd, BIND, PARAMS, atlas, accdir)
        if r.returncode != 0:
            print(f"  ACCESSORY BUILD FAILED:\n{r.stdout[-400:]}{r.stderr[-400:]}"); continue
        print(f"  {r.stdout.strip().splitlines()[-1]}")

        # 4. attach accessory
        out = d / f"PlLy{col}_hairacc.dat"
        r = run(EXE, "--accessory", body, accdir / "cape.smd", ATTACH,
                accdir / "dynamics_local.json", out)
        if "SUCCESS" not in r.stdout:
            print(f"  ATTACH FAILED:\n{r.stdout[-400:]}"); continue
        print(f"  {r.stdout.strip().splitlines()[-1]}")

        # 5. QA render of the body (ponytail should be gone, textures intact)
        r = run(EXE, "--csp", body, d / f"PlLy{col}_nohair.png")
        print(f"  body render: {'ok' if (d / f'PlLy{col}_nohair.png').exists() else 'FAILED'}")
        print(f"  -> {out.name} ({out.stat().st_size} bytes)" if out.exists() else "  NO OUTPUT")


if __name__ == "__main__":
    main()
