"""
Viewer Blueprint - 3D model viewer endpoints.

Handles starting, stopping, and getting paths for the 3D model viewer.
"""

import os
import json
import time
import socket
import shutil
import zipfile
import tempfile
import subprocess
import urllib.request
import logging
from pathlib import Path
from flask import Blueprint, request, jsonify

from core.config import STORAGE_PATH, VANILLA_ASSETS_DIR, HSDRAW_EXE, LOGS_PATH, PROCESSOR_DIR, get_subprocess_args
from core.state import get_viewer_process, set_viewer_process, get_viewer_port, set_viewer_port

logger = logging.getLogger(__name__)

viewer_bp = Blueprint('viewer', __name__)


# Character prefixes for AJ files
VIEWER_CHAR_PREFIXES = {
    "C. Falcon": "PlCa", "Falco": "PlFc", "Fox": "PlFx",
    "Marth": "PlMs", "Roy": "PlFe", "Bowser": "PlKp",
    "DK": "PlDk", "Ganondorf": "PlGn", "Jigglypuff": "PlPr",
    "Kirby": "PlKb", "Link": "PlLk", "Luigi": "PlLg",
    "Mario": "PlMr", "Mewtwo": "PlMt", "Ness": "PlNs",
    "Peach": "PlPe", "Pichu": "PlPc", "Pikachu": "PlPk",
    "Ice Climbers": "PlPp", "Samus": "PlSs", "Sheik": "PlSk",
    "Yoshi": "PlYs", "Young Link": "PlCl", "Zelda": "PlZd",
    "Dr. Mario": "PlDr", "G&W": "PlGw"
}


def to_windows_path(path):
    """Convert paths for Windows if running in WSL"""
    path_str = str(path)
    if os.name != 'nt' and path_str.startswith('/mnt/'):
        # Convert WSL path to Windows path
        drive = path_str[5].upper()
        return f"{drive}:{path_str[6:]}".replace('/', '\\')
    return path_str


def find_scene_file(character):
    """Find a scene file for a character"""
    csp_data_dir = PROCESSOR_DIR / "csp_data" / character

    if csp_data_dir.exists():
        # Try scene.yml first (most common)
        if (csp_data_dir / "scene.yml").exists():
            return csp_data_dir / "scene.yml"
        else:
            # Look for any .yml file (cspfinal.yml, CSP.yml, etc.)
            yml_files = sorted(csp_data_dir.glob("*.yml"))
            if yml_files:
                return yml_files[0]

    return None


def find_aj_file(character):
    """Find the AJ (animation archive) file for a character"""
    if character in VIEWER_CHAR_PREFIXES:
        prefix = VIEWER_CHAR_PREFIXES[character]
        aj_path = VANILLA_ASSETS_DIR / character / f"{prefix}AJ.dat"
        if aj_path.exists():
            return aj_path
    return None


def stop_existing_viewer():
    """Stop any existing viewer process"""
    viewer_process = get_viewer_process()
    if viewer_process is not None:
        try:
            viewer_process.terminate()
            viewer_process.wait(timeout=2)
        except:
            viewer_process.kill()
        set_viewer_process(None)
        set_viewer_port(None)


