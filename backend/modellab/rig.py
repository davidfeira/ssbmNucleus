"""Rig a foreign mesh onto a Melee character's skeleton by surface weight transfer.

Pipeline:
  1. Load the character's "rig kit" (SMD exported from the vanilla costume DAT
     by ``HSDRawViewer --model export``): skeleton + vanilla mesh with weights.
  2. Load the foreign mesh (SMD, or GLB/OBJ via trimesh).
  3. Align the foreign mesh to the vanilla mesh (uniform height scale +
     center match, optional Y rotation for source-orientation fixes).
  4. For every foreign vertex, find the closest point on the vanilla mesh
     surface and barycentrically interpolate that face's bone weights.
  5. Emit an SMD with the rig kit's skeleton (verbatim — so the headless
     import's preserve-skeleton path triggers) and the foreign geometry,
     plus the texture sidecar/PNGs the import needs.

CLI:
  python rig.py --rigkit fox/fox_vanilla.smd --mesh falco/falco_vanilla.smd \
      --out out/falco_on_fox.smd [--rot-y 0] [--max-weights 4]
"""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modellab import smd  # noqa: E402

# Melee's engine supports at most 2 bone influences per vertex (community
# "Bone Affect Limit = 2"); more than that deforms wrong in-game.
MAX_WEIGHTS_DEFAULT = 2


# --------------------------------------------------------------------------- #
# foreign mesh loading                                                        #
# --------------------------------------------------------------------------- #
class ForeignMesh:
    """Triangle soup: positions/normals/uvs per corner + material per triangle."""

    def __init__(self, tri_pos, tri_norm, tri_uv, tri_mat, textures, tri_group=None):
        self.tri_pos = tri_pos      # (T, 3, 3)
        self.tri_norm = tri_norm    # (T, 3, 3)
        self.tri_uv = tri_uv        # (T, 3, 2)
        self.tri_mat = tri_mat      # list[str] length T
        self.textures = textures    # material name -> source png Path (or None)
        # mesh-grouping key per triangle. Grouping must follow the SOURCE
        # mesh, not the material: merging disconnected parts that share a
        # material makes the triangle stripper bridge them with visible
        # streak polygons.
        self.tri_group = tri_group if tri_group is not None else list(tri_mat)
        self.group_names: dict = {}

    def single_mask(self) -> np.ndarray:
        """True per triangle for _SINGLE (parent-joint-space) source meshes."""
        return np.array([
            "_SINGLE" in str(self.group_names.get(g, "")) for g in self.tri_group
        ])


def load_foreign_smd(path: Path) -> ForeignMesh:
    m = smd.load(path)
    tri_pos = np.array([[v.pos for v in t.verts] for t in m.triangles])
    tri_norm = np.array([[v.normal for v in t.verts] for t in m.triangles])
    tri_uv = np.array([[v.uv for v in t.verts] for t in m.triangles])
    tri_mat = [t.material for t in m.triangles]
    # the source SMD's vertex parent = its mesh placeholder node
    tri_group = [t.verts[0].parent if t.verts[0].parent is not None else t.material
                 for t in m.triangles]
    tri_src_w = [[v.weights for v in t.verts] for t in m.triangles]

    textures = {}
    sidecar = Path(str(path) + ".textures.json")
    if sidecar.exists():
        for mat, tex in json.loads(sidecar.read_text()).items():
            textures[mat] = path.parent / tex
    fm = ForeignMesh(tri_pos, tri_norm, tri_uv, tri_mat, textures, tri_group)
    # mesh node names — "_SINGLE" meshes (e.g. "Joint_41_Object_0_SINGLE")
    # are stored in parent-joint space, not world space, and must keep the
    # vanilla single-bind pathway through the importer
    fm.group_names = {b.id: b.name for b in m.bones}
    fm.src_smd = m   # for source-side weight/bone analysis
    fm.tri_src_w = tri_src_w
    return fm


def load_foreign_trimesh(path: Path) -> ForeignMesh:
    import trimesh

    scene = trimesh.load(path)
    meshes = (
        [g for g in scene.geometry.values()]
        if isinstance(scene, trimesh.Scene) else [scene]
    )

    tri_pos, tri_norm, tri_uv, tri_mat = [], [], [], []
    textures = {}
    for i, mesh in enumerate(meshes):
        mat_name = f"mat{i}"
        # pull the baseColor texture out of the material if present
        img = None
        material = getattr(mesh.visual, "material", None)
        if material is not None:
            img = getattr(material, "baseColorTexture", None) or getattr(material, "image", None)
        if img is not None:
            textures[mat_name] = img  # PIL image, saved later
        else:
            textures[mat_name] = None

        faces = mesh.faces
        verts = mesh.vertices
        norms = mesh.vertex_normals
        uv = getattr(mesh.visual, "uv", None)
        if uv is None:
            uv = np.zeros((len(verts), 2))

        tri_pos.append(verts[faces])
        tri_norm.append(norms[faces])
        tri_uv.append(uv[faces])
        tri_mat.extend([mat_name] * len(faces))

    fm = ForeignMesh(
        np.concatenate(tri_pos),
        np.concatenate(tri_norm),
        np.concatenate(tri_uv),
        tri_mat,
        textures,
    )
    return fm


def load_foreign(path: Path) -> ForeignMesh:
    if path.suffix.lower() == ".smd":
        return load_foreign_smd(path)
    return load_foreign_trimesh(path)


# --------------------------------------------------------------------------- #
# raw-mesh preview (no rig, no GL: painter's-algorithm software render)       #
# --------------------------------------------------------------------------- #
def _face_colors(foreign: ForeignMesh) -> np.ndarray:
    """(T, 3) base color per triangle: texture sampled at the UV centroid."""
    from PIL import Image

    T = len(foreign.tri_pos)
    colors = np.full((T, 3), 0.72)
    mats = np.asarray(foreign.tri_mat)
    uv_cent = foreign.tri_uv.mean(axis=1)
    for mat in set(foreign.tri_mat):
        tex = foreign.textures.get(mat)
        if tex is None:
            continue
        img = tex if not isinstance(tex, (str, Path)) else Image.open(tex)
        arr = np.asarray(img.convert("RGB"), dtype=np.float64) / 255.0
        h, w = arr.shape[:2]
        idx = np.where(mats == mat)[0]
        uv = uv_cent[idx] % 1.0
        px = np.clip((uv[:, 0] * (w - 1)).astype(int), 0, w - 1)
        py = np.clip(((1.0 - uv[:, 1]) * (h - 1)).astype(int), 0, h - 1)
        colors[idx] = arr[py, px]
    return colors


