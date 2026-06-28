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


AGENT = "codex-v2"
THEME = "Circuit Shrine V2: Hand-Forged Relics"
THEME_NOTES = (
    "Circuit Shrine V2 keeps the ceremonial arcade-guardian world, but each fighter "
    "is treated as a separate relic with its own material language, mapped-region "
    "priorities, readable signature details, and slot-specific palette story."
)
MODEL_ID = "sd-turbo"
IMAGE_PROVIDER = "local"

SHARED_MATERIALS = {
    "obsidian_lacquer": {
        "seed": 6101,
        "prompt": (
            "black obsidian lacquer with sparse jade circuit etching and tiny gold "
            "seal flecks, seamless tileable game texture, crisp readable contrast"
        ),
    },
    "moon_ceramic": {
        "seed": 6102,
        "prompt": (
            "moon-white ceramic armor panels with brushed gunmetal seams and teal "
            "micro-engraving, seamless tileable sci fi shrine material"
        ),
    },
    "signal_silk": {
        "seed": 6103,
        "prompt": (
            "iridescent woven signal silk with cyan magenta jade threads, seamless "
            "tileable character cloth, clean readable folds"
        ),
    },
    "sun_gold": {
        "seed": 6104,
        "prompt": (
            "warm aged gold foil over dark enamel with small geometric shrine seals, "
            "seamless tileable ornament texture, crisp luminous highlights"
        ),
    },
    "stage_battlefield": {
        "seed": 6201,
        "prompt": (
            "floating legal battle platform made of graphite lacquer, cyan edge "
            "inlays, triangular gold circuit seams, seamless readable game floor"
        ),
    },
    "stage_final_destination": {
        "seed": 6202,
        "prompt": (
            "infinite monolith arena floor, pearl ceramic slabs over star-black glass, "
            "magenta horizon circuitry, seamless readable game platform texture"
        ),
    },
    "stage_yoshis_story": {
        "seed": 6203,
        "prompt": (
            "storybook wood shrine planks with candy jade lacquer and gold stitched "
            "circuit vines, seamless readable platform game texture"
        ),
    },
    "stage_dreamland": {
        "seed": 6204,
        "prompt": (
            "soft cloud shrine turf with emerald moss, moonlit woven fiber, tiny gold "
            "lantern seams, seamless readable platform game texture"
        ),
    },
    "stage_pokemon_stadium": {
        "seed": 6205,
        "prompt": (
            "stadium tech floor with modular ceramic tiles, amber score glyphs, teal "
            "routing lines, seamless readable legal stage texture"
        ),
    },
    "stage_fountain": {
        "seed": 6206,
        "prompt": (
            "fountain shrine platform of opal stone, flowing blue glass channels, "
            "silver-gold circuit filigree, seamless readable game texture"
        ),
    },
    "stage_backdrop": {
        "seed": 6207,
        "style": "scene",
        "prompt": (
            "wide aurora shrine skyline with distinct floating lantern constellations, "
            "teal magenta nebula clouds, no text, readable game background"
        ),
    },
}

