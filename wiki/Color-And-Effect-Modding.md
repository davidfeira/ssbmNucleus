# Color And Effect Modding

This is the best-documented modding area in the repo today.

## What The Existing Research Covers

The current research material is strongest on character effect colors and effect-related offsets. The raw notes cover:

- Fox and Falco laser-related edits
- shine and other shared effect edits in `EfFxData.dat`
- sword trail work for sword characters
- assorted effect blocks for other characters and menu visuals

## Common Patterns

The existing notes repeatedly call out a few recurring structures:

- `98 00` blocks tied to RGBY-style matrices
- `42 48` blocks tied to RGBA or material-like color data
- `07 07 07` style data blocks
- `CF` and `DF` effect blocks

These patterns matter because a lot of DAT editing is less about named fields and more about learning which byte layouts reliably correspond to visible color behavior.

## Typical Workflow

The documented workflow is still fairly manual:

1. find a known mod that changes the same effect
2. diff the edited DAT against vanilla
3. identify the bytes or blocks that moved
4. test in-game and verify whether the effect is character-local or shared

The notes also reference tooling like HxD, Dolphin dumps, and other Melee tools for inspecting the results.

## Important Caveat

Effect and gameplay edits are not equally safe. Some categories of edits can desync netplay or trip Slippi validation, so visual changes should be kept separate from assumptions about gameplay safety.

## Source Material

- [smashboards_offsets_reference.md](../docs/color-effects-reference/smashboards_offsets_reference.md)
- [extras_expansion_notes.md](../docs/color-effects-reference/extras_expansion_notes.md)
- [smashboards_thread_extracted.txt](../docs/color-effects-reference/smashboards_thread_extracted.txt)
- [melee_color_offsets.json](../docs/color-effects-reference/melee_color_offsets.json)
