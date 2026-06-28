"""
detect_pool.py - run the unified-import content classifier over the local
ssbm-backup mod pool and tally the results.

Validates backend/blueprints/import_unified/detection.py against real-world
uploads before the /import/file route is rewired onto it:

  - archives:   every .zip/.7z under uploads/posts and post_zips (no ground
                truth; we eyeball the distribution + unknowns)
  - loose DATs: sampled from the DB dump where file_type='character_dat',
                wrapped in a temp zip exactly like the route does, and the
                detected character is compared against the DB's character

Usage:
    python detect_pool.py archives [--backup-root D:/ssbm-backup] [--limit N]
    python detect_pool.py dats [--backup-root D:/ssbm-backup] [--sample N] [--seed N]
    python detect_pool.py isos [--slippi-root D:/Slippi]

Writes a JSONL report next to tests/artifacts/nucleus/.
"""
import argparse
import importlib.util
import json
import random
import sys
import tempfile
import zipfile
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND = REPO_ROOT / 'backend'
BACKUP_ROOT = Path('D:/ssbm-backup')
SLIPPI_ROOT = Path('D:/Slippi')
ARTIFACTS = REPO_ROOT / 'tests' / 'artifacts' / 'nucleus'

sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mod_pool import ModPool  # noqa: E402


