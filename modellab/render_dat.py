"""Render an imported costume DAT through HSDRaw's REAL textured renderer
(--csp) — the game-accurate check the grey Python painters can't do. The
painters paint flat grey and derive their own normals, so they are blind to
texture/UV/material/stored-normal bugs (e.g. the AI-costume UV scramble that
read as in-game 'chrome'). This renders the actual DAT the way the game shades
it, so those bugs show up offline.

usage: render_dat.py <costume.dat> <out.png>
"""
import subprocess
import sys
from pathlib import Path

EXE = Path(__file__).resolve().parents[1] / (
    "utility/tools/HSDLib/HSDRawViewer/bin/Release/net6.0-windows/"
    "HSDRawViewer.exe")


def render_dat(dat_path, out_png, timeout=240):
    """Run HSDRaw --csp on a costume DAT; returns True on success."""
    out = Path(out_png)
    if out.exists():
        out.unlink()
    r = subprocess.run([str(EXE), "--csp", str(dat_path), str(out)],
                       capture_output=True, text=True, timeout=timeout)
    if not out.exists():
        sys.stderr.write(f"render failed:\n{r.stdout[-600:]}\n{r.stderr[-400:]}\n")
        return False
    return True


if __name__ == "__main__":
    ok = render_dat(sys.argv[1], sys.argv[2])
    print(("rendered " if ok else "FAILED ") + sys.argv[2])
    sys.exit(0 if ok else 1)
