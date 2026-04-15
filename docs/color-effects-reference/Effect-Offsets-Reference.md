# Effect Offsets Reference

Sources:
- [legacy offsets markdown](smashboards_offsets_reference.md)
- [structured offsets json](melee_color_offsets.json)

## Format Reference

### `CF_##`
- Color effect format with AD DF markers
- Structure: `CF [count] [color1 RGBA] AD DF [flags] [color2 RGB]`
- Note: AD DF appears to be a separator/marker

### `07_07_07`
- Basic two-color format
- Structure: `[04|07] [R1] [G1] [B1] 00 [R2] [G2] [B2]`
- Note: First byte is 04 or 07, then two RGB colors

### `42_48`
- Three-color gradient/material format
- Structure: `[R1][G1][B1][A1] [R2][G2][B2][A2] [R3][G3][B3][A3] [3E|3F] [??] [??] [??] 42 48`
- Note: Three RGBA colors, marker bytes, then 42 48 terminator

### `98_00_##_##`
- Matrix format with RGBY 16-bit colors
- Structure: `98 00 [count_hi] [count_lo] [color] FC 00 [color] FC 00 ...`
- Note: Used for lasers, shine, complex multi-color effects

### `85_80_08`
- Menu-specific two-color format
- Structure: `85 80 08 0F ... [color 1] [color 2]`
- Note: Shows up in `MnSlMap.usd` for loading-preview and NOW LOADING elements

### `random`
- Non-standard format, often just RGB values
- Structure: `Varies per effect`

## File Reference

- `PlFx.dat`: Fox (character-specific)
- `PlFc.dat`: Falco (character-specific)
- `PlMs.dat`: Marth
- `PlCa.dat`: Captain Falcon
- `PlGn.dat`: Ganondorf
- `PlKp.dat`: Bowser
- `PlDr.dat`: Dr. Mario
- `PlPe.dat`: Peach
- `PlPp.dat`: Ice Climbers
- `PlKb.dat`: Kirby
- `EfFxData.dat`: Fox/Falco shared effects, including shine and Firefox
- `EfCaData.dat`: Captain Falcon effects
- `EfGnData.dat`: Ganondorf effects
- `EfCoData.dat`: Common/shared effects, including dust and smoke
- `EfKpData.dat`: Bowser effects
- `EfKbData.dat`: Kirby effects
- `EfLgData.dat`: Luigi effects
- `EfPkData.dat`: Pikachu effects
- `PlCo.dat`: Common character data, including shields and auras

## Texture Types

- `_5`: with transparency support
- `_8`: standard texture
- `_9`: used for Firefox flame and some effects
- `_14`: used for Falcon Punch

## Body Auras / Hitbox Elements

- `Normal`: no aura
- `Fire`: fire effect on hit
- `Electric`: lightning effect on hit
- `Darkness`: dark purple aura, like Ganondorf moves

These are scattered throughout character files and `PlCo.dat`.

Warning: changing hitbox elements can cause netplay desyncs.

## Tools Mentioned

- `HxD`: hex editor; `Ctrl+K` compares files and `F6` cycles differences
- `GCRebuilder` / `GCTool`: import or export DAT files from ISO
- `Dolphin`: texture dumping; OpenGL dumps `.tga`, Direct3D11 dumps `.png`
- `DAT Texture Wizard`: DAT file editing
- `CrazyHand`: hitbox and moveset editor
- `Melee Toolkit`: general-purpose Melee tool
- `TexConv.exe` + `TCS scripts`: TPL format conversion

## Tips

- To find unknown offsets, compare edited and vanilla files in HxD and cycle through differences.
- For `98 00 ## ##`, the useful starting offset is the `98`, and the bytes at offset `+0x2` hold the color count.
- For `42 48`, the useful start is usually the `42` marker minus `0x10`.
- Firefox and shine both live in `EfFxData.dat`, so edits there often need to be merged.
- `PlFc.dat` and `PlFx.dat` changes may cause desyncs. `EfCoData.dat` and shine edits were noted as appearing safe.

## Practical Workflow

1. find a known effect mod that changes the same thing
2. diff it against vanilla
3. identify the matching format or offset block
4. verify whether the file is costume-local, character-local, or shared

## Status

- 🟢 Nucleus already has an effect mod that covers this offset block.
- 🔴 The offset is known, but the app does not expose it yet.

## Offset Data

## C. Falcon

### `EfCaData.dat`

#### `CF_##`

