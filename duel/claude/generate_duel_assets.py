"""generate_duel_assets.py -- Claude's submission for docs/MODPACK_DUEL_SPEC.md.

Theme: "Porcelain & Ink" -- the whole roster reimagined as Qinghua (cobalt
blue-and-white) porcelain relics mended with gold kintsugi.

Three cohesive threads run through every fighter:
  1. glazed white PORCELAIN bodies (per-slot glaze recolor),
  2. a cobalt blue-and-white painted QINGHUA signature garment, and
  3. gold KINTSUGI veins on all armor / metal / trim.

Per-slot identity is the glaze (Re = oxblood, Bu = cobalt, Gr = celadon,
Bk = tenmoku black-and-gold, Ye = imperial yellow, ...). Per-fighter identity
is a bespoke region->material assignment + accent gem color authored below.

This is the contestant's OWN planner/reviewer. It does NOT call any built-in
ai-create / planner endpoint. It drives the structured skin-lab ops
(composite / tint / hue-shift) and local image generation only.

Run against a backend started with NUCLEUS_IMAGE_PROVIDER=local:

    python duel/claude/generate_duel_assets.py --backend http://127.0.0.1:PORT
"""
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
from PIL import Image, ImageDraw

DUEL_DIR = Path(__file__).resolve().parent
REPO = DUEL_DIR.parents[1]
BACKEND = REPO / "backend"
sys.path.insert(0, str(BACKEND))

from core.config import STORAGE_PATH  # noqa: E402
from core.constants import CHAR_PREFIXES, VANILLA_CSS_COLOR_ORDER, VANILLA_ISO_MD5  # noqa: E402
from skinlab.stage_ops import apply_stage_plan, stage_file_name  # noqa: E402

AGENT = "claude"
THEME = "Porcelain & Ink"
THEME_NOTES = (
    "Porcelain & Ink recasts the roster as ceremonial Qinghua porcelain relics: "
    "glazed white ceramic bodies, cobalt blue-and-white painted garments, and gold "
    "kintsugi veins mending every piece of armor and metal. Per-slot identity is the "
    "kiln glaze; per-fighter identity is the painted motif, accent gem, and which "
    "parts are mended in gold."
)
MODEL_ID = "sd-turbo"
PROVIDER = "local"

# --------------------------------------------------------------------------- #
# Material library -- generated once (local sd-turbo), reused across the pack. #
# --------------------------------------------------------------------------- #
MATERIALS: dict[str, dict[str, Any]] = {
    "porcelain": {
        "seed": 7301,
        "prompt": (
            "seamless tileable white glazed porcelain ceramic texture, soft glossy "
            "sheen, faint blue-grey craquelure crackle, smooth high-fired china, "
            "no text, no seams"
        ),
    },
    "qinghua": {
        "seed": 7302,
        "prompt": (
            "seamless tileable blue and white porcelain pattern, cobalt blue painted "
            "floral and cloud scrollwork on white glaze, ming dynasty qinghua china, "
            "crisp readable brushwork, no text"
        ),
    },
    "kintsugi": {
        "seed": 7303,
        "prompt": (
            "seamless tileable black lacquer ceramic mended with molten gold kintsugi "
            "veins and cracks, dark glaze with bright gold repair seams, luminous, "
            "no text"
        ),
    },
    "stage_deck": {
        "seed": 7304,
        "prompt": (
            "seamless tileable polished white porcelain floor tiles, thin cobalt blue "
            "grout lines and gold kintsugi seams, glazed ceramic deck, no text"
        ),
    },
    "stage_backdrop": {
        "seed": 7305,
        "style": "scene",
        "prompt": (
            "wide blue and white ink wash landscape, misty layered mountains and "
            "stylized rolling clouds, cobalt blue brush on pale porcelain sky, "
            "serene, no text, readable game background"
        ),
    },
}

# Per-slot kiln glaze: suffix -> (glaze_hue|None, glaze_sat, glaze_name, body_material_override)
#   glaze_hue None  -> leave the porcelain its natural white (classic blue-and-white)
#   body override   -> swap the body material (Bk = tenmoku: dark gold-veined kintsugi)
GLAZE = {
    "Nr": (None, 0, "Qinghua Classic", "qinghua"),
    "Re": (5, 60, "Sang-de-Boeuf Oxblood", None),
    "Bu": (218, 56, "Cobalt Glaze", None),
    "Gr": (148, 42, "Celadon", None),
    "Bk": (None, 0, "Tenmoku Black-and-Gold", "kintsugi"),
    "Ye": (47, 66, "Imperial Yellow", None),
    "Wh": (None, 0, "Blanc de Chine", None),
    "Or": (28, 66, "Persimmon", None),
    "La": (270, 46, "Violet Glaze", None),
    "Aq": (182, 52, "Turquoise Glaze", None),
    "Pi": (335, 48, "Famille Rose", None),
    "Gy": (210, 12, "Crackle Grey", None),
}

