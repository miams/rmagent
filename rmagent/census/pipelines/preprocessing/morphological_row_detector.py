"""
Census row detection using morphological operations.

This detector uses OpenCV's morphological operations (the recommended approach for
detecting horizontal lines in forms/tables) combined with domain knowledge about
census form structure.

Key improvements over Hough-based detection:
- Uses morphological opening to detect horizontal lines (more reliable for forms)
- Incorporates knowledge of census structure (40 uniform rows)
- Validates detected lines against expected patterns
- Separate detection for main table vs supplemental questions
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


class MorphologicalRowDetector:
    """
    Detect census rows using morphological operations.

    This approach is specifically optimized for detecting horizontal lines in forms/tables.
    """

    def __init__(
        self,
        expected_rows: int = 40,
        expected_row_height_range: Tuple[int, int] = (50, 85),
        kernel_width_ratio: int = 30,  # Kernel width = img_width // ratio
        adaptive_block_size: int = 15,
        adaptive_c: int = 2,
        morph_iterations: int = 2,
        min_line_width_ratio: float = 0.2,  # Line must span 20% of width
        cluster_distance: int = 5,
        padding_top: int = 5,
        padding_bottom: int = 33,
    ):
        """
        Initialize morphological row detector.

        Args:
            expected_rows: Expected number of rows in main table (default: 40)
            expected_row_height_range: Plausible row heights in pixels (min, max)
            kernel_width_ratio: Horizontal kernel width = img_width // ratio
            adaptive_block_size: Block size for adaptive thresholding (must be odd)
            adaptive_c: Constant for adaptive thresholding
            morph_iterations: Number of morphological iterations
            min_line_width_ratio: Minimum line width as fraction of image width
            cluster_distance: Max distance to merge nearby lines
            padding_top: Padding above row for readability
            padding_bottom: Padding below row for descenders
        """
        self.expected_rows = expected_rows
        self.expected_row_height_range = expected_row_height_range
        self.kernel_width_ratio = kernel_width_ratio
        self.adaptive_block_size = adaptive_block_size
        self.adaptive_c = adaptive_c
        self.morph_iterations = morph_iterations
        self.min_line_width_ratio = min_line_width_ratio
        self.cluster_distance = cluster_distance
        self.padding_top = padding_top
        self.padding_bottom = padding_bottom

    def detect_rows(
        self, image: np.ndarray, include_supplemental: bool = False
    ) -> List[RowBoundary]:
        """
        Detect all census rows using morphological operations.

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

        # Step 1: Detect main table rows (middle 65% of page)
        main_rows = self._detect_main_table_rows(gray)

        if not main_rows:
            logger.warning("Failed to detect main table rows")
            return []

        logger.info(f"Detected {len(main_rows)} main table rows")

        # Step 2: Optionally detect supplemental rows (bottom 15-20% of page)
        if include_supplemental:
            supp_rows = self._detect_supplemental_rows(gray, main_rows)
            if supp_rows:
                main_rows.extend(supp_rows)
                logger.info(f"Added {len(supp_rows)} supplemental rows")

        return main_rows

    def _detect_main_table_rows(self, gray: np.ndarray) -> List[RowBoundary]:
        """
        Detect the 40 main data table rows using morphological operations.

        Strategy:
        1. Use morphological opening to detect horizontal lines
        2. Extract Y-coordinates of detected lines
        3. Validate against expected census structure (40 uniform rows)
        4. Fit uniform grid using detected lines as anchor points

        Args:
            gray: Grayscale image

        Returns:
            List of 40 RowBoundary objects for main data table
        """
        img_height, img_width = gray.shape

        # Define data section region (middle 65% of page where 40-row table is)
        data_section_top = int(img_height * 0.10)
        data_section_bottom = int(img_height * 0.85)
        data_section = gray[data_section_top:data_section_bottom, :]

        # Step 1: Detect horizontal lines in data section
        detected_lines_y = self._detect_horizontal_lines_morphological(data_section)

        if len(detected_lines_y) < 3:
            logger.warning(f"Only detected {len(detected_lines_y)} lines in main table section")
            return []

        # Offset Y-coordinates to full image space
        detected_lines_y = [y + data_section_top for y in detected_lines_y]

        logger.info(f"Detected {len(detected_lines_y)} horizontal lines in main table section")

        # Step 2: Fit uniform 40-row grid using detected lines as anchors
        rows = self._fit_uniform_grid(
            detected_lines_y,
            expected_rows=self.expected_rows,
            img_height=img_height
        )

        return rows

    def _detect_horizontal_lines_morphological(self, gray: np.ndarray) -> List[int]:
        """
        Detect horizontal lines using morphological operations.

        This is OpenCV's recommended approach for detecting lines in forms/tables.

        Args:
            gray: Grayscale image (or image section)

        Returns:
            List of Y-coordinates of detected horizontal lines
        """
        img_height, img_width = gray.shape

        # 1. Adaptive thresholding (handles varying lighting)
        thresh = cv2.adaptiveThreshold(
            gray,
            255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY_INV,  # Invert: black becomes white
            self.adaptive_block_size,
            self.adaptive_c
        )

        # 2. Create horizontal kernel (wide, 1px tall)
        horizontal_kernel_width = img_width // self.kernel_width_ratio
        horizontal_kernel = cv2.getStructuringElement(
            cv2.MORPH_RECT, (horizontal_kernel_width, 1)
        )

        # 3. Morphological opening: removes text/noise, keeps horizontal lines
        detected_lines_img = cv2.morphologyEx(
            thresh,
            cv2.MORPH_OPEN,
            horizontal_kernel,
            iterations=self.morph_iterations
        )

        # 4. Find contours of detected lines
        contours, _ = cv2.findContours(
            detected_lines_img,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # 5. Extract Y-coordinates from contours
        line_y_coords = []
        min_line_width = int(img_width * self.min_line_width_ratio)

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # Filter: must be reasonably wide
            if w >= min_line_width:
                # Use vertical center of contour as line position
                line_y_coords.append(y + h // 2)

        # 6. Cluster nearby lines (handle double-ruled or thick lines)
        clustered_lines = self._cluster_lines(line_y_coords)

        logger.debug(
            f"Morphological detection: {len(line_y_coords)} raw lines → "
            f"{len(clustered_lines)} clustered lines"
        )

        return sorted(clustered_lines)

    def _cluster_lines(self, y_positions: List[int]) -> List[int]:
        """
        Cluster nearby Y-positions to merge double-ruled or thick lines.

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
            if y - clusters[-1][-1] <= self.cluster_distance:
                clusters[-1].append(y)
            else:
                clusters.append([y])

        # Return mean of each cluster
        clustered = [int(np.mean(cluster)) for cluster in clusters]

        logger.debug(
            f"Clustered {len(y_positions)} positions into {len(clustered)} lines "
            f"(cluster_distance={self.cluster_distance}px)"
        )

        return clustered

    def _fit_uniform_grid(
        self,
        detected_lines: List[int],
        expected_rows: int,
        img_height: int
    ) -> List[RowBoundary]:
        """
        Fit a uniform grid of rows using detected lines as anchor points.

        Domain knowledge: Census forms have exactly 40 uniformly-spaced rows.
        Even if we only detect some lines, we can fit a complete grid.

        Strategy:
        1. Find the most uniform sequence of detected lines
        2. Calculate average spacing from that sequence
        3. Validate spacing is plausible (50-85px per row)
        4. Extrapolate to create full 40-row grid

        Args:
            detected_lines: Y-coordinates of detected lines (sorted)
            expected_rows: Number of rows to generate (40)
            img_height: Image height in pixels

        Returns:
            List of RowBoundary objects for uniform rows
        """
        if len(detected_lines) < 3:
            logger.warning("Need at least 3 detected lines for grid fitting")
            return []

        # Step 1: Find most uniform spacing sequence
        best_sequence = self._find_most_uniform_sequence(detected_lines)

        if not best_sequence:
            logger.warning("No uniform spacing sequence found in detected lines")
            return []

        num_lines, avg_spacing, region_start, region_end = best_sequence

        logger.info(
            f"Found uniform sequence: {num_lines} lines, avg_spacing={avg_spacing:.1f}px, "
            f"region y={region_start}-{region_end}"
        )

        # Step 2: Correct spacing if detecting every Nth row
        # Do this BEFORE validation to get true row height
        min_height, max_height = self.expected_row_height_range
        corrected_spacing = avg_spacing

        if avg_spacing > max_height:
            # Likely detecting every 2-3 rows instead of every row
            for divisor in [2.0, 2.5, 3.0]:
                candidate_spacing = avg_spacing / divisor
                if min_height <= candidate_spacing <= max_height:
                    logger.info(
                        f"Correcting spacing: {avg_spacing:.1f}px / {divisor} = "
                        f"{candidate_spacing:.1f}px (detecting every {divisor:.1f} rows)"
                    )
                    corrected_spacing = candidate_spacing
                    break

        # Step 3: Validate corrected spacing
        if not (min_height <= corrected_spacing <= max_height):
            logger.warning(
                f"Spacing {corrected_spacing:.1f}px outside expected range "
                f"[{min_height}, {max_height}]px - proceeding anyway"
            )

        estimated_row_height = corrected_spacing

        # Step 3: Calculate how many rows the detected region spans
        detected_span = region_end - region_start
        num_rows_in_region = int(detected_span / estimated_row_height)

        # Step 4: Try different placements and pick best fit
        best_placement = self._find_best_grid_placement(
            region_start,
            region_end,
            num_rows_in_region,
            estimated_row_height,
            expected_rows,
            img_height
        )

        if not best_placement:
            logger.warning("Could not find valid grid placement")
            return []

        top_row_1, assumed_start_row = best_placement

        logger.info(
            f"Grid fitting: row_height={estimated_row_height:.1f}px, "
            f"top_row_1={top_row_1}, "
            f"(detected region = rows {assumed_start_row}-{assumed_start_row+num_rows_in_region-1})"
        )

        # Step 5: Generate uniform rows
        rows = []
        for i in range(expected_rows):
            y_start = int(top_row_1 + i * estimated_row_height)
            y_end = int(top_row_1 + (i + 1) * estimated_row_height)
            height = y_end - y_start

            row = RowBoundary(
                row_index=i + 1,  # 1-based
                y_start=y_start,
                y_end=y_end,
                height=height,
            )
            rows.append(row)

        return rows

    def _find_most_uniform_sequence(
        self, detected_lines: List[int]
    ) -> Optional[Tuple[int, float, int, int]]:
        """
        Find the longest sequence of uniformly-spaced lines.

        Args:
            detected_lines: Y-coordinates of detected lines (sorted)

        Returns:
            Tuple of (num_lines, avg_spacing, region_start, region_end) or None
        """
        if len(detected_lines) < 3:
            return None

        # Calculate spacings between consecutive lines
        spacings = []
        for i in range(len(detected_lines) - 1):
            spacing = detected_lines[i + 1] - detected_lines[i]
            spacings.append((i, spacing, detected_lines[i], detected_lines[i + 1]))

        # Find sequences with uniform spacing (within 20% variance)
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
            return None

        # Return longest uniform sequence
        uniform_sequences.sort(reverse=True)
        return uniform_sequences[0]

    def _find_best_grid_placement(
        self,
        region_start: int,
        region_end: int,
        num_rows_in_region: int,
        row_height: float,
        total_rows: int,
        img_height: int
    ) -> Optional[Tuple[int, int]]:
        """
        Find the best placement for the uniform grid within image bounds.

        Args:
            region_start: Y-coordinate where detected region starts
            region_end: Y-coordinate where detected region ends
            num_rows_in_region: Number of rows in detected region
            row_height: Estimated row height in pixels
            total_rows: Total number of rows to place (40)
            img_height: Image height in pixels

        Returns:
            Tuple of (top_row_1, assumed_start_row) or None
        """
        best_candidate = None
        best_score = -1

        # Try different assumptions about which rows the detected region represents
        max_start_row = max(1, total_rows - num_rows_in_region + 1)

        for start_row_num in range(1, max_start_row + 1):
            # Calculate where row 1 would be if detected region starts at start_row_num
            rows_before_region = start_row_num - 1
            estimated_top_row_1 = region_start - rows_before_region * row_height
            estimated_bottom_row_40 = estimated_top_row_1 + total_rows * row_height

            # Check if this fits within image bounds
            if estimated_top_row_1 < 0 or estimated_bottom_row_40 > img_height:
                continue

            # Score based on margins (prefer centered table)
            margin_top = estimated_top_row_1 / img_height
            margin_bottom = (img_height - estimated_bottom_row_40) / img_height

            # Require minimum margins for header/footer
            if margin_top < 0.05 or margin_bottom < 0.03:
                continue

            # Score: prefer balanced margins
            score = min(margin_top, margin_bottom)

            if score > best_score:
                best_score = score
                best_candidate = (int(estimated_top_row_1), start_row_num)

        return best_candidate

    def _detect_supplemental_rows(
        self, gray: np.ndarray, main_rows: List[RowBoundary]
    ) -> List[RowBoundary]:
        """
        Detect 2 supplemental question rows below the main table.

        Supplemental rows are in the bottom ~15-20% of the page.
        They have a different structure than main rows.

        Args:
            gray: Grayscale image
            main_rows: The 40 main data rows

        Returns:
            List of 2 supplemental RowBoundary objects, or empty list
        """
        if not main_rows:
            return []

        img_height = gray.shape[0]

        # Define supplemental section (below main table)
        supp_section_top = main_rows[-1].y_end + 50  # 50px buffer below main table
        supp_section_bottom = int(img_height * 0.97)

        if supp_section_top >= supp_section_bottom:
            logger.warning("No space for supplemental rows below main table")
            return []

        supp_section = gray[supp_section_top:supp_section_bottom, :]

        # Detect lines in supplemental section
        detected_lines_y = self._detect_horizontal_lines_morphological(supp_section)

        if len(detected_lines_y) < 2:
            logger.warning("Not enough lines detected for supplemental rows")
            return []

        # Offset to full image space
        detected_lines_y = [y + supp_section_top for y in detected_lines_y]

        # Supplemental rows are typically same height as main rows
        avg_main_row_height = sum(r.height for r in main_rows) / len(main_rows)

        # Create 2 supplemental rows using detected lines
        # Simple approach: use first two detected lines as boundaries
        if len(detected_lines_y) >= 3:
            supp_rows = [
                RowBoundary(
                    row_index=41,
                    y_start=detected_lines_y[0],
                    y_end=detected_lines_y[1],
                    height=detected_lines_y[1] - detected_lines_y[0],
                ),
                RowBoundary(
                    row_index=42,
                    y_start=detected_lines_y[1],
                    y_end=detected_lines_y[2],
                    height=detected_lines_y[2] - detected_lines_y[1],
                ),
            ]
            return supp_rows

        return []

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
    Convenience function to detect census rows using morphological operations.

    Args:
        image: Input image (array or path)
        expected_rows: Expected number of rows (default: 40)
        **options: Detector options

    Returns:
        List of RowBoundary objects

    Example:
        >>> rows = detect_census_rows("census_1940.jpg")
        >>> print(f"Detected {len(rows)} rows")
    """
    detector = MorphologicalRowDetector(expected_rows=expected_rows, **options)

    # Load image if path provided
    if isinstance(image, (str, Path)):
        image = cv2.imread(str(image))
        if image is None:
            raise ValueError(f"Failed to load image: {image}")

    return detector.detect_rows(image)
