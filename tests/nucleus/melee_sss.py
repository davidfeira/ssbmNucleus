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

# Scene id: major byte at 0x80479D30 (0x02 = VS mode), minor at 0x80479D33
# (within VS: 0x00 = character select, 0x01 = stage select, 0x02 = in-game).
# We gate steering on being ON the stage-select scene, because the cursor
# pointer chain still resolves on other screens but reads junk (often 0,0) --
# without this guard, move_to would happily push inputs on the wrong screen.
SCENE_MAJOR = 0x80479D30
SCENE_MINOR = 0x80479D33
VS_MAJOR = 0x02
SSS_MINOR = 0x01

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

    def on_stage_select(self):
        """True only when the game is actually on the stage-select scene -- a
        guard before steering, since the cursor read is meaningless elsewhere."""
        return (self.d.u8(SCENE_MAJOR) == VS_MAJOR
                and self.d.u8(SCENE_MINOR) == SSS_MINOR)

    def wait_for_stage_select(self, timeout=8.0):
        """Wait until the stage-select scene is up (e.g. after a START whose
        transition is still in flight). Returns False on timeout."""
        start = time.time()
        while time.time() - start < timeout:
            if self.on_stage_select():
                return True
            time.sleep(0.05)
        return False

    def ensure_stage_select(self):
        """Make sure we're on the stage-select scene, advancing from a locked
        CSS with START if needed. Pressing START over THIS persistent pipe (vs
        a separate per-frame `gotostage`) avoids the connection-handoff that was
        dropping the START -- and we verify the scene actually changed, retrying
        a couple times. Returns True once stage select is up."""
        if self.on_stage_select():
            return True
        for _ in range(4):
            self.p.tap("START", 0.06)
            if self.wait_for_stage_select(timeout=2.5):
                return True
        return self.on_stage_select()

    def hovered_stage(self):
        """The enums.Stage id the cursor is currently over (ground truth, used to
        confirm a selection). Returns the raw byte; compare to STAGE_ID.

        Address note: on standard / 20XX / DAS builds the id is the byte at
        SSS_HOVERED_STAGE (0x804D6CAD). On the full m-ex roster build the SSS
        struct is shifted one byte -- 0x804D6CAD reads 0x00 and the real id is at
        +1 (0x804D6CAE). Read 0x804D6CAD and fall back to +1, which works on both
        (verified: 0x804D6CAE gave 0x18=Battlefield, 0x06=Yoshi's on the m-ex
        grid, matching the on-screen names)."""
        v = self.d.u8(SSS_HOVERED_STAGE)
        if not v:
            v = self.d.u8(SSS_HOVERED_STAGE + 1)
        return v

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

    def select(self, name, press=True, hold=None):
        """Steer to a stage by name and press A to pick it (which, with a
        locked CSS, starts the match on that stage). Navigation is purely by
        the cursor coordinate -- like libmelee, since the hovered-stage byte
        stays NO_STAGE until a stage is actually confirmed, so it can't gate a
        pre-press check. When press=True, confirms the match actually started
        (the scene leaves stage-select), re-pressing A if a tap didn't take, and
        returns whether it started; with press=False, returns whether the cursor
        reached the stage's cell. `hold` (e.g. 'X') is held through the load to
        trigger a DAS alternate stage."""
        key = norm(name)
        if key not in STAGE_TARGET:
            raise KeyError(f"no stage target for '{name}' "
                           f"(known: {', '.join(sorted(STAGE_TARGET))})")
        # Don't steer unless we're truly on the stage-select scene (advancing
        # from a locked CSS with START if needed) -- otherwise the cursor read
        # is junk and we'd push inputs on the wrong screen.
        if not self.ensure_stage_select():
            return False
        tx, ty = STAGE_TARGET[key]
        reached = self.move_to(tx, ty)
        if not press:
            return reached
        return self._confirm(tx, ty, hold=hold)

    def _confirm(self, tx, ty, hold=None):
        """Press A and verify the match actually starts (the scene leaves
        stage-select). A single tap occasionally doesn't take, so re-center on
        the cell and re-press a few times. If `hold` is a button (e.g. 'X'),
        keep it held through the confirm + load -- that's the DAS (Dynamic
        Alternate Stages) trigger: holding the button as the stage loads makes
        the game load that stage's alternate. Returns True once the match
        starts. (Don't use A/B/R here -- A selects, B backs out, R flips m-ex
        pages; X/Y/Z/L are safe to hold.)"""
        if hold:
            self.p.press(hold)
        try:
            for _ in range(6):
                self.p.center()   # only re-centers the stick; keeps `hold` down
                time.sleep(0.12)
                self.p.tap("A", 0.08)
                time.sleep(0.4)
                if not self.on_stage_select():
                    if hold:
                        time.sleep(0.7)  # keep holding so DAS reads it at load
                    return True
                # cursor may have drifted off the tile -- nudge back on before retry
                self.move_to(tx, ty, timeout=2.0)
            return False
        finally:
            if hold:
                self.p.release(hold)

    def switch_page(self, n, settle=0.6):
        """Advance n m-ex stage-select pages by pressing R (the page-switch
        input). Custom stages live on a page after the main Melee page, so we
        R to that page before steering to the stage. No-op when n <= 0."""
        for _ in range(max(0, n)):
            self.p.tap("R", 0.08)
            time.sleep(settle)

    def select_at(self, x, y, page=0, press=True, hold=None):
        """Select a stage by its explicit SSS icon coordinate (and page) -- from
        the build manifest (the app's own SSS layout) rather than the hardcoded
        vanilla targets, which only match a stock layout. Use this for any stage
        whose real coordinate we know (custom stages, and vanilla stages on a
        build whose layout differs from libmelee's). Advances to the stage's
        page with R first, then steers to (x,y) and confirms. `hold` (e.g. 'X')
        triggers a DAS alternate."""
        if not self.ensure_stage_select():
            return False
        self.switch_page(page)
        reached = self.move_to(x, y)
        # A page-switch R tap can be dropped (esp. the first one right after the
        # START->SSS transition), silently leaving us on page 0 -- where (x,y) is
        # a VANILLA stage, not the custom one we meant. VERIFY: if we asked for a
        # non-zero (custom) page but the hovered tile is a known vanilla stage,
        # the switch didn't take -- R again and re-steer until the tile is custom
        # (an id NOT in STAGE_ID). This is what made the modpack land on
        # Battlefield instead of the custom stage before the guard existed.
        if page > 0:
            vanilla_ids = set(STAGE_ID.values())
            for _ in range(4):
                hv = self.hovered_stage()
                if hv and hv not in vanilla_ids:
                    break  # on a custom tile -> page switch worked
                self.switch_page(1)
                reached = self.move_to(x, y)
        if not press:
            return reached
        return self._confirm(x, y, hold=hold)

    # --- layout-INDEPENDENT selection by hovered-stage id --------------------
    #
    # Fixed-coordinate selection (select/select_at) assumes a known SSS layout.
    # It breaks on builds whose layout differs -- notably a FULL m-ex stage
    # roster (all stages on one screen), where Battlefield etc. are nowhere near
    # the tournament-layout coords. The robust fix mirrors character selection:
    # steer by the ground-truth hovered id (0x804D6CAD) rather than coordinates,
    # sweeping the cursor until it's actually over the target stage.

    def find_stage_pos(self, target_id, pages=1, verbose=False):
        """Closed-loop, layout-INDEPENDENT search: SETTLE the cursor at a grid of
        points and read the hovered-stage id at each, until the target stage is
        under the cursor; return that (x,y) -- or None. Settle-read is required
        because the hovered byte only updates when the cursor RESTS on a tile, not
        mid-glide. `pages` sweeps that many m-ex pages (R between them).

        NOTE: depends on hovered_stage() (0x804D6CAD) being populated. That holds
        on standard / 20XX / DAS builds, but NOT on this modpack's full-m-ex SSS
        where the byte reads 0x00 (the live highlight is index-driven from a
        relocated field) -- that build needs the real hovered field discovered
        first (a discover.py-style snapshot diff between two known stages)."""
        if not self.ensure_stage_select():
            return None
        xs = [-26, -21, -16, -11, -6, -1, 4, 9, 14, 19, 24]
        ys = [-16, -11, -6, -1, 4, 9, 14]
        for page in range(max(1, pages)):
            for yi, y in enumerate(ys):
                row = xs if yi % 2 == 0 else list(reversed(xs))
                for x in row:
                    self.move_to(x, y, wiggle=1.2, timeout=1.5)
                    time.sleep(0.06)
                    if self.hovered_stage() == target_id:
                        return self.read_pos()
                if verbose:
                    print(f"  page {page} row y={y:+.0f}: scanned")
            if page + 1 < pages:
                self.switch_page(1)
        return None

    def select_by_id(self, target_id, press=True, hold=None, pages=1):
        """Select a stage by its hovered-stage id via closed-loop settle-read
        search -- robust to ANY SSS layout (tournament, full m-ex roster, custom
        pages), as long as hovered_stage() is populated on the build (see
        find_stage_pos). target_id is an enums.Stage byte (STAGE_ID['battlefield']
        =0x18, or a custom stage's id). `hold` (e.g. 'X') triggers a DAS alternate.
        Returns whether the match started (press=True) / cursor is on it (False)."""
        pos = self.find_stage_pos(target_id, pages=pages)
        if pos is None or pos[0] is None:
            return False
        for _ in range(3):
            self.move_to(pos[0], pos[1], wiggle=0.9)
            if self.hovered_stage() == target_id:
                break
            time.sleep(0.1)
        if not press:
            return self.hovered_stage() == target_id
        return self._confirm(pos[0], pos[1], hold=hold)


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
