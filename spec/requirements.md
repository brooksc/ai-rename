# ai-rename Requirements Specification

## Overview

`ai-rename` is a command-line utility that uses AI to intelligently rename files based on their content. It provides an interactive interface for reviewing and confirming rename suggestions.

[X] Core Features:
- Intelligent Renaming: Using Google's Gemini Flash 2.0 model to analyze file content and suggest meaningful renaming
- Interactive Control: All operations performed sequentially with a consistent, text-based user interface
- Taxonomy-Guided Organization: File organization guided by user-supplied taxonomy document
- Safe File Management: Option to move files to Trash for manual review instead of direct renaming
- System Diagnostics: Comprehensive system checks and troubleshooting

## Core Requirements

### 1. Command Line Interface

```bash
ai-rename [OPTIONS] [PATHS]...

Options:
  --config PATH            Path to configuration file
  -d, --debug             Enable debug logging
  --llm-model TEXT        Gemini model to use (default: gemini-2.0-flash)
  -r, --recursive         Process directories recursively
  -n, --dry-run          Show what would be done without making changes
  -t, --taxonomy PATH     Path to taxonomy rules file
  -o, --output PATH       Output directory for renamed files
  --diag                  Run system diagnostics and exit
  -h, --help             Show this message and exit
  -e, --extension=EXT    Only process specific extensions
  --debug-prompts        Generate prompt and response files for debugging
  --trash                Move files to trash instead of renaming
```

[X] Command Line Requirements:
- Support recursive directory processing
- Enable dry-run mode for previewing changes
- Allow custom configuration and taxonomy files
- Provide detailed debug logging
- Support file extension filtering
- Enable taxonomy updates based on user decisions
- System diagnostic capabilities
- LLM provider selection
- Debug prompt inspection
- Trash directory support

### 2. File Processing Requirements

#### 2.1 File Selection
[X] Core Selection Features:
- Process single files or entire directories
- Support recursive directory traversal
- Filter files by extension(s)
- Skip hidden files (starting with .)
- Handle symlinks safely (skip by default)
- Skip system files
- Configurable symlink handling

#### 2.2 Text Extraction
[X] Supported File Types:
- Plain text (.txt)
- PDF documents (.pdf)
- Microsoft Word (.doc, .docx)
- Rich Text Format (.rtf)

[X] Extraction Requirements:
- Configurable text preview length
- Skip unsupported types
- Use native PDF handling capabilities
- Handle encoding detection and conversion
- Extract metadata when available
- Support for compressed files

#### 2.3 File Operations
[X] Core Operations:
- Support dry-run mode
- Enable custom output directory specification
- Validate target paths before renaming
- Create parent directories as needed
- Handle name collisions (auto-numbering)
- Maintain backup and undo functionality
- Move files to local Trash directory for manual review
- Atomic rename operations
- File permission handling

#### 2.4 Date-Based Filename Requirements
[X] Date Handling Priority:
1. Document-specific dates (invoice, service, tax dates)
2. Dates mentioned in document content
3. Document creation/modification date
4. Current date as last resort

[X] Date Formatting:
- YYYY-MM-DD for most documents
- YYYY for tax documents and annual statements
- Pattern: YYYY-MM-DD_description.ext
- Pattern: YYYY_description.ext (year-based)
- Configurable date formats
- Timezone handling

### 3. Taxonomy System

[X] The taxonomy document is a markdown file that contains:

1. Directory Structure:
   - Definition of main categories and subcategories
   - Hierarchy of folders and subfolders
   - Special folder handling rules

2. Naming Conventions:
   - Patterns for different types of files
   - Date format preferences
   - Case conventions
   - Special character handling

3. Category Definitions:
   - Detailed descriptions of what belongs in each category
   - Examples of file types for each category
   - Cross-referencing rules

4. Personal Preferences:
   - Specific terminology or abbreviations
   - Industry-specific organization needs
   - Individual filing preferences

#### 3.1 Configuration
[X] System Setup:
- Support custom taxonomy file location
- Load taxonomy rules from markdown format
- Default config: ~/.config/ai-rename/taxonomy.md
- Support natural language rule descriptions
- Include clear examples per category
- Define explicit date priority rules
- Version control support
- Rule validation

#### 3.2 Rule Structure
[X] Core Requirements:
- Natural language markdown format
- Category-based organization
- Clear examples for rule types
- Explicit variable definitions
- Priority ordering
- Special case handling
- Date format specifications
- Path template definitions
- Rule inheritance
- Override capabilities

