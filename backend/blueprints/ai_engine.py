"""AI engine management API — the Settings hub's backend.

GET  /api/mex/ai-engine/status      setup state: engine, hardware, gating
GET  /api/mex/ai-engine/models      catalog with download/fit/stats per model
POST /api/mex/ai-engine/models/<id>/download   (events: aiengine_download_*)
POST /api/mex/ai-engine/models/<id>/delete
POST /api/mex/ai-engine/models/<id>/toggle     {enabled}
POST /api/mex/ai-engine/install     {variant?: 'cuda'|'cpu'}  (events: aiengine_install_*)
GET  /api/mex/ai-engine/routing
POST /api/mex/ai-engine/routing     {standard?: {provider,model}|null, strong?: ...}
POST /api/mex/ai-engine/resolve     {tasks: [{kind, tier?}], clientHasKey?}
GET  /api/mex/ai-engine/stats?days=90
"""
import logging
import os
import threading

from flask import Blueprint, jsonify, request

from aiengine import (hardware, installer, models_admin, routing, runner,
                      telemetry)
from aiengine.paths import engine_available, engine_python, hf_cache_dir
from aiengine.registry import MODELS, find
from aiengine.settings_store import load_settings, save_settings

logger = logging.getLogger(__name__)

ai_engine_bp = Blueprint('ai_engine', __name__)

_download_lock = threading.Lock()
_downloading = {}      # model_id -> True while a download thread runs


def _local_model_ready():
    """True when at least one enabled local model is downloaded AND the
    engine can run it."""
    if not engine_available():
        return False
    disabled = set(load_settings().get('disabledModels') or [])
    return bool(models_admin.downloaded_ids() - disabled)


@ai_engine_bp.route('/api/mex/ai-engine/status', methods=['GET'])
def engine_status():
    state = installer.read_state()
    check = runner.check() if engine_available() else None
    settings = load_settings()
    return jsonify({
        'success': True,
        'engine': {
            'installed': engine_available(),
            'managed': not os.environ.get('NUCLEUS_AIENGINE_PYTHON'),
            'python': str(engine_python()),
            'torchVariant': state.get('torchVariant'),
            'ok': bool(check and check.get('ok')),
            'cuda': bool(check and check.get('cuda')),
            'diffusersVersion': (check or {}).get('diffusersVersion'),
        },
        'hardware': hardware.detect(),
        'hasBackendKey': bool(os.environ.get('OPENROUTER_API_KEY')),
        'localModelReady': _local_model_ready(),
        'routing': settings.get('tierRouting'),
        'installState': {
            'installing': installer.is_installing(),
            'phase': state.get('phase'),
            'error': state.get('error'),
            'finishedAt': state.get('finishedAt'),
        },
    })


@ai_engine_bp.route('/api/mex/ai-engine/models', methods=['GET'])
def list_models():
    statuses = models_admin.get_statuses()
    settings = load_settings()
    disabled = set(settings.get('disabledModels') or [])
    hw = hardware.detect()
    stats = telemetry.model_stats()
    check = runner.check() if engine_available() else None
    pipelines = (check or {}).get('pipelines') or {}
    has_key = bool(os.environ.get('OPENROUTER_API_KEY'))

    models = []
    for spec in MODELS.values():
        st = statuses.get(spec.id) or {}
        entry = {
            'id': spec.id,
            'label': routing.label_for(spec),
            'description': spec.description,
            'speedBlurb': spec.speed_blurb,
            'kind': spec.kind,
            'repoId': spec.repo_id,
            'vramGb': spec.vram_estimate_gb,
            'diskEstimateGb': spec.disk_estimate_gb,
            'tierFit': sorted(spec.tier_fit),
            'costPerImageUsd': spec.cost_per_image_usd,
            'downloaded': st.get('downloaded', False),
            'partial': st.get('partial', False),
            'downloading': bool(_downloading.get(spec.id)),
            'sizeOnDiskBytes': st.get('sizeOnDiskBytes', 0),
            'enabled': spec.id not in disabled,
            'fit': hardware.model_fit(spec, hw),
            # known-missing pipeline class in the installed diffusers
            'needsEngineUpdate': (spec.kind == 'local' and pipelines
                                  and pipelines.get(spec.pipeline_class) is False),
            'stats': (stats.get(spec.id) or stats.get(spec.repo_id)
                      if spec.kind == 'local' else stats.get(spec.repo_id)),
            'requiresKey': spec.kind == 'api' and not has_key,
        }
        models.append(entry)

    return jsonify({
        'success': True,
        'models': models,
        'totalDiskBytes': sum(st.get('sizeOnDiskBytes', 0)
                              for st in statuses.values()),
        'cacheDir': str(hf_cache_dir()),
    })


@ai_engine_bp.route('/api/mex/ai-engine/models/<model_id>/download',
                    methods=['POST'])
