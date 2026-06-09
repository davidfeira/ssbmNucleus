# Menus System (CSS / SSS Customization)

Menu mod management for the Character Select Screen (CSS) and Stage Select
Screen (SSS). Backend lives in the `backend/blueprints/menus/` package; all
routes register on the single `menus_bp` blueprint (see
[API_REFERENCE.md](API_REFERENCE.md#menus-blueprint) for the endpoint list).

```
backend/blueprints/menus/
├── __init__.py      # menus_bp definition, imports submodules
├── helpers.py       # shared constants, storage paths, catalog persistence
├── icons.py         # CSS icon grid mods (import / edit / install)
├── backgrounds.py   # menu background mods (shared CSS/SSS pool)
├── sss.py           # SSS layout editor + stage icons
├── layout.py        # CSS layout editor + fighter icons
└── doors.py         # CSS door textures
```

Storage for all menu mods lives under `storage/menus/`.

## CSS Icon Grid Mods

Replacement sets for the character icons on the CSS. A mod can arrive in two
flavors:

1. **Loose PNGs** named after characters (a large alias table maps filenames
   like `falc.png`, `gnw.png`, `ics.png` to canonical character names)
2. **Compiled CSS dat files** (`MnSlChr.dat/.usd`, `mexSelectChr.dat`,
   optional `MxDt.dat`) — icons are extracted via HSDRawViewer

Either way, imports are normalized to a tiny per-mod payload:

```
storage/menus/css/icon_grid/
    metadata.json                 # catalog of installed mods
    <mod_id>/
        mod.json                  # per-mod manifest (icons + names + screenshot)
        screenshot.png            # optional preview
        icons/<Character>.png     # one labeled icon per character
```

Per-icon editing is supported (relabel to a different character, replace,
add, delete), and installation into the open MEX project can be done for the
whole grid or one icon at a time. The icon-grid installer is also reused by
`import_unified/` when a unified import detects a CSS mod.

## Menu Backgrounds

A background mod is a normalized `background.dat` bundle (a model/animation
bundle extracted from a `MnSlChr` or `MnSlMap` dat via HSDRawViewer) plus an
optional screenshot, stored under `storage/menus/css/background/<mod_id>/`.

The same pool of backgrounds installs into **either** screen of the loaded
MEX project:

- CSS: `POST /api/mex/menus/css/background/install/{mod_id}` (patches `MnSlChr.usd`)
- SSS: `POST /api/mex/menus/sss/background/install/{mod_id}` (patches `MnSlMap.usd`)

(`/api/mex/menus/background/...` aliases exist for list/import/delete in
addition to the `css/background` paths.)

## CSS Doors

A door mod is a single `door.png` texture (the CSS "door"/port panels),
stored under `storage/menus/css/doors/<mod_id>/` and installed into
`MnSlChr.usd` via HSDRawViewer's `--css-doors` import.

## Layout Editors

Both select screens have layout editors backed by the loaded MEX project's
manager (MexCLI):

- **CSS layout** — `GET|POST /api/mex/menus/css/layout` reads/writes the
  character grid layout; `GET /api/mex/menus/css/fighter-icon` serves fighter
  icon images straight from the project assets.
- **SSS layout** — `GET|POST /api/mex/menus/sss/layout` reads/writes the
  stage select layout; `GET /api/mex/menus/sss/stage-icon` serves stage icon
  images.

All install/layout operations require an open MEX project; vault-side
operations (import, edit, delete) work without one.
