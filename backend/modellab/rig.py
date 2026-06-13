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


def _clean_soup(verts, faces):
    """Recover a near-manifold mesh from AI triangle soup so QEM can collapse
    it. Hunyuan3D's marching-cubes export DUPLICATES every face (~1.66x) and
    leaves non-manifold edges — QEM simplifiers treat each as a border and
    stop at a huge floor (the pilot: 234k faces, euler 92871, both pyfqmr AND
    fast_simplification refused to go below 92930 = the duplicate-face count).
    Merging coincident verts + dropping degenerate/duplicate faces drops euler
    to ~0 and lets decimation reach the real target."""
    import trimesh
    m = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    m.merge_vertices(digits_vertex=4)
    m.update_faces(m.nondegenerate_faces(height=1e-6))
    m.update_faces(m.unique_faces())
    m.remove_unreferenced_vertices()
    return np.asarray(m.vertices), np.asarray(m.faces)


def _reproject_attrs(o_pos, o_uv, o_norm, pts, pts_n=None):
    """Transfer UV + normal from the original triangles to decimated vertices
    by CLOSEST-POINT-ON-TRIANGLE barycentric interpolation.

    Nearest-vertex (or nearest deduplicated-position) transfer corrupts a
    textured atlas: the decimator MOVES vertices, so a small position error
    jumps to a different UV island, and welding seam corners (same position,
    different UV) picks one side arbitrarily — the whole body samples scrambled
    atlas fragments (the in-game "chrome"). Barycentric within a single source
    triangle keeps each sample on a consistent UV island.

    pts_n (per-query surface normals, e.g. the decimated face normals) breaks
    ties by ORIENTATION: AI 'soup' has internal/overlapping faces (jacket over
    body, hollow cavities), so the geometrically-nearest original face to a
    surface vertex can be a back/internal face with unrelated UVs. Scoring
    distance * (1 + 2*(1-alignment)) makes a misaligned face have to be far
    closer to win, keeping samples on the correct outer surface.

    Fast + bounded memory: cKDTree over face CENTROIDS (no point duplication,
    so no scipy hang), K nearest faces per vertex, clamped-barycentric closest
    point. (The old trimesh.proximity.closest_point was O(query*faces) in
    memory — 40GB+ on a 234k-face mesh.)"""
    from scipy.spatial import cKDTree
    F = len(o_pos)
    cent = o_pos.mean(axis=1)
    tree = cKDTree(cent, balanced_tree=False, compact_nodes=False)
    K = min(12, F)
    ofn = np.cross(o_pos[:, 1] - o_pos[:, 0], o_pos[:, 2] - o_pos[:, 0])
    ofl = np.linalg.norm(ofn, axis=1, keepdims=True)
    ofn = np.divide(ofn, ofl, out=np.zeros_like(ofn), where=ofl > 1e-12)

    def sample(q, qn):
        _, idx = tree.query(q, k=K, workers=-1)
        if idx.ndim == 1:
            idx = idx[:, None]
        n = len(q)
        bs = np.full(n, np.inf)
        buv = np.zeros((n, 2))
        bn = np.zeros((n, 3))
        for k in range(idx.shape[1]):
            f = idx[:, k]
            tp = o_pos[f]
            a, b, c = tp[:, 0], tp[:, 1], tp[:, 2]
            v0, v1, v2 = b - a, c - a, q - a
            d00 = (v0 * v0).sum(1); d01 = (v0 * v1).sum(1); d11 = (v1 * v1).sum(1)
            d20 = (v2 * v0).sum(1); d21 = (v2 * v1).sum(1)
            den = d00 * d11 - d01 * d01
            den = np.where(np.abs(den) < 1e-12, 1e-12, den)
            vv = (d11 * d20 - d01 * d21) / den
            ww = (d00 * d21 - d01 * d20) / den
            bary = np.clip(np.stack([1 - vv - ww, vv, ww], axis=1), 0, None)
            bary /= bary.sum(1, keepdims=True) + 1e-12
            recon = (bary[:, :, None] * tp).sum(1)
            dist = np.linalg.norm(q - recon, axis=1)
            sc = dist * (1.0 + 2.0 * (1.0 - np.clip((ofn[f] * qn).sum(1), -1, 1))) \
                if qn is not None else dist
            m = sc < bs
            bs[m] = sc[m]
            buv[m] = (bary[:, :, None] * o_uv[f])[m].sum(1)
            bn[m] = (bary[:, :, None] * o_norm[f])[m].sum(1)
        return buv, bn

    best_uv, best_n = sample(pts, pts_n)

    # per-face UV coherence: a decimated triangle whose 3 corners landed on
    # DIFFERENT atlas islands (large UV spread) is a cross-island shard (the
    # speckle that survives even at high tri counts). Re-sample those faces at
    # the CENTROID and flatten all 3 corners onto it — one atlas point, no
    # stretch across islands. Corners come grouped 3-per-face (v2[f2]).
    uvf = best_uv.reshape(-1, 3, 2)
    spread = np.linalg.norm(uvf - uvf.mean(1, keepdims=True), axis=2).max(1)
    bad = spread > 0.06
    if bad.any():
        pf = pts.reshape(-1, 3, 3)[bad].mean(1)
        nf = pts_n.reshape(-1, 3, 3)[bad].mean(1) if pts_n is not None else None
        cuv, cn = sample(pf, nf)
        bad3 = np.repeat(bad, 3)
        best_uv[bad3] = np.repeat(cuv, 3, axis=0)
        best_n[bad3] = np.repeat(cn, 3, axis=0)

    ln = np.linalg.norm(best_n, axis=1, keepdims=True)
    best_n = np.divide(best_n, ln, out=np.zeros_like(best_n), where=ln > 1e-9)
    return best_uv, best_n


