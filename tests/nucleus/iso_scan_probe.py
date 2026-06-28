#!/usr/bin/env python3
"""Run the ISO scanner against a real local ISO corpus and write a JSON report."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _iter_isos(root: Path):
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        if path.suffix.lower() not in ('.iso', '.gcm'):
            continue
        name = path.name.lower()
        if name.endswith('.nkit.iso') or '.nkit.' in name:
            continue
        yield path


def _select_isos(args) -> list[Path]:
    if args.iso:
        paths = [Path(p).resolve() for p in args.iso]
    else:
        paths = list(_iter_isos(Path(args.slippi_root)))
        if args.match:
            needle = args.match.lower()
            paths = [p for p in paths if needle in str(p).lower()]
    paths = sorted(paths, key=lambda p: str(p).lower())
    if args.limit:
        paths = paths[:args.limit]
    missing = [str(p) for p in paths if not p.exists()]
    if missing:
        raise SystemExit(f"Missing ISO path(s): {missing}")
    if not paths:
        raise SystemExit("No ISO/GCM files selected")
    return paths


def _load_scanner(args):
    if args.parallelism is not None:
        os.environ['MEX_CSP_PARALLELISM'] = str(args.parallelism)
    if args.stagger is not None:
        os.environ['MEX_CSP_LAUNCH_STAGGER'] = str(args.stagger)

    backend_dir = _repo_root() / 'backend'
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    import iso_scanner  # noqa: PLC0415

    return iso_scanner


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('iso', nargs='*', help='Explicit ISO/GCM path(s) to scan')
    parser.add_argument('--slippi-root', default=r'D:\Slippi', help='Corpus root when no explicit ISO is provided')
    parser.add_argument('--match', help='Substring filter for auto-selected ISO paths')
    parser.add_argument('--limit', type=int, help='Maximum number of auto-selected ISOs')
    parser.add_argument('--parallelism', type=int, help='Override MEX_CSP_PARALLELISM for this run')
    parser.add_argument('--stagger', type=float, help='Override MEX_CSP_LAUNCH_STAGGER for this run')
    parser.add_argument('--keep-work', action='store_true', help='Keep extracted/rendered scanner work dir')
    parser.add_argument('--out', help='Report path; defaults to tests/artifacts/nucleus/iso_scan_probe_<job>.json')
    args = parser.parse_args()

    repo = _repo_root()
    selected = _select_isos(args)
    iso_scanner = _load_scanner(args)

    job_id = f"probe_{int(time.time())}"
    work_dir = iso_scanner.SCAN_WORK_ROOT / job_id
    work_dir.mkdir(parents=True, exist_ok=True)
    job = iso_scanner.IsoScanJob(
        job_id=job_id,
        iso_paths=[str(p) for p in selected],
        work_dir=work_dir,
    )

    events = []

    def on_event(name, payload):
        events.append({'name': name, 'payload': payload})
        if name == 'iso_scan_progress':
            print(f"{payload.get('percent', 0):3}% {payload.get('phase')}: {payload.get('message')}")

    print(f"Scanning {len(selected)} ISO(s):")
    for path in selected:
        print(f"  {path}")

    iso_scanner._run_scan(job, on_event)

    report = job.to_dict(f"probe://{job.job_id}")
    report.update({
        'iso_paths': [str(p) for p in selected],
        'work_dir': str(work_dir),
        'events': events,
    })

    out = Path(args.out) if args.out else repo / 'tests' / 'artifacts' / 'nucleus' / f'iso_scan_probe_{job_id}.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f"Report: {out}")
    print(f"Status: {job.status}; total_new={report['total_new']}; stats={job.stats}")
    if job.preview_failures:
        print("Preview failures:")
        for failure in job.preview_failures:
            print(f"  {failure['character']} {failure['costume_code']}: {failure['status']}")

    if not args.keep_work:
        root = iso_scanner.SCAN_WORK_ROOT.resolve()
        target = work_dir.resolve()
        if target.parent == root and target.name.startswith('probe_'):
            shutil.rmtree(target, ignore_errors=True)

    return 0 if job.status == 'complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
