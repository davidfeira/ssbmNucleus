"""Retake all Funky Kong CSPs in the DK 'fist' scene pose.

Funky Kong is a DK reskin (PlyDonkey5KRe skeleton), so DK's baked scene
animation applies directly. The 'fist' pose (custom_poses/DK/fist.yml) is a
SCENE pose (useSceneAnimation: true), so we merge DK's csp_data scene.yml
(settings + baked animation) with the pose's camera/frame/hiddenNodes into one
scene.yml and render every Funky costume DAT against it. Generates SD (scale 1,
136x188) + HD (scale 4, 544x752) and writes them to every CSP location:
  - root csp_<i>.png (SD)                          [bundled costumes only]
  - costumes/<stem>_csp.png (SD) + _csp_hd.png (HD)
  - costumes/<stem>.zip -> csp.png (SD)
  - fighter.zip inner <stem>.zip -> csp.png (SD)   [bundled costumes only]
  - skins/<id>_csp.png (SD) + _csp_hd.png (HD), skins/<id>.zip -> csp.png (SD)
Stocks are a separate bind-pose head shot (pose-independent) and are NOT touched.
Run from modellab/.
"""
import io
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(r"C:/Users/david/projects/ssbmNucleus-master/ssbmNucleus")
VAULT = ROOT / "storage/custom_characters/funky-kong"
EXE = ROOT / "utility/tools/HSDLib/HSDRawViewer/bin/Release/net6.0-windows/HSDRawViewer.exe"
SCENE_SRC = ROOT / "utility/tools/processor/csp_data/DK/scene.yml"
POSE = ROOT / "utility/assets/vanilla/custom_poses/DK/fist.yml"
WORK = ROOT / "tmp_funky"
WORK.mkdir(exist_ok=True)

# (stem, source costume zip, root index or None for added skins)
BUNDLED = [("PlFkNr", VAULT / "costumes/PlFkNr.zip", 0),
           ("PlFkRd", VAULT / "costumes/PlFkRd.zip", 1),
           ("PlFkBl", VAULT / "costumes/PlFkBl.zip", 2),
           ("PlFkGr", VAULT / "costumes/PlFkGr.zip", 3)]
ADDED = [("e53defa0", "PlFkLk", VAULT / "skins/e53defa0.zip")]


# ---- scene-pose merge (same logic as backend poses._build_scene_pose_yaml) --
def parse_pose(text):
    out = {'camera': {}, 'hiddenNodes': []}
    in_cam = in_hid = False
    for raw in text.splitlines():
        if not raw.strip():
            continue
        if raw.startswith('- ') and in_hid:
            try:
                out['hiddenNodes'].append(int(raw[2:].strip()))
            except ValueError:
                pass
            continue
        if not raw[0].isspace():
            in_cam = raw.startswith('camera:')
            in_hid = raw.startswith('hiddenNodes:')
            if ':' in raw and not in_cam and not in_hid:
                k, v = raw.split(':', 1)
                out[k.strip()] = v.strip()
            continue
        if in_cam and ':' in raw:
            k, v = raw.split(':', 1)
            out['camera'][k.strip()] = v.strip()
    return out


def build_scene(scene_path, pose):
    lines = scene_path.read_text(encoding='utf-8', errors='replace').splitlines()
    order, tops = [], {}
    for i, l in enumerate(lines):
        if l and not l[0].isspace() and not l.startswith('-'):
            order.append(l.split(':', 1)[0].strip())
            tops[order[-1]] = i

    def na(key, eof):
        idx = order.index(key)
        return tops[order[idx + 1]] if idx + 1 < len(order) else eof

    cam = pose.get('camera') or {}
    cs, ce = tops['camera'], na('camera', len(lines))
    nc = ['camera:']
    for cl in lines[cs + 1:ce]:
        k = cl.split(':', 1)[0].strip()
        nc.append(f'  {k}: {cam[k]}' if k in cam else cl)
    keep_key = 'settings' if 'settings' in tops else 'animation'
    keep = lines[tops[keep_key]:na('animation', len(lines))]
    hdr = [f"frame: {pose.get('frame', 0)}",
           f"cSPMode: {str(pose.get('cSPMode', 'true')).lower()}",
           f"showGrid: {str(pose.get('showGrid', 'false')).lower()}",
           f"showBackdrop: {str(pose.get('showBackdrop', 'false')).lower()}"] + nc
    ft = ['hiddenNodes:'] + [f'- {n}' for n in pose['hiddenNodes']] if pose.get('hiddenNodes') else []
    return '\n'.join(hdr + keep + ft) + '\n'


