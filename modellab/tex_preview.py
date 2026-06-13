"""Render an SMD with its TEXTURE applied via the stored UVs (flat per-tri
sample at the UV centroid). The grey lab previews hide UV corruption; this
exposes it — scrambled UVs sample the wrong atlas islands (the in-game chrome).

usage: tex_preview.py <rigged.smd> <texture.png> <out.png> [yaw]
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

from modellab import smd  # noqa: E402

m = smd.load(sys.argv[1])
tex = np.asarray(Image.open(sys.argv[2]).convert("RGB"))
out = sys.argv[3]
yaw = math.radians(float(sys.argv[4]) if len(sys.argv) > 4 else 20.0)
TH, TW = tex.shape[:2]

pos = np.array([[v.pos for v in t.verts] for t in m.triangles])
uv = np.array([[v.uv for v in t.verts] for t in m.triangles])      # (T,3,2)

rot = np.array([[math.cos(yaw), 0, math.sin(yaw)], [0, 1, 0],
                [-math.sin(yaw), 0, math.cos(yaw)]])
P = pos @ rot.T

# flat per-tri color: sample texture at the UV centroid (v flipped)
cuv = uv.mean(axis=1)
tx = np.clip((cuv[:, 0] % 1.0) * (TW - 1), 0, TW - 1).astype(int)
ty = np.clip((1.0 - cuv[:, 1] % 1.0) * (TH - 1), 0, TH - 1).astype(int)
col = tex[ty, tx]                                                   # (T,3)
# simple lambert so form is readable
fn = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
nl = np.linalg.norm(fn, axis=1, keepdims=True)
fn = np.divide(fn, nl, out=np.zeros_like(fn), where=nl > 1e-9)
L = np.array([0.3, 0.5, 0.8]); L = L / np.linalg.norm(L)
sh = np.clip(0.55 + 0.45 * np.abs(fn @ L), 0, 1)[:, None]
col = np.clip(col * sh, 0, 255).astype(np.uint8)

SIZE = 460
xy = P[:, :, :2].copy(); xy[:, :, 1] *= -1
lo, hi = xy.reshape(-1, 2).min(0), xy.reshape(-1, 2).max(0)
span = max((hi - lo).max(), 1e-9); margin = 0.06 * SIZE
q = (xy - lo) / span * (SIZE - 2 * margin) + margin
q += (SIZE - 2 * margin - (hi - lo) / span * (SIZE - 2 * margin)) / 2

im = Image.new("RGB", (SIZE, SIZE), (18, 20, 30)); d = ImageDraw.Draw(im)
for i in np.argsort(P[:, :, 2].mean(axis=1)):
    d.polygon([tuple(p) for p in q[i]], fill=tuple(int(c) for c in col[i]))
im.save(out)
print("saved", out)
