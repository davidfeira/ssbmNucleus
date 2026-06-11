"""Hue-grouped texture summary for a stage stats.json (coarse classification aid).
Usage: python scripts/skinlab_stage_summary.py <stage_dir>
"""
import json
import sys
from pathlib import Path

stats = json.loads((Path(sys.argv[1]) / 'stats.json').read_text(encoding='utf-8'))
groups = {}
for idx, s in sorted(stats.items(), key=lambda kv: int(kv[0])):
    bands = s.get('topHueBands') or []
    if s.get('saturatedPct', 0) < 15 or not bands:
        key = 'GRAY'
    else:
        h = bands[0]['center']
        key = ('red' if h <= 15 else 'orange' if h <= 40 else 'yellow' if h <= 65
               else 'olive' if h <= 95 else 'green' if h <= 150 else 'teal' if h <= 185
               else 'blue' if h <= 250 else 'purple' if h <= 290
               else 'magenta' if h <= 330 else 'red')
        lum = s.get('meanLum', 50)
        key += ' dark' if lum < 35 else (' light' if lum > 70 else '')
    groups.setdefault(key, []).append(f"{idx}({s['size'][0]}x{s['size'][1]})")
for k, v in sorted(groups.items()):
    print(f"{k}: {' '.join(v)}")