- 🔴 `0x12F`: Trailing Smoke Down B. Data: `FF FF FF FF AD DF 00 D2 CE 9E`
- 🔴 `0x14A`: Trailing Smoke Down B. Data: `FF FF FF FF AD DF 00 6F 66 39`
- 🔴 `0x15A`: Trailing Smoke Down B. Data: `FF FF FF FF AD DF 00 6F 66 39`
- 🔴 `0x16C`: Trailing Smoke Down B. Data: `FF FF FF B4 AD DF 00 00 00 00`
- 🔴 `0x17C`: Trailing Smoke Down B. Data: `FF FF FF 64 AD DF 00 00 00 00`
- 🔴 `0x1DA`: Trailing Smoke Neutral B. Data: `FF FF FF FF AD DF 00 FF C2 57`
- 🔴 `0x1E7`: Trailing Smoke Neutral B. Data: `FF 5A 07 FF AD DF 05 CA 00 0D`
- 🔴 `0x219`: Trailing Smoke Neutral B. Data: `00 00 00 64 AD DF 09 FF 11 19`
- 🔴 `0x29C`: Square Dots Neutral B. Data: `FF 05 1A FF AD DF 00 FF FF 82`
- 🔴 `0x2AC`: Square Dots Neutral B. Data: `FF FF 6E FF AD DF 00 FF 0C 14`
- 🔴 `0x3AC`: Smoke on wings of Neutral B. Data: `FE FF E1 FF AD DF 00 A6 04 01`
- 🔴 `0x3B9`: Smoke on wings of Neutral B. Data: `FF A8 51 FF AD DF 09 CC 0A 0D`
- 🔴 `0x3EF`: Smoke on wings of Neutral B. Data: `FF 61 0C 00 AD DF 09 00 00 00`
- 🔴 `0x474`: Square Dots Down B. Data: `FF 29 0C FF AD DF 00 FF FF 82`
- 🔴 `0x484`: Square Dots Down B. Data: `FF FF 6E FF AD DF 00 FF 0C 14`
- 🔴 `0x4DA`: Circle Dots Down B. Data: `FF FF FF FF AD DF 00 FC FF 19`
- 🔴 `0x4E6`: Circle Dots Down B. Data: `F8 62 11 00 AD DF 06 C5 09 10`
- 🔴 `0x539`: Circle Dots Down B. Data: `FF F9 DE FF AD DF 00 FF F0 11`
- 🔴 `0x58E`: Trailing Smoke Down B. Data: `FF FF FF FF AD DF 00 D2 CE 9E`
- 🔴 `0x5A9`: Trailing Smoke Down B. Data: `FF FF FF FF AD DF 00 6F 66 39`
- 🔴 `0x5B9`: Trailing Smoke Down B. Data: `FF FF FF FF AD DF 00 00 00 00`
- 🔴 `0x5CC`: Trailing Smoke Down B. Data: `FF FF FF B4 AD DF 00 00 00 00`
- 🔴 `0x5DC`: Trailing Smoke Down B. Data: `FF FF FF 64 AD DF 00 00 00 00`
- 🔴 `0x640`: Trailing Smoke Down B and After Smoke of Over B. Data: `F3 F0 94 00 AD DF 00 FF 78 17`
- 🔴 `0x64E`: Trailing Smoke Down B and After Smoke of Over B. Data: `AD 40 05 50 AD DF 07 62 06 03`
- 🔴 `0x65C`: Trailing Smoke Down B and After Smoke of Over B. Data: `DE 5A 26 00 AD DF 0F 00 00 00`
- 🔴 `0x6AF`: Front of Down B. Data: `FF FF FF FF AD DF 00 FF F3 07`
- 🔴 `0x76F`: Smoke of Over B large. Data: `CA CA CA C8 AD DF 00 C5 1D 00`
- 🔴 `0x77F`: Smoke of Over B small. Data: `FF DB 0C 64 AD DF 00 A1 08 0D`
- 🔴 `0x78F`: Smoke Behind Falcon Over B. Data: `C7 C6 B9 C8 AD DF 00 E1 D2 04`
- 🔴 `0x79F`: Smoke Behind Falcon Over B. Data: `FF AF 19 64 AD DF 00 A3 0B 0E`
- 🔴 `0x82C`: Square Dots Over B. Data: `FF 05 1A FF AD DF 00 FF FF 82`
- 🔴 `0x83C`: Square Dots Over B. Data: `FF FF 6E FF AD DF 00 FF 0C 14`
- 🔴 `0x8A0`: Square Smoke after Over B. Data: `F3 F0 94 00 AD DF 00 FF 78 17`
- 🔴 `0x8AE`: Smoke after Over B. Data: `AE 6F 57 50 AD DF 07 63 32 30`
- 🔴 `0x8BC`: Smoke after Over B. Data: `DE D4 CF 00 AD DF 0F 00 00 00`
- 🔴 `0x91A`: Smoke after neutral B. Data: `DE 8E 2B FF AD DF 00 FF 07 07`
- 🔴 `0x927`: Smoke after neutral B. Data: `FD 51 26 FF AD DF 09 A4 04 09`
- 🔴 `0x958`: Smoke after neutral B. Data: `00 00 00 64 AD DF 09 75 00 03`

#### `07_07_07`

- 🔴 `0x1DE00`: Tip of falcon kick. Data: `04 FF FF E5 00 FF B2 00`
- 🔴 `0x202E0`: Tip of falcon punch. Data: `04 FF 7F 00 00 FF 00 00`
- 🔴 `0x22D60`: Falcon punch lens flare extending lines. Data: `04 FF FF FF 00 00 7F FF`
- 🔴 `0x22E30`: Falcon punch lens flare extending lines. Data: `07 FF FF FF 00 00 7F FF`
- 🔴 `0x22EF0`: Falcon punch lens flare extending lines. Data: `04 FF FF FF 00 00 7F FF`
- 🔴 `0x22FC0`: Falcon punch lens flare extending lines. Data: `04 FF FF FF 00 00 7F FF`
- 🔴 `0x23090`: Falcon punch lens flare extending lines. Data: `04 FF FF FF 00 00 7F FF`
- 🔴 `0x23160`: Falcon punch lens flare extending lines. Data: `04 FF FF FF 00 00 7F FF`
- 🔴 `0x23220`: Falcon punch lens flare extending lines. Data: `04 FF FF FF 00 00 7F FF`
- 🔴 `0x232F0`: Falcon punch lens flare extending lines. Data: `04 FF FF FF 00 00 7F FF`
- 🔴 `0x233C0`: Falcon punch lens flare extending lines. Data: `04 FF FF FF 00 00 7F FF`
- 🔴 `0x23490`: Falcon punch lens flare extending lines. Data: `04 FF FF FF 00 00 7F FF`
- 🔴 `0x24B70`: Raptor Boost Hand Lens Flare. Data: `04 F9 FF B2 00 FF B2 00`

#### `42_48`

- 🔴 `0x22D00`: Falcon Punch Small Lens Flare Beginning. Data: `80 80 80 FF FF CC 00 FF FF FF FF FF 00 00 00 00`
- 🔴 `0x235C0`: Falcon Punch Big Lens Flare Beginning. Data: `80 80 80 FF FF 99 00 FF FF FF FF FF 00 00 00 00`
- 🔴 `0x25440`: Part of Raptor Boost Smoke. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 00 00 00 00`

## Dr. Mario

### `PlDr.dat`

#### `42_48`

- 🔴 `0x19CA0`: Cape Color. Data: `FF FF FF FF FF FF FF FF 33 33 33 FF 3F 80 00 00`

## Falco

### `PlFc.dat`

#### `42_48`

- 🔴 `0x7C00`: Inside of Falco's jacket. Data: `80 48 1F FF F7 87 2C FF FF FF FF FF 3F 80 00 00`
- 🟢 `0x1EC40`: Side B illusion. Data: `00 99 FF FF CC E6 FF FF FF FF FF FF 3E 99 99 9A`

#### `98_00_##_##`

