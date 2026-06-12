"""Compare three skeleton frames for falco's head chain:
(a) SMD-FK bind (= the DAT's inverse-bind, via the exporter)
(b) TRS-locals bind (LiveJObj world from JObj TRS, our bind json)
(c) Wait1 frame 0 (anim json)"""
import sys

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from modellab import smd  # noqa: E402
from modellab.rig import joint_world_positions, load_pose  # noqa: E402

import numpy as np  # noqa: E402

m = smd.load(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\modellab\rigkits\falco\falco_vanilla.smd")
a = joint_world_positions(m)
b = {j: mm[:3, 3] for j, mm in load_pose(
    r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\modellab\rigkits\falco\falco_bind.json").items()}
c = {j: mm[:3, 3] for j, mm in load_pose(
    r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\modellab\rigkits\falco\falco_wait1.json").items()}

print(f"{'bone':>8} {'smd-fk bind':>22} {'trs bind':>22} {'wait1':>22}")
for j in (0, 1, 2, 4, 19, 21, 38, 39, 41, 44, 45, 46, 47, 48):
    fa = np.round(a.get(j, [0, 0, 0]), 1).tolist() if j in a else "-"
    fb = np.round(b.get(j, [0, 0, 0]), 1).tolist() if j in b else "-"
    fc = np.round(c.get(j, [0, 0, 0]), 1).tolist() if j in c else "-"
    print(f"JOBJ_{j:>3} {str(fa):>22} {str(fb):>22} {str(fc):>22}")
