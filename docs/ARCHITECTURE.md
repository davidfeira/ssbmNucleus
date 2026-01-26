# SSBM Nucleus Architecture

Deep technical documentation for AI assistants to quickly understand the codebase.

## System Overview

SSBM Nucleus is a desktop application for managing Super Smash Bros. Melee costume and stage mods. It uses a 3-layer architecture:

```
┌──────────────────────────────────────────┐
│   Electron (Desktop Container)           │  Node.js-based window/file management
├──────────────────────────────────────────┤
│   React 19 + Vite (Frontend)             │  Web UI running on localhost:3000 (dev)
│   Socket.io Client (Real-time updates)   │
├──────────────────────────────────────────┤
│   Flask (Python Backend)                 │  REST API on localhost:5000
│   MexCLI Bridge (C# .NET 6 Integration)  │
├──────────────────────────────────────────┤
│   Utility Tools (C# & Python)            │  CSP generation, HSDRawViewer, Processor
└──────────────────────────────────────────┘
```

### Communication Flow

- **Electron ↔ React**: IPC (Inter-Process Communication) + file dialogs
- **React ↔ Flask**: HTTP REST API + WebSocket (Socket.io)
- **Flask ↔ MexCLI**: Subprocess JSON commands
- **Flask ↔ Utilities**: Subprocess invocation + file I/O

### Startup Sequence

1. **Electron** (`electron/main.js`) spawns Python Flask backend as subprocess
2. **Electron** waits for Flask to start on localhost:5000
3. **Electron** creates BrowserWindow and loads:
   - **Dev**: `http://localhost:3000` (Vite dev server)
   - **Prod**: Built files from `viewer/dist/`
4. **React** mounts and calls Flask API for initial data
5. **Flask** initializes all blueprints and SocketIO

---

## Backend Structure

### Flask Blueprints

Located in `backend/blueprints/`. Each blueprint handles a specific domain:

| Blueprint | File | Purpose |
|-----------|------|---------|
| **project_bp** | `project.py` | MEX project open/create, fighter listing, status |
| **assets_bp** | `assets.py` | Serve vanilla/storage/utility files and images |
| **costumes_bp** | `costumes.py` | Import/remove/reorder costumes in MEX project |
| **export_bp** | `export.py` | Build ISO with progress tracking via WebSocket |
| **storage_costumes_bp** | `storage_costumes.py` | Vault costume operations (rename, delete, CSP, Slippi validation) |
| **storage_stages_bp** | `storage_stages.py` | Stage vault operations and metadata |
| **vault_backup_bp** | `vault_backup.py` | Backup/restore/clear storage vault |
| **mod_export_bp** | `mod_export.py` | Export costumes/stages as ZIP mods |
| **import_bp** | `import_unified.py` | Unified import with auto-detection (ZIP/7z) |
| **das_bp** | `das.py` | Dynamic Alternate Stages framework |
| **poses_bp** | `poses.py` | CSP pose/animation management |
| **setup_bp** | `setup.py` | First-run setup, ISO verification |
| **slippi_bp** | `slippi.py` | Dolphin integration, texture packs |
| **xdelta_bp** | `xdelta.py` | Binary patch creation/application |
| **bundles_bp** | `bundles.py` | `.ssbm` mod bundle management |
| **viewer_bp** | `viewer.py` | 3D model preview (HSDRawViewer) |
| **extras_bp** | `extras_api.py` | Character effects (lasers, shine colors) |

### Core Modules

```
backend/core/
├── config.py      # Path management, platform detection (dev vs bundled)
├── state.py       # Global state (MexManager instance, viewer process, SocketIO)
├── constants.py   # Character prefixes, vanilla costume counts
└── helpers.py     # Utility functions
```

### Supporting Modules

```
backend/
├── character_detector.py  # Auto-detect character from ZIP structure
├── stage_detector.py      # Auto-detect stage from ZIP structure
├── texture_pack.py        # Texture pack processing
├── extra_types.py         # Effect color type definitions
└── first_run_setup.py     # Setup wizard logic
```

### Backend State Management

Global state in `backend/core/state.py`:
- `_mex_manager` - MexManager instance (project context)
- `_current_project_path` - Active MEX project path
- `_viewer_process` - 3D viewer subprocess handle
- `_viewer_port` - 3D viewer port number
- `_socketio` - Flask-SocketIO reference for real-time updates

---

## Frontend Structure

### Component Hierarchy

```
App.jsx (Root - state: activeTab, metadata, setupNeeded)
├── FirstRunSetup.jsx          # Initial setup wizard
├── Header                     # Tab navigation
└── Main Content:
    │
    ├── StorageViewer.jsx      # Vault tab (activeTab === 'storage')
    │   ├── ModeToolbar.jsx    # Mode switcher
    │   ├── CharactersGrid.jsx
    │   │   └── CharacterDetailView.jsx
    │   │       ├── SkinCard.jsx
    │   │       │   ├── EditModal.jsx
    │   │       │   ├── CspManagerModal.jsx
    │   │       │   ├── [Effect Editor Modals]
    │   │       │   └── XdeltaCreateModal.jsx
    │   │       └── PoseManagerModal.jsx
    │   ├── StagesGrid.jsx
    │   │   └── StageDetailView.jsx
    │   └── ExtrasPageView.jsx
    │
    ├── MexPanel.jsx           # Install tab (activeTab === 'mex')
    │   ├── ProjectSelector.jsx
    │   ├── CharacterMode.jsx
    │   └── StageMode.jsx
    │
    └── Settings.jsx           # Settings tab (activeTab === 'settings')
        ├── IsoPathSection.jsx
        ├── SlippiPathSection.jsx
        ├── HdCspSection.jsx
        └── [Other setting sections]
```

