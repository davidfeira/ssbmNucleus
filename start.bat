@echo off
echo ========================================
echo Starting MEX Costume Manager
echo ========================================
echo.

REM Kill any existing Python and Node processes
echo Cleaning up existing processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM node.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo Starting Backend (Flask)...
start "MEX Backend" cmd /k "cd /d "%~dp0" && python backend/mex_api.py"

echo Waiting for backend to start...
timeout /t 3 /nobreak >nul

echo.
echo Starting Frontend (Vite)...
start "MEX Frontend" cmd /k "cd /d "%~dp0viewer" && npm run dev"

echo.
echo ========================================
echo Both servers are starting!
echo ========================================
echo.
echo Backend:  http://127.0.0.1:5000
echo Frontend: http://localhost:3002
echo.
echo Press any key to open frontend in browser...
pause >nul

start http://localhost:3002

echo.
echo To stop servers, close both terminal windows.
echo.