- 🟢 `0x13440-0x13490`: Laser: wide, transparent
- 🟢 `0x134E0-0x13530`: Laser: thin, semi-transparent
- 🟢 `0x13580-0x135D0`: Laser: outline opaque
- 🔴 `0x13640-0x13680`: Laser: white center line

## Fox

### `PlFx.dat`

#### `42_48`

- 🟢 `0x22050`: Side B Illusion. Data: `00 99 FF FF CC E6 FF FF FF FF FF FF 3E 99 99 9A`

#### `98_00_##_##`

- 🟢 `0x13E20-0x13E70`: Laser: wide, transparent
- 🟢 `0x13EC0-0x13F10`: Laser: thin, semi-transparent
- 🟢 `0x13F60-0x13FB0`: Laser: outline opaque
- 🔴 `0x14000-0x14022`: Laser: Tip of middle white line
- 🔴 `0x14023-0x14060`: Laser: white center line

## Fox / Falco Shared

### `EfFxData.dat`

#### `CF_##`

- 🔴 `0x125`: Shine Sparkles. Data: `CF 00 FF FF FF FF AD DF 00 2A A3 EE`
- 🟢 `0x2EE`: Trailing Fire Large Up B. Data: `CF 00 FF FF FF`
- 🟢 `0x2F4`: Trailing Fire Large Up B. Data: `CF 18 FF FF FF`
- 🟢 `0x324`: Trailing Fire Large Up B. Data: `CF 08 FF FF FF`
- 🟢 `0x32B`: Trailing Fire Large Up B. Data: `CF 08 FF FF FF`
- 🔴 `0x383`: Trailing Fire Small Up B. Data: `CF 00 FF F8 8F FF AD DF 00 FF A9 07`
- 🔴 `0x393`: Trailing Fire Small Up B. Data: `CF 00 FF 71 11 FF AD DF 00 91 07 0B`
- 🔴 `0x3A3`: Trailing Fire Small Up B. Data: `CF 00 FF FD EE FF AD DF 00 FF EF 05`
- 🔴 `0x3B3`: Trailing Fire Small Up B. Data: `CF 00 FF 76 14 FF AD DF 00 FF 94 19`
- 🔴 `0x3C4`: Trailing Fire Small Up B. Data: `CF 08 FA 91 19 00 AD DF 08 87 05 0B`
- 🔴 `0x43A`: Square Dots Up B. Data: `CF 00 FF 29 0C FF AD DF 00 FF FF 82`
- 🔴 `0x44A`: Square Dots Up B. Data: `CF 00 FF FF 6E FF AD DF 00 FF 0C 14`
- 🔴 `0x4A9`: Trailing Smoke Over B. Data: `CF 00 7F 7F 7F B4 AD DF 00 0C 05 C1`
- 🔴 `0x5AF`: Lines Coming Off Up B Charge. Data: `CF 00 FF FF FF 64 AD DF 00 86 0A FA`
- 🟢 `0x52E`: Trailing Fire Big Up B. Data: `CF 00 FF FF FF`
- 🟢 `0x536`: Trailing Fire Big Up B. Data: `CF 18 FF FF FF`

#### `07_07_07`

- 🔴 `0x1A500`: Lens Flare of Up B in motion. Data: `04 FF E5 4C 00 FF 33 00`
- 🟢 `0x1B450`: Fire Ring for Up B. Data: `04 FF FF CC 00 FF 7F 00`
- 🟢 `0x1B520`: Fire Ring for Up B. Data: `04 FF FF 00 00 FF 33 00`

#### `98_00_##_##`

- 🟢 `0x1AC80-0x1AD00`: Tip of Firefox
- 🟢 `0x1C2A0-0x1C340`: Shine main effect
- 🟢 `0x1C8E0-0x1C990`: First Frames of Shine (inner hex, outer glow, outer border)

## Jigglypuff

### `EfPrData.dat`

#### `07_07_07`

- 🔴 `0x5440`: Red note of Sing. Data: `07 07 07 04 FF FF FF 00 FF 00 00`
- 🔴 `0x55C0`: Green note of Sing. Data: `07 07 07 04 FF FF FF 00 00 FF 00`
- 🔴 `0x5500`: Blue note of Sing. Data: `07 07 07 04 FF FF FF 00 00 00 FF`

## Kirby

### `PlKb.dat`

#### `07_07_07`

- 🔴 `0x117D0`: Up B projectile front/trail. Data: `07 07 07 04 FF FF FF 00 00 B2 FF`
- 🔴 `0x11890`: Up B other half. Data: `07 07 07 04 FF FF FF 00 00 B2 FF`

#### `42_48`

- 🔴 `0x12ABC`: Side B hammer handle. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 3F 80 00 00 42 48`
- 🔴 `0x12B5C`: Side B hammer head wood. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 3F 80 00 00 42 48`
- 🔴 `0x12BFC`: Side B hammer head star. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 3F 80 00 00 42 48`

### `EfKbData.dat`

#### `07_07_07`

- 🔴 `0xD15C`: Up B falling effect. Data: `07 07 07 04 FF FF FF 00 00 B2 FF`
- 🔴 `0xF50C`: Jab rapid color. Data: `07 07 07 04 FF FF FF 00 00 CC FF`

#### `42_48`

- 🔴 `0xC17C`: Up B spin at top. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 00 00 00 00 42 48`
- 🔴 `0xD1CC`: Up B falling colors. Data: `80 80 80 FF 00 FF FF FF FF FF FF FF 00 00 00 00 42 48`
- 🔴 `0xEC94`: Side B end effect. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 00 00 00 00 42 48`

#### `CF_##`

