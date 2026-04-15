# Dynamic Alternate Stages

This page captures the official DAS behavior that the current stage workflow depends on.

It is based on the official Dynamic Alternate Stages instructions you provided, then translated into the terms Nucleus uses.

## What DAS Is

Dynamic Alternate Stages replaces a vanilla stage file with a loader-style setup that can pick from alternate stage files.

Important consequence:

- the DAS stage files are **not standalone**
- they **replace** the vanilla stage files
- you still need to provide actual alt stage files for the system to load

## Official Requirements

According to the official notes:

- M-EX is required
- the DAS stage files are console compatible
- the DAS stage files are Slippi Online compatible
- there is no hard limit on the number of alts per stage

## Folder Layout

In the active M-EX filesystem, alts belong in a folder named after the stage code.

Examples:

- `GrSt` for Yoshi's Story
- `GrOp` for Dreamland
- `GrPs` for Pokemon Stadium

The alt files themselves can be named freely as long as they use the expected stage file extension:

- `.dat` for most supported stages
- Pokemon Stadium alts may appear as `.dat` or `.usd`
- the important behavior is to preserve the original extension when moving or installing them

## What Gets Replaced

The official docs are explicit here:

- the provided DAS files replace the vanilla stage files
- they cannot function by themselves

So the actual playable setup is:

1. replace the stage with the DAS-enabled version
2. create the stage-code folder
3. put alt stage files inside that folder

Without the alts, you only have the replacement layer, not the full stage-variant setup.

## Official Manual Install Flow

The official flow is:

1. create or open an M-EX filesystem from a vanilla ISO
2. copy the DAS `ISO Files` into the filesystem's `files` folder, replacing when prompted
3. place each stage's alts into the matching stage-code folder
4. reopen that filesystem in mexTool
5. export back to ISO

## Button Triggers

Officially, a button-triggered alt is selected by putting a supported button name in parentheses inside the alt filename.

Examples:

- `GrSt (L).dat`
- `(X) GrOp.dat`

Supported buttons:

- `L`
- `R`
- `Z`
- `B`
- `X`
- `Y`

Nucleus represents the same idea with button-token suffixes such as `(B)` and `(X)` in the active project filenames.

## How This Maps To Nucleus

Nucleus automates part of this workflow, but the same DAS rules still apply.

For the app-level storage vs active-project split, see [Vault Vs Project](Vault-Vs-Project.md). For the user-facing stage flow, see [Stage Mod Workflow](Stage-Mod-Workflow.md).

## What Nucleus Automates

Relative to the official manual instructions, Nucleus mainly automates importing stage variants, installing the DAS layer, and moving variants into the right project locations.

## What Still Matters From The Official Docs

Even with automation, the official constraints still matter:

- DAS is still an M-EX-based workflow
- the active project still relies on stage-code folders
- variants still work by replacing the stage with a DAS-enabled loader plus alt files
- button-trigger behavior is still filename-driven

## Related Pages

- [Stage Mod Workflow](Stage-Mod-Workflow.md)
- [Vault Vs Project](Vault-Vs-Project.md)
- [Character Files And Ownership](Character-Files-And-Ownership.md)
