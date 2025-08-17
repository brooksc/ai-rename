"""Security validation for file operations."""

import os
import re
import stat
from pathlib import Path

from loguru import logger
from src.core.exceptions import SecurityError


class SystemPathValidator:
    """Validates paths for security."""

    def __init__(self,
                 allow_hidden: bool = False,
                 custom_protected_paths: set[str] | None = None,
                 custom_protected_patterns: set[str] | None = None):
        """Initialize validator.

        Args:
            allow_hidden: Whether to allow hidden files
            custom_protected_paths: Additional protected paths
            custom_protected_patterns: Additional protected patterns
        """
        self.allow_hidden = allow_hidden

        # Protected paths
        self.protected_paths = {
            "/bin", "/sbin", "/usr/bin", "/usr/sbin",
            "/etc", "/var", "/dev", "/proc",
            "/sys", "/root", "/boot", "/lib", "/opt"
        }
        if custom_protected_paths:
            self.protected_paths.update(custom_protected_paths)

        # Protected patterns
        self.protected_patterns = {
            r"^\.git/",
            r"^\.env$",
            r"\.pem$",
            r"\.key$",
            r"passwd$",
            r"shadow$",
            r"sudoers$",
            r"authorized_keys$"
        }
        if custom_protected_patterns:
            self.protected_patterns.update(custom_protected_patterns)

        # Compile patterns
        self.compiled_patterns = [re.compile(p) for p in self.protected_patterns]

        # Use secure temp directory
        self.temp_dir = os.path.expanduser("~/.ai-rename/tmp")
        os.makedirs(self.temp_dir, mode=0o700, exist_ok=True)

    def is_protected_path(self, path: Path) -> bool:
        """Check if path is protected.

        Args:
            path: Path to check

        Returns:
            True if protected
        """
        path_str = str(path.resolve())

        # Check protected paths
        for protected in self.protected_paths:
            if path_str.startswith(protected):
                return True

        # Check patterns
        return any(pattern.search(path_str) for pattern in self.compiled_patterns)

    def is_protected_name(self, name: str) -> bool:
        """Check if filename is protected.

        Args:
            name: Filename to check

        Returns:
            True if protected
        """
        # Check hidden files
        if not self.allow_hidden and name.startswith("."):
            return True

        # Check patterns
        return any(pattern.search(name) for pattern in self.compiled_patterns)

    def validate_operation(self, src_path: Path, dst_path: Path):
        """Validate file operation.

        Args:
            src_path: Source path
            dst_path: Destination path

        Raises:
            SecurityError: If operation is not allowed
        """
        # Check source exists
        if not src_path.exists():
            raise SecurityError(f"Source path does not exist: {src_path}")

        # Check protected paths
        if self.is_protected_path(src_path):
            raise SecurityError(f"Source path is protected: {src_path}")
        if self.is_protected_path(dst_path):
            raise SecurityError(f"Destination path is protected: {dst_path}")

        # Check protected names
        if self.is_protected_name(src_path.name):
            raise SecurityError(f"Source filename is protected: {src_path.name}")
        if self.is_protected_name(dst_path.name):
            raise SecurityError(f"Destination filename is protected: {dst_path.name}")

    def validate_symlink(self, path: Path):
        """Validate symlink.

        Args:
            path: Path to symlink

        Raises:
            SecurityError: If symlink is not allowed
        """
        if not path.is_symlink():
            return

        target = path.resolve()
        if self.is_protected_path(target):
            raise SecurityError(f"Symlink target is protected: {target}")

    def sanitize_path(self, path: Path) -> Path:
        """Sanitize path.

        Args:
            path: Path to sanitize

        Returns:
            Sanitized path
        """
        # Remove invalid characters
        name = re.sub(r'[<>:"|?*]', '', str(path.name))

        # Ensure relative path
        if path.is_absolute():
            path = Path(str(path).lstrip("/"))

        return path.with_name(name)

    def get_safe_path(self, path: Path) -> Path:
        """Get safe version of path.

        Args:
            path: Path to make safe

        Returns:
            Safe path
        """
        # Sanitize path
        safe_path = self.sanitize_path(path)

        # Validate path
        if self.is_protected_path(safe_path):
            raise SecurityError(f"Path is protected: {safe_path}")
        if self.is_protected_name(safe_path.name):
            raise SecurityError(f"Filename is protected: {safe_path.name}")

        return safe_path

    def is_system_file(self, path: Path) -> bool:
        """Check if a file is a system file.

        Args:
            path: Path to check

        Returns:
            bool: True if file is a system file
        """
        if not path.exists():
            return False

        # Check filename against system patterns
        if any(pattern.search(path.name) for pattern in self.compiled_patterns):
            return True

        try:
            # Check file attributes
            if os.name == 'nt':  # Windows
                attrs = os.stat(path).st_file_attributes
                return bool(attrs & (stat.FILE_ATTRIBUTE_SYSTEM | stat.FILE_ATTRIBUTE_HIDDEN))
            else:  # Unix-like
                return bool(os.stat(path).st_flags & (stat.UF_HIDDEN | stat.UF_SYSTEM))
        except (AttributeError, OSError):
            return False

    def validate_permissions(self, path: Path, check_write: bool = False) -> None:
        """Validate file permissions.

        Args:
            path: Path to check
            check_write: Whether to check write permission

        Raises:
            SecurityError: If permissions are insufficient
        """
        try:
            # Check if path exists
            if not path.exists():
                if check_write:
                    # Check parent directory for write permission
                    parent = path.parent
                    if not parent.exists():
                        raise SecurityError(f"Parent directory does not exist: {parent}")
                    if not os.access(parent, os.W_OK):
                        raise SecurityError(f"No write permission for parent directory: {parent}")
                return

            # Check basic access
            if not os.access(path, os.R_OK):
                raise SecurityError(f"No read permission: {path}")

            if check_write and not os.access(path, os.W_OK):
                raise SecurityError(f"No write permission: {path}")

            # Check if directory is writable
            if path.is_dir() and check_write:
                test_file = path / '.write_test'
                try:
                    test_file.touch()
                    test_file.unlink()
                except (OSError, PermissionError) as e:
                    raise SecurityError(f"Directory is not writable: {path} ({e})") from e
                except Exception as e:
                    logger.error(f"Unexpected error testing directory permissions: {e}")
                    raise SecurityError(f"Cannot verify directory permissions: {path} ({e})") from e

        except SecurityError:
            raise
        except (OSError, AttributeError) as e:
            raise SecurityError(f"Cannot access path for permission check: {path} ({e})") from e
        except Exception as e:
            logger.error(f"Unexpected error checking permissions: {e}")
            raise SecurityError(f"Unexpected permission check failure for {path}: {e}") from e
