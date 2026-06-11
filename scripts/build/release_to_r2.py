"""
release_to_r2.py - publish the built SSBM Nucleus installer to the R2 releases
bucket, vAMP-style (versioned exe + latest.json manifest).

Run AFTER scripts/build/build.bat has produced the installer in the repo root.

    python scripts/build/release_to_r2.py [--notes "What's new"] [--dry-run]

What it does:
  1. Reads the version from package.json.
  2. Finds the electron-builder installer ("SSBM Nucleus Setup <ver>.exe").
  3. Copies it to releases/SSBM-Nucleus_<ver>_x64-setup.exe and writes
     releases/latest.json {version, notes, pub_date, url, sha256, size}.
  4. Uploads both to s3://<bucket>/windows/ on R2 (boto3 if installed,
     otherwise prints the aws-cli commands to run).

R2 config comes from environment variables (same shape as vAMP's release job):
    R2_ACCOUNT_ID          Cloudflare account id
    R2_ACCESS_KEY_ID       R2 API token key id
    R2_SECRET_ACCESS_KEY   R2 API token secret
    R2_RELEASES_BUCKET     bucket name (default: nucleus-releases)
With no credentials set, behaves like --dry-run: artifacts are still produced
locally and the upload commands are printed.

Public URL assumes a custom domain on the bucket, e.g.
releases.ssbmnucleus.net -> https://releases.ssbmnucleus.net/windows/latest.json
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RELEASES_DIR = REPO_ROOT / 'releases'
RELEASES_BASE_URL = 'https://releases.ssbmnucleus.net/windows'
DEFAULT_BUCKET = 'nucleus-releases'

# Known credential files (first hit wins; env vars already set take precedence)
CRED_FILES = [
    Path('D:/ssbm-backup/r2.env'),
    REPO_ROOT.parent / 'meleeWebsite' / 'backend' / '.env',
]


def load_creds():
    """Populate R2_* env vars from the saved credential files if not set."""
    for f in CRED_FILES:
        if not f.exists():
            continue
        for line in f.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line.startswith('R2_') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())


def find_installer(version):
    """electron-builder names it '<productName> Setup <version>.exe'.
    Only accept the installer matching package.json's version - publishing a
    stale build under a new version number is the failure mode to avoid."""
    exact = REPO_ROOT / f'SSBM Nucleus Setup {version}.exe'
    if exact.exists():
        return exact
    others = sorted(REPO_ROOT.glob('SSBM Nucleus Setup *.exe'))
    if others:
        sys.exit(
            f'package.json says {version} but only found: '
            f'{", ".join(o.name for o in others)}.\n'
            f'Rebuild (scripts\\build\\build.bat) or fix package.json version.')
    return None


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--notes', default='')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--version', help='publish a specific version instead of '
                    'package.json (e.g. re-publishing an older built installer)')
    args = ap.parse_args()

    load_creds()
    version = args.version or json.loads(
        (REPO_ROOT / 'package.json').read_text(encoding='utf-8'))['version']
    if not re.match(r'^\d+\.\d+\.\d+', version):
        sys.exit(f'unexpected version in package.json: {version!r}')

    installer = find_installer(version)
    if not installer:
        sys.exit('No installer exe found in repo root - run scripts\\build\\build.bat first.')
    print(f'version:   {version}')
    print(f'installer: {installer.name} ({installer.stat().st_size / 1_048_576:.1f} MB)')

    # --- stage artifacts ------------------------------------------------------
    RELEASES_DIR.mkdir(exist_ok=True)
    exe_name = f'SSBM-Nucleus_{version}_x64-setup.exe'
    staged_exe = RELEASES_DIR / exe_name
    shutil.copy2(installer, staged_exe)

    manifest = {
        'version': version,
        'notes': args.notes or f'SSBM Nucleus v{version}',
        'pub_date': datetime.now(timezone.utc).isoformat(),
        'platforms': {
            'windows-x86_64': {
                'url': f'{RELEASES_BASE_URL}/{exe_name}',
                'sha256': sha256_of(staged_exe),
                'size': staged_exe.stat().st_size,
            },
        },
    }
    manifest_path = RELEASES_DIR / 'latest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'staged:    {staged_exe}')
    print(f'manifest:  {manifest_path}')

    # --- upload ---------------------------------------------------------------
    bucket = os.environ.get('R2_RELEASES_BUCKET', DEFAULT_BUCKET)
    account = os.environ.get('R2_ACCOUNT_ID')
    key_id = os.environ.get('R2_ACCESS_KEY_ID')
    secret = os.environ.get('R2_SECRET_ACCESS_KEY')

    if args.dry_run or not (account and key_id and secret):
        if not args.dry_run:
            print('\nR2 credentials not set (R2_ACCOUNT_ID / R2_ACCESS_KEY_ID / '
                  'R2_SECRET_ACCESS_KEY) - skipping upload.')
        endpoint = f'https://{account or "<ACCOUNT_ID>"}.r2.cloudflarestorage.com'
        print('\nTo upload manually (aws cli):')
        print(f'  set AWS_ACCESS_KEY_ID=...&& set AWS_SECRET_ACCESS_KEY=...')
        print(f'  aws s3 cp "{staged_exe}" s3://{bucket}/windows/{exe_name} --endpoint-url {endpoint}')
        print(f'  aws s3 cp "{manifest_path}" s3://{bucket}/windows/latest.json --endpoint-url {endpoint}')
        return

    try:
        import boto3
    except ImportError:
        sys.exit('boto3 not installed - pip install boto3, or use the aws-cli commands above.')

    s3 = boto3.client(
        's3',
        endpoint_url=f'https://{account}.r2.cloudflarestorage.com',
        aws_access_key_id=key_id,
        aws_secret_access_key=secret,
        region_name='auto',
    )
    print(f'\nUploading to s3://{bucket}/windows/ ...')
    s3.upload_file(str(staged_exe), bucket, f'windows/{exe_name}',
                   ExtraArgs={'ContentType': 'application/octet-stream'})
    s3.upload_file(str(manifest_path), bucket, 'windows/latest.json',
                   ExtraArgs={'ContentType': 'application/json',
                              'CacheControl': 'no-cache'})
    print(f'done:')
    print(f'  {RELEASES_BASE_URL}/{exe_name}')
    print(f'  {RELEASES_BASE_URL}/latest.json')


if __name__ == '__main__':
    main()
