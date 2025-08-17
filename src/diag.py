"""System diagnostics and health checks."""

import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

import google.generativeai as genai
from loguru import logger

from src.config import Config
from src.constants import SUPPORTED_FILE_TYPES
from src.core.llm import LLMClient
from src.core.taxonomy import TaxonomyParser


class DiagnosticsError(Exception):
    """Error during system diagnostics."""
    pass


def check_gemini(config: Config) -> dict[str, Any]:
    """Check Gemini API connection and configuration.

    Args:
        config: Application configuration

    Returns:
        Dict containing check results
    """
    try:
        logger.debug("Creating Gemini client")
        llm_client = LLMClient(
            model=config.gemini.model,
            temperature=config.gemini.temperature,
            timeout=config.gemini.timeout,
            api_key=config.gemini.api_key
        )

        # Test connection
        llm_client.test_connection()

        return {
            "status": "ok",
            "message": f"Gemini connection successful (model: {config.gemini.model})",
            "config": {
                "model": config.gemini.model,
                "temperature": config.gemini.temperature,
                "timeout": config.gemini.timeout,
                "api_key_set": bool(config.gemini.api_key)
            }
        }

    except (ValueError, ConnectionError, TimeoutError) as e:
        return {
            "status": "error",
            "message": f"Gemini connection failed: {e!s}",
            "config": {
                "model": config.gemini.model,
                "temperature": config.gemini.temperature,
                "timeout": config.gemini.timeout,
                "api_key_set": bool(config.gemini.api_key)
            }
        }
    except Exception as e:
        logger.error(f"Unexpected error during Gemini check: {e}")
        return {
            "status": "error",
            "message": f"Unexpected Gemini check error: {e!s}",
            "config": {
                "model": config.gemini.model,
                "temperature": config.gemini.temperature,
                "timeout": config.gemini.timeout,
                "api_key_set": bool(config.gemini.api_key)
            }
        }

        try:
            # Create test PDF
            with NamedTemporaryFile(suffix='.pdf', delete=False) as test_pdf:
                test_pdf.write(b'%PDF-1.4\nTest PDF for Gemini API')
                test_pdf.flush()
                logger.debug(f"Created test PDF at {test_pdf.name}")

            # Test PDF handling with Gemini
            try:
                genai.configure(api_key=config.gemini.api_key)
                model = genai.GenerativeModel(config.gemini.model)
                pdf_file = genai.upload_file(test_pdf.name, mime_type='application/pdf')
                response = model.generate_content([pdf_file, "What is this document about?"])
                if response.text:
                    return {
                        "status": "ok",
                        "message": "Gemini PDF handling verified and working",
                        "model": config.gemini.model
                    }
                else:
                    return {
                        "status": "error",
                        "message": "Gemini returned empty response for PDF test",
                        "model": config.gemini.model
                    }
            except (FileNotFoundError, PermissionError) as e:
                return {
                    "status": "error",
                    "message": f"Cannot access test PDF file: {e}",
                    "model": config.gemini.model,
                    "error": str(e)
                }
            except (ValueError, ConnectionError, TimeoutError) as e:
                return {
                    "status": "error",
                    "message": f"Gemini API error during PDF test: {e}",
                    "model": config.gemini.model,
                    "error": str(e)
                }
            except Exception as e:
                logger.error(f"Unexpected error during PDF test: {e}")
                return {
                    "status": "error",
                    "message": f"Unexpected PDF test failure: {e}",
                    "model": config.gemini.model,
                    "error": str(e)
                }
            finally:
                # Clean up test file
                test_pdf.unlink()
        except (OSError, PermissionError) as e:
            return {
                "status": "error",
                "message": f"Cannot create test PDF file: {e}"
            }
        except Exception as e:
            logger.error(f"Unexpected error creating test PDF: {e}")
            return {
                "status": "error",
                "message": f"Unexpected test PDF creation error: {e}"
            }


def check_taxonomy(config: Config) -> dict[str, Any]:
    """Check taxonomy file validity.

    Args:
        config: Application configuration

    Returns:
        Dict containing check results
    """
    try:
        taxonomy_path = config.taxonomy.path
        if not taxonomy_path.exists():
            return {
                "status": "error",
                "message": f"Taxonomy file not found at {taxonomy_path}",
                "path": str(taxonomy_path)
            }

        try:
            parser = TaxonomyParser(taxonomy_path)
            if not parser.rules:
                return {
                    "status": "warning",
                    "message": "Taxonomy file contains no rules",
                    "path": str(taxonomy_path)
                }

            return {
                "status": "ok",
                "message": f"Taxonomy file valid with {len(parser.rules)} rules",
                "path": str(taxonomy_path),
                "rules": len(parser.rules)
            }

        except (FileNotFoundError, PermissionError) as e:
            return {
                "status": "error",
                "message": f"Cannot access taxonomy file: {e}",
                "path": str(taxonomy_path)
            }
        except (ValueError, TypeError) as e:
            return {
                "status": "error",
                "message": f"Invalid taxonomy file format: {e}",
                "path": str(taxonomy_path)
            }
        except Exception as e:
            logger.error(f"Unexpected error parsing taxonomy: {e}")
            return {
                "status": "error",
                "message": f"Unexpected taxonomy parsing error: {e}",
                "path": str(taxonomy_path)
            }

    except (AttributeError, TypeError) as e:
        return {
            "status": "error",
            "message": f"Invalid taxonomy configuration: {e}"
        }
    except Exception as e:
        logger.error(f"Unexpected error checking taxonomy: {e}")
        return {
            "status": "error",
            "message": f"Unexpected taxonomy check error: {e}"
        }