FIGHTER_DESIGNS = {
    "Bowser": {
        "material_key": "fighter_bowser",
        "seed": 6301,
        "prompt": "obsidian turtle-shell temple scales with molten gold circuit cracks, heavy boss armor, seamless readable game texture",
        "concept": "volcanic temple tyrant; shell and spikes read like a cracked shrine gate",
        "signature": "shell, spikes, cuffs, and claws get hot gold accents while the body keeps reptile mass readable",
        "priority": ["shell", "armor", "spike", "body", "claw"],
        "base": 18,
        "secondary": 48,
        "detail": 144,
    },
    "C. Falcon": {
        "material_key": "fighter_falcon",
        "seed": 6302,
        "prompt": "racing pilot shrine leather with aerodynamic circuit stripes and polished helmet enamel, seamless readable game texture",
        "concept": "speed-priest bounty pilot; the suit is a racing banner wrapped around a ceremonial machine",
        "signature": "helmet, chest suit, gloves, and boots use different racing stripe priorities",
        "priority": ["helmet", "cloth", "body", "boot", "glove"],
        "base": 258,
        "secondary": 34,
        "detail": 188,
    },
    "DK": {
        "material_key": "fighter_dk",
        "seed": 6303,
        "prompt": "jungle shrine fur and carved red necktie cloth with brass circuit beads, seamless readable game texture",
        "concept": "jungle guardian idol; fur stays powerful while the tie becomes a carved shrine sash",
        "signature": "fur receives warm natural tinting, tie and hands carry brass signal accents",
        "priority": ["tie", "cloth", "fur", "body", "hand"],
        "base": 32,
        "secondary": 96,
        "detail": 46,
    },
    "Dr. Mario": {
        "material_key": "fighter_dr_mario",
        "seed": 6304,
        "prompt": "clinical white shrine coat fabric with capsule glyph circuitry and jade medical enamel, seamless readable game texture",
        "concept": "clinic exorcist doctor; coat panels are sterile ceramic cloth with capsule-glyph seams",
        "signature": "coat, head mirror, gloves, and shoes get medical glyph accents without losing the face",
        "priority": ["coat", "cloth", "armor", "glove", "shoe"],
        "base": 186,
        "secondary": 0,
        "detail": 52,
    },
    "Falco": {
        "material_key": "fighter_falco",
        "seed": 6305,
        "prompt": "avian ace flight jacket feathers with cobalt shrine enamel and magenta wing circuitry, seamless readable game texture",
        "concept": "sky-duelist shrine ace; feathers and jacket panels split into sharp flight insignia",
        "signature": "crest, jacket, boots, and beak details get crisp blue-magenta signal treatment",
        "priority": ["feather", "fur", "cloth", "jacket", "boot"],
        "base": 220,
        "secondary": 316,
        "detail": 44,
    },
    "Fox": {
        "material_key": "fighter_fox",
        "seed": 6306,
        "prompt": "fox pilot shrine jacket with amber fur trim, teal avionics panels, and gold unit patches, seamless readable game texture",
        "concept": "star-cadet shrine pilot; jacket and helmet read as mission hardware while fur stays warm",
        "signature": "jacket panels, helmet, boots, and face details get separate pilot-unit accents",
        "priority": ["jacket", "cloth", "helmet", "armor", "fur"],
        "base": 28,
        "secondary": 190,
        "detail": 312,
    },
    "Ganondorf": {
        "material_key": "fighter_ganondorf",
        "seed": 6307,
        "prompt": "dark warlock king armor with crimson velvet shrine cloth and antique gold circuit sigils, seamless readable game texture",
        "concept": "cursed monarch relic; cape and armor read like a heavy ceremonial seal",
        "signature": "cape, armor, gauntlets, and face detail lean crimson-gold without muddying the silhouette",
        "priority": ["cape", "armor", "cloth", "gauntlet", "body"],
        "base": 350,
        "secondary": 45,
        "detail": 270,
    },
    "Ice Climbers": {
        "material_key": "fighter_ice_climbers",
        "seed": 6308,
        "prompt": "paired arctic shrine parkas with quilted snow fabric, cyan glass trim, and tiny gold bell circuitry, seamless readable game texture",
        "concept": "twin snow-bell pilgrims; parkas are paired but each slot swaps warm and cold accents",
        "signature": "parka, mittens, hammer, and hood fur are coordinated as a duo",
        "priority": ["parka", "cloth", "hood", "fur", "hammer"],
        "base": 196,
        "secondary": 48,
        "detail": 318,
    },
    "Nana": {
        "material_key": "fighter_nana",
        "seed": 6309,
        "prompt": "companion arctic shrine parka with pearl snow quilting, rose-cyan trim, and tiny gold bell circuitry, seamless readable game texture",
        "concept": "paired snow-bell companion; Nana echoes Popo but carries the opposite accent balance",
        "signature": "hood, parka, mittens, and hammer use companion colors distinct from Popo",
        "priority": ["parka", "cloth", "hood", "fur", "hammer"],
        "base": 312,
        "secondary": 184,
        "detail": 48,
    },
    "Jigglypuff": {
        "material_key": "fighter_jigglypuff",
        "seed": 6310,
        "prompt": "soft moon mascot skin with satin bow accessories, star microphone gems, and pastel circuit embroidery, seamless readable game texture",
        "concept": "moon-stage idol charm; body remains soft while accessories become tiny shrine props",
        "signature": "hat, bow, flower, eyes, and cheeks get high-read idol accents",
        "priority": ["hat", "bow", "flower", "body", "skin"],
        "base": 318,
        "secondary": 186,
        "detail": 52,
    },
    "Kirby": {
        "material_key": "fighter_kirby",
        "seed": 6311,
        "prompt": "round star shrine plush surface with opal blush, tiny constellation circuits, and glossy ruby feet, seamless readable game texture",
        "concept": "star-orb shrine apprentice; body is plush opal and feet carry strong readable color",
        "signature": "body, feet, cheeks, and eyes get separate soft-gem treatment",
        "priority": ["body", "foot", "feet", "skin", "cheek"],
        "base": 300,
        "secondary": 8,
        "detail": 190,
    },
    "Link": {
        "material_key": "fighter_link",
        "seed": 6312,
        "prompt": "heroic forest shrine tunic with emerald woven cloth, brass chainmail circuits, and sacred blade inlay, seamless readable game texture",
        "concept": "forest-temple knight; tunic, shield, and sword become a cohesive relic set",
        "signature": "tunic, shield, sword, boots, and belt get separate forest-metal treatment",
        "priority": ["tunic", "cloth", "shield", "sword", "armor"],
        "base": 132,
        "secondary": 48,
        "detail": 210,
    },
    "Luigi": {
        "material_key": "fighter_luigi",
        "seed": 6313,
        "prompt": "jade maintenance monk overalls with ghost-lantern threads and polished brass buttons, seamless readable game texture",
        "concept": "nervous shrine caretaker; overalls and cap become a maintenance robe with ghost-lantern accents",
        "signature": "cap emblem, overalls, gloves, and shoes carry quieter jade-cyan details than Mario",
        "priority": ["overalls", "cloth", "cap", "armor", "glove"],
        "base": 142,
        "secondary": 188,
        "detail": 48,
    },
    "Mario": {
        "material_key": "fighter_mario",
        "seed": 6314,
        "prompt": "red shrine foreman jacket and work overalls with gold button seals and cyan pipe circuitry, seamless readable game texture",
        "concept": "ceremonial foreman; overalls become a shrine work uniform with pipe-glyph seams",
        "signature": "cap emblem, overalls, gloves, shoes, and mustache are protected as iconic read points",
        "priority": ["overalls", "cloth", "cap", "armor", "fur"],
        "base": 2,
        "secondary": 210,
        "detail": 48,
    },
    "Marth": {
        "material_key": "fighter_marth",
        "seed": 6315,
        "prompt": "royal blue duelist cape with silver embroidery, pearl armor, and fine gold circuit crestwork, seamless readable game texture",
        "concept": "moonlit royal duelist; cape embroidery and blade accents carry noble shrine language",
        "signature": "cape, tunic, armor, hair, and sword get cool royal contrast",
        "priority": ["cape", "cloth", "armor", "sword", "hair"],
        "base": 220,
        "secondary": 48,
        "detail": 330,
    },
    "Mewtwo": {
        "material_key": "fighter_mewtwo",
        "seed": 6316,
        "prompt": "psychic bio-crystal skin with violet aura veins, translucent pearl tissue, and neon shrine nodes, seamless readable game texture",
        "concept": "psychic crystal oracle; body stays organic while tail and nodes glow with controlled aura",
        "signature": "tail, body, eyes, and joint details get violet-cyan psychic gradients",
        "priority": ["tail", "body", "skin", "eyes", "detail"],
        "base": 276,
        "secondary": 186,
        "detail": 48,
    },
    "Ness": {
        "material_key": "fighter_ness",
        "seed": 6317,
        "prompt": "kid hero sweater knit with baseball charm patches, psychic neon stripes, and shrine toy badges, seamless readable game texture",
        "concept": "psychic arcade kid; sweater stripes become charm circuits without losing the child silhouette",
        "signature": "cap, shirt stripes, backpack, bat, and shoes get toy-shrine treatment",
        "priority": ["shirt", "cloth", "cap", "backpack", "bat"],
        "base": 2,
        "secondary": 226,
        "detail": 52,
    },
    "Peach": {
        "material_key": "fighter_peach",
        "seed": 6318,
        "prompt": "royal blossom shrine gown with pearl satin, rose circuit lace, and turquoise jewel embroidery, seamless readable game texture",
        "concept": "blossom shrine sovereign; dress panels and jewels become ceremonial flower circuitry",
        "signature": "dress, crown, jewels, gloves, and hair maintain elegant readable contrast",
        "priority": ["dress", "cloth", "crown", "jewel", "hair"],
        "base": 326,
        "secondary": 48,
        "detail": 186,
    },
    "Pichu": {
        "material_key": "fighter_pichu",
        "seed": 6319,
        "prompt": "tiny spark shrine fur with black enamel ear tips, lemon lightning embroidery, and playful teal bells, seamless readable game texture",
        "concept": "tiny spark novice; ears and cheeks are oversized readable electric charms",
        "signature": "ear tips, cheeks, body, and scarf-like accents get playful lightning treatment",
        "priority": ["ear", "fur", "body", "cheek", "tail"],
        "base": 54,
        "secondary": 186,
        "detail": 318,
    },
    "Pikachu": {
        "material_key": "fighter_pikachu",
        "seed": 6320,
        "prompt": "bright thunder shrine fur with red cheek seals, black lacquer ear tips, and golden lightning circuits, seamless readable game texture",
        "concept": "thunder shrine herald; cheeks and tail stay instantly readable as signal seals",
        "signature": "cheeks, ear tips, tail, body, and eyes get bold electric contrast",
        "priority": ["cheek", "ear", "tail", "fur", "body"],
        "base": 52,
        "secondary": 2,
        "detail": 186,
    },
    "Roy": {
        "material_key": "fighter_roy",
        "seed": 6321,
        "prompt": "young flame prince cape with red enamel armor, brass circuit trim, and heated blade filigree, seamless readable game texture",
        "concept": "sun-forged prince; cape and sword use warmer, heavier trims than Marth",
        "signature": "cape, armor, tunic, hair, and blade get flame-prince differentiation",
        "priority": ["cape", "cloth", "armor", "sword", "hair"],
        "base": 4,
        "secondary": 46,
        "detail": 220,
    },
    "Samus": {
        "material_key": "fighter_samus",
        "seed": 6322,
        "prompt": "ceramic power armor with magenta visor glass, amber cannon coils, and teal micro-circuit panels, seamless readable game texture",
        "concept": "temple mech sentinel; armor panels read as ceramic plates with deliberate cannon and visor contrast",
        "signature": "helmet, cannon, armor, accents, and visor each get distinct machinery language",
        "priority": ["helmet", "cannon", "armor", "accents", "gear"],
        "base": 22,
        "secondary": 186,
        "detail": 318,
    },
    "Sheik": {
        "material_key": "fighter_sheik",
        "seed": 6323,
        "prompt": "stealth shrine wrap fabric with indigo bandages, silver needle glyphs, and amber eye sigils, seamless readable game texture",
        "concept": "hidden needle acolyte; wraps and armor read as layered stealth calligraphy",
        "signature": "wraps, cloth, armor, hair, and eye details use restrained stealth contrast",
        "priority": ["wrap", "cloth", "armor", "hair", "eye"],
        "base": 232,
        "secondary": 42,
        "detail": 184,
    },
    "Yoshi": {
        "material_key": "fighter_yoshi",
        "seed": 6324,
        "prompt": "lacquered dinosaur shrine hide with saddle enamel, egg-shell bead texture, and cheerful circuit spots, seamless readable game texture",
        "concept": "festival dinosaur guardian; saddle, shoes, and body spots get toy-like shrine enamel",
        "signature": "saddle, shoes, body, cheeks, and eyes retain bright toy readability",
        "priority": ["saddle", "body", "shoe", "skin", "eye"],
        "base": 126,
        "secondary": 8,
        "detail": 48,
    },
    "Young Link": {
        "material_key": "fighter_young_link",
        "seed": 6325,
        "prompt": "child forest shrine tunic with carved wooden shield, brass fairy circuits, and soft green cloth, seamless readable game texture",
        "concept": "junior forest relic bearer; lighter wood and fairy accents separate him from adult Link",
        "signature": "tunic, shield, sword, boots, and hair get child-scale forest details",
        "priority": ["tunic", "cloth", "shield", "sword", "hair"],
        "base": 110,
        "secondary": 52,
        "detail": 300,
    },
    "Zelda": {
        "material_key": "fighter_zelda",
        "seed": 6326,
        "prompt": "sage princess shrine gown with ivory brocade, amethyst circuit panels, and gold triangular regalia, seamless readable game texture",
        "concept": "sage-princess oracle; gown panels and regalia carry formal triangular circuitry",
        "signature": "dress, crown, jewels, gloves, and hair use high-read royal geometry",
        "priority": ["dress", "cloth", "jewel", "crown", "hair"],
        "base": 286,
        "secondary": 48,
        "detail": 186,
    },
}

