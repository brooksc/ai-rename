"""Name collision handling and path generation."""

import re
from pathlib import Path


class NameCollisionHandler:
    """Handles file name collisions."""

    def __init__(self, auto_number: bool = True, max_attempts: int = 100):
        """Initialize handler.

        Args:
            auto_number: Whether to automatically number duplicates
            max_attempts: Maximum attempts to find unique name
        """
        self.auto_number = auto_number
        self.max_attempts = max_attempts
        self.collision_counts = {}
        self.used_paths: set[Path] = set()

    def clear(self) -> None:
        """Clear used paths cache."""
        self.used_paths.clear()

    def add_existing(self, path: Path) -> None:
        """Add existing path to used paths.

        Args:
            path: Path to add
        """
        self.used_paths.add(path)

    def _split_numbered_name(self, name: str) -> tuple[str, int | None, str]:
        """Split a filename into base, number, and extension.

        Args:
            name: Filename to split

        Returns:
            tuple: (base_name, number, extension)
        """
        # Match pattern: base_name (n).ext or base_name.ext
        pattern = r"^(.+?)(?:\s*\((\d+)\))?((?:\.[^.]+)?)$"
        match = re.match(pattern, name)

        if not match:
            # Fallback: split extension only
            base = Path(name).stem
            ext = Path(name).suffix
            return base, None, ext

        base, num_str, ext = match.groups()
        number = int(num_str) if num_str else None

        return base, number, ext

    def _make_numbered_name(self, base: str, number: int | None, ext: str) -> str:
        """Create numbered filename.

        Args:
            base: Base filename
            number: Optional number to append
            ext: File extension

        Returns:
            str: Combined filename
        """
        if number is None:
            return f"{base}{ext}"
        return f"{base} ({number}){ext}"

    def get_unique_path(self, path: Path) -> Path:
        """Get unique path that doesn't exist.

        Args:
            path: Original path

        Returns:
            Unique path

        Raises:
            ValueError: If unique path cannot be found
        """
        if not path.exists():
            return path

        if not self.auto_number:
            raise ValueError(f"Path already exists: {path}")

        # Track collision
        self.track_collision(path)

        # Try numbered variations
        stem = path.stem
        suffix = path.suffix
        parent = path.parent

        for i in range(1, self.max_attempts + 1):
            new_path = parent / f"{stem} ({i}){suffix}"
            if not new_path.exists():
                return new_path

        raise ValueError(f"Could not find unique path after {self.max_attempts} attempts")

    def track_collision(self, path: Path):
        """Track collision for path.

        Args:
            path: Path that had collision
        """
        str_path = str(path)
        self.collision_counts[str_path] = self.collision_counts.get(str_path, 0) + 1

    def get_collision_count(self, path: Path) -> int:
        """Get number of collisions for path.

        Args:
            path: Path to check

        Returns:
            Number of collisions
        """
        return self.collision_counts.get(str(path), 0)

    def clear_collision_counts(self) -> None:
        """Clear collision counts."""
        self.collision_counts.clear()

    def get_next_available_name(self, path: Path) -> Path:
        """Get next available name for path.

        Args:
            path: Original path

        Returns:
            Next available name

        Raises:
            ValueError: If no available name found
        """
        if not path.exists():
            return path

        stem = path.stem
        suffix = path.suffix
        parent = path.parent
        count = self.get_collision_count(path)

        if count >= self.max_attempts:
            raise ValueError(f"Maximum collision count reached for {path}")

        if not self.auto_number:
            raise ValueError(f"Path exists and auto-numbering disabled: {path}")

        new_path = parent / f"{stem} ({count + 1}){suffix}"
        self.track_collision(path)
        return new_path

    def get_unique_paths(self, paths: dict[Path, Path]) -> dict[Path, Path]:
        """Get unique paths for multiple files.

        Args:
            paths: Mapping of source paths to destination paths

        Returns:
            Mapping of source paths to unique destination paths
        """
        result = {}
        seen_paths: set[Path] = set()

        for src_path, dst_path in paths.items():
            if dst_path in seen_paths:
                # Path collision - get unique path
                unique_path = self.get_unique_path(dst_path)
                result[src_path] = unique_path
                seen_paths.add(unique_path)
            else:
                # No collision
                result[src_path] = dst_path
                seen_paths.add(dst_path)

        return result

    def merge_directories(self, source_dir: Path, target_dir: Path) -> dict[Path, Path]:
        """Generate unique paths for merging directories.

        Args:
            source_dir: Source directory
            target_dir: Target directory

        Returns:
            dict: Mapping of source paths to unique target paths
        """
        # Collect existing files in target
        for path in target_dir.rglob("*"):
            if path.is_file():
                self.add_existing(path)

        # Map source files to target
        paths = {}
        for src in source_dir.rglob("*"):
            if src.is_file():
                rel_path = src.relative_to(source_dir)
                dst = target_dir / rel_path
                paths[src] = dst

        return self.get_unique_paths(paths)
