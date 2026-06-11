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


def test_tint_colorizes_whites_keeping_lightness():
    from skinlab import compose
    arr = _solid(8, 8, (220, 220, 220, 255))   # near-white (no hue)
    arr[0, 0] = (40, 40, 40, 255)              # dark pixel outside mask (lum_min)
    mask = compose.build_mask(arr, sat_max=18, lum_min=30)
    out = compose.tint(arr, mask, hue=120.0, saturation=50.0)
    px = out[4, 4]
    assert px[1] > px[0] and px[1] > px[2]     # white became green
    assert px.max() > 180                      # stayed light
    assert tuple(out[0, 0][:3]) == (40, 40, 40)  # unmasked untouched
    assert compose.tint(arr, np.zeros((8, 8), dtype=bool), 120) is None


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


def test_build_mask_hue_wraparound_and_bounds():
    from skinlab import compose
    arr = np.zeros((1, 4, 4), dtype=np.uint8)
    arr[0, 0] = (200, 40, 40, 255)    # red, hue ~0
    arr[0, 1] = (40, 40, 200, 255)    # blue, hue ~240
    arr[0, 2] = (128, 128, 128, 255)  # gray
    arr[0, 3] = (200, 40, 40, 0)      # transparent red
    # wrap range 330..30 selects red only
    m = compose.build_mask(arr, hue_min=330, hue_max=30, sat_min=15)
    assert m.tolist() == [[True, False, False, False]]
    # plain range selects blue
    m = compose.build_mask(arr, hue_min=200, hue_max=260)
    assert m.tolist() == [[False, True, False, False]]
    # low-sat bright = gray
    m = compose.build_mask(arr, sat_max=10, lum_min=30)
    assert m.tolist() == [[False, False, True, False]]


def test_composite_modulates_by_original_lightness():
    from skinlab import compose
    arr = np.zeros((2, 2, 4), dtype=np.uint8)
    arr[0, 0] = (60, 60, 220, 255)    # dark blue
    arr[0, 1] = (170, 170, 250, 255)  # light blue
    arr[1, 0] = (128, 128, 128, 255)  # gray (unmasked)
    arr[1, 1] = (60, 60, 220, 0)      # transparent
    material = np.full((1, 1, 3), 128, dtype=np.uint8)  # flat gray fabric
    mask = compose.build_mask(arr, hue_min=200, hue_max=260, sat_min=15)
    out = compose.composite(arr, material, mask)
    # light pixel ends up brighter than dark pixel (shading survived)
    assert out[0, 1, :3].mean() > out[0, 0, :3].mean()
    assert tuple(out[1, 0][:3]) == (128, 128, 128)   # unmasked untouched
    assert out[1, 1, 3] == 0                          # alpha preserved
    # empty mask -> None
    assert compose.composite(arr, material, np.zeros((2, 2), dtype=bool)) is None


def test_hue_shift_only_masked_pixels():
    from skinlab import compose
    arr = np.zeros((1, 2, 4), dtype=np.uint8)
    arr[0, 0] = (40, 40, 200, 255)   # blue
    arr[0, 1] = (200, 40, 40, 255)   # red
    mask = compose.build_mask(arr, hue_min=200, hue_max=260)
    out = compose.hue_shift(arr, mask, hue_delta=-120.0)
    assert out[0, 0, 1] > out[0, 0, 2]               # blue (240) - 120 -> green (120)
    assert tuple(out[0, 1][:3]) == (200, 40, 40)     # red untouched
    assert compose.hue_shift(arr, mask) is None      # no deltas -> None


def test_fox_region_map_is_valid():
    import json as _json
    path = BACKEND_DIR / 'assets' / 'texture_regions' / 'Fox.json'
    region_map = _json.loads(path.read_text(encoding='utf-8'))
    regions = region_map['regions']
    assert set(region_map['protected']) <= set(
        regions['eyes'] + regions['face_detail'])
    for name, idxs in regions.items():
        assert idxs == sorted(set(idxs)), name
        assert all(0 <= i < region_map['basis']['textureCount'] for i in idxs), name
    # every region with a mask hint parses into build_mask kwargs
    from blueprints.skin_lab import _mask_kwargs
    from skinlab import compose
    arr = np.zeros((1, 1, 4), dtype=np.uint8)
    for name, hint in region_map['maskHints'].items():
        compose.build_mask(arr, **_mask_kwargs(hint))


def test_composite_routes_validation():
    from blueprints import skin_lab as sl_module
    app = Flask(__name__)
    app.register_blueprint(sl_module.skin_lab_bp)
    with app.test_client() as c:
        # bad material shape fails before needing a session
        res = c.post('/api/mex/skin-lab/composite', json={'region': 'fur', 'material': {}})
        assert res.status_code == 400
        assert 'material' in res.get_json()['error']
        # hue-shift requires a delta
        res = c.post('/api/mex/skin-lab/hue-shift', json={'region': 'fur'})
        assert res.status_code == 400
        # with a valid material but no session -> 409
        import base64 as _b64
        import io as _io
        from PIL import Image as _Image
        buf = _io.BytesIO()
        _Image.new('RGB', (4, 4), (255, 0, 0)).save(buf, format='PNG')
        res = c.post('/api/mex/skin-lab/composite', json={
            'region': 'fur',
            'material': {'data': _b64.b64encode(buf.getvalue()).decode()}})
        assert res.status_code == 409
        res = c.get('/api/mex/skin-lab/regions')
        assert res.status_code == 409


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
