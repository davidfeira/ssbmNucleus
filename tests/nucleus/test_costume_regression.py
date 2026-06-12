"""
test_costume_regression.py - verify a normal costume zip still flows through
phase 1 of /api/mex/import/file after the phase-0 dispatch was added
(slippi dialog -> import -> CSP generation -> delete again).

Run:  python tests/nucleus/test_costume_regression.py [pool_zip_path]
"""
import io
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / 'backend'))

import mex_api  # noqa: E402
from core.metadata import load_metadata  # noqa: E402

client = mex_api.app.test_client()

# a small single-costume zip from the pool mirror (Fox PlFxNr variant)
DEFAULT_ZIP = Path('D:/ssbm-backup/uploads/posts/2024/07/post_17121/Soapshoe Sonic')  # placeholder


def skins_for(character):
    meta = load_metadata(default={'characters': {}})
    return {s['id'] for s in meta.get('characters', {}).get(character, {}).get('skins', [])}


def main():
    zip_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if not zip_path or not zip_path.exists():
        sys.exit('pass a costume zip path from the pool')

    def post(**form):
        data = {'file': (io.BytesIO(zip_path.read_bytes()), zip_path.name)}
        data.update(form)
        r = client.post('/api/mex/import/file', data=data,
                        content_type='multipart/form-data')
        return r.status_code, r.get_json()

    status, body = post()
    print('first response:', status, {k: body.get(k) for k in ('success', 'type', 'message')})

    if body.get('type') == 'slippi_dialog':
        print('slippi dialog shown (phase 1 intact); importing as-is...')
        status, body = post(slippi_action='import_as_is')
        print('second response:', status, {k: body.get(k) for k in ('success', 'type', 'message')})
    if body.get('type') == 'duplicate_dialog':
        print('duplicate dialog shown (phase 1 + dup detection intact). done, no cleanup needed.')
        return

    assert body.get('success') and body.get('type') == 'character', body
    costumes = body.get('costumes') or []
    print('imported:', costumes)

    # delete what we just imported
    for c in costumes:
        char = c['character']
        meta = load_metadata(default={'characters': {}})
        skins = meta.get('characters', {}).get(char, {}).get('skins', [])
        # newest skin = last in list
        if not skins:
            continue
        skin_id = skins[-1]['id']
        r = client.post('/api/mex/storage/costumes/delete',
                        json={'character': char, 'skinId': skin_id})
        print(f'deleted {char}/{skin_id}:', r.status_code, r.get_json().get('success'))

    print('costume regression OK')


if __name__ == '__main__':
    main()
