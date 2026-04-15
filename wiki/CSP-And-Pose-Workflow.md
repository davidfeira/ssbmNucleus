# CSP And Pose Workflow

Nucleus has extra CSP tools on top of normal costume import.

## What The App Can Do

- generate a missing CSP on import from the default vanilla pose
- let you make and save custom poses in the app
- batch-generate CSPs for many costumes with a saved pose
- capture HD CSPs from either the default pose or a saved pose for [Texture Pack Mode](Texture-Pack-Mode.md)

## Missing CSPs On Import

When you import a costume ZIP:

- an included CSP can be reused
- if the ZIP is missing a CSP, Nucleus can generate one from the DAT
- that generated CSP uses the character's normal default pose workflow rather than requiring you to pose it first

This gives the costume a usable portrait immediately, even if the original mod archive did not include one.

## Custom Poses

A pose is a reusable scene setup for one character.

In practice, that means you can use the app to make your own CSP poses instead of being locked to the default one.

Saved poses are useful because:

- they can be reused across multiple costumes of the same character
- they give you a consistent portrait style across a whole costume set
- they can be used later for both normal CSP generation and HD CSP capture

When possible, Nucleus also generates a thumbnail for the saved pose so it is easy to pick again later.

## Batch Generation

Once you have a saved pose, you can use it to mass-generate CSPs for your costumes.

This is one of the strongest portrait workflows in the app:

- pick a saved pose
- select multiple skins for that character
- generate matching CSPs for the whole set

That is the easiest way to give a full costume library a consistent look without posing every skin from scratch.

## HD CSPs

Nucleus can also capture HD CSPs at a higher resolution.

The important distinction is:

- normal CSPs are the regular portrait assets the skin uses in the app
- HD CSPs are higher-resolution portrait images stored separately for HD-oriented workflows

You can generate HD CSPs from:

- the default vanilla pose
- a saved custom pose

That makes HD capture useful whether you want a cleaner version of the normal portrait or a full custom posed set.

## Texture Pack Mode

HD CSPs can also be generated for use with [Texture Pack Mode](Texture-Pack-Mode.md).

That workflow can use the HD portrait files instead of only relying on the normal in-project CSPs, which is what makes it useful for Dolphin texture-pack output.

## Ice Climbers Note

Ice Climbers are still the main exception.

Their portrait workflow is treated as a paired Popo/Nana portrait problem rather than two totally separate single-character portraits.

In practice, Nucleus handles the pairing automatically. You select Popo, and the app fills in the rest of the pair behavior for you.

The main current limitation is custom poses: they do not work properly for Ice Climbers yet, because their portrait setup is more complicated than a normal one-character pose workflow.

For that special case, see [Ice Climbers Pairing](Ice-Climbers-Pairing.md).

## Summary

A normal CSP is your skin's standard portrait.

A pose is a reusable recipe for making portraits.

An HD CSP is a higher-resolution version of that portrait workflow, mainly useful for HD presentation and texture-pack export.
