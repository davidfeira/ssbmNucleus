# Skin Creator

The Skin Creator is the in-app editor for making your own costume: open a skin, paint on it, recolor it, watch the changes on the live 3D model, and save the result as a new vault skin.

## Opening A Costume

The Skin Creator opens from the vault. You can start from:

- any vault skin (there is also an "edit this skin" path from a costume's detail view)
- a vanilla costume, as a clean base

The costume loads into a live 3D viewport with its full texture list alongside.

## The 3D Preview

The viewport is a real render of the actual DAT:

- rotate, zoom, and pan the camera
- changes you make to textures show up on the model immediately
- load the character's real animations and scrub frames to see the skin in motion

## Painting And Textures

Each texture in the DAT can be edited directly:

- paint on the texture canvas with the built-in tools (with undo/redo)
- **export** any texture as PNG to edit in an external editor
- **import** a PNG back onto a texture — it is resized to the texture's native size automatically

Costume DATs hide some textures in animation swaps (eye blink frames, for example); the Skin Creator exposes those too, so recolors do not miss the closed-eye frames.

## The Color Palette Tool

The recolor tool clusters every texture's pixels into color groups, then lets you shift each group's hue and saturation as one unit.

Lightness is left untouched, so shading, folds, and seams survive the recolor. This is the fast path from "red Falcon" to "green Falcon" without repainting anything.

One caveat: details that share a hue with the thing you are shifting (eyes matching a jacket, say) move together. For surgical edits, export the texture and edit the pixels directly.

## Saving

Saving exports the edited DAT and sends it through the normal import intake as a **new** vault skin:

- CSP and stock previews are generated automatically
- Slippi validation runs, exactly like a hand-imported skin
- the original costume you started from is untouched

Skins made for a custom character save into that character's skin list instead.

## Related Pages

- [Character Mod Workflow](Character-Mod-Workflow.md)
- [CSP And Pose Workflow](CSP-And-Pose-Workflow.md)
- [Slippi Safety](Slippi-Safety.md)
