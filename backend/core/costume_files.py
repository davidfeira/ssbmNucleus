"""
Helpers for locating costume archives across the backend.

Most costume archives are ``.dat`` files. Captain Falcon's red costume can
also appear as ``.usd`` while still behaving like a normal character costume.
"""

from pathlib import Path
from typing import Iterable, Optional


COSTUME_ARCHIVE_EXTENSIONS = ('.dat', '.usd')


def is_costume_archive_filename(filename: str) -> bool:
    """Return True if the ZIP entry / path looks like a character costume archive."""
    if not filename or filename.endswith('/') or filename.startswith('__MACOSX'):
        return False

    path = Path(filename)
    return (
        path.suffix.lower() in COSTUME_ARCHIVE_EXTENSIONS
        and path.stem.lower().startswith('pl')
    )


def get_costume_archive_extension(filename: str, default: str = '.dat') -> str:
    """Return the costume archive extension for a filename, defaulting to .dat."""
    suffix = Path(filename).suffix.lower()
    return suffix if suffix in COSTUME_ARCHIVE_EXTENSIONS else default


def list_costume_archive_names(filenames: Iterable[str]) -> list[str]:
    """Return all filenames that look like costume archives."""
    return [name for name in filenames if is_costume_archive_filename(name)]


def find_costume_archive_name(filenames: Iterable[str]) -> Optional[str]:
    """Return the first costume archive filename from an iterable of names."""
    for name in filenames:
        if is_costume_archive_filename(name):
            return name
    return None


def find_extracted_costume_archive(root: Path) -> Optional[Path]:
    """Find the first costume archive inside an extracted ZIP directory."""
    if not root.exists():
        return None

    for path in sorted(root.rglob('*')):
        relative_name = path.relative_to(root).as_posix()
        if path.is_file() and is_costume_archive_filename(relative_name):
            return path
    return None


def find_vanilla_costume_archive(costume_dir: Path, costume_code: str) -> Optional[Path]:
    """Find a vanilla costume archive by code within a costume directory."""
    for ext in COSTUME_ARCHIVE_EXTENSIONS:
        candidate = costume_dir / f"{costume_code}{ext}"
        if candidate.exists():
            return candidate
    return None
