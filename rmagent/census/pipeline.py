"""
Census extraction pipeline orchestrator.

Coordinates the end-to-end workflow:
1. Image preprocessing (deskew, denoise, CLAHE)
2. Layout detection (table grid, cell boundaries)
3. OCR extraction (Tesseract with confidence scoring)
4. Person matching (fuzzy match to RootsMagic PersonID)
5. Database insertion (census entries + provenance)
6. Progress tracking and error handling
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import cv2
import numpy as np
from psycopg2.extras import Json

from rmagent.census.catalog import CensusMediaCatalog
from rmagent.census.pipelines.matching import match_census_entry
from rmagent.census.pipelines.ocr import TesseractOCREngine
from rmagent.census.pipelines.preprocessing import (
    detect_census_layout,
    preprocess_census_image,
)
from rmagent.census.sidecar import CensusSidecarDB
from rmagent.config.config import load_app_config

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Results from processing a single census image."""

    image_path: str
    census_year: int
    success: bool
    error_message: Optional[str] = None

    # Processing metrics
    preprocessing_time: float = 0.0
    layout_detection_time: float = 0.0
    ocr_time: float = 0.0
    matching_time: float = 0.0
    database_time: float = 0.0
    total_time: float = 0.0

    # Extraction metrics
    num_cells_detected: int = 0
    num_cells_extracted: int = 0
    num_persons_matched: int = 0
    num_entries_created: int = 0

    # Quality metrics
    avg_ocr_confidence: float = 0.0
    avg_match_confidence: float = 0.0
    low_confidence_fields: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        """Human-readable summary."""
        if not self.success:
            return f"❌ {Path(self.image_path).name}: {self.error_message}"

        return (
            f"✅ {Path(self.image_path).name}: "
            f"{self.num_entries_created} entries created "
            f"({self.num_cells_extracted} cells, "
            f"{self.num_persons_matched} matched, "
            f"{self.total_time:.1f}s)"
        )