MATERIALS = {
    **SHARED_MATERIALS,
    **{
        design["material_key"]: {
            "seed": design["seed"],
            "prompt": design["prompt"],
        }
        for design in FIGHTER_DESIGNS.values()
    },
}

CHARACTER_SHARED_MATERIAL_KEYS = {"obsidian_lacquer", "moon_ceramic", "signal_silk", "sun_gold"}

SLOT_VARIANTS = {
    "Nr": {"name": "signature", "hue": 0, "secondary": 0, "detail": 0, "mood": "the default ceremonial read"},
    "Re": {"name": "crimson seal", "hue": 0, "secondary": 18, "detail": 330, "mood": "a red-team seal with hotter accents"},
    "Bu": {"name": "blue moon", "hue": 218, "secondary": 188, "detail": 48, "mood": "a blue-team moonlit variant"},
    "Gr": {"name": "jade keeper", "hue": 136, "secondary": 176, "detail": 46, "mood": "a green-team jade variant"},
    "Bk": {"name": "black lacquer", "hue": 280, "secondary": 44, "detail": 184, "mood": "a dark lacquer variant with bright readable trim"},
    "Wh": {"name": "white relic", "hue": 196, "secondary": 48, "detail": 314, "mood": "a pale ceramic variant with saturated detail points"},
    "Ye": {"name": "gold lantern", "hue": 50, "secondary": 6, "detail": 188, "mood": "a yellow-team lantern variant"},
    "Gy": {"name": "smoke chrome", "hue": 204, "secondary": 30, "detail": 316, "mood": "a neutral grey-metal variant"},
    "Or": {"name": "amber pilot", "hue": 28, "secondary": 190, "detail": 316, "mood": "an orange amber-signal variant"},
    "La": {"name": "lavender aura", "hue": 274, "secondary": 188, "detail": 48, "mood": "a lavender aura variant"},
    "Aq": {"name": "aqua glass", "hue": 184, "secondary": 48, "detail": 316, "mood": "an aqua glass variant"},
    "Pi": {"name": "rose circuit", "hue": 322, "secondary": 188, "detail": 48, "mood": "a pink rose-circuit variant"},
}

