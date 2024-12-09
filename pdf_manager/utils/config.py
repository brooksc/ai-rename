import os
import yaml
from typing import Dict, Any
from pathlib import Path

DEFAULT_CONFIG = {
    'paths': {
        'library': '~/Documents/PDFLibrary',
        'backup': '~/Documents/PDFLibrary/backups',
        'temp': '/tmp/pdf_manager'
    },
    'processing': {
        'ocr_enabled': False,
        'content_analysis': True,
        'max_threads': 2,
        'allowed_types': ['application/pdf'],
        'max_file_size': 52428800  # 50MB
    },
    'llm': {
        'provider': 'openai',
        'model': 'gpt-4',
        'fallback_provider': 'anthropic',
        'fallback_model': 'claude-3-opus',
        'cache': {
            'enabled': True,
            'directory': '~/Documents/PDFLibrary/llm_cache',
            'max_age': 604800  # 7 days
        },
        'max_chunk_size': 4000,
        'summary_length': 250,
        'auto_categorize': True,
        'tag_generation': True
    },
    'database': {
        'path': '~/Documents/PDFLibrary/library.db',
        'backup_count': 3
    }
}

class Config:
    def __init__(self, config_path: str = None):
        self.config = DEFAULT_CONFIG.copy()
        if config_path:
            self.load_config(config_path)
        self.apply_env_vars()
        self.validate_config()

    def load_config(self, config_path: str) -> None:
        """Load configuration from YAML file."""
        config_path = os.path.expanduser(config_path)
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                self._deep_update(self.config, user_config)

    def apply_env_vars(self) -> None:
        """Apply environment variables to configuration."""
        # LLM API keys
        self.config['llm']['litellm_config'] = {
            'api_key': os.getenv('OPENAI_API_KEY'),
            'organization': os.getenv('OPENAI_ORG_ID'),
            'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY')
        }

        # Override paths if environment variables are set
        if pdf_lib := os.getenv('PDF_LIBRARY_PATH'):
            self.config['paths']['library'] = pdf_lib
        if temp_dir := os.getenv('PDF_TEMP_DIR'):
            self.config['paths']['temp'] = temp_dir

    def validate_config(self) -> None:
        """Validate configuration values."""
        # Expand user paths
        for key, path in self.config['paths'].items():
            self.config['paths'][key] = os.path.expanduser(path)
            
        # Create necessary directories
        for path in self.config['paths'].values():
            os.makedirs(path, exist_ok=True)

        # Validate LLM settings
        if not self.config['llm']['litellm_config']['api_key']:
            raise ValueError("No LLM API key found in environment variables")

        # Validate processing settings
        if self.config['processing']['max_file_size'] <= 0:
            raise ValueError("max_file_size must be positive")

    def _deep_update(self, d: Dict[str, Any], u: Dict[str, Any]) -> None:
        """Recursively update nested dictionaries."""
        for k, v in u.items():
            if isinstance(v, dict) and k in d and isinstance(d[k], dict):
                self._deep_update(d[k], v)
            else:
                d[k] = v

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default

    def __getitem__(self, key: str) -> Any:
        """Get configuration value using dictionary syntax."""
        return self.get(key)
