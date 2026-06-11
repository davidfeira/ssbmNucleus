"""Replay the squad's Ice Climbers + Nana plans as PAIRED vault imports
(one zip per model, normal import flow -> linked pair + generated CSP).

Usage: python scripts/skinlab_vault_squad_ics.py --port <p> --confirm <dir>
"""
import argparse
import io
import json
import sys
import zipfile
from pathlib import Path

import requests

SCRIPTS = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS))

from skinlab_collect import slugify  # noqa: E402
from skinlab_gauntlet import Lab, execute_steps  # noqa: E402

MODEL_SHORT = {
    'google/gemini-3-flash-preview': 'gemini-3-flash',
    'openai/gpt-5-mini': 'gpt-5-mini',
}


def build_half(port, character, code, plan):
    lab = Lab(port)
    lab.session = lab.open(character, code)
    try:
        execute_steps(lab, plan['steps'])
        if plan.get('fixes'):
            execute_steps(lab, plan['fixes'])
        r = requests.get(f'{lab.base}/export-dat', timeout=300)
        r.raise_for_status()
        return r.content
    finally:
        lab.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', required=True)
    ap.add_argument('--confirm', required=True)
    args = ap.parse_args()

    confirm = Path(args.confirm)
    ic = json.loads((confirm / slugify('Ice Climbers') / 'results.json')
                    .read_text(encoding='utf-8'))
    nana = json.loads((confirm / slugify('Nana') / 'results.json')
                      .read_text(encoding='utf-8'))

    for model, short in MODEL_SHORT.items():
        ic_plan = (ic.get(model) or {}).get('plan') or {}
        nana_plan = (nana.get(model) or {}).get('plan') or {}
        if not (ic_plan.get('valid') and nana_plan.get('valid')):
            print(f'{short}: missing a valid half, skipping', flush=True)
            continue
        name = f"{ic_plan.get('skin_name', 'IC Duo')} ({short})"
        print(f'=== {short}: "{name}"', flush=True)
        try:
            popo_dat = build_half(args.port, 'Ice Climbers', 'PlPpNr', ic_plan)
            nana_dat = build_half(args.port, 'Nana', 'PlNnNr', nana_plan)
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
                z.writestr('PlPpNr.dat', popo_dat)
                z.writestr('PlNnNr.dat', nana_dat)
            buf.seek(0)
            r = requests.post(f'http://127.0.0.1:{args.port}/api/mex/import/file',
                              files={'file': (f'{name}.zip', buf.getvalue(),
                                              'application/zip')},
                              data={'custom_title': name}, timeout=300)
            body = r.json()
            print(f"  {'vaulted' if body.get('success') else 'FAILED'}:",
                  str(body)[:200], flush=True)
        except Exception as e:
            print(f'  FAILED: {e}', flush=True)


if __name__ == '__main__':
    main()
