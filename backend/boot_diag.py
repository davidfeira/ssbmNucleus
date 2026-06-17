"""boot_diag.py -- launch the test Dolphin with output CAPTURED (boot.launch normally
sends it to DEVNULL) to find why it dies on launch. Run from backend/."""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core.config import STORAGE_PATH  # noqa: E402
from ingame.boot import DolphinBoot  # noqa: E402

iso = str((STORAGE_PATH.parent / "output" / "count-comp-511.iso").resolve())
boot = DolphinBoot(iso, None, str(STORAGE_PATH / "test-runs"), log=print)
boot.prepare()
args = [boot.exe, "-u", str(boot.user_dir), "-b", "-e", boot.iso_path]
print("ARGS:", args)
outpath = STORAGE_PATH.parent / "output" / "dolphin_stdout.txt"
with open(outpath, "wb") as out:
    p = subprocess.Popen(args, cwd=str(Path(boot.exe).parent), stdout=out, stderr=subprocess.STDOUT)
    exited = None
    for i in range(20):
        time.sleep(1)
        rc = p.poll()
        if rc is not None:
            exited = (i + 1, rc)
            break
if exited:
    print(f"Dolphin EXITED after ~{exited[0]}s, exit code {exited[1]}")
else:
    print("Dolphin still ALIVE after 20s (healthy launch); killing")
    try:
        p.terminate()
    except Exception:
        pass
print("=== captured stdout/stderr (tail) ===")
try:
    print(outpath.read_text(errors="ignore")[-2500:])
except Exception as e:
    print("(none)", e)
log = boot.user_dir / "Logs" / "dolphin.log"
if log.exists():
    print("=== dolphin.log (tail) ===")
    print(log.read_text(errors="ignore")[-2500:])
boot.cleanup()
