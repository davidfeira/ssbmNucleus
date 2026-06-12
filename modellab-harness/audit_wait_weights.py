"""Audit weights in WAIT space: which bones drive verts that are head-high in
the pose the game actually shows (the space where contamination matters)."""
import sys

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from modellab import smd  # noqa: E402
from modellab.rig import (joint_world_matrices, load_pose, skin_matrices,  # noqa: E402
                          repose_points)

import numpy as np  # noqa: E402

RK = r"C:\Users\david\projects\ssbmNucleus-master\modellab\rigkits"
out = smd.load(r"C:\Users\david\projects\ssbmNucleus-master\modellab\out\falco_on_fox\falco_v8.smd")

# stored verts are target-bind space; play them forward to fox WAIT
tgt_skin = skin_matrices(joint_world_matrices(out), load_pose(RK + r"\fox\fox_wait1.json"))
pts = np.array([v.pos for t in out.triangles for v in t.verts])
w = [v.weights for t in out.triangles for v in t.verts]
wait_pts = repose_points(pts, w, tgt_skin)

wcount: dict = {}
n = 0
for i, wl in enumerate(w):
    if wait_pts[i][1] > 10.0:
        n += 1
        for b, ww in wl:
            wcount[b] = wcount.get(b, 0) + 1
print(f"verts head-high in WAIT (> y10): {n}")
print("their bones:", dict(sorted(wcount.items(), key=lambda kv: -kv[1])[:10]))
hx = wait_pts[wait_pts[:, 1] > 10.0]
print(f"wait head extent: x[{hx[:,0].min():.1f},{hx[:,0].max():.1f}] "
      f"y[{hx[:,1].min():.1f},{hx[:,1].max():.1f}] z[{hx[:,2].min():.1f},{hx[:,2].max():.1f}]")