@dataclass
class BatchResult:
    """Results from batch processing multiple images."""

    total_images: int
    successful: int
    failed: int
    total_entries_created: int
    total_time: float

    results: list[ProcessingResult] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Percentage of successful images."""
        if self.total_images == 0:
            return 0.0
        return (self.successful / self.total_images) * 100

    def summary(self) -> str:
        """Generate batch summary."""
        return (
            f"\n{'='*70}\n"
            f"Batch Processing Complete\n"
            f"{'='*70}\n"
            f"Total Images:  {self.total_images}\n"
            f"Successful:    {self.successful} ({self.success_rate:.1f}%)\n"
            f"Failed:        {self.failed}\n"
            f"Total Entries: {self.total_entries_created}\n"
            f"Total Time:    {self.total_time:.1f}s ({self.total_time/60:.1f}m)\n"
            f"Avg Time/Image: {self.total_time/self.total_images if self.total_images else 0:.1f}s\n"
            f"{'='*70}\n"
        )


class CensusPipeline:
    """End-to-end census extraction pipeline."""

    def __init__(
        self,
        rm_database_path: Optional[Path] = None,
        census_db_url: Optional[str] = None,
        media_root: Optional[Path] = None,
    ):
        """
        Initialize census pipeline.

        Args:
            rm_database_path: Path to RootsMagic database (optional, uses config)
            census_db_url: PostgreSQL connection string (optional, uses config)
            media_root: Root directory for census images (optional, uses config)
        """
        # Load configuration
        self.config = load_app_config(require_llm_credentials=False)

        # Database paths
        self.rm_db_path = rm_database_path or self.config.database.database_path
        self.census_db_url = census_db_url or self.config.census.db_url
        self.media_root = media_root or self.config.database.media_root_directory

        # Initialize components
        self.sidecar_db = CensusSidecarDB(self.census_db_url)
        self.ocr_engine = TesseractOCREngine(language="eng", psm=3)

        # Processing directories
        self.processed_dir = Path("data/census/images/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Census pipeline initialized")
        logger.info(f"  RM Database: {self.rm_db_path}")
        logger.info(f"  Census DB: {self.census_db_url}")
        logger.info(f"  Media Root: {self.media_root}")

    def resolve_image_path(self, image_path_or_relative: str) -> Path:
        """
        Resolve image path from database or absolute path.

        Args:
            image_path_or_relative: Absolute path or relative path from catalog

        Returns:
            Absolute Path to image file

        Raises:
            FileNotFoundError: If image doesn't exist
        """
        path = Path(image_path_or_relative)

        # If already absolute and exists, return it
        if path.is_absolute() and path.exists():
            return path

        # If media_root configured, try relative to that
        if self.media_root:
            # Strip "images/" prefix if present (from catalog)
            path_str = str(path).replace("images/", "").replace("images\\", "")
            # Convert backslashes to forward slashes
            path_str = path_str.replace("\\", "/")
            full_path = self.media_root / path_str
            if full_path.exists():
                return full_path

        # Try as-is
        if path.exists():
            return path

        raise FileNotFoundError(f"Census image not found: {image_path_or_relative}")

    def process_image(
        self, image_path: str | Path, census_year: int, media_id: Optional[int] = None
    ) -> ProcessingResult:
        """
        Process a single census image through the full pipeline.

        Args:
            image_path: Path to census image
            census_year: Census year (e.g., 1940)
            media_id: RootsMagic MediaID (optional, for linking)

        Returns:
            ProcessingResult with metrics and status
        """
        start_time = datetime.now()
        result = ProcessingResult(
            image_path=str(image_path), census_year=census_year, success=False
        )

        try:
            # Resolve image path
            image_path = self.resolve_image_path(str(image_path))
            logger.info(f"Processing: {image_path.name}")

            # Connect to databases
            if not self.sidecar_db.conn:
                self.sidecar_db.connect()

            # Stage 1: Preprocessing
            step_start = datetime.now()
            processed_path = self.processed_dir / f"{image_path.stem}_processed.jpg"
            preprocess_census_image(str(image_path), str(processed_path))
            result.preprocessing_time = (datetime.now() - step_start).total_seconds()
            logger.info(f"  ✓ Preprocessing: {result.preprocessing_time:.2f}s")

            # Stage 2: Layout Detection
            step_start = datetime.now()
            layout = detect_census_layout(str(processed_path), census_year=census_year)
            result.num_cells_detected = len(layout.cells) if layout else 0
            result.layout_detection_time = (datetime.now() - step_start).total_seconds()
            logger.info(
                f"  ✓ Layout: {result.num_cells_detected} cells in {result.layout_detection_time:.2f}s"
            )

            if not layout or not layout.cells:
                raise ValueError("No table layout detected in image")

            # Stage 3: OCR Extraction
            step_start = datetime.now()

            # For 1940 census, map common columns
            # Column mapping based on 1940 census metadata
            field_mappings = {
                0: "dwelling_number",  # Column 1-2
                1: "family_number",  # Column 3-4
                2: "street_address",  # Column 5-6
                3: "name",  # Column 7
                4: "relationship_to_head",  # Column 8
                5: "sex",  # Column 9
                6: "race",  # Column 10
                7: "age",  # Column 11
                8: "marital_status",  # Column 12
            }

            # Extract cells by row
            image = cv2.imread(str(processed_path))
            rows_data = self.ocr_engine.extract_by_row(image, layout, field_mappings)

            total_confidence = 0
            total_fields = 0
            for row_id, cells in rows_data.items():
                for cell in cells:
                    if cell.ocr_result.confidence:
                        total_confidence += cell.ocr_result.confidence
                        total_fields += 1

            result.num_cells_extracted = total_fields
            result.avg_ocr_confidence = (
                total_confidence / total_fields if total_fields > 0 else 0.0
            )
            result.ocr_time = (datetime.now() - step_start).total_seconds()
            logger.info(
                f"  ✓ OCR: {result.num_cells_extracted} fields extracted "
                f"(avg conf: {result.avg_ocr_confidence:.2f}) in {result.ocr_time:.2f}s"
            )

            # Stage 4: Person Matching & Database Insertion
            step_start = datetime.now()

            # First, ensure page record exists
            page_id = self._create_page_record(
                media_id=media_id,
                census_year=census_year,
                image_path=str(image_path),
                processed_path=str(processed_path),
                layout=layout,
            )

            # Create a default household for all entries on this page
            # (In future, we can group by dwelling/family number)
            household_id = self._create_household(page_id, census_year)

            # Process each row as a potential person
            match_confidences = []
            for row_id, cells in rows_data.items():
                # Extract basic fields from this row
                row_fields = {}
                for cell in cells:
                    if cell.field_name:
                        row_fields[cell.field_name] = cell.ocr_result.text

                # Skip if no name
                if "name" not in row_fields or not row_fields["name"].strip():
                    continue

                # Try to match person
                match_result = match_census_entry(
                    name=row_fields.get("name", ""),
                    rm_db_path=str(self.rm_db_path),
                    age=self._parse_age(row_fields.get("age")),
                    census_year=census_year,
                    birthplace=None,  # Not extracted yet
                )

                person_id = None
                match_confidence = 0.0
                if match_result.best_match:
                    person_id = match_result.best_match.person_id
                    match_confidence = match_result.confidence
                    match_confidences.append(match_confidence)
                    result.num_persons_matched += 1

                # Create census entry
                entry_id = self._create_entry(
                    household_id=household_id,
                    person_id=person_id,
                    line_number=row_id,
                    row_fields=row_fields,
                    match_confidence=match_confidence,
                )

                result.num_entries_created += 1

                # Create provenance for each field
                for cell in cells:
                    if cell.field_name and entry_id:
                        self._create_provenance(entry_id, cell)

            result.avg_match_confidence = (
                sum(match_confidences) / len(match_confidences)
                if match_confidences
                else 0.0
            )
            result.database_time = (datetime.now() - step_start).total_seconds()
            logger.info(
                f"  ✓ Database: {result.num_entries_created} entries, "
                f"{result.num_persons_matched} matched "
                f"(avg conf: {result.avg_match_confidence:.2f}) in {result.database_time:.2f}s"
            )

            # Mark page as complete
            self._update_page_status(page_id, "complete")

            # Success!
            result.success = True
            result.total_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"✅ Completed: {image_path.name} ({result.total_time:.2f}s)")

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.total_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Failed: {image_path} - {e}", exc_info=True)

        return result

    def process_batch(
        self,
        image_paths: list[str | Path],
        census_year: int,
        show_progress: bool = True,
    ) -> BatchResult:
        """
        Process multiple census images.

        Args:
            image_paths: List of image paths to process
            census_year: Census year for all images
            show_progress: Print progress during processing

        Returns:
            BatchResult with aggregated metrics
        """
        start_time = datetime.now()
        results = []

        logger.info(f"Starting batch processing: {len(image_paths)} images")

        for idx, image_path in enumerate(image_paths, 1):
            if show_progress:
                print(f"\n[{idx}/{len(image_paths)}] Processing: {Path(image_path).name}")

            result = self.process_image(image_path, census_year)
            results.append(result)

            if show_progress:
                print(f"  {result}")

        total_time = (datetime.now() - start_time).total_seconds()

        batch_result = BatchResult(
            total_images=len(image_paths),
            successful=sum(1 for r in results if r.success),
            failed=sum(1 for r in results if not r.success),
            total_entries_created=sum(r.num_entries_created for r in results),
            total_time=total_time,
            results=results,
        )

        if show_progress:
            print(batch_result.summary())

        return batch_result

    def _parse_age(self, age_str: Optional[str]) -> Optional[int]:
        """Parse age from OCR text."""
        if not age_str:
            return None
        try:
            # Remove common OCR artifacts
            cleaned = age_str.strip().replace("O", "0").replace("l", "1")
            return int(cleaned)
        except ValueError:
            return None

    def _create_page_record(
        self,
        media_id: Optional[int],
        census_year: int,
        image_path: str,
        processed_path: str,
        layout: Any,
    ) -> int:
        """Create or update census_page record."""
        # Serialize layout metadata
        layout_metadata = {
            "num_rows": layout.num_rows,
            "num_cols": layout.num_cols,
            "cells": [
                {
                    "row": cell.row,
                    "col": cell.col,
                    "bbox": {
                        "x": cell.bbox[0],
                        "y": cell.bbox[1],
                        "width": cell.bbox[2],
                        "height": cell.bbox[3],
                    },
                }
                for cell in layout.cells
            ],
        }

        # Check if page already exists
        if media_id:
            existing = self.sidecar_db.execute_one(
                "SELECT page_id FROM census_page WHERE media_id = %s", (media_id,)
            )
            if existing:
                # Update existing
                self.sidecar_db.execute(
                    """
                    UPDATE census_page SET
                        census_year = %s,
                        processed_path = %s,
                        layout_metadata = %s,
                        processing_status = 'processing'
                    WHERE media_id = %s
                    """,
                    (census_year, processed_path, Json(layout_metadata), media_id),
                )
                return existing["page_id"]

        # Insert new page
        result = self.sidecar_db.execute_one(
            """
            INSERT INTO census_page
                (media_id, census_year, image_path, processed_path, layout_metadata, processing_status)
            VALUES (%s, %s, %s, %s, %s, 'processing')
            RETURNING page_id
            """,
            (media_id, census_year, image_path, processed_path, Json(layout_metadata)),
        )
        return result["page_id"]

    def _update_page_status(self, page_id: int, status: str, error: Optional[str] = None):
        """Update page processing status."""
        self.sidecar_db.execute(
            """
            UPDATE census_page SET
                processing_status = %s,
                error_message = %s,
                ocr_completed_at = CASE WHEN %s = 'complete' THEN CURRENT_TIMESTAMP ELSE ocr_completed_at END
            WHERE page_id = %s
            """,
            (status, error, status, page_id),
        )

    def _create_household(self, page_id: int, census_year: int) -> int:
        """Create or get household for this page."""
        # For now, create one household per page
        # In future, we can group by dwelling/family number
        result = self.sidecar_db.execute_one(
            """
            INSERT INTO census_household
                (page_id, dwelling_number, family_number, address)
            VALUES (%s, NULL, NULL, NULL)
            RETURNING household_id
            """,
            (page_id,),
        )
        return result["household_id"]

    def _create_entry(
        self,
        household_id: int,
        person_id: Optional[int],
        line_number: int,
        row_fields: dict[str, str],
        match_confidence: float,
    ) -> int:
        """Create census_entry record."""
        # Common fields
        name = row_fields.get("name", "").strip()
        age = self._parse_age(row_fields.get("age"))
        sex = row_fields.get("sex", "").strip()[:1].upper() if row_fields.get("sex") else None
        race = row_fields.get("race", "").strip()

        # JSONB fields (year-specific)
        fields_jsonb = {}
        for field_name in [
            "relationship_to_head",
            "marital_status",
            "dwelling_number",
            "family_number",
            "street_address",
        ]:
            if field_name in row_fields and row_fields[field_name].strip():
                fields_jsonb[field_name] = row_fields[field_name].strip()

        result = self.sidecar_db.execute_one(
            """
            INSERT INTO census_entry
                (household_id, person_id, line_number, name, age, sex, race, fields, match_confidence)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING entry_id
            """,
            (
                household_id,
                person_id,
                line_number,
                name if name else None,
                age,
                sex,
                race if race else None,
                Json(fields_jsonb),
                match_confidence,
            ),
        )
        return result["entry_id"]

    def _create_provenance(self, entry_id: int, cell: Any):
        """Create field provenance record."""
        # Serialize bbox (cell.cell is the CellRegion, cell.cell.bbox is the bounding box)
        bbox_json = {
            "x": cell.cell.bbox[0],
            "y": cell.cell.bbox[1],
            "width": cell.cell.bbox[2],
            "height": cell.cell.bbox[3],
        }

        field_path = cell.field_name
        if field_path not in ["name", "age", "sex", "race", "birthplace", "occupation"]:
            field_path = f"fields.{field_path}"

        self.sidecar_db.execute(
            """
            INSERT INTO census_field_provenance
                (entry_id, field_path, ocr_model, ocr_confidence, raw_ocr_text, cell_coordinates)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                entry_id,
                field_path,
                "tesseract",
                cell.ocr_result.confidence,
                cell.ocr_result.raw_text,
                Json(bbox_json),
            ),
        )

    def close(self):
        """Close database connections."""
        if self.sidecar_db:
            self.sidecar_db.close()


