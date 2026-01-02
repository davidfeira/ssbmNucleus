"""
Texture Pack Generation Module

Generates base-4 color encoded placeholder CSPs for texture pack mode,
and watches Dolphin's dump folder to decode and copy high-res textures.

Uses a 16x16 image with finder markers and 7 data cells to encode
costume indices up to 16,384 (4^7).
"""

import io
import json
import shutil
import threading
import time
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, List, Tuple, Dict
from PIL import Image

logger = logging.getLogger(__name__)

# =============================================================================
# Base-4 Color Encoding System
# =============================================================================

# Data colors (at corners of RGB cube for max distinction)
DATA_COLORS = [
    (0, 0, 0, 255),        # 0 = BLACK
    (255, 0, 0, 255),      # 1 = RED
    (0, 255, 0, 255),      # 2 = GREEN
    (0, 0, 255, 255),      # 3 = BLUE
]

# Finder marker colors (unique combo to identify our placeholders)
FINDER_COLORS = {
    'M1': (255, 255, 255, 255),  # WHITE
    'M2': (255, 0, 255, 255),    # MAGENTA
    'M3': (0, 255, 255, 255),    # CYAN
    'M4': (255, 255, 0, 255),    # YELLOW
}

GRAY = (128, 128, 128, 255)

# Layout: 4x4 grid of cells
# [M1][M2][D6][D5]
# [M3][D4][D3][D2]
# [  ][D1][D0][  ]
# [  ][  ][  ][M4]

DATA_POSITIONS = [
    (0, 2), (0, 3),        # D6, D5
    (1, 1), (1, 2), (1, 3),  # D4, D3, D2
    (2, 1), (2, 2)         # D1, D0
]

FINDER_POSITIONS = {
    'M1': (0, 0),
    'M2': (0, 1),
    'M3': (1, 0),
    'M4': (3, 3),
}


def generate_encoded_placeholder(index: int, size: int = 16) -> Image.Image:
    """
    Generate a 16x16 placeholder with base-4 encoded index.

    Uses 7 data cells to encode values 0-16383 (4^7).
    Finder markers in corners identify this as our placeholder.

    Args:
        index: Costume index (0-16383)
        size: Image size (default 16x16)

    Returns:
        PIL Image object
    """
    img = Image.new('RGBA', (size, size), GRAY)
    cell = size // 4

    def fill_cell(row: int, col: int, color: Tuple[int, int, int, int]):
        for y in range(row * cell, (row + 1) * cell):
            for x in range(col * cell, (col + 1) * cell):
                img.putpixel((x, y), color)

    # Draw finder markers
    for name, (row, col) in FINDER_POSITIONS.items():
        fill_cell(row, col, FINDER_COLORS[name])

    # Encode index in base-4 across 7 cells (D6 to D0)
    for i, (row, col) in enumerate(DATA_POSITIONS):
        digit = (index >> (2 * (6 - i))) & 3
        fill_cell(row, col, DATA_COLORS[digit])

    return img


def save_encoded_placeholder(index: int, output_path: Path, size: int = 16) -> None:
    """
    Generate and save an encoded placeholder to disk.

    Args:
        index: Costume index (0-16383)
        output_path: Path to save the PNG
        size: Image size (default 16x16)
    """
    img = generate_encoded_placeholder(index, size)
    img.save(output_path, format='PNG')
    logger.debug(f"Saved encoded placeholder index={index} to {output_path}")


def decode_placeholder(img: Image.Image) -> Optional[int]:
    """
    Decode a dumped texture to extract the costume index.

    Verifies finder pattern first, then reads 7 base-4 data cells.

    Args:
        img: PIL Image (scaled up from 16x16 by Dolphin)

    Returns:
        Costume index (0-16383) or None if not our placeholder
    """
    cell_w = img.width // 4
    cell_h = img.height // 4

    def get_pixel(row: int, col: int) -> Tuple[int, int, int]:
        """Sample center of cell."""
        cx = col * cell_w + cell_w // 2
        cy = row * cell_h + cell_h // 2
        pixel = img.getpixel((cx, cy))
        return pixel[:3] if isinstance(pixel, tuple) else (pixel, pixel, pixel)

    def is_finder_match(row: int, col: int, expected: Tuple[int, int, int, int]) -> bool:
        """Check if cell matches expected finder color (with tolerance)."""
        r, g, b = get_pixel(row, col)
        er, eg, eb = expected[:3]
        return abs(r - er) < 80 and abs(g - eg) < 80 and abs(b - eb) < 80

    # Verify finder pattern
    for name, (row, col) in FINDER_POSITIONS.items():
        if not is_finder_match(row, col, FINDER_COLORS[name]):
            return None  # Not our placeholder

    def decode_data_color(row: int, col: int) -> int:
        """Decode a data cell to base-4 digit (0-3)."""
        r, g, b = get_pixel(row, col)

        # Check which color it's closest to
        if r < 80 and g < 80 and b < 80:
            return 0  # BLACK
        if r > 180 and g < 80 and b < 80:
            return 1  # RED
        if r < 80 and g > 180 and b < 80:
            return 2  # GREEN
        if r < 80 and g < 80 and b > 180:
            return 3  # BLUE

        # Fallback: find closest by dominant channel
        if r >= g and r >= b:
            return 1  # RED
        if g >= r and g >= b:
            return 2  # GREEN
        if b >= r and b >= g:
            return 3  # BLUE
        return 0  # BLACK

    # Read 7 base-4 digits (D6 to D0)
    index = 0
    for i, (row, col) in enumerate(DATA_POSITIONS):
        digit = decode_data_color(row, col)
        index |= (digit << (2 * (6 - i)))

    return index


