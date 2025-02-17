"""Interactive user interface for ai-rename."""

import os
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import click
from loguru import logger
from rich.console import Console
from rich.table import Table

from src.core.llm import LLMClient
from src.core.taxonomy import TaxonomyParser, TaxonomyRule
from src.ui.navigation import NavigationManager


@dataclass
class FileRenameProposal:
    """Proposed file rename operation.

    Args:
        current_path: Current file path
        new_path: Proposed new path
        content_preview: Preview of file content
        reasoning: Explanation for the rename
        taxonomy_rule: Matching taxonomy rule if any
        override_instructions: Optional override instructions that were applied
    """
    current_path: Path
    new_path: Path
    content_preview: str
    reasoning: str
    taxonomy_rule: TaxonomyRule | None = None
    override_instructions: str | None = None


class UserInterface:
    """Interactive user interface."""

    def __init__(self, autoaccept: bool = False):
        """Initialize interface.
        
        Args:
            autoaccept: Whether to automatically accept all rename suggestions
        """
        self.console = Console()
        self.navigation = NavigationManager()
        self.progress = None
        self.total_files = 0
        self.processed_files = 0
        self.status = "Ready"
        self.expanded_paths = set()
        self.autoaccept = autoaccept
        logger.debug(f"UserInterface initialized with autoaccept={autoaccept}")

    def _format_path(self, path: Path) -> str:
        """Format path for display.

        Args:
            path: Path to format

        Returns:
            str: Formatted path
        """
        # Convert to string and replace home directory with ~
        path_str = str(path).replace(str(Path.home()), "~")

        # If path is not expanded, show only the last component
        if path not in self.expanded_paths:
            return f"{path.name} ►"  # Add arrow to indicate it can be expanded
        return path_str

    def _toggle_path_expansion(self, path: Path) -> None:
        """Toggle path expansion state.

        Args:
            path: Path to toggle
        """
        if path in self.expanded_paths:
            self.expanded_paths.remove(path)
        else:
            self.expanded_paths.add(path)

    def _format_path_with_home(self, path: Path) -> str:
        """Format path by replacing home directory with ~ and preserving relative path.

        Args:
            path: Path to format

        Returns:
            str: Formatted path with ~ for home directory and full relative path
        """
        # First replace home directory with ~
        formatted = str(path).replace(str(Path.home()), "~")
        
        # If this is a source file, show the full relative path from the source directory
        if '/source/' in formatted:
            parts = formatted.split('/source/')
            if len(parts) == 2:
                return f"~/pdf/source/{parts[1]}"
        
        return formatted

    def display_proposal(self, proposal: FileRenameProposal, taxonomy_path: Path | None = None) -> None:
        """Display rename proposal to user.

        Args:
            proposal: Rename proposal to display
            taxonomy_path: Taxonomy path for display
        """
        # Print newline to ensure we're on a fresh line after progress
        self.console.print("\n")

        # Display header
        self.console.print(">>> AI-RENAME ================================================")
        self.console.print(">>> Command: rename                        Status: Processing\n")

        # Display current file
        self.console.print(f"Current File: {self._format_path_with_home(proposal.current_path)}\n")

        # Display taxonomy info if available
        if taxonomy_path:
            self.console.print(f"Taxonomy:\n- Using: {self._format_path_with_home(taxonomy_path)}\n")
        
        # Display override if active
        if proposal.override_instructions:
            self.console.print("[yellow]Override Active:[/yellow]")
            self.console.print(f"[yellow]{proposal.override_instructions}[/yellow]\n")

        # Display paths
        self.console.print(f"Old Path/Filename: {self._format_path_with_home(proposal.current_path)}")
        self.console.print(f"New Path/Filename: {self._format_path_with_home(proposal.new_path)}\n")

        # Display reasoning
        self.console.print("Reasoning:")
        self.console.print(proposal.reasoning + "\n")

        # Display commands
        self.console.print("Commands:")
        self.console.print("  A)ccept   V)iew file  T)rash  !)override  ?)ask question  S)kip  Q)uit\n")

        # Display input prompt
        self.console.print(">>> Ready for input: ", end="")

    def get_user_input(self) -> str:
        """Get input from user.

        Returns:
            str: User input
        """
        # If autoaccept is enabled, automatically return 'A'
        logger.debug(f"Getting user input (autoaccept={self.autoaccept})")
        if self.autoaccept:
            logger.debug("Autoaccept enabled, returning 'A'")
            self.console.print("A\n")
            return 'a'  # Return lowercase to match the command handling

        import sys
        import termios
        import tty

        # Save the terminal settings
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            # Set the terminal to raw mode
            tty.setraw(sys.stdin.fileno())
            # Read a single character
            ch = sys.stdin.read(1)
            ch = ch.lower()  # Convert to lowercase immediately
            return ch
        finally:
            # Restore the terminal settings
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            # Print newline since we're in raw mode
            print()

    def view_file(self, path: Path) -> None:
        """Open file in default viewer.

        Args:
            path: Path to file to view
        """
        try:
            if os.name == 'posix':  # macOS/Linux
                subprocess.run(['open', str(path)], check=True)
            elif os.name == 'nt':  # Windows
                os.startfile(str(path))
        except Exception as e:
            logger.error(f"Failed to open file: {e}")

    def ask_question(self, taxonomy: TaxonomyParser) -> None:
        """Handle user question about taxonomy.

        Args:
            taxonomy: Taxonomy parser instance
        """
        try:
            self.console.print("\nExplain how you want the file organized:")
            explanation = click.prompt("", type=str)
            # Log the question for debugging
            logger.debug(f"User question: {explanation}")
            # Generate LLM response for taxonomy update
            llm_client = LLMClient()
            response = llm_client.generate_rename_suggestion(
                content=explanation,
                file_path=Path("taxonomy_update.txt"),
                taxonomy_rules=taxonomy.content
            )
            # Show the proposed changes
            self.console.print("\nProposed changes based on your explanation:")
            self.console.print(response.reasoning)
            if click.confirm("\nWould you like to apply these changes?", default=False):
                # Update taxonomy based on explanation
                taxonomy.update_rules_from_explanation(explanation)
                self.console.print("[green]Taxonomy updated successfully!")
            else:
                self.console.print("[yellow]Changes cancelled.")
        except Exception as e:
            logger.error(f"Failed to process question: {e}")
            self.console.print(f"[red]Error handling question: {e}")
            if click.confirm("\nWould you like to skip this file?", default=True):
                return
            raise

    def move_to_trash(self, file_path: Path) -> bool:
        """Move file to trash folder.

        Args:
            file_path: Path to file to move

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create Trash directory if it doesn't exist
            trash_dir = file_path.parent / 'Trash'
            trash_dir.mkdir(exist_ok=True)
            
            # Generate target path in trash
            target_path = trash_dir / file_path.name
            
            # If file already exists in trash, append timestamp
            if target_path.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                target_path = trash_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            
            # Move file to trash
            shutil.move(str(file_path), str(target_path))
            logger.info(f"Moved {file_path} to trash at {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to move file to trash: {e}")
            self.console.print(f"[red]Error moving file to trash: {e}")
            return False

    def handle_rename(self, proposal: FileRenameProposal, taxonomy: TaxonomyParser,
                     rename_func: Callable[[Path, Path], None]) -> bool:
        """Handle rename operation interaction.

        Args:
            proposal: Rename proposal
            taxonomy: Taxonomy parser
            rename_func: Function to perform rename

        Returns:
            bool: True if should continue, False to quit
        """
        while True:
            self.display_proposal(proposal, taxonomy.path if taxonomy else None)
            # Get user input or auto-accept
            logger.debug(f"Getting user input (autoaccept={self.autoaccept})")
            if self.autoaccept:
                # If autoaccept is enabled, automatically accept the rename
                logger.debug("Autoaccept enabled, skipping user input")
                cmd = 'a'
            else:
                cmd = self.get_user_input()

            if cmd == 'a':
                try:
                    rename_func(proposal.current_path, proposal.new_path)
                    return True
                except Exception as e:
                    logger.error(f"Failed to rename file: {e}")
                    if not click.confirm("Try again?", default=True):
                        return True
            elif cmd == 'v':
                self.view_file(proposal.current_path)
            elif cmd == '?':
                self.ask_question(taxonomy)
            elif cmd == '!':
                # Handle override instructions
                override = self.handle_override()
                if override:
                    # Get new proposal with override
                    try:
                        llm_client = LLMClient()
                        # Preserve any existing capture_dir setting
                        capture_dir = getattr(llm_client, 'capture_dir', None)
                        new_suggestion = llm_client.generate_rename_suggestion(
                            content=proposal.content_preview,
                            file_path=proposal.current_path,
                            taxonomy_rules=taxonomy.content if taxonomy else None,
                            override_instructions=override,
                            capture_dir=capture_dir
                        )
                        # Create new proposal with override
                        proposal = FileRenameProposal(
                            current_path=proposal.current_path,
                            new_path=Path(new_suggestion.suggested_path),
                            content_preview=proposal.content_preview,
                            reasoning=new_suggestion.reasoning,
                            taxonomy_rule=proposal.taxonomy_rule,
                            override_instructions=override
                        )
                        continue
                    except Exception as e:
                        logger.error(f"Failed to generate new proposal with override: {e}")
                        self.console.print(f"[red]Error generating new proposal: {e}")
            elif cmd == 's':
                return True
            elif cmd == 't':
                if self.move_to_trash(proposal.current_path):
                    return True
            elif cmd == 'q':
                return False
            else:
                logger.error("Invalid command")

    def display_progress(self, processed: int, total: int) -> None:
        """Display progress information.

        Args:
            processed: Current progress
            total: Total items
        """
        self.console.print(f"Progress: {processed}/{total} files processed", end="\r")

    def display_summary(self, total: int, renamed: int, skipped: int, failed: int) -> None:
        """Display operation summary.

        Args:
            total: Total files processed
            renamed: Files successfully renamed
            skipped: Files skipped
            failed: Files that failed
        """
        table = Table(show_header=False, title="Operation Summary")
        table.add_row("Total Processed:", str(total))
        table.add_row("Successfully Renamed:", str(renamed))
        table.add_row("Skipped:", str(skipped))
        table.add_row("Failed:", str(failed))
        self.console.print(table)

    def handle_override(self) -> str | None:
        """Handle user override prompt.

        Returns:
            str | None: Override instructions if provided, None if cancelled
        """
        self.console.print("\n[yellow]Enter override instructions (empty to cancel):")
        override = click.prompt("", type=str, default="", show_default=False)
        if not override.strip():
            self.console.print("[yellow]Override cancelled")
            return None
        return override.strip()