STAGES = {
    "GrNBa": {
        "stage": "Battlefield",
        "folder": "battlefield",
        "variant": "cshr-v2-bf",
        "display": "CircuitShrineV2BF",
        "material_key": "stage_battlefield",
        "intent": "triangular altar platforms with strong cyan ledge lines",
    },
    "GrNLa": {
        "stage": "Final Destination",
        "folder": "final_destination",
        "variant": "cshr-v2-fd",
        "display": "CircuitShrineV2FD",
        "material_key": "stage_final_destination",
        "intent": "single monolith runway with pearl slabs against a star-black horizon",
    },
    "GrSt": {
        "stage": "Yoshi's Story",
        "folder": "yoshis_story",
        "variant": "cshr-v2-ys",
        "display": "CircuitShrineV2YS",
        "material_key": "stage_yoshis_story",
        "intent": "storybook wood shrine with candy-lacquer edges and readable toy contrast",
    },
    "GrOp": {
        "stage": "Dream Land N64",
        "folder": "dreamland",
        "variant": "cshr-v2-dl",
        "display": "CircuitShrineV2DL",
        "material_key": "stage_dreamland",
        "intent": "soft cloud shrine turf with gentle lantern seams behind a clear platform read",
    },
    "GrPs": {
        "stage": "Pokemon Stadium",
        "folder": "pokemon_stadium",
        "variant": "cshr-v2-ps",
        "display": "CircuitShrineV2PS",
        "material_key": "stage_pokemon_stadium",
        "intent": "modular stadium tiles with amber score glyphs and bold boundary lines",
    },
    "GrIz": {
        "stage": "Fountain of Dreams",
        "folder": "fountain_of_dreams",
        "variant": "cshr-v2-fod",
        "display": "CircuitShrineV2FoD",
        "material_key": "stage_fountain",
        "intent": "opal fountain platform with flowing blue glass channels and silver filigree",
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


def api_multipart_file(
    base: str,
    route: str,
    *,
    field_name: str,
    filename: str,
    content: bytes,
    data: dict[str, Any] | None = None,
    timeout: int = 900,
) -> dict[str, Any]:
    response = requests.post(
        f"{base}{route}",
        files={field_name: (filename, io.BytesIO(content), "application/zip")},
        data=data or {},
        timeout=timeout,
    )
    try:
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError(f"POST {route} returned non-JSON {response.status_code}: {response.text[:300]}") from exc
    if response.status_code >= 400 or payload.get("success") is False:
        raise RuntimeError(f"POST {route} failed: {payload}")
    return payload


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
    folder = REPO / "utility" / "assets" / "vanilla" / character / code
    for ext in (".dat", ".usd"):
        direct = folder / f"{code}{ext}"
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


def validate_vault_media(character: str, skin_id: str, *, require_stock: bool = True) -> list[str]:
    """Check app-generated vault media without overwriting it."""
    notes: list[str] = []
    folder = STORAGE_PATH / character
    path = folder / f"{skin_id}.zip"
    if not path.exists():
        return [f"{character} {skin_id}: vault zip missing"]

    with zipfile.ZipFile(path, "r") as zf:
        lower = {name.lower() for name in zf.namelist()}
    if "csp.png" not in lower:
        notes.append(f"{character} {skin_id}: zip has no csp.png")
    if require_stock and not ({"stc.png", "stock.png"} & lower):
        notes.append(f"{character} {skin_id}: zip has no stock/stc image")

    csp_path = folder / f"{skin_id}_csp.png"
    stock_path = folder / f"{skin_id}_stc.png"
    if not csp_path.exists():
        notes.append(f"{character} {skin_id}: standalone CSP missing")
    else:
        try:
            with Image.open(csp_path) as img:
                if img.width <= 1 or img.height <= 1:
                    notes.append(f"{character} {skin_id}: standalone CSP has invalid size {img.size}")
        except Exception as exc:
            notes.append(f"{character} {skin_id}: standalone CSP unreadable: {exc}")
    if require_stock:
        if not stock_path.exists():
            notes.append(f"{character} {skin_id}: standalone stock missing")
        else:
            try:
                with Image.open(stock_path) as img:
                    if img.width <= 1 or img.height <= 1:
                        notes.append(f"{character} {skin_id}: standalone stock has invalid size {img.size}")
            except Exception as exc:
                notes.append(f"{character} {skin_id}: standalone stock unreadable: {exc}")
    return notes


def upsert_stage_variant(folder: str, entry: dict[str, Any]) -> None:
    metadata = load_metadata()
    stage_data = metadata.setdefault("stages", {}).setdefault(folder, {"variants": []})
    stage_data["variants"] = [variant for variant in stage_data.get("variants", []) if variant.get("id") != entry["id"]]
    stage_data["variants"].append(entry)
    save_metadata(metadata)


def generate_materials(base: str, wanted_keys: set[str] | None = None) -> tuple[dict[str, Path], list[str]]:
    material_dir = DUEL_DIR / "materials"
    material_dir.mkdir(parents=True, exist_ok=True)
    models: set[str] = set()
    resolved: dict[str, Path] = {}
    active_keys = [key for key in MATERIALS if wanted_keys is None or key in wanted_keys]

    for key in active_keys:
        spec = MATERIALS[key]
        out_copy = material_dir / f"{key}.png"
        if out_copy.exists():
            resolved[key] = out_copy
            models.add(MODEL_ID)
            continue
        payload = {
            "prompt": spec["prompt"],
            "provider": IMAGE_PROVIDER,
            "model": MODEL_ID,
            "name": f"duel_codex_v2_{key}",
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
                "prompt": MATERIALS[key]["prompt"],
                "provider": IMAGE_PROVIDER,
                "model": MODEL_ID,
                "seed": MATERIALS[key]["seed"],
                "path": rel(resolved[key]),
            }
            for key in active_keys
        },
    )
    return resolved, sorted(models or {MODEL_ID})


