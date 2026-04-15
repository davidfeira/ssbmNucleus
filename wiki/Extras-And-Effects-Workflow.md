# Extras And Effects Workflow

Extras are not full costume imports. They are targeted modifications applied to specific files in the current project.

## What Counts As An Extra

In the current app, extras mostly mean:

- effect color edits
- effect-gradient edits
- targeted model swaps
- targeted texture edits

These are things like lasers, shines, sword trails, gun models, and related effect assets.

## How Extras Differ From Costumes

Character costume workflow is centered on a stored ZIP that later gets installed into the project.

Extras work differently:

- the preset or mod definition lives in the vault metadata
- installing the extra patches a DAT file in the active project directly

So extras are closer to "apply this edit to the current build" than to "import a self-contained costume package."

## Current Supported Area

The strongest current extras support is around:

- Fox and Falco effect families
- sword trails for sword characters
- a smaller set of other effect types like Pikachu thunder and Mewtwo shadow ball

There is also support for some model- and texture-based extras, not just pure color swaps.

Fox and Falco are the most important "shared vs local" example in the current app:

- laser and side-B are character-local
- shine, up-B, and laser ring are shared through `EfFxData.dat`

For the full breakdown, see [Fox And Falco Shared Extras](Fox-And-Falco-Shared-Extras.md).

## What Installing An Extra Does

At a high level, extra installation does this:

1. Finds the right target DAT file in the current MEX project.
2. Loads the saved extra preset from vault metadata.
3. Detects the right offsets or regions in the target file.
4. Applies the patch directly to the project file.

That means the result is immediately part of the active project build.

## Why Offset Detection Matters

Some extras use dynamic offset detection instead of trusting a single hardcoded offset forever.

That matters because DAT layout can shift after other edits, and a patching workflow is much more robust if it can locate the right region in the current file instead of assuming a static byte position.

## Shared Extras

Some extras are treated as shared or owner-backed assets rather than being stored independently for every character.

That means the vault may store the extra under one character while other characters read or install that same extra through shared ownership rules.

Fox/Falco shared effects are the clearest current example of this pattern.

## Restore Behavior

Extras are reversible in a different way from costumes.

Instead of uninstalling a separate ZIP, the restore flow is about putting the target project asset back to its vanilla state for that extra or texture region.

## Good Mental Model

An extra is "a saved patch recipe for a known asset in the current project," not a standalone costume mod.
