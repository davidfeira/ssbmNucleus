"""Retake all Dry Bowser CSPs in the 'drybo' pose.

Dry Bowser is a Bowser reskin (PlyKoopa5K skeleton). The 'drybo' pose
(custom_poses/Bowser/drybo.yml) is a SYMBOL pose
(animSymbol: PlyKoopa5K_Share_ACTION_Turn_figatree), so we render each costume
DAT with the pose yml + Dry Bowser's own AJ (aj_cache.dat, which carries the
Koopa symbols). Generates SD (scale 1, 136x188) + HD (scale 4, 544x752) and
writes them to every CSP location:
  - root csp_<i>.png (SD)
  - costumes/<stem>_csp.png (SD) + _csp_hd.png (HD)
  - costumes/<stem>.zip -> csp.png (SD)
  - fighter.zip inner <stem>.zip -> csp.png (SD)
Stocks (stc.png) are a pose-independent head shot and are NOT touched.
Run from modellab/.
"""
import io
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(r"C:/Users/david/projects/ssbmNucleus-master/ssbmNucleus")
VAULT = ROOT / "storage/custom_characters/dry-bowser"
EXE = ROOT / "utility/tools/HSDLib/HSDRawViewer/bin/Release/net6.0-windows/HSDRawViewer.exe"
POSE = ROOT / "utility/assets/vanilla/custom_poses/Bowser/drybo.yml"
AJ = VAULT / "aj_cache.dat"
WORK = ROOT / "tmp_drybo"
WORK.mkdir(exist_ok=True)

# (stem, root index) — costumes in fighter.json order
COSTUMES = [("PlDbNr", 0), ("PlDbRe", 1), ("PlDbBu", 2), ("PlDbGr", 3), ("PlDbYe", 4)]
FIGHTER_ZIP = VAULT / "fighter.zip"


def render(dat, out, scale):
    if out.exists():
        out.unlink()
    cmd = [str(EXE), "--csp", str(dat), str(out)]
    if scale > 1:
        cmd += ["--scale", str(scale)]
    cmd += [str(POSE), str(AJ)]
    subprocess.run(cmd, cwd=WORK, capture_output=True, text=True, timeout=300)
    return out.exists()


def dat_from_zip(zip_path, stem):
    with zipfile.ZipFile(zip_path) as zf:
        for n in zf.namelist():
            if Path(n).name.lower() == f"{stem.lower()}.dat":
                d = WORK / f"{stem}.dat"
                d.write_bytes(zf.read(n))
                return d
    return None


def replace_in_zip(zip_path, member, data):
    zin = zipfile.ZipFile(zip_path, "r")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zin.infolist():
            zo.writestr(it, data if it.filename == member else zin.read(it.filename))
    zin.close()
    zip_path.write_bytes(buf.getvalue())


def replace_inner_csp(outer_zip, inner_name, sd_bytes):
    outer = zipfile.ZipFile(outer_zip, "r")
    inner = zipfile.ZipFile(io.BytesIO(outer.read(inner_name)))
    ib = io.BytesIO()
    with zipfile.ZipFile(ib, "w", zipfile.ZIP_DEFLATED) as zo:
        for n in inner.namelist():
            zo.writestr(n, sd_bytes if n == "csp.png" else inner.read(n))
    new_inner = ib.getvalue()
    outer.close()
    replace_in_zip(outer_zip, inner_name, new_inner)


for stem, idx in COSTUMES:
    src_zip = VAULT / "costumes" / f"{stem}.zip"
    dat = dat_from_zip(src_zip, stem)
    if not dat:
        print(f"{stem}: DAT not found")
        continue
    sd = WORK / f"{stem}_sd.png"
    hd = WORK / f"{stem}_hd.png"
    if not (render(dat, sd, 1) and render(dat, hd, 4)):
        print(f"{stem}: RENDER FAILED")
        continue
    sd_bytes, hd_bytes = sd.read_bytes(), hd.read_bytes()
    (VAULT / f"csp_{idx}.png").write_bytes(sd_bytes)
    (VAULT / "costumes" / f"{stem}_csp.png").write_bytes(sd_bytes)
    (VAULT / "costumes" / f"{stem}_csp_hd.png").write_bytes(hd_bytes)
    replace_in_zip(VAULT / "costumes" / f"{stem}.zip", "csp.png", sd_bytes)
    replace_inner_csp(FIGHTER_ZIP, f"{stem}.zip", sd_bytes)
    print(f"{stem} (csp_{idx}): SD+HD -> root + costumes + fighter.zip")

print("done")
