# Nucleus mod crash-test harness

End-to-end harness that builds a modded Melee ISO with the SSBM Nucleus backend,
boots it, gets into a match with the mod active, and **reads live game RAM to
report whether the mod loaded or crashed**. It pairs the Nucleus backend API
with the Dolphin pipe-input harness in [`../dolphin`](../dolphin) and a
memory-feedback observer.

## Pipeline

```
build-modded-iso.js              run-modded-match.js (orchestrator)
─────────────────────            ──────────────────────────────────
spawn dev backend (_run_backend) (optionally --build first)
create + open project            launch modded ISO  ── ../dolphin/control.js
install mod (by --type):         wait for input pipe + menu
  costume  /api/mex/import        drive menus  ── ../dolphin/pipe.js startmatch
  character /custom-characters       CSS → CPU → char+costume → stage → START
  stage    /custom-stages         observe match ── observe.py (RAM)
export ISO ─────────────────►    VERDICT: PASS / FAIL (crash report)
last-build.json (manifest)
```

## Usage

Mod types and how each is triggered in-game (all end in PASS/FAIL):

| `--type` | what | in-game trigger |
|---|---|---|
| `costume` | fighter skin | select fighter + color |
| `character` | custom m-ex fighter | select its CSS grid slot (app's placement) |
| `stage` | custom m-ex stage | R to its SSS page + select |
| `das` | stage skins (Dynamic Alternate Stages) | hold X/Y/Z on stage-select; many per ISO |
| `effect` | blaster/laser/sword model | select fighter, perform the move (neutral-B) |

```sh
# Build a modded ISO by type (no game):
node tests/nucleus/build-modded-iso.js                      # Fox + first vault costume
node tests/nucleus/build-modded-iso.js --type character --mod wolf
node tests/nucleus/build-modded-iso.js --type stage --mod "Hyrule Castle 64"
node tests/nucleus/build-modded-iso.js --type das --variants-per-stage 3   # up to 18 skins/ISO
node tests/nucleus/build-modded-iso.js --type effect --fighter Fox --extra gun

# Build AND run a crash-test match, ending in PASS/FAIL:
node tests/nucleus/run-modded-match.js --build
node tests/nucleus/run-modded-match.js --build --type character --mod sonic
node tests/nucleus/run-modded-match.js --build --type das          # tests every skin in one boot
node tests/nucleus/run-modded-match.js --build --type effect --fighter Falco --extra gun

# Re-use the last build:
node tests/nucleus/run-modded-match.js

# Robust path: select the character AND stage by memory feedback (default BF):
node tests/nucleus/run-modded-match.js --closed-loop
node tests/nucleus/run-modded-match.js --closed-loop --stage dreamland
```

`--closed-loop` does the discrete steps (menu nav, port-2 CPU) via the per-frame
pipe, then a single memory-feedback process (`cl_match.py`) that **selects the
character + costume AND the stage by reading the cursors in RAM** and starts the
match — deterministic, immune to cursor acceleration/frame timing. `--stage
<name>` chooses the stage (battlefield, fd, dreamland, yoshis, stadium,
fountain; default battlefield). The default (non-closed-loop) path uses
`pipe.js startmatch` (timing).

**Custom m-ex characters and stages are selected in-match too**, using the app's
own layout as ground truth (not empirical calibration): the build places the new
icon into a real roster slot / stage page (the app's "add to grid / new page"
step) and records its coordinate in the manifest (`cssIcon` / `sssIcon`).
`run-modded-match.js` then does the closed-loop match — for a custom fighter,
steer to its CSS icon `(x, y-3.5)`; for a custom stage, press **R** to its SSS
page then steer to its coordinate. (DAS mods still fall back to **boot-health**:
boot + reach CSS + watch process/frame health, which crash-tests any mod without
selecting it.)

The build writes the ISO to `output/<project>.iso` and a manifest to
`tests/artifacts/nucleus/last-build.json`, e.g.:

```json
{ "iso": ".../output/harness-test.iso", "modType": "costume",
  "fighter": "Fox", "colorIndex": 4, "costumeId": "angy-plfxag" }
```

`colorIndex` is the modded costume's slot = the number of `X` presses on the CSS
to reach it. For `character`/`stage` mods the manifest carries
`characterName`/`stageName` instead.

## Observability / crash detection (`observe.py`)

Reads live emulated RAM (no libmelee, no Slippi stream) for an objective verdict:

| signal | verdict |
|---|---|
| Dolphin process exits | **crashed** |
| emulated RAM / `GALE01` gone | **crashed** |
| frame counter (`0x80479D60`) frozen >2s | **hung** |
| left in-game <4s after entering | **ended** (soft crash) |
| reached in-game and ran | **healthy** |

Scene (Melee 1.02): major `0x80479D30 == 0x02` (VS), in-match `0x80479D33 == 0x02`.
On failure it writes a JSON report + screenshot to
`tests/artifacts/nucleus/crash-reports/`. `run-modded-match.js` runs it for 25s
right after the match starts.

## Memory-feedback CSS + stage control

Reimplements libmelee's approach directly on Slippi, decoupled from libmelee and
Slippi's stream format: locate MEM1 in the Dolphin process (`GALE01` signature),
read the cursors from RAM, and drive a **persistent** controller pipe with
closed-loop control.

- `melee_mem.py` / `melee_pipe.py` — RAM reads + persistent input pipe.
- `melee_css.py` (`Cursor`) — character select: PD cursor control, costume by
  reading the costume index, hovered-character confirmation (`0x803F0E0A`, a
  grid-independent CSS index). `calibrate.py` builds `grid.json`;
  `char_select.py` / `cl_select.py` select by name.
- `melee_sss.py` (`StageCursor`) — stage select: cursor X/Y from a pointer chain
  (`*(*(*(*(0x804D7820)+0x10)+0x28)+0x38/+0x3C)`), bang-bang steering to
  libmelee's per-stage coordinates (the cursor has a deadzone that eats small
  PD pushes), then A to start. `cl_stage.py` selects by name.
