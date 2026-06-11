"""Replay the cheap-squad confirmation plans into the vault, one skin per
model per character, named "<skin name> (<model>)".

Materials are cached by prompt hash from the original runs, so replays are
fast. Ice Climbers + Nana are skipped (solo IC halves can't be imported).

Resumable: skips skins already in the character's vault folder.

Usage:
  python scripts/skinlab_vault_squad.py --port <p> \
      --confirm C:/path/gauntlet_out/confirm [--only Marth,Fox]
"""
import argparse
import json
import re
import sys
from pathlib import Path

import requests

SCRIPTS = Path(__file__).parent
REPO = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from skinlab_collect import ROSTER, slugify  # noqa: E402
from skinlab_gauntlet import Lab, execute_steps  # noqa: E402

NR = {name: code for name, code in ROSTER}
MODEL_SHORT = {
    'google/gemini-3-flash-preview': 'gemini-3-flash',
    'openai/gpt-5-mini': 'gpt-5-mini',
}
SKIP = {'Ice Climbers', 'Nana'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', required=True)
    ap.add_argument('--confirm', required=True)
    ap.add_argument('--only', default='')
    args = ap.parse_args()

    only = {s.strip() for s in args.only.split(',') if s.strip()}
    confirm = Path(args.confirm)
    failures = []

    for character, code in ROSTER:
        if character in SKIP or (only and character not in only):
            continue
        results_path = confirm / slugify(character) / 'results.json'
        if not results_path.exists():
            continue
        results = json.loads(results_path.read_text(encoding='utf-8'))
        for model, info in results.items():
            plan = (info or {}).get('plan') or {}
            if not plan.get('valid') or not plan.get('steps'):
                continue
            short = MODEL_SHORT.get(model, re.sub(r'[^\w.-]', '_', model))
            skin_name = (plan.get('skin_name') or 'AI Skin').strip()
            name = f'{skin_name} ({short})'
            vault = REPO / 'storage' / character
            if vault.exists() and any(z.name.startswith(name[:40])
                                      for z in vault.glob('*.zip')):
                print(f'{character} / {short}: already vaulted, skipping', flush=True)
                continue
            print(f'=== {character} / {short}: "{skin_name}"', flush=True)
            lab = Lab(args.port)
            try:
                lab.session = lab.open(character, code)
                execute_steps(lab, plan['steps'])
                if plan.get('fixes'):
                    execute_steps(lab, plan['fixes'])
                r = requests.post(f'{lab.base}/save', json={'name': name},
                                  timeout=600).json()
                if not r.get('success'):
                    raise RuntimeError(r.get('error') or 'save failed')
                print(f'  vaulted: {name}', flush=True)
            except Exception as e:
                failures.append(f'{character}/{short}')
                print(f'  FAILED: {e}', flush=True)
            finally:
                try:
                    lab.close()
                except Exception:
                    pass
    print('done. failures:', failures or 'none', flush=True)


if __name__ == '__main__':
    main()
