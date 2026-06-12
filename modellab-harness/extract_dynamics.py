"""Extract per-character DYNAMIC bone chains (cloth/tail physics) from vanilla
Pl*.dat ftData+0x2C (SBM_PhysicsGroup): these bones are physics-driven and
foreign geometry must not be weighted to them (capes grabbing fox's tail chain
= the in-game flailing). Writes backend/modellab/dynamic_bones.json:
{code: [chain root bone indices]} — the rigger expands each root to its
subtree using the rig kit's bone tree."""
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from skinlab.datprobe import DatFile  # noqa: E402

SRC = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\storage\test-base\files")
OUT = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend\modellab\dynamic_bones.json")

CODES = ['PlCa', 'PlCl', 'PlDk', 'PlDr', 'PlFc', 'PlFe', 'PlFx', 'PlGn',
         'PlGw', 'PlKb', 'PlKp', 'PlLg', 'PlLk', 'PlMr', 'PlMs', 'PlMt',
         'PlNn', 'PlNs', 'PlPc', 'PlPe', 'PlPk', 'PlPp', 'PlPr', 'PlSk',
         'PlSs', 'PlYs', 'PlZd']


def rptr(d, off):
    return d.u32(off) if off in d.relocs else None


tables = {}
for code in CODES:
    dat = SRC / f"{code}.dat"
    if not dat.exists():
        continue
    try:
        d = DatFile(dat)
        ft = next(o for n, o in d.roots if n.startswith('ftData'))
        grp = rptr(d, ft + 0x2C)
        if grp is None:
            tables[code] = []
            print(f"{code}: no physics group")
            continue
        n = d.u32(grp + 0x00)
        arr = rptr(d, grp + 0x04)
        roots = []
        if arr is not None and n <= 64:
            for i in range(n):
                desc = arr + i * 0x18
                bone = d.u32(desc + 0x00)
                nparams = d.u32(desc + 0x08)
                roots.append({"bone": bone, "chain_len": nparams})
        tables[code] = roots
        print(f"{code}: {len(roots)} dynamic chains "
              f"{[(r['bone'], r['chain_len']) for r in roots]}")
    except Exception as e:
        tables[code] = []
        print(f"{code}: ERROR {e}")

OUT.write_text(json.dumps(tables, indent=1))
print("->", OUT)
