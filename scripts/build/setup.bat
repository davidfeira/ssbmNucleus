@echo off
echo ========================================
echo SSBM Nucleus - Development Setup
echo ========================================
echo.

cd /d "%~dp0..\.."

REM Check for Node.js
echo [1/6] Checking Node.js...
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Node.js not found. Installing via winget...
    winget install OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to install Node.js. Please install manually from https://nodejs.org
        pause
        exit /b 1
    )
    echo.
    echo ========================================
    echo Node.js installed! Please restart this script.
    echo ========================================
    pause
    exit /b 0
) else (
    for /f "tokens=*" %%i in ('node --version') do echo Found Node.js %%i
)

REM Check for Python
echo.
echo [2/6] Checking Python...
set "PYTHON_CMD="
where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "PYTHON_CMD=python"
) else (
    if exist "C:\Users\%USERNAME%\AppData\Local\Python\bin\python3.exe" (
        set "PYTHON_CMD=C:\Users\%USERNAME%\AppData\Local\Python\bin\python3.exe"
    )
)

if "%PYTHON_CMD%"=="" (
    echo ERROR: Python not found. Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('%PYTHON_CMD% --version') do echo Found %%i

REM Check for .NET SDK
echo.
echo [3/6] Checking .NET SDK...
set "DOTNET_CMD="
where dotnet >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set "DOTNET_CMD=dotnet"
) else (
    if exist "C:\Program Files\dotnet\dotnet.exe" (
        set "DOTNET_CMD=C:\Program Files\dotnet\dotnet.exe"
    ) else if exist "C:\Program Files (x86)\dotnet\dotnet.exe" (
        set "DOTNET_CMD=C:\Program Files (x86)\dotnet\dotnet.exe"
    )
)

if "%DOTNET_CMD%"=="" (
    echo .NET SDK not found. Installing via winget...
    winget install Microsoft.DotNet.SDK.6 --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to install .NET SDK. Please install manually from https://dotnet.microsoft.com/download/dotnet/6.0
        pause
        exit /b 1
    )
    echo.
    echo ========================================
    echo .NET SDK installed! Please restart this script.
    echo ========================================
    pause
    exit /b 0
) else (
    for /f "tokens=*" %%i in ('"%DOTNET_CMD%" --version') do echo Found .NET SDK %%i
)

REM Check for .NET Core 3.1 Runtime (needed for SlippiCostumeValidator)
echo.
echo [3.5/6] Checking .NET Core 3.1 Runtime...
"%DOTNET_CMD%" --list-runtimes 2>nul | findstr /C:"Microsoft.NETCore.App 3.1" >nul
if %ERRORLEVEL% NEQ 0 (
    echo .NET Core 3.1 Runtime not found. Installing via winget...
    winget install Microsoft.DotNet.Runtime.3_1 --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL% NEQ 0 (
        echo WARNING: Failed to install .NET Core 3.1 Runtime.
        echo Slippi costume validation may not work.
        echo Please install manually from https://dotnet.microsoft.com/download/dotnet/3.1
    ) else (
        echo .NET Core 3.1 Runtime installed!
    )
) else (
    echo Found .NET Core 3.1 Runtime
)

REM Create Python virtual environment
echo.
echo [4/6] Setting up Python virtual environment...
if not exist "venv" (
    echo Creating venv...
    %PYTHON_CMD% -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
) else (
    echo venv already exists
)

echo Installing Python dependencies...
call venv\Scripts\activate
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

REM Install npm dependencies
echo.
echo [5/6] Installing npm dependencies...
echo Installing root dependencies...
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install root npm dependencies
    pause
    exit /b 1
)

echo Installing viewer dependencies...
cd viewer
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install viewer npm dependencies
    pause
    exit /b 1
)
cd ..

REM Build MexCLI
echo.
echo [6/7] Building MexCLI...
if exist "utility\MexManager\MexCLI\MexCLI.csproj" (
    "%DOTNET_CMD%" build -c Release utility\MexManager\MexCLI\MexCLI.csproj
    if %ERRORLEVEL% NEQ 0 (
        echo WARNING: Failed to build MexCLI. Some features may not work.
    ) else (
        echo MexCLI built successfully
    )
) else (
    echo WARNING: MexCLI project not found, skipping...
)

REM Build HSDRawViewer (for CSP generation)
echo.
echo [7/7] Building HSDRawViewer...
if exist "utility\website\backend\tools\HSDLib\HSDRawViewer\HSDRawViewer.csproj" (
    "%DOTNET_CMD%" build -c Release utility\website\backend\tools\HSDLib\HSDRawViewer\HSDRawViewer.csproj
    if %ERRORLEVEL% NEQ 0 (
        echo WARNING: Failed to build HSDRawViewer. CSP generation may not work.
    ) else (
        echo HSDRawViewer built successfully
    )
) else (
    echo WARNING: HSDRawViewer project not found, skipping...
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the app, run: start.bat
echo.
pause
