# Fox And Falco Shared Extras

Fox and Falco are the clearest example of why some extras are marked as shared and some are not.

The short version is:

- if the effect lives in `EfFxData.dat`, it is shared
- if the effect lives in `PlFx.dat` or `PlFc.dat`, it is not shared

That is the main reason the app presents some Fox/Falco extras as shared.

## Why Some Are Shared

Fox and Falco both use `EfFxData.dat` for some effect families.

So when an extra patches that file, it is not really making a separate Fox-only version and Falco-only version. It is changing one shared effect file that both characters use.

That is why the app marks those extras as shared.

## Why Some Are Not Shared

Other Fox/Falco effects live in their own character files:

- `PlFx.dat` for Fox
- `PlFc.dat` for Falco

When an extra patches those files, Fox and Falco can each have their own separate version of the effect.

That is why those extras are not marked as shared.

## Current Split

Not shared:

- laser
- side-B
- gun model

Those are character-local because they live in `PlFx.dat` or `PlFc.dat`.

Shared:

- shine
- up-B color
- up-B fire texture
- laser ring

Those are shared because they use `EfFxData.dat`.

## Practical Rule

If you are looking at a Fox/Falco extra and wondering whether it should be shared, the question is usually just:

- does it patch `EfFxData.dat`?

If yes, shared makes sense.

If it patches `PlFx.dat` or `PlFc.dat`, it usually should not be shared.

## Good Mental Model

The app is not being arbitrary here.

Some Fox/Falco effects are shared because the underlying Melee file is shared.

Some are not shared because the underlying Melee file is character-specific.

## Related Pages

- [Extras And Effects Workflow](Extras-And-Effects-Workflow.md)
- [Character Files And Ownership](Character-Files-And-Ownership.md)
- [Color And Effect Modding](Color-And-Effect-Modding.md)
