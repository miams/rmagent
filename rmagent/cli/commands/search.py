"""Search command - Search database by name or place."""

import re
import click
from rich.console import Console
from rich.table import Table

from rmagent.config.config import load_app_config
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


def _parse_name_variations(name: str, all_variants: list[str]) -> list[str]:
    """
    Parse bracket syntax for surname variations.

    Examples:
        "John Iiams [Ijams]" -> ["John Iiams", "John Ijams"]
        "John Iams [Ijams] [Imes]" -> ["John Iams", "John Ijams", "John Imes"]
        "John [ALL]" -> ["John Iams", "John Iames", "John Iiams", ...]

    Args:
        name: Search string with optional [variant] or [ALL] syntax
        all_variants: List of surnames for [ALL] keyword

    Returns:
        List of name variations to search
    """
    # Check if there are any brackets
    if "[" not in name:
        return [name]

    # Extract brackets and base name (everything before first bracket)
    bracket_pattern = r'\[([^\]]+)\]'
    brackets = re.findall(bracket_pattern, name)
    base_name = re.sub(bracket_pattern, '', name).strip()

    if not brackets:
        return [name]

    variations = []
    base_parts = base_name.split()

    # Handle [ALL] keyword
    if "ALL" in [b.strip().upper() for b in brackets]:
        # For [ALL], treat base_name as prefix and append all variants
        if base_name:
            for variant in all_variants:
                variations.append(f"{base_name} {variant}".strip())
        else:
            # No base name, just return variants
            variations.extend(all_variants)
    else:
        # Add base name first
        variations.append(base_name)

        # Replace last word of base name with each bracketed variation
        if len(base_parts) > 0:
            prefix = " ".join(base_parts[:-1]) if len(base_parts) > 1 else ""
            for bracket in brackets:
                variant = bracket.strip()
                if prefix:
                    variations.append(f"{prefix} {variant}".strip())
                else:
                    variations.append(variant)

    return variations


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
    default=10000,
    help="Maximum number of results (default: 10000)",
)
@click.option(
    "--exact",
    is_flag=True,
    help="Exact name match only (no phonetic matching)",
)
@click.option(
    "--married-name",
    is_flag=True,
    help="Include married surnames for women (in addition to maiden names)",
)
@click.option(
    "--kilometers",
    "-km",
    type=float,
    help="Search radius in kilometers (requires --place to return single result)",
)
@click.option(
    "--miles",
    "-mi",
    type=float,
    help="Search radius in miles (requires --place to return single result)",
)
@click.pass_obj
def search(
    ctx,
    name: str | None,
    place: str | None,
    limit: int,
    exact: bool,
    married_name: bool,
    kilometers: float | None,
    miles: float | None,
):
    """
    Search the database by name or place.

    The default search uses a multi-strategy approach:
    1. Searches for text in surname OR given name fields (includes alternate names)
    2. For multi-word queries, matches ALL words across combined name
    3. Falls back to phonetic matching if no exact matches found

    \b
    Surname Variations (Bracket Syntax):
        Use brackets to search multiple surname spellings:
        - "John Iiams [Ijams]"           Searches both "John Iiams" and "John Ijams"
        - "John Iams [Ijams] [Imes]"     Searches all three variations
        - "John [ALL]"                   Searches all configured surname variants

    Configure [ALL] variants in config/.env:
        SURNAME_VARIANTS_ALL=Iams,Iames,Iiams,Iiames,Ijams,Ijames,Imes,Eimes

    \b
    Exact Matching (--exact flag):
        For names: Structured search (assumes last word is surname)
        For places: Exact place name match (no flexible matching)

    Use --married-name to find women by their married surnames.

    \b
    Place Search with Flexible Matching (default):
        County is optional - both work:
        - "Scottsdale, Maricopa"  matches "Scottsdale, Maricopa, Arizona, United States"
        - "Scottsdale, Arizona"   matches "Scottsdale, Maricopa, Arizona, United States"

    \b
    Radius Search (GPS-based):
        Use --kilometers or --miles to find places within a radius.
        Requires --place search to return exactly ONE place.
        - rmagent search --place "Phoenix, Maricopa, Arizona" --kilometers 100
        - rmagent search --place "Baltimore, Maryland" --miles 50

    \b
    Examples:
        rmagent search --name "Smith"                     # Finds all Smiths
        rmagent search --name "John Smith"                # Finds John Smiths
        rmagent search --name "Lucy Virginia Dorsey"      # Finds across full name
        rmagent search --name "Janet Bross"               # Finds alternate names
        rmagent search --name "John Iiams [Ijams]"        # Surname variations
        rmagent search --name "John [ALL]"                # All configured variants
        rmagent search --name "Janet Iiams" --married-name  # Find by married name
        rmagent search --name "Smith" --exact             # Exact name match
        rmagent search --place "Maryland"                 # Search by place
        rmagent search --place "Scottsdale, Arizona"      # Flexible place matching
        rmagent search --place "Phoenix, Maricopa, Arizona, United States" --exact  # Exact place
        rmagent search --place "Phoenix, Arizona" --kilometers 100  # Radius search
        rmagent search --name "Smith" --limit 10          # Limit results
    """
    try:
        # Validate inputs
        if not name and not place:
            console.print("[red]Error:[/red] Please specify --name or --place to search")
            raise click.Abort()

        # Validate radius search options
        if kilometers is not None and miles is not None:
            console.print(
                "[red]Error:[/red] Cannot specify both --kilometers and --miles. Choose one."
            )
            raise click.Abort()

        radius_km = None
        radius_unit = None
        if kilometers is not None:
            if kilometers <= 0:
                console.print("[red]Error:[/red] Radius must be positive")
                raise click.Abort()
            radius_km = kilometers
            radius_unit = "km"
        elif miles is not None:
            if miles <= 0:
                console.print("[red]Error:[/red] Radius must be positive")
                raise click.Abort()
            radius_km = miles * 1.60934  # Convert miles to kilometers
            radius_unit = "mi"

        if radius_km is not None and not place:
            console.print(
                "[red]Error:[/red] Radius search requires --place to be specified"
            )
            raise click.Abort()

        with ctx.get_database() as db:
            queries = QueryService(db)

            # Search by name
            if name:
                # Load config to get surname variants for [ALL] keyword
                config = load_app_config(configure_logger=False)
                all_variants = config.search.surname_variants_all

                # Parse name variations (supports [variant] and [ALL] syntax)
                name_variations = _parse_name_variations(name, all_variants)

                # Show which variations are being searched
                if len(name_variations) > 1:
                    console.print(
                        f"[dim]Searching {len(name_variations)} name variations...[/dim]"
                    )

                # Collect results from all variations
                all_results = []
                seen_person_ids = set()

                if exact:
                    # Exact mode: Parse name and use structured search
                    # For Western names, assume last word is surname
                    for variation in name_variations:
                        name_parts = variation.strip().split()
                        if len(name_parts) == 1:
                            # Single word - could be surname or given name
                            # Try both
                            try:
                                surname_results = queries.search_primary_names(
                                    surname=name_parts[0], limit=limit
                                )
                                for r in surname_results:
                                    if r["PersonID"] not in seen_person_ids:
                                        all_results.append(r)
                                        seen_person_ids.add(r["PersonID"])
                            except ValueError:
                                pass
                            try:
                                given_results = queries.search_primary_names(
                                    given=name_parts[0], limit=limit
                                )
                                for r in given_results:
                                    if r["PersonID"] not in seen_person_ids:
                                        all_results.append(r)
                                        seen_person_ids.add(r["PersonID"])
                            except ValueError:
                                pass
                        else:
                            # Multiple words - last word is probably surname
                            surname = name_parts[-1]
                            given = " ".join(name_parts[:-1])
                            try:
                                variation_results = queries.search_primary_names(
                                    surname=surname, given=given, limit=limit
                                )
                                for r in variation_results:
                                    if r["PersonID"] not in seen_person_ids:
                                        all_results.append(r)
                                        seen_person_ids.add(r["PersonID"])
                            except ValueError:
                                pass

                    results = all_results
                else:
                    # Flexible mode (default): Multi-strategy search

                    for variation in name_variations:
                        if married_name:
                            # Married name search for females
                            if len(variation.strip().split()) > 1:
                                # Multi-word: Use word-based search (more precise)
                                variation_results = queries.search_names_with_married_by_words(
                                    search_text=variation, limit=limit
                                )
                            else:
                                # Single word: Use flexible search
                                variation_results = queries.search_names_with_married(
                                    search_text=variation, limit=limit
                                )
                        else:
                            # Standard search (includes alternate names)
                            if len(variation.strip().split()) > 1:
                                # Multi-word: Use word-based search (more precise)
                                # This finds people where ALL words appear across name fields
                                variation_results = queries.search_names_by_words(
                                    search_text=variation, limit=limit
                                )
                            else:
                                # Single word: Use flexible search
                                # This finds people where word appears in surname OR given name
                                variation_results = queries.search_names_flexible(
                                    search_text=variation, limit=limit
                                )

                        # Add unique results
                        for r in variation_results:
                            if r["PersonID"] not in seen_person_ids:
                                all_results.append(r)
                                seen_person_ids.add(r["PersonID"])

                    results = all_results

                    # Fallback: If still no results, try phonetic search on last word
                    if not results:
                        # Try phonetic on the first variation's last word
                        first_variation = name_variations[0]
                        name_parts = first_variation.strip().split()
                        if name_parts:
                            # Try phonetic search on last word (assumed surname)
                            surname_mp = _get_surname_metaphone(db, name_parts[-1])
                            if surname_mp:
                                console.print("[dim]No exact matches. Trying phonetic search...[/dim]\n")
                                results = queries.search_primary_names_phonetic(
                                    surname_phonetic=surname_mp, limit=limit
                                )

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
                # First, search for matching places
                place_results = queries.find_places_by_name(pattern=place, limit=limit, exact=exact)

                # If radius search is requested, validate and perform radius search
                if radius_km is not None:
                    if not place_results:
                        console.print(
                            f"[red]Error:[/red] No places found matching '{place}'. "
                            "Radius search requires an exact place match."
                        )
                        raise click.Abort()
                    elif len(place_results) > 1:
                        console.print(
                            f"[red]Error:[/red] Found {len(place_results)} places matching '{place}'. "
                            "Radius search requires exactly ONE place.\n"
                        )
                        console.print(
                            "[yellow]Tip:[/yellow] Use --exact flag for exact place name matching, "
                            "or be more specific in your search.\n"
                        )
                        console.print("[bold]Matching places:[/bold]")
                        for pr in place_results[:10]:  # Show first 10
                            console.print(f"  • {pr['Name']} (ID: {pr['PlaceID']})")
                        raise click.Abort()

                    # Exactly 1 place found - perform radius search
                    center_place = place_results[0]
                    center_place_id = center_place["PlaceID"]
                    center_place_name = center_place["Name"]

                    console.print(
                        f"\n[bold]📍 Searching within {kilometers if radius_unit == 'km' else miles} "
                        f"{radius_unit} of:[/bold]"
                    )
                    console.print(f"   {center_place_name} (ID: {center_place_id})")
                    console.print("─" * 80)

                    try:
                        radius_results = queries.find_places_within_radius(
                            center_place_id=center_place_id,
                            radius_km=radius_km,
                            limit=limit,
                        )

                        if radius_results:
                            console.print(
                                f"\n[bold]🌍 Found {len(radius_results)} place(s) within radius:[/bold]"
                            )

                            table = Table(show_header=True, header_style="bold cyan")
                            table.add_column("ID", style="dim", width=8)
                            table.add_column("People Found", style="dim", width=13, justify="right")
                            table.add_column("Place Name", style="bold")
                            table.add_column("Distance", style="dim", width=12, justify="right")

                            for place_row in radius_results:
                                place_id_int = place_row["PlaceID"]
                                place_id = str(place_id_int)
                                place_name = place_row["Name"]
                                distance_km = place_row["DistanceKm"]

                                # Get count of people with events at this place
                                person_count = queries.get_person_count_by_place(place_id_int)

                                if radius_unit == "mi":
                                    distance_display = f"{distance_km / 1.60934:.1f} mi"
                                else:
                                    distance_display = f"{distance_km:.1f} km"

                                table.add_row(place_id, str(person_count), place_name, distance_display)

                            console.print(table)
                            console.print()
                        else:
                            console.print(
                                f"[yellow]No places found within {kilometers if radius_unit == 'km' else miles} "
                                f"{radius_unit}[/yellow]"
                            )

                    except ValueError as e:
                        console.print(f"[red]Error:[/red] {e}")
                        raise click.Abort()

                else:
                    # Standard place search (no radius)
                    if place_results:
                        console.print(
                            f"\n[bold]📍 Found {len(place_results)} place(s) matching '{place}':[/bold]"
                        )
                        console.print("─" * 60)

                        table = Table(show_header=True, header_style="bold cyan")
                        table.add_column("ID", style="dim", width=8)
                        table.add_column("People Found", style="dim", width=13, justify="right")
                        table.add_column("Place Name")

                        for place_row in place_results:
                            place_id_int = _get_value(place_row, "PlaceID")
                            place_id = str(place_id_int)
                            place_name = _get_value(place_row, "Name")

                            # Get count of people with events at this place
                            person_count = queries.get_person_count_by_place(place_id_int)

                            table.add_row(place_id, str(person_count), place_name)

                        console.print(table)
                        console.print()
                    else:
                        console.print(f"[yellow]No places found matching '{place}'[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        if ctx.verbose:
            console.print_exception()
        raise click.Abort()
