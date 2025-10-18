"""
Region-guided census row detection using morphological operations.

This detector uses domain knowledge about census form structure to guide
the morphological line detection process. Different regions of the form
are processed with different strategies.

Census Form Structure (1940):
- Top 0-15%: Header region (filter out)
- 15-20%: Top transition (row 1 likely here, mixed with header lines)
- 20-80%: Main data table (40 uniform rows)
- 80-85%: Bottom transition (row 40, extends further left)
- 85-100%: Supplemental questions (separate processing)
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


class RegionGuidedDetector:
    """
    Detect census rows using morphological operations guided by domain knowledge.

    Key insight: The census form has predictable structure. We can use region-specific
    strategies to improve detection accuracy.
    """

    def __init__(
        self,
        expected_rows: int = 40,
        expected_row_height: int = 65,  # Typical 1940 census
        kernel_width_ratio: int = 40,  # More lenient for broken lines
        padding_top: int = 5,
        padding_bottom: int = 33,
    ):
        """
        Initialize region-guided detector.

        Args:
            expected_rows: Expected number of rows (40 for 1940 census)
            expected_row_height: Expected row height in pixels
            kernel_width_ratio: Horizontal kernel width = img_width // ratio
            padding_top: Padding above row for readability
            padding_bottom: Padding below row for descenders
        """
        self.expected_rows = expected_rows
        self.expected_row_height = expected_row_height
        self.kernel_width_ratio = kernel_width_ratio
        self.padding_top = padding_top
        self.padding_bottom = padding_bottom

    def detect_rows(
        self, image: np.ndarray, include_supplemental: bool = False
    ) -> List[RowBoundary]:
        """
        Detect census rows using region-guided morphological operations.

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
        logger.info(f"Regions defined: header={regions['header']}, "
                   f"top={regions['top_transition']}, "
                   f"main={regions['main_table']}, "
                   f"bottom={regions['bottom_transition']}")

        # Step 1: Detect lines in main table region (most reliable)
        main_lines = self._detect_lines_in_region(
            gray,
            regions['main_table'],
            region_name="main_table"
        )

        if len(main_lines) < 10:
            logger.warning(f"Only {len(main_lines)} lines in main table region")
            return []

        logger.info(f"Main table: detected {len(main_lines)} lines")

        # Step 2: Detect first table boundary (top of row 1) in top transition region
        first_boundary = self._detect_first_table_boundary(
            gray,
            regions['top_transition'],
            img_width
        )

        if first_boundary:
            top_lines = [first_boundary]
            logger.info(f"Top transition: detected first table boundary at y={first_boundary}")
        else:
            # Fallback to old method
            top_lines = self._detect_lines_in_region(
                gray,
                regions['top_transition'],
                region_name="top_transition"
            )
            logger.info(f"Top transition: fallback detected {len(top_lines)} lines")

        # Step 3: Detect row 40 in bottom transition region
        bottom_lines = self._detect_lines_in_region(
            gray,
            regions['bottom_transition'],
            region_name="bottom_transition",
            check_left_extension=True  # Row 40 extends further left
        )

        logger.info(f"Bottom transition: detected {len(bottom_lines)} lines")

        # Step 4: Combine all detected lines
        all_lines = sorted(set(top_lines + main_lines + bottom_lines))

        logger.info(f"Total unique lines across regions: {len(all_lines)}")

        # Step 5: Fill gaps using uniform spacing
        rows = self._create_uniform_grid(all_lines, img_height)

        if len(rows) != self.expected_rows:
            logger.warning(f"Generated {len(rows)} rows, expected {self.expected_rows}")

        # Step 6: Optionally detect supplemental rows
        if include_supplemental and len(rows) == self.expected_rows:
            supp_region = regions['supplemental']
            supp_rows = self._detect_supplemental_rows(gray, supp_region, rows[-1])
            if supp_rows:
                rows.extend(supp_rows)
                logger.info(f"Added {len(supp_rows)} supplemental rows")

        return rows

    def _define_regions(self, img_height: int) -> dict:
        """
        Define regions based on census form structure.

        Args:
            img_height: Image height in pixels

        Returns:
            Dictionary of region boundaries {name: (y_start, y_end)}
        """
        return {
            'header': (0, int(img_height * 0.15)),
            'top_transition': (int(img_height * 0.15) + 150, int(img_height * 0.25) + 150),
            'main_table': (int(img_height * 0.25) + 150, int(img_height * 0.80)),
            'bottom_transition': (int(img_height * 0.80), int(img_height * 0.85)),
            'supplemental': (int(img_height * 0.85), int(img_height * 1.00)),
        }

    def _detect_first_table_boundary(
        self,
        gray: np.ndarray,
        region: Tuple[int, int],
        img_width: int
    ) -> Optional[int]:
        """
        Detect first table boundary using multi-criteria approach.

        Uses three criteria in order of reliability:
        1. BLANK COLUMN: First line with segments in blank column (11-12.3%)
        2. SPACING RATIO: First line with gap_ratio > 1.5x (header->data transition)
        3. THICKNESS: Second-thickest line (first is usually header)

        Args:
            gray: Grayscale image
            region: (y_start, y_end) tuple for top_transition region
            img_width: Image width

        Returns:
            Y-coordinate of first table boundary (in full image space), or None
        """
        y_start, y_end = region
        region_img = gray[y_start:y_end, :]

        # Use lenient kernel to detect all possible lines
        kernel_width = img_width // 120
        thresh = cv2.adaptiveThreshold(
            region_img,
            255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY_INV,
            15,
            2
        )

        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, 1))
        detected_lines_img = cv2.morphologyEx(
            thresh,
            cv2.MORPH_OPEN,
            horizontal_kernel,
            iterations=2
        )

        contours, _ = cv2.findContours(
            detected_lines_img,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Collect segments
        all_segments = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            line_y = y + h // 2
            all_segments.append({
                'x': x,
                'y': line_y,
                'x_end': x + w,
                'width': w,
                'height': h
            })

        # Group by Y
        segment_groups = self._group_segments_by_y(all_segments, tolerance=5)

        # Define column boundaries
        line_numbers_start = img_width * 0.08
        line_numbers_end = img_width * 0.12
        blank_column_start = img_width * 0.11
        blank_column_end = img_width * 0.123

        # Analyze all lines
        candidates = []
        for group in segment_groups:
            avg_y = int(np.mean([s['y'] for s in group]))
            full_y = y_start + avg_y
            max_height = max(s['height'] for s in group)

            # Check for segments in key areas
            has_line_numbers = any(
                line_numbers_start < s['x'] < line_numbers_end
                for s in group
            )

            has_blank_column = any(
                blank_column_start < s['x'] < blank_column_end
                for s in group
            )

            min_x = min(s['x'] for s in group)
            max_x_end = max(s['x_end'] for s in group)
            span = max_x_end - min_x
            span_pct = span / img_width * 100

            # Candidate criteria
            is_candidate = (has_line_numbers and span_pct > 50 and max_height > 3)

            if is_candidate:
                candidates.append({
                    'y': avg_y,
                    'full_y': full_y,
                    'max_height': max_height,
                    'has_blank_column': has_blank_column
                })

        if not candidates:
            logger.warning("No candidates found in top_transition region")
            return None

        # Calculate gaps between candidates
        for i in range(len(candidates)):
            if i < len(candidates) - 1:
                gap_after = candidates[i+1]['full_y'] - candidates[i]['full_y']
                candidates[i]['gap_after'] = gap_after

                if i > 0:
                    gap_before = candidates[i]['full_y'] - candidates[i-1]['full_y']
                    candidates[i]['gap_ratio'] = gap_after / gap_before if gap_before > 0 else 0
                else:
                    candidates[i]['gap_ratio'] = 0
            else:
                candidates[i]['gap_after'] = 0
                candidates[i]['gap_ratio'] = 0

        # MULTI-CRITERIA DETECTION

        # CRITERION 1: Has blank column (most reliable when available)
        blank_column_lines = [c for c in candidates if c['has_blank_column']]
        if blank_column_lines:
            # Take FIRST (topmost) line with blank column
            first_boundary = min(blank_column_lines, key=lambda c: c['y'])
            logger.debug(f"First boundary detected via blank_column: y={first_boundary['full_y']}")
            return first_boundary['full_y']

        # CRITERION 2: Spacing ratio (fallback when blank column blocked by handwriting)
        if len(candidates) >= 2:
            # Find candidate with gap_ratio > 1.5x (header->data transition)
            spacing_candidates = [c for c in candidates if c['gap_ratio'] > 1.5]

            if spacing_candidates:
                # Take the FIRST candidate with significant gap increase
                first_boundary = spacing_candidates[0]
                logger.debug(f"First boundary detected via spacing_ratio: y={first_boundary['full_y']}")
                return first_boundary['full_y']

            # If no clear spacing ratio, look for second-thickest line
            sorted_by_height = sorted(candidates, key=lambda c: c['max_height'], reverse=True)
            if len(sorted_by_height) >= 2:
                first_boundary = sorted_by_height[1]
                logger.debug(f"First boundary detected via thickness_fallback: y={first_boundary['full_y']}")
                return first_boundary['full_y']

        # CRITERION 3: Single candidate (edge case)
        if len(candidates) == 1:
            logger.debug(f"First boundary detected via single_candidate: y={candidates[0]['full_y']}")
            return candidates[0]['full_y']

        logger.warning("Could not detect first table boundary using any criterion")
        return None

    def _group_segments_by_y(
        self,
        segments: List[dict],
        tolerance: int = 5
    ) -> List[List[dict]]:
        """Group line segments by Y-coordinate within tolerance."""
        if not segments:
            return []

        segments = sorted(segments, key=lambda s: s['y'])
        groups = [[segments[0]]]

        for seg in segments[1:]:
            if abs(seg['y'] - groups[-1][0]['y']) <= tolerance:
                groups[-1].append(seg)
            else:
                groups.append([seg])

        return groups

    def _detect_lines_in_region(
        self,
        gray: np.ndarray,
        region: Tuple[int, int],
        region_name: str,
        check_left_extension: bool = False
    ) -> List[int]:
        """
        Detect horizontal lines in a specific region using morphological operations.

        Args:
            gray: Grayscale image
            region: (y_start, y_end) tuple
            region_name: Name of region for logging
            check_left_extension: If True, check for lines extending to left margin

        Returns:
            List of Y-coordinates (in full image space)
        """
        y_start, y_end = region
        region_img = gray[y_start:y_end, :]
        img_height, img_width = gray.shape

        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            region_img,
            255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY_INV,
            15,
            2
        )

        # Create horizontal kernel
        kernel_width = img_width // self.kernel_width_ratio
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, 1))

        # Morphological opening
        detected_lines_img = cv2.morphologyEx(
            thresh,
            cv2.MORPH_OPEN,
            horizontal_kernel,
            iterations=2
        )

        # Find contours
        contours, _ = cv2.findContours(
            detected_lines_img,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Extract Y-coordinates with region-specific filters
        line_y_coords = []

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Region-specific width requirements
            if region_name == "bottom_transition" and check_left_extension:
                # Row 40 extends to left margin (x should be close to 0)
                # and should be reasonably wide
                if x < img_width * 0.02 and w > img_width * 0.3:
                    line_y_coords.append(y + h // 2)
            else:
                # Standard requirement: must span significant width
                # But more lenient than before (15% instead of 20%)
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

    def _create_uniform_grid(
        self, detected_lines: List[int], img_height: int
    ) -> List[RowBoundary]:
        """
        Create uniform 40-row grid using detected lines as anchors.

        Strategy:
        1. Calculate spacing from most uniform section of detected lines
        2. Extrapolate to create 40 uniform rows
        3. Validate against image bounds

        Args:
            detected_lines: Y-coordinates of detected lines (sorted)
            img_height: Image height in pixels

        Returns:
            List of 40 RowBoundary objects
        """
        if len(detected_lines) < 3:
            logger.warning("Need at least 3 detected lines for grid creation")
            return []

        # Calculate spacing between consecutive lines
        spacings = []
        for i in range(len(detected_lines) - 1):
            spacing = detected_lines[i + 1] - detected_lines[i]
            # Only consider plausible row spacings (30-120px)
            if 30 <= spacing <= 120:
                spacings.append(spacing)

        if not spacings:
            logger.warning("No plausible spacings found")
            return []

        # Use median spacing (more robust than mean)
        estimated_row_height = int(np.median(spacings))

        logger.info(
            f"Spacing analysis: detected {len(detected_lines)} lines, "
            f"median spacing={estimated_row_height}px"
        )

        # Find best anchor point (line closest to expected row 20 position)
        expected_middle = img_height * 0.50
        anchor_line = min(detected_lines, key=lambda y: abs(y - expected_middle))
        anchor_row_num = 20  # Assume anchor is around middle

        # Calculate top of row 1
        top_row_1 = anchor_line - (anchor_row_num - 1) * estimated_row_height

        # Validate bounds
        bottom_row_40 = top_row_1 + 40 * estimated_row_height
        if top_row_1 < 0 or bottom_row_40 > img_height:
            logger.warning(
                f"Grid doesn't fit: top_row_1={top_row_1}, "
                f"bottom_row_40={bottom_row_40}, img_height={img_height}"
            )
            # Adjust to fit
            if top_row_1 < 0:
                top_row_1 = int(img_height * 0.15)
            estimated_row_height = int((img_height * 0.85 - top_row_1) / 40)

        logger.info(
            f"Grid: row_height={estimated_row_height}px, top_row_1={top_row_1}"
        )

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
        y_start, y_end = supp_region
        supp_section = gray[y_start:y_end, :]

        # Use same morphological detection
        lines_in_supp = self._detect_lines_in_region(
            gray,
            supp_region,
            region_name="supplemental"
        )

        if len(lines_in_supp) < 2:
            logger.warning("Not enough lines for supplemental rows")
            return []

        # Create 2 supplemental rows from detected lines
        # Assume row height similar to main rows
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
            # Color code by region
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


def detect_census_rows(
    image: np.ndarray | str | Path,
    expected_rows: int = 40,
    **options,
) -> List[RowBoundary]:
    """
    Convenience function to detect census rows.

    Args:
        image: Input image (array or path)
        expected_rows: Expected number of rows (default: 40)
        **options: Detector options

    Returns:
        List of RowBoundary objects
    """
    detector = RegionGuidedDetector(expected_rows=expected_rows, **options)

    if isinstance(image, (str, Path)):
        image = cv2.imread(str(image))
        if image is None:
            raise ValueError(f"Failed to load image: {image}")

    return detector.detect_rows(image)