# Legacy function for compatibility - redirects to new system
def save_placeholder_csp(color: Tuple[int, int, int], output_path: Path, size: Tuple[int, int] = (16, 16)) -> None:
    """Legacy function - use save_encoded_placeholder instead."""
    # This shouldn't be called anymore, but keep for safety
    logger.warning("save_placeholder_csp called - should use save_encoded_placeholder")
    img = Image.new('RGBA', size, (*color, 255))
    img.save(output_path, format='PNG')


@dataclass
class CostumeMapping:
    """Maps a placeholder index to a costume's real CSP."""
    index: int                    # Global costume index (encoded in placeholder)
    character: str                # Character name
    costume_index: int            # Costume index within character
    skin_id: str                  # Storage skin ID (for lookup)
    real_csp_path: str            # Path to the actual high-res CSP
    matched: bool = False         # Whether texture was matched
    dumped_filename: Optional[str] = None  # TEX_0x... filename when matched


@dataclass
class TexturePackMapping:
    """Tracks all costume placeholders for a texture pack build."""
    build_id: str                 # Unique build identifier
    build_name: str               # ISO filename (without .iso)
    created_at: str               # ISO timestamp
    costumes: List[Dict] = field(default_factory=list)

    def add_costume(self, costume: CostumeMapping) -> None:
        """Add a costume mapping."""
        self.costumes.append(asdict(costume))

    def find_by_index(self, index: int) -> Optional[Dict]:
        """
        Find a costume mapping by its encoded index.

        Args:
            index: Decoded index from placeholder (0-16383)

        Returns:
            Costume mapping dict if found, None otherwise
        """
        for costume in self.costumes:
            if costume['index'] == index:
                return costume
        return None

    # Keep legacy method for backwards compatibility
    def find_by_color(self, color: Tuple[int, int, int], tolerance: int = 15) -> Optional[Dict]:
        """Legacy method - use find_by_index instead."""
        logger.warning("find_by_color called - should use find_by_index")
        return None

    def get_unmatched_count(self) -> int:
        """Return count of costumes not yet matched."""
        return sum(1 for c in self.costumes if not c['matched'])

    def get_matched_count(self) -> int:
        """Return count of costumes already matched."""
        return sum(1 for c in self.costumes if c['matched'])

    def save(self, output_path: Path) -> None:
        """Save mapping to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> 'TexturePackMapping':
        """Load mapping from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(
            build_id=data['build_id'],
            build_name=data['build_name'],
            created_at=data['created_at'],
            costumes=data.get('costumes', [])
        )