- 🔴 `0x1C8`: Dash Attack smoke
- 🔴 `0x1D5`: Dash Attack smoke
- 🔴 `0x1FD`: Dash Attack faint smoke
- 🔴 `0x27A`: Dash Attack square particles
- 🔴 `0x28A`: Dash Attack square particles
- 🔴 `0x37F`: Neutral B swallow particle
- 🔴 `0x38C`: Neutral B swallow particles
- 🔴 `0x3A7`: Neutral B particles
- 🔴 `0x3AD`: Neutral B particles
- 🔴 `0x42C`: Neutral B swallow particles
- 🔴 `0x439`: Neutral B swallow particles
- 🔴 `0x454`: Neutral B particles
- 🔴 `0x45A`: Neutral B particles
- 🔴 `0x51C`: Down B rocks
- 🔴 `0x529`: Down B rocks
- 🔴 `0x530`: Down B rocks
- 🔴 `0x589`: Down B halo effect
- 🔴 `0x596`: Down B inner halo
- 🔴 `0x5F1`: Down B line effect
- 🔴 `0x5FE`: Down B lines
- 🔴 `0x605`: Down B lines
- 🔴 `0x664`: Down B rocks
- 🔴 `0x671`: Down B rocks
- 🔴 `0x678`: Down B rocks
- 🔴 `0x6D4`: Down B rocks
- 🔴 `0x6E1`: Down B rocks
- 🔴 `0x6E8`: Down B rocks
- 🔴 `0x794`: Down B leaving rock
- 🔴 `0x7A1`: Down B leaving rock
- 🔴 `0x7A8`: Down B leaving rock
- 🔴 `0x801`: Down B halo leaving
- 🔴 `0x80E`: Down B halo
- 🔴 `0x815`: Down B halo
- 🔴 `0x869`: Down B ray effect
- 🔴 `0x876`: Down B ray
- 🔴 `0x87D`: Down B ray
- 🔴 `0x8DC`: Down B rocks
- 🔴 `0x8E9`: Down B rocks
- 🔴 `0x8F0`: Down B rocks
- 🔴 `0x94C`: Down B rocks
- 🔴 `0x959`: Down B rocks
- 🔴 `0x960`: Down B rocks

#### `98_00_##_##`

- 🔴 `0xB580-0xB5F5`: Dash attack front column
- 🔴 `0xB5F6-0xB657`: Dash attack second column
- 🔴 `0xB658-0xB6A5`: Dash attack last column
- 🔴 `0xC3C0-0xC416`: Up B blade 1 trailing
- 🔴 `0xC417-0xC46D`: Up B blade 1 solid
- 🔴 `0xC4C0-0xC576`: Up B blade 2
- 🔴 `0xC5C0-0xC5DE`: Up B blade 3 tip
- 🔴 `0xC5DF-0xC675`: Up B blade 3 rest
- 🔴 `0xC6C0-0xC716`: Up B blade 4 trailing
- 🔴 `0xC717-0xC75D`: Up B blade 4 solid
- 🔴 `0xC7A0-0xC7EE`: Up B shadow spin
- 🔴 `0xDA80-0xDB5A`: Up B sword color
- 🔴 `0xDB5B-0xDB99`: Up B sword handle
- 🔴 `0xDB9A-0xDBC0`: Up B handle back

## Ice Climbers

### `PlPp.dat`

#### `42_48`

- 🔴 `0xE840`: Up B Rope. Data: `B3 B3 B3 FF FF FF FF FF FF FF FF FF 3F 80 00 00`

## Link

### `PlLk.dat`

#### `random`

- 🟢 `0x35EC`: Sword Swing. Data: `FF 00 00 FF FF 00 FF FF FF`. Note: Older notes sometimes cite 0x35E0 as the line start, but the editable color bytes begin at 0x35EC

## Luigi

### `PlLg.dat`

#### `07_07_07`

- 🔴 `0xF3B8`: Fireball aura inner/outer. Data: `07 07 07 04 FF 66 00 00 FF 33 00`. Note: constrained by 42_48 at F428

#### `42_48`

- 🔴 `0xF428`: Fireball aura. Data: `80 80 80 FF 00 FF 00 FF FF FF FF FF 3F 00 00 00 42 48`
- 🔴 `0xF4C8`: Fireball color. Data: `00 00 00 FF FF FF FF FF FF FF FF FF 00 00 00 00 42 48`

### `EfLgData.dat`

#### `07_07_07`

- 🔴 `0x111E0`: Neutral B ring. Data: `07 07 07 04 CC FF E5 00 19 B2 00`
- 🔴 `0x11A70`: Tornado outer. Data: `07 07 07 04 FF FF B2 00 FF B2 00`
- 🔴 `0x11B48`: Tornado upper. Data: `07 07 07 04 FF FF B2 00 FF CC 00`
- 🔴 `0x11C14`: Tornado inner side 1. Data: `07 07 07 04 FF FF E5 00 FF FF 00`
- 🔴 `0x11CE0`: Tornado inner side 2. Data: `07 07 07 04 FF FF CC 00 FF FF 00`
- 🔴 `0x11DAC`: Tornado underneath. Data: `07 07 07 04 FF FF CC 00 FF B2 00`

#### `CF_##`

- 🔴 `0xE8`: Fireball hand smoke
- 🔴 `0xFD`: Fireball hand smoke
- 🔴 `0x10A`: Fireball smoke trail
- 🔴 `0x192`: Smoke behind fireball
- 🔴 `0x1A5`: Smoke behind fireball
- 🔴 `0x1B2`: Faint smoke behind fireball
- 🔴 `0x26B`: Fireball wall collision particles
- 🔴 `0x278`: Fireball wall collision particles
- 🔴 `0x2DB`: Fireball wall collision particles
- 🔴 `0x2E8`: Fireball particles
- 🔴 `0x350`: Fireball collision dust
- 🔴 `0x363`: Fireball collision dust
- 🔴 `0x370`: Fireball collision dust
- 🔴 `0x3FC`: Square particles behind fireball

#### `42_48`

- 🔴 `0x1125C`: Ring around hand after fireball. Data: `80 80 80 FF 66 FF 99 FF FF FF FF FF 00 00 00 00 42 48`
- 🔴 `0x11AEC`: Tornado outer ring finish. Data: `80 80 80 FF FF FF D0 FF FF FF FF FF 00 00 00 00 42 48`
- 🔴 `0x11BB8`: Tornado finish. Data: `80 80 80 FF FF FF D0 FF FF FF FF FF 00 00 00 00 42 48`
- 🔴 `0x11C84`: Tornado finish side 1. Data: `80 80 80 FF FF FF D0 FF FF FF FF FF 00 00 00 00 42 48`
- 🔴 `0x11D50`: Tornado finish side 2. Data: `80 80 80 FF FF FF D0 FF FF FF FF FF 00 00 00 00 42 48`
- 🔴 `0x11E20`: Tornado below Luigi. Data: `80 80 80 FF FF FF E3 FF FF FF FF FF 00 00 00 00 42 48`

