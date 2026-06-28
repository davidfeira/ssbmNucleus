"""
First-run setup module for extracting vanilla assets from user's Melee ISO.

This module handles:
1. Extracting the user's vanilla Melee 1.02 ISO using mexcli
2. Reading fighter JSONs to get asset mappings
3. Copying DATs, CSPs, stocks, CSS icons to utility/assets/vanilla/
4. Copying stage images to utility/assets/stages/
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
import logging
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Callable, Optional

from core.config import get_subprocess_args

logger = logging.getLogger(__name__)


class FirstRunSetup:
    """Handles first-run setup: extracting vanilla assets from user's Melee ISO."""

    BUILTIN_GIGA_SLUG = "giga-bowser"
    BUILTIN_GIGA_NAME = "Giga Bowser"
    BUILTIN_GIGA_FIGHTER_JSON = "031.json"
    BUILTIN_GIGA_FIGHTER_INDEX = 31
    BUILTIN_GIGA_COSTUMES = (
        {"code": "Nr", "name": "Normal", "regions": {}},
        {
            "code": "Re",
            "name": "Red",
            "regions": {
                "skin": {"hue": 18, "saturation": 62},
                "shell": {"hue": 350, "saturation": 72},
                "fur": {"hue": 8, "saturation": 82},
            },
        },
        {
            "code": "Bu",
            "name": "Blue",
            "regions": {
                "skin": {"hue": 210, "saturation": 46},
                "shell": {"hue": 232, "saturation": 76},
                "fur": {"hue": 190, "saturation": 70},
            },
        },
        {
            "code": "Gr",
            "name": "Green",
            "regions": {
                "skin": {"hue": 108, "saturation": 52},
                "shell": {"hue": 142, "saturation": 78},
                "fur": {"hue": 78, "saturation": 70},
            },
        },
    )

    # Original fighters (indices 0-26 in fighter JSONs)
    # Includes: Mario(0), Fox(1)...Ganondorf(25), Roy(26)
    # Note: Nana(11) is included as separate from Popo/Ice Climbers
    VANILLA_FIGHTER_COUNT = 27

    # Stage icon mappings (ISO assets/sss/ -> utility/assets/stages/)
    STAGE_ICONS = {
        "icon_036.png": "pokemon stadium.png",
        "icon_012.png": "yoshis story.png",
        "icon_016.png": "fountain of dreams.png",
        "icon_050.png": "final destination.png",
        "icon_048.png": "battlefield.png",
        "icon_052.png": "dreamland.png"
    }

    # Characters whose CSPs should NOT be overwritten (kept in git)
    # Sheik has custom CSPs since vanilla Melee doesn't have separate Sheik portraits
    PRESERVE_CSP_CHARACTERS = ["Sheik"]

    # Asset overrides for characters with incorrect mappings in fighter JSONs
    # Mr. Game & Watch's JSON points to wrong CSP/stock indices
    ASSET_OVERRIDES = {
        "Mr. Game & Watch": {
            "PlGwNr": {
                "csp": "csp/csp_015",
                "icon": "icons/ft_109"
            }
        }
    }

    # Expected size of extracted ISO in bytes (~1.4GB for vanilla Melee)
    EXPECTED_EXTRACTION_SIZE = 1_400_000_000

    # Menu sound mappings: index in main.ssm -> filename
    # These are the UI sounds used in the app
    MENU_SOUNDS = {
        115: "new_skin",
        116: "big_achievement",
        117: "back",
        118: "start",
        119: "tick",
        120: "error",
        127: "click",
        135: "camera_click",
        216: "major_error"
    }

    # Mapping: csp_data folder -> list of (vanilla_char, costume_code) tuples
    # Used to copy vanilla DATs to csp_data directory for CSP generation tooling
    CSP_DATA_DAT_MAPPING = {
        "Bowser": [("Bowser", "PlKpNr")],
        "C. Falcon": [("C. Falcon", "PlCaNr")],
        "DK": [("DK", "PlDkBp")],
        "Dr. Mario": [("Dr. Mario", "PlDrNr")],
        "Falco": [("Falco", "PlFcNr")],
        "G&W": [("Mr. Game & Watch", "PlGwNr")],
        "Ganondorf": [("Ganondorf", "PlGnNr")],
        "Ice Climbers": [("Ice Climbers", "PlPpNr"), ("Nana", "PlNnNr")],
        "Ice Climbers (Nana)": [("Nana", "PlNnNr")],
        "Ice Climbers (Popo)": [("Ice Climbers", "PlPpNr")],
        "Jigglypuff": [("Jigglypuff", "PlPrNr")],
        "Kirby": [("Kirby", "PlKbNr")],
        "Link": [("Link", "PlLkNr")],
        "Luigi": [("Luigi", "PlLgNr")],
        "Mario": [("Mario", "PlMrNr")],
        "Marth": [("Marth", "PlMsNr")],
        "Mewtwo": [("Mewtwo", "PlMtNr")],
        "Ness": [("Ness", "PlNsNr")],
        "Peach": [("Peach", "PlPeNr")],
        "Pichu": [("Pichu", "PlPcNr")],
        "Pikachu": [("Pikachu", "PlPkNr")],
        "Roy": [("Roy", "PlFeNr")],
        "Samus": [("Samus", "PlSsNr")],
        "Sheik": [("Sheik", "PlSkNr")],
        "Yoshi": [("Yoshi", "PlYsNr")],
        "Young Link": [("Young Link", "PlClNr")],
        "Zelda": [("Zelda", "PlZdNr")],
    }

    def __init__(self, project_root: Path, mexcli_path: Path):
        """
        Initialize the first-run setup handler.

        Args:
            project_root: Root path of the project
            mexcli_path: Path to mexcli executable
        """
        self.project_root = project_root
        self.mexcli_path = mexcli_path
        self.vanilla_dir = project_root / "utility" / "assets" / "vanilla"
        self.stages_dir = project_root / "utility" / "assets" / "stages"
        self.sounds_dir = project_root / "utility" / "assets" / "vanilla" / "sounds"

        # Detect bundled resources directory (for production builds)
        # Bundled Sheik PNGs need to be copied to PROJECT_ROOT since they're not in the ISO
        if getattr(sys, 'frozen', False):
            exe_path = Path(sys.executable)
            self.bundled_resources_dir = exe_path.parent.parent  # resources/
            # In production, tools are bundled in resources/
            self.csp_data_dir = self.bundled_resources_dir / "utility" / "tools" / "processor" / "csp_data"
            self.hsdraw_path = self.bundled_resources_dir / "utility" / "HSDRawViewer" / "HSDRawViewer.exe"
        else:
            self.bundled_resources_dir = None
            # In development, tools are in project root
            self.csp_data_dir = project_root / "utility" / "tools" / "processor" / "csp_data"
            self.hsdraw_path = project_root / "utility" / "tools" / "HSDLib" / "HSDRawViewer" / "bin" / "Release" / "net6.0-windows" / "HSDRawViewer.exe"

    def check_setup_needed(self) -> dict:
        """
        Check if first-run setup is needed.

        Returns:
            dict with 'complete' bool and 'details' about what's missing
        """
        if not self.vanilla_dir.exists():
            return {
                'complete': False,
                'reason': 'vanilla_dir_missing',
                'details': 'Vanilla assets directory does not exist'
            }

        # Check for at least some character folders
        # Exclude non-character directories like custom_poses
        excluded_dirs = {'custom_poses'}
        char_folders = [d for d in self.vanilla_dir.iterdir() if d.is_dir() and d.name not in excluded_dirs]
        if len(char_folders) < self.VANILLA_FIGHTER_COUNT:
            return {
                'complete': False,
                'reason': 'insufficient_characters',
                'details': f'Found {len(char_folders)} character folders, expected {self.VANILLA_FIGHTER_COUNT}'
            }

        # Sample check: verify a few characters have proper structure
        sample_chars = list(char_folders)[:5]
        for char_dir in sample_chars:
            # Check for at least one costume subfolder with csp.png
            costume_dirs = [d for d in char_dir.iterdir() if d.is_dir() and d.name.startswith('Pl')]
            if not costume_dirs:
                return {
                    'complete': False,
                    'reason': 'missing_costumes',
                    'details': f'Character {char_dir.name} has no costume folders'
                }

            # Check first costume has required files
            first_costume = costume_dirs[0]
            if not (first_costume / 'csp.png').exists():
                return {
                    'complete': False,
                    'reason': 'missing_csp',
                    'details': f'Costume {first_costume.name} missing csp.png'
                }

        # Check stages
        if not self.stages_dir.exists():
            return {
                'complete': False,
                'reason': 'stages_dir_missing',
                'details': 'Stages directory does not exist'
            }

        stage_count = len(list(self.stages_dir.glob('*.png'))) + len(list(self.stages_dir.glob('*.jpg')))
        if stage_count < len(self.STAGE_ICONS):
            return {
                'complete': False,
                'reason': 'insufficient_stages',
                'details': f'Found {stage_count} stage images, expected {len(self.STAGE_ICONS)}'
            }

        return {
            'complete': True,
            'details': 'All vanilla assets present'
        }

    def _copy_bundled_sheik_assets(self) -> dict:
        """
        Copy bundled Sheik PNGs from resources to PROJECT_ROOT.

        Sheik has custom CSPs since vanilla Melee doesn't have separate Sheik portraits.
        These are bundled with the app and need to be copied to the user's writable
        directory before ISO extraction (which skips Sheik CSPs via PRESERVE_CSP_CHARACTERS).
        """
        if not self.bundled_resources_dir:
            # Not running as bundled exe, skip
            return {'success': True}

        bundled_sheik_dir = self.bundled_resources_dir / "utility" / "assets" / "vanilla" / "Sheik"
        if not bundled_sheik_dir.exists():
            logger.warning(f"Bundled Sheik assets not found at: {bundled_sheik_dir}")
            return {'success': True}  # Not fatal, continue anyway

        try:
            dest_sheik_dir = self.vanilla_dir / "Sheik"
            dest_sheik_dir.mkdir(parents=True, exist_ok=True)

            # Copy all PNG files (CSPs, stock icons, css_icon)
            copied_count = 0
            for src_file in bundled_sheik_dir.rglob("*.png"):
                # Preserve subdirectory structure (e.g., PlSkNr/csp.png)
                rel_path = src_file.relative_to(bundled_sheik_dir)
                dest_file = dest_sheik_dir / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dest_file)
                copied_count += 1

            logger.info(f"Copied {copied_count} bundled Sheik PNGs to {dest_sheik_dir}")
            return {'success': True, 'copied': copied_count}

        except Exception as e:
            logger.error(f"Failed to copy bundled Sheik assets: {e}")
            return {'success': False, 'error': str(e)}

    def _copy_bundled_sounds(self) -> dict:
        """
        Copy bundled menu sounds from resources to PROJECT_ROOT.

        Menu sounds are bundled with the app for reliability instead of
        extracting them from the ISO at runtime.
        """
        if not self.bundled_resources_dir:
            # Not running as bundled exe, skip
            return {'success': True}

        bundled_sounds_dir = self.bundled_resources_dir / "utility" / "assets" / "vanilla" / "sounds"
        if not bundled_sounds_dir.exists():
            logger.warning(f"Bundled sounds not found at: {bundled_sounds_dir}")
            return {'success': True}  # Not fatal, continue anyway

        try:
            self.sounds_dir.mkdir(parents=True, exist_ok=True)

            # Copy all WAV files
            copied_count = 0
            for src_file in bundled_sounds_dir.glob("*.wav"):
                dest_file = self.sounds_dir / src_file.name
                shutil.copy2(src_file, dest_file)
                copied_count += 1

            logger.info(f"Copied {copied_count} bundled sounds to {self.sounds_dir}")
            return {'success': True, 'copied': copied_count}

        except Exception as e:
            logger.error(f"Failed to copy bundled sounds: {e}")
            return {'success': False, 'error': str(e)}

    def _read_metadata(self) -> dict:
        metadata_file = self.project_root / "storage" / "metadata.json"
        if not metadata_file.exists():
            return {
                "version": "1.0",
                "characters": {},
                "stages": {},
                "custom_stages": [],
                "custom_characters": [],
            }
        with open(metadata_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        data.setdefault("version", "1.0")
        data.setdefault("characters", {})
        data.setdefault("stages", {})
        data.setdefault("custom_stages", [])
        data.setdefault("custom_characters", [])
        return data

    def _write_metadata(self, metadata: dict) -> None:
        metadata_file = self.project_root / "storage" / "metadata.json"
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    @staticmethod
    def _zip_with_replacements(zip_path: Path, replacements: dict[str, bytes]) -> None:
        tmp_path = zip_path.with_suffix(zip_path.suffix + ".tmp")
        written = set()
        with zipfile.ZipFile(zip_path, "r") as src, zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as dst:
            existing = {item.filename for item in src.infolist()}
            for item in src.infolist():
                data = replacements.get(item.filename)
                if data is None:
                    data = src.read(item.filename)
                else:
                    written.add(item.filename)
                dst.writestr(item, data)
            for name, data in replacements.items():
                if name not in written and name not in existing:
                    dst.writestr(name, data)
        tmp_path.replace(zip_path)

    @staticmethod
    def _fit_png(source_path: Path, size: tuple[int, int]) -> bytes:
        from io import BytesIO
        from PIL import Image

        with Image.open(source_path) as source:
            img = source.convert("RGBA")
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)
        resampling = getattr(Image, "Resampling", Image)
        img.thumbnail(size, getattr(resampling, "LANCZOS", Image.BICUBIC))
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        x = (size[0] - img.width) // 2
        y = (size[1] - img.height) // 2
        canvas.alpha_composite(img, (x, y))
        buf = BytesIO()
        canvas.save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def _make_text_banner(size: tuple[int, int], text: str) -> bytes:
        from io import BytesIO
        from PIL import Image, ImageDraw, ImageFont

        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        font = None
        for font_name in ("arialbd.ttf", "arial.ttf"):
            try:
                font = ImageFont.truetype(font_name, max(8, size[1] - 8))
                break
            except Exception:
                font = None
        if font is None:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = max(0, (size[0] - text_w) // 2)
        y = max(0, (size[1] - text_h) // 2 - 1)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0, 220))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    def _resolve_asset_png(assets_dir: Path, ref: str | None) -> Path | None:
        if not ref:
            return None
        path = assets_dir / (ref.replace("\\", "/") + ".png")
        return path if path.exists() else None

    def _bundled_giga_icon(self) -> Path | None:
        # Giga has no in-game CSS icon to derive, so ship a hand-made one. The
        # asset lives at backend/assets/builtin/<slug>/icon.png. In a frozen
        # build self.project_root is the user-data dir (LocalAppData), NOT the
        # install, so resolve from the PyInstaller bundle (_MEIPASS) there;
        # fall back to the source tree path for dev.
        rel = Path("backend") / "assets" / "builtin" / self.BUILTIN_GIGA_SLUG / "icon.png"
        candidates = []
        if getattr(sys, "frozen", False):
            candidates.append(Path(sys._MEIPASS) / rel)
        candidates.append(self.project_root / rel)
        for path in candidates:
            if path.exists():
                return path
        return None

    def _giga_bowser_seed_current(self, char_dir: Path) -> bool:
        zip_path = char_dir / "fighter.zip"
        fighter_json_path = char_dir / "fighter.json"
        if not zip_path.exists() or not fighter_json_path.exists():
            return False

        expected_dat_files = {
            f"PlGk{spec['code']}.dat" for spec in self.BUILTIN_GIGA_COSTUMES
        }
        expected_zip_files = {
            f"PlGk{spec['code']}.zip" for spec in self.BUILTIN_GIGA_COSTUMES
        }

        try:
            with open(fighter_json_path, "r", encoding="utf-8") as f:
                fighter_data = json.load(f)
            current_dat_files = {
                ((costume.get("file") or {}).get("fileName") or "")
                for costume in fighter_data.get("costumes", [])
            }
            if not expected_dat_files.issubset(current_dat_files):
                return False
            if (
                fighter_data.get("redCostumeIndex") != 1
                or fighter_data.get("blueCostumeIndex") != 2
                or fighter_data.get("greenCostumeIndex") != 3
            ):
                return False

            with zipfile.ZipFile(zip_path, "r") as zf:
                names = set(zf.namelist())
                if not expected_zip_files.issubset(names):
                    return False
                for zip_name in expected_zip_files:
                    with zipfile.ZipFile(zf.open(zip_name), "r") as costume_zip:
                        inner_names = set(costume_zip.namelist())
                        stem = Path(zip_name).stem
                        if f"{stem}.dat" not in inner_names:
                            return False

            bundled_icon = self._bundled_giga_icon()
            current_icon = char_dir / "css_icon.png"
            if bundled_icon and (
                not current_icon.exists()
                or current_icon.read_bytes() != bundled_icon.read_bytes()
            ):
                return False
        except Exception:
            return False

        return True

    def _patch_giga_bowser_fighter_data(
        self,
        fighter_data: dict,
        bowser_data: dict | None,
        costume_specs: list[dict] | None = None,
    ) -> dict:
        data = json.loads(json.dumps(fighter_data))
        data["name"] = self.BUILTIN_GIGA_NAME
        data["seriesID"] = 11
        data["targetTestStage"] = (bowser_data or {}).get("targetTestStage", 42)
        data["classicTrophyId"] = (bowser_data or {}).get("classicTrophyId", 30)
        data["adventureTrophyId"] = (bowser_data or {}).get("adventureTrophyId", 31)
        data["allStarTrophyId"] = (bowser_data or {}).get("allStarTrophyId", 32)
        data["racetoTheFinishTime"] = (bowser_data or {}).get("racetoTheFinishTime", 52)
        data["resultScreenScale"] = 0.35
        data["endingScreenScale"] = 0.2
        costume_specs = costume_specs or [self.BUILTIN_GIGA_COSTUMES[0]]
        code_to_index = {spec["code"]: i for i, spec in enumerate(costume_specs)}
        data["redCostumeIndex"] = code_to_index.get("Re", 0)
        data["blueCostumeIndex"] = code_to_index.get("Bu", 0)
        data["greenCostumeIndex"] = code_to_index.get("Gr", 0)

        bowser_files = (bowser_data or {}).get("files") or {}
        files = data.setdefault("files", {})
        for key in (
            "demoFile", "demoWait", "demoResult", "demoIntro", "demoEnding",
            "rstAnimFile", "rstAnimCount", "kirbyCapFileName", "kirbyCapSymbol",
            "kirbyEffectFile", "kirbyEffectSymbol",
        ):
            if bowser_files.get(key) not in (None, ""):
                files[key] = bowser_files[key]

        data["assets"] = {
            "cssIcon": "css\\icon",
            "resultBannerBig": "rst\\big_banner",
            "resultSmallBig": "rst\\small_banner",
        }
        base_costume = json.loads(json.dumps((data.get("costumes") or [{}])[0]))
        base_file = base_costume.setdefault("file", {})
        base_file.setdefault("visibilityIndex", 0)
        base_file.setdefault("jointSymbol", "PlyGkoopa5K_Share_joint")
        base_file.setdefault("materialSymbol", "PlyGkoopa5K_Share_matanim_joint")
        costumes = []
        for index, spec in enumerate(costume_specs):
            costume = json.loads(json.dumps(base_costume))
            costume["name"] = spec["name"]
            costume["colorSmashGroup"] = int(base_costume.get("colorSmashGroup", -132)) - index
            file_info = costume.setdefault("file", {})
            file_info["visibilityIndex"] = 0
            file_info["fileName"] = f"PlGk{spec['code']}.dat"
            file_info["jointSymbol"] = "PlyGkoopa5K_Share_joint"
            file_info["materialSymbol"] = "PlyGkoopa5K_Share_matanim_joint"
            costume["icon"] = None
            costume["csp"] = None
            costumes.append(costume)
        data["costumes"] = costumes
        return data

    def _render_giga_csp(self, dat_path: Path) -> Path | None:
        try:
            import generate_csp as csp_renderer
        except Exception as e:
            logger.warning(f"Giga Bowser CSP renderer unavailable: {e}")
            return None

        try:
            if self.hsdraw_path.exists():
                csp_renderer.HSDRAW_EXE = str(self.hsdraw_path)
            rendered = csp_renderer.generate_csp(str(dat_path))
            if rendered and Path(rendered).exists():
                return Path(rendered)
        except Exception as e:
            logger.warning(f"Giga Bowser CSP render failed: {e}")
        return None

    def _make_giga_stock(self, dat_path, csp_path):
        """Proper Melee-style stock icon for a Giga costume via the stock
        generator. Giga is a model with no vanilla stock asset, so stock_gen
        falls through to its csp-crop path (head crop + 15-colour quantize +
        dark outline) using a bind-pose head-shot of the costume DAT. Falls
        back to a plain CSP downscale only if generation fails. (Previously the
        seed always used the downscale, which shrank the whole-body CSP into an
        illegible 24x24 blob — see docs/CSP_LOWPOLY_HIDING.md.)"""
        csp_bytes = csp_path.read_bytes() if csp_path and csp_path.exists() else None
        if dat_path and Path(dat_path).exists():
            try:
                from skinlab.stock_gen import generate_stock
                from generate_csp import generate_head_shot
                from core.config import VANILLA_ASSETS_DIR
                result = generate_stock(
                    VANILLA_ASSETS_DIR, self.BUILTIN_GIGA_NAME, Path(dat_path).stem,
                    modded_dat_path=str(dat_path), modded_csp=csp_bytes,
                    head_shot_provider=lambda: generate_head_shot(str(dat_path)))
                if result:
                    return result[0]
            except Exception as e:
                logger.warning(f"Giga Bowser stock_gen failed, using CSP downscale: {e}")
        if csp_path and csp_path.exists():
            return self._fit_png(csp_path, (24, 24))
        return None

    @staticmethod
    def _costume_zip_with_dat(
        base_zip_bytes: bytes,
        dat_name: str,
        dat_bytes: bytes,
        csp_bytes: bytes | None = None,
        stock_bytes: bytes | None = None,
    ) -> bytes:
        from io import BytesIO

        out = BytesIO()
        wrote_dat = False
        wrote_csp = False
        wrote_stock = False
        with zipfile.ZipFile(BytesIO(base_zip_bytes), "r") as src, \
                zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
            for item in src.infolist():
                basename = Path(item.filename).name.lower()
                if basename.endswith(".dat"):
                    if not wrote_dat:
                        dst.writestr(dat_name, dat_bytes)
                        wrote_dat = True
                    continue
                if basename == "csp.png":
                    if csp_bytes is not None:
                        dst.writestr("csp.png", csp_bytes)
                        wrote_csp = True
                    continue
                if basename == "stc.png":
                    if stock_bytes is not None:
                        dst.writestr("stc.png", stock_bytes)
                        wrote_stock = True
                    continue
                dst.writestr(item, src.read(item.filename))
            if not wrote_dat:
                dst.writestr(dat_name, dat_bytes)
            if csp_bytes is not None and not wrote_csp:
                dst.writestr("csp.png", csp_bytes)
            if stock_bytes is not None and not wrote_stock:
                dst.writestr("stc.png", stock_bytes)
        return out.getvalue()

    def _run_hsdraw_texture(self, args: list[str | Path], context: str) -> str:
        if not self.hsdraw_path.exists():
            raise FileNotFoundError(f"HSDRawViewer not found at {self.hsdraw_path}")
        result = subprocess.run(
            [str(self.hsdraw_path), *[str(arg) for arg in args]],
            capture_output=True,
            text=True,
            cwd=str(self.project_root),
            **get_subprocess_args(),
        )
        if result.returncode != 0:
            output = "\n".join(
                part for part in (result.stdout, result.stderr) if part
            ).strip()
            tail = output[-2000:] if output else f"exit code {result.returncode}"
            raise RuntimeError(f"{context} failed: {tail}")
        return result.stdout or ""

    def _make_giga_recolor_dat(self, base_dat: Path, out_dat: Path, spec: dict) -> Path:
        import uuid
        import numpy as np
        from PIL import Image
        from skinlab import compose as compose_mod

        # Bundled asset: in a frozen build self.project_root is the user-data dir,
        # so resolve from the PyInstaller bundle (_MEIPASS) there. (Same gotcha as
        # _bundled_giga_icon; without this Giga recolors silently fail in the
        # installed build and Giga ends up with only the Normal costume.)
        rmrel = Path("backend") / "assets" / "texture_regions" / "Bowser.json"
        region_map_path = (
            Path(sys._MEIPASS) / rmrel if getattr(sys, "frozen", False)
            else self.project_root / rmrel
        )
        if not region_map_path.exists():
            region_map_path = self.project_root / rmrel
        with open(region_map_path, "r", encoding="utf-8") as f:
            region_map = json.load(f)
        regions = region_map.get("regions") or {}
        protected = set(region_map.get("protected") or [])

        out_dat.parent.mkdir(parents=True, exist_ok=True)
        work_dir = out_dat.parent / f"{out_dat.stem}_{uuid.uuid4().hex[:8]}_textures"
        work_dir.mkdir(parents=True, exist_ok=True)
        root_joint = "PlyGkoopa5K_Share_joint"
        current_dat = base_dat
        selected_textures = []
        seen_indexes = set()
        for region, params in (spec.get("regions") or {}).items():
            for index in regions.get(region, []):
                index = int(index)
                if index in protected or index in seen_indexes:
                    continue
                selected_textures.append((region, index, params))
                seen_indexes.add(index)

        changed = 0
        try:
            for order, (region, index, params) in enumerate(selected_textures):
                exported_png = work_dir / f"{order:03d}_{index:03d}.png"
                tinted_png = work_dir / f"{order:03d}_{index:03d}_tinted.png"
                next_dat = work_dir / f"{out_dat.stem}_step_{changed + 1:03d}.dat"
                try:
                    self._run_hsdraw_texture(
                        ["--texture", "export", current_dat, root_joint, index, exported_png],
                        f"Giga Bowser {spec['name']} texture {index} export",
                    )
                    with Image.open(exported_png) as image:
                        arr = np.array(image.convert("RGBA"))
                    mask = compose_mod.build_mask(arr)
                    result = compose_mod.tint(
                        arr,
                        mask,
                        hue=float(params["hue"]),
                        saturation=float(params.get("saturation", 60)),
                    )
                    if result is None:
                        continue
                    Image.fromarray(np.asarray(result).astype("uint8"), "RGBA").save(tinted_png)
                    self._run_hsdraw_texture(
                        ["--texture", "import", current_dat, root_joint, index, tinted_png, next_dat],
                        f"Giga Bowser {spec['name']} texture {index} import",
                    )
                    current_dat = next_dat
                    changed += 1
                except Exception as e:
                    logger.warning(
                        "Giga Bowser %s texture %s (%s) recolor skipped: %s",
                        spec["name"],
                        index,
                        region,
                        e,
                    )
            if changed == 0:
                raise RuntimeError(f"no Giga Bowser textures changed for {spec['name']}")
            shutil.copy2(current_dat, out_dat)
        finally:
            shutil.rmtree(work_dir, ignore_errors=True)
        return out_dat

    def _seed_builtin_giga_bowser(self, temp_dir: Path, force: bool = False,
                                  progress_callback=None) -> dict:
        """Seed Giga Bowser into the custom-character vault from vanilla ISO data."""
        n_costumes = len(self.BUILTIN_GIGA_COSTUMES)

        def _seed_progress(pct, message, done=0):
            # Keep the bar visibly moving — the CSP/stock renders below are slow
            # and otherwise sit silently, which looks frozen on first run.
            if progress_callback:
                progress_callback('seeding_builtins', int(pct), message, done, n_costumes)

        storage_dir = self.project_root / "storage"
        char_root = storage_dir / "custom_characters"
        char_dir = char_root / self.BUILTIN_GIGA_SLUG
        metadata = self._read_metadata()
        existing = next(
            (
                c for c in metadata.get("custom_characters", [])
                if c.get("slug") == self.BUILTIN_GIGA_SLUG
                or c.get("name", "").lower() == self.BUILTIN_GIGA_NAME.lower()
            ),
            None,
        )
        if existing and (char_dir / "fighter.zip").exists() and not force:
            existing_is_builtin = (
                existing.get("builtin")
                or existing.get("source") == "builtin"
                or existing.get("slug") == self.BUILTIN_GIGA_SLUG
            )
            if not existing_is_builtin:
                return {
                    "success": True,
                    "seeded": False,
                    "reason": "custom_character_conflict",
                }
            if self._giga_bowser_seed_current(char_dir):
                return {"success": True, "seeded": False, "reason": "already_present"}

        project_path = temp_dir / "temp_project.mexproj"
        if not project_path.exists():
            project_path = temp_dir / "project.mexproj"
        fighters_dir = temp_dir / "data" / "fighters"
        assets_dir = temp_dir / "assets"
        files_dir = temp_dir / "files"
        giga_json = fighters_dir / self.BUILTIN_GIGA_FIGHTER_JSON
        bowser_json = fighters_dir / "005.json"
        if not project_path.exists() or not giga_json.exists():
            return {"success": False, "error": "Giga Bowser fighter data not found in extracted project"}

        with open(giga_json, "r", encoding="utf-8") as f:
            fighter_data = json.load(f)
        bowser_data = None
        if bowser_json.exists():
            with open(bowser_json, "r", encoding="utf-8") as f:
                bowser_data = json.load(f)
        char_dir.mkdir(parents=True, exist_ok=True)
        zip_path = char_dir / "fighter.zip"

        _seed_progress(4, 'Exporting Giga Bowser fighter…')
        cmd = [
            str(self.mexcli_path),
            "export-fighter",
            str(project_path),
            str(self.BUILTIN_GIGA_FIGHTER_INDEX),
            str(zip_path),
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(self.project_root),
            **get_subprocess_args(),
        )
        if result.returncode != 0 or not zip_path.exists():
            return {
                "success": False,
                "error": result.stderr or result.stdout or "mexcli export-fighter failed",
            }

        _seed_progress(10, 'Rendering Giga Bowser portrait…', 1)
        csp_path = self._render_giga_csp(files_dir / "PlGkNr.dat")
        if csp_path is None:
            bowser_csp = self._resolve_asset_png(assets_dir, "csp\\csp_025")
            csp_path = bowser_csp

        costume_assets = [{
            "spec": self.BUILTIN_GIGA_COSTUMES[0],
            "dat_path": files_dir / "PlGkNr.dat",
            "csp_path": csp_path,
        }]
        recolor_dir = temp_dir / "giga_bowser_recolors"
        recolor_dir.mkdir(parents=True, exist_ok=True)
        # Place Giga's ftData (PlGk.dat) beside the recolor costume DATs. The CSP
        # renderer derives the per-character low-poly hide list from a sibling
        # Pl<XX>.dat (_find_ftdata); without it the recolor renders fall back to a
        # wrong scene hide list and drop Giga's hand. The Normal costume renders
        # from files_dir, which already has PlGk.dat as a sibling.
        giga_ftdata = files_dir / "PlGk.dat"
        if giga_ftdata.exists():
            shutil.copy2(giga_ftdata, recolor_dir / "PlGk.dat")
        recolor_specs = self.BUILTIN_GIGA_COSTUMES[1:]
        for ri, spec in enumerate(recolor_specs):
            # Recolor renders are the slow part — spread them across 10–70%.
            done = ri + 2
            pct = 10 + int(60 * (ri / max(1, len(recolor_specs))))
            _seed_progress(pct, f"Rendering {spec['name']} costume ({done}/{n_costumes})…", done)
            try:
                stem = f"PlGk{spec['code']}"
                dat_path = self._make_giga_recolor_dat(
                    files_dir / "PlGkNr.dat",
                    recolor_dir / f"{stem}.dat",
                    spec,
                )
                recolor_csp = self._render_giga_csp(dat_path)
                if recolor_csp is None:
                    recolor_csp = csp_path
                costume_assets.append({
                    "spec": spec,
                    "dat_path": dat_path,
                    "csp_path": recolor_csp,
                })
            except Exception as e:
                logger.warning(f"Giga Bowser {spec['name']} recolor failed: {e}")

        costume_specs = [asset["spec"] for asset in costume_assets]
        fighter_data = self._patch_giga_bowser_fighter_data(
            fighter_data, bowser_data, costume_specs)

        replacements: dict[str, bytes] = {
            "fighter.json": json.dumps(fighter_data, indent=2).encode("utf-8"),
            "big_banner.png": self._make_text_banner((256, 28), "GIGA BOWSER"),
            "small_banner.png": self._make_text_banner((120, 24), "GIGA"),
        }

        has_css_icon = False

        bundled_icon = self._bundled_giga_icon()

        if csp_path and csp_path.exists():
            icon_bytes = (
                bundled_icon.read_bytes()
                if bundled_icon
                else self._fit_png(csp_path, (64, 56))
            )
            replacements["icon.png"] = icon_bytes
            (char_dir / "css_icon.png").write_bytes(icon_bytes)
            has_css_icon = True
        else:
            fallback_icon = bundled_icon or self._resolve_asset_png(assets_dir, "css\\icon_005")
            if fallback_icon:
                icon_bytes = fallback_icon.read_bytes()
                replacements["icon.png"] = icon_bytes
                (char_dir / "css_icon.png").write_bytes(icon_bytes)
                has_css_icon = True

        for key in (
            "fighterDataPath", "animFile", "demoFile", "rstAnimFile",
            "effectFile", "kirbyCapFileName", "kirbyEffectFile",
        ):
            name = (fighter_data.get("files") or {}).get(key)
            if name:
                file_path = files_dir / name
                if file_path.exists():
                    replacements[name] = file_path.read_bytes()

        with zipfile.ZipFile(zip_path, "r") as zf:
            costume_zip = zf.read("PlGkNr.zip")

        costume_meta = []
        for index, asset in enumerate(costume_assets):
            spec = asset["spec"]
            # Stock-icon renders run here — spread across 70–95%.
            _seed_progress(70 + int(25 * (index / max(1, len(costume_assets)))),
                           f"Building {spec['name']} stock icon…", index + 1)
            stem = f"PlGk{spec['code']}"
            csp_asset_path = asset.get("csp_path")
            csp_bytes = csp_asset_path.read_bytes() if csp_asset_path and csp_asset_path.exists() else None
            stock_bytes = self._make_giga_stock(asset.get("dat_path"), csp_asset_path)
            if csp_bytes:
                (char_dir / f"csp_{index}.png").write_bytes(csp_bytes)
            if stock_bytes:
                (char_dir / f"stock_{index}.png").write_bytes(stock_bytes)
            replacements[f"{stem}.zip"] = self._costume_zip_with_dat(
                costume_zip,
                f"{stem}.dat",
                asset["dat_path"].read_bytes(),
                csp_bytes,
                stock_bytes,
            )
            costume_meta.append({
                "id": stem,
                "color": spec["name"],
                "filename": f"{stem}.zip",
                "dat_name": f"{stem}.dat",
                "has_csp": csp_bytes is not None,
                "has_stock": stock_bytes is not None,
            })

        _seed_progress(96, 'Finalizing Giga Bowser…', n_costumes)
        self._zip_with_replacements(zip_path, replacements)

        with open(char_dir / "fighter.json", "w", encoding="utf-8") as f:
            json.dump(fighter_data, f, indent=2)

        costumes_dir = char_dir / "costumes"
        costumes_dir.mkdir(exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zf:
            for index, meta in enumerate(costume_meta):
                (costumes_dir / meta["filename"]).write_bytes(zf.read(meta["filename"]))
                if meta["has_csp"]:
                    shutil.copy2(char_dir / f"csp_{index}.png", costumes_dir / f"{meta['id']}_csp.png")
                if meta["has_stock"]:
                    shutil.copy2(char_dir / f"stock_{index}.png", costumes_dir / f"{meta['id']}_stc.png")

        entry = {
            "slug": self.BUILTIN_GIGA_SLUG,
            "name": self.BUILTIN_GIGA_NAME,
            "source": "builtin",
            "builtin": True,
            "date_added": datetime.now().isoformat(),
            "series_id": fighter_data.get("seriesID", 11),
            "costume_count": len(costume_meta),
            "has_css_icon": has_css_icon,
            "costume_meta": costume_meta,
        }

        chars = metadata.setdefault("custom_characters", [])
        if existing:
            chars[chars.index(existing)] = entry
        else:
            chars.append(entry)
        self._write_metadata(metadata)
        logger.info("Seeded built-in Giga Bowser custom character")
        return {"success": True, "seeded": True}

    def run_setup(
        self,
        iso_path: str,
        progress_callback: Optional[Callable[[str, int, str, int, int], None]] = None
    ) -> dict:
        """
        Run the first-run setup process.

        Args:
            iso_path: Path to the user's vanilla Melee 1.02 ISO
            progress_callback: Callback(phase, percentage, message, completed, total)

        Returns:
            dict with 'success' bool and 'message' or 'error'
        """
        temp_dir = None

        try:
            # Phase 0: Copy bundled assets (production only)
            # Must happen before extraction since PRESERVE_CSP_CHARACTERS skips Sheik
            self._copy_bundled_sheik_assets()
            # Copy bundled sounds (more reliable than extracting from ISO)
            self._copy_bundled_sounds()

            # Create temp directory for MEX project
            temp_dir = Path(tempfile.mkdtemp(prefix='nucleus_setup_'))
            logger.info(f"Created temp directory: {temp_dir}")

            # Phase 1: Extract ISO using mexcli create
            if progress_callback:
                progress_callback('extracting', 0, 'Extracting ISO (this may take 1-2 minutes)...', 0, 100)

            result = self._extract_iso(iso_path, temp_dir, progress_callback)
            if not result['success']:
                return result

            # Phase 2: Copy character assets
            if progress_callback:
                progress_callback('copying_characters', 0, 'Copying character assets...', 0, 100)

            result = self._copy_character_assets(temp_dir, progress_callback)
            if not result['success']:
                return result

            # Phase 2b: Seed built-in custom fighters from the extracted game.
            # Giga Bowser is present in Melee but normally inaccessible; package
            # him into the same vault format as imported m-ex fighters.
            if progress_callback:
                progress_callback('seeding_builtins', 0, 'Seeding built-in custom characters...', 0,
                                  len(self.BUILTIN_GIGA_COSTUMES))
            builtin_result = self._seed_builtin_giga_bowser(
                temp_dir, progress_callback=progress_callback)
            if not builtin_result.get('success'):
                logger.warning(f"Giga Bowser seed failed: {builtin_result.get('error')}")
            elif progress_callback:
                progress_callback('seeding_builtins', 100, 'Seeded built-in custom characters',
                                  len(self.BUILTIN_GIGA_COSTUMES), len(self.BUILTIN_GIGA_COSTUMES))

            # Phase 3: Copy stage images
            if progress_callback:
                progress_callback('copying_stages', 0, 'Copying stage images...', 0, 6)

            result = self._copy_stage_images(temp_dir, progress_callback)
            if not result['success']:
                return result

            # Phase 4: Copy DAT files to csp_data for CSP generation tooling
            if progress_callback:
                progress_callback('copying_csp_data', 0, 'Copying CSP data files...', 0, 100)

            result = self._copy_csp_data_dats(progress_callback)
            if not result['success']:
                logger.warning(f"csp_data DAT copy had issues: {result.get('error')}")
                # Don't fail setup, just warn - these files are supplementary

            # Phase 5: Extract menu sounds from main.ssm
            if progress_callback:
                progress_callback('extracting_sounds', 0, 'Extracting menu sounds...', 0, len(self.MENU_SOUNDS))

            result = self._extract_menu_sounds(temp_dir, progress_callback)
            if not result['success']:
                logger.warning(f"Sound extraction had issues: {result.get('error')}")
                # Don't fail setup, just warn - sounds are supplementary

            # Success
            if progress_callback:
                progress_callback('complete', 100, 'Setup complete!', 100, 100)

            return {
                'success': True,
                'message': 'Vanilla assets extracted successfully',
                'characters': self.VANILLA_FIGHTER_COUNT,
                'builtin_custom_characters': 1 if builtin_result.get('seeded') else 0,
                'stages': len(self.STAGE_ICONS)
            }

        except Exception as e:
            logger.error(f"Setup failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            # Cleanup temp directory
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temp directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp directory: {e}")

    def _get_folder_size(self, folder: Path) -> int:
        """Calculate total size of all files in a folder."""
        total = 0
        try:
            for f in folder.rglob('*'):
                if f.is_file():
                    total += f.stat().st_size
        except Exception:
            pass
        return total

    def _extract_iso(
        self,
        iso_path: str,
        temp_dir: Path,
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """Extract ISO using mexcli create command."""
        try:
            # Run mexcli create
            cmd = [
                str(self.mexcli_path),
                'create',
                iso_path,
                str(temp_dir),
                'temp_project'
            ]

            logger.info(f"Running: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Monitor folder size in background thread for progress
            stop_monitoring = threading.Event()
            current_phase = {'value': 'extracting', 'base_pct': 0}

            def monitor_size():
                phase_ticks = {'installing': 0, 'saving': 0}
                while not stop_monitoring.is_set():
                    size = self._get_folder_size(temp_dir)
                    size_mb = size // (1024 * 1024)

                    phase = current_phase['value']

                    if phase == 'extracting':
                        # Extraction: 0-70% based on folder size
                        pct = min(70, int((size / self.EXPECTED_EXTRACTION_SIZE) * 70))
                    elif phase == 'installing':
                        # Installing: 70-85%, increment over time
                        phase_ticks['installing'] += 1
                        pct = min(85, 70 + phase_ticks['installing'])
                    elif phase == 'saving':
                        # Saving: 85-95%, increment over time
                        phase_ticks['saving'] += 1
                        pct = min(95, 85 + phase_ticks['saving'])
                    else:
                        pct = 100

                    if progress_callback and phase != 'complete':
                        msg = {
                            'extracting': f'Extracting ISO files... ({size_mb} MB)',
                            'installing': f'Installing MEX framework... ({size_mb} MB)',
                            'saving': 'Finalizing project...'
                        }.get(phase, 'Processing...')
                        progress_callback('extracting', pct, msg, pct, 100)

                    time.sleep(0.3)

            monitor_thread = threading.Thread(target=monitor_size, daemon=True)
            monitor_thread.start()

            # Collect all output for logging
            stdout_lines = []

            # Read output line by line for phase changes
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue

                # Save all output for error logging
                stdout_lines.append(line)
                logger.info(f"mexcli output: {line}")

                try:
                    data = json.loads(line)
                    status = data.get('status', '')

                    if status == 'installing':
                        current_phase['value'] = 'installing'
                        current_phase['base_pct'] = 70
                    elif status == 'saving':
                        current_phase['value'] = 'saving'
                        current_phase['base_pct'] = 85
                    elif status == 'complete':
                        current_phase['value'] = 'complete'
                        if progress_callback:
                            progress_callback('extracting', 100, 'Extraction complete', 100, 100)

                except json.JSONDecodeError:
                    # Not JSON, just regular output
                    pass

            process.wait()
            stop_monitoring.set()
            monitor_thread.join(timeout=1)

            if process.returncode != 0:
                stderr = process.stderr.read()
                stdout_text = '\n'.join(stdout_lines)
                logger.error(f"mexcli failed with return code {process.returncode}")
                logger.error(f"mexcli stdout: {stdout_text}")
                logger.error(f"mexcli stderr: {stderr}")
                return {
                    'success': False,
                    'error': f'mexcli create failed (code {process.returncode}): {stdout_text or stderr}'
                }

            # Verify extraction produced expected files
            data_dir = temp_dir / 'data' / 'fighters'
            if not data_dir.exists():
                return {
                    'success': False,
                    'error': 'Extraction did not produce expected fighter data'
                }

            return {'success': True}

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to extract ISO: {e}'
            }

    def _copy_character_assets(
        self,
        temp_dir: Path,
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """Copy character assets from extracted temp project to vanilla dir."""
        try:
            # Ensure vanilla directory exists
            self.vanilla_dir.mkdir(parents=True, exist_ok=True)

            # Read fighter JSONs
            data_dir = temp_dir / 'data' / 'fighters'
            assets_dir = temp_dir / 'assets'
            files_dir = temp_dir / 'files'

            total_costumes = 0
            completed_costumes = 0

            # First pass: count total costumes
            for i in range(self.VANILLA_FIGHTER_COUNT):
                json_path = data_dir / f'{i:03d}.json'
                if json_path.exists():
                    with open(json_path, 'r') as f:
                        fighter_data = json.load(f)
                    total_costumes += len(fighter_data.get('costumes', []))

            # Second pass: copy assets
            for i in range(self.VANILLA_FIGHTER_COUNT):
                json_path = data_dir / f'{i:03d}.json'
                if not json_path.exists():
                    logger.warning(f"Fighter JSON not found: {json_path}")
                    continue

                with open(json_path, 'r') as f:
                    fighter_data = json.load(f)

                char_name = fighter_data.get('name', f'Unknown_{i}')
                char_dir = self.vanilla_dir / char_name
                char_dir.mkdir(parents=True, exist_ok=True)

                # Copy CSS icon (character select screen icon)
                css_icon_ref = fighter_data.get('assets', {}).get('cssIcon', '')
                if css_icon_ref:
                    # Convert "css\\icon" to "css/icon.png"
                    css_icon_path = assets_dir / (css_icon_ref.replace('\\', '/') + '.png')
                    if css_icon_path.exists():
                        shutil.copy2(css_icon_path, char_dir / 'css_icon.png')

                # Copy animation archive (PlXxAJ.dat)
                anim_file = fighter_data.get('files', {}).get('animFile', '')
                if anim_file:
                    anim_path = files_dir / anim_file
                    if anim_path.exists():
                        shutil.copy2(anim_path, char_dir / anim_file)

                # Copy costumes
                for costume in fighter_data.get('costumes', []):
                    costume_file = costume.get('file', {}).get('fileName', '')
                    if not costume_file:
                        continue

                    # Create costume folder (e.g., PlMrNr)
                    costume_code = Path(costume_file).stem
                    costume_dir = char_dir / costume_code
                    costume_dir.mkdir(parents=True, exist_ok=True)

                    # Copy DAT file
                    dat_path = files_dir / costume_file
                    if dat_path.exists():
                        shutil.copy2(dat_path, costume_dir / costume_file)

                    # Check for asset overrides (e.g., Mr. Game & Watch has wrong mappings)
                    char_overrides = self.ASSET_OVERRIDES.get(char_name, {})
                    costume_overrides = char_overrides.get(costume_code, {})

                    # Copy CSP (skip for characters with preserved CSPs in git)
                    if char_name not in self.PRESERVE_CSP_CHARACTERS:
                        csp_ref = costume_overrides.get('csp') or costume.get('csp', '')
                        if csp_ref:
                            csp_path = assets_dir / (csp_ref.replace('\\', '/') + '.png')
                            if csp_path.exists():
                                shutil.copy2(csp_path, costume_dir / 'csp.png')

                    # Copy stock icon
                    icon_ref = costume_overrides.get('icon') or costume.get('icon', '')
                    if icon_ref:
                        icon_path = assets_dir / (icon_ref.replace('\\', '/') + '.png')
                        if icon_path.exists():
                            shutil.copy2(icon_path, costume_dir / 'stock.png')

                    completed_costumes += 1

                    if progress_callback:
                        pct = int((completed_costumes / total_costumes) * 100)
                        progress_callback(
                            'copying_characters',
                            pct,
                            f'Copying {char_name} - {costume.get("name", costume_code)}',
                            completed_costumes,
                            total_costumes
                        )

            return {'success': True}

        except Exception as e:
            logger.error(f"Failed to copy character assets: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to copy character assets: {e}'
            }

    def _copy_stage_images(
        self,
        temp_dir: Path,
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """Copy stage images from extracted temp project."""
        try:
            # Ensure stages directory exists
            self.stages_dir.mkdir(parents=True, exist_ok=True)

            sss_dir = temp_dir / 'assets' / 'sss'

            completed = 0
            for src_name, dst_name in self.STAGE_ICONS.items():
                src_path = sss_dir / src_name
                dst_path = self.stages_dir / dst_name

                if src_path.exists():
                    shutil.copy2(src_path, dst_path)
                    logger.info(f"Copied stage: {src_name} -> {dst_name}")
                else:
                    logger.warning(f"Stage icon not found: {src_path}")

                completed += 1

                if progress_callback:
                    pct = int((completed / len(self.STAGE_ICONS)) * 100)
                    progress_callback(
                        'copying_stages',
                        pct,
                        f'Copying {dst_name}',
                        completed,
                        len(self.STAGE_ICONS)
                    )

            return {'success': True}

        except Exception as e:
            logger.error(f"Failed to copy stage images: {e}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to copy stage images: {e}'
            }

    def _copy_csp_data_dats(
        self,
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """Copy vanilla DAT files to csp_data directory for CSP generation tooling."""
        try:
            if not self.csp_data_dir.exists():
                logger.warning("csp_data directory does not exist, skipping DAT copy")
                return {'success': True}

            copied = 0
            total = sum(len(v) for v in self.CSP_DATA_DAT_MAPPING.values())

            for csp_folder, mappings in self.CSP_DATA_DAT_MAPPING.items():
                dest_folder = self.csp_data_dir / csp_folder
                if not dest_folder.exists():
                    logger.debug(f"Skipping {csp_folder} - folder doesn't exist")
                    continue

                for mapping in mappings:
                    vanilla_char, costume_code = mapping
                    src_dir = self.vanilla_dir / vanilla_char / costume_code
                    src_path = None
                    for ext in ('.dat', '.usd'):
                        candidate = src_dir / f"{costume_code}{ext}"
                        if candidate.exists():
                            src_path = candidate
                            break

                    dest_path = dest_folder / f"{costume_code}.dat"

                    if src_path and src_path.exists():
                        shutil.copy2(src_path, dest_path)
                        logger.debug(f"Copied {costume_code}.dat to csp_data/{csp_folder}/")
                    else:
                        logger.warning(f"Source not found: {src_path}")

                    copied += 1
                    if progress_callback:
                        pct = int((copied / total) * 100)
                        progress_callback('copying_csp_data', pct, f'Copying {costume_code}.dat', copied, total)

            logger.info(f"Copied {copied} DAT files to csp_data")
            return {'success': True}

        except Exception as e:
            logger.error(f"Failed to copy csp_data DATs: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    def _extract_menu_sounds(
        self,
        temp_dir: Path,
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """Extract menu sounds from main.ssm using HSDRawViewer."""
        try:
            # Find main.ssm in the extracted ISO
            main_ssm = temp_dir / 'files' / 'audio' / 'us' / 'main.ssm'
            if not main_ssm.exists():
                # Try alternate location
                main_ssm = temp_dir / 'files' / 'audio' / 'main.ssm'

            if not main_ssm.exists():
                logger.warning(f"main.ssm not found in extracted ISO")
                return {'success': False, 'error': 'main.ssm not found'}

            # Check if HSDRawViewer exists
            if not self.hsdraw_path.exists():
                # Try Debug build
                debug_path = self.hsdraw_path.parent.parent.parent / "Debug" / "net6.0-windows" / "HSDRawViewer.exe"
                if debug_path.exists():
                    self.hsdraw_path = debug_path
                else:
                    logger.warning(f"HSDRawViewer not found at {self.hsdraw_path}")
                    return {'success': False, 'error': 'HSDRawViewer.exe not found'}

            # Ensure sounds directory exists
            self.sounds_dir.mkdir(parents=True, exist_ok=True)

            # Create JSON mapping file for sound names
            names_json = self.sounds_dir / 'menu_sounds.json'
            with open(names_json, 'w') as f:
                json.dump({str(k): v for k, v in self.MENU_SOUNDS.items()}, f, indent=2)

            # Run HSDRawViewer to extract sounds
            cmd = [
                str(self.hsdraw_path),
                '--sound', 'extract',
                str(main_ssm),
                str(self.sounds_dir),
                '--names', str(names_json)
            ]

            logger.info(f"Running: {' '.join(cmd)}")

            if progress_callback:
                progress_callback('extracting_sounds', 10, 'Extracting sounds from main.ssm...', 1, len(self.MENU_SOUNDS))

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                **get_subprocess_args()
            )

            if result.returncode != 0:
                logger.error(f"HSDRawViewer failed: {result.stderr}")
                return {'success': False, 'error': f'Sound extraction failed: {result.stderr}'}

            # Remove numbered sound files, keep only named ones
            for f in self.sounds_dir.glob('sound_*.wav'):
                f.unlink()

            # Verify we got the sounds we wanted
            extracted_count = 0
            for name in self.MENU_SOUNDS.values():
                sound_file = self.sounds_dir / f'{name}.wav'
                if sound_file.exists():
                    extracted_count += 1

            if progress_callback:
                progress_callback('extracting_sounds', 100, f'Extracted {extracted_count} menu sounds', extracted_count, len(self.MENU_SOUNDS))

            logger.info(f"Extracted {extracted_count}/{len(self.MENU_SOUNDS)} menu sounds")
            return {'success': True, 'extracted': extracted_count}

        except subprocess.TimeoutExpired:
            logger.error("Sound extraction timed out")
            return {'success': False, 'error': 'Sound extraction timed out'}
        except Exception as e:
            logger.error(f"Failed to extract menu sounds: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}