def decimate(foreign: ForeignMesh, max_tris: int) -> ForeignMesh:
    """Reduce the foreign mesh to ~max_tris, re-projecting UVs and normals
    from the original surface (the simplifier drops attributes)."""
    import pyfqmr

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
        cv, cf = _clean_soup(verts, faces)
        s = pyfqmr.Simplify()
        s.setMesh(cv, cf)
        s.simplify_mesh(target_count=n_target, aggressiveness=7,
                        preserve_border=False, verbose=0)
        v2, f2, fn2 = s.getMesh()           # fn2 = per-face normals

        # re-project UV + normal from the ORIGINAL triangles onto the decimated
        # vertices by closest-point barycentric, using the decimated face
        # normals to reject internal/back faces (seam- + soup-safe — see
        # _reproject_attrs)
        corners = v2[f2].reshape(-1, 3)
        fn2 = np.asarray(fn2)
        fl = np.linalg.norm(fn2, axis=1, keepdims=True)
        fn2 = np.divide(fn2, fl, out=np.zeros_like(fn2), where=fl > 1e-9)
        corner_n = np.repeat(fn2, 3, axis=0)
        uv, nrm = _reproject_attrs(tri, foreign.tri_uv[idx],
                                   foreign.tri_norm[idx], corners,
                                   pts_n=corner_n)

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
    part_of=None, vert_parts=None, match_pos=None, smooth_iters=4,
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

    # match positions may differ from the real geometry: a tall source torso
    # keeps its looks but BINDS as if compressed onto the target's hip->neck
    # span (querying with the real positions handed upper-chest verts
    # near-arbitrary torso bones — the run-pose garble)
    mpts = np.asarray(match_pos).reshape(-1, 3) if match_pos is not None else pts

    tree = cKDTree(van_pts)
    K = min(24, len(van_pts))
    d_geo, idx = tree.query(mpts, k=K)
    anchor_d = np.linalg.norm(mpts[:, None, :] - anchors[idx], axis=2)
    score = d_geo + 1.2 * anchor_d

    # semantic part constraint: a vert labeled with a body part may only
    # sample vanilla corners whose dominant bone belongs to an ALLOWED part
    # (head verts never ride arm bones — cross-part sampling was the source
    # of every shard/melt artifact on cross-character rigs)
    if part_of and vert_parts is not None:
        from modellab.skeleton_parts import ALLOWED
        sample_part = []
        for wlist in van_corner_w:
            mass: dict = {}
            for bone, w in wlist:
                p = part_of.get(stabilize(bone))
                if p:
                    mass[p] = mass.get(p, 0.0) + w
            sample_part.append(max(mass, key=mass.get) if mass else None)
        sample_part = np.asarray(sample_part, dtype=object)

        def allowed_of(vp):
            # vp may be a single label or a SET of labels (mixed-weight verts
            # like skirts keep every >=15% part); None = unconstrained
            if vp is None:
                return None
            labels = vp if isinstance(vp, (set, frozenset)) else {vp}
            out = set()
            for p in labels:
                a = ALLOWED.get(p)
                if a is None:
                    return None
                out |= a
            return out

        penalty = np.zeros_like(score)
        for k in range(len(pts)):
            allowed = allowed_of(vert_parts[k])
            if allowed is None:
                continue
            cand = sample_part[idx[k]]
            penalty[k] = [0.0 if (cp is None or cp in allowed) else 1e4
                          for cp in cand]
        score = score + penalty

    best = idx[np.arange(len(pts)), score.argmin(axis=1)]

    raw = []
    for k in range(len(pts)):
        acc: dict[int, float] = {}
        for bone, w in van_corner_w[best[k]]:
            bone = stabilize(bone)
            acc[bone] = acc.get(bone, 0.0) + w
        total = sum(acc.values()) or 1.0
        raw.append({b: w / total for b, w in acc.items()})

    smoothed = smooth_weights(pts, raw, iterations=smooth_iters)

    # distance gate: smoothing can diffuse weights far up the body (collar ->
    # head picks up ARM bones; at non-rest poses those verts stretch between
    # head and arm). A vert may only keep weights to bones physically near it.
    height = float(pts[:, 1].max() - pts[:, 1].min()) or 1.0
    max_reach = max(2.0, 0.15 * height)
    stable_ids = [b for b in world if b in stable]
    stable_pos = np.array([world[b] for b in stable_ids])

    if part_of and vert_parts is not None:
        from modellab.skeleton_parts import ALLOWED as _ALLOWED
    out = []
    for k, acc in enumerate(smoothed):
        gated = {b: w for b, w in acc.items()
                 if b in world and
                 float(np.linalg.norm(mpts[k] - world[b])) <= max_reach}
        if not gated:
            # no held bone is near (crest tips, prop extremities): ride the
            # single nearest STABLE bone instead of a far-flung mixture —
            # restricted to the vert's allowed body parts when labeled
            cand_ids, cand_pos = stable_ids, stable_pos
            if part_of and vert_parts is not None and vert_parts[k]:
                vp = vert_parts[k]
                labels = vp if isinstance(vp, (set, frozenset)) else {vp}
                allowed = set()
                for p in labels:
                    a = _ALLOWED.get(p)
                    if a is None:
                        allowed = None
                        break
                    allowed |= a
                if allowed:
                    sel = [i for i, b in enumerate(stable_ids)
                           if part_of.get(b) in allowed]
                    if sel:
                        cand_ids = [stable_ids[i] for i in sel]
                        cand_pos = stable_pos[sel]
            nearest = cand_ids[int(np.linalg.norm(cand_pos - mpts[k], axis=1).argmin())]
            gated = {nearest: 1.0}
        top = sorted(gated.items(), key=lambda kv: -kv[1])[:max_weights]
        total = sum(w for _, w in top) or 1.0
        out.append([(b, w / total) for b, w in top])

    # cloth keeps an anchor: capes may FOLD with the legs but not ride them —
    # a cape vert majority-bound to one thigh swings between the legs. Cap
    # the leg share at half and give the rest to the nearest torso bone.
    if part_of and vert_parts is not None:
        torso_ids = [b for b in stable_ids if part_of.get(b) == "torso"]
        torso_pos = (np.array([world[b] for b in torso_ids])
                     if torso_ids else None)
        leg_parts = {"l_leg", "r_leg"}
        for k in range(len(pts)):
            vp = vert_parts[k]
            labels = vp if isinstance(vp, (set, frozenset)) else ({vp} if vp else set())
            if "cloth" not in labels or torso_pos is None:
                continue
            leg_share = sum(w for b, w in out[k]
                            if part_of.get(b) in leg_parts)
            if leg_share <= 0.5:
                continue
            scale_down = 0.5 / leg_share
            kept = [(b, w * scale_down) if part_of.get(b) in leg_parts
                    else (b, w) for b, w in out[k]]
            spill = 1.0 - sum(w for _, w in kept)
            anchor = torso_ids[int(np.linalg.norm(
                torso_pos - mpts[k], axis=1).argmin())]
            merged: dict = {}
            for b, w in kept:
                merged[b] = merged.get(b, 0.0) + w
            merged[anchor] = merged.get(anchor, 0.0) + spill
            top = sorted(merged.items(), key=lambda kv: -kv[1])[:max_weights]
            total = sum(w for _, w in top) or 1.0
            out[k] = [(b, w / total) for b, w in top]

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

    # (a triangle-coherence snap pass lived here briefly: it re-bound any
    # triangle spanning skeleton-distant bones to its mates' blend. REVERTED —
    # the snapping was a positive-feedback loop (each fix created new
    # incoherent boundary triangles; iteration counts GREW) and produced
    # region-scale melting in-game. Cross-part contamination must be
    # prevented at SAMPLING time via skeleton part labels, not patched after.)
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


def parametric_weights(pts, vert_parts, proxy_parts, proxy_parents, proxy_pos,
                       tgt_parts, tgt_parents, tgt_pos, log=print):
    """Weight each vert by its fraction ALONG ITS OWN LIMB, mapped onto the
    target's bone chain — so the bend lives at the HUMAN's joint (where the
    geometry bends), not where a proximity transfer's single-bone sample lands.

    For each part: take the proxy chain's root->tip axis, project every vert to
    a fraction t in [0,1], and map t onto the target bone chain by cumulative
    LENGTH fraction, blending the two bracketing target bones. A vert at the
    human's knee (t~0.5) thus blends Fox's knee-adjacent bones and bends with
    them. Returns per-corner {bone: weight} (pre-smoothing). Used for the GLB/AI
    path; melee sources keep the proximity transfer."""
    HIP = 4
    part_data = {}
    for part in {p for p in vert_parts if p}:
        pchain = _part_chain(part, proxy_parts, proxy_parents, proxy_pos)
        tchain = _part_chain(part, tgt_parts, tgt_parents, tgt_pos)
        if len(pchain) < 2 or len(tchain) < 1:
            continue
        root = np.asarray(proxy_pos[pchain[0]], float)
        axis = np.asarray(proxy_pos[pchain[-1]], float) - root
        L = float(np.linalg.norm(axis))
        if L < 1e-6:
            continue
        tfr = _chain_param(tchain, tgt_pos)[0] if len(tchain) >= 2 else [0.0]
        part_data[part] = (root, axis / L, L, tchain, tfr)

    out = []
    for k in range(len(pts)):
        d = part_data.get(vert_parts[k])
        if d is None:
            out.append({HIP: 1.0})
            continue
        root, ax, L, tchain, tfr = d
        if len(tchain) == 1:
            out.append({tchain[0]: 1.0})
            continue
        t = float(np.clip(np.dot(pts[k] - root, ax) / L, 0.0, 1.0))
        wl = {tchain[-1]: 1.0}
        for i in range(len(tfr) - 1):
            if t <= tfr[i + 1] + 1e-9:
                seg = tfr[i + 1] - tfr[i]
                a = float(np.clip((t - tfr[i]) / seg if seg > 1e-9 else 0.0, 0, 1))
                wl = {tchain[i]: 1.0 - a, tchain[i + 1]: a}
                break
        out.append({b: w for b, w in wl.items() if w > 1e-4})
    from collections import Counter
    log("parametric weights: parts "
        f"{dict(Counter(p for p in vert_parts if p in part_data))}")
    return out


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


