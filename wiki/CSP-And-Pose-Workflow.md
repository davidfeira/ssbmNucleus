# CSP And Pose Workflow

Nucleus treats portraits as their own workflow, not just a side effect of costume import.

## CSPs In The Normal Costume Workflow

When a costume is imported:

- an included CSP can be reused
- a missing CSP can be generated from the DAT
- a normal CSP is stored both as a vault preview and inside the costume ZIP

That gives the costume a usable portrait immediately, even if the original archive did not include one.

Ice Climbers are the main exception to the "one DAT generates one portrait" rule:

- the pair uses one shared portrait workflow
- Nana does not need a separate CSP asset

## Stocks

Stock icons are closely related but separate from CSPs.

If the imported costume does not include a stock icon, Nucleus can fall back to the matching vanilla stock when available.

For Ice Climbers, the same rule applies to stocks: the pair should use one shared stock set rather than separate Nana stock assets.

## Editing CSPs

Normal CSP updates are treated as part of the costume package:

- the standalone preview file is updated
- the costume ZIP is updated so the CSP travels with the stored mod

HD CSPs are different. They are stored as standalone files rather than being written back into the costume ZIP.

## HD CSP Capture

The HD capture flow renders a higher-resolution CSP from the costume DAT at a chosen scale.

This is useful when the standard CSP is good enough for normal UI but you also want a cleaner source image for packaging, previews, or texture-pack-related workflows.

## Alternate CSPs

Nucleus also treats alternate CSPs as managed assets.

That means a skin can have:

- a main CSP
- alternate CSPs
- an active selection that chooses which portrait is currently in use

## Poses

Saved poses are reusable scene files for generating CSPs.

In the current workflow, a pose is a saved camera and scene setup rather than a property of one single skin.

That makes poses reusable across multiple costumes of the same character.

## What A Pose Save Contains

At a high level, a saved pose captures things like:

- animation symbol
- camera position and scale
- frame selection
- hidden node settings
- CSP-mode display settings

Pose files are stored as YAML scene files under the vanilla-assets area, because they act more like reusable templates than vault-specific skin files.

## Pose Thumbnails

When possible, Nucleus generates a thumbnail for the saved pose using vanilla costume and animation data.

That gives the pose library a preview image without tying the pose to a specific custom skin.

## Batch CSP Generation

One of the strongest workflows here is using a saved pose to batch-generate CSPs for multiple skins.

That turns a reusable pose scene into a consistent portrait set across a whole character's library.

## Good Mental Model

A CSP is a portrait asset for a skin.

A pose is a reusable scene recipe for generating portraits.

For Ice Climbers, the portrait asset is usually best thought of as a **pair portrait** rather than two unrelated single-character portraits.

See [Ice Climbers Pairing](Ice-Climbers-Pairing.md).
