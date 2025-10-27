# MexManager Integration

This document describes the MexManager integration system for importing costumes into MEX projects and exporting ISOs.

## Overview

The integration consists of two main components:

1. **MexCLI** - C# command-line interface wrapping MexManager's core functionality
2. **mex_bridge.py** - Python module providing a high-level API for the CLI

## Architecture

```
┌─────────────────┐
│   Web Frontend  │
│  (React + Vite) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Python Backend │
│  mex_bridge.py  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     MexCLI      │
│   (C# .NET 6)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│     mexLib      │
│  (MexManager)   │
└─────────────────┘
```

## Components

### 1. MexCLI (Command-Line Interface)

Located in: `utility/MexManager/MexCLI/`

#### Commands

```bash
# Open and validate project
mexcli.exe open <project.mexproj>

# List all fighters
mexcli.exe list-fighters <project.mexproj>

# Import costume ZIP
mexcli.exe import-costume <project.mexproj> <fighter_name> <costume.zip>

# Save project
mexcli.exe save <project.mexproj>

# Export ISO
mexcli.exe export <project.mexproj> <output.iso>

# Get project info
mexcli.exe info <project.mexproj>
```

#### Output Format

All commands return JSON on stdout:

```json
{
  "success": true,
  "data": "..."
}
```

Errors return:

```json
{
  "success": false,
  "error": "Error message",
  "stackTrace": "..."
}
```

### 2. Python Bridge (mex_bridge.py)

High-level Python API wrapping the CLI.

#### Installation

No installation needed - just ensure `mexcli.exe` is built.

#### Usage Example

```python
from mex_bridge import MexManager

# Initialize
mex = MexManager(
    cli_path="utility/MexManager/MexCLI/bin/Release/net6.0/mexcli.exe",
    project_path="build/project.mexproj"
)

# Get project info
info = mex.get_info()
print(f"Project: {info['build']['name']}")

# List fighters
fighters = mex.list_fighters()
for fighter in fighters:
    print(f"{fighter['name']}: {fighter['costumeCount']} costumes")

# Import costume
result = mex.import_costume(
    fighter_name="Fox",
    zip_path="storage/Fox/PlFxNr_custom/PlFxNr_custom.zip"
)
print(f"Imported {result['costumesImported']} costume(s)")

# Export ISO with progress
def progress_callback(percentage, message):
    print(f"Export progress: {percentage}% - {message}")

mex.export_iso(
    output_path="output/modded_game.iso",
    progress_callback=progress_callback
)
```

#### API Reference

**MexManager(cli_path, project_path)**
- Initialize MexManager bridge
- Raises `MexManagerError` if paths are invalid

**open_project() -> Dict**
- Open and validate project
- Returns: project info dict

**get_info() -> Dict**
- Get detailed project information
- Returns: build info and counts

**list_fighters() -> List[Dict]**
- List all fighters
- Returns: list of fighter dicts with internalId, externalId, name, costumeCount

**get_fighter_by_name(name: str) -> Optional[Dict]**
- Get fighter by name (case-insensitive)
- Returns: fighter dict or None

**import_costume(fighter_name: str, zip_path: str) -> Dict**
- Import costume ZIP for character
- Automatically saves project after import
- Returns: import results with costume count

**save_project() -> Dict**
- Save project changes
- Returns: success dict

**export_iso(output_path: str, progress_callback=None) -> Dict**
- Export modified ISO
- progress_callback: Optional function(percentage, message)
- Returns: export results

**get_character_id(character_name: str) -> Optional[int]**
- Convert character name to internal ID
- Returns: internal ID or None

## Testing

### Test MexCLI Directly

```bash
cd utility/MexManager/MexCLI/bin/Release/net6.0

# Test info command
./mexcli.exe info ../../../../../../build/project.mexproj

# Test list fighters
./mexcli.exe list-fighters ../../../../../../build/project.mexproj
```

### Test Python Bridge

```bash
# From project root
python mex_bridge.py info
python mex_bridge.py list
```

## Integration Workflow

### Typical Costume Import Flow

1. User selects costume from vault (frontend)
2. User clicks "Add to MEX" button
3. Frontend sends request to backend API
4. Backend uses `mex_bridge.py` to:
   - Verify project is open
   - Find fighter by name
   - Import costume ZIP
   - Save project
5. Backend returns success/failure to frontend
6. Frontend updates UI

### ISO Export Flow

1. User clicks "Export ISO" button
2. Frontend opens export dialog
3. Frontend establishes WebSocket connection for progress
4. Backend uses `mex_bridge.py` to export ISO
5. Progress updates sent via WebSocket
6. Download link provided when complete

## File Locations

```
new aka/
├── utility/
│   └── MexManager/
│       ├── MexCLI/                          # CLI wrapper
│       │   ├── MexCLI.csproj
│       │   ├── Program.cs
│       │   ├── Commands/
│       │   │   ├── OpenCommand.cs
│       │   │   ├── InfoCommand.cs
│       │   │   ├── ListFightersCommand.cs
│       │   │   ├── ImportCostumeCommand.cs
│       │   │   ├── SaveCommand.cs
│       │   │   └── ExportCommand.cs
│       │   └── bin/Release/net6.0/
│       │       └── mexcli.exe               # Built executable
│       └── mexLib/                          # MexManager library
├── mex_bridge.py                            # Python bridge
├── build/                                   # MEX project folder
│   ├── project.mexproj
│   ├── data/
│   ├── assets/
│   ├── files/
│   └── sys/
└── docs/
    └── MEX_INTEGRATION.md                   # This file
```

## Error Handling

All operations raise `MexManagerError` on failure:

```python
from mex_bridge import MexManager, MexManagerError

try:
    mex = MexManager(cli_path="...", project_path="...")
    result = mex.import_costume("Fox", "costume.zip")
except MexManagerError as e:
    print(f"Operation failed: {e}")
```

## Building MexCLI

To rebuild the CLI after making changes:

```bash
cd utility/MexManager/MexCLI
dotnet build -c Release
```

Output will be in: `bin/Release/net6.0/mexcli.exe`

## Next Steps

### Phase 3: Web Backend
- Create FastAPI/Flask backend
- Add REST endpoints for MEX operations
- WebSocket support for progress updates

### Phase 4: Frontend
- Create MexPanel component
- Split-view layout (vault | MEX operations)
- ISO export with progress bar

## Troubleshooting

### "MexCLI executable not found"
- Ensure MexCLI is built: `cd utility/MexManager/MexCLI && dotnet build -c Release`
- Check path in MexManager initialization

### "Project file not found"
- Verify .mexproj path is correct
- Ensure project structure exists (data/, files/, assets/, sys/)

### "ZIP file not found"
- Verify costume ZIP path
- Ensure ZIP contains valid costume files (.dat, .png)

### Import fails with "No costumes found"
- Check ZIP structure - should contain PlXxYy.dat files
- Verify costume naming matches MEX conventions

## Version History

**v1.0** (Current)
- Initial implementation
- CLI wrapper with all core commands
- Python bridge with full API
- JSON-based communication
- Progress reporting for ISO export
