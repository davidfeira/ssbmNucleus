from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from PIL import Image, ImageDraw, ImageOps


DUEL_DIR = Path(__file__).resolve().parent
REPO = DUEL_DIR.parents[1]
BACKEND = REPO / "backend"
sys.path.insert(0, str(BACKEND))

from core.config import STORAGE_PATH  # noqa: E402
from core.constants import CHAR_PREFIXES, VANILLA_CSS_COLOR_ORDER, VANILLA_ISO_MD5  # noqa: E402
from skinlab.stage_ops import apply_stage_plan, stage_file_name  # noqa: E402


AGENT = "codex"
THEME = "Circuit Shrine"
THEME_NOTES = (
    "Circuit Shrine turns the roster into ceremonial arcade guardians: black lacquer, "
    "pearlescent ceramic armor, jade and cyan circuit traces, magenta signal gems, "
    "and warm gold seals. Slots vary by accent hue while preserving silhouettes."
)
MODEL_ID = "sd-turbo"
IMAGE_PROVIDER = "local"

MATERIALS = {
    "lacquer_circuit": {
        "seed": 6101,
        "prompt": (
            "black lacquer fabric with fine jade and cyan circuit traces, subtle gold "
            "foil inlay, seamless tileable game texture, high contrast but readable"
        ),
    },
    "ceramic_metal": {
        "seed": 6102,
        "prompt": (
            "pearlescent white ceramic and brushed gunmetal panels with tiny teal "
            "circuit engravings, seamless tileable sci fi shrine material"
        ),
    },
    "aurora_fiber": {
        "seed": 6103,
        "prompt": (
            "soft iridescent fur and woven fiber, aurora cyan violet jade strands, "
            "seamless tileable character material, clean readable texture"
        ),
    },
    "gold_seal": {
        "seed": 6104,
        "prompt": (
            "aged gold foil over dark enamel with small geometric shrine seals, "
            "seamless tileable ornament texture, crisp luminous highlights"
        ),
    },
    "stage_deck": {
        "seed": 6105,
        "prompt": (
            "legal fighting stage floor of dark graphite lacquer, bright cyan edge "
            "inlays, gold circuit seams, seamless tileable arcade shrine deck"
        ),
    },
    "stage_backdrop": {
        "seed": 6106,
        "style": "scene",
        "prompt": (
            "wide aurora night shrine skyline with floating circuit lanterns, teal "
            "and magenta nebula clouds, no text, readable game background"
        ),
    },
}

PALETTES = [
    {"primary": 182, "secondary": 48, "detail": 318, "skin": 36},
    {"primary": 316, "secondary": 172, "detail": 45, "skin": 30},
    {"primary": 226, "secondary": 94, "detail": 333, "skin": 38},
    {"primary": 144, "secondary": 28, "detail": 205, "skin": 32},
    {"primary": 270, "secondary": 176, "detail": 52, "skin": 34},
    {"primary": 18, "secondary": 196, "detail": 292, "skin": 40},
]

STAGES = {
    "GrNBa": {
        "stage": "Battlefield",
        "folder": "battlefield",
        "variant": "cshr-bf",
        "display": "CircuitShrineBF",
    },
    "GrNLa": {
        "stage": "Final Destination",
        "folder": "final_destination",
        "variant": "cshr-fd",
        "display": "CircuitShrineFD",
    },
    "GrSt": {
        "stage": "Yoshi's Story",
        "folder": "yoshis_story",
        "variant": "cshr-ys",
        "display": "CircuitShrineYS",
    },
    "GrOp": {
        "stage": "Dream Land N64",
        "folder": "dreamland",
        "variant": "cshr-dl",
        "display": "CircuitShrineDL",
    },
    "GrPs": {
        "stage": "Pokemon Stadium",
        "folder": "pokemon_stadium",
        "variant": "cshr-ps",
        "display": "CircuitShrinePS",
    },
    "GrIz": {
        "stage": "Fountain of Dreams",
        "folder": "fountain_of_dreams",
        "variant": "cshr-fod",
        "display": "CircuitShrineFoD",
    },
}


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(DUEL_DIR.resolve()).as_posix()
    except ValueError:
        try:
            return path.resolve().relative_to(REPO.resolve()).as_posix()
        except ValueError:
            return str(path)