def render_mesh_preview(mesh_path, out_png, size=420, yaws=(20.0, 110.0)):
    """Render the RAW foreign mesh (front-ish + side view, lambert shading,
    textured faces) so a generated model can be judged BEFORE rigging."""
    from PIL import Image, ImageDraw

    foreign = load_foreign(Path(mesh_path))
    base = _face_colors(foreign)
    light = np.array([0.35, 0.55, 0.75])
    light = light / np.linalg.norm(light)

    panes = []
    for yaw in yaws:
        a = math.radians(yaw)
        rot = np.array([
            [math.cos(a), 0, math.sin(a)],
            [0, 1, 0],
            [-math.sin(a), 0, math.cos(a)],
        ])
        tris = foreign.tri_pos @ rot.T          # (T, 3, 3)
        n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
        nl = np.linalg.norm(n, axis=1, keepdims=True)
        n = n / np.maximum(nl, 1e-12)
        shade = 0.34 + 0.66 * np.clip(np.abs(n @ light), 0, 1)
        rgb = np.clip(base * shade[:, None] * 255, 0, 255).astype(np.uint8)

        xy = tris[:, :, [0, 1]].copy()
        xy[:, :, 1] *= -1.0                      # y up -> image down
        lo = xy.reshape(-1, 2).min(axis=0)
        hi = xy.reshape(-1, 2).max(axis=0)
        span = max((hi - lo).max(), 1e-9)
        margin = 0.07 * size
        pts = (xy - lo) / span * (size - 2 * margin) + margin
        # center the smaller axis
        used = (hi - lo) / span * (size - 2 * margin)
        pts += (size - 2 * margin - used) / 2

        im = Image.new("RGB", (size, size), (23, 30, 42))
        draw = ImageDraw.Draw(im)
        order = np.argsort(tris[:, :, 2].mean(axis=1))   # far first
        for t in order:
            draw.polygon([tuple(p) for p in pts[t]], fill=tuple(rgb[t]))
        panes.append(im)

    out = Image.new("RGB", (size * len(panes), size), (23, 30, 42))
    for i, im in enumerate(panes):
        out.paste(im, (i * size, 0))
    out.save(out_png)
    return out_png


def decimate(foreign: ForeignMesh, max_tris: int) -> ForeignMesh:
    """Reduce the foreign mesh to ~max_tris, re-projecting UVs and normals
    from the original surface (fast_simplification drops attributes)."""
    import trimesh
    import fast_simplification

    if len(foreign.tri_pos) <= max_tris:
        return foreign

    out_pos, out_norm, out_uv, out_mat, out_group = [], [], [], [], []
    groups = list(dict.fromkeys(foreign.tri_group))
    budget_per = max_tris / len(foreign.tri_pos)

    for g in groups:
        idx = [i for i, gg in enumerate(foreign.tri_group) if gg == g]
        tri = foreign.tri_pos[idx]
        n_target = max(int(len(idx) * budget_per), 16)
        if len(idx) <= n_target:
            out_pos.append(tri)
            out_norm.append(foreign.tri_norm[idx])
            out_uv.append(foreign.tri_uv[idx])
            out_mat.extend(foreign.tri_mat[i] for i in idx)
            out_group.extend([g] * len(idx))
            continue

        verts = tri.reshape(-1, 3)
        faces = np.arange(len(verts)).reshape(-1, 3)
        src = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
        ratio = 1.0 - (n_target / len(src.faces))
        v2, f2 = fast_simplification.simplify(
            src.vertices, src.faces, target_reduction=min(max(ratio, 0.0), 0.99))

        # re-project per-corner attributes from the ORIGINAL surface
        orig = trimesh.Trimesh(vertices=verts, faces=faces, process=False)
        corners = v2[f2].reshape(-1, 3)
        closest, _, tri_id = trimesh.proximity.closest_point(orig, corners)
        bary = trimesh.triangles.points_to_barycentric(tri[tri_id], closest)
        bad = ~np.isfinite(bary).all(axis=1)
        bary[bad] = 1.0 / 3.0
        # UV interpolation across seams is wrong — snap to the dominant corner
        dominant = bary.argmax(axis=1)
        uv = foreign.tri_uv[idx][tri_id, dominant]
        nrm = np.einsum("kc,kcj->kj", bary, foreign.tri_norm[idx][tri_id])
        norms = np.linalg.norm(nrm, axis=1, keepdims=True)
        nrm = nrm / np.maximum(norms, 1e-9)

        n_f = len(f2)
        out_pos.append(corners.reshape(n_f, 3, 3))
        out_norm.append(nrm.reshape(n_f, 3, 3))
        out_uv.append(uv.reshape(n_f, 3, 2))
        mat = foreign.tri_mat[idx[0]]
        out_mat.extend([mat] * n_f)
        out_group.extend([g] * n_f)

    fm = ForeignMesh(
        np.concatenate(out_pos), np.concatenate(out_norm),
        np.concatenate(out_uv), out_mat, foreign.textures, out_group)
    fm.group_names = foreign.group_names
    return fm


