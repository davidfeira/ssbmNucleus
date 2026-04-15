# Manual Import

Manual import adds supported mod archives to the vault.

It does **not** install them into the current MEX project yet.

## Supported Files

- `.zip`
- `.7z`

## What Nucleus Does

When you use the import button, Nucleus:

1. saves the archive temporarily
2. scans for character mods first
3. if none are found, scans for stage mods
4. imports the result into the vault

So you are not choosing character or stage first. The app scans the archive and decides what it is.

## Character Mod Archives

For character mods, the usual bundle is:

- the costume DAT
- a CSP image
- a stock icon

Nucleus will try to match included assets automatically.

If assets are missing:

- it can generate a CSP for you
- it can use a vanilla stock icon as a placeholder

Character imports also go through Slippi safety validation.

Character mods exported as ZIPs from **mexTool** work well here. That format already matches what Nucleus expects to scan.

## Stage Mod Archives

For stage mods, the usual bundle is:

- the stage file
- an optional screenshot

The screenshot is not required, but it is useful because Nucleus can use it as the preview image in the vault.

## Good Packaging

The simplest packaging rules are:

- character mod: DAT + CSP + stock
- stage mod: stage file + screenshot
