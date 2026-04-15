# Slippi Safety

Nucleus uses two different Slippi-safety models: automated checks for costumes, manual status for stages.

## The Big Distinction

For character costumes, Nucleus has an **automated validation and fix flow**.

For stage variants, Nucleus currently only stores a **manual Slippi status flag**.

So "Slippi safe" does not mean the same thing everywhere in the app.

## Character Costumes

When you import a character archive into the vault, Nucleus validates each detected costume DAT for Slippi safety before finishing the import.

If any costume fails the check, the app does not silently continue. It returns a dialog flow so the user can decide whether to:

- fix the costume
- import it as-is

## What "Fix" Means In Practice

If you choose to auto-fix during import:

- the fixed DAT becomes the one written into the stored costume ZIP
- the costume is treated as tested and safe

If you import as-is:

- the original DAT is stored
- the app records that the costume was tested and not considered safe

## Retesting Stored Costumes

Vault costumes can be retested later.

Retest is not just a label refresh. If you choose the fix path, Nucleus can update the stored costume package with the fixed DAT.

## Manual Override

Nucleus also supports a manual override for costume safety.

That does **not** change the DAT. It only changes the app's stored status.

## Stage Slippi Status

Stage variants do not currently go through the same automatic validator path.

Instead, stage Slippi state is a manual status flag.

## What The App Actually Knows

Today, Nucleus can say these things with confidence:

- whether the costume validator reported the DAT as safe
- whether a fix was applied
- whether the user manually overrode the result
- whether a stage status was set manually

What it does **not** document in this repo is the full low-level rule set used by the external Slippi validator.

So the app knows the outcome of validation, but not necessarily every internal rule behind that outcome.

## Practical Warning

The older color/effect notes in the repo also mention desync risk for some gameplay-adjacent edits, such as hitbox-element changes.

That means "visual modding" and "Slippi safety" are related but not identical topics. Some visual-looking changes still touch gameplay-relevant data.

## Summary

For costumes, Slippi safety in Nucleus is:

- validator result first
- auto-fix support second
- manual override as metadata only

For stages, Slippi safety is currently:

- a manually maintained status flag

For the developer-facing validation details, see [Slippi Validation Internals](Slippi-Validation-Internals.md).

## Related Pages

- [Character Mod Workflow](Character-Mod-Workflow.md)
- [Stage Mod Workflow](Stage-Mod-Workflow.md)
- [Slippi Validation Internals](Slippi-Validation-Internals.md)