def download_model(model_id):
    from core.state import get_socketio
    socketio = get_socketio()

    spec = find(model_id)
    if spec is None or spec.kind != 'local':
        return jsonify({'success': False,
                        'error': f'unknown local model: {model_id}'}), 404

    hw = hardware.detect(force=True)
    already = (models_admin.get_statuses().get(spec.id) or {}) \
        .get('sizeOnDiskBytes', 0)
    need = max(0, int(spec.disk_estimate_gb * 1.1 * 1024**3) - already)
    if hw['diskFreeBytes'] < need:
        return jsonify({'success': False,
                        'error': f'not enough disk space (~{spec.disk_estimate_gb:.0f}GB '
                                 'needed)'}), 400

    with _download_lock:
        if any(_downloading.values()):
            return jsonify({'success': False,
                            'error': 'another download is already running'}), 409
        _downloading[spec.id] = True

    def run():
        try:
            for tick in models_admin.download_model_with_progress(spec.id):
                if tick['status'] == 'progress':
                    socketio.emit('aiengine_download_progress',
                                  {'modelId': spec.id, **tick})
                elif tick['status'] == 'done':
                    socketio.emit('aiengine_download_complete',
                                  {'modelId': spec.id})
                else:
                    socketio.emit('aiengine_download_error',
                                  {'modelId': spec.id,
                                   'error': tick.get('message')})
        except Exception as e:
            logger.error(f'[ai-engine] download failed: {e}', exc_info=True)
            socketio.emit('aiengine_download_error',
                          {'modelId': spec.id, 'error': str(e)})
        finally:
            _downloading.pop(spec.id, None)

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True, 'started': True})


@ai_engine_bp.route('/api/mex/ai-engine/models/<model_id>/delete',
                    methods=['POST'])
def delete_model(model_id):
    if _downloading.get(model_id):
        return jsonify({'success': False,
                        'error': 'model is currently downloading'}), 409
    try:
        freed = models_admin.delete_model_cache(model_id)
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    return jsonify({'success': True, 'freedBytes': freed})


@ai_engine_bp.route('/api/mex/ai-engine/models/<model_id>/toggle',
                    methods=['POST'])
def toggle_model(model_id):
    spec = find(model_id)
    if spec is None:
        return jsonify({'success': False,
                        'error': f'unknown model: {model_id}'}), 404
    enabled = bool((request.get_json(silent=True) or {}).get('enabled', True))
    disabled = set(load_settings().get('disabledModels') or [])
    if enabled:
        disabled.discard(spec.id)
    else:
        disabled.add(spec.id)
    save_settings({'disabledModels': sorted(disabled)})
    return jsonify({'success': True, 'enabled': enabled})


@ai_engine_bp.route('/api/mex/ai-engine/install', methods=['POST'])
def install_engine():
    from core.state import get_socketio
    data = request.get_json(silent=True) or {}
    variant = (data.get('variant') or '').strip().lower() or None
    if variant not in (None, 'cuda', 'cpu'):
        return jsonify({'success': False,
                        'error': "variant must be 'cuda' or 'cpu'"}), 400
    started, err = installer.start_install(get_socketio(), variant=variant)
    if not started:
        return jsonify({'success': False, 'error': err}), 409
    return jsonify({'success': True, 'started': True})


@ai_engine_bp.route('/api/mex/ai-engine/routing', methods=['GET', 'POST'])
def tier_routing():
    if request.method == 'GET':
        return jsonify({'success': True,
                        'routing': load_settings().get('tierRouting')})
    data = request.get_json(silent=True) or {}
    updates = {}
    for tier in routing.TIERS:
        if tier not in data:
            continue
        target = data[tier]
        if target is None:
            updates[tier] = None
            continue
        spec = find((target or {}).get('model'))
        if spec is None:
            return jsonify({'success': False,
                            'error': f'unknown model for {tier}: '
                                     f'{(target or {}).get("model")}'}), 400
        updates[tier] = {'provider': 'openrouter' if spec.kind == 'api' else 'local',
                         'model': spec.repo_id if spec.kind == 'api' else spec.id}
    settings = save_settings({'tierRouting': updates})
    return jsonify({'success': True, 'routing': settings['tierRouting']})


@ai_engine_bp.route('/api/mex/ai-engine/resolve', methods=['POST'])
def resolve_tasks():
    data = request.get_json(silent=True) or {}
    client_key = bool(data.get('clientHasKey'))
    out = []
    for task in (data.get('tasks') or []):
        kind = (task or {}).get('kind') or 'material'
        tier = (task or {}).get('tier') or \
            ('strong' if kind in ('backdrop', 'scene') else 'standard')
        try:
            resolved = routing.resolve(
                tier,
                override_model=(task or {}).get('model'),
                client_key=client_key)
            out.append({'kind': kind, 'tier': tier, **resolved})
        except routing.RoutingError as e:
            out.append({'kind': kind, 'tier': tier, 'error': str(e)})
    return jsonify({'success': True, 'tasks': out})


@ai_engine_bp.route('/api/mex/ai-engine/planners', methods=['GET'])
def local_planners():
    """Installed Ollama models usable as LOCAL planner LLMs (planner ids are
    'ollama:<name>'). Empty when Ollama isn't installed/running."""
    from blueprints.skin_lab_ai import list_local_planners
    models = list_local_planners()
    return jsonify({'success': True, 'ollamaAvailable': bool(models),
                    'local': models})


@ai_engine_bp.route('/api/mex/ai-engine/stats', methods=['GET'])
def generation_stats():
    try:
        days = int(request.args.get('days', 90))
    except ValueError:
        days = 90
    return jsonify({'success': True, **telemetry.aggregate(days)})
