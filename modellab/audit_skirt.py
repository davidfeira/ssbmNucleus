"""Where do the rigged output's lower-body verts actually bind? Histogram
assigned bones (with fox part labels) for verts in the skirt band."""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import numpy as np  # noqa: E402

from modellab import smd  # noqa: E402
from modellab.rig import load_dynamics  # noqa: E402
from modellab.skeleton_parts import label_parts  # noqa: E402

out = smd.load(sys.argv[1])
fox = smd.load(str(Path(__file__).parent / "rigkits" / "fox" / "fox_vanilla.smd"))
parts = label_parts(fox, dynamic_roots=load_dynamics("PlFx"))

hist = Counter()
n = 0
for t in out.triangles:
    for v in t.verts:
        x, y, z = v.pos
        if 1.2 <= y <= 4.2 and abs(x) <= 2.2:     # skirt band in fox bind
            n += 1
            for b, w in v.weights:
                hist[(b, parts.get(b))] += w
print(f"skirt-band corners: {n}")
for (b, p), w in hist.most_common(14):
    print(f"  JOBJ_{b:<3} {str(p):<7} mass {w:7.1f}")
