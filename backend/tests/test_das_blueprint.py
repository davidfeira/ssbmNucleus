import sys
from pathlib import Path

from flask import Flask


BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from blueprints.das import (
    add_button_indicator,
    das_bp,
    get_variant_match_key,
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
