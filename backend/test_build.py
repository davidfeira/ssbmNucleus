"""
test_build.py -- assemble a MINIMAL, FULLY THROWAWAY test ISO containing the
vanilla Melee base plus exactly ONE mod, for the per-mod "Test in game" feature.

Every build is fresh and self-contained: create a brand-new MEX project from the
user's vanilla ISO, install just the one mod, export a throwaway ISO, and delete
the whole project afterwards. Nothing is cached or shared between tests, so a test
can never be polluted by a previous one. Each build uses its OWN MexManager
instance, so it never touches the user's currently-loaded project.

Supports four mod kinds:
  * costume          -> import-costume        (drive: fighter + costume index)
  * custom character -> add-fighter + place CSS icon  (drive: lock by CSS icon)
  * custom stage     -> add-stage + place SSS icon    (drive: select by SSS icon)
  * stage skin (DAS) -> DAS framework + variant behind a hold button
"""

import json
import logging
import shutil
import subprocess
import sys
import uuid
import zipfile
from pathlib import Path

from core.config import (PROJECT_ROOT, STORAGE_PATH, BASE_PATH, MEXCLI_PATH,
                         get_subprocess_args)

# mex_bridge lives under scripts/tools (state.py adds this too).
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "tools"))
from mex_bridge import MexManager  # noqa: E402

logger = logging.getLogger(__name__)

TEST_BUILD_DIR = STORAGE_PATH / "test-builds"   # throwaway projects + ISOs

CUSTOM_CHARACTERS_PATH = STORAGE_PATH / "custom_characters"
CUSTOM_STAGES_PATH = STORAGE_PATH / "custom_stages"
DAS_STORAGE_PATH = STORAGE_PATH / "das"

# DAS stage code -> (storage folder, the stage name the in-game selector uses).
DAS_STAGES = {
    "GrNBa": ("battlefield", "battlefield"),
    "GrNLa": ("final_destination", "finaldestination"),
    "GrSt": ("yoshis_story", "yoshisstory"),
    "GrOp": ("dreamland", "dreamland"),
    "GrPs": ("pokemon_stadium", "pokemonstadium"),
    "GrIz": ("fountain_of_dreams", "fountainofdreams"),
}


def _mexcli_create(vanilla_iso, proj_dir, name="NucleusTest"):
    cmd = [str(MEXCLI_PATH), "create", str(vanilla_iso), str(proj_dir), name]
    logger.info("mexcli create: %s", cmd)
    result = subprocess.run(
        cmd, capture_output=True, text=True, cwd=str(PROJECT_ROOT),
        **get_subprocess_args(),
    )
    if result.returncode != 0:
        raise RuntimeError(
            "mexcli create failed: " + (result.stderr or result.stdout or "unknown error").strip()
        )


def create_temp_project(vanilla_iso, log=lambda m: None):
    """Create a FRESH throwaway MEX project from the vanilla ISO. Returns
    (proj_dir, project_file); the caller MUST delete proj_dir when done."""
    if not vanilla_iso or not Path(vanilla_iso).exists():
        raise FileNotFoundError(
            f"Vanilla Melee ISO not found: {vanilla_iso}. Set it in Settings."
        )
    TEST_BUILD_DIR.mkdir(parents=True, exist_ok=True)
    proj_dir = TEST_BUILD_DIR / f"proj_{uuid.uuid4().hex[:12]}"
    log("Creating a fresh test project from the vanilla ISO…")
    _mexcli_create(vanilla_iso, proj_dir)
    proj = proj_dir / "project.mexproj"
    if not proj.exists():
        shutil.rmtree(proj_dir, ignore_errors=True)
        raise RuntimeError("mexcli create did not produce a project.mexproj")
    return proj_dir, proj


# --------------------------------------------------------------------------- #
# CSS / SSS icon placement (ported from the harness build-modded-iso.js).       #
# m-ex's add-fighter / add-stage leave a new icon at the default (0,0) -- which  #
# is BELOW the roster grid (the port-panel zone), so in-game the cursor can't    #
# hover+lock it. Move it into a free, lockable grid slot and return the exact    #
# coordinate the runner drives.                                                  #
# --------------------------------------------------------------------------- #
def _r(v):
    return round(v or 0)


