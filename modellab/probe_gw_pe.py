"""Walk PlGw/PlPe lookup structures word by word with reloc checks to find
where the visibility chase derails."""
import sys

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from pathlib import Path

from skinlab.datprobe import DatFile

FILES = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\storage\test-base\files")

for code in ["PlGw", "PlPe"]:
    d = DatFile(FILES / f"{code}.dat")
    ft = next(o for n, o in d.roots if n.startswith("ftData"))
    lookups = d.ptr(ft + 0x08)
    vis_len = d.u32(lookups + 0x00)
    vis_arr = d.ptr(lookups + 0x04)
    print(f"\n{code}: lookups@{lookups:#x} vis_len={vis_len} vis_arr={vis_arr:#x} "
          f"data_size={d.data_size:#x}")
    for c in range(vis_len):
        entry = vis_arr + c * 0x10
        words = [d.u32(entry + i * 4) for i in range(4)]
        inrel = [(entry + i * 4) in d.relocs for i in range(4)]
        print(f"  entry {c}: " + "  ".join(
            f"{w:#x}{'*' if r else ' '}" for w, r in zip(words, inrel)))
        # chase high table if it's a real pointer
        if inrel[0]:
            tbl = words[0]
            n = d.u32(tbl + 0x00)
            arr_ok = (tbl + 0x04) in d.relocs
            print(f"    high tbl@{tbl:#x}: count={n} arr_reloc={arr_ok}")
