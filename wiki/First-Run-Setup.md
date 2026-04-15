# First-Run Setup

This is the workflow that creates Nucleus's baseline data from a clean Melee ISO.

## What It Needs

Nucleus expects a vanilla Melee 1.02 ISO. That baseline is important because later workflows depend on known-good vanilla files for comparison, fallback assets, CSP generation, and restoration.

## How Nucleus Verifies The ISO

In the current setup flow, Nucleus tries auto-detect first and still allows manual browse as a fallback.

At a high level, the detection flow is:

1. Nucleus checks the default Slippi Dolphin folders under `AppData/Roaming/Slippi Launcher`
2. if present, it reads `User/Config/Dolphin.ini`
3. it collects configured ISO locations from Dolphin's settings
4. it also checks nearby Slippi folders as a fallback
5. it looks for `.iso` and `.gcm` candidates and gives common vanilla-style names like `GALE01`, `vanilla`, and `Melee` higher priority
6. the backend hashes candidate files and compares them against the known vanilla Melee 1.02 MD5
7. setup only continues if the hash matches

If auto-detect misses, you can still browse to the ISO manually.

So the "is this really a vanilla 1.02 ISO?" check is hash-based, not filename-based.

## What Setup Produces

The first-run process is not importing your mods. It is extracting and seeding the app's own reference data.

At a high level, setup prepares:

- vanilla character assets
- vanilla stage assets
- stock icons and stage icons
- AJ animation archives used by viewers and CSP generation
- supporting `csp_data` files used for CSP workflows

## Why It Matters Later

A lot of later features silently rely on setup having happened already:

- missing stocks can fall back to vanilla assets
- CSP generation has the vanilla data it needs
- pose thumbnails can be rendered against vanilla costume and animation files
- stage and UI previews have a stable source of baseline assets
