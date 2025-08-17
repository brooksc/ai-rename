"""Tests for custom exceptions."""

import pytest

from src.core.exceptions import (
    AiRenameError,
    AuthenticationError,
    ConfigError,
    DiagnosticsError,
    ExtractionError,
    FileOperationError,
    LLMError,
    RateLimitError,
    RenameError,
    SecurityError,
    TaxonomyError,
    ValidationError,
)


class TestExceptionHierarchy:
    """Tests for exception inheritance hierarchy."""

    def test_ai_rename_error_is_base_exception(self):
        """Test that AiRenameError is the base exception."""
        error = AiRenameError("test message")
        assert isinstance(error, Exception)
        assert str(error) == "test message"

    def test_llm_error_inherits_from_ai_rename_error(self):
        """Test that LLMError inherits from AiRenameError."""
        error = LLMError("llm error")
        assert isinstance(error, AiRenameError)
        assert isinstance(error, Exception)
        assert str(error) == "llm error"

    def test_rate_limit_error_inherits_from_llm_error(self):
        """Test that RateLimitError inherits from LLMError."""
        error = RateLimitError("rate limit exceeded")
        assert isinstance(error, LLMError)
        assert isinstance(error, AiRenameError)
        assert isinstance(error, Exception)

    def test_authentication_error_inherits_from_llm_error(self):
        """Test that AuthenticationError inherits from LLMError."""
        error = AuthenticationError("auth failed")
        assert isinstance(error, LLMError)
        assert isinstance(error, AiRenameError)

    def test_all_errors_inherit_from_ai_rename_error(self):
        """Test that all custom errors inherit from AiRenameError."""
        error_classes = [
            SecurityError,
            FileOperationError,
            ExtractionError,
            TaxonomyError,
            ConfigError,
            ValidationError,
            RenameError,
        ]

        for error_class in error_classes:
            error = error_class("test message")
            assert isinstance(error, AiRenameError)
            assert isinstance(error, Exception)

    def test_diagnostics_error_inherits_from_exception(self):
        """Test that DiagnosticsError inherits directly from Exception."""
        error = DiagnosticsError("diagnostics failed")
        assert isinstance(error, Exception)
        # Should NOT inherit from AiRenameError
        assert not isinstance(error, AiRenameError)


class TestSpecificExceptions:
    """Tests for specific exception types."""

    def test_llm_error(self):
        """Test LLMError functionality."""
        message = "LLM request failed"
        error = LLMError(message)
        assert str(error) == message

    def test_rate_limit_error(self):
        """Test RateLimitError functionality."""
        message = "Rate limit exceeded"
        error = RateLimitError(message)
        assert str(error) == message

    def test_authentication_error(self):
        """Test AuthenticationError functionality."""
        message = "Invalid API key"
        error = AuthenticationError(message)
        assert str(error) == message

    def test_security_error(self):
        """Test SecurityError functionality."""
        message = "Security validation failed"
        error = SecurityError(message)
        assert str(error) == message

    def test_file_operation_error(self):
        """Test FileOperationError functionality."""
        message = "Failed to read file"
        error = FileOperationError(message)
        assert str(error) == message

    def test_extraction_error(self):
        """Test ExtractionError functionality."""
        message = "Text extraction failed"
        error = ExtractionError(message)
        assert str(error) == message

    def test_taxonomy_error(self):
        """Test TaxonomyError functionality."""
        message = "Invalid taxonomy rules"
        error = TaxonomyError(message)
        assert str(error) == message

    def test_config_error(self):
        """Test ConfigError functionality."""
        message = "Configuration error"
        error = ConfigError(message)
        assert str(error) == message

    def test_validation_error(self):
        """Test ValidationError functionality."""
        message = "Input validation failed"
        error = ValidationError(message)
        assert str(error) == message

    def test_rename_error(self):
        """Test RenameError functionality."""
        message = "File rename failed"
        error = RenameError(message)
        assert str(error) == message

    def test_diagnostics_error(self):
        """Test DiagnosticsError functionality."""
        message = "System diagnostics failed"
        error = DiagnosticsError(message)
        assert str(error) == message


class TestExceptionCatching:
    """Tests for exception catching behavior."""

    def test_catch_specific_exception(self):
        """Test catching specific exception types."""
        with pytest.raises(LLMError):
            raise LLMError("test")

    def test_catch_base_exception(self):
        """Test catching base exception catches derived exceptions."""
        with pytest.raises(AiRenameError):
            raise LLMError("test")

    def test_catch_hierarchy(self):
        """Test exception catching follows inheritance hierarchy."""
        # LLMError should be caught by AiRenameError
        try:
            raise LLMError("test")
        except AiRenameError:
            pass
        else:
            pytest.fail("Should have caught LLMError as AiRenameError")

        # RateLimitError should be caught by LLMError
        try:
            raise RateLimitError("test")
        except LLMError:
            pass
        else:
            pytest.fail("Should have caught RateLimitError as LLMError")

    def test_exception_with_cause(self):
        """Test exceptions with cause chaining."""
        original_error = ValueError("original error")

        try:
            raise LLMError("wrapper error") from original_error
        except LLMError as e:
            assert str(e) == "wrapper error"
            assert e.__cause__ is original_error
            assert isinstance(e.__cause__, ValueError)
