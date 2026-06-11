"""Generation-run ledger: storage/ai_runs.jsonl, one JSON object per line.

  {"ts": 1760000000.1, "provider": "local", "model": "sd-turbo",
   "tier": "standard", "kind": "material" | "ailab" | "stage",
   "seconds": 14.2, "success": true, "cached": false, "est_cost_usd": 0.0}

Append-only; aggregation reads the whole file (a few KB per hundred runs).
"""
import json
import statistics
import threading
import time

from aiengine.paths import RUNS_LEDGER

_lock = threading.Lock()


def record_run(provider, model, tier, kind, seconds, success,
               cached=False, est_cost_usd=0.0):
    entry = {
        'ts': round(time.time(), 1),
        'provider': provider,
        'model': model,
        'tier': tier,
        'kind': kind,
        'seconds': round(float(seconds), 2),
        'success': bool(success),
        'cached': bool(cached),
        'est_cost_usd': round(float(est_cost_usd or 0.0), 4),
    }
    line = json.dumps(entry)
    with _lock:
        RUNS_LEDGER.parent.mkdir(parents=True, exist_ok=True)
        with RUNS_LEDGER.open('a', encoding='utf-8') as f:
            f.write(line + '\n')


def _read_runs(days=None):
    cutoff = time.time() - days * 86400 if days else 0
    runs = []
    try:
        with RUNS_LEDGER.open('r', encoding='utf-8') as f:
            for line in f:
                try:
                    run = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if run.get('ts', 0) >= cutoff:
                    runs.append(run)
    except OSError:
        pass
    return runs


def aggregate(days=90):
    """Per-model stats + totals over the window. Timing stats consider only
    successful, non-cached runs (cache hits would skew averages to ~0)."""
    runs = _read_runs(days)
    groups = {}
    for run in runs:
        groups.setdefault((run.get('provider'), run.get('model')), []).append(run)

    per_model = []
    for (provider, model), items in groups.items():
        attempts = [r for r in items if not r.get('cached')]
        timed = [r['seconds'] for r in attempts if r.get('success')]
        per_model.append({
            'provider': provider,
            'model': model,
            'runs': len(attempts),
            'successRate': (sum(1 for r in attempts if r.get('success'))
                            / len(attempts)) if attempts else None,
            'avgSeconds': round(sum(timed) / len(timed), 1) if timed else None,
            'medianSeconds': round(statistics.median(timed), 1) if timed else None,
            'cachedHits': sum(1 for r in items if r.get('cached')),
            'lastTs': max(r['ts'] for r in items),
            'totalCostUsd': round(sum(r.get('est_cost_usd', 0)
                                      for r in items if r.get('success')), 3),
        })
    per_model.sort(key=lambda m: m['lastTs'], reverse=True)

    return {
        'perModel': per_model,
        'totals': {
            'runs': sum(m['runs'] for m in per_model),
            'cachedHits': sum(m['cachedHits'] for m in per_model),
            'costUsd': round(sum(m['totalCostUsd'] for m in per_model), 3),
        },
    }


def model_stats(days=90):
    """{model: {runs, avgSeconds, medianSeconds, lastTs}} keyed by the model
    string recorded in the ledger — convenience for the catalog endpoint."""
    return {m['model']: {'runs': m['runs'], 'avgSeconds': m['avgSeconds'],
                         'medianSeconds': m['medianSeconds'], 'lastTs': m['lastTs']}
            for m in aggregate(days)['perModel']}
