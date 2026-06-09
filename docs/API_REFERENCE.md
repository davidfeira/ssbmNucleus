# API Reference

Complete documentation of all Flask backend endpoints.

## Overview

- **Base URL**: `http://localhost:5000` (port is dynamic — the backend prefers 5000 but falls back to a free OS-assigned port; Electron reads the actual port at startup)
- **Response Format**: JSON with `{ success: boolean, ... }`
- **Async Operations**: WebSocket events for progress (export, import, setup, ISO scan, in-game testing)
- **File Uploads**: Multipart form data

---

## Blueprint Summary

| Blueprint | Purpose | Endpoints |
|-----------|---------|-----------|
| project_bp | MEX project management | 14 |
| assets_bp | File serving (images, assets) | 5 |
| costumes_bp | Import/remove/reorder in MEX | 3 |
| export_bp | ISO export with progress | 2 |
| storage_costumes_bp | Vault costume operations | 18 |
| storage_stages_bp | Stage vault operations | 7 |
| vault_backup_bp | Backup/restore storage | 5 |
| mod_export_bp | Export as ZIP mods | 3 |
| import_bp | Unified import (auto-detect) | 1 |
| das_bp | Dynamic Alternate Stages | 8 |
| poses_bp | CSP pose management | 5 |
| setup_bp | First-run setup | 4 |
| slippi_bp | Dolphin/texture packs | 10 |
| xdelta_bp | Binary patches | 11 |
| bundles_bp | .ssbm mod bundles | 10 |
| viewer_bp | 3D model preview | 9 |
| settings_bp | Settings (placeholder, no routes) | 0 |
| iso_scan_bp | Rip costumes from ISOs | 7 |
| menus_bp | CSS/SSS menu mods | 31 |
| custom_stages_bp | Custom (m-ex) stages | 16 |
| custom_characters_bp | Custom (m-ex) fighters | 12 |
| test_in_game_bp | In-game test harness | 8 |
| extras_bp | Character effects (extras) | 12 |

---

## Project Blueprint

### GET /api/mex/status
Get current MEX project status.

**Response:**
```json
{
  "success": true,
  "connected": true,
  "projectLoaded": true,
  "project": { "name": "MyMod", "path": "/path/to/project" },
  "counts": { "fighters": 26, "stages": 29 }
}
```

### POST /api/mex/project/open
Open existing MEX project.

**Body:**
```json
{ "projectPath": "/path/to/project.mexproj" }
```

### GET /api/mex/project/list
List all app-managed MEX projects (with which one is currently open).

### POST /api/mex/project/close
Close the currently loaded MEX project without deleting it.

### POST /api/mex/project/create
Create new MEX project from vanilla ISO.

**Body:**
```json
{
  "isoPath": "/path/to/vanilla.iso",
  "projectDir": "/path/to/output",
  "projectName": "MyMod"
}
```

### POST /api/mex/project/delete
Delete an app-managed MEX project directory.

**Body:**
```json
{ "projectPath": "/path/to/project" }
```

### GET /api/mex/project/build
Get disc-banner metadata (title/creator/description) and banner image preview.

### POST /api/mex/project/build
Set disc-banner fields and (optionally) the 96x32 banner image.

**Body:** any of `shortName`, `longName`, `shortMaker`, `longMaker`, `description`, `bannerPngBase64`.

### GET /api/mex/fighters
List all fighters in project.

**Response:**
```json
{
  "success": true,
  "fighters": ["Mario", "Fox", "C. Falcon", ...]
}
```

### GET /api/mex/fighters/{fighter_name}/costumes
Get costumes for specific fighter.

**Response:**
```json
{
  "success": true,
  "fighter": "Fox",
  "costumes": [
    { "index": 0, "code": "PlFxNr", "cspUrl": "/assets/...", "stockUrl": "/assets/..." },
    ...
  ]
}
```

### GET /api/mex/fighters/{fighter_name}/team-colors
Get team color costume indices.

**Response:**
```json
{
  "success": true,
  "fighter": "Fox",
  "red": 1,
  "blue": 2,
  "green": 3
}
```

