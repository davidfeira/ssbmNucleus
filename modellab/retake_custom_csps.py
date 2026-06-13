"""Retake custom-character CSPs in their intended (donor-named) poses.

Each custom char clones a vanilla skeleton; its 'intended' pose lives under that
donor's custom_poses folder, named after the custom char. All four handled here
are SYMBOL poses (Ply<Donor>5K_Share_ACTION_*_figatree), rendered against the
donor's vanilla AJ (which carries every symbol). Costume stems + their csp_<i>
index come straight from fighter.json order. Generates SD (136x188) + HD
(544x752) and writes to every CSP location; stocks (stc.png) are pose-
independent and left untouched. Run from modellab/.
"""
import io
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(r"C:/Users/david/projects/ssbmNucleus-master/ssbmNucleus")
EXE = ROOT / "utility/tools/HSDLib/HSDRawViewer/bin/Release/net6.0-windows/HSDRawViewer.exe"
POSES = ROOT / "utility/assets/vanilla/custom_poses"
VANILLA = ROOT / "utility/assets/vanilla"
WORK = ROOT / "tmp_retake"
WORK.mkdir(exist_ok=True)

# slug -> (pose yml, donor vanilla AJ)
CONFIG = {
    "slippy":            (POSES / "Fox/slippi.yml",          VANILLA / "Fox/PlFxAJ.dat"),
    "shadow-mewtwo":     (POSES / "Mewtwo/shadowmetwto.yml", VANILLA / "Mewtwo/PlMtAJ.dat"),
    "phantom-ganondorf": (POSES / "Ganondorf/phantomganon.yml", VANILLA / "Ganondorf/PlGnAJ.dat"),
    "cdi-king":          (POSES / "Ganondorf/cdiking.yml",   VANILLA / "Ganondorf/PlGnAJ.dat"),
    "blaziken":          (POSES / "C. Falcon/blaziken.yml",  VANILLA / "C. Falcon/PlCaAJ.dat"),
}


def render(dat, out, pose, aj, scale):
    if out.exists():
        out.unlink()
    cmd = [str(EXE), "--csp", str(dat), str(out)]
    if scale > 1:
        cmd += ["--scale", str(scale)]
    cmd += [str(pose), str(aj)]
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


def render_pair(stem, src_zip, pose, aj):
    dat = dat_from_zip(src_zip, stem)
    if not dat:
        print(f"  {stem}: DAT not found in {src_zip.name}")
        return None, None
    sd, hd = WORK / f"{stem}_sd.png", WORK / f"{stem}_hd.png"
    if not (render(dat, sd, pose, aj, 1) and render(dat, hd, pose, aj, 4)):
        print(f"  {stem}: RENDER FAILED")
        return None, None
    return sd.read_bytes(), hd.read_bytes()


for slug, (pose, aj) in CONFIG.items():
    vault = ROOT / "storage/custom_characters" / slug
    fighter = json.load(open(vault / "fighter.json", encoding="utf-8"))
    stems = [Path((c.get("file") or {}).get("fileName") or "").stem
             for c in fighter.get("costumes", [])]
    fighter_zip = vault / "fighter.zip"
    print(f"=== {slug} ({pose.parent.name}/{pose.name}) ===")

    for idx, stem in enumerate(stems):
        src_zip = vault / "costumes" / f"{stem}.zip"
        if not src_zip.exists():
            print(f"  {stem}: costume zip missing")
            continue
        sd_bytes, hd_bytes = render_pair(stem, src_zip, pose, aj)
        if sd_bytes is None:
            continue
        (vault / f"csp_{idx}.png").write_bytes(sd_bytes)
        (vault / "costumes" / f"{stem}_csp.png").write_bytes(sd_bytes)
        (vault / "costumes" / f"{stem}_csp_hd.png").write_bytes(hd_bytes)
        replace_in_zip(vault / "costumes" / f"{stem}.zip", "csp.png", sd_bytes)
        replace_inner_csp(fighter_zip, f"{stem}.zip", sd_bytes)
        print(f"  {stem} (csp_{idx}): SD+HD -> root + costumes + fighter.zip")

    # added skins: skins/<id>.zip carries one <PlXX>.dat
    skins_dir = vault / "skins"
    for skin_zip in sorted(skins_dir.glob("*.zip")) if skins_dir.exists() else []:
        skin_id = skin_zip.stem
        with zipfile.ZipFile(skin_zip) as zf:
            dat_stem = next((Path(n).stem for n in zf.namelist()
                             if n.lower().endswith(".dat")), None)
        if not dat_stem:
            print(f"  skin {skin_id}: no DAT")
            continue
        sd_bytes, hd_bytes = render_pair(dat_stem, skin_zip, pose, aj)
        if sd_bytes is None:
            continue
        (skins_dir / f"{skin_id}_csp.png").write_bytes(sd_bytes)
        (skins_dir / f"{skin_id}_csp_hd.png").write_bytes(hd_bytes)
        replace_in_zip(skin_zip, "csp.png", sd_bytes)
        print(f"  skin {skin_id} ({dat_stem}): SD+HD -> skins/")

print("done")
