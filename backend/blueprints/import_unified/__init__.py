"""
Import Unified Blueprint package - Unified file import endpoint.

Handles importing both character costumes and stage mods from ZIP/7z files,
with auto-detection and slippi safety validation.

All routes register on the single `import_bp` blueprint defined here, split
across cohesive submodules:

    helpers.py     filename sanitizing, DAT hashing, duplicate detection
    characters.py  character costume import + Ice Climbers pairing
    stages.py      stage mod import
    effects.py     effect/model mod import (extras system)
    routes.py      the unified /api/mex/import/file endpoint

`from blueprints.import_unified import import_bp` (and the helper API used by
iso_scan.py) keeps working exactly as it did when this was a single
import_unified.py module.
"""

from flask import Blueprint

import_bp = Blueprint('import', __name__)

# Import route module so its routes register on import_bp. This import must
# come after import_bp is defined.
from . import routes  # noqa: E402,F401

# Re-export the public surface so existing `from blueprints.import_unified
# import ...` statements keep working (e.g. iso_scan.py uses
# import_character_costume and fix_ice_climbers_pairing).
from .helpers import (  # noqa: E402,F401
    sanitize_filename,
    compute_dat_hash,
    compute_hash_from_stored_skin,
    check_duplicate_skin,
    check_duplicate_stage,
    check_duplicate_patch,
    check_duplicate_effect,
    extract_custom_name_from_filename,
)
from .characters import fix_ice_climbers_pairing, import_character_costume  # noqa: E402,F401
from .stages import import_stage_mod  # noqa: E402,F401
from .effects import _import_effect_mod  # noqa: E402,F401
from .routes import import_file  # noqa: E402,F401

__all__ = [
    'import_bp',
    'sanitize_filename',
    'compute_dat_hash',
    'compute_hash_from_stored_skin',
    'check_duplicate_skin',
    'check_duplicate_stage',
    'check_duplicate_patch',
    'check_duplicate_effect',
    'extract_custom_name_from_filename',
    'fix_ice_climbers_pairing',
    'import_character_costume',
    'import_stage_mod',
    'import_file',
]