### POST /api/mex/fighters/{fighter_name}/team-colors
Set team color index.

**Body:**
```json
{ "color": "red", "costumeIndex": 5 }
```

### GET /api/mex/recommended-compression
Get recommended CSP compression ratio.

**Response:**
```json
{
  "success": true,
  "totalCostumes": 156,
  "vanillaCostumes": 128,
  "addedCostumes": 28,
  "ratio": 0.8
}
```

### POST /api/mex/shutdown
Gracefully shutdown Flask server.

---

## Costumes Blueprint

### POST /api/mex/import
Import costume to MEX project.

**Body:**
```json
{
  "fighter": "Fox",
  "costumePath": "/path/to/costume/folder"
}
```

### POST /api/mex/remove
Remove costume from project.

**Body:**
```json
{
  "fighter": "Fox",
  "costumeIndex": 5
}
```

### POST /api/mex/reorder
Reorder costume slots.

**Body:**
```json
{
  "fighter": "Fox",
  "fromIndex": 3,
  "toIndex": 1
}
```

---

## Export Blueprint

### POST /api/mex/export/start
Start ISO export (async).

**Body:**
```json
{
  "filename": "MyMod.iso",
  "cspCompression": 0.8,
  "useColorSmash": true,
  "texturePackMode": false,
  "slippiDolphinPath": "/path/to/slippi"
}
```

**WebSocket Events:**
- `export_progress` - `{ stage, progress, message }`
- `export_complete` - `{ success, filename, path }`
- `export_error` - `{ error }`

### GET /api/mex/export/download/{filename}
Download exported ISO (auto-deleted after download).

---

## Storage Costumes Blueprint

### GET /api/mex/storage/metadata
Get the storage vault `metadata.json` (all characters/stages/custom content).

### GET /api/mex/storage/costumes
List all costumes in vault.

**Query:** `?character=Fox` (optional filter)

**Response:**
```json
{
  "success": true,
  "costumes": {
    "Fox": {
      "skins": [
        {
          "id": "abc123",
          "color": "Green Fox",
          "costumeCode": "PlFxGr",
          "cspUrl": "/storage/Fox/abc123/csp.png",
          "stockUrl": "/storage/Fox/abc123/stock.png",
          "slippiSafe": true
        }
      ],
      "folders": []
    }
  }
}
```

### POST /api/mex/storage/costumes/delete
Delete costume from vault.

**Body:**
```json
{ "character": "Fox", "skinId": "abc123" }
```

### POST /api/mex/storage/costumes/rename
Rename costume.

**Body:**
```json
{ "character": "Fox", "skinId": "abc123", "newName": "Cool Fox" }
```

### POST /api/mex/storage/costumes/update-csp
Update CSP image (multipart form).

**Form Data:**
- `character`: "Fox"
- `skinId`: "abc123"
- `csp`: (file)
- `isHd`: "true" (optional)

### POST /api/mex/storage/costumes/{character}/{skin_id}/csp/capture-hd
Generate HD CSP at specified scale.

**Body:**
```json
{ "scale": 4 }
```

### POST /api/mex/storage/costumes/{character}/{skin_id}/csp/manage
Manage CSPs (swap, remove, add, regenerate).

**Body (varies by action):**
```json
{ "action": "swap", "altId": 2 }
{ "action": "reset" }
{ "action": "remove", "target": "alt", "altId": 1 }
{ "action": "regenerate-hd", "scale": 4 }
```

### POST /api/mex/storage/costumes/update-stock
Update stock icon (multipart form).

### POST /api/mex/storage/costumes/retest-slippi
Retest for Slippi safety.

**Body:**
```json
{ "character": "Fox", "skinId": "abc123", "autoFix": true }
```

### POST /api/mex/storage/costumes/override-slippi
Manually override Slippi status.

**Body:**
```json
{ "character": "Fox", "skinId": "abc123", "slippiSafe": true }
```

### POST /api/mex/storage/costumes/reorder
Reorder skins in vault.