# --------------------------------------------------------------------------- #
# alignment + weight transfer                                                 #
# --------------------------------------------------------------------------- #
def align(foreign: ForeignMesh, target_pts: np.ndarray, rot_y_deg: float = 0.0):
    """Uniform scale by height (Y extent) + center match, after optional Y spin.

    _SINGLE meshes live in parent-joint space, not world space: they are
    excluded from the fit statistics and only receive the uniform scale
    (valid in any space), never the translation.
    """
    single_tri = foreign.single_mask()
    single_v = np.repeat(single_tri, 3)
    pts = foreign.tri_pos.reshape(-1, 3)

    if rot_y_deg:
        a = math.radians(rot_y_deg)
        rot = np.array([
            [math.cos(a), 0, math.sin(a)],
            [0, 1, 0],
            [-math.sin(a), 0, math.cos(a)],
        ])
        pts[~single_v] = pts[~single_v] @ rot.T
        norms = foreign.tri_norm.reshape(-1, 3)
        norms[~single_v] = norms[~single_v] @ rot.T
        foreign.tri_norm = norms.reshape(foreign.tri_norm.shape)

    world = pts[~single_v]
    src_min, src_max = world.min(axis=0), world.max(axis=0)
    tgt_min, tgt_max = target_pts.min(axis=0), target_pts.max(axis=0)

    scale = (tgt_max[1] - tgt_min[1]) / max(src_max[1] - src_min[1], 1e-9)
    pts = pts * scale
    # match the feet (min-Y) and horizontal centers rather than raw centroids:
    # Melee models stand on y=0
    world = pts[~single_v]
    src_min, src_max = world.min(axis=0), world.max(axis=0)
    offset = np.array([
        (tgt_min[0] + tgt_max[0]) / 2 - (src_min[0] + src_max[0]) / 2,
        tgt_min[1] - src_min[1],
        (tgt_min[2] + tgt_max[2]) / 2 - (src_min[2] + src_max[2]) / 2,
    ])
    pts[~single_v] = pts[~single_v] + offset

    foreign.tri_pos = pts.reshape(foreign.tri_pos.shape)
    return scale, offset


def drop_hidden_source_groups(foreign: ForeignMesh, src_char_code,
                              src_smd: smd.SMD = None, log=print):
    """For melee-costume sources, drop groups that can't transfer:

    1. The source's LOW-POLY set (its visibility table) — stored displaced,
       normally hidden in-game (the falco 'sail').
    2. Groups dominated by the source's ACCESSORY bone chains (<2% of its
       surface weight mass). Their geometry is PARKED in the bind pose and
       only placed correctly by the source's own animations folding those
       bones in — retargeted, it renders at the parked spot (the falco
       'head spike' = his crest, parked at y 13-17, animated down in-game).
    """
    visible, _ = load_visibility(src_char_code)
    order = {g: i for i, g in enumerate(dict.fromkeys(foreign.tri_group))}

    drop = set()
    if visible:
        drop |= {g for g, i in order.items() if i not in visible}

    if src_smd is not None:
        mass: dict[int, float] = {}
        group_mass: dict = {}
        for t in src_smd.triangles:
            g = t.verts[0].parent
            for v in t.verts:
                for bone, w in v.weights:
                    mass[bone] = mass.get(bone, 0.0) + w
                    gm = group_mass.setdefault(g, {})
                    gm[bone] = gm.get(bone, 0.0) + w
        total = sum(mass.values()) or 1.0
        unstable = {b for b, m in mass.items() if m / total < 0.02}
        for g, gm in group_mass.items():
            # group keys here are vertex-parent ids — the same key space as
            # foreign.tri_group for SMD sources
            if g not in order or g in drop:
                continue
            # _SINGLE meshes (eyes etc.) are world-positioned correctly at
            # bind; they get re-weighted by position instead of dropped
            if "_SINGLE" in str(foreign.group_names.get(g, "")):
                continue
            gtotal = sum(gm.values()) or 1.0
            unstable_share = sum(w for b, w in gm.items() if b in unstable)
            if unstable_share / gtotal > 0.6:
                drop.add(g)

    if not drop:
        return foreign
    keep = [i for i, g in enumerate(foreign.tri_group) if g not in drop]
    log(f"dropped {len(foreign.tri_group) - len(keep)} tris from "
        f"{len(drop)} hidden/parked source groups")
    fm = ForeignMesh(
        foreign.tri_pos[keep], foreign.tri_norm[keep], foreign.tri_uv[keep],
        [foreign.tri_mat[i] for i in keep], foreign.textures,
        [foreign.tri_group[i] for i in keep])
    fm.group_names = foreign.group_names
    if hasattr(foreign, "tri_src_w"):
        fm.tri_src_w = [foreign.tri_src_w[i] for i in keep]
    if hasattr(foreign, "src_smd"):
        fm.src_smd = foreign.src_smd
    return fm


def split_groups(foreign: ForeignMesh, target_groups: int) -> None:
    """Recursively split the largest mesh groups along their longest axis
    until the model has target_groups DObjs. The game's per-costume model
    machinery indexes DObj lists built for the vanilla costume; a model with
    far fewer DObjs hangs at load (observed: 1 DObj = frame-1 hang, vanilla
    counts = healthy). Smaller display lists per DObj are also GX-friendlier."""
    groups: dict = {}
    for i, g in enumerate(foreign.tri_group):
        groups.setdefault(g, []).append(i)

    serial = 0
    while len(groups) < target_groups:
        big = max(groups, key=lambda g: len(groups[g]))
        idx = groups[big]
        if len(idx) < 2:
            break
        cent = foreign.tri_pos[idx].mean(axis=1)
        axis = (cent.max(axis=0) - cent.min(axis=0)).argmax()
        order = np.argsort(cent[:, axis])
        half = len(idx) // 2
        keep = [idx[i] for i in order[:half]]
        move = [idx[i] for i in order[half:]]
        new_key = f"__split_{serial}"
        serial += 1
        groups[big] = keep
        groups[new_key] = move
        for i in move:
            foreign.tri_group[i] = new_key
        # splits inherit world-space (non-_SINGLE) handling: no group_names entry


def joint_world_matrices(rigkit: smd.SMD) -> dict[int, np.ndarray]:
    """World 4x4 of every joint from the rig kit's bind pose (FK)."""
    def euler(rx, ry, rz):
        cx, sx = math.cos(rx), math.sin(rx)
        cy, sy = math.cos(ry), math.sin(ry)
        cz, sz = math.cos(rz), math.sin(rz)
        Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
        Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
        Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
        return Rz @ Ry @ Rx

    mats: dict[int, np.ndarray] = {}
    for b in rigkit.bones:
        if not b.name.startswith("JOBJ_"):
            continue
        local = np.eye(4)
        local[:3, :3] = euler(*b.rot)
        local[:3, 3] = b.pos
        mats[b.id] = mats[b.parent] @ local if b.parent in mats else local
    return mats


