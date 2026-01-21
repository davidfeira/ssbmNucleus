"""
Extra types configuration for character-specific mods.
Each extra type defines editable properties that modify specific dat file offsets.
Python mirror of frontend config with additional patching information.
"""

# Extra type definitions per character
# NOTE: Offsets are character-specific - do not copy between characters
EXTRA_TYPES = {
    "Falco": [
        {
            "id": "laser",
            "name": "Laser Color",
            "description": "Change laser beam colors",
            "target_file": "PlFc.dat",
            # Offset definitions for the 98 matrix format (Falco-specific)
            "offsets": {
                "wide": {"start": 0x13440, "end": 0x134A0, "format": "RGBY"},
                "thin": {"start": 0x134E0, "end": 0x13540, "format": "RGBY"},
                "outline": {"start": 0x13580, "end": 0x135E0, "format": "RGBY"}
            },
            # Vanilla/default colors (Falco's red laser)
            "vanilla": {
                "wide": "FC00",
                "thin": "FC00",
                "outline": "FC00"
            },
            "properties": [
                {"id": "wide", "name": "Wide Layer", "description": "Transparent outer glow"},
                {"id": "thin", "name": "Thin Layer", "description": "Semi-transparent middle"},
                {"id": "outline", "name": "Outline", "description": "Opaque inner core"}
            ]
        },
        {
            "id": "sideb",
            "name": "Side-B Color",
            "description": "Phantasm afterimage colors",
            "target_file": "PlFc.dat",
            "format": "42_48",
            # 42_48 format: 3 RGBA colors at a single offset
            "offsets": {
                "primary": {"start": 0x1EC48, "size": 4, "format": "RGBA"},
                "secondary": {"start": 0x1EC4C, "size": 4, "format": "RGBA"},
                "tertiary": {"start": 0x1EC50, "size": 4, "format": "RGBA"}
            },
            "vanilla": {
                "primary": "0099FFFF",
                "secondary": "CCE6FFFF",
                "tertiary": "FFFFFFFF"
            },
            "properties": [
                {"id": "primary", "name": "Primary", "description": "Main afterimage color"},
                {"id": "secondary", "name": "Secondary", "description": "Edge/gradient color"},
                {"id": "tertiary", "name": "Glow", "description": "Outer glow color"}
            ]
        },
        {
            "id": "gun",
            "name": "Gun Model",
            "description": "Replace Falco's blaster gun model",
            "target_file": "PlFc.dat",
            "type": "model",  # Model type - uses .dae file instead of hex patches
            "model_path": "ftDataFalco/Articles/Articles_1/Model_/RootModelJoint",
            "icon": "gun"
        }
    ],
    "Marth": [
        {
            "id": "sword",
            "name": "Sword Trail",
            "description": "Sword swing trail colors",
            "target_file": "PlMs.dat",
            # 9 bytes: 3x RGB colors for sword trail gradient
            "offsets": {
                "main": {"start": 0x3948, "size": 3, "format": "RGB"},
                "secondary": {"start": 0x394B, "size": 3, "format": "RGB"},
                "tertiary": {"start": 0x394E, "size": 3, "format": "RGB"}
            },
            "vanilla": {
                "main": "FF0000",      # Red
                "secondary": "FFFF00", # Yellow
                "tertiary": "FFFFFF"   # White
            },
            "properties": [
                {"id": "main", "name": "Main", "description": "Primary trail color", "format": "RGB"},
                {"id": "secondary", "name": "Secondary", "description": "Middle gradient color", "format": "RGB"},
                {"id": "tertiary", "name": "Edge", "description": "Outer edge color", "format": "RGB"}
            ]
        }
    ],
    "Roy": [
        {
            "id": "sword",
            "name": "Sword Trail",
            "description": "Sword swing trail colors",
            "target_file": "PlFe.dat",
            "offsets": {
                "main": {"start": 0x3AA0, "size": 3, "format": "RGB"},
                "secondary": {"start": 0x3AA3, "size": 3, "format": "RGB"},
                "tertiary": {"start": 0x3AA6, "size": 3, "format": "RGB"}
            },
            "vanilla": {
                "main": "FF00EB",      # Magenta/Pink
                "secondary": "785000", # Brown/Orange
                "tertiary": "FFFFFF"   # White
            },
            "properties": [
                {"id": "main", "name": "Main", "description": "Primary trail color", "format": "RGB"},
                {"id": "secondary", "name": "Secondary", "description": "Middle gradient color", "format": "RGB"},
                {"id": "tertiary", "name": "Edge", "description": "Outer edge color", "format": "RGB"}
            ]
        }
    ],
    "Link": [
        {
            "id": "sword",
            "name": "Sword Trail",
            "description": "Sword swing trail colors",
            "target_file": "PlLk.dat",
            "offsets": {
                "main": {"start": 0x35EC, "size": 3, "format": "RGB"},
                "secondary": {"start": 0x35EF, "size": 3, "format": "RGB"},
                "tertiary": {"start": 0x35F2, "size": 3, "format": "RGB"}
            },
            "vanilla": {
                "main": "FF0000",      # Red
                "secondary": "FFFF00", # Yellow
                "tertiary": "FFFFFF"   # White
            },
            "properties": [
                {"id": "main", "name": "Main", "description": "Primary trail color", "format": "RGB"},
                {"id": "secondary", "name": "Secondary", "description": "Middle gradient color", "format": "RGB"},
                {"id": "tertiary", "name": "Edge", "description": "Outer edge color", "format": "RGB"}
            ]
        }
    ],
    "Young Link": [
        {
            "id": "sword",
            "name": "Sword Trail",
            "description": "Sword swing trail colors",
            "target_file": "PlCl.dat",
            "offsets": {
                "main": {"start": 0x3790, "size": 3, "format": "RGB"},
                "secondary": {"start": 0x3793, "size": 3, "format": "RGB"},
                "tertiary": {"start": 0x3796, "size": 3, "format": "RGB"}
            },
            "vanilla": {
                "main": "FF0000",      # Red
                "secondary": "FFFF00", # Yellow
                "tertiary": "FFFFFF"   # White
            },
            "properties": [
                {"id": "main", "name": "Main", "description": "Primary trail color", "format": "RGB"},
                {"id": "secondary", "name": "Secondary", "description": "Middle gradient color", "format": "RGB"},
                {"id": "tertiary", "name": "Edge", "description": "Outer edge color", "format": "RGB"}
            ]
        }
    ],
    "Pikachu": [
        {
            "id": "thunder",
            "name": "Thunder",
            "description": "Down-B Thunder bolt colors",
            "target_file": "PlPk.dat",
            "format": "07_07_07",
            "shared": True,
            "sharedWith": ["Pichu"],
            "owner": "Pikachu",
            # 07 07 07 04 format at 0xC354
            "offsets": {
                "color1": {"start": 0xC358, "size": 3, "format": "RGB"},
                "color2": {"start": 0xC35C, "size": 3, "format": "RGB"}
            },
            "vanilla": {
                "color1": "FFFFFF",  # White
                "color2": "FFFF00"   # Yellow
            },
            "properties": [
                {"id": "color1", "name": "Primary", "description": "Main bolt color", "format": "RGB"},
                {"id": "color2", "name": "Secondary", "description": "Bolt glow color", "format": "RGB"}
            ]
        }
    ],
    "Mewtwo": [
        {
            "id": "shadow_ball",
            "name": "Shadow Ball",
            "description": "Shadow Ball colors",
            "target_file": "PlMt.dat",
            "format": "direct_rgb",
            # Direct RGB format - no marker, just R1G1B1 00 R2G2B2 00
            "offsets": {
                "color1": {"start": 0x100B0, "size": 3, "format": "RGB"},
                "color2": {"start": 0x100B4, "size": 3, "format": "RGB"}
            },
            "vanilla": {
                "color1": "FFFFFF",  # White
                "color2": "0000FF"   # Blue
            },
            "properties": [
                {"id": "color1", "name": "Primary", "description": "Main ball color", "format": "RGB"},
                {"id": "color2", "name": "Secondary", "description": "Inner glow color", "format": "RGB"}
            ]
        }
    ],
    "Fox": [
        {
            "id": "laser",
            "name": "Laser Color",
            "description": "Change laser beam colors",
            "target_file": "PlFx.dat",
            # Offset definitions for the 98 matrix format (Fox-specific)
            "offsets": {
                "wide": {"start": 0x13E20, "end": 0x13E80, "format": "RGBY"},
                "thin": {"start": 0x13EC0, "end": 0x13F20, "format": "RGBY"},
                "outline": {"start": 0x13F60, "end": 0x13FC0, "format": "RGBY"}
            },
            # Vanilla/default colors (Fox's green laser)
            "vanilla": {
                "wide": "FC00",
                "thin": "FC00",
                "outline": "FC00"
            },
            "properties": [
                {"id": "wide", "name": "Wide Layer", "description": "Transparent outer glow"},
                {"id": "thin", "name": "Thin Layer", "description": "Semi-transparent middle"},
                {"id": "outline", "name": "Outline", "description": "Opaque inner core"}
            ]
        },
        {
            "id": "sideb",
            "name": "Side-B Color",
            "description": "Illusion afterimage colors",
            "target_file": "PlFx.dat",
            "format": "42_48",
            # 42_48 format: 3 RGBA colors at a single offset
            "offsets": {
                "primary": {"start": 0x2204C, "size": 4, "format": "RGBA"},
                "secondary": {"start": 0x22050, "size": 4, "format": "RGBA"},
                "tertiary": {"start": 0x22054, "size": 4, "format": "RGBA"}
            },
            "vanilla": {
                "primary": "0099FFFF",
                "secondary": "CCE6FFFF",
                "tertiary": "FFFFFFFF"
            },
            "properties": [
                {"id": "primary", "name": "Primary", "description": "Main afterimage color"},
                {"id": "secondary", "name": "Secondary", "description": "Edge/gradient color"},
                {"id": "tertiary", "name": "Glow", "description": "Outer glow color"}
            ]
        },
        {
            "id": "upb",
            "name": "Up-B Color",
            "description": "Firefox/Firebird flame colors",
            "target_file": "EfFxData.dat",
            "shared": True,  # Shared between Fox and Falco
            "sharedWith": ["Falco"],  # Characters that share this extra
            "owner": "Fox",  # Which character owns the mods in storage
            "offsets": {
                # 98 matrix format for flame tip (mixed color/position data - needs safe mode)
                "tip": {"start": 0x1AC80, "end": 0x1AD00, "format": "RGBY", "vanilla": "FE60"},
                # 98 matrix format for firefox body when not textured
                "body": {"start": 0x1A880, "end": 0x1AA50, "format": "RGB", "vanilla": "FFFFFF"},
                # CF format - trailing fire (all sizes combined)
                # CF XX RR GG BB - color at offset+2
                "trail": {
                    "format": "CF",
                    "offsets": [
                        0x2EE, 0x2F4, 0x324, 0x32B,  # Large trailing fire
                        0x52E, 0x534  # Big trailing fire
                    ]
                },
                # 07 07 07 04 format - fire rings
                # Pattern: 07 07 07 04 RR GG BB 00 RR GG BB - colors at +4 and +8
                "rings": {
                    "format": "070707",
                    "offsets": [0x1B454, 0x1B520]  # Actual marker positions
                }
            },
            "vanilla": {
                "tip": "FE60",      # Fire orange (RGBY)
                "body": "FFFFFF",   # White (RGB)
                "trail": "FFFFFF",  # White (RGB)
                "rings": "FFFF00"   # Yellow (RGB) - from FF FF CC / FF 7F 00
            },
            "properties": [
                {"id": "tip", "name": "Flame Tip", "description": "Fire effect at the tip (RGBY)"},
                {"id": "body", "name": "Body Glow", "description": "Firefox body when charging"},
                {"id": "trail", "name": "Trail Fire", "description": "Trailing fire particles"},
                {"id": "rings", "name": "Fire Rings", "description": "Circular fire rings"}
            ]
        },
        {
            "id": "upb_texture",
            "name": "Up-B Fire Texture",
            "description": "Firefox/Firebird flame color (hue shift)",
            "target_file": "EfFxData.dat",
            "type": "texture",  # Texture type - uses hue shift instead of hex patches
            "texture_path": "effFoxDataTable/Models_4_/RootJoint",
            "texture_index": 1,  # 2nd texture (index 1) is the fire texture
            "shared": True,  # Shared between Fox and Falco
            "sharedWith": ["Falco"],
            "owner": "Fox",
            "vanilla_hue": 15,  # Orange-red, detected from vanilla texture
            "properties": [
                {"id": "hue", "name": "Hue", "description": "Fire color hue (0-360)", "type": "slider", "min": 0, "max": 360}
            ]
        },
        {
            "id": "shine",
            "name": "Shine Color",
            "description": "Reflector shield colors (two-color gradient)",
            "target_file": "EfFxData.dat",
            "shared": True,  # Shared between Fox and Falco
            "sharedWith": ["Falco"],  # Characters that share this extra
            "owner": "Fox",  # Which character owns the mods in storage
            "format": "shine_gradient",  # Special two-color gradient format
            "offsets": {
                # 98 matrix format for main hexagon shape - contains two alternating colors
                "hex": {"start": 0x1C2A0, "end": 0x1C350, "format": "RGBY"}
            },
            # Two-color vanilla pattern: primary (bright edge) and secondary (fill)
            # These are the colors that appear in the hex region in alternating pattern
            "vanilla": {
                "primary": "621F",    # Bright blue edge/outline vertices
                "secondary": "AB9F"   # Grayish fill/interior vertices
            },
            "properties": [
                {"id": "primary", "name": "Primary (Edge)", "description": "Bright edge/outline color", "format": "RGBY"},
                {"id": "secondary", "name": "Secondary (Fill)", "description": "Fill/interior color", "format": "RGBY"}
            ]
        },
        {
            "id": "laser_ring",
            "name": "Laser Ring",
            "description": "Laser hit ring effect colors",
            "target_file": "EfFxData.dat",
            "shared": True,
            "sharedWith": ["Falco"],
            "owner": "Fox",
            # Two RGB colors + 6 hue index bytes that must be zeroed
            "offsets": {
                "color1": {"start": 0x1D2FC, "size": 3, "format": "RGB"},
                "color2": {"start": 0x1D300, "size": 3, "format": "RGB"},
                # Hue index bytes - set to 00 for custom colors
                "hue1": {"start": 0x1D974, "size": 1, "format": "BYTE"},
                "hue2": {"start": 0x1D988, "size": 1, "format": "BYTE"},
                "hue3": {"start": 0x1D99C, "size": 1, "format": "BYTE"},
                "hue4": {"start": 0x1D9B0, "size": 1, "format": "BYTE"},
                "hue5": {"start": 0x1D9C4, "size": 1, "format": "BYTE"},
                "hue6": {"start": 0x1D9D8, "size": 1, "format": "BYTE"}
            },
            "vanilla": {
                "color1": "FF004C",
                "color2": "B20000",
                "hue1": "0C",
                "hue2": "0D",
                "hue3": "0E",
                "hue4": "10",
                "hue5": "11",
                "hue6": "12"
            },
            "properties": [
                {"id": "color1", "name": "Primary", "description": "Main ring color", "format": "RGB"},
                {"id": "color2", "name": "Secondary", "description": "Secondary ring color", "format": "RGB"}
            ]
        },
        {
            "id": "gun",
            "name": "Gun Model",
            "description": "Replace Fox's blaster gun model",
            "target_file": "PlFx.dat",
            "type": "model",  # Model type - uses .dae file instead of hex patches
            "model_path": "ftDataFox/Articles/Articles_1/Model_/RootModelJoint",
            "icon": "gun"
        }
    ]
}

