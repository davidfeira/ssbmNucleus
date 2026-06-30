@echo off
REM ============================================================================
REM  release.bat - one-shot release for SSBM Nucleus.
REM
REM  Pipeline: backend tests -> build installer (build.bat) -> CSP regression
REM            -> tag -> publish to R2 -> publish GitHub Release (installer+notes)
REM
REM  Usage (run from anywhere):
REM    scripts\build\release.bat "short update note for the in-app updater"
REM    scripts\build\release.bat "short note" dry    test + build only, NO publish
REM
REM  Before running:
REM    1) commit + push your work (release packages the committed HEAD)
REM    2) edit scripts\build\RELEASE_NOTES.md  (the GitHub changelog body)
REM    3) bump "version" in package.json if needed (drives the tag + filenames)
REM  Requires: project venv, gh CLI (authenticated), R2 creds (D:\ssbm-backup\r2.env).
REM ============================================================================
setlocal enableextensions

pushd "%~dp0..\.." || (echo ERROR: cannot cd to repo root & exit /b 1)
set "ROOT=%CD%"
set "PY=%ROOT%\venv\Scripts\python.exe"
set "NOTESFILE=%ROOT%\scripts\build\RELEASE_NOTES.md"
set "R2NOTE=%~1"
set "MODE=%~2"

if not exist "%PY%" (echo ERROR: venv python not found at %PY% & goto :fail)
if not exist "%NOTESFILE%" (echo ERROR: %NOTESFILE% not found - write the GitHub changelog first & goto :fail)
if "%R2NOTE%"=="" set /p "R2NOTE=Short update note (shown in the in-app updater): "
if "%R2NOTE%"=="" (echo ERROR: a short update note is required & goto :fail)

del "%TEMP%\nuc_release_ver.txt" 2>nul
"%PY%" -c "import json;open(r'%TEMP%\nuc_release_ver.txt','w').write(json.load(open('package.json'))['version'])"
set "VER="
if exist "%TEMP%\nuc_release_ver.txt" set /p VER=<"%TEMP%\nuc_release_ver.txt"
del "%TEMP%\nuc_release_ver.txt" 2>nul
if "%VER%"=="" (echo ERROR: could not read version from package.json & goto :fail)

echo.
echo ============================================================
echo  Release v%VER%
echo  Update note: %R2NOTE%
if /i "%MODE%"=="dry" echo  MODE: DRY RUN (test + build only, no publish)
echo ============================================================

REM --- only release committed work (ignore untracked build artifacts) ---
set "DIRTY="
for /f "delims=" %%s in ('git status --porcelain -uno') do set "DIRTY=1"
if defined DIRTY (echo ERROR: working tree has uncommitted changes - commit first. & git status --short & goto :fail)

echo.
echo [1/6] Backend tests...
"%PY%" -m pytest "%ROOT%\backend\tests" -q
if errorlevel 1 (echo TESTS FAILED - aborting. & goto :fail)

echo.
echo [2/6] Building installer (build.bat)...
call "%ROOT%\scripts\build\build.bat" <nul
cd /d "%ROOT%"
if not exist "%ROOT%\SSBM Nucleus Setup %VER%.exe" (echo ERROR: installer not found after build: "SSBM Nucleus Setup %VER%.exe" & goto :fail)

echo.
echo [3/6] CSP renderer regression (shipped self-contained build)...
"%PY%" "%ROOT%\utility\tools\processor\csp_regression\run_regression.py" --exe "%ROOT%\utility\tools\HSDLib\HSDRawViewer\bin\Release\net6.0-windows\win-x64"
if errorlevel 1 (echo CSP REGRESSION FAILED - aborting. & goto :fail)

if /i "%MODE%"=="dry" (
  echo.
  echo DRY RUN OK: tests + build + regression passed. No publish performed.
  echo Installer: "%ROOT%\SSBM Nucleus Setup %VER%.exe"
  goto :done
)

echo.
set /p "OK=Publish v%VER% to R2 + GitHub now? (y/N): "
if /i not "%OK%"=="y" (echo Aborted before publish. Installer is at the repo root. & goto :done)

echo.
echo [4/6] Pushing branch + tag v%VER%...
git push origin HEAD
if errorlevel 1 (echo ERROR: git push failed & goto :fail)
git rev-parse -q --verify "refs/tags/v%VER%" >nul
if errorlevel 1 (
  git tag -a "v%VER%" -m "Release %VER%"
  git push origin "v%VER%"
  if errorlevel 1 (echo ERROR: pushing tag failed & goto :fail)
) else (
  echo   tag v%VER% already exists - skipping create.
)

echo.
echo [5/6] Publishing to R2...
"%PY%" -m pip install --quiet --disable-pip-version-check boto3 >nul 2>&1
"%PY%" "%ROOT%\scripts\build\release_to_r2.py" --notes "%R2NOTE%"
if errorlevel 1 (echo R2 PUBLISH FAILED & goto :fail)

echo.
echo [6/6] Publishing GitHub release...
set "ASSET=%ROOT%\releases\SSBM-Nucleus_%VER%_x64-setup.exe"
if not exist "%ASSET%" (echo ERROR: staged asset not found: %ASSET% & goto :fail)
gh release view "v%VER%" >nul 2>&1
if errorlevel 1 (
  gh release create "v%VER%" --title "v%VER%" --notes-file "%NOTESFILE%" --latest "%ASSET%"
) else (
  echo   release v%VER% exists - updating notes + asset.
  gh release upload "v%VER%" "%ASSET%" --clobber
  gh release edit "v%VER%" --notes-file "%NOTESFILE%" --latest
)
if errorlevel 1 (echo GITHUB RELEASE FAILED & goto :fail)

echo.
echo ============================================================
echo  DONE - v%VER% released to R2 + GitHub
echo   R2    : https://releases.ssbmnucleus.net/windows/latest.json
echo   GitHub: https://github.com/davidfeira/ssbmNucleus/releases/tag/v%VER%
echo ============================================================

:done
popd
exit /b 0

:fail
echo.
echo RELEASE ABORTED.
popd
exit /b 1