**Body:**
```json
{ "character": "Fox", "fromIndex": 0, "toIndex": 3 }
```

### POST /api/mex/storage/costumes/move-to-top
Move skin to top of list.

**Body:**
```json
{ "character": "Fox", "skinId": "abc123" }
```

### POST /api/mex/storage/costumes/move-to-bottom
Move skin to bottom of list.

### POST /api/mex/storage/folders/create
Create folder for organizing skins.

**Body:**
```json
{ "character": "Fox", "name": "Tournament Skins" }
```

### POST /api/mex/storage/folders/rename
Rename folder.

**Body:**
```json
{ "character": "Fox", "folderId": "folder123", "newName": "New Name" }
```

### POST /api/mex/storage/folders/delete
Delete folder (skins moved to root).

### POST /api/mex/storage/folders/toggle
Toggle folder expanded/collapsed state.

### POST /api/mex/storage/skins/set-folder
Assign skin to folder.

**Body:**
```json
{ "character": "Fox", "skinId": "abc123", "folderId": "folder123" }
```

---

## Storage Stages Blueprint

### POST /api/mex/storage/stages/delete
Delete stage variant.

**Body:**
```json
{ "stageFolder": "Battlefield", "variantId": "abc123" }
```

### POST /api/mex/storage/stages/rename
Rename stage variant.

**Body:**
```json
{ "stageFolder": "Battlefield", "variantId": "abc123", "newName": "Night BF" }
```

### POST /api/mex/storage/stages/update-screenshot
Update screenshot (multipart form).

**Form Data:**
- `stageFolder`: "Battlefield"
- `variantId`: "abc123"
- `screenshot`: (file)

### POST /api/mex/storage/stages/set-slippi
Set Slippi safety status.

**Body:**
```json
{ "stageName": "Battlefield", "variantId": "abc123", "slippiSafe": true }
```

### POST /api/mex/storage/stages/reorder
Reorder variants.

### POST /api/mex/storage/stages/move-to-top
Move variant to top.

### POST /api/mex/storage/stages/move-to-bottom
Move variant to bottom.

---

## Import Blueprint

### POST /api/mex/import/file
Unified import endpoint (auto-detects content type).

**Form Data:**
- `file`: ZIP or 7z file
- `slippi_action`: "fix" | "import_as_is" (optional, for retry)
- `custom_title`: Custom name (optional)

**Response (character):**
```json
{
  "success": true,
  "type": "character",
  "character": "Fox",
  "imported": [{ "id": "abc123", "name": "Cool Fox", "slippi_safe": true }]
}
```

**Response (Slippi dialog):**
```json
{
  "success": true,
  "type": "slippi_dialog",
  "message": "This costume is not Slippi safe. Choose an action:",
  "costumes": [{ "path": "...", "character": "Fox", "color": "Green" }]
}
```

---

## Mod Export Blueprint

### POST /api/mex/storage/costumes/export
Export costume as ZIP.

**Body:**
```json
{ "character": "Fox", "skinId": "abc123", "colorName": "Green Fox" }
```

### POST /api/mex/storage/stages/export
Export stage as ZIP.

**Body:**
```json
{
  "stageCode": "GrBf",
  "stageName": "Battlefield",
  "variantId": "abc123",
  "variantName": "Night BF"
}
```

### GET /api/mex/export/mod/{filename}
Download exported mod ZIP.

---

## DAS Blueprint (Dynamic Alternate Stages)

### GET /api/mex/das/status
Check if DAS framework is installed.

**Response:**
```json
{
  "success": true,
  "installed": true,
  "installedStages": 6,
  "totalStages": 29
}
```

### POST /api/mex/das/install
Install DAS framework to project.

### GET /api/mex/das/stages
List all DAS-supported stages.

### GET /api/mex/das/stages/{stage_code}/variants
Get variants for specific stage.

### GET /api/mex/das/storage/variants
List variants in storage.

**Query:** `?stage=GrBf` (optional filter)

### POST /api/mex/das/import
Import DAS variant to project.

