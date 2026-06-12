"""AI Model Studio backend — prompt or mesh file → rigged Melee costume.

The model analog of the AI Skin Studio (skin_lab_ai): instead of repainting a
vanilla costume's textures, this generates (or accepts) a 3D MODEL and rigs
it onto the character's preserved skeleton:

  theme ──(assetFarm: image → Hunyuan3D)──> mesh.glb ─┐
  mesh upload (.glb/.obj/.smd) ────────────────────────┤
                                                       ▼
        rig kit (HSDRawViewer --model export, cached per character)
                                                       ▼
        modellab.rig: decimate → split to vanilla DObj count → align →
        closest-point weight transfer → SMD + textures
                                                       ▼
        HSDRawViewer --model import (preserve skeleton + flags + textures)
                                                       ▼
        preview render (--csp) → save through the unified intake

POST /api/mex/model-lab/create {character, theme?, meshFile?, meshName?,
                                rotY?, maxTris?}
  -> background thread; STOPS after the mesh exists and emits
     modellab_mesh_ready {preview, character, canRegenerate} — a software
     render of the RAW model so a bad generation can be thrown away without
     paying for rigging. modellab_progress / modellab_error as usual.
POST /api/mex/model-lab/rig -> rig the approved pending mesh; events:
     modellab_progress, modellab_complete {success, preview, character}.
GET  /api/mex/model-lab/status -> {enabled, canGenerate, canUpload, running,
     hasPendingMesh, hasPending}
POST /api/mex/model-lab/save {name} -> vault via unified intake (CSP/stock
     come from the intake's auto-generation)
POST /api/mex/model-lab/discard
"""
import base64
import io
import os
import re
import shutil
import subprocess
import tempfile
import threading
import zipfile
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request

import logging

logger = logging.getLogger(__name__)

model_lab_bp = Blueprint('model_lab', __name__)

MODEL_LAB_ENABLED = os.environ.get('NUCLEUS_MODEL_LAB', '1') != '0'

# assetFarm checkout with its venv = local prompt->3D generation (dev setups).
# Without it the studio still works in mesh-upload mode.
ASSETFARM_DIR = Path(os.environ.get(
    'NUCLEUS_ASSETFARM', r'C:\Users\david\projects\assetFarm'))

_lock = threading.Lock()
_running = False
# the last finished generation, waiting on save/discard:
# {datBytes, character, datName, preview, workDir}
_pending = None
# a generated/uploaded mesh awaiting approval before rigging:
# {meshPath, workDir, character, theme, rotY, maxTris, preview}
_pending_mesh = None

_CHAR_TO_CODE = {
    'Fox': 'Fx', 'Falco': 'Fc', 'Captain Falcon': 'Ca', 'Donkey Kong': 'Dk',
    'Dr. Mario': 'Dr', 'Ganondorf': 'Gn', 'Kirby': 'Kb', 'Bowser': 'Kp',
    'Link': 'Lk', 'Luigi': 'Lg', 'Mario': 'Mr', 'Marth': 'Ms',
    'Mewtwo': 'Mt', 'Ness': 'Ns', 'Peach': 'Pe', 'Pichu': 'Pc',
    'Pikachu': 'Pk', 'Jigglypuff': 'Pr', 'Roy': 'Fe', 'Samus': 'Ss',
    'Yoshi': 'Ys', 'Zelda': 'Ze', 'Young Link': 'Cl',
    'Mr. Game & Watch': 'Gw', 'Ice Climbers': 'Pp', 'Sheik': 'Sk',
}


def _hsdraw_exe():
    from core.config import HSDRAW_EXE
    return Path(HSDRAW_EXE)


def _storage():
    from core.config import STORAGE_PATH
    return Path(STORAGE_PATH)


def _emit(event, payload):
    from core.state import get_socketio
    sio = get_socketio()
    if sio:
        sio.emit(event, payload)


def _progress(stage, percentage, message):
    _emit('modellab_progress',
          {'stage': stage, 'percentage': percentage, 'message': message})


