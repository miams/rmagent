"""
Core genealogy agent orchestration for RMTool.

The GenealogyAgent composes the RM database layer, query helpers,
data-quality validator, and prompt registry to expose higher-level
operations (biography generation, Q&A, quality summaries, and timeline
context). It accepts injectable factories to facilitate unit testing and
alternative data stores.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from rmtool.agent.llm_provider import LLMProvider, LLMResult
from rmtool.agent.prompts import render_prompt
from rmtool.rmlib.database import RMDatabase
from rmtool.rmlib.queries import QueryService
from rmtool.rmlib.quality import DataQualityValidator, QualityReport
from rmtool.rmlib.parsers.date_parser import parse_rm_date


QueryServiceFactory = Callable[[RMDatabase], QueryService]
ValidatorFactory = Callable[[RMDatabase], DataQualityValidator]


def _default_query_factory(db: RMDatabase) -> QueryService:
    return QueryService(db)


def _default_validator_factory(db: RMDatabase) -> DataQualityValidator:
    return DataQualityValidator(db)


@dataclass
class ConversationTurn:
    """Simple memory structure for question answering."""

    question: str
    answer: str


@dataclass
class GenealogyAgent:
    """
    Higher-level AI agent for genealogical tasks.

    Args:
        db_path: Path to RootsMagic database (.rmtree) or None for stub-only tests.
        llm_provider: Provider implementing the LLMProvider interface.
        extension_path: Optional path to ICU extension (default ./sqlite-extension/icu.dylib).
        query_service_factory: Optional factory to create QueryService instances.
        validator_factory: Optional factory to create DataQualityValidator instances.
    """

    llm_provider: LLMProvider
    db_path: Optional[Path] = None
    extension_path: Path = Path("./sqlite-extension/icu.dylib")
    query_service_factory: QueryServiceFactory = _default_query_factory
    validator_factory: ValidatorFactory = _default_validator_factory
    _memory: List[ConversationTurn] = field(default_factory=list)

    # ---- Public API -----------------------------------------------------

    def generate_biography(self, person_id: int, style: str = "standard", max_tokens: Optional[int] = None) -> LLMResult:
        """Generate a narrative biography using the configured prompts/LLM."""

        context = self._build_biography_context(person_id, style)
        prompt = render_prompt("biography", context)
        return self._invoke_llm(prompt, max_tokens=max_tokens)

    def analyze_data_quality(self) -> QualityReport:
        """Run the full data-quality validator and return the structured report."""

        def _run_validator(db: Optional[RMDatabase]) -> QualityReport:
            if db is None:
                validator = self.validator_factory(None)  # type: ignore[arg-type]
            else:
                validator = self.validator_factory(db)
            return validator.run_all_checks()

        return self._with_database(_run_validator)

    def ask(self, question: str, person_id: Optional[int] = None, max_tokens: Optional[int] = None) -> LLMResult:
        """Answer ad-hoc questions with light context and persistent memory."""

        context = self._build_qa_context(question, person_id)
        prompt = render_prompt("qa", context)
        result = self._invoke_llm(prompt, max_tokens=max_tokens)
        self._memory.append(ConversationTurn(question=question, answer=result.text))
        return result

    def generate_timeline_summary(self, person_id: int, max_tokens: Optional[int] = None) -> LLMResult:
        """Create a timeline-oriented summary for timeline export preparation."""

        context = self._build_timeline_context(person_id)
        prompt = render_prompt("timeline", context)
        return self._invoke_llm(prompt, max_tokens=max_tokens)

    def memory(self) -> Sequence[ConversationTurn]:
        """Return a read-only view of conversation history."""

        return tuple(self._memory)

    # ---- Context Builders -----------------------------------------------

    def _build_biography_context(self, person_id: int, style: str) -> Dict[str, str]:
        def _builder(db: Optional[RMDatabase]) -> Dict[str, str]:
            query = self._make_query_service(db)
            person = self._row_to_dict(query.get_person_with_primary_name(person_id))
            if person is None:
                raise ValueError(f"Person {person_id} not found")
            events = self._rows_to_dicts(query.get_person_events(person_id))
            ancestors = self._rows_to_dicts(query.get_direct_ancestors(person_id, generations=3))
            spouses = self._rows_to_dicts(query.get_spouses(person_id))
            children = self._rows_to_dicts(query.get_children(person_id))
            parents = self._row_to_dict(query.get_parents(person_id))
            siblings = self._rows_to_dicts(self._fetch_siblings(query, parents, person_id))
            life_span = self._derive_life_span(person, events)

            person_summary = self._format_person_summary(person, style)
            timeline_overview = self._format_events(events)
            relationship_notes = self._format_ancestors(ancestors)
            family_overview = self._format_family_overview(spouses, children, siblings)
            early_life_overview = self._format_early_life(person, parents, siblings, life_span)
            family_loss_notes = self._format_family_losses(life_span, parents, spouses, siblings, children)
            sibling_lines = self._format_siblings(siblings)
            sibling_summary = "\n".join(sibling_lines) if sibling_lines else "No sibling records available."

            return {
                "person_summary": person_summary,
                "timeline_overview": timeline_overview,
                "relationship_notes": relationship_notes,
                "family_overview": family_overview,
                "early_life_overview": early_life_overview,
                "family_loss_notes": family_loss_notes,
                "sibling_summary": sibling_summary,
                "source_notes": "Sources include citations extracted from RootsMagic events.",
            }

        return self._with_database(_builder)

    def _build_qa_context(self, question: str, person_id: Optional[int]) -> Dict[str, str]:
        def _builder(db: Optional[RMDatabase]) -> Dict[str, str]:
            snippets: List[str] = []
            query = self._make_query_service(db)

            if person_id is not None:
                person = self._row_to_dict(query.get_person_with_primary_name(person_id))
                if person:
                    snippets.append(self._format_person_summary(person, style="short"))
                    events = self._rows_to_dicts(query.get_person_events(person_id))
                    snippets.append(self._format_events(events))
                    spouses = self._rows_to_dicts(query.get_spouses(person_id))
                    children = self._rows_to_dicts(query.get_children(person_id))
                    parents = self._row_to_dict(query.get_parents(person_id))
                    siblings = self._rows_to_dicts(self._fetch_siblings(query, parents, person_id))
                    life_span = self._derive_life_span(person, events)
                    snippets.append(self._format_family_overview(spouses, children, siblings))
                    snippets.append(self._format_early_life(person, parents, siblings, life_span))

            history_snippets = [f"Q: {turn.question}\nA: {turn.answer}" for turn in self._memory[-3:]]
            snippets.extend(history_snippets)

            return {
                "question": question,
                "context_snippets": "\n".join(snippets) or "No prior context.",
            }

        return self._with_database(_builder)

    def _build_timeline_context(self, person_id: int) -> Dict[str, str]:
        def _builder(db: Optional[RMDatabase]) -> Dict[str, str]:
            query = self._make_query_service(db)
            person = self._row_to_dict(query.get_person_with_primary_name(person_id))
            events = self._rows_to_dicts(query.get_person_events(person_id))

            person_name = self._format_person_name(person) if person else f"Person {person_id}"
            events_json = self._format_events_json(events)
            return {"person_name": person_name, "events_json": events_json}

        return self._with_database(_builder)

    # ---- Helper Methods -------------------------------------------------

    def _invoke_llm(self, prompt: str, max_tokens: Optional[int] = None) -> LLMResult:
        kwargs = {}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        return self.llm_provider.generate(prompt, **kwargs)

    def _with_database(self, fn: Callable[[Optional[RMDatabase]], Dict[str, str] | QualityReport]) -> Dict[str, str] | QualityReport:
        if self.db_path is None:
            return fn(None)
        with RMDatabase(self.db_path, extension_path=self.extension_path) as db:
            return fn(db)

    def _make_query_service(self, db: Optional[RMDatabase]) -> QueryService:
        if db is None:
            return self.query_service_factory(None)  # type: ignore[arg-type]
        return self.query_service_factory(db)

    @staticmethod
    def _format_person_name(row: Optional[Dict[str, str]]):
        if not row:
            return "Unknown Person"
        given = row.get("Given", "").strip()
        surname = row.get("Surname", "").strip()
        full = f"{given} {surname}".strip()
        return full or "Unknown Person"

    def _format_person_summary(self, row, style: str) -> str:
        if not row:
            return "Person not found."
        name = self._format_person_name(row)
        birth_year = row.get("BirthYear")
        death_year = row.get("DeathYear")
        span = ""
        if birth_year or death_year:
            span = f" ({birth_year or '?'}-{death_year or '?'})"
        return f"{name}{span} • Style: {style}"

    @staticmethod
    def _format_events(events) -> str:
        lines = []
        for event in events or []:
            event_type = event.get("EventType")
            date = event.get("Date") or ""
            place = event.get("Place") or ""
            details = event.get("Details") or ""
            lines.append(f"- {event_type}: {date} {place} {details}".strip())
        return "\n".join(lines) if lines else "No events available."

    @staticmethod
    def _format_events_json(events) -> str:
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
    def _format_ancestors(ancestors) -> str:
        lines = []
        for ancestor in ancestors or []:
            rel = ancestor.get("Relationship")
            name = f"{ancestor.get('Given', '')} {ancestor.get('Surname', '')}".strip()
            generation = ancestor.get("Generation")
            lines.append(f"- {rel} ({generation}): {name}")
        return "\n".join(lines) if lines else "Ancestor data unavailable."

    @staticmethod
    def _row_to_dict(row):
        if row is None or isinstance(row, dict):
            return row
        if hasattr(row, "keys"):
            return {key: row[key] for key in row.keys()}
        return row

    def _rows_to_dicts(self, rows):
        if rows is None:
            return rows
        return [self._row_to_dict(row) for row in rows]

    def _format_family_overview(self, spouses, children, siblings) -> str:
        spouse_lines = self._format_spouses(spouses)
        child_lines = self._format_children(children)
        sibling_lines = self._format_siblings(siblings)
        sections = []
        if spouse_lines:
            sections.append("Spouses:\n" + "\n".join(spouse_lines))
        if child_lines:
            sections.append("Children:\n" + "\n".join(child_lines))
        if sibling_lines:
            sections.append("Siblings:\n" + "\n".join(sibling_lines))
        return "\n\n".join(sections) if sections else "No marriage or child data available."

    def _format_spouses(self, spouses) -> List[str]:
        lines: List[str] = []
        if not spouses:
            return lines
        for spouse in spouses:
            name = self._format_person_name(spouse)
            marriage_date = self._format_rm_date(spouse.get("MarriageDate"))
            marriage_place = (spouse.get("MarriagePlace") or "").strip()
            birth_year = spouse.get("BirthYear")
            death_year = spouse.get("DeathYear")
            death_info = self._format_death_detail(spouse)
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

    def _format_children(self, children) -> List[str]:
        lines: List[str] = []
        if not children:
            return lines
        for child in children:
            name = self._format_person_name(child)
            birth_date = self._format_rm_date(child.get("BirthDate"))
            birth_place = (child.get("BirthPlace") or "").strip()
            birth_year = child.get("BirthYear")
            death_year = child.get("DeathYear")
            death_info = self._format_death_detail(child)
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

    def _format_siblings(self, siblings) -> List[str]:
        lines: List[str] = []
        if not siblings:
            return lines
        for sibling in siblings:
            name = self._format_person_name(sibling)
            birth_date = self._format_rm_date(sibling.get("BirthDate"))
            birth_place = (sibling.get("BirthPlace") or "").strip()
            death_info = self._format_death_detail(sibling)
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

    def _format_early_life(self, person, parents, siblings, life_span: Dict[str, Optional[int]]) -> str:
        person_name = self._format_person_name(person)
        birth_year = life_span.get("birth_year")
        parent_bits = []
        father_age = self._calculate_parent_age(parents, "FatherBirthYear", birth_year)
        mother_age = self._calculate_parent_age(parents, "MotherBirthYear", birth_year)
        if father_age is not None:
            father_name = self._combine_name(parents, "FatherGiven", "FatherSurname")
            parent_bits.append(f"{father_name} (~{father_age})")
        if mother_age is not None:
            mother_name = self._combine_name(parents, "MotherGiven", "MotherSurname")
            parent_bits.append(f"{mother_name} (~{mother_age})")

        total_children = len(siblings) + 1
        birth_order = self._determine_birth_order(person, siblings, life_span)
        if birth_order:
            order_label = f"{self._ordinal(birth_order)} of {total_children} children"
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
            older = [s for s in siblings if self._is_older_than_subject(s, life_span)]
            younger = [s for s in siblings if not self._is_older_than_subject(s, life_span)]
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

    def _format_family_losses(self, life_span, parents, spouses, siblings, children) -> str:
        losses = []
        birth_year = life_span.get("birth_year")
        death_year = life_span.get("death_year")
        relatives: List[Tuple[str, Dict[str, str]]] = []

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
            death_year_value = self._parse_year_from_row(data, "DeathYear", "DeathDate")
            if death_year_value is None:
                continue
            if birth_year is not None and death_year_value < birth_year:
                continue
            if death_year is not None and death_year_value > death_year:
                continue
            name = self._format_person_name(data)
            losses.append(f"- {name} ({relation}) died in {death_year_value}.")

        return "\n".join(losses) if losses else "No recorded family deaths occurred during the subject's lifetime."

    def _calculate_parent_age(self, parents, birth_year_key: str, child_birth_year: Optional[int]) -> Optional[int]:
        if not parents or child_birth_year is None:
            return None
        birth_year = parents.get(birth_year_key)
        if birth_year is None:
            return None
        return child_birth_year - birth_year

    def _combine_name(self, row, given_key: str, surname_key: str) -> str:
        if not row:
            return ""
        return f"{row.get(given_key, '').strip()} {row.get(surname_key, '').strip()}".strip()

    def _determine_birth_order(self, person, siblings, life_span) -> Optional[int]:
        entries: List[Tuple[Tuple[int, int], int]] = []
        subject_id = person.get("PersonID")
        subject_sort = life_span.get("birth_sort")
        subject_year = life_span.get("birth_year")
        entries.append((self._sort_key(subject_sort, subject_year), subject_id or 0))
        for sibling in siblings or []:
            sort_key = self._sort_key(self._extract_sort_value(sibling.get("BirthSortDate")), sibling.get("BirthYear"))
            entries.append((sort_key, sibling.get("PersonID") or 0))
        entries.sort(key=lambda item: (item[0], item[1]))
        for idx, (_, pid) in enumerate(entries, start=1):
            if pid == subject_id:
                return idx
        return None

    def _is_older_than_subject(self, sibling, life_span) -> bool:
        sibling_key = self._sort_key(self._extract_sort_value(sibling.get("BirthSortDate")), sibling.get("BirthYear"))
        subject_key = self._sort_key(life_span.get("birth_sort"), life_span.get("birth_year"))
        return sibling_key < subject_key

    @staticmethod
    def _sort_key(sort_value: Optional[int], year: Optional[int]) -> Tuple[int, int]:
        sentinel = 9223372036854775807
        return (
            sort_value if sort_value is not None else sentinel,
            year if year is not None else sentinel,
        )

    def _extract_sort_value(self, value: Optional[int]) -> Optional[int]:
        if value in (None, 0):
            return None
        return value

    def _derive_life_span(self, person, events) -> Dict[str, Optional[int]]:
        birth_year = person.get("BirthYear")
        death_year = person.get("DeathYear")
        birth_sort = None
        death_sort = None
        for event in events or []:
            event_type = (event.get("EventType") or "").lower()
            sort_date = self._extract_sort_value(event.get("SortDate"))
            if "birth" in event_type and birth_sort is None:
                birth_sort = sort_date
                birth_year = birth_year or self._parse_year_from_rm_date(event.get("Date"))
            if "death" in event_type and death_sort is None:
                death_sort = sort_date
                death_year = death_year or self._parse_year_from_rm_date(event.get("Date"))
        return {
            "birth_year": birth_year,
            "death_year": death_year,
            "birth_sort": birth_sort,
            "death_sort": death_sort,
        }

    def _fetch_siblings(self, query: QueryService, parents: Optional[Dict[str, str]], person_id: int):
        if not parents:
            return []
        siblings = []
        seen = {person_id}
        for key in ("FatherID", "MotherID"):
            parent_id = parents.get(key)
            if parent_id:
                rows = query.get_children(parent_id)
                for row in rows or []:
                    row_dict = self._row_to_dict(row)
                    pid = row_dict.get("PersonID") if row_dict else None
                    if pid is None or pid in seen or pid == person_id:
                        continue
                    seen.add(pid)
                    siblings.append(row_dict)
        siblings.sort(key=lambda row: self._sort_key(self._extract_sort_value(row.get("BirthSortDate")), row.get("BirthYear")))
        return siblings

    def _parse_year_from_row(self, row, year_key: str, date_key: str) -> Optional[int]:
        if not row:
            return None
        year = row.get(year_key)
        if year is not None:
            return year
        return self._parse_year_from_rm_date(row.get(date_key))

    def _format_death_detail(self, row) -> Optional[str]:
        year = row.get("DeathYear")
        if year:
            return f"died {year}"
        death_date = self._format_rm_date(row.get("DeathDate"))
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
    def _format_rm_date(value: Optional[str]) -> Optional[str]:
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

    def _parse_year_from_rm_date(self, value: Optional[str]) -> Optional[int]:
        if not value:
            return None
        normalized = value.strip()
        if not normalized:
            return None
        try:
            parsed = parse_rm_date(normalized)
        except Exception:
            return self._extract_year_from_string(normalized)
        year = getattr(parsed, "year", None)
        if year:
            return year
        return self._extract_year_from_string(normalized)

    @staticmethod
    def _extract_year_from_string(value: str) -> Optional[int]:
        digits = "".join(ch if ch.isdigit() else " " for ch in value)
        for part in digits.split():
            if len(part) == 4:
                try:
                    return int(part)
                except ValueError:
                    continue
        return None

    def _ordinal(self, value: Optional[int]) -> str:
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
