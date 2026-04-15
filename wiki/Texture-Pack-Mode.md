# Texture Pack Mode

Texture-pack mode is the export path you use when you want **HD character portraits in Dolphin**, not just a normal playable ISO.

The important practical detail is that this is mainly a **CSP pipeline**. It is not a general-purpose "turn the whole build into a texture pack" system.

## What It Is For

Normal ISO export writes the current project into a playable build.

Texture-pack mode goes a step further:

- it still exports the ISO
- it also helps build a Dolphin texture-pack folder for the build's portraits

Use it when you want the build to keep normal in-game behavior but show higher-resolution CSS portraits through Dolphin's texture loading.

## The Actual Flow

The real user flow is:

1. export the current project with texture-pack mode enabled
2. Nucleus temporarily swaps the project's portrait files with small placeholders just for the export
3. Nucleus restores the normal project portraits after export, so the project itself is not left in that placeholder state
4. open the exported ISO in Slippi Dolphin
5. scroll through the costumes on the character select screen
6. as Dolphin dumps those placeholder portraits, Nucleus matches them back to the correct costumes
7. Nucleus writes the real portrait images into Dolphin's load folder
8. when you are done matching costumes, stop listening and keep the generated texture-pack folder

So the mode is really:

- export an ISO
- let Dolphin reveal which portrait texture belongs to which costume
- replace those dumped placeholders with the real images

## Where The Real Portraits Come From

Texture-pack mode uses the portrait files Nucleus already knows about.

In practice, that means:

- if a costume has an HD CSP, Nucleus can use that
- otherwise it can fall back to the normal CSP

That is why this mode pairs naturally with the portrait tools on [CSP And Pose Workflow](CSP-And-Pose-Workflow.md).

## The Main Tradeoff

This workflow is powerful, but it is also kind of annoying.

The slow part is that you still have to scroll through the costumes yourself so Nucleus can see each dumped placeholder and learn the correct Dolphin load filename for that portrait.

So the more costumes you have, the more this process pays off, but also the more manual it feels.

That is why texture-pack mode makes the most sense for:

- finished builds
- large costume libraries
- situations where the extra portrait quality is actually worth the setup time

This may get automated later, but right now the registration step is still manual.

## Quick Exports Vs Finished Builds

If you just want to test a few skins, do a quick build, or check whether something basically works, normal ISO export is usually better.

In that case, use [CSP Compression](CSP-Compression.md) instead.

That path just downsizes the portraits a bit so the build stays lighter in memory, which is much less work than running the full texture-pack flow.

Texture-pack mode is the nicer-looking option, but it is usually only worth the extra effort once the build is more finished.

## What You Get At The End

The result is not just an ISO.

You end up with:

- the exported ISO
- a build-specific portrait texture-pack folder under Dolphin's `Load/Textures/GALE01` path

That folder is what lets Dolphin show the higher-resolution portraits for the build.

## Related Pages

- [CSP And Pose Workflow](CSP-And-Pose-Workflow.md)
- [CSP Compression](CSP-Compression.md)
- [Character Mod Workflow](Character-Mod-Workflow.md)