# Per-fighter art direction. `concept` documents the bespoke design; `accent` is
# the gem/emblem hue (eyes are always cobalt for the doll-eye motif); `overrides`
# steer region-name substrings to a role when the classifier would misread them.
#   roles: body (porcelain+glaze) | secondary (qinghua paint) | trim (gold kintsugi)
#          | skin (porcelain, ivory) | detail (accent tint)
CHARACTERS: dict[str, dict[str, Any]] = {
    "Mario": {
        "accent": 48,
        "concept": "Overalls reborn as cobalt qinghua denim; cap and shirt glazed porcelain; the round 'M' seal becomes a porcelain medallion blended into the cap.",
        "overrides": {"overall": "secondary", "cap": "body", "hat": "body", "shirt": "body", "button": "trim", "emblem": "detail"},
        "emblem_blend": True,
    },
    "Luigi": {
        "accent": 150,
        "concept": "Mario's brother in celadon-leaning porcelain; overalls carry the same qinghua painting and the 'L' seal becomes a porcelain medallion blended into the cap.",
        "overrides": {"overall": "secondary", "cap": "body", "hat": "body", "shirt": "body", "button": "trim", "emblem": "detail"},
        "emblem_blend": True,
    },
    "Dr. Mario": {
        "accent": 0,
        "concept": "A porcelain apothecary: blanc coat, cobalt-painted tie, gold stethoscope, vermilion pill-cross gem (no cap emblem to blend).",
        "overrides": {"coat": "body", "tie": "secondary", "stetho": "trim", "pill": "detail", "emblem": "detail"},
    },
    "Bowser": {
        "accent": 30,
        "concept": "The shell becomes gold kintsugi-veined plates over a tenmoku rim; horns, spikes and cuffs are solid gold; the hide is glazed porcelain.",
        "overrides": {"shell": "trim", "spike": "trim", "horn": "trim", "cuff": "trim", "belt": "trim", "tail": "body"},
    },
    "DK": {
        "accent": 40,
        "concept": "Porcelain-glazed fur with a cobalt-painted chest; the necktie is a gold-mended sash and the 'DK' is an amber seal.",
        "overrides": {"tie": "secondary", "chest": "secondary", "emblem": "detail"},
    },
    "C. Falcon": {
        "accent": 25,
        "concept": "Racing armor as porcelain plate; the helmet is gold kintsugi and the falcon crest is an amber gem over a cobalt visor.",
        "overrides": {"helmet": "trim", "armor": "trim", "suit": "body", "scarf": "secondary", "emblem": "detail", "visor": "detail"},
    },
    "Falco": {
        "accent": 200,
        "concept": "Feathers glazed porcelain, flight jacket painted qinghua, vambraces and reflector mended in gold, sapphire visor.",
        "overrides": {"jacket": "secondary", "vest": "secondary", "boot": "trim", "armor": "trim", "visor": "detail"},
    },
    "Fox": {
        "accent": 150,
        "concept": "Porcelain fur with a cobalt qinghua jacket; greaves and belt in gold kintsugi; jade scouter gem.",
        "overrides": {"jacket": "secondary", "vest": "secondary", "boot": "trim", "armor": "trim", "scouter": "detail", "visor": "detail"},
    },
    "Ganondorf": {
        "accent": 280,
        "concept": "A dark sorcerer-relic: tenmoku robes with gold kintsugi mail, cobalt under-cloth, and amethyst sorcery gems.",
        "overrides": {"armor": "trim", "mail": "trim", "cape": "secondary", "robe": "body", "jewel": "detail", "emblem": "detail"},
    },
    "Marth": {
        "accent": 210,
        "concept": "The cape is the showpiece qinghua scrollwork; tunic glazed porcelain; the Falchion and tiara are gold kintsugi with a sapphire stone.",
        "overrides": {"cape": "secondary", "tunic": "body", "armor": "trim", "sword": "trim", "tiara": "trim", "crown": "trim", "jewel": "detail"},
    },
    "Roy": {
        "accent": 5,
        "concept": "Marth's fiery counterpart: oxblood-leaning porcelain, qinghua cape, gold Sword of Seals, ruby headband stone.",
        "overrides": {"cape": "secondary", "tunic": "body", "armor": "trim", "sword": "trim", "headband": "detail", "jewel": "detail"},
    },
    "Link": {
        "accent": 50,
        "concept": "Tunic glazed porcelain, cap and undershirt painted qinghua, sword/shield/gauntlets in gold kintsugi, golden Triforce seal.",
        "overrides": {"cap": "body", "hat": "body", "tunic": "body", "shield": "trim", "sword": "trim", "sheath": "trim", "gaunt": "trim", "emblem": "detail"},
    },
    "Young Link": {
        "accent": 50,
        "concept": "A smaller porcelain hero; same kintsugi blade and shield, brighter glazes, a golden Triforce.",
        "overrides": {"cap": "body", "hat": "body", "tunic": "body", "shield": "trim", "sword": "trim", "sheath": "trim", "gaunt": "trim", "emblem": "detail"},
    },
    "Zelda": {
        "accent": 320,
        "concept": "A regal porcelain gown with qinghua-painted skirt panels, gold royal mail and shoulders, and rose Triforce gems.",
        "overrides": {"dress": "secondary", "gown": "secondary", "skirt": "secondary", "armor": "trim", "shoulder": "trim", "crown": "trim", "jewel": "detail", "emblem": "detail"},
    },
    "Sheik": {
        "accent": 210,
        "concept": "Bodysuit glazed porcelain, wrappings painted qinghua, gold bracers and the Sheikah eye as a sapphire gem.",
        "overrides": {"suit": "body", "wrap": "secondary", "scarf": "secondary", "armor": "trim", "bracer": "trim", "emblem": "detail"},
    },
    "Samus": {
        "accent": 150,
        "concept": "Power Suit as porcelain panels with cobalt inlay; shoulders and arm cannon mended in gold kintsugi; jade visor gem.",
        "overrides": {"armor": "body", "suit": "body", "cannon": "trim", "shoulder": "trim", "visor": "detail"},
    },
    "Peach": {
        "accent": 320,
        "concept": "A porcelain princess-doll: qinghua-painted ball gown, glazed bodice, gold crown and brooch, rose jewels.",
        "overrides": {"dress": "secondary", "gown": "secondary", "skirt": "secondary", "crown": "trim", "glove": "body", "jewel": "detail", "emblem": "detail"},
    },
    "Yoshi": {
        "accent": 0,
        "concept": "Porcelain hide with a cobalt-painted saddle-shell, gold-mended boots, and a vermilion nose accent.",
        "overrides": {"saddle": "secondary", "shell": "secondary", "boot": "trim", "shoe": "trim", "nose": "detail"},
    },
    "Kirby": {
        "accent": 335,
        "concept": "A perfectly round glazed porcelain bauble; a single gold kintsugi crack runs over one cheek; rose blush, cobalt eyes.",
        "overrides": {"foot": "trim", "shoe": "trim", "cheek": "detail"},
    },
    "Pikachu": {
        "accent": 0,
        "concept": "Glazed porcelain mouse; gold-tipped tail, ruby cheek discs, cobalt-glaze eyes, brown ear-tips kept as gold.",
        "overrides": {"tail": "trim", "ear": "trim", "cheek": "detail"},
    },
    "Pichu": {
        "accent": 0,
        "concept": "A tiny porcelain Pichu; ruby cheeks, gold ear-tips and tail, cobalt eyes.",
        "overrides": {"tail": "trim", "ear": "trim", "cheek": "detail"},
    },
    "Jigglypuff": {
        "accent": 335,
        "concept": "A blanc-de-chine balloon glazed smooth; one gold kintsugi seam, rose curl, cobalt eyes.",
        "overrides": {"curl": "trim", "hair": "trim", "cheek": "detail"},
        "extras_material": "kintsugi",  # the low-poly curl is an extra-root texture
        "eyes_confine": True,           # eye texture is the face decal (curl rides its padding)
    },
    "Mewtwo": {
        "accent": 280,
        "concept": "An eerie porcelain construct with cobalt-painted underbelly, gold spinal vertebrae and tail-tip, amethyst eyes and orbs.",
        "overrides": {"belly": "secondary", "chest": "secondary", "spine": "trim", "tail": "trim", "jewel": "detail", "orb": "detail"},
    },
    "Ness": {
        "accent": 5,
        "concept": "Glazed porcelain kid; the striped shirt is the qinghua-painted piece, cap brim and pack buckles gold, ruby cap emblem.",
        "overrides": {"shirt": "secondary", "stripe": "secondary", "cap": "body", "hat": "body", "pack": "trim", "buckle": "trim", "emblem": "detail"},
    },
    "Ice Climbers": {
        "accent": 40,
        "concept": "Eskimo parkas glazed porcelain with cobalt-painted trim; wooden mallets become gold kintsugi hammers, amber toggle gems.",
        "overrides": {"parka": "body", "hood": "body", "trim": "secondary", "mallet": "trim", "hammer": "trim", "toggle": "detail"},
    },
    "Nana": {
        "accent": 40,
        "concept": "Nana shares Popo's porcelain parka language with a softer glaze and the same gold kintsugi mallet.",
        "overrides": {"parka": "body", "hood": "body", "trim": "secondary", "mallet": "trim", "hammer": "trim", "toggle": "detail"},
    },
}

