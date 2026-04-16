@echo off
echo ========================================
echo Building MEX Manager Distribution
echo ========================================
echo.

REM Store project root directory for absolute paths
REM %~dp0 gives us the directory where this batch file is located (scripts\build\)
REM Go up 2 directories to get to project root
set "PROJECT_ROOT=%~dp0..\.."
pushd "%PROJECT_ROOT%"
set "PROJECT_ROOT=%cd%"
popd

REM Disable code signing to avoid symlink issues on Windows
set CSC_IDENTITY_AUTO_DISCOVERY=false
set DEBUG=electron-builder
set "PACKAGE_STAGE=%PROJECT_ROOT%\build-package-staging"
set "PACKAGE_OUTPUT=%PROJECT_ROOT%\dist-electron"

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if %errorlevel% neq 0 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Force delete old build artifacts to prevent caching issues
echo Cleaning old build artifacts...
if exist "%PROJECT_ROOT%\dist" (
    rmdir /s /q "%PROJECT_ROOT%\dist"
)
if exist "%~dp0build" (
    rmdir /s /q "%~dp0build"
)
if exist "%~dp0__pycache__" (
    rmdir /s /q "%~dp0__pycache__"
)

echo.
echo [1/5] Building Python Backend...
echo ----------------------------------------
python -m PyInstaller "%~dp0mex_backend.spec" --clean --noconfirm --distpath "%PROJECT_ROOT%\dist"
if %errorlevel% neq 0 (
    echo ERROR: Python backend build failed
    pause
    exit /b 1
)

echo.
echo [2/5] Building .NET MexCLI (self-contained)...
echo ----------------------------------------
if not exist "%PROJECT_ROOT%\utility\MexManager\MexCLI" (
    echo ERROR: Cannot find MexCLI directory at %PROJECT_ROOT%\utility\MexManager\MexCLI
    pause
    exit /b 1
)
cd /d "%PROJECT_ROOT%\utility\MexManager\MexCLI"
dotnet publish -c Release -r win-x64 --self-contained true -p:PublishSingleFile=false -o "%PROJECT_ROOT%\dist-backend\mex"
if %errorlevel% neq 0 (
    echo ERROR: MexCLI build failed
    cd /d "%PROJECT_ROOT%"
    pause
    exit /b 1
)

echo Copying codes.gct to dist-backend\mex...
copy /Y "bin\Release\net6.0\codes.gct" "%PROJECT_ROOT%\dist-backend\mex\codes.gct"

echo Copying Sheik vanilla CSP assets...
xcopy /E /I /Y "%PROJECT_ROOT%\utility\assets\vanilla\Sheik" "%PROJECT_ROOT%\dist-backend\mex\utility\assets\vanilla\Sheik"
cd /d "%PROJECT_ROOT%"

echo.
echo [3/5] Building HSDRawViewer (self-contained)...
echo ----------------------------------------
if not exist "%PROJECT_ROOT%\utility\website\backend\tools\HSDLib\HSDRawViewer" (
    echo ERROR: Cannot find HSDRawViewer directory
    pause
    exit /b 1
)
cd /d "%PROJECT_ROOT%\utility\website\backend\tools\HSDLib\HSDRawViewer"
dotnet publish -c Release -r win-x64 --self-contained true -o "%PROJECT_ROOT%\dist-backend\hsdraw"
if %errorlevel% neq 0 (
    echo ERROR: HSDRawViewer build failed
    cd /d "%PROJECT_ROOT%"
    pause
    exit /b 1
)
cd /d "%PROJECT_ROOT%"

echo.
echo [4/5] Building React Frontend...
echo ----------------------------------------
if not exist "%PROJECT_ROOT%\viewer" (
    echo ERROR: Cannot find viewer directory at %PROJECT_ROOT%\viewer
    pause
    exit /b 1
)
cd /d "%PROJECT_ROOT%\viewer"
call npm run build
if %errorlevel% neq 0 (
    echo ERROR: Frontend build failed
    cd /d "%PROJECT_ROOT%"
    pause
    exit /b 1
)
cd /d "%PROJECT_ROOT%"

echo.
echo [5/5] Creating Electron Installer...
echo ----------------------------------------
set "ELECTRON_VERSION="
for /f %%I in ('node -p "require(\"./node_modules/electron/package.json\").version"') do set "ELECTRON_VERSION=%%I"
if not defined ELECTRON_VERSION (
    echo ERROR: Unable to determine installed Electron version
    pause
    exit /b 1
)

REM Clear electron-builder cache to avoid symlink issues
if exist "%LOCALAPPDATA%\electron-builder\Cache\winCodeSign\" (
    echo Clearing electron-builder cache...
    rmdir /s /q "%LOCALAPPDATA%\electron-builder\Cache\winCodeSign"
)

echo Preparing clean packaging stage...
if exist "%PACKAGE_STAGE%" (
    rmdir /s /q "%PACKAGE_STAGE%"
)
mkdir "%PACKAGE_STAGE%"
mkdir "%PACKAGE_STAGE%\node_modules"

