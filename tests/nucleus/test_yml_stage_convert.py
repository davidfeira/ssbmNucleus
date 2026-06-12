"""
test_yml_stage_convert.py - verify classic stage.yml packages convert and
install.

Phase A (no Dolphin):
  1. convert 3 real pool packages (Deadline has the full embedded-array case:
     10 map GOBJ functions + 1 moving collision + sound.spk)
  2. import the converted zip through /api/mex/import/file (exercises the
     custom_stage dispatch) into the vault
  3. build a test ISO from it (create temp project -> mexcli add-stage ->
     export) and scan the generated files/MxDt.dat for every map GOBJ
     function address — proof the embedded table survived into the build
  The built ISO is kept at storage/test-builds/zzyml_deadline.iso for phase B.

Phase B (--live, needs Dolphin closed):
  4. boot the ISO and run the standard custom-stage in-game test (select the
     stage on the SSS, sustain a solo match) -> PASS/CRASH verdict.
  5. cleanup (vault entry + ISO) happens after a passing live run, or pass
     --cleanup to force it.

Run:  python tests/nucleus/test_yml_stage_convert.py [--live] [--cleanup]
"""
import io
import json
import shutil
import struct
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / 'backend'))

POOL = Path('D:/ssbm-backup/uploads/posts')
VANILLA = r'D:\Slippi\Super Smash Bros. Melee (USA) (En,Ja) (v1.02).iso'
SLIPPI = r'C:\Users\david\AppData\Roaming\Slippi Launcher\netplay'
KEPT_ISO = REPO_ROOT / 'storage' / 'test-builds' / 'zzyml_deadline.iso'
STATE_FILE = REPO_ROOT / 'storage' / 'test-builds' / 'zzyml_state.json'

SAMPLES = [
    POOL / '2022/05/post_15850/Deadline/Deadline.zip',
    POOL / '2024/11/post_17244/Omega_Battlefield.zip',
    POOL / '2025/04/post_17357/Vs._Andross.zip',
]

import mex_api  # noqa: E402
from stage_yml_converter import convert_stage_yml_zip  # noqa: E402

client = mex_api.app.test_client()


def phase_a():
    from test_build import create_temp_project, place_custom_stage_icon, _export, MEXCLI_PATH
    from mex_bridge import MexManager

    print('== 1. convert ==')
    converted = {}
    for p in SAMPLES:
        new_zip, info = convert_stage_yml_zip(p.read_bytes(), p.stem)
        converted[p.stem] = (new_zip, info)
        print(f'  {p.stem}: {info}')

    deadline_zip, deadline_info = converted['Deadline']
    assert deadline_info['mapGOBJs'] == 10, deadline_info
    assert deadline_info['movingCollisions'] == 1, deadline_info

    print('== 2. vault import via unified endpoint ==')
    resp = client.post('/api/mex/import/file', data={
        'file': (io.BytesIO(deadline_zip), 'zzyml_deadline.zip')},
        content_type='multipart/form-data')
    body = resp.get_json()
    print('  import:', resp.status_code, body)
    assert body.get('success') and body.get('type') == 'custom_stage', body
    slug = body['stage']['slug']

    print('== 3. build + MxDt structural check ==')
    stage_zip = REPO_ROOT / 'storage' / 'custom_stages' / slug / 'stage.zip'
    assert stage_zip.exists()

    with zipfile.ZipFile(io.BytesIO(deadline_zip)) as zf:
        stage_json = json.loads(zf.read('stage.json'))
    gobj_addrs = [g['onCreation'] for g in stage_json['mapGOBJs']]

    proj_dir, proj = create_temp_project(VANILLA, log=lambda m: print('   ', m))
    try:
        mex = MexManager(str(MEXCLI_PATH), str(proj))
        res = mex._run_command('add-stage', str(proj), str(stage_zip))
        print('  add-stage:', res)
        assert res.get('success'), res
        sss_icon = place_custom_stage_icon(mex, res.get('name') or slug)
        KEPT_ISO.parent.mkdir(parents=True, exist_ok=True)
        _export(mex, KEPT_ISO, None, lambda m: print('   ', m))

        mxdt = (proj_dir / 'files' / 'MxDt.dat').read_bytes()
        missing = [hex(a) for a in gobj_addrs
                   if struct.pack('>I', a) not in mxdt]
        found = len(gobj_addrs) - len(missing)
        print(f'  MxDt.dat: {found}/{len(gobj_addrs)} map GOBJ addresses embedded')
        assert not missing, f'missing from MxDt: {missing}'

        # moving collision: lineID 0, gobjID 3 -> 0000 0003 xxxx near the table
        mc = struct.pack('>hh', 0, 3)
        print(f'  MxDt.dat: moving-collision pattern present: {mc in mxdt}')

        STATE_FILE.write_text(json.dumps({
            'slug': slug, 'name': res.get('name'), 'sssIcon': sss_icon}))
        print(f'\nPHASE A OK — ISO kept at {KEPT_ISO}')
        print('run with --live (Dolphin closed) to boot-test it')
    finally:
        shutil.rmtree(proj_dir, ignore_errors=True)


def phase_b():
    from ingame.runner import run_test

    state = json.loads(STATE_FILE.read_text())
    print(f"== 4. live in-game test of '{state['name']}' ==")
    runs_root = REPO_ROOT / 'storage' / 'test-runs'
    runs_root.mkdir(parents=True, exist_ok=True)

    result = run_test(
        iso_path=str(KEPT_ISO), slippi_path=SLIPPI, runs_root=str(runs_root),
        manifest={'customStage': {'name': state['name'],
                                  'sssIcon': state['sssIcon']}},
        emit=lambda s, p, m: print(f'  [{s} {p}%] {m}'),
        log=lambda m: print(f'  {m}'),
    )
    print('\nverdict:', result.get('verdict'), '| pass:', result.get('pass'),
          '| reason:', result.get('reason'))
    for c in result.get('checks', []):
        print('  check:', c)
    if result.get('pass'):
        cleanup()
    sys.exit(0 if result.get('pass') else 1)


def cleanup():
    print('== cleanup ==')
    if STATE_FILE.exists():
        slug = json.loads(STATE_FILE.read_text())['slug']
        r = client.post(f'/api/mex/custom-stages/{slug}/delete')
        print(f'  deleted vault stage {slug}:', r.status_code)
        STATE_FILE.unlink()
    KEPT_ISO.unlink(missing_ok=True)


if __name__ == '__main__':
    if '--cleanup' in sys.argv:
        cleanup()
    elif '--live' in sys.argv:
        phase_b()
    else:
        phase_a()
