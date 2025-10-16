"""
Census sidecar database schema models.

Defines the structure for the census extraction sidecar PostgreSQL database.
This database stores extracted census data using a hybrid schema:
- Common fields (name, age, sex, race, birthplace, occupation) as columns
- Year-specific fields (e.g., income_1940, education_level) in JSONB
- OCR provenance tracking for each field
- Review workflow and audit logging

Architecture: Hybrid Schema with PostgreSQL JSONB
- Performance: 0.8ms queries for review UI
- Flexibility: JSONB handles varying census year structures
- Type safety: Common fields have proper data types
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OCRModel(str, Enum):
    """OCR/HTR model types."""

    TESSERACT = "tesseract"
    KRAKEN = "kraken"
    CALAMARI = "calamari"
    VISION_LLM = "vision_llm"


class ReviewStatus(str, Enum):
    """Review status for census entries."""

    PENDING = "pending"
    APPROVED = "approved"
    CORRECTED = "corrected"
    FLAGGED = "flagged"
    SKIPPED = "skipped"


class CensusPage(BaseModel):
    """Represents a census page image and its metadata."""

    page_id: Optional[int] = None  # Primary key
    media_id: int  # RootsMagic MediaID
    person_id: Optional[int] = None  # Primary person linked to this image
    census_year: int  # 1790-1950 (excluding 1890)
    image_path: str  # Path to original image
    processed_path: Optional[str] = None  # Path to preprocessed image
    layout_metadata: Optional[dict] = None  # JSON: cell coordinates, row/col counts
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CensusHousehold(BaseModel):
    """Represents a household unit in a census page."""

    household_id: Optional[int] = None  # Primary key
    page_id: int  # Foreign key to CensusPage
    dwelling_number: Optional[str] = None
    family_number: Optional[str] = None
    address: Optional[str] = None
    enumeration_district: Optional[str] = None
    sheet_number: Optional[str] = None
    line_number_start: Optional[int] = None
    line_number_end: Optional[int] = None
    # Cross-page household tracking
    prev_page_id: Optional[int] = None
    next_page_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CensusFormat(str, Enum):
    """Census record format types."""

    AGGREGATE = "aggregate"  # Pre-1850 tally format (household head only)
    INDIVIDUAL = "individual"  # Post-1850 individual records


class CensusEntry(BaseModel):
    """Represents a single person entry in a census record.

    Hybrid schema design:
    - Common fields (name, age, sex, race, birthplace, occupation) as typed columns
    - Year-specific fields (e.g., income_1940, education_level) in JSONB 'fields'
    - Present in 10+ census years = common field (1850-1950)

    RootsMagic linkage:
    - person_id: Links to RootsMagic PersonTable
    - event_id: Links to census EventTable record
    - citation_id: Links to CitationTable for source documentation
    """

    entry_id: Optional[int] = None  # Primary key
    household_id: int  # Foreign key to CensusHousehold
    person_id: Optional[int] = None  # RootsMagic PersonID
    event_id: Optional[int] = None  # RootsMagic EventID for census event
    citation_id: Optional[int] = None  # RootsMagic CitationID for source
    match_confidence: Optional[float] = None  # 0.0-1.0 matching score
    line_number: Optional[int] = None

    # Census format and special flags
    census_format: CensusFormat = CensusFormat.INDIVIDUAL  # Default post-1850
    implied: bool = False  # True if genealogist-assessed pre-1850 family member
    enumeration_date: Optional[str] = None  # Actual census date (vs official year)

    # Common fields (present in 10+ census years: 1850-1950)
    name: Optional[str] = None  # Full name as recorded
    age: Optional[int] = None  # Age in years
    sex: Optional[str] = None  # M/F/Male/Female
    race: Optional[str] = None  # Race/color as recorded
    birthplace: Optional[str] = None  # Birthplace (city, state, country)
    occupation: Optional[str] = None  # Occupation as recorded

    # Year-specific fields (JSONB)
    # Examples: relationship_to_head, marital_status, father_birthplace,
    # mother_birthplace, immigration_year, income_wages, education_level
    fields: dict = Field(default_factory=dict)  # PostgreSQL JSONB

    # Review tracking
    review_status: ReviewStatus = ReviewStatus.PENDING
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CensusFieldProvenance(BaseModel):
    """Provenance tracking for individual census fields.

    Stores OCR metadata and image coordinates for each extracted field.
    Links to specific entry and field path (e.g., "name", "fields.income_1940").
    """

    provenance_id: Optional[int] = None  # Primary key
    entry_id: int  # Foreign key to CensusEntry
    field_path: str  # e.g., "name", "age", "fields.income_1940", "fields.relationship_to_head"

    # OCR metadata
    ocr_model: OCRModel
    ocr_confidence: Optional[float] = None  # 0.0-1.0
    raw_ocr_text: Optional[str] = None  # Before normalization

    # Image region
    cell_coordinates: Optional[dict] = None  # JSON: {x, y, width, height}
    cell_image_path: Optional[str] = None  # Path to cropped cell snippet

    created_at: datetime = Field(default_factory=datetime.utcnow)


class CensusReviewLog(BaseModel):
    """Audit log for reviewer actions.

    Records all changes made during human review, including field corrections
    and entry-level actions (approve, flag, skip).
    Tracks both common field changes (name, age) and JSONB field changes (fields.income_1940).
    """

    log_id: Optional[int] = None  # Primary key
    entry_id: int  # Foreign key to CensusEntry
    reviewer_id: str  # Username/ID of reviewer
    action: str  # "approve", "correct", "flag", "skip"
    field_path: Optional[str] = None  # e.g., "name", "age", "fields.income_1940"
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CensusFieldMetadata(BaseModel):
    """Metadata describing census fields for LLM context and narrative generation.

    Provides structured information about what each census field means, how to
    interpret it, and how to express it in biographical narratives. Critical for
    LLM-assisted biography generation.

    Key use cases:
    - LLM context: "What does 'income_wages' mean in 1940 census?"
    - Narrative templates: "earning ${value} annually"
    - Field validation: Check enum values match expected categories
    - Multi-year comparisons: Track which fields are common across census years
    """

    field_id: Optional[int] = None  # Primary key
    census_year: int  # Which census year this field appears in
    field_path: str  # e.g., "income_wages", "fields.relationship_to_head"
    display_name: str  # Human-readable name: "Wage Income"
    description: Optional[str] = None  # Full explanation of what field represents
    column_number: Optional[int] = None  # Official column number on census form (e.g., 30 for income)
    column_range: Optional[str] = None  # For multi-column fields (e.g., "15-16" for birthplace)
    data_type: Optional[str] = None  # "integer", "string", "enum", "boolean"
    enum_values: Optional[list] = None  # For categorical fields: ["Head", "Wife", "Son", ...]
    narrative_template: Optional[str] = None  # How to express in biography: "earning ${value} annually"
    narrative_priority: Optional[int] = None  # Order of importance (1=high, 10=low)
    common_across_years: bool = False  # TRUE if field exists in multiple census years
    sample_only: bool = False  # TRUE if only collected for sample lines (e.g., 1940 lines 14, 29)
    sample_lines: Optional[list] = None  # Which line numbers (e.g., [14, 29] for 1940)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# PostgreSQL schema definition with JSONB
# Hybrid schema: common fields as columns + year-specific fields in JSONB
SIDECAR_SCHEMA = """
-- Census page: image metadata and processing status
CREATE TABLE IF NOT EXISTS census_page (
    page_id SERIAL PRIMARY KEY,
    media_id INTEGER NOT NULL UNIQUE,
    person_id INTEGER,  -- Primary person linked to this image
    census_year INTEGER NOT NULL CHECK (census_year BETWEEN 1790 AND 1950),
    image_path TEXT NOT NULL,
    processed_path TEXT,
    layout_metadata JSONB,  -- Cell coordinates, row/col structure
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Household: group of people living together
CREATE TABLE IF NOT EXISTS census_household (
    household_id SERIAL PRIMARY KEY,
    page_id INTEGER NOT NULL REFERENCES census_page(page_id),
    dwelling_number TEXT,
    family_number TEXT,
    address TEXT,
    enumeration_district TEXT,
    sheet_number TEXT,
    line_number_start INTEGER,
    line_number_end INTEGER,
    prev_page_id INTEGER,  -- Cross-page household tracking
    next_page_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Entry: single person in census
-- Hybrid schema: common fields as columns + year-specific fields in JSONB
CREATE TABLE IF NOT EXISTS census_entry (
    entry_id SERIAL PRIMARY KEY,
    household_id INTEGER NOT NULL REFERENCES census_household(household_id),

    -- RootsMagic linkage
    person_id INTEGER,  -- RootsMagic PersonID
    event_id INTEGER,  -- RootsMagic EventID for census event
    citation_id INTEGER,  -- RootsMagic CitationID for source documentation
    match_confidence REAL CHECK (match_confidence >= 0 AND match_confidence <= 1),
    line_number INTEGER,

    -- Census format and special flags
    census_format TEXT NOT NULL DEFAULT 'individual' CHECK (census_format IN ('aggregate', 'individual')),
    implied BOOLEAN NOT NULL DEFAULT FALSE,  -- Genealogist-assessed pre-1850 family member
    enumeration_date TEXT,  -- Actual census date (vs official year)

    -- Common fields (present in 10+ census years: 1850-1950)
    name TEXT,
    age INTEGER CHECK (age >= 0 AND age <= 150),
    sex TEXT CHECK (sex IN ('M', 'F', 'Male', 'Female', NULL)),
    race TEXT,
    birthplace TEXT,
    occupation TEXT,

    -- Year-specific fields (JSONB for flexibility)
    -- Examples: relationship_to_head, marital_status, father_birthplace,
    -- mother_birthplace, immigration_year, income_wages, education_level
    fields JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Review tracking
    review_status TEXT DEFAULT 'pending' CHECK (review_status IN ('pending', 'approved', 'corrected', 'flagged', 'skipped')),
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Provenance: OCR metadata for each field
CREATE TABLE IF NOT EXISTS census_field_provenance (
    provenance_id SERIAL PRIMARY KEY,
    entry_id INTEGER NOT NULL REFERENCES census_entry(entry_id),
    field_path TEXT NOT NULL,  -- e.g., "name", "age", "fields.income_1940"

    ocr_model TEXT NOT NULL CHECK (ocr_model IN ('tesseract', 'kraken', 'calamari', 'vision_llm')),
    ocr_confidence REAL CHECK (ocr_confidence >= 0 AND ocr_confidence <= 1),
    raw_ocr_text TEXT,  -- Before normalization

    cell_coordinates JSONB,  -- {x, y, width, height}
    cell_image_path TEXT,  -- Path to cropped cell snippet

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Review log: audit trail for all reviewer actions
CREATE TABLE IF NOT EXISTS census_review_log (
    log_id SERIAL PRIMARY KEY,
    entry_id INTEGER NOT NULL REFERENCES census_entry(entry_id),
    reviewer_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('approve', 'correct', 'flag', 'skip')),
    field_path TEXT,  -- e.g., "name", "fields.income_1940"
    old_value TEXT,
    new_value TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Field metadata: describes census fields for LLM context and narrative generation
CREATE TABLE IF NOT EXISTS census_field_metadata (
    field_id SERIAL PRIMARY KEY,
    census_year INTEGER NOT NULL CHECK (census_year BETWEEN 1790 AND 1950),
    field_path TEXT NOT NULL,  -- e.g., "income_wages", "fields.relationship_to_head"
    display_name TEXT NOT NULL,  -- Human-readable name
    description TEXT,  -- Full explanation of what the field represents
    column_number INTEGER,  -- Official column number on census form (e.g., 30 for income)
    column_range TEXT,  -- For multi-column fields (e.g., "15-16" for birthplace)
    data_type TEXT,  -- "integer", "string", "enum", "boolean"
    enum_values JSONB,  -- For categorical fields: ["Head", "Wife", "Son", ...]
    narrative_template TEXT,  -- How to express in biography: "earning ${value} annually"
    narrative_priority INTEGER,  -- Order of importance (1=high, 10=low)
    common_across_years BOOLEAN DEFAULT FALSE,  -- TRUE if field exists in multiple census years
    sample_only BOOLEAN DEFAULT FALSE,  -- TRUE if only collected for sample lines (e.g., 1940 lines 14, 29)
    sample_lines JSONB,  -- Which line numbers for sample: [14, 29] for 1940
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (census_year, field_path)
);

-- Indexes for common queries

-- Page indexes
CREATE INDEX IF NOT EXISTS idx_page_media ON census_page(media_id);
CREATE INDEX IF NOT EXISTS idx_page_year ON census_page(census_year);

-- Household indexes
CREATE INDEX IF NOT EXISTS idx_household_page ON census_household(page_id);

-- Entry indexes (common fields)
CREATE INDEX IF NOT EXISTS idx_entry_person ON census_entry(person_id);
CREATE INDEX IF NOT EXISTS idx_entry_event ON census_entry(event_id);
CREATE INDEX IF NOT EXISTS idx_entry_citation ON census_entry(citation_id);
CREATE INDEX IF NOT EXISTS idx_entry_status ON census_entry(review_status);
CREATE INDEX IF NOT EXISTS idx_entry_household ON census_entry(household_id);
CREATE INDEX IF NOT EXISTS idx_entry_format ON census_entry(census_format);
CREATE INDEX IF NOT EXISTS idx_entry_name ON census_entry(name);
CREATE INDEX IF NOT EXISTS idx_entry_occupation ON census_entry(occupation);
CREATE INDEX IF NOT EXISTS idx_entry_birthplace ON census_entry(birthplace);

-- Partial index for implied pre-1850 entries
CREATE INDEX IF NOT EXISTS idx_entry_implied ON census_entry(implied) WHERE implied = TRUE;

-- JSONB GIN indexes for fast queries on year-specific fields
CREATE INDEX IF NOT EXISTS idx_entry_fields_gin ON census_entry USING GIN (fields);

-- Functional indexes for common JSONB queries
CREATE INDEX IF NOT EXISTS idx_entry_relationship ON census_entry ((fields->>'relationship_to_head'));
CREATE INDEX IF NOT EXISTS idx_entry_marital_status ON census_entry ((fields->>'marital_status'));

-- Partial index for 1940 income queries (example of year-specific optimization)
CREATE INDEX IF NOT EXISTS idx_entry_income_1940
    ON census_entry ((fields->>'income_wages'))
    WHERE (fields->>'income_wages') IS NOT NULL;

-- Provenance indexes
CREATE INDEX IF NOT EXISTS idx_provenance_entry ON census_field_provenance(entry_id);
CREATE INDEX IF NOT EXISTS idx_provenance_field_path ON census_field_provenance(field_path);

-- Review log indexes
CREATE INDEX IF NOT EXISTS idx_review_entry ON census_review_log(entry_id);
CREATE INDEX IF NOT EXISTS idx_review_reviewer ON census_review_log(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_review_created ON census_review_log(created_at);

-- Field metadata indexes
CREATE INDEX IF NOT EXISTS idx_metadata_year ON census_field_metadata(census_year);
CREATE INDEX IF NOT EXISTS idx_metadata_field_path ON census_field_metadata(field_path);
CREATE INDEX IF NOT EXISTS idx_metadata_common ON census_field_metadata(common_across_years) WHERE common_across_years = TRUE;
CREATE INDEX IF NOT EXISTS idx_metadata_sample ON census_field_metadata(sample_only) WHERE sample_only = TRUE;
"""
