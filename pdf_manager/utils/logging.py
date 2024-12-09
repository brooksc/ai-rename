import logging
import sys
from pathlib import Path
from typing import Optional
from rich.logging import RichHandler
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

def setup_logging(log_file: Optional[str] = None, debug: bool = False) -> None:
    """Set up logging configuration with optional file output and debug mode."""
    level = logging.DEBUG if debug else logging.INFO
    
    # Create formatters
    console_format = "%(message)s"
    file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Set up rich console handler
    console = Console()
    rich_handler = RichHandler(
        console=console,
        show_path=debug,
        enable_link_path=debug,
        markup=True,
        rich_tracebacks=True
    )
    rich_handler.setLevel(level)
    rich_handler.setFormatter(logging.Formatter(console_format))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(rich_handler)
    
    # Add file handler if log file is specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(file_format))
        root_logger.addHandler(file_handler)

def get_progress() -> Progress:
    """Create a progress bar for long-running operations."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=Console(),
        transient=True
    )

class LoggedError(Exception):
    """Base exception class that ensures proper logging of errors."""
    def __init__(self, message: str, *args):
        super().__init__(message, *args)
        logging.error(message)

class ConfigError(LoggedError):
    """Configuration-related errors."""
    pass

class ProcessingError(LoggedError):
    """PDF processing-related errors."""
    pass

class DatabaseError(LoggedError):
    """Database-related errors."""
    pass

class LLMError(LoggedError):
    """LLM-related errors."""
    pass
