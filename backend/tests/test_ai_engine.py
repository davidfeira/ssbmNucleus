"""Unit tests for the aiengine package: tier resolver matrix, hardware fit
badges, telemetry aggregation, settings round-trip."""
import json
import sys
import time
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from aiengine import hardware, routing, telemetry
from aiengine.registry import MODELS
from aiengine.routing import RoutingError


GPU_16GB = {'gpu': {'name': 'Test RTX', 'vramMb': 16384},
            'diskFreeBytes': 100 * 1024**3}
GPU_8GB = {'gpu': {'name': 'Small GPU', 'vramMb': 8192},
           'diskFreeBytes': 100 * 1024**3}
NO_GPU = {'gpu': None, 'diskFreeBytes': 100 * 1024**3}


@pytest.fixture
def env(monkeypatch, tmp_path):
    """Knobs for the resolver's runtime inputs."""
    state = {'downloaded': set(), 'hw': GPU_16GB, 'engine': True,
             'settings': {'tierRouting': {'standard': None, 'strong': None},
                          'disabledModels': [], 'hfCacheDir': None}}
    monkeypatch.setattr('aiengine.models_admin.downloaded_ids',
                        lambda: set(state['downloaded']))
    monkeypatch.setattr('aiengine.hardware.detect',
                        lambda force=False: state['hw'])
    monkeypatch.setattr('aiengine.routing.engine_available',
                        lambda: state['engine'])
    monkeypatch.setattr('aiengine.settings_store.load_settings',
                        lambda: dict(state['settings']))
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    # the dev machine may have a real encrypted key stored — tests must not
    monkeypatch.setattr('aiengine.keystore.load_key', lambda: None)
    return state


# --------------------------------------------------------------------------
# routing.resolve
# --------------------------------------------------------------------------
def test_resolve_nothing_usable_raises(env):
    with pytest.raises(RoutingError):
        routing.resolve('standard')


def test_resolve_standard_prefers_fastest_local(env):
    env['downloaded'] = {'sd-turbo', 'flux-klein-4b'}
    r = routing.resolve('standard')
    assert r['provider'] == 'local'
    assert r['model'] == 'sd-turbo'
    assert not r['escalated']


def test_resolve_strong_escalates_past_tile_only_local(env, monkeypatch):
    env['downloaded'] = {'sd-turbo'}
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-test')
    r = routing.resolve('strong')
    assert r['provider'] == 'openrouter'
    assert r['escalated'] is True
    assert r['reason']


def test_resolve_strong_uses_scene_capable_local(env):
    env['downloaded'] = {'sd-turbo', 'z-image-turbo'}
    r = routing.resolve('strong')
    assert r['model'] == 'z-image-turbo'
    assert r['escalated'] is True   # standard would pick sd-turbo


def test_resolve_strong_skips_local_that_does_not_fit_vram(env, monkeypatch):
    env['downloaded'] = {'sd-turbo', 'z-image-turbo'}
    env['hw'] = GPU_8GB   # z-image needs ~16GB
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-test')
    r = routing.resolve('strong')
    assert r['provider'] == 'openrouter'


def test_resolve_strong_last_resort_warns(env):
    env['downloaded'] = {'sd-turbo'}   # no key, no scene-capable model
    r = routing.resolve('strong')
    assert r['model'] == 'sd-turbo'
    assert 'quality' in (r['reason'] or '')


