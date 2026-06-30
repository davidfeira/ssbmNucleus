"""
Export Blueprint - ISO export routes with progress tracking.

Handles ISO export with WebSocket progress updates and download.
"""

import os
import shutil
import threading
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, after_this_request

from core.config import OUTPUT_PATH, STORAGE_PATH
from core.state import get_mex_manager, get_socketio, get_current_project_path, mexcli_lock

logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__)


def _resolve_project_dat(files_dir, file_name):
    """Locate a costume's model DAT in a project's files/ dir.

    Handles region-resolved names (Red Falcon's costume fileName is 'PlCaRe.' --
    a trailing dot, no extension; the game appends usd/dat by region). Prefers
    .dat (the model) over .usd. Returns a Path or None.
    """
    from pathlib import Path
    if not file_name:
        return None
    files_dir = Path(files_dir)
    direct = files_dir / file_name
    if direct.is_file():
        return direct
    stem = file_name.rstrip('.')
    for ext in ('.dat', '.usd', ''):
        cand = files_dir / f"{stem}{ext}"
        if cand.is_file():
            return cand
    return None


@export_bp.route('/api/mex/export/start', methods=['POST'])
def start_export():
    """
    Start ISO export (async operation with WebSocket progress)

    Body:
    {
        "filename": "modded_game.iso",  // optional
        "cspCompression": 1.0,  // optional, 0.1-1.0, default 1.0
        "useColorSmash": false,  // optional, boolean, default false
        "texturePackMode": false,  // optional, boolean, default false
        "slippiDolphinPath": "..."  // required if texturePackMode is true
    }
    """
    try:
        data = request.json or {}
        filename = data.get('filename', f'game_{datetime.now().strftime("%Y%m%d_%H%M%S")}.iso')
        csp_compression = data.get('cspCompression', 1.0)
        use_color_smash = data.get('useColorSmash', False)
        texture_pack_mode = data.get('texturePackMode', False)
        slippi_dolphin_path = data.get('slippiDolphinPath')

        # Validate compression range
        if not isinstance(csp_compression, (int, float)) or csp_compression < 0.1 or csp_compression > 1.0:
            return jsonify({
                'success': False,
                'error': 'cspCompression must be a number between 0.1 and 1.0'
            }), 400

        # Validate useColorSmash
        if not isinstance(use_color_smash, bool):
            return jsonify({
                'success': False,
                'error': 'useColorSmash must be a boolean'
            }), 400

        # Validate texture pack mode requirements
        if texture_pack_mode:
            if not slippi_dolphin_path:
                return jsonify({
                    'success': False,
                    'error': 'slippiDolphinPath is required when texturePackMode is enabled'
                }), 400

        output_file = OUTPUT_PATH / filename
        build_id = f"build_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"=== ISO EXPORT START ===")
        logger.info(f"Filename: {filename}")
        logger.info(f"CSP Compression: {csp_compression}")
        logger.info(f"Use Color Smash: {use_color_smash}")
        logger.info(f"Texture Pack Mode: {texture_pack_mode}")

        def export_with_progress():
            """Export ISO in background thread with WebSocket progress updates"""
            from pathlib import Path
            import tempfile
            mapping = None
            temp_root = None   # isolated temp copy of the project (texture-pack mode)
            socketio = get_socketio()
            current_project_path = get_current_project_path()

            # Hold the workspace lock for the entire export so a background
            # costume reorder (optimistic UI, applied asynchronously) can't run a
            # second MexCLI process on the project mid-build. If a reorder is
            # still in flight, this blocks until it finishes — i.e. the export
            # waits for pending order changes to settle first.
            mexcli_lock.acquire()
            try:
                def progress_callback(percentage, message):
                    socketio.emit('export_progress', {
                        'percentage': percentage,
                        'message': message
                    })

                mex = get_mex_manager()
                work_mex = mex   # what we export from; a TEMP copy in texture-pack mode

                # Heal legacy DAS folders on the LIVE project before any temp copy:
                # older versions wrote Pokemon Stadium alts as .usd, which the m-ex
                # loader rejects -> "no valid alts found" assert (dynamicAlts.c) and
                # a crash at stage load. Renaming them to .dat fixes this build and
                # the on-disk project permanently. Idempotent (no-op once clean).
                try:
                    from blueprints.das import migrate_das_folder_extensions
                    das_heal = migrate_das_folder_extensions(
                        Path(current_project_path).parent / 'files')
                    if das_heal['renamed'] or das_heal['removed']:
                        logger.info(
                            f"DAS folder heal: renamed {len(das_heal['renamed'])} "
                            f"+ removed {len(das_heal['removed'])} legacy .usd alt(s)")
                except Exception as e:
                    logger.warning(f"DAS extension migration skipped: {e}")

                # Texture-pack mode does ALL its work (placeholder swap, recompile,
                # export) on an isolated COPY of the project, so a crash — even an
                # OOM kill mid-export — can NEVER leave the real project full of
                # placeholder CSPs. The live project is read-only here.
                if texture_pack_mode:
                    from texture_pack import (
                        save_encoded_placeholder,
                        TexturePackMapping,
                        CostumeMapping,
                        find_hd_csp_by_hash,
                    )
                    from skinlab.hd_csp_cache import (
                        get_or_render_hd, hash_dat, get_cached, effective_key_hash)
                    from skinlab.csp_concurrency import csp_workers
                    from concurrent.futures import ThreadPoolExecutor, as_completed
                    from mex_bridge import MexManager
                    from core.config import MEXCLI_PATH

                    # Clear the DUMP folder to prevent old placeholders from confusing the scanner
                    if slippi_dolphin_path:
                        dump_path = Path(slippi_dolphin_path) / "User" / "Dump" / "Textures" / "GALE01"
                        if dump_path.exists():
                            shutil.rmtree(dump_path)
                            dump_path.mkdir(parents=True)
                            logger.info(f"Cleared dump folder: {dump_path}")

                    # Copy the live project into a throwaway temp dir and run everything
                    # against that copy via its own MexManager.
                    progress_callback(1, 'Preparing an isolated copy of the project…')
                    live_project_dir = current_project_path.parent
                    temp_root = Path(tempfile.mkdtemp(prefix='nucleus_texexport_'))
                    temp_project_dir = temp_root / live_project_dir.name
                    shutil.copytree(live_project_dir, temp_project_dir)
                    temp_mexproj = temp_project_dir / current_project_path.name
                    work_mex = MexManager(cli_path=str(MEXCLI_PATH), project_path=str(temp_mexproj))
                    logger.info(f"Texture-pack export isolated to temp project: {temp_project_dir}")

                    live_csp_dir = live_project_dir / "assets" / "csp"   # originals (untouched)
                    temp_csp_dir = temp_project_dir / "assets" / "csp"   # placeholders go here

                    # Create mapping
                    build_name = filename.replace('.iso', '')
                    mapping = TexturePackMapping(
                        build_id=build_id,
                        build_name=build_name,
                        created_at=datetime.now().isoformat()
                    )

                    temp_files_dir = temp_project_dir / "files"

                    # Pass 1: enumerate every costume slot that has a CSP, so HD
                    # render progress can be reported against a known total.
                    fighters = work_mex.list_fighters()
                    slots = []  # ordered; global index = position in this list
                    for fighter in fighters:
                        try:
                            result = work_mex._run_command("get-costumes", str(work_mex.project_path), fighter['name'])
                        except Exception as e:
                            logger.warning(f"Error listing costumes for {fighter['name']}: {e}")
                            continue
                        for costume_idx, costume in enumerate(result.get('costumes', [])):
                            if not costume.get('csp'):
                                continue
                            csp_ref = costume['csp'].replace('\\', '/')
                            csp_name = f"{csp_ref.split('/')[-1]}.png"
                            if not (temp_csp_dir / csp_name).exists():
                                continue
                            slots.append({
                                'character': fighter['name'],
                                'costume_index': costume_idx,
                                'skin_id': costume.get('name', f"costume_{costume_idx}"),
                                'csp_name': csp_name,
                                'file_name': costume.get('fileName') or '',
                            })

                    total_slots = len(slots)
                    logger.info(f"Texture-pack: {total_slots} costume CSP slots to process")

                    # Pass 2: resolve each slot's HD CSP, then swap in the 16x16
                    # placeholder. HD priority per slot: the user's vault HD CSP,
                    # then the DAT-hash cache, then a fresh 4x render (patch costumes
                    # are custom art with no vault/vanilla match -> render once, cached
                    # by DAT hash so every later export is instant). A failed render
                    # leaves hd_csp_path=None -> SD fallback (never breaks a build).
                    # Renders are the slow part and independent per slot, so resolve
                    # them in parallel (worker count auto-sized to the machine); the
                    # mapping + placeholder write is cheap and done serially after.
                    def _resolve_slot_hd(slot):
                        """Resolve (hd_csp_path, dat_hash, was_miss) for one slot.
                        Thread-safe: only reads shared inputs and renders via
                        get_or_render_hd (own temp dir + atomic cache publish +
                        staggered launch)."""
                        live_sd = str(live_csp_dir / slot['csp_name'])
                        try:
                            vault_hd = find_hd_csp_by_hash(STORAGE_PATH, live_sd, slot['character'])
                        except Exception:
                            vault_hd = None
                        if vault_hd:
                            return str(vault_hd), None, False
                        dat_path = _resolve_project_dat(temp_files_dir, slot['file_name'])
                        if dat_path is None:
                            return None, None, False
                        dat_hash = hash_dat(dat_path)

                        # Ice Climbers: composite Nana onto Popo so the HD portrait
                        # matches the in-game both-climbers CSP. For a Nana-primary
                        # slot generate_csp renders nothing and we fall back to SD.
                        paired_dat_path = None
                        if dat_path.name[:4].lower() in ('plpp', 'plnn'):
                            try:
                                from generate_csp import find_ice_climbers_pair
                                _ct, pair_path, _pc, _nc = find_ice_climbers_pair(str(dat_path))
                                if pair_path:
                                    paired_dat_path = pair_path
                            except Exception as e:
                                logger.warning(f"ICs pair lookup failed for {dat_path.name}: {e}")

                        eff_hash = effective_key_hash(
                            dat_path, paired_dat_path=paired_dat_path, dat_hash=dat_hash)
                        was_miss = bool(eff_hash) and get_cached(eff_hash) is None
                        hd = get_or_render_hd(
                            dat_path, dat_hash=dat_hash, paired_dat_path=paired_dat_path)
                        return (str(hd) if hd else None), dat_hash, was_miss

                    rendered = 0
                    hd_by_index = {}  # global_index -> (hd_csp_path, dat_hash)
                    workers = csp_workers()
                    done = 0
                    progress_callback(
                        1, f"Rendering HD portraits (0/{total_slots}, ×{workers} workers)…")
                    with ThreadPoolExecutor(max_workers=workers) as pool:
                        futs = {pool.submit(_resolve_slot_hd, s): i
                                for i, s in enumerate(slots)}
                        for fut in as_completed(futs):
                            gi = futs[fut]
                            try:
                                hd_csp_path, dat_hash, was_miss = fut.result()
                            except Exception as e:
                                logger.warning(
                                    f"HD resolve failed for slot {gi} "
                                    f"({slots[gi]['character']}/{slots[gi]['skin_id']}): {e}")
                                hd_csp_path, dat_hash, was_miss = None, None, False
                            hd_by_index[gi] = (hd_csp_path, dat_hash)
                            if was_miss and hd_csp_path:
                                rendered += 1
                            done += 1
                            if done % 4 == 0 or done == total_slots:
                                pct = 1 + int(4 * done / max(1, total_slots))
                                progress_callback(
                                    pct,
                                    f"Rendering HD portraits "
                                    f"({done}/{total_slots}, ×{workers} workers)…")

                    # Assemble the mapping + placeholders in slot order (cheap, ordered).
                    for global_index, slot in enumerate(slots):
                        hd_csp_path, dat_hash = hd_by_index.get(global_index, (None, None))
                        live_sd_csp = str(live_csp_dir / slot['csp_name'])
                        mapping.add_costume(CostumeMapping(
                            index=global_index,
                            character=slot['character'],
                            costume_index=slot['costume_index'],
                            skin_id=slot['skin_id'],
                            real_csp_path=live_sd_csp,
                            hd_csp_path=hd_csp_path,
                            dat_hash=dat_hash,
                        ))
                        # Replace the COPY's CSP with the encoded placeholder (16x16)
                        save_encoded_placeholder(global_index, temp_csp_dir / slot['csp_name'])

                    global_index = total_slots
                    logger.info(
                        f"Created {global_index} placeholder CSPs (in temp copy); "
                        f"{rendered} HD portraits rendered this export")

                    # Save a debug sample so user can verify the placeholder format
                    debug_placeholder = OUTPUT_PATH / "debug_placeholder_sample.png"
                    save_encoded_placeholder(12345, debug_placeholder)  # Test index to verify encoding

                    # Save mapping
                    mapping_file = OUTPUT_PATH / f"{build_id}_texture_mapping.json"
                    mapping.save(mapping_file)
                    logger.info(f"Saved texture mapping to {mapping_file}")

                    # Recompile the COPY's CSPs from the placeholder PNGs (regenerates
                    # its .tex files so the export uses the placeholders, not cached tex).
                    logger.info("Recompiling CSPs from placeholder PNGs (temp copy)...")
                    recompile_result = work_mex.recompile_csps()
                    logger.info(f"CSP recompile complete: {recompile_result.get('message', 'done')}")

                # Note: Extras are patched immediately on import, not at export time

                # Note: character sound packs are installed per-project from
                # the Sounds menu (character_sounds.py), not at export time

                # Bake Frame Speed Modifier data (fsm.txt) for installed custom
                # characters into the project's main.dol. In texture-pack mode bake
                # into the TEMP copy so the live project's dol isn't modified.
                try:
                    from fsm_patcher import apply_project_fsm
                    from blueprints.custom_characters import CUSTOM_CHARACTERS_PATH
                    fsm_project_path = Path(work_mex.project_path) if texture_pack_mode else current_project_path
                    fsm_count = apply_project_fsm(fsm_project_path, CUSTOM_CHARACTERS_PATH)
                    if fsm_count:
                        logger.info(f"FSM: baked {fsm_count} frame-speed entries into main.dol")
                        progress_callback(2, f"Baked {fsm_count} frame-speed (FSM) entries into the game")
                except Exception as e:
                    logger.warning(f"FSM patching skipped: {e}")

                # Run the actual export from the working project (the temp copy in
                # texture-pack mode). When using texture pack mode, skip compression
                # entirely because placeholders must stay at fixed 16x16 size.
                skip_compression = texture_pack_mode
                result = work_mex.export_iso(str(output_file), progress_callback, csp_compression, use_color_smash, skip_compression)

                # No CSP restore needed: the live project was never modified — all
                # placeholder work happened in the temp copy (cleaned up below).

                socketio.emit('export_complete', {
                    'success': True,
                    'filename': filename,
                    'path': str(output_file),
                    'texturePackMode': texture_pack_mode,
                    'buildId': build_id if texture_pack_mode else None,
                    'totalCostumes': len(mapping.costumes) if mapping else 0
                })

            except Exception as e:
                logger.error(f"Export failed: {e}", exc_info=True)
                socketio.emit('export_error', {
                    'success': False,
                    'error': str(e)
                })
            finally:
                # Always clean up the isolated temp project copy.
                if temp_root and Path(temp_root).exists():
                    shutil.rmtree(temp_root, ignore_errors=True)
                    logger.info("Cleaned up temp texture-pack project copy")
                mexcli_lock.release()

        # Start export in background thread
        thread = threading.Thread(target=export_with_progress)
        thread.start()

        return jsonify({
            'success': True,
            'message': 'Export started',
            'filename': filename,
            'buildId': build_id if texture_pack_mode else None
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@export_bp.route('/api/mex/export/download/<filename>', methods=['GET'])
def download_iso(filename):
    """Download exported ISO file"""
    try:
        file_path = OUTPUT_PATH / filename

        if not file_path.exists():
            return jsonify({
                'success': False,
                'error': 'File not found'
            }), 404

        @after_this_request
        def remove_file(response):
            try:
                os.remove(file_path)
                logger.info(f"Deleted ISO file after download: {filename}")
            except Exception as error:
                logger.error(f"Error deleting ISO file {filename}: {str(error)}")
            return response

        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
