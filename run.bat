@echo off
setlocal enabledelayedexpansion

echo ========================================
echo  SSBM Nucleus - Dev Launcher
echo ========================================
echo.

REM Work from the directory where this script lives
cd /d "%~dp0"

REM ----------------------------------------
REM  Check prerequisites
REM ----------------------------------------
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.10+ and add it to PATH.
    pause
    exit /b 1
)

where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Install Node.js 18+ and add it to PATH.
    pause
    exit /b 1
)

where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] npm not found. Install Node.js 18+ and add it to PATH.
    pause
    exit /b 1
)

where dotnet >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] .NET SDK not found. Install .NET 6 SDK and add it to PATH.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo [OK] Node found:
node --version
echo [OK] dotnet found:
dotnet --version
echo.

REM ----------------------------------------
REM  Setup Python virtual environment
REM ----------------------------------------
if not exist venv\Scripts\python.exe (
    echo [SETUP] Creating Python virtual environment...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
    echo.
)

REM ----------------------------------------
REM  Ensure pip is available in venv
REM ----------------------------------------
venv\Scripts\python.exe -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [SETUP] Bootstrapping pip in virtual environment...
    venv\Scripts\python.exe -m ensurepip --upgrade
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to bootstrap pip. Try: python -m ensurepip
        pause
        exit /b 1
    )
    echo [OK] pip bootstrapped.
)

REM ----------------------------------------
REM  Install Python dependencies
REM ----------------------------------------
echo [SETUP] Checking Python dependencies...
venv\Scripts\python.exe -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [SETUP] Installing Python dependencies...
    venv\Scripts\python.exe -m pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install Python dependencies.
        pause
        exit /b 1
    )
    echo [OK] Python dependencies installed.
) else (
    echo [OK] Python dependencies already installed.
)
echo.

REM ----------------------------------------
REM  Install npm dependencies (root)
REM ----------------------------------------
if not exist node_modules (
    echo [SETUP] Installing root npm dependencies...
    call npm install
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install root npm dependencies.
        pause
        exit /b 1
    )
    echo [OK] Root npm dependencies installed.
) else (
    echo [OK] Root npm dependencies already installed.
)
echo.

REM ----------------------------------------
REM  Install npm dependencies (viewer)
REM ----------------------------------------
if not exist viewer\node_modules (
    echo [SETUP] Installing viewer npm dependencies...
    cd viewer
    call npm install
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install viewer npm dependencies.
        pause
        exit /b 1
    )
    cd ..
    echo [OK] Viewer npm dependencies installed.
) else (
    echo [OK] Viewer npm dependencies already installed.
)
echo.

REM ----------------------------------------
REM  Build MexCLI (.NET)
REM ----------------------------------------
if not exist utility\MexManager\MexCLI\bin\Release\net6.0\mexcli.exe (
    echo [SETUP] Building MexCLI...
    dotnet build utility\MexManager\MexCLI -c Release
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to build MexCLI.
        pause
        exit /b 1
    )
    echo [OK] MexCLI built.
)
echo.

REM ----------------------------------------
REM  Copy codes.gct to MexCLI output
REM ----------------------------------------
if not exist utility\MexManager\MexCLI\bin\Release\net6.0\codes.gct (
    echo [SETUP] Copying codes.gct to MexCLI directory...
    copy utility\MexManager\MexManager.Desktop\codes.gct utility\MexManager\MexCLI\bin\Release\net6.0\codes.gct >nul
    echo [OK] codes.gct copied.
)

REM ----------------------------------------
REM  Build HSDRawViewer (.NET)
REM ----------------------------------------
if not exist utility\website\backend\tools\HSDLib\HSDRawViewer\bin\Release\net6.0\HSDRawViewer.exe (
    echo [SETUP] Building HSDRawViewer...
    dotnet build utility\website\backend\tools\HSDLib\HSDRawViewer -c Release
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to build HSDRawViewer.
        pause
        exit /b 1
    )
    echo [OK] HSDRawViewer built.
)
echo.

REM ----------------------------------------
REM  Create logs directory
REM ----------------------------------------
if not exist logs mkdir logs

REM ----------------------------------------
REM  Kill stale processes by name
REM ----------------------------------------
echo [CLEANUP] Stopping any existing Nucleus processes...
taskkill /F /IM mex_backend.exe 2>nul
taskkill /F /FI "WINDOWTITLE eq MEX Manager*" 2>nul
timeout /t 2 /nobreak >nul
echo [OK] Stale processes cleaned up.
echo.

REM ----------------------------------------
REM  Launch everything
REM  (Electron starts its own Flask backend,
REM   so we only need Vite + Electron here)
REM ----------------------------------------
set ROOT=%cd%

echo [START] Starting Vite Dev Server (port 3000)...
start "Vite Dev Server" cmd /k "cd /d %ROOT%\viewer && npm run dev"

echo Waiting for Vite...
timeout /t 3 /nobreak >nul

echo [START] Starting Electron App (includes Flask backend)...
start "MEX Manager" cmd /k "cd /d %ROOT% && npm run electron"

echo.
echo ========================================
echo  SSBM Nucleus is starting!
echo ========================================
echo.
echo  Backend:  Port assigned dynamically (managed by Electron)
echo  Frontend: http://localhost:3000
echo  Electron: Desktop app window
echo.
echo  To stop: close the Electron window
echo.
