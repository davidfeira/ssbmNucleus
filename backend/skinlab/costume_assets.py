"""costume_assets.py -- the ONE canonical way to build a costume's portrait
assets (CSP + stock icon) from its DAT.

Every producer of a vault costume -- the unified import, skin-lab saves, the
modpack-duel generator, the "regenerate CSP" actions -- should call
`build_csp_and_stock` instead of re-implementing the render/recolor glue. The
real work still lives in `generate_csp` (HSDRawViewer headless render with the
character's proper anim + camera assets) and `skinlab.stock_gen.generate_stock`
(deterministic recolor / head-shot crop); this module just wires them together
with the agreed fallbacks so the result is identical no matter who asks.

The character and costume color are auto-detected from the DAT content by
`generate_csp` (DATParser.detect_character), so the temp filename does not
matter -- but we name it after the costume code anyway for readable logs.
"""
from __future__ import annotations

import logging
import os
import shutil
import tempfile

from core.config import VANILLA_ASSETS_DIR
from generate_csp import generate_csp, generate_head_shot
from skinlab.stock_gen import generate_stock, recolor_gw_stock

# Characters whose stock icon is DERIVED (recolored) from the vanilla one rather
# than rendered/texture-diffed: Mr. Game & Watch carries no color in his model
# (the game recolors him from GAMEWATCH_COLOR by slot), so he's always a solid
# color -- recoloring the vanilla icon is exact and can't fail to a white render.
_GW_NAMES = ("Mr. Game & Watch", "G&W")

logger = logging.getLogger(__name__)


def _vanilla_stock(character: str, costume_code: str) -> tuple[bytes | None, str]:
    """Vanilla stock for this costume code, else the character's default (Nr)."""
    direct = VANILLA_ASSETS_DIR / character / costume_code / "stock.png"
    if direct.exists():
        return direct.read_bytes(), "vanilla"
    if len(costume_code) >= 4:
        default_code = costume_code[:4] + "Nr"
        default = VANILLA_ASSETS_DIR / character / default_code / "stock.png"
        if default.exists():
            return default.read_bytes(), "vanilla_default"
    return None, "missing"


def build_stock(
    character: str,
    costume_code: str,
    dat_data: bytes,
    *,
    dat_path: str | None = None,
    aligned_csp: bytes | None = None,
    is_nana: bool = False,
    popo_stock: bytes | None = None,
    vanilla_fallback: bool = True,
    color_index: int | None = None,
    log: logging.Logger | None = None,
) -> tuple[bytes | None, str, str | None]:
    """Derive ONE costume's stock icon. Returns (png_bytes|None, source, method).

    source: 'generated' | 'copied_from_popo' | 'vanilla' | 'vanilla_default' |
            'missing'.  method: the generate_stock method when generated (e.g.
            'texture-diff' / 'csp-diff' / 'head-shot'), else mirrors source.

    `aligned_csp` (our OWN render, vanilla pose => pixel-aligned) may feed the
    csp-diff path; community/custom CSPs must not. `vanilla_fallback=False` makes
    a failed generation return (None,'missing',None) instead of a vanilla icon --
    used by the "preview a generated stock" UI which wants generated-only.
    `color_index` is the CSS slot for characters recolored from the vanilla icon
    (Mr. Game & Watch: 0=black default, 1=red, 2=blue, 3=green).
    """
    log = log or logger
    if is_nana:
        if popo_stock:
            return popo_stock, "copied_from_popo", "copied_from_popo"
        return None, "missing", None

    # Mr. Game & Watch: recolor the vanilla icon by slot, never render him (his
    # model has no color, so the render/texture-diff path can only make black or a
    # white head-shot). color_index 0 (default) leaves the vanilla black icon as-is.
    if character in _GW_NAMES:
        data, source = _vanilla_stock(character, costume_code)
        if data is not None:
            return recolor_gw_stock(data, color_index), source, "gw_recolor"
        return (None, "missing", None) if not vanilla_fallback else (None, source, source)

    own_tmp = None
    if dat_path is None:
        own_tmp = tempfile.mkdtemp(prefix="stock_")
        dat_path = os.path.join(own_tmp, f"{costume_code or 'costume'}.dat")
        with open(dat_path, "wb") as f:
            f.write(dat_data)
    try:
        try:
            generated = generate_stock(
                VANILLA_ASSETS_DIR, character, costume_code or "",
                modded_dat_path=dat_path,
                modded_csp=aligned_csp,
                head_shot_provider=lambda: generate_head_shot(dat_path))
            if generated:
                stock_bytes, method = generated
                log.info(f"Generated stock for {costume_code} via {method}")
                return stock_bytes, "generated", method
        except Exception as e:
            log.warning(f"Stock generation failed for {costume_code}: {e}")
        if vanilla_fallback:
            data, source = _vanilla_stock(character, costume_code)
            return data, source, source
        return None, "missing", None
    finally:
        if own_tmp:
            shutil.rmtree(own_tmp, ignore_errors=True)


