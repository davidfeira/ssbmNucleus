"""
Configuration and path constants for the MEX API backend.

Handles platform detection and path configuration for both development
and bundled (PyInstaller) execution modes.
"""

import os
import sys
import subprocess
from pathlib import Path


def get_subprocess_args():
    """Get platform-specific args to hide subprocess windows on Windows."""
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return {'startupinfo': startupinfo, 'creationflags': subprocess.CREATE_NO_WINDOW}
    return {}


# Project root detection
if getattr(sys, 'frozen', False):
    # Running as bundled exe
    # When installed: C:\Users\...\AppData\Local\Programs\Melee Nexus\resources\backend\mex_backend.exe
    EXE_PATH = Path(sys.executable)
    RESOURCES_DIR = EXE_PATH.parent.parent  # resources/

    # For user data, use writable locations outside the install directory
    if os.name != 'nt' and '/tmp/.mount_' in str(EXE_PATH):
        # AppImage: Use home directory for writable data
        PROJECT_ROOT = Path.home() / '.melee-nexus'
    else:
        # Windows: Use LocalAppData for writable user data
        appdata = os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local'))
        PROJECT_ROOT = Path(appdata) / 'SSBM Nucleus'
    PROJECT_ROOT.mkdir(exist_ok=True)
else:
    # Running as Python script (development)
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    RESOURCES_DIR = PROJECT_ROOT  # In dev, resources are in project root

# Backend directory (for local imports)
BACKEND_DIR = Path(__file__).parent.parent

# Base path for bundled/dev assets
if getattr(sys, 'frozen', False):
    BASE_PATH = RESOURCES_DIR
else:
    BASE_PATH = PROJECT_ROOT

# MEX CLI path (platform-aware)
if getattr(sys, 'frozen', False):
    # Running as compiled exe bundled with Electron
    if os.name == 'nt':
        MEXCLI_PATH = RESOURCES_DIR / "utility/mex/mexcli.exe"
    else:
        # Linux: Check mex-linux first (production), then mex (fallback)
        linux_path = RESOURCES_DIR / "utility/mex-linux/mexcli"
        fallback_path = RESOURCES_DIR / "utility/mex/mexcli"
        MEXCLI_PATH = linux_path if linux_path.exists() else fallback_path
else:
    # Running as Python script (development)
    if os.name == 'nt':
        MEXCLI_PATH = PROJECT_ROOT / "utility/MexManager/MexCLI/bin/Release/net6.0/mexcli.exe"
    else:
        # On Linux in dev mode, look for linux-x64 build
        MEXCLI_PATH = PROJECT_ROOT / "utility/MexManager/MexCLI/bin/Release/net6.0/linux-x64/mexcli"

# HSDRawViewer path for 3D model streaming
if getattr(sys, 'frozen', False):
    HSDRAW_EXE = RESOURCES_DIR / "utility/HSDRawViewer/HSDRawViewer.exe"
else:
    HSDRAW_EXE = PROJECT_ROOT / "utility/website/backend/tools/HSDLib/HSDRawViewer/bin/Release/net6.0-windows/HSDRawViewer.exe"

# User data paths (writable locations)
MEX_PROJECT_PATH = PROJECT_ROOT / "build/project.mexproj"
STORAGE_PATH = PROJECT_ROOT / "storage"
OUTPUT_PATH = PROJECT_ROOT / "output"
LOGS_PATH = PROJECT_ROOT / "logs"

# Asset paths (user-extracted assets, not bundled)
VANILLA_ASSETS_DIR = PROJECT_ROOT / "utility" / "assets" / "vanilla"

# Processor tools paths for CSP generation and slippi validation
if getattr(sys, 'frozen', False):
    # Running as bundled exe - modules are bundled in the exe
    PROCESSOR_DIR = Path(sys._MEIPASS) / "utility" / "website" / "backend" / "tools" / "processor"
    SERVICES_DIR = Path(sys._MEIPASS) / "utility" / "website" / "backend" / "app" / "services"
else:
    # Running as Python script
    PROCESSOR_DIR = PROJECT_ROOT / "utility" / "website" / "backend" / "tools" / "processor"
    SERVICES_DIR = PROJECT_ROOT / "utility" / "website" / "backend" / "app" / "services"

# Add processor tools to path for imports (CSP generation, slippi validation)
sys.path.insert(0, str(PROCESSOR_DIR))
sys.path.insert(0, str(SERVICES_DIR))
sys.path.insert(0, str(BACKEND_DIR))

# Ensure directories exist
STORAGE_PATH.mkdir(exist_ok=True)
OUTPUT_PATH.mkdir(exist_ok=True)
LOGS_PATH.mkdir(exist_ok=True)
MEX_PROJECT_PATH.parent.mkdir(exist_ok=True)  # Create build/ directory
