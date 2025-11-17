# Linux Build Guide for Melee Nexus

This guide covers building Melee Nexus for Linux as an AppImage.

## Prerequisites

### System Dependencies

Install these via your package manager:

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-venv python3-pip nodejs npm wine

# Fedora
sudo dnf install python3 nodejs npm wine

# Arch Linux
sudo pacman -S python nodejs npm wine
```

### .NET 6 SDK

Download and install from Microsoft:

```bash
wget https://dot.net/v1/dotnet-install.sh
chmod +x dotnet-install.sh
./dotnet-install.sh --version 6.0
```

Or use your package manager:

```bash
# Ubuntu 22.04+
sudo apt install dotnet-sdk-6.0

# Fedora
sudo dnf install dotnet-sdk-6.0
```

## Quick Start

### 1. Set Up Python Virtual Environment

A pre-configured venv has been created with all dependencies:

```bash
source activate-venv.sh
```

Or activate manually:

```bash
source venv/bin/activate
```

### 2. Build for Linux

Simply run the build script:

```bash
./scripts/build/scripts/build/build-linux.sh
```

The script will:
- Activate the Python virtual environment
- Build the Python backend with PyInstaller
- Build MexCLI for linux-x64
- Build the React frontend
- Package everything as an AppImage

### 3. Run the AppImage

```bash
chmod +x dist-electron/*.AppImage
./dist-electron/*.AppImage
```

## What's Included

The Linux build includes:

- ✅ **Electron app** (native Linux)
- ✅ **Python backend** (PyInstaller bundle for Linux)
- ✅ **MexCLI** (.NET 6 linux-x64 self-contained)
- ✅ **React frontend** (built with Vite)
- ✅ **HSDRawViewer.exe** (runs via Wine for CSP generation)

## Wine Requirement

For **CSP (Character Select Portrait) generation**, Wine is required to run HSDRawViewer.exe:

```bash
# Ubuntu/Debian
sudo apt install wine

# Fedora
sudo dnf install wine

# Arch Linux
sudo pacman -S wine
```

If Wine is not available, CSP generation will be skipped with a warning.

## Troubleshooting

### Build script won't run

Fix line endings:

```bash
sed -i 's/\r$//' scripts/build/build-linux.sh
chmod +x scripts/build/build-linux.sh
```

### PyInstaller not found

Make sure venv is activated:

```bash
source venv/bin/activate
pip install pyinstaller
```

### .NET build fails

Ensure .NET 6 SDK is installed:

```bash
dotnet --version  # Should show 6.x.x
```

### AppImage won't run

Make it executable:

```bash
chmod +x dist-electron/*.AppImage
```

### Wine errors for CSP generation

Test HSDRawViewer directly:

```bash
cd utility/website/backend/tools/HSDLib/HSDRawViewer/bin/Release/net6.0-windows
wine HSDRawViewer.exe --csp <test.dat> output.png
```

## Development

To work on the Linux version:

1. **Activate venv:**
   ```bash
   source venv/bin/activate
   ```

2. **Run dev mode:**
   ```bash
   npm run dev
   ```

3. **Test changes:**
   ```bash
   ./scripts/build/scripts/build/build-linux.sh
   ```

## Virtual Environment Details

The venv includes:
- Flask 3.0.0
- Flask-CORS 4.0.0
- Flask-SocketIO 5.3.5
- python-socketio 5.10.0
- PyInstaller 6.16.0
- Pillow (PIL)
- py7zr (7z support)

To recreate the venv:

```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller pillow py7zr
```

## Distribution

The generated AppImage is a single portable file that contains:
- All application code
- Python runtime
- .NET runtime
- Node/Electron runtime
- All dependencies

Users simply download and run - no installation required!

## Platform-Specific Notes

### File Paths
All path operations use cross-platform APIs (`pathlib`, `path.join()`).

### Case Sensitivity
Linux filesystems are case-sensitive. Ensure asset files have consistent naming.

### Process Management
Process cleanup uses `pkill` on Linux instead of Windows `taskkill`.

## Support

For issues specific to Linux builds, check:
1. All dependencies installed correctly
2. venv is activated
3. .NET SDK version is 6.x
4. Wine is installed for CSP generation

Happy building! 🐧
