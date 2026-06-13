"""Apply the LowPoly repoint to a LIVE vault custom-character fighter.zip so its
shadow + magnifier render (Melee draws the shadow from the low-poly model; these
custom chars have empty low DObjs). Replaces ONLY the ftData inside the zip;
every other entry is copied byte-for-byte. Backs up the whole char folder first,
builds to a temp zip, verifies, then atomically replaces.

usage: apply_repoint_to_vault.py <slug> <ftCode> <costume.smd>
   ex: apply_repoint_to_vault.py deoxys PlUu modellab/vault_lowpoly/PlUuNr.smd
"""
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

slug, ftcode, smd = sys.argv[1], sys.argv[2], str(Path(sys.argv[3]).resolve())
live = ROOT / "storage" / "custom_characters" / slug / "fighter.zip"
assert live.exists(), f"no fighter.zip: {live}"

# 1. back up the whole char folder (timestamped, outside the repo)
ts = time.strftime("%Y%m%d-%H%M%S")
bk = ROOT.parent / "_vault_backups" / f"{ts}-{slug}-apply" / slug
bk.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(live.parent, bk)
print(f"backup -> {bk}")

work = ROOT / "modellab" / "vault_lowpoly" / f"apply_{slug}"
work.mkdir(parents=True, exist_ok=True)

# 2. extract the CURRENT ftData (whatever the live state is right now)
with zipfile.ZipFile(live) as z:
    names = z.namelist()
    (work / f"{ftcode}.dat").write_bytes(z.read(f"{ftcode}.dat"))

# 3. repoint it (run the standalone script — it sets up its own import paths)
rp_out = work / f"{ftcode}_rp.dat"
rp_out.unlink(missing_ok=True)
r = subprocess.run([sys.executable, str(ROOT / "modellab" / "repoint_lowpoly.py"),
                    str(work / f"{ftcode}.dat"), smd, str(rp_out)],
                   capture_output=True, text=True)
print(r.stdout.strip())
if not rp_out.exists():
    sys.exit(f"repoint failed:\n{r.stdout}\n{r.stderr}")
newdat = rp_out.read_bytes()

# 4. repack to a TEMP zip, preserving every other entry exactly
tmp = work / "fighter_new.zip"
with zipfile.ZipFile(live) as zin, zipfile.ZipFile(tmp, "w") as zout:
    for it in zin.infolist():
        data = newdat if it.filename == f"{ftcode}.dat" else zin.read(it.filename)
        zout.writestr(it, data, compress_type=it.compress_type)

# 5. verify the temp zip before touching the live one
with zipfile.ZipFile(tmp) as z:
    assert z.testzip() is None, "temp zip failed integrity"
    assert z.read(f"{ftcode}.dat") == newdat, "ftData not swapped"
    assert set(z.namelist()) == set(names), "entry set changed!"

# 6. atomic replace
os.replace(tmp, live)
print(f"APPLIED repoint to {live}")
print(f"  (restore from: {bk})")
