#!/bin/bash
# Build script for Linux AppImage
# Run this in WSL or native Linux

set -e  # Exit on error

echo "================================"
echo "Melee Nexus Linux Build Script"
echo "================================"
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Warning: This script should be run on Linux or WSL"
fi

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Add .NET to PATH if installed in home directory
if [ -d "$HOME/.dotnet" ]; then
    export PATH="$HOME/.dotnet:$PATH"
    export DOTNET_ROOT="$HOME/.dotnet"
fi

echo -e "${BLUE}[1/5] Checking dependencies...${NC}"

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 not found. Install with: sudo apt install python3${NC}"
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo -e "${RED}Warning: venv not found. Creating virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install pyinstaller pillow py7zr
fi

# Check for PyInstaller (should be in venv now)
if ! python3 -c "import PyInstaller" &> /dev/null; then
    echo -e "${RED}Error: PyInstaller not found in venv. Try: pip install pyinstaller${NC}"
    exit 1
fi

# Check for .NET SDK
if ! command -v dotnet &> /dev/null; then
    echo -e "${RED}Error: dotnet not found. Install .NET 6 SDK:${NC}"
    echo "  wget https://dot.net/v1/dotnet-install.sh"
    echo "  chmod +x dotnet-install.sh"
    echo "  ./dotnet-install.sh --version 6.0"
    exit 1
fi

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: node not found. Install with: sudo apt install nodejs npm${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All dependencies found${NC}"
echo ""

# Step 1: Build Python Backend
echo -e "${BLUE}[2/5] Building Python backend with PyInstaller...${NC}"
pyinstaller scripts/build/mex_backend.spec --clean --noconfirm
if [ -f "dist/mex_backend" ]; then
    echo -e "${GREEN}✓ Python backend built successfully${NC}"
else
    echo -e "${RED}✗ Python backend build failed${NC}"
    exit 1
fi
echo ""

# Step 2: Build .NET MexCLI for Linux
echo -e "${BLUE}[3/5] Building MexCLI for linux-x64...${NC}"
cd utility/MexManager/MexCLI

# Clean previous builds
rm -rf bin/Release/net6.0/linux-x64 2>/dev/null || true

# Build for linux-x64
dotnet publish -c Release -r linux-x64 --self-contained true \
    -p:PublishSingleFile=false \
    -o ../../../dist-backend/mex-linux

if [ -f "../../../dist-backend/mex-linux/mexcli" ]; then
    chmod +x "../../../dist-backend/mex-linux/mexcli"

    # Copy codes.gct to the same directory as mexcli
    if [ -f "bin/Release/net6.0/codes.gct" ]; then
        cp "bin/Release/net6.0/codes.gct" "../../../dist-backend/mex-linux/codes.gct"
        echo -e "${GREEN}✓ MexCLI built successfully (with codes.gct)${NC}"
    else
        echo -e "${GREEN}✓ MexCLI built successfully${NC}"
        echo -e "${RED}⚠ Warning: codes.gct not found${NC}"
    fi
else
    echo -e "${RED}✗ MexCLI build failed${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"
echo ""

# Step 3: Copy HSDRawViewer.exe for Wine
echo -e "${BLUE}[4/5] Copying HSDRawViewer.exe for Wine support...${NC}"
HSDRAW_SRC="utility/website/backend/tools/HSDLib/HSDRawViewer/bin/Release/net6.0-windows"
if [ -d "$HSDRAW_SRC" ]; then
    mkdir -p dist-backend/hsdraw
    cp -r "$HSDRAW_SRC"/* dist-backend/hsdraw/
    echo -e "${GREEN}✓ HSDRawViewer.exe copied (Wine required for CSP generation)${NC}"
else
    echo -e "${RED}⚠ Warning: HSDRawViewer not found. CSP generation will not work.${NC}"
fi
echo ""

# Step 4: Build React Frontend
echo -e "${BLUE}[5/5] Building React frontend...${NC}"
cd viewer
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi
npm run build

if [ -d "dist" ]; then
    echo -e "${GREEN}✓ Frontend built successfully${NC}"
else
    echo -e "${RED}✗ Frontend build failed${NC}"
    exit 1
fi

cd "$PROJECT_ROOT"
echo ""

# Step 5: Package with electron-builder
echo -e "${BLUE}[6/6] Packaging AppImage with electron-builder...${NC}"
npm run package:linux

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

if [ -d "dist-electron" ]; then
    echo "AppImage location:"
    find dist-electron -name "*.AppImage" -type f
    echo ""
    echo "To run:"
    echo "  chmod +x <AppImage_file>"
    echo "  ./<AppImage_file>"
    echo ""
    echo "For CSP generation, install Wine:"
    echo "  sudo apt install wine"
else
    echo -e "${RED}Error: dist-electron directory not found${NC}"
    exit 1
fi