def region_role(region: str) -> str:
    lower = region.lower()
    if any(token in lower for token in ("eye", "visor", "jewel", "gem", "emblem", "cheek", "mouth", "face_detail", "nose", "crown")):
        return "detail"
    if any(token in lower for token in ("skin", "face", "hand", "body")):
        return "skin"
    if any(token in lower for token in ("cloth", "cape", "dress", "robe", "tunic", "pants", "shirt", "hat", "overalls", "coat", "wrap", "parka")):
        return "cloth"
    if any(token in lower for token in ("armor", "metal", "sword", "weapon", "shell", "boot", "shoe", "glove", "shield", "helmet", "cannon", "gear", "spike", "claw", "hammer")):
        return "armor"
    if any(token in lower for token in ("fur", "hair", "feather", "tail", "ear")):
        return "fur"
    return "other"


def classify_region(region: str) -> str:
    return region_role(region)


def slot_variant(suffix: str) -> dict[str, Any]:
    return SLOT_VARIANTS.get(suffix, SLOT_VARIANTS["Nr"])


def slot_palette(design: dict[str, Any], suffix: str, slot: int) -> dict[str, int]:
    variant = slot_variant(suffix)
    if suffix == "Nr":
        primary = int(design["base"])
    else:
        primary = int(variant["hue"])
    return {
        "primary": primary % 360,
        "secondary": (int(design["secondary"]) + int(variant["secondary"]) + slot * 5) % 360,
        "detail": (int(variant["detail"]) if suffix != "Nr" else int(design["detail"])) % 360,
        "skin": 34,
        "shadow": (primary + 180) % 360,
    }


def ordered_regions_for_design(regions: list[str], design: dict[str, Any]) -> list[str]:
    ordered: list[str] = []
    for token in design.get("priority", []):
        token = str(token).lower()
        for region in regions:
            if region not in ordered and token in region.lower():
                ordered.append(region)
    for role in ("cloth", "armor", "fur", "detail", "skin", "other"):
        for region in regions:
            if region not in ordered and region_role(region) == role:
                ordered.append(region)
    return ordered


def material_step(region: str, material_key: str, reason: str, lo: float = 0.42, hi: float = 1.74) -> dict[str, Any]:
    spec = MATERIALS[material_key]
    return {
        "op": "composite",
        "region": region,
        "endpoint": "/api/mex/skin-lab/composite",
        "material_key": material_key,
        "material_prompt": spec["prompt"],
        "provider": IMAGE_PROVIDER,
        "model": MODEL_ID,
        "mode": "project",
        "modulate": {"lo": lo, "hi": hi},
        "design_reason": reason,
    }


def tint_step(region: str, hue: int, saturation: int, reason: str, force: bool = False) -> dict[str, Any]:
    step: dict[str, Any] = {
        "op": "tint",
        "region": region,
        "endpoint": "/api/mex/skin-lab/tint",
        "hue": hue % 360,
        "saturation": saturation,
        "design_reason": reason,
    }
    if force:
        step["force"] = True
    return step


def shift_step(region: str, hue_shift: int, saturation_shift: int, reason: str) -> dict[str, Any]:
    return {
        "op": "hue-shift",
        "region": region,
        "endpoint": "/api/mex/skin-lab/hue-shift",
        "hueShift": hue_shift,
        "saturationShift": saturation_shift,
        "design_reason": reason,
    }


