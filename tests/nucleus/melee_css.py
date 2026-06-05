"""
melee_css.py -- character-select state + closed-loop cursor control, read from
live RAM (melee_mem) and driven over the pipe (melee_pipe). No timing guesswork:
we read the cursor's actual position every step and steer toward the target, so
positioning is deterministic regardless of cursor acceleration or grid layout.

Addresses (Melee 1.02, found empirically by discover.py -- see that file):
  port-1 cursor X  0x804A85FC  (float, ~ -30 left .. +30 right)
  port-1 cursor Y  0x804A860C  (float, ~ -27 up .. +25 down; +Y is downward)
  port-1 costume   0x80480823  (byte, increments on X)
"""

import time

P1_CURSOR_X = 0x804A85FC
P1_CURSOR_Y = 0x804A860C
P1_COSTUME = 0x80480823


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


class Cursor:
    def __init__(self, dolphin, pipe):
        self.d = dolphin
        self.p = pipe

    def pos(self):
        return self.d.f32(P1_CURSOR_X), self.d.f32(P1_CURSOR_Y)

    def costume(self):
        return self.d.u8(P1_COSTUME)

    def set_costume(self, target, max_presses=16):
        """Cycle the costume with X, reading the costume index each time, until
        it equals target. No press-counting -- closed-loop on the real value."""
        for _ in range(max_presses):
            cur = self.costume()
            if cur == target:
                return True
            self.p.tap("X", 0.05)
            time.sleep(0.22)
        return self.costume() == target

    def select(self, tx, ty, costume=0, lock=True):
        """Closed-loop character selection: steer to the cell, set the costume by
        reading it, then lock with A."""
        arrived = self.move_to(tx, ty)
        time.sleep(0.1)
        got_costume = self.set_costume(costume)
        if lock:
            self.p.tap("A", 0.05)
        return arrived and got_costume

    def move_to(self, tx, ty, tol=0.9, timeout=5.0, gain=0.06, verbose=False):
        """Closed-loop: steer the cursor to (tx,ty) by setting stick deflection
        proportional to the position error each step, easing off as it arrives.
        Stick x=1.0 increases X (right); stick y=1.0 increases Y (down)."""
        start = time.time()
        last = None
        while time.time() - start < timeout:
            x, y = self.pos()
            if x is None or y is None:
                return False
            ex, ey = tx - x, ty - y
            if abs(ex) < tol and abs(ey) < tol:
                self.p.center()
                if verbose:
                    print(f"  arrived ({x:+.1f},{y:+.1f}) err({ex:+.1f},{ey:+.1f})")
                return True
            sx = 0.5 + clamp(ex * gain, -0.5, 0.5)
            sy = 0.5 + clamp(ey * gain, -0.5, 0.5)
            self.p.main(sx, sy)
            if verbose and (last is None or time.time() - last > 0.2):
                print(f"  at ({x:+.1f},{y:+.1f}) -> target ({tx:+.1f},{ty:+.1f}) stick({sx:.2f},{sy:.2f})")
                last = time.time()
            time.sleep(0.03)
        self.p.center()
        return False


if __name__ == "__main__":
    import sys
    from melee_mem import Dolphin
    from melee_pipe import Pipe

    d = Dolphin()
    p = Pipe()
    print(f"attached pid {d.pid}; cursor now at {Cursor(d, p).pos()}")
    cur = Cursor(d, p)
    # Demo: drive to a few targets, reading back the achieved position.
    targets = [(0.0, 0.0), (22.0, -18.0), (-25.0, 15.0), (0.0, 0.0)]
    if len(sys.argv) >= 3:
        targets = [(float(sys.argv[1]), float(sys.argv[2]))]
    for tx, ty in targets:
        ok = cur.move_to(tx, ty, verbose=True)
        x, y = cur.pos()
        print(f"target ({tx:+.1f},{ty:+.1f}) -> {'OK' if ok else 'TIMEOUT'} at ({x:+.1f},{y:+.1f})")
        time.sleep(0.3)
