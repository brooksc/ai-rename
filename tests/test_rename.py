"""Tests for core rename functionality."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from src.core.exceptions import RenameError
from src.core.llm import LLMClient, RenameSuggestion
from src.rename import (
    _process_file,
    extract_date_from_content,
    get_document_date,
    is_supported_file,
    rename_files,
)


class TestDateExtraction:
    """Tests for date extraction functionality."""

    def test_extract_date_iso_format(self):
        """Test extracting ISO format date (YYYY-MM-DD)."""
        content = "Document date: 2024-01-15"
        date = extract_date_from_content(content)

        assert date is not None
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15

    def test_extract_date_us_format(self):
        """Test extracting US format date (MM/DD/YYYY)."""
        content = "Invoice date: 01/15/2024"
        date = extract_date_from_content(content)

        assert date is not None
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15

    def test_extract_date_month_name_format(self):
        """Test extracting date with month name."""
        content = "Service date: January 15, 2024"
        date = extract_date_from_content(content)

        assert date is not None
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15

    def test_extract_date_no_date_found(self):
        """Test extracting date when no date is present."""
        content = "This document has no dates in it whatsoever."
        date = extract_date_from_content(content)

        assert date is None

    def test_extract_date_multiple_dates(self):
        """Test extracting date when multiple dates are present."""
        content = "Created: 2024-01-01, Service: 2024-01-15, Due: 2024-01-30"
        date = extract_date_from_content(content)

        # Should return the first valid date found
        assert date is not None
        assert date.year == 2024
        assert date.month == 1
        assert date.day == 1

    def test_extract_date_invalid_date(self):
        """Test extracting date with invalid date patterns."""
        content = "Document date: 2024-13-40"  # Invalid month and day
        date = extract_date_from_content(content)

        assert date is None

    def test_extract_date_partial_match(self):
        """Test extracting date with partial pattern matches."""
        content = "File 2024-01 incomplete date"
        date = extract_date_from_content(content)

        assert date is None  # Incomplete date should not match


class TestDocumentDate:
    """Tests for document date resolution."""

    def test_get_document_date_from_content(self, sample_txt_file):
        """Test getting document date from content."""
        content = "Invoice date: 2024-01-15\nAmount: $100"

        date, source = get_document_date(sample_txt_file, content)

        assert date.year == 2024
        assert date.month == 1
        assert date.day == 15
        assert source == "content"

    def test_get_document_date_from_file_stat(self, sample_txt_file):
        """Test getting document date from file modification time."""
        content = "No dates in this content"

        date, source = get_document_date(sample_txt_file, content)

        assert isinstance(date, datetime)
        assert source == "file"

    def test_get_document_date_fallback_to_current(self, temp_dir):
        """Test fallback to current date when file stat fails."""
        # Create a file path that doesn't exist
        nonexistent_file = temp_dir / "nonexistent.txt"
        content = "No dates in this content"

        with patch('src.rename.datetime') as mock_datetime:
            mock_now = datetime(2024, 1, 1)
            mock_datetime.now.return_value = mock_now
            mock_datetime.fromtimestamp.side_effect = Exception("Stat failed")

            date, source = get_document_date(nonexistent_file, content)

            assert date == mock_now
            assert source == "current"


class TestFileSupportCheck:
    """Tests for file support checking."""

    def test_is_supported_file_pdf(self, temp_dir):
        """Test PDF file support check."""
        pdf_file = temp_dir / "test.pdf"
        pdf_file.touch()

        assert is_supported_file(pdf_file) is True

    def test_is_supported_file_txt(self, temp_dir):
        """Test TXT file support check."""
        txt_file = temp_dir / "test.txt"
        txt_file.touch()

        # Based on constants.py, only PDF is currently supported
        assert is_supported_file(txt_file) is False

    def test_is_supported_file_unsupported(self, temp_dir):
        """Test unsupported file type."""
        image_file = temp_dir / "test.jpg"
        image_file.touch()

        assert is_supported_file(image_file) is False

    def test_is_supported_file_case_insensitive(self, temp_dir):
        """Test file support check is case insensitive."""
        pdf_file = temp_dir / "test.PDF"
        pdf_file.touch()

        assert is_supported_file(pdf_file) is True


class TestProcessFile:
    """Tests for single file processing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm_client = Mock(spec=LLMClient)
        self.mock_ui = Mock()

    def test_process_file_success(self, sample_txt_file, sample_config):
        """Test successful file processing."""
        # Mock LLM response
        suggestion = RenameSuggestion(
            suggested_path="Person/ACME/Financial/2024-01-15_invoice.txt",
            filename="2024-01-15_invoice.txt",
            reasoning="This is an invoice from ACME Corp"
        )
        self.mock_llm_client.generate_rename_suggestion.return_value = suggestion

        # Mock UI interaction
        self.mock_ui.handle_rename.return_value = True

        result = _process_file(
            path=sample_txt_file,
            llm_client=self.mock_llm_client,
            dry_run=False,
            ui=self.mock_ui
        )

        assert result is True
        self.mock_llm_client.generate_rename_suggestion.assert_called_once()
        self.mock_ui.handle_rename.assert_called_once()

    def test_process_file_missing_llm_client(self, sample_txt_file):
        """Test file processing without LLM client."""
        with pytest.raises(RenameError, match="LLM client is required"):
            _process_file(
                path=sample_txt_file,
                llm_client=None,
                dry_run=False
            )

    def test_process_file_pdf_size_limit(self, temp_dir):
        """Test PDF file size limit enforcement."""
        # Create a large PDF file (over 1MB)
        large_pdf = temp_dir / "large.pdf"
        large_content = b"Large PDF content" * 100000  # Over 1MB
        large_pdf.write_bytes(large_content)

        result = _process_file(
            path=large_pdf,
            llm_client=self.mock_llm_client,
            dry_run=False,
            ui=self.mock_ui
        )

        # Should skip large files
        assert result is True
        self.mock_llm_client.generate_rename_suggestion.assert_not_called()

    def test_process_file_dry_run_mode(self, sample_txt_file):
        """Test file processing in dry run mode."""
        suggestion = RenameSuggestion(
            suggested_path="test/path.txt",
            filename="test.txt",
            reasoning="test reasoning"
        )
        self.mock_llm_client.generate_rename_suggestion.return_value = suggestion

        with patch('src.rename.logger') as mock_logger:
            _process_file(
                path=sample_txt_file,
                llm_client=self.mock_llm_client,
                dry_run=True
            )

            # Should log what would be done
            mock_logger.info.assert_called()
            # Should not call UI for rename
            self.mock_ui.handle_rename.assert_not_called()

    def test_process_file_with_output_dir(self, sample_txt_file, temp_dir):
        """Test file processing with custom output directory."""
        output_dir = temp_dir / "output"
        suggestion = RenameSuggestion(
            suggested_path="Person/Test/2024-01-15_file.txt",
            filename="2024-01-15_file.txt",
            reasoning="test reasoning"
        )
        self.mock_llm_client.generate_rename_suggestion.return_value = suggestion
        self.mock_ui.handle_rename.return_value = True

        result = _process_file(
            path=sample_txt_file,
            llm_client=self.mock_llm_client,
            dry_run=False,
            output_dir=output_dir,
            ui=self.mock_ui
        )

        assert result is True
        # Check that proposal was created with output directory path
        call_args = self.mock_ui.handle_rename.call_args[0][0]
        assert str(output_dir) in str(call_args.new_path)

    def test_process_file_with_promptjson(self, sample_txt_file, temp_dir):
        """Test file processing with prompt JSON capture."""
        suggestion = RenameSuggestion(
            suggested_path="test/path.txt",
            filename="test.txt",
            reasoning="test reasoning"
        )
        self.mock_llm_client.generate_rename_suggestion.return_value = suggestion

        # Mock the debug files creation
        prompt_file = sample_txt_file.parent / "request.prompt"
        response_file = sample_txt_file.parent / "response.json"
        prompt_file.write_text("test prompt")
        response_file.write_text('{"test": "response"}')

        _process_file(
            path=sample_txt_file,
            llm_client=self.mock_llm_client,
            dry_run=False,
            promptjson=True
        )

        # Should have called LLM with capture directory
        self.mock_llm_client.generate_rename_suggestion.assert_called_once()
        call_kwargs = self.mock_llm_client.generate_rename_suggestion.call_args[1]
        assert call_kwargs.get('capture_dir') == sample_txt_file.parent

    def test_process_file_read_error(self, temp_dir):
        """Test file processing with file read error."""
        # Create a file that can't be read
        unreadable_file = temp_dir / "unreadable.txt"
        unreadable_file.touch()

        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with pytest.raises(RenameError, match="Failed to read content"):
                _process_file(
                    path=unreadable_file,
                    llm_client=self.mock_llm_client,
                    dry_run=False
                )

    def test_process_file_llm_error(self, sample_txt_file):
        """Test file processing with LLM error."""
        self.mock_llm_client.generate_rename_suggestion.side_effect = Exception("LLM failed")

        with pytest.raises(RenameError, match="Failed to get rename suggestion"):
            _process_file(
                path=sample_txt_file,
                llm_client=self.mock_llm_client,
                dry_run=False
            )


