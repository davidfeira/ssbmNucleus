"""
DAS Blueprint - Dynamic Alternate Stages endpoints.

Handles DAS framework installation, stage variant management,
and import/removal of stage variants from storage to project.
"""

import os
import re
import json
import glob
import shutil
import zipfile
import logging
from pathlib import Path
from flask import Blueprint, request, jsonify

from core.config import PROJECT_ROOT, STORAGE_PATH, BASE_PATH
from core.state import get_project_files_dir

logger = logging.getLogger(__name__)

das_bp = Blueprint('das', __name__)

# DAS Stage configuration
DAS_STAGES = {
    'GrNBa': {'code': 'GrNBa', 'name': 'Battlefield', 'folder': 'battlefield'},
    'GrNLa': {'code': 'GrNLa', 'name': 'Final Destination', 'folder': 'final_destination'},
    'GrSt': {'code': 'GrSt', 'name': "Yoshi's Story", 'folder': 'yoshis_story'},
    'GrOp': {'code': 'GrOp', 'name': 'Dreamland', 'folder': 'dreamland'},
    'GrPs': {'code': 'GrPs', 'name': 'Pokemon Stadium', 'folder': 'pokemon_stadium'},
    'GrIz': {'code': 'GrIz', 'name': 'Fountain of Dreams', 'folder': 'fountain_of_dreams'}
}

# Mapping of stage codes to default screenshot filenames
DAS_DEFAULT_SCREENSHOTS = {
    'GrNBa': 'battlefield.jpg',
    'GrNLa': 'final destination.png',
    'GrSt': 'Yoshis story.jpg',
    'GrOp': 'dreamland.jpg',
    'GrPs': 'pokemon stadium.jpg',
    'GrIz': 'Fountain of Dreams.webp'
}


def strip_button_indicator(filename):
    """
    Remove button indicator from filename stem
    Example: vanilla(B) -> vanilla
    """
    return re.sub(r'\(([ABXYLRZ])\)$', '', filename, flags=re.IGNORECASE)


def extract_button_indicator(filename):
    """
    Extract button indicator from filename stem
    Example: vanilla(B) -> B
    Returns None if no button indicator found
    """
    match = re.search(r'\(([ABXYLRZ])\)$', filename, flags=re.IGNORECASE)
    return match.group(1).upper() if match else None


def add_button_indicator(filename, button):
    """
    Add button indicator to filename (replaces existing if present)
    Example: vanilla, B -> vanilla(B)
    """
    cleaned = strip_button_indicator(filename)
    return f"{cleaned}({button.upper()})"


def sanitize_filename(name):
    """
    Sanitize a display name for use as a filename
    Removes filesystem-unsafe characters while keeping readability
    """
    sanitized = re.sub(r'[<>:"/\\|?*]', '', name)
    sanitized = sanitized.strip()
    return sanitized


def find_stage_screenshot(folder_path: Path, variant_id: str):
    """
    Find a stage screenshot with any image extension.
    Returns (exists: bool, path: Path or None, extension: str or None)
    """
    # Look for screenshot with any common image extension
    pattern = str(folder_path / f"{variant_id}_screenshot.*")
    matches = glob.glob(pattern)

    # Filter to only image extensions
    image_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp'}
    for match in matches:
        ext = os.path.splitext(match)[1].lower()
        if ext in image_extensions:
            return True, Path(match), ext

    return False, None, None


