"""
Poses Blueprint - Pose management for CSP generation.

Handles saving, listing, deleting poses and batch CSP generation using poses.
"""

import os
import re
import json
import time
import shutil
import zipfile
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

from core.config import STORAGE_PATH, VANILLA_ASSETS_DIR, PROCESSOR_DIR
from core.constants import CHAR_PREFIXES
from generate_csp import generate_single_csp_internal, apply_character_specific_layers

logger = logging.getLogger(__name__)

poses_bp = Blueprint('poses', __name__)


@poses_bp.route('/api/mex/storage/poses/save', methods=['POST'])
def save_pose():
    """Save a pose scene YAML file for CSP generation.

    Saves to: vanilla_assets/custom_poses/{character}/{pose_name}.yml
    """
    try:
        data = request.json
        character = data.get('character')
        pose_name = data.get('poseName')
        scene_data = data.get('sceneData')

        if not character or not pose_name or not scene_data:
            return jsonify({
                'success': False,
                'error': 'Missing character, poseName, or sceneData parameter'
            }), 400

        # Sanitize pose name for filesystem
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', pose_name)
        safe_name = safe_name.strip()
        if not safe_name:
            return jsonify({
                'success': False,
                'error': 'Invalid pose name'
            }), 400

        # Create poses directory if needed
        poses_dir = VANILLA_ASSETS_DIR / "custom_poses" / character
        poses_dir.mkdir(parents=True, exist_ok=True)

        # Build YAML content
        yaml_content = f"""frame: {scene_data.get('frame', 0)}
cSPMode: {str(scene_data.get('cspMode', True)).lower()}
showGrid: {str(scene_data.get('showGrid', False)).lower()}
showBackdrop: {str(scene_data.get('showBackdrop', False)).lower()}
animSymbol: {scene_data.get('animSymbol', '')}
camera:
  x: {scene_data.get('camera', {}).get('x', 0)}
  y: {scene_data.get('camera', {}).get('y', 10)}
  z: {scene_data.get('camera', {}).get('z', -80)}
  scale: {scene_data.get('camera', {}).get('scale', 1)}
  fovRadians: {scene_data.get('camera', {}).get('fovRadians', 0.5236)}
  rotationXRadians: {scene_data.get('camera', {}).get('rotationXRadians', 0)}
  rotationYRadians: {scene_data.get('camera', {}).get('rotationYRadians', 0)}
"""
        # Add hidden nodes if present (these hide low-poly models etc)
        hidden_nodes = scene_data.get('hiddenNodes', [])
        if hidden_nodes:
            yaml_content += "hiddenNodes:\n"
            for node in hidden_nodes:
                yaml_content += f"- {node}\n"

        # Save pose file
        pose_path = poses_dir / f"{safe_name}.yml"
        with open(pose_path, 'w') as f:
            f.write(yaml_content)

        logger.info(f"[OK] Saved pose '{safe_name}' for {character} at {pose_path}")

        # Generate thumbnail using vanilla Nr costume
        thumbnail_path = None
        try:
            char_prefix = CHAR_PREFIXES.get(character)
            if char_prefix:
                costume_code = f"Pl{char_prefix}Nr"
                vanilla_dat = VANILLA_ASSETS_DIR / character / costume_code / f"{costume_code}.dat"
                # AJ file contains animations - needed for loading animation by symbol
                aj_file = VANILLA_ASSETS_DIR / character / f"Pl{char_prefix}AJ.dat"

                if vanilla_dat.exists():
                    logger.info(f"Generating pose thumbnail using {vanilla_dat}")
                    logger.info(f"AJ file: {aj_file} (exists: {aj_file.exists()})")

                    # Generate CSP with the pose scene file and AJ file for animations
                    csp_path = generate_single_csp_internal(
                        str(vanilla_dat),
                        character,
                        str(pose_path),  # Use pose YAML as scene file
                        str(aj_file) if aj_file.exists() else None,
                        1  # 1x scale for thumbnails
                    )

                    if csp_path and Path(csp_path).exists():
                        # Move CSP to thumbnail location
                        thumbnail_path = poses_dir / f"{safe_name}_thumb.png"
                        shutil.move(csp_path, thumbnail_path)
                        logger.info(f"[OK] Generated pose thumbnail at {thumbnail_path}")
                else:
                    logger.warning(f"Vanilla DAT not found: {vanilla_dat}")
        except Exception as thumb_err:
            logger.error(f"Failed to generate pose thumbnail: {thumb_err}", exc_info=True)
            # Continue without thumbnail - pose was still saved

        return jsonify({
            'success': True,
            'path': str(pose_path),
            'poseName': safe_name,
            'hasThumbnail': thumbnail_path is not None
        })
    except Exception as e:
        logger.error(f"Save pose error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@poses_bp.route('/api/mex/storage/poses/list/<character>', methods=['GET'])
def list_poses(character):
    """List all saved poses for a character."""
    try:
        poses_dir = VANILLA_ASSETS_DIR / "custom_poses" / character

        if not poses_dir.exists():
            return jsonify({
                'success': True,
                'poses': []
            })

        poses = []
        for pose_file in poses_dir.glob("*.yml"):
            thumb_path = poses_dir / f"{pose_file.stem}_thumb.png"
            poses.append({
                'name': pose_file.stem,
                'path': str(pose_file),
                'hasThumbnail': thumb_path.exists(),
                'thumbnailUrl': f"/storage/poses/{character}/{pose_file.stem}_thumb.png" if thumb_path.exists() else None
            })

        return jsonify({
            'success': True,
            'poses': sorted(poses, key=lambda p: p['name'])
        })
    except Exception as e:
        logger.error(f"List poses error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@poses_bp.route('/storage/poses/<character>/<filename>')
def serve_pose_thumbnail(character, filename):
    """Serve pose thumbnail images."""
    try:
        poses_dir = VANILLA_ASSETS_DIR / "custom_poses" / character
        full_path = poses_dir / filename
        logger.info(f"Serving pose thumbnail: {full_path}")
        logger.info(f"Directory exists: {poses_dir.exists()}, File exists: {full_path.exists()}")

        if not full_path.exists():
            logger.error(f"Thumbnail not found: {full_path}")
            return jsonify({'error': 'File not found'}), 404

        return send_file(str(full_path), mimetype='image/png')
    except Exception as e:
        logger.error(f"Error serving thumbnail: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@poses_bp.route('/api/mex/storage/poses/delete', methods=['POST'])
def delete_pose():
    """Delete a saved pose and its thumbnail."""
    try:
        data = request.json
        character = data.get('character')
        pose_name = data.get('poseName')

        if not character or not pose_name:
            return jsonify({
                'success': False,
                'error': 'Missing character or poseName parameter'
            }), 400

        poses_dir = VANILLA_ASSETS_DIR / "custom_poses" / character
        pose_path = poses_dir / f"{pose_name}.yml"
        thumb_path = poses_dir / f"{pose_name}_thumb.png"

        if not pose_path.exists():
            return jsonify({
                'success': False,
                'error': f'Pose {pose_name} not found'
            }), 404

        pose_path.unlink()
        if thumb_path.exists():
            thumb_path.unlink()
            logger.info(f"[OK] Deleted pose thumbnail '{pose_name}_thumb.png'")

        logger.info(f"[OK] Deleted pose '{pose_name}' for {character}")

        return jsonify({
            'success': True
        })
    except Exception as e:
        logger.error(f"Delete pose error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@poses_bp.route('/api/mex/storage/poses/batch-generate-csp', methods=['POST'])
def batch_generate_pose_csps():
    """Generate CSPs for multiple skins using a saved pose.

    Request body:
    {
        "character": "Fox",
        "poseName": "jump",
        "skinIds": ["skin-id-1", "skin-id-2"],
        "hdResolution": "2x"  // Optional, e.g., "2x", "3x", "4x"
    }
    """
    try:
        data = request.json
        character = data.get('character')
        pose_name = data.get('poseName')
        skin_ids = data.get('skinIds', [])
        hd_resolution = data.get('hdResolution')

        # Parse resolution to scale factor
        hd_scale = 1
        if hd_resolution:
            try:
                hd_scale = int(hd_resolution.replace('x', ''))
            except (ValueError, AttributeError):
                hd_scale = 1

        if not character or not pose_name or not skin_ids:
            return jsonify({
                'success': False,
                'error': 'Missing character, poseName, or skinIds parameter'
            }), 400

        # Get pose file path
        pose_path = VANILLA_ASSETS_DIR / "custom_poses" / character / f"{pose_name}.yml"
        if not pose_path.exists():
            return jsonify({
                'success': False,
                'error': f'Pose {pose_name} not found'
            }), 404

        # Get AJ file path
        char_prefix = CHAR_PREFIXES.get(character)
        if not char_prefix:
            return jsonify({
                'success': False,
                'error': f'Unknown character: {character}'
            }), 400

        aj_file = VANILLA_ASSETS_DIR / character / f"Pl{char_prefix}AJ.dat"

        # Load metadata to find skin ZIPs
        metadata_file = STORAGE_PATH / 'metadata.json'
        if not metadata_file.exists():
            return jsonify({
                'success': False,
                'error': 'Metadata file not found'
            }), 404

        with open(metadata_file, 'r') as f:
            metadata = json.load(f)

        char_data = metadata.get('characters', {}).get(character, {})
        skins = char_data.get('skins', [])

        # Build skin lookup by ID
        skin_lookup = {skin['id']: skin for skin in skins if skin.get('type') != 'folder'}

        results = []
        generated = 0
        failed = 0

        for skin_id in skin_ids:
            skin = skin_lookup.get(skin_id)
            if not skin:
                results.append({
                    'skinId': skin_id,
                    'success': False,
                    'error': 'Skin not found'
                })
                failed += 1
                continue

            zip_path = STORAGE_PATH / character / skin.get('filename', '')
            if not zip_path.exists():
                results.append({
                    'skinId': skin_id,
                    'success': False,
                    'error': 'ZIP file not found'
                })
                failed += 1
                continue

            # Extract DAT from ZIP to temp directory
            temp_dir = None
            try:
                temp_dir = tempfile.mkdtemp(prefix='csp_batch_')
                logger.info(f"Extracting {zip_path} to {temp_dir}")

                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(temp_dir)

                # Find DAT file in extraction
                dat_file = None
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.dat') and file.startswith('Pl'):
                            dat_file = Path(root) / file
                            break
                    if dat_file:
                        break

                if not dat_file or not dat_file.exists():
                    results.append({
                        'skinId': skin_id,
                        'success': False,
                        'error': 'No DAT file found in ZIP'
                    })
                    failed += 1
                    continue

                # When HD resolution specified, generate BOTH normal and HD versions
                scales_to_generate = [(hd_scale, True), (1, False)] if hd_scale > 1 else [(1, False)]
                existing_alts = skin.get('alternate_csps', [])
                alt_num = len(existing_alts) + 1
                skin_generated = False

                for gen_scale, is_hd in scales_to_generate:
                    logger.info(f"Generating CSP for {skin_id} using pose {pose_name} (scale={gen_scale}x)")

                    # Generate CSP
                    csp_path = generate_single_csp_internal(
                        str(dat_file),
                        character,
                        str(pose_path),
                        str(aj_file) if aj_file.exists() else None,
                        gen_scale
                    )

                    if csp_path and Path(csp_path).exists():
                        # Apply character-specific layers (Fox gun, Ness flip, etc.)
                        apply_character_specific_layers(csp_path, character, gen_scale)

                        # Determine alternate CSP filename
                        suffix = '_hd' if is_hd else ''
                        alt_filename = f"{skin_id}_csp_alt_{alt_num}{suffix}.png"
                        alt_path = STORAGE_PATH / character / alt_filename

                        # Move generated CSP to storage
                        shutil.move(csp_path, alt_path)
                        logger.info(f"[OK] Saved alternate CSP: {alt_path}")

                        # Update skin metadata with alternate CSP info
                        alt_entry = {
                            'id': f"alt_{int(time.time())}_{alt_num}{'_hd' if is_hd else ''}",
                            'filename': alt_filename,
                            'pose_name': pose_name,
                            'is_hd': is_hd,
                            'timestamp': datetime.now().isoformat()
                        }

                        # Find and update skin in metadata
                        for s in skins:
                            if s.get('id') == skin_id:
                                if 'alternate_csps' not in s:
                                    s['alternate_csps'] = []
                                s['alternate_csps'].append(alt_entry)
                                break

                        skin_generated = True
                    else:
                        logger.warning(f"Failed to generate {gen_scale}x CSP for {skin_id}")

                if skin_generated:
                    results.append({
                        'skinId': skin_id,
                        'success': True,
                        'altCspPath': f"/storage/{character}/{skin_id}_csp_alt_{alt_num}.png"
                    })
                    generated += 1
                else:
                    results.append({
                        'skinId': skin_id,
                        'success': False,
                        'error': 'CSP generation failed'
                    })
                    failed += 1

            except Exception as skin_err:
                logger.error(f"Error generating CSP for {skin_id}: {skin_err}", exc_info=True)
                results.append({
                    'skinId': skin_id,
                    'success': False,
                    'error': str(skin_err)
                })
                failed += 1
            finally:
                # Cleanup temp directory
                if temp_dir and os.path.exists(temp_dir):
                    try:
                        shutil.rmtree(temp_dir)
                        logger.info(f"Cleaned up temp dir: {temp_dir}")
                    except Exception as cleanup_err:
                        logger.warning(f"Failed to cleanup temp dir: {cleanup_err}")

        # Save updated metadata
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"[OK] Batch CSP generation complete: {generated} generated, {failed} failed")

        return jsonify({
            'success': True,
            'generated': generated,
            'failed': failed,
            'results': results
        })

    except Exception as e:
        logger.error(f"Batch generate CSP error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