def api_json(base: str, method: str, route: str, body: dict[str, Any] | None = None, timeout: int = 120) -> dict[str, Any]:
    url = f"{base}{route}"
    response = requests.request(method, url, json=body, timeout=timeout)
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"{method} {route} returned non-JSON {response.status_code}: {response.text[:300]}") from exc
    if response.status_code >= 400 or payload.get("success") is False:
        raise RuntimeError(f"{method} {route} failed: {payload}")
    return payload


def api_bytes(base: str, route: str, timeout: int = 120) -> bytes:
    response = requests.get(f"{base}{route}", timeout=timeout)
    response.raise_for_status()
    return response.content


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", value)


def costume_code(character: str, suffix: str) -> str:
    return f"Pl{CHAR_PREFIXES[character]}{suffix}"


def vanilla_dat_path(character: str, code: str) -> Path | None:
    direct = REPO / "utility" / "assets" / "vanilla" / character / code / f"{code}.dat"
    if direct.exists():
        return direct
    return None


def fallback_vanilla_dat_path(character: str) -> tuple[Path, str]:
    for suffix in VANILLA_CSS_COLOR_ORDER.get(character, []):
        code = costume_code(character, suffix) if character != "Nana" else f"PlNn{suffix}"
        path = vanilla_dat_path(character, code)
        if path:
            return path, code
    raise RuntimeError(f"no fallback vanilla DAT found for {character}")


def load_metadata() -> dict[str, Any]:
    return read_json(STORAGE_PATH / "metadata.json", {"characters": {}, "stages": {}})


def save_metadata(metadata: dict[str, Any]) -> None:
    write_json(STORAGE_PATH / "metadata.json", metadata)


def find_skin(character: str, name: str, code: str) -> dict[str, Any] | None:
    metadata = load_metadata()
    skins = metadata.get("characters", {}).get(character, {}).get("skins", [])
    for skin in reversed(skins):
        if skin.get("color") == name and skin.get("costume_code") == code:
            zip_path = STORAGE_PATH / character / str(skin.get("filename", ""))
            if zip_path.exists():
                return skin
    return None


def preview_media_bytes(preview_path: Path, character: str, code: str) -> tuple[bytes, bytes]:
    source = preview_path
    if not source.exists():
        vanilla = REPO / "utility" / "assets" / "vanilla" / character / code / "csp.png"
        source = vanilla if vanilla.exists() else source

    try:
        img = Image.open(source).convert("RGBA")
    except Exception:
        img = Image.new("RGBA", (640, 360), (10, 12, 18, 255))
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), f"{THEME} {character} {code}", fill=(210, 245, 245, 255))

    csp = ImageOps.fit(img, (136, 188), Image.LANCZOS, centering=(0.5, 0.42))
    stock = ImageOps.fit(img, (24, 24), Image.LANCZOS, centering=(0.5, 0.42))
    csp_io = io.BytesIO()
    stock_io = io.BytesIO()
    csp.save(csp_io, format="PNG")
    stock.save(stock_io, format="PNG")
    return csp_io.getvalue(), stock_io.getvalue()


def rewrite_zip_with_media(path: Path, csp_data: bytes, stock_data: bytes) -> None:
    existing: dict[str, bytes] = {}
    if path.exists():
        with zipfile.ZipFile(path, "r") as zf:
            for name in zf.namelist():
                if name.lower() in {"csp.png", "stc.png", "stock.png"}:
                    continue
                existing[name] = zf.read(name)

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in existing.items():
            zf.writestr(name, data)
        zf.writestr("csp.png", csp_data)
        zf.writestr("stc.png", stock_data)
    tmp_path.replace(path)


def ensure_zip_media(character: str, skin_id: str, code: str, preview_path: Path) -> None:
    folder = STORAGE_PATH / character
    path = folder / f"{skin_id}.zip"
    if not path.exists():
        return

    needs_rewrite = True
    with zipfile.ZipFile(path, "r") as zf:
        lower = {name.lower() for name in zf.namelist()}
        needs_rewrite = not {"csp.png", "stc.png"}.issubset(lower)

    csp_data, stock_data = preview_media_bytes(preview_path, character, code)
    if needs_rewrite:
        rewrite_zip_with_media(path, csp_data, stock_data)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{skin_id}_csp.png").write_bytes(csp_data)
    (folder / f"{skin_id}_stc.png").write_bytes(stock_data)

    metadata = load_metadata()
    skins = metadata.setdefault("characters", {}).setdefault(character, {"skins": []}).setdefault("skins", [])
    for skin in skins:
        if skin.get("id") == skin_id:
            skin["has_csp"] = True
            skin["has_stock"] = True
            skin["csp_source"] = "duel_preview"
            skin["stock_source"] = "duel_preview"
            break
    save_metadata(metadata)


