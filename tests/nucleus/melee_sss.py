"""
melee_sss.py -- stage-select screen state + closed-loop stage selection, read
from live RAM (melee_mem) and driven over the pipe (melee_pipe). The CSS analog
of melee_css.py, for the stage that a match is played on.

Addresses / encoding decoded from libmelee's "Extract Menu Info" gecko code
(GALE01r2.ini, the SendMenuFrame block) -- the same source that gave us the
hovered-character read. Validated against console.py's menu-info parsing:

  hovered stage id   byte at 0x804D6CAD   (== gamestate.stage, an enums.Stage
                     value: Battlefield=0x18, FD=0x19, Dreamland=0x1A,
                     Stadium=0x12, Yoshi's=0x06, Fountain=0x08)
  stage cursor X/Y   a POINTER CHAIN, only valid on the stage-select scene:
                       P0 = *(0x804D7820)
                       P1 = *(P0 + 0x10)
                       P2 = *(P1 + 0x28)
                       x  = float at P2 + 0x38
                       y  = float at P2 + 0x3C

Stage-select cursor axes: +x = right, +y = DOWN (verified empirically:
stick-down raises cursor.y, stick-up lowers it). The cursor has a large input
deadzone -- small (PD-style) deflections don't move it at all, it just stalls --
so, like libmelee, we steer with FULL-deflection bang-bang (one axis at a time,
re-polling fast) and stop inside a wiggle box. Full tilt always beats the
deadzone; fast re-reads catch the overshoot.

The target cursor coordinates per stage come straight from libmelee's
menuhelper.choose_stage (the legal-stage tournament layout).
"""

import time

SSS_CURSOR_PTR = 0x804D7820
SSS_HOVERED_STAGE = 0x804D6CAD

# enums.Stage value (the byte at SSS_HOVERED_STAGE) -- used to CONFIRM the cursor
# is over the intended stage, the same way hovered() confirms a character.
STAGE_ID = {
    "battlefield": 0x18,
    "finaldestination": 0x19,
    "dreamland": 0x1A,
    "pokemonstadium": 0x12,
    "yoshisstory": 0x06,
    "fountainofdreams": 0x08,
}

# Target stage-cursor coordinates (from libmelee menuhelper.choose_stage). +x
# right, +y up. RANDOM is the random-stage tile, handy as a known anchor.
STAGE_TARGET = {
    "battlefield": (1.0, -9.0),
    "finaldestination": (6.7, -9.0),
    "dreamland": (12.5, -9.0),
    "pokemonstadium": (15.0, 3.5),
    "yoshisstory": (3.5, 15.5),
    "fountainofdreams": (10.0, 15.5),
    "random": (-13.5, 3.5),
}

ALIASES = {
    "bf": "battlefield",
    "fd": "finaldestination", "dreamland64": "dreamland", "dl": "dreamland",
    "ps": "pokemonstadium", "stadium": "pokemonstadium", "ps2": "pokemonstadium",
    "ys": "yoshisstory", "yoshis": "yoshisstory", "yoshistory": "yoshisstory",
    "fod": "fountainofdreams", "fountain": "fountainofdreams",
    "rng": "random", "randomstage": "random",
}


def norm(name):
    key = "".join(ch for ch in str(name).lower() if ch.isalnum())
    return ALIASES.get(key, key)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


