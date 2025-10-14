"""
Core genealogy agent orchestration for RMAgent.

The GenealogyAgent composes the RM database layer, query helpers,
data-quality validator, and prompt registry to expose higher-level
operations (biography generation, Q&A, quality summaries, and timeline
context). It accepts injectable factories to facilitate unit testing and
alternative data stores.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from rmagent.agent.formatters import GenealogyFormatters
from rmagent.agent.llm_provider import LLMProvider, LLMResult
from rmagent.agent.prompts import render_prompt
from rmagent.rmlib.database import RMDatabase
from rmagent.rmlib.quality import DataQualityValidator, QualityReport
from rmagent.rmlib.queries import QueryService

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
    db_path: Path | None = None
    extension_path: Path = Path("./sqlite-extension/icu.dylib")
    query_service_factory: QueryServiceFactory = _default_query_factory
    validator_factory: ValidatorFactory = _default_validator_factory
    _memory: list[ConversationTurn] = field(default_factory=list)

    # ---- Public API -----------------------------------------------------

    def generate_biography(self, person_id: int, style: str = "standard", max_tokens: int | None = None) -> LLMResult:
        """Generate a narrative biography using the configured prompts/LLM."""

        context = self._build_biography_context(person_id, style)
        prompt = render_prompt("biography", context)
        return self._invoke_llm(prompt, max_tokens=max_tokens)

    def analyze_data_quality(self) -> QualityReport:
        """Run the full data-quality validator and return the structured report."""

        def _run_validator(db: RMDatabase | None) -> QualityReport:
            if db is None:
                validator = self.validator_factory(None)  # type: ignore[arg-type]
            else:
                validator = self.validator_factory(db)
            return validator.run_all_checks()

        return self._with_database(_run_validator)

    def ask(self, question: str, person_id: int | None = None, max_tokens: int | None = None) -> LLMResult:
        """Answer ad-hoc questions with light context and persistent memory."""

        context = self._build_qa_context(question, person_id)
        prompt = render_prompt("qa", context)
        result = self._invoke_llm(prompt, max_tokens=max_tokens)
        self._memory.append(ConversationTurn(question=question, answer=result.text))
        return result

    def generate_timeline_summary(self, person_id: int, max_tokens: int | None = None) -> LLMResult:
        """Create a timeline-oriented summary for timeline export preparation."""

        context = self._build_timeline_context(person_id)
        prompt = render_prompt("timeline", context)
        return self._invoke_llm(prompt, max_tokens=max_tokens)

    def memory(self) -> Sequence[ConversationTurn]:
        """Return a read-only view of conversation history."""

        return tuple(self._memory)

    # ---- Context Builders -----------------------------------------------

    def _build_biography_context(self, person_id: int, style: str) -> dict[str, str]:
        def _builder(db: RMDatabase | None) -> dict[str, str]:
            query = self._make_query_service(db)
            person = GenealogyFormatters.row_to_dict(query.get_person_with_primary_name(person_id))
            if person is None:
                raise ValueError(f"Person {person_id} not found")
            events = GenealogyFormatters.rows_to_dicts(query.get_person_events(person_id))
            ancestors = GenealogyFormatters.rows_to_dicts(query.get_direct_ancestors(person_id, generations=3))
            spouses = GenealogyFormatters.rows_to_dicts(query.get_spouses(person_id))
            children = GenealogyFormatters.rows_to_dicts(query.get_children(person_id))
            parents = GenealogyFormatters.row_to_dict(query.get_parents(person_id))
            siblings = GenealogyFormatters.rows_to_dicts(self._fetch_siblings(query, parents, person_id))
            life_span = GenealogyFormatters.derive_life_span(person, events)

            person_summary = GenealogyFormatters.format_person_summary(person, style)

            # Build event-to-citations mapping for inline citation markers
            event_citations_map = self._build_event_citations_map(query, events)

            # Format timeline with inline citation IDs
            timeline_overview = GenealogyFormatters.format_events(events, event_citations_map)

            relationship_notes = GenealogyFormatters.format_ancestors(ancestors)
            family_overview = GenealogyFormatters.format_family_overview(spouses, children, siblings)
            early_life_overview = GenealogyFormatters.format_early_life(person, parents, siblings, life_span)
            family_loss_notes = GenealogyFormatters.format_family_losses(
                life_span, parents, spouses, siblings, children
            )
            sibling_lines = GenealogyFormatters.format_siblings(siblings)
            sibling_summary = "\n".join(sibling_lines) if sibling_lines else "No sibling records available."

            # Extract person-level notes
            person_notes = person.get("Note") or ""
            person_notes_formatted = person_notes if person_notes else "No person-level notes available."

            # Generate style-specific length guidance
            length_guidance = self._get_length_guidance_for_style(style)

            return {
                "person_summary": person_summary,
                "person_notes": person_notes_formatted,
                "timeline_overview": timeline_overview,
                "relationship_notes": relationship_notes,
                "family_overview": family_overview,
                "early_life_overview": early_life_overview,
                "family_loss_notes": family_loss_notes,
                "sibling_summary": sibling_summary,
                "source_notes": "Sources are cited inline with timeline events using {{cite:ID}} markers.",
                "length_guidance": length_guidance,
            }

        return self._with_database(_builder)

    def _build_qa_context(self, question: str, person_id: int | None) -> dict[str, str]:
        def _builder(db: RMDatabase | None) -> dict[str, str]:
            snippets: list[str] = []
            query = self._make_query_service(db)

            if person_id is not None:
                person = GenealogyFormatters.row_to_dict(query.get_person_with_primary_name(person_id))
                if person:
                    snippets.append(GenealogyFormatters.format_person_summary(person, style="short"))
                    events = GenealogyFormatters.rows_to_dicts(query.get_person_events(person_id))
                    snippets.append(GenealogyFormatters.format_events(events))
                    spouses = GenealogyFormatters.rows_to_dicts(query.get_spouses(person_id))
                    children = GenealogyFormatters.rows_to_dicts(query.get_children(person_id))
                    parents = GenealogyFormatters.row_to_dict(query.get_parents(person_id))
                    siblings = GenealogyFormatters.rows_to_dicts(self._fetch_siblings(query, parents, person_id))
                    life_span = GenealogyFormatters.derive_life_span(person, events)
                    snippets.append(GenealogyFormatters.format_family_overview(spouses, children, siblings))
                    snippets.append(GenealogyFormatters.format_early_life(person, parents, siblings, life_span))

            history_snippets = [f"Q: {turn.question}\nA: {turn.answer}" for turn in self._memory[-3:]]
            snippets.extend(history_snippets)

            return {
                "question": question,
                "context_snippets": "\n".join(snippets) or "No prior context.",
            }

        return self._with_database(_builder)

    def _build_timeline_context(self, person_id: int) -> dict[str, str]:
        def _builder(db: RMDatabase | None) -> dict[str, str]:
            query = self._make_query_service(db)
            person = GenealogyFormatters.row_to_dict(query.get_person_with_primary_name(person_id))
            events = GenealogyFormatters.rows_to_dicts(query.get_person_events(person_id))

            person_name = GenealogyFormatters.format_person_name(person) if person else f"Person {person_id}"
            events_json = GenealogyFormatters.format_events_json(events)
            return {"person_name": person_name, "events_json": events_json}

        return self._with_database(_builder)

    # ---- Helper Methods -------------------------------------------------

    def _get_length_guidance_for_style(self, style: str) -> str:
        """Return length-specific guidance based on requested style."""
        style_lower = style.lower()

        if style_lower == "short":
            return """**SHORT (250-500 words):**