**Body:**
```json
{ "stageCode": "GrBf", "variantPath": "/path/to/variant" }
```

### POST /api/mex/das/remove
Remove DAS variant from project.

### POST /api/mex/das/rename
Rename DAS variant file.

---

## Poses Blueprint

### POST /api/mex/storage/poses/save
Save pose scene for CSP generation.

**Body:**
```json
{
  "character": "Fox",
  "poseName": "Action Pose",
  "sceneData": { /* YAML scene data */ }
}
```

### GET /api/mex/storage/poses/list/{character}
List saved poses.

### GET /storage/poses/{character}/{filename}
Serve pose thumbnail image.

### POST /api/mex/storage/poses/delete
Delete saved pose.

### POST /api/mex/storage/poses/batch-generate-csp
Generate CSPs for multiple skins using a pose.

**Body:**
```json
{
  "character": "Fox",
  "poseName": "Action Pose",
  "skinIds": ["abc123", "def456"],
  "hdResolution": 4
}
```

---

## Setup Blueprint

### GET /api/mex/setup/status
Check if first-run setup is needed.

**Response:**
```json
{
  "success": true,
  "complete": false,
  "reason": "missing_vanilla_assets",
  "details": "Run setup with vanilla ISO"
}
```

### POST /api/mex/setup/start
Start first-run setup.

**Body:**
```json
{ "isoPath": "/path/to/vanilla.iso" }
```

**WebSocket Events:**
- `setup_progress` - `{ stage, progress, message }`
- `setup_complete` - `{ success }`
- `setup_error` - `{ error }`

### GET /api/mex/setup/auto-detect
Auto-detect Slippi path and ISO.

**Response:**
```json
{
  "success": true,
  "slippiPath": "/path/to/slippi",
  "isoPath": "/path/to/melee.iso",
  "isoFolderPath": "/path/to/iso/folder"
}
```

### POST /api/mex/verify-iso
Verify ISO is vanilla NTSC 1.02.

**Body:**
```json
{ "isoPath": "/path/to/melee.iso" }
```

**Response:**
```json
{
  "success": true,
  "valid": true,
  "md5": "0e63d4223b01d9aba596259dc155a174",
  "expected": "0e63d4223b01d9aba596259dc155a174"
}
```

---

## Vault Backup Blueprint

### GET /api/mex/storage/stats
Get storage vault statistics (sizes, counts).

### POST /api/mex/storage/backup
Create backup ZIP of entire storage.

**Response:**
```json
{
  "success": true,
  "filename": "vault_backup_20240115.zip",
  "size": 52428800,
  "path": "/path/to/backup.zip"
}
```

### GET /api/mex/storage/backup/download/{filename}
Download backup file.

### POST /api/mex/storage/restore
Restore from backup (multipart form).

**Form Data:**
- `file`: ZIP backup
- `mode`: "replace" | "merge"

### POST /api/mex/storage/clear
Clear storage.

**Body:**
```json
{ "clearIntake": true, "clearLogs": true }
```

---

## Slippi Blueprint

### POST /api/mex/settings/slippi-path/verify
Verify Slippi Dolphin path.

**Body:**
```json
{ "slippiPath": "/path/to/slippi" }
```

### GET /api/dolphin/iso-folder
Get ISO folder from Dolphin.ini.

**Query:** `?slippiPath=/path/to/slippi`

### GET /api/mex/texture-pack/stats
Get texture pack folder statistics.

**Query:** `?slippiPath=/path/to/slippi`

### POST /api/mex/texture-pack/clear
Clear texture pack folder.

### POST /api/mex/texture-pack/start-listening
Start watching for dumped textures.

**Body:**
```json
{ "buildId": "build123", "slippiPath": "/path/to/slippi" }
```

**WebSocket Events:**
- `texture_matched` - `{ character, costumeIndex, skinId, filename }`
- `texture_progress` - `{ matched, total, percentage }`

### POST /api/mex/texture-pack/stop-listening
Stop watching and finalize.

