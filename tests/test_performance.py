import time
import pytest
import psutil
import os
from pdf_manager.core.pdf_processor import PDFProcessor
from pdf_manager.llm.provider import LLMProvider

class ResourceMonitor:
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.peak_memory = 0
        self.start_memory = 0
        self.start_time = 0

    def __enter__(self):
        self.start_memory = self.process.memory_info().rss
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_memory = self.process.memory_info().rss
        self.peak_memory = max(self.start_memory, end_memory)

@pytest.mark.slow
def test_processing_performance(test_config, test_db, sample_pdf):
    """Test processing speed for different file sizes."""
    processor = PDFProcessor(test_config, LLMProvider(test_config['llm'], test_db))
    
    start_time = time.time()
    result = processor.process_pdf(str(sample_pdf))
    processing_time = time.time() - start_time
    
    assert processing_time < 5.0  # Should process within 5 seconds
    assert result is not None
    assert result['hash'] is not None

@pytest.mark.slow
def test_llm_response_time(test_llm):
    """Test LLM response times."""
    text = "This is a test document for performance testing."
    
    start_time = time.time()
    result = test_llm.process_text(text, 'summarize')
    response_time = time.time() - start_time
    
    assert response_time < 10.0  # Should complete within 10 seconds
    assert result['content'] is not None

@pytest.mark.slow
def test_memory_usage(test_config, test_db, sample_pdf):
    """Monitor memory usage during processing."""
    with ResourceMonitor() as monitor:
        processor = PDFProcessor(test_config, LLMProvider(test_config['llm'], test_db))
        result = processor.process_pdf(str(sample_pdf))
        
        assert result is not None
        assert monitor.peak_memory < 500_000_000  # Less than 500MB

@pytest.mark.slow
def test_batch_processing_performance(test_config, test_db, test_dir):
    """Test batch processing performance."""
    # Create multiple test PDFs
    pdf_files = []
    for i in range(5):
        pdf_path = test_dir / f"test_{i}.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\ntest content")
        pdf_files.append(pdf_path)
    
    processor = PDFProcessor(test_config, LLMProvider(test_config['llm'], test_db))
    
    start_time = time.time()
    for pdf_file in pdf_files:
        result = processor.process_pdf(str(pdf_file))
        assert result is not None
    
    total_time = time.time() - start_time
    avg_time = total_time / len(pdf_files)
    
    assert avg_time < 3.0  # Average processing time should be under 3 seconds per file

@pytest.mark.slow
def test_llm_cache_performance(test_llm):
    """Test LLM cache performance improvement."""
    text = "Test document for cache performance testing."
    
    # First call (no cache)
    start_time = time.time()
    result1 = test_llm.process_text(text, 'summarize')
    uncached_time = time.time() - start_time
    
    # Second call (should use cache)
    start_time = time.time()
    result2 = test_llm.process_text(text, 'summarize')
    cached_time = time.time() - start_time
    
    assert cached_time < uncached_time
    assert result2.get('cached', False) is True 