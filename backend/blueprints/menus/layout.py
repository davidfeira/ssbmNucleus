"""
CSS (Character Select Screen) layout editor endpoints.

Layout reads/writes go through the loaded MEX project's manager; fighter icons
are served straight from the project assets directory.
"""

import logging
from pathlib import Path
from flask import request, jsonify, send_file

from core.state import get_current_project_path, get_mex_manager

from . import menus_bp

logger = logging.getLogger(__name__)


@menus_bp.route('/api/mex/menus/css/layout', methods=['GET'])
def get_css_layout():
    """Get the full CSS layout from the current MEX project."""
    try:
        mex = get_mex_manager()
        if mex is None:
            return jsonify({'success': False, 'error': 'No MEX project loaded'}), 400
        result = mex.get_css_layout()
        return jsonify(result)
    except Exception as e:
        logger.error(f'Get CSS layout error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/layout', methods=['POST'])
def set_css_layout():
    """Save CSS layout changes to the MEX project."""
    try:
        mex = get_mex_manager()
        if mex is None:
            return jsonify({'success': False, 'error': 'No MEX project loaded'}), 400

        layout_data = request.get_json()
        if not layout_data or 'icons' not in layout_data:
            return jsonify({'success': False, 'error': 'Missing icons data'}), 400

        import json as _json
        result = mex.set_css_layout(_json.dumps(layout_data))
        return jsonify(result)
    except Exception as e:
        logger.error(f'Set CSS layout error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/fighter-icon', methods=['GET'])
def get_css_fighter_icon():
    """Serve a fighter icon PNG from the MEX project assets directory."""
    try:
        icon_path = request.args.get('path')
        if not icon_path:
            return jsonify({'success': False, 'error': 'Missing path parameter'}), 400

        icon_file = Path(icon_path)
        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No MEX project loaded'}), 400

        project_dir = project_path.parent.resolve()
        try:
            icon_file.resolve().relative_to(project_dir)
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid path'}), 403

        if not icon_file.exists():
            return jsonify({'success': False, 'error': 'Icon file not found'}), 404

        return send_file(str(icon_file), mimetype='image/png', max_age=0)
    except Exception as e:
        logger.error(f'Get CSS fighter icon error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