### POST /api/mex/texture-pack/apply-offline
Apply a build's texture pack from a harvested index→filename table — no ISO boot, no CSS scrolling. Copies each real CSP into Dolphin's `Load/` folder under the precomputed filename.

### POST /api/mex/texture-pack/auto-apply
Fully automatic texture pack naming using a managed, build-independent index→filename table (no Dolphin launch at all).

### GET|POST /api/dolphin/texture-settings
Read or update Dolphin texture settings.

### GET /api/mex/texture-pack/status
Get texture watcher status.

---

## XDelta Blueprint

### GET /api/mex/xdelta/list
List all xdelta patches.

### POST /api/mex/xdelta/import
Import xdelta patch (multipart form).

**Form Data:**
- `file`: .xdelta file
- `name`: Patch name
- `description`: Description
- `image`: Preview image (optional)

### POST /api/mex/xdelta/update/{patch_id}
Update patch metadata.

### POST /api/mex/xdelta/update-image/{patch_id}
Update patch image.

### POST /api/mex/xdelta/delete/{patch_id}
Delete patch.

### POST /api/mex/xdelta/build/{patch_id}
Build ISO from xdelta patch.

**Body:**
```json
{ "vanillaIsoPath": "/path/to/vanilla.iso" }
```

**WebSocket Events:**
- `xdelta_progress`, `xdelta_complete`, `xdelta_error`

### POST /api/mex/xdelta/play/{patch_id}
Build the patch's ISO (if missing) and launch it in the user's real Slippi Dolphin.

**Body:**
```json
{ "slippiPath": "/path/to/slippi", "vanillaIsoPath": "/path/to/vanilla.iso" }
```

### GET /api/mex/xdelta/download/{filename}
Download built ISO.

### POST /api/mex/xdelta/create
Create xdelta patch from modded ISO.

**Body:**
```json
{
  "vanillaIsoPath": "/path/to/vanilla.iso",
  "moddedIsoPath": "/path/to/modded.iso",
  "name": "My Mod",
  "description": "Description"
}
```

### GET /api/mex/xdelta/download-patch/{patch_id}
Download xdelta patch file.

---

## Bundles Blueprint

### GET /api/mex/bundle/list
List all bundles.

### POST /api/mex/bundle/play/{bundle_id}
Build the bundle's ISO (if missing), load its texture pack, and launch it in the user's real Slippi Dolphin.

**Body:**
```json
{ "slippiPath": "/path/to/slippi", "vanillaIsoPath": "/path/to/vanilla.iso" }
```

### POST /api/mex/bundle/delete/{bundle_id}
Delete bundle.

### POST /api/mex/bundle/update/{bundle_id}
Update bundle metadata.

### POST /api/mex/bundle/update-image/{bundle_id}
Update bundle image.

### POST /api/mex/bundle/export
Export .ssbm bundle.

**Body:**
```json
{
  "name": "My Bundle",
  "description": "Bundle description",
  "buildName": "build123",
  "vanillaIsoPath": "/path/to/vanilla.iso",
  "exportedIsoPath": "/path/to/modded.iso",
  "texturePackPath": "/path/to/textures"
}
```

**WebSocket Events:**
- `bundle_export_progress`, `bundle_export_complete`, `bundle_export_error`

### GET /api/mex/bundle/download/{bundle_id}
Download .ssbm bundle.

### POST /api/mex/bundle/install/{bundle_id}
Install bundle from storage.

**Body:**
```json
{
  "slippiPath": "/path/to/slippi",
  "vanillaIsoPath": "/path/to/vanilla.iso"
}
```

### POST /api/mex/bundle/import
Import .ssbm bundle (multipart form).

### POST /api/mex/bundle/preview
Preview bundle without importing.

---

## Viewer Blueprint

### POST /api/viewer/start
Start 3D model viewer.

**Body:**
```json
{ "character": "Fox", "skinId": "abc123" }
```

**Response:**
```json
{
  "success": true,
  "port": 8765,
  "wsUrl": "ws://localhost:8765"
}
```

### POST /api/viewer/paths
Get file paths for embedded viewer.

### POST /api/mex/viewer/paths-vanilla
Get paths for vanilla costume.

