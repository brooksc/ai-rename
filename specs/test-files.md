# PDF Test Files Specification (Simplified)

## 1. Core Test Files

### 1.1 Basic Test Set
```
test_files/
├── simple.pdf               # Clean, single-page text document
├── report.pdf              # Multi-page document with text and images (5-10 pages)
├── scanned.pdf            # Scanned document (for OCR testing)
├── complex.pdf            # Technical document with tables, diagrams
└── damaged.pdf            # Partially corrupted file for error handling
```

### 1.2 File Descriptions

1. `simple.pdf`
   - Single page text document
   - Clear metadata (title, author, date)
   - Basic formatting
   - Purpose: Basic functionality testing

2. `report.pdf`
   - 5-10 pages
   - Mix of text and images
   - Multiple sections/headings
   - Tables and lists
   - Purpose: LLM processing and summarization testing

3. `scanned.pdf`
   - Scanned text document
   - No embedded text
   - Clear, readable scan
   - Purpose: OCR functionality testing (when enabled)

4. `complex.pdf`
   - Technical content
   - Tables and diagrams
   - Multiple columns
   - Purpose: Layout handling and complex content processing

5. `damaged.pdf`
   - Partially corrupted file
   - Still openable but with errors
   - Purpose: Error handling testing

## 2. Test Scenarios

### 2.1 Basic Processing
- Text extraction from `simple.pdf`
- Metadata extraction from all files
- OCR processing of `scanned.pdf`
- Error handling with `damaged.pdf`

### 2.2 LLM Processing
- Summarization of `report.pdf`
- Technical content analysis of `complex.pdf`
- Tag generation for all files
- Category detection for different content types

### 2.3 Organization Testing
- File naming and placement
- Duplicate detection (using copies of existing files)
- Tag management
- Search functionality

## 3. Creating Test Files

### 3.1 Generation Methods
1. `simple.pdf`: Create in Word/LibreOffice, export to PDF
2. `report.pdf`: Use a real-world report or create from template
3. `scanned.pdf`: Print and scan `simple.pdf`
4. `complex.pdf`: Use a technical paper or documentation
5. `damaged.pdf`: Manually corrupt a copy of `simple.pdf`

### 3.2 Test File Requirements
- Files should be under 5MB (except `report.pdf` which can be larger)
- Use common fonts
- Include standard metadata where applicable
- Avoid password protection
- Use PDF version 1.7 or earlier

## 4. Additional Test Files (Optional)

Only create these if needed for specific feature testing:
```
test_files/optional/
├── large.pdf              # >50MB file (resource testing)
├── form.pdf              # PDF with form fields
├── password.pdf          # Password-protected
└── multilingual.pdf      # Content in multiple languages
```

## 5. Using Test Files

### 5.1 Basic Workflow
1. Start with `simple.pdf` for basic functionality
2. Progress to `report.pdf` for LLM features
3. Test OCR with `scanned.pdf` if enabled
4. Use `complex.pdf` for advanced processing
5. Verify error handling with `damaged.pdf`

### 5.2 Maintenance
- Keep test files in version control
- Document any modifications
- Update files if core functionality changes
- Maintain a backup copy