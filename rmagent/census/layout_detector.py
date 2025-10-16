"""
Census-specific layout detection using column templates.

Uses census field metadata to map detected table regions to known census columns.
This heuristic approach works better than blind ML detection for standardized forms.
"""

import cv2
import numpy as np
from dataclasses import dataclass
from typing import List, Tuple, Optional

from rmagent.census.models.schema import CensusFieldMetadata
from rmagent.config.census_years import CENSUS_YEAR_CONFIGS


@dataclass
class TableCell:
    """A detected cell in the census table."""

    x: int
    y: int
    width: int
    height: int
    field_name: Optional[str] = None
    column_number: Optional[int] = None

    @property
    def x2(self) -> int:
        return self.x + self.width

    @property
    def y2(self) -> int:
        return self.y + self.height

    @property
    def center_x(self) -> int:
        return self.x + self.width // 2

    @property
    def center_y(self) -> int:
        return self.y + self.height // 2


@dataclass
class ColumnTemplate:
    """Expected column position and field mapping."""

    field_name: str
    column_number: int
    min_x_ratio: float  # Position as ratio of image width (0.0-1.0)
    max_x_ratio: float
    expected_width_ratio: float  # Expected width as ratio of image width


class CensusLayoutDetector:
    """
    Detect census table layout using column templates and heuristics.

    Strategy:
    1. Detect horizontal lines to find row boundaries
    2. Use census field metadata to create column templates
    3. Map detected regions to known census fields
    4. Extract cells at row/column intersections
    """

    def __init__(self, census_year: int):
        self.census_year = census_year
        self.year_config = CENSUS_YEAR_CONFIGS.get(census_year)
        if not self.year_config:
            raise ValueError(f"No configuration for census year {census_year}")

        self.field_metadata = self.year_config.fields

    def detect_layout(self, image: np.ndarray) -> List[TableCell]:
        """
        Detect census table layout and return cells.

        Args:
            image: OpenCV image (BGR or grayscale)

        Returns:
            List of TableCell objects with field names assigned
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        img_height, img_width = gray.shape

        # Step 1: Detect horizontal lines (rows)
        row_positions = self._detect_rows(gray)

        # Step 2: Build column templates from field metadata
        column_templates = self._build_column_templates(img_width)

        # Step 3: Extract cells at row/column intersections
        cells = self._extract_cells(row_positions, column_templates, img_height, img_width)

        return cells

    def _detect_rows(self, gray: np.ndarray) -> List[int]:
        """
        Detect horizontal row boundaries using morphological operations.

        Returns Y-coordinates of row separators.
        """
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        # Detect edges
        edges = cv2.Canny(thresh, 50, 150, apertureSize=3)

        # Detect horizontal lines using Hough transform
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=200,
            minLineLength=gray.shape[1] * 0.4,  # At least 40% of image width
            maxLineGap=100,
        )

        # Extract Y positions of horizontal lines
        y_positions = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                # Check if line is approximately horizontal
                if abs(y2 - y1) < 10:
                    y_pos = (y1 + y2) // 2
                    y_positions.append(y_pos)

        # Cluster nearby lines (merge within 15 pixels)
        y_positions = self._cluster_positions(y_positions, min_gap=15)

        # Filter out lines that are too close to top/bottom (headers/footers)
        img_height = gray.shape[0]
        y_positions = [
            y for y in y_positions if img_height * 0.05 < y < img_height * 0.95
        ]

        return sorted(y_positions)

    def _cluster_positions(self, positions: List[int], min_gap: int) -> List[int]:
        """Merge positions that are within min_gap pixels of each other."""
        if not positions:
            return []

        positions = sorted(set(positions))
        clustered = [positions[0]]

        for pos in positions[1:]:
            if pos - clustered[-1] > min_gap:
                clustered.append(pos)

        return clustered

    def _build_column_templates(self, img_width: int) -> List[ColumnTemplate]:
        """
        Build column templates from census field metadata.

        Uses empirical ratios based on 1940 census column widths.
        For a proper implementation, these would be measured from sample images.
        """
        # For 1940 census, we'll use approximate column positions
        # These are estimated based on standard 1940 census form layout

        # Simplified template: divide image into regions based on field groups
        templates = []

        # Name column (typically 20-25% of image width, starting around 5%)
        templates.append(
            ColumnTemplate("name", 7, 0.05, 0.25, 0.20)
        )

        # Relation column (narrow, ~3%)
        templates.append(
            ColumnTemplate("relation", 8, 0.25, 0.28, 0.03)
        )

        # Sex column (very narrow, ~2%)
        templates.append(
            ColumnTemplate("sex", 9, 0.28, 0.30, 0.02)
        )

        # Race column (narrow, ~3%)
        templates.append(
            ColumnTemplate("race", 10, 0.30, 0.33, 0.03)
        )

        # Age column (narrow, ~2%)
        templates.append(
            ColumnTemplate("age", 11, 0.33, 0.35, 0.02)
        )

        # Birthplace column (~8%)
        templates.append(
            ColumnTemplate("birthplace", 13, 0.37, 0.45, 0.08)
        )

        # Occupation column (~10%)
        templates.append(
            ColumnTemplate("occupation", 17, 0.55, 0.65, 0.10)
        )

        # NOTE: This is a simplified template with only the most common fields.
        # A full implementation would include all 40 fields with measured ratios.

        return templates

    def _extract_cells(
        self,
        row_positions: List[int],
        column_templates: List[ColumnTemplate],
        img_height: int,
        img_width: int,
    ) -> List[TableCell]:
        """
        Extract cells at row/column intersections.

        Args:
            row_positions: Y-coordinates of row separators
            column_templates: Column position templates
            img_height: Image height in pixels
            img_width: Image width in pixels

        Returns:
            List of TableCell objects
        """
        cells = []

        # Create row boundaries (spaces between horizontal lines)
        row_boundaries = []
        for i in range(len(row_positions) - 1):
            y_start = row_positions[i]
            y_end = row_positions[i + 1]
            height = y_end - y_start

            # Filter out very small rows (likely noise)
            if height > 20:
                row_boundaries.append((y_start, y_end, height))

        # Extract cells at each row/column intersection
        for row_y, row_y2, row_h in row_boundaries:
            for template in column_templates:
                # Calculate column position from template ratios
                col_x = int(template.min_x_ratio * img_width)
                col_x2 = int(template.max_x_ratio * img_width)
                col_w = col_x2 - col_x

                # Create cell
                cell = TableCell(
                    x=col_x,
                    y=row_y,
                    width=col_w,
                    height=row_h,
                    field_name=template.field_name,
                    column_number=template.column_number,
                )
                cells.append(cell)

        return cells
