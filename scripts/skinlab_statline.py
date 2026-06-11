"""One-line-per-index summary of a mapping stats.json for classification.

Usage: python scripts/skinlab_statline.py <mapping_dir/char>
"""
import json
import sys
from pathlib import Path

HUE_NAMES = [(15, 'red'), (40, 'orange'), (65, 'yellow'), (95, 'olive'),
             (150, 'green'), (185, 'teal'), (250, 'blue'), (290, 'purple'),
             (330, 'magenta'), (360, 'red')]


def hue_name(h):
    for limit, name in HUE_NAMES:
        if h <= limit:
            return name
    return 'red'


stats = json.loads((Path(sys.argv[1]) / 'stats.json').read_text(encoding='utf-8'))
for idx, s in sorted(stats.items(), key=lambda kv: int(kv[0])):
    hues = ' '.join(f"{hue_name(b['center'])}{b['center']}:{int(b['share'] * 100)}%"
                    for b in s.get('topHueBands', []))
    gray = 'GRAY' if s.get('saturatedPct', 0) < 15 else ''
    vis = f"F{s.get('visible_front', 0):>6} B{s.get('visible_back', 0):>6}"
    hidden = 'HIDDEN' if (s.get('visible_front', 0) + s.get('visible_back', 0)) < 50 else ''
    print(f"#{idx:>3} {s['size'][0]:>3}x{s['size'][1]:<3} sat{s.get('meanSat', 0):>5} "
          f"lum{s.get('meanLum', 0):>5} {vis} {gray}{hidden} {hues}")