call :CopyFile "%PROJECT_ROOT%\package.json" "%PACKAGE_STAGE%\package.json" "package.json"
if %errorlevel% neq 0 (
    pause
    exit /b 1
)

call :CopyDir "%PROJECT_ROOT%\electron" "%PACKAGE_STAGE%\electron" "Electron app files"
if %errorlevel% neq 0 (
    pause
    exit /b 1
)

call :CopyDir "%PROJECT_ROOT%\viewer\dist" "%PACKAGE_STAGE%\viewer\dist" "built frontend"
if %errorlevel% neq 0 (
    pause
    exit /b 1
)

call :CopyDir "%PROJECT_ROOT%\viewer\public" "%PACKAGE_STAGE%\viewer\public" "viewer public assets"
if %errorlevel% neq 0 (
    pause
    exit /b 1
)

call :CopyDir "%PROJECT_ROOT%\dist" "%PACKAGE_STAGE%\dist" "Python backend bundle"
if %errorlevel% neq 0 (
    pause
    exit /b 1
)

call :CopyDir "%PROJECT_ROOT%\dist-backend" "%PACKAGE_STAGE%\dist-backend" ".NET backend bundle"
if %errorlevel% neq 0 (
    pause
    exit /b 1
)

call :CopyDir "%PROJECT_ROOT%\utility\assets\vanilla\Sheik" "%PACKAGE_STAGE%\utility\assets\vanilla\Sheik" "Sheik assets"
if %errorlevel% neq 0 (
    pause
    exit /b 1
)

call :CopyDir "%PROJECT_ROOT%\utility\assets\vanilla\sounds" "%PACKAGE_STAGE%\utility\assets\vanilla\sounds" "menu sounds"
if %errorlevel% neq 0 (
    pause
    exit /b 1
)

call :CopyDir "%PROJECT_ROOT%\utility\assets\buttons" "%PACKAGE_STAGE%\utility\assets\buttons" "button assets"
if %errorlevel% neq 0 (
    pause
    exit /b 1
)

call :CopyDir "%PROJECT_ROOT%\utility\DynamicAlternateStages" "%PACKAGE_STAGE%\utility\DynamicAlternateStages" "Dynamic Alternate Stages assets"
if %errorlevel% neq 0 (
    pause
    exit /b 1
)

call :CopyDir "%PROJECT_ROOT%\utility\website\backend\tools" "%PACKAGE_STAGE%\utility\website\backend\tools" "backend tools"
if %errorlevel% neq 0 (
    pause
    exit /b 1
)

call :CopyDir "%PROJECT_ROOT%\utility\xdelta" "%PACKAGE_STAGE%\utility\xdelta" "xdelta binaries"
if %errorlevel% neq 0 (
    pause
    exit /b 1
)

call :CopyFile "%PROJECT_ROOT%\scripts\tools\clear_storage.py" "%PACKAGE_STAGE%\scripts\tools\clear_storage.py" "clear_storage.py"
if %errorlevel% neq 0 (
    pause
    exit /b 1
)

if exist "%PACKAGE_OUTPUT%" (
    rmdir /s /q "%PACKAGE_OUTPUT%"
)

call "%PROJECT_ROOT%\node_modules\.bin\electron-builder.cmd" --win --projectDir "%PACKAGE_STAGE%" "--config.directories.output=%PACKAGE_OUTPUT%" "--config.electronVersion=%ELECTRON_VERSION%"
if %errorlevel% neq 0 (
    echo ERROR: Electron packaging failed
    pause
    exit /b 1
)

echo.
echo Copying installer to project root...
copy /Y "%PROJECT_ROOT%\dist-electron\*.exe" "%PROJECT_ROOT%\"

echo.
echo Cleaning up build artifacts...
rmdir /s /q "%PROJECT_ROOT%\dist"
rmdir /s /q "%PROJECT_ROOT%\dist-backend"
rmdir /s /q "%PROJECT_ROOT%\dist-electron"
if exist "%PACKAGE_STAGE%" (
    rmdir /s /q "%PACKAGE_STAGE%"
)

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
dir /b "%PROJECT_ROOT%\*.exe" 2>nul
echo.
pause
goto :eof

:CopyDir
if not exist "%~1" (
    echo ERROR: Missing %~3 at %~1
    exit /b 1
)
robocopy "%~1" "%~2" /E /NFL /NDL /NJH /NJS /NC /NS >nul
if %errorlevel% geq 8 (
    echo ERROR: Failed to copy %~3
    exit /b 1
)
exit /b 0

:CopyFile
if not exist "%~1" (
    echo ERROR: Missing %~3 at %~1
    exit /b 1
)
for %%I in ("%~2") do (
    if not exist "%%~dpI" mkdir "%%~dpI"
)
copy /Y "%~1" "%~2" >nul
if %errorlevel% neq 0 (
    echo ERROR: Failed to copy %~3
    exit /b 1
)
exit /b 0
