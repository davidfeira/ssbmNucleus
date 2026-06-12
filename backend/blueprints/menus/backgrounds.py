"""
Menu background mods (shared CSS/SSS pool).

A background mod is a normalized `background.dat` bundle (extracted from a
MnSlChr or MnSlMap dat via HSDRawViewer) plus an optional screenshot:

    storage/menus/css/background/
        metadata.json               # catalog of installed mods
        <mod_id>/
            mod.json                # per-mod manifest
            background.dat          # the model/animation bundle
            screenshot.png          # optional preview

The same pool installs into either the CSS (MnSlChr.usd) or the SSS
(MnSlMap.usd) of the currently loaded MEX project.
"""

import os
import shutil
import subprocess
import tempfile
import uuid
import zipfile
import logging
from pathlib import Path
from datetime import datetime
from flask import request, jsonify

from core.config import HSDRAW_EXE, MEXCLI_PATH, get_subprocess_args
from core.state import get_project_files_dir, get_current_project_path

from . import menus_bp
from .helpers import (
    BG_PATH, BG_METADATA,
    load_catalog, save_catalog, load_mod_json, save_mod_json,
    _safe_extract_zip, _find_screenshot, _run_hsd_cli,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# CSS Background mod catalog
# ─────────────────────────────────────────────────────────────────────────────

def _load_bg_catalog():
    return load_catalog(BG_METADATA, version='1.0')


def _save_bg_catalog(data):
    save_catalog(BG_METADATA, data)


def _load_bg_mod_json(mod_id):
    return load_mod_json(BG_PATH, mod_id)


def _save_bg_mod_json(mod_id, mod):
    save_mod_json(BG_PATH, mod_id, mod)


def _attach_bg_urls(mod):
    """Add screenshot URL to a background mod dict."""
    out = dict(mod)
    mod_id = mod.get('id')
    if not mod_id:
        return out
    base = f'/storage/menus/css/background/{mod_id}'
    if mod.get('screenshot'):
        out['screenshotUrl'] = f"{base}/{mod['screenshot']}"
    return out


def _find_mnslchr_dat(directory):
    """Find a MnSlChr dat/usd file in an extracted directory."""
    directory = Path(directory)
    for p in sorted(directory.rglob('*')):
        if not p.is_file():
            continue
        name_lower = p.name.lower()
        if name_lower.startswith('mnslchr') and name_lower.endswith(('.dat', '.usd')):
            return p
    return None


def _find_mnslmap_dat(directory):
    """Find a MnSlMap dat/usd file in an extracted directory."""
    directory = Path(directory)
    for p in sorted(directory.rglob('*')):
        if not p.is_file():
            continue
        name_lower = p.name.lower()
        if name_lower.startswith('mnslmap') and name_lower.endswith(('.dat', '.usd')):
            return p
    return None


@menus_bp.route('/api/mex/menus/css/background/list', methods=['GET'])
@menus_bp.route('/api/mex/menus/background/list', methods=['GET'])
def list_bg_mods():
    """List all installed background mods (shared CSS/SSS pool)."""
    try:
        catalog = _load_bg_catalog()
        mods = []
        for entry in catalog.get('mods', []):
            mod_id = entry.get('id')
            if not mod_id:
                continue
            out = dict(entry)
            if entry.get('screenshot'):
                out['screenshotUrl'] = f"/storage/menus/css/background/{mod_id}/{entry['screenshot']}"
            mod_json = _load_bg_mod_json(mod_id)
            if mod_json:
                out['includeScene'] = mod_json.get('includeScene', False)
            mods.append(out)
        return jsonify({'success': True, 'mods': mods})
    except Exception as e:
        logger.error(f'List bg mods error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


def import_bg_archive(src_path, original_filename, name=None, description=''):
    """Import a menu background mod (shared CSS/SSS pool) from a file on disk.

    Accepts .zip (containing MnSlChr.dat/.usd or MnSlMap.dat/.usd) or a raw
    .dat/.usd file. Auto-detects CSS vs SSS source and extracts the background
    model/animation bundle via HSDRawViewer.

    Returns the mod dict (without URLs). Raises ValueError for bad input,
    RuntimeError for extraction failures. Shared by the dedicated route and
    the unified /import/file dispatcher.
    """
    fname_lower = original_filename.lower()
    is_zip = fname_lower.endswith('.zip')
    name = (name or '').strip() or Path(original_filename).stem
    description = (description or '').strip()

    with tempfile.TemporaryDirectory(prefix='menubg_') as tmp:
        temp_root = Path(tmp)

        if is_zip:
            extract_dir = temp_root / 'extracted'
            extract_dir.mkdir()
            try:
                _safe_extract_zip(Path(src_path), extract_dir)
            except zipfile.BadZipFile:
                raise ValueError('Invalid or corrupt zip file')
            source_dat = _find_mnslchr_dat(extract_dir)
            hsd_cmd = '--css-bg'
            if source_dat is None:
                source_dat = _find_mnslmap_dat(extract_dir)
                hsd_cmd = '--sss-bg'
            screenshot_src = _find_screenshot(extract_dir)
        else:
            source_dat = temp_root / Path(original_filename).name
            shutil.copyfile(str(src_path), str(source_dat))
            screenshot_src = None
            # Detect by filename; default to CSS, fall back to SSS
            if 'mnslmap' in fname_lower:
                hsd_cmd = '--sss-bg'
            else:
                hsd_cmd = '--css-bg'

        if source_dat is None or not source_dat.exists():
            raise ValueError('No MnSlChr or MnSlMap .dat/.usd found in upload')

        export_dir = temp_root / 'bg_export'
        export_dir.mkdir()
        result = _run_hsd_cli([hsd_cmd, 'export', str(source_dat), str(export_dir)])
        if result is None:
            # Try the other command in case detection was wrong
            alt_cmd = '--sss-bg' if hsd_cmd == '--css-bg' else '--css-bg'
            result = _run_hsd_cli([alt_cmd, 'export', str(source_dat), str(export_dir)])
        if result is None:
            raise RuntimeError('Failed to extract background from DAT')

        bg_dat = export_dir / 'background.dat'
        if not bg_dat.exists():
            raise RuntimeError('HSDRawViewer did not produce background.dat')

        # Create mod entry
        mod_id = str(uuid.uuid4())[:8]
        mod_dir = BG_PATH / mod_id
        mod_dir.mkdir(parents=True, exist_ok=True)

        # Copy background.dat
        shutil.copy(str(bg_dat), str(mod_dir / 'background.dat'))

        # Copy screenshot if available
        screenshot_filename = None
        if screenshot_src is not None and screenshot_src.exists():
            screenshot_filename = f'screenshot{screenshot_src.suffix.lower()}'
            shutil.copy(str(screenshot_src), str(mod_dir / screenshot_filename))

        mod = {
            'id': mod_id,
            'name': name,
            'description': description,
            'screenshot': screenshot_filename,
            'created': datetime.now().isoformat(),
        }
        _save_bg_mod_json(mod_id, mod)

        catalog = _load_bg_catalog()
        catalog.setdefault('mods', []).append({
            'id': mod_id,
            'name': name,
            'description': description,
            'screenshot': screenshot_filename,
            'created': mod['created'],
        })
        _save_bg_catalog(catalog)

        logger.info(f'[OK] Imported CSS background mod: {name} ({mod_id})')
        return mod


@menus_bp.route('/api/mex/menus/css/background/import', methods=['POST'])
@menus_bp.route('/api/mex/menus/background/import', methods=['POST'])
def import_bg_mod():
    """Import a menu background mod (shared CSS/SSS pool)."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        fname_lower = file.filename.lower()
        if not fname_lower.endswith(('.zip', '.dat', '.usd')):
            return jsonify({'success': False, 'error': 'File must be .zip, .dat, or .usd'}), 400

        suffix = Path(file.filename).suffix.lower()
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        try:
            mod = import_bg_archive(tmp_path, file.filename,
                                    name=request.form.get('name'),
                                    description=request.form.get('description'))
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        return jsonify({'success': True, 'mod': _attach_bg_urls(mod)})

    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except RuntimeError as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    except Exception as e:
        logger.error(f'Import bg mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/background/install/<mod_id>', methods=['POST'])
def install_bg_to_mex(mod_id):
    """Install a CSS background mod into the currently loaded MEX project.

    1. Runs HSDRawViewer --css-bg import to swap the background in MnSlChr.usd
    2. Runs mexcli add-code to inject the Gecko code that disables the hardcoded
       CSS background animation, so the custom one is visible.
    """
    try:
        mod = _load_bg_mod_json(mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No MEX project loaded'}), 400

        files_dir = get_project_files_dir()
        if files_dir is None:
            return jsonify({'success': False, 'error': 'No project files directory'}), 400

        mnslchr_usd = Path(files_dir) / 'MnSlChr.usd'
        if not mnslchr_usd.exists():
            return jsonify({'success': False, 'error': f'MnSlChr.usd not found at {mnslchr_usd}'}), 400

        bg_dat = BG_PATH / mod_id / 'background.dat'
        if not bg_dat.exists():
            return jsonify({'success': False, 'error': 'background.dat missing from mod'}), 400

        if not HSDRAW_EXE.exists():
            return jsonify({'success': False, 'error': f'HSDRawViewer not found at {HSDRAW_EXE}'}), 500

        with tempfile.TemporaryDirectory(prefix='cssbg_install_') as tmp:
            output_usd = Path(tmp) / 'MnSlChr.usd'

            hsd_args = [
                '--css-bg', 'import',
                str(mnslchr_usd), str(bg_dat), str(output_usd)
            ]
            if mod.get('includeScene'):
                hsd_args.append('--include-scene')
            result = _run_hsd_cli(hsd_args)
            if result is None:
                return jsonify({'success': False, 'error': 'HSDRawViewer --css-bg import failed'}), 500

            if not output_usd.exists():
                return jsonify({'success': False, 'error': 'Import produced no output file'}), 500

            # Copy output back to project
            shutil.copy(str(output_usd), str(mnslchr_usd))
            logger.info(f'  Replaced MnSlChr.usd with custom background')

        # Step 2: Add Gecko code to disable hardcoded CSS BG animation
        logger.info(f'  MexCLI path: {MEXCLI_PATH} (exists={MEXCLI_PATH.exists()})')
        logger.info(f'  Project path: {project_path}')
        if MEXCLI_PATH.exists():
            try:
                cmd = [str(MEXCLI_PATH), 'add-code',
                       str(project_path),
                       'Disable Hardcoded CSS BG Anim',
                       '04263384 48000010']
                logger.info(f'  Running: {" ".join(cmd)}')
                code_result = subprocess.run(
                    cmd,
                    capture_output=True, text=True, timeout=60,
                    **get_subprocess_args()
                )
                logger.info(f'  add-code exit={code_result.returncode} stdout={code_result.stdout[:500]}')
                if code_result.stderr:
                    logger.info(f'  add-code stderr={code_result.stderr[:500]}')
            except Exception as e:
                logger.warning(f'  Failed to add Gecko code: {e}')
        else:
            logger.warning(f'  MexCLI not found at {MEXCLI_PATH}; skipping Gecko code injection')

        msg = f'Installed background "{mod["name"]}". Rebuild ISO to apply.'
        logger.info(f'[OK] Installed CSS background mod {mod_id}')
        return jsonify({'success': True, 'message': msg})

    except Exception as e:
        logger.error(f'Install bg mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/css/background/delete/<mod_id>', methods=['POST'])
@menus_bp.route('/api/mex/menus/background/delete/<mod_id>', methods=['POST'])
def delete_bg_mod(mod_id):
    """Delete a background mod and its files."""
    try:
        catalog = _load_bg_catalog()
        mods = catalog.get('mods', [])
        idx = next((i for i, m in enumerate(mods) if m.get('id') == mod_id), -1)
        if idx < 0:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        mod_dir = BG_PATH / mod_id
        if mod_dir.exists():
            shutil.rmtree(mod_dir, ignore_errors=True)

        mods.pop(idx)
        _save_bg_catalog(catalog)
        logger.info(f'[OK] Deleted background mod: {mod_id}')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Delete bg mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/background/update/<mod_id>', methods=['POST'])
def update_bg_mod_settings(mod_id):
    """Update settings for a background mod (e.g. includeScene toggle)."""
    try:
        mod = _load_bg_mod_json(mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        data = request.get_json(silent=True) or {}
        if 'includeScene' in data:
            mod['includeScene'] = bool(data['includeScene'])

        _save_bg_mod_json(mod_id, mod)
        return jsonify({'success': True, 'mod': _attach_bg_urls(mod)})
    except Exception as e:
        logger.error(f'Update bg mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@menus_bp.route('/api/mex/menus/sss/background/install/<mod_id>', methods=['POST'])
def install_sss_bg_to_mex(mod_id):
    """Install a background mod into the SSS (MnSlMap.usd) of the loaded MEX project.

    Uses HSDRawViewer --sss-bg import to swap the background in MnSlMap.usd.
    """
    try:
        mod = _load_bg_mod_json(mod_id)
        if not mod:
            return jsonify({'success': False, 'error': 'Mod not found'}), 404

        project_path = get_current_project_path()
        if project_path is None:
            return jsonify({'success': False, 'error': 'No MEX project loaded'}), 400

        files_dir = get_project_files_dir()
        if files_dir is None:
            return jsonify({'success': False, 'error': 'No project files directory'}), 400

        mnslmap_usd = Path(files_dir) / 'MnSlMap.usd'
        if not mnslmap_usd.exists():
            return jsonify({'success': False, 'error': f'MnSlMap.usd not found at {mnslmap_usd}'}), 400

        bg_dat = BG_PATH / mod_id / 'background.dat'
        if not bg_dat.exists():
            return jsonify({'success': False, 'error': 'background.dat missing from mod'}), 400

        if not HSDRAW_EXE.exists():
            return jsonify({'success': False, 'error': f'HSDRawViewer not found at {HSDRAW_EXE}'}), 500

        with tempfile.TemporaryDirectory(prefix='sssbg_install_') as tmp:
            output_usd = Path(tmp) / 'MnSlMap.usd'

            hsd_args = [
                '--sss-bg', 'import',
                str(mnslmap_usd), str(bg_dat), str(output_usd)
            ]
            if mod.get('includeScene'):
                hsd_args.append('--include-scene')
            result = _run_hsd_cli(hsd_args)
            if result is None:
                return jsonify({'success': False, 'error': 'HSDRawViewer --sss-bg import failed'}), 500

            if not output_usd.exists():
                return jsonify({'success': False, 'error': 'Import produced no output file'}), 500

            shutil.copy(str(output_usd), str(mnslmap_usd))
            logger.info(f'  Replaced MnSlMap.usd with custom background')

        msg = f'Installed background "{mod["name"]}" to SSS. Rebuild ISO to apply.'
        logger.info(f'[OK] Installed SSS background mod {mod_id}')
        return jsonify({'success': True, 'message': msg})

    except Exception as e:
        logger.error(f'Install SSS bg mod error: {e}', exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
