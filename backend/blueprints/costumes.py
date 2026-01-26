"""
Costumes Blueprint - Costume import/remove/reorder routes for MEX project.

Handles importing costumes from storage, removing costumes, and reordering them.
"""

import json
import time
import logging
from flask import Blueprint, request, jsonify

from core.config import PROJECT_ROOT
from core.state import get_mex_manager, reload_mex_manager

# Import MexManagerError for proper exception handling
import sys
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "tools"))
from mex_bridge import MexManagerError

logger = logging.getLogger(__name__)

costumes_bp = Blueprint('costumes', __name__)


@costumes_bp.route('/api/mex/import', methods=['POST'])
def import_costume():
    """
    Import costume to MEX project

    Body:
    {
        "fighter": "Fox",
        "costumePath": "storage/Fox/PlFxNr_custom/PlFxNr_custom.zip"
    }
    """
    try:
        data = request.json
        fighter_name = data.get('fighter')
        costume_path = data.get('costumePath')

        logger.info(f"=== IMPORT REQUEST ===")
        logger.info(f"Fighter: {fighter_name}")
        logger.info(f"Costume Path: {costume_path}")
        logger.info(f"Request Data: {json.dumps(data, indent=2)}")

        if not fighter_name or not costume_path:
            logger.error("Missing fighter or costumePath parameter")
            return jsonify({
                'success': False,
                'error': 'Missing fighter or costumePath parameter'
            }), 400

        # Resolve costume path relative to project root
        full_costume_path = PROJECT_ROOT / costume_path

        logger.info(f"Full costume path: {full_costume_path}")
        logger.info(f"Path exists: {full_costume_path.exists()}")

        if not full_costume_path.exists():
            logger.error(f"Costume ZIP not found: {costume_path}")
            return jsonify({
                'success': False,
                'error': f'Costume ZIP not found: {costume_path}'
            }), 404

        logger.info(f"Calling MexCLI to import costume...")
        mex = get_mex_manager()
        result = mex.import_costume(fighter_name, str(full_costume_path))

        logger.info(f"Import result: {json.dumps(result, indent=2)}")

        # Small delay to ensure file system has flushed the write
        time.sleep(0.15)

        # Force reload to pick up file changes for subsequent requests
        reload_mex_manager()
        logger.info(f"Reloaded MEX manager to pick up changes")

        logger.info(f"=== IMPORT COMPLETE ===")

        return jsonify({
            'success': True,
            'result': result
        })
    except MexManagerError as e:
        logger.error(f"MexManagerError: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500


@costumes_bp.route('/api/mex/remove', methods=['POST'])
def remove_costume():
    """
    Remove costume from MEX project

    Body:
    {
        "fighter": "Fox",
        "costumeIndex": 3
    }
    """
    try:
        data = request.json
        fighter_name = data.get('fighter')
        costume_index = data.get('costumeIndex')

        logger.info(f"=== REMOVE REQUEST ===")
        logger.info(f"Fighter: {fighter_name}")
        logger.info(f"Costume Index: {costume_index}")

        if fighter_name is None or costume_index is None:
            logger.error("Missing fighter or costumeIndex parameter")
            return jsonify({
                'success': False,
                'error': 'Missing fighter or costumeIndex parameter'
            }), 400

        # Validate costume index
        if not isinstance(costume_index, int) or costume_index < 0:
            logger.error(f"Invalid costume index: {costume_index}")
            return jsonify({
                'success': False,
                'error': 'costumeIndex must be a non-negative integer'
            }), 400

        logger.info(f"Calling MexCLI to remove costume...")
        mex = get_mex_manager()
        result = mex.remove_costume(fighter_name, costume_index)

        logger.info(f"Remove result: {json.dumps(result, indent=2)}")

        # Force reload to pick up file changes for subsequent requests
        reload_mex_manager()
        logger.info(f"Reloaded MEX manager to pick up changes")

        logger.info(f"=== REMOVE COMPLETE ===")

        return jsonify({
            'success': True,
            'result': result
        })
    except MexManagerError as e:
        logger.error(f"MexManagerError: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500


@costumes_bp.route('/api/mex/reorder', methods=['POST'])
def reorder_costume():
    """
    Reorder costume in MEX project (swap positions)

    Body:
    {
        "fighter": "Fox",
        "fromIndex": 2,
        "toIndex": 0
    }

    Note: For Ice Climbers (Popo), paired Nana costumes are automatically reordered
    """
    try:
        data = request.json
        fighter_name = data.get('fighter')
        from_index = data.get('fromIndex')
        to_index = data.get('toIndex')

        logger.info(f"=== REORDER REQUEST ===")
        logger.info(f"Fighter: {fighter_name}")
        logger.info(f"From Index: {from_index}")
        logger.info(f"To Index: {to_index}")

        if fighter_name is None or from_index is None or to_index is None:
            logger.error("Missing fighter, fromIndex, or toIndex parameter")
            return jsonify({
                'success': False,
                'error': 'Missing fighter, fromIndex, or toIndex parameter'
            }), 400

        # Validate indices
        if not isinstance(from_index, int) or from_index < 0:
            logger.error(f"Invalid from_index: {from_index}")
            return jsonify({
                'success': False,
                'error': 'fromIndex must be a non-negative integer'
            }), 400

        if not isinstance(to_index, int) or to_index < 0:
            logger.error(f"Invalid to_index: {to_index}")
            return jsonify({
                'success': False,
                'error': 'toIndex must be a non-negative integer'
            }), 400

        logger.info(f"Calling MexCLI to reorder costume...")
        mex = get_mex_manager()
        result = mex.reorder_costume(fighter_name, from_index, to_index)

        logger.info(f"Reorder result: {json.dumps(result, indent=2)}")

        # Force reload to pick up file changes for subsequent requests
        reload_mex_manager()
        logger.info(f"Reloaded MEX manager to pick up changes")

        logger.info(f"=== REORDER COMPLETE ===")

        return jsonify({
            'success': True,
            'result': result
        })
    except MexManagerError as e:
        logger.error(f"MexManagerError: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500
