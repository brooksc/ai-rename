"""External editor integration."""

import os
import subprocess
import tempfile
from pathlib import Path


class EditorError(Exception):
    """Error when interacting with external editor."""
    pass

def find_editor() -> str:
    """Find a suitable text editor."""
    # Check environment variables
    if 'EDITOR' in os.environ:
        editor = os.environ['EDITOR']
        if os.path.isfile(editor) and os.access(editor, os.X_OK):
            return editor

    # Try common editors with full paths
    common_editors = [
        '/usr/bin/nano',
        '/usr/bin/vim',
        '/usr/bin/vi',
        '/usr/local/bin/nano',
        '/usr/local/bin/vim',
        '/usr/local/bin/vi'
    ]

    for editor in common_editors:
        if os.path.isfile(editor) and os.access(editor, os.X_OK):
            return editor

    raise EditorError("No suitable text editor found")

def edit_file(editor: str, temp_path: Path) -> str:
    """Edit a file using the specified editor."""
    if not os.path.isfile(editor):
        raise EditorError(f"Editor not found: {editor}")

    if not os.access(editor, os.X_OK):
        raise EditorError(f"Editor is not executable: {editor}")

    try:
        subprocess.run(
            [editor, str(temp_path)],
            check=True,
            timeout=300  # 5 minute timeout
        )
        return temp_path.read_text()
    except subprocess.CalledProcessError as e:
        raise EditorError(f"Failed to run editor: {e}") from e
    except Exception as e:
        raise EditorError(f"Editor error: {e}") from e

def open_in_editor(content: str,
                  suffix: str | None = None) -> str:
    """Open content in external editor.

    Args:
        content: Initial content
        suffix: Optional file suffix for syntax highlighting

    Returns:
        str: Modified content

    Raises:
        EditorError: If editor interaction fails
    """
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as temp_file:
            temp_file.write(content)
            temp_file.flush()

            editor = os.environ.get('EDITOR', 'vim')
            subprocess.run([editor, temp_file.name], check=True)

            with open(temp_file.name) as f:
                return f.read()

    except subprocess.CalledProcessError:
        raise
    except Exception as e:
        raise EditorError("Editor error") from e

def preview_in_editor(file_path: Path) -> None:
    """Preview file in external editor.

    Args:
        file_path: Path to file

    Raises:
        EditorError: If editor interaction fails
    """
    try:
        editor = os.environ.get('EDITOR', 'vim')
        subprocess.run([editor, str(file_path)], check=True)
    except subprocess.CalledProcessError:
        raise
    except Exception as e:
        raise EditorError("Editor error") from e

def edit_suggestion(suggestion: str) -> str:
    """Edit rename suggestion in external editor.

    Args:
        suggestion: Current suggestion

    Returns:
        str: Modified suggestion

    Raises:
        EditorError: If editor interaction fails
    """
    try:
        return open_in_editor(suggestion, suffix='.json')
    except subprocess.CalledProcessError:
        raise
    except Exception as e:
        raise EditorError("Failed to edit suggestion") from e
