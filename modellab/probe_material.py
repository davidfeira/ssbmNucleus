"""Walk a costume DAT's JOBJ->DOBJ->MOBJ tree and report each material's
RenderFlags — specifically whether XLU (translucent, 1<<30) is set. XLU on a
solid costume = the importer saw IsTransparent()==true (e.g. CMPR punch-through
alpha) and flagged it translucent, which blends overlapping faces in-game
(the chrome-shard look).

usage: probe_material.py <dat> [joint_symbol_substr]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from skinlab.datprobe import DatFile  # noqa: E402

XLU = 1 << 30
DIFFUSE = 1 << 2
CONSTANT = 1 << 0
VERTEX = 1 << 1
TEX0 = 1 << 4

d = DatFile(sys.argv[1])
want = sys.argv[2] if len(sys.argv) > 2 else "_joint"


def rptr(off):
    return d.u32(off) if off in d.relocs else None


root = next((o for n, o in d.roots if want in n and n.endswith("joint")), None)
if root is None:
    root = next((o for n, o in d.roots if n.endswith("joint")), None)
print("root joint:", hex(root) if root else None)

seen_mobj = set()
flagctr = {}
n_xlu = 0
n_mobj = 0


def walk_jobj(j, depth=0):
    global n_xlu, n_mobj
    while j is not None:
        dobj = rptr(j + 0x10)
        while dobj is not None:
            mobj = rptr(dobj + 0x08)
            if mobj is not None and mobj not in seen_mobj:
                seen_mobj.add(mobj)
                rf = d.u32(mobj + 0x04)
                n_mobj += 1
                if rf & XLU:
                    n_xlu += 1
                flagctr[rf] = flagctr.get(rf, 0) + 1
            dobj = rptr(dobj + 0x04)
        child = rptr(j + 0x08)
        if child is not None:
            walk_jobj(child, depth + 1)
        j = rptr(j + 0x0C)


walk_jobj(root)
print(f"materials: {n_mobj}, with XLU: {n_xlu}")
for rf, c in sorted(flagctr.items()):
    bits = []
    if rf & CONSTANT: bits.append("CONSTANT")
    if rf & VERTEX: bits.append("VERTEX")
    if rf & DIFFUSE: bits.append("DIFFUSE")
    if rf & TEX0: bits.append("TEX0")
    if rf & XLU: bits.append("XLU")
    print(f"  RenderFlags={rf:#010x} [{'|'.join(bits)}] x{c}")
