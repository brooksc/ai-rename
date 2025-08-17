"""Tests for taxonomy parsing and rules."""

import pytest
from pathlib import Path

from src.core.taxonomy import TaxonomyParser, TaxonomyRule
from src.core.exceptions import TaxonomyError


class TestTaxonomyRule:
    """Tests for TaxonomyRule class."""

    def test_taxonomy_rule_creation(self):
        """Test creating a TaxonomyRule instance."""
        rule = TaxonomyRule(
            name="Medical",
            pattern="medical|doctor|hospital",
            target_dir="Person/{Name}/Medical/",
            description="Medical documents for persons",
            examples=["Lab results", "Doctor visits"],
            priority=1,
            date_format="full"
        )
        
        assert rule.name == "Medical"
        assert rule.pattern.pattern == "medical|doctor|hospital"  # pattern is compiled regex
        assert rule.target_dir == "Person/{Name}/Medical/"
        assert rule.description == "Medical documents for persons"
        assert rule.examples == ["Lab results", "Doctor visits"]

    def test_taxonomy_rule_str_representation(self):
        """Test string representation of TaxonomyRule."""
        rule = TaxonomyRule(
            name="Financial",
            pattern="invoice|receipt|payment",
            target_dir="Person/{Name}/Financial/",
            description="Financial documents",
            examples=["Invoices"],
            priority=1,
            date_format="full"
        )
        
        str_repr = str(rule)
        assert "Financial" in str_repr
        assert "Person/{Name}/Financial/" in str_repr


class TestTaxonomyParser:
    """Tests for TaxonomyParser class."""

    def test_taxonomy_parser_creation(self, sample_taxonomy_file):
        """Test creating a TaxonomyParser instance."""
        parser = TaxonomyParser(sample_taxonomy_file)
        
        assert parser.file_path == sample_taxonomy_file
        assert parser.content is not None
        assert len(parser.content) > 0

    def test_taxonomy_parser_with_nonexistent_file(self, temp_dir):
        """Test TaxonomyParser with non-existent file."""
        nonexistent_file = temp_dir / "nonexistent.md"
        
        with pytest.raises(TaxonomyError, match="Taxonomy file not found"):
            TaxonomyParser(nonexistent_file)

    def test_taxonomy_parser_with_empty_file(self, temp_dir):
        """Test TaxonomyParser with empty file."""
        empty_file = temp_dir / "empty.md"
        empty_file.write_text("")
        
        with pytest.raises(TaxonomyError, match="Taxonomy file is empty"):
            TaxonomyParser(empty_file)

    def test_taxonomy_parser_loads_content(self, sample_taxonomy_file, sample_taxonomy_content):
        """Test that TaxonomyParser loads file content correctly."""
        parser = TaxonomyParser(sample_taxonomy_file)
        
        assert parser.content == sample_taxonomy_content
        assert "Document Organization Taxonomy" in parser.content
        assert "Medical" in parser.content
        assert "Financial" in parser.content

    def test_taxonomy_parser_with_unicode_content(self, temp_dir):
        """Test TaxonomyParser with Unicode content."""
        unicode_content = """# Taxonomía de Documentos

## Médico
- **Ruta:** `Persona/{Nombre}/Médico/{fecha}_{descripción}.pdf`
- **Reglas:** Documentos médicos con caracteres especiales: ñ, á, é, í, ó, ú
"""
        unicode_file = temp_dir / "unicode.md"
        unicode_file.write_text(unicode_content, encoding="utf-8")
        
        parser = TaxonomyParser(unicode_file)
        
        assert "Taxonomía" in parser.content
        assert "Médico" in parser.content
        assert "ñ, á, é, í, ó, ú" in parser.content

    def test_taxonomy_parser_with_large_file(self, temp_dir):
        """Test TaxonomyParser with a large file."""
        # Create a large taxonomy file
        large_content = "# Large Taxonomy\n\n"
        for i in range(1000):
            large_content += f"## Category {i}\n"
            large_content += f"- Path: Category_{i}/{{date}}_{{description}}.pdf\n"
            large_content += f"- Description: Category {i} documents\n\n"
        
        large_file = temp_dir / "large.md"
        large_file.write_text(large_content)
        
        parser = TaxonomyParser(large_file)
        
        assert len(parser.content) > 10000
        assert "Category 999" in parser.content

    def test_taxonomy_parser_readonly_content(self, sample_taxonomy_file):
        """Test that taxonomy content is read-only (immutable)."""
        parser = TaxonomyParser(sample_taxonomy_file)
        original_content = parser.content
        
        # The content should be the same each time we access it
        assert parser.content == original_content
        assert parser.content is not None


