@echo off
echo Building HSDRawViewer...
echo.

cd /d "%~dp0..\..\utility\website\backend\tools\HSDLib"
dotnet build HSDRawViewer -c Release

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed
    pause
    exit /b 1
)

echo.
echo Build successful!
pause
