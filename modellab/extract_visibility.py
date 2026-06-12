"""Extract per-character costume visibility tables (HighPoly/LowPoly DObj
index sets) from Pl*.dat fighter data files into visibility_tables.json."""
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from skinlab.datprobe import DatFile  # noqa: E402

# VANILLA fighter dats store the lookup tables at data offset 0 with the
# pointer relocated — needs the reloc-aware datprobe.ptr (0-in-relocs is a
# real pointer, not null). Never extract these from a mod build: Beyond Melee
# restructured 7 characters' models and those tables don't fit vanilla kits.
SRC = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\storage\test-base\files")
OUT = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend\modellab\visibility_tables.json")

CODES = ['PlCa', 'PlCl', 'PlDk', 'PlDr', 'PlFc', 'PlFe', 'PlFx', 'PlGn',
         'PlGw', 'PlKb', 'PlKp', 'PlLg', 'PlLk', 'PlMr', 'PlMs', 'PlMt',
         'PlNn', 'PlNs', 'PlPc', 'PlPe', 'PlPk', 'PlPp', 'PlPr', 'PlSk',
         'PlSs', 'PlYs', 'PlZd']


def rptr(d, off):
    """Pointer ONLY if the field offset is in the reloc table (vanilla dats
    pad lookup arrays: vis_len over-counts and trailing entries are garbage
    non-pointer words — G&W claims 11 entries, has 1)."""
    return d.u32(off) if off in d.relocs else None


def read_table(d, lookups, off):
    table = rptr(d, lookups + off)
    if table is None:
        return None
    count = d.u32(table + 0x00)
    arr = rptr(d, table + 0x04)
    if arr is None or count > 64:
        return None
    entries = []
    for i in range(count):
        le = arr + i * 0x8
        n = d.u32(le + 0x00)
        data = rptr(d, le + 0x04)
        entries.append(list(d.raw[0x20 + data:0x20 + data + n])
                       if data is not None and n <= 256 else [])
    return entries


tables = {}
for code in CODES:
    dat = SRC / f"{code}.dat"
    if not dat.exists():
        continue
    try:
        d = DatFile(dat)
        ft = next(o for n, o in d.roots if n.startswith('ftData'))
        lookups = d.ptr(ft + 0x08)
        if lookups is None:
            tables[code] = {"error": "no lookup tables"}
            print(f"{code}: no lookup tables")
            continue
        vis_len = d.u32(lookups + 0x00)
        vis_arr = rptr(d, lookups + 0x04)
        costumes = []
        for c in range(vis_len):
            entry = vis_arr + c * 0x10
            tbl = {
                "high": read_table(d, entry, 0x00),
                "low": read_table(d, entry, 0x04),
            }
            if tbl["high"] is None and tbl["low"] is None:
                continue          # padding entry (vis_len over-counts)
            costumes.append(tbl)
        tables[code] = {"costumes": costumes}
        c0 = costumes[0]
        high = sorted({i for e in (c0['high'] or []) for i in e})
        low = sorted({i for e in (c0['low'] or []) for i in e})
        print(f"{code}: {vis_len} costume tables; c0 high={len(high)} low={len(low)} "
              f"max={max(high + low) if high + low else '-'}")
    except Exception as e:
        tables[code] = {"error": str(e)}
        print(f"{code}: ERROR {e}")

OUT.write_text(json.dumps(tables, indent=1))
print("->", OUT)