def _joint_symbol(dat_path):
    """The costume's *_Share_joint root symbol (skip the matanim one)."""
    raw = Path(dat_path).read_bytes()
    syms = re.findall(rb'[\x20-\x7e]{8,}', raw)
    for s in syms:
        s = s.decode('ascii', 'replace')
        if s.endswith('_joint') and 'matanim' not in s:
            return s
    raise RuntimeError(f'no joint symbol found in {dat_path}')


def _vanilla_costume(character):
    """Vanilla Nr costume DAT for the character (rig-kit + import base)."""
    code = _CHAR_TO_CODE.get(character)
    if not code:
        raise RuntimeError(f'unsupported character: {character}')
    from blueprints.viewer import find_vanilla_costume_file
    dat = find_vanilla_costume_file(character, f'Pl{code}Nr')
    if not dat or not Path(dat).exists():
        raise RuntimeError(f'vanilla costume Pl{code}Nr not found for {character}')
    return Path(dat), f'Pl{code}Nr'


def _run_hsdraw(args, timeout=600):
    from core.config import get_subprocess_args
    r = subprocess.run([str(_hsdraw_exe()), *args], capture_output=True,
                       text=True, timeout=timeout, **get_subprocess_args())
    out = (r.stdout or '') + (r.stderr or '')
    return r.returncode, out


def _rig_kit(character, log):
    """Per-character rig kit (SMD + weights + textures), exported once."""
    kit_dir = _storage() / 'modellab' / 'rigkits' / character.replace(' ', '_')
    kit_smd = kit_dir / 'rigkit.smd'
    if kit_smd.exists():
        return kit_smd
    kit_dir.mkdir(parents=True, exist_ok=True)
    dat, _ = _vanilla_costume(character)
    sym = _joint_symbol(dat)
    log(f'exporting rig kit for {character} ({sym})')
    code, out = _run_hsdraw(['--model', 'export', str(dat), sym, str(kit_smd)])
    if code != 0 or not kit_smd.exists():
        raise RuntimeError(f'rig kit export failed:\n{out[-800:]}')
    return kit_smd


def _generate_mesh(theme, work_dir, log):
    """Prompt -> textured GLB via the local assetFarm checkout."""
    af_python = ASSETFARM_DIR / '.venv' / 'Scripts' / 'python.exe'
    if not af_python.exists():
        raise RuntimeError('local 3D generation is not available '
                           '(assetFarm not found) — upload a mesh instead')
    out_before = {p for p in (ASSETFARM_DIR / 'output').rglob('*.glb')}
    log('generating mesh (image → Hunyuan3D)… this takes a few minutes')
    r = subprocess.run(
        [str(af_python), '-m', 'assetfarm', 'generate', 'prompt_to_3d',
         '-p', f'{theme}, full body, T-pose, front view, game character',
         '-n', 'modellab', '--project', 'nucleus-model-lab'],
        cwd=str(ASSETFARM_DIR), capture_output=True, text=True, timeout=3600)
    if r.returncode != 0:
        raise RuntimeError(f'mesh generation failed:\n{(r.stdout or "")[-400:]}'
                           f'\n{(r.stderr or "")[-400:]}')
    new = sorted({p for p in (ASSETFARM_DIR / 'output').rglob('*.glb')} - out_before,
                 key=lambda p: p.stat().st_mtime)
    if not new:
        raise RuntimeError('mesh generation produced no .glb output')
    mesh = work_dir / 'generated.glb'
    shutil.copyfile(new[-1], mesh)
    return mesh


def _render_preview(dat_path, work_dir):
    png = work_dir / 'preview.png'
    code, out = _run_hsdraw(['--csp', str(dat_path), str(png)], timeout=300)
    if not png.exists():
        return None
    return 'data:image/png;base64,' + base64.b64encode(png.read_bytes()).decode()


