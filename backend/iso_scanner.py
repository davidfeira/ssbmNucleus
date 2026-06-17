"""
ISO scanner - background scan pipeline for ripping new costume skins from ISOs.

Mirrors scripts/tools/scan_iso_dumps.py but wrapped as a callable module that
emits progress callbacks, generates CSPs/DATs per candidate skin into a
per-job work directory, and exposes the result grouped by character so a UI
can render selectable thumbnails.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from core.config import (
    PROJECT_ROOT, RESOURCES_DIR, STORAGE_PATH, OUTPUT_PATH, VANILLA_ASSETS_DIR,
    get_subprocess_args,
)

# These come from PROCESSOR_DIR / SERVICES_DIR which are already on sys.path
# via core.config import side effects.
from detect_character import DATParser
from dat_processor import validate_for_slippi
from generate_csp import HSDRAW_EXE, generate_csp

logger = logging.getLogger(__name__)

# ---------- Constants ----------

CHAR_EXTENSIONS = {
    '.dat', '.lat', '.rat', '.uat', '.vat', '.wat', '.xat', '.yat', '.zat',
    '.aat', '.bat', '.cat', '.eat', '.fat', '.gat', '.hat', '.iat', '.jat', '.kat',
    '.1at', '.2at', '.3at', '.4at', '.5at', '.6at', '.7at', '.8at', '.9at', '.0at',
}

def _resolve_wit_exe() -> Path:
    """Find wit.exe in either the bundled install or the dev repo."""
    rel = Path("tools") / "wit-v3.05a-r8638-cygwin64" / "bin" / "wit.exe"
    # In bundled mode RESOURCES_DIR points at the install's `resources/`, which
    # is where electron-builder lays the `extraResources` entries.
    bundled = RESOURCES_DIR / rel
    if bundled.exists():
        return bundled
    return PROJECT_ROOT / rel


WIT_EXE = _resolve_wit_exe()
SCAN_WORK_ROOT = OUTPUT_PATH / "iso_scan"
SCAN_CLEANUP_MAX_AGE_SECONDS = int(os.environ.get('NUCLEUS_ISO_SCAN_MAX_AGE_SECONDS', str(12 * 60 * 60)))


def _safe_scan_job_dir(job_id: str) -> Optional[Path]:
    """Return the direct child work dir for job_id, rejecting traversal."""
    if not job_id:
        return None
    job_name = Path(job_id).name
    if job_name != job_id:
        return None
    root = SCAN_WORK_ROOT.resolve()
    candidate = (SCAN_WORK_ROOT / job_id).resolve()
    if candidate.parent != root:
        return None
    return candidate


def _dir_size(path: Path) -> int:
    total = 0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                pass
    return total


def cleanup_stale_jobs(max_age_seconds: Optional[int] = SCAN_CLEANUP_MAX_AGE_SECONDS) -> dict:
    """Remove inactive ISO scan work dirs old enough to be considered stale."""
    SCAN_WORK_ROOT.mkdir(parents=True, exist_ok=True)
    now = time.time()
    removed: list[str] = []
    bytes_removed = 0
    with _jobs_lock:
        active_ids = set(_jobs.keys())

    for child in SCAN_WORK_ROOT.iterdir():
        if not child.is_dir() or child.name in active_ids:
            continue
        safe_child = _safe_scan_job_dir(child.name)
        if safe_child is None or safe_child != child.resolve():
            continue
        try:
            age_seconds = now - child.stat().st_mtime
        except OSError:
            continue
        if max_age_seconds is not None and max_age_seconds > 0 and age_seconds < max_age_seconds:
            continue
        try:
            bytes_removed += _dir_size(child)
            shutil.rmtree(child)
            removed.append(child.name)
        except Exception as e:
            logger.warning(f"[iso-scan][cleanup] failed to remove {child}: {e}")

    if removed:
        logger.info(
            f"[iso-scan][cleanup] removed {len(removed)} stale job dir(s), "
            f"{bytes_removed} bytes"
        )

    return {'removed': len(removed), 'bytes_removed': bytes_removed, 'job_ids': removed}

def _csp_parallelism() -> int:
    """Pick a worker count for thumbnail generation.

    Defaults to the machine's logical CPU count (HSDRawViewer is mostly
    I/O-bound on GPU/CPU swaps, so threads scale well once the file-lock
    collision is gone). Clamped to [1, 16] to avoid runaway RAM on huge boxes,
    and overridable via the MEX_CSP_PARALLELISM env var for tuning.
    """
    env = os.environ.get('MEX_CSP_PARALLELISM')
    if env and env.isdigit():
        return max(1, min(int(env), 32))
    cpus = os.cpu_count() or 2
    return max(1, min(cpus, 16))


CSP_PARALLELISM = _csp_parallelism()

# HSDRawViewer.Program.RunCSPGeneration has two hardcoded Thread.Sleep
# barriers (500ms after MainForm.OpenFile, 1000ms after form.Show) that
# wait for async WinForms / OpenGL initialization to settle. When N
# instances spin up simultaneously, those sleeps don't reliably cover the
# real init time and whichever process loses the race continues to render
# before its viewport is ready — that's the inconsistent blank-render /
# T-pose pattern the user kept hitting on Zelda, Mewtwo, Falco, etc.
#
# Workaround: serialize the *launch* of HSDRawViewer instances so each
# one gets clean run of its ~1.5s init window before the next one starts.
# After that they render in parallel as before. The default 1.5s matches
# Program.cs's combined Sleep budget; bump higher if you still see flaky
# renders, lower (or 0 to disable) if speed matters more than reliability.
_LAUNCH_STAGGER_S = float(os.environ.get('MEX_CSP_LAUNCH_STAGGER', '1.5'))
_launch_lock = threading.Lock()

# In-memory job registry. Bounded by user action; cleared on backend restart.
_jobs: dict[str, "IsoScanJob"] = {}
_jobs_lock = threading.Lock()


# ---------- Job state ----------

# Two-letter `Pl<Xx>...` prefix → canonical character name, per
# docs/research/new-414/Melee-Files.md. Used to override DATParser's symbol-based
# detection when filename and symbol disagree (e.g. male wireframe DATs share
# the "ftDataBoy" symbol with Young Link, so symbol alone tags the wireframe
# as Young Link). Filename is the more reliable signal — modders don't usually
# rename costume files, they just edit contents.
CHAR_CODE_TO_NAME = {
    'Bo': 'Male Wireframe',
    'Ca': 'C. Falcon',
    'Ch': 'Crazy Hand',
    'Cl': 'Young Link',
    'Dk': 'DK',
    'Dr': 'Dr. Mario',
    'Fc': 'Falco',
    'Fe': 'Roy',
    'Fx': 'Fox',
    'Gk': 'Giga Bowser',
    'Gl': 'Female Wireframe',
    'Gn': 'Ganondorf',
    'Gw': 'Mr. Game & Watch',
    'Kb': 'Kirby',
    'Kp': 'Bowser',
    'Lg': 'Luigi',
    'Lk': 'Link',
    'Mh': 'Master Hand',
    'Mr': 'Mario',
    'Ms': 'Marth',
    'Mt': 'Mewtwo',
    'Nn': 'Ice Climbers (Nana)',
    'Ns': 'Ness',
    'Pc': 'Pichu',
    'Pe': 'Peach',
    'Pk': 'Pikachu',
    'Pp': 'Ice Climbers',
    'Pr': 'Jigglypuff',
    'Sb': 'Sandbag',
    'Sk': 'Sheik',
    'Ss': 'Samus',
    'Ys': 'Yoshi',
    'Zd': 'Zelda',
}

_INTERNAL_TO_EXTERNAL = [
    0x08, 0x02, 0x00, 0x01, 0x04, 0x05, 0x06,
    0x13, 0x0B, 0x0C, 0x0E, 0x20, 0x0D, 0x10,
    0x11, 0x0F, 0x0A, 0x07, 0x09, 0x12, 0x15,
    0x16, 0x14, 0x18, 0x03, 0x19, 0x17, 0x1A,
    0x1E, 0x1B, 0x1C, 0x1D, 0x1F,
]

# Characters the user never wants surfaced in scan results. Wireframes and
# bosses aren't selectable in normal play so showing them as importable skins
# is just noise.
SKIP_CHARACTERS = {
    'Kirby',
    'Male Wireframe', 'Female Wireframe',
    'Master Hand', 'Crazy Hand', 'Giga Bowser', 'Sandbag',
}


def _character_from_filename(path: str) -> Optional[str]:
    """Map `PlXxYy.dat` -> character name via the 2-char code lookup table."""
    name = os.path.basename(path)
    stem = os.path.splitext(name)[0]
    if len(stem) < 4 or not stem.lower().startswith('pl'):
        return None
    return CHAR_CODE_TO_NAME.get(stem[2:4])


def _is_custom_fighter_file(path: str) -> bool:
    """True for costume files that belong to an m-ex CUSTOM fighter slot.

    Added fighters get freshly generated Pl codes (e.g. PlQpQg.dat in a build
    with a custom 'Qp' character). Their CONTENT still carries the symbols of
    whatever vanilla fighter they were cloned from, so symbol-based detection
    would happily misfile them as e.g. Fox skins — but they belong to the
    custom fighter (the custom-characters ISO scan extracts them properly,
    fighter + costumes together). Filename code not in the vanilla table =
    custom fighter slot.

    Extra COSTUME slots for vanilla fighters (PlFxYe, PlFxAg, ...) keep the
    vanilla character code and are NOT matched by this.
    """
    name = os.path.basename(path)
    stem = os.path.splitext(name)[0]
    if len(stem) < 4 or not stem.lower().startswith('pl'):
        return False
    return stem[2:4] not in CHAR_CODE_TO_NAME


@dataclass
class CandidateSkin:
    key: str
    character: str
    costume_code: str
    dat_path: str
    csp_path: Optional[str]
    stock_path: Optional[str]
    dat_hash: str
    source_iso: str
    # For Ice Climbers: the paired Nana DAT (when the primary is Popo) or
    # Popo DAT (when the primary is Nana). None for non-paired skins.
    paired_dat_path: Optional[str] = None
    paired_costume_code: Optional[str] = None


@dataclass
class IsoScanJob:
    job_id: str
    iso_paths: list[str]
    work_dir: Path
    status: str = 'pending'  # pending | extracting | scanning | slippi | csp | complete | error
    phase_message: str = ''
    percent: int = 0
    error: Optional[str] = None
    stats: dict = field(default_factory=lambda: {
        'existing': 0, 'vanilla': 0, 'dupes': 0,
        'slippi_matched': 0, 'data_mod': 0, 'custom_fighter': 0,
        'unknown': 0, 'errors': 0,
        'stock_icons': 0,
        'total_files': 0,
    })
    candidates: dict[str, list[CandidateSkin]] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    cancelled: bool = False

    def to_dict(self, csp_url_base: str) -> dict:
        chars = {}
        for char, skins in self.candidates.items():
            chars[char] = [
                {
                    'key': s.key,
                    'costume_code': s.costume_code,
                    'csp_url': f"{csp_url_base}/{s.key}/csp" if s.csp_path else None,
                    'source_iso': s.source_iso,
                    'dat_hash': s.dat_hash[:12],
                }
                for s in skins
            ]
        return {
            'job_id': self.job_id,
            'status': self.status,
            'phase_message': self.phase_message,
            'percent': self.percent,
            'error': self.error,
            'stats': self.stats,
            'characters': chars,
            'total_new': sum(len(v) for v in self.candidates.values()),
        }


# ---------- Helpers ----------

def _md5(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def _md5_file(path: str | Path) -> str:
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def _load_vault_hashes() -> set[str]:
    """Hashes of every DAT the user already has — both the *original* hash
    saved at import time and the actual stored zip contents.

    When `import_character_costume` runs with auto_fix=True (the default for
    scan-imports), metadata.json's `dat_hash` field records the PRE-fix hash
    of the source DAT, but the zip on disk stores the slippi-FIXED bytes.
    Those have different hashes. So when a modder distributes a skin in
    slippi-safe form and the user already has it, scanning that ISO would
    leak it as 'new' unless we also include the stored-zip hash. Solution:
    walk every storage/<Char>/*.zip, hash the inner DAT, add it to the set.
    Cheap one-shot at scan start.
    """
    out: set[str] = set()
    metadata_file = STORAGE_PATH / 'metadata.json'
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            for char_data in metadata.get('characters', {}).values():
                for skin in char_data.get('skins', []):
                    h = skin.get('dat_hash')
                    if h:
                        out.add(h)
        except Exception as e:
            logger.warning(f"[iso-scan][vault] metadata.json read failed: {e}")

    metadata_count = len(out)

    # Layer in hashes of the actual DAT bytes stored in each vault zip. These
    # may differ from metadata's dat_hash when auto_fix changed the file at
    # import time.
    import zipfile as _zipfile
    zip_count = 0
    if STORAGE_PATH.exists():
        for char_dir in STORAGE_PATH.iterdir():
            if not char_dir.is_dir() or char_dir.name in ('xdelta', 'das', 'bundles'):
                continue
            for zip_path in char_dir.glob('*.zip'):
                try:
                    with _zipfile.ZipFile(zip_path, 'r') as zf:
                        for inner in zf.namelist():
                            lower = inner.lower()
                            if lower.endswith(('.dat', '.usd')) and 'plco' not in lower:
                                out.add(hashlib.md5(zf.read(inner)).hexdigest())
                                zip_count += 1
                                break  # one DAT per costume zip
                except Exception as e:
                    logger.debug(f"[iso-scan][vault] could not hash {zip_path}: {e}")

    logger.info(
        f"[iso-scan][vault] loaded {len(out)} unique hashes "
        f"({metadata_count} from metadata.json dat_hash, "
        f"{zip_count} from vault zip contents)"
    )
    return out


# Known vanilla DAT hashes that aren't always present in user vanilla folders.
# The first-run vanilla extraction occasionally drops costumes whose data is
# split across the `.dat` and `.usd` localized variants (Red Falcon is the
# known case: `utility/assets/vanilla/C. Falcon/PlCaRe/` exists with csp.png
# and stock.png but no PlCaRe.dat). Without this supplemental set, those
# costumes leak through every scan as bogus "new" skins because their ISO
# hash has no match in the vanilla folder.
_SUPPLEMENTAL_VANILLA_HASHES = {
    'ce3dfba030d0ecbeeaf0c288aca29f0b': 'PlCaRe.dat (Red Falcon, vanilla)',
}


def _load_vanilla_hashes() -> set[str]:
    out = set()
    if not VANILLA_ASSETS_DIR.exists():
        return out
    for dat in VANILLA_ASSETS_DIR.rglob('*.dat'):
        try:
            out.add(_md5_file(dat))
        except Exception:
            pass

    # Layer on the supplemental hashes and report which slots they cover so
    # gaps in the user's vanilla folder are visible at scan start.
    for h, label in _SUPPLEMENTAL_VANILLA_HASHES.items():
        if h not in out:
            out.add(h)
            logger.info(
                f"[iso-scan][vanilla] using supplemental hash for {label} — "
                f"missing from {VANILLA_ASSETS_DIR}"
            )

    # Warn for any vanilla subfolder named `PlXxYy` that has no DAT in it.
    # These slots will leak as 'new skins' in scans of any modded ISO until
    # the user re-runs vanilla extraction or we add the hash above.
    try:
        for char_dir in VANILLA_ASSETS_DIR.iterdir():
            if not char_dir.is_dir():
                continue
            for slot_dir in char_dir.iterdir():
                if not slot_dir.is_dir():
                    continue
                if not slot_dir.name.startswith('Pl') or len(slot_dir.name) != 6:
                    continue
                if not any(slot_dir.glob('*.dat')):
                    logger.warning(
                        f"[iso-scan][vanilla] {char_dir.name}/{slot_dir.name}/ "
                        f"has no .dat — that slot will leak as new in scans"
                    )
    except OSError:
        pass

    return out


def _is_character_file(path: str) -> bool:
    """Decide whether a filename looks like a per-color costume archive.

    Per docs/research/new-414/Melee-Files.md the Melee `Pl*` namespace covers several
    different file kinds — only one of them is a costume:

        PlCo.dat        common player data    (skip)
        PlXx.dat        shared character data (skip — 4-char stem)
        PlXxAJ.dat      animation joint file  (skip — 'AJ' suffix)
        PlXxYy.dat      *costume* archive     (keep — 6-char stem)

    DATParser.is_character_costume() filters out anything that slipped through
    at the content level via the `Ply...5K_Share_joint` symbol check, but it's
    expensive (parses every DAT). This pre-filter trims the obvious shared /
    animation files by name alone so we never even hash them.

    Color (last 2 chars) is intentionally NOT constrained — mods are free to
    invent new slot codes like `Zz`, `Q1`, etc., and we want to surface those.
    """
    name = os.path.basename(path).lower()
    if not name.startswith('pl'):
        return False
    if name == 'plco.dat':
        return False
    stem, ext = os.path.splitext(name)
    if ext not in CHAR_EXTENSIONS:
        return False
    # PlXx.dat (shared) is 4 chars; PlXxYy.dat (costume) is 6.
    if len(stem) != 6:
        return False
    # PlXxAJ.dat is the animation joint archive — same length as a costume
    # but the trailing "AJ" gives it away.
    if stem.endswith('aj'):
        return False
    return True


def _slippi_fixed_hash(dat_path: str) -> Optional[str]:
    """Apply Slippi auto-fix to a copy of the DAT and hash the result.

    Returns the fixed-file MD5, or None if no fix was applied / on error.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as tmp:
            shutil.copy2(dat_path, tmp.name)
            tmp_path = tmp.name
        try:
            res = validate_for_slippi(tmp_path, auto_fix=True)
            if res.get('fix_applied'):
                return _md5_file(tmp_path)
            return None
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    except Exception:
        return None


def _ensure_dat_ext(name: str) -> str:
    """Normalize an archive filename to .dat (or leave .usd alone).

    MEX-built ISOs use extra-slot extensions (.lat / .rat / .xat / ...) as a
    slot marker, but the binary format is identical to .dat. We rename to
    .dat so HSDRawViewer and the import helpers (which only recognise .dat
    and .usd) treat them as costumes. Don't *append* .dat on top of the old
    extension — replace it, otherwise we get names like PlMrNr.lat.dat.
    """
    if not name:
        return 'costume.dat'
    if name.lower().endswith(('.dat', '.usd')):
        return name
    stem, _ = os.path.splitext(name)
    return stem + '.dat'


def _stock_lookup_key(costume_code: str) -> str:
    """Normalize a costume filename/code for stock lookup."""
    return os.path.splitext(os.path.basename(costume_code or ''))[0].lower()


def _to_external_id(internal_id: int, character_count: int = 0x21) -> int:
    """Port of mexLib.MexFighterIDConverter.ToExternalID for vanilla ids."""
    base_character_count = 0x21
    internal_special_count = 6
    external_special_count = 7
    added_chars = character_count - base_character_count
    is_special = internal_id >= character_count - internal_special_count

    if internal_id >= character_count - internal_special_count - added_chars and not is_special:
        return (base_character_count - external_special_count) + (
            internal_id - (base_character_count - internal_special_count)
        )

    external_id = internal_id + (-added_chars if is_special else 0)
    if external_id < len(_INTERNAL_TO_EXTERNAL):
        external_id = _INTERNAL_TO_EXTERNAL[external_id]
    if is_special:
        external_id += added_chars
    if internal_id == 11:  # Popo special case in mexLib; stock extractor skips Nana.
        external_id = character_count - 1
    return external_id


def _vanilla_stock_frame(internal_id: int, costume_index: int) -> Optional[int]:
    """Frame used by vanilla IfAll Stc_scemdls for a costume stock icon."""
    if internal_id > 26 or internal_id == 11:
        return None
    external_id = _to_external_id(internal_id, 0x21)
    if internal_id == 7:
        external_id = 25
    elif external_id == 26:
        pass
    elif external_id >= 19:
        external_id -= 1
    return external_id + costume_index * 30


class _DolReader:
    """Minimal big-endian DOL address reader for Melee's costume tables."""

    def __init__(self, path: Path):
        self.data = path.read_bytes()
        self.section_offsets = [self._u32_at(i * 4) for i in range(18)]
        self.section_addresses = [self._u32_at(0x48 + i * 4) for i in range(18)]
        self.section_lengths = [self._u32_at(0x90 + i * 4) for i in range(18)]

    def _u32_at(self, offset: int) -> int:
        if offset < 0 or offset + 4 > len(self.data):
            return 0
        return int.from_bytes(self.data[offset:offset + 4], 'big')

    def _to_file_offset(self, address: int) -> Optional[int]:
        if address & 0x80000000:
            for section_offset, section_address, section_length in zip(
                self.section_offsets, self.section_addresses, self.section_lengths
            ):
                if not section_address:
                    continue
                if section_address <= address < section_address + section_length:
                    return section_offset + (address - section_address)
            return None
        return address if 0 <= address < len(self.data) else None

    def read_u8(self, address: int) -> Optional[int]:
        offset = self._to_file_offset(address)
        if offset is None or offset >= len(self.data):
            return None
        return self.data[offset]

    def read_u32(self, address: int) -> Optional[int]:
        offset = self._to_file_offset(address)
        if offset is None or offset + 4 > len(self.data):
            return None
        return self._u32_at(offset)

    def read_string(self, address: int) -> str:
        offset = self._to_file_offset(address)
        if offset is None:
            return ''
        end = offset
        while end < len(self.data) and self.data[end] != 0:
            end += 1
        try:
            return self.data[offset:end].decode('ascii', errors='ignore')
        except Exception:
            return ''

    def read_string_pointer(self, address: int) -> str:
        pointer = self.read_u32(address)
        if not pointer:
            return ''
        return self.read_string(pointer)


def _read_dol_costume_stock_frames(dol_path: Path) -> dict[str, int]:
    """Map costume stem -> vanilla stock animation frame using main.dol order."""
    reader = _DolReader(dol_path)
    mapping: dict[str, int] = {}

    for internal_id in range(0x21):
        costume_count = reader.read_u8(0x803C0EC0 + 0x4 + internal_id * 8)
        costume_pointer = reader.read_u32(0x803C2360 + internal_id * 4)
        if not costume_count or not costume_pointer:
            continue

        for costume_index in range(costume_count):
            frame = _vanilla_stock_frame(internal_id, costume_index)
            if frame is None:
                continue
            file_name = reader.read_string_pointer(costume_pointer + costume_index * 0x0C)
            key = _stock_lookup_key(file_name)
            if key:
                mapping[key] = frame

    return mapping


def _find_disc_file(root: Path, preferred_names: tuple[str, ...]) -> Optional[Path]:
    """Find a file under a WIT extraction, preferring names in order."""
    matches: dict[str, Path] = {}
    wanted = {n.lower() for n in preferred_names}
    for path in root.rglob('*'):
        if path.is_file() and path.name.lower() in wanted:
            matches.setdefault(path.name.lower(), path)
    for name in preferred_names:
        match = matches.get(name.lower())
        if match:
            return match
    return None


def _run_stock_icon_export(ifall_path: Path, out_dir: Path) -> Optional[dict]:
    if not os.path.exists(HSDRAW_EXE):
        logger.warning(f"[iso-scan][stock] HSDRawViewer not found: {HSDRAW_EXE}")
        return None
    out_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [HSDRAW_EXE, '--stock-icons', 'export', str(ifall_path), str(out_dir)],
        capture_output=True, text=True, **get_subprocess_args(),
    )
    if result.returncode != 0:
        logger.warning(
            f"[iso-scan][stock] export failed for {ifall_path}: "
            f"{(result.stderr or result.stdout)[-500:]}"
        )
        return None
    manifest_path = out_dir / 'manifest.json'
    if not manifest_path.exists():
        logger.warning(f"[iso-scan][stock] no manifest written for {ifall_path}")
        return None
    try:
        return json.loads(manifest_path.read_text(encoding='utf-8'))
    except Exception as e:
        logger.warning(f"[iso-scan][stock] bad manifest for {ifall_path}: {e}")
        return None


def _build_stock_map_for_iso(iso_dir: Path, out_dir: Path) -> dict[str, str]:
    """Extract actual ISO stock icons and map costume stem -> PNG path."""
    ifall_path = _find_disc_file(iso_dir, ('IfAll.usd', 'IfAll.dat'))
    dol_path = _find_disc_file(iso_dir, ('main.dol',))
    if not ifall_path or not dol_path:
        logger.info(
            f"[iso-scan][stock] {iso_dir.name}: missing "
            f"{'IfAll' if not ifall_path else 'main.dol'}, stock extraction skipped"
        )
        return {}

    try:
        costume_frames = _read_dol_costume_stock_frames(dol_path)
    except Exception as e:
        logger.warning(f"[iso-scan][stock] {iso_dir.name}: DOL parse failed: {e}")
        return {}
    if not costume_frames:
        logger.info(f"[iso-scan][stock] {iso_dir.name}: no DOL costume frames found")
        return {}

    manifest = _run_stock_icon_export(ifall_path, out_dir)
    if not manifest:
        return {}
    if manifest.get('format') != 'vanilla':
        logger.info(
            f"[iso-scan][stock] {iso_dir.name}: {manifest.get('format')} stock "
            "table is not DOL-frame compatible, stock extraction skipped"
        )
        return {}

    frame_to_png: dict[int, str] = {}
    for entry in manifest.get('entries', []):
        try:
            frame = int(entry.get('frame'))
            width = int(entry.get('width', 0))
            height = int(entry.get('height', 0))
        except (TypeError, ValueError):
            continue
        # Costume stock icons are 24x24; skip timer digits and cursor fragments
        # that live in the same Stc_scemdls animation bank.
        if width != 24 or height != 24:
            continue
        filename = entry.get('filename')
        if not filename:
            continue
        png_path = out_dir / filename
        if png_path.exists():
            frame_to_png[frame] = str(png_path)

    stock_map = {
        key: frame_to_png[frame]
        for key, frame in costume_frames.items()
        if frame in frame_to_png
    }
    logger.info(
        f"[iso-scan][stock] {iso_dir.name}: mapped {len(stock_map)} stocks "
        f"from {manifest.get('format')} IfAll ({len(costume_frames)} DOL costumes)"
    )
    return stock_map


def _build_stock_maps(extract_root: Path, stocks_root: Path) -> dict[str, dict[str, str]]:
    maps: dict[str, dict[str, str]] = {}
    for iso_dir in extract_root.iterdir():
        if not iso_dir.is_dir():
            continue
        stock_map = _build_stock_map_for_iso(iso_dir, stocks_root / iso_dir.name)
        if stock_map:
            maps[iso_dir.name] = stock_map
    return maps


def _ic_color_suffix(costume_code: str) -> Optional[str]:
    """Extract the 2-char Melee color suffix from PlPpXX / PlNnXX costume codes."""
    stem = os.path.splitext(costume_code)[0]
    return stem[-2:] if len(stem) >= 4 else None


def _pair_ice_climbers(pre_candidates: list[dict]) -> list[dict]:
    """Combine Popo + Nana DATs from the same (source_iso, color) into a single
    paired 'Ice Climbers' candidate. Unmatched halves pass through as solo
    entries — never silently dropped."""
    popo = [c for c in pre_candidates if c['character'] == 'Ice Climbers']
    nana = [c for c in pre_candidates if c['character'] == 'Ice Climbers (Nana)']
    other = [c for c in pre_candidates
             if c['character'] not in ('Ice Climbers', 'Ice Climbers (Nana)')]

    logger.info(
        f"[iso-scan][ic] entering pairing: {len(popo)} Popo, "
        f"{len(nana)} Nana, {len(other)} other characters"
    )
    for p in popo:
        logger.info(
            f"[iso-scan][ic]   Popo: code={p.get('costume_code')!r:14} "
            f"suf={_ic_color_suffix(p.get('costume_code'))!r:6} "
            f"source={p.get('source_iso')!r}"
        )
    for n in nana:
        logger.info(
            f"[iso-scan][ic]   Nana: code={n.get('costume_code')!r:14} "
            f"suf={_ic_color_suffix(n.get('costume_code'))!r:6} "
            f"source={n.get('source_iso')!r}"
        )

    # Index Nana by (source, color suffix). Each Nana can be claimed once.
    nana_index: dict[tuple[str, str], dict] = {}
    for n in nana:
        suf = _ic_color_suffix(n['costume_code'])
        if suf:
            nana_index.setdefault((n['source_iso'], suf), n)

    paired: list[dict] = []
    unmatched_popo: list[dict] = []
    for p in popo:
        suf = _ic_color_suffix(p['costume_code'])
        match = nana_index.pop((p['source_iso'], suf), None) if suf else None
        if not match:
            unmatched_popo.append(p)
            continue
        out = dict(p)
        out['paired_path'] = match['path']
        out['paired_costume_code'] = match['costume_code']
        logger.info(
            f"[iso-scan][ic] PAIR {p.get('costume_code')} <-> "
            f"{match.get('costume_code')}  (suf={suf!r}, "
            f"source={p.get('source_iso')!r}) — exact suffix match"
        )
        paired.append(out)

    # Fallback pairing for ISOs where Popo/Nana don't share suffixes
    # (e.g. Akaneia ships PlPpNr + PlPpBu + PlNnGr — no shared suffix, but
    # they're clearly meant to go together since the modder usually only
    # adds 1-2 IC pairs per ISO). We can't *truly* match without ground-truth
    # metadata, but greedy pairing-by-order within the same source ISO is
    # the practical heuristic — the user said "we kind of just have to guess".
    leftover_nana = list(nana_index.values())
    by_source_popo: dict[str, list[dict]] = {}
    for p in unmatched_popo:
        by_source_popo.setdefault(p['source_iso'], []).append(p)
    by_source_nana: dict[str, list[dict]] = {}
    for n in leftover_nana:
        by_source_nana.setdefault(n['source_iso'], []).append(n)

    guess_pairs = 0
    for source, popos in by_source_popo.items():
        nanas = by_source_nana.get(source, [])
        for p, n in zip(popos, nanas):
            out = dict(p)
            out['paired_path'] = n['path']
            out['paired_costume_code'] = n['costume_code']
            logger.info(
                f"[iso-scan][ic] PAIR {p.get('costume_code')} <-> "
                f"{n.get('costume_code')}  (suf mismatch, "
                f"source={source!r}) — guessed pairing"
            )
            paired.append(out)
            guess_pairs += 1
        # Anything left over in popos beyond min(len(popos), len(nanas)) is
        # truly unmatched — pair with a placeholder Nana=None so generate_csp
        # falls through to solo render rather than dropping the skin entirely.
        for p in popos[len(nanas):]:
            logger.info(
                f"[iso-scan][ic] SOLO Popo {p.get('costume_code')!r} — no "
                f"Nana left to guess-pair in source={source!r}, rendering solo"
            )
            paired.append(dict(p))
        for n in nanas[len(popos):]:
            # Lone Nana with no Popo at all: solo Nana — generate_csp's Ice
            # Climbers path renders her solo when no pair_file is provided.
            logger.info(
                f"[iso-scan][ic] SOLO Nana {n.get('costume_code')!r} — no "
                f"Popo left to guess-pair in source={source!r}, rendering solo"
            )
            paired.append(dict(n))

    # Nanas whose source had no unmatched Popos at all:
    for source, nanas in by_source_nana.items():
        if source in by_source_popo:
            continue  # already handled in the loop above
        for n in nanas:
            logger.info(
                f"[iso-scan][ic] SOLO Nana {n.get('costume_code')!r} — no "
                f"unmatched Popo in source={source!r}, rendering solo"
            )
            paired.append(dict(n))

    logger.info(
        f"[iso-scan][ic] pairing done: {len(paired)} entries "
        f"({len(paired) - guess_pairs - sum(1 for x in paired if not x.get('paired_path'))} exact-suffix pairs, "
        f"{guess_pairs} guessed pairs, "
        f"{sum(1 for x in paired if not x.get('paired_path'))} solo)"
    )
    return other + paired


def wit_available() -> bool:
    return WIT_EXE.exists()


def _extract_iso(iso_path: Path, dest_dir: Path) -> bool:
    """Extract one ISO into dest_dir using wit. Returns True on success."""
    if not WIT_EXE.exists():
        return False
    try:
        result = subprocess.run(
            [str(WIT_EXE), 'EXTRACT', str(iso_path), str(dest_dir)],
            capture_output=True, text=True, **get_subprocess_args(),
        )
        if result.returncode != 0:
            logger.warning(f"wit failed for {iso_path.name}: {result.stderr[:300]}")
            return False
        return True
    except Exception as e:
        logger.warning(f"wit invocation failed for {iso_path.name}: {e}")
        return False


# ---------- Public API ----------

def start_scan(iso_paths: list[str], on_event: Callable[[str, dict], None]) -> IsoScanJob:
    """Create a job and spawn the scan thread.

    `on_event` is called as `on_event(event_name, payload)` where event_name is
    one of 'iso_scan_progress' | 'iso_scan_complete' | 'iso_scan_error'.
    Payload always includes the `job_id`.
    """
    job_id = uuid.uuid4().hex[:12]
    SCAN_WORK_ROOT.mkdir(parents=True, exist_ok=True)
    cleanup_stale_jobs()
    work_dir = SCAN_WORK_ROOT / job_id
    work_dir.mkdir(parents=True, exist_ok=True)
    job = IsoScanJob(job_id=job_id, iso_paths=list(iso_paths), work_dir=work_dir)
    with _jobs_lock:
        _jobs[job_id] = job

    thread = threading.Thread(
        target=_run_scan, args=(job, on_event), daemon=True,
        name=f"iso-scan-{job_id}",
    )
    thread.start()
    return job


def get_job(job_id: str) -> Optional[IsoScanJob]:
    with _jobs_lock:
        return _jobs.get(job_id)


def delete_job(job_id: str) -> bool:
    with _jobs_lock:
        job = _jobs.pop(job_id, None)
    work_dir = job.work_dir if job else _safe_scan_job_dir(job_id)
    if work_dir is None:
        return False
    existed = work_dir.exists()
    try:
        shutil.rmtree(work_dir, ignore_errors=True)
    except Exception as e:
        logger.warning(f"[iso-scan][cleanup] failed to delete job {job_id}: {e}")
    return bool(job or existed)


def cancel_job(job_id: str) -> bool:
    with _jobs_lock:
        job = _jobs.get(job_id)
    if not job:
        return False
    job.cancelled = True
    return True


# ---------- Scan pipeline ----------

def _emit(job: IsoScanJob, on_event, status: str, message: str, percent: int):
    job.status = status
    job.phase_message = message
    job.percent = percent
    try:
        on_event('iso_scan_progress', {
            'job_id': job.job_id,
            'status': status,
            'message': message,
            'percent': percent,
            'stats': job.stats,
        })
    except Exception as e:
        logger.warning(f"emit failed: {e}")


def _run_scan(job: IsoScanJob, on_event):
    t_start = time.time()
    logger.info(
        f"[iso-scan] === job {job.job_id} START === "
        f"isos={len(job.iso_paths)} workers={CSP_PARALLELISM}"
    )
    for p in job.iso_paths:
        logger.info(f"[iso-scan]   ISO: {p}")
    try:
        # --- Phase 1: extract ---
        extract_root = job.work_dir / "extracted"
        extract_root.mkdir(exist_ok=True)

        if not wit_available():
            job.error = (
                "wit.exe not found. Place wit-v3.05a-r8638-cygwin64 in "
                "<project>/tools/. Download: https://wit.wiimm.de/"
            )
            job.status = 'error'
            on_event('iso_scan_error', {'job_id': job.job_id, 'error': job.error})
            return

        for i, iso_path_str in enumerate(job.iso_paths):
            if job.cancelled:
                break
            iso_path = Path(iso_path_str)
            pct = int(5 + (i / max(1, len(job.iso_paths))) * 15)
            _emit(job, on_event, 'extracting',
                  f"Extracting {iso_path.name} ({i+1}/{len(job.iso_paths)})", pct)
            dest = extract_root / iso_path.stem
            if dest.exists():
                # Reuse existing extraction
                continue
            ok = _extract_iso(iso_path, dest)
            if not ok:
                shutil.rmtree(dest, ignore_errors=True)
                job.stats['errors'] += 1

        if job.cancelled:
            _finalize(job, on_event, cancelled=True)
            return

        # --- Phase 2: walk + hash filter ---
        _emit(job, on_event, 'scanning', "Loading vault & vanilla hashes...", 22)
        vault_hashes = _load_vault_hashes()
        vanilla_hashes = _load_vanilla_hashes()
        stock_maps = _build_stock_maps(extract_root, job.work_dir / "stocks")
        job.stats['stock_icons'] = sum(len(v) for v in stock_maps.values())

        all_files: list[tuple[str, str]] = []  # (path, source_iso_stem)
        for iso_dir in extract_root.iterdir():
            if not iso_dir.is_dir():
                continue
            for root, _, files in os.walk(iso_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    if _is_character_file(fp):
                        all_files.append((fp, iso_dir.name))

        job.stats['total_files'] = len(all_files)

        # Each pre-candidate is a dict to keep things readable.
        pre_candidates: list[dict] = []
        seen_hashes: set[str] = set()

        for i, (fp, source) in enumerate(all_files):
            if job.cancelled:
                break
            if i % 100 == 0:
                pct = 22 + int((i / max(1, len(all_files))) * 30)
                _emit(job, on_event, 'scanning',
                      f"Hashing files {i}/{len(all_files)}", pct)
            try:
                file_hash = _md5_file(fp)
            except Exception:
                job.stats['errors'] += 1
                continue

            if file_hash in vault_hashes:
                job.stats['existing'] += 1
                continue
            if file_hash in vanilla_hashes:
                job.stats['vanilla'] += 1
                continue
            if file_hash in seen_hashes:
                job.stats['dupes'] += 1
                continue
            seen_hashes.add(file_hash)

            # Custom-fighter costume slots (PlQp*, ...) are NOT vanilla-char
            # skins: their content symbols still say e.g. Fox (cloned from
            # Fox), so the symbol-based identification below would misfile
            # them. They're handled by the custom-characters scan instead.
            if _is_custom_fighter_file(fp):
                job.stats['custom_fighter'] += 1
                logger.info(
                    f"[iso-scan][id] CUSTOM_FIGHTER {os.path.basename(fp)} — "
                    "non-vanilla Pl code; belongs to a custom character"
                )
                continue

            # Identify character
            try:
                parser = DATParser(fp)
                parser.read_dat()
                if not parser.is_character_costume():
                    job.stats['data_mod'] += 1
                    logger.debug(
                        f"[iso-scan][id] DATA_MOD {os.path.basename(fp)} — no Ply*5K symbol"
                    )
                    continue
                character, symbol = parser.detect_character()
                # Filename-prefix override: PlBoXX.dat and PlClXX.dat both
                # carry an "ftDataBoy" symbol, so symbol-based detection tags
                # wireframes as Young Link. The 2-char filename prefix is the
                # authoritative signal — trust it when it disagrees.
                filename_character = _character_from_filename(fp)
                if filename_character and filename_character != character:
                    logger.warning(
                        f"[iso-scan][id] OVERRIDE {os.path.basename(fp)}: "
                        f"symbol={symbol!r} said {character!r} but filename "
                        f"prefix says {filename_character!r} — trusting filename"
                    )
                    character = filename_character
                if not character:
                    job.stats['unknown'] += 1
                    root_syms = [n.get('symbol') for n in parser.root_nodes][:5]
                    logger.warning(
                        f"[iso-scan][id] UNKNOWN {os.path.basename(fp)} — "
                        f"root symbols: {root_syms}"
                    )
                    continue
                costume_code = parser.get_character_filename() or os.path.basename(fp)
            except Exception as e:
                job.stats['errors'] += 1
                logger.warning(
                    f"[iso-scan][id] ERROR parsing {os.path.basename(fp)}: {e}"
                )
                continue

            # Drop characters the user has marked uninteresting.
            if character in SKIP_CHARACTERS:
                logger.info(
                    f"[iso-scan][id] SKIP {character} ({costume_code}) — in SKIP_CHARACTERS"
                )
                continue

            logger.info(
                f"[iso-scan][id] {character:22} code={costume_code!r:14} "
                f"symbol={symbol!r} src={source!r}"
            )
            pre_candidates.append({
                'path': fp, 'hash': file_hash,
                'character': character, 'costume_code': costume_code,
                'source_iso': source, 'symbol': symbol,
                'stock_path': stock_maps.get(source, {}).get(_stock_lookup_key(costume_code)),
            })

        if job.cancelled:
            _finalize(job, on_event, cancelled=True)
            return

        # --- Phase 2b: pair Ice Climbers Popo + Nana by (source_iso, color suffix) ---
        candidates = _pair_ice_climbers(pre_candidates)

        # --- Phase 3: Slippi-fixed hash check (against both vault AND vanilla) ---
        survivors: list[dict] = []
        for i, c in enumerate(candidates):
            if job.cancelled:
                break
            if i % 25 == 0:
                pct = 52 + int((i / max(1, len(candidates))) * 18)
                _emit(job, on_event, 'slippi',
                      f"Slippi-fix check {i}/{len(candidates)}", pct)
            fixed = _slippi_fixed_hash(c['path'])
            if fixed and (fixed in vault_hashes or fixed in vanilla_hashes):
                job.stats['slippi_matched'] += 1
                continue
            survivors.append(c)

        if job.cancelled:
            _finalize(job, on_event, cancelled=True)
            return

        # --- Phase 4: copy DATs + generate CSPs into work dir (parallel) ---
        skins_dir = job.work_dir / "skins"
        skins_dir.mkdir(exist_ok=True)

        results: dict[int, Optional[CandidateSkin]] = {}
        results_lock = threading.Lock()
        completed_counter = {'n': 0, 'errors': 0}

        total = len(survivors)
        _emit(job, on_event, 'csp',
              f"Generating thumbnails 0/{total} (×{CSP_PARALLELISM} workers)", 70)

        with ThreadPoolExecutor(max_workers=CSP_PARALLELISM) as ex:
            futures = {
                ex.submit(_build_candidate, i, c, skins_dir, job): i
                for i, c in enumerate(survivors)
            }
            for fut in as_completed(futures):
                if job.cancelled:
                    for f in futures:
                        f.cancel()
                    break
                idx = futures[fut]
                try:
                    candidate, had_error = fut.result()
                except Exception as e:
                    logger.warning(f"CSP worker for #{idx} crashed: {e}")
                    candidate, had_error = None, True
                with results_lock:
                    results[idx] = candidate
                    if had_error:
                        completed_counter['errors'] += 1
                    completed_counter['n'] += 1
                    n = completed_counter['n']
                if n % 5 == 0 or n == total:
                    pct = 70 + int((n / max(1, total)) * 28)
                    _emit(job, on_event, 'csp',
                          f"Generating thumbnails {n}/{total} (×{CSP_PARALLELISM} workers)", pct)

        # Stitch results back together in submission order so the UI grid is stable.
        for i in range(total):
            cand = results.get(i)
            if cand is not None:
                job.candidates.setdefault(cand.character, []).append(cand)
        job.stats['errors'] += completed_counter['errors']

        _finalize(job, on_event, cancelled=job.cancelled)

    except Exception as e:
        logger.error(f"ISO scan failed: {e}", exc_info=True)
        job.error = str(e)
        job.status = 'error'
        try:
            on_event('iso_scan_error', {'job_id': job.job_id, 'error': str(e)})
        except Exception:
            pass


def _build_candidate(idx: int, c: dict, skins_dir: Path, job: IsoScanJob) -> tuple[Optional[CandidateSkin], bool]:
    """Per-candidate worker: copy DAT(s) + run HSDRawViewer to generate a CSP.
    Returns (candidate_or_None, had_error)."""
    if job.cancelled:
        return None, False

    worker = threading.current_thread().name
    t0 = time.time()
    key = f"{c['character'].replace(' ', '_').replace('(', '').replace(')', '')}_{c['hash'][:10]}_{idx}"
    skin_folder = skins_dir / key
    skin_folder.mkdir(exist_ok=True)

    primary_name = _ensure_dat_ext(c['costume_code'])
    dat_dest = skin_folder / primary_name
    try:
        shutil.copy2(c['path'], dat_dest)
    except Exception as e:
        logger.warning(f"[iso-scan][csp][{worker}] copy fail {c['path']}: {e}")
        return None, True

    paired_dest: Optional[Path] = None
    if c.get('paired_path'):
        paired_name = _ensure_dat_ext(c.get('paired_costume_code') or 'pair.dat')
        paired_dest = skin_folder / paired_name
        try:
            shutil.copy2(c['paired_path'], paired_dest)
            logger.info(
                f"[iso-scan][csp][{worker}] paired DAT staged for {key}: "
                f"{c['costume_code']} + {c.get('paired_costume_code')}"
            )
        except Exception as e:
            logger.warning(f"[iso-scan][csp][{worker}] paired DAT copy fail for {key}: {e}")
            paired_dest = None

    csp_dest: Optional[Path] = None
    csp_status = 'ok'
    # Serialize HSDRawViewer launches by holding the lock for STAGGER_S
    # before invoking generate_csp. The lock is only contended at process
    # start; once the subprocess is spawned and into its render phase,
    # other workers are free to launch. See _LAUNCH_STAGGER_S comment.
    if _LAUNCH_STAGGER_S > 0:
        wait_start = time.time()
        with _launch_lock:
            waited_ms = int((time.time() - wait_start) * 1000)
            time.sleep(_LAUNCH_STAGGER_S)
            if waited_ms > 50:
                logger.debug(
                    f"[iso-scan][csp][{worker}] #{idx} waited {waited_ms}ms "
                    f"for launch slot before starting HSDRawViewer"
                )
    try:
        generated = generate_csp(str(dat_dest))
        if generated and os.path.exists(generated):
            csp_dest = skin_folder / "csp.png"
            shutil.move(generated, csp_dest)
        else:
            csp_status = 'no_output'
    except Exception as e:
        csp_status = f'exception: {e}'

    elapsed_ms = int((time.time() - t0) * 1000)
    logger.info(
        f"[iso-scan][csp][{worker}] #{idx:<3} {c['character']:22} "
        f"{primary_name:14} csp={csp_status:10} {elapsed_ms:>5}ms"
    )

    stock_dest: Optional[Path] = None
    stock_path = c.get('stock_path')
    if stock_path and os.path.exists(stock_path):
        try:
            stock_dest = skin_folder / "stock.png"
            shutil.copy2(stock_path, stock_dest)
        except Exception as e:
            logger.warning(f"[iso-scan][stock][{worker}] copy fail for {key}: {e}")
            stock_dest = None

    return CandidateSkin(
        key=key,
        character=c['character'],
        costume_code=c['costume_code'],
        dat_path=str(dat_dest),
        csp_path=str(csp_dest) if csp_dest else None,
        stock_path=str(stock_dest) if stock_dest else None,
        dat_hash=c['hash'],
        source_iso=c['source_iso'],
        paired_dat_path=str(paired_dest) if paired_dest else None,
        paired_costume_code=c.get('paired_costume_code'),
    ), False


def _finalize(job: IsoScanJob, on_event, cancelled: bool):
    if cancelled:
        job.status = 'cancelled'
        job.phase_message = 'Cancelled'
    else:
        job.status = 'complete'
        job.phase_message = 'Done'
        job.percent = 100

    elapsed = time.time() - job.created_at
    logger.info(f"[iso-scan] === job {job.job_id} {job.status.upper()} === "
                f"elapsed={elapsed:.1f}s")
    logger.info(f"[iso-scan] stats: {job.stats}")
    by_char = {c: len(s) for c, s in sorted(job.candidates.items())}
    logger.info(f"[iso-scan] candidates by character ({sum(by_char.values())} total): {by_char}")
    # How many got CSPs vs not
    with_csp = sum(1 for s in job.candidates.values() for x in s if x.csp_path)
    without_csp = sum(1 for s in job.candidates.values() for x in s if not x.csp_path)
    with_stock = sum(1 for s in job.candidates.values() for x in s if x.stock_path)
    paired_ic = sum(1 for s in job.candidates.values() for x in s if x.paired_dat_path)
    logger.info(f"[iso-scan] csp coverage: {with_csp} rendered, {without_csp} blank/no-preview; "
                f"{with_stock} actual stocks; {paired_ic} paired IC candidates")

    try:
        on_event('iso_scan_complete', {
            'job_id': job.job_id,
            'status': job.status,
            'stats': job.stats,
            'total_new': sum(len(v) for v in job.candidates.values()),
        })
    except Exception:
        pass
