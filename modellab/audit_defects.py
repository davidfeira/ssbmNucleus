"""Defect metrics for a rigged output SMD — measure what the eye sees:

SEAMS: corners coincident in bind whose assigned weights differ pull apart
when posed (the in-game body cracks). Metric: max posed separation per weld.

GARBLE/STRETCH: triangles whose edges stretch far beyond their bind length in
a pose (mis-bound verts dragging against neighbors).

usage: audit_defects.py <rigged.smd> [out_prefix]
Renders each pose with defect triangles highlighted red.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
import numpy as np  # noqa: E402

from modellab import smd  # noqa: E402
from modellab.rig import (joint_world_matrices, load_pose,  # noqa: E402
                          repose_points, skin_matrices)

RK = Path(__file__).parent / "rigkits" / "fox"
POSES = ["fox_wait1.json", "fox_run_f8.json", "fox_squat.json",
         "fox_jab_f9.json"]

rig_path = sys.argv[1]
prefix = sys.argv[2] if len(sys.argv) > 2 else str(
    Path(__file__).parent / "shots" / (Path(rig_path).stem + "_defects"))

m = smd.load(rig_path)
bind = joint_world_matrices(m)
tris = list(m.triangles)
pts = np.array([v.pos for t in tris for v in t.verts])
w = [v.weights for t in tris for v in t.verts]
n_tri = len(tris)

# drop dummy micro-tris from consideration
area0 = np.linalg.norm(np.cross(
    pts.reshape(-1, 3, 3)[:, 1] - pts.reshape(-1, 3, 3)[:, 0],
    pts.reshape(-1, 3, 3)[:, 2] - pts.reshape(-1, 3, 3)[:, 0]), axis=1)
real_tri = area0 > 1e-5

# weld bind positions
key = np.round(pts / 1e-4).astype(np.int64)
welded: dict = {}
corner_to_v = np.empty(len(pts), dtype=np.int64)
for i, k in enumerate(map(tuple, key)):
    corner_to_v[i] = welded.setdefault(k, len(welded))
groups: dict = {}
for i in range(len(pts)):
    if real_tri[i // 3]:
        groups.setdefault(corner_to_v[i], []).append(i)

bind_edge = np.linalg.norm(
    pts.reshape(-1, 3, 3) - np.roll(pts.reshape(-1, 3, 3), 1, axis=1), axis=2)

# SHELL-GAP pairs: unique verts CLOSE in bind but not welded (armor shell
# over skin) — if their separation grows when posed, the layer slides off
# the body (invisible to weld-seam and stretch metrics: the geometry is
# disconnected). Sample pairs via KD radius query.
from scipy.spatial import cKDTree  # noqa: E402

u_ids = [c[0] for c in groups.values()]
u_pts = pts[u_ids]
tree = cKDTree(u_pts)
raw_pairs = tree.query_pairs(0.5, output_type="ndarray")
shell_pairs = np.array([(u_ids[a], u_ids[b]) for a, b in raw_pairs])
bind_d = (np.linalg.norm(pts[shell_pairs[:, 0]] - pts[shell_pairs[:, 1]], axis=1)
          if len(shell_pairs) else np.zeros(0))

# same-part pairs are the FIXABLE defect (a shell sliding off the surface it
# covers); cross-part contacts (sword passing the body, skirt vs thigh) move
# apart legitimately
from modellab.rig import load_dynamics  # noqa: E402
from modellab.skeleton_parts import label_parts  # noqa: E402

fox = smd.load(str(RK / "fox_vanilla.smd"))
fox_parts = label_parts(fox, dynamic_roots=load_dynamics("PlFx"))
corner_part = [fox_parts.get(max(wl, key=lambda bw: bw[1])[0]) if wl else None
               for wl in w]
same_part = (np.array([corner_part[a] is not None
                       and corner_part[a] == corner_part[b]
                       for a, b in shell_pairs])
             if len(shell_pairs) else np.zeros(0, dtype=bool))

from PIL import Image, ImageDraw  # noqa: E402

SIZE = 460
light = np.array([0.35, 0.55, 0.75])
light /= np.linalg.norm(light)

total_seams = 0
for pose_file in POSES:
    posed = repose_points(pts, w, skin_matrices(bind, load_pose(RK / pose_file)))

    # SEAMS: welded corners separating
    seams = []
    for vid, corners in groups.items():
        if len(corners) < 2:
            continue
        P = posed[corners]
        sep = float(np.linalg.norm(P - P.mean(axis=0), axis=1).max() * 2)
        if sep > 0.35:
            seams.append((sep, corners[0]))
    seams.sort(reverse=True)

    # STRETCH: posed edge length vs bind
    p3 = posed.reshape(-1, 3, 3)
    edge = np.linalg.norm(p3 - np.roll(p3, 1, axis=1), axis=2)
    ratio = edge / np.maximum(bind_edge, 1e-6)
    tri_bad = (ratio.max(axis=1) > 2.6) & real_tri
    seam_tris = {c // 3 for _, c in seams}

    # SHELL-GAP: contact pairs whose separation grows when posed
    gap_same = gap_cross = 0
    worst_same = 0.0
    if len(shell_pairs):
        posed_d = np.linalg.norm(posed[shell_pairs[:, 0]]
                                 - posed[shell_pairs[:, 1]], axis=1)
        growth = posed_d - bind_d
        bad = growth > 0.6
        gap_same = int((bad & same_part).sum())
        gap_cross = int((bad & ~same_part).sum())
        worst_same = float(growth[same_part].max()) if same_part.any() else 0.0

    name = pose_file.replace("fox_", "").replace(".json", "")
    print(f"{name:>10}: seams>{0.35} = {len(seams):3d} "
          f"(worst {seams[0][0]:.2f} @tri {seams[0][1] // 3})" if seams else
          f"{name:>10}: seams = 0", end="")
    print(f"   stretch>2.6x = {int(tri_bad.sum()):3d}"
          f"   SAME-part gaps = {gap_same:4d} (worst {worst_same:.2f})"
          f"   cross-part = {gap_cross:4d}")
    total_seams += len(seams)

    # render with defects in red
    a = math.radians(20)
    rot = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0],
                    [-math.sin(a), 0, math.cos(a)]])
    t = p3[real_tri] @ rot.T
    flags = (tri_bad | np.isin(np.arange(n_tri), list(seam_tris)))[real_tri]
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    grey = np.clip((0.30 + 0.70 * np.clip(np.abs(n @ light), 0, 1)) * 225,
                   0, 255).astype(np.uint8)
    xy = t[:, :, [0, 1]].copy()
    xy[:, :, 1] *= -1
    lo, hi = xy.reshape(-1, 2).min(axis=0), xy.reshape(-1, 2).max(axis=0)
    span = max((hi - lo).max(), 1e-9)
    margin = 0.06 * SIZE
    p = (xy - lo) / span * (SIZE - 2 * margin) + margin
    p += (SIZE - 2 * margin - (hi - lo) / span * (SIZE - 2 * margin)) / 2
    im = Image.new("RGB", (SIZE, SIZE), (23, 30, 42))
    draw = ImageDraw.Draw(im)
    for i in np.argsort(t[:, :, 2].mean(axis=1)):
        g = int(grey[i])
        col = (235, 60, 60) if flags[i] else (g, g, g)
        draw.polygon([tuple(q) for q in p[i]], fill=col)
    ImageDraw.Draw(im).text((8, 6), name, fill=(150, 170, 200))
    im.save(f"{prefix}_{name}.png")

print(f"total seam verts across poses: {total_seams}")
