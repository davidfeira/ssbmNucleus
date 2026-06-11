"""Stage texture collector: contact sheet + stats from a --stage-textures
export directory (no viewer session; stages can't render in HSD anyway).

Usage:
  python scripts/skinlab_stage_collect.py <export_dir>
Writes contact.png + stats one-liners to stdout.
"""
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from skinlab_collect import texture_stats  # noqa: E402

HUE_NAMES = [(15, 'red'), (40, 'orange'), (65, 'yellow'), (95, 'olive'),
             (150, 'green'), (185, 'teal'), (250, 'blue'), (290, 'purple'),
             (330, 'magenta'), (360, 'red')]


def hue_name(h):
    for limit, name in HUE_NAMES:
        if h <= limit:
            return name
    return 'red'


def main():
    export_dir = Path(sys.argv[1])
    manifest = json.loads((export_dir / 'manifest.json').read_text(encoding='utf-8'))
    entries = manifest['textures']

    cell, cols = 112, 7
    rows = (len(entries) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cell, rows * (cell + 16)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    stats = {}
    for n, e in enumerate(entries):
        img = Image.open(export_dir / e['filename'])
        stats[e['index']] = {**texture_stats(img), 'group': e['group'],
                             'format': e['format']}
        thumb = img.convert('RGB')
        thumb.thumbnail((cell - 8, cell - 8), Image.NEAREST)
        x, y = (n % cols) * cell, (n // cols) * (cell + 16)
        sheet.paste(thumb, (x + 4, y + 16))
        draw.text((x + 4, y + 2), f"#{e['index']} g{e['group']}", fill=(255, 255, 80))
    sheet.save(export_dir.parent / 'contact.png')
    (export_dir.parent / 'stats.json').write_text(json.dumps(stats, indent=1),
                                                  encoding='utf-8')

    for idx, s in stats.items():
        hues = ' '.join(f"{hue_name(b['center'])}{b['center']}:{int(b['share'] * 100)}%"
                        for b in s.get('topHueBands', []))
        gray = 'GRAY' if s.get('saturatedPct', 0) < 15 else ''
        print(f"#{idx:>3} g{s['group']} {s['size'][0]:>3}x{s['size'][1]:<3} "
              f"{s['format']:<7} sat{s.get('meanSat', 0):>5} lum{s.get('meanLum', 0):>5} "
              f"{gray} {hues}")
    print('contact ->', export_dir.parent / 'contact.png')


if __name__ == '__main__':
    main()
