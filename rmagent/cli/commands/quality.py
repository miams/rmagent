"""Quality command - Run data quality checks."""

from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from rmagent.generators.quality_report import QualityReportGenerator, ReportFormat
from rmagent.rmlib.quality import QualitySeverity

console = Console()


@click.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["markdown", "html", "csv"], case_sensitive=False),
    default="markdown",
    help="Report format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file (default: stdout for markdown)",
)
@click.option(
    "--sample-limit",
    type=int,
    default=25,
    help="Maximum sample issues to include per rule",
)
@click.option(
    "--category",
    "-c",
    type=click.Choice(
        [
            "required",
            "logical",
            "integrity",
            "sources",
            "dates",
            "values",
        ],
        case_sensitive=False,
    ),
    help="Filter by category",
)
@click.option(
    "--severity",
    "-s",
    type=click.Choice(["critical", "high", "medium", "low"], case_sensitive=False),
    help="Filter by severity",
)
@click.pass_obj
def quality(
    ctx,
    format: str,
    output: Path | None,
    sample_limit: int,
    category: str | None,
    severity: str | None,
):
    """
    Run data quality checks on the database.

    \b
    Examples:
        rmagent quality
        rmagent quality --format html --output report.html
        rmagent quality --severity critical
        rmagent quality --category logical --format csv --output issues.csv
        rmagent quality --sample-limit 50
    """
    try:
        # Map string to enum
        format_enum = {
            "markdown": ReportFormat.MARKDOWN,
            "html": ReportFormat.HTML,
            "csv": ReportFormat.CSV,
        }[format.lower()]

        # Map category filter to full names
        category_map = {
            "required": "Required Fields",
            "logical": "Logical Consistency",
            "integrity": "Referential Integrity",
            "sources": "Source Quality",
            "dates": "Date Validity",
            "values": "Value Ranges",
        }
        category_filter = category_map.get(category.lower()) if category else None

        # Map severity filter
        severity_filter = None
        if severity:
            severity_filter = {
                "critical": QualitySeverity.CRITICAL,
                "high": QualitySeverity.HIGH,
                "medium": QualitySeverity.MEDIUM,
                "low": QualitySeverity.LOW,
            }[severity.lower()]

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
                category_filter=category_filter,
                severity_filter=severity_filter,
            )

            progress.update(task, completed=True)

        # Display summary statistics
        _display_summary(generator, category_filter, severity_filter)

        # Output to file or stdout
        if output:
            console.print(f"\n[green]✓[/green] Quality report written to: {output}")
        else:
            # Only print to stdout if markdown and no output file
            if format_enum == ReportFormat.MARKDOWN:
                console.print()
                console.print(report_output)
            else:
                console.print(
                    "[yellow]Warning:[/yellow] HTML and CSV formats require --output option"
                )

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        if ctx.verbose:
            console.print_exception()
        raise click.Abort()


def _display_summary(
    generator: QualityReportGenerator,
    category_filter: str | None,
    severity_filter: QualitySeverity | None,
):
    """Display Rich-formatted summary statistics."""
    # Get the last generated report
    report = generator._last_report
    if not report:
        return

    console.print()
    console.print("[bold]📊 Data Quality Summary[/bold]")
    console.print()

    # Database statistics
    stats_table = Table(show_header=True, header_style="bold cyan")
    stats_table.add_column("Metric", style="dim")
    stats_table.add_column("Count", justify="right")

    stats_table.add_row("Total People", f"{report.summary.get('total_people', 0):,}")
    stats_table.add_row("Total Events", f"{report.summary.get('total_events', 0):,}")
    stats_table.add_row("Total Sources", f"{report.summary.get('total_sources', 0):,}")
    stats_table.add_row("Total Citations", f"{report.summary.get('total_citations', 0):,}")

    console.print(stats_table)
    console.print()

    # Issues by severity
    severity_table = Table(show_header=True, header_style="bold yellow")
    severity_table.add_column("Severity", style="dim")
    severity_table.add_column("Count", justify="right")

    for sev in [
        QualitySeverity.CRITICAL,
        QualitySeverity.HIGH,
        QualitySeverity.MEDIUM,
        QualitySeverity.LOW,
    ]:
        count = report.totals_by_severity.get(sev, 0)
        if severity_filter and sev != severity_filter:
            continue
        icon = _get_severity_icon(sev)
        style = _get_severity_style(sev)
        severity_table.add_row(f"{icon} {sev.value.capitalize()}", f"[{style}]{count:,}[/{style}]")

    console.print(severity_table)
    console.print()

    # Issues by category (if no filter applied)
    if not category_filter:
        category_table = Table(show_header=True, header_style="bold green")
        category_table.add_column("Category", style="dim")
        category_table.add_column("Count", justify="right")

        for cat in sorted(report.totals_by_category.keys()):
            count = report.totals_by_category[cat]
            category_table.add_row(cat, f"{count:,}")

        console.print(category_table)
        console.print()

    # Total issues
    total = report.summary.get("issue_total", 0)
    if total > 0:
        console.print(f"[bold red]⚠️  Total Issues: {total:,}[/bold red]")
    else:
        console.print("[bold green]✓ No issues found![/bold green]")


def _get_severity_icon(severity: QualitySeverity) -> str:
    """Get emoji icon for severity level."""
    icons = {
        QualitySeverity.CRITICAL: "🔴",
        QualitySeverity.HIGH: "🟠",
        QualitySeverity.MEDIUM: "🟡",
        QualitySeverity.LOW: "🟢",
    }
    return icons.get(severity, "⚪")


def _get_severity_style(severity: QualitySeverity) -> str:
    """Get Rich style for severity level."""
    styles = {
        QualitySeverity.CRITICAL: "bold red",
        QualitySeverity.HIGH: "bold yellow",
        QualitySeverity.MEDIUM: "yellow",
        QualitySeverity.LOW: "green",
    }
    return styles.get(severity, "white")