- REQUIRED: Begin with ## Introduction section (birth, parents, death if applicable)
- Focus on essential life events only: birth, death, marriage, key career milestones
- 2-3 concise paragraphs minimum
- Minimal family details - just mention parents' names and spouse
- Omit detailed historical context and analysis
- Use brief, factual sentences"""

        elif style_lower == "standard":
            return """**STANDARD (500-1500 words):**
- REQUIRED: Begin with ## Introduction section (birth, parents, death if applicable)
- Balanced narrative covering all major life sections
- 5-8 paragraphs with moderate detail
- Include: birth, early life, education, career, marriage, children (names only), later life, death
- Moderate family context: mention parents, spouse(s), number of children
- Include some historical context where relevant
- Use complete sections with section headers"""

        elif style_lower == "comprehensive":
            return """**COMPREHENSIVE (1500+ words):**
- REQUIRED: Begin with ## Introduction section (birth, parents, death if applicable)
- Detailed multi-section biography with rich historical and family context
- 10+ paragraphs covering all aspects of life with extensive detail
- CRITICAL: Expand significantly on family relationships:
  * Parents: Include their backgrounds, occupations, when/where they died, their ages at subject's birth
  * Siblings: Name each sibling, their birth/death dates, occupations, marriages, birth order analysis
  * Spouse(s): Detailed background of each spouse, their family, courtship context, marriage details
  * Children: Name each child with birth/death dates, marriages, occupations, accomplishments
