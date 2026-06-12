"""Compare bind-pose vs Wait1 rest-pose bone positions."""
import json
import sys

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from modellab import smd  # noqa: E402
from modellab.rig import joint_world_positions  # noqa: E402

import numpy as np  # noqa: E402

pose = json.loads(open(
    r"C:\Users\david\projects\ssbmNucleus-master\modellab\rigkits\fox\fox_wait1.json").read())
kit = smd.load(r"C:\Users\david\projects\ssbmNucleus-master\modellab\rigkits\fox\fox_vanilla.smd")
bind = joint_world_positions(kit)

print("bones displaced >1.5 units between bind and Wait1 frame 0:")
for b in pose["bones"]:
    i = b["index"]
    if i in bind:
        d = float(np.linalg.norm(np.array(b["pos"]) - bind[i]))
        if d > 1.5:
            print(f"  JOBJ_{i}: bind {np.round(bind[i], 1).tolist()} -> "
                  f"wait1 {np.round(b['pos'], 1).tolist()}  moved {d:.1f}")
