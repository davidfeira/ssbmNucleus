"""
Texture extras - for hue-shifted textures (Up-B fire, etc.).

Texture export/import via HSDRaw CLI, hue shifting/detection, and the
/api/mex/storage/textures/* routes.
"""

import logging
import subprocess
import shutil
from flask import request, jsonify

from extra_types import get_extra_type, get_storage_character
from core.config import get_subprocess_args

from . import extras_bp
from . import helpers
from .helpers import find_dat_file

logger = logging.getLogger(__name__)


def shift_texture_hue(input_png, output_png, hue_degrees):
    """Shift hue of texture, preserving alpha and luminance.

    Args:
        input_png: Path to input PNG file
        output_png: Path to save hue-shifted PNG
        hue_degrees: Hue shift amount in degrees (0-360)

    Returns:
        True if successful
    """
    from PIL import Image
    import colorsys

    img = Image.open(input_png).convert('RGBA')
    pixels = img.load()

    for y in range(img.height):
        for x in range(img.width):
            r, g, b, a = pixels[x, y]
            # Convert to HLS (hue, lightness, saturation)
            h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)
            # Shift hue
            h = (h + hue_degrees/360) % 1.0
            # Convert back to RGB
            r, g, b = colorsys.hls_to_rgb(h, l, s)
            pixels[x, y] = (int(r*255), int(g*255), int(b*255), a)

    img.save(output_png)
    logger.info(f"Hue shifted texture saved to {output_png}")
    return True