def check_config(config: Config) -> dict[str, Any]:
    """Validate configuration.

    Args:
        config: Application configuration

    Returns:
        Dict containing check results
    """
    try:
        # Validate Gemini config
        if not config.gemini.model:
            return {
                "status": "error",
                "message": "Gemini model not configured"
            }
        if not config.gemini.api_key:
            return {
                "status": "error",
                "message": "Gemini API key not configured"
            }



        # Validate taxonomy config
        if not config.taxonomy.path:
            return {
                "status": "error",
                "message": "Taxonomy path not configured"
            }
        if not config.taxonomy.backup_dir:
            return {
                "status": "error",
                "message": "Taxonomy backup directory not configured"
            }

        # Check backup directory exists or can be created
        try:
            config.taxonomy.backup_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            return {
                "status": "error",
                "message": f"Cannot create taxonomy backup directory: {e}",
                "path": str(config.taxonomy.backup_dir)
            }
        except Exception as e:
            logger.error(f"Unexpected error creating backup directory: {e}")
            return {
                "status": "error",
                "message": f"Unexpected backup directory error: {e}",
                "path": str(config.taxonomy.backup_dir)
            }

        return {
            "status": "ok",
            "message": "Configuration valid",
            "config": {
                "llm": {
                    "url": config.llm.url,
                    "model": config.llm.model
                },
                "extraction": {
                    "gemini_model": config.gemini.model
                },
                "taxonomy": {
                    "path": str(config.taxonomy.path),
                    "backup_dir": str(config.taxonomy.backup_dir)
                }
            }
        }

    except (AttributeError, TypeError) as e:
        return {
            "status": "error",
            "message": f"Invalid configuration object: {e}"
        }
    except Exception as e:
        logger.error(f"Unexpected error validating configuration: {e}")
        return {
            "status": "error",
            "message": f"Unexpected configuration validation error: {e}"
        }


def check_system() -> dict[str, Any]:
    """Check system configuration.

    Returns:
        Dict containing check results
    """
    try:
        # Check Python version

        # Check supported file types
        if not SUPPORTED_FILE_TYPES:
            return {
                "status": "error",
                "message": "No supported file types configured"
            }

        return {
            "status": "ok",
            "message": "System checks passed",
            "platform": sys.platform,
            "python_version": sys.version,
            "cwd": str(Path.cwd()),
            "supported_types": list(SUPPORTED_FILE_TYPES)
        }

    except (OSError, AttributeError) as e:
        return {
            "status": "error",
            "message": f"System environment error: {e}"
        }
    except Exception as e:
        logger.error(f"Unexpected error during system check: {e}")
        return {
            "status": "error",
            "message": f"Unexpected system check error: {e}"
        }


def run_diagnostics(config: Config) -> dict[str, Any]:
    """Run system diagnostics.

    Args:
        config: Application configuration

    Returns:
        Dict containing all diagnostic results

    Raises:
        DiagnosticsError: If diagnostics fail critically
    """
    try:
        results = {
            "system": check_system(),
            "config": check_config(config),
            "taxonomy": check_taxonomy(config),
            "gemini": check_gemini(config)
        }

        # Count status types
        status_counts = {"ok": 0, "error": 0, "warning": 0}
        for check in results.values():
            if isinstance(check, dict):
                status = check.get("status", "error")
                status_counts[status] = status_counts.get(status, 0) + 1

        # Overall status is ok if no errors and at most 2 warnings
        results["status"] = (
            status_counts["error"] == 0 and
            status_counts["warning"] <= 2
        )

        # Add summary
        results["summary"] = {
            "total_checks": sum(status_counts.values()),
            "passed": status_counts["ok"],
            "warnings": status_counts["warning"],
            "errors": status_counts["error"]
        }

        return results

    except (KeyError, TypeError, AttributeError) as e:
        raise DiagnosticsError(f"Invalid diagnostics data structure: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during diagnostics: {e}")
        raise DiagnosticsError(f"Unexpected diagnostics failure: {e}") from e
