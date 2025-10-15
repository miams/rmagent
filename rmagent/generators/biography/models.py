"""
Data models for biography generation.

Contains all dataclasses and enums used throughout the biography module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path


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
    media_root_directory: Path | None = None  # Root directory for media files (replaces ? in MediaPath)

    def calculate_word_count(self) -> int:
        """
        Calculate word count from biography narrative content only.

        Excludes front matter, footnotes, and sources sections.
        """
        all_text = "\n".join(
            [
                self.introduction,
                self.early_life,
                self.education,
                self.career,
                self.marriage_family,
                self.later_life,
                self.death_legacy,
            ]
        )
        return len(all_text.split())

    def render_markdown(self, include_metadata: bool = True) -> str:
        """Render complete biography as Markdown with optional front matter."""
        # Import here to avoid circular dependency
        from .rendering import BiographyRenderer

        renderer = BiographyRenderer(media_root_directory=self.media_root_directory)
        return renderer.render_markdown(self, include_metadata)

    def render_metadata(self) -> str:
        """Render Hugo-style front matter metadata."""
        # Import here to avoid circular dependency
        from .rendering import BiographyRenderer

        renderer = BiographyRenderer(media_root_directory=self.media_root_directory)
        return renderer.render_metadata(self)

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


def get_row_value(row, key: str, default=None):
    """Get value from sqlite3.Row object with default."""
    try:
        return row[key] if key in row.keys() else default
    except (KeyError, TypeError):
        return default
