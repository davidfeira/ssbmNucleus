"""Diagnostic costume: 77 small cubes, one per DObj index, laid out in a grid
(row = index // 10, col = index % 10). Boot + pause screenshot reveals exactly
which DObj indices the game renders for this costume slot."""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from modellab import smd  # noqa: E402

KIT = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\modellab\rigkits\fox\fox_vanilla.smd")
OUT = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\modellab\out\staircase")
OUT.mkdir(parents=True, exist_ok=True)

kit = smd.load(KIT)
joints = [b for b in kit.bones if b.name.startswith("JOBJ_")]

out = smd.SMD(bones=list(joints))
next_id = max(b.id for b in joints) + 1

N = 77
S = 0.42           # cube half size


def cube_tris(cx, cy, cz):
    v = [(cx - S, cy - S, cz - S), (cx + S, cy - S, cz - S),
         (cx + S, cy + S, cz - S), (cx - S, cy + S, cz - S),
         (cx - S, cy - S, cz + S), (cx + S, cy - S, cz + S),
         (cx + S, cy + S, cz + S), (cx - S, cy + S, cz + S)]
    quads = [(0, 1, 2, 3), (5, 4, 7, 6), (4, 0, 3, 7),
             (1, 5, 6, 2), (3, 2, 6, 7), (4, 5, 1, 0)]
    tris = []
    for a, b, c, d in quads:
        tris.append((v[a], v[b], v[c]))
        tris.append((v[a], v[c], v[d]))
    return tris


for i in range(N):
    node = next_id
    out.bones.append(smd.Bone(id=node, name=f"Joint_0_Object_{i}", parent=-1))
    next_id += 1
    # 4 vertical strips x 20 rows: column = i % 4, height = i // 4. Gaps in a
    # strip identify hidden indices unambiguously at any camera distance.
    row, col = divmod(i, 4)[::-1] if False else (i // 4, i % 4)
    cx = (col - 1.5) * 1.5
    cy = 0.6 + row * 1.0
    cz = 0.0
    for a, b, c in cube_tris(cx, cy, cz):
        verts = []
        for p in (a, b, c):
            verts.append(smd.Vertex(pos=p, normal=(0, 0, 1), uv=(0.5, 0.5),
                                    weights=[(4, 1.0)], parent=node))
        out.triangles.append(smd.Triangle(material="mat0", verts=tuple(verts)))

smd.save(out, OUT / "staircase.smd")
shutil.copyfile(
    r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\modellab\out\hunyuan_on_fox\mat0.png",
    OUT / "mat0.png")
(OUT / "staircase.smd.textures.json").write_text(json.dumps({"mat0": "mat0.png"}))
print("staircase SMD written:", OUT / "staircase.smd")
