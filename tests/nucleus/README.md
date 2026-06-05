# Nucleus mod crash-test harness

End-to-end harness that builds a modded Melee ISO with the SSBM Nucleus backend,
then boots it and starts a match with the mod selected — to check whether a mod
loads in-game or crashes. It pairs the Nucleus backend API with the Dolphin
pipe-input harness in [`../dolphin`](../dolphin).

## Pipeline

```
build-modded-iso.js          run-modded-match.js (orchestrator)
─────────────────────        ──────────────────────────────────
spawn dev backend            (optionally build first)
  └ _run_backend.py          launch modded ISO  ── ../dolphin/control.js
create project               wait for input pipe + menu
open project                 drive menus        ── ../dolphin/pipe.js startmatch
import vault costume           CSS → CPU → char+costume → stage → START
export ISO  ───────────────► screenshot the running match
last-build.json (manifest)
```

## Usage

```sh
# Build a modded ISO (Fox + first slippi-safe vault costume), no game:
node tests/nucleus/build-modded-iso.js
node tests/nucleus/build-modded-iso.js --fighter Falco --costume <vault-id>

# Build AND run a match with the mod selected, then screenshot it:
node tests/nucleus/run-modded-match.js --build

# Re-use the last build and just run the match:
node tests/nucleus/run-modded-match.js
```

The build writes the ISO to `output/<project>.iso` and a manifest to
`tests/artifacts/nucleus/last-build.json`:

```json
{ "iso": ".../output/harness-test.iso", "fighter": "Fox",
  "colorIndex": 4, "costumeId": "angy-plfxag", "costumeCount": 5 }
```

`colorIndex` is the modded costume's slot, which is also the number of `X`
presses on the CSS to reach it (`pipe.js char Fox --color 4`).

## How it drives the app

- **Backend, not UI.** It calls the Flask REST API the desktop app's frontend
  uses (`/api/mex/project/create`, `/project/open`, `/import`, `/export/start`),
  so it exercises the real build engine (MexCLI, CSP generation, ISO export)
  without clicking through Electron.
- **Isolated.** The dev backend roots all data in the repo (`projects/`,
  `storage/`, `output/`); the installed app uses `%LOCALAPPDATA%\SSBM Nucleus`.
  Running this harness does not touch the installed app's data. It picks a free
  port (preferring 5000), so close the app first only if you want port 5000.
- **`_run_backend.py`** is a thin launcher: it presents a fake-TTY stdin so
  flask-socketio's dev-server guard lets the server bind under a non-interactive
  parent, then runs `backend/mex_api.py` unchanged. No app code is modified.

## Requirements

- The Nucleus dev setup must be complete (vanilla assets extracted) — check
  `GET /api/mex/setup/status`. MexCLI must be built at
  `utility/MexManager/MexCLI/bin/Release/net6.0/mexcli.exe`.
- A vanilla 1.02 ISO for `project/create` (default: the melee working ISO the
  dolphin tests use; override with `--iso`).
- Node 18+ (uses global `fetch`) and the repo `venv` with the backend deps.