class StageCursor:
    """Stage-select state + closed-loop cursor control.

    Mirrors melee_css.Cursor but for the stage grid: it reads the cursor's live
    position (a pointer chain) and the hovered stage id, and steers with simple
    bang-bang tilt control (matching libmelee's choose_stage), which converges
    reliably on this screen without PD tuning.
    """

    def __init__(self, dolphin, pipe):
        self.d = dolphin
        self.p = pipe

    def _p2(self):
        """Resolve the pointer chain to P2 (the struct holding cursor x/y), or
        None if it doesn't resolve (e.g. we're not on the stage-select scene)."""
        a = self.d.deref(SSS_CURSOR_PTR, 0x10)   # P0 + 0x10
        if a is None:
            return None
        b = self.d.deref(a, 0x28)                # P1 + 0x28
        if b is None:
            return None
        p2 = self.d.u32(b)                       # P2
        if p2 is None or not (0x80000000 <= p2 < 0x81800000):
            return None
        return p2

    def pos(self):
        """Validated stage-cursor read; (None, None) if the chain doesn't
        resolve or the value is garbage/NaN/out of the screen's range."""
        p2 = self._p2()
        if p2 is None:
            return (None, None)
        x = self.d.f32(p2 + 0x38)
        y = self.d.f32(p2 + 0x3C)
        if x is None or y is None or x != x or y != y or abs(x) > 40 or abs(y) > 40:
            return (None, None)
        return (x, y)

    def read_pos(self, tries=6):
        for _ in range(tries):
            x, y = self.pos()
            if x is not None:
                return (x, y)
            time.sleep(0.01)
        return (None, None)

    def hovered_stage(self):
        """The enums.Stage id the cursor is currently over (ground truth, used
        to confirm a selection). Returns the raw byte; compare to STAGE_ID."""
        return self.d.u8(SSS_HOVERED_STAGE)

    def hovered_name(self):
        v = self.hovered_stage()
        for name, sid in STAGE_ID.items():
            if sid == v:
                return name
        return None

    def move_to(self, tx, ty, wiggle=1.5, timeout=8.0, verbose=False):
        """Full-deflection bang-bang to (tx,ty), correcting the larger error
        first, holding the tilt and re-polling fast so overshoot is caught
        within a frame or two. +x right, +y down: so ex>0 -> tilt right (x=1.0),
        ey>0 -> tilt down (y=1.0). Stops (and re-centers) inside the wiggle box.
        Full deflection is required -- the cursor's deadzone eats small pushes."""
        start = time.time()
        last_log = None
        while time.time() - start < timeout:
            x, y = self.read_pos()
            if x is None:
                self.p.center()
                time.sleep(0.02)
                continue
            ex, ey = tx - x, ty - y
            if abs(ex) <= wiggle and abs(ey) <= wiggle:
                self.p.center()
                if verbose:
                    print(f"  arrived ({x:+.1f},{y:+.1f}) err({ex:+.1f},{ey:+.1f})")
                return True
            # One axis at a time, larger error first (mirrors libmelee).
            if abs(ey) > wiggle and abs(ey) >= abs(ex):
                self.p.main(0.5, 1.0 if ey > 0 else 0.0)   # +y down = pipe y 1.0
            else:
                self.p.main(1.0 if ex > 0 else 0.0, 0.5)
            if verbose and (last_log is None or time.time() - last_log > 0.15):
                print(f"  at ({x:+.1f},{y:+.1f}) -> ({tx:+.1f},{ty:+.1f}) "
                      f"err({ex:+.1f},{ey:+.1f})")
                last_log = time.time()
            time.sleep(0.016)
        self.p.center()
        return False

    def select(self, name, press=True, settle=0.35):
        """Steer to a stage by name and press A to pick it (which, with a
        locked CSS, starts the match on that stage). Navigation is purely by
        the cursor coordinate -- like libmelee, since the hovered-stage byte
        stays NO_STAGE until a stage is actually confirmed, so it can't gate a
        pre-press check. Returns whether the cursor reached the stage's cell;
        whether the right stage actually loaded is confirmed downstream by the
        observer (the match starts healthy) or a screenshot."""
        key = norm(name)
        if key not in STAGE_TARGET:
            raise KeyError(f"no stage target for '{name}' "
                           f"(known: {', '.join(sorted(STAGE_TARGET))})")
        tx, ty = STAGE_TARGET[key]
        reached = self.move_to(tx, ty)
        if press:
            self.p.tap("A", 0.06)
            time.sleep(settle)
        return reached


if __name__ == "__main__":
    import sys
    from melee_mem import Dolphin
    from melee_pipe import Pipe

    d = Dolphin()
    p = Pipe()
    sc = StageCursor(d, p)
    # Sacrificial neutral + settle for the per-frame -> persistent handoff.
    p.neutral()
    time.sleep(0.3)
    if len(sys.argv) >= 2 and sys.argv[1] not in ("read", "watch"):
        name = sys.argv[1]
        press = "--no-press" not in sys.argv
        ok = sc.select(name, press=press)
        x, y = sc.pos()
        print(f"stage {name}: ok={ok} pos=({x},{y}) "
              f"hovered={sc.hovered_name()} (0x{(sc.hovered_stage() or 0):02X})")
        p.close()
    else:
        # Read-only: print cursor + hovered stage a few times (address check).
        for _ in range(20):
            x, y = sc.pos()
            hv = sc.hovered_stage()
            xs = f"{x:+.2f}" if x is not None else "None"
            ys = f"{y:+.2f}" if y is not None else "None"
            print(f"cursor=({xs},{ys}) hovered={sc.hovered_name()} "
                  f"(0x{(hv or 0):02X})")
            time.sleep(0.25)
