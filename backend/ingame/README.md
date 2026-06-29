# `backend/ingame/` — in-game test engine (SOLO, no CPU, no cursor)

**This is THE way to boot a built ISO and get a fighter into a match for any
in-game test** — crash probes, move/side-B tests, screenshots, RAM diagnostics.

It loads the match by **writing the player block directly to game RAM** and
relaxing the "Ready to Fight" gate, so you play **alone (1 player, no CPU)** and
never touch the character- or stage-select cursor.

## Why this, and NOT the CPU/cursor method

There is an older path (`tests/dolphin/` + `tests/nucleus/cl_match.py` +
`pipe.js cpustep`) that steers the CSS cursor and **adds a CPU** to satisfy
Melee's 2-player start gate. **Do not use it for gameplay/crash testing.** It is:

- **Slower** — a multi-second cursor sweep to click a character + add a CPU,
  with timing-calibrated stick holds that drift per build.
- **A confound** — the CPU walks over, attacks you, and moves the camera, which
  corrupts move/crash repros (e.g. a CPU hit interrupts the move you're testing).
- **Fragile** — custom fighters aren't in the cursor grid, so it needs CSS-icon
  coordinates from the build manifest.

The cursor path is only correct when the **CSS/SSS UI itself** is under test
(icon placement, grid layout, menu mods).

> Recurring failure: agents discover `tests/dolphin/` first, wire up
> `cl_match` + `cpustep`, fight a CPU, and waste a build cycle. If you're here
> to test *gameplay*, use the solo flow below.

## The solo flow (copy `backend/fsm_crash_probe.py`)

`fsm_crash_probe.py` is the worked template; `zs_mismatch_probe.py` is another.
Run from `backend/` with plain `python` (uses the backend's deps).

```python
from ingame.boot import DolphinBoot          # isolated throwaway Slippi User dir
from ingame.melee_mem import Dolphin          # RPM read/write of MEM1
from ingame.melee_pipe import Pipe            # controller input over the named pipe
from ingame.melee_css import Cursor
from ingame.melee_sss import StageCursor, INTERNAL_STAGE_ID
from ingame.observe import wait_in_game, wait_game_frames
from ingame import nav, match_setup

boot = DolphinBoot(str(iso), None, str(runs_root), log=print)
boot.prepare(); boot.launch()
boot.wait_for_pipe(timeout=45)
d = Dolphin(boot.pid)
while not d.locate(): ...                     # find MEM1 base

match_setup.patch_one_player(d)               # CSS gate cmpwi r4,2 -> r4,1 (allow solo)
p = boot.open_pipe()                          # controller pipe, retried across Dolphin's re-arm windows
nav.nav_to_css(d, p)                          # Slippi online menu -> offline VS CSS
nav.wait_css_ready(d, Cursor(d, p))
match_setup.force_time_infinite(d)            # Time / no limit, so a solo match sustains

CKIND = 0x1A                                  # external CSS id; FIRST added m-ex fighter = 0x1A
match_setup.write_solo_player(d, CKIND, 0)    # write port-0 = fighter, ports 1-5 = NA
match_setup.warp_to_stage_select(d)           # memory warp CSS -> SSS (no cursor)
sc = StageCursor(d, p); sc.wait_for_stage_select()
match_setup.write_solo_player(d, CKIND, 0)    # re-assert after the warp
sc.force_select(INTERNAL_STAGE_ID["battlefield"])   # direct stage-id write, no SSS cursor

wait_in_game(d); wait_game_frames(d, 200)     # past READY/GO!
# ... now drive inputs + sample state ...
boot.cleanup()
```

### `ckind` (which fighter)
`ckind` is the **external CSS fighter id**. Vanilla = 0x00–0x19. **m-ex added
fighters start at 0x1A** (the first added fighter = 0x1A, the next 0x1B, …). For
a build whose only custom fighter is Metal Mario, `ckind = 0x1A`. Confirm with
`mexcli list-fighters <project.mexproj>` (the `externalId`).

### Driving inputs (`Pipe`)
Open the pipe with **`boot.open_pipe()`** (not `Pipe(...)` directly): Slippi
Dolphin tears its controller pipe down and re-arms it on controller refreshes
(game boot / stage load), so a single-shot open can land in that gap and die with
`CreateFile(...slippibot1) failed: 2`. `open_pipe()` retries across the gap and
bails fast if Dolphin actually exited.

`press/release/tap(btn,hold)`, `main(x,y)` / `c(x,y)` control & C sticks
(0.0–1.0, 0.5 center; y=0 up, x=1 right), `tilt(x,y,hold)`, `center()`,
`neutral()`, and `frame([...])` for one raw atomic frame.

A **side-special (side-B)** = stick to a side + B, atomically:
```python
p.frame(["SET MAIN 1.000 0.500", "PRESS B", "FLUSH"]); time.sleep(0.1)
p.frame(["RELEASE B", "SET MAIN 0.500 0.500", "FLUSH"])
```

### Detecting a crash / hang
- **Hang / assert halt** (e.g. m-ex `assertion "0" failed ... item not
  initialized`): the global frame counter `0x80479D60` stops advancing while the
  game stays in-scene. Sample it; >2–3 s frozen = hung.
- **Hard crash**: `d.alive()` false or MEM1 unreadable.
- Per-player ftData: `gobj = u32(0x80453080 + 0xE90*port + 0xB0); ft = u32(gobj+0x2C)`;
  action state at `ft+0x10`, anim frame f32 at `ft+0x894`.

## The no-CPU memory pokes (`match_setup.py`)
- `patch_one_player(d)` — RPM-patches the CSS start gate at `0x80263064`
  (`cmpwi r4,2` → `cmpwi r4,1`) so a 1-player roster is "Ready to Fight".
- `force_time_infinite(d)` — GameRules `0x8045BF10`: mode=Time, time=0.
- `write_solo_player(d, ckind, color)` — writes the StartMeleeData /
  VsModeData player blocks: port 0 = fighter, ports 1–5 = NA.
- `warp_to_stage_select(d)` — pokes the scene loop (`0x80479D35`/`0x80479D64`)
  to jump CSS→SSS without the cursor or START gate.

All addresses are NTSC 1.02. See `match_setup.py` for the authoritative list.
