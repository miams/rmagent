"""
Biography generator for RMAgent.

Generates formatted biographical narratives following the 9-section structure
from RM11_Biography_Best_Practices.md. Handles privacy rules, citation formatting,
and length variations (short/standard/comprehensive).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

from rmagent.agent.genealogy_agent import GenealogyAgent
from rmagent.rmlib.database import RMDatabase
from rmagent.rmlib.models import OwnerType
from rmagent.rmlib.parsers.date_parser import is_unknown_date, parse_rm_date
from rmagent.rmlib.parsers.name_parser import format_full_name
from rmagent.rmlib.parsers.place_parser import format_place_medium, format_place_short
from rmagent.rmlib.queries import QueryService


class BiographyLength(str, Enum):
    """Biography length variations."""

    SHORT = "short"  # 250-500 words (2-3 paragraphs)
    STANDARD = "standard"  # 500-1500 words (5-8 paragraphs)
    COMPREHENSIVE = "comprehensive"  # 1500+ words (10+ paragraphs, multiple sections)


class CitationStyle(str, Enum):
    """Citation formatting styles."""

    FOOTNOTE = "footnote"  # Academic style with numbered footnotes
    PARENTHETICAL = "parenthetical"  # Genealogical style with inline source references
    NARRATIVE = "narrative"  # Popular style with narrative attribution


@dataclass
class LLMMetadata:
    """Metadata from LLM generation for biography."""

    provider: str  # anthropic, openai, ollama
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_time: float  # seconds (context building)
    llm_time: float  # seconds (LLM generation)
    cost: float | None = None


@dataclass
class EventContext:
    """Contextual information for a single event."""

    event_id: int
    event_type: str
    date: str  # Formatted display date
    place: str
    details: str
    note: str  # Event note (EventTable.Note) - often contains full transcriptions
    is_private: bool
    proof: int
    citations: list[dict]  # CitationID, SourceID, Page, etc.
    sort_date: int


@dataclass
class PersonContext:
    """Complete person context for biography generation."""

    person_id: int
    full_name: str
    given_name: str
    surname: str
    prefix: str | None
    suffix: str | None
    nickname: str | None

    birth_year: int | None
    birth_date: str | None
    birth_place: str | None

    death_year: int | None
    death_date: str | None
    death_place: str | None

    sex: int  # 0=Male, 1=Female, 2=Unknown
    is_private: bool
    is_living: bool  # Calculated based on 110-year rule

    # Person-level notes (PersonTable.Note)
    person_notes: str | None = None

    # Relationships
    father_id: int | None = None
    father_name: str | None = None
    mother_id: int | None = None
    mother_name: str | None = None
    spouses: list[dict] = field(default_factory=list)
    children: list[dict] = field(default_factory=list)
    siblings: list[dict] = field(default_factory=list)

    # Events categorized by type
    vital_events: list[EventContext] = field(default_factory=list)
    education_events: list[EventContext] = field(default_factory=list)
    occupation_events: list[EventContext] = field(default_factory=list)
    military_events: list[EventContext] = field(default_factory=list)
    residence_events: list[EventContext] = field(default_factory=list)
    other_events: list[EventContext] = field(default_factory=list)

    # Media
    media_files: list[dict] = field(default_factory=list)

    # Sources
    all_citations: list[dict] = field(default_factory=list)


@dataclass
class Biography:
    """Generated biography with structured sections."""

    person_id: int
    full_name: str
    length: BiographyLength
    citation_style: CitationStyle

    # Generated content
    introduction: str
    early_life: str
    education: str
    career: str
    marriage_family: str
    later_life: str
    death_legacy: str
    footnotes: str  # Footnotes section (only for FOOTNOTE citation style)
    sources: str

    # Metadata
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC).astimezone())
    word_count: int = 0
    privacy_applied: bool = False
    birth_year: int | None = None
    death_year: int | None = None
    llm_metadata: LLMMetadata | None = None
    citation_count: int = 0
    source_count: int = 0
    media_files: list[dict] = field(default_factory=list)  # Media files for images

    def _calculate_word_count(self) -> int:
        """Calculate word count from all biography sections."""
        all_text = "\n".join([
            self.introduction,
            self.early_life,
            self.education,
            self.career,
            self.marriage_family,
            self.later_life,
            self.death_legacy,
            self.footnotes,
            self.sources,
        ])
        return len(all_text.split())

    @staticmethod
    def _format_tokens(count: int) -> str:
        """Format token count with k suffix."""
        if count >= 1000:
            return f"{count/1000:.1f}k"
        return str(count)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration as Xm Ys or Xs."""
        if seconds >= 60:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m{secs}s" if secs > 0 else f"{minutes}m"
        return f"{int(seconds)}s"

    def render_metadata(self) -> str:
        """Render Hugo-style front matter metadata."""
        lines = ["---"]

        # Title with years
        years_str = ""
        if self.birth_year or self.death_year:
            birth = self.birth_year or "????"
            death = self.death_year or "????"
            years_str = f" ({birth}-{death})"
        lines.append(f'Title: "Biography of {self.full_name}{years_str}"')

        # Timestamp in ISO 8601 format with timezone (format as -05:00)
        tz_str = self.generated_at.strftime("%z")
        tz_formatted = f"{tz_str[:3]}:{tz_str[3:]}" if tz_str else ""
        date_str = self.generated_at.strftime("%Y-%m-%dT%H:%M:%S") + tz_formatted
        lines.append(f'Date: {date_str}')

        # Person ID
        lines.append(f'PersonID: {self.person_id}')

        # LLM Metadata (if available)
        if self.llm_metadata:
            lines.append(f'TokensIn: {self._format_tokens(self.llm_metadata.prompt_tokens)}')
            lines.append(f'TokensOut: {self._format_tokens(self.llm_metadata.completion_tokens)}')
            lines.append(f'TotalTokens: {self._format_tokens(self.llm_metadata.total_tokens)}')
            lines.append(f'LLM: {self.llm_metadata.provider.capitalize()}')
            lines.append(f'Model: {self.llm_metadata.model}')
            lines.append(f'PromptTime: {self._format_duration(self.llm_metadata.prompt_time)}')
            lines.append(f'LLMTime: {self._format_duration(self.llm_metadata.llm_time)}')

        # Biography stats (calculate word count dynamically)
        word_count = self._calculate_word_count()
        lines.append(f'Words: {word_count:,}')
        lines.append(f'Citations: {self.citation_count}')
        lines.append(f'Sources: {self.source_count}')

        lines.append("---\n")
        return "\n".join(lines)

    def render_markdown(self, include_metadata: bool = True) -> str:
        """Render complete biography as Markdown with optional front matter."""
        sections = []

        # Hugo-style front matter metadata
        if include_metadata:
            sections.append(self.render_metadata())

        # Title with lifespan years
        years_str = ""
        if self.birth_year or self.death_year:
            birth = self.birth_year or "????"
            death = self.death_year or "????"
            years_str = f" ({birth}-{death})"
        sections.append(f"# Biography of {self.full_name}{years_str}\n")

        # Separate primary and additional images (only for STANDARD and COMPREHENSIVE)
        primary_image = None
        additional_images = []
        if self.length != BiographyLength.SHORT and self.media_files:
            for media in self.media_files:
                is_primary = media.get("IsPrimary", 0) == 1 if hasattr(media, 'get') else media["IsPrimary"] == 1
                if is_primary and primary_image is None:
                    primary_image = media
                elif not is_primary:
                    additional_images.append(media)

        # Introduction
        if self.introduction:
            sections.append("## Introduction\n")

            # Add primary portrait image with text wrapping (if available)
            if primary_image:
                from pathlib import Path
                # Format the media path
                media_path = primary_image.get("MediaPath", "") if hasattr(primary_image, 'get') else primary_image["MediaPath"]
                media_file = primary_image.get("MediaFile", "") if hasattr(primary_image, 'get') else primary_image["MediaFile"]

                # Strip RootsMagic's ?\ or ?/ prefix if present
                if media_path.startswith("?\\"):
                    media_path = media_path[2:]
                elif media_path.startswith("?/"):
                    media_path = media_path[2:]

                # Combine path components
                if media_path:
                    full_path = Path(media_path) / media_file
                else:
                    full_path = Path(media_file)

                # Convert to POSIX-style path for Markdown
                image_path = full_path.as_posix()

                # Caption: "Full Name (birth_year-death_year)"
                caption = f"{self.full_name}"
                if self.birth_year or self.death_year:
                    birth = self.birth_year or "????"
                    death = self.death_year or "????"
                    caption += f" ({birth}-{death})"

                # Use HTML for text wrapping - align right with width constraint
                sections.append(f'<img src="{image_path}" alt="{caption}" align="right" width="300" />\n')

            sections.append(self.introduction)
            sections.append("")

        # Early Life & Family Background
        if self.early_life:
            sections.append("## Early Life & Family Background\n")
            sections.append(self.early_life)
            sections.append("")

        # Education
        if self.education:
            sections.append("## Education\n")
            sections.append(self.education)
            sections.append("")

        # Career & Accomplishments
        if self.career:
            sections.append("## Career & Accomplishments\n")
            sections.append(self.career)
            sections.append("")

        # Marriage & Family
        if self.marriage_family:
            sections.append("## Marriage & Family\n")
            sections.append(self.marriage_family)
            sections.append("")

        # Later Life & Activities
        if self.later_life:
            sections.append("## Later Life & Activities\n")
            sections.append(self.later_life)
            sections.append("")

        # Death & Legacy
        if self.death_legacy:
            sections.append("## Death & Legacy\n")
            sections.append(self.death_legacy)
            sections.append("")

        # Photos (additional non-primary images)
        if additional_images:
            sections.append("## Photos\n")
            for media in additional_images:
                from pathlib import Path
                # Format the media path
                media_path = media.get("MediaPath", "") if hasattr(media, 'get') else media["MediaPath"]
                media_file = media.get("MediaFile", "") if hasattr(media, 'get') else media["MediaFile"]

                # Strip RootsMagic's ?\ or ?/ prefix if present
                if media_path.startswith("?\\"):
                    media_path = media_path[2:]
                elif media_path.startswith("?/"):
                    media_path = media_path[2:]

                # Combine path components
                if media_path:
                    full_path = Path(media_path) / media_file
                else:
                    full_path = Path(media_file)

                # Convert to POSIX-style path for Markdown
                image_path = full_path.as_posix()

                # Caption: "Full Name (birth_year-death_year)"
                caption = f"{self.full_name}"
                if self.birth_year or self.death_year:
                    birth = self.birth_year or "????"
                    death = self.death_year or "????"
                    caption += f" ({birth}-{death})"

                # Standard markdown image format (no text wrapping for additional images)
                sections.append(f"![{caption}]({image_path})\n")
                sections.append(f"*{caption}*\n")
            sections.append("")

        # Footnotes (only for FOOTNOTE citation style)
        if self.footnotes and self.citation_style == CitationStyle.FOOTNOTE:
            sections.append("## Footnotes\n")
            sections.append(self.footnotes)
            sections.append("")

        # Sources
        if self.sources:
            sections.append("## Sources\n")
            sections.append(self.sources)
            sections.append("")

        content = "\n".join(sections)
        # Update word_count for consistency (though metadata renders dynamically)
        self.word_count = self._calculate_word_count()
        return content

    def __str__(self) -> str:
        """String representation returns rendered markdown."""
        return self.render_markdown()


