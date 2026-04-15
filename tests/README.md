# Test Harnesses

`tests/dolphin` contains a first-pass Windows harness for launching Dolphin against an ISO with an isolated user directory, a scripted keyboard timeline, and checkpoint screenshots.

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