def export_texture(dat_path, node_path, tex_index, output_png):
    """Export texture from DAT using HSDRaw CLI.

    Args:
        dat_path: Path to the .dat file
        node_path: Path within DAT to JOBJ containing texture
        tex_index: Index of texture to export
        output_png: Path to save exported PNG

    Returns:
        True if successful, raises exception on failure
    """
    if not helpers.HSDRAW_VIEWER_PATH:
        raise RuntimeError("HSDRawViewer path not configured")

    cmd = [
        str(helpers.HSDRAW_VIEWER_PATH),
        '--texture', 'export',
        str(dat_path),
        node_path,
        str(tex_index),
        str(output_png)
    ]

    logger.info(f"Running texture export: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, **get_subprocess_args())

    if result.returncode != 0:
        logger.error(f"Texture export failed: {result.stderr}")
        raise RuntimeError(f"Texture export failed: {result.stderr}")

    logger.info(f"Texture export output: {result.stdout}")
    return True


def import_texture(dat_path, node_path, tex_index, input_png, output_dat):
    """Import texture into DAT using HSDRaw CLI.

    Args:
        dat_path: Path to the source .dat file
        node_path: Path within DAT to JOBJ containing texture
        tex_index: Index of texture to replace
        input_png: Path to the PNG file to import
        output_dat: Path to save the modified .dat file

    Returns:
        True if successful, raises exception on failure
    """
    if not helpers.HSDRAW_VIEWER_PATH:
        raise RuntimeError("HSDRawViewer path not configured")

    cmd = [
        str(helpers.HSDRAW_VIEWER_PATH),
        '--texture', 'import',
        str(dat_path),
        node_path,
        str(tex_index),
        str(input_png),
        str(output_dat)
    ]

    logger.info(f"Running texture import: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, **get_subprocess_args())

    if result.returncode != 0:
        logger.error(f"Texture import failed: {result.stderr}")
        raise RuntimeError(f"Texture import failed: {result.stderr}")

    logger.info(f"Texture import output: {result.stdout}")
    return True


def ensure_vanilla_texture(character, extra_type, type_config):
    """Ensure vanilla reference texture exists, exporting if necessary.

    Args:
        character: Character name
        extra_type: Extra type ID (e.g., 'upb_texture')
        type_config: Extra type configuration

    Returns:
        Path to vanilla texture PNG, or None on failure
    """
    # Get storage character
    storage_char = get_storage_character(character, extra_type)

    # Create textures directory
    textures_dir = helpers.STORAGE_PATH / storage_char / 'textures'
    textures_dir.mkdir(parents=True, exist_ok=True)

    vanilla_png = textures_dir / f"{extra_type}_vanilla.png"

    # If vanilla already exists, return it
    if vanilla_png.exists():
        logger.info(f"Using existing vanilla texture: {vanilla_png}")
        return vanilla_png

    # Export vanilla texture from MEX project
    try:
        files_dir = helpers.get_project_files_dir()
    except Exception as e:
        logger.error(f"Cannot get project files dir: {e}")
        return None

    target_file = type_config['target_file']
    dat_path = find_dat_file(files_dir, target_file)

    if not dat_path or not dat_path.exists():
        logger.error(f"Could not find {target_file} to export vanilla texture")
        return None

    try:
        node_path = type_config['texture_path']
        tex_index = type_config['texture_index']
        export_texture(dat_path, node_path, tex_index, vanilla_png)
        logger.info(f"Exported vanilla texture to {vanilla_png}")
        return vanilla_png
    except Exception as e:
        logger.error(f"Failed to export vanilla texture: {e}")
        return None


def detect_texture_hue(png_path):
    """Analyze a texture and detect its dominant hue.

    Args:
        png_path: Path to PNG file

    Returns:
        Dominant hue in degrees (0-360), or None if detection fails
    """
    from PIL import Image
    import colorsys

    try:
        img = Image.open(png_path).convert('RGBA')
        pixels = img.load()

        # Collect hues from non-transparent, saturated pixels
        hue_votes = {}

        for y in range(img.height):
            for x in range(img.width):
                r, g, b, a = pixels[x, y]
                if a < 32:  # Skip mostly transparent pixels
                    continue

                h, l, s = colorsys.rgb_to_hls(r/255, g/255, b/255)

                # Only count pixels with decent saturation and not too dark/light
                if s > 0.2 and 0.1 < l < 0.9:
                    # Round hue to nearest 5 degrees for binning
                    hue_deg = int(round(h * 360 / 5) * 5) % 360
                    hue_votes[hue_deg] = hue_votes.get(hue_deg, 0) + 1

        if not hue_votes:
            logger.warning(f"No saturated pixels found in {png_path}")
            return None

        # Return the most common hue
        dominant_hue = max(hue_votes, key=hue_votes.get)
        logger.info(f"Detected dominant hue: {dominant_hue} degrees from {png_path}")
        return dominant_hue

    except Exception as e:
        logger.error(f"Failed to detect hue from {png_path}: {e}")
        return None


@extras_bp.route('/api/mex/storage/textures/current/<character>/<extra_type>', methods=['GET'])
def get_current_texture_hue(character, extra_type):
    """Get the current hue of a texture extra by exporting and analyzing it.

    This is lazy-loaded - only called when user views the extra panel.
    """
    try:
        # Get extra type config
        type_config = get_extra_type(character, extra_type)
        if not type_config:
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" not defined for {character}'
            }), 400

        if type_config.get('type') != 'texture':
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" is not a texture type'
            }), 400

        # Find the target DAT file
        try:
            files_dir = helpers.get_project_files_dir()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        target_file = type_config['target_file']
        dat_path = find_dat_file(files_dir, target_file)

        if not dat_path or not dat_path.exists():
            return jsonify({
                'success': False,
                'error': f'Could not find {target_file} in MEX project'
            }), 404

        # Get storage character for cache directory
        storage_char = get_storage_character(character, extra_type)
        textures_dir = helpers.STORAGE_PATH / storage_char / 'textures'
        textures_dir.mkdir(parents=True, exist_ok=True)

        # Check if we have a cached export that's still valid
        current_png = textures_dir / f"{extra_type}_current.png"
        cache_valid = False

        if current_png.exists():
            # Check if DAT is newer than our cached export
            dat_mtime = dat_path.stat().st_mtime
            cache_mtime = current_png.stat().st_mtime
            cache_valid = cache_mtime > dat_mtime

        if not cache_valid:
            # Export current texture from DAT
            node_path = type_config['texture_path']
            tex_index = type_config['texture_index']

            try:
                export_texture(dat_path, node_path, tex_index, current_png)
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to export texture: {e}'
                }), 500

        # Detect the hue
        current_hue = detect_texture_hue(str(current_png))
        vanilla_hue = type_config.get('vanilla_hue', 30)

        return jsonify({
            'success': True,
            'hue': current_hue,
            'vanillaHue': vanilla_hue,
            'isVanilla': current_hue is not None and abs(current_hue - vanilla_hue) < 10
        })

    except Exception as e:
        logger.error(f"Get current texture hue error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@extras_bp.route('/api/mex/storage/textures/install', methods=['POST'])
def install_texture_extra():
    """Install a texture extra by applying hue shift and importing into DAT.

    For texture extras, the hue value is applied to the vanilla reference texture
    and the result is imported into the target DAT file.

    Request body:
    {
        "character": "Fox",
        "extraType": "upb_texture",
        "hue": 180  // Hue shift in degrees (0-360)
    }
    """
    try:
        data = request.json
        character = data.get('character')
        extra_type = data.get('extraType')
        hue = data.get('hue', 0)

        if not character or not extra_type:
            return jsonify({
                'success': False,
                'error': 'Missing character or extraType parameter'
            }), 400

        # Get extra type config
        type_config = get_extra_type(character, extra_type)
        if not type_config:
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" not defined for {character}'
            }), 400

        if type_config.get('type') != 'texture':
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" is not a texture type'
            }), 400

        # Ensure vanilla texture exists
        vanilla_png = ensure_vanilla_texture(character, extra_type, type_config)
        if not vanilla_png:
            return jsonify({
                'success': False,
                'error': 'Could not get vanilla reference texture'
            }), 500

        # Get storage character for temp files
        storage_char = get_storage_character(character, extra_type)
        textures_dir = helpers.STORAGE_PATH / storage_char / 'textures'

        # Create hue-shifted texture
        hue_shifted_png = textures_dir / f"{extra_type}_hue_{int(hue)}.png"

        # Calculate hue shift from vanilla
        vanilla_hue = type_config.get('vanilla_hue', 30)  # Default orange ~30 degrees
        hue_shift = hue - vanilla_hue

        if abs(hue_shift) < 1:
            # No shift needed, use vanilla directly
            hue_shifted_png = vanilla_png
            logger.info("No hue shift needed, using vanilla texture")
        else:
            shift_texture_hue(str(vanilla_png), str(hue_shifted_png), hue_shift)
            logger.info(f"Created hue-shifted texture: {hue_shifted_png}")

        # Find the target DAT file
        try:
            files_dir = helpers.get_project_files_dir()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        target_file = type_config['target_file']
        dat_path = find_dat_file(files_dir, target_file)

        if not dat_path or not dat_path.exists():
            return jsonify({
                'success': False,
                'error': f'Could not find {target_file} in MEX project'
            }), 404

        # Import the hue-shifted texture into the DAT
        node_path = type_config['texture_path']
        tex_index = type_config['texture_index']

        # Write to a temp file then replace original
        temp_dat = dat_path.parent / f"{dat_path.stem}_temp{dat_path.suffix}"

        try:
            import_texture(dat_path, node_path, tex_index, hue_shifted_png, temp_dat)
            # Replace original with modified
            shutil.move(str(temp_dat), str(dat_path))
            logger.info(f"[OK] Installed texture with hue {hue} to {target_file}")
        except Exception as e:
            if temp_dat.exists():
                temp_dat.unlink()
            raise

        return jsonify({
            'success': True,
            'hue': hue
        })

    except Exception as e:
        logger.error(f"Install texture extra error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@extras_bp.route('/api/mex/storage/textures/restore-vanilla', methods=['POST'])
def restore_vanilla_texture():
    """Restore vanilla texture.

    Request body:
    {
        "character": "Fox",
        "extraType": "upb_texture"
    }
    """
    try:
        data = request.json
        character = data.get('character')
        extra_type = data.get('extraType')

        if not character or not extra_type:
            return jsonify({
                'success': False,
                'error': 'Missing character or extraType parameter'
            }), 400

        # Get extra type config
        type_config = get_extra_type(character, extra_type)
        if not type_config:
            return jsonify({
                'success': False,
                'error': f'Extra type "{extra_type}" not defined for {character}'
            }), 400

        # Ensure vanilla texture exists
        vanilla_png = ensure_vanilla_texture(character, extra_type, type_config)
        if not vanilla_png:
            return jsonify({
                'success': False,
                'error': 'Could not get vanilla reference texture'
            }), 500

        # Find the target DAT file
        try:
            files_dir = helpers.get_project_files_dir()
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 400

        target_file = type_config['target_file']
        dat_path = find_dat_file(files_dir, target_file)

        if not dat_path or not dat_path.exists():
            return jsonify({
                'success': False,
                'error': f'Could not find {target_file} in MEX project'
            }), 404

        # Import the vanilla texture
        node_path = type_config['texture_path']
        tex_index = type_config['texture_index']
        temp_dat = dat_path.parent / f"{dat_path.stem}_temp{dat_path.suffix}"

        try:
            import_texture(dat_path, node_path, tex_index, vanilla_png, temp_dat)
            shutil.move(str(temp_dat), str(dat_path))
            logger.info(f"[OK] Restored vanilla texture for {character}/{extra_type}")
        except Exception as e:
            if temp_dat.exists():
                temp_dat.unlink()
            raise

        return jsonify({
            'success': True
        })

    except Exception as e:
        logger.error(f"Restore vanilla texture error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