def _mesh_stage(character, theme, mesh_path, work_dir):
    """Stage 1: obtain the mesh (generate or use the upload) and render a
    raw-model preview for approval. Returns the _pending_mesh dict."""
    log = lambda m: logger.info(f'[model-lab] {m}')  # noqa: E731

    if mesh_path is None:
        _progress('generate', 15, 'Generating the 3D model…')
        mesh_path = _generate_mesh(theme, work_dir, log)

    _progress('mesh_preview', 85, 'Rendering the model preview…')
    from modellab.rig import render_mesh_preview
    png = work_dir / 'mesh_preview.png'
    render_mesh_preview(mesh_path, png)
    preview = ('data:image/png;base64,'
               + base64.b64encode(png.read_bytes()).decode())

    return {
        'meshPath': str(mesh_path),
        'workDir': str(work_dir),
        'character': character,
        'theme': theme,
        'preview': preview,
    }


def _rig_stage(character, mesh_path, rot_y, max_tris, work_dir):
    """Stage 2 (after approval): rig the mesh, import it over the vanilla
    costume, render the costume preview. Returns the _pending session dict."""
    log = lambda m: logger.info(f'[model-lab] {m}')  # noqa: E731

    _progress('rigkit', 8, 'Preparing the character rig kit…')
    kit = _rig_kit(character, log)

    _progress('rig', 35, 'Rigging the model onto the skeleton…')
    from modellab.rig import rig_mesh
    rigged = work_dir / 'rigged.smd'
    code = _CHAR_TO_CODE.get(character)
    rig_mesh(str(kit), str(mesh_path), str(rigged),
             rot_y=rot_y or 0.0, max_tris=max_tris or 6000,
             char_code=f'Pl{code}' if code else None, log=log)

    _progress('import', 70, 'Building the costume DAT…')
    base_dat, code_nr = _vanilla_costume(character)
    sym = _joint_symbol(base_dat)
    out_dat = work_dir / f'{code_nr}.dat'
    rc, out = _run_hsdraw(['--model', 'import', str(base_dat), sym,
                           str(rigged), str(out_dat), '--strip-matanim'])
    if rc != 0 or not out_dat.exists():
        raise RuntimeError(f'model import failed:\n{out[-800:]}')

    _progress('preview', 90, 'Rendering the preview…')
    preview = _render_preview(out_dat, work_dir)

    return {
        'datBytes': out_dat.read_bytes(),
        'datName': f'{code_nr}.dat',
        'character': character,
        'preview': preview,
        'workDir': str(work_dir),
    }


@model_lab_bp.route('/api/mex/model-lab/status', methods=['GET'])
def status():
    can_generate = (ASSETFARM_DIR / '.venv' / 'Scripts' / 'python.exe').exists()
    return jsonify({
        'enabled': MODEL_LAB_ENABLED and _hsdraw_exe().exists(),
        'canGenerate': can_generate,
        'canUpload': True,
        'running': _running,
        'hasPendingMesh': _pending_mesh is not None,
        'hasPending': _pending is not None,
    })


