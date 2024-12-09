import pytest
from ai_rename import FileProcessor

def test_clean_filename():
    """Test the clean_filename function with various inputs."""
    processor = FileProcessor({}, None)

    # Test valid filenames
    assert processor.clean_filename("ValidFilename") == "ValidFilename"
    assert processor.clean_filename("Valid Filename") == "Valid Filename"
    assert processor.clean_filename("Valid_Filename") == "Valid Filename"
    assert processor.clean_filename("Valid-Filename") == "Valid Filename"
    assert processor.clean_filename("ValidFilename123") == "ValidFilename123"

    # Test invalid characters
    assert processor.clean_filename("Invalid*Filename!") == "Invalid Filename"
    assert processor.clean_filename("Invalid#Filename$") == "Invalid Filename"
    assert processor.clean_filename("Invalid@Filename%") == "Invalid Filename"
    assert processor.clean_filename("Invalid^Filename&") == "Invalid Filename"

    # Test multiple spaces and underscores
    assert processor.clean_filename("Too   Many   Spaces") == "Too Many Spaces"
    assert processor.clean_filename("Too___Many___Underscores") == "Too Many Underscores"
    assert processor.clean_filename("Mixed   Spaces_And_Underscores") == "Mixed Spaces And Underscores"

    # Test camel case
    assert processor.clean_filename("camelCaseFilename") == "camel Case Filename"
    assert processor.clean_filename("PascalCaseFilename") == "Pascal Case Filename"

    # Test file extensions
    assert processor.clean_filename("FilenameWithExtension.pdf") == "FilenameWithExtension"
    assert processor.clean_filename("Filename With Extension.pdf") == "Filename With Extension"
    assert processor.clean_filename("Filename_With_Extension.pdf") == "Filename With Extension"

    # Test length validation
    assert processor.clean_filename("A" * 101) == ""
    assert processor.clean_filename("B" * 150) == ""
    assert processor.clean_filename("A") == ""
    assert processor.clean_filename("BB") == ""

def test_generate_filename(mock_requests, sample_config):
    """Test the generate_filename function."""
    processor = FileProcessor(sample_config, None)
    
    # Test successful filename generation
    filename = processor.generate_filename("Sample OCR text")
    assert filename == "Generated Filename"
    
    # Test API error handling
    mock_requests.side_effect = Exception("API Error")
    filename = processor.generate_filename("Sample OCR text")
    assert filename == "" 