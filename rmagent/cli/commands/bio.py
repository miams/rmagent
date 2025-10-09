"""Biography command - Generate AI-powered biographies."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from rmagent.generators.biography import BiographyGenerator, BiographyLength, CitationStyle
from rmagent.agent.genealogy_agent import GenealogyAgent

console = Console()


@click.command()
@click.argument('person_id', type=int)
@click.option(
    '--length',
    type=click.Choice(['short', 'standard', 'comprehensive'], case_sensitive=False),
    default='standard',
    help='Biography length',
)
@click.option(
    '--citation-style',
    type=click.Choice(['footnote', 'parenthetical', 'narrative'], case_sensitive=False),
    default='footnote',
    help='Citation style',
)
@click.option(
    '--output',
    '-o',
    type=click.Path(path_type=Path),
    help='Output file (default: stdout)',
)
@click.option(
    '--no-ai',
    is_flag=True,
    help='Use template-based generation (no AI)',
)
@click.option(
    '--no-sources',
    is_flag=True,
    help='Exclude source citations',
)
@click.pass_obj
def bio(
    ctx,
    person_id: int,
    length: str,
    citation_style: str,
    output: Optional[Path],
    no_ai: bool,
    no_sources: bool,
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
            'short': BiographyLength.SHORT,
            'standard': BiographyLength.STANDARD,
            'comprehensive': BiographyLength.COMPREHENSIVE,
        }[length.lower()]

        citation_style_enum = {
            'footnote': CitationStyle.FOOTNOTE,
            'parenthetical': CitationStyle.PARENTHETICAL,
            'narrative': CitationStyle.NARRATIVE,
        }[citation_style.lower()]

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Generating biography for person {person_id}...", total=None)

            # Create generator
            config = ctx.load_config()
            agent = None if no_ai else GenealogyAgent(
                db=None,  # Will be set by generator
                llm_provider=config.build_provider(),
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

        # Render as markdown
        markdown_output = bio_result.render_markdown()

        # Output to file or stdout
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(markdown_output, encoding='utf-8')
            console.print(f"\n[green]✓[/green] Biography written to: {output}")
            console.print(f"  Length: {len(markdown_output.split())} words")
        else:
            console.print()
            console.print(markdown_output)

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        if ctx.verbose:
            console.print_exception()
        raise click.Abort()
