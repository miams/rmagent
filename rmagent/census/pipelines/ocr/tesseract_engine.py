"""
Tesseract OCR engine for census text extraction.

Provides OCR extraction with confidence scoring and provenance tracking
for census images. Handles both full-page and cell-level extraction.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import pytesseract
from PIL import Image

from rmagent.census.models.schema import OCRModel
from rmagent.census.pipelines.preprocessing.layout_detector import (
    CellRegion,
    TableLayout,
)

logger = logging.getLogger(__name__)


@dataclass
class OCRResult:
    """Result of OCR extraction."""

    text: str
    confidence: float  # 0.0-1.0
    raw_text: str  # Before normalization
    bbox: Optional[Tuple[int, int, int, int]] = None  # x, y, width, height
    model: OCRModel = OCRModel.TESSERACT

    def __str__(self) -> str:
        return f"{self.text} ({self.confidence:.2f})"


@dataclass
class CellOCRResult:
    """OCR result for a table cell."""

    cell: CellRegion
    ocr_result: OCRResult
    field_name: Optional[str] = None  # e.g., "name", "age", "occupation"


class TesseractOCREngine:
    """Tesseract-based OCR extraction for census images."""

    def __init__(
        self,
        language: str = "eng",
        psm: int = 6,  # Page segmentation mode
        oem: int = 3,  # OCR Engine mode (LSTM)
        tesseract_path: Optional[str] = None,
    ):
        """
        Initialize Tesseract OCR engine.

        Args:
            language: Tesseract language code (e.g., 'eng', 'fra')
            psm: Page segmentation mode (6=uniform block of text)
            oem: OCR engine mode (3=default, 1=LSTM only)
            tesseract_path: Optional custom Tesseract executable path

        Page Segmentation Modes (psm):
            0 = Orientation and script detection (OSD) only
            1 = Automatic page segmentation with OSD
            3 = Fully automatic page segmentation, but no OSD (default)
            6 = Assume a single uniform block of text
            7 = Treat the image as a single text line
            11 = Sparse text. Find as much text as possible
            13 = Raw line. Treat the image as a single text line
        """
        self.language = language
        self.psm = psm
        self.oem = oem

        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path

        # Verify Tesseract is available
        try:
            version = pytesseract.get_tesseract_version()
            logger.info(f"Initialized Tesseract OCR v{version}")
        except Exception as e:
            raise RuntimeError(f"Tesseract not found: {e}") from e

    def extract_text(
        self,
        image: np.ndarray | Image.Image,
        psm: Optional[int] = None,
    ) -> OCRResult:
        """
        Extract text from image using Tesseract.

        Args:
            image: Input image (numpy array or PIL Image)
            psm: Override page segmentation mode for this extraction

        Returns:
            OCRResult with extracted text and confidence
        """
        # Convert to PIL Image if needed
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)

        # Build Tesseract config
        config = self._build_tesseract_config(psm or self.psm)

        # Extract text with confidence
        data = pytesseract.image_to_data(
            image, lang=self.language, config=config, output_type=pytesseract.Output.DICT
        )

        # Combine words and calculate average confidence
        words = []
        confidences = []

        for i, text in enumerate(data["text"]):
            if text.strip():
                words.append(text)
                conf = float(data["conf"][i])
                if conf >= 0:  # -1 means no confidence
                    confidences.append(conf)

        raw_text = " ".join(words)
        normalized_text = self._normalize_text(raw_text)

        # Calculate average confidence (0-100 scale to 0-1)
        avg_confidence = (
            sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
        )

        logger.debug(
            f"Extracted text: '{normalized_text[:50]}...' (confidence: {avg_confidence:.2f})"
        )

        return OCRResult(
            text=normalized_text,
            confidence=avg_confidence,
            raw_text=raw_text,
            model=OCRModel.TESSERACT,
        )

    def extract_cell(
        self,
        image: np.ndarray,
        cell: CellRegion,
        field_name: Optional[str] = None,
    ) -> CellOCRResult:
        """
        Extract text from a specific table cell.

        Args:
            image: Full census image
            cell: Cell region to extract
            field_name: Optional field name for this cell

        Returns:
            CellOCRResult with text and metadata
        """
        # Crop cell from image
        cell_image = image[
            cell.y : cell.y + cell.height, cell.x : cell.x + cell.width
        ]

        # Use single-line PSM for most census cells
        psm = 7 if cell.height < 50 else 6

        # Extract text
        ocr_result = self.extract_text(cell_image, psm=psm)
        ocr_result.bbox = cell.bbox

        return CellOCRResult(
            cell=cell, ocr_result=ocr_result, field_name=field_name
        )

    def extract_table_cells(
        self,
        image: np.ndarray,
        layout: TableLayout,
        field_mappings: Optional[Dict[int, str]] = None,
    ) -> List[CellOCRResult]:
        """
        Extract text from all cells in a table layout.

        Args:
            image: Full census image
            layout: Detected table layout
            field_mappings: Optional dict mapping column index to field name

        Returns:
            List of CellOCRResult for each cell

        Example:
            >>> field_mappings = {0: "dwelling_number", 1: "family_number", 2: "name"}
            >>> results = engine.extract_table_cells(image, layout, field_mappings)
        """
        results = []

        for cell in layout.cells:
            field_name = field_mappings.get(cell.col) if field_mappings else None
            cell_result = self.extract_cell(image, cell, field_name)
            results.append(cell_result)

        logger.info(f"Extracted text from {len(results)} cells")
        return results

    def extract_by_row(
        self,
        image: np.ndarray,
        layout: TableLayout,
        field_mappings: Optional[Dict[int, str]] = None,
    ) -> Dict[int, List[CellOCRResult]]:
        """
        Extract cells organized by row.

        Args:
            image: Full census image
            layout: Detected table layout
            field_mappings: Optional dict mapping column index to field name

        Returns:
            Dict mapping row index to list of CellOCRResults
        """
        all_results = self.extract_table_cells(image, layout, field_mappings)

        # Group by row
        by_row: Dict[int, List[CellOCRResult]] = {}
        for result in all_results:
            row_idx = result.cell.row
            if row_idx not in by_row:
                by_row[row_idx] = []
            by_row[row_idx].append(result)

        # Sort cells within each row by column
        for row_results in by_row.values():
            row_results.sort(key=lambda r: r.cell.col)

        return by_row

    def _build_tesseract_config(self, psm: int) -> str:
        """Build Tesseract configuration string."""
        return f"--oem {self.oem} --psm {psm}"

    def _normalize_text(self, text: str) -> str:
        """
        Normalize extracted text.

        Handles common OCR issues:
        - Extra whitespace
        - Common character misreads (e.g., 'l' vs '1', 'O' vs '0')

        Args:
            text: Raw OCR text

        Returns:
            Normalized text
        """
        # Remove extra whitespace
        text = " ".join(text.split())

        # Basic cleanup
        text = text.strip()

        # Fix common OCR errors in numbers
        # (Conservative - only fix obvious cases)
        # Example: "l23" -> "123" (but not "Illinois")
        text = re.sub(r"\bl(\d)", r"1\1", text)  # Leading l before digit
        text = re.sub(r"(\d)l\b", r"\g<1>1", text)  # Trailing l after digit

        return text


def extract_census_text(
    image: np.ndarray | str | Path,
    layout: Optional[TableLayout] = None,
    **options,
) -> List[OCRResult] | List[CellOCRResult]:
    """
    Convenience function to extract text from census image.

    Args:
        image: Input image (array or path)
        layout: Optional table layout for cell-by-cell extraction
        **options: OCR engine options (language, psm, oem)

    Returns:
        List of OCRResult (if no layout) or CellOCRResult (if layout provided)

    Example:
        >>> # Full page extraction
        >>> results = extract_census_text("census.jpg", psm=3)
        >>> print(results[0].text)

        >>> # Cell-by-cell extraction
        >>> from rmagent.census.pipelines.preprocessing import detect_census_layout
        >>> layout = detect_census_layout("census.jpg")
        >>> results = extract_census_text("census.jpg", layout=layout)
    """
    engine = TesseractOCREngine(**options)

    # Load image if path provided
    if isinstance(image, (str, Path)):
        image = cv2.imread(str(image), cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"Failed to load image: {image}")

    if layout:
        # Cell-by-cell extraction
        return engine.extract_table_cells(image, layout)
    else:
        # Full page extraction
        result = engine.extract_text(image)
        return [result]
