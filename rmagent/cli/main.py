"""
RMAgent CLI - Command-line interface for RootsMagic AI agent.

Provides commands for querying persons, generating biographies, running data
quality checks, asking questions, generating timelines, and exporting to Hugo.
"""

import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.logging import RichHandler

from rmagent.config.config import load_app_config
from rmagent.rmlib.database import RMDatabase

# Initialize Rich console for formatted output
console = Console()


# Global context for passing shared objects between commands
class CLIContext:
    """Shared context for CLI commands."""

    def __init__(
        self,
        database_path: Path | None = None,
        llm_provider: str | None = None,
        verbose: bool = False,
    ):
        self.database_path = database_path
        self.llm_provider = llm_provider
        self.verbose = verbose
        self.config = None
        self.db = None

    def load_config(self):
        """Load application configuration."""
        if not self.config:
            self.config = load_app_config()
            # Override with CLI options if provided
            if self.database_path:
                self.config.database.database_path = self.database_path
            if self.llm_provider:
                self.config.llm.default_provider = self.llm_provider
        return self.config

    def get_database(self) -> RMDatabase:
        """Get database connection (creates if needed)."""
        if not self.db:
            config = self.load_config()
            db_path = config.database.database_path
            if not db_path:
                raise click.UsageError(
                    "No database specified. Use --database option or set RM_DATABASE_PATH in config/.env"
                )
            extension_path = config.database.sqlite_extension_path
            self.db = RMDatabase(db_path, extension_path=extension_path)
        return self.db


@click.group()
@click.option(
    "--database",
    "-d",
    type=click.Path(exists=True, path_type=Path),
    help="Path to RootsMagic database (.rmtree file)",
)
@click.option(
    "--llm-provider",
    type=click.Choice(["anthropic", "openai", "ollama"], case_sensitive=False),
    help="LLM provider (anthropic/openai/ollama)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.version_option(version="0.1.0", prog_name="rmagent")
@click.pass_context
def cli(ctx, database: Path | None, llm_provider: str | None, verbose: bool):
    """
    RMAgent - AI-powered genealogy assistant for RootsMagic databases.

    Query persons, generate biographies, analyze data quality, create timelines,
    and export content for Hugo static sites.

    \b
    Examples:
        # Query person by ID
        rmagent person 1

        # Generate biography
        rmagent bio 1 --length standard --output bio.md

        # Run data quality checks
        rmagent quality --severity critical

        # Ask a question
        rmagent ask "Who were John Smith's parents?"

        # Generate timeline
        rmagent timeline 1 --output timeline.json

        # Export to Hugo
        rmagent export hugo 1 --output-dir content/people

        # Search by name
        rmagent search --name "Smith"
    """
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )

    # Create CLI context and store in Click context
    ctx.obj = CLIContext(
        database_path=database,
        llm_provider=llm_provider,
        verbose=verbose,
    )


# Import and register command modules
from rmagent.cli.commands import ask, bio, export, person, quality, search, timeline

cli.add_command(person.person)
cli.add_command(bio.bio)
cli.add_command(quality.quality)
cli.add_command(ask.ask)
cli.add_command(timeline.timeline)
cli.add_command(export.export)
cli.add_command(search.search)


def main():
    """Entry point for CLI."""
    try:
        cli(obj=None)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logging.exception("Unhandled exception")
        sys.exit(1)


if __name__ == "__main__":
    main()
