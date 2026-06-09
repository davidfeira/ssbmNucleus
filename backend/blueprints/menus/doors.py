"""
CSS Doors endpoints.

A door mod is a single `door.png` texture installed into MnSlChr.usd via
HSDRawViewer --css-doors import:

    storage/menus/css/doors/
        metadata.json               # list of installed door mods
        <mod_id>/
            door.png
"""

import json
import shutil
import tempfile
import uuid
import logging
from pathlib import Path
from datetime import datetime
from flask import request, jsonify, send_file

from core.config import HSDRAW_EXE
from core.state import get_project_files_dir, get_current_project_path

from . import menus_bp
from .helpers import DOORS_PATH, DOORS_METADATA, _run_hsd_cli

logger = logging.getLogger(__name__)


def _load_doors_metadata():
    # NOTE: unlike the dict-shaped catalogs (icon grid / backgrounds), this is
    # a bare list and a corrupt metadata.json deliberately raises (surfacing as
    # a 500 from the routes) rather than silently returning an empty list — so
    # it isn't folded into core.metadata.load_metadata.
    if DOORS_METADATA.exists():
        return json.loads(DOORS_METADATA.read_text())
    return []


def _save_doors_metadata(mods):
    DOORS_METADATA.write_text(json.dumps(mods, indent=2))


@menus_bp.route('/api/mex/menus/css/doors/list', methods=['GET'])
def list_door_mods():
    try:
        mods = _load_doors_metadata()
        for mod in mods:
            mod_dir = DOORS_PATH / mod['id']
            img = mod_dir / 'door.png'
            if img.exists():
                mod['imageUrl'] = f'/api/mex/menus/css/doors/image/{mod["id"]}'
        return jsonify({'success': True, 'mods': mods})
    except Exception as e:
        logger.error(f'List door mods error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/doors/image/<mod_id>', methods=['GET'])
def get_door_image(mod_id):
    try:
        img = DOORS_PATH / mod_id / 'door.png'
        if not img.exists():
            return jsonify({'success': False, 'error': 'Not found'}), 404
        return send_file(str(img), mimetype='image/png', max_age=0)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/doors/import', methods=['POST'])
def import_door_mod():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        f = request.files['file']
        if not f.filename:
            return jsonify({'success': False, 'error': 'Empty filename'}), 400

        mod_id = str(uuid.uuid4())[:8]
        mod_dir = DOORS_PATH / mod_id
        mod_dir.mkdir(parents=True, exist_ok=True)

        name = request.form.get('name', Path(f.filename).stem)
        door_path = mod_dir / 'door.png'
        f.save(str(door_path))

        mod = {
            'id': mod_id,
            'name': name,
            'created': datetime.now().isoformat()
        }

        mods = _load_doors_metadata()
        mods.append(mod)
        _save_doors_metadata(mods)

        mod['imageUrl'] = f'/api/mex/menus/css/doors/image/{mod_id}'
        return jsonify({'success': True, 'mod': mod})
    except Exception as e:
        logger.error(f'Import door mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/doors/delete/<mod_id>', methods=['POST'])
def delete_door_mod(mod_id):
    try:
        mods = _load_doors_metadata()
        mods = [m for m in mods if m['id'] != mod_id]
        _save_doors_metadata(mods)
        mod_dir = DOORS_PATH / mod_id
        if mod_dir.exists():
            shutil.rmtree(str(mod_dir))
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Delete door mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/doors/install/<mod_id>', methods=['POST'])
def install_door_mod(mod_id):
    """Install a door texture into MnSlChr.usd using HSDRawViewer --css-doors import."""
    try:
        mods = _load_doors_metadata()
        mod = next((m for m in mods if m['id'] == mod_id), None)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        door_png = DOORS_PATH / mod_id / 'door.png'
        if not door_png.exists():
            return jsonify({'success': False, 'error': 'door.png missing from mod'}), 400

        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No MEX project loaded'}), 400

        files_dir = get_project_files_dir()
        if files_dir is None:
            return jsonify({'success': False, 'error': 'No project files directory'}), 400

        mnslchr = Path(files_dir) / 'MnSlChr.usd'
        if not mnslchr.exists():
            return jsonify({'success': False, 'error': f'MnSlChr.usd not found at {mnslchr}'}), 400

        if not HSDRAW_EXE.exists():
            return jsonify({'success': False, 'error': f'HSDRawViewer not found'}), 500

        with tempfile.TemporaryDirectory(prefix='cssdoors_') as tmp:
            output_usd = Path(tmp) / 'MnSlChr.usd'
            result = _run_hsd_cli([
                '--css-doors', 'import',
                str(mnslchr), str(door_png), str(output_usd)
            ])
            if result is None:
                return jsonify({'success': False, 'error': 'HSDRawViewer --css-doors import failed'}), 500

            if not output_usd.exists():
                return jsonify({'success': False, 'error': 'Import produced no output file'}), 500

            shutil.copy(str(output_usd), str(mnslchr))

        msg = f'Installed door "{mod["name"]}". Rebuild ISO to apply.'
        logger.info(f'[OK] Installed CSS door mod {mod_id}')
        return jsonify({'success': True, 'message': msg})
    except Exception as e:
        logger.error(f'Install door mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