## Mario

### `PlMr.dat`

#### `07_07_07`

- 🔴 `0xFA40`: Fireball aura inner/outer. Data: `07 07 07 04 FF 66 00 00 FF 33 00`. Note: constrained by 42_48 at FAB0

#### `42_48`

- 🔴 `0xFAB0`: Fireball aura. Data: `80 80 80 FF FF 4C 00 FF FF FF FF FF 3F 00 00 00 42 48`
- 🔴 `0xFB50`: Fireball color. Data: `00 00 00 FF FF FF FF FF FF FF FF FF 00 00 00 00 42 48`
- 🔴 `0x14EAC`: Cape back color. Data: `FF FF FF FF FF FF FF FF 33 33 33 FF 3F 80 00 00`

### `EfMrData.dat`

#### `07_07_07`

- 🔴 `0x11AF4`: Fireball hand circle. Data: `07 07 07 04 FF FF B2 00 FF 66 00`
- 🔴 `0x1237C`: Tornado outside. Data: `07 07 07 04 B2 FF FF 00 00 00 FF`
- 🔴 `0x12448`: Tornado outside. Data: `07 07 07 04 B2 FF FF 00 00 00 FF`
- 🔴 `0x12514`: Tornado inner side 1. Data: `07 07 07 04 99 CC FF 00 00 00 FF`
- 🔴 `0x125E0`: Tornado inner side 2. Data: `07 07 07 04 99 CC FF 00 00 00 FF`
- 🔴 `0x126AC`: Tornado underneath. Data: `07 07 07 04 CC FF FF 00 00 33 FF`

#### `CF_##`

- 🔴 `0x160`: Fireball hand smoke
- 🔴 `0x175`: Fireball hand smoke
- 🔴 `0x182`: Fireball hand smoke
- 🔴 `0x20A`: Trailing fire from fireball
- 🔴 `0x21D`: Trailing fire from fireball
- 🔴 `0x22A`: Trailing fire from fireball
- 🔴 `0x2E3`: Ball particles behind fireball
- 🔴 `0x2F0`: Ball particles behind fireball
- 🔴 `0x353`: Ball particles behind fireball
- 🔴 `0x360`: Particles around fireball
- 🔴 `0x3C9`: Fireball landing dust
- 🔴 `0x3DB`: Fireball landing dust
- 🔴 `0x3E8`: Fireball landing dust
- 🔴 `0x474`: Square particles behind fireball
- 🔴 `0x484`: Square particles behind fireball
- 🔴 `0x4DE`: Cape front sparkle
- 🔴 `0x4EC`: Cape front sparkle
- 🔴 `0x503`: Cape sparkle faint
- 🔴 `0x567`: Cape smaller sparkles
- 🔴 `0x62C`: Up B contact effect
- 🔴 `0x63D`: Up B contact faint
- 🔴 `0x69C`: Up B contact rays
- 🔴 `0x6A9`: Up B contact rays faint
- 🔴 `0x700`: Up B fist effect
- 🔴 `0x70D`: Up B fist effect faint

#### `42_48`

- 🔴 `0x11B64`: Ring around hand after fireball. Data: `80 80 80 FF FF FF 99 FF FF FF FF FF 00 00 00 00 42 48`
- 🔴 `0x123EC`: Tornado outer ending. Data: `80 80 80 FF FF FF D0 FF FF FF FF FF 00 00 00 00 42 48`
- 🔴 `0x124B8`: Tornado outer ending. Data: `80 80 80 FF FF FF D0 FF FF FF FF FF 00 00 00 00 42 48`
- 🔴 `0x12584`: Tornado spin side 1. Data: `80 80 80 FF FF FF D0 FF FF FF FF FF 00 00 00 00 42 48`
- 🔴 `0x12650`: Tornado spin side 2. Data: `80 80 80 FF FF FF D0 FF FF FF FF FF 00 00 00 00 42 48`
- 🔴 `0x1271B`: Tornado below Mario. Data: `80 80 80 FF FF FF E3 FF FF FF FF FF 00 00 00 00 42 48`

## Marth

### `PlMs.dat`

#### `random`

- 🟢 `0x3948`: Sword Swing. Data: `FF 00 00 FF FF 00 FF FF FF`

## Mewtwo

### `PlMt.dat`

#### `07_07_07`

- 🟢 `0x100B0`: Shadow Ball center when thrown. Data: `FF FF FF 00 00 00 FF 00`
- 🔴 `0x102D0`: Inner Shadow Ball bolt. Data: `FF FF FF 00 00 7F FF 00`
- 🔴 `0x10390`: Inner Shadow Ball bolt. Data: `FF FF FF 00 00 7F FF 00`
- 🔴 `0x10450`: Inner Shadow Ball bolt. Data: `FF FF FF 00 00 7F FF 00`
- 🔴 `0x10510`: Inner Shadow Ball bolt. Data: `FF FF FF 00 00 7F FF 00`
- 🔴 `0x105D0`: Shadow Ball center charging. Data: `FF FF FF 00 00 00 FF 00`

### `EfMtData.dat`

#### `07_07_07`

- 🔴 `0xC758`: Up Smash swirl. Data: `66 00 CC 00 00 00 00 00`
- 🔴 `0xCD30`: Forward Smash burst. Data: `FF A9 FF 00 33 00 66 00`
- 🔴 `0xCDFC`: Forward Smash burst. Data: `FF 7F FF 00 00 00 00 FF`
- 🔴 `0xD994`: Up B flash. Data: `E5 FF FF 00 66 00 66 00`
- 🔴 `0xDA54`: Up B flash. Data: `E5 FF FF 00 66 00 66 00`
- 🔴 `0xDBE0`: Up B light. Data: `FF FF FF 00 00 00 FF 00`

