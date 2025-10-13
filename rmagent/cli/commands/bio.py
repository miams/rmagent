"""Biography command - Generate AI-powered biographies."""

import re
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from rmagent.agent.genealogy_agent import GenealogyAgent
from rmagent.generators.biography import BiographyGenerator, BiographyLength, CitationStyle

console = Console()

# Default biography output directory
DEFAULT_BIO_DIR = Path("./reports/biographies")


@click.command()
@click.argument("person_id", type=int)
@click.option(
    "--length",
    type=click.Choice(["short", "standard", "comprehensive"], case_sensitive=False),
    default="standard",
    help="Biography length",
)
@click.option(
    "--citation-style",
    type=click.Choice(["footnote", "parenthetical", "narrative"], case_sensitive=False),
    default="footnote",
    help="Citation style",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file (default: ./reports/biographies/Surname, Given (birth-death)-length-cite.md)",
)
@click.option(
    "--no-ai",
    is_flag=True,
    help="Use template-based generation (no AI)",
)
@click.option(
    "--no-sources",
    is_flag=True,
    help="Exclude source citations",
)
@click.option(
    "--meta/--no-meta",
    default=None,
    help="Include Hugo-style front matter metadata (default: from config)",
)
@click.pass_obj
def bio(
    ctx,
    person_id: int,
    length: str,
    citation_style: str,
    output: Path | None,
    no_ai: bool,
    no_sources: bool,
    meta: bool | None,
):
    """
    Generate biography for a person.

    \b
    Examples:
        rmagent bio 1
        rmagent bio 1 --length comprehensive
        rmagent bio 1 --output bio.md --citation-style footnote
        rmagent bio 1 --no-ai  # Template-based (no LLM)
    """
    try:
        # Map string to enum
        length_enum = {
            "short": BiographyLength.SHORT,
            "standard": BiographyLength.STANDARD,
            "comprehensive": BiographyLength.COMPREHENSIVE,
        }[length.lower()]

        citation_style_enum = {
            "footnote": CitationStyle.FOOTNOTE,
            "parenthetical": CitationStyle.PARENTHETICAL,
            "narrative": CitationStyle.NARRATIVE,
        }[citation_style.lower()]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Generating biography for person {person_id}...", total=None)

            # Create generator
            config = ctx.load_config()
            agent = (
                None
                if no_ai
                else GenealogyAgent(
                    llm_provider=config.build_provider(),
                    db_path=config.database.database_path,
                    extension_path=config.database.sqlite_extension_path,
                )
            )

            generator = BiographyGenerator(
                db=config.database.database_path,
                extension_path=config.database.sqlite_extension_path,
                agent=agent,
            )

            # Generate biography
            bio_result = generator.generate(
                person_id=person_id,
                length=length_enum,
                citation_style=citation_style_enum,
                include_sources=not no_sources,
                use_ai=not no_ai,
            )

            progress.update(task, completed=True)

        # Determine metadata inclusion (from flag or config default)
        include_metadata = meta if meta is not None else config.biography.meta_default

        # Render as markdown
        markdown_output = bio_result.render_markdown(include_metadata=include_metadata)

        # Determine output path
        if output:
            output_path = output
        else:
            # Generate default filename
            output_path = _generate_biography_filename(
                bio_result.full_name,
                bio_result.length,
                bio_result.citation_style,
                generator,
                person_id,
            )

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown_output, encoding="utf-8")
        console.print(f"\n[green]✓[/green] Biography written to: {output_path}")
        console.print(f"  Length: {len(markdown_output.split())} words")

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        if ctx.verbose:
            console.print_exception()
        raise click.Abort()


def _generate_biography_filename(
    full_name: str,
    length: BiographyLength,
    citation_style: CitationStyle,
    generator: BiographyGenerator,
    person_id: int,
) -> Path:
    """
    Generate filename for biography following pattern:
    Surname, Given (bbbb-dddd)-length-cite.md

    Handles collisions with sequential numbering (_1, _2, etc.)
    """
    # Extract birth/death years from context
    try:
        context = generator._extract_person_context(person_id, include_media=False)
        birth_year = str(context.birth_year) if context.birth_year else "????"
        death_year = str(context.death_year) if context.death_year else "????"
        surname = context.surname or "Unknown"
        given = context.given_name or "Unknown"
    except Exception:
        # Fallback if extraction fails
        birth_year = "????"
        death_year = "????"
        surname = "Unknown"
        given = "Unknown"

    # Sanitize name components for filesystem
    surname_safe = re.sub(r'[<>:"/\\|?*]', "", surname)
    given_safe = re.sub(r'[<>:"/\\|?*]', "", given)

    # Build base filename
    base_name = f"{surname_safe}, {given_safe} ({birth_year}-{death_year})-{length.value}-{citation_style.value}"

    # Check for collisions and add sequential number if needed
    output_path = DEFAULT_BIO_DIR / f"{base_name}.md"

    if output_path.exists():
        counter = 1
        while True:
            output_path = DEFAULT_BIO_DIR / f"{base_name}_{counter}.md"
            if not output_path.exists():
                break
            counter += 1

    return output_path
