import io
import json
import sys
import zipfile
from pathlib import Path

import pytest
from flask import Flask

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from blueprints import custom_characters as cc_module
from blueprints import custom_stages as cs_module
from blueprints import storage_costumes as sc_module
from core import metadata as core_metadata


def _png_bytes(size=(8, 8), color=(255, 0, 0, 255)):
    from PIL import Image
    img = Image.new('RGBA', size, color)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return buf.getvalue()


def _costume_zip_bytes(dat_name='PlXxGr.dat', with_assets=True):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr(dat_name, b'\x00' * 64)
        if with_assets:
            zf.writestr('csp.png', _png_bytes())
            zf.writestr('stc.png', _png_bytes(size=(4, 4)))
    return buf.getvalue()


def _make_fighter_zip(costume_dats=('PlXxNr.dat', 'PlXxBu.dat'), name='Testo', series_id=2):
    """Minimal fighter.zip the way MexFighter.ToPackage lays it out."""
    fighter_json = {
        'name': name,
        'seriesID': series_id,
        'canWallJump': False,
        'costumes': [
            {
                'name': Path(d).stem,
                'colorSmashGroup': 0,
                'file': {'visibilityIndex': i, 'fileName': d, 'jointSymbol': 'TestJoint'},
            }
            for i, d in enumerate(costume_dats)
        ],
        'files': {'fighterDataPath': 'PlXx.dat'},
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr('fighter.json', json.dumps(fighter_json, indent=2))
        zf.writestr('PlXx.dat', b'\x00' * 32)
        for d in costume_dats:
            inner = io.BytesIO()
            with zipfile.ZipFile(inner, 'w') as izf:
                izf.writestr(d, b'\x00' * 64)
                izf.writestr('csp.png', _png_bytes())
                izf.writestr('stc.png', _png_bytes(size=(4, 4)))
            zf.writestr(f'{Path(d).stem}.zip', inner.getvalue())
    return buf.getvalue(), fighter_json


@pytest.fixture
def client(tmp_path, monkeypatch):
    storage = tmp_path / 'storage'
    custom_chars = storage / 'custom_characters'
    custom_chars.mkdir(parents=True)

    monkeypatch.setattr(cc_module, 'STORAGE_PATH', storage)
    monkeypatch.setattr(cc_module, 'CUSTOM_CHARACTERS_PATH', custom_chars)
    monkeypatch.setattr(cc_module, 'METADATA_FILE', storage / 'metadata.json')
    monkeypatch.setattr(cs_module, 'METADATA_FILE', storage / 'metadata.json')
    # canonical-skin endpoints (shared edit stack) resolve through these
    monkeypatch.setattr(core_metadata, 'METADATA_FILE', storage / 'metadata.json')
    monkeypatch.setattr(sc_module, 'STORAGE_PATH', storage)

    # Seed one custom character "Testo" with 2 bundled costumes
    slug = 'testo'
    char_dir = custom_chars / slug
    char_dir.mkdir()
    zip_bytes, fighter_json = _make_fighter_zip()
    (char_dir / 'fighter.zip').write_bytes(zip_bytes)
    (char_dir / 'fighter.json').write_text(json.dumps(fighter_json, indent=2))
    (char_dir / 'csp_0.png').write_bytes(_png_bytes())
    (char_dir / 'csp_1.png').write_bytes(_png_bytes(color=(0, 0, 255, 255)))
    (char_dir / 'stock_0.png').write_bytes(_png_bytes(size=(4, 4)))
    (char_dir / 'stock_1.png').write_bytes(_png_bytes(size=(4, 4)))

    # Seed a canonical character with one skin zip (for copy-from-vault)
    fox_dir = storage / 'Fox'
    fox_dir.mkdir()
    (fox_dir / 'cool-fox.zip').write_bytes(_costume_zip_bytes('PlFxOrMod.dat'))

    metadata = {
        'characters': {
            'Fox': {
                'skins': [
                    {'id': 'cool-fox', 'color': 'Cool Fox', 'filename': 'cool-fox.zip'},
                ]
            }
        },
        'stages': {},
        'custom_stages': [
            {'type': 'folder', 'id': 'folder_aa11', 'name': 'Faves', 'expanded': True},
            {'id': 'stage-1', 'slug': 'stage-1', 'name': 'Stage One'},
        ],
        'custom_characters': [
            {
                'slug': slug,
                'name': 'Testo',
                'source': 'zip',
                'date_added': '2026-06-10T00:00:00',
                'series_id': 2,
                'costume_count': 2,
                'has_css_icon': False,
            }
        ],
    }
    (storage / 'metadata.json').write_text(json.dumps(metadata, indent=2))

    app = Flask(__name__)
    app.register_blueprint(cc_module.custom_characters_bp)
    app.register_blueprint(cs_module.custom_stages_bp)
    app.register_blueprint(sc_module.storage_costumes_bp)
    with app.test_client() as c:
        c.slug = slug
        c.storage = storage
        c.char_dir = char_dir
        yield c


def test_add_and_remove_skin_via_upload(client):
    res = client.post(f'/api/mex/custom-characters/{client.slug}/skins/add', data={
        'file': (io.BytesIO(_costume_zip_bytes('PlXxGr.dat')), 'green.zip'),
        'name': 'Green',
    }, content_type='multipart/form-data')
    assert res.status_code == 200, res.get_json()
    skin = res.get_json()['skin']
    assert skin['color'] == 'Green'   # canonical field for the shared edit stack
    assert skin['name'] == 'Green'    # display alias
    assert skin['has_csp'] is True
    assert skin['dat_name'] == 'PlXxGr.dat'

    skin_zip = client.char_dir / 'skins' / skin['filename']
    assert skin_zip.exists()
    assert (client.char_dir / 'skins' / f"{skin['id']}_csp.png").exists()

    # detail shows it under added_skins
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert len(detail['added_skins']) == 1
    assert detail['added_skins'][0]['csp_url']
    img = client.get(detail['added_skins'][0]['csp_url'])
    assert img.status_code == 200
    img.close()  # release the file handle (Windows) before deleting below

    # remove
    res = client.post(f"/api/mex/custom-characters/{client.slug}/skins/{skin['id']}/remove")
    assert res.get_json()['success'] is True
    assert not skin_zip.exists()
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert detail['added_skins'] == []


def test_add_skin_from_canonical_vault(client):
    res = client.post(f'/api/mex/custom-characters/{client.slug}/skins/add',
                      json={'character': 'Fox', 'skinId': 'cool-fox'})
    assert res.status_code == 200, res.get_json()
    skin = res.get_json()['skin']
    assert skin['name'] == 'Cool Fox'
    assert skin['source_character'] == 'Fox'
    assert skin['dat_name'] == 'PlFxOrMod.dat'

    # copied zip is byte-identical to the canonical skin zip
    copied = (client.char_dir / 'skins' / skin['filename']).read_bytes()
    original = (client.storage / 'Fox' / 'cool-fox.zip').read_bytes()
    assert copied == original


def test_add_skin_rejects_bad_zips(client):
    # no dat inside
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr('readme.txt', 'hi')
    res = client.post(f'/api/mex/custom-characters/{client.slug}/skins/add', data={
        'file': (io.BytesIO(buf.getvalue()), 'bad.zip'),
    }, content_type='multipart/form-data')
    assert res.status_code == 400

    # dat stem too short for MexCostume.FromZip's [4:6] key
    res = client.post(f'/api/mex/custom-characters/{client.slug}/skins/add', data={
        'file': (io.BytesIO(_costume_zip_bytes('Pl.dat')), 'short.zip'),
    }, content_type='multipart/form-data')
    assert res.status_code == 400


def test_bare_dat_upload_gets_wrapped(client):
    res = client.post(f'/api/mex/custom-characters/{client.slug}/skins/add', data={
        'file': (io.BytesIO(b'\x00' * 64), 'PlXxWh.dat'),
    }, content_type='multipart/form-data')
    assert res.status_code == 200, res.get_json()
    skin = res.get_json()['skin']
    assert skin['dat_name'] == 'PlXxWh.dat'
    assert skin['has_csp'] is False
    with zipfile.ZipFile(client.char_dir / 'skins' / skin['filename']) as zf:
        assert zf.namelist() == ['PlXxWh.dat']


def test_remove_bundled_costume_rewrites_zip_and_previews(client):
    res = client.post(f'/api/mex/custom-characters/{client.slug}/costumes/0/remove')
    assert res.status_code == 200, res.get_json()
    assert res.get_json()['costume_count'] == 1

    # storage fighter.json updated
    fighter = json.loads((client.char_dir / 'fighter.json').read_text())
    assert [c['file']['fileName'] for c in fighter['costumes']] == ['PlXxBu.dat']

    # fighter.zip: inner costume zip dropped + embedded fighter.json updated
    with zipfile.ZipFile(client.char_dir / 'fighter.zip') as zf:
        names = zf.namelist()
        assert 'PlXxNr.zip' not in names
        assert 'PlXxBu.zip' in names
        zmeta = json.loads(zf.read('fighter.json'))
        assert len(zmeta['costumes']) == 1

    # csp_1 shifted down to csp_0
    assert (client.char_dir / 'csp_0.png').exists()
    assert not (client.char_dir / 'csp_1.png').exists()

    # can't remove the last costume
    res = client.post(f'/api/mex/custom-characters/{client.slug}/costumes/0/remove')
    assert res.status_code == 400


def test_bundled_costume_to_skin(client):
    res = client.post(f'/api/mex/custom-characters/{client.slug}/costumes/0/to-skin')
    assert res.status_code == 200, res.get_json()
    data = res.get_json()
    assert data['costume_count'] == 1
    skin = data['skin']
    assert skin['dat_name'] == 'PlXxNr.dat'
    assert skin['has_csp'] is True

    # costume gone from fighter.json + fighter.zip, present in skins/
    fighter = json.loads((client.char_dir / 'fighter.json').read_text())
    assert [c['file']['fileName'] for c in fighter['costumes']] == ['PlXxBu.dat']
    with zipfile.ZipFile(client.char_dir / 'fighter.zip') as zf:
        assert 'PlXxNr.zip' not in zf.namelist()
    skin_zip = client.char_dir / 'skins' / skin['filename']
    with zipfile.ZipFile(skin_zip) as zf:
        assert 'PlXxNr.dat' in zf.namelist()

    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert len(detail['costumes']) == 1
    assert len(detail['added_skins']) == 1

    # last bundled costume cannot be moved out
    res = client.post(f'/api/mex/custom-characters/{client.slug}/costumes/0/to-skin')
    assert res.status_code == 400


def test_series_list_and_set_series(client):
    res = client.get('/api/mex/custom-characters/series-list')
    series = res.get_json()['series']
    assert len(series) == 17
    assert series[2]['name'] == 'Star Fox'
    # vanilla icons shipped for 0..15
    assert all(s['icon_url'] for s in series[:16])

    icon = client.get('/api/mex/custom-characters/series-icon/2')
    assert icon.status_code == 200

    res = client.post(f'/api/mex/custom-characters/{client.slug}/set-series', json={'seriesId': 5})
    assert res.get_json()['series_name'] == 'Kirby'

    fighter = json.loads((client.char_dir / 'fighter.json').read_text())
    assert fighter['seriesID'] == 5
    with zipfile.ZipFile(client.char_dir / 'fighter.zip') as zf:
        assert json.loads(zf.read('fighter.json'))['seriesID'] == 5
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert detail['series_id'] == 5 and detail['series_name'] == 'Kirby'

    res = client.post(f'/api/mex/custom-characters/{client.slug}/set-series', json={'seriesId': 99})
    assert res.status_code == 400


def test_rename_updates_fighter_zip(client):
    res = client.post(f'/api/mex/custom-characters/{client.slug}/rename',
                      json={'newName': 'Testo Prime'})
    assert res.get_json()['success'] is True
    with zipfile.ZipFile(client.char_dir / 'fighter.zip') as zf:
        assert json.loads(zf.read('fighter.json'))['name'] == 'Testo Prime'


def _make_scan_project(tmp_path, extra_series=(('Street Fighter', 'series\\icon_017'),)):
    """Fake scanned-project layout: data/series.json + assets/series icons."""
    proj = tmp_path / 'scan_project'
    (proj / 'data').mkdir(parents=True)
    (proj / 'assets' / 'series').mkdir(parents=True)
    series = [{'name': n, 'icon': None, 'model': None} for n in (
        'F-Zero', 'Donkey Kong', 'Star Fox', 'Game & Watch', 'Ice Climber', 'Kirby',
        'Super Mario', 'Fire Emblem', 'EarthBound', 'Pokémon', 'Metroid', 'Smash Bros.',
        'Yoshi', 'The Legend of Zelda', 'Master Hand', 'Crazy Hand', 'Special Stages')]
    for name, icon_ref in extra_series:
        series.append({'name': name, 'icon': icon_ref, 'model': None})
        icon_png = proj / 'assets' / (icon_ref.replace('\\', '/') + '.png')
        icon_png.write_bytes(_png_bytes(size=(80, 64), color=(255, 255, 255, 255)))
    (proj / 'data' / 'series.json').write_text(json.dumps(series), encoding='utf-8')
    return proj


def test_extract_custom_series_from_scan_project(client, tmp_path):
    proj = _make_scan_project(tmp_path)
    cs = cc_module._extract_custom_series(proj, 17, client.char_dir)
    assert cs == {'name': 'Street Fighter', 'source_id': 17, 'active': True, 'has_icon': True}
    assert (client.char_dir / 'series_icon.png').exists()
    # vanilla ids are not "custom"
    assert cc_module._extract_custom_series(proj, 2, client.char_dir) is None
    # out-of-range id in source project -> nothing to extract
    assert cc_module._extract_custom_series(proj, 99, client.char_dir) is None


def test_replace_series_icon_and_activate(client):
    res = client.post(f'/api/mex/custom-characters/{client.slug}/replace-series-icon', data={
        'file': (io.BytesIO(_png_bytes(size=(128, 128))), 'emblem.png'),
    }, content_type='multipart/form-data')
    assert res.status_code == 200, res.get_json()
    cs = res.get_json()['custom_series']
    assert cs['active'] is True
    assert cs['name'] == 'Testo Series'  # default name

    # normalized to the in-game 80x64
    from PIL import Image
    assert Image.open(client.char_dir / 'series_icon.png').size == (80, 64)

    # detail reflects it
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert detail['custom_series']['active'] is True
    assert detail['custom_series']['icon_url']
    icon = client.get(detail['custom_series']['icon_url'])
    assert icon.status_code == 200
    icon.close()

    # rename via set-series-custom
    res = client.post(f'/api/mex/custom-characters/{client.slug}/set-series-custom',
                      json={'name': 'Street Fighter'})
    assert res.get_json()['custom_series']['name'] == 'Street Fighter'

    # picking a vanilla franchise deactivates the custom one
    res = client.post(f'/api/mex/custom-characters/{client.slug}/set-series', json={'seriesId': 6})
    assert res.get_json()['success'] is True
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert detail['custom_series']['active'] is False

    # and it can be reactivated without re-uploading
    res = client.post(f'/api/mex/custom-characters/{client.slug}/set-series-custom', json={})
    assert res.get_json()['custom_series']['active'] is True


def test_resolve_install_series_matches_by_name(client, tmp_path):
    # target project already has the series -> reuse its index, no CLI call
    proj = _make_scan_project(tmp_path)
    (client.char_dir / 'series_icon.png').write_bytes(_png_bytes(size=(80, 64)))
    entry = {'series_id': 19, 'custom_series': {'name': 'Street Fighter', 'active': True}}
    sid, warnings = cc_module._resolve_install_series(
        entry, client.char_dir, proj / 'project.mexproj', 'mexcli-not-needed')
    assert sid == 17
    assert warnings == []


def test_resolve_install_series_clamps_dangling_id(client, tmp_path):
    # no custom series info, seriesID beyond target project's list -> Smash Bros.
    proj = _make_scan_project(tmp_path, extra_series=())
    entry = {'series_id': 19}
    sid, warnings = cc_module._resolve_install_series(
        entry, client.char_dir, proj / 'project.mexproj', 'mexcli-not-needed')
    assert sid == 11
    assert warnings

    # in-range vanilla id is left untouched
    entry = {'series_id': 2}
    sid, warnings = cc_module._resolve_install_series(
        entry, client.char_dir, proj / 'project.mexproj', 'mexcli-not-needed')
    assert sid is None and warnings == []


def test_replace_icon_and_banner_assets(client):
    # add a banner entry to the seeded fighter.zip so it shows up in detail
    cc_module._rewrite_fighter_zip(client.char_dir, replace_entries={
        'big_banner.png': _png_bytes(size=(256, 28)),
    })
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert 'big_banner' in detail['zip_assets']
    assert 'icon' not in detail['zip_assets']  # seeded zip has no icon.png

    banner = client.get(detail['zip_assets']['big_banner']['url'])
    assert banner.status_code == 200
    banner.close()

    # replace the CSS icon: normalized to 64x56, written to zip + vault copy
    res = client.post(f'/api/mex/custom-characters/{client.slug}/replace-asset/icon', data={
        'file': (io.BytesIO(_png_bytes(size=(128, 128), color=(10, 200, 30, 255))), 'icon.png'),
    }, content_type='multipart/form-data')
    assert res.get_json()['success'] is True, res.get_json()

    from PIL import Image
    assert Image.open(client.char_dir / 'css_icon.png').size == (64, 56)
    with zipfile.ZipFile(client.char_dir / 'fighter.zip') as zf:
        assert 'icon.png' in zf.namelist()
        assert Image.open(io.BytesIO(zf.read('icon.png'))).size == (64, 56)

    # banner replace normalizes to 256x28
    res = client.post(f'/api/mex/custom-characters/{client.slug}/replace-asset/big_banner', data={
        'file': (io.BytesIO(_png_bytes(size=(512, 512))), 'banner.png'),
    }, content_type='multipart/form-data')
    assert res.get_json()['success'] is True
    with zipfile.ZipFile(client.char_dir / 'fighter.zip') as zf:
        assert Image.open(io.BytesIO(zf.read('big_banner.png'))).size == (256, 28)

    res = client.post(f'/api/mex/custom-characters/{client.slug}/replace-asset/bogus', data={
        'file': (io.BytesIO(_png_bytes()), 'x.png'),
    }, content_type='multipart/form-data')
    assert res.status_code == 400


def test_wall_jump_and_costume_rename(client):
    res = client.post(f'/api/mex/custom-characters/{client.slug}/set-wall-jump',
                      json={'canWallJump': True})
    assert res.get_json()['can_wall_jump'] is True
    fighter = json.loads((client.char_dir / 'fighter.json').read_text())
    assert fighter['canWallJump'] is True
    with zipfile.ZipFile(client.char_dir / 'fighter.zip') as zf:
        assert json.loads(zf.read('fighter.json'))['canWallJump'] is True

    res = client.post(f'/api/mex/custom-characters/{client.slug}/costumes/1/rename',
                      json={'name': 'Blue Suit'})
    assert res.get_json()['success'] is True
    fighter = json.loads((client.char_dir / 'fighter.json').read_text())
    assert fighter['costumes'][1]['name'] == 'Blue Suit'
    with zipfile.ZipFile(client.char_dir / 'fighter.zip') as zf:
        assert json.loads(zf.read('fighter.json'))['costumes'][1]['name'] == 'Blue Suit'

    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert detail['costumes'][1]['name'] == 'Blue Suit'
    assert detail['can_wall_jump'] is True

    res = client.post(f'/api/mex/custom-characters/{client.slug}/costumes/9/rename',
                      json={'name': 'x'})
    assert res.status_code == 400


def test_detail_extras_based_on_and_counts(client):
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    # seeded joint symbol is 'TestJoint' (no Ply...5K pattern) -> None
    assert detail['based_on'] is None
    assert detail['has_kirby_cap'] is False
    assert detail['costumes'][0]['dat'] == 'PlXxNr.dat'

    # the Ply<Name>5K pattern is what real fighters use
    assert cc_module._based_on_from_joint(
        {'costumes': [{'file': {'jointSymbol': 'PlyZelda5K_Share_joint'}}]}) == 'Zelda'


def test_shared_edit_stack_works_on_custom_skins(client):
    """The canonical skin endpoints (rename / update-csp / csp manage /
    delete) operate on custom-character skins via the pseudo-character key
    'custom_characters/<slug>/skins'."""
    res = client.post(f'/api/mex/custom-characters/{client.slug}/skins/add', data={
        'file': (io.BytesIO(_costume_zip_bytes('PlXxGr.dat')), 'green.zip'),
        'name': 'Green',
    }, content_type='multipart/form-data')
    skin_id = res.get_json()['skin']['id']
    pseudo = f'custom_characters/{client.slug}/skins'

    # rename through the canonical endpoint
    res = client.post('/api/mex/storage/costumes/rename', json={
        'character': pseudo, 'skinId': skin_id, 'newName': 'Emerald'})
    assert res.get_json()['success'] is True, res.get_json()
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert detail['added_skins'][0]['color'] == 'Emerald'
    assert detail['added_skins'][0]['name'] == 'Emerald'

    # CSP replace through the canonical endpoint: updates the loose preview
    # AND the csp.png inside the skin zip
    res = client.post('/api/mex/storage/costumes/update-csp', data={
        'character': pseudo,
        'skinId': skin_id,
        'csp': (io.BytesIO(_png_bytes(color=(0, 0, 255, 255))), 'new.png'),
    }, content_type='multipart/form-data')
    assert res.get_json()['success'] is True, res.get_json()
    skins_dir = client.char_dir / 'skins'
    assert (skins_dir / f'{skin_id}_csp.png').exists()
    with zipfile.ZipFile(skins_dir / f'{skin_id}.zip') as zf:
        assert zf.read('csp.png') == _png_bytes(color=(0, 0, 255, 255))
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert detail['added_skins'][0]['csp_source'] == 'custom'

    # alt CSP management through the canonical endpoint
    res = client.post(f'/api/mex/storage/costumes/{pseudo}/{skin_id}/csp/manage', data={
        'action': 'add',
        'file': (io.BytesIO(_png_bytes(color=(255, 255, 0, 255))), 'alt.png'),
    }, content_type='multipart/form-data')
    body = res.get_json()
    assert body['success'] is True, body
    assert body['url'] == f'/storage/{pseudo}/{skin_id}_csp_alt_1.png'
    assert (skins_dir / f'{skin_id}_csp_alt_1.png').exists()
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert len(detail['added_skins'][0]['alternate_csps']) == 1

    # delete through the canonical endpoint removes files + the entry
    res = client.post('/api/mex/storage/costumes/delete', json={
        'character': pseudo, 'skinId': skin_id})
    assert res.get_json()['success'] is True, res.get_json()
    assert not (skins_dir / f'{skin_id}.zip').exists()
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert detail['added_skins'] == []


def test_get_char_data_resolver(client):
    meta = json.loads((client.storage / 'metadata.json').read_text())
    # canonical
    assert core_metadata.get_char_data(meta, 'Fox') is meta['characters']['Fox']
    # custom pseudo key aliases the added_skins list
    view = core_metadata.get_char_data(meta, f'custom_characters/{client.slug}/skins')
    assert view is not None
    entry = next(c for c in meta['custom_characters'] if c['slug'] == client.slug)
    assert view['skins'] is entry['added_skins']
    # unknown forms
    assert core_metadata.get_char_data(meta, 'custom_characters/nope/skins') is None
    assert core_metadata.get_char_data(meta, 'custom_characters/x/other') is None
    assert core_metadata.get_char_data(meta, 'NotAChar') is None


def test_vanilla_fighter_name_normalization():
    # 'Mr. Game and Watch' in a modded build must still count as vanilla
    for name in ('Mr. Game & Watch', 'Mr. Game and Watch', 'MR. GAME & WATCH',
                 'Mr Game & Watch', 'Captain Falcon', 'C. Falcon', 'Donkey Kong'):
        assert cc_module._norm_fighter_name(name) in cc_module.VANILLA_FIGHTER_NAMES_NORM, name
    for name in ('Chun-Li', 'Wolf', 'Sonic', 'Lucas TDX'):
        assert cc_module._norm_fighter_name(name) not in cc_module.VANILLA_FIGHTER_NAMES_NORM, name


def test_bundled_costume_modal_namespace(client):
    """Bundled costumes open in the shared edit stack directly via the
    'custom_characters/<slug>/costumes' pseudo key — synced costume_meta +
    materialized zips, with edits folded back at install."""
    # detail syncs the mirror
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert [c['edit_id'] for c in detail['costumes']] == ['PlXxNr', 'PlXxBu']
    costumes_dir = client.char_dir / 'costumes'
    assert (costumes_dir / 'PlXxNr.zip').exists()
    assert (costumes_dir / 'PlXxNr_csp.png').exists()

    pseudo = f'custom_characters/{client.slug}/costumes'

    # rename through the canonical endpoint → costume_meta color
    res = client.post('/api/mex/storage/costumes/rename', json={
        'character': pseudo, 'skinId': 'PlXxNr', 'newName': 'Crimson'})
    assert res.get_json()['success'] is True, res.get_json()
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert detail['costumes'][0]['name'] == 'Crimson'

    # CSP replace lands in the materialized zip + preview
    res = client.post('/api/mex/storage/costumes/update-csp', data={
        'character': pseudo,
        'skinId': 'PlXxNr',
        'csp': (io.BytesIO(_png_bytes(color=(0, 255, 255, 255))), 'new.png'),
    }, content_type='multipart/form-data')
    assert res.get_json()['success'] is True, res.get_json()
    with zipfile.ZipFile(costumes_dir / 'PlXxNr.zip') as zf:
        assert zf.read('csp.png') == _png_bytes(color=(0, 255, 255, 255))

    # detail now serves the materialized preview
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert detail['costumes'][0]['csp_url'].endswith('costumes/PlXxNr_csp.png')

    # inline rename endpoint keeps the mirror in sync too
    res = client.post(f'/api/mex/custom-characters/{client.slug}/costumes/0/rename',
                      json={'name': 'Scarlet'})
    assert res.get_json()['success'] is True
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert detail['costumes'][0]['name'] == 'Scarlet'

    # removing the costume prunes the mirror on next sync
    res = client.post(f'/api/mex/custom-characters/{client.slug}/costumes/0/remove')
    assert res.get_json()['success'] is True
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert [c['edit_id'] for c in detail['costumes']] == ['PlXxBu']
    assert not (costumes_dir / 'PlXxNr.zip').exists()


def test_install_zip_folds_costume_edits(client, tmp_path):
    """The temp install zip carries materialized costume edits + renames."""
    pseudo = f'custom_characters/{client.slug}/costumes'
    client.get(f'/api/mex/custom-characters/{client.slug}/detail')  # sync mirror
    client.post('/api/mex/storage/costumes/rename', json={
        'character': pseudo, 'skinId': 'PlXxBu', 'newName': 'Ocean'})
    client.post('/api/mex/storage/costumes/update-csp', data={
        'character': pseudo, 'skinId': 'PlXxBu',
        'csp': (io.BytesIO(_png_bytes(color=(1, 2, 3, 255))), 'new.png'),
    }, content_type='multipart/form-data')

    # replicate the install-time fold-back
    metadata = json.loads((client.storage / 'metadata.json').read_text())
    entry = next(c for c in metadata['custom_characters'] if c['slug'] == client.slug)
    meta_by_id = {m['id']: m for m in entry.get('costume_meta', [])}
    replace_entries = {
        f.name: f.read_bytes()
        for f in (client.char_dir / 'costumes').glob('*.zip')
        if f.stem in meta_by_id
    }
    out = tmp_path / 'install.zip'

    def _mutate(meta):
        for costume in meta.get('costumes', []):
            stem = Path((costume.get('file') or {}).get('fileName') or '').stem
            m = meta_by_id.get(stem)
            if m and m.get('color'):
                costume['name'] = m['color']
        return meta
    cc_module._rewrite_zip_fighter_json(client.char_dir / 'fighter.zip', out,
                                        mutate_json=_mutate, replace_entries=replace_entries)

    with zipfile.ZipFile(out) as zf:
        meta = json.loads(zf.read('fighter.json'))
        assert [c['name'] for c in meta['costumes']][1] == 'Ocean'
        import io as _io
        with zipfile.ZipFile(_io.BytesIO(zf.read('PlXxBu.zip'))) as inner:
            assert inner.read('csp.png') == _png_bytes(color=(1, 2, 3, 255))


def test_victory_theme_extraction_from_scan_project(client, tmp_path):
    proj = _make_scan_project(tmp_path)
    (proj / 'files' / 'audio').mkdir(parents=True)
    (proj / 'files' / 'audio' / 'sf_fanfare.hps').write_bytes(b'HPS-FAKE-DATA')
    music = [{'name': f'Track {i}', 'fileName': f't{i}.hps'} for i in range(20)]
    music[17] = {'name': 'Street Fighter Fanfare', 'fileName': 'sf_fanfare.hps'}
    (proj / 'data' / 'music.json').write_text(json.dumps(music), encoding='utf-8')

    fighter_data = {'victoryTheme': 17, 'announcerCall': 510054}
    updates = cc_module._extract_audio_meta(proj, fighter_data, client.char_dir)
    assert updates['victory_theme'] == {'name': 'Street Fighter Fanfare'}
    assert (client.char_dir / 'victory_theme.hps').read_bytes() == b'HPS-FAKE-DATA'

    # out-of-range victory theme -> nothing extracted
    other_dir = tmp_path / 'other_char'
    other_dir.mkdir()
    assert cc_module._extract_audio_meta(proj, {'victoryTheme': 99}, other_dir) == {}

    # the scan flow persists the updates into the metadata entry
    metadata = json.loads((client.storage / 'metadata.json').read_text())
    entry = next(c for c in metadata['custom_characters'] if c['slug'] == client.slug)
    entry.update(updates)
    (client.storage / 'metadata.json').write_text(json.dumps(metadata, indent=2))

    # detail exposes it
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert detail['victory_theme_info'] == {'name': 'Street Fighter Fanfare', 'available': True}

    # announcer wav (decoded at scan in real flow) is served directly
    (client.char_dir / 'announcer.wav').write_bytes(b'RIFF-FAKE')
    detail = client.get(f'/api/mex/custom-characters/{client.slug}/detail').get_json()['detail']
    assert detail['announcer_available'] is True
    res = client.get(f'/api/mex/custom-characters/{client.slug}/audio/announcer')
    assert res.status_code == 200
    res.close()


def test_stage_playlist_extraction(client, tmp_path):
    proj = _make_scan_project(tmp_path)
    (proj / 'files' / 'audio').mkdir(parents=True)
    (proj / 'files' / 'audio' / 'metal.hps').write_bytes(b'HPS-A')
    (proj / 'files' / 'audio' / 'battle.hps').write_bytes(b'HPS-B')
    music = [{'name': 'Metal Mario Fight', 'fileName': 'metal.hps'},
             {'name': 'Metal Battle', 'fileName': 'battle.hps'}]
    (proj / 'data' / 'music.json').write_text(json.dumps(music), encoding='utf-8')

    stage_data = {'playlist': {'entries': [
        {'musicID': 0, 'chanceToPlay': 75},
        {'musicID': 1, 'chanceToPlay': 50},
        {'musicID': 99, 'chanceToPlay': 10},   # dangling — skipped
    ]}}
    stage_dir = tmp_path / 'stage_vault'
    stage_dir.mkdir()
    updates = cs_module._extract_stage_playlist(proj, stage_data, stage_dir)
    assert updates == {'playlist': [
        {'name': 'Metal Mario Fight', 'chance': 75},
        {'name': 'Metal Battle', 'chance': 50},
    ]}
    assert (stage_dir / 'music_0.hps').read_bytes() == b'HPS-A'
    assert (stage_dir / 'music_1.hps').read_bytes() == b'HPS-B'

    # empty playlist -> no updates
    assert cs_module._extract_stage_playlist(proj, {'playlist': {'entries': []}}, stage_dir) == {}


def test_parse_cli_json_handles_indented_output_with_noise():
    noisy = "Trimmed Image 80 64\nTrimmed Image 24 24\n{\n  \"success\": true,\n  \"seriesId\": 17\n}"
    assert cc_module._parse_cli_json(noisy) == {'success': True, 'seriesId': 17}
    assert cc_module._parse_cli_json('{"a": 1}') == {'a': 1}
    assert cc_module._parse_cli_json('not json at all') == {}
    assert cc_module._parse_cli_json('') == {}


def test_custom_stage_set_folder(client):
    res = client.post('/api/mex/custom-stages/set-folder',
                      json={'stageId': 'stage-1', 'folderId': 'folder_aa11'})
    assert res.get_json()['success'] is True
    meta = json.loads((client.storage / 'metadata.json').read_text())
    stage = next(s for s in meta['custom_stages'] if s.get('id') == 'stage-1')
    assert stage['folder_id'] == 'folder_aa11'

    # unassign
    res = client.post('/api/mex/custom-stages/set-folder',
                      json={'stageId': 'stage-1', 'folderId': None})
    assert res.get_json()['success'] is True
    meta = json.loads((client.storage / 'metadata.json').read_text())
    stage = next(s for s in meta['custom_stages'] if s.get('id') == 'stage-1')
    assert 'folder_id' not in stage
