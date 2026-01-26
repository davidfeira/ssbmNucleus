"""
Blueprint modules for the MEX API backend.

Each blueprint handles a specific area of functionality.
"""

from .assets import assets_bp
from .project import project_bp
from .costumes import costumes_bp
from .export import export_bp
from .storage_costumes import storage_costumes_bp
from .storage_stages import storage_stages_bp
from .vault_backup import vault_backup_bp
from .mod_export import mod_export_bp
from .import_unified import import_bp
from .das import das_bp
from .poses import poses_bp
from .setup import setup_bp
from .slippi import slippi_bp
from .xdelta import xdelta_bp
from .bundles import bundles_bp
from .viewer import viewer_bp

__all__ = [
    'assets_bp',
    'project_bp',
    'costumes_bp',
    'export_bp',
    'storage_costumes_bp',
    'storage_stages_bp',
    'vault_backup_bp',
    'mod_export_bp',
    'import_bp',
    'das_bp',
    'poses_bp',
    'setup_bp',
    'slippi_bp',
    'xdelta_bp',
    'bundles_bp',
    'viewer_bp',
]
