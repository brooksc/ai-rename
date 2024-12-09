import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from pdf_manager.llm.provider import LLMProvider
from pdf_manager.llm.cache import LLMCache
from pdf_manager.utils.logging import LLMError

@pytest.fixture
def mock_config():
    """Create mock configuration."""
    return {
        'provider': 'openai',
        'model': 'gpt-4',
        'fallback_provider': 'anthropic',
        'fallback_model': 'claude-3-opus',
        'cache': {
            'enabled': True,
            'directory': '/tmp/cache',
            'max_age': 3600
        },
        'max_chunk_size': 4000,
        'summary_length': 250,
        'litellm_config': {
            'api_key': 'test_key',
            'organization': None
        }
    }

@pytest.fixture
def mock_db():
    """Create mock database."""
    return MagicMock()

@pytest.fixture
def llm_provider(mock_config, mock_db):
    """Create LLM provider with mocked configuration."""
    return LLMProvider(mock_config, mock_db)

def test_llm_initialization(llm_provider):
    """Test LLM provider initialization."""
    assert llm_provider.config['provider'] == 'openai'
    assert llm_provider.config['model'] == 'gpt-4'

@patch('litellm.completion')
def test_llm_call(mock_completion, llm_provider):
    """Test LLM API call."""
    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Test response"))
    ]
    mock_response.usage = MagicMock(total_tokens=10)
    mock_completion.return_value = mock_response
    
    # Make call
    result = llm_provider._make_llm_call("Test prompt", "openai/gpt-4")
    
    assert result['content'] == "Test response"
    assert result['tokens_used'] == 10
    assert result['model'] == "openai/gpt-4"

@patch('litellm.completion')
def test_llm_fallback(mock_completion, llm_provider):
    """Test LLM fallback behavior."""
    # Make first call fail
    mock_completion.side_effect = [
        Exception("API Error"),
        MagicMock(
            choices=[MagicMock(message=MagicMock(content="Fallback response"))],
            usage=MagicMock(total_tokens=5)
        )
    ]
    
    result = llm_provider._make_llm_call("Test prompt", "openai/gpt-4")
    
    assert result['content'] == "Fallback response"
    assert result['model'] == "anthropic/claude-3-opus"

def test_cache_key_generation(llm_provider):
    """Test cache key generation."""
    key1 = llm_provider._get_cache_key("test prompt", "model1")
    key2 = llm_provider._get_cache_key("test prompt", "model1")
    key3 = llm_provider._get_cache_key("test prompt", "model2")
    
    assert key1 == key2  # Same prompt and model should generate same key
    assert key1 != key3  # Different models should generate different keys

@patch('litellm.completion')
def test_process_text(mock_completion, llm_provider):
    """Test text processing with different operations."""
    mock_response = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Processed text"))],
        usage=MagicMock(total_tokens=10)
    )
    mock_completion.return_value = mock_response
    
    operations = ['summarize', 'categorize', 'tag', 'extract_metadata']
    
    for operation in operations:
        result = llm_provider.process_text("Test text", operation)
        assert result['content'] == "Processed text"
        assert not result.get('cached', False)

def test_invalid_operation(llm_provider):
    """Test handling of invalid operation."""
    with pytest.raises(LLMError, match="Unknown operation"):
        llm_provider.process_text("Test text", "invalid_operation")

@pytest.fixture
def llm_cache(mock_config, mock_db):
    """Create LLM cache instance."""
    return LLMCache(mock_db, mock_config)

def test_cache_get_set(llm_cache, mock_db):
    """Test cache get and set operations."""
    # Mock database response
    mock_db.conn.execute.return_value.fetchone.return_value = {
        'response': 'cached response',
        'tokens_used': 5,
        'model_used': 'test-model',
        'created_at': datetime.utcnow().isoformat()
    }
    
    # Test cache hit
    result = llm_cache.get('test_hash')
    assert result['response'] == 'cached response'
    assert result['cached'] is True
    
    # Test cache set
    llm_cache.set('test_hash', 'new response', 10, 'test-model')
    mock_db.conn.execute.assert_called()

def test_cache_expiration(llm_cache, mock_db):
    """Test cache expiration handling."""
    # Mock expired cache entry
    mock_db.conn.execute.return_value.fetchone.return_value = {
        'response': 'old response',
        'created_at': (datetime.utcnow() - timedelta(hours=2)).isoformat()
    }
    
    # Should return None for expired entry
    result = llm_cache.get('test_hash')
    assert result is None

def test_cache_stats(llm_cache, mock_db):
    """Test cache statistics."""
    # Mock statistics query results
    mock_db.conn.execute.return_value.fetchone.return_value = {
        'count': 10,
        'total_size': 1000,
        'total_tokens': 500
    }
    mock_db.conn.execute.return_value.fetchall.return_value = [
        {'model_used': 'gpt-4', 'count': 5},
        {'model_used': 'claude', 'count': 5}
    ]
    
    stats = llm_cache.get_stats()
    
    assert stats['count'] == 10
    assert stats['total_tokens'] == 500
    assert len(stats['models']) == 2