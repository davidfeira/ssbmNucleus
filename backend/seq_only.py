"""seq_only.py -- build ONE sequential-import project (kept) with the current mexcli.
Used to byte-diff the ORIGINAL exe's output vs the rebuilt exe's (import_ab's ab_seq).
Run from backend/:  python seq_only.py <project_name>
"""
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH, MEXCLI_PATH  # noqa: E402
from stress_build import run_mexcli, parse_json, TEST_BASE  # noqa: E402

name = sys.argv[1] if len(sys.argv) > 1 else "orig_seq"
print(f"using mexcli: {Path(MEXCLI_PATH).resolve()}")
w = (STORAGE_PATH / "test-builds" / name).resolve()
if w.exists():
    shutil.rmtree(w, ignore_errors=True)
shutil.copytree(TEST_BASE, w)
proj = str((w / "project.mexproj").resolve())
plan = {f: [str(z.resolve()) for z in sorted((STORAGE_PATH / f).glob("*.zip"))[:8]]
        for f in ["Fox", "Falco", "Marth"]}
for f, zs in plan.items():
    for z in zs:
        r = parse_json(run_mexcli(["import-costume", proj, f, z]).stdout) or {}
        if not r.get("success"):
            raise SystemExit(f"import failed {f}: {r.get('error')}")
print(f"built {name} (sequential, 24 costumes) at {w}")
