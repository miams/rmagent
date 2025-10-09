"""Search command - Search database."""

import click
from rich.console import Console
from rich.table import Table

from rmagent.rmlib.queries import QueryService

console = Console()


@click.command()
@click.option(
    '--name',
    '-n',
    type=str,
    help='Search by name (surname or given name)',
)
@click.option(
    '--place',
    '-p',
    type=str,
    help='Search by place name',
)
@click.option(
    '--limit',
    '-l',
    type=int,
    default=20,
    help='Maximum number of results',
)
@click.option(
    '--phonetic',
    is_flag=True,
    help='Use phonetic (Metaphone) matching',
)
@click.pass_obj
def search(ctx, name: str, place: str, limit: int, phonetic: bool):
    """
    Search the database.

    \b
    Examples:
        rmagent search --name "Smith"
        rmagent search --name "John Smith" --limit 10
        rmagent search --place "Maryland"
        rmagent search --name "Smyth" --phonetic  # Finds "Smith" too
    """
    try:
        if not name and not place:
            console.print("[red]Error:[/red] Please specify --name or --place")
            raise click.Abort()

        with ctx.get_database() as db:
            queries = QueryService(db)

            if name:
                # Search by name
                with console.status(f"[dim]Searching for: {name}...[/dim]"):
                    if phonetic:
                        # Phonetic search (Metaphone)
                        results = queries.search_persons_metaphone(name, limit=limit)
                    else:
                        # Exact search
                        results = queries.search_persons_by_name(name, limit=limit)

                if not results:
                    console.print(f"\n[yellow]No results found for:[/yellow] {name}")
                    return

                console.print(f"\n[bold]Found {len(results)} match(es):[/bold]")
                if phonetic:
                    console.print("[dim](using phonetic matching)[/dim]")
                console.print()

                # Create table
                table = Table(show_header=True, header_style="bold cyan")
                table.add_column("ID", style="dim", width=8)
                table.add_column("Name", style="bold")
                table.add_column("Birth", style="dim")
                table.add_column("Death", style="dim")

                for person in results:
                    person_id = str(person.get('PersonID', ''))
                    surname = person.get('Surname', '')
                    given = person.get('Given', '')
                    full_name = f"{given} {surname}".strip()
                    birth_year = str(person.get('BirthYear', '')) if person.get('BirthYear') else ''
                    death_year = str(person.get('DeathYear', '')) if person.get('DeathYear') else ''

                    table.add_row(person_id, full_name, birth_year, death_year)

                console.print(table)

            elif place:
                # Search by place
                with console.status(f"[dim]Searching for events in: {place}...[/dim]"):
                    results = queries.search_events_by_place(place, limit=limit)

                if not results:
                    console.print(f"\n[yellow]No events found in:[/yellow] {place}")
                    return

                console.print(f"\n[bold]Found {len(results)} event(s) in {place}:[/bold]\n")

                # Create table
                table = Table(show_header=True, header_style="bold cyan")
                table.add_column("Person", style="bold")
                table.add_column("Event Type")
                table.add_column("Date", style="dim")
                table.add_column("Place")

                for event in results:
                    person_name = f"{event.get('Given', '')} {event.get('Surname', '')}".strip()
                    event_type = event.get('EventType', '')

                    # Format date
                    from rmagent.rmlib.parsers.date_parser import parse_rm_date
                    date_str = event.get('Date', '')
                    formatted_date = parse_rm_date(date_str).format_display() if date_str else ''

                    place_name = event.get('Place', '')

                    table.add_row(person_name, event_type, formatted_date, place_name)

                console.print(table)

            console.print()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {e}")
        if ctx.verbose:
            console.print_exception()
        raise click.Abort()
