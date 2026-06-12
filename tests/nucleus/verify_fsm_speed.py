"""verify_fsm_speed.py -- functional FSM check: measure animation speed live.

With a match running and port 1 on the ground, taps A (jab) until the jab
action state (0x2C Attack11) appears, then samples the player's animation
frame float (ftData+0x894) against the global frame counter. GodMewtwo's FSM
gives jab1 (subaction 46) x3.0 speed from frame 0 and x1.0 from frame 8 --
so the anim frame should advance ~3.0/game-frame early, then ~1.0/frame.
Without FSM it's ~1.0 throughout.

Usage: melee_venv/Scripts/python verify_fsm_speed.py [--port 1]
"""

import argparse
import time

from melee_mem import Dolphin
from melee_pipe import Pipe

FRAME_COUNTER = 0x80479D60
STATIC_PLAYER = 0x80453080
STATIC_STRIDE = 0xE90
AS_ATTACK11 = 0x2C


def ft_data(d, port):
    gobj = d.u32(STATIC_PLAYER + STATIC_STRIDE * port + 0xB0)
    if not gobj or not (0x80000000 <= gobj < 0x81800000):
        raise RuntimeError(f"no fighter GObj for port {port + 1} (0x{gobj or 0:08X})")
    ft = d.u32(gobj + 0x2C)
    if not ft or not (0x80000000 <= ft < 0x81800000):
        raise RuntimeError(f"no ftData for port {port + 1}")
    return ft


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=1, help="1-based controller port")
    args = ap.parse_args()
    port = args.port - 1

    d = Dolphin()
    ft = ft_data(d, port)
    print(f"p{args.port} ftData=0x{ft:08X} action_state=0x{d.u32(ft + 0x10):X}")

    pipe = Pipe(port=args.port)
    pipe.neutral()
    time.sleep(0.3)

    # tap A until the jab action state shows up (a few tries in case the
    # character is landing/turning), then record the whole jab
    per_frame = {}
    for attempt in range(5):
        pipe.tap("A")
        t_end = time.time() + 1.2
        seen = False
        while time.time() < t_end:
            st = d.u32(ft + 0x10)
            if st == AS_ATTACK11:
                seen = True
                gf = d.u32(FRAME_COUNTER)
                af = d.f32(ft + 0x894)
                if gf is not None and af is not None and gf not in per_frame:
                    per_frame[gf] = af
            elif seen:
                break
            time.sleep(0.001)
        if seen:
            break
        print(f"  (attempt {attempt + 1}: no jab seen, retrying)")
        time.sleep(0.4)
    pipe.neutral()
    pipe.close()

    if not per_frame:
        print("FAIL: never saw the jab action state (0x2C)")
        return 1

    frames = sorted(per_frame)
    print(f"jab captured over {len(frames)} game frames "
          f"(anim {per_frame[frames[0]]:.1f} -> {per_frame[frames[-1]]:.1f})")
    print("game-frame: anim frame (rate/frame)")
    rates = []  # (anim_frame, rate)
    for a, b in zip(frames, frames[1:]):
        gap = b - a
        rate = (per_frame[b] - per_frame[a]) / gap
        rates.append((per_frame[a], rate))
        print(f"  {a}: {per_frame[a]:7.2f} ({rate:+.2f}/frame over {gap})")

    early = [r for af, r in rates if af < 7]
    late = [r for af, r in rates if af >= 9]
    if early:
        print(f"\nearly jab (anim<7): avg rate {sum(early) / len(early):.2f} (FSM expects ~3.0)")
    if late:
        print(f"late jab (anim>=9): avg rate {sum(late) / len(late):.2f} (FSM expects ~1.0)")
    ok = early and sum(early) / len(early) > 2.0
    print("FSM ACTIVE: jab startup is sped up x3" if ok
          else "FSM NOT OBSERVED: jab advanced at normal speed")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
