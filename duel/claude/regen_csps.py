"""regen_csps.py -- rebuild proper CSP + stock for the already-generated duel
costumes using the canonical skinlab.costume_assets.build_csp_and_stock (the
SAME path the unified import uses). Fixes the earlier mistake where csp.png/
stc.png were viewer frames (black bg, no CSP camera).

Rewrites each vault zip's csp.png/stc.png, the storage sidecar pngs, and the
metadata has_csp/has_stock/source fields. Ice Climbers Popo gets a composite CSP
with its Nana; Nana copies Popo's CSP + stock.

Run from repo root: venv/Scripts/python.exe duel/claude/regen_csps.py
"""
from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

DUEL = Path(__file__).resolve().parent
REPO = DUEL.parents[1]
sys.path.insert(0, str(REPO / "backend"))

from core.config import STORAGE_PATH  # noqa: E402
from core.metadata import load_metadata, save_metadata  # noqa: E402
from skinlab.costume_assets import build_csp_and_stock  # noqa: E402


def log(m):
    print(m, flush=True)


def dat_from_zip(zip_path: Path):
    with zipfile.ZipFile(zip_path) as z:
        name = next(n for n in z.namelist() if n.lower().endswith((".dat", ".usd")))
        return name, z.read(name)


def rewrite_zip(zip_path: Path, csp: bytes | None, stock: bytes | None):
    """Keep the costume DAT, replace csp.png/stc.png."""
    with zipfile.ZipFile(zip_path) as z:
        members = {n: z.read(n) for n in z.namelist()
                   if n.lower() not in ("csp.png", "stc.png", "stock.png")}
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in members.items():
            z.writestr(n, data)
        if csp:
            z.writestr("csp.png", csp)
        if stock:
            z.writestr("stc.png", stock)
    zip_path.write_bytes(buf.getvalue())


def update_meta_entry(meta, character, skin_id, assets):
    for s in meta.get("characters", {}).get(character, {}).get("skins", []):
        if s.get("id") == skin_id:
            s["has_csp"] = assets["csp"] is not None
            s["has_stock"] = assets["stock"] is not None
            s["csp_source"] = assets["csp_source"]
            s["stock_source"] = assets["stock_source"]
            return True
    return False


def persist(character, skin_id, zip_path: Path, assets, meta):
    rewrite_zip(zip_path, assets["csp"], assets["stock"])
    folder = STORAGE_PATH / character
    folder.mkdir(parents=True, exist_ok=True)
    if assets["csp"]:
        (folder / f"{skin_id}_csp.png").write_bytes(assets["csp"])
    if assets["stock"]:
        (folder / f"{skin_id}_stc.png").write_bytes(assets["stock"])
    update_meta_entry(meta, character, skin_id, assets)


def main(only=None):
    """Rebuild CSP/stock for all duel costumes, or just `only` (a set/list of
    character display names) when targeting specific fighters."""
    only_set = set(only) if only else None
    manifest = json.loads((DUEL / "manifest.json").read_text(encoding="utf-8"))
    meta = load_metadata(default={"characters": {}, "stages": {}})
    n = 0

    # Regular fighters (skip Ice Climbers; handled with Nana below)
    for character, entries in manifest["characters"].items():
        if character == "Ice Climbers":
            continue
        if only_set and character not in only_set:
            continue
        for e in entries:
            zip_path = REPO / e["zipPath"]
            _, dat = dat_from_zip(zip_path)
            assets = build_csp_and_stock(character, e["costumeCode"], dat, log=None)
            persist(character, e["vaultSkinId"], zip_path, assets, meta)
            n += 1
            log(f"[regen] {n} {character} {e['costumeCode']} "
                f"csp={assets['csp_source']} stock={assets['stock_source']}")

    # Ice Climbers Popo (composite with Nana) + Nana (copies Popo)
    ic_entries = {e["slot"]: e for e in manifest["characters"].get("Ice Climbers", [])}
    ic_pairs = manifest.get("ice_climbers_pairs", []) if (
        not only_set or only_set & {"Ice Climbers", "Nana"}) else []
    for pair in ic_pairs:
        slot = pair["slot"]
        popo_e = ic_entries[slot]
        popo_zip = REPO / popo_e["zipPath"]
        nana_zip = REPO / pair["nanaZipPath"]
        _, popo_dat = dat_from_zip(popo_zip)
        _, nana_dat = dat_from_zip(nana_zip)

        popo_assets = build_csp_and_stock(
            "Ice Climbers", pair["popoCode"], popo_dat,
            paired_dat_data=nana_dat, log=None)
        persist("Ice Climbers", pair["popoVaultSkinId"], popo_zip, popo_assets, meta)
        n += 1
        log(f"[regen] {n} Ice Climbers {pair['popoCode']} "
            f"csp={popo_assets['csp_source']} stock={popo_assets['stock_source']}")

        nana_assets = build_csp_and_stock(
            "Nana", pair["nanaCode"], nana_dat, is_nana=True,
            popo_csp=popo_assets["csp"], popo_stock=popo_assets["stock"], log=None)
        persist("Nana", pair["nanaVaultSkinId"], nana_zip, nana_assets, meta)
        n += 1
        log(f"[regen] {n} Nana {pair['nanaCode']} "
            f"csp={nana_assets['csp_source']} stock={nana_assets['stock_source']}")

    save_metadata(meta)
    log(f"[regen] done: {n} costumes")
    return 0


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma list of character display names")
    a = ap.parse_args()
    only = [c.strip() for c in a.only.split(",") if c.strip()] or None
    raise SystemExit(main(only))
