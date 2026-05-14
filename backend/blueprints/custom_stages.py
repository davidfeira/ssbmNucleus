"""
Custom Stages Blueprint - Manage m-ex custom stages in the vault.

Custom stages are entirely new stages (not DAS texture variants). They are
imported from MexManager-exported ZIP packages or scanned from an open m-ex
project. Each stage is stored as:

    storage/custom_stages/<slug>/
        stage.zip       (original ZIP preserved for re-export)
        icon.png        (extracted for fast serving)
        banner.png      (extracted for detail view)
        stage.json      (extracted metadata)

Metadata is tracked under metadata.json["custom_stages"] (list of objects).
"""

import json
import re
import shutil
import zipfile
import logging
from pathlib import Path
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file

from core.config import STORAGE_PATH
from core.state import get_current_project_path

logger = logging.getLogger(__name__)

custom_stages_bp = Blueprint('custom_stages', __name__)

CUSTOM_STAGES_PATH = STORAGE_PATH / 'custom_stages'
CUSTOM_STAGES_PATH.mkdir(parents=True, exist_ok=True)

METADATA_FILE = STORAGE_PATH / 'metadata.json'


def _sanitize_filename(name):
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()


def _make_slug(name):
    slug = _sanitize_filename(name).lower().replace(' ', '-')
    slug = re.sub(r'-+', '-', slug).strip('-')
    if not slug:
        slug = 'custom-stage'
    return slug


def _dedupe_slug(slug):
    if not (CUSTOM_STAGES_PATH / slug).exists():
        return slug
    counter = 2
    while (CUSTOM_STAGES_PATH / f"{slug}-{counter}").exists():
        counter += 1
    return f"{slug}-{counter}"


def _read_metadata():
    if not METADATA_FILE.exists():
        return {'characters': {}, 'stages': {}, 'custom_stages': []}
    with open(METADATA_FILE, 'r') as f:
        data = json.load(f)
    if 'custom_stages' not in data:
        data['custom_stages'] = []
    return data


def _write_metadata(data):
    with open(METADATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)


