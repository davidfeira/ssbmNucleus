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
P1_LOCKED = 0x804AA162  # 0 = hovering, 1 = locked in (coin down)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


class Cursor:
    def __init__(self, dolphin, pipe):
        self.d = dolphin
        self.p = pipe

    def pos(self):
        """Validated cursor read; returns (None, None) on an out-of-range or
        NaN value (the address occasionally returns a transient garbage read)."""
        x = self.d.f32(P1_CURSOR_X)
        y = self.d.f32(P1_CURSOR_Y)
        if x is None or y is None or x != x or y != y or abs(x) > 45 or abs(y) > 40:
            return (None, None)
        return (x, y)

    def read_pos(self, tries=5):
        for _ in range(tries):
            x, y = self.pos()
            if x is not None:
                return (x, y)
            time.sleep(0.01)
        return (None, None)

    def costume(self):
        return self.d.u8(P1_COSTUME)

    def locked(self):
        return self.d.u8(P1_LOCKED) == 1

    def unlock(self):
        """If a character is locked in, press B to release it (so we can pick
        a different one). Safe no-op when already free."""
        if self.locked():
            self.p.tap("B", 0.05)
            time.sleep(0.25)
            return True
        return False

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
        """Closed-loop character selection: release any prior lock, steer to the
        cell, set the costume by reading it, then lock with A and confirm."""
        self.unlock()
        arrived = self.move_to(tx, ty)
        time.sleep(0.1)
        got_costume = self.set_costume(costume)
        if lock:
            for _ in range(3):
                self.p.tap("A", 0.05)
                time.sleep(0.2)
                if self.locked():
                    break
        return arrived and got_costume and (self.locked() if lock else True)

    def move_to(self, tx, ty, tol=1.0, timeout=8.0, kp=0.05, kd=0.18, verbose=False):
        """Closed-loop PD control: steer the cursor to (tx,ty) with stick
        deflection = kp*error - kd*velocity. The velocity (damping) term stops
        the cursor overshooting/oscillating, so it converges tight enough
        (tol ~1 unit) to land on the lockable centre of the cell -- a looser tol
        leaves it at a cell edge where A won't lock. x=1.0 right, y=1.0 down."""
        start = time.time()
        prev = None
        last_log = None
        while time.time() - start < timeout:
            x, y = self.read_pos()
            if x is None:
                self.p.center()
                time.sleep(0.02)
                continue
            ex, ey = tx - x, ty - y
            if abs(ex) < tol and abs(ey) < tol:
                self.p.center()
                if verbose:
                    print(f"  arrived ({x:+.1f},{y:+.1f}) err({ex:+.1f},{ey:+.1f})")
                return True
            vx = (x - prev[0]) if prev else 0.0
            vy = (y - prev[1]) if prev else 0.0
            sx = 0.5 + clamp(kp * ex - kd * vx, -0.5, 0.5)
            sy = 0.5 + clamp(kp * ey - kd * vy, -0.5, 0.5)
            self.p.main(sx, sy)
            prev = (x, y)
            if verbose and (last_log is None or time.time() - last_log > 0.2):
                print(f"  at ({x:+.1f},{y:+.1f}) v({vx:+.1f},{vy:+.1f}) -> ({tx:+.1f},{ty:+.1f}) stick({sx:.2f},{sy:.2f})")
                last_log = time.time()
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