def build_csp_and_stock(
    character: str,
    costume_code: str,
    dat_data: bytes,
    *,
    existing_csp: bytes | None = None,
    existing_stock: bytes | None = None,
    paired_dat_data: bytes | None = None,
    is_nana: bool = False,
    popo_csp: bytes | None = None,
    popo_stock: bytes | None = None,
    allow_stock_gen: bool = True,
    color_index: int | None = None,
    log: logging.Logger | None = None,
) -> dict:
    """Return {csp, csp_source, stock, stock_source} for one costume.

    csp/stock are PNG bytes (or None if unavailable). *_source is provenance:
    'imported' (came in with the costume), 'generated', 'copied_from_popo',
    'vanilla', 'vanilla_default', or 'missing'.

    Rules (identical to the unified import flow):
      CSP    -- existing wins; else Ice Climbers Popo composites with its Nana
                (paired_dat_data); else Nana copies Popo (popo_csp); else render
                via generate_csp (proper anim + camera).
      stock  -- existing wins; else Nana copies Popo (popo_stock); else recolor
                the vanilla icon via generate_stock (aligned to our own render
                when we just generated the CSP); else vanilla / default fallback.

    `allow_stock_gen=False` skips the recolor step: a missing stock falls
    straight back to the vanilla icon (Nana still copies Popo). The ISO-scan
    bulk import uses this -- generate_stock is the slow part of a 90-skin batch
    and its result is approximate anyway.
    """
    log = log or logger
    tmp_dir = tempfile.mkdtemp(prefix="csp_assets_")
    dat_path = os.path.join(tmp_dir, f"{costume_code or 'costume'}.dat")
    with open(dat_path, "wb") as f:
        f.write(dat_data)

    csp_data = existing_csp
    csp_source = "imported" if existing_csp else None
    stock_data = existing_stock
    stock_source = "imported" if existing_stock else None

    try:
        # ---- CSP -------------------------------------------------------------
        if csp_data is None:
            if paired_dat_data is not None:
                nana_path = os.path.join(tmp_dir, "PlNnPair.dat")
                with open(nana_path, "wb") as f:
                    f.write(paired_dat_data)
                try:
                    out = generate_csp(dat_path, paired_dat_filepath=nana_path)
                    if out and os.path.exists(out):
                        with open(out, "rb") as f:
                            csp_data = f.read()
                        csp_source = "generated"
                        _drop(out)
                    else:
                        log.warning(f"composite CSP generation failed for {costume_code}")
                except Exception as e:
                    log.warning(f"composite CSP generation error for {costume_code}: {e}")
            elif is_nana:
                if popo_csp:
                    csp_data, csp_source = popo_csp, "copied_from_popo"
            else:
                try:
                    out = generate_csp(dat_path)
                    if out and os.path.exists(out):
                        with open(out, "rb") as f:
                            csp_data = f.read()
                        csp_source = "generated"
                        _drop(out)
                        _drop(out + ".head.json")
                    else:
                        log.warning(f"CSP generation failed for {costume_code}")
                except Exception as e:
                    log.warning(f"CSP generation error for {costume_code}: {e}")

        # ---- stock -----------------------------------------------------------
        if stock_data is None:
            if not allow_stock_gen:
                # Fast path (ISO-scan bulk import): skip the texture-diff /
                # head-shot stock generator entirely. Nana still copies Popo's
                # icon; everyone else falls straight back to the vanilla stock
                # for this costume (the character's default colour if the exact
                # slot has none).
                if is_nana:
                    stock_data = popo_stock
                    stock_source = "copied_from_popo" if popo_stock else "missing"
                elif character in _GW_NAMES:
                    data, stock_source = _vanilla_stock(character, costume_code)
                    stock_data = recolor_gw_stock(data, color_index) if data else None
                else:
                    stock_data, stock_source = _vanilla_stock(character, costume_code)
            else:
                # only our OWN render (vanilla pose => pixel-aligned) may feed the
                # csp-diff path; community/custom CSPs must not.
                aligned_csp = csp_data if csp_source == "generated" else None
                stock_data, stock_source, _ = build_stock(
                    character, costume_code, dat_data, dat_path=dat_path,
                    aligned_csp=aligned_csp, is_nana=is_nana, popo_stock=popo_stock,
                    color_index=color_index, vanilla_fallback=True, log=log)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return {
        "csp": csp_data, "csp_source": csp_source or "missing",
        "stock": stock_data, "stock_source": stock_source or "missing",
    }


def _drop(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass
