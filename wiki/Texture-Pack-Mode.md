# Texture Pack Mode

Texture-pack mode is an export workflow that turns the current build's character portraits into a Dolphin texture pack.

The important practical detail is that this is mainly a **CSP texture-pack pipeline**, not a generic "dump every texture in the game" system.

## What It Does

In normal ISO export, Nucleus writes the current M-EX project to a playable ISO.

In texture-pack mode, Nucleus does extra work around the project's CSP files:

1. backs up the project's current CSPs
2. replaces them with encoded placeholder images
3. exports the ISO
4. restores the original project CSPs
5. watches Slippi Dolphin's dump folder
6. swaps dumped placeholder textures with the real CSPs in Dolphin's load folder

That produces a Dolphin texture-pack result from the current build without permanently changing the project.

## What It Is For

This mode exists so the exported build can use high-resolution CSP-style textures in Dolphin, where normal in-ISO size limits do not apply the same way.

The current implementation is centered on:

- character select portraits
- per-costume matching on the CSS
- preferring HD CSPs from storage when they are available

## Requirements

Texture-pack mode depends on a few things being true:

- you need an active M-EX project to export
- you need a valid Slippi Dolphin path in Settings
- Dolphin needs to be dumping textures into `User/Dump/Textures/GALE01`
- the build needs costumes with CSP entries to match against

If no textures are being dumped, the watcher has nothing to match.

## Export Flow

When texture-pack mode is enabled during ISO export, the backend:

1. creates a `buildId` for the export
2. backs up `assets/csp` to `assets/csp_backup`
3. walks the fighters and costumes in the current M-EX project
4. records a mapping from a global placeholder index to each costume's real CSP
5. replaces each project CSP with a small encoded placeholder PNG
6. exports the ISO
7. restores the original CSPs back into the project

It also writes supporting files into the output area:

- a mapping file like `<buildId>_texture_mapping.json`
- a `debug_placeholder_sample.png` image for inspection

The project should end the export with its normal CSPs restored.

## Listening Flow

After the ISO finishes exporting, Nucleus can start a watcher for that `buildId`.

The watcher:

- loads the saved mapping file
- derives Dolphin paths under `User/Dump/Textures/GALE01` and `User/Load/Textures/GALE01`
- polls the dump folder for new `tex*.png` files
- decodes any placeholder texture it recognizes
- maps that decoded index back to a specific character costume
- copies the real CSP into the load folder using the dumped texture's filename

The intended user flow is:

1. export with texture-pack mode enabled
2. start listening
3. open the exported ISO in Dolphin
4. scroll through each character's costumes on the CSS
5. let Nucleus match the dumped textures as they appear
6. stop listening when the matches are done

## How Matching Works

The placeholder system is not random.

Nucleus generates a 16x16 image with:

- four finder markers
- seven data cells
- a base-4 encoded costume index

When Dolphin dumps that image, the watcher samples the dumped PNG, verifies the finder markers, decodes the index, and looks up the costume in the saved mapping.

That is why the workflow depends on seeing the placeholders on the CSS first. The watcher is matching dumped portrait textures, not guessing from filenames alone.

## HD CSP Preference

When a dumped placeholder is matched, Nucleus tries to use the best real image it can find.

The current order is:

1. try to find an HD CSP in storage using perceptual-hash matching
2. if no HD match is found, fall back to the backed-up project CSP

So texture-pack mode benefits from the CSP and HD-CSP workflows, but it does not require every costume to already have a custom HD file.

## Output Layout

Matched textures are written into Dolphin's load path under a build-specific subfolder:

- `User/Load/Textures/GALE01/<build_name>/`

Each copied file keeps the dumped Dolphin texture filename so Dolphin can load it correctly.

When listening stops, Nucleus saves the updated mapping again and reports the final texture-pack path.

## What It Does Not Do

Texture-pack mode does not currently behave like a general texture-modding lab.

It is not:

- a generic stage-texture pack builder
- a character model texture dumper
- an automatic in-game texture crawler
- a substitute for the normal ISO export path

Its current job is much narrower: derive loadable CSP textures from the current build by using Dolphin's dump/load system.

## Common Failure Cases

If the workflow feels stuck, the usual problems are:

- the Slippi Dolphin path is missing or wrong
- the mapping file for the build was not found
- Dolphin is not producing dumped `tex*.png` files
- the relevant costumes were never visited on the CSS
- the costume has no usable CSP entry to map from

The fastest sanity check is whether the dump folder is receiving new texture PNGs while you browse costumes.

## Related Pages

- [CSP And Pose Workflow](CSP-And-Pose-Workflow.md)
- [Vault And Distribution Workflow](Vault-And-Distribution-Workflow.md)
- [Character Mod Workflow](Character-Mod-Workflow.md)
