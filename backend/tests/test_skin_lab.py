import sys
from pathlib import Path

import numpy as np
import pytest
from flask import Flask

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from skinlab import palette


def _solid(w, h, rgba):
    arr = np.zeros((h, w, 4), dtype=np.uint8)
    arr[:, :] = rgba
    return arr


def test_hsl_round_trip():
    rgb = np.array([[255, 0, 0], [0, 255, 0], [0, 0, 255],
                    [200, 150, 60], [17, 230, 190]], dtype=np.float64)
    h, s, l = palette.rgb_to_hsl(rgb)
    back = palette.hsl_to_rgb(h, s, l)
    assert np.abs(back.astype(int) - rgb.astype(int)).max() <= 1


def test_analyze_finds_distinct_hue_groups():
    # one red texture, one green texture (both > MIN_GROUP_PIXELS)
    red = _solid(32, 32, (200, 40, 40, 255))
    green = _solid(32, 32, (40, 200, 40, 255))
    groups, pixel_maps = palette.analyze({0: red, 1: green}, max_groups=2)
    assert len(groups) == 2
    hues = sorted(g['centerHue'] for g in groups)
    assert hues[0] < 30 or hues[0] > 330      # red-ish
    assert 90 < hues[1] < 150                 # green-ish
    # every opaque pixel assigned to some group
    assert set(np.unique(pixel_maps[0])) <= {0, 1}
    assert set(np.unique(pixel_maps[1])) <= {0, 1}


def test_analyze_skips_grays_and_extremes():
    gray = _solid(32, 32, (128, 128, 128, 255))     # s < 15
    black = _solid(32, 32, (5, 5, 5, 255))          # l < 10
    clear = _solid(32, 32, (200, 40, 40, 0))        # transparent
    groups, pixel_maps = palette.analyze({0: gray, 1: black, 2: clear}, max_groups=4)
    assert groups == []
    for m in pixel_maps.values():
        assert (m == 255).all()


def test_apply_hue_shift_recolors_only_the_group():
    # red square with a gray border: shift red +120 degrees -> green, gray untouched
    arr = _solid(32, 32, (128, 128, 128, 255))
    arr[8:24, 8:24] = (200, 40, 40, 255)   # 256 px, above the 100-px group floor
    groups, pixel_maps = palette.analyze({0: arr}, max_groups=1)
    assert len(groups) == 1
    out = palette.apply_adjustments(arr, pixel_maps[0], {0: (120.0, 0.0)})
    assert out is not None
    center = out[16, 16]
    assert center[1] > center[0] and center[1] > center[2]   # now green-dominant
    assert tuple(out[0, 0][:3]) == (128, 128, 128)           # gray border untouched
    assert (out[..., 3] == 255).all()                        # alpha preserved


def test_apply_no_adjustments_returns_none():
    arr = _solid(8, 8, (200, 40, 40, 255))
    groups, pixel_maps = palette.analyze({0: arr}, max_groups=1)
    assert palette.apply_adjustments(arr, pixel_maps[0], {0: (0.0, 0.0)}) is None


def test_saturation_shift_clamps():
    arr = _solid(16, 16, (200, 40, 40, 255))
    groups, pixel_maps = palette.analyze({0: arr}, max_groups=1)
    out = palette.apply_adjustments(arr, pixel_maps[0], {0: (0.0, -200.0)})
    # fully desaturated -> r == g == b
    px = out[4, 4]
    assert abs(int(px[0]) - int(px[1])) <= 1 and abs(int(px[1]) - int(px[2])) <= 1


def test_routes_require_session():
    from blueprints import skin_lab as sl_module
    app = Flask(__name__)
    app.register_blueprint(sl_module.skin_lab_bp)
    with app.test_client() as c:
        assert c.get('/api/mex/skin-lab/status').get_json() == {'success': True, 'open': False}
        for method, url in [
            ('get', '/api/mex/skin-lab/textures'),
            ('get', '/api/mex/skin-lab/texture/0'),
            ('post', '/api/mex/skin-lab/camera'),
            ('get', '/api/mex/skin-lab/frame'),
            ('post', '/api/mex/skin-lab/palette/analyze'),
            ('get', '/api/mex/skin-lab/export-dat'),
            ('post', '/api/mex/skin-lab/save'),
        ]:
            res = getattr(c, method)(url, json={})
            assert res.status_code == 409, url
        # close is idempotent
        assert c.post('/api/mex/skin-lab/close').get_json()['success'] is True
