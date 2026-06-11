"""Task-tier → model resolution.

Tasks come in two strengths: 'standard' (seamless material swatches — any
model copes) and 'strong' (coherent scene work like stage backdrops — 1-step
turbo models produce mush). The user maps each tier to a model in Settings;
when a strong task lands on a different model than a standard one would,
that's an ESCALATION and the UI says so before money is spent.
"""
from aiengine import hardware, keystore, models_admin
from aiengine.paths import engine_available
from aiengine.registry import (DEFAULT_API_MODEL, MODELS,
                               TIER_LOCAL_PREFERENCE, find)

TIERS = ('standard', 'strong')


def _key_available(client_key=False):
    return bool(keystore.get_openrouter_key()) or bool(client_key)


def label_for(spec, model=None):
    """Human label for a resolved model, e.g. 'SD-Turbo (local, free)' or
    'Nano Banana (API, ~4¢/image)'. Falls back to the raw model string for
    unknown API slugs."""
    if spec is None:
        return f'{model} (API)'
    name = spec.description.split('—')[0].strip() or spec.id
    if spec.kind == 'api':
        return f'{name} (API, ~{int(round(spec.cost_per_image_usd * 100))}¢/image)'
    return f'{name} (local, free)'


def _usable(spec, downloaded, disabled, client_key):
    if spec.kind == 'api':
        return _key_available(client_key)
    return (engine_available()
            and spec.id in downloaded
            and spec.id not in disabled)


def _result(spec, model, escalated=False, reason=None):
    is_api = spec.kind == 'api' if spec else True
    return {
        'provider': 'openrouter' if is_api else 'local',
        # API models travel as their OpenRouter slug, locals as registry id
        'model': (spec.repo_id if is_api else spec.id) if spec else model,
        'label': label_for(spec, model),
        'estCostUsd': spec.cost_per_image_usd if spec else 0.0,
        'isApi': is_api,
        'escalated': escalated,
        'reason': reason,
    }


def _resolve_base(tier, downloaded, disabled, client_key, settings):
    """Resolution WITHOUT per-request overrides: configured routing, then
    defaults. Returns (spec_or_None, reason_or_None); None spec means nothing
    usable at all."""
    configured = (settings.get('tierRouting') or {}).get(tier)
    if configured and configured.get('model'):
        spec = find(configured['model'])
        if spec and _usable(spec, downloaded, disabled, client_key):
            return spec, None
        # configured but not currently usable -> fall through to defaults

    hw = hardware.detect()
    if tier == 'strong':
        for mid in TIER_LOCAL_PREFERENCE['strong']:
            spec = MODELS[mid]
            if (_usable(spec, downloaded, disabled, client_key)
                    and hardware.model_fit(spec, hw) in ('good', 'slow')):
                return spec, None
        if _key_available(client_key):
            return MODELS[DEFAULT_API_MODEL], None
        # last resort: any usable local, quality warning attached
        for mid in TIER_LOCAL_PREFERENCE['standard']:
            spec = MODELS[mid]
            if _usable(spec, downloaded, disabled, client_key):
                return spec, 'no scene-capable model available; quality may suffer'
        return None, None

    for mid in TIER_LOCAL_PREFERENCE['standard']:
        spec = MODELS[mid]
        if _usable(spec, downloaded, disabled, client_key):
            return spec, None
    if _key_available(client_key):
        return MODELS[DEFAULT_API_MODEL], None
    return None, None


def resolve(tier, override_provider=None, override_model=None, client_key=False):
    """Resolve a tier to a concrete provider+model. Returns the dict described
    in _result, or raises RoutingError when nothing is usable."""
    from aiengine.settings_store import load_settings

    tier = tier if tier in TIERS else 'standard'
    settings = load_settings()
    downloaded = models_admin.downloaded_ids()
    disabled = set(settings.get('disabledModels') or [])

    # 1. explicit override from the request wins outright
    if override_model:
        spec = find(override_model)
        if spec:
            return _result(spec, override_model)
        if '/' in str(override_model):
            # unknown API slug — honor it, _openrouter_generate will validate
            return _result(None, override_model)
        # unknown local id: fall through to normal resolution
    elif (override_provider or '').lower() == 'openrouter':
        if _key_available(client_key):
            return _result(MODELS[DEFAULT_API_MODEL], None)
    elif (override_provider or '').lower() in ('local', 'assetfarm'):
        for mid in TIER_LOCAL_PREFERENCE.get(tier, []) + TIER_LOCAL_PREFERENCE['standard']:
            spec = MODELS[mid]
            if _usable(spec, downloaded, disabled, client_key):
                return _result(spec, None)
        raise RoutingError('no usable local model (download one in Settings)')

    # 2./3. configured routing, then defaults
    spec, reason = _resolve_base(tier, downloaded, disabled, client_key, settings)
    if spec is None:
        raise RoutingError(
            'AI Studio is not set up: add an OpenRouter key or download a '
            'local model in Settings')

    escalated = False
    if tier == 'strong':
        base_spec, _ = _resolve_base('standard', downloaded, disabled,
                                     client_key, settings)
        if base_spec and base_spec.id != spec.id:
            escalated = True
            reason = reason or ('backgrounds need scene coherence; '
                                f'{base_spec.id} is tile-only')
    return _result(spec, None, escalated=escalated, reason=reason)


class RoutingError(RuntimeError):
    pass
