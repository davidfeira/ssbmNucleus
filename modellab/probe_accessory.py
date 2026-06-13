"""Inspect a mexCostume root: accessory joint tree, dobjs, lookup tables,
dynamics — find what the runtime could choke on."""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from skinlab.datprobe import DatFile  # noqa: E402

d = DatFile(sys.argv[1])


def rptr(off):
    return d.u32(off) if off in d.relocs else None


def f32(off):
    return struct.unpack_from(">f", d.raw, 0x20 + off)[0]


print("roots:", d.roots)
mex = next((o for n, o in d.roots if n == "mexCostume"), None)
if mex is None:
    sys.exit("no mexCostume root")

vis = rptr(mex + 0x00)
mat = rptr(mex + 0x04)
n_acc = d.u32(mex + 0x08)
accs = rptr(mex + 0x0C)
print(f"mexCostume @{mex:#x}: vis={vis} mat={mat} accCount={n_acc} accs={accs}")
if vis is not None:
    print(f"  visLookup: count={d.u32(vis)} table={rptr(vis + 4)}")
if mat is not None:
    print(f"  matLookup: table={rptr(mat)}")

acc = rptr(accs + 0x00) if accs is not None else None
print(f"accessory[0] @ {acc}")
root = rptr(acc + 0x00)
print(f"  RootJoint={root:#x} AttachBone={d.u32(acc + 0x04)} "
      f"DynCount={d.u32(acc + 0x08)} DynDef={rptr(acc + 0x0C)} "
      f"LookupCount={d.u32(acc + 0x10)} Lookup={rptr(acc + 0x14)} "
      f"HitCount={d.u32(acc + 0x18)} HitDef={rptr(acc + 0x1C)} "
      f"Anim={rptr(acc + 0x20)} MatAnim={rptr(acc + 0x24)} SubAct={rptr(acc + 0x28)}")

# walk the accessory jobj tree: jobj = flags@4? HSD_JOBJ: 0x00 name?, layout:
# 0x00 = string ptr (unused), 0x04 flags, 0x08 child, 0x0C next, 0x10 dobj,
# 0x14.. trs floats
def walk(j, depth, idx):
    while j is not None:
        child = rptr(j + 0x08)
        nxt = rptr(j + 0x0C)
        dobj = rptr(j + 0x10)
        ndobj = 0
        dd = dobj
        while dd is not None:
            ndobj += 1
            dd = rptr(dd + 0x04)
        tx, ty, tz = f32(j + 0x2C), f32(j + 0x30), f32(j + 0x34)
        print(f"  {'  ' * depth}jobj[{idx[0]}] flags={d.u32(j + 4):#x} "
              f"dobjs={ndobj} t=({tx:.2f},{ty:.2f},{tz:.2f})")
        idx[0] += 1
        if child is not None:
            walk(child, depth + 1, idx)
        j = nxt


walk(root, 0, [0])

dyn = rptr(acc + 0x0C)
if dyn is not None:
    for i in range(d.u32(acc + 0x08)):
        de = rptr(dyn + i * 4)
        print(f"  dyn[{i}]: bone={d.u32(de)} params={d.u32(de + 8)} "
              f"@{rptr(de + 4)}")

lk = rptr(acc + 0x14)
if lk is not None:
    for name, off in (("high", 0), ("low", 4), ("metal", 8), ("metalmain", 12)):
        t = rptr(lk + off)
        if t is None:
            print(f"  lookup {name}: NULL")
            continue
        cnt = d.u32(t + 0x00)
        arr = rptr(t + 0x04)
        e = rptr(arr + 4) if arr is not None else None
        n = d.u32(arr) if arr is not None else 0
        ent = list(d.raw[0x20 + e:0x20 + e + n]) if e is not None else []
        print(f"  lookup {name}: tables={cnt} entry_count={n} entries={ent}")