def place_custom_fighter_icon(mex, fighter_name):
    """Move the new fighter's CSS icon into a free roster slot; return
    {x, y, index} (cursor target is (x, y-3.5); index == in-game grid index)."""
    layout = mex.get_css_layout()
    icons = layout.get("icons", []) or []
    if not icons:
        raise RuntimeError("CSS layout returned no icons")
    idx = next((i for i, ic in enumerate(icons) if (ic.get("fighterName") or "") == fighter_name), -1)
    if idx < 0:
        idx = next((i for i, ic in enumerate(icons) if _r(ic.get("x")) == 0 and _r(ic.get("y")) == 0), -1)
    if idx < 0:
        idx = len(icons) - 1
    # Free roster slots: the bottom-row empty edge cells, clear of the port panels.
    candidates = [(-28.15, 2.0, -1.0), (28.25, 2.0, -1.0),
                  (-28.15, 9.2, -1.0), (28.25, 9.2, -1.0),
                  (-28.15, 16.4, -1.0), (28.25, 16.4, -1.0)]
    occupied = set((_r(ic.get("x")), _r(ic.get("y"))) for i, ic in enumerate(icons) if i != idx)
    slot = next(((x, y, z) for (x, y, z) in candidates if (_r(x), _r(y)) not in occupied), candidates[0])
    icons[idx] = {**icons[idx], "x": slot[0], "y": slot[1], "z": slot[2]}
    mex.set_css_layout(json.dumps({"template": layout.get("template"), "icons": icons}))
    return {"x": slot[0], "y": slot[1], "index": idx}


def place_custom_stage_icon(mex, stage_name):
    """Move the new stage's SSS icon to a clear, reachable spot; return
    {page, x, y} (the page to R-switch to and the stage-cursor target)."""
    layout = mex.get_sss_layout()
    pages = layout.get("pages", []) or []
    if not pages:
        raise RuntimeError("SSS layout returned no pages")

    def icons_of(pg):
        return pg.get("icons") or pg.get("stageIcons") or []

    found = None
    for pi, pg in enumerate(pages):
        icons = icons_of(pg)
        ii = next((j for j, ic in enumerate(icons) if (ic.get("stageName") or "") == stage_name), -1)
        if ii < 0 and pi > 0:
            ii = next((j for j, ic in enumerate(icons) if _r(ic.get("x")) == 0 and _r(ic.get("y")) == 0), -1)
        if ii >= 0:
            found = (pi, ii)
            break
    if not found:
        raise RuntimeError(f"could not find the custom stage icon for '{stage_name}'")
    slot = (1.3, -9.1, 0.0)  # Battlefield's bottom-row position -- easy for the cursor
    icons = icons_of(pages[found[0]])
    icons[found[1]] = {**icons[found[1]], "x": slot[0], "y": slot[1], "z": slot[2]}
    mex.set_sss_layout(json.dumps({"pages": pages}))
    return {"page": found[0], "x": slot[0], "y": slot[1]}


def _das_install_framework(files_dir, log=lambda m: None):
    """Port of das.py das_install: copy each vanilla stage to <code>/vanilla.dat
    and replace the root stage file with the DAS loader."""
    das_source = BASE_PATH / "utility" / "DynamicAlternateStages"
    if not das_source.exists():
        raise FileNotFoundError(f"DAS framework source not found at {das_source}")
    files_dir.mkdir(parents=True, exist_ok=True)
    for code in DAS_STAGES:
        root_ext = ".usd" if code == "GrPs" else ".dat"
        stage_folder = files_dir / code
        stage_folder.mkdir(exist_ok=True)
        original_stage = files_dir / f"{code}{root_ext}"
        loader_src = das_source / f"{code}{root_ext}"
        vanilla_in_folder = stage_folder / "vanilla.dat"
        if not vanilla_in_folder.exists() and original_stage.exists():
            shutil.copy2(original_stage, vanilla_in_folder)
        if loader_src.exists():
            shutil.copy2(loader_src, original_stage)
    log("DAS framework installed into the test project")


def _export(mex, out_iso, progress_cb, log):
    Path(out_iso).parent.mkdir(parents=True, exist_ok=True)
    log("Exporting the test ISO…")
    mex.export_iso(str(out_iso), progress_cb, 1.0, False, False)
    if not Path(out_iso).exists():
        raise RuntimeError("export did not produce an ISO")


# --------------------------------------------------------------------------- #
# Build functions -- each: fresh project -> install one mod -> export -> nuke.   #
# --------------------------------------------------------------------------- #
def build_single_costume_iso(vanilla_iso, character, skin_zip, out_iso,
                             progress_cb=None, log=lambda m: None):
    """Fresh project + the one costume (storage zip). Returns the in-game costume
    index (color slot) of the imported costume."""
    skin_zip = Path(skin_zip)
    if not skin_zip.exists():
        raise FileNotFoundError(f"Costume archive not found: {skin_zip}")
    proj_dir, proj = create_temp_project(vanilla_iso, log=log)
    try:
        mex = MexManager(str(MEXCLI_PATH), str(proj))
        log(f"Importing the {character} costume…")
        imp = mex.import_costume(character, str(skin_zip))
        total = imp.get("totalCostumes")
        if total is None:
            fighter = mex.get_fighter_by_name(character)
            total = fighter.get("costumeCount") if fighter else None
        if not total:
            raise RuntimeError("could not determine the imported costume index")
        index = int(total) - 1
        _export(mex, out_iso, progress_cb, log)
        return index
    finally:
        shutil.rmtree(proj_dir, ignore_errors=True)


