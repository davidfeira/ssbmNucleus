# Vault Vs Project

This is the most important distinction in the app.

## The Vault

The vault is your library. It stores imported costumes, stage variants, preview images, pose files, extra presets, patch metadata, and the main `metadata.json` that ties everything together.

The vault is meant to be stable and reusable. Importing something into the vault usually means "save this for later and make it manageable."

## The Current MEX Project

The current MEX project is the active build you are editing. This is the set of files that the game or ISO export actually uses.

Installing or applying something to the project means "write this into the current build."

## The Difference In Practice

- importing a costume ZIP puts it in the vault
- installing that costume from the character panel writes it into the active MEX project
- importing a stage ZIP puts a stage variant in the vault
- importing a DAS variant into a stage slot writes a stage file into the active MEX project
- creating or installing an extra patches a project DAT directly
- exporting an ISO reads the current MEX project, not the whole vault
- backing up the vault preserves your library, not a full game build

## Why This Split Is Good

Without this split, it would be hard to reuse the same library across multiple project setups.

The vault gives you:

- a permanent collection
- previews and metadata
- import, rename, reorder, and folder organization
- backup and restore

The project gives you:

- the currently playable build
- costume order and stage files that match the open project
- the exact files used by ISO export and patch creation

## Typical Loop

1. Import mods into the vault.
2. Choose which ones to install into the current MEX project.
3. Reorder or tweak the project build.
4. Export an ISO or create a patch.

If something feels confusing, ask: "am I saving this in the vault, or am I changing the active project?"
