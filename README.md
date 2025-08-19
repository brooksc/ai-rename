# AI-Rename

An intelligent file renaming utility that uses AI to suggest better file names based on content and optional taxonomy rules.

[![Tests](https://img.shields.io/badge/tests-162%20passing-green.svg)](tests/)
[![Type Safety](https://img.shields.io/badge/mypy-type%20safe-blue.svg)](#)
[![Code Quality](https://img.shields.io/badge/ruff-compliant-blue.svg)](#)
[![Error Handling](https://img.shields.io/badge/exceptions-specific%20types-green.svg)](#)


## Background

I wrote this script as I had 2100 PDF files I had collected from scanning documents, my emails, etc.  They had unhelpful filenames like SCAN09430.pdf.  With this script, I fed it a taxonomy document which outlines how I want the files organized, it parsed the PDF file using Gemini Flash 2.0 and found an appropriate path and filename.

At this time this script is ONLY tested with Gemini Flash 2.0 and in particular it's using the Gemini capability to parse PDFs.

You can run this script in interactive mode, at which point it will show you each suggestion and ask you to accept or skip.  You can view the doc, give an override to influence the path/filename recommendation or also discuss how to change the taxonomy to get the recommendation you want in the future.    

I spent time earlier using a variety of local LLMs via ollama and I could never achieve the quality of classification that I was seeking, hence the dependency on Gemini.  

The majority of this code has been written using Agentic AI development - via Cursor, Windsurf and now Claude Code.  

## Installation

### Quick Install

```bash
git clone https://github.com/yourusername/ai-rename.git
cd ai-rename
pip install -e .
```

### Development Setup

```bash
git clone https://github.com/yourusername/ai-rename.git
cd ai-rename

# Using uv (recommended)
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Or using pip
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

After installation, the `ai-rename` command will be available in your PATH.

## Quick Start

```bash
# Basic usage
ai-rename path/to/files

# With taxonomy rules
ai-rename -t taxonomy.md path/to/files

# Recursive with extension filter
ai-rename -r -e .pdf -e .txt path/to/files

# Run diagnostics
ai-rename --diag
```

## Features

### Core Functionality
- Content-aware file renaming using AI (Google Gemini)
- Custom taxonomy rules in markdown format
- Interactive UI with file preview
- Dry run mode for safe testing
- Extension filtering and recursive processing

### Quality & Reliability
- **Comprehensive test suite** (162 tests covering core functionality)
- **Professional error handling** with specific exception types
- **Type safety** with mypy annotations
- **Robust diagnostics** and logging
- **Secure configuration** management

### User Experience
- Simple installation with `pip install -e .`
- Rich interactive interface
- Detailed progress tracking
- Override and customization options
- Trash directory for manual review

## Configuration

Configuration is stored in `~/.config/ai-rename/config.yaml`. Example:

```yaml
llm:
  model: gemini-2.0-flash  # Google's Gemini Flash 2.0 model
  timeout: 30
  temperature: 0.7

extraction:
  max_text_length: 10000
  preview_length: 1000
  supported_formats:
    - .txt
    - .pdf
    - .doc
    - .docx

ui:
  show_preview: true
  confirm_rename: true
  trash_dir: ~/.Trash/ai-rename
```

### Environment Variables

Required environment variable for Google Gemini:

```bash
export GEMINI_API_KEY=your_key_here
```

## Taxonomy Rules

Create taxonomy rules in markdown format:

```markdown
# Document Organization

## Person
- Tax returns -> Person/{Name}/Tax/{YYYY}
- Medical records -> Person/{Name}/Medical/{YYYY-MM-DD}_{Description}

## Property
- Insurance -> Property/{Address}/Insurance/{YYYY}
```

## Command Reference

- `-r, --recurse`: Process subdirectories
- `-e, --extension`: Filter by file extension
- `-t, --taxonomy`: Path to taxonomy rules
- `-n, --dry-run`: Show suggestions without renaming
- `-d, --debug`: Enable debug logging
- `--diag`: Run system diagnostics
- `--llm-provider`: LLM provider to use
- `--llm-model`: LLM model to use
- `--autoaccept`: Automatically accept all rename suggestions
- `--trash`: Move files to trash instead of renaming

## Interactive Commands

- `y`: Accept suggestion
- `n`: Skip file
- `e`: Edit suggestion
- `v`: View file contents
- `t`: Move to trash
- `!`: Override AI with custom instructions
- `q`: Quit program
- `?`: Show help

## Development

### Quick Commands

```bash
# Run tests
pytest -v

# Type checking
mypy src --ignore-missing-imports

# Code formatting
ruff check . --fix
black .

# Full development workflow
pytest && mypy src --ignore-missing-imports && ruff check .
```

### Project Quality

- **Test Coverage**: 162 comprehensive tests across all modules
- **Error Handling**: Zero bare exceptions, specific error types throughout
- **Type Safety**: Critical type annotations with mypy compliance
- **Code Quality**: Ruff-compliant formatting and linting
- **Documentation**: Comprehensive inline docs and examples

See [Development Guide](docs/development.md) and [Roadmap](docs/roadmap.md) for detailed information.

## Recent Improvements (August 2025)

- ✅ **Comprehensive Test Infrastructure**: 162 tests with pytest framework
- ✅ **Professional Error Handling**: Replaced 50+ bare exceptions with specific types
- ✅ **Type Safety**: Added critical type annotations and PyYAML stubs
- ✅ **Package Quality**: Verified pip installation and console script functionality
- ✅ **Code Quality**: Improved debugging, logging, and error messages

## License

MIT License - see LICENSE file for details. 
