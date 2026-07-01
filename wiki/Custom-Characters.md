# Custom Characters

Custom characters are **wholly new fighters** added to the roster through m-ex — Sonic, Shadow, Mewtwo clones, and so on. They are not costume swaps on an existing fighter; they get their own CSS slot.

## Where They Come From

Two sources:

- **MexManager character packages** — a fighter ZIP exported from MexManager. Import it with the normal Import button; Nucleus detects it as a custom character.
- **Scanning a modded ISO** — Nucleus can extract non-vanilla fighters out of an existing m-ex build, so you can rip a character from a modpack you already have.

## What The Vault Stores

Each custom character is a vault entry with:

- the original fighter package (kept intact so it can be re-exported)
- its CSS icon and per-costume portraits
- extracted metadata (name, costumes, sounds)

Custom characters appear in their own vault section, separate from vanilla-character costumes.

## The Detail View

Opening a custom character shows its costumes and support assets. From there you can:

- rename or delete the character
- browse its costume slots
- add **custom skins** to the character — drag a costume from a vanilla character onto a custom character's skin area, or import skins made for it
- assign the character to a **custom series** (the franchise symbol shown behind its portraits)
- browse and edit its **sound bank** (see [Sound Mods](Sound-Mods.md))

## Installing

Installing a custom character adds it to the open MEX project's roster via m-ex: CSS slot, fighter data, sounds, and all. Removing it takes it back out.

Sound banks and announcer calls are handled automatically on install — imported characters reuse vanilla banks where possible and get a generic announcer call, so a reskin-type character does not bloat the build with duplicate audio.

## Testing

A custom character (or one specific skin of it) can be smoke-tested with [Test In Game](Test-In-Game.md): Nucleus builds a minimal ISO with just that character, boots it in an isolated Dolphin, picks the character on the CSS, and reports whether the match loads.

## Compatibility Notes

- Characters authored in special modified builds can depend on that build's custom m-ex core. If a character crashes on a vanilla-based project with an m-ex assertion, it likely needs its original base build.
- Custom characters based on Kirby or Ice Climbers inherit those characters' special-case behavior.

## Related Pages

- [Character Mod Workflow](Character-Mod-Workflow.md)
- [Custom Stages](Custom-Stages.md)
- [Sound Mods](Sound-Mods.md)
- [Test In Game](Test-In-Game.md)