def test_resolve_key_only_setup_goes_api(env, monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-test')
    r = routing.resolve('standard')
    assert r['provider'] == 'openrouter'
    assert r['isApi']


def test_resolve_client_key_counts(env):
    r = routing.resolve('standard', client_key=True)
    assert r['provider'] == 'openrouter'


def test_resolve_honors_configured_routing(env, monkeypatch):
    env['downloaded'] = {'sd-turbo', 'flux-klein-4b'}
    env['settings']['tierRouting'] = {
        'standard': {'provider': 'local', 'model': 'flux-klein-4b'},
        'strong': None}
    r = routing.resolve('standard')
    assert r['model'] == 'flux-klein-4b'


def test_resolve_configured_but_unusable_falls_back(env):
    env['downloaded'] = {'sd-turbo'}
    env['settings']['tierRouting'] = {
        'standard': {'provider': 'local', 'model': 'flux-klein-4b'},  # not downloaded
        'strong': None}
    r = routing.resolve('standard')
    assert r['model'] == 'sd-turbo'


def test_resolve_disabled_model_is_skipped(env):
    env['downloaded'] = {'sd-turbo', 'flux-klein-4b'}
    env['settings']['disabledModels'] = ['sd-turbo']
    r = routing.resolve('standard')
    assert r['model'] == 'flux-klein-4b'


def test_resolve_explicit_override_wins(env, monkeypatch):
    env['downloaded'] = {'sd-turbo'}
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-test')
    r = routing.resolve('strong', override_model='sd-turbo')
    assert r['model'] == 'sd-turbo'
    assert not r['escalated']


def test_resolve_unknown_api_slug_is_honored(env, monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-test')
    r = routing.resolve('standard', override_model='someorg/new-model')
    assert r['provider'] == 'openrouter'
    assert r['model'] == 'someorg/new-model'


def test_resolve_api_model_travels_as_slug(env, monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-test')
    r = routing.resolve('strong')
    assert '/' in r['model']   # OpenRouter slug, not registry id


def test_resolve_no_engine_means_no_local(env, monkeypatch):
    env['downloaded'] = {'sd-turbo'}
    env['engine'] = False
    with pytest.raises(RoutingError):
        routing.resolve('standard')


def test_resolve_forced_local_without_models_raises(env, monkeypatch):
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-test')
    with pytest.raises(RoutingError):
        routing.resolve('standard', override_provider='local')


# --------------------------------------------------------------------------
# hardware.model_fit
# --------------------------------------------------------------------------
@pytest.mark.parametrize('model_id,hw,expected', [
    ('sd-turbo', GPU_16GB, 'good'),
    ('z-image-turbo', GPU_16GB, 'slow'),      # 16GB est on a 16GB card
    ('z-image-turbo', GPU_8GB, 'insufficient_vram'),
    ('flux-klein-4b', GPU_16GB, 'slow'),       # 13GB est is >80% of 16GB
    ('flux-klein-4b', GPU_8GB, 'insufficient_vram'),
    ('sd-turbo', NO_GPU, 'no_gpu'),
    ('gemini-image', NO_GPU, 'good'),          # API models always fit
])
def test_model_fit(model_id, hw, expected):
    assert hardware.model_fit(MODELS[model_id], hw) == expected


# --------------------------------------------------------------------------
# telemetry
# --------------------------------------------------------------------------
def test_telemetry_record_and_aggregate(monkeypatch, tmp_path):
    ledger = tmp_path / 'ai_runs.jsonl'
    monkeypatch.setattr('aiengine.telemetry.RUNS_LEDGER', ledger)

    telemetry.record_run('local', 'sd-turbo', 'standard', 'material', 14.0, True)
    telemetry.record_run('local', 'sd-turbo', 'standard', 'material', 18.0, True)
    telemetry.record_run('local', 'sd-turbo', 'standard', 'ailab', 5.0, False)
    telemetry.record_run('local', 'sd-turbo', 'standard', 'ailab', 0.0, True,
                         cached=True)
    telemetry.record_run('openrouter', 'google/g', 'strong', 'stage', 9.0, True,
                         est_cost_usd=0.04)

    agg = telemetry.aggregate(days=1)
    by_model = {m['model']: m for m in agg['perModel']}
    sd = by_model['sd-turbo']
    assert sd['runs'] == 3                 # cached hit not an attempt
    assert sd['cachedHits'] == 1
    assert sd['avgSeconds'] == 16.0        # successful, non-cached only
    assert sd['successRate'] == pytest.approx(2 / 3)
    assert by_model['google/g']['totalCostUsd'] == pytest.approx(0.04)
    assert agg['totals']['runs'] == 4


def test_telemetry_window_filters_old_runs(monkeypatch, tmp_path):
    ledger = tmp_path / 'ai_runs.jsonl'
    monkeypatch.setattr('aiengine.telemetry.RUNS_LEDGER', ledger)
    old = {'ts': time.time() - 100 * 86400, 'provider': 'local',
           'model': 'sd-turbo', 'tier': 'standard', 'kind': 'material',
           'seconds': 1.0, 'success': True, 'cached': False,
           'est_cost_usd': 0.0}
    ledger.write_text(json.dumps(old) + '\n', encoding='utf-8')
    telemetry.record_run('local', 'sd-turbo', 'standard', 'material', 2.0, True)
    agg = telemetry.aggregate(days=30)
    assert agg['totals']['runs'] == 1


def test_telemetry_tolerates_corrupt_lines(monkeypatch, tmp_path):
    ledger = tmp_path / 'ai_runs.jsonl'
    monkeypatch.setattr('aiengine.telemetry.RUNS_LEDGER', ledger)
    ledger.write_text('not json\n', encoding='utf-8')
    telemetry.record_run('local', 'sd-turbo', 'standard', 'material', 2.0, True)
    assert telemetry.aggregate()['totals']['runs'] == 1


# --------------------------------------------------------------------------
# keystore (encrypted OpenRouter key at rest)
# --------------------------------------------------------------------------
def test_keystore_round_trip(monkeypatch, tmp_path):
    from aiengine import keystore
    monkeypatch.setattr('aiengine.keystore.KEY_PATH', tmp_path / 'openrouter.key')
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)

    assert keystore.load_key() is None
    keystore.save_key('sk-or-v1-test123')
    # at rest it is NOT plaintext
    stored = (tmp_path / 'openrouter.key').read_text()
    assert 'sk-or-v1-test123' not in stored
    assert keystore.load_key() == 'sk-or-v1-test123'
    assert keystore.get_openrouter_key() == 'sk-or-v1-test123'

    keystore.save_key('')   # empty clears
    assert keystore.load_key() is None
    assert not (tmp_path / 'openrouter.key').exists()


def test_keystore_env_fallback(monkeypatch, tmp_path):
    from aiengine import keystore
    monkeypatch.setattr('aiengine.keystore.KEY_PATH', tmp_path / 'openrouter.key')
    monkeypatch.setenv('OPENROUTER_API_KEY', 'sk-env')
    assert keystore.get_openrouter_key() == 'sk-env'
    keystore.save_key('sk-stored')
    assert keystore.get_openrouter_key() == 'sk-stored'   # store wins


def test_keystore_corrupt_file_reads_as_none(monkeypatch, tmp_path):
    from aiengine import keystore
    path = tmp_path / 'openrouter.key'
    monkeypatch.setattr('aiengine.keystore.KEY_PATH', path)
    monkeypatch.delenv('OPENROUTER_API_KEY', raising=False)
    path.write_text('dpapi:not-even-base64!!!')
    assert keystore.load_key() is None
    assert keystore.get_openrouter_key() is None


# --------------------------------------------------------------------------
# settings_store
# --------------------------------------------------------------------------
def test_settings_round_trip(monkeypatch, tmp_path):
    monkeypatch.setattr('aiengine.settings_store.CONFIG_PATH',
                        tmp_path / 'ai_studio.json')
    from aiengine import settings_store
    s = settings_store.load_settings()
    assert s['tierRouting'] == {'standard': None, 'strong': None}

    settings_store.save_settings({
        'tierRouting': {'strong': {'provider': 'openrouter',
                                   'model': 'google/gemini-2.5-flash-image'}},
        'disabledModels': ['flux-klein-4b'],
        'ignoredKey': 'dropped'})
    s = settings_store.load_settings()
    assert s['tierRouting']['strong']['model'] == 'google/gemini-2.5-flash-image'
    assert s['tierRouting']['standard'] is None    # merge keeps the other tier
    assert s['disabledModels'] == ['flux-klein-4b']
    assert 'ignoredKey' not in s
