import os
import click
import logging
from pathlib import Path
from typing import Dict, Any
from rich.console import Console
from rich.table import Table
from ..utils.config import Config
from ..utils.logging import setup_logging
from ..core.database import Database
from ..core.pdf_processor import PDFProcessor
from ..core.organization import DocumentOrganizer
from ..llm.provider import LLMProvider

console = Console()

def init_components(config_path: str) -> tuple[Config, Database, PDFProcessor, DocumentOrganizer]:
    """Initialize all required components."""
    config = Config(config_path)
    db = Database(config['database.path'])
    llm = LLMProvider(config['llm'], db)
    processor = PDFProcessor(config, llm)
    organizer = DocumentOrganizer(config, db)
    return config, db, processor, organizer

@click.group()
@click.option('--config', '-c', type=str, help='Path to config file')
@click.option('--debug/--no-debug', default=False, help='Enable debug logging')
@click.pass_context
def cli(ctx: click.Context, config: str, debug: bool):
    """PDF Manager - Intelligent document management system."""
    setup_logging(debug=debug)
    try:
        ctx.obj = init_components(config)
    except Exception as e:
        console.print(f"[red]Failed to initialize: {e}[/red]")
        ctx.exit(1)

@cli.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('--recursive/--no-recursive', '-r', default=False,
              help='Process directory recursively')
@click.pass_obj
def process(components: tuple, path: str, recursive: bool):
    """Process PDF files and extract information."""
    config, db, processor, organizer = components
    path = Path(path)

    try:
        if path.is_file():
            files = [path]
        else:
            pattern = '**/*.pdf' if recursive else '*.pdf'
            files = list(path.glob(pattern))

        with click.progressbar(files, label='Processing files') as progress_files:
            for file in progress_files:
                try:
                    # Process file
                    result = processor.process_pdf(str(file))
                    
                    # Add to database
                    doc_id = db.add_document(
                        filename=file.name,
                        path=str(file),
                        hash=result['hash'],
                        content_summary=result.get('summary')
                    )
                    
                    # Add metadata
                    if result.get('metadata'):
                        db.add_metadata(doc_id, result['metadata'])
                    
                    # Organize document
                    organizer.organize_document(
                        doc_id,
                        str(file),
                        result.get('categories', []),
                        result.get('tags', [])
                    )

                except Exception as e:
                    logging.error(f"Failed to process {file}: {e}")

    except Exception as e:
        console.print(f"[red]Processing failed: {e}[/red]")

@cli.command()
@click.argument('query', type=str)
@click.pass_obj
def search(components: tuple, query: str):
    """Search for documents in the library."""
    _, db, _, _ = components

    try:
        results = db.search_documents(query)
        
        if not results:
            console.print("No matching documents found.")
            return

        table = Table(show_header=True)
        table.add_column("ID")
        table.add_column("Filename")
        table.add_column("Path")
        table.add_column("Summary")

        for doc in results:
            table.add_row(
                str(doc['id']),
                doc['filename'],
                doc['path'],
                doc.get('content_summary', '')[:100] + '...'
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Search failed: {e}[/red]")

@cli.command()
@click.argument('doc_id', type=int)
@click.argument('tags', nargs=-1)
@click.pass_obj
def tag(components: tuple, doc_id: int, tags: tuple):
    """Add tags to a document."""
    _, db, _, _ = components

    try:
        db.add_tags(doc_id, list(tags))
        console.print(f"[green]Added tags to document {doc_id}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to add tags: {e}[/red]")

@cli.command()
@click.option('--force/--no-force', default=False,
              help='Force reorganization of all files')
@click.pass_obj
def organize(components: tuple, force: bool):
    """Organize or reorganize the document library."""
    _, _, _, organizer = components

    try:
        stats = organizer.reorganize_library()
        
        table = Table(show_header=True)
        table.add_column("Metric")
        table.add_column("Count")
        
        table.add_row("Processed", str(stats['processed']))
        table.add_row("Failed", str(stats['failed']))
        table.add_row("Skipped", str(stats['skipped']))
        
        console.print(table)

    except Exception as e:
        console.print(f"[red]Organization failed: {e}[/red]")

@cli.command()
@click.pass_obj
def stats(components: tuple):
    """Show library statistics."""
    _, _, _, organizer = components

    try:
        stats = organizer.get_organization_stats()
        
        # Document stats
        console.print("\n[bold]Document Statistics[/bold]")
        doc_table = Table(show_header=True)
        doc_table.add_column("Metric")
        doc_table.add_column("Value")
        doc_table.add_row("Total Documents", str(stats['total_docs']))
        doc_table.add_row("Unique Paths", str(stats['unique_paths']))
        console.print(doc_table)
        
        # Category distribution
        console.print("\n[bold]Top Categories[/bold]")
        cat_table = Table(show_header=True)
        cat_table.add_column("Category")
        cat_table.add_column("Count")
        for cat, count in list(stats['categories'].items())[:10]:
            cat_table.add_row(cat, str(count))
        console.print(cat_table)
        
        # Tag distribution
        console.print("\n[bold]Top Tags[/bold]")
        tag_table = Table(show_header=True)
        tag_table.add_column("Tag")
        tag_table.add_column("Count")
        for tag, count in list(stats['tags'].items())[:10]:
            tag_table.add_row(tag, str(count))
        console.print(tag_table)

    except Exception as e:
        console.print(f"[red]Failed to get statistics: {e}[/red]")

@cli.command()
@click.pass_obj
def cleanup(components: tuple):
    """Clean up missing files from the database."""
    _, _, _, organizer = components

    try:
        stats = organizer.cleanup_missing_files()
        console.print(f"Removed {stats['removed']} entries, {stats['errors']} errors")
    except Exception as e:
        console.print(f"[red]Cleanup failed: {e}[/red]")

if __name__ == '__main__':
    cli()
