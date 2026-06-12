"""
test_screenshot_backfill.py - LIVE end-to-end test of the import-time stage
screenshot backfill: imports a screenshot-less Battlefield variant through
/api/mex/import/file, waits for the background worker to build the one-skin
ISO, boot Dolphin, capture the stage, and save the preview — then deletes the
test variant.

Boots a real (throwaway) Dolphin window for ~a minute. Windows only.

Run:  python tests/nucleus/test_screenshot_backfill.py
"""
import io
import sys
import time
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / 'backend'))

VANILLA = r'D:\Slippi\Super Smash Bros. Melee (USA) (En,Ja) (v1.02).iso'
SLIPPI = r'C:\Users\david\AppData\Roaming\Slippi Launcher\netplay'
SOURCE_VARIANT = REPO_ROOT / 'storage' / 'das' / 'battlefield' / 'art-deco-b.zip'
TIMEOUT_S = 8 * 60

import mex_api  # noqa: E402
from core.metadata import load_metadata  # noqa: E402

client = mex_api.app.test_client()


def find_variant(stage_folder, variant_id):
    meta = load_metadata(default={'stages': {}})
    for v in meta.get('stages', {}).get(stage_folder, {}).get('variants', []):
        if v['id'] == variant_id:
            return v
    return None


def main():
    # 1. build a screenshot-less stage zip from an existing variant's dat
    with zipfile.ZipFile(SOURCE_VARIANT) as zf:
        dat_name = next(n for n in zf.namelist()
                        if n.lower().endswith(('.dat', '.usd')))
        dat_data = zf.read(dat_name)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr(dat_name, dat_data)
    test_zip = buf.getvalue()
    print(f'test zip: {dat_name} only ({len(dat_data)} bytes), no screenshot')

    # 2. import it (it's a hash-duplicate of the source variant -> force)
    data = {'file': (io.BytesIO(test_zip), 'zzbackfill.zip'),
            'duplicate_action': 'import_anyway',
            'vanillaIsoPath': VANILLA,
            'slippiDolphinPath': SLIPPI}
    resp = client.post('/api/mex/import/file', data=data,
                       content_type='multipart/form-data')
    body = resp.get_json()
    print('import response:', resp.status_code, body)
    assert body.get('success') and body.get('type') == 'stage', body
    assert body.get('screenshot_backfill'), 'backfill was not queued!'
    variant_id = body['screenshot_backfill'][0]
    stage_folder = 'battlefield'

    v = find_variant(stage_folder, variant_id)
    assert v and not v.get('has_screenshot'), v
    print(f'variant {variant_id} imported without screenshot; waiting for backfill...')

    # 3. wait for the worker (ISO build + Dolphin boot + capture)
    t0 = time.time()
    ok = False
    while time.time() - t0 < TIMEOUT_S:
        v = find_variant(stage_folder, variant_id)
        if v and v.get('has_screenshot'):
            ok = True
            break
        time.sleep(5)
        print(f'  ...{int(time.time() - t0)}s')

    shot = REPO_ROOT / 'storage' / 'das' / stage_folder / f'{variant_id}_screenshot.png'
    if ok:
        size = shot.stat().st_size if shot.exists() else 0
        print(f'BACKFILL OK after {int(time.time() - t0)}s — {shot} ({size} bytes)')
        assert size > 20_000, f'screenshot suspiciously small: {size}'
    else:
        print('BACKFILL TIMED OUT')

    # 4. cleanup
    r = client.post('/api/mex/storage/stages/delete',
                    json={'stageFolder': stage_folder, 'variantId': variant_id})
    print('cleanup:', r.status_code, r.get_json())

    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