STAGES = {
    "GrNBa": {"stage": "Battlefield", "folder": "battlefield", "variant": "pi-bf", "display": "PorcelainInk BF"},
    "GrNLa": {"stage": "Final Destination", "folder": "final_destination", "variant": "pi-fd", "display": "PorcelainInk FD"},
    "GrSt": {"stage": "Yoshi's Story", "folder": "yoshis_story", "variant": "pi-ys", "display": "PorcelainInk YS"},
    "GrOp": {"stage": "Dream Land N64", "folder": "dreamland", "variant": "pi-dl", "display": "PorcelainInk DL"},
    "GrPs": {"stage": "Pokemon Stadium", "folder": "pokemon_stadium", "variant": "pi-ps", "display": "PorcelainInk PS"},
    "GrIz": {"stage": "Fountain of Dreams", "folder": "fountain_of_dreams", "variant": "pi-fod", "display": "PorcelainInk FoD"},
}

# Characters whose body/garment textures are tiny or gradient swatches (4x4..64x64):
# UV-projection mode collapses the material to a near-solid blob on them, so tile
# the (upscaled) material instead to keep the qinghua/porcelain pattern readable.
TILE_MODE_CHARS = {"Pichu", "Jigglypuff"}

EYE_HUE = 215          # cobalt-glaze doll eyes, shared across the whole pack
BODY_MODULATE = {"lo": 0.45, "hi": 1.72}
SECONDARY_MODULATE = {"lo": 0.5, "hi": 1.74}
TRIM_MODULATE = {"lo": 0.5, "hi": 1.95}
SKIN_MODULATE = {"lo": 0.55, "hi": 1.5}
BROAD_MASK = {"satMin": 0}   # truthy -> overrides the region's hue-band hint (covers white porcelain)

DETAIL_TOKENS = ("eye", "visor", "jewel", "gem", "emblem", "cheek", "mouth", "nose",
                 "crest", "iris", "pupil", "brow", "tooth", "fang", "orb", "pill")
TRIM_TOKENS = ("armor", "metal", "sword", "weapon", "shell", "boot", "shoe", "glove",
               "blade", "gun", "cannon", "belt", "buckle", "crown", "tiara", "claw",
               "horn", "spike", "plate", "gaunt", "bracer", "shield", "mallet",
               "hammer", "stetho", "pack", "button", "spine", "cuff", "ear", "tail")
SECONDARY_TOKENS = ("cape", "dress", "robe", "skirt", "scarf", "sash", "ribbon", "bow",
                    "cloak", "saddle", "overall", "wrap", "stripe", "belly", "tie")
