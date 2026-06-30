"""
Poses Blueprint - Pose management for CSP generation.

Handles saving, listing, deleting poses and batch CSP generation using poses.
"""

import os
import re
import json
import time
import shutil
import hashlib
import zipfile
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

from core.config import STORAGE_PATH, VANILLA_ASSETS_DIR, PROCESSOR_DIR
from core.constants import CHAR_PREFIXES
from core.costume_files import find_extracted_costume_archive
from core.metadata import load_metadata, save_metadata, get_char_data, custom_character_slug
from core.state import get_mex_manager, reload_mex_manager, mexcli_lock
from generate_csp import generate_single_csp_internal, apply_character_specific_layers

logger = logging.getLogger(__name__)

poses_bp = Blueprint('poses', __name__)


def _pose_character_key(character):
    """Directory key for a character's poses. The two custom-character pseudo
    keys ('custom_characters/<slug>/skins' and '.../costumes') share ONE
    folder so a pose made on a bundled costume serves the added skins too."""
    slug = custom_character_slug(character)
    return f'custom_characters/{slug}' if slug else character


def _poses_dir(character):
    return VANILLA_ASSETS_DIR / "custom_poses" / _pose_character_key(character)


def _character_aj_file(character):
    """AJ archive for pose rendering: vanilla assets for canonical characters,
    the fighter.zip animation archive (cached) for custom characters."""
    slug = custom_character_slug(character)
    if slug:
        from blueprints.viewer import extract_custom_character_aj
        return extract_custom_character_aj(slug)
    char_prefix = CHAR_PREFIXES.get(character)
    if not char_prefix:
        return None
    return VANILLA_ASSETS_DIR / character / f"Pl{char_prefix}AJ.dat"


# ----- "Scene poses": save the baked vanilla CSP pose + a custom camera ------
#
# Scene-mode characters (DK, Mewtwo, Ganon, ...) load a baked animation from
# their csp_data/<char>/scene.yml in the viewer. A user can pose with that
# baked animation (no AJ symbol) and just rotate/scrub. Such a pose stores
# `useSceneAnimation: true` (no animSymbol). At render time we merge the
# character's scene.yml (its settings + baked `animation:` block, kept
# byte-for-byte) with the pose's camera/frame/hiddenNodes into a temp
# `scene.yml`, which the existing scene-mode render path consumes.

def _character_scene_file(character):
    """The baked csp_data scene.yml for a character (canonical scene-mode
    char, or a custom char whose donor skeleton is scene-mode). None when the
    character has no baked scene — those must pose via an AJ symbol."""
    slug = custom_character_slug(character)
    if slug:
        from blueprints.viewer import custom_character_based_on
        name = custom_character_based_on(slug)
    else:
        name = character
    if not name:
        return None
    folder = name
    if name == 'Ice Climbers':
        folder = 'Ice Climbers (Popo)'
    if name == 'Mr. Game & Watch':
        folder = 'G&W'
    scene = PROCESSOR_DIR / 'csp_data' / folder / 'scene.yml'
    return scene if scene.exists() else None


def _parse_pose_yaml(text):
    """Parse the flat pose YAML this module writes (frame/camera/hiddenNodes/
    flags). Hand-rolled to avoid a pyyaml dependency."""
    out = {'camera': {}, 'hiddenNodes': []}
    in_camera = False
    in_hidden = False
    for raw in text.splitlines():
        if not raw.strip():
            continue
        if raw.startswith('- ') and in_hidden:
            try:
                out['hiddenNodes'].append(int(raw[2:].strip()))
            except ValueError:
                pass
            continue
        if not raw[0].isspace():
            in_camera = raw.startswith('camera:')
            in_hidden = raw.startswith('hiddenNodes:')
            if ':' in raw and not in_camera and not in_hidden:
                k, v = raw.split(':', 1)
                out[k.strip()] = v.strip()
            continue
        if in_camera and ':' in raw:
            k, v = raw.split(':', 1)
            out['camera'][k.strip()] = v.strip()
    return out


