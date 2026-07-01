# Changelog

All notable changes to SSBM Nucleus are documented here.

## Unreleased

### 🐛 Fixes
- **The character page's "Available to Import" list now matches the vault's
  order.** Costumes you filed into a folder (e.g. an "Animelee" folder) were
  grouped together in the vault but showed up scattered in raw import-order on
  the character page, so the two screens disagreed. The import list now orders
  costumes exactly like the vault — folder members grouped where the folder
  sits — just as a flat list, without the folder headers. Ordering only; no
  costumes are added, removed, or changed on disk.

### ⚙️ Internal
- **Vault storage moved to SQLite.** The vault index (costumes, stages, custom
  content, bundles) can now be stored in a SQLite database (`storage/vault.db`)
  instead of the single `storage/metadata.json` blob. Shipped builds default to
  the DB backend; it's migrated automatically from `metadata.json` on first
  launch with a backup and a round-trip-validation check (and falls back to JSON
  if anything looks wrong). `metadata.json` is kept in sync as a live backup and
  remains the portable format for vault backups/exports. Lays the groundwork to
  eliminate list-position ordering bugs and makes concurrent writes safe across
  processes. Set `NUCLEUS_VAULT_DB=0` to stay on JSON. See
  `docs/VAULT_SQLITE_MIGRATION.md`.
- Added a backend pytest suite + GitHub Actions CI that runs it.

## 0.4.2

### 🐛 Fixes
- **Character select portraits render alt costumes correctly.** Recolor/alt
  costumes were drawn with the default costume's low-poly mask, so accessories
  vanished or low-poly geometry poked through — Pikachu's blue/green hats were
  missing and the red cap showed an artifact, Pichu's backpack/cheeks were wrong,
  and Peach's Daisy sleeves were blocky. Each costume now uses its own visibility
  data. Regenerate CSPs to refresh existing portraits.
- **Jigglypuff's costume hats now show up in portraits.** Hats that ship as a
  separate model are spliced into the render and follow the posed head.
- **Merging a vault backup no longer corrupts custom characters you already have.**
  A conflicting item is now kept entirely as-is — the backup's copy of it (and any
  stray extra files) is skipped — instead of leaking files into your version. The
  merge also shows a report of what was added vs. kept.

### 🚀 Improvements
- **Vault restore now shows live progress.** Importing a vault backup displays an
  upload bar and then a per-file extract/merge status instead of an indefinite
  wait with no feedback.
- CSP rendering uses two-sided lighting so back-facing surfaces no longer go dark.

### 🔧 Changes
- Stages imported without a bundled screenshot no longer boot Dolphin to capture
  one during import. Use the bulk DAS "capture screenshots" flow instead.

## 0.4.1

### 🐛 Fixes
- **Ice Climbers no longer crash in Classic mode and online.** Nana's intro/result
  demo animations were exported empty, which made her T-pose on the VS banner and
  crash the game when starting a 1P or netplay match. Existing projects are repaired
  automatically on the next export.
- **Imported Jigglypuff costumes no longer crash the game.** The importer grabbed
  Jigglypuff's hat model (1 joint) instead of the body (50 joints), which crashed on
  load. Re-import affected Puff skins to fix existing ones.

## 0.4.0

The big update is finally here.

### ✨ New features
- **In-app updater** — future versions update from inside the app (Settings → Updates)
- **In-game testing** — test skins in game directly from the app
- **Stage screenshots** — capture clean in-game previews for stages
- **Custom characters & stages** — import, manage, and install them
- **Menu mods** — CSS + grid editor, SSS + grid editor, and HUD
- **Game banner editing**
- **Sound mods & stage music**
- **ISO scan** — pull every skin / stage / custom character / custom stage from any
  ISO into your vault (skips what you already have)
- **Start a project from a vanilla Melee patch** in your vault (Animelee, etc.)
- **Pose manager** improvements
- **Experimental stock-icon generator** (still janky)

### 🚀 Improvements
- Better loading screens and feedback
- Faster batch skin installation
- Better mod importing & project management
- **Exporting**: improved CSP compression, automated texture-pack scanning, and
  create/launch xdelta patches inside the app

### 🐛 Bug fixes
- Pokémon Stadium should finally be fixed
- Ice Climbers fixes
- Red Falcon fixes
- Kirby and Game & Watch actually work now

### ⚠️ Known issues
- Non-default Captain Falcon skins desync
- Extras still need work

### 🔜 Coming next
Trailer · guide · more bug fixes · better console support · website improvements ·
more mod-creation tools · and more :)

**Download:** https://ssbmnucleus.net/download
