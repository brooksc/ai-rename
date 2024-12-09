import os
import pytest
from pathlib import Path
from pdf_manager.utils.config import Config

@pytest.fixture
def temp_config(tmp_path):
    """Create a temporary config file."""
    config_content = """
paths:
  library: ~/test_library
  backup: ~/test_library/backups
  temp: /tmp/test_manager

processing:
  ocr_enabled: true
  content_analysis: true
  max_threads: 1
  allowed_types:
    - application/pdf
  max_file_size: 10485760

llm:
  provider: openai
  model: gpt-4
  cache:
    enabled: true
    directory: ~/test_library/cache
    max_age: 3600
"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content)
    return str(config_file)

def test_config_loading(temp_config, monkeypatch):
    """Test configuration loading from file."""
    # Mock environment variables
    monkeypatch.setenv('OPENAI_API_KEY', 'test_key')
    
    # Load config
    config = Config(temp_config)
    
    # Check basic values
    assert config['paths']['library'] == os.path.expanduser('~/test_library')
    assert config['processing']['ocr_enabled'] is True
    assert config['llm']['provider'] == 'openai'

def test_config_validation(temp_config, monkeypatch):
    """Test configuration validation."""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_key')
    config = Config(temp_config)
    
    # Check expanded paths
    assert os.path.isabs(config['paths']['library'])
    assert os.path.isabs(config['paths']['backup'])
    assert os.path.isabs(config['paths']['temp'])

def test_missing_api_key(temp_config, monkeypatch):
    """Test handling of missing API key."""
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    
    with pytest.raises(ValueError, match="No LLM API key found"):
        Config(temp_config)

def test_default_config():
    """Test default configuration when no file is provided."""
    os.environ['OPENAI_API_KEY'] = 'test_key'
    config = Config()
    
    assert config['processing']['ocr_enabled'] is False
    assert isinstance(config['processing']['max_file_size'], int)
    assert config['llm']['provider'] == 'openai'

def test_config_get_method(temp_config, monkeypatch):
    """Test the get method with default values."""
    monkeypatch.setenv('OPENAI_API_KEY', 'test_key')
    config = Config(temp_config)
    
    # Test existing key
    assert config.get('llm.provider') == 'openai'
    
    # Test missing key with default
    assert config.get('nonexistent.key', 'default') == 'default'
    
    # Test nested key
    assert config.get('llm.cache.enabled') is True 