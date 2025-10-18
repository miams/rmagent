"""
Enhanced row detection for census tables using Hough line transform.

More sensitive than morphological operations for detecting individual census rows.
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

    row_index: int  # 1-based index (matches printed census line numbers: 1-40)
    y_start: int    # Top Y coordinate
    y_end: int      # Bottom Y coordinate
    height: int     # Row height in pixels
    confidence: float = 1.0

    def crop_from_image(
        self, image: np.ndarray, padding_top: int = 5, padding_bottom: int = 33
    ) -> np.ndarray:
        """
        Crop this row from the given image with padding.

        Args:
            image: Input image
            padding_top: Pixels to include above row (default: 5 for readability)
            padding_bottom: Pixels to include below row (default: 33 for descenders)

        Returns:
            Cropped row image with padding
        """
        y1 = max(0, self.y_start - padding_top)
        y2 = min(image.shape[0], self.y_end + padding_bottom)
        return image[y1:y2, :]


class CensusRowDetector:
    """
    Detect individual census rows using Hough line transform.

    More sensitive than morphological operations for finding all 40 row separators.
    """

    def __init__(
        self,
        expected_rows: int = 40,
        min_line_length_ratio: float = 0.25,  # Line must span 25% of width (census lines vary)
        hough_threshold: int = 20,  # Hough accumulator threshold (lowered for sensitivity)
        min_row_height: int = 20,  # Minimum pixels between rows
        line_cluster_distance: int = 18,  # Merge lines within 18px (optimized for 40 rows)
        padding_top: int = 5,  # Padding above row for readability
        padding_bottom: int = 33,  # Padding below row for descenders (g, y, p, j)
    ):
        """
        Initialize row detector.

        Args:
            expected_rows: Expected number of rows (default: 40 for 1940 census)
            min_line_length_ratio: Minimum line width as fraction of image width
            hough_threshold: Hough transform threshold (lower = more sensitive)
            min_row_height: Minimum height between row separators
            line_cluster_distance: Max distance to merge nearby lines
        """
        self.expected_rows = expected_rows
        self.min_line_length_ratio = min_line_length_ratio
        self.hough_threshold = hough_threshold
        self.min_row_height = min_row_height
        self.line_cluster_distance = line_cluster_distance
        self.padding_top = padding_top
        self.padding_bottom = padding_bottom

    def detect_rows(
        self, image: np.ndarray, include_supplemental: bool = False
    ) -> List[RowBoundary]:
        """
        Detect all census rows in the image using uniform spacing.

        Census forms have uniformly-spaced rows. We detect the top and bottom boundaries
        of the 40-row section, then generate uniform row boundaries.

        Args:
            image: Input image (grayscale or BGR)
            include_supplemental: If True, also detect 2 supplemental question rows

        Returns:
            List of RowBoundary objects, sorted top to bottom
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        img_height, img_width = gray.shape

        # Step 1: Detect horizontal lines using Hough transform
        horizontal_lines_y = self._detect_horizontal_lines(gray)

        if len(horizontal_lines_y) < 10:
            logger.warning(f"Only {len(horizontal_lines_y)} lines detected - need more for boundary detection")
            return []

        logger.info(f"Detected {len(horizontal_lines_y)} horizontal lines")

        # Step 2: Try to extract rows using two approaches
        # Approach 1: Look for large section with 30-60 detected lines (works when many lines detected)
        # Approach 2: Find uniform spacing pattern and fit grid (works with fewer lines)

        rows = None

        # Try original approach first (requires 30-60 lines in a section)
        if len(horizontal_lines_y) >= 30:
            rows = self._extract_uniform_rows(horizontal_lines_y, img_height)
            if rows:
                logger.info(f"Used section-based extraction ({len(horizontal_lines_y)} lines detected)")

        # Fall back to grid fitting if original approach failed
        if not rows and len(horizontal_lines_y) >= 3:
            logger.info(f"Trying grid fitting approach ({len(horizontal_lines_y)} lines detected)")
            rows = self._extract_uniform_rows_by_grid_fitting(horizontal_lines_y, img_height)
            if rows:
                logger.info("Used grid-fitting extraction")

        if not rows:
            logger.warning(f"Failed to extract rows (detected {len(horizontal_lines_y)} lines)")
            return []

        logger.info(f"Extracted {len(rows)} uniform rows")

        # Step 3: Validate row count
        if len(rows) < self.expected_rows * 0.9:  # At least 90% of expected
            logger.warning(
                f"Detected {len(rows)} rows, expected {self.expected_rows}. "
                f"May need to adjust detection parameters."
            )

        # Step 4: Optionally detect supplemental rows
        if include_supplemental:
            supp_rows = self._detect_supplemental_rows(horizontal_lines_y, rows)
            if supp_rows:
                rows.extend(supp_rows)
                logger.info(f"Added {len(supp_rows)} supplemental rows")

        return rows

    def _detect_horizontal_lines(self, gray: np.ndarray) -> List[int]:
        """
        Detect horizontal line Y-coordinates using Hough line transform.

        Returns sorted list of Y-coordinates.
        """
        img_height, img_width = gray.shape

        # Edge detection (Canny) - use sensitive parameters to detect faint lines
        edges = cv2.Canny(gray, 10, 50, apertureSize=3)

        # Hough line transform
        # rho=1, theta=pi/180, threshold adjustable
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=self.hough_threshold,
            minLineLength=int(img_width * self.min_line_length_ratio),
            maxLineGap=50  # Allow small gaps in lines
        )

        if lines is None:
            logger.warning("Hough transform found no lines")
            return []

        logger.debug(f"Hough transform found {len(lines)} line segments")

        # Extract horizontal lines (small vertical variation)
        horizontal_y_positions = []
        for line in lines:
            x1, y1, x2, y2 = line[0]

            # Check if line is roughly horizontal (y1 ~ y2)
            if abs(y2 - y1) < 10:  # Allow 10px vertical variation
                # Use average Y position
                y_avg = (y1 + y2) // 2
                horizontal_y_positions.append(y_avg)

        logger.debug(f"Found {len(horizontal_y_positions)} horizontal line segments")

        # Cluster nearby lines
        clustered_lines = self._cluster_lines(horizontal_y_positions)

        logger.debug(f"Clustered to {len(clustered_lines)} distinct horizontal lines")

        # Filter out margin lines (top 3% and bottom 3%)
        filtered_lines = [
            y for y in clustered_lines
            if img_height * 0.03 < y < img_height * 0.97
        ]

        logger.info(
            f"Detected {len(filtered_lines)} horizontal lines after filtering "
            f"(removed {len(clustered_lines) - len(filtered_lines)} margin lines)"
        )

        return sorted(filtered_lines)

    def _cluster_lines(self, y_positions: List[int]) -> List[int]:
        """
        Cluster nearby Y-positions to merge double-ruled lines.

        Args:
            y_positions: List of Y-coordinates

        Returns:
            List of clustered Y-coordinates (mean of each cluster)
        """
        if not y_positions:
            return []

        y_positions = sorted(y_positions)
        clusters = [[y_positions[0]]]

        for y in y_positions[1:]:
            # Check if close to last cluster
            if y - clusters[-1][-1] <= self.line_cluster_distance:
                clusters[-1].append(y)
            else:
                clusters.append([y])

        # Return mean of each cluster
        clustered = [int(np.mean(cluster)) for cluster in clusters]

        logger.debug(
            f"Clustered {len(y_positions)} positions into {len(clustered)} lines "
            f"(cluster_distance={self.line_cluster_distance}px)"
        )

        return clustered

    def _extract_uniform_rows_by_grid_fitting(
        self, detected_lines: List[int], img_height: int
    ) -> List[RowBoundary]:
        """
        Extract 40 uniform rows by fitting a grid to detected line spacing patterns.

        This approach works even when only a few lines are detected. It finds
        the most uniform spacing pattern and extrapolates a full 40-row grid.

        Args:
            detected_lines: Y-coordinates of detected horizontal lines (sorted)
            img_height: Image height in pixels

        Returns:
            List of RowBoundary objects for 40 uniform rows
        """
        if len(detected_lines) < 3:
            logger.warning("Need at least 3 detected lines for grid fitting")
            return []

        # Calculate spacings between consecutive detected lines
        spacings = []
        for i in range(len(detected_lines) - 1):
            spacing = detected_lines[i + 1] - detected_lines[i]
            spacings.append((i, spacing, detected_lines[i], detected_lines[i + 1]))

        # Look for sequences of uniform spacing (census table rows)
        # Uniform = within 20% variance
        uniform_sequences = []

        for i in range(len(spacings)):
            sequence = [spacings[i]]
            base_spacing = spacings[i][1]

            # Extend sequence while spacing remains similar
            for j in range(i + 1, len(spacings)):
                current_spacing = spacings[j][1]
                variance = abs(current_spacing - base_spacing) / base_spacing

                if variance < 0.2:  # Within 20%
                    sequence.append(spacings[j])
                    # Update running average
                    base_spacing = sum(s[1] for s in sequence) / len(sequence)
                else:
                    break

            if len(sequence) >= 3:  # Need at least 3 uniform spacings
                avg_spacing = sum(s[1] for s in sequence) / len(sequence)
                y_start = sequence[0][2]
                y_end = sequence[-1][3]
                uniform_sequences.append((len(sequence), avg_spacing, y_start, y_end))

        if not uniform_sequences:
            logger.warning("No uniform spacing sequences found")
            return []

        # Use longest uniform sequence (most detected lines with consistent spacing)
        uniform_sequences.sort(reverse=True)  # Sort by length
        num_lines, avg_spacing, region_start, region_end = uniform_sequences[0]

        logger.info(
            f"Found uniform spacing: {num_lines} lines, avg={avg_spacing:.1f}px, "
            f"region y={region_start}-{region_end}"
        )

        # Estimate row height from detected spacing
        # Important: The detected spacing might be detecting every Nth row (e.g., every 2-3 rows)
        # if lines are faint. Check if spacing is a multiple of expected row height (~60-70px).

        detected_spacing = avg_spacing

        # If spacing is large (>100px), it's likely detecting every 2-3 rows
        # Expected row height for 1940 census: ~60-70px
        # If detected spacing is ~170px, it's likely every 2.5 rows (170/2.5 = 68px)

        if detected_spacing > 100:
            # Try dividing by 2, 2.5, 3 to find actual row height
            candidates = []
            for divisor in [2.0, 2.5, 3.0]:
                candidate_height = detected_spacing / divisor
                if 50 <= candidate_height <= 80:  # Reasonable row height range
                    candidates.append((divisor, candidate_height))

            if candidates:
                # Use the divisor that gives closest to 65px (typical 1940 census)
                best_divisor, estimated_row_height = min(candidates, key=lambda x: abs(x[1] - 65))
                logger.info(
                    f"Detected spacing {detected_spacing:.1f}px is likely every {best_divisor:.1f} rows. "
                    f"Estimated row height: {estimated_row_height:.1f}px"
                )
            else:
                estimated_row_height = detected_spacing
        else:
            estimated_row_height = detected_spacing

        # Strategy: The detected uniform region represents some subset of the 40 rows.
        # We need to determine which rows, then extrapolate the full 40-row grid.

        # Key constraint: The 40-row table must fit within image bounds.
        # We'll try different assumptions about which rows were detected and pick the best fit.

        # Calculate how many row-heights the detected region spans
        detected_span = region_end - region_start
        num_row_heights_in_region = int(detected_span / estimated_row_height)  # Actual number of rows detected

        # The detected region spans num_row_heights_in_region rows out of 40 total
        # Try different assumptions about which rows the detected region represents

        best_candidate = None
        best_score = -1

        # Try assuming detected region starts at different row numbers
        max_start_row = max(1, 41 - num_row_heights_in_region)  # Don't try too late
        for start_row_num in range(1, max_start_row + 1):
            # If detected region spans rows start_row_num to start_row_num+num_row_heights_in_region
            # Then top of detected region = top of row start_row_num
            # Calculate top of row 1
            rows_before_region = start_row_num - 1  # e.g., if start_row_num=5, rows 1-4 before region
            estimated_top_row_1 = region_start - rows_before_region * estimated_row_height
            estimated_bottom_row_40 = estimated_top_row_1 + 40 * estimated_row_height

            # Check if this fits within image bounds (with some tolerance)
            if estimated_top_row_1 < 0 or estimated_bottom_row_40 > img_height:
                continue  # Out of bounds

            # Score based on how well it uses the available image space
            # Prefer solutions that:
            # 1. Keep reasonable margins from top/bottom
            # 2. Center the table in the middle portion of the image

            margin_top = estimated_top_row_1 / img_height
            margin_bottom = (img_height - estimated_bottom_row_40) / img_height

            # Require minimum margins (5% top, 3% bottom for header/footer space)
            if margin_top < 0.05 or margin_bottom < 0.03:
                continue

            # Score: prefer balanced margins (centered table)
            score = min(margin_top, margin_bottom)

            if score > best_score:
                best_score = score
                best_candidate = (estimated_top_row_1, estimated_bottom_row_40, start_row_num)

        if best_candidate is None:
            logger.warning(
                f"No valid grid placement found for {num_lines} detected lines. "
                f"Image height={img_height}, estimated_row_height={estimated_row_height:.1f}"
            )
            return []

        estimated_top_row_1 = int(best_candidate[0])
        assumed_start_row = best_candidate[2]

        logger.info(
            f"Grid fitting: row_height={estimated_row_height:.1f}px, "
            f"top_row_1={estimated_top_row_1}, "
            f"(assumed detected region spans rows {assumed_start_row}-{assumed_start_row+num_row_heights_in_region-1})"
        )

        # Generate 40 uniform rows
        rows = []
        for i in range(self.expected_rows):
            y_start = int(estimated_top_row_1 + i * estimated_row_height)
            y_end = int(estimated_top_row_1 + (i + 1) * estimated_row_height)
            height = y_end - y_start

            row = RowBoundary(
                row_index=i + 1,  # 1-based
                y_start=y_start,
                y_end=y_end,
                height=height,
            )
            rows.append(row)

        return rows

    def _extract_uniform_rows(
        self, detected_lines: List[int], img_height: int
    ) -> List[RowBoundary]:
        """
        Extract uniform 40-row section from detected lines.

        Census forms have a uniform 40-row data section separated by large gaps
        from headers and supplementary sections. We find this section and generate
        uniform row boundaries.

        Args:
            detected_lines: Y-coordinates of detected horizontal lines (sorted)
            img_height: Image height in pixels

        Returns:
            List of RowBoundary objects for 40 uniform rows
        """
        if len(detected_lines) < 10:
            return []

        # Split into sections based on large gaps (>150px)
        sections = []
        section_start_idx = 0

        for i in range(len(detected_lines) - 1):
            gap = detected_lines[i + 1] - detected_lines[i]
            if gap > 150:  # Section boundary
                section_lines = detected_lines[section_start_idx : i + 1]
                if len(section_lines) > 0:
                    sections.append((section_start_idx, i + 1, section_lines))
                section_start_idx = i + 1

        # Don't forget last section
        if section_start_idx < len(detected_lines):
            section_lines = detected_lines[section_start_idx:]
            if len(section_lines) > 0:
                sections.append(
                    (section_start_idx, len(detected_lines), section_lines)
                )

        # Find main data section: longest section with 30-60 lines
        main_section_lines = None
        max_lines_in_range = 0

        for start_idx, end_idx, section_lines in sections:
            num_lines = len(section_lines)
            if 30 <= num_lines <= 60 and num_lines > max_lines_in_range:
                main_section_lines = section_lines
                max_lines_in_range = num_lines

        if main_section_lines is None:
            logger.error("Could not identify main 40-row data section")
            return []

        logger.info(
            f"Found main data section: {len(main_section_lines)} detected lines, "
            f"y={main_section_lines[0]}-{main_section_lines[-1]}"
        )

        # Calculate uniform row height
        # Census forms: rows are uniformly spaced
        # First detected line = bottom of row 1, last detected line = top of row 40
        bottom_of_row_1 = main_section_lines[0]
        top_of_row_40 = main_section_lines[-1]

        # From bottom of row 1 to top of row 40 = 38 row heights
        # (row 1 bottom to row 40 top skips 38 boundaries)
        vertical_span = top_of_row_40 - bottom_of_row_1
        uniform_row_height = vertical_span / 38.0

        # Calculate top of row 1
        top_of_row_1 = bottom_of_row_1 - uniform_row_height

        logger.info(
            f"Uniform row height: {uniform_row_height:.2f}px "
            f"(calculated from bottom row 1 at {bottom_of_row_1} to top row 40 at {top_of_row_40})"
        )

        # Generate 40 uniform rows with 1-based indexing (matches printed line numbers)
        rows = []
        for i in range(self.expected_rows):
            y_start = int(top_of_row_1 + i * uniform_row_height)
            y_end = int(top_of_row_1 + (i + 1) * uniform_row_height)
            height = y_end - y_start

            row = RowBoundary(
                row_index=i + 1,  # 1-based: row 1-40 (not 0-39)
                y_start=y_start,
                y_end=y_end,
                height=height
            )
            rows.append(row)

        return rows

    def _detect_supplemental_rows(
        self, detected_lines: List[int], main_rows: List[RowBoundary]
    ) -> List[RowBoundary]:
        """
        Detect 2 supplemental question rows below the 40 main rows.

        Args:
            detected_lines: All detected horizontal lines
            main_rows: The 40 main data rows

        Returns:
            List of 2 supplemental RowBoundary objects, or empty list if not found
        """
        if not main_rows:
            return []

        # Bottom of last main row
        bottom_main_section = main_rows[-1].y_end

        # Find lines below main section
        supp_lines = [y for y in detected_lines if y > bottom_main_section + 100]

        if len(supp_lines) < 2:
            logger.warning("Not enough lines detected for supplemental rows")
            return []

        # Look for a line that's roughly in the middle of a row (indicates supplemental section)
        # Supplemental rows are typically 67px tall (same as main rows)
        SUPP_ROW_HEIGHT = 67

        # Find potential middle-of-row line (should have reasonable spacing on both sides)
        middle_line_candidates = []
        for i, y in enumerate(supp_lines):
            if i < len(supp_lines) - 1:
                spacing_to_next = supp_lines[i + 1] - y
                # Middle of row should be ~33px from surrounding lines
                if 20 < spacing_to_next < 80:
                    middle_line_candidates.append(y)

        if not middle_line_candidates:
            logger.warning("Could not identify supplemental row middle marker")
            return []

        # Use first candidate as middle of supplemental row 1
        middle_supp_1 = middle_line_candidates[0]

        # Calculate supplemental rows (uniform 67px height)
        top_supp_1 = middle_supp_1 - SUPP_ROW_HEIGHT // 2
        bottom_supp_1 = top_supp_1 + SUPP_ROW_HEIGHT
        top_supp_2 = bottom_supp_1
        bottom_supp_2 = top_supp_2 + SUPP_ROW_HEIGHT

        logger.info(
            f"Supplemental rows: Row 1 y={top_supp_1}-{bottom_supp_1}, "
            f"Row 2 y={top_supp_2}-{bottom_supp_2}"
        )

        supp_rows = [
            RowBoundary(
                row_index=41,  # Supp row 1 (or could use 'S1')
                y_start=top_supp_1,
                y_end=bottom_supp_1,
                height=SUPP_ROW_HEIGHT,
            ),
            RowBoundary(
                row_index=42,  # Supp row 2 (or could use 'S2')
                y_start=top_supp_2,
                y_end=bottom_supp_2,
                height=SUPP_ROW_HEIGHT,
            ),
        ]

        return supp_rows

    def visualize_rows(
        self,
        image: np.ndarray,
        rows: List[RowBoundary],
        output_path: Optional[str | Path] = None,
    ) -> np.ndarray:
        """
        Draw detected rows on image for visualization.

        Args:
            image: Input image
            rows: List of detected row boundaries
            output_path: Optional path to save visualization

        Returns:
            Image with drawn rows
        """
        # Convert to color if grayscale
        if len(image.shape) == 2:
            vis_image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            vis_image = image.copy()

        img_width = vis_image.shape[1]

        # Draw row boundaries
        for row in rows:
            # Top boundary (green)
            cv2.line(
                vis_image,
                (0, row.y_start),
                (img_width, row.y_start),
                (0, 255, 0),  # Green
                2
            )

            # Bottom boundary (red)
            cv2.line(
                vis_image,
                (0, row.y_end),
                (img_width, row.y_end),
                (0, 0, 255),  # Red
                1
            )

            # Row label
            label = f"Row {row.row_index} (h={row.height}px)"
            cv2.putText(
                vis_image,
                label,
                (10, row.y_start + row.height // 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 0, 0),  # Blue
                2
            )

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), vis_image)
            logger.info(f"Saved row visualization: {output_path}")

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
        **options: Detector options (hough_threshold, etc.)

    Returns:
        List of RowBoundary objects

    Example:
        >>> rows = detect_census_rows("census_1940.jpg", expected_rows=40)
        >>> print(f"Detected {len(rows)} rows")
        Detected 41 rows
    """
    detector = CensusRowDetector(expected_rows=expected_rows, **options)

    # Load image if path provided
    if isinstance(image, (str, Path)):
        image = cv2.imread(str(image))
        if image is None:
            raise ValueError(f"Failed to load image: {image}")

    return detector.detect_rows(image)
