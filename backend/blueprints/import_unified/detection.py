"""
Pure content-type detection for the unified import endpoint.

Classifies an uploaded archive WITHOUT importing anything — no storage writes,
no metadata mutation. The /import/file route dispatches on the result, and the
mod-pool harness (tests/nucleus/detect_pool.py) runs the same classifier
offline against the backup corpus.

Types, in dispatch priority order:
    custom_character        zip containing fighter.json (full fighter package)
    custom_stage            zip containing stage.json (Nucleus stage package)
    mex_stage_yml           zip containing stage.yml (classic m-ex stage
                            package; recognized but needs yml→json conversion)
    bundle                  .ssbm extension, or manifest.json + textures/*.png
    character               costume DAT(s) detected by character_detector
    stage                   stage DAT(s) detected by stage_detector
    xdelta                  .xdelta extension or .xdelta member(s)
    css_icon_grid           '='-prefixed icon PNGs, or MnSlChr/MexSelectChr dat
    pause_screen            GmPause*.dat/.usd member
    css_background          MnSlMap (SSS) dat; MnSlChr ambiguous w/ icon grid
    music                   .hps extension or .hps member(s)
    character_renamed       costume DAT(s) whose filenames don't start with
                            'Pl' but whose contents parse to a known character
                            (e.g. lucinablack.dat → Marth). Not yet importable:
                            character_detector's filename filter skips them.
    custom_fighter_costume  DAT(s) with Ply joint symbols but no vanilla
                            character match (Akaneia Sonic/Knuckles etc.) —
                            belongs in a custom character's skin list
    ic_half                 only unpaired Popo-only / Nana-only costumes
                            (importable once the matching half is provided)
    dolphin_textures        Dolphin texture pack (tex1_*.png hash names)
    sound_bank              .spk / .ssm sound files
    unsupported_audio       mp3/wav/ogg (not .hps — can't go into an ISO)
    nested_archive          nothing recognized directly, but contains inner
                            archives worth recursing into
    unknown                 nothing recognized

'effect' mods cannot be auto-detected (a gun/laser dat looks like any other
dat) — they only arrive via the explicit mod_type=effect hint.

Returned dict:
    {
        'type': <one of the above>,
        'confidence': 'high' | 'medium' | 'low',
        'candidates': [types...],   # every plausible type, best first
        'detail': {...},            # payload for the chosen type
        'all_details': {...},       # payloads for every candidate
    }
"""

import json
import logging
import os
import tempfile
import zipfile
from pathlib import Path

from character_detector import detect_character_from_zip, DATParser, read_7z_member
from stage_detector import detect_stage_from_zip

try:
    import py7zr
    HAS_7Z = True
except ImportError:
    HAS_7Z = False

logger = logging.getLogger(__name__)

ARCHIVE_EXTS = {'.zip', '.7z', '.rar'}
AUDIO_EXTS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac'}
MAX_FALLBACK_DAT_PARSES = 8


def _archive_names(archive_path):
    """List member names of a zip/7z archive, excluding macOS junk.
    Returns None if the file can't be read as an archive."""
    path = Path(archive_path)
    try:
        if path.suffix.lower() == '.7z':
            if not HAS_7Z:
                return None
            with py7zr.SevenZipFile(path, 'r') as sz:
                names = sz.getnames()
        else:
            with zipfile.ZipFile(path, 'r') as zf:
                names = zf.namelist()
    except Exception:
        return None
    return [n for n in names
            if not n.startswith('__MACOSX') and not Path(n).name.startswith('._')]


def _read_member(archive_path, member):
    """Read one member's bytes from a zip/7z archive; None on failure."""
    path = Path(archive_path)
    try:
        if path.suffix.lower() == '.7z':
            if not HAS_7Z:
                return None
            with py7zr.SevenZipFile(path, 'r') as sz:
                return read_7z_member(sz, member)
        with zipfile.ZipFile(path, 'r') as zf:
            return zf.read(member)
    except Exception:
        return None


def _find_member(names, basename_lower):
    """First member whose basename matches (case-insensitive), else None."""
    for n in names:
        if Path(n).name.lower() == basename_lower:
            return n
    return None


