@echo off
echo ========================================
echo Starting MEX Manager (Electron)
echo ========================================
echo.

REM Kill any existing Python and Node processes
echo Cleaning up existing processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
taskkill /F /IM electron.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting Backend (Flask)...
start "MEX Backend" cmd /k "cd /d "%~dp0" && python backend/mex_api.py"

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo.
echo Starting Vite Dev Server...
start "Vite Dev Server" cmd /k "cd /d "%~dp0viewer" && npm run dev"

echo Waiting for Vite to start...
timeout /t 3 /nobreak >nul

echo.
echo Starting Electron App...
start "MEX Manager" cmd /k "cd /d "%~dp0" && npm run electron"

echo.
echo ========================================
echo MEX Manager is starting!
echo ========================================
echo.
echo Backend:  http://127.0.0.1:5000
echo Frontend: http://localhost:3000 (Vite Dev Server)
echo Electron: Desktop app window
echo.
echo To stop, close all terminal windows or run stop.bat
echo.
