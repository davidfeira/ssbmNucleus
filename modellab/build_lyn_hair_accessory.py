"""Build Lyn's ponytail as a fresh m-ex physics accessory (mexCostume).

The static ponytail was already removed from the body via
`HSDRawViewer --remove-tris-by-bone` (bones 46-50,56). This script takes the
SAME triangles out of the full-body SMD export, re-homes them into the HEAD
bone's local frame, rigs them to a fresh straight joint chain that traces the
real ponytail bone positions, and copies Roy's cape dynamic-params onto that
chain. Output (acc dir): cape.smd + cape.smd.textures.json + atlas png +
dynamics_local.json + attach.json -> feed to `HSDRawViewer --accessory`.

usage: build_lyn_hair_accessory.py <lyn.smd> <bind.json> <roy_cape_params.json>
                                    <atlas.png> <out_acc_dir>
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from modellab import smd  # noqa: E402

smd_path, bind_path, params_path, atlas_path, out_dir = sys.argv[1:6]
out_dir = Path(out_dir)
out_dir.mkdir(parents=True, exist_ok=True)

ATTACH_BONE = 24                      # head bone (ponytail rides this rigidly)
CLOTH_BONES = {46, 47, 48, 49, 50, 56}
# v2: glue the SKULL-CONNECTING section (band 46/56 + upper strand 47) to the
# STATIC anchor J2 so it stays fixed to the head; only the long lower strand
# (48->49->50) swings. v1 put 47 on the first dynamic joint, so the part that
# meets the skull swung free -> the visible gap.
STATIC_BONES = {46, 56, 47}           # -> J2 (static anchor, rigid to head)
DYN_BONES = [48, 49, 50]              # -> J3,J4,J5 (the swinging strand)
ANCHOR_LOCAL = 2
DYN_START_LOCAL = 3                    # J3 = first moving joint (bone 48)
SRC_TO_LOCAL = {b: ANCHOR_LOCAL for b in STATIC_BONES}
SRC_TO_LOCAL.update({b: DYN_START_LOCAL + i for i, b in enumerate(DYN_BONES)})
DYN_SRC_CHAIN = "47"                   # Roy cape chain to copy params from
CHAIN_BONES = [46] + DYN_BONES        # skeleton joints to place (anchor + dyn)

bind = json.load(open(bind_path))["bones"]
params = json.load(open(params_path))


def mat4(idx):
    m = bind[idx]["matrix"]            # row-major, row-vector convention (v' = v*M)
    return np.array(m, dtype=np.float64).reshape(4, 4)


M_head = mat4(ATTACH_BONE)
M_head_inv = np.linalg.inv(M_head)
R_inv = M_head_inv[:3, :3]


def to_head_local(p):
    v = np.array([p[0], p[1], p[2], 1.0]) @ M_head_inv
    return v[:3]


def bone_world(idx):
    return np.array(bind[idx]["pos"], dtype=np.float64)


# ---- accessory skeleton: J0 attach, J1 offset, then the chain (head-local) ----
chain_hl = {b: to_head_local(bone_world(b)) for b in CHAIN_BONES}
acc = smd.SMD()
acc.bones.append(smd.Bone(id=0, name="JOBJ_0", parent=-1))
acc.bones.append(smd.Bone(id=1, name="JOBJ_1", parent=0))
prev_hl = np.zeros(3)
prev_id = 1
for k, b in enumerate(CHAIN_BONES):
    lid = SRC_TO_LOCAL[b]
    local_pos = chain_hl[b] - prev_hl   # offset from parent (identity-rot chain)
    acc.bones.append(smd.Bone(id=lid, name=f"JOBJ_{lid}", parent=prev_id,
                              pos=tuple(float(x) for x in local_pos)))
    prev_hl = chain_hl[b]
    prev_id = lid

# placeholder mesh-object node (IONET groups the mesh under a node)
MAT = "lyn_hair"
obj_node = max(SRC_TO_LOCAL.values()) + 1
acc.bones.append(smd.Bone(id=obj_node, name="Joint_1_Object_0", parent=-1))

# ---- ponytail geometry from the body SMD, re-homed to head-local ----
body = smd.load(smd_path)


def primary(v):
    return max(v.weights, key=lambda kv: kv[1])[0] if v.weights else -1


n_tri = 0
for t in body.triangles:
    prims = [primary(v) for v in t.verts]
    if sum(1 for p in prims if p in CLOTH_BONES) < 2:
        continue
    n_tri += 1
    verts = []
    for v in t.verts:
        pl = to_head_local(v.pos)
        nl = np.array(v.normal) @ R_inv
        nn = np.linalg.norm(nl)
        nl = nl / nn if nn > 1e-9 else nl
        src = primary(v)
        lid = SRC_TO_LOCAL.get(src, DYN_START_LOCAL)
        verts.append(smd.Vertex(
            pos=tuple(float(x) for x in pl),
            normal=tuple(float(x) for x in nl),
            uv=tuple(v.uv), weights=[(lid, 1.0)], parent=obj_node))
    acc.triangles.append(smd.Triangle(material=MAT, verts=tuple(verts)))

smd.save(acc, out_dir / "cape.smd")
(out_dir / "cape.smd.textures.json").write_text(json.dumps({MAT: Path(atlas_path).name}))
shutil.copyfile(atlas_path, out_dir / Path(atlas_path).name)

# ---- dynamics: Roy cape params on the swinging strand (root = J3 = bone 48) ----
src = params[DYN_SRC_CHAIN]
dyn = [{
    "bone": DYN_START_LOCAL,
    "PARAM1": src["PARAM1"], "PARAM2": src["PARAM2"], "PARAM3": src["PARAM3"],
    "joints": src["joints"][:len(DYN_BONES)],   # one param per moving joint
}]
(out_dir / "dynamics_local.json").write_text(json.dumps(dyn, indent=1))
(out_dir / "attach.json").write_text(json.dumps({"attachBone": ATTACH_BONE}))

print(f"hair accessory: {n_tri} tris, static anchor {sorted(STATIC_BONES)} -> J{ANCHOR_LOCAL}, "
      f"swing {DYN_BONES} -> J{DYN_START_LOCAL}.. ({len(DYN_BONES)} joints), "
      f"attach bone {ATTACH_BONE} -> {out_dir}")
