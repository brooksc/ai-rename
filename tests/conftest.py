import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock
from pdf_manager.utils.config import Config
from pdf_manager.core.database import Database
from pdf_manager.llm.provider import LLMProvider

@pytest.fixture
def test_dir(tmp_path):
    """Create a temporary test directory."""
    return tmp_path

@pytest.fixture
def sample_pdf(test_dir):
    """Create a sample PDF file for testing."""
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    pdf_path = test_dir / "test.pdf"
    pdf_path.write_bytes(pdf_content)
    return pdf_path

@pytest.fixture
def test_config(test_dir):
    """Create a test configuration."""
    config = {
        'paths': {
            'library': str(test_dir / "library"),
            'backup': str(test_dir / "backup"),
            'temp': str(test_dir / "temp")
        },
        'processing': {
            'ocr_enabled': False,
            'content_analysis': True,
            'max_threads': 1,
            'allowed_types': ['application/pdf'],
            'max_file_size': 1048576  # 1MB
        },
        'llm': {
            'provider': 'openai',
            'model': 'gpt-4',
            'fallback_provider': None,
            'fallback_model': None,
            'cache': {
                'enabled': True,
                'directory': str(test_dir / "cache"),
                'max_age': 3600
            },
            'max_chunk_size': 1000,
            'summary_length': 100,
            'auto_categorize': True,
            'tag_generation': True,
            'litellm_config': {
                'api_key': 'test_key',
                'organization': None
            }
        },
        'database': {
            'path': str(test_dir / "test.db"),
            'backup_count': 1
        }
    }
    return config

@pytest.fixture
def mock_litellm():
    """Mock litellm completion function."""
    with pytest.MonkeyPatch() as mp:
        mock = MagicMock()
        mock.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Test response"))],
            usage=MagicMock(total_tokens=10)
        )
        mp.setattr("litellm.completion", mock)
        yield mock

@pytest.fixture
def test_db(test_config):
    """Create a test database instance."""
    db = Database(test_config['database']['path'])
    yield db
    db.close()
    try:
        Path(test_config['database']['path']).unlink()
    except FileNotFoundError:
        pass

@pytest.fixture
def test_llm(test_config, test_db):
    """Create a test LLM provider instance."""
    return LLMProvider(test_config['llm'], test_db)

@pytest.fixture(autouse=True)
def setup_test_env(test_dir):
    """Set up test environment variables."""
    os.environ['OPENAI_API_KEY'] = 'test_key'
    os.environ['PDF_LIBRARY_PATH'] = str(test_dir / "library")
    os.environ['PDF_TEMP_DIR'] = str(test_dir / "temp")
    yield
    # Clean up
    for key in ['OPENAI_API_KEY', 'PDF_LIBRARY_PATH', 'PDF_TEMP_DIR']:
        os.environ.pop(key, None) 