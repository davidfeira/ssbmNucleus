"""Animation contact sheet for a rigged output SMD: pose it into several
dumped animation frames (LBS with the assigned weights) and render one row
per pose — the fast no-Dolphin QA loop.

usage: anim_preview.py <rigged.smd> <out.png> [pose1.json pose2.json ...]
       (default poses: fox wait1/run/jab/nair from the fox rig kit)
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import numpy as np  # noqa: E402

from modellab import smd  # noqa: E402
from modellab.rig import (joint_world_matrices, load_pose,  # noqa: E402
                          repose_points, skin_matrices)

RK = Path(__file__).parent / "rigkits" / "fox"
DEFAULT_POSES = ["fox_wait1.json", "fox_run_f8.json",
                 "fox_jab_f9.json", "fox_nair_f10.json"]

rig_path, out_png = sys.argv[1], sys.argv[2]
pose_files = [Path(p) for p in sys.argv[3:]] or [RK / p for p in DEFAULT_POSES]

m = smd.load(rig_path)
bind = joint_world_matrices(m)
tris = list(m.triangles)
pts = np.array([v.pos for t in tris for v in t.verts])
w = [v.weights for t in tris for v in t.verts]

from PIL import Image, ImageDraw  # noqa: E402

SIZE = 380
YAWS = (20.0, 110.0)
light = np.array([0.35, 0.55, 0.75])
light /= np.linalg.norm(light)

panes = []
for pose_file in pose_files:
    posed = repose_points(pts, w, skin_matrices(bind, load_pose(pose_file)))
    posed = posed.reshape(-1, 3, 3)
    area = np.linalg.norm(np.cross(posed[:, 1] - posed[:, 0],
                                   posed[:, 2] - posed[:, 0]), axis=1)
    posed = posed[area > 1e-5]          # drop hidden-slot dummy tris
    for yaw in YAWS:
        a = math.radians(yaw)
        rot = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0],
                        [-math.sin(a), 0, math.cos(a)]])
        t = posed @ rot.T
        n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
        grey = np.clip((0.30 + 0.70 * np.clip(np.abs(n @ light), 0, 1)) * 235,
                       0, 255).astype(np.uint8)
        xy = t[:, :, [0, 1]].copy()
        xy[:, :, 1] *= -1
        lo, hi = xy.reshape(-1, 2).min(axis=0), xy.reshape(-1, 2).max(axis=0)
        span = max((hi - lo).max(), 1e-9)
        margin = 0.06 * SIZE
        p = (xy - lo) / span * (SIZE - 2 * margin) + margin
        p += (SIZE - 2 * margin - (hi - lo) / span * (SIZE - 2 * margin)) / 2
        im = Image.new("RGB", (SIZE, SIZE), (23, 30, 42))
        draw = ImageDraw.Draw(im)
        for i in np.argsort(t[:, :, 2].mean(axis=1)):
            g = int(grey[i])
            draw.polygon([tuple(q) for q in p[i]], fill=(g, g, g))
        ImageDraw.Draw(im).text((8, 6), f"{pose_file.stem}  yaw{int(yaw)}",
                                fill=(150, 170, 200))
        panes.append(im)

cols = len(YAWS)
rows = len(pose_files)
sheet = Image.new("RGB", (SIZE * cols, SIZE * rows), (23, 30, 42))
for i, im in enumerate(panes):
    sheet.paste(im, ((i % cols) * SIZE, (i // cols) * SIZE))
sheet.save(out_png)
print("saved", out_png)