### POST /api/mex/viewer/start-vanilla
Start viewer for vanilla costume.

### POST /api/mex/viewer/paths-vault
Get paths for vault costume.

### POST /api/mex/viewer/start-vault
Start viewer for vault costume.

### POST /api/viewer/stop
Stop 3D viewer.

### GET /api/viewer/status
Get viewer status.

### GET /api/mex/vanilla/costumes/{character}
Get vanilla costumes for character.

**Response:**
```json
{
  "success": true,
  "costumes": [
    { "code": "PlFxNr", "colorName": "Default", "hasCsp": true, "hasStock": true },
    { "code": "PlFxOr", "colorName": "Orange", "hasCsp": true, "hasStock": true }
  ]
}
```

---

## Settings Blueprint

Registered but currently a placeholder with no routes (the custom vault
location feature it hosted was removed).

---

## ISO Scan Blueprint

Rips new costume skins out of vanilla/modded ISOs as a background job (see
`backend/iso_scanner.py` for the pipeline). Progress is emitted over WebSocket.

### GET /api/mex/iso-scan/preflight
Report whether `wit.exe` (Wiimms ISO Tools) is available.

### POST /api/mex/iso-scan/start
Start a scan job over a list of ISO paths.

**Body:**
```json
{ "iso_paths": ["/path/to/a.iso", "/path/to/b.iso"] }
```

### GET /api/mex/iso-scan/{job_id}
Poll current job state / final result (candidates grouped by character).

### GET /api/mex/iso-scan/{job_id}/csp/{key}/csp
Serve a candidate skin's generated CSP PNG.

### POST /api/mex/iso-scan/{job_id}/import
Import the selected candidate keys into the vault.

### POST /api/mex/iso-scan/{job_id}/cancel
Request cancellation of a running job.

### DELETE /api/mex/iso-scan/{job_id}
Drop the job's work directory and state.

---

## Menus Blueprint

CSS/SSS menu mod management. See [MENUS_SYSTEM.md](MENUS_SYSTEM.md) for concepts.

### CSS Icon Grid

### GET /api/mex/menus/css/icon_grid/list
List imported icon grid mods.

### POST /api/mex/menus/css/icon_grid/import
Import an icon grid mod (multipart form; loose PNGs or compiled `MnSlChr` dat).

### GET /api/mex/menus/css/icon_grid/{mod_id}/icons
List the per-character icons of a mod.

### POST /api/mex/menus/css/icon_grid/update/{mod_id}
Update mod metadata (name, etc.).

### POST /api/mex/menus/css/icon_grid/{mod_id}/relabel
Re-assign an icon to a different character.

### POST /api/mex/menus/css/icon_grid/{mod_id}/replace_icon
Replace a single icon image (multipart form).

### POST /api/mex/menus/css/icon_grid/{mod_id}/delete_icon
Delete a single icon from the mod.

### POST /api/mex/menus/css/icon_grid/{mod_id}/add_icon
Add an icon image for a character (multipart form).

### POST /api/mex/menus/css/icon_grid/install/{mod_id}
Install the full icon grid into the open MEX project.

### POST /api/mex/menus/css/icon_grid/install/{mod_id}/icon
Install a single icon from the mod into the project.

**Body:** `{ "character": "Fox" }`

### POST /api/mex/menus/css/icon_grid/delete/{mod_id}
Delete an icon grid mod from storage.

### CSS / Menu Backgrounds

(`/api/mex/menus/background/...` aliases exist for list/import/delete.)

### GET /api/mex/menus/css/background/list
List imported background mods.

### POST /api/mex/menus/css/background/import
Import a background mod (multipart form).

### POST /api/mex/menus/css/background/install/{mod_id}
Install a background into the project's CSS.

### POST /api/mex/menus/css/background/delete/{mod_id}
Delete a background mod.

### POST /api/mex/menus/background/update/{mod_id}
Update background mod settings.

### POST /api/mex/menus/sss/background/install/{mod_id}
Install a background into the project's SSS.