### Custom Hooks

Located in `viewer/src/hooks/`:

| Hook | Purpose |
|------|---------|
| `useApi.js` | HTTP request wrapper with error handling |
| `useDownloadQueue.js` | Nucleus protocol download/import queue |
| `useFileImport.js` | Drag-and-drop file handling |
| `useCspManager.js` | CSP generation UI state |
| `useEditModal.js` | Edit modal state management |
| `useDragAndDrop.js` | Drag-and-drop file operations |
| `useXdeltaPatches.js` | XDelta patch management |
| `useFolderManagement.js` | Vault folder operations |
| `usePersistentState.js` | LocalStorage persistence |
| `useModalState.js` | Modal visibility tracking |

### State Management

Frontend uses vanilla React hooks (no Redux/Zustand):

**App.jsx root state:**
- `activeTab` - Current view (storage, mex, settings)
- `metadata` - Storage vault data (all costumes, stages)
- `setupNeeded` - First-run setup status
- `currentDownload`, `phase`, `error`, `result` - Download queue state

**Data flow:**
- Components receive data via props from App.jsx
- API calls update App state, triggering re-renders
- WebSocket updates trigger metadata refresh

---

## Directory Structure

```
new aka/
├── backend/
│   ├── mex_api.py              # Flask app entry point
│   ├── core/                   # Config, state, constants
│   └── blueprints/             # 17 Flask blueprints
│
├── viewer/
│   ├── src/
│   │   ├── App.jsx             # Root component
│   │   ├── components/
│   │   │   ├── storage/        # Vault components
│   │   │   ├── mex/            # MEX panel components
│   │   │   ├── settings/       # Settings sections
│   │   │   └── shared/         # Dialogs, modals
│   │   ├── hooks/              # Custom React hooks
│   │   └── utils/              # Helpers (sounds, colors)
│   └── dist/                   # Built frontend (Vite output)
│
├── electron/
│   ├── main.js                 # Main process, Flask startup, IPC
│   ├── preload.js              # Context bridge API
│   └── viewer-manager.js       # Named pipe IPC to 3D viewer
│
├── utility/
│   ├── MexManager/
│   │   ├── MexCLI/             # C# command-line wrapper
│   │   └── mexLib/             # Core MexManager library
│   ├── website/
│   │   └── backend/tools/
│   │       ├── processor/      # CSP generation (Python)
│   │       └── HSDLib/         # 3D viewer (C#)
│   ├── assets/                 # Vanilla game assets, UI icons
│   ├── DynamicAlternateStages/ # DAS framework
│   └── xdelta/                 # Binary diff utilities
│
├── storage/                    # User's mod vault (runtime)
│   ├── [character]/
│   │   └── [costume_id]/
│   │       ├── metadata.json
│   │       └── [costume files]
│   └── stages/
│
├── build/                      # MEX project folder (runtime)
│   ├── project.mexproj
│   ├── data/fighters/
│   ├── files/                  # Vanilla game files
│   └── assets/
│
├── output/                     # Export output
├── logs/                       # Application logs
├── docs/                       # Documentation
└── scripts/
    ├── tools/                  # mex_bridge.py, utilities
    └── build/                  # Build scripts
```

---

## Key Technologies

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Desktop | Electron 28 | Window manager, file dialogs, subprocess mgmt |
| Frontend | React 19 | UI framework |
| Frontend Build | Vite | Dev server & bundler |
| Frontend Realtime | Socket.io Client | WebSocket communication |
| Backend | Flask | REST API framework |
| Backend Realtime | Flask-SocketIO | WebSocket server |
| Integration | MexCLI (.NET 6) | MEX project manipulation |
| Utilities | HSDRawViewer (.NET 6) | 3D model viewer |
| Utilities | processor (Python) | CSP generation, Slippi validation |

---

## Request/Response Flow Examples

### Importing a Costume

```
1. User drags ZIP onto app
2. React → Flask POST /api/mex/import/file
3. Flask → character_detector.py (identify character from ZIP)
4. Flask → Extract to storage/[character]/[id]/
5. Flask → Return costume metadata
6. React → Update UI with new costume
```

### Exporting ISO

```
1. User clicks Export
2. React → Flask POST /api/mex/export/start
3. Flask → MexCLI subprocess (build ISO)
4. MexCLI → Emit progress via stdout
5. Flask → WebSocket emit progress to React
6. React → Update progress bar
7. Flask → Return download path
```

### Generating CSP

```
1. User opens CSP manager
2. React → Flask GET /api/mex/viewer/start
3. Flask → Start HSDRawViewer subprocess
4. HSDRawViewer → Render character pose
5. User adjusts pose, clicks Generate
6. React → Flask POST /api/mex/storage/poses/generate
7. Flask → processor/generate_csp.py
8. Flask → Return generated CSP image
```

---

## Development Commands

```bash
# Development
npm run dev           # Flask + Vite dev server
npm run electron:dev  # Flask + Electron with hot reload

# Production build
npm run build         # Build React → viewer/dist/
npm run package       # Create installer with electron-builder
npm run package:win   # Windows NSIS installer
npm run package:linux # Linux AppImage
```

## Bundled Resources (Production)

electron-builder packages:
- `dist/` → Backend Python bundled via PyInstaller
- `viewer/dist/` → Frontend assets
- `utility/assets/` → Vanilla game graphics
- `utility/HSDRawViewer/` → 3D viewer executable
- `utility/website/backend/tools/` → Processor tools
