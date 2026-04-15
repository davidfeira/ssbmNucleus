# Slippi Safety

This page documents how Nucleus currently thinks about Slippi safety.

## The Big Distinction

For character costumes, Nucleus has an **automated validation and fix flow**.

For stage variants, Nucleus currently only stores a **manual Slippi status flag**.

So "Slippi safe" does not mean the same thing everywhere in the app.

## Character Costume Validation

When you import a character archive into the vault, Nucleus validates each detected costume DAT for Slippi safety before finishing the import.

If any costume fails the check, the app does not silently continue. It returns a dialog flow so the user can decide whether to:

- fix the costume
- import it as-is

## Why The Validator Uses Temp Files

The validator is not a pure read-only checker. It can modify the DAT file as part of the fixing process.

Because of that, Nucleus uses a copy-first workflow:

1. copy the DAT to a temp file
2. run validation on the temp copy
3. confirm the original was not modified
4. if auto-fix was chosen, copy the fixed temp DAT back into place

That is why the validation code is careful about filenames and hashes.

## Proper Melee Filenames Matter

The validator expects a proper Melee-style costume filename such as `PlFxGr.dat`.

Nucleus reconstructs that name from the parsed character and color before validation. If it cannot determine the proper filename, validation cannot proceed cleanly.

## What "Fix" Means In Practice

If you choose to auto-fix during import:

- the temp DAT is fixed
- the fixed DAT becomes the one written into the stored costume ZIP
- the costume metadata is marked as tested and safe

If you import as-is:

- the original DAT is stored
- the metadata records that the costume was tested and not considered safe

## Retesting Stored Costumes

Vault costumes can be retested later.

That flow:

- extracts the stored DAT from the costume ZIP
- validates it again
- optionally applies an auto-fix
- if fixed, rewrites the DAT inside the stored ZIP
- updates the stored Slippi metadata

So retest is not just a label refresh. It can actually update the stored costume package if you choose the fix path.

## Manual Override

Nucleus also supports a manual override for costume safety.

That does **not** change the DAT. It only changes metadata:

- `slippi_safe`
- `slippi_manual_override`
- test date

This is useful when the user wants to force the library to treat a costume as safe or unsafe, but it is important to remember that this is metadata, not proof.

## Stage Slippi Status

Stage variants do not currently go through the same automatic validator path.

Instead, stage Slippi state is stored as manual metadata on the variant. In other words, the stage side of the system is currently closer to "known status annotation" than to "validated and auto-fixable pipeline."

## What The App Actually Knows

Today, Nucleus can say these things with confidence:

- whether the costume validator reported the DAT as safe
- whether a fix was applied
- whether the user manually overrode the result

What it does **not** document in this repo is the full low-level rule set used by the external Slippi validator.

So the app knows the outcome of validation, but not necessarily every internal rule behind that outcome.

## Practical Warning

The older color/effect notes in the repo also mention desync risk for some gameplay-adjacent edits, such as hitbox-element changes.

That means "visual modding" and "Slippi safety" are related but not identical topics. Some visual-looking changes still touch gameplay-relevant data.

## Good Mental Model

For costumes, Slippi safety in Nucleus is:

- validator result first
- auto-fix support second
- manual override as metadata only

For stages, Slippi safety is currently:

- a manually maintained status flag

## Related Pages

- [Character Mod Workflow](Character-Mod-Workflow.md)
- [Stage Mod Workflow](Stage-Mod-Workflow.md)
- [DAT File Structure](DAT-File-Structure.md)
