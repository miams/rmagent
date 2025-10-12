"""Export command - Export to Hugo blog."""

from pathlib import Path

import click
from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

from rmagent.generators.biography import BiographyLength
from rmagent.generators.hugo_exporter import HugoExporter

console = Console()


@click.group()
def export():
    """Export content to various formats."""
    pass


@export.command()
@click.argument("person_id", type=int, required=False)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default="content/people",
    help="Output directory for Hugo content",
)
@click.option(
    "--bio-length",
    type=click.Choice(["short", "standard", "comprehensive"], case_sensitive=False),
    default="standard",
    help="Biography length",
)
@click.option(
    "--include-timeline",
    is_flag=True,
    default=True,
    help="Include timeline in export",
)
@click.option(
    "--media-base-path",
    type=str,
    default="/media/",
    help="Base path for media files in Hugo",
)
@click.option(
    "--all",
    "export_all",
    is_flag=True,
    help="Export all persons (batch mode)",
)
@click.option(
    "--batch-ids",
    type=str,
    help="Comma-separated list of person IDs to export",
)
@click.pass_obj
def hugo(
    ctx,
    person_id: int | None,
    output_dir: Path,
    bio_length: str,
    include_timeline: bool,
    media_base_path: str,
    export_all: bool,
    batch_ids: str | None,
):
    """
    Export person(s) to Hugo blog format.

    \b
    Examples:
        rmagent export hugo 1
        rmagent export hugo 1 --output-dir content/people
        rmagent export hugo 1 --bio-length comprehensive
        rmagent export hugo --batch-ids 1,2,3,4,5
        rmagent export hugo --all  # Export all persons
    """
    try:
        # Map string to enum
        length_enum = {
            "short": BiographyLength.SHORT,
            "standard": BiographyLength.STANDARD,
            "comprehensive": BiographyLength.COMPREHENSIVE,
        }[bio_length.lower()]

        # Create exporter
        config = ctx.load_config()
        exporter = HugoExporter(
            db=config.database.database_path,
            extension_path=config.database.sqlite_extension_path,
            media_base_path=media_base_path,
        )

        if export_all:
            # Export all persons
            console.print("[yellow]Warning:[/yellow] Exporting all persons may take a while...")
            # Get all person IDs
            from rmagent.rmlib.database import RMDatabase

            with RMDatabase(
                config.database.database_path, extension_path=config.database.sqlite_extension_path
            ) as db:
                all_persons = db.query("SELECT PersonID FROM PersonTable")
                person_ids = [p["PersonID"] for p in all_persons]

            console.print(f"Exporting {len(person_ids)} persons...")

            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Exporting persons...", total=len(person_ids))

                result = exporter.export_batch(
                    person_ids=person_ids,
                    output_dir=output_dir,
                    bio_length=length_enum,
                    include_timeline=include_timeline,
                    generate_index=True,
                )

                progress.update(task, completed=len(person_ids))

            success_count = len(result["markdown_files"])
            error_count = len(person_ids) - success_count
            console.print(f"\n[green]✓[/green] Exported {success_count} persons to: {output_dir}")
            if error_count > 0:
                console.print(f"[yellow]⚠[/yellow] {error_count} persons failed")

        elif batch_ids:
            # Export specific list of persons
            person_ids = [int(pid.strip()) for pid in batch_ids.split(",")]
            console.print(f"Exporting {len(person_ids)} persons...")

            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Exporting persons...", total=len(person_ids))

                result = exporter.export_batch(
                    person_ids=person_ids,
                    output_dir=output_dir,
                    bio_length=length_enum,
                    include_timeline=include_timeline,
                    generate_index=True,
                )

                progress.update(task, completed=len(person_ids))

            success_count = len(result["markdown_files"])
            error_count = len(person_ids) - success_count
            console.print(f"\n[green]✓[/green] Exported {success_count} persons to: {output_dir}")
            if error_count > 0:
                console.print(f"[yellow]⚠[/yellow] {error_count} persons failed")

        elif person_id:
            # Export single person
            with Progress(
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Exporting person {person_id}...", total=None)

                result = exporter.export_person(
                    person_id=person_id,
                    output_dir=output_dir,
                    bio_length=length_enum,
                    include_timeline=include_timeline,
                )

                progress.update(task, completed=True)

            console.print(f"\n[green]✓[/green] Exported to: {result['markdown']}")
            if include_timeline and result.get("timeline_json"):
                console.print(f"  Timeline JSON: {result['timeline_json']}")
                console.print(f"  Timeline HTML: {result['timeline_html']}")

        else:
            console.print("[red]Error:[/red] Please specify a person ID, --batch-ids, or --all")
            raise click.Abort()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        if ctx.verbose:
            console.print_exception()
        raise click.Abort()
