# CSP And Pose Workflow

Nucleus has extra CSP tools on top of normal costume import.

## What The App Can Do

- generate a missing CSP on import from the default vanilla pose
- let you make and save custom poses in the app
- batch-generate CSPs for many costumes with a saved pose
- retake a single costume's CSP with the active pose from its edit modal
- generate a matching stock icon from a recolored costume
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

## Retaking A Single CSP

A costume's edit modal has a **Retake CSP** button. It re-renders that one costume's portrait with the currently active pose and shows a preview before you confirm, so you can refresh a single skin without running a batch.

## Stock Icons

Recolored costumes can get a matching stock icon generated automatically. Nucleus measures how the costume's colors moved relative to the vanilla costume and applies the same movement to the vanilla stock icon's palette — so the icon follows the skin without anyone drawing pixel art. This runs at import for recolors, and the vault has a button to generate or regenerate a stock on demand.

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

HD CSPs are always rendered at 4x resolution, and they never go inside the ISO — they exist purely for Dolphin texture-pack output. The **Manage CSPs** view on a costume shows all of its portraits (normal, HD, and alternates) in one grid.

That makes HD capture useful whether you want a cleaner version of the normal portrait or a full custom posed set.

## Texture Pack Mode

HD CSPs can also be generated for use with [Texture Pack Mode](Texture-Pack-Mode.md).

That workflow can use the HD portrait files instead of only relying on the normal in-project CSPs, which is what makes it useful for Dolphin texture-pack output.

## Poses On The Install Page

Applying a pose from the install page regenerates **all** of that character's in-ISO portraits with the pose — including vanilla costumes and costumes that came from a patch — so the whole select-screen column ends up in a consistent style, not just your vault skins.

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
