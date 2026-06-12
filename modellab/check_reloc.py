"""Is ftData+0x08 in the reloc table for vanilla Pl*.dat (i.e. its 0x0 word a
VALID pointer to data offset 0) rather than null?"""
import sys

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from pathlib import Path

from skinlab.datprobe import DatFile

FILES = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\storage\test-base\files")
for code in ["PlFx", "PlLg", "PlNn", "PlPp", "PlGw", "PlPe", "PlGn", "PlZd"]:
    d = DatFile(FILES / f"{code}.dat")
    ft = next(o for n, o in d.roots if n.startswith("ftData"))
    off = ft + 0x08
    print(f"{code}: word={d.u32(off):#x}  off-in-relocs={off in d.relocs}")
    if off in d.relocs:
        tbl = d.u32(off)
        n = d.u32(tbl + 0x00)
        arr = d.u32(tbl + 0x04)
        print(f"   lookup table at {tbl:#x}: vis_len={n} vis_arr={arr:#x} "
              f"item_hold_bone={d.raw[0x20 + tbl + 0x10]}")
