"""
Vault Backup Blueprint - Backup and restore operations.

Handles creating backups of the storage vault and restoring from backups.
"""

import os
import json
import shutil
import zipfile
import tempfile
import logging
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, after_this_request

from core.config import PROJECT_ROOT, STORAGE_PATH, LOGS_PATH

logger = logging.getLogger(__name__)

vault_backup_bp = Blueprint('vault_backup', __name__)


@vault_backup_bp.route('/api/mex/storage/backup', methods=['POST'])
def backup_vault():
    """Create a backup ZIP of the entire storage vault"""
    try:
        logger.info("=== VAULT BACKUP REQUEST ===")

        backups_dir = PROJECT_ROOT / "output" / "vault_backups"
        backups_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_filename = f"vault_backup_{timestamp}.zip"
        backup_path = backups_dir / backup_filename

        logger.info(f"Creating backup: {backup_path}")

        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(STORAGE_PATH):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(STORAGE_PATH)
                    zipf.write(file_path, arcname)

        backup_size = backup_path.stat().st_size
        logger.info(f"Backup created successfully: {backup_size} bytes")
        logger.info("=== VAULT BACKUP COMPLETE ===")

        return jsonify({
            'success': True,
            'filename': backup_filename,
            'size': backup_size,
            'path': str(backup_path)
        })
    except Exception as e:
        logger.error(f"Vault backup error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@vault_backup_bp.route('/api/mex/storage/backup/download/<filename>', methods=['GET'])
def download_backup(filename):
    """Download a backup file"""
    try:
        backups_dir = PROJECT_ROOT / "output" / "vault_backups"
        backup_path = backups_dir / filename

        if not backup_path.exists():
            return jsonify({'success': False, 'error': 'Backup file not found'}), 404

        @after_this_request
        def remove_file(response):
            try:
                os.remove(backup_path)
                logger.info(f"Deleted backup file after download: {filename}")
            except Exception as error:
                logger.error(f"Error deleting backup file {filename}: {str(error)}")
            return response

        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/zip'
        )
    except Exception as e:
        logger.error(f"Backup download error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@vault_backup_bp.route('/api/mex/storage/restore', methods=['POST'])
def restore_vault():
    """Restore vault from a backup ZIP file"""
    try:
        logger.info("=== VAULT RESTORE REQUEST ===")

        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No backup file uploaded'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not file.filename.lower().endswith('.zip'):
            return jsonify({'success': False, 'error': 'Only ZIP files are supported'}), 400

        restore_mode = request.form.get('mode', 'replace')

        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = Path(tmp.name)

        try:
            with zipfile.ZipFile(tmp_path, 'r') as zipf:
                file_list = zipf.namelist()
                if 'metadata.json' not in file_list:
                    return jsonify({'success': False, 'error': 'Invalid backup file: metadata.json not found'}), 400

            logger.info(f"Restore mode: {restore_mode}")

            if restore_mode == 'replace':
                logger.info("Clearing existing storage...")
                if STORAGE_PATH.exists():
                    shutil.rmtree(STORAGE_PATH)
                STORAGE_PATH.mkdir(parents=True, exist_ok=True)

            logger.info("Extracting backup...")
            with zipfile.ZipFile(tmp_path, 'r') as zipf:
                zipf.extractall(STORAGE_PATH)

            logger.info("=== VAULT RESTORE COMPLETE ===")

            return jsonify({
                'success': True,
                'message': f'Vault restored successfully ({restore_mode} mode)',
                'mode': restore_mode
            })
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
    except Exception as e:
        logger.error(f"Vault restore error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@vault_backup_bp.route('/api/mex/storage/clear', methods=['POST'])
def clear_storage():
    """Clear storage based on provided options."""
    try:
        data = request.json or {}
        clear_intake = data.get('clearIntake', False)
        clear_logs = data.get('clearLogs', False)

        logger.info("=== CLEAR STORAGE REQUEST ===")
        logger.info(f"Clear Intake: {clear_intake}")
        logger.info(f"Clear Logs: {clear_logs}")

        removed_count = 0
        output_lines = []

        # Clear storage
        logger.info("Clearing storage...")
        output_lines.append("Clearing storage...")

        # Remove character folders in storage (excluding 'das' folder)
        if STORAGE_PATH.exists():
            for item in STORAGE_PATH.iterdir():
                if item.is_dir() and item.name != "das":
                    logger.info(f"  Removing: {item.name}/")
                    output_lines.append(f"  Removing: {item.name}/")
                    shutil.rmtree(item)
                    removed_count += 1

        # Remove stage variant folders in storage/das/
        das_dir = STORAGE_PATH / "das"
        if das_dir.exists():
            for stage_folder in das_dir.iterdir():
                if stage_folder.is_dir():
                    variant_count = 0
                    for variant_item in stage_folder.iterdir():
                        if variant_item.is_file():
                            variant_item.unlink()
                        else:
                            shutil.rmtree(variant_item)
                        variant_count += 1
                    if variant_count > 0:
                        logger.info(f"  Removing: das/{stage_folder.name}/ ({variant_count} items)")
                        output_lines.append(f"  Removing: das/{stage_folder.name}/ ({variant_count} items)")
                        removed_count += 1

        # Clear Python cache directories
        for cache_dir in PROJECT_ROOT.rglob("__pycache__"):
            if cache_dir.is_dir():
                logger.info(f"  Removing: {cache_dir.relative_to(PROJECT_ROOT)}")
                output_lines.append(f"  Removing: {cache_dir.relative_to(PROJECT_ROOT)}")
                shutil.rmtree(cache_dir)
                removed_count += 1

        # Reset metadata.json to default structure
        metadata_file = STORAGE_PATH / 'metadata.json'
        if metadata_file.exists() or STORAGE_PATH.exists():
            logger.info("  Resetting: metadata.json")
            output_lines.append("  Resetting: metadata.json")
            STORAGE_PATH.mkdir(parents=True, exist_ok=True)
            with open(metadata_file, 'w') as f:
                json.dump({'version': '1.0', 'characters': {}, 'stages': {}}, f, indent=2)
            removed_count += 1

        if removed_count > 0:
            output_lines.append(f"[OK] Cleared {removed_count} items from storage")
        else:
            output_lines.append("[INFO] Storage is already empty")

        # Optionally clear intake
        if clear_intake:
            logger.info("\nClearing intake...")
            output_lines.append("\nClearing intake...")
            intake_dir = PROJECT_ROOT / "intake"
            intake_count = 0
            if intake_dir.exists():
                for item in intake_dir.iterdir():
                    if item.is_file():
                        logger.info(f"  Removing: {item.name}")
                        output_lines.append(f"  Removing: {item.name}")
                        item.unlink()
                        intake_count += 1
            if intake_count > 0:
                output_lines.append(f"[OK] Cleared {intake_count} files from intake")
            else:
                output_lines.append("[INFO] Intake is already empty")

        # Optionally clear logs
        if clear_logs:
            logger.info("\nClearing logs...")
            output_lines.append("\nClearing logs...")
            logs_count = 0
            if LOGS_PATH.exists():
                for item in LOGS_PATH.iterdir():
                    if item.is_file() and item.suffix == '.log':
                        logger.info(f"  Removing: {item.name}")
                        output_lines.append(f"  Removing: {item.name}")
                        item.unlink()
                        logs_count += 1
            if logs_count > 0:
                output_lines.append(f"[OK] Cleared {logs_count} log files")
            else:
                output_lines.append("[INFO] No log files to clear")

        logger.info("=== CLEAR STORAGE COMPLETE ===")
        output_lines.append("\nDone!")

        return jsonify({
            'success': True,
            'message': 'Storage cleared successfully',
            'output': '\n'.join(output_lines)
        })
    except Exception as e:
        logger.error(f"Clear storage error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500