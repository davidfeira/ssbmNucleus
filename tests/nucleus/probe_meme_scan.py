"""
probe_meme_scan.py - reproduce the MEME WIP scan against the running backend
and identify exactly which files the 'blank' candidates are, plus how blank
their CSP renders actually are. Read-only: imports nothing, deletes the job.
"""
import hashlib
import io
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

API = 'http://127.0.0.1:5000/api/mex'
ISO = r'D:\Slippi\extra\MEME WIP.iso'
PROBE_DIR = Path(os.environ['TEMP']) / 'meme_probe'

from PIL import Image  # noqa: E402


def post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json'})
    return json.load(urllib.request.urlopen(req))


def get(url):
    return json.load(urllib.request.urlopen(url))


def main():
    # map of hash prefix -> extracted filename for identification
    by_prefix = {}
    for p in PROBE_DIR.rglob('*.dat'):
        h = hashlib.md5(p.read_bytes()).hexdigest()
        by_prefix[h[:12]] = (p.name, p.stat().st_size)

    r = post(f'{API}/iso-scan/start', {'iso_paths': [ISO]})
    assert r.get('success'), r
    job_id = r['job_id']
    print('job:', job_id)

    while True:
        j = get(f'{API}/iso-scan/{job_id}')
        if j.get('status') in ('complete', 'error', 'cancelled'):
            break
        time.sleep(3)

    print('status:', j['status'], '| stats:', j.get('stats'))
    for char, skins in (j.get('characters') or {}).items():
        for s in skins:
            fname, size = by_prefix.get(s['dat_hash'], ('?', 0))
            cover = '?'
            if s.get('csp_url'):
                try:
                    png = urllib.request.urlopen(
                        f"http://127.0.0.1:5000{s['csp_url']}").read()
                    img = Image.open(io.BytesIO(png)).convert('RGBA')
                    px = list(img.getdata())
                    visible = sum(1 for p in px if p[3] > 16)
                    cover = f'{100 * visible / len(px):.1f}% px visible'
                except Exception as e:
                    cover = f'csp fetch failed: {e}'
            print(f'  {char:8} code={s["costume_code"]:10} hash={s["dat_hash"]} '
                  f'file={fname:18} size={size:>7}  render: {cover}')

    urllib.request.urlopen(
        urllib.request.Request(f'{API}/iso-scan/{job_id}', method='DELETE'))
    print('job deleted')


if __name__ == '__main__':
    main()