class TestTaxonomyParsing:
    """Tests for parsing taxonomy rules from content."""

    def test_parse_basic_taxonomy_structure(self, sample_taxonomy_parser):
        """Test parsing basic taxonomy structure."""
        content = sample_taxonomy_parser.content
        
        # Test that basic structure is preserved
        assert "# Document Organization Taxonomy" in content
        assert "## Core Principles" in content
        assert "## Categories" in content
        assert "### Medical" in content
        assert "### Financial" in content

    def test_extract_category_sections(self, sample_taxonomy_parser):
        """Test extracting category sections from taxonomy."""
        content = sample_taxonomy_parser.content
        
        # Should contain medical category information
        assert "Person/{Name}/Medical/{date}_{description}.pdf" in content
        assert "Medical documents for specific persons" in content
        
        # Should contain financial category information  
        assert "Person/{Name}/Financial/{date}_{description}.pdf" in content
        assert "Financial documents including invoices" in content

    def test_taxonomy_contains_rules(self, sample_taxonomy_parser):
        """Test that taxonomy contains rule definitions."""
        content = sample_taxonomy_parser.content
        
        # Should contain path templates
        assert "{Name}" in content
        assert "{date}" in content
        assert "{description}" in content
        
        # Should contain rule descriptions
        assert "Medical documents" in content
        assert "Financial documents" in content

    def test_taxonomy_date_format_rules(self, sample_taxonomy_parser):
        """Test that taxonomy contains date format rules."""
        content = sample_taxonomy_parser.content
        
        # Should contain date format specifications
        assert "YYYY-MM-DD" in content
        assert "Date Priority" in content

    def test_taxonomy_file_extension_handling(self, sample_taxonomy_parser):
        """Test that taxonomy handles file extensions."""
        content = sample_taxonomy_parser.content
        
        # Should specify PDF extension in examples
        assert ".pdf" in content


class TestTaxonomyValidation:
    """Tests for taxonomy validation."""

    def test_taxonomy_with_invalid_encoding(self, temp_dir):
        """Test taxonomy parser with invalid encoding."""
        # Create a file with invalid UTF-8 encoding
        invalid_file = temp_dir / "invalid_encoding.md"
        with open(invalid_file, "wb") as f:
            f.write(b"\xff\xfe# Invalid encoding\n")
        
        # Should handle encoding errors gracefully
        with pytest.raises(TaxonomyError):
            TaxonomyParser(invalid_file)

    def test_taxonomy_permission_error(self, temp_dir, monkeypatch):
        """Test taxonomy parser with permission errors."""
        # Create a file
        restricted_file = temp_dir / "restricted.md"
        restricted_file.write_text("# Restricted taxonomy")
        
        # Mock permission error
        def mock_read_text(*args, **kwargs):
            raise PermissionError("Permission denied")
        
        monkeypatch.setattr(Path, "read_text", mock_read_text)
        
        with pytest.raises(TaxonomyError, match="Permission denied"):
            TaxonomyParser(restricted_file)

    def test_taxonomy_with_minimal_content(self, temp_dir):
        """Test taxonomy parser with minimal valid content."""
        minimal_content = "# Minimal Taxonomy\n\n## Category\n- Rule: test"
        minimal_file = temp_dir / "minimal.md"
        minimal_file.write_text(minimal_content)
        
        parser = TaxonomyParser(minimal_file)
        
        assert parser.content == minimal_content
        assert "Minimal Taxonomy" in parser.content