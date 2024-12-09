# PDF Manager Testing Specification

## 1. Core Test Cases

### 1.1 Basic PDF Processing
```python
def test_basic_text_extraction():
    """Test extracting text from a simple PDF"""
    processor = PDFProcessor()
    text = processor.extract_text("test_files/basic.pdf")
    assert text is not None
    assert len(text) > 0

def test_metadata_extraction():
    """Test basic metadata extraction"""
    processor = PDFProcessor()
    metadata = processor.extract_metadata("test_files/basic.pdf")
    assert metadata.get('title') is not None

def test_ocr_processing():
    """Test OCR on scanned document (if enabled)"""
    if config.processing.ocr_enabled:
        processor = PDFProcessor()
        text = processor.process_with_ocr("test_files/scanned.pdf")
        assert len(text) > 0
```

### 1.2 LLM Integration
```python
def test_llm_summarization():
    """Test document summarization via LLM"""
    processor = PDFProcessor()
    summary = processor.get_summary("test_files/basic.pdf")
    assert summary is not None
    assert len(summary) > 0

def test_llm_categorization():
    """Test document categorization"""
    processor = PDFProcessor()
    categories = processor.get_categories("test_files/basic.pdf")
    assert len(categories) > 0

def test_llm_tag_generation():
    """Test automatic tag generation"""
    processor = PDFProcessor()
    tags = processor.generate_tags("test_files/basic.pdf")
    assert len(tags) > 0

def test_llm_fallback():
    """Test LLM provider fallback"""
    processor = PDFProcessor()
    with mock.patch('pdf_manager.llm.primary_provider', side_effect=Exception):
        summary = processor.get_summary("test_files/basic.pdf")
        assert summary is not None  # Should use fallback provider
```

### 1.3 Organization Features
```python
def test_file_organization():
    """Test basic file organization"""
    organizer = FileOrganizer()
    result = organizer.process_file("test_files/basic.pdf")
    assert result.success
    assert os.path.exists(result.new_path)

def test_duplicate_detection():
    """Test duplicate file handling"""
    organizer = FileOrganizer()
    result1 = organizer.process_file("test_files/basic.pdf")
    result2 = organizer.process_file("test_files/duplicate.pdf")
    assert result2.duplicate
    assert result2.original_path == result1.new_path
```

### 1.4 Search Functionality
```python
def test_content_search():
    """Test searching by content"""
    searcher = DocumentSearcher()
    results = searcher.search_content("test")
    assert len(results) > 0

def test_tag_search():
    """Test searching by tags"""
    searcher = DocumentSearcher()
    results = searcher.search_tags(["report"])
    assert len(results) >= 0
```

## 2. Required Test Files

### 2.1 Basic Test Set
```
test_files/
├── basic.pdf              # Simple text document
├── scanned.pdf           # Scanned document (for OCR testing)
├── long.pdf             # Multi-page document
├── duplicate.pdf        # Copy of basic.pdf
└── complex.pdf          # Document with mixed content
```

### 2.2 LLM Test Set
```
test_files/llm/
├── short.pdf            # 1-2 pages
├── medium.pdf          # 5-10 pages
├── technical.pdf       # Technical content
├── narrative.pdf       # Narrative content
└── multilingual.pdf    # Content in multiple languages
```

## 3. Integration Tests

### 3.1 Command Line Interface
```python
def test_cli_process_command():
    """Test basic process command"""
    result = run_command(['process', 'test_files/basic.pdf'])
    assert result.exit_code == 0

def test_cli_search_command():
    """Test search command"""
    result = run_command(['search', '--text', 'test'])
    assert result.exit_code == 0
    assert len(result.output) > 0

def test_cli_stats_command():
    """Test statistics command"""
    result = run_command(['stats'])
    assert result.exit_code == 0
    assert 'LLM Usage' in result.output
```

### 3.2 Configuration Tests
```python
def test_config_loading():
    """Test configuration file loading"""
    config = load_config('test_files/config.yaml')
    assert config.llm.provider is not None
    assert config.processing.max_file_size > 0

def test_llm_config():
    """Test LLM configuration"""
    config = load_config('test_files/config.yaml')
    llm = LLMProcessor(config)
    assert llm.is_configured()
    assert llm.can_connect()
```

## 4. Performance Tests

### 4.1 Basic Benchmarks
```python
def test_processing_performance():
    """Test processing speed for different file sizes"""
    processor = PDFProcessor()
    
    start_time = time.time()
    processor.process_file("test_files/basic.pdf")
    assert time.time() - start_time < 5.0  # Should process within 5 seconds

def test_llm_response_time():
    """Test LLM response times"""
    processor = PDFProcessor()
    
    start_time = time.time()
    processor.get_summary("test_files/short.pdf")
    assert time.time() - start_time < 10.0  # Should complete within 10 seconds
```

### 4.2 Resource Usage
```python
def test_memory_usage():
    """Monitor memory usage during processing"""
    monitor = ResourceMonitor()
    with monitor:
        processor = PDFProcessor()
        processor.process_file("test_files/large.pdf")
    
    assert monitor.peak_memory < 500_000_000  # Less than 500MB
```

## 5. Manual Test Checklist

### 5.1 Basic Functionality
- [ ] Process single PDF file
- [ ] Process directory of PDFs
- [ ] Search for specific content
- [ ] Add and remove tags
- [ ] Check file organization

### 5.2 LLM Features
- [ ] Generate summary
- [ ] Get automatic tags
- [ ] Test fallback provider
- [ ] Verify cache functionality
- [ ] Check token usage tracking

### 5.3 Error Handling
- [ ] Try invalid file
- [ ] Test network interruption
- [ ] Check API key issues
- [ ] Verify error messages

## 6. Test Configuration

```yaml
# test_config.yaml
processing:
  ocr_enabled: false
  max_file_size: 10485760  # 10MB for testing

llm:
  provider: openai
  model: gpt-3.5-turbo  # Use cheaper model for testing
  cache:
    enabled: true
    directory: ./test_cache

database:
  path: :memory:  # Use in-memory database for testing
```

## 7. Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/test_pdf_processing.py
pytest tests/test_llm_integration.py
pytest tests/test_cli.py

# Run with coverage
pytest --cov=pdf_manager tests/
```