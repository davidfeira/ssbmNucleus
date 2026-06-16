"""
exercise_moveset.py -- after a match has started, drive the player through a
COMPLETE moveset (crouch, every tilt/smash, all four specials, grab, shield,
dodges, aerials, taunt) while watching process+frame health for a crash or hang.

This exists because an idle "stand at 0%" health watch misses crashes that only
fire when a SPECIFIC animation plays -- exactly the failure mode of a corrupted
fighter AJ (animation) file (e.g. CDI King crashing on crouch / a special). We
play every subaction so a corrupted animation has to reveal itself.

Reads the global frame counter (0x80479D60) and scene state (major 0x80479D30,
sub 0x80479D33) the same way observe.py does. A crash = process dead or RAM
unreadable; a hang = frame counter frozen while still in-game.

    python exercise_moveset.py [--pid N]

Exit 0 if the whole moveset ran with the game alive and advancing; 1 on
crash/hang. Leaving the in-game scene (a death/timeout) ends the run cleanly as
a pass for that point -- we only fail on an actual crash or freeze.
"""

import sys
import time

from melee_pipe import Pipe
from melee_mem import Dolphin

FRAME_COUNTER = 0x80479D60
SCENE_MAJOR = 0x80479D30
SCENE_SUBSTATE = 0x80479D33

# control stick: y=0.0 UP, y=1.0 DOWN, x=0.0 LEFT, x=1.0 RIGHT, 0.5 center.
UP, DOWN, LEFT, RIGHT, MID = 0.0, 1.0, 0.0, 1.0, 0.5


def pid_from_argv():
    if "--pid" in sys.argv:
        return int(sys.argv[sys.argv.index("--pid") + 1])
    return None


class Health:
    def __init__(self, d):
        self.d = d
        self.last_frame = None
        self.last_change = time.time()

    def check(self, label):
        """Return (ok, msg). ok=False means a real crash/hang."""
        if not self.d.alive():
            return False, f"process exited during '{label}' (CRASH)"
        frame = self.d.u32(FRAME_COUNTER)
        if frame is None:
            # RAM briefly unreadable can be a transient; re-probe once.
            time.sleep(0.2)
            frame = self.d.u32(FRAME_COUNTER)
            if frame is None:
                if not self.d.alive():
                    return False, f"process exited during '{label}' (CRASH)"
                return False, f"MEM1 unreadable during '{label}' (CRASH)"
        now = time.time()
        if frame != self.last_frame:
            self.last_frame = frame
            self.last_change = now
        elif now - self.last_change > 3.0:
            major = self.d.u8(SCENE_MAJOR)
            sub = self.d.u8(SCENE_SUBSTATE)
            return False, f"frame frozen at {frame} for >3s during '{label}' (HANG) [scene {major}/{sub}]"
        return True, f"{label}: frame={frame}"

    def in_game(self):
        return self.d.u8(SCENE_MAJOR) == 0x02 and self.d.u8(SCENE_SUBSTATE) == 0x02


def run():
    d = Dolphin(pid_from_argv())
    p = Pipe(port=1)
    h = Health(d)

    print("waiting out the GO! countdown...")
    time.sleep(3.5)

    def step(label, fn, settle=0.6):
        fn()
        time.sleep(settle)
        p.neutral()
        time.sleep(0.25)
        ok, msg = h.check(label)
        print(("  OK  " if ok else " FAIL ") + msg)
        if not ok:
            return False
        if not h.in_game():
            # a death/timeout left the match -- not a crash; stop cleanly.
            print(f"  (left in-game scene after '{label}'; ending exercise as pass)")
            raise StopIteration
        return True

    # Heavy / unique animations first (the likeliest AJ-corruption crashers for a
    # Ganon-based fighter): crouch, then all four specials.
    moves = [
        ("crouch (hold down 1.2s)", lambda: p.tilt(MID, DOWN, 1.2)),
        ("crouch->stand", lambda: (p.main(MID, DOWN), time.sleep(0.4), p.center())),
        ("neutral-B (Warlock Punch)", lambda: p.tap("B", 0.05)),
        ("side-B (Flame Choke)", lambda: (p.main(RIGHT, MID), p.tap("B", 0.05), p.center())),
        ("up-B (Dark Dive)", lambda: (p.main(MID, UP), p.tap("B", 0.05), p.center())),
        ("down-B (Wizard's Foot)", lambda: (p.main(MID, DOWN), p.tap("B", 0.05), p.center())),
        # Ground attacks
        ("jab (A)", lambda: p.tap("A", 0.05)),
        ("f-tilt", lambda: (p.main(RIGHT, MID), p.tap("A", 0.05), p.center())),
        ("u-tilt", lambda: (p.main(MID, UP), p.tap("A", 0.05), p.center())),
        ("d-tilt", lambda: (p.main(MID, DOWN), p.tap("A", 0.05), p.center())),
        # Smashes via C-stick
        ("f-smash", lambda: (p.c(RIGHT, MID), time.sleep(0.1), p.c(MID, MID))),
        ("u-smash", lambda: (p.c(MID, UP), time.sleep(0.1), p.c(MID, MID))),
        ("d-smash", lambda: (p.c(MID, DOWN), time.sleep(0.1), p.c(MID, MID))),
        # Dash + dash attack
        ("dash", lambda: (p.main(RIGHT, MID), time.sleep(0.35), p.center())),
        ("dash attack", lambda: (p.main(RIGHT, MID), time.sleep(0.2), p.tap("A", 0.05), p.center())),
        # Defensive
        ("shield (L)", lambda: (p.press("L"), time.sleep(0.5), p.release("L"))),
        ("spot dodge", lambda: (p.press("L"), p.main(MID, DOWN), time.sleep(0.3), p.release("L"), p.center())),
        ("roll back", lambda: (p.press("L"), p.main(LEFT, MID), time.sleep(0.3), p.release("L"), p.center())),
        ("grab (Z)", lambda: p.tap("Z", 0.05)),
        # Jump + aerials
        ("jump", lambda: p.tap("X", 0.05)),
        ("n-air", lambda: (p.tap("X", 0.05), time.sleep(0.18), p.tap("A", 0.05))),
        ("f-air", lambda: (p.tap("X", 0.05), time.sleep(0.18), p.c(RIGHT, MID), time.sleep(0.1), p.c(MID, MID))),
        ("u-air", lambda: (p.tap("X", 0.05), time.sleep(0.18), p.c(MID, UP), time.sleep(0.1), p.c(MID, MID))),
        ("d-air", lambda: (p.tap("X", 0.05), time.sleep(0.18), p.c(MID, DOWN), time.sleep(0.1), p.c(MID, MID))),
        ("b-air", lambda: (p.tap("X", 0.05), time.sleep(0.18), p.c(LEFT, MID), time.sleep(0.1), p.c(MID, MID))),
        # Taunt (the most "exotic" animation, often unique data)
        ("taunt (D_UP)", lambda: p.tap("D_UP", 0.05)),
    ]

    try:
        for label, fn in moves:
            if not step(label, fn):
                p.close()
                return 1
        # A second crouch pass + idle, to catch any delayed corruption.
        if not step("crouch again", lambda: p.tilt(MID, DOWN, 1.0)):
            p.close()
            return 1
    except StopIteration:
        pass

    p.neutral()
    p.close()
    ok, msg = h.check("final")
    print(("FINAL OK  " if ok else "FINAL FAIL ") + msg)
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(run())
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {e}")
        sys.exit(2)
