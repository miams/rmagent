"""
Main biography generator class.

Handles data extraction, context building, and biography generation.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

from rmagent.agent.genealogy_agent import GenealogyAgent
from rmagent.rmlib.database import RMDatabase
from rmagent.rmlib.models import OwnerType
from rmagent.rmlib.parsers.date_parser import is_unknown_date, parse_rm_date
from rmagent.rmlib.parsers.name_parser import format_full_name
from rmagent.rmlib.parsers.place_parser import format_place_medium, format_place_short
from rmagent.rmlib.queries import QueryService

from .citations import CitationProcessor
from .models import (
    Biography,
    BiographyLength,
    CitationStyle,
    EventContext,
    LLMMetadata,
    PersonContext,
    get_row_value,
)
from .templates import BiographyTemplates


class BiographyGenerator:
    """
    Generate biographical narratives from RootsMagic data.

    Follows the 9-section structure from RM11_Biography_Best_Practices.md:
    1. Introduction (Birth & Identity)
    2. Early Life & Family Background
    3. Education
    4. Career & Occupation
    5. Marriage & Family Life
    6. Later Life & Activities
    7. Death & Legacy
    8. Sources & Notes

    Args:
        db: RMDatabase instance or path to database
        agent: Optional GenealogyAgent for AI-powered narrative generation
        extension_path: Path to ICU extension (default: ./sqlite-extension/icu.dylib)
        current_year: Current year for 110-year rule calculation (default: current year)

    Example:
        ```python
        from rmagent.generators.biography import BiographyGenerator, BiographyLength, CitationStyle
        from rmagent.agent.genealogy_agent import GenealogyAgent

        agent = GenealogyAgent(llm_provider=provider, db_path="data/Iiams.rmtree")
        generator = BiographyGenerator(db_path="data/Iiams.rmtree", agent=agent)

        bio = generator.generate(
            person_id=1,
            length=BiographyLength.STANDARD,
            citation_style=CitationStyle.FOOTNOTE,
            include_sources=True
        )

        print(bio.render_markdown())
        ```
    """

    def __init__(
        self,
        db: RMDatabase | Path | str | None = None,
        agent: GenealogyAgent | None = None,
        extension_path: Path | str = Path("./sqlite-extension/icu.dylib"),
        current_year: int | None = None,
        media_root_directory: Path | str | None = None,
    ):
        # Handle db parameter
        if isinstance(db, (Path, str)):
            self.db_path = Path(db)
            self._db = None
            self._owns_db = True
        elif isinstance(db, RMDatabase):
            self.db_path = None
            self._db = db
            self._owns_db = False
        else:
            self.db_path = None
            self._db = None
            self._owns_db = False

        self.agent = agent
        self.extension_path = Path(extension_path)
        self.current_year = current_year or datetime.now().year
        self.media_root_directory = Path(media_root_directory) if media_root_directory else None

        # Initialize helper classes
        self.citation_processor = CitationProcessor()
        self.templates = BiographyTemplates()

    def generate(
        self,
        person_id: int,
        length: BiographyLength = BiographyLength.STANDARD,
        citation_style: CitationStyle = CitationStyle.FOOTNOTE,
        include_sources: bool = True,
        include_media: bool = True,
        use_ai: bool = True,
    ) -> Biography:
        """
        Generate a biography for the specified person.

        Args:
            person_id: PersonID from PersonTable
            length: Biography length (short/standard/comprehensive)
            citation_style: Citation formatting style
            include_sources: Include sources section
            include_media: Include media references
            use_ai: Use AI agent for narrative generation (requires agent parameter)

        Returns:
            Biography instance with all sections populated

        Raises:
            ValueError: If person not found or if use_ai=True but no agent provided
        """
        # Check for agent requirement early
        if use_ai and not self.agent:
            raise ValueError("AI generation requested but no agent provided")

        # Extract person context
        context = self._extract_person_context(person_id, include_media)

        # Apply privacy rules
        self._apply_privacy_rules(context)

        # Generate biography sections
        if use_ai and self.agent:
            biography = self._generate_with_ai(context, length, citation_style, include_sources)
        else:
            biography = self._generate_template_based(context, length, citation_style, include_sources)

        return biography

    # ---- Private Methods: Data Extraction ----

    def _extract_person_context(self, person_id: int, include_media: bool = True) -> PersonContext:
        """Extract complete person context from database."""

        def _extract(db: RMDatabase) -> PersonContext:
            query = QueryService(db)

            # Get person with primary name
            person = query.get_person_with_primary_name(person_id)
            if not person:
                raise ValueError(f"Person {person_id} not found")

            # Extract name components
            full_name = format_full_name(
                given=get_row_value(person, "Given"),
                surname=get_row_value(person, "Surname"),
                prefix=get_row_value(person, "Prefix"),
                suffix=get_row_value(person, "Suffix"),
            )

            # Calculate is_living based on 110-year rule
            birth_year = get_row_value(person, "BirthYear")
            is_living = False
            if birth_year:
                age = self.current_year - birth_year
                is_living = age < 110

            # Extract birth/death information
            birth_date_str, birth_place = self._extract_vital_info(db, person_id, fact_type_id=1)  # Birth
            death_date_str, death_place = self._extract_vital_info(db, person_id, fact_type_id=2)  # Death

            # Get relationships
            parents = query.get_parents(person_id)
            father_name = None
            mother_name = None
            father_id = None
            mother_id = None

            if parents:
                father_id = get_row_value(parents, "FatherID")
                mother_id = get_row_value(parents, "MotherID")
                if father_id:
                    father_name = format_full_name(
                        given=get_row_value(parents, "FatherGiven"),
                        surname=get_row_value(parents, "FatherSurname"),
                    )
                if mother_id:
                    mother_name = format_full_name(
                        given=get_row_value(parents, "MotherGiven"),
                        surname=get_row_value(parents, "MotherSurname"),
                    )

            spouses = query.get_spouses(person_id) or []
            children = query.get_children(person_id) or []
            siblings = []  # TODO: Implement get_siblings() in QueryService

            # Get all events and categorize
            all_events = query.get_person_events(person_id)
            (
                vital_events,
                education_events,
                occupation_events,
                military_events,
                residence_events,
                other_events,
            ) = self._categorize_events(db, all_events)

            # Get media if requested
            media_files = []
            if include_media:
                media_files = self._get_media_for_person(db, person_id)

            # Get all citations
            all_citations = self._get_all_citations_for_person(db, person_id)

            # Extract person-level notes
            person_notes = get_row_value(person, "Note")

            return PersonContext(
                person_id=person_id,
                full_name=full_name,
                given_name=get_row_value(person, "Given", ""),
                surname=get_row_value(person, "Surname", ""),
                prefix=get_row_value(person, "Prefix"),
                suffix=get_row_value(person, "Suffix"),
                nickname=get_row_value(person, "Nickname"),
                birth_year=birth_year,
                birth_date=birth_date_str,
                birth_place=birth_place,
                death_year=get_row_value(person, "DeathYear"),
                death_date=death_date_str,
                death_place=death_place,
                sex=get_row_value(person, "Sex", 2),
                is_private=bool(get_row_value(person, "IsPrivate", 0)),
                is_living=is_living,
                person_notes=person_notes,
                father_id=father_id,
                father_name=father_name,
                mother_id=mother_id,
                mother_name=mother_name,
                spouses=spouses,
                children=children,
                siblings=siblings,
                vital_events=vital_events,
                education_events=education_events,
                occupation_events=occupation_events,
                military_events=military_events,
                residence_events=residence_events,
                other_events=other_events,
                media_files=media_files,
                all_citations=all_citations,
            )

        if self._db:
            return _extract(self._db)
        elif self.db_path:
            with RMDatabase(self.db_path, extension_path=self.extension_path) as db:
                return _extract(db)
        else:
            raise ValueError("No database provided")

    def _extract_vital_info(self, db: RMDatabase, person_id: int, fact_type_id: int) -> tuple[str | None, str | None]:
        """Extract date and place for a vital event (birth/death)."""
        query = QueryService(db)
        vital_events = query.get_vital_events(person_id)

        for event in vital_events:
            if get_row_value(event, "FactTypeID") == fact_type_id:
                # Parse date
                date_str = get_row_value(event, "Date")
                formatted_date = None
                if date_str and not is_unknown_date(date_str):
                    try:
                        parsed_date = parse_rm_date(date_str)
                        formatted_date = parsed_date.format_display()
                    except Exception:
                        formatted_date = None

                # Format place
                place_str = get_row_value(event, "Place")
                formatted_place = None
                if place_str:
                    try:
                        formatted_place = format_place_medium(place_str)
                    except Exception:
                        formatted_place = place_str

                return formatted_date, formatted_place

        return None, None

    def _categorize_events(self, db: RMDatabase, events: list[dict]) -> tuple[list[EventContext], ...]:
        """Categorize events into vital, education, occupation, military, residence, and other."""
        vital = []
        education = []
        occupation = []
        military = []
        residence = []
        other = []

        for event in events:
            event_ctx = self._build_event_context(db, event)
            event_type = get_row_value(event, "EventType", 0)

            # Categorize based on FactTypeID
            # Vital: Birth (1), Death (2), Burial (3), Baptism (4), Christening (5)
            if event_type in (1, 2, 3, 4, 5, 6):
                vital.append(event_ctx)
            # Education: Education (17), Graduation (18)
            elif event_type in (17, 18):
                education.append(event_ctx)
            # Occupation: Occupation (12), Retirement (27)
            elif event_type in (12, 27):
                occupation.append(event_ctx)
            # Military: Military Service (10), Drafted (63), Military Discharge (64)
            elif event_type in (10, 63, 64):
                military.append(event_ctx)
            # Residence: Residence (13), Immigration (20), Emigration (19)
            elif event_type in (13, 19, 20):
                residence.append(event_ctx)
            else:
                other.append(event_ctx)

        return vital, education, occupation, military, residence, other

    def _build_event_context(self, db: RMDatabase, event: dict) -> EventContext:
        """Build EventContext from event row."""
        # Parse date
        date_str = get_row_value(event, "Date", "")
        formatted_date = ""
        if date_str and not is_unknown_date(date_str):
            try:
                parsed = parse_rm_date(date_str)
                formatted_date = parsed.format_display()
            except Exception:
                formatted_date = date_str

        # Format place
        place_str = get_row_value(event, "Place", "")
        formatted_place = ""
        if place_str:
            try:
                formatted_place = format_place_short(place_str)
            except Exception:
                formatted_place = place_str

        # Get citations for this event
        citations = self._get_citations_for_event(db, get_row_value(event, "EventID", 0))

        return EventContext(
            event_id=get_row_value(event, "EventID", 0),
            event_type=get_row_value(event, "EventType", ""),
            date=formatted_date,
            place=formatted_place,
            details=get_row_value(event, "Details", ""),
            note=get_row_value(event, "Note", ""),
            is_private=bool(get_row_value(event, "IsPrivate", 0)),
            proof=get_row_value(event, "Proof", 0),
            citations=citations,
            sort_date=get_row_value(event, "SortDate", 0),
        )

    def _get_citations_for_event(self, db: RMDatabase, event_id: int) -> list[dict]:
        """Get all citations for an event with formatted text (Footnote, ShortFootnote, Bibliography)."""
        query = QueryService(db)
        return query.get_event_citations(event_id)

    def _get_media_for_person(self, db: RMDatabase, person_id: int) -> list[dict]:
        """Get all media files linked to person, including path and primary flag."""
        cursor = db.execute(
            """
            SELECT m.MediaID, m.MediaPath, m.MediaFile, m.Caption, m.Date, m.Description,
                   ml.IsPrimary, ml.SortOrder
            FROM MediaLinkTable ml
            JOIN MultimediaTable m ON ml.MediaID = m.MediaID
            WHERE ml.OwnerType = ? AND ml.OwnerID = ?
            ORDER BY ml.IsPrimary DESC, ml.SortOrder, ml.LinkID
            """,
            (OwnerType.PERSON.value, person_id),
        )
        return cursor.fetchall()

    def _get_all_citations_for_person(self, db: RMDatabase, person_id: int) -> list[dict]:
        """Get all citations associated with person (via events, names, etc.) with full citation data."""
        query = QueryService(db)

        # Get all events for person
        events = query.get_person_events(person_id)

        # Collect citations from all events (deduplicated by CitationID)
        all_citations = []
        seen_citation_ids = set()

        for event in events:
            event_id = get_row_value(event, "EventID")
            if not event_id:
                continue

            # Get full citation data including BLOBs
            citations = query.get_event_citations(event_id)
            for citation in citations:
                citation_id = get_row_value(citation, "CitationID")
                if citation_id in seen_citation_ids:
                    continue
                seen_citation_ids.add(citation_id)
                all_citations.append(citation)

        return all_citations

    # ---- Private Methods: Privacy Rules ----

    def _apply_privacy_rules(self, context: PersonContext) -> None:
        """Apply privacy rules to person context (modifies in place)."""
        # If person is marked private or likely living, filter events
        if context.is_private or context.is_living:
            context.privacy_applied = True  # type: ignore[misc]

            # Remove all private events
            context.vital_events = [e for e in context.vital_events if not e.is_private]
            context.education_events = [e for e in context.education_events if not e.is_private]
            context.occupation_events = [e for e in context.occupation_events if not e.is_private]
            context.military_events = [e for e in context.military_events if not e.is_private]
            context.residence_events = [e for e in context.residence_events if not e.is_private]
            context.other_events = [e for e in context.other_events if not e.is_private]

            # If likely living, also remove sensitive event types
            if context.is_living:
                # Remove occupation, residence, and education events for living persons
                context.occupation_events = []
                context.residence_events = []
                context.education_events = []

    # ---- Private Methods: Biography Generation ----

    def _generate_with_ai(
        self,
        context: PersonContext,
        length: BiographyLength,
        citation_style: CitationStyle,
        include_sources: bool,
    ) -> Biography:
        """Generate biography using AI agent."""
        if not self.agent:
            raise ValueError("AI generation requested but no agent provided")

        # Time the prompt building and LLM generation
        prompt_start = time.time()

        # Use agent's generate_biography method (includes internal timing)
        result = self.agent.generate_biography(person_id=context.person_id, style=length.value)

        total_time = time.time() - prompt_start

        # Extract LLM metadata from result
        llm_metadata = None
        if hasattr(self.agent, "llm_provider"):
            provider_name = self.agent.llm_provider.__class__.__name__.replace("Provider", "").lower()
            llm_metadata = LLMMetadata(
                provider=provider_name,
                model=result.model,
                prompt_tokens=result.usage.prompt_tokens,
                completion_tokens=result.usage.completion_tokens,
                total_tokens=result.usage.total_tokens,
                prompt_time=total_time * 0.1,  # Estimate ~10% for prompt building
                llm_time=total_time * 0.9,  # Estimate ~90% for LLM
                cost=result.cost,
            )

        # Process citations for FOOTNOTE style BEFORE parsing into sections
        footnotes_text = ""
        sources_text = ""
        response_text = result.text
        citation_count = 0
        source_count = 0

        if citation_style == CitationStyle.FOOTNOTE:
            # Process {cite:ID} markers in full response (preserves section headers)
            modified_text, footnotes, tracker = self.citation_processor.process_citations_in_text(
                response_text, context.all_citations
            )

            # Use modified text for section parsing
            response_text = modified_text

            # Generate footnotes section
            if footnotes:
                footnotes_text = self.citation_processor.generate_footnotes_section(footnotes, tracker)
                citation_count = len(footnotes)

            # Generate sources section using new bibliography method
            if include_sources:
                sources_text = self.citation_processor.generate_sources_section(context.all_citations)
                # Count unique sources
                source_ids = set()
                for citation in context.all_citations:
                    source_id = get_row_value(citation, "SourceID", 0)
                    if source_id:
                        source_ids.add(source_id)
                source_count = len(source_ids)
        else:
            # For other citation styles, use existing format
            if include_sources:
                sources_text = self.citation_processor.format_sources_section(context, citation_style)
                citation_count = len(context.all_citations)
                # Count unique sources
                source_ids = set()
                for citation in context.all_citations:
                    source_id = get_row_value(citation, "SourceID", 0)
                    if source_id:
                        source_ids.add(source_id)
                source_count = len(source_ids)

        # Parse AI response into sections (after citation processing)
        sections = self.templates.parse_ai_response(response_text)

        return Biography(
            person_id=context.person_id,
            full_name=context.full_name,
            length=length,
            citation_style=citation_style,
            introduction=sections.get("introduction", ""),
            early_life=sections.get("early_life", ""),
            education=sections.get("education", ""),
            career=sections.get("career", ""),
            marriage_family=sections.get("marriage_family", ""),
            later_life=sections.get("later_life", ""),
            death_legacy=sections.get("death_legacy", ""),
            footnotes=footnotes_text,
            sources=sources_text,
            privacy_applied=getattr(context, "privacy_applied", False),
            birth_year=context.birth_year,
            death_year=context.death_year,
            llm_metadata=llm_metadata,
            citation_count=citation_count,
            source_count=source_count,
            media_files=context.media_files,
            media_root_directory=self.media_root_directory,
        )

    def _generate_template_based(
        self,
        context: PersonContext,
        length: BiographyLength,
        citation_style: CitationStyle,
        include_sources: bool,
    ) -> Biography:
        """Generate biography using template-based approach (no AI)."""
        # Generate each section using templates
        intro = self.templates.generate_introduction(context)
        early_life = self.templates.generate_early_life(context)
        education = self.templates.generate_education(context)
        career = self.templates.generate_career(context)
        marriage = self.templates.generate_marriage_family(context)
        later_life = self.templates.generate_later_life(context)
        death = self.templates.generate_death_legacy(context)

        sources_text = ""
        citation_count = 0
        source_count = 0
        if include_sources:
            sources_text = self.citation_processor.format_sources_section(context, citation_style)
            citation_count = len(context.all_citations)
            # Count unique sources
            source_ids = set()
            for citation in context.all_citations:
                source_id = get_row_value(citation, "SourceID", 0)
                if source_id:
                    source_ids.add(source_id)
            source_count = len(source_ids)

        return Biography(
            person_id=context.person_id,
            full_name=context.full_name,
            length=length,
            citation_style=citation_style,
            introduction=intro,
            early_life=early_life,
            education=education,
            career=career,
            marriage_family=marriage,
            later_life=later_life,
            death_legacy=death,
            footnotes="",  # Template-based biographies don't use citations
            sources=sources_text,
            privacy_applied=getattr(context, "privacy_applied", False),
            birth_year=context.birth_year,
            death_year=context.death_year,
            llm_metadata=None,  # No LLM used for template-based
            citation_count=citation_count,
            source_count=source_count,
            media_files=context.media_files,
            media_root_directory=self.media_root_directory,
        )
