"""Inject a decimated low-poly into EVERY color model of a vault custom char's
fighter.zip (fills each color's empty low DObj slot via HSDRawViewer
--inject-lowpoly), so Melee's drop-shadow + magnifier are vanilla-cheap instead
of redrawing the full high model. The ftData comes from the SOURCE zip as-is —
pass the ORIGINAL (pre-repoint) fighter.zip so the low table still points at the
real low DObjs (e.g. Deoxys {19-37}) where the injected geometry now lives.

Backs up the live char folder, injects each color, verifies, atomically swaps.

usage: inject_lowpoly_to_vault.py <slug> <ftCode> <jointSymbol> <lowpoly.smd> <source_fighter.zip>
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXE = ROOT / ("utility/tools/HSDLib/HSDRawViewer/bin/Release/"
             "net6.0-windows/HSDRawViewer.exe")
sys.path.insert(0, str(ROOT / "backend"))
from skinlab.datprobe import DatFile  # noqa: E402

slug, ftcode, jsym = sys.argv[1], sys.argv[2], sys.argv[3]
lowsmd = str(Path(sys.argv[4]).resolve())
source = Path(sys.argv[5])
live = ROOT / "storage" / "custom_characters" / slug / "fighter.zip"

# low DObj index = first entry of the SOURCE ftData's (original) low table
with zipfile.ZipFile(source) as z:
    ftbytes = z.read(f"{ftcode}.dat")
tf = tempfile.NamedTemporaryFile(suffix=".dat", delete=False)
tf.write(ftbytes)
tf.close()
d = DatFile(tf.name)
ft = next(o for n, o in d.roots if n.startswith("ftData"))
lk = d.ptr(ft + 0x08)
_rp = lambda o: d.u32(o) if o in d.relocs else None  # noqa: E731
tb = _rp(_rp(lk + 4) + 4)
cnt = d.u32(tb)
arr = _rp(tb + 4)
low = sorted({i for k in range(cnt)
              for i in d.raw[0x20 + _rp(arr + k * 8 + 4):
                            0x20 + _rp(arr + k * 8 + 4) + d.u32(arr + k * 8)]})
os.unlink(tf.name)
if not low:
    sys.exit("source ftData has no low table")
low_idx = low[0]
print(f"low DObj index (from source ftData): {low_idx}  (low set {low[0]}..{low[-1]})")

ts = time.strftime("%Y%m%d-%H%M%S")
bk = ROOT.parent / "_vault_backups" / f"{ts}-{slug}-inject" / slug
bk.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(live.parent, bk)
print(f"backup -> {bk}")

work = ROOT / "modellab" / "vault_lowpoly" / f"inject_{slug}"
if work.exists():
    shutil.rmtree(work)
work.mkdir(parents=True)


def inject_dat(dat_bytes, name):
    src = work / name
    src.write_bytes(dat_bytes)
    out = work / name.replace(".dat", "_lp.dat")
    r = subprocess.run([str(EXE), "--inject-lowpoly", str(src), jsym, lowsmd,
                        str(low_idx), str(out)],
                       capture_output=True, text=True, timeout=300)
    if not out.exists():
        raise RuntimeError(f"inject failed for {name}:\n{r.stdout[-600:]}\n{r.stderr[-300:]}")
    print(f"  {name}: {r.stdout.strip().splitlines()[-1]}")
    return out.read_bytes()


items = []
with zipfile.ZipFile(source) as zin:
    for it in zin.infolist():
        data = zin.read(it.filename)
        if it.filename.startswith(ftcode) and it.filename.endswith(".zip"):
            inner = it.filename[:-4] + ".dat"            # PlUuNr.zip -> PlUuNr.dat
            cz = io.BytesIO()
            with zipfile.ZipFile(io.BytesIO(data)) as zi, \
                    zipfile.ZipFile(cz, "w") as zo:
                for cit in zi.infolist():
                    cdata = zi.read(cit.filename)
                    if cit.filename == inner:
                        cdata = inject_dat(cdata, inner)
                    zo.writestr(cit, cdata, compress_type=cit.compress_type)
            data = cz.getvalue()
        items.append((it, data))

tmp = work / "fighter_new.zip"
with zipfile.ZipFile(tmp, "w") as zout:
    for it, data in items:
        zout.writestr(it, data, compress_type=it.compress_type)
with zipfile.ZipFile(tmp) as z:
    assert z.testzip() is None, "temp fighter.zip failed integrity"
    assert set(z.namelist()) == set(zipfile.ZipFile(source).namelist())

os.replace(tmp, live)
print(f"APPLIED injected low-poly to all {ftcode}* colors -> {live}")
print(f"  restore from: {bk}")