def upsert_manual_skin(character: str, entry: dict[str, Any]) -> None:
    metadata = load_metadata()
    char_data = metadata.setdefault("characters", {}).setdefault(character, {"skins": []})
    char_data["skins"] = [skin for skin in char_data.get("skins", []) if skin.get("id") != entry["id"]]
    char_data["skins"].append(entry)
    save_metadata(metadata)


def upsert_stage_variant(folder: str, entry: dict[str, Any]) -> None:
    metadata = load_metadata()
    stage_data = metadata.setdefault("stages", {}).setdefault(folder, {"variants": []})
    stage_data["variants"] = [variant for variant in stage_data.get("variants", []) if variant.get("id") != entry["id"]]
    stage_data["variants"].append(entry)
    save_metadata(metadata)


def generate_materials(base: str) -> tuple[dict[str, Path], list[str]]:
    material_dir = DUEL_DIR / "materials"
    material_dir.mkdir(parents=True, exist_ok=True)
    models: set[str] = set()
    resolved: dict[str, Path] = {}

    for key, spec in MATERIALS.items():
        out_copy = material_dir / f"{key}.png"
        if out_copy.exists():
            resolved[key] = out_copy
            models.add(MODEL_ID)
            continue
        payload = {
            "prompt": spec["prompt"],
            "provider": IMAGE_PROVIDER,
            "model": MODEL_ID,
            "name": f"duel_codex_{key}",
            "width": 512,
            "height": 512,
            "seed": spec["seed"],
            "tier": "standard",
            "kind": "material",
        }
        if spec.get("style"):
            payload["style"] = spec["style"]
        data = api_json(base, "POST", "/api/mex/skin-lab/generate-texture", payload, timeout=900)
        model = data.get("model")
        if model:
            models.add(model)
        src = Path(data["imagePath"])
        if not src.exists():
            raise RuntimeError(f"generated material missing: {src}")
        shutil.copy2(src, out_copy)
        resolved[key] = out_copy

    write_json(
        DUEL_DIR / "materials" / "materials.json",
        {
            key: {
                "prompt": spec["prompt"],
                "provider": IMAGE_PROVIDER,
                "model": MODEL_ID,
                "seed": spec["seed"],
                "path": rel(resolved[key]),
            }
            for key, spec in MATERIALS.items()
        },
    )
    return resolved, sorted(models or {MODEL_ID})


def classify_region(region: str) -> str:
    lower = region.lower()
    if any(token in lower for token in ("eye", "visor", "jewel", "gem", "emblem", "cheek", "mouth", "face_detail", "nose")):
        return "detail"
    if any(token in lower for token in ("skin", "face", "hand")):
        return "skin"
    if any(token in lower for token in ("cloth", "cape", "dress", "robe", "tunic", "pants", "shirt", "hat")):
        return "cloth"
    if any(token in lower for token in ("armor", "metal", "sword", "weapon", "shell", "boot", "shoe", "glove")):
        return "armor"
    if any(token in lower for token in ("fur", "hair", "body", "feather")):
        return "fur"
    return "other"


