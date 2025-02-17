"""Keybindings configuration for interactive UI."""

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import yaml
from loguru import logger


@dataclass
class KeyBinding:
    """Single key binding configuration."""
    key: str
    description: str
    command: str

class KeyBindings:
    """Manages keyboard bindings for interactive UI."""

    # Default bindings
    DEFAULT_BINDINGS: ClassVar[dict[str, KeyBinding]] = {
        'y': KeyBinding('y', 'Accept suggestion', 'accept'),
        'n': KeyBinding('n', 'Skip file', 'skip'),
        'e': KeyBinding('e', 'Edit suggestion', 'edit'),
        'v': KeyBinding('v', 'View file contents', 'view'),
        'u': KeyBinding('u', 'Undo last operation', 'undo'),
        'b': KeyBinding('b', 'Batch accept remaining', 'batch'),
        'q': KeyBinding('q', 'Quit program', 'quit'),
        '?': KeyBinding('?', 'Show help', 'help'),
    }

    def __init__(self, custom_bindings: dict[str, KeyBinding] | None = None):
        """Initialize keybindings.

        Args:
            custom_bindings: Optional custom key bindings
        """
        self.bindings = dict(self.DEFAULT_BINDINGS)
        if custom_bindings:
            self.bindings.update(custom_bindings)

    @classmethod
    def from_file(cls, path: Path) -> 'KeyBindings':
        """Load keybindings from YAML file.

        Args:
            path: Path to YAML file

        Returns:
            KeyBindings: Loaded keybindings

        Format:
        ```yaml
        bindings:
          a:  # key
            description: "Accept suggestion"
            command: "accept"
          s:
            description: "Skip file"
            command: "skip"
        ```
        """
        try:
            with path.open('r') as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict) or 'bindings' not in data:
                raise ValueError("Invalid keybindings file format")

            custom = {}
            for key, binding in data['bindings'].items():
                if not isinstance(key, str) or len(key) != 1:
                    logger.warning(f"Invalid key '{key}', skipping")
                    continue

                try:
                    custom[key] = KeyBinding(
                        key=key,
                        description=binding['description'],
                        command=binding['command']
                    )
                except (KeyError, TypeError) as e:
                    logger.warning(f"Invalid binding for key '{key}': {e}")
                    continue

            return cls(custom)

        except Exception as e:
            logger.error(f"Failed to load keybindings from {path}: {e}")
            return cls()

    def get_binding(self, key: str) -> KeyBinding | None:
        """Get binding for a key.

        Args:
            key: Key to look up

        Returns:
            Optional[KeyBinding]: Binding if found
        """
        return self.bindings.get(key.lower())

    def get_command(self, key: str) -> str | None:
        """Get command for a key.

        Args:
            key: Key to look up

        Returns:
            Optional[str]: Command if found
        """
        binding = self.get_binding(key)
        return binding.command if binding else None

    def get_help_text(self) -> str:
        """Get formatted help text.

        Returns:
            str: Help text showing all bindings
        """
        lines = ["Available commands:"]
        for binding in sorted(self.bindings.values(), key=lambda b: b.key):
            lines.append(f"{binding.key} - {binding.description}")
        return "\n".join(lines)

    def is_valid_key(self, key: str) -> bool:
        """Check if a key is valid.

        Args:
            key: Key to check

        Returns:
            bool: True if key is valid
        """
        return key.lower() in self.bindings