# Character to dat file prefix mapping
CHAR_DAT_PREFIX = {
    "C. Falcon": "PlCa",
    "Falco": "PlFc",
    "Fox": "PlFx",
    "Marth": "PlMs",
    "Roy": "PlFe",
    "Bowser": "PlKp",
    "DK": "PlDk",
    "Ganondorf": "PlGn",
    "Jigglypuff": "PlPr",
    "Kirby": "PlKb",
    "Link": "PlLk",
    "Luigi": "PlLg",
    "Mario": "PlMr",
    "Mewtwo": "PlMt",
    "Ness": "PlNs",
    "Peach": "PlPe",
    "Pichu": "PlPc",
    "Pikachu": "PlPk",
    "Ice Climbers": "PlPp",
    "Samus": "PlSs",
    "Sheik": "PlSk",
    "Yoshi": "PlYs",
    "Young Link": "PlCl",
    "Zelda": "PlZd",
    "Dr. Mario": "PlDr",
    "G&W": "PlGw"
}


def has_extras(character):
    """Check if a character has any extras available (including shared)."""
    if character in EXTRA_TYPES and len(EXTRA_TYPES[character]) > 0:
        return True
    # Check if any other character has shared extras for this character
    for other_char, extras in EXTRA_TYPES.items():
        for extra in extras:
            if extra.get('shared') and character in extra.get('sharedWith', []):
                return True
    return False


def get_extra_types(character):
    """Get all extra types for a character, including shared extras from other characters."""
    # Start with the character's own extras
    result = list(EXTRA_TYPES.get(character, []))

    # Add shared extras from other characters
    for other_char, extras in EXTRA_TYPES.items():
        if other_char == character:
            continue
        for extra in extras:
            if extra.get('shared') and character in extra.get('sharedWith', []):
                # Include the shared extra (it's already configured with owner info)
                result.append(extra)

    return result


def get_extra_type(character, type_id):
    """Get a specific extra type by id (including shared extras)."""
    # Use get_extra_types which includes shared extras
    types = get_extra_types(character)
    for t in types:
        if t["id"] == type_id:
            return t
    return None


def get_storage_character(character, extra_type):
    """Get the character to use for storage (owner for shared extras).

    For shared extras, mods are stored under the owner character.
    This ensures only one set of mods exists for shared effects.
    """
    type_config = get_extra_type(character, extra_type)
    if type_config and type_config.get('shared'):
        return type_config.get('owner', character)
    return character
