# Import Inventory — every "import-shaped" thing in the desktop app

> **Update 2026-06-11 — unified detection shipped (backend phase).**
> `backend/blueprints/import_unified/detection.py` now holds a pure
> `detect_content_type()` classifier (18 types), and `/import/file` dispatches
> custom characters, custom stages, bundles (.ssbm or zip), bare .xdelta, and
> SSS/CSS backgrounds, with actionable refusal messages for everything else
> (mex stage.yml packages, IC halves, Dolphin texture packs, mp3 packs…).
> Renamed costume dats (`lucinablack.dat` → Marth) and `.rat`/`.lat` variant
> renames now import everywhere via a content fallback in
> `character_detector`; py7zr 1.0 breakage in 7z imports fixed.
> Validated against the D:/ssbm-backup mod pool: 292 archives → 8 unknowns
> (all genuinely non-importable), 300/300 loose dats matched DB ground truth.
> Harness: `tests/nucleus/detect_pool.py`; route tests:
> `tests/nucleus/test_unified_import.py`, `test_costume_regression.py`.
> **Update 2026-06-11 (later) — stage.yml conversion + screenshot backfill.**
> Classic m-ex stage packages (stage.yml, 103 in the wild corpus) now
> auto-convert and import as custom stages via `/import/file`
> (`backend/stage_yml_converter.py` + a mexLib extension carrying the
> embedded map-GOBJ/moving-collision tables into MxDt — verified healthy
> in-game with Deadline). Known gap: classic `sound.spk` isn't converted.
> Stage variants imported without a screenshot stay previewless on purpose —
> previews come from the bulk DAS "Capture Screenshots" flow (the old
> per-import background backfill queue was removed as too disruptive).
>
> Remaining for the "one drop point" vision: frontend global drag-and-drop
> surface + shared progress/dialog UI, ISO-scan unification, multi-file IC
> pairing across zips, .spk sound conversion.

Stock-take of all the ways content enters Nucleus, across the three layers:
React viewer UI → Flask backend → MexCLI / HSDRawViewer. Compiled as the first
step toward unifying the scattered import UX.

---

## Layer 1: UI entry points (viewer/)

### Main vault (characters & stages)

| Entry point | UI location | Accepts | Endpoint |
|---|---|---|---|
| **Import FAB** (floating button + window-wide drag-drop) | `components/storage/ImportFab.jsx` | `.zip .7z .dat .usd .xdelta .ssbm .iso .gcm`, multi-select | `POST /import/file` (auto-detects type) |
| **ISO scan** (from FAB `.iso` drop) | `StorageViewer.jsx` → `IsoScanModal.jsx` | `.iso`, multi-select | `/iso-scan/start` → `/iso-scan/{id}/import` |
| **Patch import** | `StorageViewer.jsx` → `XdeltaImportModal.jsx` | `.xdelta`, `.ssbm` | `/xdelta/import`, `/bundle/import` |

> **2026-06 note:** the per-view import buttons this table was compiled around
> have since been replaced by the single `ImportFab` + unified `/import/file`
> pipeline; the table above reflects the current wiring.

Logic lives in `hooks/useFileImport.js`. Single imports get Slippi-safety and
duplicate dialogs; batch imports auto-fix/auto-skip. ISO scan streams progress
over WebSocket and shows a per-skin selection grid.

### Custom characters & custom stages (separate grids, separate buttons)

| Entry point | UI location | Accepts | Endpoint |
|---|---|---|---|
| **Import ZIP** | `CustomCharactersGrid.jsx` | `.zip` (fighter package) | `/custom-characters/import-zip` |
| **Scan ISO** | `CustomCharactersGrid.jsx` | `.iso` | `/custom-characters/scan-iso` |
| **Import ZIP** | `CustomStagesGrid.jsx` | `.zip` (stage package) | `/custom-stages/import-zip` |
| **Scan ISO** | `CustomStagesGrid.jsx` | `.iso` | `/custom-stages/scan-iso` |
| Add skin to custom char | `CustomCharacterDetailView.jsx` | `.dat`/`.zip` | `/custom-characters/<slug>/skins/add` |

