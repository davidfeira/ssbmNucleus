"""Build MY character skins into the vault: execute each hand-written plan on
the character's vanilla costume, render the review sheet, and save via the
skin-lab /save intake (name "(AI Lab)" suffixed).

Resumable: skips characters whose vault folder already has a zip whose name
starts with the plan's skin name.

Usage:
  python scripts/skinlab_mine_chars.py --port <p> --plans my_char_plans.json \
      [--only Marth,Samus] [--sheets <dir>]
"""
import argparse
import json
import sys
from pathlib import Path

import requests

SCRIPTS = Path(__file__).parent
REPO = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from skinlab_collect import ROSTER  # noqa: E402
from skinlab_gauntlet import Lab, capture_review_sheet, execute_steps  # noqa: E402

NR = {name: code for name, code in ROSTER}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', required=True)
    ap.add_argument('--plans', required=True)
    ap.add_argument('--only', default='')
    ap.add_argument('--sheets', default=str(REPO.parent / 'gauntlet_out' / 'my_chars'))
    args = ap.parse_args()

    plans = json.loads(Path(args.plans).read_text(encoding='utf-8'))
    only = {s.strip() for s in args.only.split(',') if s.strip()}
    sheets_dir = Path(args.sheets)
    sheets_dir.mkdir(parents=True, exist_ok=True)
    failures = []

    for character, plan in plans.items():
        if only and character not in only:
            continue
        name = f"{plan['name']} (AI Lab)"
        vault = REPO / 'storage' / character
        if vault.exists() and any(z.name.startswith(plan['name'])
                                  for z in vault.glob('*.zip')):
            print(f'{character}: "{plan["name"]}" already in the vault, skipping',
                  flush=True)
            continue
        print(f'=== {character}: "{plan["name"]}"', flush=True)
        lab = Lab(args.port)
        try:
            lab.session = lab.open(character, NR[character])
            execute_steps(lab, plan['steps'])
            sheet, _ = capture_review_sheet(lab)
            slug = character.replace(' ', '_').replace('.', '')
            (sheets_dir / f'{slug}.jpg').write_bytes(sheet)
            r = requests.post(f'{lab.base}/save', json={'name': name},
                              timeout=600).json()
            if not r.get('success'):
                raise RuntimeError(r.get('error') or 'save failed')
            print(f'  vaulted: {name}', flush=True)
        except Exception as e:
            failures.append(character)
            print(f'  FAILED {character}: {e}', flush=True)
        finally:
            try:
                lab.close()
            except Exception:
                pass
    print('done. failures:', failures or 'none', flush=True)


if __name__ == '__main__':
    main()
