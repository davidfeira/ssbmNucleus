@echo off
echo ========================================
echo Cleaning Project for Distribution
echo ========================================
echo.
echo This will remove:
echo - storage/ (user costumes)
echo - intake/ (pending imports)
echo - logs/ (log files)
echo - output/ (generated ISOs)
echo - build/ (MEX project data)
echo.
echo This will KEEP:
echo - utility/assets/vanilla/ (vanilla assets)
echo - utility/website/backend/tools/processor/csp_data/ (character data)
echo.
pause

echo.
echo Cleaning storage...
if exist storage\ (
    rmdir /s /q storage
    echo  - Removed storage/
)

echo Cleaning intake...
if exist intake\ (
    rmdir /s /q intake
    echo  - Removed intake/
)

echo Cleaning logs...
if exist logs\ (
    rmdir /s /q logs
    echo  - Removed logs/
)

echo Cleaning output...
if exist output\ (
    rmdir /s /q output
    echo  - Removed output/
)

echo Cleaning build...
if exist build\ (
    rmdir /s /q build
    echo  - Removed build/
)

echo.
echo ========================================
echo Cleanup Complete!
echo ========================================
echo.
echo Project is ready for distribution build.
echo Run build.bat next.
echo.
pause