#### `42_48`

- 🔴 `0xC7C4`: Up Smash mist. Data: `80 80 80 FF 00 00 00 FF`
- 🔴 `0xDA00`: Up B flash right side. Data: `80 80 80 FF FF FF FF FF`
- 🔴 `0xDAC0`: Up B flash left side. Data: `80 80 80 FF FF FF FF FF`

## Ness

### `PlNs.dat`

#### `07_07_07`

- 🔴 `0x10190`: PK Fire lens flare. Data: `04 FF FF 66 00 FF E5 00`
- 🔴 `0x11A80`: PK Fire hit bottom ring inside. Data: `04 FF FF FF 00 00 7F FF`
- 🔴 `0x11B50`: PK Fire hit main fire aura. Data: `04 FF FF E5 00 FF 99 00`
- 🔴 `0x11DF0`: PK Fire hit bottom ring outside. Data: `04 FF FF FF 00 00 7F FF`
- 🔴 `0x16A10`: PK Flash charge aura. Data: `04 00 CC 00 00 00 99 00`
- 🔴 `0x16C10`: PK Flash charge center. Data: `04 FF FF FF 00 00 E5 00`
- 🔴 `0x16CD0`: PK Flash charge flash. Data: `04 FF FF FF 00 00 E5 00`
- 🔴 `0x16D90`: PK Flash charge flash. Data: `04 FF FF FF 00 00 E5 00`
- 🔴 `0x16E50`: PK Flash charge flash. Data: `04 FF FF FF 00 00 E5 00`
- 🔴 `0x16F10`: PK Flash charge flash. Data: `04 FF FF FF 00 00 E5 00`
- 🔴 `0x1D630`: PK Flash explosion. Data: `04 00 CC 00 00 00 99 00`
- 🔴 `0x1D6F0`: PK Flash explosion. Data: `04 FF FF FF 00 00 CC 00`
- 🔴 `0x1D7B0`: PK Flash explosion. Data: `04 FF FF FF 00 00 CC 00`
- 🔴 `0x1D870`: PK Flash explosion. Data: `04 FF FF FF 00 00 CC 00`
- 🔴 `0x1D930`: PK Flash explosion. Data: `04 FF FF EF 00 00 CC 00`
- 🔴 `0x1D9F0`: PK Flash explosion. Data: `04 FF FF FF 00 00 CC 00`
- 🔴 `0x1DAB0`: PK Flash explosion. Data: `04 FF FF FF 00 00 CC 00`
- 🔴 `0x1DB70`: PK Flash explosion. Data: `04 FF FF FF 00 00 4C FF`
- 🔴 `0x1DC30`: PK Flash explosion. Data: `04 FF FF FF 00 00 4C FF`
- 🔴 `0x1DCF0`: PK Flash explosion. Data: `04 FF FF FF 00 00 CC 00`
- 🔴 `0x24030`: PK Thunder tip. Data: `04 FF FF FF 00 00 4C FF`
- 🔴 `0x2C3F7`: PK Thunder tail. Data: `04 FF FF FF 00 00 4C FF`
- 🔴 `0x2C777`: PK Thunder tail. Data: `04 FF FF FF 00 00 4C FF`
- 🔴 `0x2CAF4`: PK Thunder tail main. Data: `04 FF FF FF 00 00 4C FF`
- 🔴 `0x2D3C8`: PK Thunder aura. Data: `04 FF FF FF 00 00 00 FF`
- 🔴 `0x2D528`: PK Thunder aura and ball. Data: `04 FF FF FF 00 00 00 FF`
- 🔴 `0x2D5E8`: PK Thunder lightning. Data: `04 FF FF FF 00 00 33 FF`
- 🔴 `0x2D6A8`: PK Thunder lightning. Data: `04 FF FF FF 00 00 33 FF`
- 🔴 `0x2D768`: PK Thunder lightning. Data: `04 FF FF FF 00 00 33 FF`
- 🔴 `0x2D828`: PK Thunder lightning. Data: `04 FF FF F9 00 00 66 FF`

## Peach

### `PlPe.dat`

#### `42_48`

- 🔴 `0x160A0`: Turnip Leaves. Data: `B3 B3 B3 FF FF FF FF FF FF FF FF FF 3F 80 00 00`
- 🔴 `0x16140`: Turnip Leaves. Data: `B3 B3 B3 FF FF FF FF FF FF FF FF FF 3F 80 00 00`
- 🔴 `0x161E0`: Turnip Leaves. Data: `B3 B3 B3 FF FF FF FF FF FF FF FF FF 3F 80 00 00`
- 🔴 `0x16280`: Turnip Leaves. Data: `B3 B3 B3 FF FF FF FF FF FF FF FF FF 3F 80 00 00`
- 🔴 `0x16320`: Turnip Leaves. Data: `B3 B3 B3 FF FF FF FF FF FF FF FF FF 3F 80 00 00`
- 🔴 `0x163C0`: Turnip Leaves. Data: `B3 B3 B3 FF FF FF FF FF FF FF FF FF 3F 80 00 00`
- 🔴 `0x164F0`: Turnip Color. Data: `AC B3 A6 FF F9 FF F9 FF FF FF FF FF 3F 80 00 00`
- 🔴 `0x1D890`: Umbrella Handle. Data: `B3 B3 B3 FF FF FF FF FF FF FF FF FF 3F 80 00 00`
- 🔴 `0x1D940`: Umbrella Handle. Data: `80 80 80 FF B3 B3 B3 FF FF FF FF FF 3F 80 00 00`
- 🔴 `0x1D9D0`: Umbrella Outside Bottom Border. Data: `FF FF FF FF FF FF FF FF FF FF FF FF 3F 66 66 66`
- 🔴 `0x1DA70`: Umbrella Top. Data: `FF FF FF FF FF FF FF FF FF FF FF FF 3F 80 00 00`
- 🔴 `0x1DB10`: Umbrella Inside Bottom Border. Data: `FF FF FF FF FF FF FF FF FF FF FF FF 3F 66 66 66`

### `EfPeData.dat`

#### `42_48`

