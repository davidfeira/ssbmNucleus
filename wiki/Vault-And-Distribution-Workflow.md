# Vault And Distribution Workflow

This page covers the workflows that package, preserve, or share what you have built.

## Vault Organization

The vault is not just a dump folder. It is a managed library.

Current storage-side workflows include:

- renaming items
- reordering items
- moving skins to top or bottom
- organizing costumes into folders
- deleting items from storage

Those actions are about the library itself, not the active project build.

## Vault Backup And Restore

Nucleus can back up the entire vault as one ZIP.

That backup includes the storage files and metadata that make the library work.

Restore supports two basic mindsets:

- **replace**, where the current vault is cleared before restore
- **merge**, where the backup is extracted into the existing vault

This is about preserving your library state, not rebuilding an ISO directly.

## ISO Export

When you export, Nucleus builds from the **current MEX project**.

That means the export includes whatever costumes, stages, extras, and ordering are active in the open project at that moment.

The export workflow also includes options like:

- CSP compression
- Color Smash
- texture-pack mode

## Xdelta Patches

Nucleus has a patch-library workflow built around `.xdelta` files.

There are two main directions:

- **build** an ISO from a stored xdelta patch plus a vanilla ISO
- **create** a new xdelta patch from a vanilla ISO and a modded ISO

This is the main "share a build without sharing a full ISO" workflow.

## Patch Library

The patch library itself stores:

- the xdelta file
- metadata like name and description
- an optional image

So patch management is part of the vault-style library experience even though the patch output is distribution-focused.

## Texture Pack Mode

Texture-pack mode is a separate export-oriented workflow.

In broad terms, it:

1. exports an ISO that uses placeholder CSP-like data
2. watches Slippi Dolphin's texture dump folder
3. matches dumped textures back to costumes
4. writes the resulting textures into Dolphin's load folder structure

This is closer to "derive a texture pack from the build" than to a normal ISO export.

For the detailed flow, see [Texture Pack Mode](Texture-Pack-Mode.md).

## Good Mental Model

If the character, stage, and extra workflows are about assembling a build, this workflow is about preserving it, exporting it, or sharing it.