- `cl_match.py` — the integrated path the orchestrator uses: lock the character
  and pick the stage on **one** persistent pipe. The "locked" byte (`0x804AA162`)
  is noise, so it presses A exactly once (a loop's random count toggles the coin
  off) and verifies the lock *functionally* — START only reaches stage select
  when the character is actually locked. Stage coordinates are libmelee's vanilla
  layout (Battlefield + Dreamland screenshot-confirmed); a stage mod that
  replaces a vanilla slot is selected by picking that slot.

## Desync debugging (`desync_check.py`, `replay_diff.py`)

Two complementary desync localizers, both decoupled from libmelee's live stream:

- **`replay_diff.py <a.slp> <b.slp>`** — offline, no account needed. Each netplay
  client records its own `.slp`; on a desync the two recordings part. This diffs
  them frame-aligned (libmelee's offline reader) and prints the first frame +
  player + field that differs. Validated: a replay vs itself → `synced`; two
  different replays → desync localized. Exit 0 synced / 1 desync.
- **`desync_check.py <pid1> <pid2> [--watch N]`** — live, two running instances.
  Diffs MEM1 + named canaries (frame, RNG seed `0x804D5F90`, scene). Validated
  live: two coexisting Dolphins (`driver.js --pipe-index 2` → `\\.\pipe\slippibot2`,
  `pipe.js --port 2`) both attach + drive, and the RNG canary flags divergence.
  The remaining piece for a synced live pair is the netplay connection (needs a
  2nd Slippi account / design call); the read+diff foundation is done.

## How it drives the app

- **Backend, not UI** — calls the Flask REST API the desktop app's frontend uses,
  exercising the real build engine (MexCLI, CSP gen, ISO export) without Electron.
- **Isolated** — the dev backend roots data in the repo (`projects/`, `storage/`,
  `output/`); the installed app uses `%LOCALAPPDATA%\SSBM Nucleus`. Picks a free
  port (prefers 5000).
- **`_run_backend.py`** presents a fake-TTY stdin (flask-socketio's dev-server
  guard) and drops `tests/nucleus` from `sys.path` (so harness modules don't
  shadow stdlib), then runs `backend/mex_api.py` unchanged.

## Requirements

- Nucleus dev setup complete (`GET /api/mex/setup/status`); MexCLI built at
  `utility/MexManager/MexCLI/bin/Release/net6.0/mexcli.exe`.
- A vanilla 1.02 ISO for `project/create` (default: the dolphin tests' working ISO).
- Node 18+ (global `fetch`); the repo `venv` for the backend; `melee_venv`
  (`numpy`, `pywin32`) for the Python observer/control — both gitignored.
```
