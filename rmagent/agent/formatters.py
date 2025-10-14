"""
Formatting utilities for genealogy agent.

Contains all formatting methods for persons, events, families, and citations.
Separated from agent orchestration for better testability and maintainability.
"""

from __future__ import annotations

from rmagent.rmlib.parsers.date_parser import parse_rm_date


class GenealogyFormatters:
    """Static formatting utilities for genealogical data."""

    @staticmethod
    def format_person_name(row: dict[str, str] | None) -> str:
        """Format person's full name from database row."""
        if not row:
            return "Unknown Person"
        given = row.get("Given", "").strip()
        surname = row.get("Surname", "").strip()
        full = f"{given} {surname}".strip()
        return full or "Unknown Person"

    @staticmethod
    def format_person_summary(row, style: str) -> str:
        """Format person summary with lifespan and style."""
        if not row:
            return "Person not found."
        name = GenealogyFormatters.format_person_name(row)
        birth_year = row.get("BirthYear")
        death_year = row.get("DeathYear")
        span = ""
        if birth_year or death_year:
            span = f" ({birth_year or '?'}-{death_year or '?'})"
        return f"{name}{span} • Style: {style}"

    @staticmethod
    def format_events(events, event_citations: dict[int, list[int]] | None = None) -> str:
        """Format events list with notes and inline citation IDs for LLM context.

        Args:
            events: List of event dicts with EventID, EventType, Date, Place, Details, Note
            event_citations: Optional dict mapping EventID -> list of CitationIDs

        Returns:
            Formatted string with events, notes, and inline {{cite:ID}} markers
        """
        lines = []
        for event in events or []:
            event_id = event.get("EventID")
            event_type = event.get("EventType")
            date = GenealogyFormatters.format_rm_date(event.get("Date")) or ""
            place = event.get("Place") or ""
            details = event.get("Details") or ""
            note = event.get("Note") or ""

            # Get citation IDs for this event
            citation_ids = []
            if event_citations and event_id in event_citations:
                citation_ids = event_citations[event_id]

            # Format citation markers (e.g., "{{cite:123}}")
            citation_markers = " ".join(f"{{{{cite:{cid}}}}}" for cid in citation_ids)

            # Format main event line with inline citations
            event_line = f"- {event_type}: {date} {place} {details}".strip()
            if citation_markers:
                event_line += f" {citation_markers}"
            lines.append(event_line)

            # Add note if present (often contains full article transcriptions)
            if note:
                # Show "NOTE: " prefix only once, then indent subsequent lines
                note_lines = note.split('\n')
                for idx, note_line in enumerate(note_lines):
                    if note_line.strip():
                        if idx == 0:
                            note_text = f"    NOTE: {note_line.strip()}"
                            # Add citation markers to first line of note too
                            if citation_markers:
                                note_text += f" {citation_markers}"
                            lines.append(note_text)
                        else:
                            lines.append(f"    {note_line.strip()}")

        return "\n".join(lines) if lines else "No events available."

    @staticmethod
    def format_events_json(events) -> str:
        """Format events as JSON-style string for timeline context."""
        entries = []
        for event in events or []:
            entries.append(
                {
                    "event_id": event.get("EventID"),
                    "type": event.get("EventType"),
                    "date": event.get("Date"),
                    "place": event.get("Place"),
                    "details": event.get("Details"),
                }
            )
        return str(entries)

    @staticmethod
    def format_ancestors(ancestors) -> str:
        """Format ancestors list with relationships and generations."""
        lines = []
        for ancestor in ancestors or []:
            rel = ancestor.get("Relationship")
            name = f"{ancestor.get('Given', '')} {ancestor.get('Surname', '')}".strip()
            generation = ancestor.get("Generation")
            lines.append(f"- {rel} ({generation}): {name}")
        return "\n".join(lines) if lines else "Ancestor data unavailable."

    @staticmethod
    def row_to_dict(row):
        """Convert sqlite3.Row to dict."""
        if row is None or isinstance(row, dict):
            return row
        if hasattr(row, "keys"):
            return {key: row[key] for key in row.keys()}
        return row

    @staticmethod
    def rows_to_dicts(rows):
        """Convert list of sqlite3.Row to list of dicts."""
        if rows is None:
            return rows
        return [GenealogyFormatters.row_to_dict(row) for row in rows]

    @staticmethod
    def format_family_overview(spouses, children, siblings) -> str:
        """Format complete family overview with spouses, children, siblings."""
        spouse_lines = GenealogyFormatters.format_spouses(spouses)
        child_lines = GenealogyFormatters.format_children(children)
        sibling_lines = GenealogyFormatters.format_siblings(siblings)
        sections = []
        if spouse_lines:
            sections.append("Spouses:\n" + "\n".join(spouse_lines))
        if child_lines:
            sections.append("Children:\n" + "\n".join(child_lines))
        if sibling_lines:
            sections.append("Siblings:\n" + "\n".join(sibling_lines))
        return "\n\n".join(sections) if sections else "No marriage or child data available."

    @staticmethod
    def format_spouses(spouses) -> list[str]:
        """Format list of spouses with marriage details."""
        lines: list[str] = []
        if not spouses:
            return lines
        for spouse in spouses:
            name = GenealogyFormatters.format_person_name(spouse)
            marriage_date = GenealogyFormatters.format_rm_date(spouse.get("MarriageDate"))
            marriage_place = (spouse.get("MarriagePlace") or "").strip()
            birth_year = spouse.get("BirthYear")
            death_year = spouse.get("DeathYear")
            death_info = GenealogyFormatters.format_death_detail(spouse)
            lifespan = ""
            if birth_year or death_year:
                lifespan = f" ({birth_year or '?'}-{death_year or '?'})"
            detail_parts = []
            if marriage_date or marriage_place:
                detail = f"m. {marriage_date or 'Unknown'}"
                if marriage_place:
                    detail += f", {marriage_place}"
                detail_parts.append(detail)
            descriptor = ", ".join(detail_parts) if detail_parts else ""
            entry = f"- {name}{lifespan}"
            if descriptor:
                entry += f" — {descriptor}"
            if death_info:
                entry += f"; {death_info}"
            lines.append(entry)
        return lines

    @staticmethod
    def format_children(children) -> list[str]:
        """Format list of children with birth details."""
        lines: list[str] = []
        if not children:
            return lines
        for child in children:
            name = GenealogyFormatters.format_person_name(child)
            birth_date = GenealogyFormatters.format_rm_date(child.get("BirthDate"))
            birth_place = (child.get("BirthPlace") or "").strip()
            birth_year = child.get("BirthYear")
            death_year = child.get("DeathYear")
            death_info = GenealogyFormatters.format_death_detail(child)
            lifespan = ""
            if birth_year or death_year:
                lifespan = f" ({birth_year or '?'}-{death_year or '?'})"
            info_parts = []
            if birth_date or birth_place:
                label = birth_date or "Unknown birth date"
                if birth_place:
                    label += f" in {birth_place}"
                info_parts.append(label)
            entry = f"- {name}{lifespan}"
            if info_parts:
                entry += f" — {', '.join(info_parts)}"
            if death_info:
                entry += f"; {death_info}"
            lines.append(entry)
        return lines

    @staticmethod
    def format_siblings(siblings) -> list[str]:
        """Format list of siblings with birth/death details."""
        lines: list[str] = []
        if not siblings:
            return lines
        for sibling in siblings:
            name = GenealogyFormatters.format_person_name(sibling)
            birth_date = GenealogyFormatters.format_rm_date(sibling.get("BirthDate"))
            birth_place = (sibling.get("BirthPlace") or "").strip()
            death_info = GenealogyFormatters.format_death_detail(sibling)
            details = []
            if birth_date or birth_place:
                label = birth_date or "Unknown birth date"
                if birth_place:
                    label += f" in {birth_place}"
                details.append(label)
            if death_info:
                details.append(death_info)
            entry = f"- {name}"
            if details:
                entry += f" — {', '.join(details)}"
            lines.append(entry)
        return lines

    @staticmethod
    def format_early_life(
        person, parents, siblings, life_span: dict[str, int | None]
    ) -> str:
        """Format early life narrative with birth order, parental ages, migration notes."""
        person_name = GenealogyFormatters.format_person_name(person)
        birth_year = life_span.get("birth_year")
        parent_bits = []
        father_age = GenealogyFormatters.calculate_parent_age(parents, "FatherBirthYear", birth_year)
        mother_age = GenealogyFormatters.calculate_parent_age(parents, "MotherBirthYear", birth_year)
        if father_age is not None:
            father_name = GenealogyFormatters.combine_name(parents, "FatherGiven", "FatherSurname")
            parent_bits.append(f"{father_name} (~{father_age})")
        if mother_age is not None:
            mother_name = GenealogyFormatters.combine_name(parents, "MotherGiven", "MotherSurname")
            parent_bits.append(f"{mother_name} (~{mother_age})")

        total_children = len(siblings) + 1
        birth_order = GenealogyFormatters.determine_birth_order(person, siblings, life_span)
        if birth_order:
            order_label = f"{GenealogyFormatters.ordinal(birth_order)} of {total_children} children"
        else:
            order_label = f"one of {total_children} children"

        sibling_birth_places = {s.get("BirthPlace") for s in siblings or [] if s.get("BirthPlace")}
        migration_note = ""
        if sibling_birth_places and len(sibling_birth_places) > 1:
            migration_note = (
                f"Sibling births recorded in {', '.join(sorted(sibling_birth_places))} "
                "suggest family movement during childhood."
            )

        lines = []
        if total_children > 1:
            lines.append(f"{person_name} was the {order_label}.")
        if parent_bits:
            lines.append(f"Estimated parental ages at the birth: {', '.join(parent_bits)}.")
        if siblings:
            older = [s for s in siblings if GenealogyFormatters.is_older_than_subject(s, life_span)]
            younger = [s for s in siblings if not GenealogyFormatters.is_older_than_subject(s, life_span)]
            summary_parts = []
            if older:
                summary_parts.append(f"{len(older)} older siblings")
            if younger:
                summary_parts.append(f"{len(younger)} younger siblings")
            if summary_parts:
                lines.append(f"Siblings included {', '.join(summary_parts)}.")
        if migration_note:
            lines.append(migration_note)
        return "\n".join(lines) if lines else "Early life details are limited."

    @staticmethod
    def format_family_losses(life_span, parents, spouses, siblings, children) -> str:
        """Format family deaths that occurred during person's lifetime."""
        losses = []
        birth_year = life_span.get("birth_year")
        death_year = life_span.get("death_year")
        relatives: list[tuple[str, dict[str, str]]] = []

        if parents:
            father = {
                "Given": parents.get("FatherGiven"),
                "Surname": parents.get("FatherSurname"),
                "DeathYear": parents.get("FatherDeathYear"),
            }
            mother = {
                "Given": parents.get("MotherGiven"),
                "Surname": parents.get("MotherSurname"),
                "DeathYear": parents.get("MotherDeathYear"),
            }
            relatives.extend([("Father", father), ("Mother", mother)])

        for spouse in spouses or []:
            relatives.append(("Spouse", spouse))
        for sibling in siblings or []:
            relatives.append(("Sibling", sibling))
        for child in children or []:
            relatives.append(("Child", child))

        for relation, data in relatives:
            death_year_value = GenealogyFormatters.parse_year_from_row(data, "DeathYear", "DeathDate")
            if death_year_value is None:
                continue
            if birth_year is not None and death_year_value < birth_year:
                continue
            if death_year is not None and death_year_value > death_year:
                continue
            name = GenealogyFormatters.format_person_name(data)
            losses.append(f"- {name} ({relation}) died in {death_year_value}.")

        return (
            "\n".join(losses)
            if losses
            else "No recorded family deaths occurred during the subject's lifetime."
        )

    @staticmethod
    def calculate_parent_age(
        parents, birth_year_key: str, child_birth_year: int | None
    ) -> int | None:
        """Calculate parent's age at child's birth."""
        if not parents or child_birth_year is None:
            return None
        birth_year = parents.get(birth_year_key)
        if birth_year is None:
            return None
        return child_birth_year - birth_year

    @staticmethod
    def combine_name(row, given_key: str, surname_key: str) -> str:
        """Combine given and surname fields into full name."""
        if not row:
            return ""
        return f"{row.get(given_key, '').strip()} {row.get(surname_key, '').strip()}".strip()

    @staticmethod
    def determine_birth_order(person, siblings, life_span) -> int | None:
        """Determine birth order among siblings."""
        entries: list[tuple[tuple[int, int], int]] = []
        subject_id = person.get("PersonID")
        subject_sort = life_span.get("birth_sort")
        subject_year = life_span.get("birth_year")
        entries.append((GenealogyFormatters.sort_key(subject_sort, subject_year), subject_id or 0))
        for sibling in siblings or []:
            sort_key = GenealogyFormatters.sort_key(
                GenealogyFormatters.extract_sort_value(sibling.get("BirthSortDate")), sibling.get("BirthYear")
            )
            entries.append((sort_key, sibling.get("PersonID") or 0))
        entries.sort(key=lambda item: (item[0], item[1]))
        for idx, (_, pid) in enumerate(entries, start=1):
            if pid == subject_id:
                return idx
        return None

    @staticmethod
    def is_older_than_subject(sibling, life_span) -> bool:
        """Check if sibling is older than subject."""
        sibling_key = GenealogyFormatters.sort_key(
            GenealogyFormatters.extract_sort_value(sibling.get("BirthSortDate")), sibling.get("BirthYear")
        )
        subject_key = GenealogyFormatters.sort_key(life_span.get("birth_sort"), life_span.get("birth_year"))
        return sibling_key < subject_key

    @staticmethod
    def sort_key(sort_value: int | None, year: int | None) -> tuple[int, int]:
        """Generate sort key for date ordering."""
        sentinel = 9223372036854775807
        return (
            sort_value if sort_value is not None else sentinel,
            year if year is not None else sentinel,
        )

    @staticmethod
    def extract_sort_value(value: int | None) -> int | None:
        """Extract sort value, treating 0 as None."""
        if value in (None, 0):
            return None
        return value

    @staticmethod
    def derive_life_span(person, events) -> dict[str, int | None]:
        """Derive birth/death years and sort dates from person and events."""
        birth_year = person.get("BirthYear")
        death_year = person.get("DeathYear")
        birth_sort = None
        death_sort = None
        for event in events or []:
            event_type = (event.get("EventType") or "").lower()
            sort_date = GenealogyFormatters.extract_sort_value(event.get("SortDate"))
            if "birth" in event_type and birth_sort is None:
                birth_sort = sort_date
                birth_year = birth_year or GenealogyFormatters.parse_year_from_rm_date(event.get("Date"))
            if "death" in event_type and death_sort is None:
                death_sort = sort_date
                death_year = death_year or GenealogyFormatters.parse_year_from_rm_date(event.get("Date"))
        return {
            "birth_year": birth_year,
            "death_year": death_year,
            "birth_sort": birth_sort,
            "death_sort": death_sort,
        }

    @staticmethod
    def parse_year_from_row(row, year_key: str, date_key: str) -> int | None:
        """Parse year from row, trying year field first then date field."""
        if not row:
            return None
        year = row.get(year_key)
        if year is not None:
            return year
        return GenealogyFormatters.parse_year_from_rm_date(row.get(date_key))

    @staticmethod
    def format_death_detail(row) -> str | None:
        """Format death details (date and place)."""
        year = row.get("DeathYear")
        if year:
            return f"died {year}"
        death_date = GenealogyFormatters.format_rm_date(row.get("DeathDate"))
        death_place = (row.get("DeathPlace") or "").strip()
        if not death_date and not death_place:
            return None
        details = []
        if death_date:
            details.append(f"died {death_date}")
        if death_place:
            details.append(f"{death_place}")
        return ", ".join(details)

    @staticmethod
    def format_rm_date(value: str | None) -> str | None:
        """Format RootsMagic date string for display."""
        if not value:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        try:
            parsed = parse_rm_date(normalized)
        except Exception:  # pragma: no cover - fallback for unexpected strings
            return normalized
        if hasattr(parsed, "format_display"):
            display = parsed.format_display()
            if display:
                return display
        return normalized

    @staticmethod
    def parse_year_from_rm_date(value: str | None) -> int | None:
        """Parse year from RootsMagic date string."""
        if not value:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        try:
            parsed = parse_rm_date(normalized)
        except Exception:
            return GenealogyFormatters.extract_year_from_string(normalized)
        year = getattr(parsed, "year", None)
        if year:
            return year
        return GenealogyFormatters.extract_year_from_string(normalized)

    @staticmethod
    def extract_year_from_string(value: str) -> int | None:
        """Extract 4-digit year from string."""
        digits = "".join(ch if ch.isdigit() else " " for ch in value)
        for part in digits.split():
            if len(part) == 4:
                try:
                    return int(part)
                except ValueError:
                    continue
        return None

    @staticmethod
    def ordinal(value: int | None) -> str:
        """Convert number to ordinal string (1st, 2nd, 3rd, etc)."""
        if value is None:
            return ""
        suffix = "th"
        if value % 100 not in {11, 12, 13}:
            if value % 10 == 1:
                suffix = "st"
            elif value % 10 == 2:
                suffix = "nd"
            elif value % 10 == 3:
                suffix = "rd"
        return f"{value}{suffix}"

    @staticmethod
    def format_available_citations(citations: list[dict]) -> str:
        """
        Format citations for LLM prompt.
        Returns formatted string listing all available citations with {{cite:ID}} markers.
        Note: Braces are doubled to escape them from Python's format_map() in prompt rendering.
        """
        if not citations:
            return "No citations available."

        lines = []
        for citation in citations:
            cid = citation.get("CitationID")
            source_name = citation.get("SourceName", "Unknown")
            citation_name = citation.get("CitationName", "")
            event_type = citation.get("EventType", "")

            # Double braces to escape them from format_map() - will become {cite:123} in final prompt
            desc = f"- {{{{cite:{cid}}}}}: {source_name}"
            if citation_name:
                desc += f" ({citation_name})"
            if event_type:
                desc += f" [Used for: {event_type}]"
            lines.append(desc)

        return "\n".join(lines)
