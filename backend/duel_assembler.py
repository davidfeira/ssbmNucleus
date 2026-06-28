"""
duel_assembler.py -- manifest-driven assembler for the modpack duel spec.

This is intentionally glue, not a planner. It consumes the contestant-authored
manifest/plans and resolves exactly those vault assets into endpoint-ready work
items for tests/nucleus/build-duel-modpack.js.

Typical use from repo root:

  python backend/duel_assembler.py duel/codex/manifest.json --dry-run --emit-harness-json

Use the Node harness for project creation, editing, ISO export, and bundle export.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from core.config import (  # noqa: E402
    MEXCLI_PATH,
    PROJECT_ROOT,
    PROJECTS_PATH,
    STORAGE_PATH,
    get_subprocess_args,
)
from core.constants import (  # noqa: E402
    CHAR_PREFIXES,
    VANILLA_CSS_COLOR_ORDER,
    VANILLA_ISO_MD5,
)


EXCLUDED_CHARACTER_KEYS = {"Mr. Game & Watch", "Nana"}
NANA_STORAGE_KEYS = ("Nana", "Ice Climbers (Nana)")
NANA_PREFIX = "Nn"

LEGAL_STAGES: dict[str, dict[str, str]] = {
    "GrNBa": {"stage": "Battlefield", "folder": "battlefield", "root_ext": ".dat"},
    "GrNLa": {"stage": "Final Destination", "folder": "final_destination", "root_ext": ".dat"},
    "GrSt": {"stage": "Yoshi's Story", "folder": "yoshis_story", "root_ext": ".dat"},
    "GrOp": {"stage": "Dream Land N64", "folder": "dreamland", "root_ext": ".dat"},
    "GrPs": {"stage": "Pokemon Stadium", "folder": "pokemon_stadium", "root_ext": ".usd"},
    "GrIz": {"stage": "Fountain of Dreams", "folder": "fountain_of_dreams", "root_ext": ".dat"},
}

MODE_ALIASES = {
    "default": "default-replacement",
    "default-replacement": "default-replacement",
    "replacement": "default-replacement",
    "das": "das",
}

BUTTON_INDICATOR_RE = re.compile(r"\s*\(([ABXYLRZ])\)$", re.IGNORECASE)
WHITESPACE_RE = re.compile(r"\s+")
PROJECT_VARIANT_WORD_RE = re.compile(r"[A-Za-z0-9]+")


@dataclass(frozen=True)
class RequiredSlot:
    character: str
    slot: int
    suffix: str
    costume_code: str


@dataclass
class StageJob:
    code: str
    mode: str
    zip_path: Path
    display_name: str
    button: str | None = None


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    imports: dict[str, list[str]] = field(default_factory=dict)
    removals: dict[str, list[int]] = field(default_factory=dict)
    stage_jobs: list[StageJob] = field(default_factory=list)
    visible_slots: int = 0
    generated_costume_dats: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(value, f, indent=2)
        f.write("\n")


def required_character_slots() -> list[RequiredSlot]:
    slots: list[RequiredSlot] = []
    for character, suffixes in VANILLA_CSS_COLOR_ORDER.items():
        if character in EXCLUDED_CHARACTER_KEYS:
            continue
        prefix = CHAR_PREFIXES.get(character)
        if not prefix:
            raise RuntimeError(f"missing CHAR_PREFIXES entry for {character}")
        for slot, suffix in enumerate(suffixes):
            slots.append(RequiredSlot(character, slot, suffix, f"Pl{prefix}{suffix}"))
    return slots


def _load_metadata(storage_path: Path = STORAGE_PATH) -> dict[str, Any]:
    path = storage_path / "metadata.json"
    if not path.exists():
        return {"characters": {}, "stages": {}}
    return read_json(path)


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)


def _resolve_project_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _character_metadata_lists(metadata: dict[str, Any], character: str) -> list[list[dict[str, Any]]]:
    characters = metadata.get("characters", {})
    keys = NANA_STORAGE_KEYS if character == "Nana" else (character,)
    lists: list[list[dict[str, Any]]] = []
    for key in keys:
        value = characters.get(key, {})
        if isinstance(value, dict):
            skins = value.get("skins", [])
            if isinstance(skins, list):
                lists.append(skins)
    return lists


def _skin_zip_from_entry(
    character: str,
    entry: dict[str, Any],
    metadata: dict[str, Any],
    storage_path: Path = STORAGE_PATH,
) -> tuple[Path | None, str | None]:
    direct = _resolve_project_path(entry.get("vaultPath") or entry.get("zipPath"))
    if direct:
        return direct, None

    filename = entry.get("filename")
    vault_id = entry.get("vaultSkinId")
    if not filename and vault_id:
        for skins in _character_metadata_lists(metadata, character):
            for skin in skins:
                if skin.get("type") == "folder":
                    continue
                if skin.get("id") == vault_id:
                    filename = skin.get("filename")
                    break
            if filename:
                break

    if filename:
        return storage_path / character / filename, None

    return None, f"{character} {entry.get('costumeCode') or entry.get('slot')}: missing vaultSkinId/filename"


def _stage_zip_from_entry(
    code: str,
    entry: dict[str, Any],
    metadata: dict[str, Any],
    storage_path: Path = STORAGE_PATH,
) -> tuple[Path | None, str | None]:
    direct = _resolve_project_path(entry.get("variantPath") or entry.get("zipPath") or entry.get("vaultPath"))
    if direct:
        return direct, None

    stage_info = LEGAL_STAGES[code]
    filename = entry.get("filename")
    variant_id = entry.get("vaultVariantId") or entry.get("vaultStageVariantId")

    if not filename and variant_id:
        stage_meta = metadata.get("stages", {}).get(stage_info["folder"], {})
        for variant in stage_meta.get("variants", []):
            if variant.get("type") == "folder":
                continue
            if variant.get("id") == variant_id:
                filename = variant.get("filename") or f"{variant_id}.zip"
                break

    if filename:
        return storage_path / "das" / stage_info["folder"] / filename, None

    return None, f"{code}: missing vaultVariantId/filename"


def _relative_artifact_exists(base: Path, rel: str | None) -> bool:
    if not rel:
        return False
    path = Path(rel)
    return (path if path.is_absolute() else base / path).exists()


def validate_manifest(
    manifest: dict[str, Any],
    manifest_path: Path,
    *,
    check_files: bool = True,
    storage_path: Path = STORAGE_PATH,
) -> ValidationResult:
    metadata = _load_metadata(storage_path)
    base = manifest_path.parent
    result = ValidationResult()
    imports: dict[str, list[str]] = {}

    characters = manifest.get("characters")
    if not isinstance(characters, dict):
        result.errors.append("manifest.characters must be an object")
        characters = {}

    by_character: dict[str, list[RequiredSlot]] = {}
    for slot in required_character_slots():
        by_character.setdefault(slot.character, []).append(slot)

    for character, required in by_character.items():
        entries = characters.get(character)
        if not isinstance(entries, list):
            result.errors.append(f"{character}: missing character entry list")
            continue
        by_slot = {entry.get("slot"): entry for entry in entries if isinstance(entry, dict)}
        if len(by_slot) != len(required):
            result.errors.append(f"{character}: expected {len(required)} slots, found {len(by_slot)}")

        for slot in required:
            entry = by_slot.get(slot.slot)
            if not entry:
                result.errors.append(f"{character}: missing slot {slot.slot} ({slot.costume_code})")
                continue
            code = entry.get("costumeCode")
            if code != slot.costume_code:
                result.errors.append(
                    f"{character} slot {slot.slot}: expected costumeCode {slot.costume_code}, found {code}"
                )
            if check_files:
                if not _relative_artifact_exists(base, entry.get("plan")):
                    result.errors.append(f"{character} {slot.costume_code}: plan file not found")
                if not _relative_artifact_exists(base, entry.get("preview")):
                    result.warnings.append(f"{character} {slot.costume_code}: preview file not found")

            zip_path, error = _skin_zip_from_entry(character, entry, metadata, storage_path)
            if error:
                result.errors.append(error)
                continue
            if zip_path is None:
                result.errors.append(f"{character} {slot.costume_code}: could not resolve vault zip")
                continue
            if check_files and not zip_path.exists():
                result.errors.append(f"{character} {slot.costume_code}: vault zip not found: {_display_path(zip_path)}")
            imports.setdefault(character, []).append(str(zip_path.resolve()))

    pairs = manifest.get("ice_climbers_pairs")
    if not isinstance(pairs, list):
        result.errors.append("manifest.ice_climbers_pairs must be a list")
        pairs = []
    pair_by_slot = {pair.get("slot"): pair for pair in pairs if isinstance(pair, dict)}
    ic_suffixes = VANILLA_CSS_COLOR_ORDER["Ice Climbers"]
    nana_suffixes = VANILLA_CSS_COLOR_ORDER["Nana"]
    if len(pair_by_slot) != len(ic_suffixes):
        result.errors.append(f"ice_climbers_pairs: expected {len(ic_suffixes)} pairs, found {len(pair_by_slot)}")

    nana_imports: list[str] = []
    for slot, popo_suffix in enumerate(ic_suffixes):
        pair = pair_by_slot.get(slot)
        if not pair:
            result.errors.append(f"ice_climbers_pairs: missing slot {slot}")
            continue

        expected_popo = f"Pl{CHAR_PREFIXES['Ice Climbers']}{popo_suffix}"
        expected_nana = f"Pl{NANA_PREFIX}{nana_suffixes[slot]}"
        if pair.get("popoCode") != expected_popo:
            result.errors.append(f"ice_climbers_pairs slot {slot}: expected popoCode {expected_popo}")
        if pair.get("nanaCode") != expected_nana:
            result.errors.append(f"ice_climbers_pairs slot {slot}: expected nanaCode {expected_nana}")

        ic_entry = (characters.get("Ice Climbers") or [{}])[slot] if isinstance(characters.get("Ice Climbers"), list) else {}
        if pair.get("popoVaultSkinId") and ic_entry.get("vaultSkinId") != pair.get("popoVaultSkinId"):
            result.errors.append(f"ice_climbers_pairs slot {slot}: popoVaultSkinId does not match Ice Climbers slot")

        nana_entry = {
            "slot": slot,
            "costumeCode": expected_nana,
            "vaultSkinId": pair.get("nanaVaultSkinId"),
            "filename": pair.get("nanaFilename"),
            "vaultPath": pair.get("nanaVaultPath"),
            "zipPath": pair.get("nanaZipPath"),
        }
        zip_path, error = _skin_zip_from_entry("Nana", nana_entry, metadata, storage_path)
        if error:
            result.errors.append(error)
            continue
        if zip_path is None:
            result.errors.append(f"Nana {expected_nana}: could not resolve vault zip")
            continue
        if check_files and not zip_path.exists():
            result.errors.append(f"Nana {expected_nana}: vault zip not found: {_display_path(zip_path)}")
        nana_imports.append(str(zip_path.resolve()))

    if nana_imports:
        imports["Nana"] = nana_imports

    stages = manifest.get("stages")
    if not isinstance(stages, dict):
        result.errors.append("manifest.stages must be an object")
        stages = {}
    for code, stage_info in LEGAL_STAGES.items():
        entry = stages.get(code)
        if not isinstance(entry, dict):
            result.errors.append(f"{code}: missing stage entry for {stage_info['stage']}")
            continue
        mode = MODE_ALIASES.get(str(entry.get("mode") or "").strip().lower())
        if not mode:
            result.errors.append(f"{code}: mode must be default-replacement or das")
            continue
        if check_files:
            if not _relative_artifact_exists(base, entry.get("plan")):
                result.errors.append(f"{code}: plan file not found")
            if not _relative_artifact_exists(base, entry.get("preview")):
                result.warnings.append(f"{code}: preview file not found")

        zip_path, error = _stage_zip_from_entry(code, entry, metadata, storage_path)
        if error:
            result.errors.append(error)
            continue
        if zip_path is None:
            result.errors.append(f"{code}: could not resolve stage vault zip")
            continue
        if check_files and not zip_path.exists():
            result.errors.append(f"{code}: stage zip not found: {_display_path(zip_path)}")

        button = str(entry.get("button") or "X").upper() if mode == "das" else None
        if button and button not in {"A", "B", "X", "Y", "L", "R", "Z"}:
            result.errors.append(f"{code}: invalid DAS button {button}")
        result.stage_jobs.append(
            StageJob(
                code=code,
                mode=mode,
                zip_path=zip_path.resolve(),
                display_name=entry.get("skinName") or entry.get("vaultVariantId") or stage_info["stage"],
                button=button,
            )
        )

    result.imports = imports
    result.removals = {
        character: list(range(len(suffixes) - 1, -1, -1))
        for character, suffixes in VANILLA_CSS_COLOR_ORDER.items()
        if character not in EXCLUDED_CHARACTER_KEYS
    }
    result.removals["Nana"] = list(range(len(VANILLA_CSS_COLOR_ORDER["Nana"]) - 1, -1, -1))
    result.visible_slots = sum(len(v) for k, v in VANILLA_CSS_COLOR_ORDER.items() if k not in EXCLUDED_CHARACTER_KEYS)
    result.generated_costume_dats = result.visible_slots + len(VANILLA_CSS_COLOR_ORDER["Nana"])
    return result


def _run(cmd: list[str | Path], *, cwd: Path = PROJECT_ROOT, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    rendered = [str(part) for part in cmd]
    return subprocess.run(
        rendered,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=timeout,
        **get_subprocess_args(),
    )


def _parse_cli_json(text: str) -> dict[str, Any]:
    if not text:
        return {}
    lines = text.splitlines()
    for i in range(len(lines) - 1, -1, -1):
        if lines[i].strip() == "{" and not lines[i].startswith((" ", "\t")):
            try:
                return json.loads("\n".join(lines[i:]))
            except json.JSONDecodeError:
                break
    out = None
    for line in lines:
        s = line.strip()
        if s.startswith("{") and s.endswith("}"):
            try:
                out = json.loads(s)
            except json.JSONDecodeError:
                pass
    if out is not None:
        return out
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {}


def run_mexcli(args: list[str | Path], *, timeout: int = 3600) -> dict[str, Any]:
    if not Path(MEXCLI_PATH).exists():
        raise RuntimeError(f"MexCLI not found: {MEXCLI_PATH}")
    cp = _run([MEXCLI_PATH, *args], timeout=timeout)
    parsed = _parse_cli_json(cp.stdout)
    if cp.returncode != 0 or parsed.get("success") is False:
        message = parsed.get("error") or cp.stderr or cp.stdout or f"MexCLI exited {cp.returncode}"
        raise RuntimeError(message.strip())
    return parsed


def hash_md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _safe_managed_project_dir(project_name: str) -> Path:
    if not project_name or any(ch in project_name for ch in '\\/:*?"<>|'):
        raise ValueError(f"invalid project name: {project_name!r}")
    project_dir = (PROJECTS_PATH / project_name).resolve()
    project_dir.relative_to(PROJECTS_PATH.resolve())
    return project_dir


def create_project(vanilla_iso: Path, project_name: str, *, force: bool = False) -> Path:
    project_dir = _safe_managed_project_dir(project_name)
    if project_dir.exists():
        if not force:
            raise RuntimeError(f"project already exists: {_display_path(project_dir)} (use --force to replace it)")
        if project_dir == PROJECTS_PATH.resolve():
            raise RuntimeError("refusing to delete the managed projects root")
        shutil.rmtree(project_dir)
    project_dir.parent.mkdir(parents=True, exist_ok=True)
    run_mexcli(["create", vanilla_iso, project_dir, project_name], timeout=1800)
    project_path = project_dir / "project.mexproj"
    if not project_path.exists():
        raise RuntimeError(f"MexCLI create completed but project file is missing: {project_path}")
    return project_path


def normalize_whitespace(name: str) -> str:
    return WHITESPACE_RE.sub(" ", name or "").strip()


def strip_button_indicator(filename: str) -> str:
    return normalize_whitespace(BUTTON_INDICATOR_RE.sub("", filename or ""))


def extract_button_indicator(filename: str) -> str | None:
    match = BUTTON_INDICATOR_RE.search(filename or "")
    return match.group(1).upper() if match else None


def add_button_indicator(filename: str, button: str) -> str:
    return f"{strip_button_indicator(filename)}({button.upper()})"


def sanitize_filename(name: str) -> str:
    return normalize_whitespace(re.sub(r'[<>:"/\\|?*]', "", name or ""))


def normalize_variant_name(name: str) -> str:
    sanitized = sanitize_filename(name)
    button = extract_button_indicator(sanitized)
    base_name = strip_button_indicator(sanitized)
    words = PROJECT_VARIANT_WORD_RE.findall(base_name)
    if words:
        normalized_base = "".join(word[:1].upper() + word[1:] for word in words)
    else:
        normalized_base = re.sub(r"\s+", "", base_name)
    return add_button_indicator(normalized_base, button) if button else normalized_base


def _extract_stage_data(zip_path: Path) -> bytes:
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = sorted(n for n in zf.namelist() if n.lower().endswith((".dat", ".usd")))
        if not names:
            raise RuntimeError(f"no .dat/.usd stage file found in {zip_path}")
        return zf.read(names[0])


def install_das_framework(project_path: Path) -> None:
    project_files = project_path.parent / "files"
    das_source = PROJECT_ROOT / "utility" / "DynamicAlternateStages"
    if not das_source.exists():
        raise RuntimeError(f"DAS framework source not found: {das_source}")
    project_files.mkdir(parents=True, exist_ok=True)
    for code, info in LEGAL_STAGES.items():
        root_ext = info["root_ext"]
        stage_folder = project_files / code
        stage_folder.mkdir(exist_ok=True)
        original_stage = project_files / f"{code}{root_ext}"
        vanilla_in_folder = stage_folder / "vanilla.dat"
        if original_stage.exists() and not vanilla_in_folder.exists():
            shutil.copy2(original_stage, vanilla_in_folder)
        loader_src = das_source / f"{code}{root_ext}"
        if not loader_src.exists():
            raise RuntimeError(f"DAS loader not found: {loader_src}")
        shutil.copy2(loader_src, original_stage)


def install_stage_job(project_path: Path, job: StageJob) -> str:
    project_files = project_path.parent / "files"
    stage_info = LEGAL_STAGES[job.code]
    data = _extract_stage_data(job.zip_path)
    if job.mode == "default-replacement":
        target = project_files / f"{job.code}{stage_info['root_ext']}"
        target.write_bytes(data)
        return _display_path(target)

    if job.mode != "das":
        raise RuntimeError(f"unknown stage mode: {job.mode}")
    stage_folder = project_files / job.code
    stage_folder.mkdir(exist_ok=True)
    name = normalize_variant_name(add_button_indicator(job.display_name, job.button or "X"))
    target = stage_folder / f"{name}.dat"
    target.write_bytes(data)
    return _display_path(target)


def resolve_xdelta_exe() -> str:
    if sys.platform.startswith("win"):
        exe = PROJECT_ROOT / "utility" / "xdelta" / "xdelta3.exe"
        if exe.exists():
            return str(exe)
    return "xdelta3"


def create_bundle(
    vanilla_iso: Path,
    final_iso: Path,
    bundle_path: Path,
    *,
    name: str,
    description: str,
    build_name: str,
    texture_pack_path: Path | None = None,
) -> None:
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="duel_bundle_") as temp_name:
        temp_dir = Path(temp_name)
        bundle_dir = temp_dir / "bundle"
        bundle_dir.mkdir()
        patch_path = bundle_dir / "patch.xdelta"
        cp = _run(
            [resolve_xdelta_exe(), "-e", "-1", "-s", vanilla_iso, final_iso, patch_path],
            timeout=3600,
        )
        if cp.returncode != 0:
            raise RuntimeError((cp.stderr or cp.stdout or "xdelta3 failed").strip())

        texture_count = 0
        if texture_pack_path and texture_pack_path.exists():
            textures_dir = bundle_dir / "textures"
            textures_dir.mkdir()
            for png in texture_pack_path.glob("*.png"):
                shutil.copy2(png, textures_dir / png.name)
                texture_count += 1

        write_json(
            bundle_dir / "manifest.json",
            {
                "version": "1.0",
                "name": name,
                "description": description,
                "build_name": build_name,
                "created": datetime.now(timezone.utc).isoformat(),
                "texture_count": texture_count,
                "has_image": False,
            },
        )
        with zipfile.ZipFile(bundle_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in bundle_dir.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(bundle_dir))


def _rel_to_manifest(path: Path, manifest_dir: Path) -> str:
    try:
        return path.resolve().relative_to(manifest_dir.resolve()).as_posix()
    except ValueError:
        try:
            return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
        except ValueError:
            return str(path)


def harness_payload(result: ValidationResult) -> dict[str, Any]:
    """Return endpoint-ready import/remove/stage work derived from validation.

    The HTTP endpoints expect repo-relative storage paths, while validation keeps
    absolute paths so file checks are unambiguous.
    """
    import_items = []
    for fighter, paths in result.imports.items():
        for zip_path in paths:
            import_items.append({"fighter": fighter, "costumePath": _display_path(Path(zip_path))})

    remove_items = []
    for fighter, indices in result.removals.items():
        for index in indices:
            remove_items.append({"fighter": fighter, "costumeIndex": index})

    stage_items = []
    for job in result.stage_jobs:
        stage_items.append({
            "stageCode": job.code,
            "stage": LEGAL_STAGES[job.code]["stage"],
            "stageFolder": LEGAL_STAGES[job.code]["folder"],
            "mode": job.mode,
            "button": job.button,
            "variantPath": _display_path(job.zip_path),
            "displayName": job.display_name,
        })

    return {
        "visibleSlots": result.visible_slots,
        "generatedCostumeDats": result.generated_costume_dats,
        "importItems": import_items,
        "removeItems": remove_items,
        "stageItems": stage_items,
    }


def update_manifest_build(
    manifest_path: Path,
    manifest: dict[str, Any],
    *,
    vanilla_md5: str,
    project_path: Path,
    final_iso: Path,
    bundle_path: Path | None,
) -> None:
    manifest.setdefault("created_at", datetime.now(timezone.utc).isoformat())
    build = manifest.setdefault("build", {})
    build["sourceIsoMd5"] = vanilla_md5
    build["nucleusProject"] = _rel_to_manifest(project_path, PROJECT_ROOT)
    build["finalIso"] = _rel_to_manifest(final_iso, manifest_path.parent)
    if bundle_path:
        build["bundle"] = _rel_to_manifest(bundle_path, manifest_path.parent)
    verification = manifest.setdefault("verification", {})
    verification.setdefault("bootHealth", "not_run")
    verification.setdefault("stageCaptures", "not_run")
    verification.setdefault("notes", [])
    write_json(manifest_path, manifest)


def assemble(args: argparse.Namespace) -> int:
    manifest_path = Path(args.manifest).resolve()
    manifest = read_json(manifest_path)
    result = validate_manifest(manifest, manifest_path, check_files=not args.skip_artifact_checks)

    print(f"visible slots: {result.visible_slots}")
    print(f"generated costume DATs including Nana pairs: {result.generated_costume_dats}")
    print(f"costume import fighters: {len(result.imports)}")
    print(f"stage jobs: {len(result.stage_jobs)}")
    for warning in result.warnings:
        print(f"warning: {warning}")
    if result.errors:
        for error in result.errors:
            print(f"error: {error}", file=sys.stderr)
        return 2
    if args.emit_harness_json:
        print("HARNESS_JSON " + json.dumps(harness_payload(result), separators=(",", ":")))
    if args.dry_run:
        print("dry-run ok")
        return 0
    print(
        "Use tests/nucleus/build-duel-modpack.js for endpoint-driven assembly; "
        "this helper only validates and resolves manifest work.",
        file=sys.stderr,
    )
    return 2

    vanilla_iso = Path(args.vanilla_iso).resolve()
    if not vanilla_iso.exists():
        raise RuntimeError(f"vanilla ISO not found: {vanilla_iso}")
    vanilla_md5 = hash_md5(vanilla_iso)
    if not args.skip_md5 and vanilla_md5.lower() != VANILLA_ISO_MD5:
        raise RuntimeError(f"vanilla ISO MD5 mismatch: expected {VANILLA_ISO_MD5}, got {vanilla_md5}")

    project_name = args.project_name or manifest.get("build", {}).get("projectName") or f"duel-{manifest.get('agent', 'codex')}"
    duel_dir = manifest_path.parent
    exports_dir = duel_dir / "exports"
    project_record_dir = duel_dir / "project"
    exports_dir.mkdir(parents=True, exist_ok=True)
    project_record_dir.mkdir(parents=True, exist_ok=True)

    print(f"creating project {project_name}")
    project_path = create_project(vanilla_iso, project_name, force=args.force)
    (project_record_dir / "project_name.txt").write_text(project_name + "\n", encoding="utf-8")

    import_manifest = project_record_dir / "import-costumes.json"
    remove_manifest = project_record_dir / "remove-costumes.json"
    write_json(import_manifest, result.imports)
    write_json(remove_manifest, result.removals)

    print(f"importing {sum(len(v) for v in result.imports.values())} generated costume files")
    run_mexcli(["import-costumes", project_path, import_manifest], timeout=7200)
    print("removing original vanilla visible slots")
    run_mexcli(["remove-costumes", project_path, remove_manifest], timeout=3600)

    if any(job.mode == "das" for job in result.stage_jobs):
        print("installing DAS framework")
        install_das_framework(project_path)
    for job in result.stage_jobs:
        target = install_stage_job(project_path, job)
        detail = f" hold {job.button}" if job.button else ""
        print(f"installed stage {job.code} as {job.mode}{detail}: {target}")

    final_iso = exports_dir / "final.iso"
    if not args.no_export:
        print(f"exporting ISO: {_display_path(final_iso)}")
        run_mexcli(
            [
                "export",
                project_path,
                final_iso,
                str(args.csp_compression),
                str(args.color_smash).lower(),
                str(args.skip_compression).lower(),
            ],
            timeout=7200,
        )
    else:
        print("skipping ISO export (--no-export)")

    bundle_path = exports_dir / "final.ssbm"
    if not args.no_bundle:
        if not final_iso.exists():
            raise RuntimeError("cannot create bundle because final.iso was not exported")
        print(f"creating bundle: {_display_path(bundle_path)}")
        create_bundle(
            vanilla_iso,
            final_iso,
            bundle_path,
            name=manifest.get("theme") or project_name,
            description=f"SSBM Nucleus duel submission by {manifest.get('agent', 'unknown')}",
            build_name=project_name,
        )
    else:
        bundle_path = None
        print("skipping .ssbm bundle (--no-bundle)")

    if not args.no_update_manifest:
        update_manifest_build(
            manifest_path,
            manifest,
            vanilla_md5=vanilla_md5,
            project_path=project_path,
            final_iso=final_iso,
            bundle_path=bundle_path,
        )

    print("duel assembly complete")
    print(f"project: {_display_path(project_path)}")
    print(f"iso: {_display_path(final_iso)}")
    if bundle_path:
        print(f"bundle: {_display_path(bundle_path)}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble a modpack duel submission from manifest.json")
    parser.add_argument("manifest", help="Path to duel/<agent_slug>/manifest.json")
    parser.add_argument("--vanilla-iso", help=argparse.SUPPRESS)
    parser.add_argument("--project-name", help="Managed Nucleus project name, default duel-<agent>")
    parser.add_argument("--dry-run", action="store_true", help="Validate only; do not create project or export")
    parser.add_argument("--emit-harness-json", action="store_true", help="Print endpoint-ready resolved work as HARNESS_JSON")
    parser.add_argument("--force", action="store_true", help="Replace an existing managed project with the same name")
    parser.add_argument("--skip-md5", action="store_true", help="Do not enforce the vanilla ISO MD5")
    parser.add_argument("--skip-artifact-checks", action="store_true", help="Do not require plan/preview files during validation")
    parser.add_argument("--no-export", action="store_true", help="Stop after project assembly")
    parser.add_argument("--no-bundle", action="store_true", help="Do not create exports/final.ssbm")
    parser.add_argument("--no-update-manifest", action="store_true", help="Do not write build paths back to manifest.json")
    parser.add_argument("--csp-compression", default="1.0", help="MexCLI export CSP compression, 0.1-1.0")
    parser.add_argument("--color-smash", action="store_true", help="Enable export color-smash")
    parser.add_argument("--skip-compression", action="store_true", help="Pass skip-compression=true to MexCLI export")
    args = parser.parse_args(argv)
    return args


def main(argv: list[str] | None = None) -> int:
    try:
        return assemble(parse_args(argv or sys.argv[1:]))
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