Note: these "Scan ISO" buttons are a *different* scan pipeline than the main
vault's `IsoScanModal` (temp MexCLI project vs. wit-based costume scan), single
file only, no progress UI parity.

### Menu mods (one import button per view)

| Entry point | UI location | Accepts | Endpoint |
|---|---|---|---|
| Import Icon Grid Mod | `IconGridModsView.jsx` | `.zip` | `/import/file` (type hint) |
| Import Door Texture | `DoorModsView.jsx` | images | `/menus/css/doors/import` |
| Import pause mod | `PauseModsView.jsx` | `.zip .dat .usd` + images | `/menus/pause/import` |
| Import background | `BackgroundModsView.jsx` | `.zip .dat .usd` | `/menus/background/import` |

### Image uploads (metadata/asset editing, not "content import" per se)

- CSP upload — `CspManagerModal.jsx`, `EditModal.jsx`
- Stock icon upload — `EditModal.jsx`
- Screenshot upload — `EditModal.jsx`
- Custom char icon/portrait/misc — `CustomCharacterDetailView.jsx`
- Pause textures — `PauseTextureEditor.jsx`
- Bundle/xdelta preview images — `BundleEditModal.jsx`, `XdeltaEditModal.jsx`
- SSS layout JSON — `SssLayoutEditor.jsx`
- Model files (`.dae .dat`) — `GunEditorModal.jsx`

### Settings / setup

- First-run ISO selection — `FirstRunSetup.jsx` (native dialog → `/setup/start`)
- Vanilla ISO path — `IsoPathSection.jsx` (→ `/verify-iso`)
- Slippi Dolphin folder — `SlippiPathSection.jsx`
- **Import Vault** (restore backup zip, replace/merge) — `BackupRestore.jsx` (→ `/storage/restore`)

### MEX build mode (vault → project, "install" rather than import)

- Open `.mexproj` — `mex/ProjectSelector.jsx`
- Batch add custom characters — `mex/charactermode/AddCharacterModal.jsx`
- Batch import stage variants — `mex/stagemode/VariantsPanel.jsx`

### What does NOT exist in the UI

- No global drag-and-drop import. `useDragAndDrop.js` is reorder/folder-organize
  only. Nothing accepts a file dropped from Explorer.
- No single "Import anything" surface — every content type has its own button
  in its own view, even though the backend has a unified auto-detect endpoint.

---

## Layer 2: Backend endpoints (backend/)

### The unified endpoint (already auto-detects 5 types)

`POST /api/mex/import/file` — `blueprints/import_unified/routes.py:42`
Detection cascade: character costume → stage mod → xdelta → CSS icon grid →
pause screen. Handles Slippi-safety dialog round-trip, hash-based duplicate
detection with user override, Ice Climbers Popo/Nana pairing, CSP generation,
explicit `mod_type=effect` routing.

**This is the natural seed for unification — but most UI surfaces bypass it.**

### Everything that bypasses it

