# Custom Content: Characters, Stages, ISO Scanning

Three related systems for getting wholly new content into the vault and into
builds. Endpoint lists: [API_REFERENCE.md](API_REFERENCE.md).

---

## Custom Characters (`backend/blueprints/custom_characters.py`)

Entirely new fighters added via m-ex (not costume swaps). Sources:

- **MexManager-exported ZIP packages** (`POST /api/mex/custom-characters/import-zip`)
- **Scanning a modded ISO** (`POST /api/mex/custom-characters/scan-iso`) —
  extracts non-vanilla fighters out of an existing m-ex build

Vault layout:

```
storage/custom_characters/<slug>/
    fighter.zip     # original ZIP preserved for re-export
    fighter.json    # extracted metadata
    css_icon.png    # CSS icon for grid display
    csp_0.png ...   # per-costume CSP portraits
```

Tracked in `storage/metadata.json` under `custom_characters`. Operations:
list, detail, rename, delete, export (download original ZIP), serve
icon/CSP/stock images, and install into / remove from the open MEX project
(via MexCLI). Installed characters can be smoke-tested in-game via
`POST /api/mex/test-in-game/custom-character` (see
[INGAME_TESTING.md](INGAME_TESTING.md)).

---

## Custom Stages (`backend/blueprints/custom_stages.py`)

Entirely new stages added via m-ex's stage system — distinct from DAS stage
skins, which are alternate textures for the 6 legal stages. (Original design
doc: [CUSTOM_STAGES_SPEC.md](CUSTOM_STAGES_SPEC.md); the implementation may
differ in details.)

Sources mirror custom characters: MexManager-exported ZIPs
(`import-zip`) or scanning an existing build (`scan-iso`).

Vault layout:

```
storage/custom_stages/<slug>/
    stage.zip       # original ZIP preserved for re-export
    icon.png        # SSS icon, extracted for fast serving
    banner.png      # banner image for detail view
    stage.json      # extracted metadata
```

Tracked in `storage/metadata.json` under `custom_stages`. Operations: list,
rename, delete, export, serve icon/banner, install into / remove from the
open project, list stages currently in the project (`/in-project`), reorder,
and vault folder management (create/rename/delete/toggle — same model as
costume folders). In-game smoke test:
`POST /api/mex/test-in-game/custom-stage`.

---

## ISO Scanning (`backend/blueprints/iso_scan.py` + `backend/iso_scanner.py`)

Rips new **costume skins** out of a list of vanilla/modded ISOs as a
background job:

1. `GET /api/mex/iso-scan/preflight` — checks that `wit.exe` (Wiimms ISO
   Tools) is available for ISO extraction.
2. `POST /api/mex/iso-scan/start` with `{ "iso_paths": [...] }` (`.iso`/`.gcm`;
   nkit not supported) — starts a scan thread and returns a `job_id`.
3. The pipeline (in `iso_scanner.py`) extracts each ISO, hashes character DAT
   files against the vault and vanilla hashes to find *new* skins, runs
   Slippi-safety validation, and generates a CSP preview per candidate into a
   per-job work directory. Progress is emitted over WebSocket as
   `iso_scan_progress` (`{ job_id, status, message, percent }`).
4. The UI polls `GET /api/mex/iso-scan/{job_id}` for candidates grouped by
   character, renders thumbnails from
   `GET /api/mex/iso-scan/{job_id}/csp/{key}/csp`, and the user selects which
   to keep.
5. `POST /api/mex/iso-scan/{job_id}/import` imports the selected candidates
   into the vault; `cancel` / `DELETE` abort and clean up.

Note: the custom characters and custom stages blueprints have their own
separate `scan-iso` endpoints for extracting *m-ex custom content* from a
build — the iso_scan blueprint is specifically for costume skins.
