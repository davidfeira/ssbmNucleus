# Changelog

All notable changes to SSBM Nucleus are documented here.

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