def load_detection():
    """Load detection.py by path so we don't drag in the Flask blueprint."""
    spec = importlib.util.spec_from_file_location(
        'detection', BACKEND / 'blueprints' / 'import_unified' / 'detection.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def iter_archives(backup_root=BACKUP_ROOT):
    backup_root = Path(backup_root)
    roots = [backup_root / 'uploads' / 'posts', backup_root / 'post_zips']
    for root in roots:
        if not root.exists():
            continue
        for p in sorted(root.rglob('*')):
            if not (p.is_file() and p.suffix.lower() in ('.zip', '.7z')):
                continue
            if '__MACOSX' in p.parts or p.name.startswith('._'):
                continue
            yield p


def run_archives(detection, backup_root=BACKUP_ROOT, limit=0):
    results = []
    counts = Counter()
    backup_root = Path(backup_root)
    archives = list(iter_archives(backup_root))
    if limit:
        archives = archives[:limit]
    print(f'classifying {len(archives)} archives...')
    for i, p in enumerate(archives, 1):
        try:
            r = detection.detect_content_type(str(p))
        except Exception as e:
            r = {'type': 'ERROR', 'confidence': '-', 'candidates': [],
                 'detail': {'error': str(e)}}
        counts[r['type']] += 1
        try:
            display_path = str(p.relative_to(backup_root))
        except ValueError:
            display_path = str(p)
        results.append({
            'file': display_path,
            'absolute_path': str(p),
            'type': r['type'],
            'confidence': r['confidence'],
            'candidates': r['candidates'],
            'detail': {k: v for k, v in r['detail'].items()
                       if k not in ('char_infos', 'stage_infos')},
        })
        if i % 25 == 0:
            print(f'  {i}/{len(archives)}')

    print('\n== archive classification ==')
    for t, n in counts.most_common():
        print(f'  {t:<18} {n}')

    print('\n== multi-candidate (ambiguous-ish) ==')
    for r in results:
        if len(r['candidates']) > 1:
            print(f'  {r["type"]:<16} {r["candidates"]}  {r["file"]}')

    print('\n== unknown / nested / error ==')
    for r in results:
        if r['type'] in ('unknown', 'nested_archive', 'ERROR'):
            print(f'  {r["type"]:<16} {r["file"]}  {r["detail"]}')

    return results


# detector short names → website DB names
_CHAR_ALIASES = {
    'c. falcon': 'captain falcon',
    'dk': 'donkey kong',
    'g&w': 'mr. game & watch',
    'game & watch': 'mr. game & watch',
    'ice climbers (nana)': 'ice climbers',
    'ice climbers (popo)': 'ice climbers',
    'puff': 'jigglypuff',
    'ganon': 'ganondorf',
    'doc': 'dr. mario',
    'young link': 'young link',
}


def _norm_char(name):
    n = (name or '').strip().lower()
    return _CHAR_ALIASES.get(n, n)


def run_dats(detection, backup_root=BACKUP_ROOT, sample=300, seed=42):
    pool = ModPool(backup_root)
    rows = [f for f in pool.files.values()
            if f.get('file_type') == 'character_dat'
            and pool.local_exists(f.get('file_url'))]
    random.Random(seed).shuffle(rows)
    rows = rows[:sample]
    print(f'classifying {len(rows)} loose character DATs (of {sample} sampled)...')

    results = []
    counts = Counter()
    char_match = Counter()
    with tempfile.TemporaryDirectory(prefix='detect_pool_') as tmp:
        for i, f in enumerate(rows, 1):
            dat_path = pool.local_path(f['file_url'])
            zip_path = Path(tmp) / f'{f["id"]}.zip'
            with zipfile.ZipFile(zip_path, 'w') as zf:
                zf.write(dat_path, dat_path.name)
            try:
                r = detection.detect_content_type(str(zip_path),
                                                  filename=dat_path.name)
            except Exception as e:
                r = {'type': 'ERROR', 'detail': {'error': str(e)},
                     'candidates': [], 'confidence': '-'}
            counts[r['type']] += 1

            expected_char = _norm_char(f.get('character'))
            detected_chars = [_norm_char(c.get('character'))
                              for c in r['detail'].get('costumes', [])]
            if r['type'] not in ('character', 'character_renamed', 'ic_half'):
                verdict = 'NOT_CHARACTER'
            elif not expected_char:
                verdict = 'no_ground_truth'
            elif r['type'] == 'ic_half':
                verdict = ('match_ic_half' if expected_char == 'ice climbers'
                           else 'CHAR_MISMATCH')
            elif expected_char in detected_chars:
                verdict = ('match' if r['type'] == 'character'
                           else 'match_renamed')
            else:
                verdict = 'CHAR_MISMATCH'
            char_match[verdict] += 1

            results.append({
                'file_id': f['id'], 'dat': dat_path.name,
                'expected': f.get('character'), 'type': r['type'],
                'detected': r['detail'].get('costumes'), 'verdict': verdict,
            })
            zip_path.unlink(missing_ok=True)
            if i % 50 == 0:
                print(f'  {i}/{len(rows)}')

    print('\n== loose DAT classification ==')
    for t, n in counts.most_common():
        print(f'  {t:<18} {n}')
    print('\n== ground-truth comparison ==')
    for v, n in char_match.most_common():
        print(f'  {v:<18} {n}')
    print('\n== failures ==')
    for r in results:
        if r['verdict'] in ('NOT_CHARACTER', 'CHAR_MISMATCH'):
            print(f'  {r["verdict"]:<14} expected={r["expected"]!r:<16} '
                  f'got={r["detected"]} ({r["dat"]}, file {r["file_id"]})')

    return results


def run_isos(slippi_root=SLIPPI_ROOT, limit=0):
    slippi_root = Path(slippi_root)
    if not slippi_root.exists():
        raise FileNotFoundError(f'slippi root not found: {slippi_root}')

    isos = [
        p for p in sorted(slippi_root.rglob('*'))
        if p.is_file() and p.suffix.lower() in ('.iso', '.gcm')
        and '.nkit' not in p.name.lower()
    ]
    if limit:
        isos = isos[:limit]

    results = []
    total_bytes = 0
    print(f'found {len(isos)} ISO/GCM files under {slippi_root}')
    for p in isos:
        size = p.stat().st_size
        total_bytes += size
        try:
            display_path = str(p.relative_to(slippi_root))
        except ValueError:
            display_path = str(p)
        entry = {
            'file': display_path,
            'absolute_path': str(p),
            'bytes': size,
            'gib': round(size / (1024 ** 3), 3),
        }
        results.append(entry)
        print(f'  {entry["gib"]:>6.3f} GiB  {display_path}')

    print(f'\nTotal: {round(total_bytes / (1024 ** 3), 3)} GiB')
    print('Use these paths with the app ISO scanner or a targeted backend scan run.')
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['archives', 'dats', 'isos'])
    ap.add_argument('--backup-root', default=str(BACKUP_ROOT))
    ap.add_argument('--slippi-root', default=str(SLIPPI_ROOT))
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--sample', type=int, default=300)
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()

    if args.command == 'archives':
        detection = load_detection()
        results = run_archives(detection, args.backup_root, args.limit)
    elif args.command == 'dats':
        detection = load_detection()
        results = run_dats(detection, args.backup_root, args.sample, args.seed)
    else:
        results = run_isos(args.slippi_root, args.limit)

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    out = ARTIFACTS / f'detect_pool_{args.command}.jsonl'
    with open(out, 'w', encoding='utf-8') as fh:
        for r in results:
            fh.write(json.dumps(r, default=str) + '\n')
    print(f'\nreport: {out}')


if __name__ == '__main__':
    main()
