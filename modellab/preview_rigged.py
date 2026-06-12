"""Render a RIGGED output SMD posed into the target's Wait1 — offline view of
exactly what the game shows in the rest stance (no Dolphin needed).

usage: preview_rigged.py <rigged.smd> <wait_pose.json> <out.png> [yaw1,yaw2]
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import numpy as np  # noqa: E402

from modellab import smd  # noqa: E402
from modellab.rig import (joint_world_matrices, load_pose,  # noqa: E402
                          repose_points, skin_matrices)

rig_path, pose_path, out_png = sys.argv[1], sys.argv[2], sys.argv[3]
yaws = [float(y) for y in (sys.argv[4].split(",") if len(sys.argv) > 4
                           else ["20", "110"])]

m = smd.load(rig_path)
skin = skin_matrices(joint_world_matrices(m), load_pose(pose_path))

tris = [t for t in m.triangles]
pts = np.array([v.pos for t in tris for v in t.verts])
w = [v.weights for t in tris for v in t.verts]
posed = repose_points(pts, w, skin).reshape(-1, 3, 3)

# drop dummy micro-triangles (the hidden-slot fillers)
area = np.linalg.norm(np.cross(posed[:, 1] - posed[:, 0],
                               posed[:, 2] - posed[:, 0]), axis=1)
posed = posed[area > 1e-5]

from PIL import Image, ImageDraw  # noqa: E402

size = 460
light = np.array([0.35, 0.55, 0.75])
light /= np.linalg.norm(light)
panes = []
for yaw in yaws:
    a = math.radians(yaw)
    rot = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0],
                    [-math.sin(a), 0, math.cos(a)]])
    t = posed @ rot.T
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    shade = (0.30 + 0.70 * np.clip(np.abs(n @ light), 0, 1))
    grey = np.clip(shade * 235, 0, 255).astype(np.uint8)

    xy = t[:, :, [0, 1]].copy()
    xy[:, :, 1] *= -1
    lo, hi = xy.reshape(-1, 2).min(axis=0), xy.reshape(-1, 2).max(axis=0)
    span = max((hi - lo).max(), 1e-9)
    margin = 0.06 * size
    p = (xy - lo) / span * (size - 2 * margin) + margin
    used = (hi - lo) / span * (size - 2 * margin)
    p += (size - 2 * margin - used) / 2

    im = Image.new("RGB", (size, size), (23, 30, 42))
    draw = ImageDraw.Draw(im)
    for i in np.argsort(t[:, :, 2].mean(axis=1)):
        g = int(grey[i])
        draw.polygon([tuple(q) for q in p[i]], fill=(g, g, g))
    panes.append(im)

out = Image.new("RGB", (size * len(panes), size), (23, 30, 42))
for i, im in enumerate(panes):
    out.paste(im, (i * size, 0))
out.save(out_png)
print("saved", out_png)
