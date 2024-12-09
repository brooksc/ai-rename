import pytest
import os
import yaml
import argparse
from ai_rename import read_config, write_config, create_config, parse_arguments, setup_logging

def test_read_config(temp_dir):
    """Test configuration file reading."""
    config_file = os.path.join(temp_dir, 'config.yaml')
    test_config = {
        'LANGUAGE': 'eng',
        'ORIG_SUBDIR': 'test_orig',
        'API_TOKEN': 'test_token',
        'API_BASE': 'http://test.api',
        'MODEL': 'test_model'
    }
    
    # Test successful config reading
    with open(config_file, 'w') as f:
        yaml.dump(test_config, f)
    
    config = read_config()
    assert config['LANGUAGE'] == 'eng'
    assert config['ORIG_SUBDIR'] == 'test_orig'
    assert config['API_TOKEN'] == 'test_token'
    
    # Test missing config file
    os.remove(config_file)
    config = read_config()
    assert config == {}
    
    # Test invalid config file
    with open(config_file, 'w') as f:
        f.write('invalid: yaml: content:')
    config = read_config()
    assert config == {}

def test_write_config(temp_dir):
    """Test configuration file writing."""
    test_config = {
        'LANGUAGE': 'eng',
        'ORIG_SUBDIR': 'test_orig'
    }
    
    write_config(test_config)
    
    # Verify config was written correctly
    with open('config.yaml', 'r') as f:
        saved_config = yaml.safe_load(f)
    
    assert saved_config['LANGUAGE'] == test_config['LANGUAGE']
    assert saved_config['ORIG_SUBDIR'] == test_config['ORIG_SUBDIR']

def test_create_config(monkeypatch):
    """Test configuration creation from user input."""
    # Mock user inputs
    inputs = iter(['fra', 'custom_orig'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    
    config = create_config()
    
    assert config['LANGUAGE'] == 'fra'
    assert config['ORIG_SUBDIR'] == 'custom_orig'
    
    # Test default values
    inputs = iter(['', ''])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    
    config = create_config()
    
    assert config['LANGUAGE'] == 'eng'
    assert config['ORIG_SUBDIR'] == 'orig'

def test_parse_arguments():
    """Test command line argument parsing."""
    # Test with directory
    args = parse_arguments(['test_dir'])
    assert args.directory == 'test_dir'
    assert not args.dry_run
    assert not args.rename
    assert not args.move
    assert not args.copy
    assert not args.summarize
    assert not args.debug
    
    # Test with all flags
    args = parse_arguments([
        'test_dir',
        '-n',
        '-r',
        '-m',
        '-c',
        '-s',
        '-d',
        '--progress-bar',
        '--keep-original',
        '--model', 'custom_model'
    ])
    assert args.directory == 'test_dir'
    assert args.dry_run
    assert args.rename
    assert args.move
    assert args.copy
    assert args.summarize
    assert args.debug
    assert args.progress_bar
    assert args.keep_original
    assert args.model == 'custom_model'
    
    # Test LLM test mode
    args = parse_arguments(['-t'])
    assert args.test_llm
    assert args.directory is None

def test_setup_logging(temp_dir, caplog):
    """Test logging setup."""
    # Test debug mode
    setup_logging(True)
    assert caplog.get_records('debug')
    
    # Test info mode
    setup_logging(False)
    assert not caplog.get_records('debug')
    
    # Verify log file creation
    assert os.path.exists('file_processor.log') 