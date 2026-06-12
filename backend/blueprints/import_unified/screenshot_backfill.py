"""
Background screenshot backfill for DAS stage variants imported without one.

When the unified import lands a stage variant that has no screenshot, the
route enqueues a capture job here. A single worker thread drains the queue:
build the one-skin test ISO (test_build.build_stage_skin_iso), boot it in the
throwaway Dolphin and grab a clean whole-stage shot (ingame.capture.
capture_stage), save it exactly like the manual /storage/stages/
update-screenshot flow, and emit `stage_screenshot_backfilled` so the UI can
refresh the variant card.

Politeness rules:
  - shares the one-Dolphin-at-a-time slot with user-started tests
    (test_in_game.try_acquire_test_slot) and never preempts them;
  - defers while ANY Dolphin window is open (the user might be playing);
  - skips a job if the variant gained a screenshot in the meantime (manual
    upload or capture) or was deleted;
  - failures are logged and dropped — the variant just stays previewless,
    same as before this feature existed.

Windows-only, like the rest of the in-game harness.
"""

import logging
import os
import queue
import threading
import time
from datetime import datetime

from core.config import STORAGE_PATH
from core.metadata import load_metadata, save_metadata
from core.state import get_socketio

logger = logging.getLogger(__name__)

_queue = queue.Queue()
_worker_lock = threading.Lock()
_worker_started = False

# How long a job will politely wait for the engine/Dolphin to be free.
WAIT_FOR_SLOT_SECONDS = 15 * 60
POLL_SECONDS = 10


def enqueue_stage_screenshot(stage_code, stage_folder, variant_id,
                             vanilla_iso_path, slippi_dolphin_path):
    """Queue a screenshot capture for a freshly imported stage variant.
    Returns True if queued, False if prerequisites are missing (non-Windows,
    paths not provided). Never raises."""
    if os.name != 'nt':
        return False
    if not vanilla_iso_path or not slippi_dolphin_path:
        logger.info(f'[backfill] skipping {stage_folder}/{variant_id}: '
                    'no vanilla ISO / Slippi path in import request')
        return False
    if not stage_code:
        return False

    _queue.put({
        'stage_code': stage_code,
        'stage_folder': stage_folder,
        'variant_id': variant_id,
        'vanilla': vanilla_iso_path,
        'slippi': slippi_dolphin_path,
    })
    _ensure_worker()
    logger.info(f'[backfill] queued screenshot capture for '
                f'{stage_folder}/{variant_id} (queue size ~{_queue.qsize()})')
    return True


def pending_count():
    return _queue.qsize()


def _ensure_worker():
    global _worker_started
    with _worker_lock:
        if _worker_started:
            return
        _worker_started = True
    threading.Thread(target=_worker, name='stage-screenshot-backfill',
                     daemon=True).start()


def _worker():
    while True:
        job = _queue.get()
        try:
            _process(job)
        except Exception:
            logger.exception(f'[backfill] job failed: {job}')
        finally:
            _queue.task_done()


def _variant_entry(stage_folder, variant_id):
    metadata = load_metadata(default={'stages': {}})
    for v in metadata.get('stages', {}).get(stage_folder, {}).get('variants', []):
        if v['id'] == variant_id:
            return metadata, v
    return metadata, None


def _wait_for_engine():
    """Wait until the test slot is free AND no Dolphin window is open.
    Returns True once the slot is claimed, False on timeout."""
    from blueprints.test_in_game import try_acquire_test_slot, release_test_slot

    deadline = time.monotonic() + WAIT_FOR_SLOT_SECONDS
    last_log = 0.0
    while time.monotonic() < deadline:
        blocker = None
        if try_acquire_test_slot():
            # Slot claimed — but if the user has their own Dolphin open
            # (playing a match), back off and re-check later.
            try:
                from ingame.boot import dolphin_running
                if dolphin_running():
                    release_test_slot()
                    blocker = 'a Dolphin window is open'
                else:
                    return True
            except Exception:
                return True  # can't check → proceed; boot will fail loudly
        else:
            blocker = 'a test is running'
        if time.monotonic() - last_log > 60:
            logger.info(f'[backfill] waiting: {blocker} '
                        f'({int(deadline - time.monotonic())}s before giving up)')
            last_log = time.monotonic()
        time.sleep(POLL_SECONDS)
    return False


