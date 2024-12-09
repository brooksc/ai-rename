#!/usr/bin/env python3

import os
import shutil
import logging
from pathlib import Path
import yaml
from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()

def setup_logging():
    """Set up basic logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[logging.StreamHandler()]
    )

def create_config(config_path: Path) -> None:
    """Create configuration file from example."""
    example_path = Path(__file__).parent.parent / "config.yaml.example"
    
    if not example_path.exists():
        console.print("[red]Error: config.yaml.example not found[/red]")
        return
    
    # Read example config
    with open(example_path) as f:
        config = yaml.safe_load(f)
    
    # Customize paths
    library_path = Prompt.ask(
        "Enter path for PDF library",
        default=os.path.expanduser("~/Documents/PDFLibrary")
    )
    config['paths']['library'] = library_path
    config['paths']['backup'] = str(Path(library_path) / "backups")
    config['paths']['temp'] = str(Path(library_path) / "temp")
    
    # LLM settings
    if Confirm.ask("Do you want to use OpenAI's GPT-4?", default=True):
        config['llm']['provider'] = 'openai'
        config['llm']['model'] = 'gpt-4'
    else:
        provider = Prompt.ask("Enter LLM provider", choices=['openai', 'anthropic'], default='anthropic')
        config['llm']['provider'] = provider
        if provider == 'anthropic':
            config['llm']['model'] = 'claude-3-opus'
        else:
            config['llm']['model'] = 'gpt-3.5-turbo'
    
    # Cache settings
    config['llm']['cache']['directory'] = str(Path(library_path) / "llm_cache")
    
    # Database path
    config['database']['path'] = str(Path(library_path) / "library.db")
    
    # Write configuration
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    console.print(f"[green]Configuration written to {config_path}[/green]")

def create_directories(config_path: Path) -> None:
    """Create necessary directories based on configuration."""
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        paths = [
            config['paths']['library'],
            config['paths']['backup'],
            config['paths']['temp'],
            config['llm']['cache']['directory']
        ]
        
        for path in paths:
            path = os.path.expanduser(path)
            Path(path).mkdir(parents=True, exist_ok=True)
            console.print(f"[green]Created directory: {path}[/green]")
    
    except Exception as e:
        console.print(f"[red]Error creating directories: {e}[/red]")

def check_dependencies() -> bool:
    """Check if required external dependencies are installed."""
    try:
        import pytesseract
        return True
    except ImportError:
        console.print("[yellow]Warning: pytesseract not found. OCR features will be disabled.[/yellow]")
        return False

def main():
    """Initialize the PDF Manager environment."""
    setup_logging()
    console.print("[bold]PDF Manager - Environment Setup[/bold]\n")
    
    # Determine config path
    config_dir = os.getenv("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    config_path = Path(config_dir) / "pdf-manager" / "config.yaml"
    
    # Create configuration
    if config_path.exists():
        if Confirm.ask(f"Configuration file already exists at {config_path}. Overwrite?", default=False):
            create_config(config_path)
    else:
        create_config(config_path)
    
    # Create directories
    if config_path.exists():
        create_directories(config_path)
    
    # Check dependencies
    check_dependencies()
    
    console.print("\n[bold green]Setup complete![/bold green]")
    console.print("\nNext steps:")
    console.print("1. Set up your API keys in environment variables:")
    console.print("   export OPENAI_API_KEY=your_key_here")
    console.print("   export ANTHROPIC_API_KEY=your_key_here  # if using Claude")
    console.print("2. Review and customize config.yaml if needed")
    console.print("3. Run 'pdf-manager --help' to see available commands")

if __name__ == "__main__":
    main() 