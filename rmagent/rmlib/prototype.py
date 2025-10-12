#!/usr/bin/env python3
"""
Prototype script for Milestone 1: Working Prototype

Demonstrates:
1. Database connection with RMNOCASE
2. Person query with complete data (name, events, places)
3. Date parsing for all formats
4. Data quality checks
5. Basic biography generation (no AI yet)

Usage:
    python -m rmagent.rmlib.prototype --person-id 1 --check-quality
    python -m rmagent.rmlib.prototype --person-id 1541 --check-quality
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rmagent.rmlib.database import RMDatabase
from rmagent.rmlib.parsers.blob_parser import parse_citation_fields, parse_source_fields
from rmagent.rmlib.parsers.date_parser import parse_rm_date
from rmagent.rmlib.parsers.name_parser import format_full_name
from rmagent.rmlib.parsers.place_parser import (
    format_place_medium,
    format_place_short,
)
from rmagent.rmlib.quality import DataQualityValidator
from rmagent.rmlib.queries import QueryService


def get_row_value(row, key: str, default=None):
    """Get value from sqlite3.Row object with default."""
    try:
        return row[key] if key in row.keys() else default
    except (KeyError, TypeError):
        return default


def render_italics(text: str) -> str:
    """
    Render <i>...</i> or <I>...</I> tags as italic text in terminal.

    Uses ANSI italic codes: \033[3m for italic start, \033[23m to reset italic.
    Handles both lowercase and uppercase tags.
    """
    if not text:
        return ""

    # Replace both lowercase and uppercase italic tags
    result = text.replace("<i>", "\033[3m").replace("</i>", "\033[23m")
    result = result.replace("<I>", "\033[3m").replace("</I>", "\033[23m")
    return result


def format_person_info(person: dict, query_service: QueryService) -> str:
    """Format person information for display."""
    lines = []
    lines.append("=" * 70)
    lines.append(f"PERSON INFORMATION (ID: {person['PersonID']})")
    lines.append("=" * 70)

    # Format name
    full_name = format_full_name(
        given=get_row_value(person, "Given"),
        surname=get_row_value(person, "Surname"),
        prefix=get_row_value(person, "Prefix"),
        suffix=get_row_value(person, "Suffix"),
    )
    lines.append(f"\nName: {full_name}")

    # Format birth/death years
    birth_year = get_row_value(person, "BirthYear")
    death_year = get_row_value(person, "DeathYear")
    if birth_year or death_year:
        years = f"({birth_year or '?'} - {death_year or '?'})"
        lines.append(f"Years: {years}")

    # Format sex
    sex_map = {0: "Male", 1: "Female", 2: "Unknown"}
    sex = sex_map.get(get_row_value(person, "Sex"), "Unknown")
    lines.append(f"Sex: {sex}")

    return "\n".join(lines)


def format_web_tags(person_id: int, db: RMDatabase) -> str:
    """Format web tags (URLs) for a person."""
    lines = []

    # Query URLTable for this person
    web_tags = db.query(
        """
        SELECT Name, URL, Note
        FROM URLTable
        WHERE OwnerType = 0 AND OwnerID = ?
        ORDER BY Name
        """,
        (person_id,),
    )

    if not web_tags:
        return ""

    lines.append("\n" + "-" * 70)
    lines.append("WEB LINKS")
    lines.append("-" * 70)

    for tag in web_tags:
        name = get_row_value(tag, "Name", "[Unnamed]")
        url = get_row_value(tag, "URL", "")
        note = get_row_value(tag, "Note", "")

        lines.append(f"\n{name}: {url}")
        if note:
            lines.append(f"  Note: {note}")

    return "\n".join(lines)


def format_events(person_id: int, query_service: QueryService) -> str:
    """Format person's events for display."""
    lines = []
    lines.append("\n" + "-" * 70)
    lines.append("EVENTS")
    lines.append("-" * 70)

    events = query_service.get_person_events(person_id)

    if not events:
        lines.append("\nNo events recorded.")
        return "\n".join(lines)

    for event in events:
        event_type = event["EventType"]

        # Parse and format date
        date_str = event["Date"]
        if date_str:
            try:
                date = parse_rm_date(date_str)
                formatted_date = date.format_display()
            except Exception:
                formatted_date = date_str
        else:
            formatted_date = "[No date]"

        # Parse and format place
        place_str = get_row_value(event, "Place", "")
        if place_str:
            try:
                formatted_place = format_place_short(place_str)
            except Exception:
                formatted_place = place_str
        else:
            formatted_place = "[No place]"

        # Format details
        details = get_row_value(event, "Details", "")
        if details:
            details_str = f" - {details}"
        else:
            details_str = ""

        lines.append(f"\n{event_type}: {formatted_date}, {formatted_place}{details_str}")

    return "\n".join(lines)


def format_citations(person_id: int, db: RMDatabase) -> str:
    """Format citations for a person's events."""
    lines = []

    # Query citations linked to this person's events
    citations = db.query(
        """
        SELECT
            e.EventID,
            ft.Name as EventType,
            e.Date,
            e.Details,
            c.CitationID,
            c.CitationName,
            c.Fields as CitationFields,
            s.SourceID,
            s.Name as SourceName
        FROM EventTable e
        JOIN FactTypeTable ft ON e.EventType = ft.FactTypeID
        LEFT JOIN CitationLinkTable cl ON cl.OwnerType = 2 AND cl.OwnerID = e.EventID
        LEFT JOIN CitationTable c ON c.CitationID = cl.CitationID
        LEFT JOIN SourceTable s ON s.SourceID = c.SourceID
        WHERE e.OwnerType = 0 AND e.OwnerID = ?
          AND c.CitationID IS NOT NULL
        ORDER BY e.SortDate, cl.SortOrder
        """,
        (person_id,),
    )

    if not citations:
        return ""

    lines.append("\n" + "-" * 70)
    lines.append("CITATIONS")
    lines.append("-" * 70)

    # Group citations by event
    current_event = None
    citation_num = 0

    for cit in citations:
        event_id = cit["EventID"]
        event_type = cit["EventType"]
        event_date = cit["Date"]
        event_details = get_row_value(cit, "Details", "")

        # Format event header
        if event_id != current_event:
            current_event = event_id

            # Format date
            if event_date:
                try:
                    date = parse_rm_date(event_date)
                    date_str = date.format_display()
                except Exception:
                    date_str = event_date
            else:
                date_str = "[No date]"

            # Event header
            event_header = f"{event_type} ({date_str})"
            if event_details:
                event_header += f" - {event_details}"

            lines.append(f"\n{event_header}")

        # Citation details
        citation_num += 1
        _citation_id = cit["CitationID"]  # Available for future use
        source_name = get_row_value(cit, "SourceName", "[Unknown Source]")

        # Parse citation fields to get page number
        page = ""
        if cit["CitationFields"]:
            try:
                fields = parse_citation_fields(cit["CitationFields"])
                page = fields.get("Page", "")
            except Exception:
                pass

        if page:
            lines.append(f"  [{citation_num}] Citation: Page {page} → Source: {source_name}")
        else:
            lines.append(f"  [{citation_num}] Citation: (no page) → Source: {source_name}")

    return "\n".join(lines)


def format_sources(person_id: int, db: RMDatabase) -> str:
    """Format unique sources for a person's citations."""
    lines = []

    # Query unique sources for this person's events
    sources = db.query(
        """
        SELECT
            s.SourceID,
            s.Name,
            s.TemplateID,
            s.ActualText,
            s.Fields as SourceFields,
            COUNT(DISTINCT c.CitationID) as CitationCount
        FROM EventTable e
        JOIN CitationLinkTable cl ON cl.OwnerType = 2 AND cl.OwnerID = e.EventID
        JOIN CitationTable c ON c.CitationID = cl.CitationID
        JOIN SourceTable s ON s.SourceID = c.SourceID
        WHERE e.OwnerType = 0 AND e.OwnerID = ?
        GROUP BY s.SourceID
        ORDER BY s.Name
        """,
        (person_id,),
    )

    if not sources:
        return ""

    lines.append("\n" + "-" * 70)
    lines.append(f"SOURCES ({len(sources)} unique source{'s' if len(sources) != 1 else ''})")
    lines.append("-" * 70)

    for i, src in enumerate(sources, 1):
        _source_id = src["SourceID"]  # Available for future use
        source_name = src["Name"]
        template_id = src["TemplateID"]
        actual_text = get_row_value(src, "ActualText", "")
        citation_count = src["CitationCount"]

        # Display bibliography
        bibliography_text = None

        # First, try to get Bibliography field from BLOB
        if src["SourceFields"]:
            try:
                fields = parse_source_fields(src["SourceFields"])
                if "Bibliography" in fields and fields["Bibliography"]:
                    bibliography_text = fields["Bibliography"]
            except Exception:
                pass

        # Fallback to ActualText for free-form sources
        if not bibliography_text and template_id == 0 and actual_text:
            bibliography_text = actual_text

        if bibliography_text:
            # Render with italics support
            formatted_bib = render_italics(bibliography_text)
            lines.append(f"\n[{i}] {formatted_bib}")
        else:
            # No bibliography text available, just show source name
            lines.append(f"\n[{i}] {source_name}")

        # Show citation count
        lines.append(f"    (Used in {citation_count} citation{'s' if citation_count != 1 else ''})")

    return "\n".join(lines)


def format_family(person_id: int, query_service: QueryService) -> str:
    """Format person's family relationships for display."""
    lines = []
    lines.append("\n" + "-" * 70)
    lines.append("FAMILY RELATIONSHIPS")
    lines.append("-" * 70)

    # Parents
    parents = query_service.get_parents(person_id)
    if parents:
        father_name = (
            format_full_name(
                given=get_row_value(parents, "FatherGiven"),
                surname=get_row_value(parents, "FatherSurname"),
            )
            if get_row_value(parents, "FatherID")
            else "Unknown"
        )

        mother_name = (
            format_full_name(
                given=get_row_value(parents, "MotherGiven"),
                surname=get_row_value(parents, "MotherSurname"),
            )
            if get_row_value(parents, "MotherID")
            else "Unknown"
        )

        lines.append(f"\nFather: {father_name} (ID: {get_row_value(parents, 'FatherID', 'N/A')})")
        lines.append(f"Mother: {mother_name} (ID: {get_row_value(parents, 'MotherID', 'N/A')})")

    # Spouses
    spouses = query_service.get_spouses(person_id)
    if spouses:
        lines.append(f"\nSpouses ({len(spouses)}):")
        for spouse in spouses:
            spouse_name = format_full_name(
                given=get_row_value(spouse, "Given"), surname=get_row_value(spouse, "Surname")
            )
            marriage_date = get_row_value(spouse, "MarriageDate", "")
            if marriage_date:
                try:
                    date = parse_rm_date(marriage_date)
                    date_str = f" (m. {date.format_display()})"
                except Exception:
                    date_str = f" (m. {marriage_date})"
            else:
                date_str = ""
            lines.append(f"  - {spouse_name} (ID: {spouse['PersonID']}){date_str}")

    # Children
    children = query_service.get_children(person_id)
    if children:
        lines.append(f"\nChildren ({len(children)}):")
        for child in children:
            child_name = format_full_name(
                given=get_row_value(child, "Given"), surname=get_row_value(child, "Surname")
            )
            birth_year = get_row_value(child, "BirthYear", "")
            year_str = f" (b. {birth_year})" if birth_year else ""
            lines.append(f"  - {child_name} (ID: {child['PersonID']}){year_str}")

    if not parents and not spouses and not children:
        lines.append("\nNo family relationships recorded.")

    return "\n".join(lines)


def generate_basic_biography(person_id: int, query_service: QueryService) -> str:
    """Generate a basic biography (no AI enhancement yet)."""
    lines = []
    lines.append("\n" + "-" * 70)
    lines.append("BASIC BIOGRAPHY (Text-based, no AI)")
    lines.append("-" * 70)

    # Get person info
    person = query_service.get_person_with_primary_name(person_id)
    if not person:
        return "\n".join(lines + ["\nPerson not found."])

    full_name = format_full_name(
        given=get_row_value(person, "Given"),
        surname=get_row_value(person, "Surname"),
        prefix=get_row_value(person, "Prefix"),
        suffix=get_row_value(person, "Suffix"),
    )

    # Introduction
    birth_year = get_row_value(person, "BirthYear")
    death_year = get_row_value(person, "DeathYear")

    intro = f"\n{full_name}"
    if birth_year and death_year:
        intro += f" ({birth_year}-{death_year})"
    elif birth_year:
        intro += f" (b. {birth_year})"
    elif death_year:
        intro += f" (d. {death_year})"

    lines.append(intro)

    # Get vital events
    vital_events = query_service.get_vital_events(person_id)

    # Birth
    birth = next((e for e in vital_events if e["FactTypeID"] == 1), None)
    if birth:
        birth_date = get_row_value(birth, "Date", "")
        birth_place = get_row_value(birth, "Place", "")
        if birth_date:
            try:
                date = parse_rm_date(birth_date)
                birth_text = f"{full_name} was born on {date.format_display()}"
            except Exception:
                birth_text = f"{full_name} was born"
        else:
            birth_text = f"{full_name} was born"

        if birth_place:
            try:
                formatted_place = format_place_medium(birth_place)
                birth_text += f" in {formatted_place}"
            except Exception:
                birth_text += f" in {birth_place}"

        lines.append(f"\n{birth_text}.")

    # Marriage
    spouses = query_service.get_spouses(person_id)
    if spouses:
        for spouse in spouses:
            spouse_name = format_full_name(
                given=get_row_value(spouse, "Given"), surname=get_row_value(spouse, "Surname")
            )
            marriage_date = get_row_value(spouse, "MarriageDate", "")
            if marriage_date:
                try:
                    date = parse_rm_date(marriage_date)
                    lines.append(f"\n{full_name} married {spouse_name} on {date.format_display()}.")
                except Exception:
                    lines.append(f"\n{full_name} married {spouse_name}.")

    # Children
    children = query_service.get_children(person_id)
    if children:
        if len(children) == 1:
            lines.append(f"\n{full_name} had one child.")
        else:
            lines.append(f"\n{full_name} had {len(children)} children.")

    # Death
    death = next((e for e in vital_events if e["FactTypeID"] == 2), None)
    if death:
        death_date = get_row_value(death, "Date", "")
        death_place = get_row_value(death, "Place", "")
        if death_date:
            try:
                date = parse_rm_date(death_date)
                death_text = f"{full_name} died on {date.format_display()}"
            except Exception:
                death_text = f"{full_name} died"
        else:
            death_text = f"{full_name} died"

        if death_place:
            try:
                formatted_place = format_place_medium(death_place)
                death_text += f" in {formatted_place}"
            except Exception:
                death_text += f" in {death_place}"

        lines.append(f"\n{death_text}.")

    return "\n".join(lines)


def run_quality_checks(db: RMDatabase, person_id: int | None = None) -> str:
    """Run data quality checks."""
    lines = []
    lines.append("\n" + "-" * 70)
    lines.append("DATA QUALITY CHECKS")
    lines.append("-" * 70)

    validator = DataQualityValidator(db, sample_limit=5)

    # Run all validation checks
    lines.append("\nRunning all validation rules...")
    report = validator.run_all_checks()

    # Display summary
    lines.append(f"\nTotal Issues: {len(report.issues)}")

    # Show issues by severity
    lines.append("\nIssues by Severity:")
    for severity, count in report.totals_by_severity.items():
        lines.append(f"  {severity}: {count}")

    # Show issues by category
    lines.append("\nIssues by Category:")
    for category, count in report.totals_by_category.items():
        lines.append(f"  {category}: {count}")

    # Show entity counts
    lines.append("\nEntity Counts:")
    for entity, count in report.summary.items():
        lines.append(f"  {entity}: {count}")

    # Show a few sample issues
    if report.issues:
        lines.append("\nSample Issues (first 3):")
        for issue in report.issues[:3]:
            lines.append(f"\n  [{issue.severity}] {issue.rule_id}: {issue.name}")
            lines.append(f"    Description: {issue.description}")
            lines.append(f"    Affected count: {issue.count}")
            if issue.samples:
                lines.append(f"    Sample records: {len(issue.samples)}")
                for sample in issue.samples[:2]:
                    lines.append(f"      - {sample}")

    lines.append("\nData quality validation complete.")

    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Milestone 1 Working Prototype",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--person-id", type=int, required=True, help="Person ID to query")
    parser.add_argument("--check-quality", action="store_true", help="Run data quality checks")
    parser.add_argument(
        "--database",
        type=str,
        default="data/Iiams.rmtree",
        help="Path to RootsMagic database (default: data/Iiams.rmtree)",
    )
    parser.add_argument(
        "--extension",
        type=str,
        default="sqlite-extension/icu.dylib",
        help="Path to ICU extension (default: sqlite-extension/icu.dylib)",
    )

    args = parser.parse_args()

    # Validate paths
    db_path = Path(args.database)
    extension_path = Path(args.extension)

    if not db_path.exists():
        print(f"Error: Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    if not extension_path.exists():
        print(f"Error: ICU extension not found: {extension_path}", file=sys.stderr)
        sys.exit(1)

    # Connect to database
    print("Connecting to RootsMagic database...")
    try:
        with RMDatabase(db_path, extension_path=extension_path) as db:
            query_service = QueryService(db)

            # Query person
            person = query_service.get_person_with_primary_name(args.person_id)
            if not person:
                print(f"\nError: Person ID {args.person_id} not found.", file=sys.stderr)
                sys.exit(1)

            # Display person information
            print(format_person_info(person, query_service))

            # Display web tags (Find a Grave, etc.)
            web_tags_output = format_web_tags(args.person_id, db)
            if web_tags_output:
                print(web_tags_output)

            # Display events
            print(format_events(args.person_id, query_service))

            # Display family
            print(format_family(args.person_id, query_service))

            # Generate basic biography
            print(generate_basic_biography(args.person_id, query_service))

            # Display citations
            citations_output = format_citations(args.person_id, db)
            if citations_output:
                print(citations_output)

            # Display sources
            sources_output = format_sources(args.person_id, db)
            if sources_output:
                print(sources_output)

            # Run quality checks
            if args.check_quality:
                print(run_quality_checks(db, args.person_id))

            print("\n" + "=" * 70)
            print("Milestone 1 prototype complete!")
            print("=" * 70)

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
