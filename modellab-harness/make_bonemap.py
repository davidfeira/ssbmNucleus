"""Bone-marker diagnostic costume: one small cube single-bound to each stable
bone, positioned at that bone's BIND world position. In-game, each cube renders
at the bone's ANIMATED position — displaced cubes reveal which bones rest far
from their bind pose (the cause of stretched transfers)."""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from modellab import smd  # noqa: E402
from modellab.rig import joint_world_positions, load_visibility  # noqa: E402

KIT = Path(r"C:\Users\david\projects\ssbmNucleus-master\modellab\rigkits\fox\fox_vanilla.smd")
OUT = Path(r"C:\Users\david\projects\ssbmNucleus-master\modellab\out\bonemap")
OUT.mkdir(parents=True, exist_ok=True)

kit = smd.load(KIT)
joints = [b for b in kit.bones if b.name.startswith("JOBJ_")]
world = joint_world_positions(kit)

# mark every bone the vanilla mesh actually uses (the audit's 60), at its bind
used = sorted({b for t in kit.triangles for v in t.verts for b, w in v.weights
               if b in world})

out = smd.SMD(bones=list(joints))
next_id = max(b.id for b in joints) + 1
S = 0.28

visible, total = load_visibility("PlFx")
slots = ["real" if i in visible else "dummy" for i in range(total)]
marker_iter = iter(used)

def cube(node, cx, cy, cz, s):
    v = [(cx-s, cy-s, cz-s), (cx+s, cy-s, cz-s), (cx+s, cy+s, cz-s), (cx-s, cy+s, cz-s),
         (cx-s, cy-s, cz+s), (cx+s, cy-s, cz+s), (cx+s, cy+s, cz+s), (cx-s, cy+s, cz+s)]
    quads = [(0, 1, 2, 3), (5, 4, 7, 6), (4, 0, 3, 7), (1, 5, 6, 2),
             (3, 2, 6, 7), (4, 5, 1, 0)]
    tris = []
    for a, b, c, d in quads:
        tris.append((v[a], v[b], v[c]))
        tris.append((v[a], v[c], v[d]))
    return tris


for i, kind in enumerate(slots):
    node = next_id
    out.bones.append(smd.Bone(id=node, name=f"Joint_0_Object_{i}", parent=-1))
    next_id += 1
    bone = next(marker_iter, None) if kind == "real" else None
    if bone is not None:
        cx, cy, cz = world[bone]
        for a, b, c in cube(node, cx, cy, cz, S):
            verts = [smd.Vertex(pos=p, normal=(0, 0, 1), uv=(0.5, 0.5),
                                weights=[(bone, 1.0)], parent=node)
                     for p in (a, b, c)]
            out.triangles.append(smd.Triangle(material="mat0", verts=tuple(verts)))
    else:
        # dummy micro-tri
        verts = [smd.Vertex(pos=(dx, 3.0 + dy, 0.0), normal=(0, 0, 1), uv=(0.5, 0.5),
                            weights=[(4, 1.0)], parent=node)
                 for dx, dy in ((0, 0), (1e-3, 0), (0, 1e-3))]
        out.triangles.append(smd.Triangle(material="mat0", verts=tuple(verts)))

left = list(marker_iter)
print(f"markers placed: {len(used) - len(left)}/{len(used)} (left over: {left})")
smd.save(out, OUT / "bonemap.smd")
shutil.copyfile(
    r"C:\Users\david\projects\ssbmNucleus-master\modellab\out\hunyuan_on_fox\mat0.png",
    OUT / "mat0.png")
(OUT / "bonemap.smd.textures.json").write_text(json.dumps({"mat0": "mat0.png"}))
print("bonemap SMD written")