@dataclass
class CitationInfo:
    """Formatted citation information for footnotes and bibliography."""

    citation_id: int
    source_id: int
    footnote: str  # Full footnote (first use)
    short_footnote: str  # Short footnote (subsequent use)
    bibliography: str  # Bibliography entry
    is_freeform: bool  # True if TemplateID == 0
    template_name: str | None  # Template name if not free-form


@dataclass
class CitationTracker:
    """Track citations for footnote numbering and source-level deduplication."""

    # Map: CitationID -> FootnoteNumber
    citation_to_footnote: dict[int, int] = field(default_factory=dict)

    # Map: SourceID -> first CitationID encountered
    source_first_citation: dict[int, int] = field(default_factory=dict)

    # Ordered list of citations as they appear in text
    citation_order: list[int] = field(default_factory=list)

    def add_citation(self, citation_id: int, source_id: int) -> int:
        """
        Add citation to tracker, returns footnote number.
        Tracks first citation per source for full vs short footnote logic.
        """
        if citation_id in self.citation_to_footnote:
            # Already encountered, return existing number
            return self.citation_to_footnote[citation_id]

        # New citation
        footnote_num = len(self.citation_order) + 1
        self.citation_to_footnote[citation_id] = footnote_num
        self.citation_order.append(citation_id)

        # Track first citation for this source
        if source_id not in self.source_first_citation:
            self.source_first_citation[source_id] = citation_id

        return footnote_num

    def is_first_for_source(self, citation_id: int, source_id: int) -> bool:
        """Check if this is the first citation for a given source."""
        return self.source_first_citation.get(source_id) == citation_id


