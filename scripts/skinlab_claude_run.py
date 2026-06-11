"""Execute a hand-written skin plan (Claude's baseline for gauntlet concepts).

Usage:
  python scripts/skinlab_claude_run.py --port 56199 --plan plan.json \
      --out C:/path/out_dir [--character Fox --costume PlFxNr] [--keep-open]

The plan file is the same shape the gauntlet models emit:
  {"skin_name": "...", "steps": [{"op": "composite", ...}, ...]}

Renders the front/back/CSP review sheet to <out>/claude.jpg so the result
drops straight into the comparison page. --keep-open leaves the session up
for follow-up iteration (more steps / save).
"""
import argparse
import json
from pathlib import Path

from skinlab_gauntlet import Lab, capture_review_sheet, execute_steps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', required=True)
    ap.add_argument('--plan', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--character', default='Fox')
    ap.add_argument('--costume', default='PlFxNr')
    ap.add_argument('--name', default='claude')
    ap.add_argument('--keep-open', action='store_true')
    ap.add_argument('--reuse-session', action='store_true',
                    help='apply steps to the already-open session (iteration)')
    args = ap.parse_args()

    plan = json.loads(Path(args.plan).read_text(encoding='utf-8'))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    lab = Lab(args.port)
    if args.reuse_session:
        import requests
        st = requests.get(f'{lab.base}/status', timeout=30).json()
        if not st.get('open'):
            raise SystemExit('no session open to reuse')
        lab.session = st['session']
    else:
        lab.session = lab.open(args.character, args.costume)
    try:
        execute_steps(lab, plan['steps'])
        sheet_bytes, _ = capture_review_sheet(lab)
        path = out_dir / f'{args.name}.jpg'
        path.write_bytes(sheet_bytes)
        print('sheet ->', path)
    finally:
        if not args.keep_open:
            lab.close()


if __name__ == '__main__':
    main()