def _smooth_field(pts: np.ndarray, vals: np.ndarray, iterations: int = 5):
    """Laplacian-smooth a per-corner float field over the welded mesh (same
    weld/adjacency treatment as smooth_weights, but for plain vectors)."""
    key = np.round(pts / 1e-4).astype(np.int64)
    welded: dict = {}
    corner_to_v = np.empty(len(pts), dtype=np.int64)
    for i, k in enumerate(map(tuple, key)):
        corner_to_v[i] = welded.setdefault(k, len(welded))
    n_v = len(welded)

    vv = np.zeros((n_v, vals.shape[1]))
    counts = np.zeros(n_v)
    np.add.at(vv, corner_to_v, vals)
    np.add.at(counts, corner_to_v, 1)
    vv /= np.maximum(counts, 1)[:, None]

    neighbors: list[set] = [set() for _ in range(n_v)]
    for t in range(len(pts) // 3):
        a, b, c = corner_to_v[t * 3:t * 3 + 3]
        neighbors[a].update((b, c))
        neighbors[b].update((a, c))
        neighbors[c].update((a, b))

    for _ in range(iterations):
        nxt = vv.copy()
        for v in range(n_v):
            if neighbors[v]:
                nb = np.array([vv[n] for n in neighbors[v]])
                nxt[v] = 0.5 * vv[v] + 0.5 * nb.mean(axis=0)
        vv = nxt
    return vv[corner_to_v]


def part_deform(foreign: ForeignMesh, vert_parts, src_bone_parts, src_bone_pos,
                tgt_bone_parts, tgt_bone_pos, src_geom=None, tgt_geom=None,
                log=print):
    """Per-part proportion retarget: similarity-transform each labeled body
    part of the source onto the TARGET's bone anchors (both in wait space).

    A tall human's legs land on a short digitigrade fox's leg bones instead of
    hovering where the human legs used to be — proportion mismatch was the
    'floating limbs' artifact on cross-character rigs. Part SCALE comes from
    per-part MESH spread (src_geom/tgt_geom: {part: (N,3) points}) — the
    actual body size; bone-derived measures misjudge structurally different
    skeletons. Translation matches bone-anchor centroids. The per-corner
    (scale, translation) field is Laplacian-smoothed so part boundaries
    deform continuously."""
    def anchors(bone_parts, bone_pos):
        per: dict = {}
        for b, p in bone_parts.items():
            if p in (None, "util") or b not in bone_pos:
                continue
            per.setdefault(p, []).append(np.asarray(bone_pos[b]))
        return {p: np.array(v) for p, v in per.items()}

    def rms_spread(arr):
        # trimmed: drop the farthest 15% so swords/sleeves/props don't
        # inflate a part's apparent size
        c = arr.mean(axis=0)
        d2 = ((arr - c) ** 2).sum(axis=1)
        keep = d2 <= np.percentile(d2, 85)
        return float(np.sqrt(d2[keep].mean()))

    src_a = anchors(src_bone_parts, src_bone_pos)
    tgt_a = anchors(tgt_bone_parts, tgt_bone_pos)

    scales: dict = {}
    for part, sp in src_a.items():
        # cloth has no stable target home (dynamics are forbidden): ride torso
        tgt_part = part if part in tgt_a else None
        if part == "cloth":
            tgt_part = "torso" if "cloth" not in tgt_a else "cloth"
        if tgt_part is None or tgt_part not in tgt_a:
            continue
        # scale from MESH geometry spread (bone-chain lengths misjudge parts
        # whose skeletons differ structurally: fox's torso is 3 short bones
        # under a fat body, his head part includes long ear/antenna chains)
        s = 1.0
        sg = (src_geom or {}).get(part)
        tg = (tgt_geom or {}).get(tgt_part)
        if sg is not None and tg is not None and len(sg) > 8 and len(tg) > 8:
            s_sp, t_sp = rms_spread(np.asarray(sg)), rms_spread(np.asarray(tg))
            if s_sp > 1e-6 and t_sp > 1e-6:
                s = t_sp / s_sp
        if part == "head":
            # keep the source's head size — a fox-proportioned (chibi) head
            # reads as wrong on humanoid ports
            s = float(np.clip(s, 0.95, 1.1))
        scales[part] = float(np.clip(s, 0.5, 2.0))

    # symmetrize limbs: l/r spreads differ by pose and held props, anatomy
    # doesn't
    for a, b in (("l_arm", "r_arm"), ("l_leg", "r_leg")):
        if a in scales and b in scales:
            m = (scales[a] + scales[b]) / 2
            scales[a] = scales[b] = m

    def rot_between(u, v):
        """Minimal rotation matrix taking direction u to direction v."""
        u = u / max(np.linalg.norm(u), 1e-9)
        v = v / max(np.linalg.norm(v), 1e-9)
        c = float(np.dot(u, v))
        ax = np.cross(u, v)
        s = float(np.linalg.norm(ax))
        if s < 1e-8:
            return np.eye(3) if c > 0 else -np.eye(3)
        ax = ax / s
        K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
        return np.eye(3) + s * K + (1 - c) * (K @ K)

    def root_tip(pts_arr, body_center):
        d = np.linalg.norm(pts_arr - body_center, axis=1)
        root = pts_arr[int(d.argmin())]
        tip = pts_arr[int(np.linalg.norm(pts_arr - root, axis=1).argmax())]
        return root, tip

    src_center = (src_a["torso"].mean(axis=0) if "torso" in src_a
                  else np.mean([a.mean(axis=0) for a in src_a.values()], axis=0))
    tgt_center = (tgt_a["torso"].mean(axis=0) if "torso" in tgt_a
                  else np.mean([a.mean(axis=0) for a in tgt_a.values()], axis=0))

    # full per-part affine: p' = s·R·p + T. Limbs additionally ROTATE about
    # their root so the geometry lies along the TARGET's limb axis — without
    # this, a source whose wait pose holds the arms differently keeps its own
    # arm direction and renders sticking out of the target's shoulders
    LIMBS = {"l_arm", "r_arm", "l_leg", "r_leg"}
    transforms: dict = {}
    for part, s in scales.items():
        tgt_part = part if part in tgt_a else ("torso" if part == "cloth" else part)
        if part == "cloth" and "cloth" in tgt_a:
            tgt_part = "cloth"
        R = np.eye(3)
        if part in LIMBS:
            s_root, s_tip = root_tip(src_a[part], src_center)
            t_root, t_tip = root_tip(tgt_a[tgt_part], tgt_center)
            R = rot_between(s_tip - s_root, t_tip - t_root)
            pivot_s, pivot_t = s_root, t_root
        else:
            pivot_s = src_a[part].mean(axis=0)
            pivot_t = tgt_a[tgt_part].mean(axis=0)
        T = pivot_t - s * (R @ pivot_s)
        transforms[part] = (s, R, T)

    if not transforms:
        return False
    fallback = transforms.get("torso") or next(iter(transforms.values()))

    def quat(R):
        # rotation matrix -> quaternion (w, x, y, z)
        tr = R[0, 0] + R[1, 1] + R[2, 2]
        if tr > 0:
            S = math.sqrt(tr + 1.0) * 2
            return np.array([0.25 * S, (R[2, 1] - R[1, 2]) / S,
                             (R[0, 2] - R[2, 0]) / S, (R[1, 0] - R[0, 1]) / S])
        i = int(np.argmax([R[0, 0], R[1, 1], R[2, 2]]))
        j, k = (i + 1) % 3, (i + 2) % 3
        S = math.sqrt(max(1.0 + R[i, i] - R[j, j] - R[k, k], 1e-12)) * 2
        q = np.zeros(4)
        q[0] = (R[k, j] - R[j, k]) / S
        q[1 + i] = 0.25 * S
        q[1 + j] = (R[j, i] + R[i, j]) / S
        q[1 + k] = (R[k, i] + R[i, k]) / S
        return q

    def quat_mat(q):
        w, x, y, z = q
        return np.array([
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ])

    base_q = None
    pts = foreign.tri_pos.reshape(-1, 3)
    field = np.zeros((len(pts), 8))      # s, quat(4), T(3)
    for k in range(len(pts)):
        s, R, T = transforms.get(vert_parts[k], fallback)
        q = quat(R)
        if base_q is None:
            base_q = q
        if np.dot(q, base_q) < 0:        # hemisphere-align for blending
            q = -q
        field[k, 0] = s
        field[k, 1:5] = q
        field[k, 5:] = T
    # wide blend: shoulders/hips sit at part boundaries — a sharp jump
    # between torso and a rotated/compressed limb pinches them
    field = _smooth_field(pts, field, iterations=10)
    out_pts = np.empty_like(pts)
    for k in range(len(pts)):
        q = field[k, 1:5]
        n = np.linalg.norm(q)
        R = quat_mat(q / n) if n > 1e-9 else np.eye(3)
        out_pts[k] = field[k, 0] * (R @ pts[k]) + field[k, 5:]
    foreign.tri_pos = out_pts.reshape(foreign.tri_pos.shape)
    log("part deform: " + "  ".join(
        f"{p}x{s:.2f}{'+rot' if not np.allclose(R_, np.eye(3)) else ''}"
        for p, (s, R_, _) in sorted(transforms.items())))
    return True


def _part_chain(part, bone_parts, parents, positions):
    """Main bone chain of a body part: root (the part bone whose parent is
    outside the part) -> deepest descendant, as an ordered list of bone ids."""
    members = {b for b, p in bone_parts.items() if p == part and b in positions}
    if not members:
        return []
    roots = [b for b in members if parents.get(b) not in members]
    if not roots:
        roots = [min(members)]
    kids: dict = {}
    for b in members:
        par = parents.get(b)
        if par in members:
            kids.setdefault(par, []).append(b)

    best = []
    for root in roots:
        # DFS for the longest cumulative-length path
        stack = [(root, [root], 0.0)]
        local_best = ([root], 0.0)
        while stack:
            cur, path, dist = stack.pop()
            if dist >= local_best[1]:
                local_best = (path, dist)
            for c in kids.get(cur, []):
                seg = float(np.linalg.norm(np.asarray(positions[c])
                                           - np.asarray(positions[cur])))
                stack.append((c, path + [c], dist + seg))
        if local_best[1] >= (best[1] if best else -1):
            best = local_best
    return best[0]


def _chain_param(chain, positions):
    """Cumulative-length fraction (0..1) at every chain joint + total len."""
    pos = [np.asarray(positions[b]) for b in chain]
    seg = [0.0]
    for i in range(1, len(pos)):
        seg.append(seg[-1] + float(np.linalg.norm(pos[i] - pos[i - 1])))
    total = seg[-1] or 1.0
    return [s / total for s in seg], total, pos


def _chain_point(t, fracs, pos):
    """Interpolated point + tangent on a chain polyline at fraction t."""
    t = min(max(t, 0.0), 1.0)
    for i in range(1, len(fracs)):
        if t <= fracs[i] or i == len(fracs) - 1:
            f0, f1 = fracs[i - 1], fracs[i]
            a = 0.0 if f1 <= f0 else (t - f0) / (f1 - f0)
            p = pos[i - 1] + a * (pos[i] - pos[i - 1])
            d = pos[i] - pos[i - 1]
            n = np.linalg.norm(d)
            if n < 1e-9:
                d = pos[-1] - pos[0]
                n = max(np.linalg.norm(d), 1e-9)
            return p, d / n
    return pos[-1], np.array([0, 1, 0.0])


def segment_deform(foreign: ForeignMesh, src_parts, src_parents, src_pos,
                   tgt_parts, tgt_parents, tgt_pos,
                   src_geom=None, tgt_geom=None, log=print):
    """Skeleton-correspondence deform (replaces the rigid 8-part version):
    every SOURCE bone maps to the point at the same length-fraction along its
    part's TARGET chain, with an anisotropic affine — longitudinal scale =
    chain length ratio, radial scale = part mesh-thickness ratio, rotation =
    chain tangent alignment. Verts blend their bones' affines BY THEIR SOURCE
    SKIN WEIGHTS, so shoulders/hips deform like skin instead of tearing at
    part boundaries. Both skeletons in their own wait space."""
    def radius(geom, fracs, pos):
        if geom is None or len(geom) < 12:
            return None
        arr = np.asarray(geom)
        # median distance from the chain polyline (sampled at joints)
        d = np.min(np.linalg.norm(arr[:, None, :] - np.asarray(pos)[None, :, :],
                                  axis=2), axis=1)
        return float(np.median(d))

    parts = [p for p in set(src_parts.values())
             if p not in (None, "util")]
    bone_affine: dict = {}
    part_params: dict = {}
    chains: dict = {}
    info = []
    for part in parts:
        tgt_part = part
        if part not in set(tgt_parts.values()):
            if part != "cloth":
                continue
            tgt_part = "torso"
        if part == "cloth" and "cloth" not in set(tgt_parts.values()):
            tgt_part = "torso"
        s_chain = _part_chain(part, src_parts, src_parents, src_pos)
        t_chain = _part_chain(tgt_part, tgt_parts, tgt_parents, tgt_pos)
        if len(s_chain) < 2 or len(t_chain) < 2:
            continue
        s_fr, s_len, s_cpos = _chain_param(s_chain, src_pos)
        t_fr, t_len, t_cpos = _chain_param(t_chain, tgt_pos)

        def trimmed_rms(geom):
            # 3D spread with the farthest 15% dropped (swords/sleeves/props):
            # the ONE robust size signal — axis-projected spans and chain
            # radii both misfire on jackets, capes and structurally
            # different skeletons (tried; produced nub arms / balloon chests)
            if geom is None or len(geom) < 12:
                return None
            arr = np.asarray(geom)
            c = arr.mean(axis=0)
            d2 = ((arr - c) ** 2).sum(axis=1)
            keep = d2 <= np.percentile(d2, 85)
            return float(np.sqrt(d2[keep].mean()))

        s_sp = trimmed_rms((src_geom or {}).get(part))
        t_sp = trimmed_rms((tgt_geom or {}).get(tgt_part))
        if s_sp and t_sp and s_sp > 1e-6:
            s_long = t_sp / s_sp
        else:
            s_long = t_len / s_len if s_len > 1e-6 else 1.0
        s_rad = s_long          # uniform: anisotropy measurements unreliable
        if part == "head":
            s_long = s_rad = float(np.clip(s_long, 0.95, 1.1))
        s_long = float(np.clip(s_long, 0.5, 2.0))
        s_rad = float(np.clip(s_rad, 0.5, 2.0))
        info.append(f"{part}:L{s_long:.2f}/R{s_rad:.2f}")

        # ONE anisotropic affine per part (per-bone anchors scrambled regions
        # whose chains bend differently): rotate the part axis onto the
        # target's, scale length and thickness independently, pivot limbs at
        # their root joint and core parts at the chain midpoint
        src_dir = np.asarray(s_cpos[-1]) - np.asarray(s_cpos[0])
        tgt_dir = np.asarray(t_cpos[-1]) - np.asarray(t_cpos[0])
        if part in ("l_arm", "r_arm", "l_leg", "r_leg", "cloth"):
            pivot_s, pivot_t = np.asarray(s_cpos[0]), np.asarray(t_cpos[0])
        else:
            pivot_s = np.asarray(s_cpos).mean(axis=0)
            pivot_t = np.asarray(t_cpos).mean(axis=0)
        part_params[part] = [s_long, s_rad, src_dir, tgt_dir, pivot_s, pivot_t]
        chains[part] = (s_chain, s_fr, [np.asarray(p) for p in s_cpos],
                        t_fr, [np.asarray(p) for p in t_cpos])

    if not part_params:
        return False
    # l/r symmetry: wait poses bend limbs asymmetrically; anatomy doesn't
    for a, b in (("l_arm", "r_arm"), ("l_leg", "r_leg")):
        if a in part_params and b in part_params:
            ml = (part_params[a][0] + part_params[b][0]) / 2
            mr = (part_params[a][1] + part_params[b][1]) / 2
            part_params[a][0] = part_params[b][0] = ml
            part_params[a][1] = part_params[b][1] = mr

    LIMBS = ("l_arm", "r_arm", "l_leg", "r_leg")
    bone_to_aff: dict = {}      # SOURCE bone id -> affine (M, src_anchor, tgt_anchor)

    def assign_part_bones(part_name, aff):
        for b, p in src_parts.items():
            if p == part_name:
                bone_to_aff[b] = aff

    # CORE parts first (limb roots attach to the deformed torso). No rotation:
    # core chain axes are noisy (fox's "head axis" runs through his
    # ear/antenna chains) — rotating them crinks the neck.
    for part in sorted(part_params, key=lambda p: p != "torso"):
        if part in LIMBS:
            continue
        s_long, s_rad, src_dir, tgt_dir, pivot_s, pivot_t = part_params[part]
        u = src_dir / max(np.linalg.norm(src_dir), 1e-9)
        S = s_long * np.outer(u, u) + s_rad * (np.eye(3) - np.outer(u, u))
        bone_affine[part] = (S, pivot_s, pivot_t)
        assign_part_bones(part, bone_affine[part])

    # LIMBS: per-SEGMENT mapping with true joint correspondence. One rigid
    # rotation cannot unbend a source whose wait pose bends the elbow (marth's
    # crossed arms rendered beside fox's hanging arm bones) — instead the
    # upper and lower segments each get their own rotation, sharing the
    # elbow/knee anchor, so bent limbs UNBEND onto the target's pose and stay
    # connected by construction.
    for part in LIMBS:
        if part not in chains:
            continue
        s_chain, s_fr, s_cpos, t_fr, t_cpos = chains[part]
        # principal source joints: steps >= 12% of the chain (skips zero-length
        # assist joints), endpoints always included
        keep = [0]
        for i in range(1, len(s_fr)):
            if s_fr[i] - s_fr[keep[-1]] >= 0.12 or i == len(s_fr) - 1:
                keep.append(i)
        if len(keep) < 2:
            continue
        fracs = [s_fr[i] for i in keep]
        s_anchor = [s_cpos[i] for i in keep]
        t_anchor = [_chain_point(f, t_fr, t_cpos)[0] for f in fracs]
        # widen the limb laterally to the deformed torso's attachment (broad
        # shoulders sink when pinned at fox's narrow roots); height/depth stay
        # skeleton-true
        if "torso" in bone_affine:
            Mt, st, tt = bone_affine["torso"]
            dx = float((Mt @ (s_anchor[0] - st) + tt)[0] - t_anchor[0][0])
            t_anchor = [a + np.array([dx, 0, 0]) for a in t_anchor]

        def seg_frame(d_cur, d_next):
            # full orthonormal frame: x along the segment, z = bend-plane
            # normal (next segment defines the elbow/knee plane). Aligning
            # FRAMES instead of axes controls the roll about the limb —
            # minimal axis rotations left it arbitrary and twisted the
            # shoulder/trap geometry ~90 degrees.
            x = d_cur / max(np.linalg.norm(d_cur), 1e-9)
            n = np.cross(d_cur, d_next)
            if np.linalg.norm(n) < 1e-6:
                n = np.cross(x, [0.0, 1.0, 0.0])
            if np.linalg.norm(n) < 1e-6:
                n = np.cross(x, [0.0, 0.0, 1.0])
            z = n / max(np.linalg.norm(n), 1e-9)
            y = np.cross(z, x)
            return np.column_stack([x, y, z])

        seg_affs = []
        n_seg = len(fracs) - 1
        for i in range(n_seg):
            v_s = s_anchor[i + 1] - s_anchor[i]
            v_t = t_anchor[i + 1] - t_anchor[i]
            ls, lt = np.linalg.norm(v_s), np.linalg.norm(v_t)
            if ls < 1e-6 or lt < 1e-6:
                seg_affs.append((np.eye(3), s_anchor[i], t_anchor[i]))
                continue
            s = float(np.clip(lt / ls, 0.45, 1.8))
            j = i + 1 if i + 1 < n_seg else i - 1
            d_s_next = (s_anchor[j + 1] - s_anchor[j]) if 0 <= j < n_seg else v_s
            d_t_next = (t_anchor[j + 1] - t_anchor[j]) if 0 <= j < n_seg else v_t
            R = seg_frame(v_t, d_t_next) @ seg_frame(v_s, d_s_next).T
            # anisotropic: length follows the joint anchors exactly, but
            # thickness only DAMPED (s^0.4, capped) — uniform shrink made
            # noodle limbs, measured radial ratios ballooned them
            s_rad = float(np.clip(s ** 0.4, 0.8, 1.15))
            u = v_s / ls
            S = s * np.outer(u, u) + s_rad * (np.eye(3) - np.outer(u, u))
            seg_affs.append((R @ S, s_anchor[i], t_anchor[i]))
        info.append(f"{part}:{len(seg_affs)}seg")

        # every part bone joins the segment its chain-fraction falls into
        cpos_arr = np.asarray(s_cpos)
        for b, p in src_parts.items():
            if p != part or b not in src_pos:
                continue
            bp = np.asarray(src_pos[b])
            f = s_fr[int(np.linalg.norm(cpos_arr - bp, axis=1).argmin())]
            si = 0
            for i in range(len(fracs) - 1):
                if f >= fracs[i]:
                    si = i
            bone_to_aff[b] = seg_affs[si]

    if not bone_to_aff:
        return False
    fb = bone_affine.get("torso") or next(iter(bone_affine.values()))

    pts = foreign.tri_pos.reshape(-1, 3)
    wpp = [w for tw in foreign.tri_src_w for w in tw]
    out = np.empty_like(pts)
    LIMB_SET = set(LIMBS)
    for k in range(len(pts)):
        # blend affines by the vert's source skin weights — shoulder/hip/elbow
        # verts carry mixed weights and deform like skin instead of tearing.
        # WITHIN one limb, sharpen the blend (w^2): the upper/lower segment
        # rotations diverge hard (straight human knee -> digitigrade fox) and
        # a linear mix candy-wraps the knee; cross-part blends (shoulders)
        # stay linear and smooth.
        wl = [(b, w) for b, w in wpp[k] if b in bone_to_aff]
        parts_here = {src_parts.get(b) for b, _ in wl}
        if len(parts_here) == 1 and parts_here & LIMB_SET and len(wl) > 1:
            wl = [(b, w * w) for b, w in wl]
        acc = np.zeros(3)
        tot = 0.0
        for b, w in wl:
            M, sp, tp = bone_to_aff[b]
            acc += w * (M @ (pts[k] - sp) + tp)
            tot += w
        if tot <= 1e-9:
            M, sp, tp = fb
            out[k] = M @ (pts[k] - sp) + tp
        else:
            out[k] = acc / tot
    foreign.tri_pos = out.reshape(foreign.tri_pos.shape)
    log("segment deform: " + "  ".join(sorted(info)))
    return True


def _rot_between_vec(u, v):
    u = u / max(np.linalg.norm(u), 1e-9)
    v = v / max(np.linalg.norm(v), 1e-9)
    c = float(np.dot(u, v))
    ax = np.cross(u, v)
    s = float(np.linalg.norm(ax))
    if s < 1e-8:
        return np.eye(3) if c > 0 else -np.eye(3)
    ax = ax / s
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + s * K + (1 - c) * (K @ K)


def extract_cloth_accessory(foreign, vert_parts, src_parts, src_parents,
                            src_world_mats, dyn_chains, tgt_parts, tgt_parents,
                            tgt_pos, src_geom, tgt_geom, out_dir, log=print):
    """Split the CLOTH part into a mexCostume physics accessory (akaneia
    wiki): cape geometry + the source's own dynamic joint chains, in the
    frame of an attach joint the game overwrites with a fighter bone at
    runtime. Returns (keep_tri_mask, attach_bone_target, n_cloth_tris) or
    None when there is no usable cloth."""
    import shutil as _shutil

    cloth_corners = [i for i, vp in enumerate(vert_parts) if vp == "cloth"]
    if not cloth_corners or not dyn_chains:
        return None
    n_tri = len(foreign.tri_pos)
    tri_cloth = np.zeros(n_tri, dtype=bool)
    for i in cloth_corners:
        tri_cloth[i // 3] = True
    # majority vote per triangle
    counts = np.zeros(n_tri)
    for i in cloth_corners:
        counts[i // 3] += 1
    tri_cloth = counts >= 2
    if tri_cloth.sum() < 8:
        return None

    # source chain joints (from the dynamics dump: root + descendants)
    kids: dict = {}
    for b, par in src_parents.items():
        kids.setdefault(par, []).append(b)
    chain_lists = []
    for ch in dyn_chains:
        chain = [ch["bone"]]
        while True:
            nxt = [c for c in kids.get(chain[-1], [])
                   if src_parts.get(c) == "cloth"]
            if not nxt:
                break
            chain.append(nxt[0])
        chain_lists.append((ch, chain[:max(len(ch["joints"]), 1)]))

    attach_src = src_parents.get(chain_lists[0][1][0])
    if attach_src is None or attach_src not in src_world_mats:
        return None
    A = src_world_mats[attach_src]
    A_inv = np.linalg.inv(A)

    # torso scale (same trimmed-RMS signal as the deform)
    def trimmed_rms(geom):
        if geom is None or len(geom) < 12:
            return None
        arr = np.asarray(geom)
        c = arr.mean(axis=0)
        d2 = ((arr - c) ** 2).sum(axis=1)
        keep = d2 <= np.percentile(d2, 85)
        return float(np.sqrt(d2[keep].mean()))

    s_sp = trimmed_rms((src_geom or {}).get("torso"))
    t_sp = trimmed_rms((tgt_geom or {}).get("torso"))
    s = float(np.clip((t_sp / s_sp) if (s_sp and t_sp and s_sp > 1e-6)
                      else 1.0, 0.5, 2.0))

    # accessory skeleton: J0 attach + J1 offset + the source chains
    acc = smd.SMD()
    acc.bones.append(smd.Bone(id=0, name="JOBJ_0", parent=-1))
    acc.bones.append(smd.Bone(id=1, name="JOBJ_1", parent=0))
    local_of: dict = {}
    nxt_id = 2
    local_chains = []
    for ch, chain in chain_lists:
        ids = []
        for j, b in enumerate(chain):
            par_local = 1 if j == 0 else local_of[chain[j - 1]]
            wm = src_world_mats.get(b)
            pm = (src_world_mats.get(src_parents.get(b))
                  if j > 0 else A)
            lp = (np.linalg.inv(pm) @ wm)[:3, 3] * s if wm is not None \
                else np.zeros(3)
            acc.bones.append(smd.Bone(
                id=nxt_id, name=f"JOBJ_{nxt_id}", parent=par_local,
                pos=tuple(float(x) for x in lp)))
            local_of[b] = nxt_id
            ids.append(nxt_id)
            nxt_id += 1
        local_chains.append((ch, ids))

    # placeholder mesh nodes per material (IONET groups DObjs by them)
    mats = list(dict.fromkeys(
        foreign.tri_mat[t] for t in range(n_tri) if tri_cloth[t]))
    mat_node = {}
    for m in mats:
        acc.bones.append(smd.Bone(id=nxt_id, name=f"Joint_1_Object_{len(mat_node)}",
                                  parent=-1))
        mat_node[m] = nxt_id
        nxt_id += 1

    # cape triangles in attach-local space, weights remapped to local ids
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    flat_w = [w for tw in foreign.tri_src_w for w in tw]
    for t in range(n_tri):
        if not tri_cloth[t]:
            continue
        verts = []
        for c in range(3):
            k = t * 3 + c
            p = np.asarray(foreign.tri_pos[t][c])
            pl = (A_inv @ np.append(p, 1.0))[:3] * s
            nrm = A_inv[:3, :3] @ np.asarray(foreign.tri_norm[t][c])
            wl = []
            for b, w in flat_w[k]:
                wl.append((local_of.get(b, 1), w))
            merged: dict = {}
            for b, w in wl:
                merged[b] = merged.get(b, 0.0) + w
            tot = sum(merged.values()) or 1.0
            wl = sorted(((b, w / tot) for b, w in merged.items()),
                        key=lambda kv: -kv[1])[:MAX_WEIGHTS_DEFAULT]
            tot2 = sum(w for _, w in wl) or 1.0
            verts.append(smd.Vertex(
                pos=tuple(float(x) for x in pl),
                normal=tuple(float(x) for x in nrm),
                uv=tuple(float(x) for x in foreign.tri_uv[t][c]),
                weights=[(b, w / tot2) for b, w in wl],
                parent=mat_node[foreign.tri_mat[t]]))
        acc.triangles.append(smd.Triangle(material=foreign.tri_mat[t],
                                          verts=tuple(verts)))

    smd.save(acc, out_dir / "cape.smd")
    # texture sidecar + copies
    sidecar = {}
    for m in mats:
        tex = foreign.textures.get(m)
        if tex is None:
            continue
        if isinstance(tex, (str, Path)):
            name = Path(tex).name
            _shutil.copyfile(tex, out_dir / name)
        else:                       # PIL image (GLB sources)
            name = f"{m}.png"
            tex.save(out_dir / name)
        sidecar[m] = name
    (out_dir / "cape.smd.textures.json").write_text(json.dumps(sidecar))

    # localized dynamics
    dyn_local = []
    for ch, ids in local_chains:
        dyn_local.append({
            "bone": ids[0], "PARAM1": ch["PARAM1"], "PARAM2": ch["PARAM2"],
            "PARAM3": ch["PARAM3"], "joints": ch["joints"][:len(ids)],
        })
    (out_dir / "dynamics_local.json").write_text(json.dumps(dyn_local, indent=1))

    # fox-side attach bone: top of the target torso chain (chest)
    t_chain = _part_chain("torso", tgt_parts, tgt_parents, tgt_pos)
    attach_tgt = t_chain[-1] if t_chain else 4
    (out_dir / "attach.json").write_text(json.dumps({"attachBone": int(attach_tgt)}))

    log(f"cloth accessory: {int(tri_cloth.sum())} tris, "
        f"{len(local_chains)} chains, attach JOBJ_{attach_tgt} (src {attach_src})")
    return ~tri_cloth, int(attach_tgt), int(tri_cloth.sum())


def recompute_normals(foreign: ForeignMesh):
    """Smooth vertex normals from the FINAL geometry (weld + area-weighted
    face normals). The deform pipeline moves vertices through repose, part
    deform and un-pose without transforming the stored normals — the game
    then shades with stale directions (close-up torso garble; invisible in
    the lab renders, which derive face normals from geometry)."""
    pts = foreign.tri_pos.reshape(-1, 3)
    key = np.round(pts / 1e-4).astype(np.int64)
    welded: dict = {}
    corner_to_v = np.empty(len(pts), dtype=np.int64)
    for i, k in enumerate(map(tuple, key)):
        corner_to_v[i] = welded.setdefault(k, len(welded))

    fn = np.cross(foreign.tri_pos[:, 1] - foreign.tri_pos[:, 0],
                  foreign.tri_pos[:, 2] - foreign.tri_pos[:, 0])
    acc = np.zeros((len(welded), 3))
    for t in range(len(foreign.tri_pos)):
        for c in range(3):
            acc[corner_to_v[t * 3 + c]] += fn[t]
    norms = acc[corner_to_v]
    ln = np.linalg.norm(norms, axis=1, keepdims=True)
    norms = np.divide(norms, ln, out=np.zeros_like(norms), where=ln > 1e-12)
    foreign.tri_norm = norms.reshape(foreign.tri_norm.shape)


def rig_mesh(rigkit_path, mesh_path, out_path, rot_y=0.0,
             max_weights=MAX_WEIGHTS_DEFAULT, max_tris=9000, max_texture=512,
             rigid_bone=None, char_code=None, src_char_code=None,
             target_pose=None, src_pose=None, accessory_dir=None,
             cape_dynamics=None, log=print):
    """Full rigging pass (the function behind the CLI): foreign mesh ->
    SMD (+textures/sidecar) rigged to the rig kit's skeleton. Returns stats.
    With accessory_dir + cape_dynamics (the source's dynamic-params dump),
    cloth geometry is split into a mexCostume physics accessory instead of
    being skinned onto the body."""
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

    # semantic body parts: label the TARGET skeleton; for melee sources also
    # label the SOURCE skeleton and tag every foreign corner with the part its
    # source weights belong to — the transfer then forbids cross-part sampling
    from modellab.skeleton_parts import label_parts
    tgt_parts = label_parts(rigkit, dynamic_roots=chain_roots)
    vert_parts = None
    src_parts = None
    if hasattr(foreign, "src_smd") and hasattr(foreign, "tri_src_w"):
        src_parts = label_parts(
            foreign.src_smd,
            dynamic_roots=load_dynamics(src_char_code) if src_char_code else None)
        vert_parts = []
        vert_part_sets = []
        for tw in foreign.tri_src_w:
            for wlist in tw:
                mass: dict = {}
                tot = 0.0
                for bone, w in wlist:
                    p = src_parts.get(bone)
                    if p and p != "util":
                        mass[p] = mass.get(p, 0.0) + w
                        tot += w
                vert_parts.append(max(mass, key=mass.get) if mass else None)
                # EVERY part carrying >=15% of the vert's source weight stays
                # allowed — vanilla skirts/coats are waist+thigh blends, and
                # collapsing them to the dominant part forbade leg sampling
                # (the crouch "pillar": cloth that can never follow the legs)
                vert_part_sets.append(
                    {p for p, m in mass.items() if tot and m / tot >= 0.15}
                    or None)
        from collections import Counter
        log(f"source part labels: {dict(Counter(p for p in vert_parts if p))}")

    # alignment: cross-character sources with poses get the PER-PART
    # proportion retarget (each body part lands on the target's bone anchors —
    # a global scale leaves long-limbed sources' geometry floating off the
    # target's bones); everything else gets the global height/feet align.
    target_pts = (np.asarray(surf_pts) if surf_pts is not None
                  else np.array([v.pos for t in surface for v in t.verts]))
    scale = 1.0
    deformed = False
    glb_proxy = None        # set on the GLB/AI path for parametric skinning
    if vert_parts is not None and pose_world is not None and src_pose:
        src_pose_mats = load_pose(src_pose)
        src_bone_pos = {j: m[:3, 3] for j, m in src_pose_mats.items()}
        # per-part geometry: foreign verts by their source part; target
        # surface corners (wait-posed) by their dominant bone's part
        pts_flat = foreign.tri_pos.reshape(-1, 3)
        src_geom: dict = {}
        for k, vp in enumerate(vert_parts):
            if vp:
                src_geom.setdefault(vp, []).append(pts_flat[k])
        tgt_geom: dict = {}
        s_corner = 0
        for t in surface:
            for v in t.verts:
                dom = max(v.weights, key=lambda bw: bw[1])[0] if v.weights else None
                p = tgt_parts.get(dom)
                if p and p != "util":
                    tgt_geom.setdefault(p, []).append(target_pts[s_corner])
                s_corner += 1
        src_parents_map = {b.id: b.parent for b in foreign.src_smd.bones
                           if b.name.startswith("JOBJ_")}
        tgt_parents_map = {b.id: b.parent for b in rigkit.bones
                           if b.name.startswith("JOBJ_")}

        # split cloth into a mexCostume physics accessory before skinning
        if accessory_dir and cape_dynamics and Path(cape_dynamics).exists():
            dyn_chains = json.loads(Path(cape_dynamics).read_text())
            res = extract_cloth_accessory(
                foreign, vert_parts, src_parts, src_parents_map,
                src_pose_mats, dyn_chains, tgt_parts, tgt_parents_map,
                pose_world, src_geom, tgt_geom, accessory_dir, log=log)
            if res is not None:
                keep_tri, _, _ = res
                keep_c = np.repeat(keep_tri, 3)
                fm = ForeignMesh(
                    foreign.tri_pos[keep_tri], foreign.tri_norm[keep_tri],
                    foreign.tri_uv[keep_tri],
                    [m for t, m in enumerate(foreign.tri_mat) if keep_tri[t]],
                    foreign.textures,
                    [g for t, g in enumerate(foreign.tri_group) if keep_tri[t]])
                fm.group_names = foreign.group_names
                fm.src_smd = foreign.src_smd
                fm.tri_src_w = [w for t, w in enumerate(foreign.tri_src_w)
                                if keep_tri[t]]
                foreign = fm
                vert_parts = [p for i, p in enumerate(vert_parts) if keep_c[i]]
                vert_part_sets = [p for i, p in enumerate(vert_part_sets)
                                  if keep_c[i]]
                src_geom.pop("cloth", None)

        deformed = segment_deform(foreign, src_parts, src_parents_map,
                                  src_bone_pos, tgt_parts, tgt_parents_map,
                                  pose_world, src_geom=src_geom,
                                  tgt_geom=tgt_geom, log=log)
        if deformed:
            # residual floor snap (legs already land on the target's leg
            # anchors; this only closes small global error)
            pts = foreign.tri_pos.reshape(-1, 3)
            dy = float(target_pts[:, 1].min() - pts[:, 1].min())
            if abs(dy) < 2.5:
                pts[:, 1] += dy
                foreign.tri_pos = pts.reshape(foreign.tri_pos.shape)
    elif vert_parts is None and Path(mesh_path).suffix.lower() != ".smd":
        # GLB / AI foreign mesh: NO source skeleton. Segment the humanoid
        # geometrically, synthesize a proxy skeleton, and land each part on
        # Fox's BIND bone anchors — a long human's limbs otherwise overshoot
        # Fox's short bones under one global scale (janky stretched arms/legs).
        from modellab.geometric_parts import label_vertices
        # PART-CONSTRAINED transfer (not a geometry deform): segment the
        # humanoid so a forearm vert can't bind a leg bone (the in-game jank),
        # then global-align. A proxy-skeleton segment_deform was tried and
        # MANGLED the arms — rotating the A-pose onto Fox's bind T-pose stretched
        # them to noodles (proxy_skeleton() is parked in geometric_parts for a
        # future, gentler deform). The part constraint is the stable win.
        glb_labels, ginfo = label_vertices(foreign.tri_pos.reshape(-1, 3), log=log)
        scale, _ = align(foreign, target_pts, rot_y)
        bind = joint_world_positions(rigkit)
        glb_pts = foreign.tri_pos.reshape(-1, 3)
        lab = np.array(glb_labels, dtype=object)
        # (Tried feet-to-neck shrink/squash to land the human's joints on Fox's
        # — both made it WORSE: any global distortion pulls the mesh off Fox's
        # surface and the nearest-vert transfer degrades. Fox's proportions are
        # too extreme. The lever that helps is heavier weight SMOOTHING below,
        # which blends the single-bone joints so knees/elbows bend.)
        # L/R match: if the GLB faces opposite Fox, its left arm sits on Fox's
        # right side and the part constraint would drag arms across the body.
        fox_lx = float(np.mean([bind[b][0] for b, p in tgt_parts.items()
                                if p == "l_arm" and b in bind] or [0.0]))
        glb_lx = (float(glb_pts[lab == "l_arm"][:, 0].mean())
                  if (lab == "l_arm").any() else 0.0)
        if fox_lx != 0 and np.sign(fox_lx) != np.sign(glb_lx):
            swap = {"l_arm": "r_arm", "r_arm": "l_arm",
                    "l_leg": "r_leg", "r_leg": "l_leg"}
            glb_labels = [swap.get(p, p) for p in glb_labels]
            log("L/R swapped to match Fox facing")
        # proxy skeleton (on the aligned, L/R-matched mesh) drives PARAMETRIC
        # skinning at the weight step — the real fix for torn joints.
        from modellab.geometric_parts import proxy_skeleton
        _pp, _ppar, _ppos, _ = proxy_skeleton(glb_pts, glb_labels, ginfo, log=log)
        glb_proxy = (_pp, _ppar, _ppos)
        vert_parts = glb_labels
        vert_part_sets = [({p} if p else None) for p in glb_labels]
        deformed = True       # geometry finalized by the global align above
    if not deformed:
        scale, offset = align(foreign, target_pts, rot_y)

    # MATCH-SPACE for binding: the deformed torso keeps the source's height
    # (squashing it pancakes the look — tried), but then upper-chest verts sit
    # far from the target's short torso bones and bind near-arbitrarily (the
    # run-pose torso garble). Query the transfer with a torso band compressed
    # onto the target's hip->neck span; the real geometry stays untouched.
    match_pos = None
    if deformed and vert_parts is not None:
        # bind pose for the GLB path (no animation pose); Wait1 for melee
        bw = pose_world if pose_world is not None else joint_world_positions(rigkit)
        t_tor_chain = _part_chain(
            "torso", tgt_parts,
            {b.id: b.parent for b in rigkit.bones
             if b.name.startswith("JOBJ_")}, bw)
        pts_now = foreign.tri_pos.reshape(-1, 3)
        torso_mask = np.array([vp == "torso" for vp in vert_parts])
        if torso_mask.sum() > 50 and t_tor_chain:
            tys = pts_now[torso_mask][:, 1]
            s_lo, s_hi = np.percentile(tys, 5), np.percentile(tys, 95)
            t_lo = bw[t_tor_chain[0]][1]
            t_hi = bw[t_tor_chain[-1]][1]
            pad = 0.25 * max(t_hi - t_lo, 1e-6)
            t_lo, t_hi = t_lo - pad, t_hi + pad
            if s_hi - s_lo > 1e-6 and t_hi > t_lo:
                f = (t_hi - t_lo) / (s_hi - s_lo)
                if f < 0.95:        # only when the source torso is taller
                    match_pos = pts_now.copy()
                    match_pos[torso_mask, 1] = (
                        t_lo + (pts_now[torso_mask, 1] - s_lo) * f)
                    log(f"match-space torso band: x{f:.2f} "
                        f"({s_lo:.1f}..{s_hi:.1f} -> {t_lo:.1f}..{t_hi:.1f})")

    if rigid_bone is not None:
        # debug/prop mode: the whole mesh rides one bone
        weights = [[(int(rigid_bone), 1.0)]] * (len(foreign.tri_pos) * 3)
        log(f"rigid-bound everything to JOBJ_{rigid_bone}")
    elif glb_proxy is not None:
        # GLB/AI: PARAMETRIC skinning. Proximity transfer copies Fox's
        # single-bone weights and the bend never lands at the human's joint
        # (torn knees). Instead weight each vert by its fraction along its own
        # limb, mapped onto Fox's bone chain, then smooth to blend shoulders/
        # hips. recompute_normals + emit follow as usual.
        pts_w = foreign.tri_pos.reshape(-1, 3)
        tgt_parents_map = {b.id: b.parent for b in rigkit.bones
                           if b.name.startswith("JOBJ_")}
        raw = parametric_weights(
            pts_w, vert_parts, glb_proxy[0], glb_proxy[1], glb_proxy[2],
            tgt_parts, tgt_parents_map, joint_world_positions(rigkit), log=log)
        smoothed = smooth_weights(pts_w, raw, iterations=10)
        weights = []
        for d in smoothed:
            top = sorted(d.items(), key=lambda kv: -kv[1])[:max_weights]
            tot = sum(w for _, w in top) or 1.0
            weights.append([(int(b), w / tot) for b, w in top])
        log(f"parametric skinning: {len(weights)} corners, smoothed")
    else:
        weights = transfer_weights(rigkit, foreign, max_weights, surface=surface,
                                   surface_pts=surf_pts, bone_world=pose_world,
                                   forbidden=forbidden, part_of=tgt_parts,
                                   vert_parts=(vert_part_sets
                                               if vert_parts is not None
                                               else None),
                                   match_pos=match_pos)

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

    # GX lights with the STORED vertex normals; the lab painter derives its
    # own from geometry, so bad stored normals are INVISIBLE offline but show
    # in-game as specular garbage (chrome shards over the texture). Rebuild
    # smooth normals from the FINAL geometry — unconditionally: melee sources
    # scramble normals through repose/deform/un-pose, foreign (GLB/AI) meshes
    # scramble them through decimation's per-corner attribute copy. Either way
    # the only reliable normals are the ones derived from the emitted verts.
    recompute_normals(foreign)
    log("recomputed smooth vertex normals")

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
