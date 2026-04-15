# One-Click Imports

One-click import is the website-driven version of manual import.

## What It Is

The app registers a `nucleus://` protocol.

A link using that protocol can open Nucleus, download a ZIP from a URL, and send it through the normal import flow.

On the website, this is the flow behind the **Add to Nucleus** button.

## What Happens When You Open One

At a high level, the flow is:

1. Nucleus opens or focuses the app.
2. The link provides a download URL and can also provide a filename and title.
3. Nucleus downloads the ZIP.
4. The ZIP goes through the same import pipeline used by manual import.
5. If needed, the normal Slippi safety dialog still appears.
6. On success, the imported item is added to the vault.

So the one-click part is just the handoff. It does not bypass the normal scan or validation steps.

## How The Server Side Works

If a site says it supports one-click install for Nucleus, what it is really doing is packaging or hosting a ZIP in the format Nucleus already expects.

The mod format is still just a normal supported archive. The link is only what tells Nucleus where to get it.

## Texture Pack Note

Texture-pack mode is a separate export workflow.

There is not a documented combined "patch plus texture pack" bundle format in the current repo. If that gets added later, it should be documented as its own distribution format.

## Related Pages

- [Manual Import](Manual-Import.md)
- [Patches](Patches.md)
- [Texture Pack Mode](Texture-Pack-Mode.md)
