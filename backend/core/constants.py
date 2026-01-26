"""
Constants for the MEX API backend.

Contains character prefixes, vanilla costume counts, and other static data.
"""

# Character code mapping for costume lookup
# Maps character display name to their 2-letter code
CHAR_PREFIXES = {
    "C. Falcon": "Ca", "Falco": "Fc", "Fox": "Fx",
    "Marth": "Ms", "Roy": "Fe", "Bowser": "Kp",
    "DK": "Dk", "Ganondorf": "Gn", "Jigglypuff": "Pr",
    "Kirby": "Kb", "Link": "Lk", "Luigi": "Lg",
    "Mario": "Mr", "Mewtwo": "Mt", "Ness": "Ns",
    "Peach": "Pe", "Pichu": "Pc", "Pikachu": "Pk",
    "Ice Climbers": "Pp", "Samus": "Ss", "Sheik": "Sk",
    "Yoshi": "Ys", "Young Link": "Cl", "Zelda": "Zd",
    "Dr. Mario": "Dr", "G&W": "Gw"
}


def get_char_prefix(character):
    """Get the Pl prefix for a character (e.g., Fox -> PlFx)"""
    code = CHAR_PREFIXES.get(character)
    return f"Pl{code}" if code else None


# Vanilla Melee has 128 total costumes across all fighters
# (26 playable + Nana + Master Hand)
VANILLA_COSTUME_COUNT = 128

# MD5 hash of vanilla NTSC 1.02 Melee ISO
VANILLA_ISO_MD5 = "0e63d4223b01d9aba596259dc155a174"

# Stage names mapping (add if needed in the future)
STAGE_NAMES = {}
