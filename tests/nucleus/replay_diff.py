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
    normalizing enums to their int value and floats to plain floats."""
    obj = player
    for part in dotted.split("."):
        obj = getattr(obj, part)
    if hasattr(obj, "value"):       # an enum (action, character, ...)
        return obj.value
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

    ca, cb = open_replay(a_path), open_replay(b_path)
    # Index B's frames by frame number so we compare like-for-like even if the
    # two recordings start/stop a frame apart.
    b_frames = {}
    for gs in step_all(cb):
        b_frames[gs.frame] = {p: player_vector(pl, fields)
                              for p, pl in gs.players.items()}

    compared = 0
    first_desync = None
    diffs = []
    for gs in step_all(ca):
        if gs.frame not in b_frames:
            continue
        bf = b_frames[gs.frame]
        af = {p: player_vector(pl, fields) for p, pl in gs.players.items()}
        compared += 1
        if set(af) != set(bf):
            # ports themselves differ -> not the same match
            diffs.append((gs.frame, "ports", set(af), set(bf)))
            if first_desync is None:
                first_desync = gs.frame
            continue
        for port in af:
            if af[port] != bf[port]:
                # find which fields differ for a readable report
                bad = [(fields[i], af[port][i], bf[port][i])
                       for i in range(len(fields)) if af[port][i] != bf[port][i]]
                diffs.append((gs.frame, port, bad, None))
                if first_desync is None:
                    first_desync = gs.frame

    print(f"compared {compared} shared frames of:")
    print(f"  A = {a_path}")
    print(f"  B = {b_path}")
    if first_desync is None:
        print("VERDICT: synced -- identical every shared frame.")
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
