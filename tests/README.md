# Test Harnesses

This directory contains local harnesses used to boot Melee ISOs, drive Slippi
Dolphin, and collect screenshots or crash signals. The production in-app engine
lives in `backend/ingame/`; see `docs/INGAME_TESTING.md` for that Windows-only
runtime harness. The files here are lower-level developer tools and prototypes.

## `tests/dolphin`

`tests/dolphin` provides Dolphin launch and controller primitives.

### `driver.js`

Launches a chosen ISO in an isolated Dolphin `User` directory, applies known
controller/config settings, runs a scenario JSON, and writes artifacts.

```powershell
node tests/dolphin/driver.js --iso "C:\path\to\game.iso"
```

Options:

```text
--iso <path>                ISO to boot. Required unless --help is used.
--dolphin <path>            Dolphin executable. Defaults to Slippi Launcher netplay/playback if found.
--scenario <path>           Scenario JSON. Default: tests/dolphin/scenarios/boot-and-hold-a.json.
--template-user-dir <path>  Template Dolphin User dir. Defaults to "<dolphin dir>\User" when present.
--run-dir <path>            Use an explicit artifact directory for this run.
--pipe-index <n>            Use \\.\pipe\slippibot<n> for port 1. Useful for two-Dolphin tests.
--texture-dump              Enable DumpTextures and HiresTextures before boot.
--keep-open                 Leave Dolphin running after the scenario finishes.
--dry-run                   Build the isolated config and print the launch plan without starting Dolphin.
--help                      Show command help.
```

Scenario steps support `wait`, `focus`, `tap`, `keyDown`, `keyUp`,
`screenshot`, and `checkpoint`. Built-in scenarios live under
`tests/dolphin/scenarios/`.

Each run writes `run.json`, `driver.log`, the temporary Dolphin `User` dir,
Dolphin stdout/stderr logs, optional `dolphin.exit.json`, and screenshots under
`tests/artifacts/dolphin/<timestamp>-<scenario>/` unless `--run-dir` is set.

### `control.js`

Interactive wrapper for a running Dolphin. It can launch an ISO, discover or
record the live PID, tap keyboard-mapped GameCube buttons, hold buttons across
calls, capture screenshots, and kill the process tree.

```powershell
node tests/dolphin/control.js launch --iso "C:\path\to\game.iso"
node tests/dolphin/control.js status
node tests/dolphin/control.js shot --label css
node tests/dolphin/control.js press A START --ms 80
node tests/dolphin/control.js down B
node tests/dolphin/control.js up B
node tests/dolphin/control.js kill
```

Screenshots and session state are stored under
`tests/artifacts/dolphin/live/`.

### `pipe.js`

Focus-free controller input through Slippi Dolphin's named pipe. It opens a new
pipe connection per input frame, matching Dolphin's one-flush-per-connection
behavior.

```powershell
node tests/dolphin/pipe.js neutral
node tests/dolphin/pipe.js tap A --ms 50
node tests/dolphin/pipe.js tilt MAIN 1.0 0.5 --ms 100
node tests/dolphin/pipe.js char Fox --color 4
node tests/dolphin/pipe.js startmatch Fox --color 4
node tests/dolphin/pipe.js gotocss
node tests/dolphin/pipe.js cpustep
node tests/dolphin/pipe.js gotostage
```

Use `--port <n>` to target `\\.\pipe\slippibot<n>`.

### `pipe-daemon.js`

Persistent bridge from a local TCP socket to Dolphin's named pipe. This keeps
one pipe connection open, which is useful when reconnect-per-frame input causes
stuck releases or stick recentering problems.

```powershell
node tests/dolphin/pipe-daemon.js --port 1 --tcp 48010
```

TCP commands are newline terminated: `TAP`, `PRESS`, `RELEASE`, `TILT`,
`HOLDTILT`, `STICK`, `TRIG`, `NEUTRAL`, and `RAW`. Logs go to
`tests/artifacts/dolphin/live/pipe-daemon.log`.

### Native helper scripts

These are implementation helpers used by `driver.js` and `control.js`:

- `win-input.ps1` focuses a Dolphin window and emits one keyboard action.
- `win-window.ps1` reports window status or captures a screenshot.
- `win-batch.ps1` batches focus, key taps, gaps, and optional screenshot capture
  in one PowerShell process for lower latency.

## `tests/nucleus`

`tests/nucleus` layers the Dolphin primitives over the Nucleus dev backend. It
builds modded ISOs through the same Flask API the desktop app uses, then boots
and observes them. See `tests/nucleus/README.md` for command details.

The main flow is:

```powershell
node tests/nucleus/build-modded-iso.js --type costume --fighter Fox
node tests/nucleus/run-modded-match.js --closed-loop
```

## WSL `emubench-dolphin`

The WSL path is optional. The scripts expect an external checkout at
`tests/external/emubench-dolphin`; that checkout is not part of this repository
by default.

Apply the local-mode patch before building the fork:

```powershell
wsl -d Ubuntu -- bash -lc "cd /mnt/c/path/to/ssbmNucleus/tests/external/emubench-dolphin && git apply /mnt/c/path/to/ssbmNucleus/tests/dolphin/patches/emubench-dolphin-local-mode.patch"
```

Smoke scripts:

```powershell
wsl -d Ubuntu -- bash /mnt/c/path/to/ssbmNucleus/tests/dolphin/wsl-http-smoke.sh /mnt/c/path/to/game.iso
wsl -d Ubuntu -- bash /mnt/c/path/to/ssbmNucleus/tests/dolphin/wsl-controller-smoke.sh /mnt/c/path/to/game.iso
```

Artifacts are written under `tests/artifacts/wsl/http-smoke/` and
`tests/artifacts/wsl/controller-smoke/`.