def joint_world_positions(rigkit: smd.SMD) -> dict[int, np.ndarray]:
    """World position of every joint from the rig kit's bind pose (FK)."""
    return {j: m[:3, 3] for j, m in joint_world_matrices(rigkit).items()}


def sane_surface(rigkit: smd.SMD):
    """The rig kit's triangles that represent the REAL playable body surface.

    Vanilla DATs carry whole alternate assemblies parked outside the body
    (e.g. Fox's second head on its own bone chain at y 11-17). Their verts
    sit near their own (parked) bones, so distance checks don't catch them —
    but they rig to an EXCLUSIVE bone block. Discriminator learned from how
    vanilla meshes are rigged: cluster mesh groups by shared weight bones and
    keep the component anchored at the feet (the global lowest vertex).
    """
    names = {b.id: b.name for b in rigkit.bones}

    # per mesh group: bone usage (weight mass) + lowest vertex
    group_bones: dict = {}
    group_min_y: dict = {}
    for t in rigkit.triangles:
        g = t.verts[0].parent
        if "_SINGLE" in names.get(g, ""):
            continue
        gb = group_bones.setdefault(g, {})
        for v in t.verts:
            group_min_y[g] = min(group_min_y.get(g, 1e9), v.pos[1])
            for bone, w in v.weights:
                gb[bone] = gb.get(bone, 0.0) + w

    # union groups that meaningfully share a bone (>=1% of each side's mass)
    groups = list(group_bones)
    parent = {g: g for g in groups}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def significant(gb):
        total = sum(gb.values()) or 1.0
        return {b for b, w in gb.items() if w / total >= 0.01}

    sig = {g: significant(gb) for g, gb in group_bones.items()}
    for i, a in enumerate(groups):
        for b in groups[i + 1:]:
            if sig[a] & sig[b]:
                ra, rb = find(a), find(b)
                if ra != rb:
                    parent[ra] = rb

    # keep the component that touches the ground (the playable body)
    floor_group = min(groups, key=lambda g: group_min_y[g])
    body = find(floor_group)
    kept_groups = {g for g in groups if find(g) == body}

    return [t for t in rigkit.triangles if t.verts[0].parent in kept_groups]