@custom_stages_bp.route('/api/mex/custom-stages/list', methods=['GET'])
def list_custom_stages():
    try:
        metadata = _read_metadata()
        stages = metadata.get('custom_stages', [])
        for stage in stages:
            stage['icon_url'] = f"/api/mex/custom-stages/{stage['slug']}/icon"
        return jsonify({'success': True, 'stages': stages})
    except Exception as e:
        logger.error(f"List custom stages error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/import-zip', methods=['POST'])
def import_custom_stage_zip():
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

            stage_json_path = None
            dat_files = []
            icon_path = None
            banner_path = None

            for name in names:
                lower = name.lower()
                basename = name.split('/')[-1].lower()
                if basename == 'stage.json':
                    stage_json_path = name
                elif basename.endswith('.dat'):
                    dat_files.append(name)
                elif basename == 'icon.png':
                    icon_path = name
                elif basename == 'banner.png':
                    banner_path = name

            if not stage_json_path:
                return jsonify({'success': False, 'error': 'ZIP must contain a stage.json file'}), 400
            if not dat_files:
                return jsonify({'success': False, 'error': 'ZIP must contain at least one .dat file'}), 400

            stage_meta = json.loads(zf.read(stage_json_path))
            stage_name = stage_meta.get('name', uploaded.filename.rsplit('.', 1)[0])

            slug = _dedupe_slug(_make_slug(stage_name))
            stage_dir = CUSTOM_STAGES_PATH / slug
            stage_dir.mkdir(parents=True, exist_ok=True)

            (stage_dir / 'stage.zip').write_bytes(zip_data)

            with open(stage_dir / 'stage.json', 'w') as f:
                json.dump(stage_meta, f, indent=2)

            has_icon = False
            if icon_path:
                (stage_dir / 'icon.png').write_bytes(zf.read(icon_path))
                has_icon = True

            has_banner = False
            if banner_path:
                (stage_dir / 'banner.png').write_bytes(zf.read(banner_path))
                has_banner = True

        entry = {
            'slug': slug,
            'name': stage_name,
            'source': 'zip',
            'date_added': datetime.now().isoformat(),
            'series_id': stage_meta.get('seriesID', 0),
            'sound_bank': stage_meta.get('soundBank', None),
            'dat_files': [n.split('/')[-1] for n in dat_files],
            'has_banner': has_banner,
            'has_icon': has_icon
        }

        metadata = _read_metadata()
        metadata['custom_stages'].append(entry)
        _write_metadata(metadata)

        logger.info(f"[OK] Imported custom stage '{stage_name}' as {slug}")
        return jsonify({'success': True, 'stage': entry})
    except zipfile.BadZipFile:
        return jsonify({'success': False, 'error': 'Invalid or corrupted ZIP file'}), 400
    except Exception as e:
        logger.error(f"Import custom stage ZIP error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/scan-project', methods=['POST'])
def scan_project_for_custom_stages():
    try:
        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No project loaded. Open a project first.'}), 400

        project_dir = project_path.parent
        files_dir = project_dir / 'files'
        data_dir = project_dir / 'data'
        assets_sss_dir = project_dir / 'assets' / 'sss'

        if not files_dir.exists():
            return jsonify({'success': False, 'error': 'Project files/ directory not found'}), 404

        VANILLA_STAGE_CODES = {'GrNBa', 'GrNLa', 'GrSt', 'GrOp', 'GrPs', 'GrIz'}

        metadata = _read_metadata()
        existing_names = {s['name'].lower() for s in metadata.get('custom_stages', [])}

        imported = []
        skipped = []

        stage_jsons = []
        for search_dir in [data_dir, assets_sss_dir]:
            if search_dir and search_dir.exists():
                stage_jsons.extend(search_dir.rglob('*.json'))

        for stage_json_path in stage_jsons:
            try:
                with open(stage_json_path, 'r') as f:
                    stage_data = json.load(f)

                stage_name = stage_data.get('name', '')
                file_name = stage_data.get('fileName', '')

                if not stage_name:
                    continue

                is_vanilla = False
                for code in VANILLA_STAGE_CODES:
                    if code in file_name or code.lower() in file_name.lower():
                        is_vanilla = True
                        break

                if is_vanilla:
                    continue

                if stage_name.lower() in existing_names:
                    skipped.append(stage_name)
                    continue

                slug = _dedupe_slug(_make_slug(stage_name))
                stage_dir = CUSTOM_STAGES_PATH / slug
                stage_dir.mkdir(parents=True, exist_ok=True)

                with open(stage_dir / 'stage.json', 'w') as f:
                    json.dump(stage_data, f, indent=2)

                icon_name = stage_data.get('iconFile', '')
                has_icon = False
                if icon_name and assets_sss_dir.exists():
                    icon_candidates = list(assets_sss_dir.rglob(icon_name))
                    if icon_candidates:
                        shutil.copy2(icon_candidates[0], stage_dir / 'icon.png')
                        has_icon = True

                banner_name = stage_data.get('bannerFile', '')
                has_banner = False
                if banner_name and assets_sss_dir.exists():
                    banner_candidates = list(assets_sss_dir.rglob(banner_name))
                    if banner_candidates:
                        shutil.copy2(banner_candidates[0], stage_dir / 'banner.png')
                        has_banner = True

                dat_files_found = []
                if file_name and files_dir.exists():
                    dat_candidates = list(files_dir.rglob(f"{file_name}*"))
                    for dc in dat_candidates:
                        if dc.suffix.lower() == '.dat':
                            dat_files_found.append(dc.name)

                entry = {
                    'slug': slug,
                    'name': stage_name,
                    'source': 'project-scan',
                    'date_added': datetime.now().isoformat(),
                    'series_id': stage_data.get('seriesID', 0),
                    'sound_bank': stage_data.get('soundBank', None),
                    'dat_files': dat_files_found,
                    'has_banner': has_banner,
                    'has_icon': has_icon
                }

                metadata['custom_stages'].append(entry)
                existing_names.add(stage_name.lower())
                imported.append(stage_name)

            except (json.JSONDecodeError, KeyError):
                continue

        if imported:
            _write_metadata(metadata)

        logger.info(f"[OK] Project scan: imported {len(imported)}, skipped {len(skipped)}")
        return jsonify({
            'success': True,
            'imported': imported,
            'skipped': skipped,
            'message': f"Imported {len(imported)} custom stage(s), skipped {len(skipped)} duplicate(s)"
        })
    except Exception as e:
        logger.error(f"Scan project for custom stages error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/<slug>/icon', methods=['GET'])
def get_custom_stage_icon(slug):
    icon_path = CUSTOM_STAGES_PATH / slug / 'icon.png'
    if icon_path.exists():
        return send_file(icon_path, mimetype='image/png')
    return jsonify({'success': False, 'error': 'Icon not found'}), 404


@custom_stages_bp.route('/api/mex/custom-stages/<slug>/banner', methods=['GET'])
def get_custom_stage_banner(slug):
    banner_path = CUSTOM_STAGES_PATH / slug / 'banner.png'
    if banner_path.exists():
        return send_file(banner_path, mimetype='image/png')
    return jsonify({'success': False, 'error': 'Banner not found'}), 404


@custom_stages_bp.route('/api/mex/custom-stages/<slug>/delete', methods=['POST'])
def delete_custom_stage(slug):
    try:
        stage_dir = CUSTOM_STAGES_PATH / slug
        if stage_dir.exists():
            shutil.rmtree(stage_dir)

        metadata = _read_metadata()
        metadata['custom_stages'] = [
            s for s in metadata.get('custom_stages', []) if s['slug'] != slug
        ]
        _write_metadata(metadata)

        logger.info(f"[OK] Deleted custom stage '{slug}'")
        return jsonify({'success': True, 'message': f'Deleted {slug}'})
    except Exception as e:
        logger.error(f"Delete custom stage error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/<slug>/rename', methods=['POST'])
def rename_custom_stage(slug):
    try:
        data = request.json
        new_name = data.get('newName', '').strip()
        if not new_name:
            return jsonify({'success': False, 'error': 'New name is required'}), 400

        metadata = _read_metadata()

        for existing in metadata.get('custom_stages', []):
            if existing['slug'] != slug and existing['name'].lower() == new_name.lower():
                return jsonify({'success': False, 'error': f"A stage named '{existing['name']}' already exists"}), 400

        stage_entry = None
        for s in metadata.get('custom_stages', []):
            if s['slug'] == slug:
                s['name'] = new_name
                stage_entry = s
                break

        if not stage_entry:
            return jsonify({'success': False, 'error': f'Stage {slug} not found'}), 404

        stage_json_path = CUSTOM_STAGES_PATH / slug / 'stage.json'
        if stage_json_path.exists():
            with open(stage_json_path, 'r') as f:
                stage_data = json.load(f)
            stage_data['name'] = new_name
            with open(stage_json_path, 'w') as f:
                json.dump(stage_data, f, indent=2)

        _write_metadata(metadata)

        logger.info(f"[OK] Renamed custom stage '{slug}' to '{new_name}'")
        return jsonify({'success': True, 'stage': stage_entry})
    except Exception as e:
        logger.error(f"Rename custom stage error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@custom_stages_bp.route('/api/mex/custom-stages/<slug>/export', methods=['GET'])
def export_custom_stage(slug):
    zip_path = CUSTOM_STAGES_PATH / slug / 'stage.zip'
    if zip_path.exists():
        return send_file(zip_path, as_attachment=True, download_name=f'{slug}.zip')

    return jsonify({'success': False, 'error': 'Stage ZIP not found (imported from project scan?)'}), 404
