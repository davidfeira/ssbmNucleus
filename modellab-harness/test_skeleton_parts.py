"""Validate skeleton_parts.label_parts against zankyou's community bone-name
tables (Mario + Captain Falcon ground truth), then print labels for the
cross-rig cast (fox/falco/marth/ganondorf)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from modellab import smd  # noqa: E402
from modellab.rig import load_dynamics  # noqa: E402
from modellab.skeleton_parts import label_parts  # noqa: E402

RK = Path(r"C:\Users\david\projects\ssbmNucleus-master\modellab\rigkits")
REF = json.load(open(r"C:\Users\david\projects\ssbmNucleus-master\modellab\bone_names_reference.json"))


def expected_part(name):
    n = name.lower()
    if n in ("topn", "transn", "xrotn", "yrotn", "thrown"):
        return "util"
    if n.startswith("l") and any(k in n for k in
                                 ("leg", "knee", "foot", "toe")):
        return "l_leg"
    if n.startswith("r") and any(k in n for k in
                                 ("leg", "knee", "foot", "toe")):
        return "r_leg"
    if n.startswith("l") and any(k in n for k in
                                 ("shoulder", "arm", "hand", "thumb", "1st",
                                  "2nd", "3rd", "4th", "have", "side")):
        return "l_arm"
    if n.startswith("r") and any(k in n for k in
                                 ("shoulder", "arm", "hand", "thumb", "1st",
                                  "2nd", "3rd", "4th", "have", "side")):
        return "r_arm"
    if any(k in n for k in ("neck", "head", "hat", "mouth", "nose", "hige",
                            "tooth", "eye")):
        return "head"
    return "torso"     # hip, waist, bust, collar, holster, pad


CASES = {"Mario": ("mario", "PlMr"), "Captain Falcon": ("captain_falcon", "PlCa")}
for char, (slug, code) in CASES.items():
    kit = smd.load(RK / slug / f"{slug}_vanilla.smd")
    labels = label_parts(kit, dynamic_roots=load_dynamics(code))
    ref = REF[char]
    bad = []
    for idx, name in ref.items():
        got = labels.get(int(idx))
        want = expected_part(name)
        # PadN sits under RShoulderN — subtree puts it in r_arm, fine
        if name == "PadN" and got == "r_arm":
            continue
        if got != want:
            bad.append(f"  {idx:>3} {name:<14} want={want:<6} got={got}")
    print(f"{char}: {len(ref) - len(bad)}/{len(ref)} bones match")
    for line in bad:
        print(line)

for slug, code in [("fox", "PlFx"), ("falco", "PlFc"),
                   ("marth", "PlMs"), ("ganondorf", "PlGn")]:
    kit = smd.load(RK / slug / f"{slug}_vanilla.smd")
    labels = label_parts(kit, dynamic_roots=load_dynamics(code))
    from collections import Counter
    print(f"{slug}: {dict(Counter(labels.values()))}")
