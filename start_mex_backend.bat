@echo off
echo Starting MEX API Backend...
echo.
echo Make sure MexCLI is built first:
echo   cd utility/MexManager/MexCLI ^&^& dotnet build -c Release
echo.
echo Starting server on http://127.0.0.1:5000
echo.
python backend/mex_api.py
pause
