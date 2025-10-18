"""
Rigorous census row detection with gap-filling algorithm.

This detector:
1. Performs initial morphological line detection
2. Identifies gaps where lines are missing
3. Re-searches those specific regions with adjusted parameters
4. Iterates until all expected lines are found (41 lines for 40 rows)
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RowBoundary:
    """Represents a detected row with Y-coordinates."""

    row_index: int  # 1-based index (1-40)
    y_start: int    # Top Y coordinate
    y_end: int      # Bottom Y coordinate
    height: int     # Row height in pixels
    confidence: float = 1.0
    region: str = "main"  # Region where detected: "main", "top", "bottom"

    def crop_from_image(
        self, image: np.ndarray, padding_top: int = 5, padding_bottom: int = 33
    ) -> np.ndarray:
        """Crop this row from the given image with padding."""
        y1 = max(0, self.y_start - padding_top)
        y2 = min(image.shape[0], self.y_end + padding_bottom)
        return image[y1:y2, :]


class RigorousDetector:
    """
    Rigorous census row detector with gap-filling.

    Strategy:
    1. Initial broad detection of horizontal lines
    2. Identify gaps where lines are likely missing
    3. Targeted re-search in gap regions with adjusted parameters
    4. Validate and create uniform 40-row grid from 41 detected lines
    """

    def __init__(
        self,
        expected_rows: int = 40,
        expected_lines: int = 41,  # 41 lines define 40 rows
        expected_row_height: int = 65,
        kernel_width_ratio: int = 40,
        padding_top: int = 5,
        padding_bottom: int = 33,
    ):
        """
        Initialize rigorous detector.

        Args:
            expected_rows: Expected number of rows (40 for 1940 census)
            expected_lines: Expected number of boundary lines (41)
            expected_row_height: Expected row height in pixels
            kernel_width_ratio: Horizontal kernel width = img_width // ratio
            padding_top: Padding above row for readability
            padding_bottom: Padding below row for descenders
        """
        self.expected_rows = expected_rows
        self.expected_lines = expected_lines
        self.expected_row_height = expected_row_height
        self.kernel_width_ratio = kernel_width_ratio
        self.padding_top = padding_top
        self.padding_bottom = padding_bottom

    def detect_rows(
        self, image: np.ndarray, include_supplemental: bool = False
    ) -> List[RowBoundary]:
        """
        Detect census rows using rigorous gap-filling algorithm.

        Args:
            image: Input image (grayscale or BGR)
            include_supplemental: If True, detect supplemental rows

        Returns:
            List of RowBoundary objects
        """
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        img_height, img_width = gray.shape

        # Define regions based on domain knowledge
        regions = self._define_regions(img_height)

        logger.info(f"Processing image: {img_width}x{img_height}")

        # Step 1: Initial line detection across all regions
        all_lines = self._initial_detection(gray, regions)

        logger.info(f"Initial detection: found {len(all_lines)} lines")

        # Step 2: Gap-filling iterations
        filled_lines = self._fill_gaps(gray, all_lines, regions)

        logger.info(f"After gap-filling: {len(filled_lines)} lines")

        # Step 3: Create 40 uniform rows from detected lines
        rows = self._create_rows_from_lines(filled_lines, img_height)

        if len(rows) != self.expected_rows:
            logger.warning(f"Generated {len(rows)} rows, expected {self.expected_rows}")

        # Step 4: Optionally detect supplemental rows
        if include_supplemental and len(rows) == self.expected_rows:
            supp_region = regions['supplemental']
            supp_rows = self._detect_supplemental_rows(gray, supp_region, rows[-1])
            if supp_rows:
                rows.extend(supp_rows)
                logger.info(f"Added {len(supp_rows)} supplemental rows")

        return rows

    def _define_regions(self, img_height: int) -> dict:
        """Define regions based on census form structure."""
        return {
            'header': (0, int(img_height * 0.15)),
            'top_transition': (int(img_height * 0.15), int(img_height * 0.20)),
            'main_table': (int(img_height * 0.20), int(img_height * 0.80)),
            'bottom_transition': (int(img_height * 0.80), int(img_height * 0.85)),
            'supplemental': (int(img_height * 0.85), int(img_height * 1.00)),
        }

    def _initial_detection(
        self, gray: np.ndarray, regions: dict
    ) -> List[int]:
        """
        Initial line detection across all regions.

        Returns:
            List of Y-coordinates (sorted, in full image space)
        """
        all_lines = []

        # Detect in top transition
        top_lines = self._detect_lines_in_region(
            gray, regions['top_transition'], "top_transition"
        )
        all_lines.extend(top_lines)

        # Detect in main table
        main_lines = self._detect_lines_in_region(
            gray, regions['main_table'], "main_table"
        )
        all_lines.extend(main_lines)

        # Detect in bottom transition
        bottom_lines = self._detect_lines_in_region(
            gray, regions['bottom_transition'], "bottom_transition",
            check_left_extension=True
        )
        all_lines.extend(bottom_lines)

        return sorted(set(all_lines))

    def _detect_lines_in_region(
        self,
        gray: np.ndarray,
        region: Tuple[int, int],
        region_name: str,
        check_left_extension: bool = False,
        kernel_width_ratio: Optional[int] = None
    ) -> List[int]:
        """
        Detect horizontal lines in a specific region.

        Args:
            gray: Grayscale image
            region: (y_start, y_end) tuple
            region_name: Name of region for logging
            check_left_extension: If True, check for lines extending to left margin
            kernel_width_ratio: Override default kernel width ratio

        Returns:
            List of Y-coordinates (in full image space)
        """
        y_start, y_end = region
        region_img = gray[y_start:y_end, :]
        img_height, img_width = gray.shape

        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            region_img, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY_INV, 15, 2
        )

        # Create horizontal kernel
        if kernel_width_ratio is None:
            kernel_width_ratio = self.kernel_width_ratio
        kernel_width = img_width // kernel_width_ratio
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, 1))

        # Morphological opening
        detected_lines_img = cv2.morphologyEx(
            thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2
        )

        # Find contours
        contours, _ = cv2.findContours(
            detected_lines_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Extract Y-coordinates with region-specific filters
        line_y_coords = []

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Region-specific width requirements
            if region_name == "bottom_transition" and check_left_extension:
                if x < img_width * 0.02 and w > img_width * 0.3:
                    line_y_coords.append(y + h // 2)
            else:
                if w > img_width * 0.15:
                    line_y_coords.append(y + h // 2)

        # Cluster nearby lines
        clustered_lines = self._cluster_lines(line_y_coords)

        # Offset to full image coordinates
        return [y + y_start for y in clustered_lines]

    def _cluster_lines(self, y_positions: List[int], distance: int = 5) -> List[int]:
        """Cluster nearby Y-positions to merge double-ruled lines."""
        if not y_positions:
            return []

        y_positions = sorted(y_positions)
        clusters = [[y_positions[0]]]

        for y in y_positions[1:]:
            if y - clusters[-1][-1] <= distance:
                clusters[-1].append(y)
            else:
                clusters.append([y])

        return [int(np.mean(cluster)) for cluster in clusters]

    def _fill_gaps(
        self, gray: np.ndarray, initial_lines: List[int], regions: dict,
        max_iterations: int = 3
    ) -> List[int]:
        """
        Fill gaps where lines are missing using targeted re-search.

        Args:
            gray: Grayscale image
            initial_lines: Lines from initial detection
            regions: Region definitions
            max_iterations: Maximum gap-filling iterations

        Returns:
            List of Y-coordinates after gap-filling
        """
        lines = initial_lines.copy()
        img_height, img_width = gray.shape

        for iteration in range(max_iterations):
            # Analyze gaps
            gaps = []
            for i in range(len(lines) - 1):
                gap_size = lines[i + 1] - lines[i]
                if gap_size > self.expected_row_height * 1.5:  # Suspicious gap
                    gaps.append({
                        'index': i,
                        'y_start': lines[i],
                        'y_end': lines[i + 1],
                        'size': gap_size,
                        'expected_lines': round(gap_size / self.expected_row_height) - 1
                    })

            if not gaps:
                logger.info(f"Gap-filling complete after {iteration} iterations")
                break

            logger.info(f"Iteration {iteration + 1}: Found {len(gaps)} gaps to fill")

            # Search each gap with more lenient parameters
            new_lines_found = []
            for gap in gaps:
                # Search in the middle 80% of the gap (avoid edges)
                search_margin = int(gap['size'] * 0.1)
                search_region = (
                    gap['y_start'] + search_margin,
                    gap['y_end'] - search_margin
                )

                # Use more lenient kernel (smaller = finds shorter line segments)
                gap_lines = self._detect_lines_in_region(
                    gray, search_region, f"gap_{gap['index']}",
                    kernel_width_ratio=50  # More lenient than default 40
                )

                new_lines_found.extend(gap_lines)

            if new_lines_found:
                lines.extend(new_lines_found)
                lines = sorted(set(lines))
                logger.info(f"  Added {len(new_lines_found)} lines, total now: {len(lines)}")
            else:
                logger.info(f"  No new lines found, stopping gap-fill")
                break

        return lines

    def _create_rows_from_lines(
        self, lines: List[int], img_height: int
    ) -> List[RowBoundary]:
        """
        Create 40 rows from detected boundary lines.

        Strategy:
        - If we have exactly 41 lines: use them directly
        - If we have fewer: create uniform grid
        - If we have more: filter to best 41

        Args:
            lines: Detected boundary line Y-coordinates
            img_height: Image height

        Returns:
            List of 40 RowBoundary objects
        """
        if len(lines) < 2:
            logger.error("Need at least 2 lines to create rows")
            return []

        # If we have close to 41 lines, use them
        if 38 <= len(lines) <= 44:
            # Use detected lines to create rows
            working_lines = lines[:self.expected_lines] if len(lines) > self.expected_lines else lines

            rows = []
            for i in range(len(working_lines) - 1):
                y_start = working_lines[i]
                y_end = working_lines[i + 1]
                height = y_end - y_start

                row = RowBoundary(
                    row_index=i + 1,
                    y_start=y_start,
                    y_end=y_end,
                    height=height
                )
                rows.append(row)

            return rows

        # Otherwise fall back to uniform grid
        logger.warning(f"Have {len(lines)} lines, expected ~{self.expected_lines}. Creating uniform grid.")
        return self._create_uniform_grid(lines, img_height)

    def _create_uniform_grid(
        self, detected_lines: List[int], img_height: int
    ) -> List[RowBoundary]:
        """Create uniform 40-row grid using detected lines as anchors."""
        if len(detected_lines) < 3:
            logger.warning("Need at least 3 detected lines for grid creation")
            return []

        # Calculate spacing between consecutive lines
        spacings = []
        for i in range(len(detected_lines) - 1):
            spacing = detected_lines[i + 1] - detected_lines[i]
            if 30 <= spacing <= 120:
                spacings.append(spacing)

        if not spacings:
            logger.warning("No plausible spacings found")
            return []

        # Use median spacing
        estimated_row_height = int(np.median(spacings))

        # Find best anchor point
        expected_middle = img_height * 0.50
        anchor_line = min(detected_lines, key=lambda y: abs(y - expected_middle))
        anchor_row_num = 20

        # Calculate top of row 1
        top_row_1 = anchor_line - (anchor_row_num - 1) * estimated_row_height

        # Validate bounds
        bottom_row_40 = top_row_1 + 40 * estimated_row_height
        if top_row_1 < 0 or bottom_row_40 > img_height:
            logger.warning(f"Grid doesn't fit, adjusting")
            if top_row_1 < 0:
                top_row_1 = int(img_height * 0.15)
            estimated_row_height = int((img_height * 0.85 - top_row_1) / 40)

        # Generate 40 uniform rows
        rows = []
        for i in range(self.expected_rows):
            y_start = int(top_row_1 + i * estimated_row_height)
            y_end = int(top_row_1 + (i + 1) * estimated_row_height)
            height = y_end - y_start

            row = RowBoundary(
                row_index=i + 1,
                y_start=y_start,
                y_end=y_end,
                height=height,
            )
            rows.append(row)

        return rows

    def _detect_supplemental_rows(
        self,
        gray: np.ndarray,
        supp_region: Tuple[int, int],
        last_main_row: RowBoundary
    ) -> List[RowBoundary]:
        """Detect 2 supplemental question rows."""
        lines_in_supp = self._detect_lines_in_region(
            gray, supp_region, "supplemental"
        )

        if len(lines_in_supp) < 2:
            logger.warning("Not enough lines for supplemental rows")
            return []

        supp_row_height = last_main_row.height

        supp_rows = [
            RowBoundary(
                row_index=41,
                y_start=lines_in_supp[0],
                y_end=lines_in_supp[0] + supp_row_height,
                height=supp_row_height,
                region="supplemental"
            ),
            RowBoundary(
                row_index=42,
                y_start=lines_in_supp[0] + supp_row_height,
                y_end=lines_in_supp[0] + 2 * supp_row_height,
                height=supp_row_height,
                region="supplemental"
            ),
        ]

        return supp_rows

    def visualize_rows(
        self,
        image: np.ndarray,
        rows: List[RowBoundary],
        output_path: Optional[str | Path] = None,
    ) -> np.ndarray:
        """Draw detected rows on image."""
        if len(image.shape) == 2:
            vis_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            vis_image = image.copy()

        img_width = vis_image.shape[1]

        for row in rows:
            if row.region == "supplemental":
                color = (255, 0, 255)  # Magenta
            else:
                color = (0, 255, 0)  # Green

            # Top boundary
            cv2.line(vis_image, (0, row.y_start), (img_width, row.y_start), color, 2)

            # Row label
            label = f"Row {row.row_index} (h={row.height}px)"
            cv2.putText(
                vis_image,
                label,
                (10, row.y_start + row.height // 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 0),
                2
            )

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), vis_image)
            logger.info(f"Saved visualization: {output_path}")

        return vis_image
