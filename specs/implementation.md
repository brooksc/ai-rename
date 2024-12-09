# PDF Manager Implementation Specification

## 1. Command Line Interface

### 1.1 Core Commands
- `process`: Process single file or directory
- `search`: Search documents by content/metadata
- `tag`: Manage document tags
- `organize`: Auto-organize documents
- `config`: Manage configuration
- `stats`: View processing and LLM usage statistics

### 1.2 Modes of Operation
1. Interactive Mode
   - Simple command prompt interface
   - Real-time feedback
   - Progress indicators
   - Basic document info display
   
2. Batch Mode
   - Configuration file driven
   - Directory processing
   - Automated organization
   - Basic logging output

### 1.3 Configuration Options
```yaml
# config.yaml
paths:
  library: ~/Documents/PDFLibrary
  backup: ~/Documents/PDFLibrary/backups
  temp: /tmp/pdf_manager

processing:
  ocr_enabled: false  # Optional feature
  content_analysis: true
  max_threads: 2
  allowed_types:
    - application/pdf
  max_file_size: 52428800  # 50MB for personal use

llm:
  provider: openai  # or anthropic, azure, etc.
  model: gpt-4  # or claude-3, etc.
  litellm_config:
    api_key: ${OPENAI_API_KEY}  # Use env variables for keys
    organization: optional_org_id
    # Additional provider-specific settings
  
  fallback_provider: anthropic  # Optional fallback
  fallback_model: claude-3-opus  # Optional fallback
  
  # Optional caching to reduce API costs
  cache:
    enabled: true
    directory: ~/Documents/PDFLibrary/llm_cache
    max_age: 604800  # 7 days in seconds

  # Processing settings
  max_chunk_size: 4000  # tokens per API call
  summary_length: 250   # words
  auto_categorize: true
  tag_generation: true

organization:
  auto_categorize: true
  create_folders: true
  tag_rules:
    - pattern: "invoice.*\\.pdf"
      tags: [invoice, financial]
    - pattern: "report.*\\.pdf"
      tags: [report, business]

database:
  path: ~/Documents/PDFLibrary/library.db
  backup_count: 3  # Reduced for personal use
```

## 2. Core Functionality

### 2.1 Document Processing
1. File Analysis
   - Type verification
   - Size validation
   - Basic structure checking
   - Duplicate detection

2. Metadata Extraction
   - Basic metadata (title, author, date)
   - Text extraction
   - Optional OCR processing
   - LLM-powered content analysis

3. LLM Processing
   - Content summarization
   - Topic extraction
   - Tag suggestion
   - Category determination

### 2.2 Organization System
1. Auto-categorization
   - LLM-based classification
   - Pattern matching
   - Basic metadata analysis
   - Similar document grouping

2. Tag Management
   - Automated tagging via LLM
   - Custom tag rules
   - Simple tag relationships
   - Tag search

3. Search Capabilities
   - Full-text search
   - Metadata queries
   - Tag filtering
   - Basic similarity search

## 3. Data Storage

### 3.1 Database Schema
```sql
-- Documents table
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL,
    path TEXT NOT NULL,
    hash TEXT NOT NULL,
    content_summary TEXT,  -- LLM-generated summary
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- Metadata table
CREATE TABLE metadata (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- Tags table (simplified)
CREATE TABLE tags (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Document tags relationship
CREATE TABLE document_tags (
    document_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id),
    FOREIGN KEY (tag_id) REFERENCES tags(id),
    PRIMARY KEY (document_id, tag_id)
);

-- LLM Processing table (new)
CREATE TABLE llm_processing (
    id INTEGER PRIMARY KEY,
    document_id INTEGER NOT NULL,
    operation TEXT NOT NULL,  -- e.g., 'summarize', 'categorize'
    model_used TEXT NOT NULL,
    result TEXT NOT NULL,
    tokens_used INTEGER,
    processed_at TIMESTAMP NOT NULL,
    FOREIGN KEY (document_id) REFERENCES documents(id)
);

-- LLM Cache table (new)
CREATE TABLE llm_cache (
    id INTEGER PRIMARY KEY,
    request_hash TEXT NOT NULL UNIQUE,
    response TEXT NOT NULL,
    tokens_used INTEGER,
    model_used TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL
);
```

### 3.2 File Organization
- Hash-based deduplication
- Simple directory structure
- Basic version tracking
- Simple backup system

## 4. Error Handling

### 4.1 Error Categories
- File access errors
- Processing errors
- Database errors
- LLM API errors
- Configuration errors

### 4.2 Recovery Procedures
- Simple retry mechanism
- Fallback to backup LLM provider
- Basic error logging
- Configuration validation

## 5. Performance Considerations

### 5.1 Processing Optimization
- Basic parallel processing
- LLM response caching
- Efficient text chunking
- Resource monitoring

### 5.2 Search Optimization
- Simple index management
- Basic query optimization
- Cache frequently used results
- Efficient tag queries

## 6. Testing Approach

### 6.1 Basic Test Categories
1. Core Tests
   - PDF processing
   - Database operations
   - LLM integration
   - File operations

2. Integration Tests
   - Command processing
   - File organization
   - Search functionality
   - LLM fallback testing

3. Performance Tests
   - Basic load testing
   - API usage monitoring
   - Resource usage tracking

## 7. Setup and Deployment

### 7.1 Requirements
- Python 3.8+
- Required packages (requirements.txt)
- LLM API credentials
- SQLite database
- Optional: Tesseract for OCR

### 7.2 Installation
```bash
pip install -r requirements.txt
cp config.yaml.example config.yaml
# Edit config.yaml with your settings
python -m pdf_manager --init-db
```

### 7.3 Basic Usage
```bash
# Process a single file
pdf_manager process document.pdf

# Process a directory
pdf_manager process ~/Documents/PDFs/

# Search documents
pdf_manager search "keyword"

# View statistics
pdf_manager stats
```