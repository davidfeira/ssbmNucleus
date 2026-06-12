"""Dump SBM_PlayerModelLookupTables (costume visibility lookups) from a Pl*.dat."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ssbmNucleus" / "backend"))
from skinlab.datprobe import DatFile  # noqa: E402

d = DatFile(sys.argv[1])
print("roots:", [n for n, _ in d.roots])
ft_off = d.roots[0][1]  # ftData root

lookups = d.ptr(ft_off + 0x08)
vis_len = d.u32(lookups + 0x00)
vis_arr = d.ptr(lookups + 0x04)
print(f"costume visibility lookups: {vis_len}")

for c in range(vis_len):
    entry = vis_arr + c * 0x10
    print(f"-- costume {c}:")
    for name, off in (("HighPoly", 0x00), ("LowPoly", 0x04),
                      ("MetalPoly", 0x08), ("MetalMain", 0x0C)):
        table = d.ptr(entry + off)
        if table is None:
            print(f"   {name}: (null)")
            continue
        count = d.u32(table + 0x00)
        entries_arr = d.ptr(table + 0x04)
        groups = []
        for i in range(count):
            le = entries_arr + i * 0x8
            n = d.u32(le + 0x00)
            data = d.ptr(le + 0x04)
            if data is None:
                groups.append([])
            else:
                raw = d.raw[len(d.raw) - len(d.raw):]  # noqa
                groups.append(list(d.raw[0x20 + data:0x20 + data + n]))
        print(f"   {name}: {count} lookup entries: {groups}")
