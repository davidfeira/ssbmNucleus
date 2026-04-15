# Character Mod Workflow

This page explains what Nucleus treats as a character mod and what happens when you import or install one.

## What Makes Up A Character Mod

At minimum, a character mod needs a costume DAT file.

In practice, Nucleus thinks about a character mod as three main pieces:

- the **DAT** file, which is the actual costume/model archive
- the **CSP**, which is the character select portrait
- the **stock**, which is the in-match stock icon

The DAT is the real mod. The CSP and stock are support assets that make the mod look complete in menus and UI.

## What Importing Does

When you import a character archive into Nucleus, you are importing it into the **vault**, not directly into the active MEX build.

At a high level, import does this:

1. Detects character costume files inside the archive.
2. Runs Slippi safety validation on the DAT.
3. Lets you choose whether to auto-fix or import as-is if the mod is not Slippi safe.
4. Copies in an included CSP if one exists, or generates one if it does not.
5. Copies in an included stock if one exists, or falls back to a matching vanilla stock when possible.
6. Stores the result as a reusable vault item with previews and status info.

## What Gets Stored

After import, the vault effectively has a normalized version of the mod:

- a stored ZIP for the costume
- a standalone CSP preview file
- a standalone stock preview file
- metadata describing the skin name, color, sources, and Slippi state

The stored ZIP is the thing Nucleus installs from later.

## Naming And Identity

Nucleus tries to build a stable skin ID from the upload name or the DAT filename, then makes it unique if needed.

That means the imported mod has:

- an internal ID used by the vault
- a display name shown in the UI
- a costume code tied to the Melee file it came from

## What Installing Does

Installing a costume is a separate step from importing it.

When you install a costume, Nucleus uses the stored ZIP from the vault and tells MexCLI to add that costume to the selected fighter in the **current MEX project**.

That means:

- the vault copy stays as your source library item
- the active project gets a new installed costume entry
- project reorder and removal happen on the installed copy, not on the vault item

## Reordering And Removal

Once a costume is installed into the project, you can reorder or remove it from the fighter's active costume list.

That changes the current project build. It does not delete the original vault item unless you explicitly remove it from storage.

## Ice Climbers Special Case

Ice Climbers are the main exception to the normal character-mod pattern.

Important consequences:

- a complete pair still needs both Popo and Nana DAT files
- the pair shares one CSP/stock set rather than giving Nana separate menu assets

For the full explanation, see [Ice Climbers Pairing](Ice-Climbers-Pairing.md).

## Good Mental Model

A normal character mod is basically three files:

- the DAT, which is the actual costume
- the CSP, which is the menu portrait
- the stock, which is the in-match icon

The DAT is the real mod. The CSP and stock are the support assets that make it usable and presentable in the UI.

Ice Climbers follow the same idea, except the costume side is a Popo/Nana DAT pair that shares one menu asset set.
