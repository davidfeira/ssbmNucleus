"""Build a decimated LOW-POLY SMD from a costume's exported high model, for the
HSDRawViewer --inject-lowpoly command. The output carries the costume's own
skeleton (so the import preserves it and the injector can remap envelopes onto
the real joints) + one textured mesh group at ~target tris (vanilla low-poly is
~420). Weights come from the nearest high vertex.

usage: build_lowpoly_smd.py <costume_export.smd> <out_lowpoly.smd> [target_tris]
"""
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import numpy as np  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402

from modellab import smd as S  # noqa: E402
from modellab.rig import ForeignMesh, decimate, recompute_normals  # noqa: E402

src_path = Path(sys.argv[1])
out_path = Path(sys.argv[2])
target = int(sys.argv[3]) if len(sys.argv) > 3 else 420

src = S.load(src_path)
# skeleton = every bone EXCEPT the mesh placeholder nodes (parent -1, _Object_)
skeleton = [b for b in src.bones
            if not (b.parent == -1 and "_Object_" in b.name)]
if not src.triangles:
    sys.exit("source SMD has no geometry")

tri_pos = np.array([[v.pos for v in t.verts] for t in src.triangles], float)
tri_norm = np.array([[v.normal for v in t.verts] for t in src.triangles], float)
tri_uv = np.array([[v.uv for v in t.verts] for t in src.triangles], float)
tri_mat = [t.material for t in src.triangles]
corner_w = [v.weights for t in src.triangles for v in t.verts]

fm = ForeignMesh(tri_pos, tri_norm, tri_uv, tri_mat, {},
                 ["hi"] * len(src.triangles))
lf = decimate(fm, target) if len(src.triangles) > target else fm
recompute_normals(lf)
_, nn = cKDTree(tri_pos.reshape(-1, 3)).query(lf.tri_pos.reshape(-1, 3),
                                              workers=-1)

# single material -> the largest source texture (best magnifier look; the
# shadow is a flat silhouette so the texture is cosmetic there)
sidecar_path = Path(str(src_path) + ".textures.json")
sidecar = json.loads(sidecar_path.read_text()) if sidecar_path.exists() else {}
low_mat = None
if sidecar:
    low_mat = max(sidecar,
                  key=lambda m: (src_path.parent / sidecar[m]).stat().st_size
                  if (src_path.parent / sidecar[m]).exists() else 0)
low_mat = low_mat or (tri_mat[0] if tri_mat else "mat0")

next_id = max(b.id for b in src.bones) + 1
out = S.SMD(bones=list(skeleton) + [S.Bone(id=next_id, name="Joint_0_Object_0",
                                           parent=-1)])
for t in range(len(lf.tri_pos)):
    verts = []
    for c in range(3):
        verts.append(S.Vertex(
            pos=tuple(lf.tri_pos[t][c]), normal=tuple(lf.tri_norm[t][c]),
            uv=tuple(lf.tri_uv[t][c]), weights=corner_w[nn[t * 3 + c]],
            parent=next_id))
    out.triangles.append(S.Triangle(material=low_mat, verts=tuple(verts)))
out_path.parent.mkdir(parents=True, exist_ok=True)
S.save(out, out_path)

# texture sidecar (single material) + copy the texture next to the SMD
if sidecar and low_mat in sidecar:
    tex = src_path.parent / sidecar[low_mat]
    dest = out_path.parent / sidecar[low_mat]
    if tex.exists() and tex.resolve() != dest.resolve():
        shutil.copyfile(tex, dest)
    Path(str(out_path) + ".textures.json").write_text(
        json.dumps({low_mat: sidecar[low_mat]}))

print(f"low-poly SMD: {len(lf.tri_pos)} tris (from {len(src.triangles)}), "
      f"{len(skeleton)} joints, material '{low_mat}' -> {out_path}")
