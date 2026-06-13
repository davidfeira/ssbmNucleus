"""Dump a fighter's FULL dynamic (cloth physics) definitions — chain bone
indices + the 15-float SBM_DynamicParams per moving joint + desc PARAM1-3 —
for reuse in mexCostume accessories (the wiki: copy params from similar
existing dynamic joints).

usage: dump_dyn_params.py <PlXx> <out.json>
"""
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from skinlab.datprobe import DatFile  # noqa: E402

FILES = Path(__file__).resolve().parents[0].parent / "storage" / "test-base" / "files"

code, out_path = sys.argv[1], sys.argv[2]
d = DatFile(FILES / f"{code}.dat")


def rptr(off):
    return d.u32(off) if off in d.relocs else None


def f32(off):
    return struct.unpack_from(">f", d.raw, 0x20 + off)[0]


ft = next(o for n, o in d.roots if n.startswith("ftData"))
grp = rptr(ft + 0x2C)
n = d.u32(grp + 0x00)
arr = rptr(grp + 0x04)

chains = []
for i in range(n):
    desc = arr + i * 0x18
    bone = d.u32(desc + 0x00)
    p_arr = rptr(desc + 0x04)
    p_n = d.u32(desc + 0x08)
    entry = {
        "bone": bone,
        "PARAM1": f32(desc + 0x0C),
        "PARAM2": f32(desc + 0x10),
        "PARAM3": f32(desc + 0x14),
        "joints": [],
    }
    for j in range(p_n):
        base = p_arr + j * 0x3C
        entry["joints"].append([f32(base + k * 4) for k in range(15)])
    chains.append(entry)

Path(out_path).write_text(json.dumps(chains, indent=1))
print(f"{code}: {len(chains)} chains -> {out_path}")
for c in chains:
    print(f"  bone {c['bone']}: {len(c['joints'])} dynamic joints, "
          f"desc params {c['PARAM1']:.3g}/{c['PARAM2']:.3g}/{c['PARAM3']:.3g}")
