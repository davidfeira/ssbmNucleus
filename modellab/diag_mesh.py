"""Diagnose a foreign mesh load + decimate in isolation, reporting size and
timing at each stage so we can see where the pilot GLB blows up RAM.

usage: diag_mesh.py <mesh>
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import numpy as np  # noqa: E402

from modellab.rig import decimate, load_foreign  # noqa: E402

mesh_path = sys.argv[1]
print(f"loading {mesh_path}", flush=True)
t = time.perf_counter()
fm = load_foreign(Path(mesh_path))
print(f"loaded: {len(fm.tri_pos)} tris  in {time.perf_counter()-t:.1f}s", flush=True)

groups = list(dict.fromkeys(getattr(fm, "tri_group", []) or ["<none>"]))
from collections import Counter  # noqa: E402
gc = Counter(getattr(fm, "tri_group", []))
print(f"groups: {len(groups)}  -> {dict(list(gc.items())[:10])}", flush=True)
print(f"textures: {[(k, getattr(v,'size',None)) for k,v in fm.textures.items()]}",
      flush=True)
verts = fm.tri_pos.reshape(-1, 3)
print(f"bbox: {verts.min(axis=0)} .. {verts.max(axis=0)}", flush=True)

print("--- decimate to 9000 ---", flush=True)
t = time.perf_counter()
fm2 = decimate(fm, 9000)
print(f"decimated: {len(fm2.tri_pos)} tris  in {time.perf_counter()-t:.1f}s",
      flush=True)
print("OK", flush=True)
