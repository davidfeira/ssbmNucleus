# Stage Mod Workflow

Nucleus currently handles stage mods as **DAS variants** for a fixed set of competitive stages.

## What Makes Up A Stage Mod

At minimum, a stage mod is a stage archive file:

- usually a `.dat`
- Pokemon Stadium can use either `.dat` or `.usd`
- Nucleus should preserve the original Pokemon Stadium extension instead of normalizing it

A screenshot is optional, but useful because Nucleus can use it as the preview image in storage.

## What Importing Does

Importing a stage archive puts it into the **vault** as a stage variant.

At a high level, import does this:

1. Detects the stage file in the uploaded archive.
2. Figures out which supported stage bucket it belongs to.
3. Creates a per-stage variant ZIP in storage.
4. Extracts the screenshot separately for preview if one exists.
5. Adds the variant to the stage library.

The stored stage variant is a library item, not yet an active project file.

## Current Scope

The live stage workflow is not a generic all-stage browser. It is built around Dynamic Alternate Stages for six competitive stages:

- Battlefield
- Final Destination
- Yoshi's Story
- Dreamland
- Pokemon Stadium
- Fountain of Dreams

## Official DAS Constraints

Stage mods in Nucleus only make sense inside the DAS workflow.

The important user-facing rule is that DAS installs the replacement layer, and the actual stage alts live alongside it.

For the official rules and install details, see [Dynamic Alternate Stages](Dynamic-Alternate-Stages.md).

## Variant Names

Imported stage variants get a sanitized ID and display name. In the current import path, names are intentionally kept short, because long stage filenames can cause problems.

That means stage naming is not just cosmetic. It affects the actual filename written into the project.

## What Installing DAS Does

The DAS framework must exist in the active MEX project before stage variant management works the intended way.

Installing DAS prepares the active project so supported stages can use alt folders and button-triggered variants.

For the exact folder names and replacement-file setup, see [Dynamic Alternate Stages](Dynamic-Alternate-Stages.md).

## What Importing A DAS Variant To The Project Does

Once a stage variant is in the vault, you can import it into the active MEX project.

That workflow:

- reads the stored ZIP from the vault
- extracts the stage file
- writes it into the stage's project folder under the current stage code
- leaves the vault copy alone

So, just like character mods, the vault copy is your source item and the project copy is the active installed result.

## Button Tokens

Inside the project, DAS variants can use button-token suffixes like `(B)`, `(X)`, `(Y)`, `(L)`, `(R)`, and `(Z)`.

Those tokens are part of the variant filename and represent button-selected stage variants.

For the exact naming convention, see [Dynamic Alternate Stages](Dynamic-Alternate-Stages.md).

## Slippi Status

Stage variants do not currently follow the same automatic Slippi validation flow as costumes.

Right now, stage Slippi status is a manual flag rather than an automated validator result.

For the full distinction, see [Slippi Safety](Slippi-Safety.md).

## Good Mental Model

A stage mod in Nucleus is "a vault variant that can be copied into one of the DAS-managed stage buckets in the current project."

For the lower-level details and official install conventions, see [Dynamic Alternate Stages](Dynamic-Alternate-Stages.md).
