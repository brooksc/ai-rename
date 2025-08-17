"""File operation utilities."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from loguru import logger

from src.core.exceptions import FileOperationError
from src.core.security import SecurityError, SystemPathValidator


@dataclass
class FileOperationConfig:
    """Configuration for file operations."""

    # File handling
    follow_symlinks: bool = False
    skip_system_files: bool = True
    preserve_metadata: bool = True

    # Text extraction
    max_text_length: int = 10000
    preview_length: int = 1000

    # Protected paths and patterns
    protected_paths: set[str] = field(default_factory=set)
    protected_patterns: set[str] = field(default_factory=set)
    system_patterns: set[str] = field(default_factory=set)
    allow_hidden: bool = False

    # Backup settings
    backup_dir: Path | None = None
    create_backups: bool = True

    def create_validator(self) -> SystemPathValidator:
        """Create a path validator with current configuration.

        Returns:
            SystemPathValidator: Configured validator instance
        """
        return SystemPathValidator(
            custom_protected_paths=self.protected_paths,
            custom_protected_patterns=self.protected_patterns,
            custom_system_patterns=self.system_patterns,
            allow_hidden=self.allow_hidden,
            skip_system_files=self.skip_system_files,
            follow_symlinks=self.follow_symlinks
        )

def is_system_file(path: Path, patterns: set[str] | None = None) -> bool:
    """Check if a file is a system file.

    Args:
        path: Path to check
        patterns: Additional patterns to consider

    Returns:
        bool: True if file is a system file
    """
    # Default system file patterns
    default_patterns = {
        '.DS_Store',  # macOS
        'Thumbs.db',  # Windows
        'desktop.ini',
        '~$',        # Temp files
        '$~',        # Temp files
    }

    if patterns:
        default_patterns.update(patterns)

    # Check name against patterns
    name = path.name
    if any(name.startswith(p) or name.endswith(p) for p in default_patterns):
        return True

    # Check if file has system attribute (Windows)
    try:
        if os.name == 'nt' and path.stat().st_file_attributes & 0x4:
            return True
    except OSError as e:
        logger.debug(f"Failed to check system file attributes: {e}")
        return False

    return False

def validate_new_path(src_path: Path, dst_path: Path) -> None:
    """Validate a new file path.

    Args:
        src_path: Source file path
        dst_path: Destination file path

    Raises:
        FileOperationError: If path is invalid
    """
    # Check if source exists
    if not src_path.exists():
        raise FileOperationError(f"Source file does not exist: {src_path}")

    # Check if destination exists
    if dst_path.exists():
        raise FileOperationError(f"Destination already exists: {dst_path}")

    # Check if destination parent exists
    if not dst_path.parent.exists():
        raise FileOperationError(f"Destination directory does not exist: {dst_path.parent}")

    # Check if destination is writable
    try:
        if not os.access(dst_path.parent, os.W_OK):
            raise FileOperationError(f"Destination directory is not writable: {dst_path.parent}")
    except OSError as e:
        raise FileOperationError(f"Failed to check destination permissions: {e}") from e

    # Check for circular references
    try:
        if dst_path.is_symlink() and dst_path.resolve() == src_path.resolve():
            raise FileOperationError("Circular symlink reference detected")
    except OSError as e:
        raise FileOperationError(f"Failed to resolve paths: {e}") from e

def check_destination_permissions(dst_path: Path) -> None:
    """Check if we have permission to write to the destination."""
    try:
        if not dst_path.parent.exists():
            raise FileOperationError(f"Destination directory does not exist: {dst_path.parent}")
        if not os.access(dst_path.parent, os.W_OK):
            raise FileOperationError(f"Destination directory is not writable: {dst_path.parent}")
    except OSError as e:
        raise FileOperationError(f"Failed to check destination permissions: {e}") from e

    # Check for circular references
    try:
        if dst_path.exists() and dst_path.resolve() == dst_path.parent.resolve():
            raise FileOperationError("Circular symlink reference detected")
    except OSError as e:
        raise FileOperationError(f"Failed to resolve paths: {e}") from e

def check_circular_reference(src: Path, dst: Path) -> None:
    """Check for circular symlink references."""
    try:
        if src.resolve() == dst.resolve():
            raise FileOperationError("Circular symlink reference detected")
    except OSError as e:
        raise FileOperationError(f"Failed to resolve paths: {e}") from e

def safe_rename(src: Path, dst: Path, config: FileOperationConfig | None = None) -> None:
    """Safely rename a file with error handling."""
    try:
        # Perform actual rename
        os.rename(src, dst)
    except OSError:
        raise
    except (ValueError, TypeError) as e:
        raise OSError(f"Invalid path parameters for rename: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during rename: {e}")
        raise OSError(f"Unexpected rename failure {src} to {dst}: {e}") from e

def get_unique_path(path: Path) -> Path:
    """Get a unique path by appending a number if needed.

    Args:
        path: Desired path

    Returns:
        Path: Unique path that doesn't exist
    """
    if not path.exists():
        return path

    counter = 1
    while True:
        new_path = path.parent / f"{path.stem}_{counter}{path.suffix}"
        if not new_path.exists():
            return new_path
        counter += 1

def is_safe_destination(path: Path) -> bool:
    """Check if path is safe for writing.

    Args:
        path: Path to check

    Returns:
        bool: True if path is safe
    """
    try:
        validator = SystemPathValidator()
        return validator.is_safe_path(path)
    except SecurityError:
        return False
