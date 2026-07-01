# Sound Mods

Nucleus handles two kinds of audio modding: **character sound packs** (voice/effect banks) and **stage song packs** (music playlists for DAS stages).

Both follow the vault-vs-project pattern: packs live in the vault, and installing writes into the open project.

## Character Sound Packs

Every character has a sound bank (their voice lines and sound effects). Nucleus lets you keep multiple packs per character and swap them.

From a character's sound-bank browser you can:

- create a new pack (it starts as a copy of the vanilla bank)
- browse every sound in the bank and **preview** it
- **replace** any individual sound with an audio file — normal formats are converted automatically
- **revert** one sound, or all of them, back to the pristine originals
- rename and delete packs
- **install** a pack into the open project, or **uninstall** back to the character's original sounds

A pack stays lossless where you have not touched it: unreplaced sounds keep their original game audio untouched.

### Notes

- Zelda and Sheik share one sound bank — a pack for one is a pack for both.
- Custom characters have sound banks too, browsable from their detail view.

## Stage Song Packs

Each DAS stage can carry a music playlist. A song pack is a per-stage set of tracks:

- add songs in normal audio formats — they are converted to the game's HPS format automatically (stereo preserved)
- reorder, rename, preview, and remove tracks
- install the pack to make it the stage's playlist in the open project
- uninstall to restore the stage's vanilla music

The playlist plays across the stage's variants; it is independent of which stage skin is loaded.

## What Ships In A Build

Installed sound packs and song packs are part of the project, so they ride along in ISO exports, patches, and bundles like any other installed mod.

## Related Pages

- [Custom Characters](Custom-Characters.md)
- [Stage Mod Workflow](Stage-Mod-Workflow.md)
- [Vault Vs Project](Vault-Vs-Project.md)
