"""Core renaming functionality."""

import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

from loguru import logger

from src.config import Config, GeminiConfig
from src.constants import SUPPORTED_FILE_TYPES
from src.core.exceptions import RenameError
from src.core.llm import LLMClient
from src.core.taxonomy import TaxonomyParser, TaxonomyRule
from src.ui.interface import FileRenameProposal, UserInterface


def extract_date_from_content(content: str) -> datetime | None:
    """Extract date from document content.

    Looks for common date formats in the content.

    Args:
        content: Document content to search

    Returns:
        datetime | None: Extracted date or None if not found
    """
    # Common date patterns
    patterns = [
        r'\b\d{4}-\d{2}-\d{2}\b',  # YYYY-MM-DD
        r'\b\d{2}/\d{2}/\d{4}\b',  # MM/DD/YYYY
        r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',  # DD Month YYYY
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, content)
        for match in matches:
            try:
                # Try different date formats
                date_str = match.group(0)
                for fmt in [
                    '%Y-%m-%d',
                    '%m/%d/%Y',
                    '%d %B %Y',
                    '%B %d, %Y',
                    '%B %d %Y',
                ]:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except ValueError:
                        continue
            except (ValueError, AttributeError, IndexError):
                # Skip malformed date strings or regex issues
                continue
            except Exception as e:
                logger.debug(f"Unexpected error parsing date pattern: {e}")
                continue

    return None

def get_document_date(path: Path, content: str) -> tuple[datetime, str]:
    """Get the most appropriate date for the document.

    Priority order:
    1. Document-specific dates (invoice, service, tax dates)
    2. Dates mentioned in document content
    3. Document creation/modification date
    4. Current date as last resort

    Args:
        path: Path to document
        content: Document content

    Returns:
        Tuple[datetime, str]: (date, source of date)
    """
    # Try to extract date from content
    content_date = extract_date_from_content(content)
    if content_date:
        return content_date, "content"

    # Try file modification date
    try:
        mod_time = path.stat().st_mtime
        return datetime.fromtimestamp(mod_time), "file"
    except (FileNotFoundError, PermissionError):
        logger.debug(f"Cannot access file modification time for {path}")
    except (OSError, ValueError) as e:
        logger.debug(f"Error reading file timestamp for {path}: {e}")
    except Exception as e:
        logger.warning(f"Unexpected error getting file modification time: {e}")

    # Use current date as last resort
    return datetime.now(), "current"

def is_supported_file(path: Path) -> bool:
    """Check if file is supported for renaming.

    Args:
        path: Path to check

    Returns:
        bool: True if file is supported, False otherwise
    """
    return path.suffix.lower() in SUPPORTED_FILE_TYPES

def rename_files(
    paths: list[Path],
    recursive: bool = False,
    dry_run: bool = False,
    config_path: Config | None = None,
    llm_client: LLMClient | None = None,
    taxonomy_file: Path | None = None,
    output_dir: Path | None = None,
    promptjson: bool = False,
    autoaccept: bool = False,
) -> None:
    """Rename files using LLM suggestions.

    Args:
        paths: List of paths to process
        recursive: Whether to process directories recursively
        dry_run: Whether to show what would be done without making changes
        config_path: Optional config file path
        llm_client: Optional LLM client instance
        taxonomy_file: Optional taxonomy rules file
        output_dir: Optional output directory
        promptjson: Whether to generate prompt/response debug files

    Raises:
        RenameError: If renaming fails
    """
    # Load configuration
    config = config_path if config_path else Config(gemini=GeminiConfig())

    # Override with command line options if provided
    if llm_client:
        config.gemini.model = llm_client.model

    # Load taxonomy if provided
    taxonomy = None
    if taxonomy_file:
        try:
            taxonomy = TaxonomyParser(taxonomy_file)
            logger.info(f"Loaded taxonomy rules from {taxonomy_file}")
        except Exception as e:
            logger.error(f"Failed to load taxonomy rules: {e}")
            raise

    # Create output directory if needed
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Using output directory: {output_dir}")

    # Initialize UI
    from src.ui.interface import UserInterface
    logger.debug(f"rename_files creating UserInterface with autoaccept={autoaccept}")
    ui = UserInterface(autoaccept=autoaccept)

    total_files = 0
    processed_files = 0
    renamed_files = 0
    skipped_files = 0
    failed_files = 0

    # Count total files first
    for path in paths:
        if path.is_file():
            if is_supported_file(path):
                total_files += 1
        elif path.is_dir() and recursive:
            total_files += sum(1 for p in path.rglob("*.pdf"))

    ui.total_files = total_files

    # Process files with progress
    for path in paths:
        try:
            if path.is_file():
                if not is_supported_file(path):
                    logger.warning(f"Skipping unsupported file: {path}")
                    skipped_files += 1
                    continue
                try:
                    if not _process_file(path, llm_client, dry_run, taxonomy, output_dir, config, promptjson, ui):
                        # User quit
                        return
                    renamed_files += 1
                except Exception as e:
                    logger.error(f"Failed to process {path}: {e}")
                    failed_files += 1
                processed_files += 1
                ui.display_progress(processed_files, total_files)
            elif path.is_dir() and recursive:
                for pdf_file in path.rglob("*.pdf"):
                    try:
                        if not _process_file(pdf_file, llm_client, dry_run, taxonomy, output_dir, config, promptjson, ui):
                            # User quit
                            return
                        renamed_files += 1
                    except Exception as e:
                        logger.error(f"Failed to process {pdf_file}: {e}")
                        failed_files += 1
                    processed_files += 1
                    ui.display_progress(processed_files, total_files)
            else:
                logger.warning(f"Skipping {path} (use --recursive for directories)")
                skipped_files += 1
        except Exception as e:
            logger.error(f"Failed to process {path}: {e}")
            failed_files += 1

    # Display final summary
    ui.display_summary(processed_files, renamed_files, skipped_files, failed_files)

