# Melee Costume Manager

A comprehensive system for organizing, managing, and browsing Super Smash Bros. Melee character costume mods with automatic detection, CSP generation, and a web viewer interface.

## Features

- **Automatic Character Detection**: Identifies character and color from DAT files
- **Smart Asset Matching**: Finds and pairs CSP/stock icons with costumes
- **CSP Generation**: Creates character portraits from DAT files when missing
- **Vanilla Asset Integration**: Uses official Melee assets as fallbacks
- **Web Viewer**: Browse your costume collection in a browser
- **Organized Storage**: Packages everything into clean, organized zip files
- **Metadata Tracking**: Complete history and source tracking for all skins

## Quick Start

### 1. Setup

Ensure you have:
- Python 3.6+
- Node.js (for web viewer)
- Your MEX build data in `build/`

First-time setup:
```bash
# Organize vanilla Melee assets (one-time setup)
python scripts/organize_vanilla_assets.py

# Install viewer dependencies
cd viewer
npm install
cd ..
```

### 2. Add Costumes

Drop your mod files into the `intake/` folder:
- **Required**: `.dat` file (character costume)
- **Optional**: CSP image (character select portrait)
- **Optional**: Stock icon

Missing files will be automatically handled!

### 3. Process Costumes

```bash
# Process all files in intake
python manage_storage.py

# Dry run (preview without making changes)
python manage_storage.py --dry-run
```

### 4. View Collection

```bash
# Start web viewer
cd viewer
npm run dev
```

Then open http://localhost:3000 in your browser!

## Directory Structure

```
melee-costume-manager/
├── intake/                 # Drop mod files here
│   ├── PlFxGr.dat
│   ├── csp_green_fox.png
│   └── ...
├── storage/                # Organized packaged skins
│   ├── metadata.json       # Master metadata
│   ├── Fox/
│   │   ├── fox-green-001.zip
│   │   └── ...
│   └── ...
├── viewer/                 # Web interface
│   ├── public/
│   │   ├── storage/        # Extracted CSPs/stocks
│   │   └── vanilla/        # Vanilla Melee assets
│   └── src/
├── utility/                # Detection and generation tools
│   └── assets/
│       └── vanilla/        # Organized vanilla assets
├── build/                  # Your MEX build data
├── logs/                   # Operation logs
├── scripts/                # Utility scripts
│   ├── organize_vanilla_assets.py
│   ├── migrate_to_intake.py
│   └── ...
├── manage_storage.py       # Main costume processor
└── clear_storage.py        # Storage cleanup tool
```

## Main Commands

### Storage Management

```bash
# Process intake folder
python manage_storage.py

# Clear all storage
python clear_storage.py

# Clear storage and intake
python clear_storage.py --clear-intake

# Clear everything including logs
python clear_storage.py --all
```

### Web Viewer

```bash
# Start development server
cd viewer && npm run dev

# Build for production
cd viewer && npm run build
```

### Utilities

```bash
# Organize vanilla Melee assets (one-time setup)
python scripts/organize_vanilla_assets.py

# Migrate old costume files
python scripts/migrate_to_intake.py <source_folder>
```

## How It Works

### Asset Priority System

When processing a costume, the system follows this priority:

**For CSPs:**
1. Look for matching CSP in intake folder
2. Generate from DAT file using HSDRawViewer
3. Use vanilla Melee CSP (matched by costume code)
4. Skip (costume will have no CSP)

**For Stock Icons:**
1. Look for matching stock in intake folder
2. Use vanilla Melee stock (matched by costume code)
3. Use default template from `utility/csp_data/`
4. Skip (costume will have no stock)

### Character Detection

The system analyzes DAT files to extract:
- **Character**: Fox, Falco, Marth, etc.
- **Color**: Default, Red, Blue, Green, Orange, etc.
- **Costume Code**: PlFxGr, PlFcBu, PlMsRe, etc.

Detection works with:
- All 26 vanilla Melee characters
- Custom MEX characters (if in build data)
- Modded costume variants

### Vanilla Assets

The system includes official Melee assets for all characters:
- CSPs (character select portraits)
- Stock icons (all colors)

Location: `utility/assets/vanilla/{Character}/{CostumeCode}/`

These are used as fallbacks and displayed on the viewer homepage.

## Web Viewer

The viewer provides a visual interface to browse your costume collection.

### Features

- **Character Grid**: View all 26 vanilla characters with their vanilla CSPs
- **Costume Browser**: Click a character to see all custom costumes
- **CSP/Stock Display**: View both CSP and stock icon for each costume
- **Source Tracking**: See where each asset came from (provided/generated/vanilla)
- **Metadata Display**: View costume details, colors, and filenames

### Homepage

The homepage shows all 26 vanilla Melee characters with their official CSPs:
- Characters with custom costumes show skin count
- Characters without customs show "0 skins" but are clickable
- Consistent vanilla aesthetic

### Character Detail

Click any character to see:
- All custom costumes for that character
- CSP and stock icon for each
- Color, ID, and source information
- Original filenames

## Package Format

Each costume is packaged as a zip file containing:

```
fox-green-001.zip
├── PlFxGrMod.dat    # Costume data (renamed for uniqueness)
├── csp.png          # Character select portrait
└── stc.png          # Stock icon (24x24)
```

Compatible with MEX import formats.

## Metadata Tracking

`storage/metadata.json` tracks comprehensive information:

