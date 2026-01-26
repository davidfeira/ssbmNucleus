"""
Project Blueprint - Project management routes.

Handles MEX project status, open, create, and fighter listing.
"""

import json
import subprocess
import logging
from pathlib import Path
from flask import Blueprint, request, jsonify

from core.config import (
    PROJECT_ROOT, MEXCLI_PATH, VANILLA_ASSETS_DIR, get_subprocess_args
)
from core.state import (
    get_mex_manager, set_project_path, get_current_project_path
)
from core.constants import VANILLA_COSTUME_COUNT
from core.helpers import calculate_auto_compression

logger = logging.getLogger(__name__)

project_bp = Blueprint('project', __name__)


def find_fighter_json_by_name(fighter_name):
    """Find fighter JSON file by scanning data/fighters/ directory.
    Returns (path, data) tuple or (None, None) if not found.
    This avoids calling MexCLI which can cause file locking issues."""
    current_project_path = get_current_project_path()
    if current_project_path is None:
        return None, None

    fighters_dir = current_project_path.parent / "data" / "fighters"
    if not fighters_dir.exists():
        return None, None

    # Scan all fighter JSON files to find matching name
    for json_file in fighters_dir.glob("*.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('name', '').lower() == fighter_name.lower():
                    return json_file, data
        except (json.JSONDecodeError, IOError):
            continue

    return None, None


@project_bp.route('/api/mex/recommended-compression', methods=['GET'])
def get_recommended_compression():
    """Get recommended CSP compression based on added costume count."""
    try:
        mex = get_mex_manager()
        fighters = mex.list_fighters()

        # Sum costumeCount from list-fighters (already included, no extra API calls)
        total_costumes = sum(f.get('costumeCount', 0) for f in fighters)

        # Calculate added costumes (can't be negative)
        added_costumes = max(0, total_costumes - VANILLA_COSTUME_COUNT)

        ratio = calculate_auto_compression(added_costumes)

        return jsonify({
            'success': True,
            'totalCostumes': total_costumes,
            'vanillaCostumes': VANILLA_COSTUME_COUNT,
            'addedCostumes': added_costumes,
            'ratio': round(ratio, 2)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'totalCostumes': 0,
            'vanillaCostumes': VANILLA_COSTUME_COUNT,
            'addedCostumes': 0,
            'ratio': 1.0
        }), 500


@project_bp.route('/api/mex/status', methods=['GET'])
def get_status():
    """Get MEX project status"""
    current_project_path = get_current_project_path()

    # Check if a project is loaded
    if current_project_path is None:
        return jsonify({
            'success': True,
            'connected': True,
            'projectLoaded': False,
            'message': 'No project loaded'
        })

    try:
        mex = get_mex_manager()
        info = mex.get_info()

        return jsonify({
            'success': True,
            'connected': True,
            'projectLoaded': True,
            'project': {
                'name': info['build']['name'],
                'version': f"{info['build']['majorVersion']}.{info['build']['minorVersion']}.{info['build']['patchVersion']}",
                'path': str(current_project_path)
            },
            'counts': info['counts']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'connected': False,
            'projectLoaded': False,
            'error': str(e)
        }), 500


@project_bp.route('/api/mex/project/open', methods=['POST'])
def open_project():
    """Open a MEX project from a given path"""
    try:
        data = request.json
        project_path = data.get('projectPath')

        if not project_path:
            return jsonify({
                'success': False,
                'error': 'No project path provided'
            }), 400

        project_file = Path(project_path)

        # Validate the path
        if not project_file.exists():
            return jsonify({
                'success': False,
                'error': f'Project file not found: {project_path}'
            }), 404

        if not project_file.suffix == '.mexproj':
            return jsonify({
                'success': False,
                'error': 'File must be a .mexproj file'
            }), 400

        # Set the project path
        set_project_path(project_path)

        # Try to get project info to verify it works
        mex = get_mex_manager()
        info = mex.get_info()

        logger.info(f"[OK] Opened MEX project: {project_path}")

        return jsonify({
            'success': True,
            'message': 'Project opened successfully',
            'project': {
                'name': info['build']['name'],
                'version': f"{info['build']['majorVersion']}.{info['build']['minorVersion']}.{info['build']['patchVersion']}",
                'path': str(project_path)
            }
        })
    except Exception as e:
        logger.error(f"Failed to open project: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@project_bp.route('/api/mex/project/create', methods=['POST'])
def create_project():
    """Create a new MEX project from a vanilla ISO"""
    try:
        data = request.json
        iso_path = data.get('isoPath')
        project_dir = data.get('projectDir')
        project_name = data.get('projectName', 'MexProject')

        logger.info(f"=== CREATE PROJECT REQUEST ===")
        logger.info(f"ISO Path: {iso_path}")
        logger.info(f"Project Dir: {project_dir}")
        logger.info(f"Project Name: {project_name}")

        if not iso_path or not project_dir:
            return jsonify({
                'success': False,
                'error': 'Missing isoPath or projectDir parameter'
            }), 400

        # Validate ISO exists
        iso_file = Path(iso_path)
        if not iso_file.exists():
            return jsonify({
                'success': False,
                'error': f'ISO file not found: {iso_path}'
            }), 404

        # Validate project directory exists
        proj_dir = Path(project_dir)
        if not proj_dir.exists():
            return jsonify({
                'success': False,
                'error': f'Project directory not found: {project_dir}'
            }), 404

        # Call MexCLI create command
        mexcli_path = str(MEXCLI_PATH)
        cmd = [mexcli_path, 'create', str(iso_file), str(proj_dir), project_name]

        logger.info(f"Running command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
            **get_subprocess_args()
        )

        logger.info(f"MexCLI stdout:\n{result.stdout}")
        logger.info(f"MexCLI stderr:\n{result.stderr}")
        logger.info(f"MexCLI return code: {result.returncode}")

        if result.returncode != 0:
            error_message = result.stderr or result.stdout or 'Unknown error'
            logger.error(f"MexCLI create failed: {error_message}")
            return jsonify({
                'success': False,
                'error': f'Failed to create project: {error_message}'
            }), 500

        # The created project file should be at projectDir/project.mexproj
        created_project_path = proj_dir / "project.mexproj"

        if not created_project_path.exists():
            logger.error(f"Project file not found after creation: {created_project_path}")
            return jsonify({
                'success': False,
                'error': 'Project was created but .mexproj file not found'
            }), 500

        logger.info(f"[OK] Project created successfully: {created_project_path}")
        logger.info(f"=== CREATE PROJECT COMPLETE ===")

        return jsonify({
            'success': True,
            'message': 'Project created successfully',
            'projectPath': str(created_project_path)
        })

    except Exception as e:
        logger.error(f"Create project error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@project_bp.route('/api/mex/fighters', methods=['GET'])
def list_fighters():
    """List all fighters in MEX project"""
    try:
        mex = get_mex_manager()
        fighters = mex.list_fighters()

        # Add default stock icon URL for each fighter
        for fighter in fighters:
            name = fighter['name']
            # Find the Normal costume folder (ends with 'Nr') in vanilla assets
            vanilla_dir = VANILLA_ASSETS_DIR / name
            if vanilla_dir.exists():
                for folder in vanilla_dir.iterdir():
                    if folder.is_dir() and folder.name.endswith('Nr'):
                        fighter['defaultStockUrl'] = f"/vanilla/{name}/{folder.name}/stock.png"
                        break

        return jsonify({
            'success': True,
            'fighters': fighters
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@project_bp.route('/api/mex/fighters/<fighter_name>/costumes', methods=['GET'])
def get_fighter_costumes(fighter_name):
    """Get costumes for a specific fighter"""
    try:
        mex = get_mex_manager()
        result = mex._run_command("get-costumes", str(mex.project_path), fighter_name)

        # Add asset URLs to each costume (relative to /api/mex since frontend adds API_URL)
        costumes = result.get('costumes', [])
        for costume in costumes:
            if costume.get('csp'):
                # Convert backslashes to forward slashes for URLs
                csp_path = costume['csp'].replace('\\', '/')
                costume['cspUrl'] = f"/assets/{csp_path}.png"
            if costume.get('icon'):
                # Convert backslashes to forward slashes for URLs
                icon_path = costume['icon'].replace('\\', '/')
                costume['iconUrl'] = f"/assets/{icon_path}.png"

        return jsonify({
            'success': True,
            'fighter': result.get('fighter'),
            'costumes': costumes
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@project_bp.route('/api/mex/fighters/<fighter_name>/team-colors', methods=['GET'])
def get_team_colors(fighter_name):
    """Get team color costume indices for a fighter"""
    try:
        current_project_path = get_current_project_path()
        if current_project_path is None:
            return jsonify({'success': False, 'error': 'No project loaded'}), 400

        # Find fighter JSON by scanning files (avoids MexCLI call)
        fighter_json_path, fighter_data = find_fighter_json_by_name(fighter_name)
        if fighter_json_path is None:
            return jsonify({'success': False, 'error': f'Fighter not found: {fighter_name}'}), 404

        return jsonify({
            'success': True,
            'fighter': fighter_name,
            'red': fighter_data.get('redCostumeIndex'),
            'blue': fighter_data.get('blueCostumeIndex'),
            'green': fighter_data.get('greenCostumeIndex')
        })
    except Exception as e:
        logger.error(f"Error getting team colors for {fighter_name}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@project_bp.route('/api/mex/fighters/<fighter_name>/team-colors', methods=['POST'])
def set_team_color(fighter_name):
    """Set a team color costume index for a fighter"""
    try:
        current_project_path = get_current_project_path()
        if current_project_path is None:
            return jsonify({'success': False, 'error': 'No project loaded'}), 400

        data = request.json
        color = data.get('color')  # 'red', 'blue', or 'green'
        costume_index = data.get('costumeIndex')

        if color not in ('red', 'blue', 'green'):
            return jsonify({'success': False, 'error': f'Invalid color: {color}'}), 400

        if costume_index is None:
            return jsonify({'success': False, 'error': 'costumeIndex is required'}), 400

        # Find fighter JSON by scanning files (avoids MexCLI call)
        fighter_json_path, fighter_data = find_fighter_json_by_name(fighter_name)
        if fighter_json_path is None:
            return jsonify({'success': False, 'error': f'Fighter not found: {fighter_name}'}), 404

        # Validate costume index is within range
        costume_count = len(fighter_data.get('costumes', []))
        if costume_index < 0 or costume_index >= costume_count:
            return jsonify({'success': False, 'error': f'Costume index {costume_index} out of range (0-{costume_count-1})'}), 400

        # Update the team color field
        field_name = f'{color}CostumeIndex'
        fighter_data[field_name] = costume_index

        # Write back to file
        with open(fighter_json_path, 'w', encoding='utf-8') as f:
            json.dump(fighter_data, f, indent=2)

        logger.info(f"Set {color} team color for {fighter_name} to costume index {costume_index}")

        return jsonify({
            'success': True,
            'fighter': fighter_name,
            'color': color,
            'costumeIndex': costume_index
        })
    except Exception as e:
        logger.error(f"Error setting team color for {fighter_name}: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@project_bp.route('/api/mex/shutdown', methods=['POST'])
def shutdown():
    """Gracefully shutdown the Flask server."""
    import os
    logger.info("Shutdown request received")

    def shutdown_server():
        from flask import request
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            # In production or when using app.run()
            os._exit(0)
        else:
            func()

    shutdown_server()
    return jsonify({'success': True, 'message': 'Server shutting down...'})