"""Retake all 5 of Lyn's CSPs in the Roy standing pose (WalkBrake f9).

Lyn shares Roy's Emblem skeleton, so we render with Roy's vanilla AJ (Lyn's
clone AJ lacks WalkBrake) + a Lyn-adjusted pose (empty hiddenNodes so her
ponytail + hands show, vs Roy's cape-hiding nodes). Rendered from the ORIGINAL
full models (ponytail in the body) so portraits look complete; the in-game
costume DATs (hair accessory) are untouched. Upgrades Lyn to the current
136x188 SD + 544x752 HD convention. Run from modellab/.
"""
import io
import subprocess
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(r"C:/Users/david/projects/ssbmNucleus-master")
TMP = ROOT / "tmp_lyntrail"
VAULT = ROOT / "ssbmNucleus/storage/custom_characters/lyn"
EXE = ROOT / "ssbmNucleus/utility/tools/HSDLib/HSDRawViewer/bin/Release/net6.0-windows/HSDRawViewer.exe"
AJ = ROOT / "ssbmNucleus/storage/test-base/files/PlFeAJ.dat"   # Roy AJ (has WalkBrake)
POSE = TMP / "lyn_standing.yml"
RENDER_CWD = TMP / "csprender"
RENDER_CWD.mkdir(exist_ok=True)

# costume index -> (stem, original full-model DAT with ponytail)
COSTUMES = [
    ("PlLyNr", TMP / "PlLyNr.dat"),
    ("PlLyRd", TMP / "recolors/Rd/PlLyRd.dat"),
    ("PlLyBu", TMP / "recolors/Bu/PlLyBu.dat"),
    ("PlLyGr", TMP / "recolors/Gr/PlLyGr.dat"),
    ("PlLyYe", TMP / "recolors/Ye/PlLyYe.dat"),
]


def render(dat, out, scale=None):
    if out.exists():
        out.unlink()
    cmd = [str(EXE), "--csp", str(dat), str(out)]
    if scale:
        cmd += ["--scale", str(scale)]
    cmd += [str(POSE), str(AJ)]
    subprocess.run(cmd, cwd=RENDER_CWD, capture_output=True, text=True, timeout=240)
    return out.exists()


def put_in_zip(zip_path, member, data):
    zin = zipfile.ZipFile(zip_path, "r")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zin.infolist():
            zo.writestr(it, data if it.filename == member else zin.read(it.filename))
    zin.close()
    zip_path.write_bytes(buf.getvalue())


def put_inner_csp(fighter_zip, stem, sd_bytes):
    """Replace csp.png inside fighter.zip's inner <stem>.zip."""
    zin = zipfile.ZipFile(fighter_zip, "r")
    inner = zipfile.ZipFile(io.BytesIO(zin.read(f"{stem}.zip")))
    ib = io.BytesIO()
    with zipfile.ZipFile(ib, "w", zipfile.ZIP_DEFLATED) as zo:
        for n in inner.namelist():
            zo.writestr(n, sd_bytes if n == "csp.png" else inner.read(n))
    new_inner = ib.getvalue()
    zin.close()
    put_in_zip(fighter_zip, f"{stem}.zip", new_inner)


for i, (stem, src) in enumerate(COSTUMES):
    sd = RENDER_CWD / f"{stem}_sd.png"
    hd = RENDER_CWD / f"{stem}_hd.png"
    ok_sd = render(src, sd, scale=1)
    ok_hd = render(src, hd, scale=4)
    if not (ok_sd and ok_hd):
        print(f"{stem}: RENDER FAILED sd={ok_sd} hd={ok_hd}")
        continue
    sd_bytes = sd.read_bytes()
    hd_bytes = hd.read_bytes()
    sd_dim = Image.open(sd).size
    hd_dim = Image.open(hd).size

    # 1) costumes/<stem>_csp.png (SD) + _csp_hd.png (HD)
    (VAULT / "costumes" / f"{stem}_csp.png").write_bytes(sd_bytes)
    (VAULT / "costumes" / f"{stem}_csp_hd.png").write_bytes(hd_bytes)
    # 2) costumes/<stem>.zip/csp.png (SD)
    put_in_zip(VAULT / "costumes" / f"{stem}.zip", "csp.png", sd_bytes)
    # 3) fighter.zip inner <stem>.zip/csp.png (SD) — install/export reads this
    put_inner_csp(VAULT / "fighter.zip", stem, sd_bytes)
    # 4) root grid csp_<i>.png (SD)
    (VAULT / f"csp_{i}.png").write_bytes(sd_bytes)

    print(f"{stem} (csp_{i}): SD {sd_dim} + HD {hd_dim} -> all 4 locations")

print("done")
