"""Search command - Search database by name or place."""

import click
from rich.console import Console
from rich.table import Table

from rmagent.rmlib.queries import QueryService

console = Console()


def _get_value(row, key, default=""):
    """Safely get value from sqlite3.Row object."""
    try:
        return row[key] if row[key] is not None else default
    except (KeyError, IndexError):
        return default


def _get_surname_metaphone(db, surname: str) -> str | None:
    """Get Metaphone encoding for a surname from the database."""
    # Query a sample name to get the Metaphone encoding
    result = db.query_one(
        "SELECT SurnameMP FROM NameTable WHERE Surname = ? COLLATE RMNOCASE LIMIT 1", (surname,)
    )
    return result["SurnameMP"] if result else None


@click.command()
@click.option(
    "--name",
    "-n",
    type=str,
    help='Search by name (surname or "Given Surname")',
)
@click.option(
    "--place",
    "-p",
    type=str,
    help="Search by place name",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=50,
    help="Maximum number of results (default: 50)",
)
@click.option(
    "--exact",
    is_flag=True,
    help="Exact name match only (no phonetic matching)",
)
@click.pass_obj
def search(ctx, name: str | None, place: str | None, limit: int, exact: bool):
    """
    Search the database by name or place.

    \b
    Examples:
        rmagent search --name "Smith"
        rmagent search --name "John Smith"
        rmagent search --place "Maryland"
        rmagent search --name "Smith" --limit 10
        rmagent search --name "Smith" --exact
    """
    try:
        # Validate inputs
        if not name and not place:
            console.print("[red]Error:[/red] Please specify --name or --place to search")
            raise click.Abort()

        with ctx.get_database() as db:
            queries = QueryService(db)

            # Search by name
            if name:
                # Try to parse name into surname and given name
                name_parts = name.strip().split(None, 1)  # Split on first space
                surname = name_parts[0] if name_parts else None
                given = name_parts[1] if len(name_parts) > 1 else None

                results = []

                # Try exact match first
                if surname and not given:
                    # Just surname - try exact match
                    try:
                        exact_results = queries.search_primary_names(surname=surname, limit=limit)
                        results.extend(exact_results)
                    except ValueError:
                        pass
                elif surname and given:
                    # Both surname and given - try exact match
                    try:
                        exact_results = queries.search_primary_names(
                            surname=surname, given=given, limit=limit
                        )
                        results.extend(exact_results)
                    except ValueError:
                        pass

                # If exact match found nothing and phonetic search enabled, try phonetic
                if not results and not exact and surname:
                    # Get the Metaphone encoding for the surname
                    surname_mp = _get_surname_metaphone(db, surname)
                    if surname_mp:
                        console.print("[dim]No exact matches. Trying phonetic search...[/dim]\n")
                        phonetic_results = queries.search_primary_names_phonetic(
                            surname_phonetic=surname_mp, limit=limit
                        )
                        results.extend(phonetic_results)

                # Display name search results
                if results:
                    console.print(
                        f"\n[bold]🔍 Found {len(results)} person(s) matching '{name}':[/bold]"
                    )
                    console.print("─" * 60)

                    table = Table(show_header=True, header_style="bold cyan")
                    table.add_column("ID", style="dim", width=8)
                    table.add_column("Name", style="bold")
                    table.add_column("Birth", style="dim", width=10)
                    table.add_column("Death", style="dim", width=10)

                    for person in results:
                        person_id = str(_get_value(person, "PersonID"))
                        given_name = _get_value(person, "Given")
                        surname_name = _get_value(person, "Surname")
                        full_name = f"{given_name} {surname_name}".strip()
                        birth_year = _get_value(person, "BirthYear", "?")
                        death_year = _get_value(person, "DeathYear", "?")

                        table.add_row(person_id, full_name, str(birth_year), str(death_year))

                    console.print(table)
                    console.print()
                else:
                    console.print(f"[yellow]No persons found matching '{name}'[/yellow]")

            # Search by place
            if place:
                place_results = queries.find_places_by_name(pattern=place, limit=limit)

                if place_results:
                    console.print(
                        f"\n[bold]📍 Found {len(place_results)} place(s) matching '{place}':[/bold]"
                    )
                    console.print("─" * 60)

                    table = Table(show_header=True, header_style="bold cyan")
                    table.add_column("ID", style="dim", width=8)
                    table.add_column("Place Name")

                    for place_row in place_results:
                        place_id = str(_get_value(place_row, "PlaceID"))
                        place_name = _get_value(place_row, "Name")
                        table.add_row(place_id, place_name)

                    console.print(table)
                    console.print()
                else:
                    console.print(f"[yellow]No places found matching '{place}'[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if ctx.verbose:
            console.print_exception()
        raise click.Abort()
