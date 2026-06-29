import sys
from pathlib import Path

from flask import Flask


BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from blueprints.das import (
    add_button_indicator,
    das_bp,
    get_variant_match_key,
    migrate_das_folder_extensions,
    normalize_variant_name,
    sanitize_filename,
    strip_button_indicator,
)
from core.state import set_project_path


def test_button_helpers_normalize_spacing():
    assert strip_button_indicator('tabuu-batt(B)') == 'tabuu-batt'
    assert strip_button_indicator('tabuu-batt (B)') == 'tabuu-batt'
    assert strip_button_indicator('tabuu   batt   (B)') == 'tabuu batt'
    assert add_button_indicator('TabuuBatt', 'x') == 'TabuuBatt(X)'
    assert sanitize_filename('tabuu   batt\t(B)') == 'tabuu batt (B)'
    assert normalize_variant_name('tabuu batt') == 'TabuuBatt'
    assert normalize_variant_name('tabuu batt (b)') == 'TabuuBatt(B)'
    assert get_variant_match_key('tabuu batt') == 'tabuubatt'
    assert get_variant_match_key('TabuuBatt(B)') == 'tabuubatt'


def test_rename_route_trims_stray_space_when_removing_button(tmp_path):
    project_dir = tmp_path / 'project'
    files_dir = project_dir / 'files' / 'GrNBa'
    files_dir.mkdir(parents=True)
    (project_dir / 'project.mexproj').write_text('', encoding='utf-8')
    (files_dir / 'TabuuBatt(B).dat').write_bytes(b'test')

    set_project_path(project_dir / 'project.mexproj')

    app = Flask(__name__)
    app.register_blueprint(das_bp)
    client = app.test_client()

    response = client.post('/api/mex/das/rename', json={
        'stageCode': 'GrNBa',
        'oldName': 'TabuuBatt(B)',
        'newName': 'tabuu batt '
    })

    assert response.status_code == 200
    assert (files_dir / 'TabuuBatt.dat').exists()
    assert not (files_dir / 'tabuu batt .dat').exists()


def test_migrate_das_extensions_heals_legacy_usd_stadium(tmp_path):
    """Legacy versions wrote Stadium alts as .usd, which the m-ex loader rejects
    ('no valid alts found' -> crash). Migration renames them to .dat."""
    files_dir = tmp_path / 'files'
    grps = files_dir / 'GrPs'
    grps.mkdir(parents=True)
    grps.joinpath('vanilla.usd').write_bytes(b'base')
    grps.joinpath('AllBlack.usd').write_bytes(b'allblack')
    grps.joinpath('TransStad.usd').write_bytes(b'transstad')

    result = migrate_das_folder_extensions(files_dir)

    # Every .usd alt is now a valid .dat alt; nothing left for the loader to reject.
    assert sorted(p.name for p in grps.glob('*.usd')) == []
    assert (grps / 'vanilla.dat').read_bytes() == b'base'
    assert (grps / 'AllBlack.dat').read_bytes() == b'allblack'
    assert (grps / 'TransStad.dat').read_bytes() == b'transstad'
    assert len(result['renamed']) == 3

    # Idempotent: a second pass is a clean no-op.
    again = migrate_das_folder_extensions(files_dir)
    assert again == {'renamed': [], 'removed': []}


def test_migrate_das_extensions_collision_handling(tmp_path):
    files_dir = tmp_path / 'files'
    grps = files_dir / 'GrPs'
    grps.mkdir(parents=True)
    # vanilla present in both extensions -> the redundant .usd base is dropped.
    grps.joinpath('vanilla.dat').write_bytes(b'base')
    grps.joinpath('vanilla.usd').write_bytes(b'stale-base-differs')
    # A variant present as identical .dat + .usd -> the duplicate .usd is dropped.
    grps.joinpath('Dup.dat').write_bytes(b'same')
    grps.joinpath('Dup.usd').write_bytes(b'same')
    # A variant whose .usd differs from an existing .dat of the same stem -> kept.
    grps.joinpath('Keep.dat').write_bytes(b'one')
    grps.joinpath('Keep.usd').write_bytes(b'two')

    result = migrate_das_folder_extensions(files_dir)

    assert list(grps.glob('*.usd')) == []
    assert (grps / 'vanilla.dat').read_bytes() == b'base'        # original kept
    assert (grps / 'Dup.dat').read_bytes() == b'same'
    assert (grps / 'Keep.dat').read_bytes() == b'one'            # original kept
    assert (grps / 'Keep_1.dat').read_bytes() == b'two'          # distinct .usd preserved
    assert sorted(result['removed']) == ['Dup.usd', 'vanilla.usd']


def test_migrate_das_extensions_leaves_dat_only_folders_untouched(tmp_path):
    files_dir = tmp_path / 'files'
    grop = files_dir / 'GrOp'
    grop.mkdir(parents=True)
    grop.joinpath('vanilla.dat').write_bytes(b'a')
    grop.joinpath('AutumnDreamland.dat').write_bytes(b'b')

    result = migrate_das_folder_extensions(files_dir)

    assert result == {'renamed': [], 'removed': []}
    assert sorted(p.name for p in grop.glob('*.dat')) == ['AutumnDreamland.dat', 'vanilla.dat']
