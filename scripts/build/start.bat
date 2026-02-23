@echo off
echo ========================================
echo Starting MEX Manager (Electron)
echo ========================================
echo.

REM Kill stale processes by name (not by port, since backend port is dynamic)
echo Cleaning up existing Nucleus processes...
taskkill /F /IM mex_backend.exe 2>nul
taskkill /F /FI "WINDOWTITLE eq MEX Manager*" 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting Backend (Flask)...
start "MEX Backend" cmd /k "%~dp0..\..\scripts\run_backend.bat"

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo.
echo Starting Vite Dev Server...
start "Vite Dev Server" cmd /k "cd /d "%~dp0..\..\viewer" && npm run dev"

echo Waiting for Vite to start...
timeout /t 3 /nobreak >nul

echo.
echo Starting Electron App...
start "MEX Manager" cmd /k "cd /d "%~dp0..\.." && npm run electron"

echo.
echo ========================================
echo MEX Manager is starting!
echo ========================================
echo.
echo Backend:  Port assigned dynamically
echo Frontend: http://localhost:3000 (Vite Dev Server)
echo Electron: Desktop app window
echo.
echo To stop, close all terminal windows or run scripts/build/stop.bat
echo.
