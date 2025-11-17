# Distribution Guide for Melee Nexus

## ✅ Comprehensive Dependency Audit Complete

All Python dependencies, external executables, and data files have been audited and included in the PyInstaller spec file.

---

## 📦 What to Distribute

**YES - Just ONE file:**
```
dist-electron/Melee Nexus Setup.exe  (~400-500MB)
```

This installer contains EVERYTHING:
- ✅ Electron app (Chromium browser + your React UI)
- ✅ Python backend bundled as `mex_backend.exe`
- ✅ .NET MexCLI with runtime (self-contained)
- ✅ .NET HSDRawViewer with ALL dependencies (lib/, runtimes/, Shader/, DLLs)
- ✅ CSP generation data (csp_data/ with all character assets)
- ✅ Vanilla assets
- ✅ All Python packages (Flask, Pillow, etc.)

**Users need:** NOTHING. No Python, no .NET, no Node.js.

---

## 🖼️ Images Not Loading - Electron Folder Structure

### How Electron Bundling Works:

When Electron builds with electron-builder:

```
Melee Nexus/
├── Melee Nexus.exe (main executable)
└── resources/
    ├── app.asar (your built viewer/dist/)
    ├── backend/
    │   └── mex_backend.exe
    └── utility/
        ├── mex/mexcli.exe
        ├── assets/vanilla/ (images here!)
        └── website/backend/tools/
            ├── HSDLib/HSDRawViewer/
            │   ├── HSDRawViewer.exe
            │   ├── lib/
            │   ├── runtimes/
            │   ├── Shader/
            │   └── *.dll
            ├── processor/
            │   ├── csp_data/ (character data here!)
            │   └── CostumeValidator/
            └── ...
```

### Why Images Weren't Loading:

1. **In Development:**
   - `viewer/public/vanilla/` exists
   - Vite serves from `public/`
   - Images load as `/vanilla/stages/dreamland.jpg`

2. **In Production (Bundled):**
   - `viewer/public/vanilla/` gets bundled into `app.asar`
   - BUT assets are also in `resources/utility/assets/vanilla/`
   - Paths need to resolve correctly

### Fix:

Your backend serves `/storage/*` through Flask, which proxies to the right location. Images should work once paths are resolved via the backend API.

---

## 🧹 Clear Storage Before Distributing?

**YES - Highly Recommended!**

### What to Clear:

```batch
# Clear user data (DO THIS before building installer)
rmdir /s /q storage\
rmdir /s /q intake\
rmdir /s /q logs\
rmdir /s /q output\
```

### What to Keep:

- ✅ `utility/assets/vanilla/` - Vanilla Melee assets (users need these)
- ✅ `utility/website/backend/tools/processor/csp_data/` - Character animation data
- ✅ `build/` - Only if you're including a sample MEX project

### Create a Clean Build Script:

```batch
# clean_for_distribution.bat
@echo off
echo Cleaning user data for distribution...
rmdir /s /q storage 2>nul
rmdir /s /q intake 2>nul
rmdir /s /q logs 2>nul
rmdir /s /q output 2>nul
rmdir /s /q build 2>nul
echo Cleaned! Ready to build installer.
pause
```

Run this BEFORE `scripts/build/build.bat`.

---

## 🎨 HSDRawViewer - Will It Work?

### Status: ✅ YES, with caveats

**What HSDRawViewer Is:**
- .NET 6.0 Windows Forms application
- 3D renderer for Melee DAT files → CSP images
- Uses DirectX/OpenGL for rendering
- Requires: `lib/`, `runtimes/`, `Shader/`, DLLs

**How It's Called:**
```python
# generate_csp.py:429
cmd = [windows_exe, "--csp", dat_file, output_file, anim_file, camera_file]
result = subprocess.run(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
```

**Bundling Strategy:**

1. **Entire HSDRawViewer directory is bundled** (via updated spec file)
   - Not just `.exe`, but ALL dependencies
   - Includes `lib/`, `runtimes/`, `Shader/`, DLLs

