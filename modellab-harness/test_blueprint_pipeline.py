"""Drive blueprints.model_lab._pipeline directly (what the UI runs)."""
import sys
import tempfile
from pathlib import Path

BACKEND = Path(r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
sys.path.insert(0, str(BACKEND))
import os
os.chdir(BACKEND)

from blueprints import model_lab

# no socketio in this context — stub the emitter
model_lab._emit = lambda event, payload: print(f"  [{event}] {payload.get('message', payload)}")

work = Path(tempfile.mkdtemp(prefix="modellab_bp_"))
session = model_lab._pipeline(
    character="Fox",
    theme="",
    mesh_path=Path(r"C:\Users\david\projects\assetFarm\test_textured.glb"),
    rot_y=0, max_tris=6000, work_dir=work,
)
print("dat bytes:", len(session["datBytes"]))
print("dat name:", session["datName"])
print("preview:", "yes" if session["preview"] else "none")

out = Path(r"C:\Users\david\projects\ssbmNucleus-master\modellab\out\blueprint_test")
out.mkdir(parents=True, exist_ok=True)
(out / session["datName"]).write_bytes(session["datBytes"])
if session["preview"]:
    import base64
    (out / "preview.png").write_bytes(
        base64.b64decode(session["preview"].split(",", 1)[1]))
print("saved to", out)
