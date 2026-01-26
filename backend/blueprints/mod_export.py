"""
Mod Export Blueprint - Export costumes and stages as ZIP files.

Handles exporting individual costumes and stage variants for sharing.
"""

import os
import json
import zipfile
import logging
from flask import Blueprint, request, jsonify, send_file, after_this_request

from core.config import STORAGE_PATH, OUTPUT_PATH

logger = logging.getLogger(__name__)

mod_export_bp = Blueprint('mod_export', __name__)

# DAS Stage configuration
DAS_STAGES = {
    'GrNBa': {'code': 'GrNBa', 'name': 'Battlefield', 'folder': 'battlefield'},
    'GrNLa': {'code': 'GrNLa', 'name': 'Final Destination', 'folder': 'final_destination'},
    'GrSt': {'code': 'GrSt', 'name': "Yoshi's Story", 'folder': 'yoshis_story'},
    'GrOp': {'code': 'GrOp', 'name': 'Dreamland', 'folder': 'dreamland'},
    'GrPs': {'code': 'GrPs', 'name': 'Pokemon Stadium', 'folder': 'pokemon_stadium'},
    'GrIz': {'code': 'GrIz', 'name': 'Fountain of Dreams', 'folder': 'fountain_of_dreams'}
}


@mod_export_bp.route('/api/mex/storage/costumes/export', methods=['POST'])
def export_costume():
    """Export a single costume as a ZIP file"""
    try:
        data = request.json
        character = data.get('character')
        skin_id = data.get('skinId')
        color_name = data.get('colorName', 'costume')

        logger.info("=== COSTUME EXPORT REQUEST ===")
        logger.info(f"Character: {character}, Skin ID: {skin_id}")

        if not character or not skin_id:
            return jsonify({'success': False, 'error': 'Missing character or skinId parameter'}), 400

        char_folder = STORAGE_PATH / character
        zip_path = char_folder / f"{skin_id}.zip"
        csp_path = char_folder / f"{skin_id}_csp.png"
        stock_path = char_folder / f"{skin_id}_stc.png"

        if not zip_path.exists():
            return jsonify({'success': False, 'error': f'Costume not found: {skin_id}'}), 404

        # Check if this is Ice Climbers Popo with paired Nana
        metadata_file = STORAGE_PATH / 'metadata.json'
        paired_nana_id = None
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            if character in metadata.get('characters', {}):
                for skin in metadata['characters'][character]['skins']:
                    if skin['id'] == skin_id:
                        if skin.get('is_popo') and skin.get('paired_nana_id'):
                            paired_nana_id = skin['paired_nana_id']
                            logger.info(f"Ice Climbers Popo detected, paired Nana: {paired_nana_id}")
                        break

        export_dir = OUTPUT_PATH / "mod_exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        safe_character = "".join(c for c in character if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
        safe_color = "".join(c for c in color_name if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
        export_filename = f"{safe_character}_{safe_color}.zip"
        export_path = export_dir / export_filename

        with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as export_zip:
            with zipfile.ZipFile(zip_path, 'r') as source_zip:
                for item in source_zip.namelist():
                    if item.lower().endswith('.dat'):
                        dat_data = source_zip.read(item)
                        export_zip.writestr(item, dat_data)
                        logger.info(f"  Added: {item}")

            if csp_path.exists():
                export_zip.write(csp_path, 'csp.png')
                logger.info(f"  Added: csp.png")

            if stock_path.exists():
                export_zip.write(stock_path, 'stc.png')
                logger.info(f"  Added: stc.png")

            if paired_nana_id:
                nana_zip_path = char_folder / f"{paired_nana_id}.zip"
                if nana_zip_path.exists():
                    with zipfile.ZipFile(nana_zip_path, 'r') as nana_zip:
                        for item in nana_zip.namelist():
                            if item.lower().endswith('.dat'):
                                nana_dat_data = nana_zip.read(item)
                                export_zip.writestr(item, nana_dat_data)
                                logger.info(f"  Added Nana: {item}")

        logger.info(f"[OK] Costume exported: {export_filename}")
        return jsonify({'success': True, 'filename': export_filename})
    except Exception as e:
        logger.error(f"Costume export error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@mod_export_bp.route('/api/mex/storage/stages/export', methods=['POST'])
def export_stage():
    """Export a single stage variant as a ZIP file"""
    try:
        data = request.json
        stage_code = data.get('stageCode')
        stage_name = data.get('stageName', 'stage')
        variant_id = data.get('variantId')
        variant_name = data.get('variantName', 'variant')

        logger.info("=== STAGE EXPORT REQUEST ===")
        logger.info(f"Stage Code: {stage_code}, Variant ID: {variant_id}")

        if not stage_code or not variant_id:
            return jsonify({'success': False, 'error': 'Missing stageCode or variantId parameter'}), 400

        if stage_code not in DAS_STAGES:
            return jsonify({'success': False, 'error': f'Unknown stage code: {stage_code}'}), 400

        stage_info = DAS_STAGES[stage_code]
        stage_folder = stage_info['folder']
        file_ext = '.usd' if stage_code == 'GrPs' else '.dat'

        storage_stage_path = STORAGE_PATH / 'das' / stage_folder
        stage_zip_path = storage_stage_path / f"{variant_id}.zip"
        screenshot_path = storage_stage_path / f"{variant_id}_screenshot.png"

        if not stage_zip_path.exists():
            return jsonify({'success': False, 'error': f'Stage variant not found in storage: {variant_id}'}), 404

        export_dir = OUTPUT_PATH / "mod_exports"
        export_dir.mkdir(parents=True, exist_ok=True)

        safe_stage = "".join(c for c in stage_name if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
        safe_variant = "".join(c for c in variant_name if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
        export_filename = f"{safe_stage}_{safe_variant}.zip"
        export_path = export_dir / export_filename

        with zipfile.ZipFile(export_path, 'w', zipfile.ZIP_DEFLATED) as export_zip:
            with zipfile.ZipFile(stage_zip_path, 'r') as source_zip:
                for item in source_zip.namelist():
                    if item.lower().endswith(file_ext):
                        stage_data = source_zip.read(item)
                        export_zip.writestr(item, stage_data)
                        logger.info(f"  Added: {item}")

            if screenshot_path.exists():
                export_zip.write(screenshot_path, 'screenshot.png')
                logger.info(f"  Added: screenshot.png")

        logger.info(f"[OK] Stage exported: {export_filename}")
        return jsonify({'success': True, 'filename': export_filename})
    except Exception as e:
        logger.error(f"Stage export error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@mod_export_bp.route('/api/mex/export/mod/<filename>', methods=['GET'])
def download_mod(filename):
    """Download an exported mod file"""
    try:
        export_dir = OUTPUT_PATH / "mod_exports"
        file_path = export_dir / filename

        if not file_path.exists():
            return jsonify({'success': False, 'error': 'Export file not found'}), 404

        @after_this_request
        def remove_file(response):
            try:
                os.remove(file_path)
                logger.info(f"Deleted mod export file after download: {filename}")
            except Exception as error:
                logger.error(f"Error deleting mod export file {filename}: {str(error)}")
            return response

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/zip'
        )
    except Exception as e:
        logger.error(f"Mod download error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
