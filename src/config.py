"""Configuration management."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from loguru import logger

from src.constants import (
    CONFIG_DIR,
    CONFIG_FILE,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_GEMINI_TEMPERATURE,
    DEFAULT_GEMINI_TIMEOUT,
)


@dataclass
class GeminiConfig:
    """Gemini configuration.

    Args:
        model: Model name
        temperature: Sampling temperature
        timeout: Request timeout in seconds
        api_key: Gemini API key
    """
    model: str = DEFAULT_GEMINI_MODEL
    temperature: float = DEFAULT_GEMINI_TEMPERATURE
    timeout: int = DEFAULT_GEMINI_TIMEOUT
    api_key: str | None = None

    def validate(self) -> None:
        """Validate configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(self.model, str):
            raise ValueError("model must be a string")
        if not isinstance(self.temperature, int | float) or not 0 <= self.temperature <= 1:
            raise ValueError("temperature must be between 0 and 1")
        if not isinstance(self.timeout, int) or self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.api_key is not None and not isinstance(self.api_key, str):
            raise ValueError("api_key must be a string or None")



@dataclass
class TaxonomyConfig:
    """Taxonomy configuration.

    Args:
        path: Path to taxonomy file
        backup_dir: Directory for taxonomy backups
    """
    path: Path = CONFIG_DIR / "taxonomy.md"
    backup_dir: Path = CONFIG_DIR / "backups"

    def validate(self) -> None:
        """Validate configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(self.path, Path):
            raise ValueError("path must be a Path")
        if not isinstance(self.backup_dir, Path):
            raise ValueError("backup_dir must be a Path")

@dataclass
class Config:
    """Application configuration."""
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    taxonomy: TaxonomyConfig = field(default_factory=TaxonomyConfig)

    def validate(self) -> None:
        """Validate configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        self.gemini.validate()
        self.taxonomy.validate()

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary.

        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        return {
            "gemini": {
                "model": self.gemini.model,
                "temperature": self.gemini.temperature,
                "timeout": self.gemini.timeout,
                "api_key": self.gemini.api_key,
            },
            "taxonomy": {
                "path": str(self.taxonomy.path),
                "backup_dir": str(self.taxonomy.backup_dir)
            }
        }

def load_config(config_path: Path | None) -> Config:
    """Load configuration from file.

    Args:
        config_path: Path to config file

    Returns:
        Config: Loaded configuration

    Raises:
        FileNotFoundError: If config file not found
        ValueError: If config is invalid
    """
    if not config_path or not config_path.exists():
        logger.warning(f"Config file not found at {config_path}, using defaults")
        return Config(gemini=GeminiConfig())

    try:
        with open(config_path) as f:
            data = yaml.safe_load(f)

        if not data:
            logger.warning("Empty config file, using defaults")
            return Config(gemini=GeminiConfig())

        gemini_data = data.get("gemini", {})
        gemini_config = GeminiConfig(
            model=gemini_data.get("model", DEFAULT_GEMINI_MODEL),
            temperature=gemini_data.get("temperature", DEFAULT_GEMINI_TEMPERATURE),
            timeout=gemini_data.get("timeout", DEFAULT_GEMINI_TIMEOUT),
            api_key=gemini_data.get("api_key"),
        )

        taxonomy_data = data.get("taxonomy", {})
        taxonomy_config = TaxonomyConfig(
            path=Path(taxonomy_data.get("path", CONFIG_DIR / "taxonomy.md")),
            backup_dir=Path(taxonomy_data.get("backup_dir", CONFIG_DIR / "backups"))
        )

        config = Config(
            gemini=gemini_config,
            taxonomy=taxonomy_config
        )
        config.validate()
        return config

    except (FileNotFoundError, PermissionError) as e:
        logger.error(f"Cannot access config file: {e}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in config file: {e}")
        raise ValueError(f"Invalid config file format: {e}") from e
    except (ValueError, TypeError) as e:
        logger.error(f"Invalid config values: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}")
        raise ValueError(f"Failed to load config: {e}") from e

def create_default_config() -> Config:
    """Create default configuration file.

    Returns:
        Config: Created configuration
    """
    config_dir = Path(CONFIG_DIR).expanduser()
    config_file = config_dir / CONFIG_FILE

    if config_file.exists():
        logger.info(f"Configuration file already exists at {config_file}")
        return load_config(config_file)

    # Create config directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)

    # Create default config
    config = Config(gemini=GeminiConfig())

    # Save config
    with open(config_file, 'w') as f:
        yaml.safe_dump(config.to_dict(), f)

    logger.info(f"Created default configuration at {config_file}")
    return config
