# Reference Files

This folder contains reference materials for understanding Melee costume modding.

## Structure

### `costume-examples/`
Sample costume files demonstrating proper file naming and structure:
- `PlFxNr.dat` - Fox neutral costume (vanilla)
- `PlFxNr sm4sh fox.dat` - Custom costume with descriptive name
- `PlFxNr_csp.png` - Character Select Portrait for costume
- `csp_*.png` - CSP images with costume name prefixes

### Vanilla Game Assets
The vanilla (unmodified) Melee files are located in `build/files/` - this is the extracted game data used by the MEX project. Key folders:
- `Pl*.dat` - Character model/costume files
- `Ef*.dat` - Effect data files
- `Gr*.dat` - Stage files
- `audio/` - Sound effects and music

## File Naming Conventions

Costume files follow the pattern: `Pl[CharCode][ColorCode].dat`

**Character Codes** (2 letters):
- Fx = Fox, Fc = Falco, Ca = Captain Falcon
- Ms = Marth, Sh = Sheik, Lk = Link
- Pk = Pikachu, Jg = Jigglypuff, Pc = Pichu
- (See MELEE_MODDING.md for full list)

**Color Codes** (2 letters):
- Nr = Neutral (default), Re = Red, Bu = Blue
- Gr = Green, Or = Orange/Yellow, La = Lavender/Purple
- (Varies by character)
