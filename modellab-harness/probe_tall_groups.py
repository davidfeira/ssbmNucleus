"""For falco source groups reaching above y=13: their bones, and how far those
bones move between bind and Wait1 — plus whether reposing moves the verts."""
import sys

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from modellab import smd  # noqa: E402
from modellab.rig import (joint_world_matrices, load_pose, skin_matrices,  # noqa: E402
                          repose_points)

import numpy as np  # noqa: E402

m = smd.load(r"C:\Users\david\projects\ssbmNucleus-master\modellab\rigkits\falco\falco_vanilla.smd")
bind = joint_world_matrices(m)
pose = load_pose(r"C:\Users\david\projects\ssbmNucleus-master\modellab\rigkits\falco\falco_wait1.json")
skin = skin_matrices(bind, pose)
names = {b.id: b.name for b in m.bones}

groups: dict = {}
for t in m.triangles:
    groups.setdefault(t.verts[0].parent, []).append(t)
order = {g: i for i, g in enumerate(groups)}

for g, ts in groups.items():
    pts = np.array([v.pos for t in ts for v in t.verts])
    if pts[:, 1].max() <= 13.0:
        continue
    w = [v.weights for t in ts for v in t.verts]
    bones = {}
    for wl in w:
        for b, ww in wl:
            bones[b] = bones.get(b, 0) + ww
    dom = sorted(bones, key=lambda b: -bones[b])[:3]
    moved = {b: round(float(np.linalg.norm(pose[b][:3, 3] - bind[b][:3, 3])), 1)
             for b in dom if b in pose and b in bind}
    reposed = repose_points(pts, w, skin)
    print(f"g{order[g]:2d} {names.get(g, g)}: tris {len(ts):3d} "
          f"bind y[{pts[:,1].min():.1f},{pts[:,1].max():.1f}] -> "
          f"wait y[{reposed[:,1].min():.1f},{reposed[:,1].max():.1f}] "
          f"dom bones {dom} moved {moved}")
