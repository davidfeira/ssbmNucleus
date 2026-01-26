"""
Storage Stages Blueprint - Storage vault stage operations.

Handles deleting, renaming, reordering, screenshot updates, and Slippi status
for stored stage variants.
"""

import re
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

from core.config import STORAGE_PATH

logger = logging.getLogger(__name__)

storage_stages_bp = Blueprint('storage_stages', __name__)


def sanitize_filename(name):
    """Sanitize filename by removing/replacing invalid characters."""
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


@storage_stages_bp.route('/api/mex/storage/stages/delete', methods=['POST'])
def delete_storage_stage():
    """Delete stage variant from storage"""
    try:
        data = request.json
        stage_folder = data.get('stageFolder')
        variant_id = data.get('variantId')

        if not stage_folder or not variant_id:
            return jsonify({'success': False, 'error': 'Missing stageFolder or variantId parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if stage_folder not in metadata.get('stages', {}):
            return jsonify({'success': False, 'error': f'Stage folder {stage_folder} not found in metadata'}), 404

        stage_data = metadata['stages'][stage_folder]
        variants = stage_data.get('variants', [])
        variant_to_delete = None
        variant_index = None

        for idx, variant in enumerate(variants):
            if variant['id'] == variant_id:
                variant_to_delete = variant
                variant_index = idx
                break

        if not variant_to_delete:
            return jsonify({'success': False, 'error': f'Variant {variant_id} not found in {stage_folder}'}), 404

        das_folder = STORAGE_PATH / 'das' / stage_folder
        zip_file = das_folder / variant_to_delete['filename']
        screenshot_file = das_folder / f"{variant_id}_screenshot.png"

        deleted_files = []
        if zip_file.exists():
            zip_file.unlink()
            deleted_files.append(str(zip_file))
        if screenshot_file.exists():
            screenshot_file.unlink()
            deleted_files.append(str(screenshot_file))

        variants.pop(variant_index)

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Deleted stage variant {variant_id} from {stage_folder}")
        return jsonify({'success': True, 'message': f'Successfully deleted {variant_id}', 'deleted_files': deleted_files})
    except Exception as e:
        logger.error(f"Delete stage variant error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_stages_bp.route('/api/mex/storage/stages/rename', methods=['POST'])
def rename_storage_stage():
    """Rename stage variant (update name field)"""
    try:
        data = request.json
        stage_folder = data.get('stageFolder')
        variant_id = data.get('variantId')
        new_name = data.get('newName')

        if not stage_folder or not variant_id or not new_name:
            return jsonify({'success': False, 'error': 'Missing stageFolder, variantId, or newName parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if stage_folder not in metadata.get('stages', {}):
            return jsonify({'success': False, 'error': f'Stage folder {stage_folder} not found in metadata'}), 404

        stage_data = metadata['stages'][stage_folder]
        variants = stage_data.get('variants', [])

        sanitized_new_name = sanitize_filename(new_name).lower()
        for variant in variants:
            if variant['id'] != variant_id:
                existing_name = sanitize_filename(variant.get('name', '')).lower()
                if existing_name == sanitized_new_name:
                    return jsonify({'success': False, 'error': f"A variant named '{variant['name']}' already exists in this stage"}), 400

        variant_found = False
        for variant in variants:
            if variant['id'] == variant_id:
                variant['name'] = new_name
                variant_found = True
                break

        if not variant_found:
            return jsonify({'success': False, 'error': f'Variant {variant_id} not found in {stage_folder}'}), 404

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Renamed stage variant {variant_id} to '{new_name}'")
        return jsonify({'success': True, 'message': f'Successfully renamed to {new_name}'})
    except Exception as e:
        logger.error(f"Rename stage variant error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_stages_bp.route('/api/mex/storage/stages/update-screenshot', methods=['POST'])
def update_stage_screenshot():
    """Update screenshot for a stage variant"""
    try:
        stage_folder = request.form.get('stageFolder')
        variant_id = request.form.get('variantId')

        if not stage_folder or not variant_id:
            return jsonify({'success': False, 'error': 'Missing stageFolder or variantId parameter'}), 400

        if 'screenshot' not in request.files:
            return jsonify({'success': False, 'error': 'No screenshot file provided'}), 400

        screenshot_file = request.files['screenshot']
        if screenshot_file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        screenshot_data = screenshot_file.read()

        das_folder = STORAGE_PATH / 'das' / stage_folder
        das_folder.mkdir(parents=True, exist_ok=True)
        storage_screenshot_path = das_folder / f"{variant_id}_screenshot.png"
        storage_screenshot_path.write_bytes(screenshot_data)

        metadata_file = STORAGE_PATH / 'metadata.json'
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            if stage_folder in metadata.get('stages', {}):
                stage_data = metadata['stages'][stage_folder]
                variants = stage_data.get('variants', [])

                for variant in variants:
                    if variant['id'] == variant_id:
                        variant['has_screenshot'] = True
                        break

                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Updated screenshot for {stage_folder}/{variant_id}")
        return jsonify({'success': True, 'message': 'Screenshot updated successfully', 'screenshotUrl': f"/storage/das/{stage_folder}/{variant_id}_screenshot.png"})
    except Exception as e:
        logger.error(f"Update screenshot error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_stages_bp.route('/api/mex/storage/stages/set-slippi', methods=['POST'])
def set_stage_slippi():
    """Manually set slippi safety status for a stage variant"""
    try:
        data = request.json
        stage_name = data.get('stageName')
        variant_id = data.get('variantId')
        slippi_safe = data.get('slippiSafe')

        if not stage_name or not variant_id or slippi_safe is None:
            return jsonify({'success': False, 'error': 'Missing stageName, variantId, or slippiSafe parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if stage_name not in metadata.get('stages', {}):
            return jsonify({'success': False, 'error': f'Stage {stage_name} not found in metadata'}), 404

        variant_found = False
        for variant in metadata['stages'][stage_name].get('variants', []):
            if variant['id'] == variant_id:
                variant['slippi_safe'] = slippi_safe
                variant['slippi_manual_override'] = True
                variant['slippi_test_date'] = datetime.now().isoformat()
                variant_found = True
                break

        if not variant_found:
            return jsonify({'success': False, 'error': f'Variant {variant_id} not found for {stage_name}'}), 404

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Manually set slippi status for {stage_name} - {variant_id}: {slippi_safe}")
        return jsonify({
            'success': True,
            'slippi_safe': slippi_safe,
            'message': f"Manually set to {'Slippi Safe' if slippi_safe else 'Not Slippi Safe'}"
        })
    except Exception as e:
        logger.error(f"Set stage slippi error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_stages_bp.route('/api/mex/storage/stages/reorder', methods=['POST'])
def reorder_stages():
    """Reorder stage variants in storage"""
    try:
        data = request.json
        stage_folder = data.get('stageFolder')
        from_index = data.get('fromIndex')
        to_index = data.get('toIndex')

        if stage_folder is None or from_index is None or to_index is None:
            return jsonify({'success': False, 'error': 'Missing stageFolder, fromIndex, or toIndex parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if stage_folder not in metadata.get('stages', {}):
            return jsonify({'success': False, 'error': f'Stage folder {stage_folder} not found in metadata'}), 404

        stage_data = metadata['stages'][stage_folder]
        variants = stage_data.get('variants', [])

        if from_index < 0 or from_index >= len(variants) or to_index < 0 or to_index >= len(variants):
            return jsonify({'success': False, 'error': 'Invalid fromIndex or toIndex'}), 400

        variant = variants.pop(from_index)
        variants.insert(to_index, variant)

        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Reordered {stage_folder} variants: moved index {from_index} to {to_index}")
        return jsonify({'success': True, 'variants': variants})
    except Exception as e:
        logger.error(f"Reorder stages error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_stages_bp.route('/api/mex/storage/stages/move-to-top', methods=['POST'])
def move_stage_to_top():
    """Move a stage variant to the top of the list"""
    try:
        data = request.json
        stage_folder = data.get('stageFolder')
        variant_id = data.get('variantId')

        if not stage_folder or not variant_id:
            return jsonify({'success': False, 'error': 'Missing stageFolder or variantId parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if stage_folder not in metadata.get('stages', {}):
            return jsonify({'success': False, 'error': f'Stage folder {stage_folder} not found in metadata'}), 404

        stage_data = metadata['stages'][stage_folder]
        variants = stage_data.get('variants', [])

        variant_index = None
        for i, variant in enumerate(variants):
            if variant['id'] == variant_id:
                variant_index = i
                break

        if variant_index is None:
            return jsonify({'success': False, 'error': f'Variant {variant_id} not found'}), 404

        if variant_index > 0:
            variant = variants.pop(variant_index)
            variants.insert(0, variant)
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"[OK] Moved {stage_folder} variant {variant_id} to top")

        return jsonify({'success': True, 'variants': variants})
    except Exception as e:
        logger.error(f"Move stage to top error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@storage_stages_bp.route('/api/mex/storage/stages/move-to-bottom', methods=['POST'])
def move_stage_to_bottom():
    """Move a stage variant to the bottom of the list"""
    try:
        data = request.json
        stage_folder = data.get('stageFolder')
        variant_id = data.get('variantId')

        if not stage_folder or not variant_id:
            return jsonify({'success': False, 'error': 'Missing stageFolder or variantId parameter'}), 400

        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({'success': False, 'error': 'Metadata file not found'}), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        if stage_folder not in metadata.get('stages', {}):
            return jsonify({'success': False, 'error': f'Stage folder {stage_folder} not found in metadata'}), 404

        stage_data = metadata['stages'][stage_folder]
        variants = stage_data.get('variants', [])

        variant_index = None
        for i, variant in enumerate(variants):
            if variant['id'] == variant_id:
                variant_index = i
                break

        if variant_index is None:
            return jsonify({'success': False, 'error': f'Variant {variant_id} not found'}), 404

        if variant_index < len(variants) - 1:
            variant = variants.pop(variant_index)
            variants.append(variant)
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            logger.info(f"[OK] Moved {stage_folder} variant {variant_id} to bottom")

        return jsonify({'success': True, 'variants': variants})
    except Exception as e:
        logger.error(f"Move stage to bottom error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
