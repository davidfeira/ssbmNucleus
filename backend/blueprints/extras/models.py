"""
Model extras - for 3D model replacements (gun, etc.).

Model extract/import via HSDRawViewer CLI and the /api/mex/storage/models/* routes.
"""

import json
import uuid
import logging
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from flask import request, jsonify
from werkzeug.utils import secure_filename

from extra_types import get_extra_type, get_storage_character
from core.config import get_subprocess_args

from . import extras_bp
from . import helpers
from .helpers import find_dat_file

logger = logging.getLogger(__name__)


def extract_model_from_dat(dat_path, jobj_path, output_dae_path):
    """Extract a model from a DAT file using HSDRawViewer CLI.

    Args:
        dat_path: Path to the source .dat file
        jobj_path: Path within the DAT to the JOBJ (e.g., "ftDataFalco/Articles/Articles_1/Model_/RootModelJoint")
        output_dae_path: Path to save the exported .dae file

    Returns:
        True if successful, raises exception on failure
    """
    if not helpers.HSDRAW_VIEWER_PATH:
        raise RuntimeError("HSDRawViewer path not configured")

    cmd = [
        str(helpers.HSDRAW_VIEWER_PATH),
        '--model', 'export',
        str(dat_path),
        jobj_path,
        str(output_dae_path)
    ]

    logger.info(f"Running model export: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, **get_subprocess_args())

    if result.returncode != 0:
        logger.error(f"Model export failed: {result.stderr}")
        raise RuntimeError(f"Model export failed: {result.stderr}")

    logger.info(f"Model export output: {result.stdout}")
    return True


def import_model_to_dat(dat_path, jobj_path, model_dae_path, output_dat_path):
    """Import a model into a DAT file using HSDRawViewer CLI.

    Args:
        dat_path: Path to the source .dat file
        jobj_path: Path within the DAT to the JOBJ
        model_dae_path: Path to the .dae model file to import
        output_dat_path: Path to save the modified .dat file

    Returns:
        True if successful, raises exception on failure
    """
    if not helpers.HSDRAW_VIEWER_PATH:
        raise RuntimeError("HSDRawViewer path not configured")

    cmd = [
        str(helpers.HSDRAW_VIEWER_PATH),
        '--model', 'import',
        str(dat_path),
        jobj_path,
        str(model_dae_path),
        str(output_dat_path)
    ]

    logger.info(f"Running model import: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, **get_subprocess_args())

    if result.returncode != 0:
        logger.error(f"Model import failed: {result.stderr}")
        raise RuntimeError(f"Model import failed: {result.stderr}")

    logger.info(f"Model import output: {result.stdout}")
    return True


@extras_bp.route('/api/mex/storage/models/create', methods=['POST'])
def create_model_extra():
    """Create a new model extra from an uploaded .dae or .dat file.

    For .dat files, extracts the model as .dae first.
    Stores the .dae in storage/[Character]/models/[uuid].dae

    Request: multipart/form-data with:
        - character: Character name (e.g., "Falco")
        - extraType: Extra type ID (e.g., "gun")
        - name: Display name for the mod
        - file: The .dae or .dat file
    """
    try:
        character = request.form.get('character')
        extra_type = request.form.get('extraType')
        name = request.form.get('name', 'Custom Model')

        if not character or not extra_type:
            return jsonify({
                'success': False,
                'error': 'Missing character or extraType parameter'
            }), 400

        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded'
            }), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Verify this extra type exists and is a model type
        type_config = get_extra_type(character, extra_type)
        if not type_config:
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" not defined for {character}'
            }), 400

        if type_config.get('type') != 'model':
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" is not a model type'
            }), 400

        # Get storage character
        storage_char = get_storage_character(character, extra_type)

        # Create models directory if needed
        models_dir = helpers.STORAGE_PATH / storage_char / 'models'
        models_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique ID
        mod_id = f"{extra_type}_{uuid.uuid4().hex[:8]}"

        # Determine file type and process
        filename = secure_filename(file.filename)
        file_ext = Path(filename).suffix.lower()

        if file_ext == '.dae':
            # Direct .dae upload - save directly
            dae_path = models_dir / f"{mod_id}.dae"
            file.save(str(dae_path))
            logger.info(f"Saved .dae model to {dae_path}")

        elif file_ext == '.dat':
            # .dat upload - need to extract the model
            # Save the .dat temporarily
            temp_dat = models_dir / f"{mod_id}_temp.dat"
            file.save(str(temp_dat))

            try:
                # Extract model from the .dat
                dae_path = models_dir / f"{mod_id}.dae"
                jobj_path = type_config.get('model_path')

                if not jobj_path:
                    return jsonify({
                        'success': False,
                        'error': 'Model path not configured for this extra type'
                    }), 400

                extract_model_from_dat(temp_dat, jobj_path, dae_path)
                logger.info(f"Extracted model from .dat to {dae_path}")

            finally:
                # Clean up temp .dat
                if temp_dat.exists():
                    temp_dat.unlink()
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported file type: {file_ext}. Use .dae or .dat'
            }), 400

        # Load metadata
        metadata_file = helpers.STORAGE_PATH / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {'characters': {}}

        # Ensure character structure exists
        if storage_char not in metadata.get('characters', {}):
            metadata['characters'][storage_char] = {'skins': [], 'extras': {}}

        char_data = metadata['characters'][storage_char]
        if 'extras' not in char_data:
            char_data['extras'] = {}
        if extra_type not in char_data['extras']:
            char_data['extras'][extra_type] = []

        # Create mod entry
        new_mod = {
            'id': mod_id,
            'name': name,
            'type': 'model',
            'date_added': datetime.now().isoformat(),
            'source': 'uploaded',
            'model_file': f"models/{mod_id}.dae"
        }

        char_data['extras'][extra_type].append(new_mod)

        # Save metadata
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Created model extra '{name}' ({extra_type}) for {storage_char}")

        return jsonify({
            'success': True,
            'mod': new_mod
        })

    except Exception as e:
        logger.error(f"Create model extra error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@extras_bp.route('/api/mex/storage/models/install', methods=['POST'])
def install_model_extra():
    """Install a model extra by importing the .dae into the target .dat file.

    Request body:
    {
        "character": "Falco",
        "extraType": "gun",
        "modId": "gun_abc123"
    }
    """
    try:
        data = request.json
        character = data.get('character')
        extra_type = data.get('extraType')
        mod_id = data.get('modId')

        if not character or not extra_type or not mod_id:
            return jsonify({
                'success': False,
                'error': 'Missing character, extraType, or modId parameter'
            }), 400

        # Get extra type config
        type_config = get_extra_type(character, extra_type)
        if not type_config:
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" not defined for {character}'
            }), 400

        if type_config.get('type') != 'model':
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" is not a model type'
            }), 400

        # Get storage character
        storage_char = get_storage_character(character, extra_type)

        # Find the .dat file in MEX project
        try:
            files_dir = helpers.get_project_files_dir()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        target_file = type_config['target_file']
        jobj_path = type_config.get('model_path')

        if not jobj_path:
            return jsonify({
                'success': False,
                'error': 'Model path not configured for this extra type'
            }), 400

        dat_path = find_dat_file(files_dir, target_file)
        if not dat_path or not dat_path.exists():
            return jsonify({
                'success': False,
                'error': f'Could not find {target_file} in MEX project'
            }), 404

        # Load metadata to find the mod
        metadata_file = helpers.STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({
                'success': False,
                'error': 'Metadata file not found'
            }), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        # Find the mod
        char_data = metadata.get('characters', {}).get(storage_char, {})
        extras = char_data.get('extras', {})
        mods = extras.get(extra_type, [])

        found_mod = None
        for mod in mods:
            if mod.get('id') == mod_id:
                found_mod = mod
                break

        if not found_mod:
            return jsonify({
                'success': False,
                'error': f'Mod {mod_id} not found'
            }), 404

        # Get the .dae file path
        model_file = found_mod.get('model_file')
        if not model_file:
            return jsonify({
                'success': False,
                'error': 'Model file not found in mod metadata'
            }), 400

        dae_path = helpers.STORAGE_PATH / storage_char / model_file
        if not dae_path.exists():
            return jsonify({
                'success': False,
                'error': f'Model file not found: {dae_path}'
            }), 404

        # Import the model into the .dat file (in place)
        # We'll write to a temp file then replace the original
        temp_output = dat_path.parent / f"{dat_path.stem}_temp{dat_path.suffix}"

        try:
            import_model_to_dat(dat_path, jobj_path, dae_path, temp_output)

            # Replace original with modified
            shutil.move(str(temp_output), str(dat_path))
            logger.info(f"[OK] Installed model '{found_mod['name']}' to {target_file}")

        except Exception as e:
            # Clean up temp file on failure
            if temp_output.exists():
                temp_output.unlink()
            raise

        return jsonify({
            'success': True
        })

    except Exception as e:
        logger.error(f"Install model extra error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@extras_bp.route('/api/mex/storage/models/delete', methods=['POST'])
def delete_model_extra():
    """Delete a model extra and its .dae file.

    Request body:
    {
        "character": "Falco",
        "extraType": "gun",
        "modId": "gun_abc123"
    }
    """
    try:
        data = request.json
        character = data.get('character')
        extra_type = data.get('extraType')
        mod_id = data.get('modId')

        if not character or not extra_type or not mod_id:
            return jsonify({
                'success': False,
                'error': 'Missing character, extraType, or modId parameter'
            }), 400

        # Get storage character
        storage_char = get_storage_character(character, extra_type)

        # Load metadata
        metadata_file = helpers.STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({
                'success': False,
                'error': 'Metadata file not found'
            }), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        # Find the mod
        char_data = metadata.get('characters', {}).get(storage_char, {})
        extras = char_data.get('extras', {})
        mods = extras.get(extra_type, [])

        # Find and remove the mod
        found_mod = None
        new_mods = []
        for mod in mods:
            if mod.get('id') == mod_id:
                found_mod = mod
            else:
                new_mods.append(mod)

        if not found_mod:
            return jsonify({
                'success': False,
                'error': f'Mod {mod_id} not found'
            }), 404

        # Delete the model file if it exists
        model_file = found_mod.get('model_file')
        if model_file:
            dae_path = helpers.STORAGE_PATH / storage_char / model_file
            if dae_path.exists():
                dae_path.unlink()
                logger.info(f"Deleted model file: {dae_path}")

        # Update metadata
        extras[extra_type] = new_mods

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Deleted model extra {mod_id} from {storage_char}")

        return jsonify({
            'success': True
        })

    except Exception as e:
        logger.error(f"Delete model extra error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
