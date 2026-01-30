#!/usr/bin/env python3
"""
ISO Dump Scanner - Extract ISOs and find new skins not in vault

Usage:
    python scan_iso_dumps.py                           # Scan existing dumps in ISO DUMPS folder
    python scan_iso_dumps.py --extract path1.iso ...   # Extract ISOs only (no scan)
    python scan_iso_dumps.py --iso path1.iso ...       # Extract and scan ISOs
    python scan_iso_dumps.py --csp                     # Enable CSP comparison (runs once at end)
"""
import os
import sys
import json
import hashlib
import shutil
import tempfile
import argparse
import subprocess
import zipfile
from pathlib import Path

# Add paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
UTILITY_DIR = PROJECT_ROOT / "utility" / "website" / "backend" / "tools" / "processor"
DAT_PROCESSOR_DIR = PROJECT_ROOT / "utility" / "website" / "backend" / "app" / "services"
sys.path.insert(0, str(UTILITY_DIR))
sys.path.insert(0, str(DAT_PROCESSOR_DIR))

from detect_character import DATParser
from dat_processor import validate_for_slippi
from generate_csp import generate_csp

# Paths
ISO_DUMPS_DIR = PROJECT_ROOT / "ISO DUMPS"
STORAGE_PATH = PROJECT_ROOT / "storage"
OUTPUT_DIR = PROJECT_ROOT / "output" / "new_skins_from_dumps"
VANILLA_ASSETS_DIR = PROJECT_ROOT / "utility" / "assets" / "vanilla"
WIT_EXE = PROJECT_ROOT / "tools" / "wit-v3.05a-r8638-cygwin64" / "bin" / "wit.exe"

# Character file extensions
CHAR_EXTENSIONS = {'.dat', '.lat', '.rat', '.uat', '.vat', '.wat', '.xat', '.yat', '.zat',
                   '.aat', '.bat', '.cat', '.eat', '.fat', '.gat', '.hat', '.iat', '.jat', '.kat',
                   '.1at', '.2at', '.3at', '.4at', '.5at', '.6at', '.7at', '.8at', '.9at', '.0at'}


def compute_dat_hash(filepath):
    """Compute MD5 hash of file data"""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def compute_slippi_fixed_hash(filepath):
    """Apply Slippi fix and return hash of fixed version"""
    try:
        with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as tmp:
            shutil.copy2(filepath, tmp.name)
            tmp_path = tmp.name

        try:
            result = validate_for_slippi(tmp_path, auto_fix=True)
            if result.get('fix_applied'):
                with open(tmp_path, 'rb') as f:
                    return hashlib.md5(f.read()).hexdigest()
            return None
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass
    except:
        return None


def apply_slippi_fix(filepath, output_path):
    """Apply Slippi fix and save to output_path. Returns True if fix was applied."""
    try:
        shutil.copy2(filepath, output_path)
        result = validate_for_slippi(str(output_path), auto_fix=True)
        return result.get('fix_applied', False)
    except Exception as e:
        print(f"    Warning: Slippi fix failed for {filepath}: {e}")
        return False


def load_vault_hashes():
    """Load all DAT hashes from vault metadata"""
    metadata_file = STORAGE_PATH / 'metadata.json'
    if not metadata_file.exists():
        return set()

    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    hashes = set()
    for char_name, char_data in metadata.get('characters', {}).items():
        for skin in char_data.get('skins', []):
            if skin.get('dat_hash'):
                hashes.add(skin['dat_hash'])

    return hashes


def load_vanilla_hashes():
    """Load hashes of vanilla costume DATs"""
    hashes = set()
    if not VANILLA_ASSETS_DIR.exists():
        return hashes

    for dat_file in VANILLA_ASSETS_DIR.rglob('*.dat'):
        with open(dat_file, 'rb') as f:
            hashes.add(hashlib.md5(f.read()).hexdigest())

    return hashes


def load_vault_csp_hashes():
    """Load CSP perceptual hashes from vault"""
    metadata_file = STORAGE_PATH / 'metadata.json'
    if not metadata_file.exists():
        return {}

    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    hashes = {}
    for char, data in metadata.get('characters', {}).items():
        for skin in data.get('skins', []):
            if skin.get('csp_hash'):
                hashes[skin['csp_hash']] = f"{char}/{skin['id']}"

    return hashes


def extract_iso(iso_path, output_dir):
    """Extract ISO using wit"""
    if not WIT_EXE.exists():
        print(f"ERROR: wit not found at {WIT_EXE}")
        print("Download from: https://wit.wiimm.de/")
        return None

    print(f"  Extracting: {iso_path.name}...", end=" ", flush=True)
    result = subprocess.run(
        [str(WIT_EXE), "EXTRACT", str(iso_path), str(output_dir)],
        capture_output=True, text=True
    )

    if result.returncode != 0:
        print(f"FAILED")
        print(f"    wit error: {result.stderr[:200]}")
        return None

    print("OK")
    return output_dir


