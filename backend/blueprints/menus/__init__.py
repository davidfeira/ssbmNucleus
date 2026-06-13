"""
Menus Blueprint package - Menu mod management (CSS / SSS).

All routes register on the single `menus_bp` blueprint defined here, split
across cohesive submodules:

    helpers.py      shared constants, path layout, catalog/mod.json persistence
    icons.py        CSS icon grid mods (import / edit / install)
    backgrounds.py  menu background mods (shared CSS/SSS pool)
    sss.py          SSS layout editor + stage icons
    layout.py       CSS layout editor + fighter icons
    doors.py        CSS door textures
    pause.py        pause screen (GmPause) texture mods
    percent.py      percent font / HUD (IfAll) texture mods

`from blueprints.menus import menus_bp` (and the icon-grid installer API used
by import_unified.py) keeps working exactly as it did when this was a single
menus.py module.
"""

from flask import Blueprint

menus_bp = Blueprint('menus', __name__)

# Import submodules so their routes register on menus_bp. Order mirrors the
# original single-file layout (icon grid → backgrounds → SSS → CSS layout →
# doors). These imports must come after menus_bp is defined.
from . import icons        # noqa: E402,F401
from . import backgrounds  # noqa: E402,F401
from . import sss          # noqa: E402,F401
from . import layout       # noqa: E402,F401
from . import doors        # noqa: E402,F401
from . import pause        # noqa: E402,F401
from . import percent      # noqa: E402,F401

# Re-export the public installer APIs (used by import_unified.py).
from .icons import install_icon_grid_mod, looks_like_icon_grid_zip  # noqa: E402,F401
from .pause import install_pause_mods_from_zip, looks_like_pause_zip  # noqa: E402,F401
from .percent import install_percent_mods_from_zip, looks_like_percent_zip  # noqa: E402,F401

__all__ = ['menus_bp', 'install_icon_grid_mod', 'looks_like_icon_grid_zip',
           'install_pause_mods_from_zip', 'looks_like_pause_zip',
           'install_percent_mods_from_zip', 'looks_like_percent_zip']
