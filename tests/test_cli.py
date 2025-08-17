"""Tests for CLI functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from src.cli import cli, setup_logging
from src.core.exceptions import DiagnosticsError


class TestCLI:
    """Tests for CLI command interface."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_cli_help(self):
        """Test CLI help command."""
        result = self.runner.invoke(cli, ['--help'])
        
        assert result.exit_code == 0
        assert "AI-powered file renaming tool" in result.output
        assert "--config" in result.output
        assert "--debug" in result.output
        assert "--dry-run" in result.output

    def test_cli_no_paths_provided(self):
        """Test CLI with no file paths provided."""
        with patch('src.cli.load_config'), patch('src.cli.LLMClient'):
            result = self.runner.invoke(cli, [])
            
            assert result.exit_code == 1
            assert "No paths provided" in result.output

    def test_cli_create_config(self):
        """Test CLI create config option."""
        with patch('src.cli.create_default_config') as mock_create:
            result = self.runner.invoke(cli, ['--create-config'])
            
            assert result.exit_code == 0
            mock_create.assert_called_once()

    def test_cli_diagnostics_success(self):
        """Test CLI diagnostics with successful checks."""
        mock_results = {
            "status": True,
            "api_check": {"status": "ok", "message": "API connection successful"},
            "config_check": {"status": "ok", "message": "Configuration valid"}
        }
        
        with patch('src.cli.create_default_config') as mock_config:
            with patch('src.cli.run_diagnostics', return_value=mock_results):
                result = self.runner.invoke(cli, ['--diag'])
                
                assert result.exit_code == 0
                assert "All diagnostics passed" in result.output

    def test_cli_diagnostics_failure(self):
        """Test CLI diagnostics with failed checks."""
        mock_results = {
            "status": False,
            "api_check": {"status": "error", "message": "API connection failed"},
            "config_check": {"status": "ok", "message": "Configuration valid"}
        }
        
        with patch('src.cli.create_default_config'):
            with patch('src.cli.run_diagnostics', return_value=mock_results):
                result = self.runner.invoke(cli, ['--diag'])
                
                assert result.exit_code == 1
                assert "Some diagnostics failed" in result.output

    def test_cli_diagnostics_error(self):
        """Test CLI diagnostics with exception."""
        with patch('src.cli.create_default_config'):
            with patch('src.cli.run_diagnostics', side_effect=DiagnosticsError("Diagnostics failed")):
                result = self.runner.invoke(cli, ['--diag'])
                
                assert result.exit_code == 1
                assert "Diagnostics failed" in result.output

    def test_cli_with_config_file(self, temp_dir):
        """Test CLI with custom config file."""
        config_file = temp_dir / "test_config.yaml"
        config_file.write_text("""
gemini:
  api_key: test-key
  model: gemini-2.0-flash
""")
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        with patch('src.cli.load_config') as mock_load:
            with patch('src.cli.LLMClient'):
                with patch('src.cli.rename_files'):
                    result = self.runner.invoke(cli, [
                        '--config', str(config_file),
                        str(test_file)
                    ])
                    
                    mock_load.assert_called_once_with(config_file)

    def test_cli_with_gemini_options(self, temp_dir):
        """Test CLI with Gemini API options."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        with patch('src.cli.create_default_config'):
            with patch('src.cli.LLMClient') as mock_llm:
                with patch('src.cli.rename_files'):
                    result = self.runner.invoke(cli, [
                        '--gemini-key', 'custom-key',
                        '--gemini-model', 'gemini-1.5-pro',
                        str(test_file)
                    ])
                    
                    # Should create LLM client with custom options
                    mock_llm.assert_called_once()
                    call_kwargs = mock_llm.call_args[1]
                    assert call_kwargs['api_key'] == 'custom-key'
                    assert call_kwargs['model'] == 'gemini-1.5-pro'

    def test_cli_recursive_flag(self, temp_dir):
        """Test CLI with recursive flag."""
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        
        with patch('src.cli.create_default_config'):
            with patch('src.cli.LLMClient'):
                with patch('src.cli.rename_files') as mock_rename:
                    result = self.runner.invoke(cli, [
                        '--recursive',
                        str(temp_dir)
                    ])
                    
                    # Should call rename_files with recursive=True
                    mock_rename.assert_called_once()
                    call_kwargs = mock_rename.call_args[1]
                    assert call_kwargs['recursive'] is True

    def test_cli_dry_run_flag(self, temp_dir):
        """Test CLI with dry run flag."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        with patch('src.cli.create_default_config'):
            with patch('src.cli.LLMClient'):
                with patch('src.cli.rename_files') as mock_rename:
                    result = self.runner.invoke(cli, [
                        '--dry-run',
                        str(test_file)
                    ])
                    
                    # Should call rename_files with dry_run=True
                    mock_rename.assert_called_once()
                    call_kwargs = mock_rename.call_args[1]
                    assert call_kwargs['dry_run'] is True

    def test_cli_taxonomy_option(self, temp_dir):
        """Test CLI with taxonomy file option."""
        taxonomy_file = temp_dir / "taxonomy.md"
        taxonomy_file.write_text("# Test taxonomy")
        
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        with patch('src.cli.create_default_config'):
            with patch('src.cli.LLMClient'):
                with patch('src.cli.rename_files') as mock_rename:
                    result = self.runner.invoke(cli, [
                        '--taxonomy', str(taxonomy_file),
                        str(test_file)
                    ])
                    
                    # Should call rename_files with taxonomy file
                    mock_rename.assert_called_once()
                    call_kwargs = mock_rename.call_args[1]
                    assert call_kwargs['taxonomy_file'] == taxonomy_file

    def test_cli_output_directory(self, temp_dir):
        """Test CLI with output directory option."""
        output_dir = temp_dir / "output"
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        with patch('src.cli.create_default_config'):
            with patch('src.cli.LLMClient'):
                with patch('src.cli.rename_files') as mock_rename:
                    result = self.runner.invoke(cli, [
                        '--output', str(output_dir),
                        str(test_file)
                    ])
                    
                    # Should call rename_files with output directory
                    mock_rename.assert_called_once()
                    call_kwargs = mock_rename.call_args[1]
                    assert call_kwargs['output_dir'] == output_dir

    def test_cli_promptjson_flag(self, temp_dir):
        """Test CLI with promptjson flag."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        with patch('src.cli.create_default_config'):
            with patch('src.cli.LLMClient'):
                with patch('src.cli.rename_files') as mock_rename:
                    result = self.runner.invoke(cli, [
                        '--promptjson',
                        str(test_file)
                    ])
                    
                    # Should call rename_files with promptjson=True
                    mock_rename.assert_called_once()
                    call_kwargs = mock_rename.call_args[1]
                    assert call_kwargs['promptjson'] is True

    def test_cli_autoaccept_flag(self, temp_dir):
        """Test CLI with autoaccept flag."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        with patch('src.cli.create_default_config'):
            with patch('src.cli.LLMClient'):
                with patch('src.cli.rename_files') as mock_rename:
                    result = self.runner.invoke(cli, [
                        '--autoaccept',
                        str(test_file)
                    ])
                    
                    # Should call rename_files with autoaccept=True
                    mock_rename.assert_called_once()
                    call_kwargs = mock_rename.call_args[1]
                    assert call_kwargs['autoaccept'] is True

    def test_cli_debug_flag(self, temp_dir):
        """Test CLI with debug flag."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        with patch('src.cli.setup_logging') as mock_setup_logging:
            with patch('src.cli.create_default_config'):
                with patch('src.cli.LLMClient'):
                    with patch('src.cli.rename_files'):
                        result = self.runner.invoke(cli, [
                            '--debug',
                            str(test_file)
                        ])
                        
                        # Should setup logging with debug=True
                        mock_setup_logging.assert_called_once_with(True)

    def test_cli_exception_handling(self, temp_dir):
        """Test CLI exception handling."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        with patch('src.cli.create_default_config'):
            with patch('src.cli.LLMClient'):
                with patch('src.cli.rename_files', side_effect=Exception("Test error")):
                    result = self.runner.invoke(cli, [str(test_file)])
                    
                    assert result.exit_code == 1
                    assert "An error occurred" in result.output

    def test_cli_exception_handling_with_debug(self, temp_dir):
        """Test CLI exception handling with debug enabled."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        with patch('src.cli.create_default_config'):
            with patch('src.cli.LLMClient'):
                with patch('src.cli.rename_files', side_effect=Exception("Test error")):
                    result = self.runner.invoke(cli, [
                        '--debug',
                        str(test_file)
                    ])
                    
                    assert result.exit_code == 1
                    # Debug mode should show more detailed error information
                    # (exact output depends on logging implementation)


class TestSetupLogging:
    """Tests for logging setup functionality."""

    def test_setup_logging_debug_mode(self):
        """Test logging setup in debug mode."""
        with patch('src.cli.logger') as mock_logger:
            setup_logging(debug=True)
            
            # Should remove default handler and add debug level
            mock_logger.remove.assert_called_once()
            mock_logger.add.assert_called_once()
            
            # Check that debug level was set
            call_args = mock_logger.add.call_args
            assert call_args[1]['level'] == "DEBUG"

    def test_setup_logging_normal_mode(self):
        """Test logging setup in normal mode."""
        with patch('src.cli.logger') as mock_logger:
            setup_logging(debug=False)
            
            # Should remove default handler and add info level
            mock_logger.remove.assert_called_once()
            mock_logger.add.assert_called_once()
            
            # Check that info level was set
            call_args = mock_logger.add.call_args
            assert call_args[1]['level'] == "INFO"


class TestCLIFileHandling:
    """Tests for CLI file path handling."""

    def test_cli_with_multiple_files(self, temp_dir):
        """Test CLI with multiple file arguments."""
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("content 1")
        file2.write_text("content 2")
        
        with patch('src.cli.create_default_config'):
            with patch('src.cli.LLMClient'):
                with patch('src.cli.rename_files') as mock_rename:
                    result = self.runner.invoke(cli, [
                        str(file1),
                        str(file2)
                    ])
                    
                    # Should call rename_files with both files
                    mock_rename.assert_called_once()
                    call_args = mock_rename.call_args[1]
                    paths = call_args['paths']
                    assert len(paths) == 2
                    assert file1 in paths
                    assert file2 in paths

    def test_cli_with_nonexistent_file(self, temp_dir):
        """Test CLI with non-existent file path."""
        nonexistent = temp_dir / "nonexistent.txt"
        
        result = self.runner.invoke(cli, [str(nonexistent)])
        
        # Click should handle the file existence check
        assert result.exit_code != 0

    def test_cli_with_glob_patterns(self, temp_dir):
        """Test CLI behavior with glob-like patterns."""
        # Create test files
        for i in range(3):
            test_file = temp_dir / f"test_{i}.txt"
            test_file.write_text(f"content {i}")
        
        # CLI doesn't expand globs itself - that's shell responsibility
        # But we can test with explicit file paths
        test_files = list(temp_dir.glob("test_*.txt"))
        
        with patch('src.cli.create_default_config'):
            with patch('src.cli.LLMClient'):
                with patch('src.cli.rename_files') as mock_rename:
                    result = self.runner.invoke(cli, [str(f) for f in test_files])
                    
                    mock_rename.assert_called_once()
                    call_args = mock_rename.call_args[1]
                    assert len(call_args['paths']) == 3