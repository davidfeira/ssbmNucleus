"""
MEX API Backend - Flask server for MexManager operations.

Main entry point that initializes the Flask app, registers all blueprints,
and handles startup/shutdown.
"""

import os
import sys
import signal
import atexit
import logging
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

# Import core configuration
from core.config import (
    PROJECT_ROOT, STORAGE_PATH, LOGS_PATH, MEXCLI_PATH,
    MEX_PROJECT_PATH, HSDRAW_EXE
)
from core.state import set_socketio, get_viewer_process, set_viewer_process
from core.helpers import cleanup_output_folder, migrate_legacy_character_names, backfill_dat_hashes

# Import all blueprints
from blueprints import (
    assets_bp,
    project_bp,
    costumes_bp,
    export_bp,
    storage_costumes_bp,
    storage_stages_bp,
    vault_backup_bp,
    mod_export_bp,
    import_bp,
    das_bp,
    poses_bp,
    setup_bp,
    slippi_bp,
    xdelta_bp,
    bundles_bp,
    viewer_bp,
)

# Import extras API (existing blueprint)
from extras_api import extras_bp, init_extras_api
from core.state import get_project_files_dir

# Create Flask app
app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {"origins": "*"},
    r"/vanilla/*": {"origins": "*"},
    r"/utility/*": {"origins": "*"},
    r"/storage/*": {"origins": "*"},
    r"/assets/*": {"origins": "*"}
})

# Configure SocketIO - threading mode works in both dev and bundled
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
set_socketio(socketio)

# Ensure directories exist
STORAGE_PATH.mkdir(exist_ok=True)
LOGS_PATH.mkdir(exist_ok=True)
MEX_PROJECT_PATH.parent.mkdir(exist_ok=True)

# Configure logging
log_file = LOGS_PATH / f"mex_api_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Clean up output folder on startup
cleanup_output_folder()

# Initialize extras API with dependencies
init_extras_api(STORAGE_PATH, get_project_files_dir, HSDRAW_EXE)

# Register all blueprints
app.register_blueprint(extras_bp)
app.register_blueprint(assets_bp)
app.register_blueprint(project_bp)
app.register_blueprint(costumes_bp)
app.register_blueprint(export_bp)
app.register_blueprint(storage_costumes_bp)
app.register_blueprint(storage_stages_bp)
app.register_blueprint(vault_backup_bp)
app.register_blueprint(mod_export_bp)
app.register_blueprint(import_bp)
app.register_blueprint(das_bp)
app.register_blueprint(poses_bp)
app.register_blueprint(setup_bp)
app.register_blueprint(slippi_bp)
app.register_blueprint(xdelta_bp)
app.register_blueprint(bundles_bp)
app.register_blueprint(viewer_bp)


# SocketIO connection handlers
@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    print('Client connected')


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    print('Client disconnected')


def cleanup_on_exit():
    """Cleanup function called on exit."""
    logger.info("Cleaning up MEX API Backend...")

    # Stop viewer if running
    viewer_process = get_viewer_process()
    if viewer_process is not None:
        try:
            viewer_process.terminate()
            viewer_process.wait(timeout=2)
        except:
            viewer_process.kill()
        set_viewer_process(None)

    logger.info("MEX API Backend shutdown complete")


def signal_handler(sig, frame):
    """Handle termination signals."""
    logger.info(f"Received signal {sig}")
    cleanup_on_exit()
    sys.exit(0)


if __name__ == '__main__':
    print(f"Starting MEX API Backend...")
    print(f"MexCLI: {MEXCLI_PATH}")
    print(f"Default Project: {MEX_PROJECT_PATH}")
    print(f"Storage: {STORAGE_PATH}")

    # Verify MexCLI exists
    if not MEXCLI_PATH.exists():
        print(f"ERROR: MexCLI not found at {MEXCLI_PATH}")
        print("Please build it first: cd utility/MexManager/MexCLI && dotnet build -c Release")
        sys.exit(1)

    # Register cleanup handlers
    atexit.register(cleanup_on_exit)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    if hasattr(signal, 'SIGBREAK'):
        # Windows-specific signal
        signal.signal(signal.SIGBREAK, signal_handler)

    # Run migration for legacy character names
    print("Checking for legacy character names to migrate...")
    migrate_legacy_character_names()

    # Backfill dat_hash for duplicate detection
    print("Checking for skins missing dat_hash...")
    backfill_dat_hashes()

    # No auto-loading - user must select a project
    print(f"INFO: MEX Manager ready. Please open a project to get started.")

    # Run the Flask app
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)