def _get_row_value(row, key: str, default=None):
    """Get value from sqlite3.Row object with default."""
    try:
        return row[key] if key in row.keys() else default
    except (KeyError, TypeError):
        return default


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
        from rmagent.generators.biography import BiographyGenerator
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
            biography = self._generate_template_based(
                context, length, citation_style, include_sources
            )

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
                given=_get_row_value(person, "Given"),
                surname=_get_row_value(person, "Surname"),
                prefix=_get_row_value(person, "Prefix"),
                suffix=_get_row_value(person, "Suffix"),
            )

            # Calculate is_living based on 110-year rule
            birth_year = _get_row_value(person, "BirthYear")
            is_living = False
            if birth_year:
                age = self.current_year - birth_year
                is_living = age < 110

            # Extract birth/death information
            birth_date_str, birth_place = self._extract_vital_info(
                db, person_id, fact_type_id=1
            )  # Birth
            death_date_str, death_place = self._extract_vital_info(
                db, person_id, fact_type_id=2
            )  # Death

            # Get relationships
            parents = query.get_parents(person_id)
            father_name = None
            mother_name = None
            father_id = None
            mother_id = None

            if parents:
                father_id = _get_row_value(parents, "FatherID")
                mother_id = _get_row_value(parents, "MotherID")
                if father_id:
                    father_name = format_full_name(
                        given=_get_row_value(parents, "FatherGiven"),
                        surname=_get_row_value(parents, "FatherSurname"),
                    )
                if mother_id:
                    mother_name = format_full_name(
                        given=_get_row_value(parents, "MotherGiven"),
                        surname=_get_row_value(parents, "MotherSurname"),
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
            person_notes = _get_row_value(person, "Note")

            return PersonContext(
                person_id=person_id,
                full_name=full_name,
                given_name=_get_row_value(person, "Given", ""),
                surname=_get_row_value(person, "Surname", ""),
                prefix=_get_row_value(person, "Prefix"),
                suffix=_get_row_value(person, "Suffix"),
                nickname=_get_row_value(person, "Nickname"),
                birth_year=birth_year,
                birth_date=birth_date_str,
                birth_place=birth_place,
                death_year=_get_row_value(person, "DeathYear"),
                death_date=death_date_str,
                death_place=death_place,
                sex=_get_row_value(person, "Sex", 2),
                is_private=bool(_get_row_value(person, "IsPrivate", 0)),
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

    def _extract_vital_info(
        self, db: RMDatabase, person_id: int, fact_type_id: int
    ) -> tuple[str | None, str | None]:
        """Extract date and place for a vital event (birth/death)."""
        query = QueryService(db)
        vital_events = query.get_vital_events(person_id)

        for event in vital_events:
            if _get_row_value(event, "FactTypeID") == fact_type_id:
                # Parse date
                date_str = _get_row_value(event, "Date")
                formatted_date = None
                if date_str and not is_unknown_date(date_str):
                    try:
                        parsed_date = parse_rm_date(date_str)
                        formatted_date = parsed_date.format_display()
                    except Exception:
                        formatted_date = None

                # Format place
                place_str = _get_row_value(event, "Place")
                formatted_place = None
                if place_str:
                    try:
                        formatted_place = format_place_medium(place_str)
                    except Exception:
                        formatted_place = place_str

                return formatted_date, formatted_place

        return None, None

    def _categorize_events(
        self, db: RMDatabase, events: list[dict]
    ) -> tuple[list[EventContext], ...]:
        """Categorize events into vital, education, occupation, military, residence, and other."""
        vital = []
        education = []
        occupation = []
        military = []
        residence = []
        other = []

        for event in events:
            event_ctx = self._build_event_context(db, event)
            event_type = _get_row_value(event, "EventType", 0)

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
        date_str = _get_row_value(event, "Date", "")
        formatted_date = ""
        if date_str and not is_unknown_date(date_str):
            try:
                parsed = parse_rm_date(date_str)
                formatted_date = parsed.format_display()
            except Exception:
                formatted_date = date_str

        # Format place
        place_str = _get_row_value(event, "Place", "")
        formatted_place = ""
        if place_str:
            try:
                formatted_place = format_place_short(place_str)
            except Exception:
                formatted_place = place_str

        # Get citations for this event
        citations = self._get_citations_for_event(db, _get_row_value(event, "EventID", 0))

        return EventContext(
            event_id=_get_row_value(event, "EventID", 0),
            event_type=_get_row_value(event, "EventType", ""),
            date=formatted_date,
            place=formatted_place,
            details=_get_row_value(event, "Details", ""),
            note=_get_row_value(event, "Note", ""),
            is_private=bool(_get_row_value(event, "IsPrivate", 0)),
            proof=_get_row_value(event, "Proof", 0),
            citations=citations,
            sort_date=_get_row_value(event, "SortDate", 0),
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
            event_id = _get_row_value(event, "EventID")
            if not event_id:
                continue

            # Get full citation data including BLOBs
            citations = query.get_event_citations(event_id)
            for citation in citations:
                citation_id = _get_row_value(citation, "CitationID")
                if citation_id in seen_citation_ids:
                    continue
                seen_citation_ids.add(citation_id)
                all_citations.append(citation)

        return all_citations

    def _format_media_path(self, media_path: str, media_file: str) -> str:
        r"""
        Format media path for local file access.

        Converts RootsMagic's ?\path notation to a path relative to the database directory.

        Args:
            media_path: MediaPath from MultimediaTable (e.g., "?\Pictures - People")
            media_file: MediaFile from MultimediaTable (e.g., "Iams, Franklin Pierce (1852-1917).jpg")

        Returns:
            Formatted path relative to database directory
        """
        # Strip RootsMagic's ?\  or ?/ prefix if present
        if media_path.startswith("?\\"):
            media_path = media_path[2:]
        elif media_path.startswith("?/"):
            media_path = media_path[2:]

        # Combine path components
        if media_path:
            # Use Path to handle cross-platform separators
            full_path = Path(media_path) / media_file
        else:
            full_path = Path(media_file)

        # Convert to POSIX-style path (forward slashes) for Markdown
        return full_path.as_posix()

    def _calculate_age_at_death(self, birth_year: int | None, death_year: int | None) -> int | None:
        """Calculate age at death from birth and death years."""
        if birth_year and death_year:
            return death_year - birth_year
        return None

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
        if hasattr(self.agent, 'llm_provider'):
            provider_name = self.agent.llm_provider.__class__.__name__.replace('Provider', '').lower()
            llm_metadata = LLMMetadata(
                provider=provider_name,
                model=result.model,
                prompt_tokens=result.usage.prompt_tokens,
                completion_tokens=result.usage.completion_tokens,
                total_tokens=result.usage.total_tokens,
                prompt_time=total_time * 0.1,  # Estimate ~10% for prompt building
                llm_time=total_time * 0.9,      # Estimate ~90% for LLM
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
            modified_text, footnotes, tracker = self._process_citations_in_text(
                response_text, context.all_citations
            )

            # Use modified text for section parsing
            response_text = modified_text

            # Generate footnotes section
            if footnotes:
                footnotes_text = self._generate_footnotes_section(footnotes, tracker)
                citation_count = len(footnotes)

            # Generate sources section using new bibliography method
            if include_sources:
                sources_text = self._generate_sources_section(context.all_citations)
                # Count unique sources
                source_ids = set()
                for citation in context.all_citations:
                    source_id = _get_row_value(citation, "SourceID", 0)
                    if source_id:
                        source_ids.add(source_id)
                source_count = len(source_ids)
        else:
            # For other citation styles, use existing format
            if include_sources:
                sources_text = self._format_sources_section(context, citation_style)
                citation_count = len(context.all_citations)
                # Count unique sources
                source_ids = set()
                for citation in context.all_citations:
                    source_id = _get_row_value(citation, "SourceID", 0)
                    if source_id:
                        source_ids.add(source_id)
                source_count = len(source_ids)

        # Parse AI response into sections (after citation processing)
        sections = self._parse_ai_response(response_text)

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
        intro = self._generate_introduction(context)
        early_life = self._generate_early_life(context)
        education = self._generate_education(context)
        career = self._generate_career(context)
        marriage = self._generate_marriage_family(context)
        later_life = self._generate_later_life(context)
        death = self._generate_death_legacy(context)

        sources_text = ""
        citation_count = 0
        source_count = 0
        if include_sources:
            sources_text = self._format_sources_section(context, citation_style)
            citation_count = len(context.all_citations)
            # Count unique sources
            source_ids = set()
            for citation in context.all_citations:
                source_id = _get_row_value(citation, "SourceID", 0)
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
        )

    # ---- Private Methods: Template Generation ----

    def _generate_introduction(self, context: PersonContext) -> str:
        """Generate introduction section."""
        lines = []

        # Basic intro: Name was born on [date] in [place]
        birth_info = ""
        if context.birth_date:
            birth_info = f" on {context.birth_date}"
        if context.birth_place:
            birth_info += f" in {context.birth_place}"

        if birth_info:
            lines.append(f"{context.full_name} was born{birth_info}.")
        else:
            lines.append(f"{context.full_name}'s birth date and place are not recorded.")

        # Parents
        if context.father_name or context.mother_name:
            parent_info = []
            if context.father_name:
                parent_info.append(context.father_name)
            if context.mother_name:
                parent_info.append(context.mother_name)
            parent_str = " and ".join(parent_info)
            pronoun = "He" if context.sex == 0 else "She" if context.sex == 1 else "They"
            verb = "was" if context.sex != 2 else "were"
            lines.append(f"{pronoun} {verb} the child of {parent_str}.")

        # Death information (if applicable)
        if context.death_date or context.death_place:
            death_info = ""
            pronoun = "He" if context.sex == 0 else "She" if context.sex == 1 else "They"
            verb = "died" if context.sex != 2 else "died"

            if context.death_date:
                death_info = f" on {context.death_date}"
            if context.death_place:
                death_info += f" in {context.death_place}"

            # Calculate age at death if both years available
            age = self._calculate_age_at_death(context.birth_year, context.death_year)
            if age is not None:
                death_info += f" at the age of {age}"

            lines.append(f"{pronoun} {verb}{death_info}.")

        return " ".join(lines)

    def _generate_early_life(self, context: PersonContext) -> str:
        """Generate early life section."""
        if not context.siblings:
            return ""

        sibling_count = len(context.siblings)
        pronoun = "He" if context.sex == 0 else "She" if context.sex == 1 else "They"
        verb = "grew" if context.sex != 2 else "grew"

        if sibling_count == 0:
            return f"{pronoun} {verb} up as an only child."
        elif sibling_count == 1:
            return f"{pronoun} had one sibling."
        else:
            return f"{pronoun} had {sibling_count} siblings."

    def _generate_education(self, context: PersonContext) -> str:
        """Generate education section."""
        if not context.education_events:
            return ""

        lines = []
        for event in context.education_events:
            event_desc = f"{event.date}" if event.date else "At an unknown date"
            if event.place:
                event_desc += f" in {event.place}"
            if event.details:
                event_desc += f", {event.details}"
            lines.append(event_desc + ".")

        return " ".join(lines)

    def _generate_career(self, context: PersonContext) -> str:
        """Generate career section."""
        if not context.occupation_events:
            return ""

        lines = []
        for event in context.occupation_events:
            if event.details:
                desc = f"{context.given_name} worked as {event.details}"
                if event.date:
                    desc += f" in {event.date}"
                if event.place:
                    desc += f" in {event.place}"
                lines.append(desc + ".")

        return " ".join(lines)

    def _generate_marriage_family(self, context: PersonContext) -> str:
        """Generate marriage and family section."""
        lines = []

        # Marriages
        if context.spouses:
            for spouse in context.spouses:
                spouse_name = format_full_name(
                    given=_get_row_value(spouse, "Given"),
                    surname=_get_row_value(spouse, "Surname"),
                )
                marriage_date = _get_row_value(spouse, "MarriageDate")
                if marriage_date and not is_unknown_date(marriage_date):
                    try:
                        parsed = parse_rm_date(marriage_date)
                        date_str = parsed.format_display()
                        lines.append(f"{context.given_name} married {spouse_name} on {date_str}.")
                    except Exception:
                        lines.append(f"{context.given_name} married {spouse_name}.")
                else:
                    lines.append(f"{context.given_name} married {spouse_name}.")

        # Children
        if context.children:
            child_count = len(context.children)
            if child_count == 1:
                lines.append("They had one child.")
            else:
                lines.append(f"They had {child_count} children.")

        return " ".join(lines)

    def _generate_later_life(self, context: PersonContext) -> str:
        """Generate later life section."""
        # Could include residence changes, later events
        if context.residence_events:
            places = [e.place for e in context.residence_events if e.place]
            if places:
                return f"{context.given_name} resided in {', '.join(places[:3])}."
        return ""

    def _generate_death_legacy(self, context: PersonContext) -> str:
        """Generate death and legacy section."""
        if not context.death_date and not context.death_place:
            return ""

        death_info = ""
        if context.death_date:
            death_info = f" on {context.death_date}"
        if context.death_place:
            death_info += f" in {context.death_place}"

        pronoun = "He" if context.sex == 0 else "She" if context.sex == 1 else "They"
        verb = "died" if context.sex != 2 else "died"

        return f"{pronoun} {verb}{death_info}."

    def _format_sources_section(self, context: PersonContext, citation_style: CitationStyle) -> str:
        """Format sources section based on citation style."""
        if not context.all_citations:
            return ""

        lines = []
        for i, citation in enumerate(context.all_citations, 1):
            source_name_raw = _get_row_value(citation, "SourceName", "Unknown Source")
            citation_name = _get_row_value(citation, "CitationName", "")

            # Remove source type prefixes like "Book: " or "Newspapers: "
            source_name = self._strip_source_type_prefix(source_name_raw)

            if citation_style == CitationStyle.FOOTNOTE:
                lines.append(f"{i}. *{source_name}*")
                if citation_name:
                    lines.append(f"   {citation_name}")
            elif citation_style == CitationStyle.PARENTHETICAL:
                lines.append(f"- *{source_name}*")
                if citation_name:
                    lines.append(f"  ({citation_name})")
            else:  # NARRATIVE
                if citation_name:
                    lines.append(f"- *{source_name}*: {citation_name}")
                else:
                    lines.append(f"- *{source_name}*")

        return "\n".join(lines)

    @staticmethod
    def _strip_source_type_prefix(source_name: str) -> str:
        """
        Remove source type prefixes like 'Book: ', 'Newspapers: ', etc.

        Examples:
            "Book: Smith Family History" -> "Smith Family History"
            "Newspapers: Baltimore Sun" -> "Baltimore Sun"
            "US Census Records" -> "US Census Records" (no change)
        """
        # Common source type prefixes in RootsMagic
        prefixes = [
            "Book: ",
            "Books: ",
            "Newspaper: ",
            "Newspapers: ",
            "Cemetery: ",
            "Cemeteries: ",
            "Census: ",
            "Church Records: ",
            "Court Records: ",
            "Military Records: ",
            "Vital Records: ",
            "Website: ",
            "Websites: ",
            "Document: ",
            "Documents: ",
            "Letter: ",
            "Letters: ",
            "Photo: ",
            "Photos: ",
        ]

        for prefix in prefixes:
            if source_name.startswith(prefix):
                return source_name[len(prefix):]

        return source_name

    def _parse_ai_response(self, response_text: str) -> dict[str, str]:
        """Parse AI-generated biography into sections."""
        # Simple parser - looks for section headers
        sections = {
            "introduction": "",
            "early_life": "",
            "education": "",
            "career": "",
            "marriage_family": "",
            "later_life": "",
            "death_legacy": "",
        }

        # Split by markdown headers and categorize
        # This is a simplified version - production would use more robust parsing
        lines = response_text.split("\n")
        current_section = None
        current_text = []

        for line in lines:
            if line.startswith("##"):
                # Save previous section
                if current_section and current_text:
                    sections[current_section] = "\n".join(current_text).strip()

                # Detect new section
                header = line.lower()
                if "introduction" in header or "birth" in header:
                    current_section = "introduction"
                elif "early life" in header or "family background" in header:
                    current_section = "early_life"
                elif "education" in header:
                    current_section = "education"
                elif "career" in header or "occupation" in header:
                    current_section = "career"
                elif "marriage" in header or "family" in header:
                    current_section = "marriage_family"
                elif "later life" in header:
                    current_section = "later_life"
                elif "death" in header or "legacy" in header:
                    current_section = "death_legacy"
                else:
                    current_section = None

                current_text = []
            elif current_section:
                current_text.append(line)

        # Save final section
        if current_section and current_text:
            sections[current_section] = "\n".join(current_text).strip()

        return sections

    # ---- Citation Formatting Methods ----

    def _format_citation_info(self, citation: dict) -> CitationInfo:
        """
        Format citation into CitationInfo with all text versions.
        Handles free-form (TemplateID=0) and template-based citations.
        """
        citation_id = _get_row_value(citation, "CitationID", 0)
        source_id = _get_row_value(citation, "SourceID", 0)
        template_id = _get_row_value(citation, "TemplateID", 0)
        template_name = _get_row_value(citation, "TemplateName")

        is_freeform = template_id == 0

        if is_freeform:
            # Use formatted fields from CitationTable if available
            footnote = _get_row_value(citation, "Footnote")
            short_footnote = _get_row_value(citation, "ShortFootnote")
            bibliography = _get_row_value(citation, "CitationBibliography")

            # Fallback: Generate from Fields BLOB if NULL
            if not footnote:
                footnote = self._generate_citation_from_fields(citation)
            if not short_footnote:
                short_footnote = self._generate_short_footnote_from_fields(citation, footnote)
            if not bibliography:
                bibliography = self._generate_bibliography_from_fields(citation)
        else:
            # Template-based: Show placeholders
            footnote = f"[Citation {citation_id}, Template: {template_name}]"
            short_footnote = footnote
            bibliography = f"[Source {source_id}, Template: {template_name}]"

        return CitationInfo(
            citation_id=citation_id,
            source_id=source_id,
            footnote=footnote,
            short_footnote=short_footnote,
            bibliography=bibliography,
            is_freeform=is_freeform,
            template_name=template_name,
        )

    def _generate_citation_from_fields(self, citation: dict) -> str:
        """
        Generate footnote text from BLOB fields (fallback).
        First checks SourceFields for pre-formatted Footnote, then CitationFields for page/details.
        Returns citation with WARNING only if all approaches fail.
        """
        citation_id = _get_row_value(citation, "CitationID", 0)

        # First, check SourceFields BLOB for pre-formatted Footnote
        source_fields_blob = _get_row_value(citation, "SourceFields")
        if source_fields_blob:
            from rmagent.rmlib.parsers.blob_parser import parse_source_fields

            try:
                source_fields = parse_source_fields(source_fields_blob)
                footnote = source_fields.get("Footnote", "")
                if footnote:
                    return footnote
            except Exception:
                pass  # Continue to next approach

        # Fallback: Check CitationFields BLOB for page/details
        citation_fields_blob = _get_row_value(citation, "CitationFields")
        if citation_fields_blob:
            from rmagent.rmlib.parsers.blob_parser import parse_citation_fields

            try:
                fields = parse_citation_fields(citation_fields_blob)
                # Simple format: Page field is most common
                page = fields.get("Page", "")
                if page:
                    return f"p. {page}"
                # If no page, show first non-empty field
                for key, value in fields.items():
                    if value:
                        return f"{key}: {value}"
            except Exception:
                pass

        return f"[Citation {citation_id}] ⚠️ WARNING: Missing citation fields"

    def _generate_short_footnote_from_fields(self, citation: dict, full_footnote: str) -> str:
        """
        Generate short footnote text from BLOB fields (fallback).
        First checks SourceFields for pre-formatted ShortFootnote, then falls back to full footnote.
        """
        # Check SourceFields BLOB for pre-formatted ShortFootnote
        source_fields_blob = _get_row_value(citation, "SourceFields")
        if source_fields_blob:
            from rmagent.rmlib.parsers.blob_parser import parse_source_fields

            try:
                source_fields = parse_source_fields(source_fields_blob)
                short_footnote = source_fields.get("ShortFootnote", "")
                if short_footnote:
                    return short_footnote
            except Exception:
                pass

        # Fallback: use full footnote
        return full_footnote

    def _generate_bibliography_from_fields(self, citation: dict) -> str:
        """
        Generate bibliography entry from SourceFields BLOB (fallback).
        First checks for pre-formatted Bibliography field, then constructs from individual fields.
        Returns source name with WARNING only if all approaches fail.
        """
        source_name = _get_row_value(citation, "SourceName", "[Unknown Source]")
        fields_blob = _get_row_value(citation, "SourceFields")

        if not fields_blob:
            return f"{source_name} ⚠️ WARNING: Missing source fields"

        from rmagent.rmlib.parsers.blob_parser import parse_source_fields

        try:
            fields = parse_source_fields(fields_blob)

            # First, check for pre-formatted Bibliography field (RootsMagic stores formatted text here)
            bibliography = fields.get("Bibliography", "")
            if bibliography:
                return bibliography

            # Fallback: Evidence Explained basic format: Author. Title. Publisher, Year.
            author = fields.get("Author", "")
            title = fields.get("Title", "")
            publisher = fields.get("Publisher", "")
            year = fields.get("Year", "")

            parts = []
            if author:
                parts.append(f"{author}.")
            if title:
                parts.append(f"*{title}.*")
            if publisher and year:
                parts.append(f"{publisher}, {year}.")
            elif publisher:
                parts.append(f"{publisher}.")
            elif year:
                parts.append(f"{year}.")

            if parts:
                return " ".join(parts)
            return f"{source_name} ⚠️ WARNING: No source details in fields"
        except Exception as e:
            return f"{source_name} ⚠️ WARNING: Failed to parse source fields ({e})"

    def _process_citations_in_text(
        self, text: str, all_citations: list[dict]
    ) -> tuple[str, list[tuple[int, CitationInfo]], CitationTracker]:
        """
        Process {{cite:ID}} markers in text, replace with [^N] footnote markers.

        Returns:
            - Modified text with [^N] markers
            - List of (footnote_num, CitationInfo) in order of appearance
            - CitationTracker with all citation metadata
        """
        import re

        tracker = CitationTracker()

        # Build lookup: CitationID -> CitationInfo
        citation_lookup = {}
        for citation in all_citations:
            cid = _get_row_value(citation, "CitationID", 0)
            citation_lookup[cid] = self._format_citation_info(citation)

        # Find all {{cite:ID}} markers (double braces as specified in prompt)
        pattern = r"\{\{cite:(\d+)\}\}"
        matches = list(re.finditer(pattern, text))

        # Replace markers with footnote numbers (in reverse to preserve positions)
        replacements = []
        for match in matches:
            citation_id = int(match.group(1))

            if citation_id not in citation_lookup:
                # Citation not found, leave placeholder
                footnote_marker = f"[^{citation_id}?]"
            else:
                citation_info = citation_lookup[citation_id]
                source_id = citation_info.source_id

                # Get or assign footnote number
                footnote_num = tracker.add_citation(citation_id, source_id)
                footnote_marker = f"[^{footnote_num}]"

            replacements.append((match.span(), footnote_marker))

        # Apply replacements in reverse order to preserve positions
        modified_text = text
        for (start, end), replacement in reversed(replacements):
            modified_text = modified_text[:start] + replacement + modified_text[end:]

        # Build ordered footnote list
        footnotes = []
        for citation_id in tracker.citation_order:
            citation_info = citation_lookup.get(citation_id)
            if citation_info:
                footnote_num = tracker.citation_to_footnote[citation_id]
                footnotes.append((footnote_num, citation_info))

        return modified_text, footnotes, tracker

    def _generate_footnotes_section(
        self, footnotes: list[tuple[int, CitationInfo]], tracker: CitationTracker
    ) -> str:
        """
        Generate footnotes section with numbered entries.
        First citation per source uses full footnote, subsequent use short.
        """
        lines = []

        for footnote_num, citation_info in footnotes:
            # Determine if first citation for this source
            is_first = tracker.is_first_for_source(citation_info.citation_id, citation_info.source_id)

            # Use full or short footnote
            footnote_text = citation_info.footnote if is_first else citation_info.short_footnote

            lines.append(f"[^{footnote_num}]: {footnote_text}")

        return "\n".join(lines)

    def _generate_sources_section(self, all_citations: list[dict]) -> str:
        """
        Generate alphabetically sorted bibliography using SourceTable.ActualText.
        Deduplicate by SourceID.
        """
        # Build unique sources map: SourceID -> CitationInfo
        sources = {}
        for citation in all_citations:
            source_id = _get_row_value(citation, "SourceID", 0)
            if source_id not in sources:
                citation_info = self._format_citation_info(citation)
                sources[source_id] = citation_info

        # Sort alphabetically by bibliography text
        sorted_sources = sorted(sources.values(), key=lambda c: c.bibliography.lower())

        # Format as list
        lines = []
        for citation_info in sorted_sources:
            lines.append(f"- {citation_info.bibliography}")

        return "\n".join(lines)
