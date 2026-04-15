# Test Harnesses

`tests/dolphin` contains two separate proof-of-concept harnesses:

- a first-pass Windows harness for launching Dolphin against an ISO with an isolated user directory, a scripted keyboard timeline, and checkpoint screenshots
- a WSL2 path for the `emubench-dolphin` fork, which exposes an HTTP control server inside Dolphin itself

It is intentionally separate from the app runtime. The goal is to prove out:

- launch a chosen Dolphin executable
- boot a chosen ISO
- run a small scripted input sequence
- capture screenshots into the run artifact directory
- keep all temporary Dolphin state inside `tests/artifacts/`

Usage:

```powershell
node tests/dolphin/driver.js --iso "C:\path\to\modded.iso"
```

Optional flags:

```powershell
node tests/dolphin/driver.js `
  --dolphin "C:\path\to\Dolphin.exe" `
  --scenario "tests\dolphin\scenarios\boot-and-hold-a.json" `
  --template-user-dir "C:\path\to\User"
```

Each run writes artifacts under `tests/artifacts/dolphin/<timestamp>-<scenario>/`, including logs, the temporary Dolphin `User` directory, and any screenshots captured by the scenario.

The current implementation is Windows-only and uses keyboard input focused into the Dolphin window. It is good enough for smoke tests, not yet for high-confidence automation.

## WSL emubench-dolphin

The cloned fork lives under `tests/external/emubench-dolphin` and can be built in WSL with CMake/Ninja. The current WSL build output is:

```text
tests/external/emubench-dolphin/build-wsl/Binaries/dolphin-emu-nogui
```

Two WSL smoke scripts are included:

```powershell
wsl -d Ubuntu -- bash /mnt/c/Users/david/projects/NucleusDesktop/tests/dolphin/wsl-http-smoke.sh /mnt/c/Users/david/OneDrive/Documents/Slippi/fr.iso
```

This boots an ISO under `Xvfb` and verifies that the Dolphin HTTP server answers on `http://127.0.0.1:8080/`.

```powershell
wsl -d Ubuntu -- bash /mnt/c/Users/david/projects/NucleusDesktop/tests/dolphin/wsl-controller-smoke.sh /mnt/c/Users/david/OneDrive/Documents/Slippi/fr.iso
```

This boots the ISO, waits for the HTTP server, then sends a simple controller payload to `POST /api/controller/0` and expects a JSON response that includes a screenshot token.

Artifacts for the WSL path are written under:

```text
tests/artifacts/wsl/http-smoke/
tests/artifacts/wsl/controller-smoke/
```

The controller smoke run currently produces persisted screenshots under:

```text
tests/artifacts/wsl/controller-smoke/user/ScreenShots/
```
