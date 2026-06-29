"""
Vault Backup Blueprint - Backup and restore operations.

Handles creating backups of the storage vault and restoring from backups.
"""

import os
import copy
import json
import uuid
import shutil
import zipfile
import tempfile
import logging
import threading
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file, after_this_request

from core.config import PROJECT_ROOT, STORAGE_PATH, LOGS_PATH
from core.state import get_socketio

logger = logging.getLogger(__name__)

vault_backup_bp = Blueprint('vault_backup', __name__)


def _emit_restore(restore_id, event, **payload):
    """Emit a vault-restore socketio event (no-op if socketio isn't wired)."""
    socketio = get_socketio()
    if socketio is None:
        return
    try:
        socketio.emit(event, {'restore_id': restore_id, **payload})
    except Exception as e:
        logger.debug(f"restore emit failed: {e}")


def _extract_zip_with_progress(zipf, dest, restore_id, lo, hi,
                               skip=(), phase='Extracting files'):
    """Extract every member of an open ZipFile into ``dest``, emitting
    ``vault_restore_progress`` percentages mapped onto the [lo, hi] band. Members
    in ``skip`` (posix relative paths) are not written. Returns the temp/extract
    root used so callers can post-process."""
    members = [m for m in zipf.namelist() if m not in skip]
    total = len(members) or 1
    last_pct = -1
    for i, member in enumerate(members, 1):
        zipf.extract(member, dest)
        pct = lo + int((i / total) * (hi - lo))
        # Throttle: only emit when the integer percent advances.
        if pct != last_pct:
            last_pct = pct
            _emit_restore(restore_id, 'vault_restore_progress',
                          percentage=pct,
                          message=f'{phase}… ({i}/{total})')


@vault_backup_bp.route('/api/mex/storage/stats', methods=['GET'])
def get_storage_stats():
    """Return total disk usage of the storage vault in bytes."""
    total = sum(f.stat().st_size for f in STORAGE_PATH.rglob('*') if f.is_file())
    return jsonify({'success': True, 'stats': {'storage': total}})


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


# Top-level metadata lists and the key that uniquely identifies an item within them.
_METADATA_LISTS = (
    ('xdelta', 'id'),
    ('custom_characters', 'slug'),
    ('custom_stages', 'slug'),
    ('bundles', 'id'),
)

# Dict-of-collections sections: section name -> key holding the per-entry item list.
_METADATA_COLLECTIONS = (
    ('characters', 'skins'),
    ('stages', 'variants'),
)


def merge_vault_metadata(current, incoming):
    """Merge ``incoming`` vault metadata into ``current``, keeping every current
    item and adding only items from the backup that aren't already present.

    The vault metadata has three shapes that each need different handling:

    * ``characters`` / ``stages`` -- dicts keyed by name, each holding a list of
      items (``skins`` / ``variants``) deduplicated by ``id``. Folder markers in a
      skin list also carry an ``id`` so they dedupe the same way.
    * ``xdelta`` / ``custom_characters`` / ``custom_stages`` / ``bundles`` --
      top-level lists deduplicated by ``id`` or ``slug``.
    * any other top-level key (e.g. ``version``) -- carried over from current,
      or from incoming when current lacks it.

    Returns ``(merged, stats)`` where ``stats`` counts items added from the backup.
    """
    merged = copy.deepcopy(current) if current else {}
    incoming = incoming or {}
    stats = {'characters': 0, 'stages': 0, 'xdelta': 0,
             'custom_characters': 0, 'custom_stages': 0, 'bundles': 0}

    # Dict-of-collections (characters/stages): merge per-name item lists by id.
    for section, item_key in _METADATA_COLLECTIONS:
        merged_section = merged.setdefault(section, {})
        for name, data in (incoming.get(section) or {}).items():
            if name not in merged_section:
                merged_section[name] = copy.deepcopy(data)
                stats[section] += len(data.get(item_key, []) if isinstance(data, dict) else [])
                continue
            existing_items = merged_section[name].setdefault(item_key, [])
            existing_ids = {item.get('id') for item in existing_items}
            for item in (data.get(item_key, []) if isinstance(data, dict) else []):
                if item.get('id') not in existing_ids:
                    existing_items.append(copy.deepcopy(item))
                    existing_ids.add(item.get('id'))
                    stats[section] += 1

    # Top-level lists (xdelta/custom_*/bundles): merge by identity key.
    for list_key, id_key in _METADATA_LISTS:
        existing_list = merged.setdefault(list_key, [])
        existing_ids = {item.get(id_key) for item in existing_list}
        for item in (incoming.get(list_key) or []):
            if item.get(id_key) not in existing_ids:
                existing_list.append(copy.deepcopy(item))
                existing_ids.add(item.get(id_key))
                stats[list_key] += 1

    # Preserve any other top-level keys the backup introduces (e.g. version).
    for key, value in incoming.items():
        if key not in merged:
            merged[key] = copy.deepcopy(value)

    return merged, stats