#### 3.3 Rule Processing
[X] Processing Features:
- Natural language interpretation
- Context-aware matching
- Category-based organization
- Example-based validation
- Clear rule priorities
- Special case handling
- Date format validation
- Path template verification
- Rule conflict resolution
- Dynamic rule updates

### 4. LLM Integration

#### 4.1 Configuration
[X] Setup Requirements:
- Secure API key management via environment variables
- Multiple provider support (Anthropic, OpenAI, Gemini, Ollama)
- Configurable model selection
- Temperature and response settings
- Request timeout settings
- Robust error handling with retries
- Rate limit compliance
- Fallback providers
- Cost optimization

[X] Important Notes:
- Provider-specific capabilities
- Handle large documents efficiently
- Maintain secure API key storage
- Cost tracking and limits
- Performance monitoring

#### 4.2 Prompt Engineering
[X] Input Format:
- File content in XML tags: `<document>content</document>`
- Taxonomy in XML tags: `<taxonomy>rules</taxonomy>`
- Context in XML tags: `<context>info</context>`

[X] Prompt Components:
- Natural language task description
- Clear context provision
- Structured requirements
- Example-based guidance
- Detailed response format
- Explicit validation rules
- Priority-based decision making
- Error handling instructions

#### 4.3 Response Format
[X] Required JSON Structure:
```json
{
  "suggested_path": "path/to/file.ext",
  "filename": "filename.ext",
  "reasoning": "Explanation for the suggestion",
  "confidence": 0.95,
  "category": "document_type"
}
```

[X] Validation Requirements:
- JSON structure verification
- Path format validation
- Date format checking
- Extension preservation
- Rule compliance verification
- Confidence scoring
- Category validation

### 5. Interactive UI

#### 5.1 Display Elements
[X] Core UI Components:
```
>>> AI-RENAME ================================================
>>> Command: rename                        Status: Processing

Current File: ~/Downloads/doc20240115.pdf

Taxonomy:
- Using: ~/Documents/taxonomy.md

Old Path/Filename: ~/Downloads/doc20240115.pdf
New Path/Filename: ~/Documents/2024/Financial/Invoices/2024-01-15_acme_invoice.pdf

Reasoning:
This appears to be an invoice from ACME Corp dated January 15, 2024.
According to taxonomy rules, invoices should be organized under
Financial/Invoices with year subfolders.

Commands:
  Y)es    N)o    E)dit    V)iew    T)rash    !)override    Q)uit

>>> Ready for input: █
```

[X] UI Requirements:
- Current file path display
- Suggested new path preview
- LLM reasoning presentation
- Command options menu
- Progress indication
- File content preview
- Before/after path comparison
- Command help display
- Error reporting system
- Status updates
- Color support

#### 5.2 User Commands
[X] Core Commands:
- Y: Accept suggestion
- N: Skip/reject suggestion
- E: Edit suggestion
- V: View file contents
- T: Move to trash
- !: Override AI with custom instructions
- Q: Quit program
- ?: Show help

[X] Command Features:
- Single-key input
- Clear feedback
- Undo support
- Custom overrides
- Help system
- Progress saving
- Session management

### 6. Diagnostic System

#### 6.1 System Checks
[X] Core Diagnostics:
- LLM provider connectivity
- API key validation
- Configuration file verification
- Taxonomy file validation
- File permissions
- Directory access
- Python environment
- Dependencies
- Resource availability

#### 6.2 Reporting
[X] Output Format:
```
=== AI-RENAME DIAGNOSTICS ===
System:
  [✓] Python Version: 3.10.0
  [✓] Operating System: macOS 13.0
  [✓] File Permissions: OK

Configuration:
  [✓] Config File: Found
  [✓] Taxonomy File: Valid
  [✓] API Keys: Available

LLM Providers:
  [✓] Anthropic: Connected
  [✓] OpenAI: Connected
  [✓] Gemini: Not Configured
  [✓] Ollama: Available

Dependencies:
  [✓] Required Packages: OK
  [✓] Optional Features: OK

File Operations:
  [✓] Write Access: OK
  [✓] Trash Directory: OK
```

[X] Reporting Features:
- Clear status indicators
- Detailed error messages
- Troubleshooting suggestions
- Performance metrics
- Resource usage
- Configuration validation
- Security checks