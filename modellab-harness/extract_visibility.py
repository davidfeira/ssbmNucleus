"""Extract per-character costume visibility tables (HighPoly/LowPoly DObj
index sets) from Pl*.dat fighter data files into visibility_tables.json."""
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from skinlab.datprobe import DatFile  # noqa: E402

# NOTE: the m-ex/Beyond-Melee fighter dats parse with this ptr-chase; VANILLA
# Pl*.dat files do not (ftData+0x08 resolves to nothing there — layout quirk
# unresolved). Vanilla model layouts for these chars are unmodified in BM, so
# the BM tables are valid for vanilla rig kits.
SRC = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\output\iso_scan\6ae8dd32f1bf\extracted\Beyond Melee v2.0 Beta\P-GALE\files")
OUT = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend\modellab\visibility_tables.json")

CODES = ['PlCa', 'PlCl', 'PlDk', 'PlDr', 'PlFc', 'PlFe', 'PlFx', 'PlGn',
         'PlGw', 'PlKb', 'PlKp', 'PlLg', 'PlLk', 'PlMr', 'PlMs', 'PlMt',
         'PlNn', 'PlNs', 'PlPc', 'PlPe', 'PlPk', 'PlPp', 'PlPr', 'PlSk',
         'PlSs', 'PlYs', 'PlZd']


def read_table(d, lookups, off):
    table = d.ptr(lookups + off)
    if table is None:
        return None
    count = d.u32(table + 0x00)
    arr = d.ptr(table + 0x04)
    entries = []
    for i in range(count):
        le = arr + i * 0x8
        n = d.u32(le + 0x00)
        data = d.ptr(le + 0x04)
        entries.append(list(d.raw[0x20 + data:0x20 + data + n]) if data else [])
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
            continue
        vis_len = d.u32(lookups + 0x00)
        vis_arr = d.ptr(lookups + 0x04)
        costumes = []
        for c in range(vis_len):
            entry = vis_arr + c * 0x10
            costumes.append({
                "high": read_table(d, entry, 0x00),
                "low": read_table(d, entry, 0x04),
            })
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