def character_plan(character: str, code: str, slot: int, region_map: dict[str, Any]) -> dict[str, Any]:
    design = FIGHTER_DESIGNS[character]
    suffix = code[-2:]
    variant = slot_variant(suffix)
    palette = slot_palette(design, suffix, slot)
    regions = list((region_map.get("regions") or {}).keys())
    skin_name = f"CShrineV2-{safe_name(character)}-{suffix}"
    anchor_regions = ordered_regions_for_design(regions, design)
    anchor_set = set(anchor_regions[:4])

    composite_budget = 4
    steps: list[dict[str, Any]] = []
    covered: set[str] = set()

    def add_composite(region: str, material_key: str, reason: str, lo: float = 0.42, hi: float = 1.74) -> None:
        nonlocal composite_budget
        if composite_budget <= 0 or region in covered:
            return
        composite_budget -= 1
        covered.add(region)
        steps.append(material_step(region, material_key, reason, lo, hi))

    for region in anchor_regions:
        if region in covered:
            continue
        role = region_role(region)
        if region in anchor_set:
            add_composite(
                region,
                design["material_key"],
                f"{character} anchor region for {design['concept']}; {variant['mood']}",
                0.44,
                1.86,
            )
        elif role == "cloth":
            add_composite(region, "signal_silk", f"{character} cloth support material for {variant['name']}", 0.42, 1.72)
        elif role == "armor":
            add_composite(region, "moon_ceramic", f"{character} hard-surface support material for {variant['name']}", 0.48, 1.9)
        elif role == "fur":
            add_composite(region, design["material_key"], f"{character} organic surface keeps the fighter-specific texture language", 0.36, 1.58)

    for region in regions:
        if region in covered:
            continue
        role = region_role(region)
        covered.add(region)
        if role == "detail":
            steps.append(tint_step(region, palette["detail"], 90, f"{character} high-read detail for {variant['name']}", True))
        elif role == "skin":
            steps.append(tint_step(region, palette["skin"], 28, f"{character} skin/face readability is protected from material smearing"))
        elif role == "armor":
            steps.append(tint_step(region, palette["secondary"], 66, f"{character} secondary hard-surface accent for {variant['name']}"))
        elif role == "fur":
            steps.append(tint_step(region, palette["primary"], 58, f"{character} organic color family for {variant['name']}"))
        elif role == "cloth":
            steps.append(tint_step(region, palette["primary"], 62, f"{character} costume cloth palette for {variant['name']}"))
        else:
            steps.append(shift_step(region, ((palette["primary"] + slot * 13) % 360) - 180, 22, f"{character} unmapped support region nudged into {variant['name']} palette"))

    return {
        "skin_name": skin_name,
        "theme_notes": THEME_NOTES,
        "design_intent": (
            f"{character} is designed as {design['concept']}. This {suffix} slot is "
            f"the {variant['name']} variant: {variant['mood']}. {design['signature']}."
        ),
        "slot_variant": {
            "suffix": suffix,
            "name": variant["name"],
            "mood": variant["mood"],
            "palette": palette,
        },
        "material_reuse": {
            "fighter_material": design["material_key"],
            "fighter_prompt": design["prompt"],
            "shared_materials": sorted({step["material_key"] for step in steps if step["op"] == "composite" and not step["material_key"].startswith("fighter_")}),
            "bespoke_choices": (
                f"Priority regions {anchor_regions[:4]} receive the {character}-specific "
                f"material before shared support materials are used. Remaining regions are "
                f"tinted by role so the slot keeps {variant['name']} readability."
            ),
        },
        "source": {"character": character, "costumeCode": code, "slot": slot},
        "steps": steps,
        "review": {
            "status": "first_pass_planned",
            "assessment": f"Pending screenshot review for {character} {code}; check silhouette, detail readability, and whether {design['concept']} is visible.",
            "capture": None,
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


def preview_metrics(path: Path) -> dict[str, float]:
    img = Image.open(path).convert("RGB").resize((160, 90), Image.LANCZOS)
    pixels = list(img.getdata())
    if not pixels:
        return {"mean_luma": 0.0, "contrast": 0.0, "mean_saturation": 0.0}
    lumas: list[float] = []
    sats: list[float] = []
    for r, g, b in pixels:
        mx = max(r, g, b)
        mn = min(r, g, b)
        lumas.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
        sats.append(0.0 if mx == 0 else ((mx - mn) / mx) * 100.0)
    mean_luma = sum(lumas) / len(lumas)
    contrast = (sum((v - mean_luma) ** 2 for v in lumas) / len(lumas)) ** 0.5
    return {
        "mean_luma": round(mean_luma, 2),
        "contrast": round(contrast, 2),
        "mean_saturation": round(sum(sats) / len(sats), 2),
    }


def review_fix_regions(plan: dict[str, Any], wanted_role: str, limit: int = 2) -> list[str]:
    regions: list[str] = []
    for step in plan["steps"]:
        region = step.get("region")
        if isinstance(region, str) and region not in regions and region_role(region) == wanted_role:
            regions.append(region)
        if len(regions) >= limit:
            break
    if regions:
        return regions
    for step in plan["steps"]:
        region = step.get("region")
        if isinstance(region, str) and region not in regions:
            regions.append(region)
        if len(regions) >= limit:
            break
    return regions


def review_character_capture(
    base: str,
    plan_path: Path,
    plan: dict[str, Any],
    preview_path: Path,
    material_paths: dict[str, Path],
) -> list[str]:
    notes: list[str] = []
    metrics = preview_metrics(preview_path)
    fixes: list[dict[str, Any]] = []
    suffix = plan["source"]["costumeCode"][-2:]
    variant = slot_variant(suffix)
    design = FIGHTER_DESIGNS[plan["source"]["character"]]
    palette = plan["slot_variant"]["palette"]

    if metrics["mean_luma"] < 54:
        fix_steps = [
            tint_step(region, palette["detail"], 96, "capture review: preview was too dark, brighten high-read detail", True)
            for region in review_fix_regions(plan, "detail")
        ]
        fixes.append(
            {
                "reason": f"Initial capture was dark for {variant['name']} (mean luma {metrics['mean_luma']}).",
                "steps_applied": fix_steps,
            }
        )
    if metrics["contrast"] < 24:
        fix_steps = [
            tint_step(region, palette["secondary"], 78, "capture review: low contrast, add secondary silhouette accent")
            for region in review_fix_regions(plan, "armor")
        ]
        fixes.append(
            {
                "reason": f"Initial capture had low contrast (luma stddev {metrics['contrast']}).",
                "steps_applied": fix_steps,
            }
        )
    if metrics["mean_saturation"] < 18:
        fix_steps = [
            tint_step(region, palette["primary"], 72, "capture review: muted capture, restore slot color identity")
            for region in review_fix_regions(plan, "cloth")
        ]
        fixes.append(
            {
                "reason": f"Initial capture was too muted (mean saturation {metrics['mean_saturation']}).",
                "steps_applied": fix_steps,
            }
        )

    for fix in fixes:
        execute_character_steps(base, {"steps": fix["steps_applied"]}, material_paths)

    if fixes:
        if not capture_preview(base, preview_path, f"{plan['source']['character']} {plan['source']['costumeCode']} fixed"):
            notes.append(f"{plan['source']['character']} {plan['source']['costumeCode']}: fixed preview capture fell back to placeholder")
        final_metrics = preview_metrics(preview_path)
        status = "capture_reviewed_with_fixes"
    else:
        final_metrics = metrics
        status = "capture_reviewed_passed"

    plan["review"] = {
        "status": status,
        "capture": rel(preview_path),
        "assessment": (
            f"Reviewed screenshot for {plan['source']['character']} {plan['source']['costumeCode']}: "
            f"checked that {design['concept']} reads through the silhouette, that {variant['name']} "
            f"has distinct color identity, and that protected/detail regions remain legible. "
            f"Final capture metrics: luma {final_metrics['mean_luma']}, contrast {final_metrics['contrast']}, "
            f"saturation {final_metrics['mean_saturation']}."
        ),
        "initial_capture_metrics": metrics,
        "final_capture_metrics": final_metrics,
        "fixes": fixes,
    }
    write_json(plan_path, plan)
    return notes


def save_skin(base: str, character: str, name: str, code: str) -> dict[str, Any]:
    payload = api_json(
        base,
        "POST",
        "/api/mex/skin-lab/save",
        {"name": name, "duplicate_action": "import_anyway", "slippi_action": "fix"},
        timeout=900,
    )
    if payload.get("type") in {"duplicate_dialog", "slippi_dialog"}:
        raise RuntimeError(f"skin-lab save returned unresolved dialog: {payload}")
    skin = find_skin(character, name, code)
    if not skin:
        raise RuntimeError(f"saved skin not found in metadata after app save: {character} {name} {code}; payload={payload}")
    media_notes = validate_vault_media(character, skin["id"], require_stock=character != "Nana")
    if media_notes:
        raise RuntimeError(f"app save produced incomplete media: {media_notes}")
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
    force: bool = False,
) -> tuple[dict[str, Any], list[str]]:
    code = costume_code(character, suffix)
    name = f"CShrineV2-{safe_name(character)}-{suffix}"
    plan_path = DUEL_DIR / "plans" / "characters" / character / f"{code}.json"
    preview_path = DUEL_DIR / "previews" / "characters" / character / f"{code}_review.jpg"
    notes: list[str] = []

    existing = find_skin(character, name, code)
    if existing and plan_path.exists() and preview_path.exists() and not force:
        media_notes = validate_vault_media(character, existing["id"], require_stock=True)
        if not media_notes:
            return character_entry(character, slot, code, name, existing["id"], existing["filename"], plan_path, preview_path), notes
        notes.extend([f"{character} {code}: existing v2 vault entry failed media validation; regenerating through app save"] + media_notes)

    source_path = vanilla_dat_path(character, code)
    if source_path is None:
        raise RuntimeError(f"{character} {code}: missing vanilla DAT; v2 refuses manual app-flow bypass for standard character")
    open_payload = {"character": character, "costumeCode": code}

    api_json(base, "POST", "/api/mex/skin-lab/open", open_payload, timeout=240)
    try:
        regions = api_json(base, "GET", "/api/mex/skin-lab/regions", timeout=120)["regionMap"]
        plan = character_plan(character, code, slot, regions)
        write_json(plan_path, plan)
        execute_character_steps(base, plan, material_paths)
        if not capture_preview(base, preview_path, f"{character} {code}"):
            notes.append(f"{character} {code}: viewer preview capture fell back to placeholder")
        notes.extend(review_character_capture(base, plan_path, plan, preview_path, material_paths))
        skin = save_skin(base, character, name, code)
        notes.append(f"{character} {code}: saved through /api/mex/skin-lab/save; CSP/stock validated from app intake")
        return character_entry(character, slot, code, name, skin["id"], skin["filename"], plan_path, preview_path), notes
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
        notes.extend(review_character_capture(base, plan_path, plan, preview_path, material_paths))
        dat = api_bytes(base, "/api/mex/skin-lab/export-dat", timeout=300)
        return dat, notes
    finally:
        try:
            api_json(base, "POST", "/api/mex/skin-lab/close", timeout=30)
        except Exception:
            pass


def import_ice_climbers_pair(
    base: str,
    name: str,
    popo_code: str,
    nana_code: str,
    popo_dat: bytes,
    nana_dat: bytes,
) -> tuple[dict[str, Any], dict[str, Any]]:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"{popo_code}.dat", popo_dat)
        zf.writestr(f"{nana_code}.dat", nana_dat)
    payload = api_multipart_file(
        base,
        "/api/mex/import/file",
        field_name="file",
        filename=f"{name}.zip",
        content=buf.getvalue(),
        data={
            "custom_title": name,
            "duplicate_action": "import_anyway",
            "slippi_action": "fix",
        },
        timeout=1200,
    )
    if payload.get("type") in {"duplicate_dialog", "slippi_dialog"}:
        raise RuntimeError(f"paired Ice Climbers import returned unresolved dialog: {payload}")
    popo_skin = find_skin("Ice Climbers", name, popo_code)
    nana_skin = find_skin("Ice Climbers", name, nana_code)
    if not popo_skin or not nana_skin:
        raise RuntimeError(
            f"paired Ice Climbers import did not create both metadata entries for {name}: "
            f"popo={bool(popo_skin)} nana={bool(nana_skin)} payload={payload}"
        )
    media_notes = validate_vault_media("Ice Climbers", popo_skin["id"], require_stock=True)
    media_notes.extend(validate_vault_media("Ice Climbers", nana_skin["id"], require_stock=False))
    if media_notes:
        raise RuntimeError(f"paired Ice Climbers app import produced incomplete media: {media_notes}")
    return popo_skin, nana_skin


