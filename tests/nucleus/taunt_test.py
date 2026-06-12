"""taunt_test.py -- tap taunt (D_UP) in a running match and watch for a crash.

Samples the global frame counter and p1 action state before/during/after the
taunt. A frozen frame counter = game hang/crash; reports the last action
state + anim frame seen so the failing subaction can be identified.

Usage: melee_venv/Scripts/python taunt_test.py [--port 1]
"""

import argparse
import time

from melee_mem import Dolphin
from melee_pipe import Pipe

FRAME_COUNTER = 0x80479D60
STATIC_PLAYER = 0x80453080
STATIC_STRIDE = 0xE90


def ft_data(d, port):
    gobj = d.u32(STATIC_PLAYER + STATIC_STRIDE * port + 0xB0)
    ft = d.u32(gobj + 0x2C) if gobj else None
    if not ft:
        raise RuntimeError(f"no ftData for port {port + 1}")
    return ft


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=1)
    ap.add_argument("--no-tap", action="store_true",
                    help="just watch (idle-hang repro), don't press taunt")
    ap.add_argument("--watch", type=float, default=8.0, help="seconds to watch")
    args = ap.parse_args()
    port = args.port - 1

    d = Dolphin()
    ft = ft_data(d, port)
    print(f"p{args.port} ftData=0x{ft:08X} action_state=0x{d.u32(ft + 0x10):X}")

    pipe = Pipe(port=args.port)
    pipe.neutral()
    time.sleep(0.3)

    if not args.no_tap:
        print("tapping D_UP (taunt)...")
        pipe.tap("D_UP", hold=0.1)
    else:
        print(f"idle watch for {args.watch}s (no input)...")

    last_states = []  # (gf, action_state, anim_frame)
    t_end = time.time() + args.watch
    frozen_since = None
    last_gf = None
    while time.time() < t_end:
        gf = d.u32(FRAME_COUNTER)
        st = d.u32(ft + 0x10)
        af = d.f32(ft + 0x894)
        if gf != last_gf:
            last_gf = gf
            frozen_since = None
            if not last_states or last_states[-1][1] != st:
                last_states.append((gf, st, af))
                print(f"  frame {gf}: action_state=0x{st:X} anim={af if af is None else round(af, 1)}")
        else:
            if frozen_since is None:
                frozen_since = time.time()
            elif time.time() - frozen_since > 2.0:
                print(f"\nCRASH/HANG: frame counter frozen at {gf} for >2s")
                print(f"last action states: {[(g, hex(s)) for g, s, _ in last_states[-6:]]}")
                pipe.close()
                return 1
        time.sleep(0.005)
    pipe.neutral()
    pipe.close()
    print(f"\nOK: game still running after taunt ({len(last_states)} state changes)")
    print(f"states seen: {[(g, hex(s)) for g, s, _ in last_states]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