def merge_plan(current, incoming):
    """Compare current vs incoming vault metadata and classify every backup item
    as NEW (not in the vault) or a CONFLICT (already present -- we keep ours).

    Returns ``(report, skip_prefixes)``:

    * ``report`` = ``{'added': {...}, 'kept': {...}}`` where each is a dict of
      per-type display-name lists, so the UI can show exactly what happened.
    * ``skip_prefixes`` = relative-path prefixes of CONFLICTING items' files. The
      file copy skips anything under these so a kept item's folder is never
      polluted by the backup's (possibly different) copy of the same item. Each
      content type maps to a path prefix:
        - custom_characters / custom_stages -> ``<kind>/<slug>/`` (whole folder)
        - skins   -> ``<Character>/<id>.`` and ``<Character>/<id>_``
        - variants-> ``das/<stage>/<id>.`` and ``das/<stage>/<id>_``
      (xdelta / bundles are single-file items, so plain skip-existing is already
      atomic for them -- no prefix needed, only a report entry.)
    """
    current = current or {}
    incoming = incoming or {}
    added = {k: [] for k in ('custom_characters', 'custom_stages',
                             'skins', 'variants', 'xdelta', 'bundles')}
    kept = {k: [] for k in added}
    skip = set()

    # Folder-per-slug items: skip the WHOLE folder on conflict.
    for key in ('custom_characters', 'custom_stages'):
        cur_slugs = {i.get('slug') for i in (current.get(key) or []) if isinstance(i, dict)}
        for item in (incoming.get(key) or []):
            if not isinstance(item, dict):
                continue
            slug = item.get('slug')
            name = item.get('name') or slug
            if slug in cur_slugs:
                kept[key].append(name)
                skip.add(f'{key}/{slug}/')
            else:
                added[key].append(name)

    # Single-file top-level items keyed by id (skip-existing is already atomic).
    for key in ('xdelta', 'bundles'):
        cur_ids = {i.get('id') for i in (current.get(key) or []) if isinstance(i, dict)}
        for item in (incoming.get(key) or []):
            if not isinstance(item, dict):
                continue
            label = item.get('name') or item.get('id')
            (kept if item.get('id') in cur_ids else added)[key].append(label)

    # Skins: flat files <Character>/<id>.* -- skip that id's files on conflict.
    cur_chars = current.get('characters') or {}
    for char, data in (incoming.get('characters') or {}).items():
        cur_ids = {s.get('id') for s in ((cur_chars.get(char) or {}).get('skins') or [])
                   if isinstance(s, dict)}
        for s in ((data or {}).get('skins') or []):
            if not isinstance(s, dict) or s.get('type') == 'folder':
                continue  # folder markers are metadata-only (no files)
            sid = s.get('id')
            label = f"{char} {s.get('color') or sid}"
            if sid in cur_ids:
                kept['skins'].append(label)
                skip.add(f'{char}/{sid}.')
                skip.add(f'{char}/{sid}_')
            else:
                added['skins'].append(label)

    # Stage variants: flat files das/<stage>/<id>.* -- skip that id's files.
    cur_stages = current.get('stages') or {}
    for stage, data in (incoming.get('stages') or {}).items():
        cur_ids = {v.get('id') for v in ((cur_stages.get(stage) or {}).get('variants') or [])
                   if isinstance(v, dict)}
        for v in ((data or {}).get('variants') or []):
            if not isinstance(v, dict):
                continue
            vid = v.get('id')
            label = f"{stage}: {v.get('name') or vid}"
            if vid in cur_ids:
                kept['variants'].append(label)
                skip.add(f'das/{stage}/{vid}.')
                skip.add(f'das/{stage}/{vid}_')
            else:
                added['variants'].append(label)

    return {'added': added, 'kept': kept}, skip


