"""
melee_sss.py -- stage-select screen state + closed-loop stage selection, read
from live RAM (melee_mem) and driven over the pipe (melee_pipe). The CSS analog
of melee_css.py, for the stage that a match is played on.

Ported from tests/nucleus/melee_sss.py (class identical; dev __main__ demo
dropped). Includes the full-m-ex fix: the hovered-stage id is at 0x804D6CAD on
standard/20XX/DAS builds and shifts to +1 (0x804D6CAE) on a full m-ex roster --
hovered_stage() reads 0x804D6CAD and falls back to +1.

  hovered stage id   byte at 0x804D6CAD   (enums.Stage value: Battlefield=0x18,
                     FD=0x19, Dreamland=0x1A, Stadium=0x12, Yoshi's=0x06,
                     Fountain=0x08)
  stage cursor X/Y   a POINTER CHAIN, only valid on the stage-select scene:
                       P0 = *(0x804D7820); P1 = *(P0+0x10); P2 = *(P1+0x28)
                       x = float at P2+0x38; y = float at P2+0x3C
"""

import time

SSS_CURSOR_PTR = 0x804D7820
SSS_HOVERED_STAGE = 0x804D6CAD

SCENE_MAJOR = 0x80479D30
SCENE_MINOR = 0x80479D33
VS_MAJOR = 0x02
SSS_MINOR = 0x01

STAGE_ID = {
    "battlefield": 0x18,
    "finaldestination": 0x19,
    "dreamland": 0x1A,
    "pokemonstadium": 0x12,
    "yoshisstory": 0x06,
    "fountainofdreams": 0x08,
}

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
    """Stage-select state + closed-loop cursor control (bang-bang tilt, matching
    libmelee's choose_stage; the cursor has a large input deadzone so small PD
    deflections stall -- full-deflection one-axis-at-a-time converges)."""

    def __init__(self, dolphin, pipe):
        self.d = dolphin
        self.p = pipe

    def _p2(self):
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
        return (self.d.u8(SCENE_MAJOR) == VS_MAJOR
                and self.d.u8(SCENE_MINOR) == SSS_MINOR)

    def wait_for_stage_select(self, timeout=8.0):
        start = time.time()
        while time.time() - start < timeout:
            if self.on_stage_select():
                return True
            time.sleep(0.05)
        return False

    def ensure_stage_select(self):
        """Make sure we're on the stage-select scene, advancing from a locked
        CSS with START if needed (over THIS persistent pipe, verifying the scene
        actually changed)."""
        if self.on_stage_select():
            return True
        for _ in range(4):
            self.p.tap("START", 0.06)
            if self.wait_for_stage_select(timeout=2.5):
                return True
        return self.on_stage_select()

    def hovered_stage(self):
        """The enums.Stage id the cursor is over. 0x804D6CAD on standard builds;
        on a full m-ex roster the struct shifts one byte so the real id is at +1
        (0x804D6CAE) -- read the base and fall back to +1."""
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
        first, holding the tilt and re-polling fast. +x right, +y down."""
        start = time.time()
        while time.time() - start < timeout:
            x, y = self.read_pos()
            if x is None:
                self.p.center()
                time.sleep(0.02)
                continue
            ex, ey = tx - x, ty - y
            if abs(ex) <= wiggle and abs(ey) <= wiggle:
                self.p.center()
                return True
            if abs(ey) > wiggle and abs(ey) >= abs(ex):
                self.p.main(0.5, 1.0 if ey > 0 else 0.0)   # +y down = pipe y 1.0
            else:
                self.p.main(1.0 if ex > 0 else 0.0, 0.5)
            time.sleep(0.016)
        self.p.center()
        return False

    def select(self, name, press=True, hold=None):
        """Steer to a stage by name and press A to pick it (which, with a locked
        CSS, starts the match). `hold` (e.g. 'X') is held through the load to
        trigger a DAS alternate stage."""
        key = norm(name)
        if key not in STAGE_TARGET:
            raise KeyError(f"no stage target for '{name}' "
                           f"(known: {', '.join(sorted(STAGE_TARGET))})")
        if not self.ensure_stage_select():
            return False
        tx, ty = STAGE_TARGET[key]
        reached = self.move_to(tx, ty)
        if not press:
            return reached
        return self._confirm(tx, ty, hold=hold)

    def _confirm(self, tx, ty, hold=None):
        """Press A and verify the match actually starts (the scene leaves
        stage-select), re-pressing if a tap didn't take. If `hold` is a button,
        keep it held through the confirm + load (the DAS trigger). Don't use
        A/B/R to hold (A selects, B backs out, R flips pages)."""
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
                self.move_to(tx, ty, timeout=2.0)
            return False
        finally:
            if hold:
                self.p.release(hold)

    def switch_page(self, n, settle=0.6):
        """Advance n m-ex stage-select pages by pressing R. Custom stages live
        on a page after the main Melee page."""
        for _ in range(max(0, n)):
            self.p.tap("R", 0.08)
            time.sleep(settle)

    def select_at(self, x, y, page=0, press=True, hold=None):
        """Select a stage by its explicit SSS icon coordinate (and page) -- from
        the build manifest. Advances to the stage's page with R first, verifying
        the page switch took (an R tap right after the START->SSS transition can
        be dropped, silently leaving us on page 0 where (x,y) is a vanilla
        stage), then steers and confirms. `hold` triggers a DAS alternate."""
        if not self.ensure_stage_select():
            return False
        self.switch_page(page)
        reached = self.move_to(x, y)
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

    def find_stage_pos(self, target_id, pages=1, verbose=False):
        """Closed-loop, layout-INDEPENDENT search: SETTLE the cursor at a grid of
        points and read the hovered-stage id at each, until the target stage is
        under the cursor; return that (x,y) -- or None. Depends on
        hovered_stage() being populated."""
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
            if page + 1 < pages:
                self.switch_page(1)
        return None

    def select_by_id(self, target_id, press=True, hold=None, pages=1):
        """Select a stage by its hovered-stage id via closed-loop settle-read
        search -- robust to ANY SSS layout, as long as hovered_stage() is
        populated. `hold` triggers a DAS alternate."""
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
