"""Deeper structural diff: per-DObj MObj render flags, POBJ flags/counts."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ssbmNucleus" / "backend"))
from skinlab.datprobe import DatFile  # noqa: E402


def dobj_details(d, root_off):
    out = []
    jobjs = d._iter_tree(root_off, 0x08, 0x0C)
    for j_idx, j in enumerate(jobjs):
        flags = d.u32(j + 0x04)
        if flags & (1 << 14) or flags & (1 << 5):  # SPLINE / PTCL
            continue
        dobj = d.ptr(j + 0x10)
        d_idx = 0
        while dobj is not None:
            mobj = d.ptr(dobj + 0x08)
            renderflags = d.u32(mobj + 0x04) if mobj else None
            tobjs = 0
            if mobj:
                tobj = d.ptr(mobj + 0x08)
                while tobj is not None:
                    tobjs += 1
                    tobj = d.ptr(tobj + 0x04)
            pobjs = []
            pobj = d.ptr(dobj + 0x0C)
            while pobj is not None:
                pflags = d.u16(pobj + 0x0C)
                dlsize = d.u16(pobj + 0x0E)
                pobjs.append((pflags, dlsize))
                pobj = d.ptr(pobj + 0x04)
            out.append((j_idx, d_idx, renderflags, tobjs, pobjs))
            dobj = d.ptr(dobj + 0x04)
            d_idx += 1
    return out


def root_of(d):
    return next(o for n, o in d.roots if n.endswith("_joint") and "matanim" not in n)


a = DatFile(sys.argv[1])
b = DatFile(sys.argv[2])
da = dobj_details(a, root_of(a))
db = dobj_details(b, root_of(b))
print(f"A dobjs: {len(da)}  B dobjs: {len(db)}")

for (ja, ia, rfa, ta, pa), (jb, ib, rfb, tb, pb) in zip(da, db):
    tag = f"j{ja}d{ia}"
    if (ja, ia) != (jb, ib):
        print(f"  ORDER MISMATCH at {tag} vs j{jb}d{ib}")
        break
    if rfa != rfb:
        print(f"  {tag}: renderflags {rfa:08x} -> {rfb:08x}")
    if ta != tb:
        print(f"  {tag}: tobj count {ta} -> {tb}")
    if len(pa) != len(pb):
        print(f"  {tag}: pobj count {len(pa)} -> {len(pb)}")
    else:
        for k, ((fa, sa), (fb, sb)) in enumerate(zip(pa, pb)):
            if fa != fb:
                print(f"  {tag} pobj{k}: flags {fa:04x} -> {fb:04x}")
