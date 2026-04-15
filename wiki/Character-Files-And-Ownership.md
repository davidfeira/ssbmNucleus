# Character Files And Ownership

This page answers one of the most important Melee-modding questions:

**Which file actually owns the thing I am trying to change?**

In practice, this question decides:

- whether a file is importable as a costume
- whether an effect is local or shared
- which workflow in Nucleus you should use
- whether a change is likely to affect one costume, one character, or multiple characters

## Costume Archives: `PlXxYy.dat`

These are the files most people think of as character skins.

They are costume-specific archives, and they are the main target of the vault costume workflow.

Examples:

- `PlFxGr.dat`
- `PlMsNr.dat`
- `PlPkBu.dat`

Ice Climbers are the main exception to the "one costume DAT equals one costume mod" mental model:

- `PlPpYy.dat` is Popo's costume DAT
- `PlNnYy.dat` is Nana's costume DAT
- one practical Ice Climbers pair usually needs both DATs together

For the paired-menu-asset side of that workflow, see [Ice Climbers Pairing](Ice-Climbers-Pairing.md).

In Nucleus terms, these are the files that should look like real costume archives with `Ply...` symbols and a known costume color.

## Character Data Files: `PlXx.dat`

These files belong to a character, but not to one specific costume slot in the same way.

They are often where character-wide effect or article data lives.

Examples from the repo's current knowledge:

- `PlFx.dat` for Fox laser and side-B-related data
- `PlFc.dat` for Falco laser and side-B-related data
- `PlMs.dat` for Marth sword trail data
- `PlPk.dat` for Pikachu thunder data

These are usually not imported through the costume-vault workflow.

## Effect Files: `Ef*.dat`

These files often own visual effects rather than the main character archive itself.

Examples:

- `EfFxData.dat` for Fox/Falco shared effects such as shine and up-B-related visuals
- `EfPkData.dat` for Pikachu/Pichu shared effect data
- `EfCaData.dat` for Captain Falcon effects

If an edit appears to affect multiple moves, multiple costumes, or even multiple characters, it is a good sign the real ownership is in an effect file rather than a costume DAT.

## Shared Character/Common Files

Some assets are not owned by one character at all.

Examples from the current notes:

- `PlCo.dat` for common character-side data
- `EfCoData.dat` for common/shared effects

These are where "why did this affect more than one thing?" questions often lead.

## UI And Menu Files

Not all modding lives in character or effect files.

The repo's notes also mention UI-oriented files like:

- `MnSlChr.usd` for menu-hand related visuals
- `GmPause.usd` for pause-screen visuals

That matters because not every color edit belongs to gameplay assets.

## Ownership Examples

Some concrete examples from the current repo knowledge:

- Fox laser is owned by `PlFx.dat`, so it is character-local.
- Falco laser is owned by `PlFc.dat`, so it is character-local.
- Fox/Falco shine and parts of up-B are in `EfFxData.dat`, so they are shared.
- Marth sword trail is in `PlMs.dat`, so it is tied to Marth's character data.
- Pikachu thunder support in the current extras config is stored through Pikachu ownership and shared with Pichu.

## Why Nucleus Cares

Nucleus uses ownership in a few different ways:

- costume import only accepts files that look like actual costume archives
- Ice Climbers costume import has to recognize a Popo/Nana pair instead of one standalone DAT
- extras target a specific `target_file` in the active project
- shared extras can be stored under one owner character while being used by multiple characters
- stage workflows are separate because stage ownership is not part of the costume-file model at all

## A Useful Rule Of Thumb

If you are asking "is this a skin," the likely owner is a costume archive.

If you are asking "why did this effect change globally," the likely owner is a character-data, effect-data, or common file.

If you are asking "why is this not importable as a costume," the likely answer is that the file does not look like a `PlXxYy` costume archive with `Ply` ownership.

## Related Pages

- [DAT File Structure](DAT-File-Structure.md)
- [Melee File Map](Melee-File-Map.md)
- [Character Mod Workflow](Character-Mod-Workflow.md)
- [Ice Climbers Pairing](Ice-Climbers-Pairing.md)
- [Extras And Effects Workflow](Extras-And-Effects-Workflow.md)
