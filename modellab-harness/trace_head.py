"""Trace falco head (g18) verts through the v7 pipeline transforms to find
where the shape distorts: source -> repose -> align -> unpose."""
import sys

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from modellab import smd  # noqa: E402
from modellab.rig import (joint_world_matrices, load_pose, skin_matrices,  # noqa: E402
                          repose_points)

import numpy as np  # noqa: E402

RK = r"C:\Users\david\projects\ssbmNucleus-master\modellab\rigkits"
src = smd.load(RK + r"\falco\falco_vanilla.smd")
out = smd.load(r"C:\Users\david\projects\ssbmNucleus-master\modellab\out\falco_on_fox\falco_v7.smd")

src_skin = skin_matrices(joint_world_matrices(src), load_pose(RK + r"\falco\falco_wait1.json"))

groups: dict = {}
for t in src.triangles:
    groups.setdefault(t.verts[0].parent, []).append(t)
g18 = list(groups)[18]
ts = groups[g18]
pts = np.array([v.pos for t in ts for v in t.verts])
w = [v.weights for t in ts for v in t.verts]

posed = repose_points(pts, w, src_skin)


def stats(label, p):
    p = np.asarray(p)
    sz = p.max(axis=0) - p.min(axis=0)
    print(f"{label:>14}: y[{p[:,1].min():5.1f},{p[:,1].max():5.1f}] "
          f"x[{p[:,0].min():5.1f},{p[:,0].max():5.1f}] "
          f"z[{p[:,2].min():5.1f},{p[:,2].max():5.1f}]  "
          f"size=({sz[0]:.1f},{sz[1]:.1f},{sz[2]:.1f})")


stats("src bind", pts)
stats("src wait", posed)

# the output SMD: find the verts nearest the head region and report extents of
# everything above y 10 in the stored output
opts = np.array([v.pos for t in out.triangles for v in t.verts])
head = opts[opts[:, 1] > 10.5]
stats("v7 stored>10.5", head)

# weights used by stored head verts
wcount = {}
for t in out.triangles:
    for v in t.verts:
        if v.pos[1] > 10.5:
            for b, ww in v.weights:
                wcount[b] = wcount.get(b, 0) + 1
print("stored head verts weight bones:", dict(sorted(wcount.items(), key=lambda kv: -kv[1])[:8]))