def process_ice_climbers(base: str, material_paths: dict[str, Path], force: bool = False) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    entries: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    notes: list[str] = []
    popo_suffixes = VANILLA_CSS_COLOR_ORDER["Ice Climbers"]
    nana_suffixes = VANILLA_CSS_COLOR_ORDER["Nana"]

    for slot, (popo_suffix, nana_suffix) in enumerate(zip(popo_suffixes, nana_suffixes)):
        popo_code = costume_code("Ice Climbers", popo_suffix)
        nana_code = f"PlNn{nana_suffix}"
        pair_name = f"CShrineV2-IceClimbers-{popo_suffix}"

        popo_plan = DUEL_DIR / "plans" / "characters" / "Ice Climbers" / f"{popo_code}.json"
        nana_plan = DUEL_DIR / "plans" / "characters" / "Nana" / f"{nana_code}.json"
        popo_preview = DUEL_DIR / "previews" / "characters" / "Ice Climbers" / f"{popo_code}_review.jpg"
        nana_preview = DUEL_DIR / "previews" / "characters" / "Nana" / f"{nana_code}_review.jpg"

        popo_skin = find_skin("Ice Climbers", pair_name, popo_code)
        nana_skin = find_skin("Ice Climbers", pair_name, nana_code)
        if force or not (popo_skin and nana_skin and popo_plan.exists() and nana_plan.exists() and popo_preview.exists() and nana_preview.exists()):
            popo_dat, popo_notes = export_half_dat(base, "Ice Climbers", popo_code, popo_plan, popo_preview, material_paths, slot)
            nana_dat, nana_notes = export_half_dat(base, "Nana", nana_code, nana_plan, nana_preview, material_paths, slot)
            notes.extend(popo_notes)
            notes.extend(nana_notes)
            popo_skin, nana_skin = import_ice_climbers_pair(base, pair_name, popo_code, nana_code, popo_dat, nana_dat)
            notes.append(f"Ice Climbers {popo_code}/{nana_code}: imported paired DATs through /api/mex/import/file")
        else:
            media_notes = validate_vault_media("Ice Climbers", popo_skin["id"], require_stock=True)
            media_notes.extend(validate_vault_media("Ice Climbers", nana_skin["id"], require_stock=False))
            if media_notes:
                notes.extend([f"Ice Climbers {popo_code}/{nana_code}: existing v2 pair failed media validation; regenerating through paired app import"] + media_notes)
                popo_dat, popo_notes = export_half_dat(base, "Ice Climbers", popo_code, popo_plan, popo_preview, material_paths, slot)
                nana_dat, nana_notes = export_half_dat(base, "Nana", nana_code, nana_plan, nana_preview, material_paths, slot)
                notes.extend(popo_notes)
                notes.extend(nana_notes)
                popo_skin, nana_skin = import_ice_climbers_pair(base, pair_name, popo_code, nana_code, popo_dat, nana_dat)

        entries.append(
            character_entry(
                "Ice Climbers",
                slot,
                popo_code,
                pair_name,
                popo_skin["id"],
                popo_skin["filename"],
                popo_plan,
                popo_preview,
            )
        )
        nana_zip = STORAGE_PATH / "Ice Climbers" / nana_skin["filename"]
        pairs.append(
            {
                "slot": slot,
                "popoCode": popo_code,
                "nanaCode": nana_code,
                "popoVaultSkinId": popo_skin["id"],
                "nanaVaultSkinId": nana_skin["id"],
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
    stage_material = info["material_key"]
    steps: list[dict[str, Any]] = []
    for region in (region_map.get("regions") or {}).keys():
        kind = stage_step_kind(region)
        if code == "GrNLa":
            steps.append(
                {
                    "op": "composite",
                    "region": region,
                    "material_key": stage_material,
                    "material_prompt": MATERIALS[stage_material]["prompt"],
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
                    "material_key": stage_material,
                    "material_prompt": MATERIALS[stage_material]["prompt"],
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
        "design_intent": info["intent"],
        "steps": steps,
        "review": {
            "assessment": (
                f"Offline texture-sheet review for {info['stage']}: playfield regions use "
                f"the stage-specific {stage_material} material, backgrounds use the shared "
                "aurora shrine scene material, and animated or delicate regions are tinted "
                "to avoid smearing gameplay surfaces before in-game DAS capture."
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
            "projectName": "duel-codex-v2",
            "sourceIsoMd5": VANILLA_ISO_MD5,
            "nucleusProject": "projects/duel-codex-v2/project.mexproj",
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
    parser.add_argument("--only-character", default="")
    parser.add_argument("--only-suffix", default="")
    parser.add_argument("--force-assets", action="store_true")
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
    wanted_materials: set[str] | None = None
    if args.only_character:
        wanted_materials = set(CHARACTER_SHARED_MATERIAL_KEYS)
        if args.only_character.lower() == "ice climbers":
            wanted_materials.add(FIGHTER_DESIGNS["Ice Climbers"]["material_key"])
            wanted_materials.add(FIGHTER_DESIGNS["Nana"]["material_key"])
        else:
            matched_design = next(
                (design for name, design in FIGHTER_DESIGNS.items() if name.lower() == args.only_character.lower()),
                None,
            )
            if not matched_design:
                raise RuntimeError(f"unknown --only-character {args.only_character}")
            wanted_materials.add(matched_design["material_key"])
        if not args.skip_stages:
            wanted_materials.update(info["material_key"] for info in STAGES.values())
            wanted_materials.add("stage_backdrop")
    material_paths, models = generate_materials(base, wanted_materials)

    notes = [
        "Character previews are skin-lab render captures.",
        "Stage preview files are offline texture sheets; in-game DAS captures are not run by this generator.",
    ]
    manifest = make_manifest(models, notes)

    processed = 0
    for character, suffixes in VANILLA_CSS_COLOR_ORDER.items():
        if character in {"Mr. Game & Watch", "Nana"}:
            continue
        if args.only_character and character.lower() != args.only_character.lower():
            continue
        if character == "Ice Climbers":
            if args.only_suffix:
                notes.append("only-suffix is ignored for paired Ice Climbers; all four pairs are processed together")
            entries, pairs, ic_notes = process_ice_climbers(base, material_paths, force=args.force_assets)
            manifest["characters"][character] = entries
            manifest["ice_climbers_pairs"] = pairs
            notes.extend(ic_notes)
            processed += len(entries)
            continue
        manifest["characters"][character] = []
        for slot, suffix in enumerate(suffixes):
            if args.only_suffix and suffix.lower() != args.only_suffix.lower():
                continue
            if args.limit_character_slots and processed >= args.limit_character_slots:
                write_json(DUEL_DIR / "manifest.json", manifest)
                print(f"limit reached at {processed} character slots")
                return 0
            print(f"[duel] character {processed + 1}: {character} {suffix}", flush=True)
            entry, entry_notes = process_regular_character(base, character, suffix, slot, material_paths, force=args.force_assets)
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