### SSS Layout

### GET /api/mex/menus/sss/layout
Get the project's stage select screen layout.

### POST /api/mex/menus/sss/layout
Set the stage select screen layout.

### GET /api/mex/menus/sss/stage-icon
Serve a stage's SSS icon image.

### CSS Layout

### GET /api/mex/menus/css/layout
Get the project's character select screen layout.

### POST /api/mex/menus/css/layout
Set the character select screen layout.

### GET /api/mex/menus/css/fighter-icon
Serve a fighter's CSS icon image.

### CSS Doors

### GET /api/mex/menus/css/doors/list
List imported door mods (CSS hand/door textures).

### GET /api/mex/menus/css/doors/image/{mod_id}
Serve a door mod's preview image.

### POST /api/mex/menus/css/doors/import
Import a door mod (multipart form).

### POST /api/mex/menus/css/doors/delete/{mod_id}
Delete a door mod.

### POST /api/mex/menus/css/doors/install/{mod_id}
Install a door mod into the project.

---

## Custom Stages Blueprint

Wholly new (m-ex) stages, distinct from DAS texture variants. See
[CUSTOM_CONTENT.md](CUSTOM_CONTENT.md).

### GET /api/mex/custom-stages/list
List custom stages in the vault.

### POST /api/mex/custom-stages/import-zip
Import a MexManager-exported stage ZIP (multipart form).

### GET /api/mex/custom-stages/in-project
List custom stages installed in the open project.

### POST /api/mex/custom-stages/scan-iso
Scan a modded ISO/project for custom stages to extract.

### GET /api/mex/custom-stages/{slug}/icon
Serve the stage's SSS icon.

### GET /api/mex/custom-stages/{slug}/banner
Serve the stage's banner image.

### POST /api/mex/custom-stages/{slug}/delete
Delete a custom stage from the vault.

### POST /api/mex/custom-stages/{slug}/rename
Rename a custom stage.

### GET /api/mex/custom-stages/{slug}/export
Download the stage's original ZIP.

### POST /api/mex/custom-stages/install
Install a vault custom stage into the open project.

**Body:** `{ "slug": "green-hill-zone" }`

### POST /api/mex/custom-stages/remove-from-project
Remove a custom stage from the open project.

### POST /api/mex/custom-stages/reorder
Reorder custom stages in the vault.

### POST /api/mex/custom-stages/folders/create
Create a vault folder for custom stages.

### POST /api/mex/custom-stages/folders/rename
Rename a folder.

### POST /api/mex/custom-stages/folders/delete
Delete a folder (stages move to root).

### POST /api/mex/custom-stages/folders/toggle
Toggle folder expanded/collapsed.

---

## Custom Characters Blueprint

Entirely new (m-ex) fighters. See [CUSTOM_CONTENT.md](CUSTOM_CONTENT.md).

### GET /api/mex/custom-characters/list
List custom characters in the vault.

### POST /api/mex/custom-characters/import-zip
Import a MexManager-exported fighter ZIP (multipart form).

### POST /api/mex/custom-characters/scan-iso
Scan a modded ISO for custom characters to extract.

### GET /api/mex/custom-characters/{slug}/icon
Serve the fighter's CSS icon.

### GET /api/mex/custom-characters/{slug}/detail
Get full fighter metadata (costumes, etc.).

### GET /api/mex/custom-characters/{slug}/csp/{index}
Serve a per-costume CSP portrait.

### GET /api/mex/custom-characters/{slug}/stock/{index}
Serve a per-costume stock icon.

### POST /api/mex/custom-characters/{slug}/delete
Delete a custom character from the vault.

### POST /api/mex/custom-characters/{slug}/rename
Rename a custom character.

### GET /api/mex/custom-characters/{slug}/export
Download the fighter's original ZIP.

### POST /api/mex/custom-characters/install
Install a vault custom character into the open project.

**Body:** `{ "slug": "shadow" }`

### POST /api/mex/custom-characters/remove-from-project
Remove a custom character from the open project.

---

## Test In Game Blueprint