def character_plan(character: str, code: str, slot: int, region_map: dict[str, Any]) -> dict[str, Any]:
    palette = PALETTES[slot % len(PALETTES)]
    regions = list((region_map.get("regions") or {}).keys())
    skin_name = f"CShrine-{safe_name(character)}-{code[-2:]}"

    composite_budget = 3
    preferred = ["cloth", "cape", "dress", "armor", "fur", "hair", "body"]
    steps: list[dict[str, Any]] = []
    covered: set[str] = set()

    def add_composite(region: str, material_key: str, lo: float = 0.38, hi: float = 1.72) -> None:
        nonlocal composite_budget
        if composite_budget <= 0 or region in covered:
            return
        composite_budget -= 1
        covered.add(region)
        spec = MATERIALS[material_key]
        steps.append(
            {
                "op": "composite",
                "region": region,
                "endpoint": "/api/mex/skin-lab/composite",
                "material_key": material_key,
                "material_prompt": spec["prompt"],
                "provider": IMAGE_PROVIDER,
                "model": MODEL_ID,
                "mode": "project",
                "modulate": {"lo": lo, "hi": hi},
            }
        )

    for wanted in preferred:
        for region in regions:
            if region in covered:
                continue
            kind = classify_region(region)
            if wanted not in region.lower() and kind != wanted:
                continue
            if kind == "cloth":
                add_composite(region, "lacquer_circuit")
            elif kind == "armor":
                add_composite(region, "ceramic_metal", 0.42, 1.82)
            elif kind == "fur":
                add_composite(region, "aurora_fiber", 0.36, 1.62)

    for region in regions:
        if region in covered:
            continue
        kind = classify_region(region)
        covered.add(region)
        if kind == "detail":
            steps.append(
                {
                    "op": "tint",
                    "region": region,
                    "endpoint": "/api/mex/skin-lab/tint",
                    "hue": palette["detail"],
                    "saturation": 86,
                    "force": True,
                }
            )
        elif kind == "skin":
            steps.append(
                {
                    "op": "tint",
                    "region": region,
                    "endpoint": "/api/mex/skin-lab/tint",
                    "hue": palette["skin"],
                    "saturation": 32,
                }
            )
        elif kind == "armor":
            steps.append(
                {
                    "op": "tint",
                    "region": region,
                    "endpoint": "/api/mex/skin-lab/tint",
                    "hue": palette["secondary"],
                    "saturation": 58,
                }
            )
        elif kind == "fur":
            steps.append(
                {
                    "op": "tint",
                    "region": region,
                    "endpoint": "/api/mex/skin-lab/tint",
                    "hue": palette["primary"],
                    "saturation": 54,
                }
            )
        else:
            steps.append(
                {
                    "op": "hue-shift",
                    "region": region,
                    "endpoint": "/api/mex/skin-lab/hue-shift",
                    "hueShift": ((palette["primary"] + slot * 17) % 360) - 180,
                    "saturationShift": 24,
                }
            )

    return {
        "skin_name": skin_name,
        "theme_notes": THEME_NOTES,
        "source": {"character": character, "costumeCode": code, "slot": slot},
        "steps": steps,
        "review": {
            "assessment": (
                "Agent-authored review target: every mapped region receives a "
                "Circuit Shrine material, tint, or hue shift; protected facial "
                "details are tinted rather than composited for readability."
            ),
            "fixes": [],
        },
    }


def execute_character_steps(base: str, plan: dict[str, Any], material_paths: dict[str, Path]) -> None:
    composites = [step for step in plan["steps"] if step["op"] == "composite"]
    rest = [step for step in plan["steps"] if step["op"] != "composite"]
    for step in composites + rest:
        op = step["op"]
        if op == "composite":
            body = {
                "region": step["region"],
                "material": {"path": str(material_paths[step["material_key"]])},
                "modulate": step.get("modulate") or {},
                "mode": step.get("mode", "project"),
            }
            if step.get("force"):
                body["force"] = True
            api_json(base, "POST", "/api/mex/skin-lab/composite", body, timeout=900)
        elif op == "tint":
            body = {
                "region": step["region"],
                "hue": step["hue"],
                "saturation": step.get("saturation", 60),
            }
            if step.get("force"):
                body["force"] = True
            api_json(base, "POST", "/api/mex/skin-lab/tint", body, timeout=180)
        elif op == "hue-shift":
            api_json(
                base,
                "POST",
                "/api/mex/skin-lab/hue-shift",
                {
                    "region": step["region"],
                    "hueShift": step.get("hueShift", 0),
                    "saturationShift": step.get("saturationShift", 0),
                },
                timeout=180,
            )
        else:
            raise RuntimeError(f"unknown op {op}")


