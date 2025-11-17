@echo off
echo ========================================
echo Stopping MEX Manager
echo ========================================
echo.

echo Stopping Electron...
taskkill /F /IM electron.exe 2>nul
if %errorlevel% equ 0 (
    echo Electron stopped successfully
) else (
    echo No Electron process found
)

echo.
echo Stopping Python (Backend)...
taskkill /F /IM python.exe 2>nul
if %errorlevel% equ 0 (
    echo Backend stopped successfully
) else (
    echo No backend process found
)

echo.
echo Stopping Node (Vite Dev Server)...
taskkill /F /IM node.exe 2>nul
if %errorlevel% equ 0 (
    echo Vite stopped successfully
) else (
    echo No Vite process found
)

echo.
echo ========================================
echo All processes stopped
echo ========================================
echo.
pause
