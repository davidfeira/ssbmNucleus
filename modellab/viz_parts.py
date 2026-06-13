"""Color a mesh by geometric part label (sanity-check the segmentation that
feeds the GLB proxy-skeleton deform). Renders front + side.

usage: viz_parts.py <mesh.glb|smd> <out.png>
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from modellab.rig import load_foreign, decimate  # noqa: E402
from modellab.geometric_parts import label_vertices  # noqa: E402

COLORS = {"head": (230, 200, 90), "torso": (90, 160, 230),
          "l_arm": (230, 110, 90), "r_arm": (150, 70, 200),
          "l_leg": (90, 210, 130), "r_leg": (210, 90, 170), None: (120, 120, 120)}

fm = load_foreign(Path(sys.argv[1]))
if len(fm.tri_pos) > 12000:
    fm = decimate(fm, 9000)
tri = fm.tri_pos                                   # (T,3,3)
verts = tri.reshape(-1, 3)
labels, info = label_vertices(verts)
tri_lab = np.array(labels).reshape(-1, 3)
# per-tri label = majority of its 3 corners
tri_part = [max(set(t), key=list(t).count) for t in tri_lab]

SIZE = 460
out = Image.new("RGB", (SIZE * 2, SIZE), (20, 22, 30))
for col, yaw_deg in enumerate((20.0, 100.0)):
    a = math.radians(yaw_deg)
    rot = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0],
                    [-math.sin(a), 0, math.cos(a)]])
    P = tri @ rot.T
    fn = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    nl = np.linalg.norm(fn, axis=1, keepdims=True)
    fn = np.divide(fn, nl, out=np.zeros_like(fn), where=nl > 1e-9)
    L = np.array([0.3, 0.5, 0.8]); L = L / np.linalg.norm(L)
    sh = np.clip(0.55 + 0.45 * np.abs(fn @ L), 0.3, 1)
    xy = P[:, :, :2].copy(); xy[:, :, 1] *= -1
    lo, hi = xy.reshape(-1, 2).min(0), xy.reshape(-1, 2).max(0)
    span = max((hi - lo).max(), 1e-9); margin = 0.07 * SIZE
    q = (xy - lo) / span * (SIZE - 2 * margin) + margin
    q += (SIZE - 2 * margin - (hi - lo) / span * (SIZE - 2 * margin)) / 2
    q[:, :, 0] += col * SIZE
    im = ImageDraw.Draw(out)
    for i in np.argsort(P[:, :, 2].mean(axis=1)):
        base = COLORS[tri_part[i]]
        c = tuple(int(np.clip(bb * sh[i], 0, 255)) for bb in base)
        im.polygon([tuple(p) for p in q[i]], fill=c)
d = ImageDraw.Draw(out)
d.text((8, 6), "  ".join(f"{k}" for k in COLORS if k), fill=(200, 200, 200))
out.save(sys.argv[2])
print("saved", sys.argv[2])
