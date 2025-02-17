"""Custom exceptions for ai-rename."""

class AiRenameError(Exception):
    """Base exception for ai-rename."""
    pass

class LLMError(AiRenameError):
    """Error when interacting with LLM."""
    pass

class RateLimitError(LLMError):
    """Error when rate limit is exceeded."""
    pass

class AuthenticationError(LLMError):
    """Error when authentication fails."""
    pass

class SecurityError(AiRenameError):
    """Error when security validation fails."""
    pass

class FileOperationError(AiRenameError):
    """Error during file operations."""
    pass

class ExtractionError(AiRenameError):
    """Error during text extraction."""
    pass

class TaxonomyError(AiRenameError):
    """Error in taxonomy rules."""
    pass

class ConfigError(AiRenameError):
    """Error during configuration operations."""
    pass

class ValidationError(AiRenameError):
    """Error during input validation."""
    pass

class DiagnosticsError(Exception):
    """Raised when system diagnostics fail."""
    pass

class RenameError(AiRenameError):
    """Raised when file renaming fails."""
    pass