class TestRenameFiles:
    """Tests for batch file processing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_llm_client = Mock(spec=LLMClient)

    def test_rename_files_single_file(self, sample_txt_file, sample_config):
        """Test renaming a single file."""
        suggestion = RenameSuggestion(
            suggested_path="test/path.txt",
            filename="test.txt",
            reasoning="test reasoning"
        )
        self.mock_llm_client.generate_rename_suggestion.return_value = suggestion

        with patch('src.rename._process_file') as mock_process:
            mock_process.return_value = True

            rename_files(
                paths=[sample_txt_file],
                recursive=False,
                dry_run=False,
                config_path=sample_config,
                llm_client=self.mock_llm_client
            )

            mock_process.assert_called_once()

    def test_rename_files_recursive_directory(self, temp_dir, sample_config):
        """Test renaming files in directory recursively."""
        # Create test PDF files in subdirectories
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        pdf1 = temp_dir / "test1.pdf"
        pdf2 = subdir / "test2.pdf"
        pdf1.write_bytes(b"PDF content")
        pdf2.write_bytes(b"PDF content")

        with patch('src.rename._process_file') as mock_process:
            mock_process.return_value = True

            rename_files(
                paths=[temp_dir],
                recursive=True,
                dry_run=False,
                config_path=sample_config,
                llm_client=self.mock_llm_client
            )

            # Should process both PDF files
            assert mock_process.call_count == 2

    def test_rename_files_unsupported_file(self, temp_dir, sample_config):
        """Test renaming with unsupported file type."""
        unsupported_file = temp_dir / "image.jpg"
        unsupported_file.write_bytes(b"image content")

        with patch('src.rename.logger') as mock_logger:
            rename_files(
                paths=[unsupported_file],
                recursive=False,
                dry_run=False,
                config_path=sample_config,
                llm_client=self.mock_llm_client
            )

            # Should log warning about unsupported file
            mock_logger.warning.assert_called()

    def test_rename_files_with_taxonomy(self, sample_txt_file, sample_config, sample_taxonomy_file):
        """Test renaming files with taxonomy rules."""
        with patch('src.rename._process_file') as mock_process:
            mock_process.return_value = True

            rename_files(
                paths=[sample_txt_file],
                recursive=False,
                dry_run=False,
                config_path=sample_config,
                llm_client=self.mock_llm_client,
                taxonomy_file=sample_taxonomy_file
            )

            # Should pass taxonomy to process function
            call_args = mock_process.call_args[1]
            assert call_args['taxonomy'] is not None

    def test_rename_files_directory_without_recursive(self, temp_dir, sample_config):
        """Test processing directory without recursive flag."""
        with patch('src.rename.logger') as mock_logger:
            rename_files(
                paths=[temp_dir],
                recursive=False,
                dry_run=False,
                config_path=sample_config,
                llm_client=self.mock_llm_client
            )

            # Should log warning about needing --recursive
            mock_logger.warning.assert_called()

    def test_rename_files_process_error(self, sample_txt_file, sample_config):
        """Test handling errors during file processing."""
        with patch('src.rename._process_file') as mock_process:
            mock_process.side_effect = Exception("Processing failed")

            with patch('src.rename.logger') as mock_logger:
                rename_files(
                    paths=[sample_txt_file],
                    recursive=False,
                    dry_run=False,
                    config_path=sample_config,
                    llm_client=self.mock_llm_client
                )

                # Should log error
                mock_logger.error.assert_called()

    def test_rename_files_user_quit(self, sample_txt_file, sample_config):
        """Test handling user quitting during processing."""
        with patch('src.rename._process_file') as mock_process:
            mock_process.return_value = False  # User quit

            rename_files(
                paths=[sample_txt_file],
                recursive=False,
                dry_run=False,
                config_path=sample_config,
                llm_client=self.mock_llm_client
            )

            # Should exit early when user quits
            mock_process.assert_called_once()