def is_character_file(filepath):
    """Check if file is a character costume file"""
    basename = os.path.basename(filepath).lower()
    ext = os.path.splitext(basename)[1]
    if not basename.startswith('pl'):
        return False
    if ext not in CHAR_EXTENSIONS:
        return False
    if basename in ['plco.dat']:
        return False
    return True


def identify_character(filepath):
    """Use DATParser to identify character from DAT file"""
    try:
        parser = DATParser(filepath)
        parser.read_dat()

        is_costume = parser.is_character_costume()
        if not is_costume:
            return None, None, "data_mod"

        character, symbol = parser.detect_character()
        if not character:
            return None, None, "unknown"

        costume_code = parser.get_character_filename()
        return character, costume_code, "costume"
    except Exception as e:
        return None, None, f"error: {e}"


def run_csp_comparison(new_skins, vault_csp_hashes, skip_chars=None):
    """Run CSP comparison pass to catch slot-duplicates"""
    skip_chars = skip_chars or []
    skip_chars_lower = [c.lower() for c in skip_chars]

    try:
        import imagehash
        from PIL import Image
        from generate_csp import generate_csp
    except ImportError as e:
        print(f"  CSP comparison unavailable: {e}")
        return new_skins, 0

    # Filter out skipped characters
    chars_to_check = {k: v for k, v in new_skins.items()
                      if k.lower() not in skip_chars_lower}
    skipped_skins = {k: v for k, v in new_skins.items()
                     if k.lower() in skip_chars_lower}

    if skip_chars:
        skipped_count = sum(len(v) for v in skipped_skins.values())
        print(f"  Skipping {len(skip_chars)} characters ({skipped_count} skins): {', '.join(skip_chars)}")

    total = sum(len(v) for v in chars_to_check.values())
    print(f"\n{'='*60}")
    print(f"PASS 3: CSP comparison ({total} skins)...")
    print(f"  Estimated time: ~{total * 8 // 60} minutes")
    print("="*60)

    csp_matched = 0
    checked = 0
    filtered_skins = dict(skipped_skins)  # Keep skipped chars as-is

    for char, skins in chars_to_check.items():
        kept = []
        for filepath, costume_code, file_hash in skins:
            checked += 1
            if checked % 20 == 0:
                print(f"  Progress: {checked}/{total} ({csp_matched} matches found)")

            try:
                csp_path = generate_csp(str(filepath))
                if not csp_path or not os.path.exists(csp_path):
                    kept.append((filepath, costume_code, file_hash))
                    continue

                img = Image.open(csp_path)
                new_hash = imagehash.phash(img, hash_size=8)
                img.close()
                os.unlink(csp_path)

                # Check for match (strict: distance <= 5)
                matched = False
                for vault_hash_str in vault_csp_hashes:
                    vault_hash = imagehash.hex_to_hash(vault_hash_str)
                    if new_hash - vault_hash <= 5:
                        csp_matched += 1
                        matched = True
                        break

                if not matched:
                    kept.append((filepath, costume_code, file_hash))

            except Exception:
                kept.append((filepath, costume_code, file_hash))

        if kept:
            filtered_skins[char] = kept

    print(f"  CSP matches removed: {csp_matched}")
    return filtered_skins, csp_matched


def extract_all_isos(iso_paths):
    """Extract multiple ISOs to ISO DUMPS folder"""
    print(f"\n{'='*60}")
    print(f"EXTRACTING {len(iso_paths)} ISOs")
    print("="*60)

    ISO_DUMPS_DIR.mkdir(exist_ok=True)
    extracted = 0
    skipped = 0

    for iso_path in iso_paths:
        iso_path = Path(iso_path)
        if not iso_path.exists():
            print(f"  ERROR: Not found: {iso_path}")
            continue

        # Skip .nkit.iso files
        if '.nkit' in iso_path.name.lower():
            print(f"  SKIP (nkit): {iso_path.name}")
            skipped += 1
            continue

        # Use ISO name as folder name
        extract_dir = ISO_DUMPS_DIR / iso_path.stem
        if extract_dir.exists():
            print(f"  SKIP (exists): {iso_path.name}")
            skipped += 1
            continue

        if extract_iso(iso_path, extract_dir):
            extracted += 1

    print(f"\nExtracted: {extracted}, Skipped: {skipped}")
    return extracted


