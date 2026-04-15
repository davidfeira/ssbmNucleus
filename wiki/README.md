# Melee Modding Wiki

This folder is for general Super Smash Bros. Melee modding knowledge and background context. Think of it as a local wiki: short, linked pages that explain how the game data is laid out, what the important terms mean, and what has or has not been reverse-engineered.

## Scope

The wiki should answer questions like:

- what files control costumes, effects, stages, and CSPs
- where color data usually lives
- what patterns or structures matter when editing DAT files
- what parts of the modding workflow are well understood
- what areas are still poorly documented

## Does Not Belong Here

Nucleus setup, build instructions, release steps, and app-specific usage docs belong in [docs](../docs/README.md).

## Local Browser View

Run `npm run wiki` from the repo root, then open `http://127.0.0.1:4173/wiki/`.

On Windows, you can also run `open_wiki.bat` from the repo root. It starts the wiki server if needed and opens the wiki in Firefox.

## Start Here

- [Workflow Map](Workflows.md)
- [Vault Vs Project](Vault-Vs-Project.md)
- [Melee File Map](Melee-File-Map.md)
- [Color And Effect Modding](Color-And-Effect-Modding.md)
- [Research Sources](Research-Sources.md)
- [Open Questions](Open-Questions.md)

## Workflow Pages

- [First-Run Setup](First-Run-Setup.md)
- [Character Mod Workflow](Character-Mod-Workflow.md)
- [Stage Mod Workflow](Stage-Mod-Workflow.md)
- [Dynamic Alternate Stages](Dynamic-Alternate-Stages.md)
- [Extras And Effects Workflow](Extras-And-Effects-Workflow.md)
- [Fox And Falco Shared Extras](Fox-And-Falco-Shared-Extras.md)
- [CSP And Pose Workflow](CSP-And-Pose-Workflow.md)
- [Texture Pack Mode](Texture-Pack-Mode.md)
- [Vault And Distribution Workflow](Vault-And-Distribution-Workflow.md)
- [Ice Climbers Pairing](Ice-Climbers-Pairing.md)

## Technical Pages

- [DAT File Structure](DAT-File-Structure.md)
- [Slippi Safety](Slippi-Safety.md)
- [Character Files And Ownership](Character-Files-And-Ownership.md)

## Writing Style

- prefer short pages over giant reference dumps
- keep one topic per page
- link raw research material instead of copying it wholesale
- call out assumptions when a detail is inferred rather than proven

## Current Raw Sources

Some of the strongest existing source material still lives under [docs/color-effects-reference](../docs/color-effects-reference/). Treat that folder as source material and this wiki as the cleaned-up version.
