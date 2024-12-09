import pytest
import os
from ai_rename import FileProcessor

def test_perform_pdf_ocr(mock_subprocess, temp_dir, sample_pdf, sample_config):
    """Test OCR processing for PDF files."""
    processor = FileProcessor(sample_config, type('Args', (), {'debug': True})())
    
    # Mock successful OCR
    mock_subprocess.return_value.stdout = "Sample OCR Text"
    mock_subprocess.return_value.stderr = ""
    
    ocr_text = processor.perform_pdf_ocr(sample_pdf)
    assert ocr_text.strip() == "Sample OCR Text"
    
    # Verify correct command calls
    calls = mock_subprocess.call_args_list
    assert len(calls) > 0
    
    # Test error handling
    mock_subprocess.side_effect = Exception("OCR Error")
    ocr_text = processor.perform_pdf_ocr(sample_pdf)
    assert ocr_text.strip() == ""

def test_perform_image_ocr(mock_subprocess, temp_dir, sample_image, sample_config):
    """Test OCR processing for image files."""
    processor = FileProcessor(sample_config, type('Args', (), {'debug': True})())
    
    # Mock successful OCR
    mock_subprocess.return_value.stdout = "Sample Image Text"
    mock_subprocess.return_value.stderr = ""
    
    ocr_text = processor.perform_image_ocr(sample_image)
    assert ocr_text.strip() == "Sample Image Text"
    
    # Test preprocessing commands
    calls = mock_subprocess.call_args_list
    assert len(calls) > 0
    
    # Test error handling
    mock_subprocess.side_effect = Exception("OCR Error")
    ocr_text = processor.perform_image_ocr(sample_image)
    assert ocr_text.strip() == ""

def test_perform_ocr(mock_subprocess, temp_dir, sample_pdf, sample_image, sample_config):
    """Test the main OCR function with different file types."""
    processor = FileProcessor(sample_config, type('Args', (), {'debug': True})())
    
    # Mock successful OCR
    mock_subprocess.return_value.stdout = "OCR Result"
    mock_subprocess.return_value.stderr = ""
    
    # Test PDF OCR
    assert processor.perform_ocr(sample_pdf).strip() == "OCR Result"
    
    # Test image OCR
    assert processor.perform_ocr(sample_image).strip() == "OCR Result"
    
    # Test unsupported file
    unsupported_file = os.path.join(temp_dir, "test.txt")
    with open(unsupported_file, 'w') as f:
        f.write("test")
    assert processor.perform_ocr(unsupported_file).strip() == ""

def test_ocr_caching(mock_subprocess, temp_dir, sample_pdf, sample_config):
    """Test OCR result caching functionality."""
    processor = FileProcessor(sample_config, type('Args', (), {'debug': True})())
    
    # First OCR call
    mock_subprocess.return_value.stdout = "Cached OCR Text"
    mock_subprocess.return_value.stderr = ""
    
    first_result = processor.perform_pdf_ocr(sample_pdf)
    first_calls = len(mock_subprocess.call_args_list)
    
    # Second OCR call (should use cache)
    second_result = processor.perform_pdf_ocr(sample_pdf)
    second_calls = len(mock_subprocess.call_args_list)
    
    assert first_result == second_result
    assert second_calls > first_calls  # Should have additional calls for checking cache

def test_ocr_preprocessing(mock_subprocess, temp_dir, sample_image, sample_config):
    """Test image preprocessing for OCR."""
    processor = FileProcessor(sample_config, type('Args', (), {'debug': True})())
    
    processor.perform_image_ocr(sample_image)
    
    # Verify preprocessing commands were called
    calls = mock_subprocess.call_args_list
    preprocessing_commands = [
        call for call in calls 
        if any(cmd in str(call) for cmd in ['mogrify', 'convert'])
    ]
    assert len(preprocessing_commands) > 0 