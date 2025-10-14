"""Timeline command - Generate timelines."""

from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from rmagent.generators.timeline import TimelineFormat, TimelineGenerator

console = Console()


@click.command()
@click.argument("person_id", type=int)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "html"], case_sensitive=False),
    default="json",
    help="Timeline format (json for embedding, html for standalone)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file (default: stdout for json)",
)
@click.option(
    "--group-by-phase",
    is_flag=True,
    help="Group events by life phases",
)
@click.option(
    "--include-family",
    is_flag=True,
    help="Include family events (spouse, children)",
)
@click.pass_obj
def timeline(
    ctx,
    person_id: int,
    format: str,
    output: Path | None,
    group_by_phase: bool,
    include_family: bool,
):
    """
    Generate timeline for a person.

    \b
    Examples:
        rmagent timeline 1
        rmagent timeline 1 --format html --output timeline.html
        rmagent timeline 1 --group-by-phase
        rmagent timeline 1 --output timeline.json
    """
    try:
        # Map string to enum
        format_enum = {
            "json": TimelineFormat.JSON,
            "html": TimelineFormat.HTML,
        }[format.lower()]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Generating timeline for person {person_id}...", total=None)

            # Create generator
            config = ctx.load_config(require_llm_credentials=False)
            generator = TimelineGenerator(
                db=config.database.database_path,
                extension_path=config.database.sqlite_extension_path,
            )

            # Generate timeline
            timeline_output = generator.generate(
                person_id=person_id,
                format=format_enum,
                output_path=output,
                group_by_phase=group_by_phase,
                include_family=include_family,
            )

            progress.update(task, completed=True)

        # Output info
        if output:
            console.print(f"\n[green]✓[/green] Timeline written to: {output}")
            if format_enum == TimelineFormat.HTML:
                console.print(f"  Open {output} in your browser to view")
            else:
                console.print("  View at: https://timeline.knightlab.com")
        else:
            # Print JSON to stdout
            if format_enum == TimelineFormat.JSON:
                console.print(timeline_output)
            else:
                console.print("[yellow]Warning:[/yellow] HTML format requires --output option")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        if ctx.verbose:
            console.print_exception()
        raise click.Abort()