def _merge_restore(zip_path, restore_id=None):
    """Restore a backup ZIP in *merge* mode: keep the current vault and add only
    items it doesn't already have. The backup's ``metadata.json`` is deep-merged
    with the current one (never overwritten). Data files for items you ALREADY
    have are skipped ATOMICALLY -- the whole conflicting item is left untouched,
    so a kept custom character/stage/skin can't end up as a mix of your build and
    the backup's. Returns ``(stats, report)``.

    Progress (when ``restore_id`` is given): extract 5->50%, copy 50->95%,
    metadata merge 95->100%.
    """
    with tempfile.TemporaryDirectory() as extract_dir:
        extract_root = Path(extract_dir)
        with zipfile.ZipFile(zip_path, 'r') as zipf:
            _extract_zip_with_progress(zipf, extract_root, restore_id, 5, 50,
                                       phase='Reading backup')

        # Merge metadata.json rather than letting extractall overwrite it.
        incoming_meta = {}
        incoming_meta_path = extract_root / 'metadata.json'
        if incoming_meta_path.exists():
            with open(incoming_meta_path, 'r', encoding='utf-8') as f:
                incoming_meta = json.load(f)

        current_meta = {}
        current_meta_path = STORAGE_PATH / 'metadata.json'
        if current_meta_path.exists():
            with open(current_meta_path, 'r', encoding='utf-8') as f:
                current_meta = json.load(f)

        report, skip_prefixes = merge_plan(current_meta, incoming_meta)
        merged_meta, stats = merge_vault_metadata(current_meta, incoming_meta)

        # Copy data files for NEW items only. Files belonging to an item you
        # already have are skipped wholesale (skip_prefixes) so your version is
        # kept intact -- no leaking the backup's extra files into your folder.
        # The dest-exists guard is a final safety for loose/shared files.
        STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        files = [s for s in extract_root.rglob('*')
                 if s.is_file() and s.relative_to(extract_root).as_posix() != 'metadata.json']
        total = len(files) or 1
        copied = 0
        last_pct = -1
        for i, src in enumerate(files, 1):
            rel = src.relative_to(extract_root)
            rel_posix = rel.as_posix()
            owned_by_conflict = any(rel_posix.startswith(p) for p in skip_prefixes)
            dest = STORAGE_PATH / rel
            if not owned_by_conflict and not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)
                copied += 1
            if restore_id:
                pct = 50 + int((i / total) * 45)
                if pct != last_pct:
                    last_pct = pct
                    _emit_restore(restore_id, 'vault_restore_progress',
                                  percentage=pct,
                                  message=f'Adding new items… ({copied} added)')

        if restore_id:
            _emit_restore(restore_id, 'vault_restore_progress',
                          percentage=95, message='Updating vault catalog…')
        with open(current_meta_path, 'w', encoding='utf-8') as f:
            json.dump(merged_meta, f, indent=2)

        return stats, report


