"""
Custom Characters Blueprint - Manage m-ex custom fighters in the vault.

Custom characters are entirely new fighters added via m-ex. They are
imported from MexManager-exported ZIP packages or scanned from an ISO.
Each fighter is stored as:

    storage/custom_characters/<slug>/
        fighter.zip     (original ZIP preserved for re-export)
        fighter.json    (extracted metadata)
        css_icon.png    (CSS icon for grid display)
        csp_0.png ...   (per-costume CSP portraits)

Metadata is tracked under metadata.json["custom_characters"] (list of objects).
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
import logging
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

from core.config import STORAGE_PATH, MEXCLI_PATH, PROJECT_ROOT, get_subprocess_args
from core.state import get_current_project_path, reload_mex_manager

logger = logging.getLogger(__name__)

custom_characters_bp = Blueprint('custom_characters', __name__)

CUSTOM_CHARACTERS_PATH = STORAGE_PATH / 'custom_characters'
CUSTOM_CHARACTERS_PATH.mkdir(parents=True, exist_ok=True)

METADATA_FILE = STORAGE_PATH / 'metadata.json'

VANILLA_FIGHTER_NAMES = {
    'C. Falcon', 'DK', 'Fox', 'Mr. Game & Watch', 'Kirby', 'Bowser',
    'Link', 'Luigi', 'Mario', 'Marth', 'Mewtwo', 'Ness', 'Peach',
    'Pikachu', 'Ice Climbers', 'Jigglypuff', 'Samus', 'Yoshi', 'Zelda',
    'Sheik', 'Falco', 'Young Link', 'Dr. Mario', 'Roy', 'Pichu',
    'Ganondorf', 'Master Hand', 'Wireframe Male', 'Wireframe Female',
    'Giga Bowser', 'Crazy Hand', 'Sandbag', 'Nana',
    'NONE', 'Popo',
}


def _sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


def _make_slug(name):
    slug = _sanitize_filename(name).lower().replace(' ', '-')
    slug = re.sub(r'-+', '-', slug).strip('-')
    if not slug:
        slug = 'custom-character'
    return slug


def _dedupe_slug(slug):
    if not (CUSTOM_CHARACTERS_PATH / slug).exists():
        return slug
    counter = 2
    while (CUSTOM_CHARACTERS_PATH / f"{slug}-{counter}").exists():
        counter += 1
    return f"{slug}-{counter}"


def _read_metadata():
    if not METADATA_FILE.exists():
        return {'characters': {}, 'stages': {}, 'custom_stages': [], 'custom_characters': []}
    with open(METADATA_FILE, 'r') as f:
        data = json.load(f)
    if 'custom_characters' not in data:
        data['custom_characters'] = []
    return data


def _write_metadata(data):
    with open(METADATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def _resolve_asset_png(assets_dir, asset_ref):
    """Resolve an asset reference like 'css\\icon' to a .png file path."""
    if not asset_ref or not assets_dir.exists():
        return None
    normalized = asset_ref.replace('\\', '/').replace('/', os.sep)
    png_path = assets_dir / f"{normalized}.png"
    if png_path.exists():
        return png_path
    basename = Path(normalized).name
    candidate = assets_dir / f"{basename}.png"
    if candidate.exists():
        return candidate
    return None


@custom_characters_bp.route('/api/mex/custom-characters/list', methods=['GET'])
def list_custom_characters():
    try:
        metadata = _read_metadata()
        characters = metadata.get('custom_characters', [])
        for char in characters:
            char['icon_url'] = f"/api/mex/custom-characters/{char['slug']}/icon"
        return jsonify({'success': True, 'characters': characters})
    except Exception as e:
        logger.error(f"List custom characters error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/import-zip', methods=['POST'])
def import_custom_character_zip():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        uploaded = request.files['file']
        if not uploaded.filename or not uploaded.filename.lower().endswith('.zip'):
            return jsonify({'success': False, 'error': 'File must be a .zip'}), 400

        zip_data = uploaded.read()

        import io
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            names = zf.namelist()

            fighter_json_path = None
            icon_path = None

            for name in names:
                basename = name.split('/')[-1].lower()
                if basename == 'fighter.json':
                    fighter_json_path = name
                elif basename == 'icon.png':
                    icon_path = name

            if not fighter_json_path:
                return jsonify({'success': False, 'error': 'ZIP must contain a fighter.json file'}), 400

            fighter_meta = json.loads(zf.read(fighter_json_path))
            fighter_name = fighter_meta.get('name', uploaded.filename.rsplit('.', 1)[0])

            slug = _dedupe_slug(_make_slug(fighter_name))
            char_dir = CUSTOM_CHARACTERS_PATH / slug
            char_dir.mkdir(parents=True, exist_ok=True)

            (char_dir / 'fighter.zip').write_bytes(zip_data)

            with open(char_dir / 'fighter.json', 'w') as f:
                json.dump(fighter_meta, f, indent=2)

            has_css_icon = False
            if icon_path:
                (char_dir / 'css_icon.png').write_bytes(zf.read(icon_path))
                has_css_icon = True

            costume_count = len(fighter_meta.get('costumes', []))

        entry = {
            'slug': slug,
            'name': fighter_name,
            'source': 'zip',
            'date_added': datetime.now().isoformat(),
            'series_id': fighter_meta.get('seriesID', 0),
            'costume_count': costume_count,
            'has_css_icon': has_css_icon
        }

        metadata = _read_metadata()
        metadata['custom_characters'].append(entry)
        _write_metadata(metadata)

        logger.info(f"[OK] Imported custom character '{fighter_name}' as {slug}")
        return jsonify({'success': True, 'character': entry})
    except zipfile.BadZipFile:
        return jsonify({'success': False, 'error': 'Invalid or corrupted ZIP file'}), 400
    except Exception as e:
        logger.error(f"Import custom character ZIP error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def _extract_custom_characters_from_project(project_dir, source_label):
    """Extract custom characters from a MEX project directory into the vault.
    Returns (imported, skipped) name lists."""
    fighters_dir = project_dir / 'data' / 'fighters'
    assets_dir = project_dir / 'assets'
    project_path = project_dir / 'project.mexproj'

    if not fighters_dir.exists():
        raise FileNotFoundError('Project data/fighters/ directory not found')

    with open(project_path, 'r') as f:
        proj_data = json.load(f)

    fighter_files = proj_data.get('fighterSaveMap', {}).get('filePaths', [])
    if not fighter_files:
        return [], []

    metadata = _read_metadata()
    existing_names = {c['name'].lower() for c in metadata.get('custom_characters', [])}

    imported = []
    skipped = []

    mexcli_path = str(MEXCLI_PATH)

    for fighter_index, fighter_file in enumerate(fighter_files):
        fighter_json_path = fighters_dir / fighter_file
        if not fighter_json_path.exists():
            continue

        try:
            with open(fighter_json_path, 'r') as f:
                fighter_data = json.load(f)

            fighter_name = fighter_data.get('name', '')
            if not fighter_name or fighter_name in VANILLA_FIGHTER_NAMES:
                continue

            if fighter_name.lower() in existing_names:
                skipped.append(fighter_name)
                continue

            slug = _dedupe_slug(_make_slug(fighter_name))
            char_dir = CUSTOM_CHARACTERS_PATH / slug
            char_dir.mkdir(parents=True, exist_ok=True)

            # Export full fighter ZIP via MexCLI
            zip_path = char_dir / 'fighter.zip'
            if Path(mexcli_path).exists():
                export_cmd = [mexcli_path, 'export-fighter', str(project_path), str(fighter_index), str(zip_path)]
                export_result = subprocess.run(
                    export_cmd, capture_output=True, text=True,
                    cwd=str(PROJECT_ROOT), **get_subprocess_args()
                )
                if export_result.returncode != 0:
                    logger.warning(f"Failed to export fighter ZIP for '{fighter_name}': {export_result.stderr or export_result.stdout}")

            with open(char_dir / 'fighter.json', 'w') as f:
                json.dump(fighter_data, f, indent=2)

            assets_obj = fighter_data.get('assets', {})
            has_css_icon = False
            icon_ref = assets_obj.get('cssIcon')
            icon_file = _resolve_asset_png(assets_dir, icon_ref)
            if icon_file:
                shutil.copy2(icon_file, char_dir / 'css_icon.png')
                has_css_icon = True

            costumes = fighter_data.get('costumes', [])
            for i, costume in enumerate(costumes):
                csp_ref = costume.get('csp')
                csp_file = _resolve_asset_png(assets_dir, csp_ref)
                if csp_file:
                    shutil.copy2(csp_file, char_dir / f'csp_{i}.png')
                stock_ref = costume.get('icon')
                stock_file = _resolve_asset_png(assets_dir, stock_ref)
                if stock_file:
                    shutil.copy2(stock_file, char_dir / f'stock_{i}.png')

            entry = {
                'slug': slug,
                'name': fighter_name,
                'source': source_label,
                'date_added': datetime.now().isoformat(),
                'series_id': fighter_data.get('seriesID', 0),
                'costume_count': len(costumes),
                'has_css_icon': has_css_icon
            }

            metadata['custom_characters'].append(entry)
            existing_names.add(fighter_name.lower())
            imported.append(fighter_name)

        except (json.JSONDecodeError, KeyError):
            continue

    if imported:
        _write_metadata(metadata)

    return imported, skipped


@custom_characters_bp.route('/api/mex/custom-characters/scan-iso', methods=['POST'])
def scan_iso_for_custom_characters():
    """Create a temp MEX project from an ISO, extract custom characters, clean up."""
    try:
        data = request.json or {}
        iso_path = data.get('isoPath', '').strip()
        if not iso_path:
            return jsonify({'success': False, 'error': 'Missing isoPath parameter'}), 400

        iso_file = Path(iso_path)
        if not iso_file.exists():
            return jsonify({'success': False, 'error': f'ISO not found: {iso_path}'}), 404
        if iso_file.suffix.lower() not in ('.iso', '.gcm'):
            return jsonify({'success': False, 'error': 'File must be an .iso or .gcm'}), 400

        mexcli_path = str(MEXCLI_PATH)
        if not Path(mexcli_path).exists():
            return jsonify({'success': False, 'error': 'MexCLI not found. Build MexCLI first.'}), 500

        temp_dir = tempfile.mkdtemp(prefix='nucleus_char_scan_')
        try:
            logger.info(f"Scanning ISO for custom characters: {iso_path}")

            cmd = [mexcli_path, 'import-iso', str(iso_file), temp_dir, 'temp_scan']
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                cwd=str(PROJECT_ROOT), **get_subprocess_args()
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or 'Unknown error'
                logger.error(f"MexCLI import-iso failed: {error_msg}")
                return jsonify({'success': False, 'error': f'Failed to open ISO: {error_msg}'}), 500

            project_dir = Path(temp_dir)
            if not (project_dir / 'project.mexproj').exists():
                return jsonify({'success': False, 'error': 'MexCLI created project but .mexproj not found'}), 500

            imported, skipped = _extract_custom_characters_from_project(project_dir, 'iso-scan')

            logger.info(f"[OK] ISO character scan: imported {len(imported)}, skipped {len(skipped)}")
            return jsonify({
                'success': True,
                'imported': imported,
                'skipped': skipped,
                'message': f"Imported {len(imported)} custom character(s), skipped {len(skipped)} duplicate(s)"
            })
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        logger.error(f"Scan ISO for custom characters error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/icon', methods=['GET'])
def get_custom_character_icon(slug):
    icon_path = CUSTOM_CHARACTERS_PATH / slug / 'css_icon.png'
    if icon_path.exists():
        return send_file(icon_path, mimetype='image/png')
    return jsonify({'success': False, 'error': 'Icon not found'}), 404


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/detail', methods=['GET'])
def get_custom_character_detail(slug):
    """Return full character detail including costume info with image URLs."""
    try:
        char_dir = CUSTOM_CHARACTERS_PATH / slug
        fighter_json_path = char_dir / 'fighter.json'
        if not fighter_json_path.exists():
            return jsonify({'success': False, 'error': 'Character not found'}), 404

        with open(fighter_json_path, 'r') as f:
            fighter_data = json.load(f)

        costumes = []
        for i, costume in enumerate(fighter_data.get('costumes', [])):
            csp_exists = (char_dir / f'csp_{i}.png').exists()
            stock_exists = (char_dir / f'stock_{i}.png').exists()
            costumes.append({
                'index': i,
                'name': costume.get('name', f'Costume {i}'),
                'csp_url': f"/api/mex/custom-characters/{slug}/csp/{i}" if csp_exists else None,
                'stock_url': f"/api/mex/custom-characters/{slug}/stock/{i}" if stock_exists else None,
            })

        detail = {
            'name': fighter_data.get('name', ''),
            'series_id': fighter_data.get('seriesID', 0),
            'can_wall_jump': fighter_data.get('canWallJump', False),
            'sound_bank': fighter_data.get('soundBank'),
            'victory_theme': fighter_data.get('victoryTheme'),
            'target_test_stage': fighter_data.get('targetTestStage'),
            'costumes': costumes,
            'has_css_icon': (char_dir / 'css_icon.png').exists(),
            'icon_url': f"/api/mex/custom-characters/{slug}/icon",
            'files': fighter_data.get('files', {}),
        }

        return jsonify({'success': True, 'detail': detail})
    except Exception as e:
        logger.error(f"Get custom character detail error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/csp/<int:index>', methods=['GET'])
def get_custom_character_csp(slug, index):
    csp_path = CUSTOM_CHARACTERS_PATH / slug / f'csp_{index}.png'
    if csp_path.exists():
        return send_file(csp_path, mimetype='image/png')
    return jsonify({'success': False, 'error': 'CSP not found'}), 404


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/stock/<int:index>', methods=['GET'])
def get_custom_character_stock(slug, index):
    stock_path = CUSTOM_CHARACTERS_PATH / slug / f'stock_{index}.png'
    if stock_path.exists():
        return send_file(stock_path, mimetype='image/png')
    return jsonify({'success': False, 'error': 'Stock icon not found'}), 404


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/delete', methods=['POST'])
def delete_custom_character(slug):
    try:
        char_dir = CUSTOM_CHARACTERS_PATH / slug
        if char_dir.exists():
            shutil.rmtree(char_dir)

        metadata = _read_metadata()
        metadata['custom_characters'] = [
            c for c in metadata.get('custom_characters', []) if c['slug'] != slug
        ]
        _write_metadata(metadata)

        logger.info(f"[OK] Deleted custom character '{slug}'")
        return jsonify({'success': True, 'message': f'Deleted {slug}'})
    except Exception as e:
        logger.error(f"Delete custom character error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/rename', methods=['POST'])
def rename_custom_character(slug):
    try:
        data = request.json
        new_name = data.get('newName', '').strip()
        if not new_name:
            return jsonify({'success': False, 'error': 'New name is required'}), 400

        metadata = _read_metadata()

        for existing in metadata.get('custom_characters', []):
            if existing['slug'] != slug and existing['name'].lower() == new_name.lower():
                return jsonify({'success': False, 'error': f"A character named '{existing['name']}' already exists"}), 400

        char_entry = None
        for c in metadata.get('custom_characters', []):
            if c['slug'] == slug:
                c['name'] = new_name
                char_entry = c
                break

        if not char_entry:
            return jsonify({'success': False, 'error': f'Character {slug} not found'}), 404

        fighter_json_path = CUSTOM_CHARACTERS_PATH / slug / 'fighter.json'
        if fighter_json_path.exists():
            with open(fighter_json_path, 'r') as f:
                fighter_data = json.load(f)
            fighter_data['name'] = new_name
            with open(fighter_json_path, 'w') as f:
                json.dump(fighter_data, f, indent=2)

        _write_metadata(metadata)

        logger.info(f"[OK] Renamed custom character '{slug}' to '{new_name}'")
        return jsonify({'success': True, 'character': char_entry})
    except Exception as e:
        logger.error(f"Rename custom character error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/<slug>/export', methods=['GET'])
def export_custom_character(slug):
    zip_path = CUSTOM_CHARACTERS_PATH / slug / 'fighter.zip'
    if zip_path.exists():
        return send_file(zip_path, as_attachment=True, download_name=f'{slug}.zip')

    return jsonify({'success': False, 'error': 'Fighter ZIP not found (imported from project scan?)'}), 404


@custom_characters_bp.route('/api/mex/custom-characters/install', methods=['POST'])
def install_custom_character():
    """Install a custom character from the vault into the currently open project."""
    try:
        data = request.json or {}
        slug = data.get('slug', '').strip()
        if not slug:
            return jsonify({'success': False, 'error': 'Missing slug parameter'}), 400

        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No project loaded. Open a project first.'}), 400

        zip_path = CUSTOM_CHARACTERS_PATH / slug / 'fighter.zip'
        if not zip_path.exists():
            return jsonify({'success': False, 'error': f'Fighter ZIP not found for "{slug}". Re-scan the ISO to generate it.'}), 404

        mexcli_path = str(MEXCLI_PATH)
        if not Path(mexcli_path).exists():
            return jsonify({'success': False, 'error': 'MexCLI not found'}), 500

        cmd = [mexcli_path, 'add-fighter', str(project_path), str(zip_path)]
        logger.info(f"Installing custom character '{slug}': {' '.join(cmd)}")

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            cwd=str(PROJECT_ROOT), **get_subprocess_args()
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or 'Unknown error'
            logger.error(f"add-fighter failed: {error_msg}")
            return jsonify({'success': False, 'error': f'Failed to add fighter: {error_msg}'}), 500

        import time
        time.sleep(0.15)
        reload_mex_manager()

        try:
            cli_output = json.loads(result.stdout.strip().split('\n')[-1])
        except (json.JSONDecodeError, IndexError):
            cli_output = {}

        logger.info(f"[OK] Installed custom character '{slug}' into project")
        return jsonify({
            'success': True,
            'message': f"Added {cli_output.get('name', slug)} to project",
            'name': cli_output.get('name', slug),
            'costumeCount': cli_output.get('costumeCount', 0),
        })
    except Exception as e:
        logger.error(f"Install custom character error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_characters_bp.route('/api/mex/custom-characters/remove-from-project', methods=['POST'])
def remove_custom_character_from_project():
    """Remove a custom character from the currently open project."""
    try:
        data = request.json or {}
        fighter_name = data.get('name', '').strip()
        if not fighter_name:
            return jsonify({'success': False, 'error': 'Missing name parameter'}), 400

        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No project loaded.'}), 400

        mexcli_path = str(MEXCLI_PATH)
        cmd = [mexcli_path, 'remove-fighter', str(project_path), fighter_name]
        logger.info(f"Removing fighter '{fighter_name}': {' '.join(cmd)}")

        result = subprocess.run(
            cmd, capture_output=True, text=True,
            cwd=str(PROJECT_ROOT), **get_subprocess_args()
        )

        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or 'Unknown error'
            return jsonify({'success': False, 'error': f'Failed to remove fighter: {error_msg}'}), 500

        import time
        time.sleep(0.15)
        reload_mex_manager()

        logger.info(f"[OK] Removed fighter '{fighter_name}' from project")
        return jsonify({'success': True, 'message': f'Removed {fighter_name}'})
    except Exception as e:
        logger.error(f"Remove fighter error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