def find_available_port():
    """Find an available port"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def wait_for_server(port, max_wait=15, poll_interval=0.5):
    """Wait for viewer server to be ready"""
    for _ in range(int(max_wait / poll_interval)):
        time.sleep(poll_interval)

        viewer_process = get_viewer_process()
        if viewer_process is None:
            return False, 'Viewer was stopped during startup'

        if viewer_process.poll() is not None:
            stdout, stderr = viewer_process.communicate()
            set_viewer_process(None)
            return False, f'Viewer failed to start: {stderr.decode() if stderr else stdout.decode()}'

        try:
            req = urllib.request.urlopen(f'http://localhost:{port}/', timeout=1)
            if req.status == 200:
                return True, None
        except:
            pass

    return False, 'Viewer failed to start within timeout'


@viewer_bp.route('/api/viewer/start', methods=['POST'])
def start_viewer():
    """Start the 3D model viewer for a costume"""
    try:
        data = request.json
        character = data.get('character')
        skin_id = data.get('skinId')

        if not character or not skin_id:
            return jsonify({'success': False, 'error': 'Missing character or skinId'}), 400

        # Stop any existing viewer
        stop_existing_viewer()

        # Find the costume in metadata
        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'No costumes in storage'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        # Find the costume
        characters = metadata.get('characters', {})
        if character not in characters:
            return jsonify({'success': False, 'error': f'Character {character} not found'}), 404

        skins = characters[character].get('skins', [])
        costume = None
        for skin in skins:
            if skin.get('id') == skin_id:
                costume = skin
                break

        if costume is None:
            return jsonify({'success': False, 'error': f'Costume {skin_id} not found'}), 404

        # Get the ZIP file path
        zip_path = STORAGE_PATH / character / costume['filename']
        if not zip_path.exists():
            return jsonify({'success': False, 'error': f'Costume file not found: {zip_path}'}), 404

        # Extract DAT file to temp location
        temp_dir = Path(tempfile.mkdtemp(prefix='viewer_'))
        dat_path = None

        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if name.lower().endswith('.dat'):
                    zf.extract(name, temp_dir)
                    dat_path = temp_dir / name
                    break

        if dat_path is None or not dat_path.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            return jsonify({'success': False, 'error': 'No DAT file found in costume'}), 404

        # Check if HSDRawViewer exists
        if not HSDRAW_EXE.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            return jsonify({
                'success': False,
                'error': f'HSDRawViewer not found at {HSDRAW_EXE}. Please build it first.'
            }), 500

        # Find an available port
        viewer_port = find_available_port()

        # Convert paths
        exe_path = to_windows_path(HSDRAW_EXE)
        dat_windows_path = to_windows_path(dat_path)
        logs_windows_path = to_windows_path(LOGS_PATH)

        # Find scene file
        scene_path = find_scene_file(character)
        scene_windows_path = to_windows_path(scene_path) if scene_path else None

        # Find AJ file
        aj_path = find_aj_file(character)
        aj_windows_path = to_windows_path(aj_path) if aj_path else None

        # Build command
        cmd = [exe_path, '--stream', str(viewer_port), dat_windows_path, logs_windows_path]
        if scene_windows_path:
            cmd.append(scene_windows_path)
        else:
            cmd.append('')  # Empty placeholder for scene file
        if aj_windows_path:
            cmd.append(aj_windows_path)

        logger.info(f"Starting viewer: {' '.join(cmd)}")

        # Start the viewer process
        viewer_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **get_subprocess_args()
        )
        set_viewer_process(viewer_process)
        set_viewer_port(viewer_port)

        # Wait for server to be ready
        ready, error = wait_for_server(viewer_port)

        if not ready:
            if get_viewer_process():
                get_viewer_process().kill()
                set_viewer_process(None)
            return jsonify({'success': False, 'error': error}), 500

        return jsonify({
            'success': True,
            'port': viewer_port,
            'wsUrl': f'ws://localhost:{viewer_port}/'
        })

    except Exception as e:
        logger.error(f"Start viewer error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@viewer_bp.route('/api/viewer/paths', methods=['POST'])
def get_viewer_paths():
    """Get file paths for embedded 3D viewer (no streaming, just paths for Electron IPC)"""
    try:
        data = request.json
        character = data.get('character')
        skin_id = data.get('skinId')

        if not character or not skin_id:
            return jsonify({'success': False, 'error': 'Missing character or skinId'}), 400

        # Find the costume in metadata
        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'No costumes in storage'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        # Find the costume
        characters = metadata.get('characters', {})
        if character not in characters:
            return jsonify({'success': False, 'error': f'Character {character} not found'}), 404

        skins = characters[character].get('skins', [])
        costume = None
        for skin in skins:
            if skin.get('id') == skin_id:
                costume = skin
                break

        if costume is None:
            return jsonify({'success': False, 'error': f'Costume {skin_id} not found'}), 404

        # Get the ZIP file path
        zip_path = STORAGE_PATH / character / costume['filename']
        if not zip_path.exists():
            return jsonify({'success': False, 'error': f'Costume file not found: {zip_path}'}), 404

        # Extract DAT file to temp location
        temp_dir = Path(tempfile.mkdtemp(prefix='viewer_'))
        dat_path = None

        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if name.lower().endswith('.dat'):
                    zf.extract(name, temp_dir)
                    dat_path = temp_dir / name
                    break

        if dat_path is None or not dat_path.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            return jsonify({'success': False, 'error': 'No DAT file found in costume'}), 404

        # Convert paths
        dat_windows_path = to_windows_path(dat_path)
        logs_windows_path = to_windows_path(LOGS_PATH)

        # Find scene file
        scene_path = find_scene_file(character)
        scene_windows_path = to_windows_path(scene_path) if scene_path else None

        # Find AJ file
        aj_path = find_aj_file(character)
        aj_windows_path = to_windows_path(aj_path) if aj_path else None

        return jsonify({
            'success': True,
            'datFile': dat_windows_path,
            'sceneFile': scene_windows_path,
            'ajFile': aj_windows_path,
            'logsPath': logs_windows_path,
            'tempDir': str(temp_dir)  # For cleanup later if needed
        })

    except Exception as e:
        logger.error(f"Get viewer paths error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@viewer_bp.route('/api/mex/viewer/paths-vanilla', methods=['POST'])
def get_viewer_paths_vanilla():
    """Get file paths for vanilla costume viewer (Electron IPC, no spawning)"""
    try:
        data = request.json
        character = data.get('character')
        costume_code = data.get('costumeCode')  # e.g., "PlFxNr"

        if not character or not costume_code:
            return jsonify({'success': False, 'error': 'Missing character or costumeCode'}), 400

        # Find the DAT file in vanilla assets
        dat_path = VANILLA_ASSETS_DIR / character / costume_code / f"{costume_code}.dat"
        if not dat_path.exists():
            return jsonify({'success': False, 'error': f'Vanilla costume not found: {dat_path}'}), 404

        dat_windows_path = to_windows_path(dat_path)
        logs_windows_path = to_windows_path(LOGS_PATH)

        # Find scene file
        scene_path = find_scene_file(character)
        scene_windows_path = to_windows_path(scene_path) if scene_path else None

        # Find AJ file
        aj_path = find_aj_file(character)
        aj_windows_path = to_windows_path(aj_path) if aj_path else None

        return jsonify({
            'success': True,
            'datFile': dat_windows_path,
            'sceneFile': scene_windows_path,
            'ajFile': aj_windows_path,
            'logsPath': logs_windows_path
        })

    except Exception as e:
        logger.error(f"Get vanilla viewer paths error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@viewer_bp.route('/api/mex/viewer/paths-vault', methods=['POST'])
def get_viewer_paths_vault():
    """Get file paths for vault costume viewer (Electron IPC, no spawning)"""
    try:
        data = request.json
        character = data.get('character')
        costume_id = data.get('costumeId')

        if not character or not costume_id:
            return jsonify({'success': False, 'error': 'Missing character or costumeId'}), 400

        # Find the costume in the vault
        char_storage = STORAGE_PATH / character
        zip_path = char_storage / f"{costume_id}.zip"

        if not zip_path.exists():
            return jsonify({'success': False, 'error': f'Costume not found in vault: {costume_id}'}), 404

        # Extract DAT file to temp location
        temp_dir = Path(tempfile.mkdtemp(prefix='viewer_vault_'))
        dat_path = None

        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if name.endswith('.dat'):
                    zf.extract(name, temp_dir)
                    dat_path = temp_dir / name
                    break

        if not dat_path or not dat_path.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
            return jsonify({'success': False, 'error': 'No DAT file found in costume archive'}), 400

        dat_windows_path = to_windows_path(dat_path)
        logs_windows_path = to_windows_path(LOGS_PATH)

        # Find scene file
        scene_path = find_scene_file(character)
        scene_windows_path = to_windows_path(scene_path) if scene_path else None

        # Find AJ file
        aj_path = find_aj_file(character)
        aj_windows_path = to_windows_path(aj_path) if aj_path else None

        return jsonify({
            'success': True,
            'datFile': dat_windows_path,
            'sceneFile': scene_windows_path,
            'ajFile': aj_windows_path,
            'logsPath': logs_windows_path,
            'tempDir': str(temp_dir)
        })

    except Exception as e:
        logger.error(f"Get vault viewer paths error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@viewer_bp.route('/api/mex/viewer/start-vanilla', methods=['POST'])
def start_viewer_vanilla():
    """Start the 3D model viewer for a vanilla costume (for skin creator)"""
    try:
        data = request.json
        character = data.get('character')
        costume_code = data.get('costumeCode')  # e.g., "PlFxNr"

        if not character or not costume_code:
            return jsonify({'success': False, 'error': 'Missing character or costumeCode'}), 400

        # Stop any existing viewer
        stop_existing_viewer()

        # Find the DAT file in vanilla assets
        dat_path = VANILLA_ASSETS_DIR / character / costume_code / f"{costume_code}.dat"
        if not dat_path.exists():
            return jsonify({'success': False, 'error': f'Vanilla costume not found: {dat_path}'}), 404

        # Check if HSDRawViewer exists
        if not HSDRAW_EXE.exists():
            return jsonify({
                'success': False,
                'error': f'HSDRawViewer not found at {HSDRAW_EXE}. Please build it first.'
            }), 500

        # Find an available port
        viewer_port = find_available_port()

        exe_path = to_windows_path(HSDRAW_EXE)
        dat_windows_path = to_windows_path(dat_path)
        logs_windows_path = to_windows_path(LOGS_PATH)

        # Find scene file
        scene_path = find_scene_file(character)
        scene_windows_path = to_windows_path(scene_path) if scene_path else None

        # Find AJ file
        aj_path = find_aj_file(character)
        aj_windows_path = to_windows_path(aj_path) if aj_path else None

        # Build command
        cmd = [exe_path, '--stream', str(viewer_port), dat_windows_path, logs_windows_path]
        if scene_windows_path:
            cmd.append(scene_windows_path)
        else:
            cmd.append('')
        if aj_windows_path:
            cmd.append(aj_windows_path)

        logger.info(f"Starting vanilla viewer: {' '.join(cmd)}")

        # Start the viewer process
        viewer_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **get_subprocess_args()
        )
        set_viewer_process(viewer_process)
        set_viewer_port(viewer_port)

        # Wait for server to be ready
        ready, error = wait_for_server(viewer_port)

        if not ready:
            if get_viewer_process():
                get_viewer_process().kill()
                set_viewer_process(None)
            return jsonify({'success': False, 'error': error}), 500

        return jsonify({
            'success': True,
            'port': viewer_port,
            'wsUrl': f'ws://localhost:{viewer_port}/'
        })

    except Exception as e:
        logger.error(f"Start vanilla viewer error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@viewer_bp.route('/api/mex/viewer/start-vault', methods=['POST'])
def start_viewer_vault():
    """Start the 3D model viewer for a vault costume (for skin creator editing)"""
    try:
        data = request.json
        character = data.get('character')
        costume_id = data.get('costumeId')

        if not character or not costume_id:
            return jsonify({'success': False, 'error': 'Missing character or costumeId'}), 400

        # Stop any existing viewer
        stop_existing_viewer()

        # Find the costume in the vault
        char_storage = STORAGE_PATH / character
        zip_path = char_storage / f"{costume_id}.zip"

        if not zip_path.exists():
            return jsonify({'success': False, 'error': f'Costume not found in vault: {costume_id}'}), 404

        # Extract DAT file to temp location
        temp_dir = Path(tempfile.mkdtemp())
        dat_path = None

        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if name.endswith('.dat'):
                    zf.extract(name, temp_dir)
                    dat_path = temp_dir / name
                    break

        if not dat_path or not dat_path.exists():
            return jsonify({'success': False, 'error': 'No DAT file found in costume archive'}), 400

        # Check if HSDRawViewer exists
        if not HSDRAW_EXE.exists():
            return jsonify({
                'success': False,
                'error': f'HSDRawViewer not found at {HSDRAW_EXE}. Please build it first.'
            }), 500

        # Find an available port
        viewer_port = find_available_port()

        exe_path = to_windows_path(HSDRAW_EXE)
        dat_windows_path = to_windows_path(dat_path)
        logs_windows_path = to_windows_path(LOGS_PATH)

        # Find scene file
        scene_path = find_scene_file(character)
        scene_windows_path = to_windows_path(scene_path) if scene_path else None

        # Find AJ file
        aj_path = find_aj_file(character)
        aj_windows_path = to_windows_path(aj_path) if aj_path else None

        # Build command
        cmd = [exe_path, '--stream', str(viewer_port), dat_windows_path, logs_windows_path]
        if scene_windows_path:
            cmd.append(scene_windows_path)
        else:
            cmd.append('')
        if aj_windows_path:
            cmd.append(aj_windows_path)

        logger.info(f"Starting vault viewer: {' '.join(cmd)}")

        # Start the viewer process
        viewer_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            **get_subprocess_args()
        )
        set_viewer_process(viewer_process)
        set_viewer_port(viewer_port)

        # Wait for server to be ready
        ready, error = wait_for_server(viewer_port)

        if not ready:
            if get_viewer_process():
                get_viewer_process().kill()
                set_viewer_process(None)
            return jsonify({'success': False, 'error': error}), 500

        return jsonify({
            'success': True,
            'port': viewer_port,
            'wsUrl': f'ws://localhost:{viewer_port}/'
        })

    except Exception as e:
        logger.error(f"Start vault viewer error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@viewer_bp.route('/api/viewer/stop', methods=['POST'])
def stop_viewer():
    """Stop the 3D model viewer"""
    try:
        stop_existing_viewer()
        return jsonify({'success': True})

    except Exception as e:
        logger.error(f"Stop viewer error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@viewer_bp.route('/api/viewer/status', methods=['GET'])
def viewer_status():
    """Get the current viewer status"""
    viewer_process = get_viewer_process()
    viewer_port = get_viewer_port()

    running = viewer_process is not None and viewer_process.poll() is None

    return jsonify({
        'success': True,
        'running': running,
        'port': viewer_port if running else None,
        'wsUrl': f'ws://localhost:{viewer_port}/' if running else None
    })


@viewer_bp.route('/api/mex/vanilla/costumes/<character>', methods=['GET'])
def get_vanilla_costumes(character):
    """Get list of vanilla costumes for a character"""
    try:
        char_dir = VANILLA_ASSETS_DIR / character
        if not char_dir.exists():
            return jsonify({'success': False, 'error': f'Character {character} not found'}), 404

        costumes = []
        for folder in sorted(char_dir.iterdir()):
            if folder.is_dir() and folder.name.startswith('Pl'):
                # Check if DAT file exists
                dat_file = folder / f"{folder.name}.dat"
                if dat_file.exists():
                    # Get color code from folder name (last 2 chars)
                    color_code = folder.name[-2:]
                    color_names = {
                        'Nr': 'Default', 'Bu': 'Blue', 'Re': 'Red', 'Gr': 'Green',
                        'Ye': 'Yellow', 'Bk': 'Black', 'Wh': 'White', 'Pi': 'Pink',
                        'Or': 'Orange', 'La': 'Lavender', 'Aq': 'Aqua', 'Gy': 'Grey',
                        'Cy': 'Cyan', 'Pr': 'Purple', 'Br': 'Brown'
                    }
                    costumes.append({
                        'code': folder.name,
                        'colorCode': color_code,
                        'colorName': color_names.get(color_code, color_code),
                        'hasCsp': (folder / 'csp.png').exists(),
                        'hasStock': (folder / 'stock.png').exists()
                    })

        return jsonify({'success': True, 'costumes': costumes})

    except Exception as e:
        logger.error(f"Get vanilla costumes error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