def _build_scene_pose_yaml(scene_path, pose):
    """Merge a character's baked scene.yml with a pose's camera/frame/
    hiddenNodes. Keeps the scene's `settings:` + `animation:` blocks intact;
    overrides only the camera fields the pose actually sets (preserving the
    scene camera's mode/clip planes, which scene-mode render needs)."""
    lines = scene_path.read_text(encoding='utf-8', errors='replace').splitlines()
    order, tops = [], {}
    for i, l in enumerate(lines):
        if l and not l[0].isspace() and not l.startswith('-'):
            key = l.split(':', 1)[0].strip()
            tops[key] = i
            order.append(key)

    def next_after(key, eof):
        idx = order.index(key)
        return tops[order[idx + 1]] if idx + 1 < len(order) else eof

    # Camera: start from the scene's camera block, override pose-set fields
    cam = pose.get('camera') or {}
    cs, ce = tops['camera'], next_after('camera', len(lines))
    new_cam = ['camera:']
    for cl in lines[cs + 1:ce]:
        k = cl.split(':', 1)[0].strip()
        new_cam.append(f'  {k}: {cam[k]}' if k in cam else cl)

    keep_key = 'settings' if 'settings' in tops else 'animation'
    keep = lines[tops[keep_key]:next_after('animation', len(lines))]

    header = [
        f"frame: {pose.get('frame', 0)}",
        f"cSPMode: {str(pose.get('cSPMode', pose.get('cspMode', True))).lower()}",
        f"showGrid: {str(pose.get('showGrid', False)).lower()}",
        f"showBackdrop: {str(pose.get('showBackdrop', False)).lower()}",
    ] + new_cam

    footer = []
    if pose.get('hiddenNodes'):
        footer.append('hiddenNodes:')
        footer += [f'- {n}' for n in pose['hiddenNodes']]

    return '\n'.join(header + keep + footer) + '\n'


def _render_pose_csp(dat_file, character, pose_path, aj_file, scale, no_shadow=False):
    """Render a CSP from a saved pose. Scene poses (`useSceneAnimation: true`)
    merge the character's baked scene.yml; symbol poses go straight through the
    animSymbol+AJ path. Returns the generated CSP path or None."""
    try:
        text = Path(pose_path).read_text(encoding='utf-8', errors='replace')
    except Exception:
        text = ''

    if re.search(r'(?m)^useSceneAnimation:\s*true\s*$', text):
        scene_src = _character_scene_file(character)
        if scene_src is None:
            logger.warning(f"Scene pose for {character} but no baked scene.yml found")
            return None
        tmp = tempfile.mkdtemp(prefix='scenepose_')
        try:
            scene_yml = Path(tmp) / 'scene.yml'   # name matters: triggers scene mode
            scene_yml.write_text(_build_scene_pose_yaml(scene_src, _parse_pose_yaml(text)),
                                 encoding='utf-8')
            return generate_single_csp_internal(
                str(dat_file), character, str(scene_yml), None, scale, no_shadow)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    return generate_single_csp_internal(
        str(dat_file), character, str(pose_path),
        str(aj_file) if aj_file and Path(aj_file).exists() else None, scale, no_shadow)


def _camera_scene_yaml(pose):
    """A viewer scene file carrying just a pose's camera/frame/hiddenNodes (no
    baked animation). For 'start from a symbol pose': SceneSettings restores the
    camera + frame on load (it ignores the unrelated keys), and the viewer loads
    the animation separately by symbol. farClip/nearClip are spelled out because
    scene-mode load replaces the whole camera, so missing planes => 0 => broken."""
    cam = pose.get('camera') or {}
    lines = [
        f"frame: {pose.get('frame', 0)}",
        f"cSPMode: {str(pose.get('cSPMode', 'true')).lower()}",
        f"showGrid: {str(pose.get('showGrid', 'false')).lower()}",
        f"showBackdrop: {str(pose.get('showBackdrop', 'false')).lower()}",
        "camera:",
        f"  x: {cam.get('x', 0)}",
        f"  y: {cam.get('y', 10)}",
        f"  z: {cam.get('z', -80)}",
        f"  scale: {cam.get('scale', 1)}",
        f"  fovRadians: {cam.get('fovRadians', 0.5236)}",
        f"  rotationXRadians: {cam.get('rotationXRadians', 0)}",
        f"  rotationYRadians: {cam.get('rotationYRadians', 0)}",
        "  farClipPlane: 100000",
        "  nearClipPlane: 10",
    ]
    if pose.get('hiddenNodes'):
        lines.append('hiddenNodes:')
        lines += [f'- {n}' for n in pose['hiddenNodes']]
    return '\n'.join(lines) + '\n'


