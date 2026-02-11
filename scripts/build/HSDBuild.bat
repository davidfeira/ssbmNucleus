@echo off
echo Building HSDRawViewer (self-contained)...
echo.

cd /d "%~dp0..\..\utility\website\backend\tools\HSDLib"
dotnet publish HSDRawViewer -c Release -r win-x64 --self-contained true -o "%~dp0..\..\dist-backend\hsdraw"

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo Build successful!
pause
