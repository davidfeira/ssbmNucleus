# Nucleus mod crash-test harness

End-to-end harness that builds a modded Melee ISO with the SSBM Nucleus backend,
boots it, gets into a match with the mod active, and **reads live game RAM to
report whether the mod loaded or crashed**. It pairs the Nucleus backend API
with the Dolphin pipe-input harness in [`../dolphin`](../dolphin) and a
memory-feedback observer.

> ## ⚡ PREFERRED: in-app engine (`backend/ingame/`) for getting into a match
>
> For "boot the ISO and get a specific character into a match" — probes, FSM
> checks, screenshot/diagnostic work — **do NOT drive the CSS cursor or add a
> CPU**. Use the in-app ingame engine's memory-loading path, which is faster and
> far more reliable:
>
> 1. `DolphinBoot` (isolated throwaway User dir) → `nav.nav_to_css`
> 2. `match_setup.patch_one_player` + `force_time_infinite` → **solo match,
>    no CPU**
> 3. `match_setup.write_solo_player(d, ckind, color)` +
>    `warp_to_stage_select(d)` — writes the player block directly
>    (ckind = CSS external id; first added m-ex fighter = 0x1A) and warps
>    CSS→SSS with **no cursor movement at all**
> 4. `StageCursor.force_select(INTERNAL_STAGE_ID["finaldestination"])` —
>    direct stage-id write, no SSS cursor
>
> Template: [`backend/fsm_crash_probe.py`](../../backend/fsm_crash_probe.py) or
> `backend/zs_mismatch_probe.py` (run from `backend/` with plain `python`).
> A solo match also removes the CPU as a confound (nothing attacks you or
> moves the camera).
>
> The cursor-driving path below (`run-modded-match.js --closed-loop`) is only
> needed when the CSS/SSS **UI itself** is under test (icon placement, grid
> layout, menu mods).

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
| `menu` | CSS background / icon grid / doors | reach the CSS (boot-health + screenshot) |
| `modpack` | one representative of every mod type | smart two-match plan in `backend/ingame/runner.py` |
| `stress` | many vault costumes for CSP/compression testing | boot-health / online-CSS memory checks |

```sh
# Build a modded ISO by type (no game):
node tests/nucleus/build-modded-iso.js                      # Fox + first vault costume
node tests/nucleus/build-modded-iso.js --type character --mod wolf
node tests/nucleus/build-modded-iso.js --type stage --mod "Hyrule Castle 64"
node tests/nucleus/build-modded-iso.js --type das --variants-per-stage 3   # up to 18 skins/ISO
node tests/nucleus/build-modded-iso.js --type effect --fighter Fox --extra gun
node tests/nucleus/build-modded-iso.js --type menu --menu icon_grid   # or background / doors
node tests/nucleus/build-modded-iso.js --type modpack
node tests/nucleus/build-modded-iso.js --type stress --count 250 --compression 0.55
node tests/nucleus/build-modded-iso.js --texture-pack --type stress --count 250

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
node tests/nucleus/run-modded-match.js --iso output/harness-test.iso --char Fox --color 4 --no-cpu
```

Common `build-modded-iso.js` flags:

- `--backend <url>` uses an already-running backend; otherwise the harness
  spawns `tests/nucleus/_run_backend.py`.
- `--keep-backend` leaves a spawned backend alive after the build.
- `--keep-project` reuses an existing project directory instead of deleting it.
- `--export-only` opens an existing project and re-exports without reinstalling
  content; useful with `--compression`.
- `--compression <ratio>` overrides the recommended CSP compression ratio.
- `--color-smash` exports with color-smash enabled.
- `--texture-pack` exports placeholder CSPs plus a texture mapping JSON for the
  texture-pack harvest/offline naming flow.
- `--slippi <path>` sets the Dolphin/Slippi path used by texture-pack export.

Common `run-modded-match.js` flags:

- `--build` runs `build-modded-iso.js` first and forwards build flags.
- `--iso <path>` boots a specific ISO.
- `--char <fighter>` / `--color <slot>` selects a vanilla fighter and costume.
- `--closed-loop` uses `cl_match.py` for RAM-feedback character and stage
  selection.
- `--stage <name>` chooses the target stage for the closed-loop path.
- `--no-cpu` requests a one-player timing path for the legacy non-closed-loop
  runner.

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

## Texture-pack harvest (`run-texture-harvest.js`)

Automates the texture-pack export flow for CSP replacement packs:

1. `build-modded-iso.js --texture-pack` exports an ISO with encoded 16x16
   placeholder CSPs and `output/<buildId>_texture_mapping.json`.
2. `control.js` boots that ISO in the fixed texture-pack run directory with
   `--texture-dump`.
3. The backend watcher decodes dumped placeholders and maps each global CSP
   index to Dolphin's real dumped filename.
4. `tex_scroll.py` sweeps the CSS so every placeholder is rendered.
5. The final table is merged into
   `tests/artifacts/nucleus/texture_filename_table.json`.

Usage:

```sh
node tests/nucleus/run-texture-harvest.js --type stress --count 250
node tests/nucleus/run-texture-harvest.js --offline --compute --type stress --count 250
node tests/nucleus/run-texture-harvest.js --sheik
```

`--offline` skips Dolphin and names the pack from a harvested table. Adding
`--compute` generates the index-to-filename table by computation instead of a
prior harvest. `--sheik` performs the short, guarded online-CSS Sheik pass used
when that cell cannot be rendered through the offline CSS.

## Online CSS memory check

The online CSS loads more CSP memory than the offline VS CSS. For compression
and CSP stress work, prefer the backend batch probe when pinning limits:

```sh
cd backend
python fps_batch.py --mode online ../output/count-comp-1000.iso
python fps_batch.py --mode both ../output/count-comp-800.iso ../output/count-comp-1000.iso
```

Use `--mode offline` for the console/local-play number and `--mode online` for
the Dolphin/Slippi number. The online path enters the Slippi unranked CSS
briefly, watches RAM/process health, and holds B out before matchmaking can pair
anyone.

The older shell wrapper is still available for a single ISO:

```sh
tests/nucleus/online_test_iso.sh output/harness-test.iso
```

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
