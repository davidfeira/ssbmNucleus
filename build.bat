@echo off
setlocal

set "PROJECT_ROOT=%~dp0"

pushd "%PROJECT_ROOT%" >nul

echo ========================================
echo SSBM Nucleus Root Build
echo ========================================
echo.
echo Running scripts\build\build.bat...
echo.

call "%PROJECT_ROOT%scripts\build\build.bat"
set "BUILD_EXIT=%ERRORLEVEL%"

if not "%BUILD_EXIT%"=="0" (
    echo.
    echo Root build wrapper detected a failure. Exit code: %BUILD_EXIT%
    popd >nul
    endlocal & exit /b %BUILD_EXIT%
)

echo.
echo Installers copied to project root:
set "FOUND_INSTALLER="
for %%F in ("%PROJECT_ROOT%*.exe") do (
    if exist "%%~fF" (
        echo   %%~fF
        set "FOUND_INSTALLER=1"
    )
)

if not defined FOUND_INSTALLER (
    echo ERROR: Build completed, but no .exe was found in the project root.
    popd >nul
    endlocal & exit /b 1
)

popd >nul
endlocal & exit /b 0