class TexturePackWatcher:
    """
    Watches Dolphin's dump folder for placeholder textures and copies
    high-res CSPs to the load folder.
    """

    def __init__(
        self,
        dump_path: Path,
        load_path: Path,
        mapping: TexturePackMapping,
        on_match: Optional[Callable[[Dict], None]] = None,
        on_progress: Optional[Callable[[int, int], None]] = None,
        poll_interval: float = 0.5
    ):
        """
        Initialize the texture pack watcher.

        Args:
            dump_path: Dolphin's texture dump directory
            load_path: Dolphin's texture load directory
            mapping: TexturePackMapping with color-to-costume mappings
            on_match: Callback when a texture is matched (receives costume dict)
            on_progress: Callback for progress updates (matched_count, total_count)
            poll_interval: Seconds between directory polls
        """
        self.dump_path = dump_path
        self.load_path = load_path
        self.mapping = mapping
        self.on_match = on_match
        self.on_progress = on_progress
        self.poll_interval = poll_interval

        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.seen_files: set = set()

    def start(self) -> None:
        """Start watching for dumped textures."""
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        logger.info(f"Texture pack watcher started. Monitoring: {self.dump_path}")

    def stop(self) -> None:
        """Stop watching and clean up."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None
        logger.info("Texture pack watcher stopped")

    def _watch_loop(self) -> None:
        """Poll dump directory for new texture files."""
        # Log on first iteration
        first_run = True
        while self.running:
            try:
                if first_run:
                    logger.info(f"Watcher polling dump_path: {self.dump_path}")
                    logger.info(f"  dump_path exists: {self.dump_path.exists()}")
                    if self.dump_path.exists():
                        files = list(self.dump_path.glob("*.png"))
                        logger.info(f"  PNG files found: {len(files)}")
                        for f in files[:5]:  # Show first 5
                            logger.info(f"    - {f.name}")
                    first_run = False
                self._check_for_new_textures()
            except Exception as e:
                logger.error(f"Texture watcher error: {e}", exc_info=True)
            time.sleep(self.poll_interval)

    def _check_for_new_textures(self) -> None:
        """Check for new dumped textures and match them using base-4 decoding."""
        if not self.dump_path.exists():
            return

        # Look for PNG files that might be dumped textures
        # Dolphin dumps with pattern: tex1_WxH_hash_hash_#.png
        for tex_file in self.dump_path.glob("*.png"):
            if tex_file.name in self.seen_files:
                continue

            self.seen_files.add(tex_file.name)

            # Skip if it doesn't look like a Dolphin texture dump
            # Dolphin uses patterns like: tex1_136x188_cbdd7d7201f3e390_9a1111f167d5ff4e_9.png
            if not tex_file.name.startswith('tex'):
                logger.debug(f"Skipping non-texture file: {tex_file.name}")
                continue

            logger.debug(f"Processing texture dump: {tex_file.name}")

            # Try to decode placeholder using base-4 encoding
            try:
                with Image.open(tex_file) as img:
                    index = decode_placeholder(img)
            except Exception as e:
                logger.error(f"Failed to read texture {tex_file}: {e}")
                continue

            if index is None:
                # Not our placeholder (finder pattern didn't match)
                logger.debug(f"  -> Not a placeholder (finder pattern not found)")
                continue

            logger.info(f"  -> Decoded index: {index}")

            # Match to costume by index
            costume = self.mapping.find_by_index(index)
            if costume and not costume['matched']:
                logger.info(f"  -> MATCH: {costume['character']} costume {costume['costume_index']}")
                self._process_match(costume, tex_file)
            elif costume and costume['matched']:
                logger.debug(f"  -> Already matched: {costume['character']}")
            else:
                logger.warning(f"  -> No costume found for index {index}")

    def _process_match(self, costume: Dict, dumped_file: Path) -> None:
        """Copy real CSP to Load folder with correct filename."""
        try:
            # Create build-specific subdirectory
            load_subdir = self.load_path / self.mapping.build_name
            load_subdir.mkdir(parents=True, exist_ok=True)

            # Copy real CSP with dumped texture's filename
            dest_file = load_subdir / dumped_file.name
            real_csp_path = costume['real_csp_path']
            original_path = real_csp_path

            # Convert Windows path to WSL path if needed
            import os
            if os.name != 'nt' and real_csp_path and len(real_csp_path) >= 2 and real_csp_path[1] == ':':
                drive_letter = real_csp_path[0].lower()
                rest_of_path = real_csp_path[2:].replace('\\', '/')
                real_csp_path = f'/mnt/{drive_letter}{rest_of_path}'
                logger.info(f"Converted path: {original_path} -> {real_csp_path}")

            real_csp = Path(real_csp_path)

            if not real_csp.exists():
                logger.warning(f"Real CSP not found: {real_csp}")
                return

            shutil.copy2(real_csp, dest_file)

            # Update mapping
            costume['matched'] = True
            costume['dumped_filename'] = dumped_file.name

            logger.info(f"Matched texture: {costume['character']} costume {costume['costume_index']} -> {dumped_file.name}")

            # Notify callbacks
            if self.on_match:
                self.on_match(costume)

            if self.on_progress:
                matched = self.mapping.get_matched_count()
                total = len(self.mapping.costumes)
                self.on_progress(matched, total)

        except Exception as e:
            logger.error(f"Failed to process match for {costume['character']}: {e}", exc_info=True)

    def get_status(self) -> Dict:
        """Get current watcher status."""
        return {
            'running': self.running,
            'matched_count': self.mapping.get_matched_count(),
            'total_count': len(self.mapping.costumes),
            'seen_files': len(self.seen_files)
        }
