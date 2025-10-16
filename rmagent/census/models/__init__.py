"""Census data models.

Hybrid schema design with PostgreSQL JSONB:
- Common fields (name, age, sex, race, birthplace, occupation) as columns
- Year-specific fields in JSONB for flexibility
- OCR provenance tracking with field paths
"""

from .schema import (
    SIDECAR_SCHEMA,
    CensusEntry,
    CensusFieldProvenance,
    CensusHousehold,
    CensusPage,
    CensusReviewLog,
    OCRModel,
    ReviewStatus,
)

__all__ = [
    "CensusPage",
    "CensusHousehold",
    "CensusEntry",
    "CensusFieldProvenance",
    "CensusReviewLog",
    "OCRModel",
    "ReviewStatus",
    "SIDECAR_SCHEMA",
]
