"""
Global state management for the MEX API backend.

Contains mutable global state (mex_manager, project paths, viewer process)
and functions to access/modify them safely.
"""

from pathlib import Path
import sys
import logging

# Add mex_bridge to path
from .config import PROJECT_ROOT

sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "tools"))
from mex_bridge import MexManager, MexManagerError

from .config import MEXCLI_PATH

logger = logging.getLogger(__name__)

# Global MEX manager instance and current project path
_mex_manager = None
_current_project_path = None

# Global 3D viewer process
_viewer_process = None
_viewer_port = None

# SocketIO instance (set by main app)
_socketio = None


def get_socketio():
    """Get the SocketIO instance."""
    return _socketio


def set_socketio(socketio):
    """Set the SocketIO instance."""
    global _socketio
    _socketio = socketio


def get_viewer_process():
    """Get the viewer process."""
    return _viewer_process


def set_viewer_process(process):
    """Set the viewer process."""
    global _viewer_process
    _viewer_process = process


def get_viewer_port():
    """Get the viewer port."""
    return _viewer_port


def set_viewer_port(port):
    """Set the viewer port."""
    global _viewer_port
    _viewer_port = port


def get_current_project_path():
    """Get the current project path."""
    return _current_project_path


def get_mex_manager():
    """Get or initialize MEX manager instance."""
    global _mex_manager, _current_project_path

    if _current_project_path is None:
        raise Exception("No MEX project loaded. Please open a project first.")

    if _mex_manager is None:
        try:
            _mex_manager = MexManager(
                cli_path=str(MEXCLI_PATH),
                project_path=str(_current_project_path)
            )
        except MexManagerError as e:
            raise Exception(f"Failed to initialize MexManager: {e}")
    return _mex_manager


def set_project_path(path):
    """Set the current project path and reset manager."""
    global _mex_manager, _current_project_path
    _current_project_path = Path(path)
    _mex_manager = None  # Reset manager so it reinitializes with new path


def reload_mex_manager():
    """Force reload of MEX manager to pick up file changes."""
    global _mex_manager
    _mex_manager = None


def get_project_files_dir():
    """Get the files/ directory for the currently loaded project."""
    if _current_project_path is None:
        raise Exception("No MEX project loaded. Please open a project first.")
    return _current_project_path.parent / "files"
