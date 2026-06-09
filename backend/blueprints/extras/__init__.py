"""
Extras API - Character effect color modifications (lasers, side-B, shine, etc.),
3D model replacements, and hue-shifted textures.

Package layout:
- helpers.py:  module-level state (set via init_extras_api), dynamic offset
               detection, and DAT color patching helpers
- colors.py:   color extras routes + apply_extras_patches()
- models.py:   model extras routes + model extract/import via HSDRawViewer
- textures.py: texture extras routes + texture export/import/hue shifting
"""

from flask import Blueprint

# Blueprint for extras routes (same blueprint name as the old extras_api module)
extras_bp = Blueprint('extras', __name__)

from .helpers import init_extras_api

# Import submodules so their routes register on extras_bp
from . import colors  # noqa: E402,F401
from . import models  # noqa: E402,F401
from . import textures  # noqa: E402,F401

# Re-export the public surface used by other modules
from .colors import apply_extras_patches  # noqa: E402,F401
from .models import extract_model_from_dat, import_model_to_dat  # noqa: E402,F401

__all__ = [
    'extras_bp',
    'init_extras_api',
    'apply_extras_patches',
    'extract_model_from_dat',
    'import_model_to_dat',
]
