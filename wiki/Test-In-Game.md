# Test In Game

"Test in game" answers one question quickly: **does this mod actually load in a real match?**

Nucleus builds a minimal throwaway ISO containing just the mod you are testing, boots it in Slippi Dolphin, drives the menus to a real offline match with the modded content selected, and reports the result — all hands-off.

## Where It Appears

The button shows up on things that can be match-tested:

- a costume's edit modal (vanilla-character skins)
- custom characters and their individual skins
- custom stages
- DAS stage variants
- pause-screen mods (as a live capture preview)

There is also a whole-build test after export, which exercises several mod types in as few matches as possible.

## What Actually Happens

1. Nucleus builds a small test ISO: vanilla plus just this mod
2. it launches an **isolated** copy of your Slippi Dolphin — a temporary config folder, so your real netplay setup is never touched
3. it navigates to the offline VS character select screen by reading the game's state, not by blind timing
4. it selects the modded character/costume/stage and starts a solo match
5. it watches the match for crashes or freezes, takes screenshots, and cleans everything up

The Dolphin window appears embedded inside the app while the test runs, so you can watch it work.

## The Verdict

Tests end in one of:

- **PASS** — the match loaded and ran healthy, with screenshots as proof
- **CRASH** — the game died (with a screenshot of where)
- **HUNG** — the game froze

## Stage Screenshot Capture

Stage variants have a related flow: **Capture Screenshot** boots the stage alone with a free camera and grabs a clean whole-stage preview image for the vault. DAS variants can be captured in batches — many variants per boot.

## Ground Rules

- **Windows only** (it drives the Dolphin window directly)
- **one test at a time**, and Nucleus asks you to close any running Dolphin first — two emulators would fight over the controller pipe
- it **never goes online**: the harness only proceeds on the offline character select and backs out if it ever sees the online menus

## Related Pages

- [Custom Characters](Custom-Characters.md)
- [Custom Stages](Custom-Stages.md)
- [Stage Mod Workflow](Stage-Mod-Workflow.md)