def run_vault_restore(restore_id, tmp_path, restore_mode):
    """Background worker: restore a backup ZIP, emitting socketio progress.

    Events (all carry ``restore_id``):
      vault_restore_progress  {percentage, message}
      vault_restore_complete  {mode, message, added?}
      vault_restore_error     {error}
    The uploaded temp ZIP is deleted when finished.
    """
    tmp_path = Path(tmp_path)
    try:
        _emit_restore(restore_id, 'vault_restore_progress',
                      percentage=2, message='Reading backup…')
        logger.info(f"Restore mode: {restore_mode}")

        if restore_mode == 'merge':
            logger.info("Merging backup into existing vault...")
            stats, report = _merge_restore(tmp_path, restore_id=restore_id)
            added = sum(stats.values())
            kept = sum(len(v) for v in report['kept'].values())
            logger.info(f"Merge added {added} new item(s), kept {kept} conflict(s): {stats}")
            if added and kept:
                message = (f'Vault merged: added {added} new item(s), '
                           f'kept your version of {kept} conflict(s)')
            elif added:
                message = f'Vault merged: added {added} new item(s)'
            elif kept:
                message = (f'Vault merged: no new items — kept your version of '
                           f'{kept} item(s) already in your vault')
            else:
                message = 'Vault merged successfully (no new items found)'
            logger.info("=== VAULT RESTORE COMPLETE ===")
            _emit_restore(restore_id, 'vault_restore_complete',
                          mode=restore_mode, message=message,
                          added=stats, report=report)
            return

        # Replace mode.
        _emit_restore(restore_id, 'vault_restore_progress',
                      percentage=3, message='Clearing current vault…')
        logger.info("Clearing existing storage...")
        if STORAGE_PATH.exists():
            shutil.rmtree(STORAGE_PATH)
        STORAGE_PATH.mkdir(parents=True, exist_ok=True)

        logger.info("Extracting backup...")
        with zipfile.ZipFile(tmp_path, 'r') as zipf:
            _extract_zip_with_progress(zipf, STORAGE_PATH, restore_id, 5, 99,
                                       phase='Restoring files')

        logger.info("=== VAULT RESTORE COMPLETE ===")
        _emit_restore(restore_id, 'vault_restore_complete',
                      mode=restore_mode,
                      message='Vault restored successfully (replace mode)')
    except Exception as e:
        logger.error(f"Vault restore error: {str(e)}", exc_info=True)
        _emit_restore(restore_id, 'vault_restore_error', error=str(e))
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass


@vault_backup_bp.route('/api/mex/storage/restore', methods=['POST'])
def restore_vault():
    """Receive a backup ZIP, validate it, and kick off the restore in a
    background thread. Returns a ``restore_id`` immediately; the client follows
    progress via the ``vault_restore_progress/complete/error`` socketio events.

    The upload (saving the multi-GB ZIP) happens during this request, so the
    client can show upload progress via XHR; the slow extract/merge then streams
    progress over the socket."""
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

        # Validate before spawning the worker, so obvious errors return inline.
        # Close the zip BEFORE unlinking -- Windows can't delete an open file.
        validation_error = None
        try:
            with zipfile.ZipFile(tmp_path, 'r') as zipf:
                if 'metadata.json' not in zipf.namelist():
                    validation_error = 'Invalid backup file: metadata.json not found'
        except zipfile.BadZipFile:
            validation_error = 'Invalid backup file: not a valid ZIP'
        if validation_error:
            tmp_path.unlink(missing_ok=True)
            return jsonify({'success': False, 'error': validation_error}), 400

        restore_id = str(uuid.uuid4())[:8]
        threading.Thread(
            target=run_vault_restore,
            args=(restore_id, str(tmp_path), restore_mode),
            daemon=True,
        ).start()

        return jsonify({
            'success': True,
            'message': 'Vault restore started',
            'restore_id': restore_id,
            'mode': restore_mode,
        })
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