- 🔴 `0xDC0`: Down B Dirt. Data: `B3 B3 B3 FF FF FF FF FF FF FF FF FF 3F 80 00 00`

## Pikachu

### `PlPk.dat`

#### `07_07_07`

- 🟢 `0xC350`: Down B Thunder. Data: `04 FF FF FF 00 FF FF 00`
- 🔴 `0x14DF0`: Ground Neutral B. Data: `04 B2 E5 FF 00 00 00 FF`
- 🔴 `0x14EC0`: Ground Neutral B. Data: `04 B2 E5 FF 00 00 00 FF`
- 🔴 `0x14F90`: Ground Neutral B. Data: `04 B2 E5 FF 00 00 00 FF`
- 🔴 `0x15060`: Ground Neutral B tail. Data: `04 B2 E5 FF 00 00 00 FF`
- 🔴 `0x151E0`: Ground Neutral B head. Data: `07 FF FF FF 00 00 4C FF`

### `EfPkData.dat`

Note: SHARED WITH PICHU

#### `CF_##`

- 🔴 `0x168`: Aerial Neutral B middle. Data: `FF FF FF C8 AD DF 00 66 81 FA`
- 🔴 `0x1D0`: Aerial Neutral B outer lens flare. Data: `0B 0B E6 C8 AD DF 00 07 07 8F`
- 🔴 `0x238`: Aerial Neutral B middle lens flare. Data: `8F D6 FF C8 AD DF 00 0C 0C FF`
- 🔴 `0x2A0`: Aerial Neutral B inner border. Data: `FE 06 1B 32 AD DF 00 FB 9E 14`
- 🔴 `0x2AC`: Aerial Neutral B inner triangles. Data: `FF FF FF FF B1 B6 04 3F C9 0F`
- 🔴 `0x35D`: Over B smoke majority. Data: `FF FF FF FF AD DF 00 F9 68 01`
- 🔴 `0x36A`: Over B outline/ending smoke. Data: `FC 8A 55 00 AD DF 10 84 00 00`
- 🔴 `0x3D8`: Over B middle lens flare. Data: `FC F8 8D FF AD DF 00 F8 CF 02`
- 🔴 `0x3E5`: Over B ending lens flare. Data: `F7 03 0B 00 AD DF 08 84 00 00`
- 🔴 `0x440`: Over B starting lens flare. Data: `FF FF FF FF AD DF 00 F8 CF 02`
- 🔴 `0x44D`: Over B lines. Data: `FD 63 68 00 AD DF 08 84 00 00`
- 🔴 `0x4A7`: Over B lines. Data: `FF FF FF FF AD DF 00 F9 68 01`
- 🔴 `0x4B0`: Over B lines. Data: `FC 8A 55 00 AD DF 0C 84 00 00`

#### `07_07_07`

- 🔴 `0x148E0`: Pre Forward Smash lightning. Data: `04 CC E5 FF 00 00 00 FF`
- 🔴 `0x14C80`: Forward Smash aura half 1. Data: `04 CC E5 FF 00 00 00 FF`
- 🔴 `0x14D40`: Forward Smash aura half 2. Data: `04 CC E5 FF 00 00 00 FF`
- 🔴 `0x14E00`: Forward Smash ball/head. Data: `04 FF FF FF 00 00 4C FF`

#### `42_48`

- 🔴 `0x13F10`: Down B Aura. Data: `FF FF FF FF FF FF FF FF FF`

## Roy

### `PlFe.dat`

#### `random`

- 🟢 `0x3AA0`: Sword Swing. Data: `FF 00 EB 78 50 00 FF FF FF`

## Young Link

### `PlCl.dat`

#### `random`

- 🟢 `0x3790`: Sword Swing. Data: `FF 00 00 FF FF 00 FF FF FF`

## Menu / Stage Select

### `MnSlChr.usd`

#### `random`

- 🔴 `0x948`: Background. Data: `80 80 80 FF 00 0B 1A FF FF FF FF`

#### `07_07_07`

- 🔴 `0x10050`: Hand color. Data: `07 FF FF FF 00 00 00 33`
- 🔴 `0x10130`: P# Outline on Hand. Data: `07 FF 33 33 00 00 00 00`
- 🔴 `0x348E88`: Bottom frame. Data: `07 07 07 07 83 8F 94 00 83 8F 94`
- 🔴 `0x348F48`: Rule. Data: `07 07 07 07 92 9E A3 00 92 9E A3`
- 🔴 `0x349008`: Top frame. Data: `07 07 07 07 83 8F 94 00 83 8F 94`

### `MnSlMap.usd`

Note: 070707 effects are often constrained by adjacent 4248 effects. Color 2 of the 4248 effect limits both 070707 colors, and setting 4248 color 2 to FFFFFF gives full control. For the 3D preview entries, color 1 only slightly nudges color 2 and is constrained by it.

#### `07_07_07`

- 🔴 `0x95A00`: STAGE SELECT text (color 1) and outline (color 2). Data: `07 07 07 07 7F 7F 7F 00 7F 7F 7F`. Note: constrained by 42_48 at 95A70
- 🔴 `0x95B78`: Wires around screen (color 1) and outline (color 2). Data: `07 07 07 04 66 66 66 00 66 66 66`. Note: constrained by 42_48 at 95BE8
- 🔴 `0x96C44`: Stage name (color 1) and outline (color 2). Data: `07 07 07 04 FF FF FF 00 FF FF FF`
- 🔴 `0x9784C`: RANDOM text (color 1) and outline (color 2). Data: `07 07 07 04 00 00 00 00 00 00 00`

#### `42_48`

