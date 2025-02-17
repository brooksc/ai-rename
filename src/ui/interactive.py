"""Interactive UI for rename operations."""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich.table import Table

from src.core.file_ops import FileOperationConfig, safe_rename
from src.core.undo import UndoManager
from src.ui.diff import show_diff


class InteractiveUI:
    """Interactive UI for rename operations."""

    def __init__(
        self,
        console: Console | None = None,
        file_config: FileOperationConfig | None = None,
        show_preview: bool = True,
        batch_confirm: bool = False,
        external_editor: str | None = None
    ):
        """Initialize UI.

        Args:
            console: Rich console instance
            file_config: File operation configuration
            show_preview: Whether to show file previews
            batch_confirm: Whether to confirm batch operations
            external_editor: External editor command
        """
        self.console = console or Console()
        self.file_config = file_config or FileOperationConfig()
        self.show_preview = show_preview
        self.batch_confirm = batch_confirm
        self.external_editor = external_editor
        self.progress = None
        self.undo_manager = UndoManager()
        self.batch_mode = False
        self.total_files = 0
        self.processed_files = 0

    def show_help(self) -> None:
        """Show help text."""
        help_text = """
Available commands:
y - Accept suggestion
n - Skip file
e - Edit suggestion
v - View file contents
d - Show diff
b - Batch accept remaining
q - Quit
h - Show this help
"""
        self.console.print(Panel(help_text, title="Help"))

    def show_file_preview(self, path: Path, content: str) -> None:
        """Show file preview.

        Args:
            path: File path
            content: File content
        """
        if not self.show_preview:
            return

        preview = content[:1000] + "..." if len(content) > 1000 else content
        self.console.print(Panel(preview, title=str(path)))

    def show_suggestion(self, current_path: Path, suggestion: dict) -> None:
        """Show rename suggestion.

        Args:
            current_path: Current file path
            suggestion: Suggestion dictionary containing suggested_path and reasoning
        """
        table = Table(show_header=False, box=None)
        table.add_row("Current:", str(current_path))
        table.add_row("Suggested:", suggestion["suggested_path"])
        table.add_row("Reasoning:", suggestion["reasoning"])
        self.console.print(Panel(table, title="Rename Suggestion"))

    def get_command(self) -> str:
        """Get command from user.

        Returns:
            Command string
        """
        cmd_map = {
            'y': 'accept',
            'n': 'skip',
            'e': 'edit',
            'v': 'view',
            'd': 'diff',
            'b': 'batch',
            'q': 'quit',
            'h': 'help'
        }

        while True:
            cmd = Prompt.ask(
                "\nEnter command",
                choices=list(cmd_map.keys()),
                default="y"
            ).lower()

            if cmd in cmd_map:
                return cmd_map[cmd]

            self.console.print("[red]Invalid command. Type 'h' for help.")

    def edit_suggestion(self, suggestion: dict) -> dict | None:
        """Edit suggestion.

        Args:
            suggestion: Current suggestion

        Returns:
            Updated suggestion or None if cancelled
        """
        try:
            new_path = Prompt.ask(
                "Enter new path",
                default=suggestion["suggested_path"]
            )

            if new_path == suggestion["suggested_path"]:
                return suggestion

            updated = suggestion.copy()
            updated["suggested_path"] = new_path
            updated["filename"] = Path(new_path).name
            updated["reasoning"] = "User edited suggestion"
            return updated

        except KeyboardInterrupt:
            return None

    def confirm_quit(self) -> bool:
        """Confirm quit operation.

        Returns:
            Whether to quit
        """
        return Confirm.ask(
            "Are you sure you want to quit?",
            default=False
        )

    def show_progress(self, total: int) -> Progress:
        """Show progress bar.

        Args:
            total: Total number of items

        Returns:
            Progress: Progress bar instance
        """
        self.total_files = total
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})")
        )
        self.progress.add_task("Processing files...", total=total)
        return self.progress

    def update_progress(self, advance: int = 1) -> None:
        """Update progress bar.

        Args:
            advance: Amount to advance
        """
        self.processed_files += advance
        self.console.print(
            f"Progress: {self.processed_files}/{self.total_files} files"
        )

    def process_suggestions(
        self,
        suggestions: list[tuple[Path, dict]],
        preview_content: dict[Path, str] | None = None,
        dry_run: bool = False
    ) -> list[tuple[Path, Path]]:
        """Process rename suggestions.

        Args:
            suggestions: List of (current_path, suggestion) tuples
            preview_content: Optional dict mapping paths to preview content
            dry_run: Whether this is a dry run

        Returns:
            List of (source, destination) paths to rename
        """
        approved = []
        show_help = True

        # In batch mode, accept all suggestions
        if self.batch_mode:
            return [(path, Path(sugg['suggested_path']))
                   for path, sugg in suggestions]

        for current_path, suggestion in suggestions:
            if show_help:
                self.show_help()
                show_help = False

            preview = None
            if preview_content and current_path in preview_content:
                preview = preview_content[current_path]

            self.show_suggestion(
                current_path,
                suggestion
            )

            while True:
                cmd = self.get_command()

                if cmd == "help":
                    self.show_help()
                elif cmd == "accept":
                    approved.append((current_path, Path(suggestion['suggested_path'])))
                    break
                elif cmd == "skip":
                    break
                elif cmd == "edit":
                    edited = self.edit_suggestion(suggestion)
                    if edited:
                        approved.append((current_path, Path(edited['suggested_path'])))
                        break
                elif cmd == "view":
                    if preview:
                        self.show_file_preview(current_path, preview)
                elif cmd == "diff":
                    show_diff(
                        self.console,
                        current_path,
                        Path(suggestion['suggested_path']),
                        preview or "",
                        suggestion['reasoning']
                    )
                elif cmd == "quit":
                    if self.confirm_quit():
                        return approved
                elif cmd == "batch":
                    self.batch_mode = True
                    return self.process_suggestions(suggestions, preview_content, dry_run)

        return approved

    def safe_rename(self, src: Path, dst: Path) -> None:
        """Safely rename file.

        Args:
            src: Source path
            dst: Destination path

        Raises:
            OSError: If rename fails
        """
        try:
            # Add to undo history before renaming
            self.undo_manager.add_operation(src, dst)

            # Perform rename using file operations module
            safe_rename(src, dst, self.file_config)

        except Exception as e:
            raise OSError(f"Failed to rename {src} to {dst}") from e

    def undo_last_operation(self) -> None:
        """Undo last rename operation."""
        try:
            result = self.undo_manager.undo_last()
            if result:
                original_path, current_path = result
                self.console.print(f"[green]Restored {original_path}")
                self.console.print(f"[green]Previous path was {current_path}")
            else:
                self.console.print("[yellow]No operations to undo")
        except Exception as e:
            self.console.print(f"[red]Error: {e!s}")
