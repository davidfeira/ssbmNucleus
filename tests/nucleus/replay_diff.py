"""
replay_diff.py -- frame-by-frame diff of two Slippi .slp replays to LOCATE a
desync. In netplay each client records its OWN .slp; when the two simulations
part (a desync), their recordings diverge from that frame on. Diffing them
frame-aligned finds the exact desync frame + which player/field first differed --
the standard way to debug a Slippi desync, here offline (no live connection, no
account): you just need the two .slp files the two clients saved.

This complements the live RAM diff (desync_check.py): that one localizes a
desync between two RUNNING clients; this one does it after the fact from the
replays. Both read state the same way conceptually -- per-frame, per-player.

    python replay_diff.py <a.slp> <b.slp> [--max-report N] [--fields f1,f2,...]

Exit 0 if the replays stay identical for every shared frame (synced), 1 if they
diverge (desync found, with the frame + fields printed).

Parsing is libmelee's offline reader (Console(is_dolphin=False)); a synced pair
is bit-identical frame-for-frame, so the comparison is exact.
"""

import sys

import melee


# Per-player fields that must match frame-for-frame in a synced match. These are
# the simulation outputs each client computes; any difference is a real desync
# (Melee is deterministic, so there's no legitimate per-client variation).
FIELDS = [
    "position.x", "position.y",
    "action", "action_frame",
    "percent", "shield_strength", "stock",
    "facing", "hitstun_frames_left", "jumps_left", "on_ground",
    "speed_air_x_self", "speed_y_self", "speed_x_attack",
    "speed_y_attack", "speed_ground_x_self",
]


def get_field(player, dotted):
    """Resolve a possibly-dotted field (e.g. 'position.x') off a PlayerState,
    normalizing enums to their int value and numpy scalars to native Python
    (so comparison and the printed report are clean)."""
    obj = player
    for part in dotted.split("."):
        obj = getattr(obj, part)
    if hasattr(obj, "value") and not hasattr(obj, "item"):  # an enum
        return obj.value
    if hasattr(obj, "item"):         # a numpy scalar -> python int/float
        return obj.item()
    return obj


def player_vector(player, fields):
    return tuple(get_field(player, f) for f in fields)


def step_all(console):
    """Generator of (frame, {port: PlayerState}) for an offline .slp."""
    while True:
        gs = console.step()
        if gs is None:
            return
        yield gs


def open_replay(path):
    c = melee.Console(path=path, is_dolphin=False, allow_old_version=True)
    c.connect()
    return c


def parse_replay(path, fields):
    """Read a .slp into {frame: {port: state_vector}} plus its identity
    (stage, {port: character}) from the first frame -- the identity lets us
    confirm two replays are the SAME match before calling a diff a 'desync'."""
    c = open_replay(path)
    frames = {}
    identity = None
    for gs in step_all(c):
        frames[gs.frame] = {int(p): player_vector(pl, fields)
                            for p, pl in gs.players.items()}
        if identity is None and gs.players:
            stage = gs.stage.value if hasattr(gs.stage, "value") else gs.stage
            chars = tuple(sorted((int(p), int(pl.character.value))
                                 for p, pl in gs.players.items()))
            identity = (int(stage), chars)
    return frames, identity


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        print(__doc__)
        return 2
    a_path, b_path = args[0], args[1]
    fields = FIELDS
    if "--fields" in sys.argv:
        fields = sys.argv[sys.argv.index("--fields") + 1].split(",")
    max_report = 10
    if "--max-report" in sys.argv:
        max_report = int(sys.argv[sys.argv.index("--max-report") + 1])

    a_frames, a_id = parse_replay(a_path, fields)
    b_frames, b_id = parse_replay(b_path, fields)

    print(f"  A = {a_path}")
    print(f"  B = {b_path}")
    # Same-match guard: a real desync pair is the SAME match (same stage +
    # characters) recorded by two clients. If those differ, this isn't a desync
    # -- it's two unrelated games, and a frame diff is meaningless.
    same_match = a_id == b_id
    if not same_match:
        print(f"  NOTE: these look like DIFFERENT matches "
              f"(A stage/chars={a_id}, B={b_id}); a desync pair is the same "
              f"match recorded by two clients. Reporting the diff anyway.")

    compared = 0
    first_desync = None
    diffs = []
    for frame in sorted(set(a_frames) & set(b_frames)):
        af, bf = a_frames[frame], b_frames[frame]
        compared += 1
        if set(af) != set(bf):
            diffs.append((frame, "ports", set(af), set(bf)))
            if first_desync is None:
                first_desync = frame
            continue
        for port in af:
            if af[port] != bf[port]:
                bad = [(fields[i], af[port][i], bf[port][i])
                       for i in range(len(fields)) if af[port][i] != bf[port][i]]
                diffs.append((frame, port, bad, None))
                if first_desync is None:
                    first_desync = frame

    print(f"compared {compared} shared frames")
    if first_desync is None:
        verdict = "synced -- identical every shared frame."
        print(f"VERDICT: {verdict}"
              if same_match else f"VERDICT: {verdict} (but different matches)")
        return 0
    print(f"VERDICT: DESYNC at frame {first_desync}")
    for frame, port, bad, _extra in diffs[:max_report]:
        if port == "ports":
            print(f"  frame {frame}: port set A={bad} B={_extra}")
        else:
            fieldstr = ", ".join(f"{name}: A={av} B={bv}" for name, av, bv in bad)
            print(f"  frame {frame} port {port}: {fieldstr}")
    if len(diffs) > max_report:
        print(f"  ... and {len(diffs) - max_report} more differing frame/port rows")
    return 1


if __name__ == "__main__":
    sys.exit(main())
