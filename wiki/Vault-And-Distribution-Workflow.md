# Vault Backup And Restore

Vault backup and restore is the library-level preservation workflow.

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

This is about preserving your library state, not exporting an ISO or rebuilding a patch.

## Separate Workflows

These are separate workflows:

- normal ISO export settings
- CSP compression
- patches
- texture-pack mode

Those are separate workflows now.

## Summary

The vault is your long-term library.

Vault backup and restore is the workflow for saving or recovering that library as a whole.
