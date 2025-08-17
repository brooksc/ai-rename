"""Pytest configuration and shared fixtures."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.config import Config, GeminiConfig
from src.core.llm import LLMClient
from src.core.taxonomy import TaxonomyParser


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_pdf_file(temp_dir):
    """Create a sample PDF file for testing."""
    pdf_path = temp_dir / "sample.pdf"
    # Create a minimal PDF-like content
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n"
    pdf_path.write_bytes(pdf_content)
    return pdf_path


@pytest.fixture
def sample_txt_file(temp_dir):
    """Create a sample text file for testing."""
    txt_path = temp_dir / "sample.txt"
    txt_content = """Invoice from ACME Corp
Date: 2024-01-15
Amount: $1,250.00
Service Period: January 2024

This is a sample invoice for testing purposes.
"""
    txt_path.write_text(txt_content)
    return txt_path


@pytest.fixture
def sample_config():
    """Create a sample configuration for testing."""
    return Config(
        gemini=GeminiConfig(
            api_key="test-api-key",
            model="gemini-2.0-flash",
            temperature=0.7,
            timeout=30
        )
    )


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    client = Mock(spec=LLMClient)
    client.model = "gemini-2.0-flash"
    client.temperature = 0.7
    client.timeout = 30
    client.test_connection.return_value = True
    return client


@pytest.fixture
def sample_taxonomy_content():
    """Sample taxonomy content for testing."""
    return """# Document Organization Taxonomy

## Core Principles
- Filenames: `YYYY-MM-DD_descriptive_name.ext`
- Date Priority: Document date, then creation date

## Categories

### Medical
- **Path:** `Person/{Name}/Medical/{date}_{description}.pdf`
- **Rules:** Medical documents for specific persons

### Financial
- **Path:** `Person/{Name}/Financial/{date}_{description}.pdf`
- **Rules:** Financial documents including invoices, receipts

### Other
- **Path:** `Other/{date}_{description}.pdf`
- **Rules:** Documents that don't fit other categories
"""


@pytest.fixture
def sample_taxonomy_file(temp_dir, sample_taxonomy_content):
    """Create a sample taxonomy file for testing."""
    taxonomy_path = temp_dir / "taxonomy.md"
    taxonomy_path.write_text(sample_taxonomy_content)
    return taxonomy_path


@pytest.fixture
def sample_taxonomy_parser(sample_taxonomy_file):
    """Create a sample taxonomy parser for testing."""
    return TaxonomyParser(sample_taxonomy_file)


@pytest.fixture
def mock_gemini_response():
    """Mock response from Gemini API."""
    response = Mock()
    response.text = """{
    "suggested_path": "Person/John_Doe/Medical/2024-01-15_medical_report.pdf",
    "filename": "2024-01-15_medical_report.pdf",
    "reasoning": "This appears to be a medical document for John Doe dated January 15, 2024."
}"""
    return response


@pytest.fixture
def sample_llm_response():
    """Sample LLM response data."""
    return {
        "suggested_path": "Person/ACME_Corp/Financial/2024-01-15_invoice.pdf",
        "filename": "2024-01-15_invoice.pdf",
        "reasoning": "This is an invoice from ACME Corp dated January 15, 2024. Based on the taxonomy rules, invoices should be categorized under Financial documents."
    }
