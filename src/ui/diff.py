"""Diff view utilities for displaying file changes."""

from pathlib import Path

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text


def highlight_changes(old: str, new: str) -> tuple[Text, Text]:
    """Highlight differences between two strings.

    Args:
        old: Original string
        new: New string

    Returns:
        tuple: (highlighted_old, highlighted_new)
    """
    # Split into parts
    old_parts = old.split('/')
    new_parts = new.split('/')

    # Create rich text objects
    old_text = Text()
    new_text = Text()

    # Compare parts
    for i, (old_part, new_part) in enumerate(zip(old_parts, new_parts, strict=False)):
        if i > 0:
            old_text.append('/')
            new_text.append('/')

        if old_part != new_part:
            old_text.append(old_part, style="red")
            new_text.append(new_part, style="green")
        else:
            old_text.append(old_part)
            new_text.append(new_part)

    # Add remaining parts
    if len(old_parts) > len(new_parts):
        for part in old_parts[len(new_parts):]:
            old_text.append('/' + part, style="red")
    elif len(new_parts) > len(old_parts):
        for part in new_parts[len(old_parts):]:
            new_text.append('/' + part, style="green")

    return old_text, new_text

def create_diff_table(changes: list[tuple[Path, dict]]) -> Table:
    """Create a table showing file changes.

    Args:
        changes: List of (current_path, suggestion) tuples

    Returns:
        Table: Rich table showing changes
    """
    table = Table(title="File Changes")

    table.add_column("Current Path", style="red")
    table.add_column("New Path", style="green")
    table.add_column("Reasoning")

    for current_path, suggestion in changes:
        old_text, new_text = highlight_changes(
            str(current_path),
            suggestion['suggested_path']
        )
        table.add_row(old_text, new_text, suggestion['reasoning'])

    return table

def show_content_diff(console: Console,
                     current_path: Path,
                     content: str,
                     suggestion: dict) -> None:
    """Show side-by-side diff of file paths and preview.

    Args:
        console: Rich console instance
        current_path: Current file path
        content: File content
        suggestion: Rename suggestion
    """
    # Create path comparison
    old_text, new_text = highlight_changes(
        str(current_path),
        suggestion['suggested_path']
    )

    path_panels = Columns([
        Panel(old_text, title="Current Path"),
        Panel(new_text, title="New Path")
    ])

    # Create content preview
    preview = Syntax(
        content[:1000] + ("..." if len(content) > 1000 else ""),
        "text",
        theme="monokai",
        line_numbers=True
    )

    # Show panels
    console.print(path_panels)
    console.print()
    console.print(Panel(preview, title="Content Preview"))
    console.print()
    console.print(Panel(suggestion['reasoning'], title="Reasoning"))

def show_batch_summary(console: Console,
                      changes: list[tuple[Path, dict]],
                      preview_content: dict[Path, str]) -> None:
    """Show summary of batch changes.

    Args:
        console: Rich console instance
        changes: List of (current_path, suggestion) tuples
        preview_content: Dict mapping paths to content
    """
    # Show overall statistics
    stats = Table(title="Batch Summary")
    stats.add_column("Total Files")
    stats.add_column("Directories Created")
    stats.add_column("Files Skipped")

    unique_dirs = {Path(s['suggested_path']).parent for _, s in changes}
    stats.add_row(
        str(len(changes)),
        str(len(unique_dirs)),
        str(len(preview_content) - len(changes))
    )

    console.print(stats)
    console.print()

    # Show detailed changes
    console.print(create_diff_table(changes))

def show_error_details(console: Console,
                      errors: list[tuple[Path, str]]) -> None:
    """Show detailed error information.

    Args:
        console: Rich console instance
        errors: List of (path, error_message) tuples
    """
    table = Table(title="Errors")
    table.add_column("File")
    table.add_column("Error")

    for path, error in errors:
        table.add_row(str(path), error)

    console.print(table)

def show_diff(console: Console,
             current_path: Path,
             suggested_path: Path,
             content: str,
             reasoning: str) -> None:
    """Show diff between current and suggested paths.

    Args:
        console: Rich console instance
        current_path: Current file path
        suggested_path: Suggested new path
        content: File content
        reasoning: Reasoning for suggestion
    """
    # Create path comparison
    old_text, new_text = highlight_changes(
        str(current_path),
        str(suggested_path)
    )

    path_panels = Columns([
        Panel(old_text, title="Current Path"),
        Panel(new_text, title="New Path")
    ])

    # Create content preview
    preview = Syntax(
        content[:1000] + ("..." if len(content) > 1000 else ""),
        "text",
        theme="monokai",
        line_numbers=True
    )

    # Show panels
    console.print(path_panels)
    console.print()
    console.print(Panel(preview, title="Content Preview"))
    console.print()
    console.print(Panel(reasoning, title="Reasoning"))
