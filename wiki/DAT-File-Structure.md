# DAT File Structure

This is a practical page about HAL DAT files as Nucleus currently understands them.

It is **not** a full reverse-engineering spec. It is the subset that matters for the workflows in this repo.

## Why DAT Structure Matters Here

A lot of Nucleus behavior depends on being able to answer a few basic questions about a DAT:

- what character does this file belong to
- is this a real costume archive or just a data/effect mod
- what symbols are exposed in the root node table
- where should a known patch or texture operation be applied

For the app, that means "good enough to detect, validate, and patch" is more important than "document every structure in the format."

## Header Shape

The lightweight parser in this repo reads a DAT header like this:

- `0x00`: file size
- `0x04`: data block size
- `0x08`: relocation table count
- `0x0C`: root node count
- `0x10`: duplicate root node count
- `0x20`: start of the main data block

From there, it calculates:

- where the relocation table starts
- where the root node table starts
- where the string table starts

## Root Nodes And String Table

The root node table is the part Nucleus relies on most for detection.

Each root node entry is treated as:

- a data offset
- a string offset

The string offset points into the string table, which is where symbol names live. Those symbol names are what the parser actually uses to infer what kind of DAT it is.

## The Symbols Nucleus Cares About

In practice, the most important symbol families are:

- `ftData...`
- `Ply...`

That distinction is one of the key heuristics behind costume detection.

## `Ply` Usually Means Costume Ownership

If the parser sees `Ply` symbols, Nucleus treats the DAT as a character costume archive candidate.

Examples of the kind of symbols this logic expects:

- `PlyCaptain5KWh_Share_joint`
- `PlyMars5KNr_Share_joint`

Those symbols are part of why the app can tell that a DAT is a costume instead of just "some file related to a character."

## `ftData` Usually Means Character Data

If the parser sees only `ftData...` symbols and no `Ply` symbols, Nucleus treats the file as character data or an effect/data mod rather than a vault-importable costume.

That matters because:

- a costume import wants a costume archive
- a data mod may still be useful, but it is not the same workflow

This is why the unified import path rejects some DATs as "not a costume" even when they clearly belong to a character.

## Filename And Color Detection

Nucleus does not rely only on the archive filename. It also derives identity from the parsed symbols.

The parser tries to reconstruct Melee-style costume filenames like `PlFxGr` or `PlMsNr` from:

- the detected character
- the detected costume color

That reconstructed filename matters for two reasons:

1. it helps the app label and store the costume consistently
2. it is required for Slippi validation, because the validator expects a proper Melee character filename

## What Nucleus Does Not Fully Parse

Nucleus does **not** currently have one universal semantic parser for all internal DAT structures.

For most deeper edits, the app uses narrower strategies such as:

- known offset ranges
- known symbol paths for model or texture work
- dynamic offset detection for a few supported effect families

So there is a difference between:

- "understanding enough of the DAT to identify it"
- "understanding enough of the DAT to edit one known region safely"

## Practical Implication

If you are trying to document or debug a new asset, the first questions are usually:

1. does the file expose `Ply` symbols or only `ftData` symbols
2. what Melee filename should this DAT correspond to
3. is the thing you want to change tied to a known offset, a known texture path, or a shared effect file

Those three questions will get you much farther in this repo than a generic overview of the whole DAT format.

## Related Pages

- [Character Files And Ownership](Character-Files-And-Ownership.md)
- [Character Mod Workflow](Character-Mod-Workflow.md)
- [Color And Effect Modding](Color-And-Effect-Modding.md)
- [Research Sources](Research-Sources.md)