2. **Path Resolution:**
   - Dev: `utility/website/backend/tools/HSDLib/HSDRawViewer/.../HSDRawViewer.exe`
   - Production: `sys._MEIPASS + '/utility/website/backend/tools/HSDLib/...'`

3. **.NET Runtime:**
   - You're building .NET as **self-contained** in `scripts/build/build.bat`
   - Runtime is included, users don't need .NET installed

### Potential Issues:

**Issue 1: Graphics Dependencies**
- HSDRawViewer uses DirectX/OpenGL
- Most Windows 10/11 machines have these
- **Mitigation**: Test on clean Windows VM

**Issue 2: Window Spawning**
- Even with `creationflags=CREATE_NO_WINDOW`, a window might flash
- **Status**: Already handled in code (line 445 of generate_csp.py)

**Issue 3: File Paths**
- HSDRawViewer expects exact paths
- **Status**: Handled with `to_windows_path()` function

### Testing HSDRawViewer:

After building, test CSP generation:
1. Run installer on clean Windows 10/11
2. Import a costume without a CSP
3. Check if CSP generates successfully
4. Look in logs for HSDRawViewer errors

---

## 🔧 Updated Build Process

### 1. Prepare for Distribution:

```batch
# Clean user data
rmdir /s /q storage intake logs output
```

### 2. Build:

```batch
scripts/build/build.bat
```

This now:
1. Bundles Python backend with **ALL** dependencies
2. Bundles HSDRawViewer with **ALL** .NET dependencies
3. Bundles csp_data/ with all character assets
4. Builds .NET MexCLI as self-contained
5. Creates Electron installer

### 3. Test Build:

On a **clean Windows VM** (no Python, no .NET):
1. Install `Melee Nexus Setup.exe`
2. Launch app
3. Test:
   - Creating MEX project
   - Importing costume (triggers HSDRawViewer)
   - Viewing images in vault
   - Exporting ISO

### 4. Distribute:

Upload **ONLY** `dist-electron/Melee Nexus Setup.exe` to:
- GitHub Releases
- Google Drive
- Your hosting

---

## 📊 Final Checklist

- [ ] Run `rmdir /s /q storage intake logs output` to clean user data
- [ ] Run `scripts/build/build.bat` to create installer
- [ ] Test installer on clean Windows VM
- [ ] Verify CSP generation works (HSDRawViewer)
- [ ] Verify images load in vault
- [ ] Verify MEX operations (import/export)
- [ ] Upload `Melee Nexus Setup.exe`
- [ ] Write user instructions

---

## 📝 User Installation Instructions

```markdown
# Melee Nexus - Installation

## Requirements
- Windows 10/11 (64-bit)
- ~500MB disk space
- **NO additional software needed**

## Installation
1. Download `Melee Nexus Setup.exe`
2. Run installer
3. Choose install location
4. Launch from desktop shortcut

## First Time Setup
1. Click "MEX Manager" tab
2. Either:
   - Create new project from vanilla ISO
   - Open existing .mexproj file
3. Start adding costumes!

## No Python, .NET, or Node.js Required!
Everything is bundled in the installer.
```

---

## 🐛 Known Limitations

1. **HSDRawViewer Graphics:**
   - Requires DirectX/OpenGL support
   - Should work on most Windows 10/11 machines
   - Fallback: Use provided CSP images instead

2. **File Size:**
   - Installer is ~400-500MB (Chromium + runtimes)
   - One-time download

3. **Antivirus False Positives:**
   - PyInstaller exes sometimes trigger AV
   - Solution: Code sign the exe (costs $$ for certificate)

---

## 🔍 Debugging Bundled App

If users report issues, have them check:

```
C:\Users\{user}\AppData\Roaming\Melee Nexus\logs\
```

Logs will show:
- Python backend errors
- HSDRawViewer failures
- Module import issues

---

**You're now ready to distribute! 🎉**
