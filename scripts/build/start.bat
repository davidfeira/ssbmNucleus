@echo off
echo ========================================
echo Starting MEX Manager (Electron)
echo ========================================
echo.

REM Kill processes on our specific ports (not all node/python which kills Claude Code)
echo Cleaning up existing processes on ports 5000 and 3000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do taskkill /F /PID %%a 2>nul
REM Kill electron windows with our app title
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
echo Backend:  http://127.0.0.1:5000
echo Frontend: http://localhost:3000 (Vite Dev Server)
echo Electron: Desktop app window
echo.
echo To stop, close all terminal windows or run scripts/build/stop.bat
echo.
