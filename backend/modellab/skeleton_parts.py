"""Semantic body-part labels for Melee skeletons.

Every fighter skeleton follows the same HSD convention (confirmed by the
community bone-name tables: zankyou's Mario/Captain dumps): jobj 0-3 are
util bones (TopN/TransN/XRotN/YRotN — never weighted), jobj 4 is the hip,
and from the hip hang two downward leg chains plus an upward spine that
branches into two lateral arm chains and an upward neck/head.

label_parts() segments a rig-kit skeleton into coarse parts:

    util | torso | head | l_arm | r_arm | l_leg | r_leg | cloth

Weight transfer uses these to forbid cross-part sampling (a head vert must
never ride an arm bone): the shard/melting artifacts on cross-character
rigs were triangles whose corners sampled skeleton-distant parts.
"""
from __future__ import annotations

import numpy as np

UTIL_COUNT = 4          # TopN, TransN, XRotN, YRotN
HIP = 4

# which target parts a vert labeled X may sample (torso is the universal
# bridge: necks, collars and waists genuinely blend into it)
ALLOWED = {
    "head":  {"head", "torso"},
    "l_arm": {"l_arm", "torso"},
    "r_arm": {"r_arm", "torso"},
    "l_leg": {"l_leg", "torso"},
    "r_leg": {"r_leg", "torso"},
    "torso": {"torso"},
    # cloth may also ride the LEGS: a floor-length cape rigidly spine-bound
    # stands like a pillar through every crouch (vanilla capes fold via
    # physics chains we can't carry) — thigh weights make it fold with the
    # body the way skirts do
    "cloth": {"torso", "l_leg", "r_leg"},
    "util":  None,           # unconstrained
    None:    None,
}


def _subtree(kids, root):
    out = []
    stack = [root]
    while stack:
        b = stack.pop()
        out.append(b)
        stack.extend(kids.get(b, []))
    return out


def label_parts(rigkit, world=None, dynamic_roots=None):
    """{jobj id -> part label} for a rig-kit SMD skeleton."""
    from modellab.rig import joint_world_positions

    if world is None:
        world = joint_world_positions(rigkit)
    joints = {b.id: b for b in rigkit.bones if b.name.startswith("JOBJ_")}
    kids: dict = {}
    for b in joints.values():
        kids.setdefault(b.parent, []).append(b.id)

    labels = {j: None for j in joints}
    for j in range(UTIL_COUNT):
        if j in labels:
            labels[j] = "util"

    if HIP not in joints:                     # not a standard fighter skeleton
        return {j: None for j in joints}
    labels[HIP] = "torso"
    hip_y = world[HIP][1]
    height = max(w[1] for w in world.values()) - min(w[1] for w in world.values())

    # classify each subtree hanging off the hip
    spine_root = None
    for child in kids.get(HIP, []):
        sub = _subtree(kids, child)
        ys = np.array([world[j][1] for j in sub])
        xs = np.array([world[j][0] for j in sub])
        if len(sub) >= 3 and ys.min() < hip_y - 0.25 * height \
                and ys.max() < hip_y + 0.15 * height:
            # reaches the floor AND never rises above the hip: a leg. (The
            # spine subtree also dips low on caped/hunched chars — but its
            # top is at head height.)
            side = "l_leg" if xs.mean() > 0 else "r_leg"
            for j in sub:
                labels[j] = side
        elif ys.max() > hip_y + 0.05 * height and len(sub) > 4:
            spine_root = child                # the torso/arms/head subtree
        else:
            for j in sub:                     # holster, waist nulls, throw
                labels[j] = "torso"

    if spine_root is not None:
        # walk the spine: single chain upward; at each node, lateral branches
        # are arms, the final upward continuation is neck/head
        cur = spine_root
        spine = []
        while True:
            spine.append(cur)
            labels[cur] = "torso"
            ch = kids.get(cur, [])
            if not ch:
                break
            up, lateral = [], []
            for c in ch:
                sub = _subtree(kids, c)
                xs = np.array([world[j][0] for j in sub])
                ys = np.array([world[j][1] for j in sub])
                # an ARM subtree lives entirely on one side; a chest subtree
                # containing both arms has lateral spread but is balanced
                one_sided = (np.sign(xs[np.abs(xs) > 0.02 * height]) ==
                             np.sign(xs.mean())).mean() > 0.8 \
                    if np.abs(xs).max() > 0.02 * height else False
                if len(sub) >= 3 and abs(xs.mean()) > 0.05 * height and one_sided:
                    lateral.append((c, xs.mean()))
                else:
                    up.append((c, ys.max(), len(sub)))
            for c, mx in lateral:
                side = "l_arm" if mx > 0 else "r_arm"
                for j in _subtree(kids, c):
                    labels[j] = side
            if not up:
                break
            # continue along the tallest remaining branch; if we've already
            # spawned arms, that branch is the neck -> everything above = head
            up.sort(key=lambda t: -t[1])
            nxt = up[0][0]
            if lateral:
                for j in _subtree(kids, nxt):
                    labels[j] = "head"
                for c, _, _ in up[1:]:
                    for j in _subtree(kids, c):
                        labels[j] = "torso"
                break
            for c, _, _ in up[1:]:
                for j in _subtree(kids, c):
                    labels[j] = "torso"
            cur = nxt

    # dynamics chains (capes/tails) override whatever part they fell into
    for root in (dynamic_roots or []):
        if root in joints:
            for j in _subtree(kids, root):
                labels[j] = "cloth"

    # leftovers inherit their parent's label
    for j in sorted(joints):
        if labels.get(j) is None:
            p = joints[j].parent
            while p in labels and labels[p] is None:
                p = joints[p].parent
            labels[j] = labels.get(p) or "torso"
    return labels