def transfer_weights(
    rigkit: smd.SMD, foreign: ForeignMesh, max_weights: int = MAX_WEIGHTS_DEFAULT,
    surface=None, surface_pts=None, bone_world=None, forbidden=None,
) -> list[list[tuple[int, float]]]:
    """Per-corner weights for the foreign mesh, sampled from the rig-kit mesh.

    surface_pts/bone_world override the surface corner positions and joint
    positions (used to match in the in-game REST pose instead of bind)."""
    # vanilla mesh as triangle soup (positions are duplicated per corner),
    # restricted to the plausibly-placed body surface
    tris = surface if surface is not None else sane_surface(rigkit)
    if surface_pts is not None:
        van_tri = np.asarray(surface_pts).reshape(len(tris), 3, 3)
    else:
        van_tri = np.array([[v.pos for v in t.verts] for t in tris])
    van_w = [[v.weights for v in t.verts] for t in tris]

    pts = foreign.tri_pos.reshape(-1, 3)
    # bone stability: accessory bones (ear tips, antennae, hair physics
    # chains) carry a tiny share of the vanilla surface's weight mass; a
    # foreign vert that samples one would flail with it in-game. Remap such
    # weights up the skeleton to the nearest high-mass ancestor.
    mass: dict[int, float] = {}
    for tw in van_w:
        for corner in tw:
            for bone, w in corner:
                mass[bone] = mass.get(bone, 0.0) + w
    total_mass = sum(mass.values()) or 1.0
    stable = {b for b, m in mass.items() if m / total_mass >= 0.02}
    if forbidden:
        # physics-driven chains: even though the vanilla surface weights them
        # (fox's own tail fur), foreign verts must remap PAST the whole chain
        stable -= set(forbidden)
    parents = {b.id: b.parent for b in rigkit.bones if b.name.startswith("JOBJ_")}

    def stabilize(bone):
        seen = set()
        while bone not in stable and bone in parents and bone not in seen:
            seen.add(bone)
            if parents[bone] < 0:
                break
            bone = parents[bone]
        return bone

    # anchor-aware k-NN matching. The single nearest surface point grabs the
    # WRONG body part wherever parts pass close together (a T-pose's arms run
    # right beside the head, so face verts sample arm weights and launch when
    # the arm swings). Among the K nearest vanilla verts, prefer samples whose
    # weighted-bone anchor is also near the foreign vert.
    from scipy.spatial import cKDTree

    world = bone_world if bone_world is not None else joint_world_positions(rigkit)
    all_pts = van_tri.reshape(-1, 3)
    all_w = [w for tw in van_w for w in tw]
    # weld duplicate corners or K nearest neighbors are all copies of the
    # same few verts and the anchor vote never sees an alternative body part
    seen: dict = {}
    uniq_idx = []
    for i, key in enumerate(map(tuple, np.round(all_pts / 1e-3).astype(np.int64))):
        if key not in seen:
            seen[key] = True
            uniq_idx.append(i)
    van_pts = all_pts[uniq_idx]
    van_corner_w = [all_w[i] for i in uniq_idx]

    anchors = np.zeros((len(van_pts), 3))
    for i, wlist in enumerate(van_corner_w):
        tot = 0.0
        for bone, w in wlist:
            bone = stabilize(bone)
            if bone in world:
                anchors[i] += world[bone] * w
                tot += w
        if tot:
            anchors[i] /= tot

    tree = cKDTree(van_pts)
    K = min(24, len(van_pts))
    d_geo, idx = tree.query(pts, k=K)
    anchor_d = np.linalg.norm(pts[:, None, :] - anchors[idx], axis=2)
    score = d_geo + 1.2 * anchor_d
    best = idx[np.arange(len(pts)), score.argmin(axis=1)]

    raw = []
    for k in range(len(pts)):
        acc: dict[int, float] = {}
        for bone, w in van_corner_w[best[k]]:
            bone = stabilize(bone)
            acc[bone] = acc.get(bone, 0.0) + w
        total = sum(acc.values()) or 1.0
        raw.append({b: w / total for b, w in acc.items()})

    smoothed = smooth_weights(pts, raw, iterations=4)

    # distance gate: smoothing can diffuse weights far up the body (collar ->
    # head picks up ARM bones; at non-rest poses those verts stretch between
    # head and arm). A vert may only keep weights to bones physically near it.
    height = float(pts[:, 1].max() - pts[:, 1].min()) or 1.0
    max_reach = max(2.0, 0.15 * height)
    stable_ids = [b for b in world if b in stable]
    stable_pos = np.array([world[b] for b in stable_ids])

    out = []
    for k, acc in enumerate(smoothed):
        gated = {b: w for b, w in acc.items()
                 if b in world and
                 float(np.linalg.norm(pts[k] - world[b])) <= max_reach}
        if not gated:
            # no held bone is near (crest tips, prop extremities): ride the
            # single nearest STABLE bone instead of a far-flung mixture
            nearest = stable_ids[int(np.linalg.norm(stable_pos - pts[k], axis=1).argmin())]
            gated = {nearest: 1.0}
        top = sorted(gated.items(), key=lambda kv: -kv[1])[:max_weights]
        total = sum(w for _, w in top) or 1.0
        out.append([(b, w / total) for b, w in top])

    # neighborhood consensus: a vert whose primary bone is (nearly) unused by
    # every nearby vert is a transfer outlier — the moment that bone moves
    # away from the region, the lone vert stretches into a spike. Snap such
    # verts to their neighborhood's dominant weighting. Welded positions
    # first, or a spike's duplicated corners would vote for themselves.
    pos_key = list(map(tuple, np.round(pts / 1e-3).astype(np.int64)))
    uniq: dict = {}
    for k, key in enumerate(pos_key):
        uniq.setdefault(key, k)
    u_ids = list(uniq.values())
    u_pts = pts[u_ids]
    utree = cKDTree(u_pts)
    NK = min(9, len(u_pts))
    radius = max(1.2, 0.05 * height)
    nd, nidx = utree.query(u_pts, k=NK)
    # two passes: a pair of mutually-adjacent outliers props each other up on
    # the first pass; once one is snapped the survivor loses its only support
    for _ in range(2):
        consensus: dict = {}
        for ui, k in enumerate(u_ids):
            votes: dict[int, float] = {}
            n_nb = 0
            for j, dist in zip(nidx[ui][1:], nd[ui][1:]):
                if dist > radius:
                    break
                n_nb += 1
                for b, w in out[u_ids[int(j)]]:
                    votes[b] = votes.get(b, 0.0) + w
            if n_nb < 3 or not votes:
                continue
            dominant = max(votes.values())
            prim = out[k][0][0]
            if votes.get(prim, 0.0) >= 0.08 * dominant:
                continue
            top = sorted(votes.items(), key=lambda kv: -kv[1])[:max_weights]
            total = sum(w for _, w in top) or 1.0
            consensus[pos_key[k]] = [(b, w / total) for b, w in top]
        if not consensus:
            break
        snapped = 0
        for k, key in enumerate(pos_key):
            if key in consensus:
                out[k] = consensus[key]
                snapped += 1
        print(f"  consensus pass: snapped {snapped} outlier corners "
              f"({len(consensus)} unique verts)")

    # triangle coherence: vanilla triangles only ever span ADJACENT bones
    # (elbow, knee). A triangle whose corners ride skeleton-DISTANT bones
    # (hip vs head) stretches into a giant shard the moment the pose spreads
    # them — the dominant close-up artifact on cross-rigged capes/feathers.
    # Enforce: each triangle's welded verts must share a bone or sit within
    # tree distance 3; snap the lone offender to its mates' blend.
    _dist_memo: dict = {}

    def tree_dist(a, b, cap=6):
        if a == b:
            return 0
        key = (a, b) if a < b else (b, a)
        hit = _dist_memo.get(key)
        if hit is not None:
            return hit
        seen_a, seen_b = {a: 0}, {b: 0}
        ca, cb = a, b
        result = cap + 1
        for step in range(1, cap + 1):
            if ca in parents and parents[ca] >= 0:
                ca = parents[ca]
                if ca in seen_b:
                    result = step + seen_b[ca]
                    break
                seen_a[ca] = step
            if cb in parents and parents[cb] >= 0:
                cb = parents[cb]
                if cb in seen_a:
                    result = step + seen_a[cb]
                    break
                seen_b[cb] = step
        _dist_memo[key] = result
        return result

    vert_of = {}
    corner_vert = [vert_of.setdefault(key, len(vert_of)) for key in pos_key]
    n_tri = len(pts) // 3
    for _ in range(3):
        fixes: dict = {}
        for t in range(n_tri):
            cs = [t * 3, t * 3 + 1, t * 3 + 2]
            sets = [dict(out[c]) for c in cs]
            if set(sets[0]) & set(sets[1]) & set(sets[2]):
                continue
            prims = [out[c][0][0] for c in cs]
            d01 = tree_dist(prims[0], prims[1])
            d02 = tree_dist(prims[0], prims[2])
            d12 = tree_dist(prims[1], prims[2])
            if max(d01, d02, d12) <= 3:
                continue
            # offender = the corner farthest from BOTH its mates
            far = [d01 + d02, d01 + d12, d02 + d12]
            o = int(np.argmax(far))
            mates = [i for i in range(3) if i != o]
            blend: dict = {}
            for i in mates:
                for b, w in sets[i].items():
                    blend[b] = blend.get(b, 0.0) + w
            top = sorted(blend.items(), key=lambda kv: -kv[1])[:max_weights]
            total = sum(w for _, w in top) or 1.0
            fixes[corner_vert[cs[o]]] = [(b, w / total) for b, w in top]
        if not fixes:
            break
        n_fixed = 0
        for k in range(len(pts)):
            if corner_vert[k] in fixes:
                out[k] = fixes[corner_vert[k]]
                n_fixed += 1
        print(f"  triangle coherence: re-bound {len(fixes)} verts "
              f"({n_fixed} corners)")
    return out