def _process_file(
    path: Path,
    llm_client: LLMClient | None,
    dry_run: bool,
    taxonomy: TaxonomyParser | None = None,
    output_dir: Path | None = None,
    config: Config | None = None,
    promptjson: bool = False,
    ui: UserInterface | None = None,
) -> bool:
    """Process a single file.

    Args:
        path: Path to file
        llm_client: LLM client instance
        dry_run: Whether to show what would be done without making changes
        taxonomy: Optional taxonomy rules
        output_dir: Optional output directory
        config: Optional config
        promptjson: Whether to generate prompt/response debug files

    Raises:
        RenameError: If processing fails
    """
    try:
        # Validate LLM client
        if not llm_client:
            raise RenameError("LLM client is required")

        # Validate taxonomy if provided
        if taxonomy and not taxonomy.content.strip():
            raise RenameError("Taxonomy file is empty")

        # For PDFs, we'll pass the file directly to Gemini
        # For other files, read the content
        content = ""
        logger.debug(f"Reading content from: {path}")
        try:
            if path.suffix.lower() == '.pdf':
                # Check file size - skip if over 1MB
                file_size = path.stat().st_size
                if file_size > 1024 * 1024:  # 1MB in bytes
                    logger.warning(f"Skipping {path}: PDF file size {file_size/1024/1024:.2f}MB exceeds 1MB limit")
                    return True

                logger.debug("PDF file detected, will be passed directly to Gemini")
                content = "<PDF file will be processed directly by Gemini>"
            else:
                with open(path, encoding='utf-8') as f:
                    content = f.read()
                logger.debug(f"Successfully read {len(content)} characters of text")
        except Exception as e:
            logger.error(f"Failed to read content from {path}: {e}")
            raise RenameError(f"Failed to read content from {path}") from e

        # Set up capture directory if promptjson enabled
        capture_dir = None
        if promptjson:
            capture_dir = path.parent
            logger.debug(f"Capturing LLM interaction in {capture_dir}")

        # Get rename suggestion
        try:
            logger.debug("Generating rename suggestion from LLM")
            suggestion = llm_client.generate_rename_suggestion(
                content=content,
                file_path=path,
                taxonomy_rules=taxonomy.content if taxonomy else None,
                capture_dir=capture_dir if promptjson else None
            )
            logger.debug(f"Got suggestion: {suggestion}")
        except Exception as e:
            logger.error(f"Failed to get rename suggestion: {e}")
            raise RenameError("Failed to get rename suggestion") from e

        # If promptjson enabled, rename the debug files to match input file and exit
        if promptjson and capture_dir:
            debug_files = {
                "request.prompt": f"{path.stem}.prompt",
                "response.json": f"{path.stem}.json"
            }
            for src, dst in debug_files.items():
                src_path = capture_dir / src
                dst_path = capture_dir / dst
                if src_path.exists():
                    try:
                        if dst_path.exists():
                            logger.warning(f"Debug file {dst} already exists, overwriting")
                            dst_path.unlink()
                        src_path.rename(dst_path)
                        logger.debug(f"Renamed {src} to {dst}")
                    except Exception as e:
                        logger.error(f"Failed to rename debug file {src} to {dst}: {e}")
            return True  # Exit early when promptjson is True

        # Get document date
        try:
            doc_date, date_source = get_document_date(path, content)
            logger.debug(f"Using date from {date_source}: {doc_date}")
        except Exception as e:
            logger.error(f"Failed to get document date: {e}")
            raise RenameError("Failed to get document date") from e

        # Get and validate target path from suggestion
        if output_dir:
            # Preserve the directory structure from the suggested path
            suggested_path = Path(suggestion.suggested_path)
            # Always use the full suggested path
            new_path = output_dir.joinpath(suggested_path)
        else:
            new_path = Path(suggestion.suggested_path)

        # Validate the new path is safe (not escaping intended directory)
        if output_dir and not new_path.is_relative_to(output_dir):
            raise RenameError(f"Suggested path {new_path} would escape output directory {output_dir}")

        # Check if target path already exists
        if new_path.exists() and not dry_run:
            logger.warning(f"Target path {new_path} already exists")
            # Add a number suffix to the filename
            counter = 1
            while new_path.exists():
                stem = new_path.stem
                # Remove existing counter if present
                if (match := re.match(r"(.+)_(\d+)$", stem)):
                    stem = match.group(1)
                new_path = new_path.with_stem(f"{stem}_{counter}")
                counter += 1
            logger.info(f"Using alternative path: {new_path}")

        if dry_run:
            logger.info(f"Would rename {path} to {new_path}")
            logger.info(f"Reasoning: {suggestion.reasoning}")
            return True

        # Create proposal for UI
        if ui is None:
            logger.error("UserInterface not initialized")
            return False
        proposal = FileRenameProposal(
            current_path=path,
            new_path=new_path,
            content_preview=content[:1000],  # Show first 1000 chars
            reasoning=suggestion.reasoning
        )

        # Handle rename interactively
        def rename_func(src: Path, dst: Path) -> None:
            try:
                dst.parent.mkdir(parents=True, exist_ok=True)
                if dst.exists():
                    raise RenameError(f"Target path {dst} already exists")
                # Move the file instead of copying
                shutil.move(src, dst)
            except Exception as e:
                logger.error(f"Failed to move file from {src} to {dst}: {e}")
                raise RenameError("Failed to move file") from e

        continue_processing = ui.handle_rename(proposal, taxonomy, rename_func)
        if continue_processing:
            logger.info(f"Renamed {path} to {new_path}")
            return True
        else:
            logger.info("Operation cancelled by user")
            return False

    except Exception as e:
        logger.error(f"Error processing {path}: {e!s}")
        if isinstance(e, RenameError):
            raise
        raise RenameError(f"Failed to rename {path}") from e

    return True  # Continue processing by default

