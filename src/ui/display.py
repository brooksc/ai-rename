"""Display utilities for UI."""

from pathlib import Path

from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

console = Console()

def display_file_info(file_path: Path, content: str) -> None:
    """Display file information.

    Args:
        file_path: Path to file
        content: File content preview
    """
    console.print(f"\n[bold]File:[/bold] {file_path}")

    # Show preview with syntax highlighting
    syntax = Syntax(content, "text", theme="monokai")
    console.print(Panel(syntax, title="Content Preview"))

def display_help(help_text: str | None = None) -> None:
    """Display help information.

    Args:
        help_text: Optional custom help text
    """
    default_help = """
    Available commands:
    ? - Show help
    b - Batch accept remaining
    e - Edit suggestion
    n - Skip file
    q - Quit program
    u - Undo last operation
    v - View file contents
    y - Accept suggestion
    """

    text = help_text if help_text else default_help
    console.print(Panel(text, title="Help"))

def display_error(message: str) -> None:
    """Display error message.

    Args:
        message: Error message
    """
    console.print(f"[red]Error:[/red] {message}")

def display_progress(current: int, total: int, message: str = "Processing") -> None:
    """Display progress bar.

    Args:
        current: Current progress
        total: Total items
        message: Progress message
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})")
    ) as progress:
        task = progress.add_task(message, total=total)
        progress.update(task, completed=current)

def display_batch_summary(operations: list[tuple[Path, dict]]) -> None:
    """Display batch operation summary.

    Args:
        operations: List of (path, suggestion) pairs
    """
    table = Table(title="Batch Operation Summary")
    table.add_column("Original Path")
    table.add_column("New Path")
    table.add_column("Reasoning")

    for path, suggestion in operations:
        table.add_row(
            str(path),
            suggestion["suggested_path"],
            suggestion["reasoning"]
        )

    console.print(table)

def display_diff(old_path: Path, new_path: Path, changes: dict[str, str]) -> None:
    """Display diff between old and new paths.

    Args:
        old_path: Original path
        new_path: New path
        changes: Dict of changes with descriptions
    """
    table = Table(title="Path Changes")
    table.add_column("Component", style="bold")
    table.add_column("Original", style="red")
    table.add_column("New", style="green")
    table.add_column("Reason", style="yellow")

    for component, reason in changes.items():
        old_value = getattr(old_path, component, '')
        new_value = getattr(new_path, component, '')
        if old_value != new_value:
            table.add_row(component, str(old_value), str(new_value), reason)

    console.print(table)

def display_external_preview(path: Path, editor: str = 'less') -> None:
    """Display file in external viewer.

    Args:
        path: Path to file
        editor: Editor command to use
    """
    import subprocess
    try:
        subprocess.run([editor, str(path)])
    except Exception as e:
        logger.error(f"Failed to open external viewer: {e}")
        display_error(f"Could not open {editor}: {e}")
