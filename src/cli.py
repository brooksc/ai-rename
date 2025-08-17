"""Command line interface for ai-rename."""

import sys
from pathlib import Path

import click
from loguru import logger

from src.config import create_default_config, load_config
from src.constants import (
    CONFIG_OPTION_HELP,
    CREATE_CONFIG_OPTION_HELP,
    DEBUG_OPTION_HELP,
    DEFAULT_GEMINI_MODEL,
    DIAG_OPTION_HELP,
    DRY_RUN_OPTION_HELP,
    GEMINI_KEY_OPTION_HELP,
    GEMINI_MODEL_OPTION_HELP,
    OUTPUT_OPTION_HELP,
    PROMPTJSON_OPTION_HELP,
    RECURSIVE_OPTION_HELP,
    TAXONOMY_OPTION_HELP,
)
from src.core.llm import LLMClient
from src.diag import DiagnosticsError, run_diagnostics
from src.rename import rename_files

CONTEXT_SETTINGS = {'help_option_names': ['-h', '--help']}

def setup_logging(debug: bool) -> None:
    """Set up logging configuration.

    Args:
        debug: Whether to enable debug logging
    """
    logger.remove()  # Remove default handler
    log_format = "<level>{level: <8}</level> | <green>{time:YYYY-MM-DD HH:mm:ss}</green> | {message}"

    if debug:
        logger.add(sys.stderr, format=log_format, level="DEBUG")
    else:
        logger.add(sys.stderr, format=log_format, level="INFO")

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "--config",
    type=click.Path(exists=False, dir_okay=False, path_type=Path),
    help=CONFIG_OPTION_HELP,
)
@click.option("--gemini-key", envvar="GOOGLE_API_KEY", help=GEMINI_KEY_OPTION_HELP)
@click.option("--gemini-model", default=DEFAULT_GEMINI_MODEL, help=GEMINI_MODEL_OPTION_HELP)
@click.option("-d", "--debug/--no-debug", default=False, help=DEBUG_OPTION_HELP)
@click.option("-r", "--recursive", is_flag=True, help=RECURSIVE_OPTION_HELP)
@click.option("-n", "--dry-run", is_flag=True, help=DRY_RUN_OPTION_HELP)
@click.option("--create-config", is_flag=True, help=CREATE_CONFIG_OPTION_HELP)
@click.option("--diag", is_flag=True, help=DIAG_OPTION_HELP)
@click.option("--taxonomy", type=click.Path(exists=True, dir_okay=False, path_type=Path), help=TAXONOMY_OPTION_HELP)
@click.option("-o", "--output", type=click.Path(file_okay=False, path_type=Path), help=OUTPUT_OPTION_HELP)
@click.option("-pj", "--promptjson", is_flag=True, help=PROMPTJSON_OPTION_HELP)
@click.option("--autoaccept", is_flag=True, help="Automatically accept all rename suggestions without prompting")
@click.argument('paths', nargs=-1, type=click.Path(exists=True, path_type=Path))
def cli(
    config: Path | None,
    debug: bool,
    gemini_key: str,
    gemini_model: str,
    recursive: bool,
    dry_run: bool,
    create_config: bool,
    diag: bool,
    taxonomy: Path | None,
    output: Path | None,
    promptjson: bool,
    autoaccept: bool,
    paths: list[Path],
) -> None:
    """AI-powered file renaming tool.

    This tool uses AI to intelligently rename files based on their content.
    It provides an interactive interface for reviewing and confirming rename
    suggestions.

    Example usage:
        ai-rename document.pdf
        ai-rename -r ~/Documents
        ai-rename --dry-run *.pdf
    """
    try:
        setup_logging(debug)

        if create_config:
            create_default_config()
            return

        if diag:
            try:
                config_obj = load_config(config) if config else create_default_config()
                # Override with command line options if provided
                if gemini_key:
                    logger.debug("Setting Gemini API key from command line")
                    config_obj.gemini.api_key = gemini_key
                if gemini_model:
                    logger.debug(f"Overriding Gemini model with: {gemini_model}")
                    config_obj.gemini.model = gemini_model
                results = run_diagnostics(config_obj)
                if results["status"]:
                    logger.info("All diagnostics passed:")
                else:
                    logger.error("Some diagnostics failed:")

                for check_name, check_result in results.items():
                    if check_name == "status":
                        continue

                    if isinstance(check_result, dict):
                        status = check_result.get("status", "unknown")
                        message = check_result.get("message", "No message")

                        if status == "ok":
                            logger.info(f"{check_name}: {message}")
                        else:
                            logger.error(f"{check_name}: {message}")

                            # Print additional debug info for failed checks
                            if debug:
                                for key, value in check_result.items():
                                    if key not in ["status", "message"]:
                                        logger.debug(f"  {key}: {value}")

                if not results["status"]:
                    sys.exit(1)
            except DiagnosticsError as e:
                logger.error(str(e))
                sys.exit(1)
            return

        if not paths:
            logger.error("No paths provided. Please specify at least one file or directory.")
            sys.exit(1)

        # Load or create config
        config_obj = load_config(config) if config else create_default_config()

        # Override with command line options if provided
        if gemini_key:
            config_obj.gemini.api_key = gemini_key
        if gemini_model:
            config_obj.gemini.model = gemini_model

        llm_client = LLMClient(
            model=config_obj.gemini.model,
            temperature=config_obj.gemini.temperature,
            timeout=config_obj.gemini.timeout,
            api_key=config_obj.gemini.api_key,
        )

        logger.debug(f"CLI received autoaccept={autoaccept}")
        rename_files(
            paths=list(paths),
            recursive=recursive,
            dry_run=dry_run,
            config_path=config_obj,
            llm_client=llm_client,
            taxonomy_file=taxonomy,
            output_dir=output,
            promptjson=promptjson,
            autoaccept=autoaccept,
        )

    except (FileNotFoundError, PermissionError) as e:
        logger.error(f"File access error: {e}")
        if debug:
            logger.exception("Detailed error information:")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        if debug:
            logger.exception("Detailed error information:")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if debug:
            logger.exception("Detailed error information:")
        sys.exit(1)

def main() -> None:
    """Main entry point for the application."""
    cli()

if __name__ == '__main__':
    main()