def capture_preview(base: str, path: Path, label: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Burn one frame after the texture pushes, then save the next render.
        api_bytes(base, "/api/mex/skin-lab/frame?fresh=8", timeout=90)
        jpg = api_bytes(base, "/api/mex/skin-lab/frame?fresh=3", timeout=90)
        path.write_bytes(jpg)
        return True
    except Exception:
        img = Image.new("RGB", (640, 360), (10, 12, 18))
        draw = ImageDraw.Draw(img)
        draw.text((24, 24), label[:90], fill=(180, 240, 240))
        draw.text((24, 52), "Preview capture failed; asset was still exported.", fill=(255, 210, 120))
        img.save(path, quality=88)
        return False


def save_skin(base: str, character: str, name: str, code: str) -> dict[str, Any]:
    api_json(
        base,
        "POST",
        "/api/mex/skin-lab/save",
        {"name": name, "duplicate_action": "import_anyway"},
        timeout=900,
    )
    skin = find_skin(character, name, code)
    if not skin:
        raise RuntimeError(f"saved skin not found in metadata: {character} {name} {code}")
    return skin


def character_entry(character: str, slot: int, code: str, skin_name: str, skin_id: str, filename: str, plan: Path, preview: Path) -> dict[str, Any]:
    return {
        "slot": slot,
        "costumeCode": code,
        "skinName": skin_name,
        "vaultSkinId": skin_id,
        "filename": filename,
        "zipPath": rel(STORAGE_PATH / character / filename),
        "plan": rel(plan),
        "preview": rel(preview),
    }


def process_regular_character(
    base: str,
    character: str,
    suffix: str,
    slot: int,
    material_paths: dict[str, Path],
) -> tuple[dict[str, Any], list[str]]:
    code = costume_code(character, suffix)
    name = f"CShrine-{safe_name(character)}-{suffix}"
    plan_path = DUEL_DIR / "plans" / "characters" / character / f"{code}.json"
    preview_path = DUEL_DIR / "previews" / "characters" / character / f"{code}_review.jpg"
    notes: list[str] = []

    existing = find_skin(character, name, code)
    if existing and plan_path.exists() and preview_path.exists():
        ensure_zip_media(character, existing["id"], code, preview_path)
        return character_entry(character, slot, code, name, existing["id"], existing["filename"], plan_path, preview_path), notes

    source_path = vanilla_dat_path(character, code)
    manual_export = source_path is None
    if manual_export:
        source_path, source_code = fallback_vanilla_dat_path(character)
        open_payload = {"character": character, "datPath": str(source_path)}
    else:
        source_code = code
        open_payload = {"character": character, "costumeCode": code}

    api_json(base, "POST", "/api/mex/skin-lab/open", open_payload, timeout=240)
    try:
        regions = api_json(base, "GET", "/api/mex/skin-lab/regions", timeout=120)["regionMap"]
        plan = character_plan(character, code, slot, regions)
        if manual_export:
            plan["source"]["fallbackCostumeCode"] = source_code
            plan["source"]["fallbackReason"] = f"{code}.dat was missing from utility/assets/vanilla"
        write_json(plan_path, plan)
        execute_character_steps(base, plan, material_paths)
        if not capture_preview(base, preview_path, f"{character} {code}"):
            notes.append(f"{character} {code}: viewer preview capture fell back to placeholder")
        dat = api_bytes(base, "/api/mex/skin-lab/export-dat", timeout=300)
        _, filename = write_half_zip(character, name, code, dat, preview_path)
        if manual_export:
            notes.append(f"{character} {code}: generated from fallback source {source_code} because the vanilla DAT was missing")
        return character_entry(character, slot, code, name, name, filename, plan_path, preview_path), notes
    finally:
        try:
            api_json(base, "POST", "/api/mex/skin-lab/close", timeout=30)
        except Exception:
            pass


def export_half_dat(base: str, character: str, code: str, plan_path: Path, preview_path: Path, material_paths: dict[str, Path], slot: int) -> tuple[bytes, list[str]]:
    notes: list[str] = []
    api_json(base, "POST", "/api/mex/skin-lab/open", {"character": character, "costumeCode": code}, timeout=240)
    try:
        regions = api_json(base, "GET", "/api/mex/skin-lab/regions", timeout=120)["regionMap"]
        plan = character_plan(character, code, slot, regions)
        write_json(plan_path, plan)
        execute_character_steps(base, plan, material_paths)
        if not capture_preview(base, preview_path, f"{character} {code}"):
            notes.append(f"{character} {code}: viewer preview capture fell back to placeholder")
        dat = api_bytes(base, "/api/mex/skin-lab/export-dat", timeout=300)
        return dat, notes
    finally:
        try:
            api_json(base, "POST", "/api/mex/skin-lab/close", timeout=30)
        except Exception:
            pass


def write_half_zip(character: str, skin_id: str, code: str, dat: bytes, preview_path: Path | None = None) -> tuple[Path, str]:
    folder = STORAGE_PATH / character
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{skin_id}.zip"
    path = folder / filename
    csp_data, stock_data = preview_media_bytes(preview_path or Path(), character, code)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{code}.dat", dat)
        zf.writestr("csp.png", csp_data)
        zf.writestr("stc.png", stock_data)
    (folder / f"{skin_id}_csp.png").write_bytes(csp_data)
    (folder / f"{skin_id}_stc.png").write_bytes(stock_data)
    entry = {
        "id": skin_id,
        "color": skin_id,
        "costume_code": code,
        "filename": filename,
        "has_csp": True,
        "has_stock": True,
        "csp_source": "duel_preview",
        "stock_source": "duel_preview",
        "date_added": datetime.now(timezone.utc).isoformat(),
        "dat_hash": hashlib.md5(dat).hexdigest(),
        "slippi_safe": True,
        "slippi_tested": False,
    }
    if character == "Nana":
        entry["is_nana"] = True
        entry["visible"] = False
    elif character == "Ice Climbers":
        entry["is_popo"] = True
        entry["visible"] = True
    upsert_manual_skin(character, entry)
    return path, filename


def process_ice_climbers(base: str, material_paths: dict[str, Path]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    entries: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    notes: list[str] = []
    popo_suffixes = VANILLA_CSS_COLOR_ORDER["Ice Climbers"]
    nana_suffixes = VANILLA_CSS_COLOR_ORDER["Nana"]

    for slot, (popo_suffix, nana_suffix) in enumerate(zip(popo_suffixes, nana_suffixes)):
        popo_code = costume_code("Ice Climbers", popo_suffix)
        nana_code = f"PlNn{nana_suffix}"
        popo_id = f"CShrine-IceClimbers-{popo_suffix}"
        nana_id = f"CShrine-Nana-{nana_suffix}"

        popo_plan = DUEL_DIR / "plans" / "characters" / "Ice Climbers" / f"{popo_code}.json"
        nana_plan = DUEL_DIR / "plans" / "characters" / "Nana" / f"{nana_code}.json"
        popo_preview = DUEL_DIR / "previews" / "characters" / "Ice Climbers" / f"{popo_code}_review.jpg"
        nana_preview = DUEL_DIR / "previews" / "characters" / "Nana" / f"{nana_code}_review.jpg"

        popo_zip = STORAGE_PATH / "Ice Climbers" / f"{popo_id}.zip"
        nana_zip = STORAGE_PATH / "Nana" / f"{nana_id}.zip"
        if not (popo_zip.exists() and nana_zip.exists() and popo_plan.exists() and nana_plan.exists()):
            popo_dat, popo_notes = export_half_dat(base, "Ice Climbers", popo_code, popo_plan, popo_preview, material_paths, slot)
            nana_dat, nana_notes = export_half_dat(base, "Nana", nana_code, nana_plan, nana_preview, material_paths, slot)
            notes.extend(popo_notes)
            notes.extend(nana_notes)
            write_half_zip("Ice Climbers", popo_id, popo_code, popo_dat, popo_preview)
            write_half_zip("Nana", nana_id, nana_code, nana_dat, nana_preview)
        ensure_zip_media("Ice Climbers", popo_id, popo_code, popo_preview)
        ensure_zip_media("Nana", nana_id, nana_code, nana_preview)

        entries.append(
            character_entry(
                "Ice Climbers",
                slot,
                popo_code,
                popo_id,
                popo_id,
                f"{popo_id}.zip",
                popo_plan,
                popo_preview,
            )
        )
        pairs.append(
            {
                "slot": slot,
                "popoCode": popo_code,
                "nanaCode": nana_code,
                "popoVaultSkinId": popo_id,
                "nanaVaultSkinId": nana_id,
                "nanaZipPath": rel(nana_zip),
                "nanaPlan": rel(nana_plan),
                "nanaPreview": rel(nana_preview),
            }
        )

    return entries, pairs, notes


def stage_step_kind(region: str) -> str:
    lower = region.lower()
    if any(token in lower for token in ("background", "sky", "cloud", "stand")):
        return "background"
    if any(token in lower for token in ("deck", "platform", "ground", "turf", "grass", "island", "edge")):
        return "deck"
    if any(token in lower for token in ("water", "river")):
        return "water"
    if any(token in lower for token in ("wood", "trunk", "foliage", "flower")):
        return "nature"
    return "detail"


def build_stage_plan(code: str, region_map: dict[str, Any]) -> dict[str, Any]:
    info = STAGES[code]
    steps: list[dict[str, Any]] = []
    for region in (region_map.get("regions") or {}).keys():
        kind = stage_step_kind(region)
        if code == "GrNLa":
            steps.append(
                {
                    "op": "composite",
                    "region": region,
                    "material_key": "stage_deck",
                    "material_prompt": MATERIALS["stage_deck"]["prompt"],
                    "provider": IMAGE_PROVIDER,
                    "model": MODEL_ID,
                    "modulate": {"lo": 1.05, "hi": 2.15},
                }
            )
        elif kind == "background":
            steps.append(
                {
                    "op": "composite",
                    "region": region,
                    "material_key": "stage_backdrop",
                    "material_prompt": MATERIALS["stage_backdrop"]["prompt"],
                    "provider": IMAGE_PROVIDER,
                    "model": MODEL_ID,
                    "modulate": {"lo": 0.55, "hi": 1.55},
                }
            )
        elif kind == "deck":
            steps.append(
                {
                    "op": "composite",
                    "region": region,
                    "material_key": "stage_deck",
                    "material_prompt": MATERIALS["stage_deck"]["prompt"],
                    "provider": IMAGE_PROVIDER,
                    "model": MODEL_ID,
                    "modulate": {"lo": 0.55, "hi": 1.85},
                }
            )
        elif kind == "water":
            steps.append({"op": "tint", "region": region, "hue": 188, "saturation": 72})
        elif kind == "nature":
            steps.append({"op": "tint", "region": region, "hue": 154, "saturation": 58})
        else:
            steps.append({"op": "tint", "region": region, "hue": 292, "saturation": 62})
    return {
        "skin_name": info["display"],
        "stage": info["stage"],
        "stageCode": code,
        "mode": "das",
        "button": "X",
        "theme_notes": THEME_NOTES,
        "steps": steps,
        "review": {
            "assessment": (
                "Offline review target: playfield regions use high-contrast lacquer deck "
                "materials, backgrounds use the aurora shrine scene material, and animated "
                "or delicate regions are tinted to avoid smearing gameplay surfaces."
            ),
            "fixes": [],
        },
    }


def make_stage_preview(work_dir: Path, out_path: Path, label: str) -> None:
    pngs = sorted((work_dir / "pngs").glob("*.png"))[:12]
    thumbs: list[Image.Image] = []
    for path in pngs:
        img = Image.open(path).convert("RGB")
        img.thumbnail((148, 96), Image.LANCZOS)
        tile = Image.new("RGB", (160, 120), (16, 18, 24))
        tile.paste(img, ((160 - img.width) // 2, 18))
        draw = ImageDraw.Draw(tile)
        draw.text((6, 4), path.stem, fill=(210, 240, 240))
        thumbs.append(tile)
    if not thumbs:
        thumbs.append(Image.new("RGB", (160, 120), (20, 20, 24)))
    cols = 4
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 160, rows * 120 + 32), (8, 10, 14))
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 8), label, fill=(220, 245, 245))
    for i, tile in enumerate(thumbs):
        sheet.paste(tile, ((i % cols) * 160, 32 + (i // cols) * 120))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def process_stage(code: str, material_paths: dict[str, Path]) -> dict[str, Any]:
    info = STAGES[code]
    plan_path = DUEL_DIR / "plans" / "stages" / f"{code}.json"
    preview_path = DUEL_DIR / "previews" / "stages" / f"{code}_capture.png"
    variant_dir = STORAGE_PATH / "das" / info["folder"]
    variant_dir.mkdir(parents=True, exist_ok=True)
    zip_path = variant_dir / f"{info['variant']}.zip"
    work_dir = DUEL_DIR / "work" / "stages" / code

    region_map = read_json(BACKEND / "assets" / "texture_regions" / "stages" / f"{code}.json", {})
    plan = build_stage_plan(code, region_map)
    write_json(plan_path, plan)

    if not zip_path.exists():
        def material_for(prompt: str, quality: bool = False) -> Path:
            for key, spec in MATERIALS.items():
                if spec["prompt"] == prompt:
                    return material_paths[key]
            return material_paths["stage_deck"]

        exec_steps = []
        for step in plan["steps"]:
            cleaned = dict(step)
            cleaned.pop("endpoint", None)
            cleaned.pop("provider", None)
            cleaned.pop("model", None)
            cleaned.pop("material_key", None)
            exec_steps.append(cleaned)
        out_dat = apply_stage_plan(code, exec_steps, [], work_dir, material_for)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(out_dat, stage_file_name(code))

    make_stage_preview(work_dir, preview_path, f"{info['stage']} - {info['display']}")
    shutil.copy2(preview_path, variant_dir / f"{info['variant']}_screenshot.png")
    dat_hash = ""
    with zipfile.ZipFile(zip_path, "r") as zf:
        stage_members = [name for name in zf.namelist() if name.lower().endswith((".dat", ".usd"))]
        if stage_members:
            dat_hash = hashlib.md5(zf.read(stage_members[0])).hexdigest()
    upsert_stage_variant(
        info["folder"],
        {
            "id": info["variant"],
            "name": info["display"],
            "filename": zip_path.name,
            "has_screenshot": True,
            "dat_hash": dat_hash,
            "screenshot_filename": f"{info['variant']}_screenshot.png",
            "date_added": datetime.now(timezone.utc).isoformat(),
        },
    )
    return {
        "stage": info["stage"],
        "skinName": info["display"],
        "mode": "das",
        "button": "X",
        "vaultVariantId": info["variant"],
        "filename": zip_path.name,
        "zipPath": rel(zip_path),
        "plan": rel(plan_path),
        "preview": rel(preview_path),
    }


def make_manifest(models: list[str], notes: list[str]) -> dict[str, Any]:
    return {
        "agent": AGENT,
        "theme": THEME,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "local_image_generation": {
            "required": True,
            "provider": IMAGE_PROVIDER,
            "models": models,
        },
        "characters": {},
        "ice_climbers_pairs": [],
        "stages": {},
        "build": {
            "projectName": "duel-codex",
            "sourceIsoMd5": VANILLA_ISO_MD5,
            "nucleusProject": "projects/duel-codex/project.mexproj",
            "finalIso": "exports/final.iso",
            "bundle": "exports/final.ssbm",
        },
        "verification": {
            "bootHealth": "not_run",
            "stageCaptures": "not_run",
            "notes": notes,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="http://127.0.0.1:5000")
    parser.add_argument("--limit-character-slots", type=int, default=0)
    parser.add_argument("--skip-stages", action="store_true")
    args = parser.parse_args()

    base = args.backend.rstrip("/")
    for path in (
        DUEL_DIR / "plans" / "characters",
        DUEL_DIR / "plans" / "stages",
        DUEL_DIR / "previews" / "characters",
        DUEL_DIR / "previews" / "stages",
        DUEL_DIR / "exports",
        DUEL_DIR / "project",
    ):
        path.mkdir(parents=True, exist_ok=True)

    api_json(base, "GET", "/api/mex/setup/status", timeout=60)
    status = api_json(base, "GET", "/api/mex/ai-engine/status", timeout=120)
    if not status.get("localModelReady"):
        raise RuntimeError(f"local image generation is not ready: {status}")
    material_paths, models = generate_materials(base)

    notes = [
        "Character previews are skin-lab render captures.",
        "Stage preview files are offline texture sheets; in-game DAS captures are not run by this generator.",
    ]
    manifest = make_manifest(models, notes)

    processed = 0
    for character, suffixes in VANILLA_CSS_COLOR_ORDER.items():
        if character in {"Mr. Game & Watch", "Nana"}:
            continue
        if character == "Ice Climbers":
            entries, pairs, ic_notes = process_ice_climbers(base, material_paths)
            manifest["characters"][character] = entries
            manifest["ice_climbers_pairs"] = pairs
            notes.extend(ic_notes)
            processed += len(entries)
            continue
        manifest["characters"][character] = []
        for slot, suffix in enumerate(suffixes):
            if args.limit_character_slots and processed >= args.limit_character_slots:
                write_json(DUEL_DIR / "manifest.json", manifest)
                print(f"limit reached at {processed} character slots")
                return 0
            print(f"[duel] character {processed + 1}: {character} {suffix}", flush=True)
            entry, entry_notes = process_regular_character(base, character, suffix, slot, material_paths)
            manifest["characters"][character].append(entry)
            notes.extend(entry_notes)
            processed += 1
            write_json(DUEL_DIR / "manifest.json", manifest)

    if not args.skip_stages:
        for code in STAGES:
            print(f"[duel] stage {code}", flush=True)
            manifest["stages"][code] = process_stage(code, material_paths)
            write_json(DUEL_DIR / "manifest.json", manifest)

    manifest["verification"]["notes"] = notes
    write_json(DUEL_DIR / "manifest.json", manifest)
    print(f"[duel] wrote {DUEL_DIR / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
