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
- **One test at a time**: two Dolphins would fight over the screen and pipe;
  the blueprint enforces a single running test and refuses to start if the
  user already has a Dolphin window open.

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
| `match_setup.py` | In-match setup (rules, ports) |
| `observe.py` | Crash/hang detection: process death or MEM1 gone → CRASH; frozen frame counter → HANG; otherwise healthy |
| `screenshot.py` | Capture Dolphin's render window via `PrintWindow(PW_RENDERFULLCONTENT)` (works even when occluded/background), with a desktop-grab fallback |
| `capture.py` | Clean stage screenshots: RAM-patches invisible fighters / no HUD / solo 1-player match, then screenshots the stage |

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

## Consumers

- **`blueprints/test_in_game.py`** — the HTTP/WebSocket shell. Endpoints for
  testing full builds, single costumes, custom characters, custom stages, and
  DAS stage skins, plus stage screenshot capture (single + batch). Runs the
  engine in a background thread and streams `test_progress` /
  `test_complete` / `test_error` over SocketIO. See
  [API_REFERENCE.md](API_REFERENCE.md#test-in-game-blueprint).
- **`blueprints/bundles.py`** and **`blueprints/xdelta.py`** — use
  `ingame.boot.launch_real` / `iso_dir_from_slippi` for their "Play" endpoints
  (launching a built ISO in the user's real Slippi Dolphin).
