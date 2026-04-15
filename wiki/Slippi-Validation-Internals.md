# Slippi Validation Internals

Implementation notes for how Nucleus wires Slippi validation into the costume workflow.

User-facing overview: [Slippi Safety](Slippi-Safety.md).

## Scope

How Nucleus calls the validator and stores the result.

Not a full explanation of every low-level rule used by the external Slippi validator itself.

## Character Costume Validation Path

For character costumes, Nucleus runs validation through `validate_for_slippi()` in `utility/website/backend/app/services/dat_processor.py`.

That wrapper is used from the import and retest flows in `backend/mex_api.py`.

## Why Filename Reconstruction Matters

The external validator expects a proper Melee costume filename such as `PlFxGr.dat`.

Because uploads and stored ZIP entries do not always use that exact name, Nucleus first parses the DAT and reconstructs the expected Melee filename from the detected character and color.

If Nucleus cannot determine that filename, validation cannot proceed cleanly.

## Copy Validate Replace Flow

The validator wrapper uses a copy-based flow instead of validating the original file in place.

At a high level, it does this:

1. hash the original DAT
2. derive the proper Melee filename
3. copy the DAT to a temporary file with that expected filename
4. run the external validator on the temp copy
5. confirm the original file's hash did not change
6. if auto-fix was requested and the validator changed the temp copy, copy the fixed temp file back to the original

This is the part that hides the temp-file details from the normal user flow.

## Import Flow

During character import in `backend/mex_api.py`, Nucleus uses two validation stages:

1. an initial check pass during upload, before import is finalized
2. the actual import pass, which either fixes or stores the DAT depending on the user's choice

The upload route uses `slippi_action` to distinguish those paths:

- no `slippi_action` means "check first and decide whether a dialog is needed"
- `fix` means import with auto-fix enabled
- `import_as_is` means import without applying the fix

When import succeeds, the stored costume entry records fields such as:

- `slippi_safe`
- `slippi_tested`
- `slippi_test_date`
- `slippi_manual_override`

## Retest Flow

Retest uses `/api/mex/storage/costumes/retest-slippi`.

That route:

1. extracts the DAT from the stored costume ZIP
2. runs `validate_for_slippi()` again
3. optionally rewrites the DAT inside the ZIP if auto-fix was chosen
4. updates the stored Slippi fields
5. clears any previous manual override

So retest is a real validation pass, not just a status toggle.

## Manual Override Flow

Manual override for costumes uses `/api/mex/storage/costumes/override-slippi`.

That path does **not** run the validator and does **not** modify the DAT. It only updates the stored status fields so the UI treats the costume as safe or unsafe.

## Stage Flow

Stages do not go through the same automated validation path.

Instead, stage status is set through `/api/mex/storage/stages/set-slippi`, which stores the chosen status and test date as metadata only.

So the key split is:

- costumes: validator-backed result, with optional auto-fix
- stages: manual status only

## Code Pointers

If you need to trace the implementation, the main entry points are:

- `utility/website/backend/app/services/dat_processor.py`
- `backend/mex_api.py`
- `utility/website/backend/tools/processor/validate_costume.py`

## Summary

Nucleus does not implement its own full Slippi rule set.

It wraps an external validator, makes sure the DAT is presented under the expected Melee filename, protects the original file during checking, and then stores the result in Nucleus metadata.

## Related Pages

- [Slippi Safety](Slippi-Safety.md)
- [Character Mod Workflow](Character-Mod-Workflow.md)
- [Melee Files Reference](../docs/new-414/Melee-Files.md)
