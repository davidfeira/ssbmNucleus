"""HF cache inspection, download, and deletion — vendored from assetFarm.

Runs in the Flask process and needs only huggingface_hub + tqdm (pure
Python), so model downloads work before/without the heavy engine install.
Honors the optional 'hfCacheDir' override; by default the STANDARD HF cache
is used so existing downloads are picked up as-is.
"""
import threading
import time

from huggingface_hub import scan_cache_dir, snapshot_download
from tqdm import tqdm as _tqdm_base

from aiengine.registry import MODELS, find


def _cache_dir_arg():
    from aiengine.settings_store import load_settings
    cache_dir = load_settings().get('hfCacheDir')
    if cache_dir:
        from pathlib import Path
        return str(Path(cache_dir) / 'hub')
    return None


def get_statuses():
    """{model_id: {'downloaded': bool, 'partial': bool, 'sizeOnDiskBytes': int,
    'nbFiles': int}} for every local model in the registry.

    A repo can sit in the cache INCOMPLETE (interrupted download: stubs and
    config present, weight shards missing) — scan_cache_dir can't tell, so a
    repo well under half its expected size counts as 'partial', not
    downloaded. snapshot_download resumes partials, so Download doubles as
    Resume."""
    kwargs = {}
    cache_dir = _cache_dir_arg()
    if cache_dir:
        kwargs['cache_dir'] = cache_dir
    try:
        cache_info = scan_cache_dir(**kwargs)
        cached = {repo.repo_id: repo for repo in cache_info.repos}
    except Exception:
        cached = {}

    statuses = {}
    for model_id, spec in MODELS.items():
        if spec.kind != 'local':
            continue
        repo = cached.get(spec.repo_id)
        size = repo.size_on_disk if repo else 0
        complete = repo is not None and \
            size >= spec.disk_estimate_gb * 0.5 * 1024**3
        statuses[model_id] = {
            'downloaded': complete,
            'partial': repo is not None and not complete,
            'sizeOnDiskBytes': size,
            'nbFiles': repo.nb_files if repo else 0,
        }
    return statuses


def downloaded_ids():
    return {mid for mid, st in get_statuses().items() if st['downloaded']}


# ---------------------------------------------------------------------------
# Download with progress (tqdm-tap pattern from assetFarm's cache_utils)
# ---------------------------------------------------------------------------
class _DownloadTracker:
    """Thread-safe shared state for tracking download progress."""

    def __init__(self):
        self._lock = threading.Lock()
        self.file_name = ''
        self.cur_file_done = 0
        self.cur_file_total = 0
        self.completed_bytes = 0
        self.total_bytes = 0
        self.files_done = 0
        self.files_total = 0
        self._seen_files = set()

    def start_file(self, name, total):
        with self._lock:
            self.file_name = name
            self.cur_file_done = 0
            self.cur_file_total = total
            if name not in self._seen_files:
                self._seen_files.add(name)
                self.total_bytes += total

    def update_file_bar(self, name, done, total):
        with self._lock:
            if name != self.file_name:
                self.completed_bytes += self.cur_file_total
                self.file_name = name
                self.cur_file_total = total
                if name not in self._seen_files:
                    self._seen_files.add(name)
                    self.total_bytes += total
            self.cur_file_done = done

    def update_count_bar(self, done, total):
        with self._lock:
            self.files_done = done
            self.files_total = total

    def snapshot(self):
        with self._lock:
            return {
                'fileName': self.file_name,
                'bytesDone': self.completed_bytes + self.cur_file_done,
                'bytesTotal': self.total_bytes,
                'filesDone': self.files_done,
                'filesTotal': self.files_total,
            }


_active_tracker = None


class _TrackingTqdm(_tqdm_base):
    """tqdm subclass that mirrors progress into the active _DownloadTracker."""

    def __init__(self, *args, **kwargs):
        self._hf_name = kwargs.pop('name', None)
        super().__init__(*args, **kwargs)
        self._is_byte_bar = (getattr(self, 'unit', '') == 'B')
        tracker = _active_tracker
        if tracker is not None and self._is_byte_bar and self.total:
            desc = self._hf_name or getattr(self, 'desc', '') or ''
            tracker.start_file(desc, self.total)

    def update(self, n=1):
        super().update(n)
        tracker = _active_tracker
        if tracker is None:
            return
        if self._is_byte_bar:
            desc = self._hf_name or getattr(self, 'desc', '') or ''
            tracker.update_file_bar(desc, self.n, self.total or 0)
        else:
            tracker.update_count_bar(self.n, self.total or 0)


def download_model_with_progress(model_id):
    """Download a model's weights, yielding progress dicts until done.
    Yields {'status': 'progress', ...tracker snapshot} every ~0.5s, then a
    final {'status': 'done'|'error', 'message': str}."""
    global _active_tracker

    spec = find(model_id)
    if spec is None or spec.kind != 'local':
        yield {'status': 'error', 'message': f'unknown local model: {model_id}'}
        return

    tracker = _DownloadTracker()
    _active_tracker = tracker
    result = {}

    def _run():
        nonlocal result
        try:
            kwargs = {'tqdm_class': _TrackingTqdm}
            cache_dir = _cache_dir_arg()
            if cache_dir:
                kwargs['cache_dir'] = cache_dir
            snapshot_download(spec.repo_id, **kwargs)
            result = {'status': 'done',
                      'message': f'downloaded {spec.id} ({spec.repo_id})'}
        except Exception as exc:
            result = {'status': 'error', 'message': str(exc)}

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    while thread.is_alive():
        snap = tracker.snapshot()
        snap['status'] = 'progress'
        yield snap
        time.sleep(0.5)
    _active_tracker = None

    yield result or {'status': 'error',
                     'message': 'download thread exited unexpectedly'}


def delete_model_cache(model_id):
    """Delete a model's cached weights. Returns freed bytes (0 if it wasn't
    cached). Raises on registry misses."""
    spec = find(model_id)
    if spec is None or spec.kind != 'local':
        raise ValueError(f'unknown local model: {model_id}')

    kwargs = {}
    cache_dir = _cache_dir_arg()
    if cache_dir:
        kwargs['cache_dir'] = cache_dir
    cache_info = scan_cache_dir(**kwargs)
    target = next((r for r in cache_info.repos if r.repo_id == spec.repo_id), None)
    if target is None:
        return 0

    hashes = [rev.commit_hash for rev in target.revisions]
    strategy = cache_info.delete_revisions(*hashes)
    freed = strategy.expected_freed_size
    strategy.execute()
    return freed
