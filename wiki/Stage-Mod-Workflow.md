# Stage Mod Workflow

Nucleus currently handles stage mods through **Dynamic Alternate Stages** for a fixed set of competitive stages.

## What Makes Up A Stage Mod

At minimum, a stage mod is a stage archive file:

- usually a `.dat`
- Pokemon Stadium can use either `.dat` or `.usd`
- Nucleus should preserve the original Pokemon Stadium extension instead of normalizing it

A screenshot is optional, but useful because Nucleus can use it as the preview image in storage.

## What Importing Does

Importing a stage archive puts it into the **vault** as a stage variant.

Import does this:

1. Detects the stage file in the uploaded archive.
2. Figures out which supported stage bucket it belongs to.
3. Creates a per-stage variant ZIP in storage.
4. Extracts the screenshot separately for preview if one exists.
5. Adds the variant to the stage library.

The stored stage variant is a library item, not yet an active project file.

For the broader import flow, see [Manual Import](Manual-Import.md).

## Current Scope

The live stage workflow is not a generic all-stage browser. It is built around Dynamic Alternate Stages for six competitive stages:

- Battlefield
- Final Destination
- Yoshi's Story
- Dreamland
- Pokemon Stadium
- Fountain of Dreams

## Dynamic Alternate Stages Setup

Stage mods in Nucleus are installed into the stage folders in the active project.

Nucleus handles the base setup for you, including keeping the original stage as a `vanilla` variant.

That means the active project ends up with:

- the stage root file replaced with the stage-variant setup
- a per-stage alt folder such as `GrSt`, `GrOp`, or `GrPs`
- the original stage copied into that folder as `vanilla.dat` or `vanilla.usd`

## Variant Names

Imported stage variants get a sanitized ID and display name. In the current import path, names are intentionally kept short because the filename is also used as the key that keeps the stored preview image tied to that variant.

So stage naming is not just cosmetic. It affects the actual filename written into the project, and right now it is also part of the preview-image lookup. That coupling is a little jank and could be improved later, but that is why the naming rules are stricter than they should ideally be.

## Folder Layout

In the active project, alts live in folders named after the stage code.

Examples:

- `GrSt` for Yoshi's Story
- `GrOp` for Dreamland
- `GrPs` for Pokemon Stadium

The alt files themselves can be named freely as long as they use the right stage extension:

- `.dat` for most supported stages
- Pokemon Stadium may use either `.dat` or `.usd`
- for Stadium, Nucleus should preserve the original extension instead of changing it

## What Importing A Stage Variant To The Project Does

Once a stage variant is in the vault, you can import it into the active MEX project.

That workflow:

- reads the stored ZIP from the vault
- extracts the stage file
- writes it into the stage's project folder under the current stage code
- leaves the vault copy alone

So, just like character mods, the vault copy is your source item and the project copy is the active installed result.

## Button Tokens

Inside the project, stage variants can use button-token suffixes like `(B)`, `(X)`, `(Y)`, `(L)`, `(R)`, and `(Z)`.

Those tokens are part of the variant filename and represent button-selected stage variants.

Examples:

- `My Yoshi Alt (L).dat`
- `Frozen Stadium (X).usd`

## Slippi Status

Stage variants do not currently follow the same automatic Slippi validation flow as costumes.

Right now, stage Slippi status is a manual flag rather than an automated validator result.

For the full distinction, see [Slippi Safety](Slippi-Safety.md).

## Summary

A stage mod in Nucleus is a vault variant that can be copied into one of the stage folders in the current project.
