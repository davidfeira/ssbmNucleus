"""Structural diff of two costume DATs (vanilla vs round-trip) using datprobe."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ssbmNucleus" / "backend"))
from skinlab.datprobe import DatFile  # noqa: E402


def jobj_summary(d, root_off):
    jobjs = d._iter_tree(root_off, 0x08, 0x0C)
    per_joint = []
    for j in jobjs:
        flags = d.u32(j + 0x04)
        dobj = d.ptr(j + 0x10)
        n = 0
        while dobj is not None:
            dobj = d.ptr(dobj + 0x04)
            n += 1
        per_joint.append((n, flags))
    return per_joint


def matanim_summary(d, root_off):
    joints = d._iter_tree(root_off, 0x00, 0x04)
    per_joint = []
    for joint in joints:
        matanim = d.ptr(joint + 0x08)
        n = 0
        while matanim is not None:
            matanim = d.ptr(matanim + 0x00)
            n += 1
        per_joint.append(n)
    return per_joint


def describe(path):
    d = DatFile(path)
    out = {"roots": [n for n, _ in d.roots]}
    for name, off in d.roots:
        if name.endswith("_matanim_joint"):
            out["matanim"] = matanim_summary(d, off)
        elif name.endswith("_joint"):
            out["jobj"] = jobj_summary(d, off)
    return out


a = describe(sys.argv[1])
b = describe(sys.argv[2])

print("A roots:", a["roots"])
print("B roots:", b["roots"])
print(f"A joints: {len(a['jobj'])}   B joints: {len(b['jobj'])}")
print(f"A total dobjs: {sum(n for n, _ in a['jobj'])}   B total dobjs: {sum(n for n, _ in b['jobj'])}")

for i, ((na, fa), (nb, fb)) in enumerate(zip(a["jobj"], b["jobj"])):
    if na != nb or fa != fb:
        print(f"  joint {i}: dobjs {na}->{nb}  flags {fa:08x}->{fb:08x}")

ma, mb = a.get("matanim", []), b.get("matanim", [])
print(f"A matanim joints: {len(ma)}   B matanim joints: {len(mb)}")
if ma and mb:
    for i, (x, y) in enumerate(zip(ma, mb)):
        if x != y:
            print(f"  matanim joint {i}: count {x}->{y}")
