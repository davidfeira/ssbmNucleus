"""ctrl_build.py -- build a small sequential test ISO with a SPECIFIED mexcli exe,
to compare the original (win-x64, untouched) vs the rebuilt one in-game.
Run from backend/:  python ctrl_build.py "<path-to-mexcli.exe>" <iso_name>
"""
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH  # noqa: E402
from stress_build import TEST_BASE, parse_json  # noqa: E402

EXE = sys.argv[1]
NAME = sys.argv[2] if len(sys.argv) > 2 else "ctrl"


def mex(args):
    return subprocess.run([EXE] + [str(a) for a in args], capture_output=True, text=True, timeout=600)


print("using exe:", EXE)
lf = parse_json(mex(["list-fighters", str((STORAGE_PATH / "test-base" / "project.mexproj").resolve())]).stdout) or {}
print("list-fighters: success =", lf.get("success"), "| total =", sum(f["costumeCount"] for f in lf.get("fighters", [])))

w = (STORAGE_PATH / "test-builds" / f"{NAME}_proj").resolve()
if w.exists():
    shutil.rmtree(w, ignore_errors=True)
shutil.copytree(TEST_BASE, w)
proj = str((w / "project.mexproj").resolve())
plan = {f: [str(z.resolve()) for z in sorted((STORAGE_PATH / f).glob("*.zip"))[:8]]
        for f in ["Fox", "Falco", "Marth"]}
for f, zs in plan.items():
    for z in zs:
        r = parse_json(mex(["import-costume", proj, f, z]).stdout) or {}
        if not r.get("success"):
            raise SystemExit(f"import fail {f}: {r.get('error')}")
iso = (STORAGE_PATH.parent / "output" / f"{NAME}.iso").resolve()
cp = mex(["export", proj, str(iso), "1.0", "false", "false"])
print(NAME, "export: success =", (parse_json(cp.stdout) or {}).get("success"),
      "| size =", (iso.stat().st_size // 1048576 if iso.exists() else "NO"), "MiB")
shutil.rmtree(w, ignore_errors=True)
