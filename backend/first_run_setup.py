"""
First-run setup module for extracting vanilla assets from user's Melee ISO.

This module handles:
1. Extracting the user's vanilla Melee 1.02 ISO using mexcli
2. Reading fighter JSONs to get asset mappings
3. Copying DATs, CSPs, stocks, CSS icons to utility/assets/vanilla/
4. Copying stage images to utility/assets/stages/
"""

import json
import shutil
import subprocess
import tempfile
import logging
import threading
import time
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class FirstRunSetup:
    """Handles first-run setup: extracting vanilla assets from user's Melee ISO."""

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
        char_folders = [d for d in self.vanilla_dir.iterdir() if d.is_dir()]
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

            # Phase 3: Copy stage images
            if progress_callback:
                progress_callback('copying_stages', 0, 'Copying stage images...', 0, 6)

            result = self._copy_stage_images(temp_dir, progress_callback)
            if not result['success']:
                return result

            # Success
            if progress_callback:
                progress_callback('complete', 100, 'Setup complete!', 100, 100)

            return {
                'success': True,
                'message': 'Vanilla assets extracted successfully',
                'characters': self.VANILLA_FIGHTER_COUNT,
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

            # Read output line by line for phase changes
            for line in process.stdout:
                line = line.strip()
                if not line:
                    continue

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
                    pass

            process.wait()
            stop_monitoring.set()
            monitor_thread.join(timeout=1)

            if process.returncode != 0:
                stderr = process.stderr.read()
                return {
                    'success': False,
                    'error': f'mexcli create failed: {stderr}'
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
                    costume_code = costume_file.replace('.dat', '')
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
