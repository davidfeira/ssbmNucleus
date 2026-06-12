"""Inspect per-POBJ envelope data in a costume DAT: which joints (by tree
index) and weights each DObj's POBJs reference, plus per-joint flag checks.
For a rigid single-bone import, every envelope should be (joint N, 1.0)."""
import struct
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from skinlab.datprobe import DatFile, HEADER_SIZE  # noqa: E402

d = DatFile(sys.argv[1])
root = next(o for n, o in d.roots if n.endswith("_joint") and "matanim" not in n)
jobjs = d._iter_tree(root, 0x08, 0x0C)
jobj_index = {off: i for i, off in enumerate(jobjs)}


def f32(off):
    return struct.unpack_from(">f", d.raw, HEADER_SIZE + off)[0]


print(f"{len(jobjs)} joints")
dobj = d.ptr(jobjs[0] + 0x10)
di = 0
issues = 0
while dobj is not None:
    pobj = d.ptr(dobj + 0x0C)
    pi = 0
    summary = []
    while pobj is not None:
        flags = d.u16(pobj + 0x0C)
        env_list = d.ptr(pobj + 0x14)
        envs = []
        if flags & 0x2000 and env_list:   # ENVELOPE
            k = 0
            while True:
                env_ptr = d.ptr(env_list + k * 4)
                if env_ptr is None:
                    break
                pairs = []
                m = 0
                while True:
                    j = d.ptr(env_ptr + m * 8)
                    if j is None:
                        break
                    wgt = f32(env_ptr + m * 8 + 4)
                    pairs.append((jobj_index.get(j, f"?{j:x}"), round(wgt, 3)))
                    m += 1
                envs.append(pairs)
                k += 1
        summary.append((pi, hex(flags), len(envs), envs[:3]))
        pobj = d.ptr(pobj + 0x04)
        pi += 1
    if di < 8 or any(e for _, _, n, e in summary for e in [e] if n and str(e).count("?")):
        print(f"dobj {di}: {summary}")
    dobj = d.ptr(dobj + 0x04)
    di += 1
print(f"total root dobjs: {di}")
