"""
mod_pool.py - query the local ssbm-backup as a pool of installable mods.

Reads the newest Supabase dump in <backup-root>/db/*.json plus the mirrored
uploads tree, and lets the harness list mods by character/tag and assemble
an installable costume zip (DAT + generated CSP/stock) for the Nucleus
backend's unified import endpoint (/api/mex/import/file).

Usage:
    python mod_pool.py stats
    python mod_pool.py list --character Kirby [--json] [--limit 20]
    python mod_pool.py show 13195
    python mod_pool.py fetch --post 13195 [--out <dir>] [--json]
    python mod_pool.py fetch --file 7484 [--out <dir>] [--json]

Stdlib only - no venv needed.
"""
import argparse
import json
import sys
import zipfile
from pathlib import Path

DEFAULT_BACKUP_ROOT = Path('D:/ssbm-backup')
DEFAULT_OUT = Path(__file__).resolve().parents[2] / 'tests' / 'artifacts' / 'nucleus' / 'mod-pool'


class ModPool:
    def __init__(self, backup_root=DEFAULT_BACKUP_ROOT, dump_path=None):
        self.root = Path(backup_root)
        self.uploads = self.root / 'uploads' / 'posts'
        if dump_path is None:
            dumps = sorted((self.root / 'db').glob('*.json'))
            if not dumps:
                raise FileNotFoundError(f'no DB dumps in {self.root / "db"}')
            dump_path = dumps[-1]
        self.dump_path = Path(dump_path)
        d = json.loads(self.dump_path.read_text(encoding='utf-8'))
        self.posts = {p['id']: p for p in d['posts']}
        self.files = {f['id']: f for f in d['files']}
        self.screenshots = d['screenshots']
        tags = {t['id']: t['tag_name'] for t in d['tags']}
        self.post_tags = {}
        for pt in d['post_tags']:
            self.post_tags.setdefault(pt['post_id'], []).append(tags.get(pt['tag_id'], '?'))
        self.files_by_post = {}
        for f in d['files']:
            self.files_by_post.setdefault(f['post_id'], []).append(f)

    # -- path helpers --------------------------------------------------------

    def local_path(self, url):
        """Map a /uploads/posts/... URL to the local mirror; None if unset."""
        if not url:
            return None
        prefix = '/uploads/posts/'
        if not url.startswith(prefix):
            return None
        return self.uploads / url[len(prefix):].replace('/', '\\')

    def local_exists(self, url):
        p = self.local_path(url)
        return bool(p and p.exists())

    # -- queries -------------------------------------------------------------

    def query(self, character=None, tag=None, file_type=None, search=None):
        """Return [(post, [matching file rows])] sorted by post id."""
        out = []
        for pid, post in sorted(self.posts.items()):
            frows = self.files_by_post.get(pid, [])
            if character:
                frows = [f for f in frows if (f.get('character') or '').lower() == character.lower()]
                if not frows:
                    continue
            if file_type:
                frows = [f for f in frows if f.get('file_type') == file_type]
                if not frows:
                    continue
            if tag and not any(tag.lower() in t.lower() for t in self.post_tags.get(pid, [])):
                continue
            if search and search.lower() not in (post.get('title') or '').lower():
                continue
            out.append((post, frows))
        return out

    def post_summary(self, post, frows):
        return {
            'post_id': post['id'],
            'title': post.get('title'),
            'tags': self.post_tags.get(post['id'], []),
            'files': [self.file_summary(f) for f in frows],
        }

    def file_summary(self, f):
        return {
            'file_id': f['id'],
            'post_id': f['post_id'],
            'filename': f.get('filename'),
            'file_type': f.get('file_type'),
            'character': f.get('character'),
            'color': f.get('color'),
            'local': self.local_exists(f.get('file_url')),
            'has_csp': self.local_exists(f.get('csp_url')),
            'has_stock': self.local_exists(f.get('stock_url')),
        }

    # -- fetch: assemble installable zip(s) -----------------------------------

    def fetch_file(self, file_id, out_dir):
        """Assemble one costume zip (DAT + csp/stock) for a files-table row."""
        f = self.files[file_id]
        dat_path = self.local_path(f.get('file_url'))
        if not dat_path or not dat_path.exists():
            raise FileNotFoundError(f'file {file_id}: DAT not in local backup: {f.get("file_url")}')

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        stem = dat_path.stem
        ext = dat_path.suffix  # .dat or .usd
        zip_path = out_dir / f'pool_{f["post_id"]}_{file_id}_{stem}.zip'

        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(dat_path, f'{stem}{ext}')
            for url_key, suffix in (('csp_url', '_csp.png'), ('stock_url', '_stock.png')):
                p = self.local_path(f.get(url_key))
                if p and p.exists():
                    zf.write(p, f'{stem}{suffix}')

        return {
            'file_id': file_id,
            'post_id': f['post_id'],
            'character': f.get('character'),
            'color': f.get('color'),
            'zip': str(zip_path),
        }

    def fetch_post(self, post_id, out_dir, file_type='character_dat'):
        frows = [f for f in self.files_by_post.get(post_id, [])
                 if not file_type or f.get('file_type') == file_type]
        results, errors = [], []
        for f in frows:
            try:
                results.append(self.fetch_file(f['id'], out_dir))
            except FileNotFoundError as e:
                errors.append(str(e))
        return {'post_id': post_id, 'title': self.posts[post_id].get('title'),
                'zips': results, 'errors': errors}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['stats', 'list', 'show', 'fetch'])
    ap.add_argument('post_id', nargs='?', type=int, help='post id (for show)')
    ap.add_argument('--backup-root', default=str(DEFAULT_BACKUP_ROOT))
    ap.add_argument('--dump', help='explicit dump json (default: newest)')
    ap.add_argument('--character')
    ap.add_argument('--tag')
    ap.add_argument('--type', dest='file_type')
    ap.add_argument('--search')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--post', type=int, help='fetch all costume files of a post')
    ap.add_argument('--file', type=int, help='fetch one files-table row')
    ap.add_argument('--out', default=str(DEFAULT_OUT))
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    pool = ModPool(args.backup_root, args.dump)

    if args.command == 'stats':
        by_char = {}
        local = 0
        for f in pool.files.values():
            if f.get('file_type') == 'character_dat':
                by_char[f.get('character') or '?'] = by_char.get(f.get('character') or '?', 0) + 1
                if pool.local_exists(f.get('file_url')):
                    local += 1
        info = {'dump': str(pool.dump_path), 'posts': len(pool.posts),
                'files': len(pool.files), 'character_dats': sum(by_char.values()),
                'character_dats_local': local,
                'by_character': dict(sorted(by_char.items(), key=lambda x: -x[1]))}
        print(json.dumps(info, indent=2))

    elif args.command == 'list':
        rows = pool.query(args.character, args.tag, args.file_type or 'character_dat', args.search)
        if args.limit:
            rows = rows[:args.limit]
        if args.json:
            print(json.dumps([pool.post_summary(p, fr) for p, fr in rows], indent=2))
        else:
            for p, fr in rows:
                local = sum(1 for f in fr if pool.local_exists(f.get('file_url')))
                print(f'{p["id"]:>6}  {p.get("title","?")[:55]:<55} '
                      f'{len(fr)} dat(s), {local} local  '
                      f'[{", ".join(sorted({f.get("color") or "?" for f in fr}))}]')
            print(f'\n{len(rows)} posts')

    elif args.command == 'show':
        if not args.post_id:
            sys.exit('show requires a post id')
        p = pool.posts[args.post_id]
        out = pool.post_summary(p, pool.files_by_post.get(args.post_id, []))
        out['description'] = (p.get('description') or '')[:500]
        out['screenshots'] = [s['screenshot_url'] for s in pool.screenshots
                              if s['post_id'] == args.post_id]
        print(json.dumps(out, indent=2))

    elif args.command == 'fetch':
        if args.file:
            res = pool.fetch_file(args.file, args.out)
        elif args.post:
            res = pool.fetch_post(args.post, args.out, args.file_type or 'character_dat')
        else:
            sys.exit('fetch requires --file <id> or --post <id>')
        print(json.dumps(res, indent=2))


if __name__ == '__main__':
    main()