| Content | Route | File |
|---|---|---|
| Legacy costume → open project | `POST /import` | `blueprints/costumes.py:25` |
| Custom character zip | `POST /custom-characters/import-zip` | `custom_characters.py:524` |
| Custom character ISO scan | `POST /custom-characters/scan-iso` | `custom_characters.py:743` |
| Custom char skin add | `POST /custom-characters/<slug>/skins/add` | `custom_characters.py:1263` |
| Custom stage zip | `POST /custom-stages/import-zip` | `custom_stages.py:125` |
| Custom stage ISO scan | `POST /custom-stages/scan-iso` | `custom_stages.py:471` |
| DAS framework install | `POST /das/install` | `das.py:186` |
| DAS variant import | `POST /das/import` | `das.py:449` |
| Xdelta patch | `POST /xdelta/import` | `xdelta.py:332` |
| Bundle (.ssbm) | `POST /bundle/import` | `bundles.py:955` |
| Icon grid (direct) | `POST /menus/css/icon_grid/import` | `menus/icons.py:587` |
| Door texture | `POST /menus/css/doors/import` | `menus/doors.py:71` |
| Pause mod (direct) | `POST /menus/pause/import` | `menus/pause.py:250` |
| CSS/SSS background | `POST /menus/css/background/import` | `menus/backgrounds.py:121` |
| Texture extras (hue shift) | `POST /storage/textures/install` | `extras/textures.py:311` |
| Model extras | `POST /storage/models/install` | `extras/models.py:245` |
| Color extras | `POST /storage/extras/install` | `extras/colors.py:506` |
| ISO scan (main vault) | `POST /iso-scan/start` + `/<job>/import` | `iso_scan.py:56,116` |
| Vault restore | `POST /storage/restore` | (BackupRestore flow) |
| AI model download | `POST /ai-engine/models/<id>/download` | `ai_engine.py:123` |

Notable: `iso-scan/<job>/import` already *reuses* the unified pipeline by
wrapping scanned DATs in synthetic zips — proof the unified path can absorb
other flows. The menu-mod direct routes overlap with unified detection for
icon grids and pause screens (two ways in for the same content).

### Import vs. install split

A recurring pattern: **import** = into vault storage + catalog json;
**install** = vault → open MEX project (doors/pause/background install routes,
extras, DAS, bundle install, MEX batch adds). Any unified UX should keep this
distinction legible.

---

## Layer 3: MexCLI commands (utility/MexManager/MexCLI/)

The lowest layer the backend shells out to. All output indented JSON.

| Command | Args | Notes |
|---|---|---|
| `import-iso` | `<iso> <outdir> <name>` | vanilla vs pre-modded detect (MxDt.dat), DOL patch, needs codes.gct |
| `import-costume` | `<proj> <fighter> <zip>` | Kirby cap-table sync across all fighters, JointSymbol slot matching |
| `add-fighter` | `<proj> <zip>` | slot-34 reserved guard, shared-file `_001` dedup, CSS icon shift |
| `add-stage` | `<proj> <zip>` | extracts dynamic DATs FromPackage misses, auto-creates Custom SSS page |
| `add-music` | `<proj> <hps> <name>` | name-reuse dedup, collision-safe filenames |
| `add-series` | `<proj> <name> [icon.png] [emblem.obj]` | both assets optional |
| `add-code` | `<proj> <name> <hex>` | partial save (codes.ini/gct only), skip-if-exists |
| `set-fighter-music` | `<proj> <fighter> <id>` | required after add-fighter (resets to 10) |
| `set-stage-playlist` | `<proj> <stage>` + stdin JSON | required after add-stage; LAST-name match |

Plus HSDRawViewer CLI for menu-mod installs (`--css-doors`, `--pause-screen`,
`--css-bg`, `--sss-bg` import/export).

---

## The scatter, summarized

1. **~14 distinct UI import buttons** (historical; now folded into ImportFab) across the vault toolbar, two custom-content
   grids, four menu-mod views, settings, and MEX panels — each wired to its own
   endpoint with its own dialog/progress conventions.
2. **Three different "scan an ISO" experiences**: main vault (wit + WebSocket
   progress + selection grid), custom characters (temp project, no grid), and
   custom stages (same but separate button).
3. **Two ways in for the same content**: icon grids and pause mods can arrive
   via `/import/file` auto-detect *or* their dedicated menu routes.
4. **A unified backend endpoint exists** (`/import/file`, 5-type auto-detect)
   and is already proven extensible (iso-scan reuses it) — but the UI never
   presents it as "drop anything here."
5. **No drag-and-drop file import anywhere**, despite drag-drop being wired
   for internal reordering.
6. **Import vs. install is implicit**, not surfaced — some buttons store to
   the vault, some mutate the open MEX project, some do both.
