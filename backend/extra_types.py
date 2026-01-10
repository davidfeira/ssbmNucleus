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
                "wide": {"start": 0x13440, "end": 0x13490},
                "thin": {"start": 0x134E0, "end": 0x13530},
                "outline": {"start": 0x13580, "end": 0x135D0}
            },
            "properties": [
                {"id": "wide", "name": "Wide Layer", "description": "Transparent outer glow"},
                {"id": "thin", "name": "Thin Layer", "description": "Semi-transparent middle"},
                {"id": "outline", "name": "Outline", "description": "Opaque inner core"}
            ]
        }
    ]
    # Fox laser offsets would be different - add when discovered
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
    """Check if a character has any extras available."""
    return character in EXTRA_TYPES and len(EXTRA_TYPES[character]) > 0


def get_extra_types(character):
    """Get all extra types for a character."""
    return EXTRA_TYPES.get(character, [])


def get_extra_type(character, type_id):
    """Get a specific extra type by id."""
    types = EXTRA_TYPES.get(character, [])
    for t in types:
        if t["id"] == type_id:
            return t
    return None
