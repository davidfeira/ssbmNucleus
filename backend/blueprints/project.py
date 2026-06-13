"""
Project Blueprint - Project management routes.

Handles MEX project status, open, create, and fighter listing.
"""

import json
import subprocess
import logging
import shutil
from pathlib import Path
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from core.config import (
    PROJECT_ROOT, PROJECTS_PATH, MEXCLI_PATH, OUTPUT_PATH, VANILLA_ASSETS_DIR, get_subprocess_args
)
from core.state import (
    get_mex_manager, set_project_path, get_current_project_path, clear_project_path
)
from core.constants import VANILLA_COSTUME_COUNT
from core.helpers import calculate_auto_compression

logger = logging.getLogger(__name__)

project_bp = Blueprint('project', __name__)


def get_next_project_directory(requested_name=None):
    """Pick a unique subdirectory under the app-managed projects folder."""
    base_name = secure_filename((requested_name or '').strip()) or 'MexProject'
    candidate = PROJECTS_PATH / base_name
    suffix = 2

    while candidate.exists():
        candidate = PROJECTS_PATH / f"{base_name}-{suffix}"
        suffix += 1

    return candidate


def is_managed_project_directory(project_dir):
    """Return True when a project directory lives under the managed projects root."""
    try:
        Path(project_dir).resolve().relative_to(PROJECTS_PATH.resolve())
        return True
    except ValueError:
        return False


def cleanup_failed_project_directory(proj_dir):
    """Remove a partially-created project directory after a failed create."""
    if not proj_dir.exists() or not is_managed_project_directory(proj_dir):
        return
    try:
        shutil.rmtree(proj_dir)
        logger.info(f"Removed partial project directory: {proj_dir}")
    except OSError as cleanup_error:
        logger.warning(f"Could not remove partial project directory: {cleanup_error}")


def build_project_response(project_path, info):
    """Build consistent project metadata for API responses."""
    project_file = Path(project_path)
    project_dir = project_file.parent

    return {
        'name': info['build']['name'],
        'version': f"{info['build']['majorVersion']}.{info['build']['minorVersion']}.{info['build']['patchVersion']}",
        'path': str(project_file),
        'projectDirectory': str(project_dir),
        'isManagedProject': is_managed_project_directory(project_dir)
    }