- Include detailed historical context (migration patterns, economic conditions, social dynamics)
- Analyze family patterns (geographic mobility, occupational trends, mortality patterns)
- Use event notes extensively - they contain rich primary source material
- Flag uncertainties explicitly and suggest research directions
- All sections should be well-developed with multiple paragraphs where data supports it"""

        else:
            # Default to standard if unrecognized
            return self._get_length_guidance_for_style("standard")

    def _invoke_llm(self, prompt: str, max_tokens: int | None = None) -> LLMResult:
        kwargs = {}
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        return self.llm_provider.generate(prompt, **kwargs)

    def _with_database(
        self, fn: Callable[[RMDatabase | None], dict[str, str] | QualityReport]
    ) -> dict[str, str] | QualityReport:
        if self.db_path is None:
            return fn(None)
        with RMDatabase(self.db_path, extension_path=self.extension_path) as db:
            return fn(db)

    def _make_query_service(self, db: RMDatabase | None) -> QueryService:
        if db is None:
            return self.query_service_factory(None)  # type: ignore[arg-type]
        return self.query_service_factory(db)

    def _fetch_siblings(self, query: QueryService, parents: dict[str, str] | None, person_id: int):
        """Fetch siblings using QueryService."""
        if not parents:
            return []
        siblings = []
        seen = {person_id}
        for key in ("FatherID", "MotherID"):
            parent_id = parents.get(key)
            if parent_id:
                rows = query.get_children(parent_id)
                for row in rows or []:
                    row_dict = GenealogyFormatters.row_to_dict(row)
                    pid = row_dict.get("PersonID") if row_dict else None
                    if pid is None or pid in seen or pid == person_id:
                        continue
                    seen.add(pid)
                    siblings.append(row_dict)
        siblings.sort(
            key=lambda row: GenealogyFormatters.sort_key(
                GenealogyFormatters.extract_sort_value(row.get("BirthSortDate")), row.get("BirthYear")
            )
        )
        return siblings

    def _build_event_citations_map(self, query: QueryService, events: list[dict]) -> dict[int, list[int]]:
        """
        Build mapping of EventID -> list of CitationIDs for inline citation markers.

        Args:
            query: QueryService instance
            events: List of event dicts with EventID

        Returns:
            Dict mapping EventID to list of CitationIDs (e.g., {123: [456, 789]})
        """
        event_citations_map: dict[int, list[int]] = {}

        for event in events or []:
            event_id = event.get("EventID")
            if not event_id:
                continue

            # Get citations for this event
            citations = GenealogyFormatters.rows_to_dicts(query.get_event_citations(event_id))

            # Extract citation IDs
            citation_ids = []
            for citation in citations or []:
                citation_id = citation.get("CitationID")
                if citation_id:
                    citation_ids.append(citation_id)

            # Store mapping
            if citation_ids:
                event_citations_map[event_id] = citation_ids

        return event_citations_map

    def _collect_all_citations_for_person(self, query: QueryService, person_id: int) -> list[dict]:
        """
        Collect all citations for a person's events using QueryService.
        Returns list of citation dicts with CitationID, SourceID, SourceName, CitationName, EventType.

        NOTE: This method is kept for backward compatibility but may be deprecated
        in favor of _build_event_citations_map for inline citation markers.
        """
        # Get all events for the person
        events = GenealogyFormatters.rows_to_dicts(query.get_person_events(person_id))

        # Collect citations from all events
        all_citations = []
        seen_citation_ids = set()

        for event in events or []:
            event_id = event.get("EventID")
            event_type = event.get("EventType", "Unknown Event")

            if not event_id:
                continue

            # Get citations for this event
            citations = GenealogyFormatters.rows_to_dicts(query.get_event_citations(event_id))

            for citation in citations or []:
                citation_id = citation.get("CitationID")

                # Skip if we've already seen this citation
                if citation_id in seen_citation_ids:
                    continue

                seen_citation_ids.add(citation_id)

                # Add event type to citation info
                citation["EventType"] = event_type
                all_citations.append(citation)

        return all_citations
