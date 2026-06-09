# Development Setup Guide

This guide will help you set up the development environment for Nucleus Desktop.

## Prerequisites

1. **Python 3.10+** - [Download from python.org](https://www.python.org/downloads/)
   - Make sure to check "Add Python to PATH" during installation

2. **Node.js 18+** - [Download from nodejs.org](https://nodejs.org/)
   - Includes npm (Node Package Manager)

3. **.NET 6 SDK** - needed to build MexCLI and HSDRawViewer

4. **Git** - [Download from git-scm.com](https://git-scm.com/)

## Quick Start (recommended)

`run.bat` in the repo root is the **primary dev launcher**. It checks
prerequisites (Python, Node, npm, dotnet), then automates all of the setup
below: creates the venv, installs Python and npm dependencies (root + viewer),
builds MexCLI and HSDRawViewer if missing (`--rebuild` forces a rebuild),
copies `codes.gct`, kills stale processes, and finally starts the Vite dev
server and the Electron app (Electron spawns the Flask backend itself).

```bash
run.bat            # set up everything (first run) and launch
run.bat --rebuild  # also rebuild MexCLI + HSDRawViewer
```

The manual steps below are only needed if you want to do the setup yourself.

## Initial Setup (manual)

### 1. Clone the Repository

```bash
git clone https://github.com/davidfeira/ssbmNucleus.git
cd ssbmNucleus
```

### 2. Install Python Dependencies

Create a virtual environment and install Python packages:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Install Node Dependencies

Install npm packages for both root and viewer:

```bash
# Install root dependencies (Electron)
npm install

# Install viewer dependencies (React + Vite)
cd viewer
npm install
cd ..
```

### 4. Copy Required Files

The mexcli tool requires the codes.gct file to be in the same directory:

```bash
# Windows (PowerShell)
Copy-Item utility\MexManager\MexManager.Desktop\codes.gct utility\MexManager\MexCLI\bin\Release\net6.0\codes.gct

# Windows (Git Bash)
cp utility/MexManager/MexManager.Desktop/codes.gct utility/MexManager/MexCLI/bin/Release/net6.0/codes.gct
```

### 5. Build HSDRawViewer (for 3D Viewer)

The 3D model viewer requires HSDRawViewer to be built with embedded mode support:

```bash
cd utility/tools/HSDLib/HSDRawViewer
dotnet build -c Release
cd ../../../../../..
```

This builds the viewer with the `--embedded` flag support, allowing it to run as a child process controlled by Electron via named pipes.

## Running in Development Mode

The primary way to run the app is the root launcher:

```bash
run.bat
```

This starts two terminal windows (the Flask backend is spawned by Electron):
- **Vite Dev Server** - React frontend (http://localhost:3000)
- **MEX Manager** - Electron desktop app (includes the Flask backend)

Alternatively, `scripts\build\start.bat` is a minimal launcher that skips all
setup checks and opens three windows (Backend, Vite, Electron) directly:

```bash
scripts\build\start.bat
```

- **MEX Backend** - Flask API server (prefers port 5000, falls back to a free OS-assigned port)
- **Vite Dev Server** - React frontend (http://localhost:3000)
- **MEX Manager** - Electron desktop app

The backend port is dynamic: it tries 5000 first and falls back to a free
port; Electron picks up the actual port at startup.

### What Each Component Does

- **Backend (Flask)**: Python API server that handles file operations, ISO manipulation, and MEX integration
- **Vite Dev Server**: Hot-reloading React development server for the UI
- **Electron**: Desktop wrapper that loads the Vite server and manages native OS features

## Logs

All three components save logs to the `logs/` folder with timestamps:
- `logs/backend_YYYYMMDD_HHMMSS.log` - Backend logs
- `logs/vite_YYYYMMDD_HHMMSS.log` - Vite dev server logs
- `logs/electron_YYYYMMDD_HHMMSS.log` - Electron logs
- `logs/mex_api_YYYYMMDD.log` - Daily backend API log (includes setup errors)

## First-Run Setup

When you first launch the app, you'll need to:
1. Select your vanilla Melee 1.02 ISO
2. Wait for asset extraction (~1-2 minutes)
3. The app will extract CSPs, stocks, and stage icons from the ISO

**Known Issue**: The vanilla ISO path doesn't get saved during setup, so you'll need to set it again in Settings.

## Project Structure

```
ssbmNucleus/
├── backend/              # Flask API server
│   ├── mex_api.py       # Main API entry point
│   └── first_run_setup.py # ISO extraction logic
├── electron/            # Electron main process
│   ├── main.js         # Electron entry point
│   └── viewer-manager.js # HSDRawViewer integration
├── viewer/             # React frontend (Vite)
│   ├── src/
│   └── package.json
├── utility/            # MEX tools and assets
│   ├── MexManager/     # MEX CLI tool
│   ├── assets/        # Extracted vanilla assets
│   └── website/       # Legacy web version
├── storage/           # User's mod collection
├── logs/             # Runtime logs
├── scripts/          # Build and run scripts
│   └── build/       # Development start scripts
└── venv/            # Python virtual environment
```

## Common Issues

### "ModuleNotFoundError: No module named 'flask'"

Make sure you activated the virtual environment and installed dependencies:
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### "codes.gct not found"

Copy the codes.gct file to the mexcli directory (see step 4 above).

### Backend won't start

Check `logs/backend_*.log` for errors. Make sure:
- Virtual environment is set up correctly
- All Python dependencies are installed

(The backend picks a free port automatically — port 5000 being in use is not
fatal, it just falls back to another port.)

### 3D Viewer doesn't connect / shows "FileNotFoundException: --embedded"

HSDRawViewer wasn't rebuilt after source changes. Rebuild it:
```bash
cd utility/tools/HSDLib/HSDRawViewer
dotnet build -c Release
```
Then restart the Electron app. You should see "Embedded mode detected" in the console when opening the 3D viewer.

## Development Tips

- **Hot Reload**: The Vite dev server will automatically reload when you edit frontend code
- **Backend Changes**: Restart the backend terminal window after editing Python code
- **Electron Changes**: Restart the Electron window after editing electron/main.js

## Building for Production

See [DISTRIBUTION_GUIDE.md](DISTRIBUTION_GUIDE.md) for instructions on building distributable packages.

## Additional Documentation

- [ROADMAP.md](ROADMAP.md) - Feature roadmap and current status
- [MEX_INTEGRATION.md](MEX_INTEGRATION.md) - MEX framework integration details
- [DISTRIBUTION_GUIDE.md](DISTRIBUTION_GUIDE.md) - Building and packaging
