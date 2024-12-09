import os
import pytest
import tempfile
import yaml
from typing import Dict, Any
import shutil

@pytest.fixture
def sample_config() -> Dict[str, Any]:
    return {
        'LANGUAGE': 'eng',
        'ORIG_SUBDIR': 'orig',
        'API_TOKEN': 'test_token',
        'API_BASE': 'http://test.api',
        'MODEL': 'test_model',
        'prompts': {
            'filename_generation': 'Generate a descriptive filename',
            'summarization': 'Summarize the content'
        }
    }

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname

@pytest.fixture
def config_file(temp_dir, sample_config):
    """Create a temporary config file."""
    config_path = os.path.join(temp_dir, 'config.yaml')
    with open(config_path, 'w') as f:
        yaml.dump(sample_config, f)
    return config_path

@pytest.fixture
def sample_pdf(temp_dir):
    """Create a sample PDF file for testing."""
    pdf_path = os.path.join(temp_dir, 'test.pdf')
    # Create a minimal PDF file
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\n%EOF')
    return pdf_path

@pytest.fixture
def sample_image(temp_dir):
    """Create a sample image file for testing."""
    image_path = os.path.join(temp_dir, 'test.png')
    # Create a minimal PNG file
    with open(image_path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n')
    return image_path

@pytest.fixture
def mock_subprocess(mocker):
    """Mock subprocess calls."""
    return mocker.patch('subprocess.run')

@pytest.fixture
def mock_litellm(mocker):
    """Mock litellm API calls."""
    mock = mocker.patch('litellm.completion')
    mock.return_value = {
        'choices': [{
            'message': {
                'content': 'Test Response'
            }
        }]
    }
    return mock

@pytest.fixture
def mock_requests(mocker):
    """Mock requests calls."""
    mock = mocker.patch('requests.post')
    mock.return_value.json.return_value = {
        'choices': [{
            'message': {
                'content': 'Generated Filename'
            }
        }]
    }
    return mock 