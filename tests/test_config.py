"""Tests for configuration management."""

import pytest
from pathlib import Path
import tempfile
import yaml

from src.config import Config, GeminiConfig, load_config, create_default_config
from src.core.exceptions import ConfigError


class TestGeminiConfig:
    """Tests for GeminiConfig class."""

    def test_gemini_config_creation(self):
        """Test creating a GeminiConfig instance."""
        config = GeminiConfig(
            api_key="test-key",
            model="gemini-2.0-flash",
            temperature=0.7,
            timeout=30
        )
        
        assert config.api_key == "test-key"
        assert config.model == "gemini-2.0-flash"
        assert config.temperature == 0.9
        assert config.timeout == 30

    def test_gemini_config_defaults(self):
        """Test default values for GeminiConfig."""
        config = GeminiConfig()
        
        assert config.api_key is None
        assert config.model == "gemini-2.0-flash"
        assert config.temperature == 0.9
        assert config.timeout == 120


class TestConfig:
    """Tests for Config class."""

    def test_config_creation(self):
        """Test creating a Config instance."""
        gemini_config = GeminiConfig(api_key="test-key")
        config = Config(gemini=gemini_config)
        
        assert config.gemini.api_key == "test-key"

    def test_config_default_gemini(self):
        """Test Config with default GeminiConfig."""
        config = Config()
        
        assert config.gemini is not None
        assert isinstance(config.gemini, GeminiConfig)


class TestConfigLoading:
    """Tests for configuration loading functions."""

    def test_load_config_with_valid_file(self, temp_dir):
        """Test loading configuration from a valid YAML file."""
        config_file = temp_dir / "config.yaml"
        config_data = {
            "gemini": {
                "api_key": "test-api-key",
                "model": "gemini-2.0-flash",
                "temperature": 0.8,
                "timeout": 60
            }
        }
        
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        config = load_config(config_file)
        
        assert config.gemini.api_key == "test-api-key"
        assert config.gemini.model == "gemini-2.0-flash"
        assert config.gemini.temperature == 0.8
        assert config.gemini.timeout == 60

    def test_load_config_with_nonexistent_file(self, temp_dir):
        """Test loading configuration from a non-existent file."""
        config_file = temp_dir / "nonexistent.yaml"
        
        with pytest.raises(ConfigError, match="Configuration file not found"):
            load_config(config_file)

    def test_load_config_with_invalid_yaml(self, temp_dir):
        """Test loading configuration from an invalid YAML file."""
        config_file = temp_dir / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [")
        
        with pytest.raises(ConfigError, match="Failed to parse configuration file"):
            load_config(config_file)

    def test_load_config_with_partial_data(self, temp_dir):
        """Test loading configuration with partial data."""
        config_file = temp_dir / "partial.yaml"
        config_data = {
            "gemini": {
                "api_key": "test-key"
                # Missing other fields - should use defaults
            }
        }
        
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)
        
        config = load_config(config_file)
        
        assert config.gemini.api_key == "test-key"
        assert config.gemini.model == "gemini-2.0-flash"  # Default
        assert config.gemini.temperature == 0.7  # Default

    def test_create_default_config(self, temp_dir, monkeypatch):
        """Test creating default configuration."""
        # Mock the config directory
        config_dir = temp_dir / ".config" / "ai-rename"
        monkeypatch.setattr("src.config.CONFIG_DIR", config_dir)
        
        config = create_default_config()
        
        assert isinstance(config, Config)
        assert config.gemini.model == "gemini-2.0-flash"
        assert config.gemini.temperature == 0.7
        
        # Check if config file was created
        config_file = config_dir / "config.yaml"
        assert config_file.exists()

    def test_load_config_none_returns_default(self):
        """Test that passing None to load_config returns default config."""
        config = load_config(None)
        
        assert isinstance(config, Config)
        assert config.gemini.model == "gemini-2.0-flash"