def detect_content_type(archive_path, filename=None, deep=True):
    """Classify an archive for import. Pure — never writes anything.

    archive_path: path to the file on disk (zip/7z/raw file)
    filename: original upload filename (extension fast-paths); defaults to
              archive_path's own name
    deep: run the DAT-parsing character/stage detectors and the content
          fallback. With deep=False only cheap name heuristics run.
    """
    filename = filename or Path(archive_path).name
    ext = Path(filename).suffix.lower()

    # ── extension fast-paths (no archive open needed) ────────────────────────
    if ext == '.xdelta':
        return _result('xdelta', 'high', detail={'patch_count': 1})
    if ext == '.ssbm':
        return _detect_bundle(archive_path, from_extension=True)
    if ext == '.hps':
        return _result('music', 'high', detail={'track_count': 1})

    names = _archive_names(archive_path)
    if names is None:
        # Raw .dat/.usd files are wrapped in a temp zip by the route before
        # detection, so an unreadable archive here is a hard unknown.
        return _result('unknown', 'low', detail={'error': 'unreadable archive'})

    basenames = [Path(n).name.lower() for n in names if not n.endswith('/')]
    candidates = []
    details = {}

    def add(type_, detail=None):
        candidates.append(type_)
        details[type_] = detail or {}

    # ── package markers (must beat raw dat detection: a fighter package is ──
    # ── full of Pl*.dat files that would misclassify as costumes) ───────────
    fighter_json = _find_member(names, 'fighter.json')
    if fighter_json is not None:
        add('custom_character',
            _package_detail(archive_path, fighter_json))

    stage_json = _find_member(names, 'stage.json')
    if stage_json is not None:
        add('custom_stage', _package_detail(archive_path, stage_json))

    stage_yml = _find_member(names, 'stage.yml')
    dat_basenames = [b for b in basenames if b.endswith(('.dat', '.usd'))]
    if stage_yml is not None and dat_basenames:
        add('mex_stage_yml', {'dats': dat_basenames})

    has_manifest = 'manifest.json' in names or 'manifest.json' in basenames
    texture_pngs = [n for n in names
                    if n.startswith('textures/') and n.lower().endswith('.png')]
    if has_manifest and texture_pngs:
        add('bundle', {'texture_count': len(texture_pngs)})

    is_package = bool(candidates)

    # ── costume / stage DAT detection (the expensive, accurate pass) ────────
    char_infos = []
    if deep and not is_package:
        try:
            char_infos = detect_character_from_zip(str(archive_path))
        except Exception as e:
            logger.warning(f'character detection failed: {e}')
        if char_infos:
            add('character', {
                'costumes': [{'character': c['character'], 'color': c['color']}
                             for c in char_infos],
                'char_infos': char_infos,
            })

        try:
            stage_infos = detect_stage_from_zip(str(archive_path))
        except Exception as e:
            logger.warning(f'stage detection failed: {e}')
            stage_infos = []
        if stage_infos:
            add('stage', {
                'stages': [s['stage_name'] for s in stage_infos],
                'stage_infos': stage_infos,
            })
    elif not deep:
        # cheap name-based approximation for harness fast mode
        pl_dats = [b for b in dat_basenames if b.startswith('pl')]
        gr_dats = [b for b in dat_basenames if b.startswith('gr')]
        if pl_dats and not is_package:
            add('character', {'dat_names': pl_dats})
        if gr_dats and not is_package:
            add('stage', {'dat_names': gr_dats})

    # ── patches ──────────────────────────────────────────────────────────────
    xdeltas = [b for b in basenames if b.endswith('.xdelta')]
    if xdeltas:
        add('xdelta', {'patch_count': len(xdeltas)})

    # ── menu mods ────────────────────────────────────────────────────────────
    equals_pngs = [b for b in basenames if b.startswith('=') and b.endswith('.png')]
    has_mnslchr = any(('mnslchr' in b or b == 'mexselectchr.dat')
                      and b.endswith(('.dat', '.usd')) for b in basenames)
    has_mnslmap = any('mnslmap' in b and b.endswith(('.dat', '.usd'))
                      for b in basenames)
    has_gmpause = any('gmpause' in b and b.endswith(('.dat', '.usd'))
                      for b in basenames)

    if len(equals_pngs) >= 2 or has_mnslchr:
        add('css_icon_grid', {'icon_pngs': len(equals_pngs),
                              'has_mnslchr': has_mnslchr})
    if has_gmpause:
        add('pause_screen')
    if has_mnslmap or has_mnslchr:
        # MnSlMap is unambiguously a background source; MnSlChr could be either
        # an icon-grid source or a CSS background source.
        add('css_background', {'source': 'sss' if has_mnslmap else 'css'})

    # ── music ────────────────────────────────────────────────────────────────
    hps = [b for b in basenames if b.endswith('.hps')]
    if hps:
        add('music', {'track_count': len(hps)})

    # ── unpaired Ice Climbers halves: pl-named IC dats that deep detection ──
    # ── dropped because no Popo/Nana partner exists in this zip. Must run ───
    # ── before the content fallback, which would claim them as 'renamed'. ───
    if deep and not candidates and dat_basenames and not char_infos:
        ic_dats = [b for b in dat_basenames
                   if b.startswith(('plpp', 'plnn'))]
        if ic_dats and len(ic_dats) == len([b for b in dat_basenames
                                            if b.startswith('pl')]) == len(dat_basenames):
            half = 'popo' if ic_dats[0].startswith('plpp') else 'nana'
            add('ic_half', {'half': half, 'dats': ic_dats})

    # ── content fallback: dats that defeated the name-based detectors. ──────
    # ── Also covers the old website's renamed-extension convention for ──────
    # ── alternate variants (.rat/.lat/.0at… are plain dats renamed). ────────
    if deep and not candidates:
        fb_type, fb_detail = _classify_dats_by_content(archive_path, names)
        if fb_type:
            add(fb_type, fb_detail)

    # ── informational last resorts ───────────────────────────────────────────
    if not candidates:
        tex_pngs = [b for b in basenames
                    if b.startswith('tex1_') and b.endswith('.png')]
        if tex_pngs:
            add('dolphin_textures', {'texture_count': len(tex_pngs)})

        sound_files = [b for b in basenames if b.endswith(('.spk', '.ssm'))]
        if not candidates and sound_files:
            add('sound_bank', {'files': sound_files})

        audio = [b for b in basenames if Path(b).suffix in AUDIO_EXTS]
        if not candidates and audio:
            add('unsupported_audio', {'count': len(audio),
                                      'extensions': sorted({Path(b).suffix for b in audio})})

        inner = [b for b in basenames if Path(b).suffix in ARCHIVE_EXTS]
        if not candidates and inner:
            add('nested_archive', {'archives': inner})

    if not candidates:
        return _result('unknown', 'low',
                       detail={'member_count': len(basenames),
                               'sample': basenames[:10]})

    chosen = candidates[0]
    # MnSlChr-only zips are genuinely ambiguous (icon grid vs background);
    # default to icon grid to match the historical cascade order.
    ambiguous = (chosen == 'css_icon_grid' and not equals_pngs
                 and 'css_background' in candidates)
    confidence = 'medium' if (ambiguous or len(candidates) > 1) else 'high'

    return _result(chosen, confidence, candidates=candidates,
                   detail=details.get(chosen, {}), all_details=details)


