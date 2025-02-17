"""Undo functionality for rename operations."""

import json
import shutil
from datetime import datetime
from pathlib import Path

from loguru import logger


class UndoManager:
    """Manages undo operations for file renames."""

    def __init__(self, backup_dir: Path | None = None):
        """Initialize undo manager.

        Args:
            backup_dir: Optional directory for storing backups
        """
        self.operations: list[dict] = []
        self.backup_dir = backup_dir or Path.home() / ".cache" / "ai-rename" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _create_backup(self, file_path: Path) -> Path:
        """Create backup of file before rename.

        Args:
            file_path: Path to file to backup

        Returns:
            Path: Path to backup file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{file_path.name}.{timestamp}.bak"

        try:
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to create backup of {file_path}: {e}")
            raise

    def add_operation(self, original_path: Path, new_path: Path) -> None:
        """Add rename operation to history.

        Args:
            original_path: Original file path
            new_path: New file path
        """
        try:
            # Create backup before recording operation
            backup_path = self._create_backup(original_path)

            operation = {
                'timestamp': datetime.now().isoformat(),
                'original_path': str(original_path),
                'new_path': str(new_path),
                'backup_path': str(backup_path)
            }

            self.operations.append(operation)
            logger.debug(f"Added operation to history: {operation}")

        except Exception as e:
            logger.error(f"Failed to record operation: {e}")
            raise

    def undo_last(self) -> tuple[Path, Path] | None:
        """Undo last rename operation.

        Returns:
            Optional[Tuple[Path, Path]]: (original_path, current_path) if successful
        """
        if not self.operations:
            logger.warning("No operations to undo")
            return None

        try:
            operation = self.operations.pop()
            original_path = Path(operation['original_path'])
            current_path = Path(operation['new_path'])
            backup_path = Path(operation['backup_path'])

            if current_path.exists():
                # Restore from backup
                shutil.copy2(backup_path, original_path)
                current_path.unlink()
                logger.info(f"Restored {original_path} from backup")

                # Clean up backup
                backup_path.unlink()
                logger.debug(f"Removed backup: {backup_path}")

                return original_path, current_path
            else:
                logger.error(f"Current path does not exist: {current_path}")
                return None

        except Exception as e:
            logger.error(f"Failed to undo operation: {e}")
            return None

    def clear_history(self) -> None:
        """Clear operation history and remove backups."""
        try:
            # Remove all backup files
            for operation in self.operations:
                backup_path = Path(operation['backup_path'])
                if backup_path.exists():
                    backup_path.unlink()
                    logger.debug(f"Removed backup: {backup_path}")

            self.operations.clear()
            logger.info("Cleared operation history")

        except Exception as e:
            logger.error(f"Failed to clear history: {e}")
            raise

    def get_history(self) -> list[dict]:
        """Get operation history.

        Returns:
            List[Dict]: List of operations
        """
        return self.operations.copy()

    def save_history(self, path: Path) -> None:
        """Save operation history to file.

        Args:
            path: Path to save history to
        """
        try:
            with path.open('w') as f:
                json.dump(self.operations, f, indent=2)
            logger.debug(f"Saved operation history to {path}")
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
            raise

    def load_history(self, path: Path) -> None:
        """Load operation history from file.

        Args:
            path: Path to load history from
        """
        try:
            with path.open('r') as f:
                self.operations = json.load(f)
            logger.debug(f"Loaded operation history from {path}")
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            raise
