@echo off
echo ========================================
echo Stopping MEX Costume Manager
echo ========================================
echo.

echo Stopping Python (Backend)...
taskkill /F /IM python.exe 2>nul
if %errorlevel% equ 0 (
    echo Backend stopped successfully
) else (
    echo No backend process found
)

echo.
echo Stopping Node (Frontend)...
taskkill /F /IM node.exe 2>nul
if %errorlevel% equ 0 (
    echo Frontend stopped successfully
) else (
    echo No frontend process found
)

echo.
echo ========================================
echo All servers stopped
echo ========================================
echo.
pause
