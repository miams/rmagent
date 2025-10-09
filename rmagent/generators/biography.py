"""
Biography generator for RMAgent.

Generates formatted biographical narratives following the 9-section structure
from RM11_Biography_Best_Practices.md. Handles privacy rules, citation formatting,
and length variations (short/standard/comprehensive).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rmagent.agent.genealogy_agent import GenealogyAgent
from rmagent.rmlib.database import RMDatabase
from rmagent.rmlib.models import OwnerType
from rmagent.rmlib.parsers.date_parser import parse_rm_date, is_unknown_date
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
class EventContext:
    """Contextual information for a single event."""

    event_id: int
    event_type: str
    date: str  # Formatted display date
    place: str
    details: str
    is_private: bool
    proof: int
    citations: List[Dict]  # CitationID, SourceID, Page, etc.
    sort_date: int


@dataclass
class PersonContext:
    """Complete person context for biography generation."""

    person_id: int
    full_name: str
    given_name: str
    surname: str
    prefix: Optional[str]
    suffix: Optional[str]
    nickname: Optional[str]

    birth_year: Optional[int]
    birth_date: Optional[str]
    birth_place: Optional[str]

    death_year: Optional[int]
    death_date: Optional[str]
    death_place: Optional[str]

    sex: int  # 0=Male, 1=Female, 2=Unknown
    is_private: bool
    is_living: bool  # Calculated based on 110-year rule

    # Relationships
    father_id: Optional[int] = None
    father_name: Optional[str] = None
    mother_id: Optional[int] = None
    mother_name: Optional[str] = None
    spouses: List[Dict] = field(default_factory=list)
    children: List[Dict] = field(default_factory=list)
    siblings: List[Dict] = field(default_factory=list)

    # Events categorized by type
    vital_events: List[EventContext] = field(default_factory=list)
    education_events: List[EventContext] = field(default_factory=list)
    occupation_events: List[EventContext] = field(default_factory=list)
    military_events: List[EventContext] = field(default_factory=list)
    residence_events: List[EventContext] = field(default_factory=list)
    other_events: List[EventContext] = field(default_factory=list)

    # Media
    media_files: List[Dict] = field(default_factory=list)

    # Sources
    all_citations: List[Dict] = field(default_factory=list)


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
    sources: str

    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    word_count: int = 0
    privacy_applied: bool = False

    def render_markdown(self) -> str:
        """Render complete biography as Markdown."""
        sections = []

        # Title
        sections.append(f"# {self.full_name}\n")

        # Introduction
        if self.introduction:
            sections.append("## Introduction\n")
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

        # Sources
        if self.sources:
            sections.append("## Sources\n")
            sections.append(self.sources)
            sections.append("")

        content = "\n".join(sections)
        self.word_count = len(content.split())
        return content

    def __str__(self) -> str:
        """String representation returns rendered markdown."""
        return self.render_markdown()


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
        db: Optional[RMDatabase | Path | str] = None,
        agent: Optional[GenealogyAgent] = None,
        extension_path: Path | str = Path("./sqlite-extension/icu.dylib"),
        current_year: Optional[int] = None,
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
            birth_date_str, birth_place = self._extract_vital_info(db, person_id, fact_type_id=1)  # Birth
            death_date_str, death_place = self._extract_vital_info(db, person_id, fact_type_id=2)  # Death

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
            vital_events, education_events, occupation_events, military_events, residence_events, other_events = (
                self._categorize_events(db, all_events)
            )

            # Get media if requested
            media_files = []
            if include_media:
                media_files = self._get_media_for_person(db, person_id)

            # Get all citations
            all_citations = self._get_all_citations_for_person(db, person_id)

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

    def _extract_vital_info(self, db: RMDatabase, person_id: int, fact_type_id: int) -> Tuple[Optional[str], Optional[str]]:
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
        self, db: RMDatabase, events: List[Dict]
    ) -> Tuple[List[EventContext], ...]:
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

    def _build_event_context(self, db: RMDatabase, event: Dict) -> EventContext:
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
            is_private=bool(_get_row_value(event, "IsPrivate", 0)),
            proof=_get_row_value(event, "Proof", 0),
            citations=citations,
            sort_date=_get_row_value(event, "SortDate", 0),
        )

    def _get_citations_for_event(self, db: RMDatabase, event_id: int) -> List[Dict]:
        """Get all citations for an event."""
        cursor = db.execute(
            """
            SELECT cl.CitationID, c.CitationName, c.SourceID, c.ActualText, c.RefNumber
            FROM CitationLinkTable cl
            JOIN CitationTable c ON cl.CitationID = c.CitationID
            WHERE cl.OwnerType = ? AND cl.OwnerID = ?
            ORDER BY cl.SortOrder
            """,
            (OwnerType.EVENT.value, event_id),
        )
        return cursor.fetchall()

    def _get_media_for_person(self, db: RMDatabase, person_id: int) -> List[Dict]:
        """Get all media files linked to person."""
        cursor = db.execute(
            """
            SELECT m.MediaID, m.MediaFile, m.Caption, m.Date, m.Description
            FROM MediaLinkTable ml
            JOIN MultimediaTable m ON ml.MediaID = m.MediaID
            WHERE ml.OwnerType = ? AND ml.OwnerID = ?
            ORDER BY ml.SortOrder
            """,
            (OwnerType.PERSON.value, person_id),
        )
        return cursor.fetchall()

    def _get_all_citations_for_person(self, db: RMDatabase, person_id: int) -> List[Dict]:
        """Get all citations associated with person (via events, names, etc.)."""
        # Get citations for all events
        cursor = db.execute(
            """
            SELECT DISTINCT cl.CitationID, c.CitationName, c.SourceID, s.Name AS SourceName
            FROM EventTable e
            JOIN CitationLinkTable cl ON cl.OwnerType = ? AND cl.OwnerID = e.EventID
            JOIN CitationTable c ON cl.CitationID = c.CitationID
            JOIN SourceTable s ON c.SourceID = s.SourceID
            WHERE e.OwnerType = ? AND e.OwnerID = ?
            ORDER BY s.Name, c.CitationName
            """,
            (OwnerType.EVENT.value, OwnerType.PERSON.value, person_id),
        )
        return cursor.fetchall()

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

        # Use agent's generate_biography method
        result = self.agent.generate_biography(person_id=context.person_id, style=length.value)

        # Parse AI response into sections
        # This is a simplified parser - a more robust version would use regex
        # to extract each section from the markdown
        sections = self._parse_ai_response(result.text)

        # Generate sources section if requested
        sources_text = ""
        if include_sources:
            sources_text = self._format_sources_section(context, citation_style)

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
            sources=sources_text,
            privacy_applied=getattr(context, "privacy_applied", False),
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
        if include_sources:
            sources_text = self._format_sources_section(context, citation_style)

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
            sources=sources_text,
            privacy_applied=getattr(context, "privacy_applied", False),
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
                lines.append(f"They had one child.")
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
            source_name = _get_row_value(citation, "SourceName", "Unknown Source")
            citation_name = _get_row_value(citation, "CitationName", "")

            if citation_style == CitationStyle.FOOTNOTE:
                lines.append(f"{i}. {source_name}")
                if citation_name:
                    lines.append(f"   {citation_name}")
            elif citation_style == CitationStyle.PARENTHETICAL:
                lines.append(f"- {source_name}")
                if citation_name:
                    lines.append(f"  ({citation_name})")
            else:  # NARRATIVE
                lines.append(f"- {source_name}: {citation_name}")

        return "\n".join(lines)

    def _parse_ai_response(self, response_text: str) -> Dict[str, str]:
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
