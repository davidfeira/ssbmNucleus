# Manual Import

Manual import adds mod files to the vault.

It does **not** install them into the current MEX project yet.

## The Import Button

There is one import affordance for the whole vault: the floating **Import** button in the bottom-right corner, which is always visible across every vault view. Dragging files anywhere onto the window does the same thing.

You do not choose a mod type first. Nucleus scans each file, detects what it is, and routes it to the right importer.

## Supported Files

- `.zip` / `.7z` — mod archives (costumes, stages, custom characters, custom stages, menu mods)
- `.dat` / `.usd` — a loose costume or stage file, even renamed (Nucleus identifies it by content)
- `.xdelta` — a build patch, added to the patch library
- `.ssbm` — a [Mod Bundle](Mod-Bundles.md)
- `.iso` / `.gcm` — starts an [ISO scan](ISO-Scanning.md) to rip skins out of the disc

Multi-select works; batch imports auto-fix or auto-skip instead of stopping on every dialog.

## Character Mod Archives

For character mods, the usual bundle is:

- the costume DAT
- a CSP image
- a stock icon

Nucleus will try to match included assets automatically.

If assets are missing:

- it can generate a CSP for you
- it can generate or fall back to a vanilla stock icon

Character imports also go through [Slippi safety validation](Slippi-Safety.md).

Character mods exported as ZIPs from **mexTool** work well here. That format already matches what Nucleus expects to scan.

## Stage Mod Archives

For stage mods, the usual bundle is:

- the stage file
- an optional screenshot

The screenshot is not required, but it is useful because Nucleus can use it as the preview image in the vault.

## Other Archive Types

The same import button also accepts:

- **custom character packages** (MexManager fighter ZIPs) — see [Custom Characters](Custom-Characters.md)
- **custom stage packages**, including classic `stage.yml` packages, which are converted automatically — see [Custom Stages](Custom-Stages.md)
- **menu mods** (CSS icon grids, backgrounds, doors) — see [Menus And Select Screen Mods](Menus-And-Select-Screen-Mods.md)

## Good Packaging

The simplest packaging rules are:

- character mod: DAT + CSP + stock
- stage mod: stage file + screenshot
