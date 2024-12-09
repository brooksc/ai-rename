import pytest
from click.testing import CliRunner
from pdf_manager.cli.commands import cli

@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()

def test_cli_help(runner):
    """Test CLI help command."""
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Commands:' in result.output
    assert 'process' in result.output
    assert 'search' in result.output

def test_cli_process_command(runner, sample_pdf, test_config):
    """Test processing a single file."""
    with runner.isolated_filesystem():
        result = runner.invoke(cli, [
            '--config', str(test_config),
            'process',
            str(sample_pdf)
        ])
        assert result.exit_code == 0
        assert 'Processing files' in result.output

def test_cli_process_directory(runner, test_dir, test_config):
    """Test processing a directory of files."""
    # Create test PDFs
    for i in range(3):
        pdf_path = test_dir / f"test_{i}.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\ntest content")
    
    result = runner.invoke(cli, [
        '--config', str(test_config),
        'process',
        '--recursive',
        str(test_dir)
    ])
    assert result.exit_code == 0
    assert 'Processing files' in result.output

def test_cli_search_command(runner, test_config, test_db):
    """Test search functionality."""
    # Add test document to database
    doc_id = test_db.add_document(
        filename="test.pdf",
        path="/test/path.pdf",
        hash="123",
        content_summary="This is a test document about Python"
    )
    test_db.add_tags(doc_id, ['test', 'python'])
    
    result = runner.invoke(cli, [
        '--config', str(test_config),
        'search',
        'Python'
    ])
    assert result.exit_code == 0
    assert 'test.pdf' in result.output

def test_cli_tag_command(runner, test_config, test_db):
    """Test adding tags to a document."""
    doc_id = test_db.add_document(
        filename="test.pdf",
        path="/test/path.pdf",
        hash="123"
    )
    
    result = runner.invoke(cli, [
        '--config', str(test_config),
        'tag',
        str(doc_id),
        'important',
        'test'
    ])
    assert result.exit_code == 0
    assert 'Added tags' in result.output

def test_cli_organize_command(runner, test_config):
    """Test library organization command."""
    result = runner.invoke(cli, [
        '--config', str(test_config),
        'organize'
    ])
    assert result.exit_code == 0
    assert 'Processed' in result.output

def test_cli_stats_command(runner, test_config, test_db):
    """Test statistics command."""
    # Add some test data
    doc_id = test_db.add_document(
        filename="test.pdf",
        path="/test/path.pdf",
        hash="123"
    )
    test_db.add_tags(doc_id, ['test'])
    
    result = runner.invoke(cli, [
        '--config', str(test_config),
        'stats'
    ])
    assert result.exit_code == 0
    assert 'Document Statistics' in result.output
    assert 'Top Tags' in result.output

def test_cli_cleanup_command(runner, test_config):
    """Test cleanup command."""
    result = runner.invoke(cli, [
        '--config', str(test_config),
        'cleanup'
    ])
    assert result.exit_code == 0
    assert 'Removed' in result.output

def test_cli_invalid_config(runner):
    """Test handling of invalid configuration."""
    result = runner.invoke(cli, [
        '--config', 'nonexistent.yaml',
        'process',
        'test.pdf'
    ])
    assert result.exit_code != 0
    assert 'Error' in result.output

def test_cli_debug_mode(runner, test_config, sample_pdf):
    """Test debug mode output."""
    result = runner.invoke(cli, [
        '--config', str(test_config),
        '--debug',
        'process',
        str(sample_pdf)
    ])
    assert result.exit_code == 0
    assert '[DEBUG]' in result.output 