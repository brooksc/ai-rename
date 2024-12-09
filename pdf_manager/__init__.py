"""PDF Manager - Intelligent document management system."""

__version__ = "1.0.0"

from .cli.commands import cli
from .core.database import Database
from .core.pdf_processor import PDFProcessor
from .core.organization import DocumentOrganizer
from .llm.provider import LLMProvider
from .llm.cache import LLMCache
from .utils.config import Config
from .utils.logging import setup_logging

__all__ = [
    'cli',
    'Database',
    'PDFProcessor',
    'DocumentOrganizer',
    'LLMProvider',
    'LLMCache',
    'Config',
    'setup_logging'
]