def build_project_listing_entry(project_file, current_project_path=None):
    """Build lightweight metadata for a managed project without opening it."""
    project_file = Path(project_file)
    project_dir = project_file.parent

    try:
        last_modified_at = int(project_file.stat().st_mtime)
    except OSError:
        last_modified_at = 0

    is_current_project = False
    if current_project_path is not None:
        try:
            is_current_project = current_project_path.resolve() == project_file.resolve()
        except OSError:
            is_current_project = False

    return {
        'name': project_dir.name,
        'path': str(project_file),
        'projectDirectory': str(project_dir),
        'isManagedProject': True,
        'isCurrentProject': is_current_project,
        'lastModifiedAt': last_modified_at
    }


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
            'project': build_project_response(current_project_path, info),
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
            'project': build_project_response(project_path, info)
        })
    except Exception as e:
        logger.error(f"Failed to open project: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@project_bp.route('/api/mex/project/list', methods=['GET'])
def list_projects():
    """List all app-managed MEX projects."""
    try:
        current_project_path = get_current_project_path()
        projects = []

        if PROJECTS_PATH.exists():
            for project_dir in PROJECTS_PATH.iterdir():
                if not project_dir.is_dir():
                    continue

                default_project_file = project_dir / 'project.mexproj'
                if default_project_file.exists():
                    project_file = default_project_file
                else:
                    mexproj_files = sorted(project_dir.glob('*.mexproj'))
                    if not mexproj_files:
                        continue
                    project_file = mexproj_files[0]

                projects.append(build_project_listing_entry(project_file, current_project_path))

        projects.sort(key=lambda project: (
            not project.get('isCurrentProject', False),
            -project.get('lastModifiedAt', 0),
            project.get('name', '').lower()
        ))

        return jsonify({
            'success': True,
            'projects': projects,
            'projectsDirectory': str(PROJECTS_PATH)
        })
    except Exception as e:
        logger.error(f"List projects error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@project_bp.route('/api/mex/project/close', methods=['POST'])
def close_project():
    """Close the currently loaded MEX project without deleting it."""
    try:
        current_project_path = get_current_project_path()

        if current_project_path is None:
            return jsonify({
                'success': True,
                'closed': False,
                'message': 'No project is currently loaded'
            })

        closed_project_path = str(current_project_path)
        clear_project_path()
        logger.info(f"[OK] Closed MEX project: {closed_project_path}")

        return jsonify({
            'success': True,
            'closed': True,
            'message': 'Project closed successfully',
            'projectPath': closed_project_path
        })
    except Exception as e:
        logger.error(f"Close project error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@project_bp.route('/api/mex/project/create', methods=['POST'])
def create_project():
    """Create a new MEX project from a vanilla ISO.

    Optionally accepts a vault xdelta patchId: the patch is applied to the
    vanilla ISO first and the project is created from the patched ISO.
    """
    temp_patched_iso = None
    try:
        data = request.json or {}
        iso_path = data.get('isoPath')
        patch_id = data.get('patchId')
        requested_project_name = (data.get('projectName') or '').strip()
        proj_dir = get_next_project_directory(requested_project_name)
        project_name = requested_project_name or proj_dir.name

        logger.info(f"=== CREATE PROJECT REQUEST ===")
        logger.info(f"ISO Path: {iso_path}")
        logger.info(f"Patch ID: {patch_id or '(none, vanilla)'}")
        logger.info(f"Projects Root: {PROJECTS_PATH}")
        logger.info(f"Project Dir: {proj_dir}")
        logger.info(f"Project Name: {project_name}")

        if not iso_path:
            return jsonify({
                'success': False,
                'error': 'Missing isoPath parameter'
            }), 400

        # Validate ISO exists
        iso_file = Path(iso_path)
        if not iso_file.exists():
            return jsonify({
                'success': False,
                'error': f'ISO file not found: {iso_path}'
            }), 404

        # Apply a vault xdelta patch on top of the vanilla ISO first if requested
        if patch_id:
            from blueprints.xdelta import XDELTA_PATH, get_xdelta_exe, load_xdelta_metadata

            patch = next((p for p in load_xdelta_metadata() if p['id'] == patch_id), None)
            if not patch:
                return jsonify({
                    'success': False,
                    'error': f'Patch not found in vault: {patch_id}'
                }), 404

            xdelta_file = XDELTA_PATH / f"{patch_id}.xdelta"
            if not xdelta_file.exists():
                return jsonify({
                    'success': False,
                    'error': f'Patch file missing from vault: {patch["name"]}'
                }), 404

            temp_patched_iso = OUTPUT_PATH / f"create_{proj_dir.name}_{patch_id}.iso"
            patch_cmd = [
                str(get_xdelta_exe()), '-d', '-f',
                '-s', str(iso_file),
                str(xdelta_file),
                str(temp_patched_iso)
            ]

            logger.info(f"Applying patch '{patch['name']}' before project creation")
            logger.info(f"Running command: {' '.join(patch_cmd)}")

            patch_result = subprocess.run(
                patch_cmd,
                capture_output=True,
                text=True,
                **get_subprocess_args()
            )

            if patch_result.returncode != 0:
                error_message = patch_result.stderr or patch_result.stdout or 'Unknown xdelta error'
                logger.error(f"xdelta3 failed: {error_message}")
                return jsonify({
                    'success': False,
                    'error': f'Failed to apply patch "{patch["name"]}": {error_message}'
                }), 500

            logger.info(f"[OK] Patched ISO ready: {temp_patched_iso}")
            iso_file = temp_patched_iso

        # Call MexCLI create command
        mexcli_path = str(MEXCLI_PATH)
        cmd = [mexcli_path, 'create', str(iso_file), str(proj_dir), project_name]
        if patch_id:
            # pass the vanilla ISO so MexCLI can backfill CSS icons the
            # patched ISO's menu files couldn't provide
            cmd.append(str(iso_path))

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
            cleanup_failed_project_directory(proj_dir)
            return jsonify({
                'success': False,
                'error': f'Failed to create project: {error_message}'
            }), 500

        # The created project file should be at projectDir/project.mexproj
        created_project_path = proj_dir / "project.mexproj"

        if not created_project_path.exists():
            logger.error(f"Project file not found after creation: {created_project_path}")
            cleanup_failed_project_directory(proj_dir)
            return jsonify({
                'success': False,
                'error': 'Project was created but .mexproj file not found'
            }), 500

        logger.info(f"[OK] Project created successfully: {created_project_path}")
        logger.info(f"=== CREATE PROJECT COMPLETE ===")

        return jsonify({
            'success': True,
            'message': 'Project created successfully',
            'projectPath': str(created_project_path),
            'projectDirectory': str(proj_dir),
            'projectsDirectory': str(PROJECTS_PATH),
            'isManagedProject': True
        })

    except Exception as e:
        logger.error(f"Create project error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        if temp_patched_iso is not None and temp_patched_iso.exists():
            try:
                temp_patched_iso.unlink()
                logger.info(f"Deleted temporary patched ISO: {temp_patched_iso}")
            except OSError as cleanup_error:
                logger.warning(f"Could not delete temporary patched ISO: {cleanup_error}")


@project_bp.route('/api/mex/project/delete', methods=['POST'])
def delete_project():
    """Delete an app-managed MEX project directory."""
    try:
        data = request.json or {}
        project_path = data.get('projectPath')

        if not project_path:
            return jsonify({
                'success': False,
                'error': 'No project path provided'
            }), 400

        project_file = Path(project_path)
        if project_file.suffix != '.mexproj':
            return jsonify({
                'success': False,
                'error': 'File must be a .mexproj file'
            }), 400

        project_dir = project_file.parent
        if not is_managed_project_directory(project_dir):
            return jsonify({
                'success': False,
                'error': 'Only app-managed projects can be deleted from Nucleus.'
            }), 403

        managed_root = PROJECTS_PATH.resolve()
        resolved_project_dir = project_dir.resolve()
        if resolved_project_dir == managed_root:
            return jsonify({
                'success': False,
                'error': 'Refusing to delete the managed projects root.'
            }), 400

        current_project_path = get_current_project_path()
        current_project_closed = False
        if current_project_path is not None:
            current_project_closed = current_project_path.resolve() == project_file.resolve()
            if current_project_closed:
                clear_project_path()

        if resolved_project_dir.exists():
            shutil.rmtree(resolved_project_dir)
            logger.info(f"[OK] Deleted managed project directory: {resolved_project_dir}")
        else:
            logger.info(f"Managed project directory already missing: {resolved_project_dir}")

        return jsonify({
            'success': True,
            'message': 'Project deleted successfully',
            'deleted': True,
            'projectPath': str(project_file),
            'projectDirectory': str(resolved_project_dir),
            'currentProjectClosed': current_project_closed
        })

    except Exception as e:
        logger.error(f"Delete project error: {str(e)}", exc_info=True)
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
        project_path = get_current_project_path()
        project_dir = project_path.parent if project_path else None

        for fighter in fighters:
            name = fighter['name']
            # Find the Normal costume folder (ends with 'Nr') in vanilla assets
            vanilla_dir = VANILLA_ASSETS_DIR / name
            if vanilla_dir.exists():
                for folder in vanilla_dir.iterdir():
                    if folder.is_dir() and folder.name.endswith('Nr'):
                        fighter['defaultStockUrl'] = f"/vanilla/{name}/{folder.name}/stock.png"
                        break

            # Fallback for custom fighters: read stock icon from project assets
            if 'defaultStockUrl' not in fighter and project_dir and fighter.get('isMexFighter'):
                fighter_json = project_dir / 'data' / 'fighters' / f"{fighter['internalId']:03d}.json"
                if fighter_json.exists():
                    import json as _json
                    fdata = _json.load(open(fighter_json))
                    costumes = fdata.get('costumes', [])
                    if costumes:
                        icon_ref = costumes[0].get('icon', '')
                        if icon_ref:
                            fighter['defaultStockUrl'] = f"/assets/{icon_ref.replace(chr(92), '/')}.png"

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
        # URLs carry the file mtime so the browser refetches when an asset is
        # replaced in place (e.g. by the apply-pose flow)
        project_dir = get_current_project_path().parent if get_current_project_path() else None

        def _asset_url(ref):
            rel = ref.replace('\\', '/')
            version = ''
            if project_dir is not None:
                asset_file = project_dir / 'assets' / f"{rel}.png"
                if asset_file.exists():
                    version = f"?v={int(asset_file.stat().st_mtime)}"
            return f"/assets/{rel}.png{version}"

        costumes = result.get('costumes', [])
        for costume in costumes:
            if costume.get('csp'):
                costume['cspUrl'] = _asset_url(costume['csp'])
            if costume.get('icon'):
                costume['iconUrl'] = _asset_url(costume['icon'])

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


@project_bp.route('/api/mex/project/build', methods=['GET'])
def get_build_info():
    """Get the disc-banner metadata (title/creator/description) + image preview."""
    try:
        current_project_path = get_current_project_path()
        if current_project_path is None:
            return jsonify({'success': False, 'error': 'No project loaded'}), 400

        return jsonify(get_mex_manager().get_build())
    except Exception as e:
        logger.error(f"Error getting build info: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@project_bp.route('/api/mex/project/build', methods=['POST'])
def set_build_info():
    """Set disc-banner fields and (optionally) the 96x32 banner image.

    Body: any of shortName, longName, shortMaker, longMaker, description,
    bannerPngBase64 (base64-encoded PNG).
    """
    try:
        current_project_path = get_current_project_path()
        if current_project_path is None:
            return jsonify({'success': False, 'error': 'No project loaded'}), 400

        data = request.json or {}
        allowed = ('shortName', 'longName', 'shortMaker', 'longMaker',
                   'description', 'bannerPngBase64')
        payload = {k: data[k] for k in allowed if k in data}

        if not payload:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400

        result = get_mex_manager().set_build(payload)
        logger.info("Updated disc banner info: %s",
                    [k for k in payload if k != 'bannerPngBase64'])
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error setting build info: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


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
