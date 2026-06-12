"""Per-group far-vert audit: groups whose verts sit far from their weight bones."""
import sys
from collections import defaultdict

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from modellab import smd  # noqa: E402
from modellab.rig import joint_world_positions  # noqa: E402

import numpy as np  # noqa: E402

m = smd.load(sys.argv[1] if len(sys.argv) > 1 else
             r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\modellab\out\falco_on_fox\falco_on_fox.smd")
world = joint_world_positions(m)
names = {b.id: b.name for b in m.bones}

groups = defaultdict(lambda: {"n": 0, "far": 0, "bones": set(),
                              "ymax": -9.0, "ymin": 99.0, "maxd": 0.0})
for t in m.triangles:
    for v in t.verts:
        g = names.get(v.parent)
        gg = groups[g]
        gg["n"] += 1
        gg["ymax"] = max(gg["ymax"], v.pos[1])
        gg["ymin"] = min(gg["ymin"], v.pos[1])
        for b, w in v.weights:
            if w > 0.3:
                gg["bones"].add(b)
        bp = np.zeros(3)
        tw = 0.0
        for b, w in v.weights:
            if b in world:
                bp += world[b] * w
                tw += w
        if tw:
            dist = float(np.linalg.norm(np.array(v.pos) - bp / tw))
            gg["maxd"] = max(gg["maxd"], dist)
            if dist > 3.5:
                gg["far"] += 1

for g, gg in sorted(groups.items(), key=lambda kv: -kv[1]["far"]):
    if gg["far"]:
        print(f"{g}: {gg['far']}/{gg['n']} far (maxd {gg['maxd']:.1f}), "
              f"y[{gg['ymin']:.1f},{gg['ymax']:.1f}], bones {sorted(gg['bones'])}")
