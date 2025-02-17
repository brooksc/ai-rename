# Development Guide

## Project Structure

```
ai-rename/
├── src/
│   ├── __init__.py         # Version and package info
│   ├── cli.py              # Command line interface
│   ├── config.py           # Configuration management
│   ├── constants.py        # Global constants
│   ├── diag.py            # Diagnostic system
│   ├── rename.py          # Core rename logic
│   ├── core/
│   │   ├── file_ops.py    # File operations
│   │   ├── llm.py         # LLM base integration
│   │   ├── taxonomy.py    # Taxonomy parsing
│   │   └── text_extract.py # Text extraction
│   ├── llm/
│   │   ├── providers.py   # LLM provider implementations
│   │   └── prompts.py     # LLM prompt templates
│   └── ui/
│       ├── display.py     # Display formatting
│       └── interactive.py # Interactive UI
├── tests/                 # Test suite
├── tools/                 # Development utilities
├── docs/                 # Documentation
└── spec/                 # Specifications
```

## Development Setup

1. Clone repository:
```bash
git clone https://github.com/yourusername/ai-rename.git
cd ai-rename
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Set up pre-commit hooks:
```bash
pre-commit install
```

## Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific test file
pytest tests/test_taxonomy.py
```

## Code Style

The project uses:
- Ruff for linting and formatting
- Mypy for type checking
- Pre-commit hooks for automated checks

Run style checks:
```bash
# Format code
ruff format src tests

# Run linter
ruff check src tests

# Type checking
mypy src tests
```

## Adding Features

1. Create a new branch:
```bash
git checkout -b feature/your-feature-name
```

2. Write tests first in `tests/`

3. Implement the feature

4. Update documentation:
   - Add feature description to README.md
   - Update relevant spec files
   - Add docstrings and type hints

5. Run test suite and style checks:
```bash
pytest
ruff check src tests
mypy src tests
```

6. Submit PR:
   - Clear description of changes
   - Reference any related issues
   - Include test coverage
   - Update CHANGELOG.md

## Debugging

The project includes several debugging tools:

1. Debug logging:
```bash
ai-rename -d path/to/files
```

2. System diagnostics:
```bash
ai-rename --diag
```

3. LLM prompt inspection:
```bash
ai-rename --debug-prompts path/to/files
```

## Release Process

1. Update version in `src/__init__.py`
2. Update CHANGELOG.md
3. Create release branch:
```bash
git checkout -b release/vX.Y.Z
```
4. Run full test suite
5. Create GitHub release
6. Merge to main

## Contributing

1. Fork the repository
2. Create feature branch
3. Follow code style guidelines
4. Write tests
5. Update documentation
6. Submit PR

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines. 