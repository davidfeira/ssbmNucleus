"""Build the <model>.textures.json sidecar for an HSDRawViewer-exported SMD.

Pairs SMD materials with the exporter's Texture_N_*.png files by replaying the
same DObj walk the exporter used: materials dedupe in first-appearance order
(SMD side and DAT side walk the identical DObj sequence), textures dedupe by
image-data content in first-appearance order (the exporter's imageToName).
"""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ssbmNucleus" / "backend"))
from skinlab.datprobe import DatFile, HEADER_SIZE, gx_image_size  # noqa: E402

GX_FMT = {0: "I4", 1: "I8", 2: "IA4", 3: "IA8", 4: "RGB565", 5: "RGB5A3",
          6: "RGBA8", 8: "CI4", 9: "CI8", 10: "CI14X2", 14: "CMP"}
TLUT_FMT = {0: "IA8", 1: "RGB565", 2: "RGB5A3"}

dat_path, smd_path = sys.argv[1:3]
d = DatFile(dat_path)
root = next(o for n, o in d.roots if n.endswith("_joint") and "matanim" not in n)

# -- DAT side: walk DObjs, dedupe mobjs + textures in first-seen order ------- #
mobj_keys = []           # first-appearance order of distinct mobj contents
mobj_to_texture = {}     # mobj key -> texture file name
image_names = {}         # image data offset -> Texture_N name

for j in d._iter_tree(root, 0x08, 0x0C):
    flags = d.u32(j + 0x04)
    if flags & (1 << 14) or flags & (1 << 5):
        continue
    dobj = d.ptr(j + 0x10)
    while dobj is not None:
        mobj = d.ptr(dobj + 0x08)
        if mobj is not None:
            # deep content key approximating the exporter's deep FNV hash:
            # render flags + material colors + every tobj's struct & image identity
            renderflags = d.u32(mobj + 0x04)
            matcol = d.ptr(mobj + 0x0C)
            matcol_bytes = bytes(
                d.raw[HEADER_SIZE + matcol:HEADER_SIZE + matcol + 0x14]
            ) if matcol else b""
            tobj_sig = []
            t = d.ptr(mobj + 0x08)
            while t is not None:
                img = d.ptr(t + 0x4C)
                tlut = d.ptr(t + 0x50)
                img_data = d.ptr(img + 0x00) if img else None
                tlut_data = d.ptr(tlut + 0x00) if tlut else None
                tobj_sig.append((img_data, tlut_data))
                t = d.ptr(t + 0x04)
            key = (renderflags, matcol_bytes, tuple(tobj_sig))
            if key not in mobj_to_texture:
                mobj_keys.append(key)
                tex_name = None
                tobj = d.ptr(mobj + 0x08)
                if tobj is not None:  # first texture only (matches DiffuseMap)
                    img_off = d.ptr(tobj + 0x4C)
                    if img_off is not None:
                        data_off = d.ptr(img_off + 0x00)
                        if data_off not in image_names:
                            fmt = d.u32(img_off + 0x08)
                            name = f"Texture_{len(image_names)}_{GX_FMT.get(fmt, fmt)}"
                            if fmt in (8, 9, 10):
                                tlut_off = d.ptr(tobj + 0x50)
                                tfmt = d.u32(tlut_off + 0x04) if tlut_off else 1
                                name += f"_{TLUT_FMT.get(tfmt, tfmt)}"
                            image_names[data_off] = name
                        tex_name = image_names[data_off] + ".png"
                mobj_to_texture[key] = tex_name
        dobj = d.ptr(dobj + 0x04)

# -- SMD side: distinct material names in first-appearance order ------------- #
smd_mats = []
seen = set()
in_tris = False
expect_material = True
verts_left = 0
for line in Path(smd_path).read_text(encoding="utf-8").splitlines():
    s = line.strip()
    if s == "triangles":
        in_tris = True
        continue
    if not in_tris or not s:
        continue
    if s == "end":
        break
    if verts_left == 0:
        if s not in seen:
            seen.add(s)
            smd_mats.append(s)
        verts_left = 3
    else:
        verts_left -= 1

print(f"DAT distinct mobjs: {len(mobj_keys)}  textures: {len(image_names)}")
print(f"SMD distinct materials: {len(smd_mats)}")
assert len(smd_mats) == len(mobj_keys), "material count mismatch - ordering assumption broken"

mapping = {}
for mat_name, key in zip(smd_mats, mobj_keys):
    tex = mobj_to_texture[key]
    if tex is not None:
        mapping[mat_name] = tex

out = Path(smd_path + ".textures.json")
out.write_text(json.dumps(mapping, indent=2), encoding="utf-8")
print(f"wrote {len(mapping)} entries -> {out}")
