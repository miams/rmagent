"""
Layout detection for census tables.

Detects table structures in census images, identifying rows, columns,
and individual cells for targeted OCR extraction.

Uses census-specific column templates based on field metadata
combined with row detection for reliable extraction.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CellRegion:
    """Represents a detected table cell with coordinates."""

    x: int
    y: int
    width: int
    height: int
    row: int
    col: int
    confidence: float = 1.0

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Return bounding box as (x, y, width, height)."""
        return (self.x, self.y, self.width, self.height)

    @property
    def center(self) -> Tuple[int, int]:
        """Return cell center coordinates."""
        return (self.x + self.width // 2, self.y + self.height // 2)


@dataclass
class TableLayout:
    """Represents detected table structure."""

    cells: List[CellRegion]
    num_rows: int
    num_cols: int
    table_bbox: Tuple[int, int, int, int]  # x, y, width, height

    def get_cell(self, row: int, col: int) -> Optional[CellRegion]:
        """Get cell at specific row and column."""
        for cell in self.cells:
            if cell.row == row and cell.col == col:
                return cell
        return None

    def get_row_cells(self, row: int) -> List[CellRegion]:
        """Get all cells in a specific row."""
        return [c for c in self.cells if c.row == row]

    def get_column_cells(self, col: int) -> List[CellRegion]:
        """Get all cells in a specific column."""
        return [c for c in self.cells if c.col == col]


class CensusLayoutDetector:
    """
    Census-specific table layout detector.

    Uses known census column templates combined with row detection
    for more reliable extraction than blind morphological operations.
    """

    def __init__(
        self,
        census_year: int = 1940,
        min_cell_height: int = 20,
    ):
        """
        Initialize layout detector.

        Args:
            census_year: Census year for column template (default: 1940)
            min_cell_height: Minimum height (pixels) for valid rows
        """
        self.census_year = census_year
        self.min_cell_height = min_cell_height

    def detect_layout(self, image: np.ndarray) -> Optional[TableLayout]:
        """
        Detect table layout using census-specific templates.

        Args:
            image: Input image (grayscale or BGR)

        Returns:
            TableLayout object with detected cells, or None if no table found
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        img_height, img_width = gray.shape

        # Step 1: Detect row boundaries
        row_positions = self._detect_rows(gray)

        if len(row_positions) < 2:
            logger.warning("Not enough rows detected")
            return None

        # Step 2: Build column templates from field metadata
        column_templates = self._build_column_templates(img_width)

        # Step 3: Create cells at row/column intersections
        cells = self._create_cells_from_templates(row_positions, column_templates, img_height, img_width)

        if not cells:
            logger.warning("No cells created from templates")
            return None

        # Calculate table bounds
        all_x = [c.x for c in cells]
        all_y = [c.y for c in cells]
        all_x2 = [c.x + c.width for c in cells]
        all_y2 = [c.y + c.height for c in cells]

        table_bbox = (
            min(all_x),
            min(all_y),
            max(all_x2) - min(all_x),
            max(all_y2) - min(all_y),
        )

        num_rows = max(c.row for c in cells) + 1
        num_cols = max(c.col for c in cells) + 1

        logger.info(f"Detected table: {num_rows} rows × {num_cols} columns, {len(cells)} cells")

        return TableLayout(
            cells=cells,
            num_rows=num_rows,
            num_cols=num_cols,
            table_bbox=table_bbox,
        )

    def _detect_rows(self, gray: np.ndarray) -> List[int]:
        """
        Detect horizontal row boundaries using morphological operations.

        Returns Y-coordinates of row separators (sorted top to bottom).
        """
        # Binarize image
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Create horizontal kernel to detect horizontal lines
        # Use wider kernel to detect table row separators
        kernel_length = gray.shape[1] // 20  # 5% of image width
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length, 1))

        # Detect horizontal lines using morphological operations
        horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)

        # Find contours of horizontal lines
        contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Extract Y positions from contours
        y_positions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # Only consider lines that span at least 30% of image width
            if w > gray.shape[1] * 0.3:
                # Use middle of the line
                y_pos = y + h // 2
                y_positions.append(y_pos)

        logger.debug(f"Found {len(y_positions)} horizontal line candidates before clustering")

        # Cluster nearby lines (merge within 20 pixels)
        y_positions = self._cluster_positions(y_positions, min_gap=20)

        logger.debug(f"Detected {len(y_positions)} horizontal lines after clustering")

        # Filter out lines at very top/bottom (margins)
        img_height = gray.shape[0]
        filtered_positions = [
            y for y in y_positions if img_height * 0.03 < y < img_height * 0.97
        ]

        logger.info(f"Detected {len(filtered_positions)} row separators (image height: {img_height}px, before filter: {len(y_positions)})")

        if len(filtered_positions) < 2:
            logger.warning(f"Only {len(filtered_positions)} rows detected - layout detection may fail")

        return sorted(filtered_positions)

    def _cluster_positions(self, positions: List[int], min_gap: int) -> List[int]:
        """Merge positions within min_gap pixels."""
        if not positions:
            return []

        positions = sorted(set(positions))
        clustered = [positions[0]]

        for pos in positions[1:]:
            if pos - clustered[-1] > min_gap:
                clustered.append(pos)

        return clustered

    def _build_column_templates(self, img_width: int) -> List[Tuple[str, float, float, int]]:
        """
        Build column templates: (field_name, min_x_ratio, max_x_ratio, col_index).

        For 1940 census, uses empirically-determined column positions.
        """
        if self.census_year == 1940:
            # 1940 Census column templates
            # These ratios are estimated from standard 1940 census layout
            templates = [
                ("name", 0.05, 0.25, 0),  # Column 7: Name (large column)
                ("relationship_to_head", 0.25, 0.28, 1),  # Column 8: Relation
                ("sex", 0.28, 0.30, 2),  # Column 9: Sex
                ("race", 0.30, 0.33, 3),  # Column 10: Race
                ("age", 0.33, 0.35, 4),  # Column 11: Age
                ("marital_status", 0.35, 0.37, 5),  # Column 12: Marital status
                ("birthplace", 0.40, 0.48, 6),  # Column 13: Birthplace
                ("occupation", 0.55, 0.65, 7),  # Column 17-19: Occupation
            ]
        else:
            # Fallback: generic columns for other years
            templates = [
                ("name", 0.05, 0.25, 0),
                ("age", 0.33, 0.35, 1),
                ("sex", 0.28, 0.30, 2),
            ]

        return templates

    def _create_cells_from_templates(
        self,
        row_positions: List[int],
        column_templates: List[Tuple[str, float, float, int]],
        img_height: int,
        img_width: int,
    ) -> List[CellRegion]:
        """
        Create cells at row/column intersections.

        Args:
            row_positions: Y-coordinates of row separators
            column_templates: Column definitions (field, x_min_ratio, x_max_ratio, col_idx)
            img_height: Image height
            img_width: Image width

        Returns:
            List of CellRegion objects
        """
        cells = []

        # Create row boundaries
        row_boundaries = []
        for i in range(len(row_positions) - 1):
            y_start = row_positions[i]
            y_end = row_positions[i + 1]
            height = y_end - y_start

            # Filter out very small rows
            if height >= self.min_cell_height:
                row_boundaries.append((y_start, height))

        # Create cells
        for row_idx, (row_y, row_h) in enumerate(row_boundaries):
            for field_name, min_x_ratio, max_x_ratio, col_idx in column_templates:
                # Calculate column position from template
                col_x = int(min_x_ratio * img_width)
                col_x2 = int(max_x_ratio * img_width)
                col_w = col_x2 - col_x

                # Create cell
                cell = CellRegion(
                    x=col_x,
                    y=row_y,
                    width=col_w,
                    height=row_h,
                    row=row_idx,
                    col=col_idx,
                )
                cells.append(cell)

        return cells

    def visualize_layout(
        self,
        image: np.ndarray,
        layout: TableLayout,
        output_path: Optional[str | Path] = None,
    ) -> np.ndarray:
        """
        Draw detected layout on image for visualization.

        Args:
            image: Input image
            layout: Detected table layout
            output_path: Optional path to save visualization

        Returns:
            Image with drawn layout
        """
        # Convert to color if grayscale
        if len(image.shape) == 2:
            vis_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            vis_image = image.copy()

        # Draw cells
        for cell in layout.cells:
            # Draw rectangle
            cv2.rectangle(
                vis_image,
                (cell.x, cell.y),
                (cell.x + cell.width, cell.y + cell.height),
                (0, 255, 0),  # Green
                2,
            )

            # Draw cell label (row, col)
            label = f"({cell.row},{cell.col})"
            cv2.putText(
                vis_image,
                label,
                (cell.x + 5, cell.y + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 0, 0),  # Blue
                1,
            )

        # Draw table boundary
        tx, ty, tw, th = layout.table_bbox
        cv2.rectangle(vis_image, (tx, ty), (tx + tw, ty + th), (0, 0, 255), 3)  # Red

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), vis_image)
            logger.info(f"Saved layout visualization: {output_path}")

        return vis_image


def detect_census_layout(
    image: np.ndarray | str | Path,
    census_year: int = 1940,
    **options,
) -> Optional[TableLayout]:
    """
    Convenience function to detect table layout in census image.

    Args:
        image: Input image (array, path, or PIL image)
        census_year: Census year for column templates (default: 1940)
        **options: Detector options (min_cell_height, etc.)

    Returns:
        TableLayout object or None if no table detected

    Example:
        >>> layout = detect_census_layout("census_1940.jpg", census_year=1940)
        >>> print(f"Found {layout.num_rows} rows, {layout.num_cols} columns")
        Found 30 rows, 15 columns
    """
    detector = CensusLayoutDetector(census_year=census_year, **options)

    # Load image if path provided
    if isinstance(image, (str, Path)):
        image = cv2.imread(str(image))
        if image is None:
            raise ValueError(f"Failed to load image: {image}")

    return detector.detect_layout(image)
