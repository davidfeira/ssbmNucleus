@echo off
echo ========================================
echo Building MEX Manager Distribution
echo ========================================
echo.

REM Disable code signing to avoid symlink issues on Windows
set CSC_IDENTITY_AUTO_DISCOVERY=false
set DEBUG=electron-builder

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

echo.
echo [1/4] Building Python Backend...
echo ----------------------------------------
python -m PyInstaller mex_backend.spec --clean --noconfirm
if %errorlevel% neq 0 (
    echo ERROR: Python backend build failed
    pause
    exit /b 1
)

echo.
echo [2/4] Building .NET MexCLI (self-contained)...
echo ----------------------------------------
cd utility\MexManager\MexCLI
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=false -o ..\..\..\dist-backend\mex
if %errorlevel% neq 0 (
    echo ERROR: MexCLI build failed
    cd ..\..\..
    pause
    exit /b 1
)

echo Copying codes.gct to dist-backend\mex...
copy /Y "bin\Release\net6.0\codes.gct" "..\..\..\dist-backend\mex\codes.gct"
cd ..\..\..

echo.
echo [3/4] Building React Frontend...
echo ----------------------------------------
cd viewer
call npm run build
if %errorlevel% neq 0 (
    echo ERROR: Frontend build failed
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo [4/4] Creating Electron Installer...
echo ----------------------------------------
REM Clear electron-builder cache to avoid symlink issues
if exist "%LOCALAPPDATA%\electron-builder\Cache\winCodeSign\" (
    echo Clearing electron-builder cache...
    rmdir /s /q "%LOCALAPPDATA%\electron-builder\Cache\winCodeSign"
)
call npm run package -- --win
if %errorlevel% neq 0 (
    echo ERROR: Electron packaging failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Installer location: dist-electron\
echo.
dir /b dist-electron\*.exe 2>nul
echo.
pause
