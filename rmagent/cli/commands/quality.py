"""Quality command - Run data quality checks."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from rmagent.generators.quality_report import QualityReportGenerator, ReportFormat

console = Console()


@click.command()
@click.option(
    '--format',
    '-f',
    type=click.Choice(['markdown', 'html', 'csv'], case_sensitive=False),
    default='markdown',
    help='Report format',
)
@click.option(
    '--output',
    '-o',
    type=click.Path(path_type=Path),
    help='Output file (default: stdout for markdown)',
)
@click.option(
    '--sample-limit',
    type=int,
    default=25,
    help='Maximum sample issues to include per rule',
)
@click.pass_obj
def quality(ctx, format: str, output: Optional[Path], sample_limit: int):
    """
    Run data quality checks on the database.

    \b
    Examples:
        rmagent quality
        rmagent quality --format html --output report.html
        rmagent quality --format csv --output issues.csv
        rmagent quality --sample-limit 50
    """
    try:
        # Map string to enum
        format_enum = {
            'markdown': ReportFormat.MARKDOWN,
            'html': ReportFormat.HTML,
            'csv': ReportFormat.CSV,
        }[format.lower()]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Running data quality validation...", total=None)

            # Create generator
            config = ctx.load_config()
            generator = QualityReportGenerator(
                db=config.database.database_path,
                extension_path=config.database.sqlite_extension_path,
                sample_limit=sample_limit,
            )

            # Generate report
            report_output = generator.generate(
                format=format_enum,
                output_path=output,
            )

            progress.update(task, completed=True)

        # Output to file or stdout
        if output:
            console.print(f"\n[green]✓[/green] Quality report written to: {output}")
        else:
            # Only print to stdout if markdown and no output file
            if format_enum == ReportFormat.MARKDOWN:
                console.print()
                console.print(report_output)
            else:
                console.print("[yellow]Warning:[/yellow] HTML and CSV formats require --output option")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        if ctx.verbose:
            console.print_exception()
        raise click.Abort()
