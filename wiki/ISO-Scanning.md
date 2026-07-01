# ISO Scanning

ISO scanning rips mod content **out of** existing ISOs and into your vault. If you have old modded builds lying around, this is how you recover their skins without the original ZIPs.

## Costume Scanning

The main scan takes one or more ISOs (`.iso` / `.gcm`; NKit images are not supported) and finds costume skins:

1. drop ISOs on the import button, or use **Scan ISOs** in the characters view
2. Nucleus extracts each ISO and hashes every character costume file
3. anything that matches vanilla Melee or a skin already in your vault is skipped — only **new** skins surface
4. each candidate gets Slippi validation and a rendered CSP preview
5. you pick which candidates to keep from a per-character selection grid
6. selected skins import into the vault like any other costume

Scans run in the background with progress streaming, and you can cancel mid-scan.

## Deduplication Is Live

The "is this new?" check is recomputed against your current vault every scan. If you delete a skin from the vault, a later scan of the same ISO will offer it again — nothing is permanently remembered as "already imported."

## DAS Variant Scanning

The stage side has its own scan: Nucleus can pull **stage variants** out of a modded ISO — both m-ex DAS folders and 20XX-style alternate stage files — and offer them as importable variants for the six DAS stages.

## Custom Content Scanning

Custom characters and custom stages have separate scan flows in their own vault sections, for extracting m-ex fighters and stages out of a modded build. See [Custom Characters](Custom-Characters.md) and [Custom Stages](Custom-Stages.md).

## Requirements

ISO extraction uses Wiimms ISO Tools, which ships with Nucleus — no separate install.

## Related Pages

- [Manual Import](Manual-Import.md)
- [Custom Characters](Custom-Characters.md)
- [Custom Stages](Custom-Stages.md)
- [Stage Mod Workflow](Stage-Mod-Workflow.md)
