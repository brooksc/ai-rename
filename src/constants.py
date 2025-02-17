"""Constants used throughout the application."""

from pathlib import Path

# Gemini Configuration
DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
DEFAULT_GEMINI_TEMPERATURE = 0.9
DEFAULT_GEMINI_TIMEOUT = 120

# File paths
CONFIG_DIR = Path.home() / ".config" / "ai-rename"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
DEFAULT_TAXONOMY_FILE = CONFIG_DIR / "taxonomy.md"
DEFAULT_BACKUP_DIR = CONFIG_DIR / "backups"

# Logging
LOG_FORMAT = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

# Options Help Text
CONFIG_OPTION_HELP = "Path to configuration file."
DEBUG_OPTION_HELP = "Enable debug logging."
GEMINI_KEY_OPTION_HELP = "Gemini API key (required)"
GEMINI_MODEL_OPTION_HELP = "Gemini model to use (default: gemini-2.0-flash)"
RECURSIVE_OPTION_HELP = "Process directories recursively."
DRY_RUN_OPTION_HELP = "Show what would be done without making changes."
CREATE_CONFIG_OPTION_HELP = "Create default configuration file."
DIAG_OPTION_HELP = "Run system diagnostics and exit."
TAXONOMY_OPTION_HELP = "Path to taxonomy rules file."
OUTPUT_OPTION_HELP = "Output directory for renamed files."
PROMPTJSON_OPTION_HELP = "Generate .prompt and .json debug files for LLM interactions."

# File Processing
SUPPORTED_FILE_TYPES = {".pdf"}  # Only PDF support for now

# UI Settings
PROMPT_SUFFIX = "> "
ERROR_PREFIX = "Error: "
SUCCESS_PREFIX = "Success: "
WARNING_PREFIX = "Warning: "

# Date Formats
DATE_FORMATS = {
    "full": "%Y-%m-%d",  # YYYY-MM-DD
    "year": "%Y",        # YYYY
}

# Taxonomy Settings
TAXONOMY_BACKUP_PREFIX = "taxonomy_backup_"
TAXONOMY_BACKUP_FORMAT = "%Y%m%d_%H%M%S"  # For backup filenames

# Diagnostic Messages
DIAG_GEMINI_ERROR = "Gemini API key not found or invalid"
DIAG_CONFIG_ERROR = "Configuration file is invalid"
DIAG_TAXONOMY_ERROR = "Taxonomy file is invalid"