def _process(job):
    stage_folder = job['stage_folder']
    variant_id = job['variant_id']

    # Re-check the variant right before working: a manual upload/capture may
    # have landed, or the variant may be gone.
    _, variant = _variant_entry(stage_folder, variant_id)
    if variant is None:
        logger.info(f'[backfill] {stage_folder}/{variant_id} no longer exists, skipping')
        return
    if variant.get('has_screenshot'):
        logger.info(f'[backfill] {stage_folder}/{variant_id} already has a screenshot, skipping')
        return

    if not _wait_for_engine():
        logger.warning(f'[backfill] gave up waiting for the test engine for '
                       f'{stage_folder}/{variant_id}')
        return

    from blueprints.test_in_game import release_test_slot
    socketio = get_socketio()
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_iso = STORAGE_PATH / 'test-builds' / f'backfill_{job["stage_code"]}_{stamp}.iso'
    runs_root = STORAGE_PATH / 'test-runs'
    runs_root.mkdir(parents=True, exist_ok=True)

    try:
        from test_build import build_stage_skin_iso
        from ingame.capture import capture_stage
        from ingame.melee_sss import INTERNAL_STAGE_ID

        socketio.emit('stage_screenshot_backfill_started', {
            'stageFolder': stage_folder, 'variantId': variant_id})
        logger.info(f'[backfill] capturing {stage_folder}/{variant_id}...')

        r = build_stage_skin_iso(
            job['vanilla'], job['stage_code'], stage_folder, variant_id,
            str(out_iso),
            log=lambda m: logger.info(f'[backfill] {m}'))

        stage_name = r['stage']
        res = capture_stage(
            str(out_iso), job['slippi'], str(runs_root),
            internal_id=INTERNAL_STAGE_ID.get(stage_name),
            hold=r.get('button'), framing_key=stage_name,
            log=lambda m: logger.info(f'[backfill] {m}'))

        if not res.get('ok') or not res.get('png'):
            logger.warning(f'[backfill] capture failed for {stage_folder}/'
                           f'{variant_id}: {res.get("reason")}')
            return

        # Save exactly like /storage/stages/update-screenshot — but only if
        # the variant STILL has no screenshot (the capture takes a while).
        metadata, variant = _variant_entry(stage_folder, variant_id)
        if variant is None or variant.get('has_screenshot'):
            logger.info(f'[backfill] {stage_folder}/{variant_id} changed during '
                        'capture, discarding shot')
            return

        das_folder = STORAGE_PATH / 'das' / stage_folder
        das_folder.mkdir(parents=True, exist_ok=True)
        for old in das_folder.glob(f'{variant_id}_screenshot.*'):
            try:
                old.unlink()
            except OSError:
                pass
        screenshot_path = das_folder / f'{variant_id}_screenshot.png'
        screenshot_path.write_bytes(res['png'])

        variant['has_screenshot'] = True
        variant['screenshot_filename'] = f'{variant_id}_screenshot.png'
        save_metadata(metadata)

        url = f'/storage/das/{stage_folder}/{variant_id}_screenshot.png'
        socketio.emit('stage_screenshot_backfilled', {
            'stageFolder': stage_folder, 'variantId': variant_id,
            'screenshotUrl': url})
        logger.info(f'[backfill] [OK] saved screenshot for {stage_folder}/{variant_id}')

    finally:
        try:
            if out_iso.exists():
                out_iso.unlink()
        except Exception:
            pass
        release_test_slot()