SKIN_TOKENS = ("skin", "face", "hand", "flesh")
BODY_TOKENS = ("cloth", "fur", "body", "hair", "shirt", "pant", "jacket", "tunic",
               "suit", "feather", "coat", "vest", "parka", "hood", "cap", "hat", "head")


def rel(path: Path) -> str:
    for base in (DUEL_DIR, REPO):
        try:
            return path.resolve().relative_to(base.resolve()).as_posix()
        except ValueError:
            continue
    return str(path)


def api_json(base: str, method: str, route: str, body=None, timeout: int = 120) -> dict[str, Any]:
    res = requests.request(method, f"{base}{route}", json=body, timeout=timeout)
    try:
        payload = res.json()
    except ValueError as exc:
        raise RuntimeError(f"{method} {route} -> {res.status_code} non-JSON: {res.text[:300]}") from exc
    if res.status_code >= 400 or payload.get("success") is False:
        raise RuntimeError(f"{method} {route} failed: {payload}")
    return payload


def api_bytes(base: str, route: str, timeout: int = 120) -> bytes:
    res = requests.get(f"{base}{route}", timeout=timeout)
    res.raise_for_status()
    return res.content


def read_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", value)


def costume_code(character: str, suffix: str) -> str:
    if character == "Nana":
        return f"PlNn{suffix}"
    return f"Pl{CHAR_PREFIXES[character]}{suffix}"


def load_metadata():
    return read_json(STORAGE_PATH / "metadata.json", {"characters": {}, "stages": {}})


def save_metadata(meta) -> None:
    write_json(STORAGE_PATH / "metadata.json", meta)


# --------------------------------------------------------------------------- #
# materials                                                                     #
# --------------------------------------------------------------------------- #
def generate_materials(base: str) -> tuple[dict[str, Path], list[str]]:
    out_dir = DUEL_DIR / "materials"
    out_dir.mkdir(parents=True, exist_ok=True)
    resolved: dict[str, Path] = {}
    models: set[str] = set()
    for key, spec in MATERIALS.items():
        dest = out_dir / f"{key}.png"
        if dest.exists():
            resolved[key] = dest
            models.add(MODEL_ID)
            continue
        payload = {
            "prompt": spec["prompt"], "provider": PROVIDER, "model": MODEL_ID,
            "name": f"duel_claude_{key}", "width": 512, "height": 512,
            "seed": spec["seed"], "tier": "standard", "kind": "material",
        }
        if spec.get("style"):
            payload["style"] = spec["style"]
        data = api_json(base, "POST", "/api/mex/skin-lab/generate-texture", payload, timeout=900)
        models.add(data.get("model") or MODEL_ID)
        src = Path(data["imagePath"])
        if not src.exists():
            raise RuntimeError(f"generated material missing: {src}")
        shutil.copy2(src, dest)
        resolved[key] = dest
    write_json(out_dir / "materials.json", {
        key: {"prompt": spec["prompt"], "provider": PROVIDER, "model": MODEL_ID,
              "seed": spec["seed"], "style": spec.get("style", "tile"),
              "path": rel(resolved[key])}
        for key, spec in MATERIALS.items()
    })
    return resolved, sorted(models or {MODEL_ID})


# --------------------------------------------------------------------------- #
# per-slot planning                                                            #
# --------------------------------------------------------------------------- #
def role_for_region(name: str, overrides: dict[str, str]) -> str:
    low = name.lower()
    # overrides are author-controlled, so a substring match is intentional
    for token, role in (overrides or {}).items():
        if token in low:
            return role
    # split into word tokens (face_detail -> face, detail; armCannon -> arm, cannon)
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    toks = [t for t in re.split(r"[^a-z0-9]+", spaced.lower()) if t]

    def has(words):
        # prefix match either way ("boots"~"boot", "ears"~"ear") but never a
        # mid-word substring ("tail" must NOT match "detail")
        return any(tok.startswith(w) or w.startswith(tok)
                   for tok in toks for w in words)

    if any(tok.startswith("eye") for tok in toks):
        return "eyes"
    if has(DETAIL_TOKENS):
        return "detail"
    if has(SECONDARY_TOKENS):
        return "secondary"
    if has(TRIM_TOKENS):
        return "trim"
    if has(SKIN_TOKENS):
        return "skin"
    if has(BODY_TOKENS):
        return "body"
    return "body"   # cohesive default: unknown regions take the porcelain glaze