def build_custom_character_iso(vanilla_iso, slug, out_iso, progress_cb=None, log=lambda m: None):
    """Fresh project + the one custom fighter (storage/custom_characters/<slug>/
    fighter.zip), placed into the CSS grid. Returns {name, cssIcon}."""
    zip_path = CUSTOM_CHARACTERS_PATH / slug / "fighter.zip"
    if not zip_path.exists():
        raise FileNotFoundError(f"Custom character archive not found: {zip_path}")
    proj_dir, proj = create_temp_project(vanilla_iso, log=log)
    try:
        mex = MexManager(str(MEXCLI_PATH), str(proj))
        log(f"Adding custom fighter '{slug}'…")
        res = mex._run_command("add-fighter", str(proj), str(zip_path))
        name = res.get("name") or slug
        log(f"Placing {name} into the CSS grid…")
        css_icon = place_custom_fighter_icon(mex, name)
        _export(mex, out_iso, progress_cb, log)
        return {"name": name, "cssIcon": css_icon}
    finally:
        shutil.rmtree(proj_dir, ignore_errors=True)


def build_custom_stage_iso(vanilla_iso, slug, out_iso, progress_cb=None, log=lambda m: None):
    """Fresh project + the one custom stage (storage/custom_stages/<slug>/
    stage.zip), placed on the SSS. Returns {name, sssIcon}."""
    zip_path = CUSTOM_STAGES_PATH / slug / "stage.zip"
    if not zip_path.exists():
        raise FileNotFoundError(f"Custom stage archive not found: {zip_path}")
    proj_dir, proj = create_temp_project(vanilla_iso, log=log)
    try:
        mex = MexManager(str(MEXCLI_PATH), str(proj))
        log(f"Adding custom stage '{slug}'…")
        res = mex._run_command("add-stage", str(proj), str(zip_path))
        name = res.get("name") or slug
        log(f"Placing {name} on the stage-select screen…")
        sss_icon = place_custom_stage_icon(mex, name)
        _export(mex, out_iso, progress_cb, log)
        return {"name": name, "sssIcon": sss_icon}
    finally:
        shutil.rmtree(proj_dir, ignore_errors=True)


def build_stage_skin_iso(vanilla_iso, stage_code, stage_folder, variant_id, out_iso,
                         button="X", progress_cb=None, log=lambda m: None):
    """Fresh project + the DAS framework + the one stage skin behind a HOLD button
    (storage/das/<stage_folder>/<variant_id>.zip). Returns {stage, button}."""
    if stage_code not in DAS_STAGES:
        raise ValueError(f"unknown DAS stage code: {stage_code}")
    variant_zip = DAS_STORAGE_PATH / stage_folder / f"{variant_id}.zip"
    if not variant_zip.exists():
        raise FileNotFoundError(f"Stage variant archive not found: {variant_zip}")
    button = (button or "X").upper()
    proj_dir, proj = create_temp_project(vanilla_iso, log=log)
    try:
        files_dir = proj_dir / "files"
        log("Installing the DAS framework…")
        _das_install_framework(files_dir, log=log)
        # Extract the variant's stage .dat and drop it in behind the hold button.
        with zipfile.ZipFile(variant_zip) as z:
            dat_name = next((n for n in z.namelist()
                             if n.lower().endswith(".dat") or n.lower().endswith(".usd")), None)
            if not dat_name:
                raise RuntimeError(f"no .dat/.usd inside {variant_zip}")
            data = z.read(dat_name)
        stage_dir = files_dir / stage_code
        stage_dir.mkdir(parents=True, exist_ok=True)
        (stage_dir / f"NucleusTestSkin({button}).dat").write_bytes(data)
        log(f"Placed the stage skin behind HOLD {button} on {DAS_STAGES[stage_code][1]}")
        mex = MexManager(str(MEXCLI_PATH), str(proj))
        _export(mex, out_iso, progress_cb, log)
        return {"stage": DAS_STAGES[stage_code][1], "button": button}
    finally:
        shutil.rmtree(proj_dir, ignore_errors=True)