Boots a freshly-built ISO in an isolated throwaway Dolphin and drives it to a
real offline match (see [INGAME_TESTING.md](INGAME_TESTING.md)). All start
endpoints run in a background thread; only one test at a time. Progress is
streamed over WebSocket: `test_progress`, `test_complete`, `test_error`.

### POST /api/mex/test-in-game/start
Start a full build test from a build manifest (smart plan covering all mod types in the build).

### POST /api/mex/test-in-game/costume
Test a single vault costume (builds a minimal ISO, selects the costume, watches for crash/hang).

### POST /api/mex/test-in-game/custom-character
Test a vault custom character in-game.

### POST /api/mex/test-in-game/custom-stage
Test a vault custom stage in-game.

### POST /api/mex/test-in-game/stage-skin
Test a DAS stage skin in-game.

### POST /api/mex/test-in-game/capture-stage-screenshot
Boot a match on a stage and capture a screenshot (used for stage previews).

### POST /api/mex/test-in-game/capture-stage-batch
Capture screenshots for multiple stages in one Dolphin session.

### GET /api/mex/test-in-game/status
Get whether a test is currently running.

---

## Extras Blueprint

Character effect mods (laser colors, shine colors, model swaps, texture hues).

### GET /api/mex/storage/extras/list/{character}
List extras in vault for a character.

### GET /api/mex/storage/extras/current/{character}/{extra_type}
Get the currently installed extra of a type for a character.

### POST /api/mex/storage/extras/create
Create a color-effect extra (e.g. custom laser/shine color).

### POST /api/mex/storage/extras/delete
Delete an extra from the vault.

### POST /api/mex/storage/extras/install
Install an extra into the open project.

### POST /api/mex/storage/extras/restore-vanilla
Restore an effect to its vanilla state.

### POST /api/mex/storage/models/create
Create a model-swap extra.

### POST /api/mex/storage/models/install
Install a model-swap extra.

### POST /api/mex/storage/models/delete
Delete a model-swap extra.

### GET /api/mex/storage/textures/current/{character}/{extra_type}
Get the current texture-hue extra for a character.

### POST /api/mex/storage/textures/install
Install a texture-hue extra.

### POST /api/mex/storage/textures/restore-vanilla
Restore textures to vanilla.

---

## Assets Blueprint

### GET /api/mex/assets/{path}
Serve MEX project asset files.

### GET /storage/{path}
Serve files from storage folder.

### GET /vanilla/{path}
Serve vanilla Melee assets.

### GET /utility/{path}
Serve utility assets (icons).

### GET /assets/{path}
Serve project assets.

---

## WebSocket Events Summary

| Event | Source | Data |
|-------|--------|------|
| `export_progress` | Export | `{ stage, progress, message }` |
| `export_complete` | Export | `{ success, filename, path }` |
| `export_error` | Export | `{ error }` |
| `setup_progress` | Setup | `{ stage, progress, message }` |
| `setup_complete` | Setup | `{ success }` |
| `setup_error` | Setup | `{ error }` |
| `texture_matched` | Slippi | `{ character, costumeIndex, skinId }` |
| `texture_progress` | Slippi | `{ matched, total, percentage }` |
| `xdelta_progress` | XDelta | `{ progress, message }` |
| `xdelta_complete` | XDelta | `{ success, filename }` |
| `xdelta_error` | XDelta | `{ error }` |
| `xdelta_create_progress` | XDelta | `{ progress, message }` |
| `xdelta_create_complete` | XDelta | `{ success }` |
| `bundle_export_progress` | Bundle | `{ progress, message }` |
| `bundle_export_complete` | Bundle | `{ success }` |
| `bundle_import_progress` | Bundle | `{ progress, message }` |
| `bundle_import_complete` | Bundle | `{ success }` |
| `iso_scan_progress` | ISO Scan | `{ job_id, status, message, percent }` |
| `test_progress` | Test In Game | `{ stage, percentage, message }` |
| `test_complete` | Test In Game | result with verdict + screenshots |
| `test_error` | Test In Game | `{ error }` |