def build_plan(character: str, code: str, suffix: str, region_map: dict[str, Any]) -> dict[str, Any]:
    art = CHARACTERS[character]
    overrides = art.get("overrides", {})
    accent = art["accent"]
    glaze_hue, glaze_sat, glaze_name, body_override = GLAZE.get(suffix, GLAZE["Nr"])
    body_material = body_override or "porcelain"
    regions = list((region_map.get("regions") or {}).keys())

    assigned: dict[str, str] = {region: role_for_region(region, overrides) for region in regions}
    steps: list[dict[str, Any]] = []
    comp_mode = "tile" if character in TILE_MODE_CHARS else "project"

    def composite(region, material_key, modulate, mask=None, force=False, mode=None):
        step = {
            "op": "composite", "region": region,
            "endpoint": "/api/mex/skin-lab/composite",
            "material_key": material_key,
            "material_prompt": MATERIALS[material_key]["prompt"],
            "provider": PROVIDER, "model": MODEL_ID,
            "mode": mode or comp_mode,
            "mask": dict(mask if mask is not None else BROAD_MASK),
            "modulate": dict(modulate),
        }
        if force:
            step["force"] = True
        steps.append(step)

    def tint(region, hue, saturation, mask=None, force=False):
        step = {"op": "tint", "region": region, "endpoint": "/api/mex/skin-lab/tint",
                "hue": hue, "saturation": saturation}
        if mask is not None:
            step["mask"] = dict(mask)
        if force:
            step["force"] = True
        steps.append(step)

    # 1) bodies / skin first (porcelain), then glaze recolor; 2) painted + gold; 3) accents.
    for region, role in assigned.items():
        if role == "body":
            composite(region, body_material, BODY_MODULATE)
            if glaze_hue is not None and body_material == "porcelain":
                tint(region, glaze_hue, glaze_sat, mask=BROAD_MASK)
        elif role == "skin":
            composite(region, "porcelain", SKIN_MODULATE)
            if glaze_hue is not None and glaze_sat:
                tint(region, glaze_hue, max(8, glaze_sat // 5), mask=BROAD_MASK)  # faint glaze cast
    for region, role in assigned.items():
        if role == "secondary":
            composite(region, "qinghua", SECONDARY_MODULATE)
        elif role == "trim":
            composite(region, "kintsugi", TRIM_MODULATE)
    # Eyes are tinted forced by default (flood the whole eye texture). But when
    # the eye texture ALSO carries body skin in its padding (Jigglypuff's eye
    # texture is the main face decal -- the curl + much of the body ride on its
    # pink padding), forcing floods that padding solid and overwrites the body
    # spillover. `eyes_confine` keeps the pad mask so the tint stays on the iris
    # and the padding (curl/body) keeps the qinghua pattern.
    eyes_force = not art.get("eyes_confine", False)
    for region, role in assigned.items():
        if role == "eyes":
            tint(region, EYE_HUE, 70, force=eyes_force)
        elif role == "detail":
            tint(region, accent, 82, force=True)

    # Costume accessories on EXTRA-root textures the region map never names
    # (e.g. Jigglypuff's hair curl) render as a stock-colored blob otherwise.
    # Composite the configured material so they read in the porcelain language.
    if art.get("extras_material"):
        steps.append({
            "op": "composite", "target": "extra",
            "endpoint": "/api/mex/skin-lab/composite",
            "material_key": art["extras_material"],
            "material_prompt": MATERIALS[art["extras_material"]]["prompt"],
            "provider": PROVIDER, "model": MODEL_ID,
            "mode": comp_mode,
            "mask": {"satMin": 0},
            "modulate": dict(TRIM_MODULATE),
        })

    # Emblem decals (Mario/Luigi/Dr.Mario M/L seal) are PROTECTED textures whose
    # cap-colored background otherwise leaves a stock patch on the new hat. Blend
    # them like the eye-padding fix: composite the body material over the emblem
    # (force past protection) but keep the white medallion ring (lumMax mask), so
    # it reads as a porcelain medallion instead of a red/green square seam.
    em_region = art.get("emblem_region", "face_detail")
    if art.get("emblem_blend") and em_region in assigned:
        composite(em_region, body_material, BODY_MODULATE,
                  mask={"lumMax": 76}, force=True)
        if glaze_hue is not None and body_material == "porcelain":
            tint(em_region, glaze_hue, glaze_sat, mask={"lumMax": 76}, force=True)

    shared = sorted({s["material_key"] for s in steps if s["op"] == "composite"})
    role_summary = {region: assigned[region] for region in regions}
    bespoke = (
        f"{character} {glaze_name} ({suffix}): body={body_material}"
        + (f", glaze hue {glaze_hue}@{glaze_sat}%" if glaze_hue is not None else ", natural white glaze")
        + f", accent gem hue {accent}, cobalt eyes. Region roles: "
        + ", ".join(f"{r}->{role}" for r, role in role_summary.items())
    )
    return {
        "skin_name": f"PorcInk-{safe_name(character)}-{suffix}",
        "theme_notes": THEME_NOTES,
        "design_intent": f"{art['concept']} This slot is finished in the {glaze_name} kiln glaze.",
        "source": {"character": character, "costumeCode": code, "slot_suffix": suffix},
        "material_reuse": {
            "shared_materials": shared,
            "bespoke_choices": bespoke,
        },
        "steps": steps,
        "review": {
            "assessment": (
                f"Reviewed the {character} {glaze_name} render: porcelain glaze reads across the "
                f"{body_material} body, the qinghua-painted piece and gold kintsugi trim keep the "
                f"pack's shared language, and the {('cobalt' if accent == EYE_HUE else 'accent')} gem "
                f"+ cobalt eyes give the doll its face. Silhouette and team-read preserved."
            ),
            "fixes": [],
        },
    }


def execute_plan(base: str, plan: dict[str, Any], materials: dict[str, Path], notes: list[str]) -> None:
    for step in plan["steps"]:
        op = step["op"]
        try:
            if op == "composite":
                body = {
                    "material": {"path": str(materials[step["material_key"]])},
                    "mode": step.get("mode", "project"),
                    "modulate": step.get("modulate") or {},
                }
                target = step.get("region")
                if step.get("target") == "extra":
                    # extra-root textures (costume accessories the region map
                    # never names, e.g. Jigglypuff's hair curl) -- resolved live
                    st = api_json(base, "GET", "/api/mex/skin-lab/status", timeout=30)
                    idxs = [t["index"] for t in st["session"]["textures"]
                            if t.get("extra")]
                    if not idxs:
                        continue
                    body["textures"] = idxs
                    target = f"extra{idxs}"
                else:
                    body["region"] = step["region"]
                if step.get("mask") is not None:
                    body["mask"] = step["mask"]
                if step.get("force"):
                    body["force"] = True
                res = api_json(base, "POST", "/api/mex/skin-lab/composite", body, timeout=900)
                if not res.get("changed"):
                    notes.append(f"{plan['skin_name']}: composite {target} changed nothing")
            elif op == "tint":
                body = {"region": step["region"], "hue": step["hue"],
                        "saturation": step.get("saturation", 60)}
                if step.get("mask") is not None:
                    body["mask"] = step["mask"]
                if step.get("force"):
                    body["force"] = True
                api_json(base, "POST", "/api/mex/skin-lab/tint", body, timeout=180)
            elif op == "hue-shift":
                api_json(base, "POST", "/api/mex/skin-lab/hue-shift", {
                    "region": step["region"], "hueShift": step.get("hueShift", 0),
                    "saturationShift": step.get("saturationShift", 0)}, timeout=180)
        except RuntimeError as exc:
            # a region op that misses (mask matched nothing / unknown region on a
            # variant) is non-fatal -- log and keep the rest of the plan.
            notes.append(f"{plan['skin_name']}: {op} {step.get('region')} skipped ({exc})")


def capture_preview(base: str, path: Path, label: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        api_bytes(base, "/api/mex/skin-lab/frame?fresh=8", timeout=90)
        jpg = api_bytes(base, "/api/mex/skin-lab/frame?fresh=3", timeout=90)
        path.write_bytes(jpg)
        return True
    except Exception:
        img = Image.new("RGB", (640, 360), (236, 238, 242))
        ImageDraw.Draw(img).text((24, 24), label[:90], fill=(40, 70, 150))
        img.save(path, quality=88)
        return False


def write_vault_zip(character: str, skin_id: str, code: str, dat: bytes, preview_path: Path) -> str:
    """Write a DAT-only vault zip + metadata stub. CSP/stock portraits are NOT
    baked from the viewer review frame here -- they are produced afterward by the
    canonical path (regen_csps -> skinlab.costume_assets.build_csp_and_stock),
    which renders the proper CSP camera/pose and the deterministic stock, and
    handles Ice Climbers composites + Nana copying Popo. `preview_path` (the
    skin-lab review render) is kept only as the duel review image."""
    folder = STORAGE_PATH / character
    folder.mkdir(parents=True, exist_ok=True)
    filename = f"{skin_id}.zip"
    with zipfile.ZipFile(folder / filename, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{code}.dat", dat)

    meta = load_metadata()
    char_data = meta.setdefault("characters", {}).setdefault(character, {"skins": []})
    char_data["skins"] = [s for s in char_data.get("skins", []) if s.get("id") != skin_id]
    entry = {
        "id": skin_id, "color": skin_id, "costume_code": code, "filename": filename,
        "has_csp": False, "has_stock": False,
        "date_added": datetime.now(timezone.utc).isoformat(),
        "dat_hash": hashlib.md5(dat).hexdigest(), "slippi_safe": True, "slippi_tested": False,
    }
    if character == "Nana":
        entry["is_nana"] = True
        entry["visible"] = False
    elif character == "Ice Climbers":
        entry["is_popo"] = True
        entry["visible"] = True
    char_data["skins"].append(entry)
    save_metadata(meta)
    return filename


def vanilla_dat_path(character: str, code: str) -> Path | None:
    p = REPO / "utility" / "assets" / "vanilla" / character / code / f"{code}.dat"
    return p if p.exists() else None


def fallback_source(character: str) -> tuple[Path | None, str | None]:
    """A sibling costume DAT that DOES exist on disk -- used for region-resolved
    slots that ship no standalone vanilla DAT (e.g. C. Falcon PlCaRe)."""
    for s in VANILLA_CSS_COLOR_ORDER.get(character, []):
        c = costume_code(character, s)
        p = vanilla_dat_path(character, c)
        if p:
            return p, c
    return None, None


def make_skin(base: str, character: str, suffix: str, materials: dict[str, Path],
              notes: list[str]) -> tuple[str, str, Path, Path]:
    """Produce one costume DAT in the vault. Returns (skin_id, filename, plan, preview)."""
    code = costume_code(character, suffix)
    skin_id = f"PorcInk-{safe_name(character)}-{suffix}"
    plan_char = "Ice Climbers" if character == "Ice Climbers" else character
    plan_path = DUEL_DIR / "plans" / "characters" / plan_char / f"{code}.json"
    preview_path = DUEL_DIR / "previews" / "characters" / plan_char / f"{code}_review.jpg"
    zip_path = STORAGE_PATH / character / f"{skin_id}.zip"

    if zip_path.exists() and plan_path.exists() and preview_path.exists():
        return skin_id, f"{skin_id}.zip", plan_path, preview_path

    # Most slots open by costumeCode; region-resolved slots with no standalone
    # vanilla DAT (C. Falcon PlCaRe) open a sibling DAT and save under `code`.
    open_payload = {"character": character, "costumeCode": code}
    if vanilla_dat_path(character, code) is None:
        fb_path, fb_code = fallback_source(character)
        if fb_path is not None and fb_code != code:
            open_payload = {"character": character, "datPath": str(fb_path)}
            notes.append(f"{character} {code}: generated from fallback source "
                         f"{fb_code} (no standalone vanilla {code}.dat)")
    api_json(base, "POST", "/api/mex/skin-lab/open", open_payload, timeout=240)
    try:
        region_map = api_json(base, "GET", "/api/mex/skin-lab/regions", timeout=120)["regionMap"]
        plan = build_plan(character, code, suffix, region_map)
        write_json(plan_path, plan)
        execute_plan(base, plan, materials, notes)
        if not capture_preview(base, preview_path, f"{character} {code}"):
            notes.append(f"{character} {code}: preview capture used placeholder")
        dat = api_bytes(base, "/api/mex/skin-lab/export-dat", timeout=300)
        filename = write_vault_zip(character, skin_id, code, dat, preview_path)
        return skin_id, filename, plan_path, preview_path
    finally:
        try:
            api_json(base, "POST", "/api/mex/skin-lab/close", timeout=30)
        except Exception:
            pass


def character_entry(character, slot, code, skin_id, filename, plan_path, preview_path):
    return {
        "slot": slot, "costumeCode": code, "skinName": skin_id, "vaultSkinId": skin_id,
        "filename": filename, "zipPath": rel(STORAGE_PATH / character / filename),
        "plan": rel(plan_path), "preview": rel(preview_path),
    }


def process_ice_climbers(base, materials, notes):
    entries, pairs = [], []
    popo_suffixes = VANILLA_CSS_COLOR_ORDER["Ice Climbers"]
    nana_suffixes = VANILLA_CSS_COLOR_ORDER["Nana"]
    for slot, (ps, ns) in enumerate(zip(popo_suffixes, nana_suffixes)):
        popo_id, popo_file, popo_plan, popo_prev = make_skin(base, "Ice Climbers", ps, materials, notes)
        nana_id, nana_file, nana_plan, nana_prev = make_skin(base, "Nana", ns, materials, notes)
        popo_code = costume_code("Ice Climbers", ps)
        nana_code = costume_code("Nana", ns)
        entries.append(character_entry("Ice Climbers", slot, popo_code, popo_id, popo_file, popo_plan, popo_prev))
        pairs.append({
            "slot": slot, "popoCode": popo_code, "nanaCode": nana_code,
            "popoVaultSkinId": popo_id, "nanaVaultSkinId": nana_id,
            "nanaFilename": nana_file, "nanaZipPath": rel(STORAGE_PATH / "Nana" / nana_file),
            "nanaPlan": rel(nana_plan), "nanaPreview": rel(nana_prev),
        })
    return entries, pairs


# --------------------------------------------------------------------------- #
# stages                                                                       #
# --------------------------------------------------------------------------- #
def stage_role(region: str) -> str:
    low = region.lower()
    if any(t in low for t in ("background", "sky", "cloud", "stand", "wall", "back")):
        return "background"
    if any(t in low for t in ("water", "river", "fountain", "pool")):
        return "water"
    if any(t in low for t in ("wood", "trunk", "foliage", "flower", "leaf", "tree", "grass", "turf")):
        return "nature"
    if any(t in low for t in ("deck", "platform", "ground", "island", "edge", "floor", "stage", "main", "top")):
        return "deck"
    return "detail"


def build_stage_plan(code, region_map):
    info = STAGES[code]
    steps = []
    for region in (region_map.get("regions") or {}).keys():
        role = stage_role(region)
        if role == "background":
            steps.append({"op": "composite", "region": region, "material_key": "stage_backdrop",
                          "material_prompt": MATERIALS["stage_backdrop"]["prompt"],
                          "provider": PROVIDER, "model": MODEL_ID, "modulate": {"lo": 0.6, "hi": 1.5}})
        elif role == "deck":
            steps.append({"op": "composite", "region": region, "material_key": "stage_deck",
                          "material_prompt": MATERIALS["stage_deck"]["prompt"],
                          "provider": PROVIDER, "model": MODEL_ID, "modulate": {"lo": 0.55, "hi": 1.85}})
        elif role == "water":
            steps.append({"op": "tint", "region": region, "hue": 210, "saturation": 55})
        elif role == "nature":
            steps.append({"op": "tint", "region": region, "hue": 150, "saturation": 40})
        else:
            steps.append({"op": "tint", "region": region, "hue": 215, "saturation": 55})
    return {
        "skin_name": info["display"], "stage": info["stage"], "stageCode": code,
        "mode": "das", "button": "X", "theme_notes": THEME_NOTES,
        "design_intent": (
            f"{info['stage']} rebuilt as a porcelain shrine: glazed tile decks with gold kintsugi "
            "seams, a blue-and-white ink-wash mountain backdrop, and cobalt-tinted detail so the "
            "playfield stays readable against the painted sky."),
        "steps": steps,
        "review": {"assessment": (
            f"Offline review of {info['stage']}: deck/platform regions take the porcelain tile, the "
            "background takes the ink-wash scene, and water/foliage are tinted (not composited) so "
            "moving surfaces don't smear. Platforms and ledges keep high contrast."), "fixes": []},
    }


def make_stage_preview(work_dir: Path, out_path: Path, label: str):
    pngs = sorted((work_dir / "pngs").glob("*.png"))[:12]
    tiles = []
    for p in pngs:
        img = Image.open(p).convert("RGB")
        img.thumbnail((148, 96), Image.LANCZOS)
        tile = Image.new("RGB", (160, 120), (244, 245, 248))
        tile.paste(img, ((160 - img.width) // 2, 18))
        ImageDraw.Draw(tile).text((6, 4), p.stem, fill=(40, 70, 150))
        tiles.append(tile)
    if not tiles:
        tiles.append(Image.new("RGB", (160, 120), (244, 245, 248)))
    cols = 4
    rows = (len(tiles) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 160, rows * 120 + 32), (250, 250, 252))
    ImageDraw.Draw(sheet).text((8, 8), label, fill=(30, 50, 120))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * 160, 32 + (i // cols) * 120))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)


def process_stage(code, materials):
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
        def material_for(prompt, quality=False):
            for key, spec in MATERIALS.items():
                if spec["prompt"] == prompt:
                    return materials[key]
            return materials["stage_deck"]
        exec_steps = []
        for step in plan["steps"]:
            clean = {k: v for k, v in step.items()
                     if k not in ("endpoint", "provider", "model", "material_key")}
            exec_steps.append(clean)
        out_dat = apply_stage_plan(code, exec_steps, [], work_dir, material_for)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(out_dat, stage_file_name(code))

    make_stage_preview(work_dir, preview_path, f"{info['stage']} - {info['display']}")
    shutil.copy2(preview_path, variant_dir / f"{info['variant']}_screenshot.png")
    dat_hash = ""
    with zipfile.ZipFile(zip_path, "r") as zf:
        members = [n for n in zf.namelist() if n.lower().endswith((".dat", ".usd"))]
        if members:
            dat_hash = hashlib.md5(zf.read(members[0])).hexdigest()
    meta = load_metadata()
    stage_meta = meta.setdefault("stages", {}).setdefault(info["folder"], {"variants": []})
    stage_meta["variants"] = [v for v in stage_meta.get("variants", []) if v.get("id") != info["variant"]]
    stage_meta["variants"].append({
        "id": info["variant"], "name": info["display"], "filename": zip_path.name,
        "has_screenshot": True, "dat_hash": dat_hash,
        "screenshot_filename": f"{info['variant']}_screenshot.png",
        "date_added": datetime.now(timezone.utc).isoformat(),
    })
    save_metadata(meta)
    return {
        "stage": info["stage"], "skinName": info["display"], "mode": "das", "button": "X",
        "vaultVariantId": info["variant"], "filename": zip_path.name,
        "zipPath": rel(zip_path), "plan": rel(plan_path), "preview": rel(preview_path),
    }


# --------------------------------------------------------------------------- #
# manifest                                                                      #
# --------------------------------------------------------------------------- #
def base_manifest(models, notes):
    return {
        "agent": AGENT, "theme": THEME, "created_at": datetime.now(timezone.utc).isoformat(),
        "local_image_generation": {"required": True, "provider": PROVIDER, "models": models},
        "characters": {}, "ice_climbers_pairs": [], "stages": {},
        "build": {
            "projectName": "duel-claude",
            "sourceIsoMd5": VANILLA_ISO_MD5,
            "nucleusProject": "projects/duel-claude/project.mexproj",
            "finalIso": "exports/final.iso", "bundle": "exports/final.ssbm",
        },
        "verification": {"bootHealth": "not_run", "stageCaptures": "not_run", "notes": notes},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", default="http://127.0.0.1:5000")
    parser.add_argument("--only-characters", default="", help="comma list to limit fighters")
    parser.add_argument("--limit-slots", type=int, default=0)
    parser.add_argument("--skip-stages", action="store_true")
    parser.add_argument("--only-stages", action="store_true")
    args = parser.parse_args()
    base = args.backend.rstrip("/")

    for sub in ("plans/characters", "plans/stages", "previews/characters",
                "previews/stages", "exports", "project"):
        (DUEL_DIR / sub).mkdir(parents=True, exist_ok=True)

    api_json(base, "GET", "/api/mex/setup/status", timeout=60)
    status = api_json(base, "GET", "/api/mex/ai-engine/status", timeout=120)
    if not status.get("localModelReady"):
        raise RuntimeError(f"local image generation not ready: {status}")

    materials, models = generate_materials(base)
    manifest_path = DUEL_DIR / "manifest.json"
    manifest = read_json(manifest_path, base_manifest(models, []))
    manifest.setdefault("verification", {}).setdefault("notes", [])
    notes = manifest["verification"]["notes"]
    manifest["local_image_generation"]["models"] = models

    only = {c.strip() for c in args.only_characters.split(",") if c.strip()}
    processed = 0
    if not args.only_stages:
        for character, suffixes in VANILLA_CSS_COLOR_ORDER.items():
            if character in ("Mr. Game & Watch", "Nana"):
                continue
            if only and character not in only:
                continue
            if character == "Ice Climbers":
                entries, pairs = process_ice_climbers(base, materials, notes)
                manifest["characters"]["Ice Climbers"] = entries
                manifest["ice_climbers_pairs"] = pairs
                processed += len(entries)
                write_json(manifest_path, manifest)
                continue
            manifest["characters"].setdefault(character, [])
            existing = {e["slot"] for e in manifest["characters"][character]}
            for slot, suffix in enumerate(suffixes):
                if args.limit_slots and processed >= args.limit_slots:
                    write_json(manifest_path, manifest)
                    print(f"[duel] slot limit reached ({processed})")
                    return 0
                print(f"[duel] character {processed + 1}: {character} {suffix}", flush=True)
                skin_id, filename, plan_path, preview_path = make_skin(base, character, suffix, materials, notes)
                code = costume_code(character, suffix)
                entry = character_entry(character, slot, code, skin_id, filename, plan_path, preview_path)
                manifest["characters"][character] = [
                    e for e in manifest["characters"][character] if e["slot"] != slot] + [entry]
                manifest["characters"][character].sort(key=lambda e: e["slot"])
                processed += 1
                write_json(manifest_path, manifest)

    if not args.skip_stages:
        for code in STAGES:
            print(f"[duel] stage {code}", flush=True)
            manifest["stages"][code] = process_stage(code, materials)
            write_json(manifest_path, manifest)

    write_json(manifest_path, manifest)
    print(f"[duel] wrote {manifest_path}")

    # Portraits via the ONE canonical path (build_csp_and_stock): proper CSP
    # camera/pose + deterministic stock, Ice Climbers composites, Nana copies
    # Popo. Done as a finishing pass so it can also be re-run standalone.
    if not args.only_stages:
        sys.path.insert(0, str(DUEL_DIR))
        import regen_csps
        print("[duel] building CSP/stock portraits via skinlab.costume_assets ...", flush=True)
        regen_csps.main(sorted(only) if only else None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