def smooth_weights(pts: np.ndarray, weights: list[dict], iterations: int = 12):
    """Laplacian smoothing of bone weights over the foreign mesh.

    Raw closest-point sampling gives neighboring triangles weights from
    DIFFERENT bones wherever the source surface is ambiguous — in any pose
    but bind, the mesh TEARS along those cliffs (the in-game shredded-shell
    artifact). Weld coincident corners, then diffuse weights across mesh
    neighbors until they vary smoothly.
    """
    # weld coincident corners (the soup duplicates verts per triangle)
    key = np.round(pts / 1e-4).astype(np.int64)
    welded: dict = {}
    corner_to_v = np.empty(len(pts), dtype=np.int64)
    for i, k in enumerate(map(tuple, key)):
        corner_to_v[i] = welded.setdefault(k, len(welded))
    n_v = len(welded)

    # vertex weights = average of their corners'
    vw: list[dict] = [{} for _ in range(n_v)]
    counts = np.zeros(n_v)
    for i, acc in enumerate(weights):
        v = corner_to_v[i]
        counts[v] += 1
        for b, w in acc.items():
            vw[v][b] = vw[v].get(b, 0.0) + w
    for v in range(n_v):
        if counts[v]:
            vw[v] = {b: w / counts[v] for b, w in vw[v].items()}

    # adjacency from triangles (corners come in consecutive triples)
    neighbors: list[set] = [set() for _ in range(n_v)]
    for t in range(len(pts) // 3):
        a, b, c = corner_to_v[t * 3:t * 3 + 3]
        neighbors[a] |= {b, c}
        neighbors[b] |= {a, c}
        neighbors[c] |= {a, b}

    for _ in range(iterations):
        new: list[dict] = []
        for v in range(n_v):
            acc = {b: w * 0.5 for b, w in vw[v].items()}
            ns = neighbors[v]
            if ns:
                k = 0.5 / len(ns)
                for n in ns:
                    for b, w in vw[n].items():
                        acc[b] = acc.get(b, 0.0) + w * k
            # keep the strongest few to bound growth
            top = sorted(acc.items(), key=lambda kv: -kv[1])[:6]
            total = sum(w for _, w in top) or 1.0
            new.append({b: w / total for b, w in top})
        vw = new

    return [vw[corner_to_v[i]] for i in range(len(pts))]


# --------------------------------------------------------------------------- #
# emit                                                                        #
# --------------------------------------------------------------------------- #
def emit(rigkit: smd.SMD, foreign: ForeignMesh, weights, out_path: Path,
         max_texture: int = 512, visible_indices=None, total_dobjs=None):
    """Write the rigged SMD. When the character's costume visibility table is
    known, REAL mesh groups are placed at the HighPoly (always-rendered) DObj
    indices and degenerate dummy DObjs fill the LowPoly (hidden) slots —
    otherwise the game's low-poly hiding eats whichever chunks land in the
    hidden index range (the in-game "shredded" artifact).
    """
    # real skeleton joints only (the rig kit also carries "Joint_X_Object_Y"
    # mesh placeholder nodes from the vanilla mesh — drop those)
    joints = [b for b in rigkit.bones if b.name.startswith("JOBJ_")]
    out = smd.SMD(bones=list(joints))

    import re

    # ordered real groups + per-group forced single-bind weights
    real_groups = list(dict.fromkeys(foreign.tri_group))
    single_joint: dict = {}
    for g in real_groups:
        src_name = str(foreign.group_names.get(g, ""))
        if "_SINGLE" in src_name:
            mj = re.match(r"Joint_(\d+)", src_name)
            if mj:
                single_joint[g] = (int(mj.group(1)), 1.0)

    # decide the DObj slot for every output index
    if visible_indices:
        total = max(total_dobjs or 0, max(visible_indices) + 1)
        slots = ["real" if i in visible_indices else "dummy" for i in range(total)]
    else:
        slots = ["real"] * len(real_groups)

    # mesh placeholder nodes in slot order: this is how IONET's SMD importer
    # reconstructs per-DObj meshes (vertex parent = mesh node id) and the
    # order determines the in-game DObj index
    next_id = max(b.id for b in joints) + 1
    group_node: dict = {}
    dummy_nodes: list = []
    real_iter = iter(real_groups)
    placed = 0
    for i, kind in enumerate(slots):
        g = next(real_iter, None) if kind == "real" else None
        name = (str(foreign.group_names.get(g, "")) if g in single_joint
                else f"Joint_0_Object_{i}")
        out.bones.append(smd.Bone(id=next_id, name=name or f"Joint_0_Object_{i}",
                                  parent=-1))
        if g is not None:
            group_node[g] = next_id
            placed += 1
        else:
            dummy_nodes.append(next_id)
        next_id += 1
    # leftover real groups (more groups than visible slots): append at the end
    for g in real_iter:
        out.bones.append(smd.Bone(id=next_id, name=f"Joint_0_Object_x{next_id}",
                                  parent=-1))
        group_node[g] = next_id
        next_id += 1

    # triangles must appear grouped in slot order for the importer to build
    # DObjs in the intended sequence
    tri_by_group: dict = {}
    for t in range(len(foreign.tri_pos)):
        tri_by_group.setdefault(foreign.tri_group[t], []).append(t)

    k_base = {g: None for g in real_groups}
    # precompute corner offsets (k) per triangle: corners are 3*t + c
    dummy_mat = foreign.tri_mat[0] if foreign.tri_mat else "mat0"

    def emit_group(g):
        node = group_node[g]
        for t in tri_by_group[g]:
            verts = []
            for c in range(3):
                w = [single_joint[g]] if g in single_joint else weights[t * 3 + c]
                verts.append(smd.Vertex(
                    pos=tuple(foreign.tri_pos[t][c]),
                    normal=tuple(foreign.tri_norm[t][c]),
                    uv=tuple(foreign.tri_uv[t][c]),
                    weights=w,
                    parent=node,
                ))
            out.triangles.append(
                smd.Triangle(material=foreign.tri_mat[t], verts=tuple(verts)))

    def emit_dummy(node):
        # one micro-triangle, textured (textureless DObjs hang the game),
        # rigidly bound to the root-adjacent joint
        base = (0.0, 3.0, 0.0)
        eps = 1e-3
        verts = []
        for dx, dy in ((0, 0), (eps, 0), (0, eps)):
            verts.append(smd.Vertex(
                pos=(base[0] + dx, base[1] + dy, base[2]),
                normal=(0.0, 0.0, 1.0), uv=(0.5, 0.5),
                weights=[(4, 1.0)], parent=node))
        out.triangles.append(smd.Triangle(material=dummy_mat, verts=tuple(verts)))

    real_iter2 = iter([g for g in real_groups])
    di = 0
    for kind in slots:
        if kind == "real":
            g = next(real_iter2, None)
            if g is not None:
                emit_group(g)
            else:
                emit_dummy(dummy_nodes[di]); di += 1  # exhausted: pad
        else:
            emit_dummy(dummy_nodes[di]); di += 1
    for g in real_iter2:
        emit_group(g)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    smd.save(out, out_path)

    # textures: copy/save next to the SMD + write the import sidecar
    sidecar = {}
    for mat, tex in foreign.textures.items():
        if tex is None:
            continue
        if isinstance(tex, Path):
            dest = out_path.parent / tex.name
            if tex.resolve() != dest.resolve():
                shutil.copyfile(tex, dest)
            sidecar[mat] = tex.name
        else:  # PIL image from a GLB material
            # clamp to Melee-scale texture memory (also: ImageSharp's pixel-span
            # path in the importer fails on very large images)
            max_dim = max_texture
            if max(tex.size) > max_dim:
                tex = tex.resize(
                    (max_dim * tex.size[0] // max(tex.size),
                     max_dim * tex.size[1] // max(tex.size)))
            name = f"{mat}.png"
            tex.convert("RGBA").save(out_path.parent / name)
            sidecar[mat] = name
    if sidecar:
        Path(str(out_path) + ".textures.json").write_text(json.dumps(sidecar, indent=2))
    return len(sidecar)


def load_pose(json_path):
    """Per-joint world 4x4s from a --dump-pose JSON (the in-game rest pose)."""
    data = json.loads(Path(json_path).read_text())
    return {b["index"]: np.array(b["matrix"]).reshape(4, 4).T
            for b in data["bones"]}


def skin_matrices(bind_mats, pose_mats):
    """Per-joint bind->pose LBS matrices (M_pose @ inv(M_bind))."""
    out = {}
    for j, mb in bind_mats.items():
        if j in pose_mats:
            out[j] = pose_mats[j] @ np.linalg.inv(mb)
    return out


def repose_points(pts, weights_per_pt, skin):
    """LBS each point by its weighted skin matrices. weights_per_pt is a list
    of [(bone, w), ...] aligned with pts rows."""
    out = np.array(pts, dtype=float, copy=True)
    for i, wlist in enumerate(weights_per_pt):
        m = np.zeros((4, 4))
        tot = 0.0
        for bone, w in wlist:
            if bone in skin:
                m += skin[bone] * w
                tot += w
        if tot <= 0:
            continue
        m /= tot
        p = m @ np.array([out[i][0], out[i][1], out[i][2], 1.0])
        out[i] = p[:3]
    return out


def load_visibility(char_code):
    """HighPoly (visible) DObj indices + total DObj count for a character's
    costume-0 visibility table; (None, None) when unknown."""
    table_path = Path(__file__).parent / "visibility_tables.json"
    if not table_path.exists() or not char_code:
        return None, None
    data = json.loads(table_path.read_text())
    entry = data.get(char_code)
    if not entry or "costumes" not in entry or not entry["costumes"]:
        return None, None
    c0 = entry["costumes"][0]
    high = {i for e in (c0.get("high") or []) for i in e}
    low = {i for e in (c0.get("low") or []) for i in e}
    if not high:
        return None, None
    return high, max(high | low) + 1


def load_dynamics(char_code):
    """Dynamic (cloth/tail physics) chain ROOT bone indices for a character
    (ftData+0x2C SBM_PhysicsGroup). Foreign geometry must never be weighted
    into these chains: their motion is physics tuned for the VANILLA part
    (fox's tail), so transplanted verts flail (capes grabbing the tail chain
    was the cross-rig 'glitchy cape/tail' artifact)."""
    path = Path(__file__).parent / "dynamic_bones.json"
    if not path.exists() or not char_code:
        return []
    data = json.loads(path.read_text())
    return [c["bone"] for c in data.get(char_code, [])]


def rig_mesh(rigkit_path, mesh_path, out_path, rot_y=0.0,
             max_weights=MAX_WEIGHTS_DEFAULT, max_tris=9000, max_texture=512,
             rigid_bone=None, char_code=None, src_char_code=None,
             target_pose=None, src_pose=None, log=print):
    """Full rigging pass (the function behind the CLI): foreign mesh ->
    SMD (+textures/sidecar) rigged to the rig kit's skeleton. Returns stats."""
    rigkit = smd.load(rigkit_path)
    foreign = load_foreign(Path(mesh_path))
    log(f"rig kit: {len(rigkit.bones)} bones, {len(rigkit.triangles)} tris; "
        f"foreign: {len(foreign.tri_pos)} tris")

    # melee-DAT sources carry their own hidden low-poly set + parked
    # accessory geometry. With pose retargeting the parked geometry folds to
    # its true place, so only the visibility-table drop applies then.
    if Path(mesh_path).suffix.lower() == ".smd":
        retargeting = bool(target_pose and src_pose)
        foreign = drop_hidden_source_groups(
            foreign, src_char_code,
            None if retargeting else getattr(foreign, "src_smd", None), log)
        if src_char_code:
            # cross-skeleton: the source's _SINGLE joint indices mean nothing
            # on the target skeleton (falco's eye joint = fox's ear chain →
            # eyes swing with the ear). Their verts are already world-space at
            # bind — drop the binding and weight them by position like
            # everything else.
            converted = sum(1 for k, v in foreign.group_names.items()
                            if "_SINGLE" in str(v))
            if converted:
                foreign.group_names = {
                    k: (str(v).replace("_SINGLE", "") if "_SINGLE" in str(v) else v)
                    for k, v in foreign.group_names.items()}
                log(f"converted {converted} _SINGLE source groups to enveloped")

    if max_tris and len(foreign.tri_pos) > max_tris:
        foreign = decimate(foreign, max_tris)
        log(f"decimated to {len(foreign.tri_pos)} tris")

    # split to fill the character's VISIBLE DObj slots (the HighPoly set from
    # its costume visibility table); hidden slots get dummy DObjs in emit().
    # Without a table, fall back to the vanilla mesh-node count.
    visible, total = load_visibility(char_code)
    vanilla_groups = sum(1 for b in rigkit.bones if not b.name.startswith("JOBJ_"))
    if total is not None and total < vanilla_groups:
        # weapon/effect DObjs sit beyond the table's coverage (Link's sword
        # parts): the table under-counts, the costume still owns them all
        total = vanilla_groups
    target = len(visible) if visible else vanilla_groups
    if target > len(set(foreign.tri_group)):
        split_groups(foreign, target)
        log(f"split into {len(set(foreign.tri_group))} mesh groups "
            f"(visible slots: {target}, total dobjs: {total or vanilla_groups})")

    # align + transfer against the PLAUSIBLE body surface only: vanilla DATs
    # park alternate meshes above the body, which would inflate the height
    # fit and hand out wrong-body-part weights
    surface = sane_surface(rigkit)
    log(f"transfer surface: {len(surface)}/{len(rigkit.triangles)} vanilla tris")

    # pose-space retargeting (melee sources): the BIND pose is not what the
    # game shows — characters rest in Wait1 frame 0 (T-pose arms fold down,
    # accessory chains fold in). Repose the source mesh to ITS rest pose
    # (where it visually belongs), match against the target surface posed to
    # ITS rest pose, then un-pose the verts into target-bind space so the
    # game's LBS reproduces the rest-pose look exactly.
    tgt_skin = None
    surf_pts = None
    pose_world = None
    if (target_pose and src_pose and hasattr(foreign, "src_smd")
            and hasattr(foreign, "tri_src_w")):
        tgt_pose_mats = load_pose(target_pose)
        tgt_skin = skin_matrices(joint_world_matrices(rigkit), tgt_pose_mats)
        src_skin = skin_matrices(joint_world_matrices(foreign.src_smd),
                                 load_pose(src_pose))
        pts = foreign.tri_pos.reshape(-1, 3)
        wpp = [w for tw in foreign.tri_src_w for w in tw]
        foreign.tri_pos = repose_points(pts, wpp, src_skin).reshape(
            foreign.tri_pos.shape)
        surf_pts = repose_points(
            [v.pos for t in surface for v in t.verts],
            [v.weights for t in surface for v in t.verts], tgt_skin)
        pose_world = {j: m[:3, 3] for j, m in tgt_pose_mats.items()}
        log("pose-space retargeting: source + target surface reposed to Wait1")

    target_pts = (np.asarray(surf_pts) if surf_pts is not None
                  else np.array([v.pos for t in surface for v in t.verts]))
    scale, offset = align(foreign, target_pts, rot_y)

    # physics chains (target's cape/tail dynamics) are forbidden weight
    # targets for foreign verts: expand each chain root to its joint subtree
    forbidden = set()
    chain_roots = load_dynamics(char_code)
    if chain_roots:
        by_name = {b.name: b.id for b in rigkit.bones if b.name.startswith("JOBJ_")}
        kids: dict = {}
        for b in rigkit.bones:
            if b.name.startswith("JOBJ_"):
                kids.setdefault(b.parent, []).append(b.id)
        for root in chain_roots:
            rid = by_name.get(f"JOBJ_{root}")
            if rid is None:
                continue
            stack = [rid]
            while stack:
                cur = stack.pop()
                forbidden.add(cur)
                stack.extend(kids.get(cur, []))
        log(f"forbidden dynamic-chain bones: {sorted(forbidden)}")

    if rigid_bone is not None:
        # debug/prop mode: the whole mesh rides one bone
        weights = [[(int(rigid_bone), 1.0)]] * (len(foreign.tri_pos) * 3)
        log(f"rigid-bound everything to JOBJ_{rigid_bone}")
    else:
        weights = transfer_weights(rigkit, foreign, max_weights, surface=surface,
                                   surface_pts=surf_pts, bone_world=pose_world,
                                   forbidden=forbidden)

    if tgt_skin is not None:
        # un-pose: store verts so target LBS at rest pose lands them exactly
        # where they are now
        pts = foreign.tri_pos.reshape(-1, 3)
        out_pts = np.array(pts, copy=True)
        for i, wlist in enumerate(weights):
            m = np.zeros((4, 4))
            tot = 0.0
            for bone, w in wlist:
                if bone in tgt_skin:
                    m += tgt_skin[bone] * w
                    tot += w
            if tot <= 0:
                continue
            p = np.linalg.inv(m / tot) @ np.array([pts[i][0], pts[i][1], pts[i][2], 1.0])
            out_pts[i] = p[:3]
        foreign.tri_pos = out_pts.reshape(foreign.tri_pos.shape)
        log("un-posed verts into target bind space")

    n_tex = emit(rigkit, foreign, weights, Path(out_path), max_texture,
                 visible_indices=visible, total_dobjs=total)
    log(f"rigged: scale {scale:.3f}, {len(weights)} corners, {n_tex} textures")
    return {"tris": len(foreign.tri_pos), "scale": scale, "textures": n_tex}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rigkit", required=True, help="character rig kit SMD (from --model export)")
    ap.add_argument("--mesh", required=True, help="foreign mesh (smd/glb/obj)")
    ap.add_argument("--out", required=True, help="output SMD path")
    ap.add_argument("--rot-y", type=float, default=0.0, help="pre-rotation of source mesh (deg)")
    ap.add_argument("--max-weights", type=int, default=MAX_WEIGHTS_DEFAULT)
    ap.add_argument("--max-tris", type=int, default=9000,
                    help="decimate the foreign mesh to roughly this many triangles")
    ap.add_argument("--max-texture", type=int, default=512,
                    help="clamp generated (GLB) textures to this dimension")
    ap.add_argument("--char-code", default=None,
                    help="Pl-code for the visibility table (e.g. PlFx)")
    args = ap.parse_args()

    rig_mesh(args.rigkit, args.mesh, args.out, rot_y=args.rot_y,
             max_weights=args.max_weights, max_tris=args.max_tris,
             max_texture=args.max_texture, char_code=args.char_code)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
