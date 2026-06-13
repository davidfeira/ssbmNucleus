"""Geometric body-part segmentation for a SKELETON-LESS humanoid mesh (the AI
/ GLB path). Melee sources hand us per-vertex parts via their skin weights;
a raw generated mesh has none, so the rigger could only globally scale it onto
Fox — long human limbs then overshoot Fox's short bones (janky stretched arms
/legs). This labels each vertex head|torso|l_arm|r_arm|l_leg|r_leg from
geometry alone (assumes a roughly upright A/T pose, Y up), so the per-part
deform can land each limb on Fox's bone anchors.

Approach: the mesh is upright with arms out. Per horizontal slab the torso is
the central mass; arms are lateral outliers (a gap separates them); legs are
the two clusters below the crotch; the head is the top-central cap.
"""
from __future__ import annotations

import numpy as np

PARTS = ["head", "torso", "l_arm", "r_arm", "l_leg", "r_leg"]


def _vertical_axis(verts):
    """Index of the up axis (longest extent) + lateral/depth indices."""
    span = verts.max(0) - verts.min(0)
    up = int(np.argmax(span))
    rest = [i for i in range(3) if i != up]
    # lateral = the wider of the remaining two (arms spread it)
    lat, dep = (rest if span[rest[0]] >= span[rest[1]] else rest[::-1])
    return up, lat, dep


def label_vertices(verts, log=print):
    """verts (N,3) -> (labels list[str|None] length N, info dict).

    Heuristic thresholds are derived from the mesh's own proportions, not
    hard-coded fractions, so it adapts to different builds."""
    verts = np.asarray(verts, float)
    up, lat, dep = _vertical_axis(verts)
    y = verts[:, up]
    x = verts[:, lat]
    y0, y1 = y.min(), y.max()
    H = max(y1 - y0, 1e-6)
    cx = float(np.median(x))
    yn = (y - y0) / H                       # 0 feet .. 1 head
    lateral = np.abs(x - cx)

    # --- arm threshold: in the upper body (yn 0.55..0.95) the lateral spread is
    # bimodal (torso near 0, arms near max). Put the cut at 45% of the reach.
    upper = (yn > 0.5) & (yn < 0.95)
    reach = np.percentile(lateral[upper], 98) if upper.any() else lateral.max()
    arm_cut = 0.42 * reach
    is_arm = (lateral > arm_cut) & (yn > 0.45)

    # --- hip line: scan the non-arm body for where one central column splits
    # into two leg clusters (a gap appears at center x). Default ~0.47.
    hip = y0 + 0.47 * H
    body = ~is_arm
    for f in np.linspace(0.40, 0.55, 16):
        yl = y0 + f * H
        sl = body & (y >= yl - 0.03 * H) & (y <= yl + 0.03 * H)
        if sl.sum() < 20:
            continue
        near = np.abs(x[sl] - cx) < 0.12 * reach   # density at the centerline
        if near.mean() < 0.18:                      # centerline hollow => crotch
            hip = yl
            break

    shoulder = y0 + 0.82 * H
    labels: list = [None] * len(verts)
    for i in range(len(verts)):
        if is_arm[i]:
            labels[i] = "l_arm" if x[i] < cx else "r_arm"
        elif y[i] < hip:
            labels[i] = "l_leg" if x[i] < cx else "r_leg"
        elif y[i] > shoulder and lateral[i] < arm_cut:
            labels[i] = "head"
        else:
            labels[i] = "torso"

    from collections import Counter
    counts = dict(Counter(labels))
    log(f"geometric parts: {counts} (up={up} lat={lat} hip@{(hip-y0)/H:.2f} "
        f"shoulder@0.82 arm_cut={arm_cut:.3f})")
    info = {"up": up, "lat": lat, "dep": dep, "cx": cx,
            "y0": y0, "y1": y1, "hip": hip, "shoulder": shoulder,
            "arm_cut": arm_cut, "reach": reach}
    return labels, info


def proxy_skeleton(verts, labels, info, log=print):
    """Synthesize a minimal Fox-shaped skeleton (a 2-joint chain per part) from
    the segmented geometry, so segment_deform can land each part on Fox's bone
    anchors. Returns (src_parts, src_parents, src_pos) keyed by synthetic joint
    id, plus src_geom {part: (N,3)} — the same inputs a melee source provides.

    Joint ids: 0 hip, 1 neck (torso chain); 2 head_base, 3 head_top;
    4/5 L shoulder/wrist; 6/7 R shoulder/wrist; 8/9 L hip/ankle; 10/11 R."""
    verts = np.asarray(verts, float)
    up, lat, dep = info["up"], info["lat"], info["dep"]
    lab = np.asarray(labels, dtype=object)

    def grp(part):
        return verts[lab == part]

    def axis_ends(pts, root_toward):
        """Two endpoints of a point cloud along its principal axis; the end
        nearer root_toward (a 3D point) is returned first (the chain root)."""
        c = pts.mean(0)
        u, s, vt = np.linalg.svd(pts - c, full_matrices=False)
        ax = vt[0]
        t = (pts - c) @ ax
        e0 = c + ax * np.percentile(t, 4)
        e1 = c + ax * np.percentile(t, 96)
        if np.linalg.norm(e0 - root_toward) <= np.linalg.norm(e1 - root_toward):
            return e0, e1
        return e1, e0

    def vend(pts, top):
        """Vertical endpoints (centroid of the top/bottom 12% slabs)."""
        yv = pts[:, up]
        lo = pts[yv <= np.percentile(yv, 12)].mean(0)
        hi = pts[yv >= np.percentile(yv, 88)].mean(0)
        return (hi, lo) if top else (lo, hi)

    torso = grp("torso")
    body_c = torso.mean(0) if len(torso) else verts.mean(0)
    pos: dict = {}
    parts: dict = {}
    parents: dict = {}

    # torso chain: hip (bottom) -> neck (top)
    neck, hip = vend(torso, top=True) if len(torso) >= 8 else (body_c, body_c)
    pos[0], parts[0], parents[0] = hip, "torso", -1
    pos[1], parts[1], parents[1] = neck, "torso", 0

    # head chain: base (near neck) -> top
    head = grp("head")
    if len(head) >= 8:
        hb, ht = vend(head, top=False)      # base=low, top=high
        pos[2], parts[2], parents[2] = hb, "head", 1
        pos[3], parts[3], parents[3] = ht, "head", 2

    # arms: shoulder (near body) -> wrist (far)
    for part, j0, j1 in (("l_arm", 4, 5), ("r_arm", 6, 7)):
        a = grp(part)
        if len(a) >= 8:
            sh, wr = axis_ends(a, neck)
            pos[j0], parts[j0], parents[j0] = sh, part, 1
            pos[j1], parts[j1], parents[j1] = wr, part, j0

    # legs: hip (top) -> ankle (bottom)
    for part, j0, j1 in (("l_leg", 8, 9), ("r_leg", 10, 11)):
        lg = grp(part)
        if len(lg) >= 8:
            hp, ak = vend(lg, top=True)
            pos[j0], parts[j0], parents[j0] = hp, part, 0
            pos[j1], parts[j1], parents[j1] = ak, part, j0

    src_geom = {p: grp(p) for p in PARTS if (lab == p).sum() >= 8}
    log(f"proxy skeleton: {len(pos)} joints, parts={sorted(set(parts.values()))}")
    return parts, parents, pos, src_geom

