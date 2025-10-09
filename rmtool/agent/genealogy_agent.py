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
from typing import Callable, Dict, List, Optional, Sequence

from rmtool.agent.llm_provider import LLMProvider, LLMResult
from rmtool.agent.prompts import render_prompt
from rmtool.rmlib.database import RMDatabase
from rmtool.rmlib.queries import QueryService
from rmtool.rmlib.quality import DataQualityValidator, QualityReport


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
            person = query.get_person_with_primary_name(person_id)
            if person is None:
                raise ValueError(f"Person {person_id} not found")
            events = query.get_person_events(person_id)
            ancestors = query.get_direct_ancestors(person_id, generations=3)

            person_summary = self._format_person_summary(person, style)
            timeline_overview = self._format_events(events)
            relationship_notes = self._format_ancestors(ancestors)

            return {
                "person_summary": person_summary,
                "timeline_overview": timeline_overview,
                "relationship_notes": relationship_notes,
                "source_notes": "Sources include citations extracted from RootsMagic events.",
            }

        return self._with_database(_builder)

    def _build_qa_context(self, question: str, person_id: Optional[int]) -> Dict[str, str]:
        def _builder(db: Optional[RMDatabase]) -> Dict[str, str]:
            snippets: List[str] = []
            query = self._make_query_service(db)

            if person_id is not None:
                person = query.get_person_with_primary_name(person_id)
                if person:
                    snippets.append(self._format_person_summary(person, style="short"))
                    events = query.get_person_events(person_id)
                    snippets.append(self._format_events(events))

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
            person = query.get_person_with_primary_name(person_id)
            events = query.get_person_events(person_id)

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
        return f"{row.get('Given', '').strip()} {row.get('Surname', '').strip()}".strip()

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
