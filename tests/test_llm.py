import pytest
from ai_rename import FileProcessor

def test_call_llm(mock_litellm, sample_config):
    """Test LLM API call functionality."""
    processor = FileProcessor(sample_config, type('Args', (), {'debug': True})())
    
    # Test successful API call
    response = processor.call_llm("Test prompt")
    assert response == "Test Response"
    
    # Test API error handling
    mock_litellm.side_effect = Exception("API Error")
    response = processor.call_llm("Test prompt")
    assert response == ""
    
    # Test response parsing error
    mock_litellm.side_effect = None
    mock_litellm.return_value = {}  # Invalid response format
    response = processor.call_llm("Test prompt")
    assert response == ""

def test_test_llm_connectivity(mock_litellm, sample_config):
    """Test LLM connectivity test function."""
    processor = FileProcessor(sample_config, type('Args', (), {'debug': True})())
    
    # Test successful connection
    mock_litellm.return_value = {
        'choices': [{
            'message': {
                'content': 'Test successful'
            }
        }]
    }
    assert processor.test_llm_connectivity() is True
    
    # Test failed connection
    mock_litellm.return_value = {
        'choices': [{
            'message': {
                'content': 'Wrong response'
            }
        }]
    }
    assert processor.test_llm_connectivity() is False
    
    # Test API error
    mock_litellm.side_effect = Exception("API Error")
    assert processor.test_llm_connectivity() is False

def test_generate_filename_with_llm(mock_requests, sample_config):
    """Test filename generation using LLM."""
    processor = FileProcessor(sample_config, type('Args', (), {'debug': True})())
    
    # Test successful filename generation
    mock_requests.return_value.json.return_value = {
        'choices': [{
            'message': {
                'content': 'Generated Filename'
            }
        }]
    }
    filename = processor.generate_filename("Sample document content")
    assert filename == "Generated Filename"
    
    # Test API error
    mock_requests.side_effect = Exception("API Error")
    filename = processor.generate_filename("Sample document content")
    assert filename == ""
    
    # Test invalid response format
    mock_requests.side_effect = None
    mock_requests.return_value.json.return_value = {}
    filename = processor.generate_filename("Sample document content")
    assert filename == ""

def test_summarize_with_llm(mock_litellm, temp_dir, sample_config):
    """Test document summarization using LLM."""
    processor = FileProcessor(sample_config, type('Args', (), {
        'debug': True,
        'summarize': True
    })())
    
    # Create test file
    test_file = "test_doc.txt"
    test_path = f"{temp_dir}/{test_file}"
    with open(test_path, 'w') as f:
        f.write("Test document content")
    
    # Test successful summarization
    mock_litellm.return_value = {
        'choices': [{
            'message': {
                'content': 'Document Summary'
            }
        }]
    }
    processor.generate_summary(test_path, test_file)
    
    # Verify summary file was created
    summary_file = f"{processor.ai_rename_dir}/{test_file.replace('.txt', '_summary.txt')}"
    assert os.path.exists(summary_file)
    with open(summary_file, 'r') as f:
        assert f.read() == "Document Summary"
    
    # Test failed summarization
    mock_litellm.side_effect = Exception("API Error")
    processor.generate_summary(test_path, test_file)
    # Should not create new summary file on error
    assert not os.path.exists(f"{processor.ai_rename_dir}/failed_summary.txt") 