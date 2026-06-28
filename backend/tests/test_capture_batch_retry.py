"""
Orchestration tests for the bulk DAS stage-screenshot capture
(/api/mex/test-in-game/capture-stage-batch).

These pin the behaviour the user asked for:
  * on a Dolphin crash, RETRY the SAME ISO (no per-variant ISO rebuilds) — so
    the number of builds equals the number of rounds, never one-per-variant;
  * a variant that crashed Dolphin is moved to the END of the next boot so it
    can't block the variants queued behind it;
  * whatever is captured is still returned (partial results) when one variant
    keeps failing.

The heavy deps (the ISO builder + the Dolphin driver) are mocked; we only
exercise the retry/pipeline orchestration in the blueprint.
"""
import sys
import time
import threading
from pathlib import Path

from flask import Flask

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import blueprints.test_in_game as tig
import test_build
import ingame.capture as cap


class _FakeSocketIO:
    def __init__(self):
        self.events = []
        self.done = threading.Event()

    def emit(self, name, payload=None):
        self.events.append((name, payload))
        if name in ('capture_batch_complete', 'capture_error'):
            self.done.set()

    def complete(self):
        return next((p for n, p in self.events if n == 'capture_batch_complete'), None)


def _run_batch(client, variants, vanilla):
    return client.post('/api/mex/test-in-game/capture-stage-batch', json={
        'variants': variants,
        'vanillaIsoPath': str(vanilla),
        'slippiDolphinPath': 'C:/fake/Dolphin.exe',
    })


def _setup(monkeypatch, tmp_path):
    monkeypatch.setattr(tig, 'STORAGE_PATH', tmp_path)
    fake = _FakeSocketIO()
    monkeypatch.setattr(tig, 'get_socketio', lambda: fake)
    # one valid base stage we can "drive"
    monkeypatch.setattr(test_build, 'DAS_STAGES',
                        {'GrNBa': ('GrNBa', 'battlefield')}, raising=False)
    monkeypatch.setattr(test_build, 'BATCH_BUTTONS', ['a', 'b', 'c', 'd'], raising=False)

    builds = []

    def fake_build(vanilla, stage_groups, out_iso, log=None):
        builds.append(stage_groups)
        Path(out_iso).write_bytes(b'ISO')  # so the finally-unlink has something
        placed = []
        for g in stage_groups:
            for i, vid in enumerate(g['variantIds']):
                placed.append({'stageCode': g['stageCode'], 'variantId': vid,
                               'button': test_build.BATCH_BUTTONS[i]})
        return placed

    monkeypatch.setattr(test_build, 'build_stage_skin_multibatch_iso', fake_build)

    vanilla = tmp_path / 'vanilla.iso'
    vanilla.write_bytes(b'V')

    app = Flask(__name__)
    app.register_blueprint(tig.test_in_game_bp)
    return app.test_client(), fake, builds, vanilla


def test_crasher_is_retried_on_same_iso_and_moved_last(monkeypatch, tmp_path):
    client, fake, builds, vanilla = _setup(monkeypatch, tmp_path)

    calls = []  # ordered id-lists received by each capture_stage_batch boot

    def fake_capture(iso_path, slippi, runs_root, variants, emit=None, log=None):
        ids = [v['id'] for v in variants]
        calls.append(ids)
        if len(calls) == 1:
            # First boot: capture the first, then "Dolphin crashes" on v1.
            return {'ok': True, 'shots': [{'id': ids[0], 'button': 'a', 'png': b'P'}],
                    'failures': [], 'reason': 'Dolphin exited mid-batch.',
                    'crashed_id': ids[1]}
        # Retry boot: capture everything that's left.
        return {'ok': True,
                'shots': [{'id': i, 'button': 'a', 'png': b'P'} for i in ids],
                'failures': [], 'reason': 'captured all', 'crashed_id': None}

    monkeypatch.setattr(cap, 'capture_stage_batch', fake_capture)

    variants = [{'stageCode': 'GrNBa', 'stageFolder': 'bf', 'variantId': f'v{i}',
                 'name': f'V{i}'} for i in range(3)]
    assert _run_batch(client, variants, vanilla).status_code == 200
    assert fake.done.wait(timeout=10)

    # ONE round -> exactly ONE build (no per-variant ISO rebuilds).
    assert len(builds) == 1
    # Two boots of the SAME iso: the initial + one retry.
    assert len(calls) == 2
    # On the retry, the crasher (GrNBa:v1) is queued LAST.
    assert calls[1][-1] == 'GrNBa:v1'
    # All three captured in the end.
    comp = fake.complete()
    assert comp['captured'] == 3 and comp['total'] == 3


def test_persistent_crasher_yields_partial_results(monkeypatch, tmp_path):
    client, fake, builds, vanilla = _setup(monkeypatch, tmp_path)

    bad = 'GrNBa:v1'

    def fake_capture(iso_path, slippi, runs_root, variants, emit=None, log=None):
        ids = [v['id'] for v in variants]
        # Capture everyone except the persistently-bad one, which crashes Dolphin.
        good = [{'id': i, 'button': 'a', 'png': b'P'} for i in ids if i != bad]
        crashed = bad if bad in ids else None
        return {'ok': bool(good), 'shots': good, 'failures': [],
                'reason': 'Dolphin exited mid-batch.' if crashed else 'ok',
                'crashed_id': crashed}

    monkeypatch.setattr(cap, 'capture_stage_batch', fake_capture)

    variants = [{'stageCode': 'GrNBa', 'stageFolder': 'bf', 'variantId': f'v{i}',
                 'name': f'V{i}'} for i in range(3)]
    assert _run_batch(client, variants, vanilla).status_code == 200
    assert fake.done.wait(timeout=10)

    assert len(builds) == 1  # still one build only
    comp = fake.complete()
    # Two good shots returned despite the one stubborn crasher.
    assert comp['captured'] == 2 and comp['total'] == 3
    failed = [r for r in comp['results'] if not r['ok']]
    assert len(failed) == 1 and failed[0]['variantId'] == 'v1'
    # Bounded: initial boot + MAX_DOLPHIN_RETRIES, no infinite loop / per-variant ISOs.


def test_unsupported_stage_skipped_without_build(monkeypatch, tmp_path):
    client, fake, builds, vanilla = _setup(monkeypatch, tmp_path)
    monkeypatch.setattr(cap, 'capture_stage_batch',
                        lambda *a, **k: {'ok': False, 'shots': [], 'failures': [],
                                         'reason': 'x', 'crashed_id': None})

    variants = [{'stageCode': 'GrZZ', 'stageFolder': 'zz', 'variantId': 'v0', 'name': 'Z'}]
    assert _run_batch(client, variants, vanilla).status_code == 200
    assert fake.done.wait(timeout=10)
    assert len(builds) == 0  # nothing buildable
    comp = fake.complete()
    assert comp['captured'] == 0
    assert comp['results'][0]['reason'] == 'unsupported stage'
