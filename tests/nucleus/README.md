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

```sh
# Build a modded ISO by type (no game):
node tests/nucleus/build-modded-iso.js                      # Fox + first vault costume
node tests/nucleus/build-modded-iso.js --fighter Falco --mod <costume-id>
node tests/nucleus/build-modded-iso.js --type character --mod wolf
node tests/nucleus/build-modded-iso.js --type stage --mod "Hyrule Castle 64"

# Build AND run a crash-test match (costume mods), ending in PASS/FAIL:
node tests/nucleus/run-modded-match.js --build
node tests/nucleus/run-modded-match.js --build --type character --mod sonic

# Re-use the last build:
node tests/nucleus/run-modded-match.js

# Robust path: select the character by memory feedback instead of timing:
node tests/nucleus/run-modded-match.js --closed-loop
```

`--closed-loop` does the discrete steps (menu nav, port-2 CPU, start) via the
per-frame pipe and the **analog character positioning + costume by reading the
cursor/costume in RAM** (`cl_select.py`) — deterministic, immune to cursor
acceleration/frame timing. The default path uses `pipe.js startmatch` (timing).
Non-costume mods auto-fall back to a **boot-health** check (boot + reach CSS +
watch process/frame health), which crash-tests any mod type without selecting it.

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

## Memory-feedback CSS control (`melee_mem.py`, `melee_pipe.py`, `melee_css.py`)

Reimplements libmelee's approach directly on Slippi, decoupled from libmelee and
Slippi's stream format: locate MEM1 in the Dolphin process (`GALE01` signature),
read cursor/costume/lock, and drive a **persistent** controller pipe with PD
closed-loop control. `calibrate.py` builds `grid.json` (char → cursor cell);
`char_select.py` selects by name. Positioning is deterministic; see the memory
note for the lock/2nd-player integration detail.

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