def scan_all_dumps(vault_hashes, vanilla_hashes):
    """Scan all folders in ISO DUMPS as one combined dataset"""
    print(f"\n{'='*60}")
    print("SCANNING ALL DUMPS")
    print("="*60)

    # Find all character files across all dumps
    all_files = []
    for dump_dir in ISO_DUMPS_DIR.iterdir():
        if not dump_dir.is_dir():
            continue
        for root, dirs, files in os.walk(dump_dir):
            for f in files:
                filepath = os.path.join(root, f)
                if is_character_file(filepath):
                    all_files.append(filepath)

    print(f"Found {len(all_files)} character files across all dumps")

    # PASS 1: Hash-based filtering
    new_skins = {}
    seen_hashes = set()
    stats = {
        'existing': 0, 'vanilla': 0, 'dupes': 0,
        'data_mod': 0, 'unknown': 0, 'errors': 0
    }

    print("\nPASS 1: Hash-based filtering...")
    for i, filepath in enumerate(all_files):
        if (i + 1) % 200 == 0:
            print(f"  Progress: {i+1}/{len(all_files)}")

        file_hash = compute_dat_hash(filepath)

        if file_hash in vault_hashes:
            stats['existing'] += 1
            continue
        if file_hash in vanilla_hashes:
            stats['vanilla'] += 1
            continue
        if file_hash in seen_hashes:
            stats['dupes'] += 1
            continue
        seen_hashes.add(file_hash)

        character, costume_code, status = identify_character(filepath)

        if status == "data_mod":
            stats['data_mod'] += 1
            continue
        elif status == "unknown" or character is None:
            stats['unknown'] += 1
            if "Unknown" not in new_skins:
                new_skins["Unknown"] = []
            new_skins["Unknown"].append((filepath, os.path.basename(filepath), file_hash))
            continue
        elif "error" in status:
            stats['errors'] += 1
            continue

        if character not in new_skins:
            new_skins[character] = []
        new_skins[character].append((filepath, costume_code, file_hash))

    print(f"\n  Pass 1 results:")
    print(f"    Already in vault: {stats['existing']}")
    print(f"    Vanilla costumes: {stats['vanilla']}")
    print(f"    Dupes within dumps: {stats['dupes']}")
    print(f"    Data mods (skipped): {stats['data_mod']}")
    print(f"    Errors: {stats['errors']}")
    print(f"    Candidates for pass 2: {sum(len(v) for v in new_skins.values())}")

    # PASS 2: Slippi-fixed hash check
    print(f"\n{'='*60}")
    print("PASS 2: Slippi-fixed hash check...")
    print("="*60)

    total = sum(len(v) for v in new_skins.values())
    slippi_matched = 0
    checked = 0
    filtered_skins = {}

    for char, skins in new_skins.items():
        kept = []
        for filepath, costume_code, file_hash in skins:
            checked += 1
            if checked % 100 == 0:
                print(f"  Progress: {checked}/{total} ({slippi_matched} matches)")

            fixed_hash = compute_slippi_fixed_hash(filepath)
            if fixed_hash and fixed_hash in vault_hashes:
                slippi_matched += 1
                continue

            kept.append((filepath, costume_code, file_hash))

        if kept:
            filtered_skins[char] = kept

    stats['slippi'] = slippi_matched
    print(f"  Slippi-fixed matches removed: {slippi_matched}")

    return filtered_skins, stats, len(all_files)


