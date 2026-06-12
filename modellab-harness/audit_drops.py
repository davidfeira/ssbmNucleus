"""Show exactly which falco source groups the filters drop and why."""
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from modellab import smd  # noqa: E402
from modellab.rig import load_visibility  # noqa: E402

import numpy as np  # noqa: E402

m = smd.load(r"C:\Users\david\projects\ssbmNucleus-master\modellab\rigkits\falco\falco_vanilla.smd")
names = {b.id: b.name for b in m.bones}

groups: dict = {}
for t in m.triangles:
    groups.setdefault(t.verts[0].parent, []).append(t)

visible, total = load_visibility("PlFc")
order = {g: i for i, g in enumerate(groups)}

mass: dict = {}
gmass: dict = {}
for g, ts in groups.items():
    for t in ts:
        for v in t.verts:
            for b, w in v.weights:
                mass[b] = mass.get(b, 0.0) + w
                gm = gmass.setdefault(g, {})
                gm[b] = gm.get(b, 0.0) + w
tot = sum(mass.values()) or 1.0
unstable = {b for b, mm in mass.items() if mm / tot < 0.02}

print(f"falco: {len(groups)} groups, visible set size {len(visible)}, total {total}")
for g, ts in groups.items():
    i = order[g]
    pts = np.array([v.pos for t in ts for v in t.verts])
    gm = gmass[g]
    gt = sum(gm.values()) or 1.0
    ushare = sum(w for b, w in gm.items() if b in unstable) / gt
    dom = sorted(gm.items(), key=lambda kv: -kv[1])[:3]
    vis = i in visible
    dropped = (not vis) or (ushare > 0.6 and "_SINGLE" not in names.get(g, ""))
    flag = "DROP-vis" if not vis else ("DROP-unstable" if dropped else "keep")
    if dropped or ushare > 0.4:
        print(f"  g{i:2d} {names.get(g, g):>28} {flag:>13} tris {len(ts):4d} "
              f"y[{pts[:,1].min():5.1f},{pts[:,1].max():5.1f}] "
              f"ushare {ushare:.2f} dom {[(b, round(w)) for b, w in dom]}")
