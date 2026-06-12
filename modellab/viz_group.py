"""Scatter-render a falco source group from front and side to identify it."""
import sys

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from modellab import smd  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

m = smd.load(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\modellab\rigkits\falco\falco_vanilla.smd")
groups: dict = {}
for t in m.triangles:
    groups.setdefault(t.verts[0].parent, []).append(t)
order = list(groups)

want = [int(a) for a in sys.argv[1:]] or [18, 35]
fig, axes = plt.subplots(len(want), 2, figsize=(8, 4 * len(want)))
if len(want) == 1:
    axes = [axes]
for row, gi in enumerate(want):
    ts = groups[order[gi]]
    pts = np.array([v.pos for t in ts for v in t.verts])
    axes[row][0].scatter(pts[:, 0], pts[:, 1], s=1)
    axes[row][0].set_title(f"g{gi} front (x/y), {len(ts)} tris")
    axes[row][0].set_aspect("equal")
    axes[row][1].scatter(pts[:, 2], pts[:, 1], s=1)
    axes[row][1].set_title(f"g{gi} side (z/y)")
    axes[row][1].set_aspect("equal")
out = r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\modellab\out\falco_groups.png"
plt.tight_layout()
plt.savefig(out, dpi=90)
print("saved", out)
