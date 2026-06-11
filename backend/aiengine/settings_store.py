"""storage/ai_studio.json — the AI Studio's persisted settings.

Shape:
  {"tierRouting": {"standard": {"provider": "local", "model": "sd-turbo"} | null,
                   "strong":   {"provider": "openrouter", "model": "google/..."} | null},
   "disabledModels": ["flux-klein-4b", ...],
   "hfCacheDir": null}

A null tier entry means "no explicit choice" — the resolver picks a default
from what's installed (see routing.py).
"""
import json
import threading

from aiengine.paths import CONFIG_PATH

_lock = threading.Lock()

DEFAULTS = {
    'tierRouting': {'standard': None, 'strong': None},
    'disabledModels': [],
    'hfCacheDir': None,
}


def load_settings():
    with _lock:
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            data = {}
    merged = {**DEFAULTS, **{k: v for k, v in data.items() if k in DEFAULTS}}
    merged['tierRouting'] = {**DEFAULTS['tierRouting'],
                             **(merged.get('tierRouting') or {})}
    return merged


def save_settings(updates):
    """Merge `updates` (top-level keys) into the stored settings and return
    the result."""
    current = load_settings()
    for key, value in updates.items():
        if key not in DEFAULTS:
            continue
        if key == 'tierRouting':
            current['tierRouting'] = {**current['tierRouting'], **(value or {})}
        else:
            current[key] = value
    with _lock:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(current, indent=2), encoding='utf-8')
    return current