```json
{
  "version": "1.0",
  "characters": {
    "Fox": {
      "skins": [
        {
          "id": "fox-green-001",
          "filename": "fox-green-001.zip",
          "character": "Fox",
          "color": "Green",
          "dat_name": "PlFxGrMod.dat",
          "costume_code": "PlFxGr",
          "has_csp": true,
          "has_stock": true,
          "csp_source": "generated",
          "stock_source": "vanilla",
          "date_added": "2025-10-27T15:39:18.123456",
          "original_files": {
            "dat": "PlFxGr.dat",
            "csp": "PlFxGr_csp.png",
            "stock": "stock.png"
          }
        }
      ]
    }
  }
}
```

### Source Types

- **provided**: File was in intake folder
- **generated**: Created from DAT file
- **vanilla**: Official Melee asset
- **default**: Template from csp_data

## Examples

### Complete Mod (DAT + CSP + Stock)

```bash
# 1. Add files to intake
cp path/to/PlFxGr.dat intake/
cp path/to/green_fox_csp.png intake/
cp path/to/green_stock.png intake/

# 2. Process
python manage_storage.py

# Result: storage/Fox/fox-green-001.zip
# CSP source: provided
# Stock source: provided
```

### DAT Only

```bash
# 1. Add just DAT file
cp path/to/PlLgNr.dat intake/

# 2. Process
python manage_storage.py

# Result: storage/Luigi/luigi-default-001.zip
# CSP source: generated (from DAT)
# Stock source: vanilla (PlLgNr stock icon)
```

### Batch Import

```bash
# 1. Drop multiple costumes
cp ~/Downloads/fox-pack/* intake/
cp ~/Downloads/falco-skins/* intake/

# 2. Process once
python manage_storage.py

# Result: All organized by character
# storage/Fox/fox-*.zip
# storage/Falco/falco-*.zip
```

## Tips

### File Naming

For best automatic matching, include costume codes in filenames:
- ✅ `PlFxGr_custom.dat`
- ✅ `csp_PlFxGr.png`
- ✅ `stock_PlFxGr.png`
- ❌ `random_name.dat`

### CSP Files

- Should be PNG format
- Include "csp" in filename or contain costume code
- Recommended size: 128x160 pixels

### Stock Icons

- Must be exactly 24x24 pixels
- PNG format with transparency
- Should match costume code

### Managing Storage

```bash
# Clear and reimport everything
python clear_storage.py
python manage_storage.py

# Clear intake after successful import
rm intake/*.dat intake/*.png
```

## Troubleshooting

### "Could not detect character"
- Ensure DAT is a character costume (not stage/item)
- Check file isn't corrupted
- Verify MEX build data exists in `build/`

### "CSP generation failed"
- Falls back to vanilla CSP
- Check HSDRawViewer is built in `utility/backend/tools/HSDLib/`
- Some custom characters may lack animation data

### Stock icons wrong color
- Stocks now use vanilla assets by default
- For custom colors, provide stock in intake
- Vanilla stocks auto-match costume code (PlFxOr→orange, PlFxGr→green)

### Viewer not updating
- Hard refresh browser (Ctrl+Shift+R)
- Check `viewer/public/storage/metadata.json` exists
- Restart dev server: `cd viewer && npm run dev`

## Technical Details

### CSP Generation

Uses HSDRawViewer for 3D rendering:
1. Load DAT file
2. Apply character-specific animation
3. Set camera angle from `csp_data/{Character}/`
4. Render at 128x160 resolution
5. Apply character-specific overlays (Fox gun, etc.)

### Stock Workflow

No longer generates stocks - uses vanilla assets:
1. Check intake folder for stock
2. If not found, use vanilla stock matching costume code
3. Fallback to default template if vanilla not available

### Vanilla Assets Organization

Run once to set up:
```bash
python scripts/organize_vanilla_assets.py
```

Extracts all CSPs and stocks from `build/assets/` into:
```
utility/assets/vanilla/
├── Fox/
│   ├── PlFxNr/
│   │   ├── csp.png
│   │   └── stock.png
│   ├── PlFxOr/
│   └── ...
├── Luigi/
└── ...
```

## Supported Characters

All 26 vanilla Melee characters plus MEX additions:
- Mario, DK, Link, Samus, Yoshi, Kirby, Fox, Pikachu
- Peach, Bowser, Ice Climbers, Sheik, Zelda
- Dr. Mario, Pichu, Falco, Marth, Young Link
- Ganondorf, Mewtwo, Roy, Mr. Game & Watch
- Ness, Luigi, Jigglypuff
- Plus any custom fighters in your build!

## Development

### Project Stack

- **Backend**: Python 3 (costume processing)
- **Frontend**: React + Vite (web viewer)
- **Detection**: Custom DAT parser
- **Generation**: HSDRawViewer (C#)
- **Assets**: Vanilla Melee resources

### Repository Structure

```
Main Scripts (root):
- manage_storage.py     # Primary costume processor
- clear_storage.py      # Storage management

Utility Scripts (scripts/):
- organize_vanilla_assets.py  # One-time setup
- migrate_to_intake.py        # Import old files
- extract_csps.py            # Legacy extractor
- package_costumes.py        # Legacy packager
```

## Credits

- **DAT Detection**: Based on [meleeWebsite](https://github.com/davidfeira/meleeWebsite) tools
- **CSP Generation**: HSDRawViewer rendering pipeline
- **Vanilla Assets**: Super Smash Bros. Melee (Nintendo/HAL Laboratory)

## License

For personal use with Super Smash Bros. Melee mods. Assets and character data are property of Nintendo/HAL Laboratory.
