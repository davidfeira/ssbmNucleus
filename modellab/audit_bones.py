"""Audit bone usage: which joints does the vanilla mesh weight to (and where),
vs what the rigger emitted. Reveals 'forbidden bone' / polluted-sample issues."""
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from modellab import smd  # noqa: E402

import numpy as np  # noqa: E402


def audit(path, label):
    m = smd.load(path)
    names = {b.id: b.name for b in m.bones}
    usage = defaultdict(lambda: {"n": 0, "w": 0.0, "ys": []})
    for t in m.triangles:
        for v in t.verts:
            for bone, w in v.weights:
                u = usage[bone]
                u["n"] += 1
                u["w"] += w
                u["ys"].append(v.pos[1])

    print(f"\n=== {label}: {len(usage)} bones referenced "
          f"(of {sum(1 for b in m.bones if b.name.startswith('JOBJ_'))} joints)")
    for bone in sorted(usage):
        u = usage[bone]
        ys = np.array(u["ys"])
        print(f"  {names.get(bone, bone):>10}  verts {u['n']:>5}  "
              f"total_w {u['w']:>8.1f}  y[{ys.min():5.1f},{ys.max():5.1f}]")
    return set(usage)


van = audit(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\modellab\rigkits\fox\fox_vanilla.smd",
            "vanilla fox mesh")
out = audit(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\modellab\out\hunyuan_on_fox\hunyuan_on_fox.smd",
            "rigged hunyuan output")
print("\nbones in output but NOT in vanilla usage:", sorted(out - van))
