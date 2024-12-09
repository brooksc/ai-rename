import pytest
import os
import shutil
from ai_rename import FileProcessor

def test_setup_directories(temp_dir, sample_config):
    """Test directory setup functionality."""
    args = type('Args', (), {'rename': True, 'move': False})()
    processor = FileProcessor(sample_config, args)
    
    dirs = processor.setup_directories(temp_dir)
    
    assert os.path.exists(os.path.join(temp_dir, 'done'))
    assert os.path.exists(os.path.join(temp_dir, sample_config['ORIG_SUBDIR']))
    assert dirs['DONE_DIR'] == os.path.join(temp_dir, 'done')
    assert dirs['ORIG_DIR'] == os.path.join(temp_dir, sample_config['ORIG_SUBDIR'])

def test_create_directory(temp_dir, sample_config):
    """Test directory creation functionality."""
    processor = FileProcessor(sample_config, None)
    
    test_dir = os.path.join(temp_dir, 'test_dir')
    processor.create_directory(test_dir)
    assert os.path.exists(test_dir)
    
    # Test creating existing directory
    processor.create_directory(test_dir)
    assert os.path.exists(test_dir)

def test_move_or_copy_file(temp_dir, sample_config):
    """Test file moving and copying functionality."""
    # Setup test files and directories
    source_file = os.path.join(temp_dir, 'source.txt')
    with open(source_file, 'w') as f:
        f.write('test content')
    
    target_dir = os.path.join(temp_dir, 'target')
    os.makedirs(target_dir)
    
    # Test move operation
    args = type('Args', (), {
        'move': True, 
        'copy': False, 
        'dry_run': False
    })()
    processor = FileProcessor(sample_config, args)
    
    new_path = os.path.join(target_dir, 'moved.txt')
    processor.move_or_copy_file(source_file, new_path, target_dir, 'source.txt')
    assert not os.path.exists(source_file)
    assert os.path.exists(new_path)
    
    # Test copy operation
    source_file = os.path.join(temp_dir, 'source2.txt')
    with open(source_file, 'w') as f:
        f.write('test content')
    
    args = type('Args', (), {
        'move': False, 
        'copy': True, 
        'dry_run': False
    })()
    processor = FileProcessor(sample_config, args)
    
    new_path = os.path.join(target_dir, 'copied.txt')
    processor.move_or_copy_file(source_file, new_path, target_dir, 'source2.txt')
    assert os.path.exists(source_file)
    assert os.path.exists(new_path)
    
    # Test dry run
    args = type('Args', (), {
        'move': True, 
        'copy': False, 
        'dry_run': True
    })()
    processor = FileProcessor(sample_config, args)
    
    source_file = os.path.join(temp_dir, 'source3.txt')
    with open(source_file, 'w') as f:
        f.write('test content')
    
    new_path = os.path.join(target_dir, 'dry_run.txt')
    processor.move_or_copy_file(source_file, new_path, target_dir, 'source3.txt')
    assert os.path.exists(source_file)
    assert not os.path.exists(new_path)

def test_process_files(temp_dir, sample_config, mock_subprocess):
    """Test batch file processing functionality."""
    # Setup test files
    pdf_file = os.path.join(temp_dir, 'test.pdf')
    image_file = os.path.join(temp_dir, 'test.jpg')
    text_file = os.path.join(temp_dir, 'test.txt')
    
    for file in [pdf_file, image_file, text_file]:
        with open(file, 'w') as f:
            f.write('test content')
    
    args = type('Args', (), {
        'rename': True,
        'move': False,
        'progress_bar': True,
        'dry_run': False,
        'debug': True
    })()
    processor = FileProcessor(sample_config, args)
    
    # Mock OCR and filename generation
    mock_subprocess.return_value.stdout = "OCR Text"
    mock_subprocess.return_value.stderr = ""
    
    # Process files
    processor.process_files(temp_dir)
    
    # Verify only PDF and image files were processed
    done_dir = os.path.join(temp_dir, 'done')
    processed_files = os.listdir(done_dir)
    assert len(processed_files) == 2  # PDF and JPG
    assert os.path.exists(text_file)  # Text file should remain unprocessed 