# Effects Workflow

Effects are not full costume imports. They are targeted modifications applied to specific files in the current project.

## What Counts As An Effect

In the current app, effects mostly mean:

- hex offset mods
- texture or model replacements done through HSDRaw

These are things like lasers, shines, sword trails, gun models, and related effect assets.

## How Effects Differ From Costumes

Character costume workflow is centered on a stored ZIP that later gets installed into the project.

Effects work differently:

- the effect definition lives in the vault metadata
- installing the effect patches a DAT file in the active project directly

So effects are closer to "apply this edit to the current build" than to "import a self-contained costume package."

## What Installing An Effect Does

At a high level, effect installation does this:

1. Finds the right target DAT file in the current MEX project.
2. Loads the saved effect definition from vault metadata.
3. Detects the right offsets or regions in the target file.
4. Applies the patch directly to the project file.

That means the result is immediately part of the active project build.

## Why Offset Detection Matters

Some effects use dynamic offset detection instead of trusting a single hardcoded offset forever.

That matters because DAT layout can shift after other edits, and a patching workflow is much more robust if it can locate the right region in the current file instead of assuming a static byte position.

## Shared Effects

Some effects are treated as shared or owner-backed assets rather than being stored independently for every character.

That means the vault may store the effect under one character while other characters read or install that same effect through shared ownership rules.

Fox/Falco shared effects are the clearest current example of this pattern. For that specific breakdown, see [Fox And Falco Shared Effects](Fox-And-Falco-Shared-Extras.md).

## Summary

An effect is "a saved patch recipe for a known asset in the current project," not a standalone costume mod.