- 🔴 `0x6D1B0`: Blue background texture layer. Data: `80 80 80 FF FD FB FF FF FF FF FF FF 3F 7F BE 77 42 48`. Note: Set alpha to 00 to remove the blue background texture
- 🔴 `0x6D250`: Background images on stage select. Data: `80 80 80 FF B3 B3 B3 FF FF FF FF FF 3E 99 99 9A 42 48`. Note: Set alpha to 00 to remove the background images
- 🔴 `0x6D2F0`: Square grid in background (color 2). Data: `66 80 80 FF 99 B3 B3 FF E6 FF FF FF 3F 00 00 00 42 48`. Note: Change 3F to 00 to hide grid
- 🔴 `0x6EE1C`: Stage select cursor (color 2). Data: `80 80 80 FF 99 B3 B3 FF FF FF FF FF 3F 7F BE 77 42 48`
- 🔴 `0x6F0FC`: Flashing outline around hovered stage icon (color 2). Data: `FF FF FF FF FF FF FF FF FF FF FF FF 3F 7F BE 77 42 48`. Note: Flash 1 uses only the red channel from color 2. Flash 2 uses the full color 2 value. Example: 00FF00 gives a black first flash and green second flash
- 🔴 `0x78B24`: Kongo Jungle wooden poles 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x78BC4`: Kongo Jungle platforms 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x78C64`: Kongo Jungle floor 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x78D04`: Jungle Japes 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x78DA4`: Mushroom Kingdom II 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x78E44`: Mushroom Kingdom 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x78EE4`: Fountain of Dreams top platform 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x78F84`: Fountain of Dreams main platform 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79024`: Fountain of Dreams flares under platform 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x790C4`: Fountain of Dreams waterfall 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79164`: Green Greens 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79204`: Dream Land 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x792A4`: Peach's Castle main 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79344`: Peach's Castle platform 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x793E4`: Peach's Castle top 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79484`: Peach's Castle other parts 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79524`: Peach's Castle drawbridge 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x795C4`: Peach's Castle peak 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79664`: Onett buildings 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79704`: Fourside 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x797A4`: Rainbow Cruise 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79844`: Brinstar 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x798E4`: Brinstar Depths 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79984`: Temple 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79A24`: Yoshi's Island 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79AC4`: Yoshi's Story 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79B64`: Yoshi's Island 64 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79C04`: Kongo Jungle 64 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79CA4`: Big Blue top 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79D44`: Mute City outer loop 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79DE4`: Mute City main track 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79E84`: Flat Zone 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79F24`: Venom/Corneria 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x79FC4`: Icicle Mountain 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x7A064`: Great Bay sphere 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x7A105`: Great Bay turtle 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x7A1A4`: All 3D preview bases. Data: `00 00 66 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x7A264`: Loading logo 3D preview. Data: `FF FF FF FF FF FF FF FF FF FF FF FF 3F 7F BE 77 42 48`
- 🔴 `0x7A304`: Pokemon Stadium 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x7A3A4`: Poke Floats 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x7A444`: Battlefield 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x7A4E4`: Final Destination 3D preview. Data: `00 33 99 FF 00 4C B3 FF 80 CC FF FF 3F 80 00 00 42 48`
- 🔴 `0x95A70`: STAGE SELECT text constraint. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 00 00 00 00 42 48`. Note: Set color 2 to FFFFFF, then use 95A00 for separate text and outline control
- 🔴 `0x95B1C`: Circular STAGE SELECT. Data: `80 80 80 FF CC CC CC FF FF FF FF FF 00 00 00 00 42 48`
- 🔴 `0x95BE8`: Wires around screen constraint. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 3F 7F BE 77 42 48`. Note: Set color 2 to FFFFFF, then use 95B78 for separate inner and outer wire control
- 🔴 `0x960D4`: Stage icon rows 2 and 4. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 3F 7F BE 77 42 48`. Note: Set alpha to 00000000 to gray out rows 2 and 4
- 🔴 `0x96174`: Some stage portrait outlines. Data: `80 80 80 FF CC CC CC FF FF FF FF FF 3F 7F BE 77 42 48`
- 🔴 `0x96234`: Stage icon rows 1 and 3. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 3F 7F BE 77 42 48`. Note: Set alpha to 00000000 to gray out rows 1 and 3
- 🔴 `0x96CB4`: Stage name color. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 3F 7F BE 77 42 48`
- 🔴 `0x97404`: Bottom row icons. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 3F 7F BE 77 42 48`. Note: Set alpha to 00000000 to gray out bottom row
- 🔴 `0x974A4`: Unknown. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 3F 7F BE 77 42 48`
- 🔴 `0x978BC`: RANDOM text constraint. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 3F 7F BE 77 42 48`. Note: Constrains the 070707 text and outline colors at 9784C
- 🔴 `0x9795C`: RANDOM box color. Data: `80 80 80 FF FF CC CC FF FF FF FF FF 3F 7F BE 77 42 48`
- 🔴 `0x97C04`: Icicle Mountain/Flat Zone icons. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 3F 7F BE 77 42 48`. Note: Set alpha to 00000000 to gray out
- 🔴 `0x97CA4`: Unknown. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 3F 7F BE 77 42 48`
- 🔴 `0x98130`: NOW LOADING screen tint after stage select (color 2). Data: `80 80 80 FF 00 00 00 FF FF FF FF FF 00 00 00 00 42 48`
- 🔴 `0x981F0`: Unknown. Data: `80 80 80 FF FF FF FF FF FF FF FF FF 3F 7F BE 77 42 48`

#### `85_80_08`

- 🔴 `0x7A1F0`: Loading logo 3D preview brightness. Data: `85 80 08 0F 07 43 04 07 96 96 96 FF 96 96 96`. Note: Both colors affect the brightness of the loading logo 3D preview at 7A264
- 🔴 `0x98180`: NOW LOADING text (color 1) and text box (color 2). Data: `85 80 08 0F 44 43 04 07 FF CC 33 FF 00 00 00`

## Pause

### `GmPause.usd`

#### `42_48`

- 🔴 `0x1234`: Bottom Right border. Data: `80 80 80 FF FF 00 FF FF FF 00 FF FF 3F 7F BE 77 42 48`
- 🔴 `0x12E0`: Bottom Left border. Data: `80 80 80 FF FF 00 FF FF FF 00 FF FF 3F 7F BE 77 42 48`
- 🔴 `0x138C`: Top Left border. Data: `80 80 80 FF FF 00 FF FF FF 00 FF FF 3F 7F BE 77 42 48`

#### `98_00_##_##`

- 🔴 `0x1FAB-0x1FAD`: + sign between A and St, RESET bar corner
- 🔴 `0x1FDB-0x1FFF`: L button