def _looks_like_dat_extension(suffix):
    """.dat/.usd, plus the old website's alternate-variant renames
    (.rat, .lat, .0at–.9at, .aat… — all plain dats with a letter swapped)."""
    if suffix in ('.dat', '.usd'):
        return True
    return len(suffix) == 4 and suffix.endswith('at') and suffix[1].isalnum()


def _classify_dats_by_content(archive_path, names):
    """Parse up to MAX_FALLBACK_DAT_PARSES dats by content. Catches costume
    dats with arbitrary filenames (lucinablack.dat → Marth) and costumes for
    non-vanilla fighters (Ply symbols, no character match)."""
    if DATParser is None:
        return None, None

    dat_members = [n for n in names
                   if _looks_like_dat_extension(Path(n).suffix.lower())
                   and not n.endswith('/')][:MAX_FALLBACK_DAT_PARSES]
    renamed = []
    custom_fighter = []
    for member in dat_members:
        data = _read_member(archive_path, member)
        if not data:
            continue
        with tempfile.NamedTemporaryFile(suffix='.dat', delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            parser = DATParser(tmp_path)
            parser.read_dat()
            character, _symbol = parser.detect_character()
            has_ply = any('Ply' in node['symbol'] for node in parser.root_nodes)
            if not has_ply:
                continue
            if character:
                renamed.append({'dat': Path(member).name,
                                'character': character,
                                'costume_code': parser.get_character_filename()})
            else:
                custom_fighter.append({'dat': Path(member).name})
        except Exception:
            continue
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    if renamed:
        return 'character_renamed', {'costumes': renamed}
    if custom_fighter:
        return 'custom_fighter_costume', {'dats': [d['dat'] for d in custom_fighter]}
    return None, None


def _result(type_, confidence, candidates=None, detail=None, all_details=None):
    return {
        'type': type_,
        'confidence': confidence,
        'candidates': candidates or [type_],
        'detail': detail or {},
        'all_details': all_details or {},
    }


def _package_detail(archive_path, member, name_key='name'):
    """Pull the display name out of a fighter.json / stage.json marker."""
    data = _read_member(archive_path, member)
    if not data:
        return {}
    try:
        meta = json.loads(data)
        return {'name': meta.get(name_key)}
    except (ValueError, UnicodeDecodeError):
        return {}


def _detect_bundle(archive_path, from_extension=False):
    names = _archive_names(archive_path) or []
    if 'manifest.json' not in names:
        if from_extension:
            return _result('bundle', 'medium',
                           detail={'warning': 'no manifest.json'})
        return _result('unknown', 'low', detail={'error': 'no manifest.json'})
    name = None
    data = _read_member(archive_path, 'manifest.json')
    if data:
        try:
            name = json.loads(data).get('name')
        except (ValueError, UnicodeDecodeError):
            pass
    textures = [n for n in names
                if n.startswith('textures/') and n.lower().endswith('.png')]
    return _result('bundle', 'high',
                   detail={'name': name, 'texture_count': len(textures)})
