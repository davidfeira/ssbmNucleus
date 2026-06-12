"""Render a raw mesh (GLB/OBJ/SMD) to a preview PNG without rigging —
the lab-side twin of the studio's mesh-approval step.

usage: preview_mesh.py <mesh> <out.png>
"""
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\david\projects\ssbmNucleus-master\ssbmNucleus\backend")
from modellab.rig import render_mesh_preview  # noqa: E402

render_mesh_preview(Path(sys.argv[1]), Path(sys.argv[2]))
print("saved", sys.argv[2])