def rename_file(file_path: str, output_dir: str, config: dict, taxonomy_rules: list[TaxonomyRule], dry_run: bool = False) -> str:
    try:
        # Extract text from file
        if isinstance(file_path, str):
            file_path = Path(file_path)

        # Read file content
        try:
            text = file_path.read_text()
        except UnicodeDecodeError:
            logger.warning(f"Could not read {file_path} as text")
            text = ""

        # Build prompt
        prompt = build_prompt(file_path, text, taxonomy_rules)

        # Get suggestion from LLM
        llm = LLMClient(config)
        response = llm.generate(prompt)

        try:
            suggestion = json.loads(response)
        except json.JSONDecodeError as e:
            raise RenameError("Failed to parse LLM response as JSON") from e

        # Get suggested path
        suggested_path = suggestion.get("suggested_path")
        if not suggested_path:
            raise RenameError("LLM response missing suggested_path")

        # Create output path
        output_path = os.path.join(output_dir, suggested_path)

        # Create parent directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Copy file to new location
        if not dry_run:
            shutil.copy2(file_path, output_path)
            logger.info(f"Copied {file_path} to {output_path}")
        else:
            logger.info(f"Would copy {file_path} to {output_path}")

        return output_path

    except Exception as e:
        raise RenameError(f"Failed to rename {file_path}") from e

def build_prompt(file_path: str, file_content: str, taxonomy_rules: list[TaxonomyRule]) -> str:
    """Build prompt for LLM.

    Args:
        file_path: Path to file
        file_content: Content of file
        taxonomy_rules: List of taxonomy rules

    Returns:
        str: Prompt for LLM
    """
    prompt = f"""You are an AI assistant that helps organize documents by analyzing their content and suggesting appropriate names and storage locations.

TASK:
Please analyze this document and suggest where it should be stored and what it should be named based on its content and the organization rules below.

DOCUMENT DETAILS:
Current filename: {os.path.basename(file_path)}
Content preview:
{file_content}

ORGANIZATION RULES:
{taxonomy_rules}

REQUIREMENTS:
1. The suggested path should follow the taxonomy rules exactly
2. The filename should start with a date in YYYY-MM-DD format (or YYYY for annual documents)
3. The filename should be descriptive and use underscores instead of spaces
4. Keep the original file extension
5. Consider document type, content, dates, and any person/property names mentioned

Please respond with a JSON object containing:
{{
    "suggested_path": "full/path/to/file/YYYY-MM-DD_descriptive_name.ext",
    "filename": "YYYY-MM-DD_descriptive_name.ext",
    "reasoning": "Detailed explanation of why this path and name were chosen, including:
                 - Which taxonomy rule was applied
                 - What dates were found and why this date was chosen
                 - What key information influenced the name
                 - Any special cases or considerations"
}}

IMPORTANT:
- Your response must be valid JSON
- The suggested_path must exactly match a path structure from the taxonomy rules
- The filename must follow the date_descriptive-name.ext format
- Dates should be chosen based on the priority order in the rules
- Use the most specific and appropriate category for the document"""

    return prompt