def _custom_base_costume_dat(slug, temp_dir):
    """Extract a custom character's first bundled costume DAT (for pose
    thumbnails). Prefers the materialized costumes/<stem>.zip, falls back to
    the inner costume zip of fighter.zip."""
    char_dir = STORAGE_PATH / 'custom_characters' / slug
    try:
        with open(char_dir / 'fighter.json', 'r', encoding='utf-8') as f:
            costumes = json.load(f).get('costumes', [])
    except Exception:
        return None

    def _dat_from_zip(zf):
        for n in zf.namelist():
            if n.lower().endswith(('.dat', '.usd')) and not n.endswith('/'):
                out = Path(temp_dir) / Path(n).name
                out.write_bytes(zf.read(n))
                return out
        return None

    for costume in costumes:
        stem = Path((costume.get('file') or {}).get('fileName') or '').stem
        if not stem:
            continue
        zip_path = char_dir / 'costumes' / f'{stem}.zip'
        if zip_path.exists():
            with zipfile.ZipFile(zip_path) as zf:
                dat = _dat_from_zip(zf)
                if dat:
                    return dat
        fighter_zip = char_dir / 'fighter.zip'
        if fighter_zip.exists():
            with zipfile.ZipFile(fighter_zip) as outer:
                inner_name = next((n for n in outer.namelist()
                                   if n.split('/')[-1].lower() == f'{stem}.zip'.lower()), None)
                if inner_name:
                    import io
                    with zipfile.ZipFile(io.BytesIO(outer.read(inner_name))) as zf:
                        dat = _dat_from_zip(zf)
                        if dat:
                            return dat
    return None


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

        # A pose needs a base animation. Two valid sources:
        #  1. An AJ animation the user picked from the list (animSymbol).
        #  2. The character's baked scene animation (scene-mode chars like DK)
        #     — used as-is when no symbol was picked but a scene.yml exists.
        # Anything else (e.g. a custom char sitting in bind pose) would render
        # as a T-pose, so it is rejected.
        anim_symbol = scene_data.get('animSymbol')
        has_symbol = bool(anim_symbol) and str(anim_symbol).strip().lower() not in ('none', 'null')
        use_scene = not has_symbol and _character_scene_file(character) is not None
        if not has_symbol and not use_scene:
            return jsonify({
                'success': False,
                'error': 'No animation selected. Pick an animation from the '
                         'list (and scrub to a frame) before saving — '
                         'otherwise the pose renders as a T-pose.'
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
        poses_dir = _poses_dir(character)
        poses_dir.mkdir(parents=True, exist_ok=True)

        # Build YAML content. Symbol poses carry `animSymbol:`; scene poses
        # carry `useSceneAnimation: true` (the baked animation is merged in
        # from the character's scene.yml at render time).
        anim_line = f"animSymbol: {anim_symbol}" if has_symbol else "useSceneAnimation: true"
        yaml_content = f"""frame: {scene_data.get('frame', 0)}
cSPMode: {str(scene_data.get('cspMode', True)).lower()}
showGrid: {str(scene_data.get('showGrid', False)).lower()}
showBackdrop: {str(scene_data.get('showBackdrop', False)).lower()}
{anim_line}
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

        # Generate thumbnail using the character's base costume
        thumbnail_path = None
        temp_dir = None
        try:
            slug = custom_character_slug(character)
            base_dat = None
            aj_file = None
            if slug:
                temp_dir = tempfile.mkdtemp(prefix='pose_thumb_')
                base_dat = _custom_base_costume_dat(slug, temp_dir)
                aj_file = _character_aj_file(character)
            else:
                char_prefix = CHAR_PREFIXES.get(character)
                if char_prefix:
                    costume_code = f"Pl{char_prefix}Nr"
                    base_dat = VANILLA_ASSETS_DIR / character / costume_code / f"{costume_code}.dat"
                    # AJ file contains animations - needed for loading animation by symbol
                    aj_file = VANILLA_ASSETS_DIR / character / f"Pl{char_prefix}AJ.dat"

            if base_dat and Path(base_dat).exists():
                logger.info(f"Generating pose thumbnail using {base_dat}")
                logger.info(f"AJ file: {aj_file} (exists: {aj_file.exists() if aj_file else False})")

                # Generate CSP from the pose (symbol pose or baked scene pose)
                csp_path = _render_pose_csp(
                    str(base_dat), character, pose_path, aj_file, 1)

                if csp_path and Path(csp_path).exists():
                    # Move CSP to thumbnail location
                    thumbnail_path = poses_dir / f"{safe_name}_thumb.png"
                    shutil.move(csp_path, thumbnail_path)
                    logger.info(f"[OK] Generated pose thumbnail at {thumbnail_path}")
            else:
                logger.warning(f"Base DAT not found for {character}")
        except Exception as thumb_err:
            logger.error(f"Failed to generate pose thumbnail: {thumb_err}", exc_info=True)
            # Continue without thumbnail - pose was still saved
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

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


@poses_bp.route('/api/mex/storage/poses/list/<path:character>', methods=['GET'])
def list_poses(character):
    """List all saved poses for a character."""
    try:
        poses_dir = _poses_dir(character)

        if not poses_dir.exists():
            return jsonify({
                'success': True,
                'poses': []
            })

        pose_key = _pose_character_key(character)
        poses = []
        for pose_file in poses_dir.glob("*.yml"):
            # transient viewer scene files written by the scene-file endpoint
            if pose_file.stem.endswith('__viewer'):
                continue
            thumb_path = poses_dir / f"{pose_file.stem}_thumb.png"
            poses.append({
                'name': pose_file.stem,
                'path': str(pose_file),
                'hasThumbnail': thumb_path.exists(),
                'thumbnailUrl': f"/storage/poses/{pose_key}/{pose_file.stem}_thumb.png" if thumb_path.exists() else None
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


@poses_bp.route('/api/mex/storage/poses/scene-file/<path:character>/<pose_name>', methods=['GET'])
def get_pose_scene_file(character, pose_name):
    """Return a viewer-ready scene file for 'start from existing pose'.

    The embedded viewer restores camera/frame/hiddenNodes from any scene file
    on load. Scene poses also restore their baked animation (merged scene.yml);
    symbol poses return the camera scene file plus the animSymbol for the client
    to load into the viewer after it connects.
    """
    try:
        pose_path = _poses_dir(character) / f"{pose_name}.yml"
        if not pose_path.exists():
            return jsonify({'success': False, 'error': f'Pose {pose_name} not found'}), 404

        text = pose_path.read_text(encoding='utf-8', errors='replace')
        parsed = _parse_pose_yaml(text)
        is_scene = bool(re.search(r'(?m)^useSceneAnimation:\s*true\s*$', text))
        out_path = _poses_dir(character) / f"{pose_name}__viewer.yml"

        if is_scene:
            scene_src = _character_scene_file(character)
            if scene_src is None:
                return jsonify({'success': False,
                                'error': 'No baked scene for this character'}), 404
            out_path.write_text(_build_scene_pose_yaml(scene_src, parsed), encoding='utf-8')
            anim_symbol = None
        else:
            out_path.write_text(_camera_scene_yaml(parsed), encoding='utf-8')
            anim_symbol = parsed.get('animSymbol')

        try:
            frame = int(float(parsed.get('frame', 0)))
        except (TypeError, ValueError):
            frame = 0

        return jsonify({'success': True, 'sceneFile': str(out_path),
                        'animSymbol': anim_symbol, 'frame': frame})
    except Exception as e:
        logger.error(f"Get pose scene-file error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@poses_bp.route('/storage/poses/<path:character>/<filename>')
def serve_pose_thumbnail(character, filename):
    """Serve pose thumbnail images."""
    try:
        poses_dir = _poses_dir(character)
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

        poses_dir = _poses_dir(character)
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


def _generate_pose_csps_for_skin(character, skin, pose_name, pose_path, aj_file, hd_scale):
    """Render alternate CSPs for one vault skin using a pose.

    Generates the SD portrait (and an HD one when hd_scale > 1) and appends
    alternate_csps entries to `skin` IN PLACE — the caller must
    save_metadata(). Returns a per-skin result dict matching the
    batch-generate-csp response shape.
    """
    skin_id = skin.get('id')
    zip_path = STORAGE_PATH / character / skin.get('filename', '')
    if not zip_path.exists():
        return {'skinId': skin_id, 'success': False, 'error': 'ZIP file not found'}

    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(prefix='csp_batch_')
        logger.info(f"Extracting {zip_path} to {temp_dir}")

        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(temp_dir)

        dat_file = find_extracted_costume_archive(Path(temp_dir))

        if not dat_file or not dat_file.exists():
            return {'skinId': skin_id, 'success': False,
                    'error': 'No costume archive found in ZIP'}

        # When HD resolution specified, generate BOTH normal and HD versions
        scales_to_generate = [(hd_scale, True), (1, False)] if hd_scale > 1 else [(1, False)]
        alt_num = len(skin.get('alternate_csps', [])) + 1
        skin_generated = False

        for gen_scale, is_hd in scales_to_generate:
            logger.info(f"Generating CSP for {skin_id} using pose {pose_name} (scale={gen_scale}x)")

            csp_path = _render_pose_csp(
                str(dat_file), character, pose_path, aj_file, gen_scale)

            if csp_path and Path(csp_path).exists():
                # Apply character-specific layers (Fox gun, Ness flip, etc.)
                apply_character_specific_layers(csp_path, character, gen_scale)

                suffix = '_hd' if is_hd else ''
                alt_filename = f"{skin_id}_csp_alt_{alt_num}{suffix}.png"
                alt_path = STORAGE_PATH / character / alt_filename

                shutil.move(csp_path, alt_path)
                logger.info(f"[OK] Saved alternate CSP: {alt_path}")

                skin.setdefault('alternate_csps', []).append({
                    'id': f"alt_{int(time.time())}_{alt_num}{'_hd' if is_hd else ''}",
                    'filename': alt_filename,
                    'pose_name': pose_name,
                    'is_hd': is_hd,
                    'timestamp': datetime.now().isoformat()
                })

                skin_generated = True
            else:
                logger.warning(f"Failed to generate {gen_scale}x CSP for {skin_id}")

        if skin_generated:
            return {'skinId': skin_id, 'success': True,
                    'altCspPath': f"/storage/{character}/{skin_id}_csp_alt_{alt_num}.png"}
        return {'skinId': skin_id, 'success': False, 'error': 'CSP generation failed'}

    except Exception as skin_err:
        logger.error(f"Error generating CSP for {skin_id}: {skin_err}", exc_info=True)
        return {'skinId': skin_id, 'success': False, 'error': str(skin_err)}
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temp dir: {temp_dir}")
            except Exception as cleanup_err:
                logger.warning(f"Failed to cleanup temp dir: {cleanup_err}")


@poses_bp.route('/api/mex/storage/poses/batch-generate-csp', methods=['POST'])
def batch_generate_pose_csps():
    """Generate CSPs for multiple skins using a saved pose.

    Request body:
    {
        "character": "Fox",
        "poseName": "jump",
        "skinIds": ["skin-id-1", "skin-id-2"],
        "hdResolution": "4x"  // Optional; defaults to 4x. "1x" skips the HD pass.
    }
    """
    try:
        data = request.json
        character = data.get('character')
        pose_name = data.get('poseName')
        skin_ids = data.get('skinIds', [])
        hd_resolution = data.get('hdResolution')

        # Parse resolution to scale factor; HD at 4x is the default
        hd_scale = 4
        if hd_resolution is not None:
            try:
                hd_scale = int(str(hd_resolution).lower().replace('x', '').strip())
            except ValueError:
                hd_scale = 4

        if not character or not pose_name or not skin_ids:
            return jsonify({
                'success': False,
                'error': 'Missing character, poseName, or skinIds parameter'
            }), 400

        # Get pose file path
        pose_path = _poses_dir(character) / f"{pose_name}.yml"
        if not pose_path.exists():
            return jsonify({
                'success': False,
                'error': f'Pose {pose_name} not found'
            }), 404

        # Get AJ file path (vanilla assets, or the custom character's archive)
        aj_file = _character_aj_file(character)
        if aj_file is None and not custom_character_slug(character):
            return jsonify({
                'success': False,
                'error': f'Unknown character: {character}'
            }), 400

        # Load metadata to find skin ZIPs
        metadata = load_metadata()
        if metadata is None:
            return jsonify({
                'success': False,
                'error': 'Metadata file not found'
            }), 404

        char_data = get_char_data(metadata, character) or {}
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

            result = _generate_pose_csps_for_skin(
                character, skin, pose_name, pose_path, aj_file, hd_scale)
            results.append(result)
            if result.get('success'):
                generated += 1
            else:
                failed += 1

        # Save updated metadata
        save_metadata(metadata)

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


# ============= Apply a pose to the open project's installed costumes =======
#
# "Pose" button on the install page (CharacterMode): replaces the portraits
# of a fighter's in-ISO costumes with renders of one pose. Vault skins that
# already have that pose as an alternate CSP are reused; missing ones are
# rendered on the fly (and saved to the vault as alternates).
#
# Flow (frontend drives it for per-costume progress):
#   1. POST project-costume-map  -> match each in-ISO costume to a vault skin
#   2. POST apply-to-costume     -> per costume: ensure pose render, overwrite
#                                   the project's CSP asset PNG
#   3. POST apply-finish         -> recompile-csps (regenerates the .tex
#                                   files the ISO export actually reads)

# Vanilla CSP texture size (must match storage_costumes.CSP_SD_SIZE)
_CSP_SD_SIZE = (136, 188)

# Sentinel pose name: restore each costume's ORIGINAL portrait (the vault
# skin's main CSP / the shipped vanilla CSP) instead of a pose render
ORIGINAL_POSE_NAME = '__original__'


def _vault_character_keys(metadata, fighter_name, explicit_character=None):
    """Vault skin-container keys to search for a MEX fighter's costumes.

    Canonical fighters map to their own key; custom characters expose two
    pseudo keys (bundled costumes + added skins). `explicit_character` is
    whatever key the frontend already resolved (canonical name or either
    pseudo key).
    """
    if explicit_character:
        slug = custom_character_slug(explicit_character)
        if slug:
            return [f'custom_characters/{slug}/costumes',
                    f'custom_characters/{slug}/skins']
        return [explicit_character]
    if fighter_name in metadata.get('characters', {}):
        return [fighter_name]
    for entry in metadata.get('custom_characters', []):
        if (entry.get('name') or '').lower() == fighter_name.lower():
            slug = entry.get('slug')
            if slug:
                return [f'custom_characters/{slug}/costumes',
                        f'custom_characters/{slug}/skins']
    return []


def _build_skin_index(metadata, char_keys):
    """[(char_key, skin, zip path, dat stems)] for every existing vault skin
    zip under the given keys. Stems come from the zip namelist only (cheap)."""
    index = []
    for key in char_keys:
        char_data = get_char_data(metadata, key) or {}
        for skin in char_data.get('skins', []):
            if skin.get('type') == 'folder':
                continue
            zip_path = STORAGE_PATH / key / skin.get('filename', '')
            if not skin.get('filename') or not zip_path.exists():
                continue
            try:
                with zipfile.ZipFile(zip_path) as zf:
                    stems = {Path(n).stem.lower() for n in zf.namelist()
                             if n.lower().endswith(('.dat', '.usd')) and not n.endswith('/')}
            except Exception as e:
                logger.warning(f"Unreadable skin zip {zip_path}: {e}")
                continue
            if stems:
                index.append({'key': key, 'skin': skin, 'zip': zip_path, 'stems': stems})
    return index


def _match_costume_to_skin(file_name, skin_index, project_dir):
    """Match one in-ISO costume DAT to a vault skin.

    Primary match is the DAT stem (imports keep the vault DAT's name, with a
    _NNN suffix when a same-named file already existed in the project).
    Recolors often share a stem (several skins all carry PlFxNr.dat), so
    stem collisions are disambiguated by comparing the project DAT's bytes
    against each candidate zip's DAT — imports copy the file verbatim.
    """
    # Region-resolved names have no extension and a trailing dot (Red
    # Falcon is 'PlCaRe.' — the game appends usd/dat by region)
    stem = Path(file_name).stem.lower().rstrip('.')
    base = re.sub(r'_\d+$', '', stem)
    candidates = [e for e in skin_index if stem in e['stems'] or base in e['stems']]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    dat_path = project_dir / 'files' / file_name
    if dat_path.exists():
        want = hashlib.sha1(dat_path.read_bytes()).hexdigest()
        for entry in candidates:
            try:
                with zipfile.ZipFile(entry['zip']) as zf:
                    for n in zf.namelist():
                        if not n.lower().endswith(('.dat', '.usd')) or n.endswith('/'):
                            continue
                        if Path(n).stem.lower() in (stem, base):
                            if hashlib.sha1(zf.read(n)).hexdigest() == want:
                                return entry
            except Exception:
                continue
    # Ambiguous (or project DAT missing): fall back to the first stem match
    return candidates[0]


@poses_bp.route('/api/mex/storage/poses/project-costume-map', methods=['POST'])
def project_costume_map():
    """Match a fighter's in-ISO costumes to vault skins.

    Body: { "fighter": "Fox", "character": "Fox" (optional vault key) }
    Returns per-costume entries with the matched skin id + vault key and the
    costume's CSP asset path (needed by apply-to-costume).
    """
    try:
        data = request.json or {}
        fighter = (data.get('fighter') or '').strip()
        if not fighter:
            return jsonify({'success': False, 'error': 'Missing fighter parameter'}), 400

        mex = get_mex_manager()
        if mex is None:
            return jsonify({'success': False, 'error': 'No MEX project loaded'}), 400

        result = mex._run_command('get-costumes', str(mex.project_path), fighter)
        if not result.get('success', True) and 'costumes' not in result:
            return jsonify({'success': False,
                            'error': result.get('error', 'Failed to list costumes')}), 500

        metadata = load_metadata() or {}
        char_keys = _vault_character_keys(metadata, fighter, data.get('character'))
        skin_index = _build_skin_index(metadata, char_keys)
        project_dir = mex.project_path.parent

        # Vanilla costumes are not vault skins — they fall back to the
        # shipped vanilla assets (utility/assets/vanilla/<char>/<code>/)
        explicit = data.get('character')
        vanilla_char = None if custom_character_slug(explicit or '') else (explicit or fighter)

        costumes = []
        for costume in result.get('costumes', []):
            file_name = costume.get('fileName') or ''
            match = _match_costume_to_skin(file_name, skin_index, project_dir)
            vanilla_code = None
            if match is None and vanilla_char:
                # trailing dot = region-resolved name (Red Falcon 'PlCaRe.')
                stem = Path(file_name).stem.rstrip('.')
                for code in (stem, re.sub(r'_\d+$', '', stem)):
                    cdir = VANILLA_ASSETS_DIR / vanilla_char / code
                    # csp.png alone still counts: PlCaRe (Red Falcon, the
                    # one .usd costume) ships without its model — renders
                    # fall back to the project's installed file
                    if ((cdir / f'{code}.dat').exists()
                            or (cdir / f'{code}.usd').exists()
                            or (cdir / 'csp.png').exists()):
                        vanilla_code = code
                        break
            costumes.append({
                'index': costume.get('index'),
                'name': costume.get('name'),
                'fileName': file_name,
                'cspAsset': costume.get('csp'),
                'skinId': match['skin'].get('id') if match else None,
                'skinCharacter': match['key'] if match else (vanilla_char if vanilla_code else None),
                'vanillaCode': vanilla_code
            })

        return jsonify({'success': True, 'fighter': fighter, 'costumes': costumes})
    except Exception as e:
        logger.error(f"Project costume map error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@poses_bp.route('/api/mex/storage/poses/apply-to-costume', methods=['POST'])
def apply_pose_to_costume():
    """Apply a pose render to ONE installed costume's project CSP asset.

    Body: { "character": <vault key>, "skinId" OR "vanillaCode",
            "poseName", "cspAsset" }
    Vault skins reuse their existing alternate CSP for the pose when present,
    otherwise it is rendered now (saving SD+HD alternates to the vault).
    Vanilla costumes render from the shipped vanilla DAT, cached under the
    pose's renders/ directory. The project PNG is overwritten in place; call
    apply-finish afterwards to recompile the .tex files.
    """
    try:
        from io import BytesIO
        from PIL import Image

        data = request.json or {}
        character = data.get('character')
        skin_id = data.get('skinId')
        vanilla_code = data.get('vanillaCode')
        pose_name = data.get('poseName')
        csp_asset = data.get('cspAsset')
        file_name = data.get('fileName')  # installed costume file (model fallback)

        if not character or not pose_name or not (skin_id or vanilla_code):
            return jsonify({'success': False,
                            'error': 'Missing character, skinId/vanillaCode, or poseName parameter'}), 400
        if not csp_asset:
            # Costume has no portrait asset to replace (never happens for
            # imported costumes) — report as skipped, not an error.
            return jsonify({'success': True, 'status': 'no_csp_asset'})

        mex = get_mex_manager()
        if mex is None:
            return jsonify({'success': False, 'error': 'No MEX project loaded'}), 400

        # The asset path comes from project-costume-map (MexCLI output); keep
        # writes pinned inside the project's assets directory anyway.
        assets_dir = (mex.project_path.parent / 'assets').resolve()
        target = (assets_dir / (csp_asset.replace('\\', '/') + '.png')).resolve()
        if not str(target).startswith(str(assets_dir)):
            return jsonify({'success': False, 'error': 'Invalid CSP asset path'}), 403

        pose_path = _poses_dir(character) / f"{pose_name}.yml"
        generated = False
        restore_original = pose_name == ORIGINAL_POSE_NAME

        if vanilla_code:
            # Vanilla costume: render from the shipped vanilla DAT, cached in
            # the pose's renders/ directory so re-applies are instant
            safe_code = re.sub(r'[^A-Za-z0-9_]', '', vanilla_code)
            costume_dir = VANILLA_ASSETS_DIR / character / safe_code
            if restore_original:
                # the shipped vanilla portrait IS the original
                src_path = costume_dir / 'csp.png'
                if not src_path.exists():
                    return jsonify({'success': False,
                                    'error': f'No vanilla portrait for {vanilla_code}'}), 404
            else:
                dat_path = costume_dir / f'{safe_code}.dat'
                if not dat_path.exists():
                    dat_path = costume_dir / f'{safe_code}.usd'
                if not dat_path.exists() and file_name:
                    # PlCaRe (Red Falcon) has no model in the shipped vanilla
                    # assets — render from the project's own installed file.
                    # Its fileName is region-resolved ('PlCaRe.', no
                    # extension): the US ISO ships PlCaRe.usd, so probe that
                    # first, then .dat.
                    files_dir = (mex.project_path.parent / 'files').resolve()
                    fname = file_name.replace('\\', '/').rstrip('.')
                    names = [fname] if Path(fname).suffix else [f'{fname}.usd', f'{fname}.dat']
                    for name in names:
                        candidate = (files_dir / name).resolve()
                        if str(candidate).startswith(str(files_dir)) and candidate.exists():
                            dat_path = candidate
                            break
                if not dat_path.exists():
                    return jsonify({'success': False,
                                    'error': f'Vanilla costume not found: {vanilla_code}'}), 404

                renders_dir = _poses_dir(character) / 'renders'
                src_path = renders_dir / f'{safe_code}__{pose_name}.png'
                if not src_path.exists():
                    if not pose_path.exists():
                        return jsonify({'success': False,
                                        'error': f'Pose {pose_name} not found'}), 404
                    aj_file = _character_aj_file(character)
                    csp_path = _render_pose_csp(
                        str(dat_path), character, pose_path, aj_file, 1)
                    if not csp_path or not Path(csp_path).exists():
                        return jsonify({'success': False,
                                        'error': 'CSP generation failed'}), 500
                    apply_character_specific_layers(csp_path, character, 1)
                    renders_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(csp_path, src_path)
                    generated = True
        else:
            metadata = load_metadata()
            if metadata is None:
                return jsonify({'success': False, 'error': 'Metadata file not found'}), 404
            char_data = get_char_data(metadata, character) or {}
            skin = next((s for s in char_data.get('skins', [])
                         if s.get('type') != 'folder' and s.get('id') == skin_id), None)
            if skin is None:
                return jsonify({'success': False, 'error': f'Skin not found: {skin_id}'}), 404

            if restore_original:
                # the vault skin's main portrait is the original; skins
                # without one are skipped (nothing to restore to)
                src_path = STORAGE_PATH / character / f'{skin_id}_csp.png'
                if not src_path.exists():
                    return jsonify({'success': True, 'status': 'no_csp_asset'})
            else:
                def _find_pose_alt(s):
                    alts = [a for a in s.get('alternate_csps', [])
                            if a.get('pose_name') == pose_name and not a.get('is_hd')]
                    return alts[-1] if alts else None

                # Reuse an existing render of this pose, or generate one now
                alt = _find_pose_alt(skin)
                if alt is None:
                    if not pose_path.exists():
                        return jsonify({'success': False,
                                        'error': f'Pose {pose_name} not found'}), 404
                    aj_file = _character_aj_file(character)
                    gen_result = _generate_pose_csps_for_skin(
                        character, skin, pose_name, pose_path, aj_file, 4)
                    save_metadata(metadata)
                    if not gen_result.get('success'):
                        return jsonify({'success': False,
                                        'error': gen_result.get('error', 'CSP generation failed')}), 500
                    generated = True
                    alt = _find_pose_alt(skin)
                    if alt is None:
                        return jsonify({'success': False,
                                        'error': 'Generated CSP not found in metadata'}), 500

                src_path = STORAGE_PATH / character / alt.get('filename', '')
                if not src_path.exists():
                    return jsonify({'success': False,
                                    'error': f"Alternate CSP file missing: {alt.get('filename')}"}), 404

        # Normalize to the vanilla portrait size (generator output already is)
        with Image.open(src_path) as src:
            img = src.convert('RGBA')
        if img.size[0] > _CSP_SD_SIZE[0] or img.size[1] > _CSP_SD_SIZE[1]:
            img.thumbnail(_CSP_SD_SIZE, Image.LANCZOS)
        buf = BytesIO()
        img.save(buf, format='PNG')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(buf.getvalue())

        logger.info(f"[OK] Applied pose '{pose_name}' to project CSP {target.name} "
                    f"({'vanilla ' + vanilla_code if vanilla_code else 'skin ' + str(skin_id)}"
                    f"{', generated' if generated else ''})")
        return jsonify({'success': True,
                        'status': 'generated' if generated else 'applied',
                        'generated': generated})
    except Exception as e:
        logger.error(f"Apply pose to costume error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@poses_bp.route('/api/mex/storage/poses/apply-finish', methods=['POST'])
def apply_pose_finish():
    """Recompile project CSP textures after apply-to-costume calls.

    The ISO export reads the pre-encoded .tex next to each CSP PNG, so the
    overwritten PNGs must be recompiled before they show up in a build.
    """
    try:
        mex = get_mex_manager()
        if mex is None:
            return jsonify({'success': False, 'error': 'No MEX project loaded'}), 400

        with mexcli_lock:
            result = mex._run_command('recompile-csps', str(mex.project_path))
            time.sleep(0.15)
            reload_mex_manager()

        if not result.get('success'):
            return jsonify({'success': False,
                            'error': result.get('error', 'Recompile failed')}), 500
        return jsonify({'success': True,
                        'recompiled': result.get('recompiledCount', 0)})
    except Exception as e:
        logger.error(f"Apply pose finish error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
