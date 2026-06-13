"""Render an SMD using its STORED vertex normals with a specular term — the
thing GX actually does, and the thing the other lab previews DON'T (they
derive face normals from geometry, hiding bad stored normals). Noisy/garbage
stored normals show up here as chrome speckle, reproducing the in-game look.

usage: spec_preview.py <rigged.smd> <out.png> [yaw]
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from modellab import smd  # noqa: E402

m = smd.load(sys.argv[1])
out = sys.argv[2]
yaw = math.radians(float(sys.argv[3]) if len(sys.argv) > 3 else 20.0)

pos = np.array([[v.pos for v in t.verts] for t in m.triangles])     # (T,3,3)
nrm = np.array([[v.normal for v in t.verts] for t in m.triangles])  # (T,3,3)

rot = np.array([[math.cos(yaw), 0, math.sin(yaw)], [0, 1, 0],
                [-math.sin(yaw), 0, math.cos(yaw)]])
P = pos @ rot.T
N = nrm @ rot.T
# renormalize stored normals (GX uses them as-is; zero/garbage => wild specular)
nl = np.linalg.norm(N, axis=2, keepdims=True)
N = np.divide(N, nl, out=np.zeros_like(N), where=nl > 1e-9)

SIZE = 460
L = np.array([0.3, 0.5, 0.8]); L = L / np.linalg.norm(L)   # light
V = np.array([0.0, 0.0, 1.0])                              # view (+Z toward cam)
# per-corner shading -> average to flat tri color (painter), so per-vertex
# normal noise still reads as tri-to-tri speckle like the game
diff = np.clip((N * L).sum(axis=2), 0, 1)                  # (T,3)
R = 2 * (N * L).sum(axis=2, keepdims=True) * N - L         # reflect
# strong specular, low exponent => normal noise blooms into chrome speckle
# (mimics GX's per-vertex specular under the in-game lighting rig)
spec = np.clip((R * V).sum(axis=2), 0, 1) ** 8             # (T,3)
shade = np.clip(0.22 + 0.5 * diff + 1.8 * spec, 0, 2.0).mean(axis=1)  # (T,)

xy = P[:, :, :2].copy(); xy[:, :, 1] *= -1
lo, hi = xy.reshape(-1, 2).min(0), xy.reshape(-1, 2).max(0)
span = max((hi - lo).max(), 1e-9); margin = 0.06 * SIZE
q = (xy - lo) / span * (SIZE - 2 * margin) + margin
q += (SIZE - 2 * margin - (hi - lo) / span * (SIZE - 2 * margin)) / 2

im = Image.new("RGB", (SIZE, SIZE), (18, 20, 30)); d = ImageDraw.Draw(im)
for i in np.argsort(P[:, :, 2].mean(axis=1)):
    g = int(np.clip(shade[i], 0, 1.6) / 1.6 * 255)
    d.polygon([tuple(p) for p in q[i]], fill=(g, g, g))
im.save(out)
print("saved", out)
