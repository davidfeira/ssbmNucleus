@echo off
echo Starting MEX API Backend...
echo.
echo Make sure MexCLI is built first:
echo   cd utility/MexManager/MexCLI ^&^& dotnet build -c Release
echo.
echo Starting server (port assigned dynamically, prefers 5000)
echo.
cd /d "%~dp0..\.."
python backend/mex_api.py
pause
