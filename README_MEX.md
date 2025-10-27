# Melee Nexus - MEX Integration

Complete system for managing costume imports and ISO exports through MexManager.

## Quick Start

### 1. Build MexCLI (One-time setup)

```bash
cd utility/MexManager/MexCLI
dotnet build -c Release
```

### 2. Install Python Dependencies (One-time setup)

```bash
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies (One-time setup)

```bash
cd viewer
npm install
```

### 4. Start the System

**Terminal 1 - Backend:**
```bash
python backend/mex_api.py
```
Or double-click: `start_mex_backend.bat`

**Terminal 2 - Frontend:**
```bash
cd viewer
npm run dev
```

### 5. Open Browser

Navigate to: `http://localhost:3001`

## Usage

### Two-Panel Interface

**Costume Vault Tab:**
- Browse all costumes in your storage
- View CSPs and stock icons
- Manage your collection

**MEX Manager Tab:**
- View MEX project status
- See all fighters and costume counts
- Import costumes from vault to MEX project
- Export modified ISO

### Importing Costumes

1. Switch to **MEX Manager** tab
2. Select a fighter from the list
3. View available costumes in storage
4. Click **"Add to MEX"** on desired costume
5. Wait for import confirmation

### Exporting ISO

1. Click **"Export ISO"** button
2. Enter desired filename (or use default)
3. Click **"Start Export"**
4. Watch progress bar (5-10 minutes)
5. Click **"Download"** when complete

## Architecture

```
┌─────────────────┐
│   Web Browser   │
│  (React + Vite) │
└────────┬────────┘
         │ HTTP/WebSocket
         ▼
┌─────────────────┐
│   Flask API     │
│  (Port 5000)    │
└────────┬────────┘
         │ subprocess
         ▼
┌─────────────────┐
│     MexCLI      │
│   (C# .NET 6)   │
└────────┬────────┘
         │ library calls
         ▼
┌─────────────────┐
│     mexLib      │
│  (MexManager)   │
└─────────────────┘
```

## API Endpoints

**GET /api/mex/status** - Get MEX project status
```json
{
  "success": true,
  "connected": true,
  "project": {
    "name": "Akaneia",
    "version": "1.0.1"
  },
  "counts": {
    "fighters": 41,
    "stages": 96
  }
}
```

**GET /api/mex/fighters** - List all fighters
```json
{
  "success": true,
  "fighters": [
    {
      "internalId": 1,
      "externalId": 2,
      "name": "Fox",
      "costumeCount": 16
    }
  ]
}
```

**POST /api/mex/import** - Import costume
```json
{
  "fighter": "Fox",
  "costumePath": "storage/Fox/PlFxNr_custom/PlFxNr_custom.zip"
}
```

**POST /api/mex/export/start** - Start ISO export
```json
{
  "filename": "game.iso"
}
```

**GET /api/mex/export/download/:filename** - Download exported ISO

## WebSocket Events

**Connected:**
- `connected` - Connection established

**Export Progress:**
- `export_progress` - Progress update (percentage, message)
- `export_complete` - Export finished successfully
- `export_error` - Export failed with error

## File Structure

```
new aka/
├── utility/
│   └── MexManager/
│       ├── MexCLI/                      # CLI wrapper
│       │   ├── MexCLI.csproj
│       │   ├── Program.cs
│       │   ├── Commands/
│       │   │   ├── OpenCommand.cs
│       │   │   ├── ListFightersCommand.cs
│       │   │   ├── ImportCostumeCommand.cs
│       │   │   ├── SaveCommand.cs
│       │   │   └── ExportCommand.cs
│       │   └── bin/Release/net6.0/
│       │       └── mexcli.exe           # Built executable
│       └── mexLib/                      # MexManager library
├── backend/
│   └── mex_api.py                       # Flask API server
├── viewer/
│   └── src/
│       ├── components/
│       │   ├── StorageViewer.jsx        # Costume vault
│       │   ├── MexPanel.jsx             # MEX manager UI
│       │   └── IsoBuilder.jsx           # ISO export modal
│       └── App.jsx                      # Main app with tabs
├── mex_bridge.py                        # Python wrapper
├── requirements.txt                     # Python dependencies
├── start_mex_backend.bat               # Backend launcher
└── docs/
    └── MEX_INTEGRATION.md              # Technical docs
```

## Features

### ✅ Implemented

- **CLI Wrapper** - Complete C# command-line interface for MexManager
- **Python Bridge** - High-level Python API
- **Flask Backend** - REST API with WebSocket support
- **React Frontend** - Two-panel interface with tabs
- **Costume Import** - One-click import from vault to MEX
- **ISO Export** - Progress-tracked ISO export with download
- **Real-time Updates** - WebSocket progress for long operations

### 🚀 Future Enhancements

- Batch costume import
- Export presets (filename templates)
- Fighter-specific costume browsing
- Costume preview before import
- Export history tracking
- Project backup/restore

## Troubleshooting

### Backend won't start

**Error:** `MexCLI not found`
- **Solution:** Build MexCLI first:
  ```bash
  cd utility/MexManager/MexCLI
  dotnet build -c Release
  ```

**Error:** `MEX project not found`
- **Solution:** Ensure `build/project.mexproj` exists

### Frontend shows connection error

- **Check:** Backend is running on port 5000
- **Check:** CORS is enabled (default)
- **Check:** No firewall blocking localhost

### Import fails

**Error:** `Fighter not found`
- **Solution:** Fighter name must match exactly (case-insensitive)
- **Valid names:** Fox, Mario, C. Falcon, etc.

**Error:** `ZIP file not found`
- **Solution:** Ensure costume ZIP exists in storage folder
- **Path:** `storage/Character/FolderName/FolderName.zip`

**Error:** `No costumes found in ZIP`
- **Solution:** ZIP must contain valid .dat files
- **Format:** PlXxYy.dat (e.g., PlFxNr.dat)

### Export fails

**Error:** `Export failed: Project not saved`
- **Solution:** Costumes auto-save, but try manual save first

**Error:** Takes too long
- **Normal:** 5-10 minutes is expected for ISO export
- **Tip:** Continue working while export runs in background

## Testing

### Test CLI directly:

```bash
cd utility/MexManager/MexCLI/bin/Release/net6.0

# Test info
./mexcli.exe info ../../../../../build/project.mexproj

# Test list fighters
./mexcli.exe list-fighters ../../../../../build/project.mexproj
```

### Test Python bridge:

```bash
python mex_bridge.py info
python mex_bridge.py list
```

### Test full stack:

1. Start backend: `python backend/mex_api.py`
2. Start frontend: `cd viewer && npm run dev`
3. Open browser: `http://localhost:3001`
4. Switch to MEX Manager tab
5. Import a costume
6. Export ISO

## Development

### Backend Development

Edit `backend/mex_api.py`:
- API automatically reloads on save (Flask debug mode)
- Check console for errors

### Frontend Development

Edit files in `viewer/src/components/`:
- Hot reload enabled (Vite)
- Check browser console for errors

### CLI Development

Edit files in `utility/MexManager/MexCLI/`:
- Rebuild: `dotnet build -c Release`
- Test: `./bin/Release/net6.0/mexcli.exe help`

## Version

**v1.0** - Initial Release
- Complete MEX integration
- Costume import/export
- Two-panel UI
- WebSocket progress

---

**Built with:** React, Vite, Flask, Flask-SocketIO, .NET 6, MexManager

**License:** Follow MexManager's license terms
