NOTE: I'm in the middle of rewriting this and it's not functional.  Star if you're interested in this and you'll get a notice once I have a release ready.  

# PDF Manager

An intelligent document management system that leverages AI capabilities for PDF organization and analysis.

## Features

- Automated PDF processing and text extraction
- Intelligent content analysis using LLMs
- Automatic metadata extraction and categorization
- Tag-based organization system
- Smart search capabilities
- Configurable document organization
- LLM response caching for efficiency
- Command-line interface with rich formatting

## Requirements

- Python 3.8+
- Tesseract OCR (optional, for OCR support)
- OpenAI API key or compatible LLM provider

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pdf-manager.git
   cd pdf-manager
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Tesseract OCR (optional):
   - macOS: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`
   - Windows: Download installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

4. Create configuration:
   ```bash
   cp config.yaml.example config.yaml
   ```

5. Set up environment variables:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   # Optional: Set up fallback provider
   export ANTHROPIC_API_KEY=your_anthropic_key_here
   ```

## Configuration

Edit `config.yaml` to customize:

- Library paths and organization
- Processing settings
- LLM provider and models
- Caching behavior
- Database location

Example configuration:
```yaml
paths:
  library: ~/Documents/PDFLibrary
  backup: ~/Documents/PDFLibrary/backups
  temp: /tmp/pdf_manager

processing:
  ocr_enabled: false
  content_analysis: true
  max_threads: 2
  allowed_types: ['application/pdf']
  max_file_size: 52428800  # 50MB

llm:
  provider: openai
  model: gpt-4
  fallback_provider: anthropic
  fallback_model: claude-3-opus
  cache:
    enabled: true
    directory: ~/Documents/PDFLibrary/llm_cache
    max_age: 604800  # 7 days
```

## Usage

### Process Files
```bash
# Process single file
pdf-manager process document.pdf

# Process directory recursively
pdf-manager -r process /path/to/documents/
```

### Search Documents
```bash
# Search by content or metadata
pdf-manager search "machine learning"
```

### Tag Management
```bash
# Add tags to document
pdf-manager tag 123 important research reference
```

### Organization
```bash
# Organize library
pdf-manager organize

# Force reorganization
pdf-manager organize --force
```

### Statistics
```bash
# View library statistics
pdf-manager stats
```

### Maintenance
```bash
# Clean up missing files
pdf-manager cleanup
```

## Development

### Project Structure
```
pdf_manager/
├── __init__.py
├── cli/
│   ├── __init__.py
│   └── commands.py
├── core/
│   ├── __init__.py
│   ├── database.py
│   ├── pdf_processor.py
│   └── organization.py
├── llm/
│   ├── __init__.py
│   ├── provider.py
│   └── cache.py
└── utils/
    ├── __init__.py
    ├── config.py
    └── logging.py
```

### Running Tests
```bash
pytest tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for GPT models
- Anthropic for Claude models
- PyMuPDF and pdfplumber for PDF processing
- Click for CLI interface
- Rich for terminal formatting
