"""refix_chars.py -- regenerate specific duel fighters' costume DATs through the
full Porcelain & Ink pipeline (reusing the generator's make_skin), then rebuild
their CSP/stock via regen_csps. Used to re-roll characters after a skin-lab fix
without touching the rest of the pack.

Needs a backend with the CURRENT skin_lab code and cached materials:
    venv/Scripts/python.exe duel/claude/refix_chars.py \
        --backend http://127.0.0.1:PORT --characters Pichu,Jigglypuff
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DUEL = Path(__file__).resolve().parent
REPO = DUEL.parents[1]
sys.path.insert(0, str(DUEL))          # import the sibling generator module
sys.path.insert(0, str(REPO / "backend"))

import generate_duel_assets as G       # noqa: E402
import regen_csps                      # noqa: E402
from core.config import STORAGE_PATH   # noqa: E402
from core.constants import CHAR_PREFIXES  # noqa: E402


def suffix_of(character: str, code: str) -> str:
    prefix = "Pl" + CHAR_PREFIXES[character]
    return code[len(prefix):]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", default="http://127.0.0.1:5000")
    ap.add_argument("--characters", required=True, help="comma list of fighters")
    args = ap.parse_args()
    base = args.backend.rstrip("/")
    chars = [c.strip() for c in args.characters.split(",") if c.strip()]

    manifest = json.loads((DUEL / "manifest.json").read_text(encoding="utf-8"))
    materials, _ = G.generate_materials(base)
    notes: list[str] = []

    for ch in chars:
        entries = manifest["characters"].get(ch, [])
        if not entries:
            print(f"[refix] {ch}: no manifest entries, skipping")
            continue
        for e in entries:
            code = e["costumeCode"]
            suffix = suffix_of(ch, code)
            skin_id = f"PorcInk-{G.safe_name(ch)}-{suffix}"
            zip_path = STORAGE_PATH / ch / f"{skin_id}.zip"
            plan_path = DUEL / "plans" / "characters" / ch / f"{code}.json"
            prev_path = DUEL / "previews" / "characters" / ch / f"{code}_review.jpg"
            for p in (zip_path, plan_path, prev_path):   # force regen
                if p.exists():
                    p.unlink()
            G.make_skin(base, ch, suffix, materials, notes)
            print(f"[refix] rebuilt DAT {ch} {code}")

    # rebuild CSP + stock for just these fighters through the canonical path
    regen_csps.main(only=chars)
    if notes:
        print("[refix] notes:")
        for n in notes:
            print("  -", n)
    print("[refix] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