@das_bp.route('/api/mex/das/status', methods=['GET'])
def das_get_status():
    """Check if DAS framework is installed"""
    try:
        # Check if DAS loader files exist in current project's files/
        project_files_path = get_project_files_dir()
        installed_stages = []

        for stage_code, stage_info in DAS_STAGES.items():
            loader_path = project_files_path / f"{stage_code}.dat"
            folder_path = project_files_path / stage_code

            if loader_path.exists() and folder_path.exists():
                installed_stages.append(stage_code)

        is_installed = len(installed_stages) > 0

        return jsonify({
            'success': True,
            'installed': is_installed,
            'installedStages': installed_stages,
            'totalStages': len(DAS_STAGES)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@das_bp.route('/api/mex/das/install', methods=['POST'])
def das_install():
    """Install DAS framework"""
    try:
        logger.info("=== DAS FRAMEWORK INSTALLATION ===")

        # Use BASE_PATH for bundled resources (includes DAS files)
        das_source = BASE_PATH / "utility" / "DynamicAlternateStages"
        project_files = get_project_files_dir()

        if not das_source.exists():
            return jsonify({
                'success': False,
                'error': f'DAS framework source not found at {das_source}'
            }), 500

        project_files.mkdir(parents=True, exist_ok=True)

        # Install each stage
        for stage_code, stage_info in DAS_STAGES.items():
            logger.info(f"Installing DAS for {stage_info['name']} ({stage_code})...")

            # Pokemon Stadium uses .usd, others use .dat
            file_ext = '.usd' if stage_code == 'GrPs' else '.dat'

            # Create stage folder first
            stage_folder = project_files / stage_code
            stage_folder.mkdir(exist_ok=True)
            logger.info(f"  Created folder: {stage_code}/")

            # Get paths
            original_stage = project_files / f"{stage_code}{file_ext}"
            loader_src = das_source / f"{stage_code}{file_ext}"
            vanilla_in_folder = stage_folder / f"vanilla{file_ext}"

            # If vanilla variant doesn't exist yet and original stage exists, copy it into folder
            if not vanilla_in_folder.exists() and original_stage.exists():
                shutil.copy2(original_stage, vanilla_in_folder)
                logger.info(f"  Copied vanilla stage to {stage_code}/vanilla{file_ext}")

                # Copy default screenshot for vanilla variant to storage
                if stage_code in DAS_DEFAULT_SCREENSHOTS:
                    default_screenshot = PROJECT_ROOT / "utility" / "assets" / "stages" / DAS_DEFAULT_SCREENSHOTS[stage_code]
                    if default_screenshot.exists():
                        storage_das_folder = STORAGE_PATH / 'das' / stage_info['folder']
                        storage_das_folder.mkdir(parents=True, exist_ok=True)
                        storage_screenshot = storage_das_folder / f"vanilla_screenshot.png"
                        shutil.copy2(default_screenshot, storage_screenshot)
                        logger.info(f"  Copied default screenshot to storage: {storage_screenshot.name}")

            # Install DAS loader (replaces original stage file)
            if loader_src.exists():
                shutil.copy2(loader_src, original_stage)
                logger.info(f"  Installed DAS loader: {stage_code}{file_ext}")
            else:
                logger.warning(f"  DAS loader not found: {loader_src}")

        logger.info("DAS framework installed successfully")

        return jsonify({
            'success': True,
            'message': 'DAS framework installed successfully'
        })
    except Exception as e:
        logger.error(f"DAS installation error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@das_bp.route('/api/mex/das/stages', methods=['GET'])
def das_list_stages():
    """List all DAS-supported stages"""
    try:
        stages = []
        for stage_code, stage_info in DAS_STAGES.items():
            stages.append({
                'code': stage_code,
                'name': stage_info['name'],
                'folder': stage_info['folder']
            })

        return jsonify({
            'success': True,
            'stages': stages
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@das_bp.route('/api/mex/das/stages/<stage_code>/variants', methods=['GET'])
def das_get_stage_variants(stage_code):
    """Get DAS variants for a specific stage from MEX project"""
    try:
        if stage_code not in DAS_STAGES:
            return jsonify({
                'success': False,
                'error': f'Unknown stage code: {stage_code}'
            }), 400

        # List stage files in current project's files/{stage_code}/ (.dat or .usd for Pokemon Stadium)
        project_files = get_project_files_dir()
        stage_folder = project_files / stage_code
        variants = []

        if stage_folder.exists() and stage_folder.is_dir():
            # Pokemon Stadium uses .usd, others use .dat
            file_pattern = '*.usd' if stage_code == 'GrPs' else '*.dat'

            # Load metadata to get slippi status and other info
            metadata_file = STORAGE_PATH / 'metadata.json'
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

            stage_folder_name = DAS_STAGES[stage_code]['folder']
            stage_metadata = metadata.get('stages', {}).get(stage_folder_name, {})
            metadata_variants = {v['id']: v for v in stage_metadata.get('variants', [])}

            for stage_file in stage_folder.glob(file_pattern):
                filename_stem = stage_file.stem  # e.g., "Autumn Dreamland" or "Autumn Dreamland(B)"

                # Extract button indicator (e.g., "Autumn Dreamland(B)" -> "B")
                button = extract_button_indicator(filename_stem)

                # Strip button indicator for matching
                display_name_from_file = strip_button_indicator(filename_stem)

                # Reverse-lookup: display name -> variant_id using metadata
                variant_id_for_screenshot = None
                variant_meta = {}

                # Try to match display name to variant in metadata
                sanitized_display_name = sanitize_filename(display_name_from_file).lower()
                for vid, vmeta in metadata_variants.items():
                    variant_display_name = vmeta.get('name', vid)
                    if sanitize_filename(variant_display_name).lower() == sanitized_display_name:
                        variant_id_for_screenshot = vid
                        variant_meta = vmeta
                        logger.info(f"Matched display name '{display_name_from_file}' to variant_id '{vid}'")
                        break

                # Fallback: if no match in metadata, treat filename as variant_id
                if variant_id_for_screenshot is None:
                    variant_id_for_screenshot = display_name_from_file
                    variant_meta = metadata_variants.get(variant_id_for_screenshot, {})
                    logger.info(f"No metadata match for '{display_name_from_file}', using as variant_id")

                # Check if screenshot exists in storage (supports multiple extensions)
                screenshot_folder = STORAGE_PATH / 'das' / stage_folder_name
                has_screenshot, screenshot_path, screenshot_ext = find_stage_screenshot(screenshot_folder, variant_id_for_screenshot)

                variants.append({
                    'name': filename_stem,
                    'filename': stage_file.name,
                    'stageCode': stage_code,
                    'button': button,
                    'hasScreenshot': has_screenshot,
                    'screenshotUrl': f"/storage/das/{stage_folder_name}/{variant_id_for_screenshot}_screenshot{screenshot_ext}" if has_screenshot else None,
                    'slippi_safe': variant_meta.get('slippi_safe'),
                    'slippi_tested': variant_meta.get('slippi_tested', False)
                })

        return jsonify({
            'success': True,
            'stage': DAS_STAGES[stage_code],
            'variants': variants
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@das_bp.route('/api/mex/das/storage/variants', methods=['GET'])
def das_list_storage_variants():
    """List all DAS variants in storage"""
    try:
        stage_code = request.args.get('stage')
        variants = []

        # Load metadata to get proper names
        metadata_file = STORAGE_PATH / 'metadata.json'
        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

        # Determine which stages to scan
        stages_to_scan = {stage_code: DAS_STAGES[stage_code]} if stage_code and stage_code in DAS_STAGES else DAS_STAGES

        for code, stage_info in stages_to_scan.items():
            stage_folder = stage_info['folder']
            stage_storage_path = STORAGE_PATH / "das" / stage_folder

            # Get variants from metadata for this stage
            stage_metadata = metadata.get('stages', {}).get(stage_folder, {})
            metadata_variants_list = stage_metadata.get('variants', [])

            if stage_storage_path.exists():
                # Build a lookup of all zip files that exist on disk
                zip_files = {zip_file.stem: zip_file for zip_file in stage_storage_path.glob('*.zip')}

                # First, add variants in metadata order (if they exist on disk)
                for variant_meta in metadata_variants_list:
                    variant_id = variant_meta['id']
                    zip_file = zip_files.get(variant_id)

                    # Only add if the zip file actually exists
                    if zip_file:
                        variant_name = variant_meta.get('name', variant_id)

                        # Check for screenshot in storage
                        has_screenshot, screenshot_path, screenshot_ext = find_stage_screenshot(stage_storage_path, variant_id)

                        variants.append({
                            'stageCode': code,
                            'stageName': stage_info['name'],
                            'id': variant_id,
                            'name': variant_name,
                            'zipPath': str(zip_file.relative_to(PROJECT_ROOT)),
                            'hasScreenshot': has_screenshot,
                            'screenshotUrl': f"/storage/das/{stage_info['folder']}/{variant_id}_screenshot{screenshot_ext}" if has_screenshot else None,
                            'slippi_safe': variant_meta.get('slippi_safe'),
                            'slippi_tested': variant_meta.get('slippi_tested', False),
                            'slippi_test_date': variant_meta.get('slippi_test_date')
                        })

                        # Remove from zip_files so we don't add it again
                        del zip_files[variant_id]

                # Then, add any remaining zip files that aren't in metadata
                for variant_id, zip_file in zip_files.items():
                    has_screenshot, screenshot_path, screenshot_ext = find_stage_screenshot(stage_storage_path, variant_id)

                    variants.append({
                        'stageCode': code,
                        'stageName': stage_info['name'],
                        'id': variant_id,
                        'name': variant_id,
                        'zipPath': str(zip_file.relative_to(PROJECT_ROOT)),
                        'hasScreenshot': has_screenshot,
                        'screenshotUrl': f"/storage/das/{stage_info['folder']}/{variant_id}_screenshot{screenshot_ext}" if has_screenshot else None,
                        'slippi_safe': None,
                        'slippi_tested': False,
                        'slippi_test_date': None
                    })

        return jsonify({
            'success': True,
            'variants': variants
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@das_bp.route('/api/mex/das/import', methods=['POST'])
def das_import_variant():
    """Import DAS variant to MEX project"""
    try:
        data = request.json
        stage_code = data.get('stageCode')
        variant_path = data.get('variantPath')

        logger.info(f"=== DAS IMPORT REQUEST ===")
        logger.info(f"Stage Code: {stage_code}")
        logger.info(f"Variant Path: {variant_path}")

        if not stage_code or not variant_path:
            return jsonify({
                'success': False,
                'error': 'Missing stageCode or variantPath parameter'
            }), 400

        if stage_code not in DAS_STAGES:
            return jsonify({
                'success': False,
                'error': f'Unknown stage code: {stage_code}'
            }), 400

        # Resolve variant path
        full_variant_path = PROJECT_ROOT / variant_path

        if not full_variant_path.exists():
            return jsonify({
                'success': False,
                'error': f'Variant ZIP not found: {variant_path}'
            }), 404

        project_files = get_project_files_dir()
        stage_folder = project_files / stage_code
        stage_folder.mkdir(exist_ok=True)

        # Pokemon Stadium uses .usd, others use .dat
        file_ext = '.usd' if stage_code == 'GrPs' else '.dat'

        with zipfile.ZipFile(full_variant_path, 'r') as zip_ref:
            # Find the stage file in the zip
            stage_files = [f for f in zip_ref.namelist() if f.endswith(file_ext) or f.endswith('.dat')]
            if not stage_files:
                return jsonify({
                    'success': False,
                    'error': f'No {file_ext} file found in ZIP'
                }), 400

            # Read the stage file data
            stage_file = stage_files[0]
            stage_data = zip_ref.read(stage_file)

            # Get variant_id from ZIP filename
            variant_id = Path(full_variant_path).stem

            # Load metadata to get display name
            metadata_file = STORAGE_PATH / 'metadata.json'
            display_name = variant_id

            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)

                stage_folder_name = DAS_STAGES[stage_code]['folder']
                stage_metadata = metadata.get('stages', {}).get(stage_folder_name, {})

                # Find the variant in metadata by id
                for variant in stage_metadata.get('variants', []):
                    if variant['id'] == variant_id:
                        display_name = variant.get('name', variant_id)
                        logger.info(f"Found display name in metadata: '{display_name}' for variant_id '{variant_id}'")
                        break

            # Use sanitized display name for filename
            final_name = sanitize_filename(display_name)
            final_path = stage_folder / f"{final_name}{file_ext}"

            # If file already exists, append suffix to avoid conflicts
            if final_path.exists():
                count = 1
                while True:
                    final_name = f"{sanitize_filename(display_name)}_{count}"
                    final_path = stage_folder / f"{final_name}{file_ext}"
                    if not final_path.exists():
                        break
                    count += 1

            # Write directly to final location
            final_path.write_bytes(stage_data)
            logger.info(f"[OK] Extracted stage file to: {final_path}")
            logger.info(f"  Using mod name: {final_name}")

        logger.info(f"DAS variant imported to: {final_path}")

        return jsonify({
            'success': True,
            'message': 'DAS variant imported successfully',
            'path': str(final_path)
        })
    except Exception as e:
        logger.error(f"DAS import error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@das_bp.route('/api/mex/das/remove', methods=['POST'])
def das_remove_variant():
    """Remove DAS variant from MEX project"""
    try:
        data = request.json
        stage_code = data.get('stageCode')
        variant_name = data.get('variantName')

        logger.info(f"=== DAS REMOVE REQUEST ===")
        logger.info(f"Stage Code: {stage_code}")
        logger.info(f"Variant Name: {variant_name}")

        if not stage_code or not variant_name:
            return jsonify({
                'success': False,
                'error': 'Missing stageCode or variantName parameter'
            }), 400

        if stage_code not in DAS_STAGES:
            return jsonify({
                'success': False,
                'error': f'Unknown stage code: {stage_code}'
            }), 400

        # Find and remove the variant file
        file_ext = '.usd' if stage_code == 'GrPs' else '.dat'
        project_files = get_project_files_dir()
        stage_folder = project_files / stage_code
        variant_path = stage_folder / f"{variant_name}{file_ext}"

        if not variant_path.exists():
            return jsonify({
                'success': False,
                'error': f'Variant not found: {variant_name}{file_ext}'
            }), 404

        variant_path.unlink()
        logger.info(f"DAS variant removed: {variant_path}")

        return jsonify({
            'success': True,
            'message': 'DAS variant removed successfully'
        })
    except Exception as e:
        logger.error(f"DAS remove error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@das_bp.route('/api/mex/das/rename', methods=['POST'])
def das_rename_variant():
    """
    Rename a DAS variant file (e.g., add/remove button indicator)

    Body:
    {
      "stageCode": "GrOp",
      "oldName": "vanilla",
      "newName": "vanilla(B)"
    }
    """
    try:
        data = request.json
        stage_code = data.get('stageCode')
        old_name = data.get('oldName')
        new_name = data.get('newName')

        logger.info(f"DAS Rename Request - Stage: {stage_code}, Old: {old_name}, New: {new_name}")

        if not stage_code or not old_name or not new_name:
            return jsonify({
                'success': False,
                'error': 'Missing stageCode, oldName, or newName parameter'
            }), 400

        if stage_code not in DAS_STAGES:
            return jsonify({
                'success': False,
                'error': f'Unknown stage code: {stage_code}'
            }), 400

        # Pokemon Stadium uses .usd, others use .dat
        file_ext = '.usd' if stage_code == 'GrPs' else '.dat'
        project_files = get_project_files_dir()
        stage_folder = project_files / stage_code

        old_path = stage_folder / f"{old_name}{file_ext}"
        new_path = stage_folder / f"{new_name}{file_ext}"

        # Check if old file exists
        if not old_path.exists():
            return jsonify({
                'success': False,
                'error': f'Source file not found: {old_name}{file_ext}'
            }), 404

        # Check if new file already exists (prevent overwriting)
        if new_path.exists():
            return jsonify({
                'success': False,
                'error': f'Target file already exists: {new_name}{file_ext}'
            }), 409

        # Rename the file
        old_path.rename(new_path)
        logger.info(f"DAS variant renamed: {old_path} -> {new_path}")

        return jsonify({
            'success': True,
            'message': 'DAS variant renamed successfully',
            'oldName': old_name,
            'newName': new_name
        })
    except Exception as e:
        logger.error(f"DAS rename error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
