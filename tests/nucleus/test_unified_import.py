"""
test_unified_import.py - in-process verification of the extended
/api/mex/import/file dispatch (no live backend needed; uses Flask test client).

Covers the new phase-0 package dispatch (custom character / custom stage /
bundle / .ssbm / mex_stage_yml) and the phase-5 diagnosis messages
(character_renamed / ic_half / unsupported_audio / dolphin_textures), then
cleans every imported test entry back out of the dev vault.

Run:  python tests/nucleus/test_unified_import.py
"""
import io
import json
import shutil
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / 'backend'))

POOL = Path('D:/ssbm-backup/uploads/posts')

import mex_api  # noqa: E402  (builds the Flask app at import time)

client = mex_api.app.test_client()

PASS, FAIL = [], []


def check(name, cond, info=''):
    (PASS if cond else FAIL).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name}  {info}")


def post_file(file_bytes, filename, **form):
    data = {'file': (io.BytesIO(file_bytes), filename)}
    data.update(form)
    resp = client.post('/api/mex/import/file', data=data,
                       content_type='multipart/form-data')
    return resp.status_code, resp.get_json()


def make_zip(entries):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        for name, payload in entries.items():
            zf.writestr(name, payload)
    return buf.getvalue()


# tiny valid 1x1 png
PNG = bytes.fromhex(
    '89504e470d0a1a0a0000000d4948445200000001000000010806000000'
    '1f15c4890000000d49444154789c626001000000ffff03000006000557'
    'bfabd40000000049454e44ae426082')


def main():
    print('== phase 0: package dispatch ==')

    # custom character package
    fighter_zip = make_zip({
        'fighter.json': json.dumps({'name': 'ZZ Detection Test Char',
                                    'costumes': [{}, {}]}),
        'icon.png': PNG,
        'PlXxNr.dat': b'\x00' * 64,
    })
    status, body = post_file(fighter_zip, 'zz_test_char.zip')
    check('custom_character import', status == 200 and body.get('type') == 'custom_character',
          f"status={status} body={body}")
    char_slug = (body.get('character') or {}).get('slug')

    # custom stage package
    stage_zip = make_zip({
        'stage.json': json.dumps({'name': 'ZZ Detection Test Stage'}),
        'GrZz.dat': b'\x00' * 64,
        'icon.png': PNG,
    })
    status, body = post_file(stage_zip, 'zz_test_stage.zip')
    check('custom_stage import', status == 200 and body.get('type') == 'custom_stage',
          f"status={status} body={body}")
    stage_slug = (body.get('stage') or {}).get('slug')

    # bundle via .ssbm extension
    bundle_bytes = make_zip({
        'manifest.json': json.dumps({'name': 'ZZ Test Bundle', 'description': ''}),
        'textures/a.png': PNG,
    })
    status, body = post_file(bundle_bytes, 'zz_test_bundle.ssbm')
    check('.ssbm bundle import', status == 200 and body.get('type') == 'bundle',
          f"status={status} body={body}")
    bundle_id = body.get('bundle_id')

    # bundle via zip markers (manifest + textures/)
    status, body = post_file(bundle_bytes, 'zz_test_bundle2.zip')
    check('zip bundle import', status == 200 and body.get('type') == 'bundle',
          f"status={status} body={body}")
    bundle_id2 = body.get('bundle_id')

    # bare .xdelta
    status, body = post_file(b'\xd6\xc3\xc4\x00fakepatch', 'zz_test_patch.xdelta')
    check('bare .xdelta import', status == 200 and body.get('type') == 'patch',
          f"status={status} body={body}")
    patch_ids = [p['id'] for p in (body.get('patches') or [])]

    # mex stage.yml package → recognized, clear refusal
    yml_zip = make_zip({'stage.yml': 'name: x', 'grzz.dat': b'\x00' * 64})
    status, body = post_file(yml_zip, 'zz_yml_stage.zip')
    check('mex_stage_yml message', status == 400 and body.get('type') == 'mex_stage_yml',
          f"status={status} body={body}")

    print('== phase 5: diagnosis messages (real pool files) ==')

    # NOTE: renamed costume dats (e.g. lucinablack.zip) now import through
    # phase 1 via the content fallback in detect_character_from_zip —
    # covered by test_costume_regression.py. character_renamed survives only
    # as a safety net.
    samples = {
        'ic_half': POOL / '2022/10/post_16109/Popo Animelee Recolor.zip',
        'unsupported_audio': POOL / '2022/01/post_15594/Music pack.zip',
        'dolphin_textures': POOL / '2020/09/post_13977/Blue Space CSS HQ Background for Dolphin.zip',
    }
    for expected_type, path in samples.items():
        if not path.exists():
            check(f'{expected_type} (sample missing)', False, str(path))
            continue
        status, body = post_file(path.read_bytes(), path.name)
        check(expected_type,
              status == 400 and body.get('type') == expected_type and body.get('error'),
              f"status={status} type={body.get('type')} error={str(body.get('error'))[:90]}")

    print('== cleanup ==')
    from core.config import STORAGE_PATH

    if char_slug:
        from blueprints import custom_characters as cc
        meta = cc._read_metadata()
        meta['custom_characters'] = [c for c in meta['custom_characters']
                                     if c['slug'] != char_slug]
        cc._write_metadata(meta)
        shutil.rmtree(cc.CUSTOM_CHARACTERS_PATH / char_slug, ignore_errors=True)
        print(f'  removed custom character {char_slug}')

    if stage_slug:
        from blueprints import custom_stages as cs
        meta = cs._read_metadata()
        meta['custom_stages'] = [s for s in meta['custom_stages']
                                 if s.get('slug') != stage_slug]
        cs._write_metadata(meta)
        shutil.rmtree(cs.CUSTOM_STAGES_PATH / stage_slug, ignore_errors=True)
        print(f'  removed custom stage {stage_slug}')

    from blueprints.bundles import load_bundle_metadata, save_bundle_metadata, BUNDLE_PATH
    bundles = load_bundle_metadata()
    keep = [b for b in bundles if b['id'] not in (bundle_id, bundle_id2)]
    if len(keep) != len(bundles):
        save_bundle_metadata(keep)
        for bid in (bundle_id, bundle_id2):
            if bid:
                (BUNDLE_PATH / f'{bid}.ssbm').unlink(missing_ok=True)
                (BUNDLE_PATH / f'{bid}.png').unlink(missing_ok=True)
        print(f'  removed test bundles {bundle_id}, {bundle_id2}')

    if patch_ids:
        from blueprints.xdelta import load_xdelta_metadata, save_xdelta_metadata
        patches = load_xdelta_metadata()
        save_xdelta_metadata([p for p in patches if p['id'] not in patch_ids])
        for pid in patch_ids:
            (STORAGE_PATH / 'xdelta' / f'{pid}.xdelta').unlink(missing_ok=True)
            (STORAGE_PATH / 'xdelta' / f'{pid}.png').unlink(missing_ok=True)
        print(f'  removed test patches {patch_ids}')

    print(f'\n{len(PASS)} passed, {len(FAIL)} failed')
    if FAIL:
        print('FAILED:', FAIL)
        sys.exit(1)


if __name__ == '__main__':
    main()
