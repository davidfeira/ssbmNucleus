"""One-off: build the PAIRED Ice Climbers vault skin (Popo + Nana in one zip --
the importer drops solo IC halves by design).

Usage: python scripts/skinlab_mine_ics.py --port <p> --plans my_char_plans.json
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

from skinlab_gauntlet import Lab, execute_steps  # noqa: E402


def build_half(port, character, code, steps):
    lab = Lab(port)
    lab.session = lab.open(character, code)
    try:
        execute_steps(lab, steps)
        r = requests.get(f'{lab.base}/export-dat', timeout=300)
        r.raise_for_status()
        return r.content
    finally:
        lab.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', required=True)
    ap.add_argument('--plans', required=True)
    args = ap.parse_args()

    plans = json.loads(Path(args.plans).read_text(encoding='utf-8'))
    name = 'Ember & Frost (AI Lab)'

    print('Popo half (Ember Climber)...', flush=True)
    popo = build_half(args.port, 'Ice Climbers', 'PlPpNr',
                      plans['Ice Climbers']['steps'])
    print('Nana half (Frostberry)...', flush=True)
    nana = build_half(args.port, 'Nana', 'PlNnNr', plans['Nana']['steps'])

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('PlPpNr.dat', popo)
        z.writestr('PlNnNr.dat', nana)
    buf.seek(0)

    r = requests.post(f'http://127.0.0.1:{args.port}/api/mex/import/file',
                      files={'file': (f'{name}.zip', buf.getvalue(), 'application/zip')},
                      data={'custom_title': name}, timeout=300)
    print(r.status_code, str(r.json())[:300], flush=True)


if __name__ == '__main__':
    main()
