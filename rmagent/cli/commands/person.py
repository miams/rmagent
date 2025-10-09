"""Person command - Query person information."""

import click
from rich.console import Console
from rich.table import Table

from rmagent.rmlib.queries import QueryService

console = Console()


def _get_value(row, key, default=''):
    """Safely get value from sqlite3.Row object."""
    try:
        return row[key] if row[key] is not None else default
    except (KeyError, IndexError):
        return default


@click.command()
@click.argument('person_id', type=int)
@click.option('--events', is_flag=True, help='Show all events')
@click.option('--ancestors', is_flag=True, help='Show ancestor tree')
@click.option('--descendants', is_flag=True, help='Show descendant tree')
@click.option('--family', is_flag=True, help='Show immediate family')
@click.pass_obj
def person(ctx, person_id: int, events: bool, ancestors: bool, descendants: bool, family: bool):
    """
    Query person information by ID.

    \b
    Examples:
        rmagent person 1
        rmagent person 1 --events
        rmagent person 1 --family
        rmagent person 1 --ancestors
    """
    try:
        with ctx.get_database() as db:
            queries = QueryService(db)

            # Get person with primary name
            person_data = queries.get_person_with_primary_name(person_id)
            if not person_data:
                console.print(f"[red]Error:[/red] Person {person_id} not found")
                raise click.Abort()

            # Display person header
            name = f"{_get_value(person_data, 'Given')} {_get_value(person_data, 'Surname')}".strip()
            birth_year = _get_value(person_data, 'BirthYear', '?')
            death_year = _get_value(person_data, 'DeathYear', '?')
            console.print(f"\n[bold]📋 Person: {name}[/bold] ({birth_year}–{death_year})")
            console.print("─" * 50)

            # Show events if requested
            if events:
                event_rows = queries.get_person_events(person_id)
                if event_rows:
                    console.print("\n[bold]Events:[/bold]")
                    table = Table(show_header=True, header_style="bold cyan")
                    table.add_column("Date", style="dim")
                    table.add_column("Type")
                    table.add_column("Place")

                    for event in event_rows:
                        from rmagent.rmlib.parsers.date_parser import parse_rm_date
                        date_str = _get_value(event, 'Date')
                        formatted_date = parse_rm_date(date_str).format_display() if date_str else ''
                        table.add_row(
                            formatted_date,
                            _get_value(event, 'EventType'),
                            _get_value(event, 'Place'),
                        )
                    console.print(table)
                else:
                    console.print("[dim]No events found[/dim]")

            # Show family if requested
            if family:
                # Get parents (returns single row with FatherID/MotherID or None)
                parents_row = queries.get_parents(person_id)
                if parents_row:
                    console.print("\n[bold]Parents:[/bold]")
                    # Check for father
                    if _get_value(parents_row, 'FatherID'):
                        father_name = f"{_get_value(parents_row, 'FatherGiven')} {_get_value(parents_row, 'FatherSurname')}".strip()
                        console.print(f"  • Father: {father_name}")
                    # Check for mother
                    if _get_value(parents_row, 'MotherID'):
                        mother_name = f"{_get_value(parents_row, 'MotherGiven')} {_get_value(parents_row, 'MotherSurname')}".strip()
                        console.print(f"  • Mother: {mother_name}")

                # Get spouses
                spouses = queries.get_spouses(person_id)
                if spouses:
                    console.print("\n[bold]Spouses:[/bold]")
                    for spouse in spouses:
                        spouse_name = f"{_get_value(spouse, 'Given')} {_get_value(spouse, 'Surname')}".strip()
                        console.print(f"  • {spouse_name}")

                # Get children
                children = queries.get_children(person_id)
                if children:
                    console.print("\n[bold]Children:[/bold]")
                    for child in children:
                        child_name = f"{_get_value(child, 'Given')} {_get_value(child, 'Surname')}".strip()
                        console.print(f"  • {child_name}")

            # Show ancestors if requested
            if ancestors:
                ancestor_rows = queries.get_direct_ancestors(person_id, generations=4)
                if ancestor_rows:
                    console.print(f"\n[bold]Ancestors:[/bold] (4 generations)")
                    for ancestor in ancestor_rows:
                        ancestor_name = f"{_get_value(ancestor, 'Given')} {_get_value(ancestor, 'Surname')}".strip()
                        gen = _get_value(ancestor, 'Generation', 1)
                        indent = "  " * gen
                        console.print(f"{indent}• {ancestor_name} (gen {gen})")
                else:
                    console.print("[dim]No ancestors found[/dim]")

            # Show descendants if requested
            if descendants:
                descendant_rows = queries.get_descendants(person_id, generations=4)
                if descendant_rows:
                    console.print(f"\n[bold]Descendants:[/bold] (4 generations)")
                    for descendant in descendant_rows:
                        descendant_name = f"{_get_value(descendant, 'Given')} {_get_value(descendant, 'Surname')}".strip()
                        gen = _get_value(descendant, 'Generation', 1)
                        indent = "  " * gen
                        console.print(f"{indent}• {descendant_name} (gen {gen})")
                else:
                    console.print("[dim]No descendants found[/dim]")

            console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if ctx.verbose:
            console.print_exception()
        raise click.Abort()