def process_single_image(
    image_path: str, census_year: int, rm_db_path: Optional[str] = None
) -> ProcessingResult:
    """
    Convenience function to process a single image.

    Args:
        image_path: Path to census image
        census_year: Census year (e.g., 1940)
        rm_db_path: Optional path to RootsMagic database

    Returns:
        ProcessingResult with metrics

    Example:
        >>> result = process_single_image("census_1940.jpg", 1940)
        >>> print(result)
        ✅ census_1940.jpg: 7 entries created (45 cells, 6 matched, 12.3s)
    """
    pipeline = CensusPipeline(rm_database_path=Path(rm_db_path) if rm_db_path else None)
    try:
        return pipeline.process_image(image_path, census_year)
    finally:
        pipeline.close()


def process_batch_images(
    image_paths: list[str], census_year: int, rm_db_path: Optional[str] = None
) -> BatchResult:
    """
    Convenience function to process multiple images.

    Args:
        image_paths: List of image paths
        census_year: Census year for all images
        rm_db_path: Optional path to RootsMagic database

    Returns:
        BatchResult with aggregated metrics

    Example:
        >>> images = ["img1.jpg", "img2.jpg", "img3.jpg"]
        >>> result = process_batch_images(images, 1940)
        >>> print(result.summary())
    """
    pipeline = CensusPipeline(rm_database_path=Path(rm_db_path) if rm_db_path else None)
    try:
        return pipeline.process_batch(image_paths, census_year)
    finally:
        pipeline.close()


__all__ = [
    "CensusPipeline",
    "ProcessingResult",
    "BatchResult",
    "process_single_image",
    "process_batch_images",
]