@model_lab_bp.route('/api/mex/model-lab/create', methods=['POST'])
def create():
    """Stage 1: generate/accept the mesh, render the raw-model preview, stop.
    Rigging only happens after approval via /rig."""
    global _running, _pending, _pending_mesh
    data = request.get_json(silent=True) or {}
    character = data.get('character')
    theme = (data.get('theme') or '').strip()
    mesh_b64 = data.get('meshFile')          # data URI or raw base64
    mesh_name = data.get('meshName') or 'upload.glb'
    rot_y = float(data.get('rotY') or 0)
    max_tris = int(data.get('maxTris') or 6000)

    if not character:
        return jsonify({'success': False, 'error': 'character is required'}), 400
    if not theme and not mesh_b64:
        return jsonify({'success': False,
                        'error': 'provide a theme or upload a mesh'}), 400

    with _lock:
        if _running:
            return jsonify({'success': False,
                            'error': 'a generation is already running'}), 409
        _running = True
        _pending = None
        if _pending_mesh is not None:          # regenerate: drop the old mesh
            shutil.rmtree(_pending_mesh.get('workDir', ''), ignore_errors=True)
            _pending_mesh = None

    work_dir = Path(tempfile.mkdtemp(prefix='modellab_'))
    mesh_path = None
    if mesh_b64:
        payload = mesh_b64.split(',', 1)[1] if mesh_b64.startswith('data:') else mesh_b64
        suffix = Path(mesh_name).suffix or '.glb'
        mesh_path = work_dir / f'upload{suffix}'
        mesh_path.write_bytes(base64.b64decode(payload))

    app = current_app._get_current_object()

    def run():
        global _running, _pending_mesh
        try:
            with app.app_context():
                session = _mesh_stage(character, theme, mesh_path, work_dir)
                session['rotY'] = rot_y
                session['maxTris'] = max_tris
                _pending_mesh = session
                _emit('modellab_mesh_ready', {
                    'success': True,
                    'preview': session['preview'],
                    'character': character,
                    'canRegenerate': bool(theme),
                })
        except Exception as e:
            logger.exception('[model-lab] mesh stage failed')
            shutil.rmtree(work_dir, ignore_errors=True)
            _emit('modellab_error', {'error': str(e)})
        finally:
            with _lock:
                _running = False

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True})


@model_lab_bp.route('/api/mex/model-lab/rig', methods=['POST'])
def rig():
    """Stage 2: rig the approved pending mesh into a costume."""
    global _running, _pending, _pending_mesh
    if _pending_mesh is None:
        return jsonify({'success': False, 'error': 'no mesh to rig'}), 400
    with _lock:
        if _running:
            return jsonify({'success': False,
                            'error': 'a generation is already running'}), 409
        _running = True

    mesh = _pending_mesh
    app = current_app._get_current_object()

    def run():
        global _running, _pending, _pending_mesh
        try:
            with app.app_context():
                session = _rig_stage(mesh['character'], Path(mesh['meshPath']),
                                     mesh.get('rotY') or 0,
                                     mesh.get('maxTris') or 6000,
                                     Path(mesh['workDir']))
                _pending = session
                _pending_mesh = None    # consumed (same workDir carries over)
                _emit('modellab_complete', {
                    'success': True,
                    'preview': session['preview'],
                    'character': mesh['character'],
                })
        except Exception as e:
            logger.exception('[model-lab] rig stage failed')
            _emit('modellab_error', {'error': str(e)})
        finally:
            with _lock:
                _running = False

    threading.Thread(target=run, daemon=True).start()
    return jsonify({'success': True})


@model_lab_bp.route('/api/mex/model-lab/save', methods=['POST'])
def save():
    """Zip the pending DAT and route it through the unified intake (which
    classifies it as a costume and auto-generates CSP + stock icon)."""
    global _pending
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'name is required'}), 400
    if _pending is None:
        return jsonify({'success': False, 'error': 'nothing to save'}), 400

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(_pending['datName'], _pending['datBytes'])

    client = current_app.test_client()
    form = {'file': (io.BytesIO(buf.getvalue()), f'{name}.zip'),
            'custom_title': name}
    for passthrough in ('slippi_action', 'duplicate_action'):
        if data.get(passthrough):
            form[passthrough] = data[passthrough]
    res = client.post('/api/mex/import/file', data=form,
                      content_type='multipart/form-data')

    payload = res.get_json(silent=True) or {}
    payload.setdefault('success', res.status_code == 200)
    if res.status_code == 200:
        shutil.rmtree(_pending.get('workDir', ''), ignore_errors=True)
        _pending = None
    return jsonify(payload), res.status_code


@model_lab_bp.route('/api/mex/model-lab/discard', methods=['POST'])
def discard():
    global _pending, _pending_mesh
    if _pending is not None:
        shutil.rmtree(_pending.get('workDir', ''), ignore_errors=True)
        _pending = None
    if _pending_mesh is not None:
        shutil.rmtree(_pending_mesh.get('workDir', ''), ignore_errors=True)
        _pending_mesh = None
    return jsonify({'success': True})
