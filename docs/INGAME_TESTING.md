# In-Game Testing (`backend/ingame/`)

The in-app "Test in game" engine: a self-contained, **Windows-only** harness
(stdlib + Pillow — no Node, no pywin32, no PowerShell, no extra installs) that
boots a freshly-built ISO in an isolated Slippi Dolphin, drives it to a real
**offline** match, selects the modded character/stage, optionally triggers an
effect move, and reports **PASS / CRASH / HUNG** with screenshots.

Public entry point: `ingame.run_test(...)` (defined in `runner.py`).

## Key Properties

- **Isolated Dolphin**: `boot.py` never launches the user's real User dir. It
  makes a temp copy of their `Config/` + Slippi login, patches it (pipe
  controller on port 1, windowed, no confirm-stop) and boots Dolphin with
  `-u <temp dir>`. The user's netplay setup is untouched.
- **Closed-loop control via RAM feedback**: menu navigation reads the live
  scene state from emulated RAM rather than relying on blind timing.
- **Never goes online**: `nav.py` only succeeds when it confirms the offline
  VS character select screen, and hard-aborts (holding B to back out) if it
  ever detects the online CSS scene (major `0x08`). The harness can never
  enter matchmaking or waste a real player's time.
- **One test at a time**: two test jobs would fight over the screen and pipe;
  the blueprint enforces a single running test. If the user already has a
  Dolphin emulator window open, the engine waits and streams a progress message
  explaining why it needs that window closed before it continues.

## Module Map

| Module | Role |
|--------|------|
| `runner.py` | Orchestrator. Builds a test PLAN from the build manifest, runs each check, aggregates the verdict, always cleans up Dolphin + temp User dir |
| `boot.py` | Locate Slippi Dolphin, create the throwaway User dir, launch the ISO. Also exposes `launch_real()` for playing builds in the user's real Slippi (used by bundles/xdelta "Play" endpoints) |
| `nav.py` | Drive the post-boot menus to the offline VS CSS by scene-state feedback; abort on the online scene |
| `melee_mem.py` | Read live emulated GameCube RAM (finds the MEM1 region tagged `GALE01` in the Dolphin process, like Dolphin Memory Engine) |
| `melee_pipe.py` | Send controller input over Dolphin's named pipe (one persistent connection, libmelee-style) |
| `melee_css.py` / `char_select.py` | Closed-loop character select (cursor driven by RAM position feedback; grid data in `grid.json`) |
| `melee_sss.py` | Closed-loop stage select |
| `match_setup.py` | In-match setup and RAM patches for solo 1-player starts, no timer, direct player block writes, and CSS-to-SSS warps |
| `observe.py` | Crash/hang detection: process death or MEM1 gone → CRASH; frozen frame counter → HANG; otherwise healthy |
| `screenshot.py` | Capture Dolphin's render window via `PrintWindow(PW_RENDERFULLCONTENT)` (works even when occluded/background), with a desktop-grab fallback |
| `capture.py` | Live screenshot capture for stages, pause-screen mods, and batched DAS variants |
| `embed.py` | Tracks the active throwaway Dolphin PID and pins/parks its render window over the frontend preview rectangle |

## Public Python API

The harness is normally reached through the Flask blueprint, but these are the
stable Python entry points:

```python
ingame.run_test(
    iso_path,
    slippi_path,
    runs_root,
    manifest=None,
    emit=None,
    log=None,
    observe_seconds=9,
    hires_textures=False,
    load_seed=None,
)
```

`emit(stage, percentage, message)` receives progress updates. The return value
is a result dict with `verdict`, `pass`, `reason`, `checks`, `screenshot`,
`drove`, and `online_aborted`.

Other direct entry points:

- `ingame.capture.capture_stage(...)` - one clean live stage preview.
- `ingame.capture.capture_pause(...)` - live preview for a pause-screen mod.
- `ingame.capture.capture_stage_batch(...)` - many DAS stage previews in one
  boot where possible.
- `ingame.boot.launch_real(slippi_path, iso_path)` - launch a build in the
  user's real Slippi Dolphin for normal play.
- `ingame.boot.iso_dir_from_slippi(slippi_path)` - resolve the user's ISO
  library folder from Dolphin.ini.
- `ingame.embed.position(x, y, width, height)` / `ingame.embed.park()` - place
  or hide the throwaway render window for the in-app preview.

Related build helper:

- `backend/test_build.py` builds throwaway one-mod ISOs for the blueprint's
  single-mod endpoints, including costumes, custom characters and skins, custom
  stages, DAS stage skins, pause-screen mods, and batched DAS screenshot ISOs.

## Smart Test Plan

`runner.build_plan(manifest)` derives the minimal set of checks from a build
manifest. A full modpack (all six mod types in one ISO) is covered by just two
matches:

- **A)** the custom character on the custom stage → covers character + stage + menu background
- **B)** the modded fighter's costume on the DAS stage (holding its button), then the effect move in-match → covers costume + DAS + effect

Single-type builds get one matching check. Anything that can't be driven
specifically falls back to a **boot-health watch** (boot → reach the CSS so the
mod's data loads → watch process/frame health), which still catches most
broken builds.

Verdict severity (worst wins): `healthy < ended < never_started < hung < crashed < error`.

## Manifest Fields

`run_test` can run without a manifest; that becomes a boot-health check at the
offline CSS. A manifest lets it select the exact content to exercise. A modpack
manifest can include several of these keys at once:

| Key | Required fields | What it drives |
|-----|-----------------|----------------|
| `costume` | `{ "fighter": "Fox", "colorIndex": 4 }` | Selects a vanilla fighter and costume slot |
| `character` | `{ "name": "Sonic", "cssIcon": { "x": ..., "y": ..., "index": ..., "fighter": 0x1A } }` | Selects a custom m-ex fighter by placed CSS icon; `fighter` enables the faster direct memory path |
| `customStage` | `{ "name": "...", "sssIcon": { "page": 1, "x": ..., "y": ..., "stageId": 0x40 } }` | Selects a custom m-ex stage by internal id when known, otherwise by SSS icon |
| `das` | `{ "stage": "battlefield", "button": "X" }` | Holds a DAS button while force-selecting the stage |
| `effect` | `{ "fighter": "Fox", "move": "neutralb" }` | Starts a match and performs the move that loads the effect |

The runner prefers cursor-free memory selection when the manifest gives enough
IDs to write the player block and force-select the stage. It falls back to the
closed-loop CSS/SSS cursor path when it must verify UI placement itself.

## Consumers

- **`blueprints/test_in_game.py`** — the HTTP/WebSocket shell. Endpoints for
  testing full builds, single costumes, custom characters, custom-character
  skins, custom stages, and DAS stage skins; live stage screenshot capture
  (single + batch); live pause-screen capture; preview window positioning; and
  status. Runs work in a background thread and streams `test_progress` /
  `test_complete` / `test_error` for tests, plus `capture_progress` /
  `capture_complete` / `capture_batch_complete` / `capture_error` for capture.
  See [API_REFERENCE.md](API_REFERENCE.md#test-in-game-blueprint).
- **`blueprints/bundles.py`** and **`blueprints/xdelta.py`** — use
  `ingame.boot.launch_real` / `iso_dir_from_slippi` for their "Play" endpoints
  (launching a built ISO in the user's real Slippi Dolphin).
