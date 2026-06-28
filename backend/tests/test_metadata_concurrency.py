"""
Regression test for the metadata.json read-modify-write race that silently
dropped vault entries (the seeded Giga Bowser vanished when several custom
characters were imported at once). A multi-file drag fires many concurrent
/import/file requests on Flask's threaded server; without a lock + atomic write
their appends clobber each other. `_append_custom_character` must keep every
entry, including a pre-existing one.
"""
import sys
import json
import threading
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import blueprints.custom_characters as cc


def test_concurrent_appends_keep_all_entries(tmp_path, monkeypatch):
    meta = tmp_path / 'metadata.json'
    # pre-existing builtin entry (stands in for the seeded Giga Bowser)
    meta.write_text(json.dumps({
        'characters': {}, 'stages': {}, 'custom_stages': [],
        'custom_characters': [{'slug': 'giga-bowser', 'name': 'Giga Bowser', 'builtin': True}],
    }), encoding='utf-8')
    monkeypatch.setattr(cc, 'METADATA_FILE', meta)

    n = 24
    barrier = threading.Barrier(n)  # maximise overlap

    def worker(i):
        barrier.wait()
        cc._append_custom_character({'slug': f'char-{i}', 'name': f'Char {i}', 'source': 'zip'})

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    data = json.loads(meta.read_text(encoding='utf-8'))
    slugs = {c['slug'] for c in data['custom_characters']}
    # the builtin survived AND all 24 concurrent appends landed — nothing lost
    assert 'giga-bowser' in slugs
    assert all(f'char-{i}' in slugs for i in range(n))
    assert len(data['custom_characters']) == n + 1


def test_write_is_atomic_valid_json(tmp_path, monkeypatch):
    meta = tmp_path / 'metadata.json'
    monkeypatch.setattr(cc, 'METADATA_FILE', meta)
    cc._write_metadata({'custom_characters': [{'slug': 'x'}]})
    # readable as valid JSON and no leftover temp file
    assert json.loads(meta.read_text(encoding='utf-8'))['custom_characters'][0]['slug'] == 'x'
    assert not (tmp_path / 'metadata.json.tmp').exists()