def export_skins(new_skins, output_dir, limit=None):
    """Export new skins as import-ready ZIP packages (Slippi-fixed DAT + CSP)"""
    if not new_skins:
        print("\nNo new skins to export.")
        return

    # Clear old export
    if output_dir.exists():
        shutil.rmtree(output_dir)

    print(f"\nExporting to: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    total = sum(len(v) for v in new_skins.values())
    if limit:
        total = min(total, limit)
        print(f"  (Limited to {limit} skins for testing)")
    exported = 0
    csp_generated = 0
    slippi_fixed = 0

    for char, skins in new_skins.items():
        if limit and exported >= limit:
            break

        char_folder = output_dir / char
        char_folder.mkdir(exist_ok=True)

        for filepath, costume_code, file_hash in skins:
            if limit and exported >= limit:
                break

            exported += 1
            if exported % 20 == 0 or (limit and exported == limit):
                print(f"  Progress: {exported}/{total}")

            # Determine names
            if costume_code:
                zip_name = f"{costume_code}_{file_hash[:8]}.zip"
                dat_name = f"{costume_code}.dat"
            else:
                base_name = os.path.splitext(os.path.basename(filepath))[0]
                zip_name = f"{base_name}_{file_hash[:8]}.zip"
                dat_name = f"{base_name}.dat"

            zip_path = char_folder / zip_name

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Create temp file for potentially-fixed DAT
                with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as tmp:
                    tmp_dat_path = tmp.name

                try:
                    # Apply Slippi fix (copies file and fixes in place)
                    if apply_slippi_fix(filepath, tmp_dat_path):
                        slippi_fixed += 1

                    # Add DAT to ZIP
                    zf.write(tmp_dat_path, dat_name)

                    # Generate CSP from the fixed DAT
                    csp_path = generate_csp(tmp_dat_path)
                    if csp_path and os.path.exists(csp_path):
                        zf.write(csp_path, "csp.png")
                        csp_generated += 1
                        try:
                            os.unlink(csp_path)
                        except:
                            pass
                finally:
                    try:
                        os.unlink(tmp_dat_path)
                    except:
                        pass

    print(f"\nExport complete!")
    print(f"  ZIPs created: {exported}")
    print(f"  CSPs generated: {csp_generated}")
    print(f"  Slippi fixes applied: {slippi_fixed}")


def main():
    parser = argparse.ArgumentParser(description='Scan ISO dumps for new skins')
    parser.add_argument('--extract', type=str, nargs='+', help='Extract ISOs only (no scan)')
    parser.add_argument('--iso', type=str, nargs='+', help='Extract and scan ISOs')
    parser.add_argument('--csp', action='store_true', help='Enable CSP comparison (runs once at end)')
    parser.add_argument('--skip-chars', type=str, nargs='+', help='Characters to skip in CSP comparison')
    parser.add_argument('--no-export', action='store_true', help='Skip exporting files')
    parser.add_argument('--limit', type=int, help='Limit export to N skins (for testing)')
    parser.add_argument('--char', type=str, nargs='+', help='Only export skins for these characters (e.g., "Fox" "Mario")')
    args = parser.parse_args()

    print("="*60)
    print("ISO DUMP SCANNER - Finding New Skins")
    print("="*60)

    # Extract-only mode
    if args.extract:
        extract_all_isos(args.extract)
        print("\nExtraction complete. Run without --extract to scan.")
        return

    # Extract + scan mode
    if args.iso:
        extract_all_isos(args.iso)

    # Check we have something to scan
    if not ISO_DUMPS_DIR.exists() or not any(ISO_DUMPS_DIR.iterdir()):
        print("ERROR: No dumps found in ISO DUMPS folder!")
        print("Use --extract or --iso to extract ISOs first.")
        return

    # Load hashes
    print("\nLoading vault hashes...")
    vault_hashes = load_vault_hashes()
    print(f"  {len(vault_hashes)} existing skins in vault")

    print("Loading vanilla hashes...")
    vanilla_hashes = load_vanilla_hashes()
    print(f"  {len(vanilla_hashes)} vanilla costumes")

    vault_csp_hashes = None
    if args.csp:
        print("Loading CSP hashes...")
        vault_csp_hashes = load_vault_csp_hashes()
        print(f"  {len(vault_csp_hashes)} CSP hashes")

    # Scan all dumps together
    new_skins, stats, total_files = scan_all_dumps(vault_hashes, vanilla_hashes)

    # PASS 3: CSP comparison (optional, runs once at the end)
    csp_matched = 0
    if args.csp and vault_csp_hashes:
        new_skins, csp_matched = run_csp_comparison(new_skins, vault_csp_hashes, args.skip_chars)

    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Total files scanned: {total_files}")
    print(f"Already in vault: {stats['existing']}")
    print(f"Vanilla costumes: {stats['vanilla']}")
    print(f"Dupes within dumps: {stats['dupes']}")
    print(f"Slippi-fixed matches: {stats['slippi']}")
    if args.csp:
        print(f"CSP matches: {csp_matched}")
    print(f"Data mods: {stats['data_mod']}")
    print(f"Unknown: {stats['unknown']}")
    print(f"Errors: {stats['errors']}")
    print(f"\nNEW UNIQUE SKINS: {sum(len(v) for v in new_skins.values())}")

    print("\nBy Character:")
    for char in sorted(new_skins.keys()):
        print(f"  {char}: {len(new_skins[char])}")

    # Export
    if not args.no_export:
        skins_to_export = new_skins
        if args.char:
            # Filter to just the specified characters
            char_filter = [c.lower() for c in args.char]
            matched = {k: v for k, v in new_skins.items() if k.lower() in char_filter}
            if not matched:
                print(f"\nNo skins found for: {', '.join(args.char)}")
                print(f"Available: {', '.join(sorted(new_skins.keys()))}")
                return
            skins_to_export = matched
            print(f"\nFiltering to {', '.join(args.char)}: {sum(len(v) for v in matched.values())} skins")
        export_skins(skins_to_export, OUTPUT_DIR, limit=args.limit)


if __name__ == "__main__":
    main()