SCENE = WORK / "scene.yml"
SCENE.write_text(build_scene(SCENE_SRC, parse_pose(POSE.read_text(encoding='utf-8'))),
                 encoding='utf-8')


def render(dat, out, scale):
    if out.exists():
        out.unlink()
    cmd = [str(EXE), "--csp", str(dat), str(out)]
    if scale > 1:
        cmd += ["--scale", str(scale)]
    cmd += [str(SCENE)]
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
    """Replace one member in a zip, preserving all others."""
    zin = zipfile.ZipFile(zip_path, "r")
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zo:
        for it in zin.infolist():
            zo.writestr(it, data if it.filename == member else zin.read(it.filename))
    zin.close()
    zip_path.write_bytes(buf.getvalue())


def replace_inner_csp(outer_zip, inner_name, sd_bytes):
    """Replace csp.png inside an inner <stem>.zip of fighter.zip."""
    outer = zipfile.ZipFile(outer_zip, "r")
    inner = zipfile.ZipFile(io.BytesIO(outer.read(inner_name)))
    ib = io.BytesIO()
    with zipfile.ZipFile(ib, "w", zipfile.ZIP_DEFLATED) as zo:
        for n in inner.namelist():
            zo.writestr(n, sd_bytes if n == "csp.png" else inner.read(n))
    new_inner = ib.getvalue()
    outer.close()
    replace_in_zip(outer_zip, inner_name, new_inner)


def render_pair(stem, src_zip):
    dat = dat_from_zip(src_zip, stem)
    if not dat:
        print(f"{stem}: DAT not found in {src_zip.name}")
        return None, None
    sd = WORK / f"{stem}_sd.png"
    hd = WORK / f"{stem}_hd.png"
    if not (render(dat, sd, 1) and render(dat, hd, 4)):
        print(f"{stem}: RENDER FAILED")
        return None, None
    return sd.read_bytes(), hd.read_bytes()


FIGHTER_ZIP = VAULT / "fighter.zip"

for stem, src_zip, idx in BUNDLED:
    sd_bytes, hd_bytes = render_pair(stem, src_zip)
    if sd_bytes is None:
        continue
    (VAULT / f"csp_{idx}.png").write_bytes(sd_bytes)
    (VAULT / "costumes" / f"{stem}_csp.png").write_bytes(sd_bytes)
    (VAULT / "costumes" / f"{stem}_csp_hd.png").write_bytes(hd_bytes)
    replace_in_zip(VAULT / "costumes" / f"{stem}.zip", "csp.png", sd_bytes)
    replace_inner_csp(FIGHTER_ZIP, f"{stem}.zip", sd_bytes)
    print(f"{stem} (csp_{idx}): SD+HD -> root + costumes + fighter.zip")

for skin_id, dat_stem, src_zip in ADDED:
    sd_bytes, hd_bytes = render_pair(dat_stem, src_zip)
    if sd_bytes is None:
        continue
    (VAULT / "skins" / f"{skin_id}_csp.png").write_bytes(sd_bytes)
    (VAULT / "skins" / f"{skin_id}_csp_hd.png").write_bytes(hd_bytes)
    replace_in_zip(VAULT / "skins" / f"{skin_id}.zip", "csp.png", sd_bytes)
    print(f"{skin_id} ({dat_stem}): SD+HD -> skins/")

print("done")
