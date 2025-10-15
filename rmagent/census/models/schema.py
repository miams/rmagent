"""
Census sidecar database schema models.

Defines the structure for the census extraction sidecar SQLite database.
This database stores extracted census data, OCR provenance, and review decisions
without modifying the RootsMagic database.
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


class CensusEntry(BaseModel):
    """Represents a single person entry in a census record.

    This table stores only metadata about the entry. Actual census field values
    are stored in CensusFieldValue table to accommodate varying census year schemas.
    """

    entry_id: Optional[int] = None  # Primary key
    household_id: int  # Foreign key to CensusHousehold
    person_id: Optional[int] = None  # Matched RootsMagic PersonID
    match_confidence: Optional[float] = None  # 0.0-1.0 matching score
    line_number: Optional[int] = None

    # Review tracking
    review_status: ReviewStatus = ReviewStatus.PENDING
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CensusFieldValue(BaseModel):
    """Stores actual census field values for entries.

    This flexible schema accommodates different census year structures.
    Each field from the census record gets its own row with provenance.
    """

    value_id: Optional[int] = None  # Primary key
    entry_id: int  # Foreign key to CensusEntry
    field_name: str  # e.g., "name", "age", "occupation", "income_1940"
    field_value: Optional[str] = None  # String representation of value
    field_type: str = "text"  # "text", "integer", "date" for parsing hints

    # Link to provenance (OCR metadata)
    provenance_id: Optional[int] = None  # Foreign key to CensusFieldProvenance

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CensusFieldProvenance(BaseModel):
    """Provenance tracking for individual census fields.

    Stores OCR metadata and image coordinates for each extracted field.
    Linked from CensusFieldValue via provenance_id.
    """

    provenance_id: Optional[int] = None  # Primary key

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
    """

    log_id: Optional[int] = None  # Primary key
    entry_id: int  # Foreign key to CensusEntry
    value_id: Optional[int] = None  # Foreign key to CensusFieldValue (if field-level edit)
    reviewer_id: str  # Username/ID of reviewer
    action: str  # "approve", "correct", "flag", "skip"
    field_name: Optional[str] = None  # Specific field edited (if applicable)
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# SQLite schema definition
SIDECAR_SCHEMA = """
-- Census page: image metadata
CREATE TABLE IF NOT EXISTS census_page (
    page_id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id INTEGER NOT NULL,
    person_id INTEGER,
    census_year INTEGER NOT NULL,
    image_path TEXT NOT NULL,
    processed_path TEXT,
    layout_metadata TEXT,  -- JSON: cell coordinates, row/col structure
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(media_id)
);

-- Household: group of people living together
CREATE TABLE IF NOT EXISTS census_household (
    household_id INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id INTEGER NOT NULL,
    dwelling_number TEXT,
    family_number TEXT,
    address TEXT,
    enumeration_district TEXT,
    sheet_number TEXT,
    line_number_start INTEGER,
    line_number_end INTEGER,
    prev_page_id INTEGER,  -- Cross-page household tracking
    next_page_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (page_id) REFERENCES census_page(page_id)
);

-- Entry: single person in census (metadata only)
CREATE TABLE IF NOT EXISTS census_entry (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id INTEGER NOT NULL,
    person_id INTEGER,  -- Matched RootsMagic PersonID
    match_confidence REAL,  -- 0.0-1.0
    line_number INTEGER,

    -- Review tracking
    review_status TEXT DEFAULT 'pending',
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (household_id) REFERENCES census_household(household_id)
);

-- Field values: actual census data (flexible schema)
CREATE TABLE IF NOT EXISTS census_field_value (
    value_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    field_name TEXT NOT NULL,  -- e.g., "name", "age", "occupation", "income_1940"
    field_value TEXT,  -- String representation
    field_type TEXT DEFAULT 'text',  -- 'text', 'integer', 'date'
    provenance_id INTEGER,  -- Link to OCR metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entry_id) REFERENCES census_entry(entry_id),
    FOREIGN KEY (provenance_id) REFERENCES census_field_provenance(provenance_id)
);

-- Provenance: OCR metadata for each field
CREATE TABLE IF NOT EXISTS census_field_provenance (
    provenance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ocr_model TEXT NOT NULL,  -- 'tesseract', 'kraken', 'calamari', 'vision_llm'
    ocr_confidence REAL,  -- 0.0-1.0
    raw_ocr_text TEXT,  -- Before normalization
    cell_coordinates TEXT,  -- JSON: {x, y, width, height}
    cell_image_path TEXT,  -- Path to cropped cell snippet
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Review log: audit trail for all reviewer actions
CREATE TABLE IF NOT EXISTS census_review_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    value_id INTEGER,  -- Specific field edited (if applicable)
    reviewer_id TEXT NOT NULL,
    action TEXT NOT NULL,  -- 'approve', 'correct', 'flag', 'skip'
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entry_id) REFERENCES census_entry(entry_id),
    FOREIGN KEY (value_id) REFERENCES census_field_value(value_id)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_page_media ON census_page(media_id);
CREATE INDEX IF NOT EXISTS idx_page_year ON census_page(census_year);
CREATE INDEX IF NOT EXISTS idx_household_page ON census_household(page_id);
CREATE INDEX IF NOT EXISTS idx_entry_person ON census_entry(person_id);
CREATE INDEX IF NOT EXISTS idx_entry_status ON census_entry(review_status);
CREATE INDEX IF NOT EXISTS idx_entry_household ON census_entry(household_id);
CREATE INDEX IF NOT EXISTS idx_field_value_entry ON census_field_value(entry_id);
CREATE INDEX IF NOT EXISTS idx_field_value_name ON census_field_value(field_name);
CREATE INDEX IF NOT EXISTS idx_field_value_entry_name ON census_field_value(entry_id, field_name);
CREATE INDEX IF NOT EXISTS idx_review_entry ON census_review_log(entry_id);
CREATE INDEX IF NOT EXISTS idx_review_value ON census_review_log(value_id);
"""
