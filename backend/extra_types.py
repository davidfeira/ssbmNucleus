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
                # 98 matrix format for flame tip
                "tip": {"start": 0x1AC80, "end": 0x1AD00, "format": "RGBY"},
                # 98 matrix format for firefox body when not textured
                "body": {"start": 0x1A880, "end": 0x1AA50, "format": "RGB"},
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
            "id": "shine",
            "name": "Shine Color",
            "description": "Reflector shield colors",
            "target_file": "EfFxData.dat",
            "shared": True,  # Shared between Fox and Falco
            "sharedWith": ["Falco"],  # Characters that share this extra
            "owner": "Fox",  # Which character owns the mods in storage
            "offsets": {
                # 98 matrix format for main hexagon shape
                "hex": {"start": 0x1C2A0, "end": 0x1C350, "format": "RGBY"},
                # 98 matrix format for inner glow
                "inner": {"start": 0x1C860, "end": 0x1C8D0, "format": "RGBY"},
                # 98 matrix format for outer glow (multiple matrices, same color)
                "outer": {
                    "format": "98_multi",
                    "ranges": [
                        {"start": 0x1C8E0, "end": 0x1C920},
                        {"start": 0x1C91F, "end": 0x1C960},
                        {"start": 0x1C95E, "end": 0x1C9A0}
                    ]
                },
                # 42_48 format for transparent bubble
                "bubble": {"start": 0x1B4C4, "format": "42_48", "size": 12}
            },
            "vanilla": {
                "hex": "621F",       # Blue-ish (RGBY)
                "inner": "63FF",     # Blue (RGBY)
                "outer": "63FF",     # Blue (RGBY)
                "bubble": "808080FFFFFFFFFFFFFFFFFF"  # Gray/white gradient (3x RGBA)
            },
            "properties": [
                {"id": "hex", "name": "Hexagon", "description": "Main shield shape", "format": "RGBY"},
                {"id": "inner", "name": "Inner Glow", "description": "Inner glow effect", "format": "RGBY"},
                {"id": "outer", "name": "Outer Glow", "description": "Outer flash effect", "format": "RGBY"},
                {"id": "bubble", "name": "Bubble", "description": "Transparent bubble overlay", "format": "42_48"}
            ]
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
