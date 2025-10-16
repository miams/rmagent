"""
Analyze census image to understand column structure.

This script will:
1. Load a census image
2. Detect vertical lines (column separators)
3. Show where each column is located
4. Save annotated image for review

Run this to understand your census images before building the detector.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import cv2
import numpy as np


def analyze_census_image(image_path: str, output_path: str = None):
    """
    Analyze census image to find column structure.

    Args:
        image_path: Path to census image
        output_path: Optional path to save annotated image
    """
    print(f"Analyzing: {Path(image_path).name}\n")

    # Load image
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    print(f"Image size: {img.shape[1]} x {img.shape[0]} pixels (width x height)")
    print()

    # Detect vertical lines (column separators)
    print("Detecting vertical lines (columns)...")
    print("Strategy: Using Canny edge detection + Hough line transform")
    print()

    # Apply adaptive thresholding to handle varying contrast
    thresh_binary = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )

    # Detect edges
    edges = cv2.Canny(thresh_binary, 50, 150, apertureSize=3)

    # Detect vertical lines using Hough Line Transform
    lines = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=100,
        minLineLength=img.shape[0] * 0.2,  # At least 20% of image height
        maxLineGap=50,
    )

    # Extract X positions of vertical lines (filter for near-vertical lines)
    vertical_positions = []
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            # Check if line is approximately vertical (slope > 5)
            if abs(x2 - x1) < 10:  # Very small horizontal change
                x_pos = (x1 + x2) // 2
                vertical_positions.append(x_pos)

    # Cluster nearby lines (merge lines within 20 pixels of each other)
    def cluster_positions(positions, min_gap=20):
        """Merge positions that are within min_gap pixels of each other."""
        if not positions:
            return []

        positions = sorted(set(positions))
        clustered = [positions[0]]

        for pos in positions[1:]:
            if pos - clustered[-1] > min_gap:
                clustered.append(pos)

        return clustered

    vertical_positions = cluster_positions(vertical_positions, min_gap=20)

    print(f"Found {len(vertical_positions)} vertical lines at X positions (after clustering):")
    for i, x in enumerate(vertical_positions):
        print(f"  Line {i}: X = {x}")
    print()

    # Detect horizontal lines (row separators)
    print("Detecting horizontal lines (rows)...")
    print()

    # Detect horizontal lines using Hough Line Transform (reuse edges from above)
    lines_h = cv2.HoughLinesP(
        edges,
        rho=1,
        theta=np.pi / 180,
        threshold=200,  # Higher threshold for rows (longer lines)
        minLineLength=img.shape[1] * 0.3,  # At least 30% of image width
        maxLineGap=100,
    )

    # Extract Y positions of horizontal lines
    horizontal_positions = []
    if lines_h is not None:
        for line in lines_h:
            x1, y1, x2, y2 = line[0]
            # Check if line is approximately horizontal (small vertical change)
            if abs(y2 - y1) < 10:  # Very small vertical change
                y_pos = (y1 + y2) // 2
                horizontal_positions.append(y_pos)

    # Cluster horizontal lines too (merge within 10 pixels for tighter grouping)
    horizontal_positions = cluster_positions(horizontal_positions, min_gap=10)

    print(f"Found {len(horizontal_positions)} horizontal lines (after clustering)")
    print(f"  First 10 Y positions: {horizontal_positions[:10]}")
    print()

    # Create annotated image
    annotated = img.copy()

    # Draw vertical lines in red
    for x in vertical_positions:
        cv2.line(annotated, (x, 0), (x, img.shape[0]), (0, 0, 255), 2)

    # Draw horizontal lines in blue
    for y in horizontal_positions:
        cv2.line(annotated, (0, y), (img.shape[1], y), (255, 0, 0), 2)

    # Identify columns (spaces between vertical lines)
    print("Column boundaries:")
    columns = []
    for i in range(len(vertical_positions) - 1):
        x_start = vertical_positions[i]
        x_end = vertical_positions[i + 1]
        width = x_end - x_start
        columns.append((x_start, x_end, width))
        print(f"  Column {i}: X {x_start:4d} to {x_end:4d} (width: {width:4d} px)")
    print()

    # Identify rows (spaces between horizontal lines)
    print(f"Estimated {len(horizontal_positions) - 1} rows in table")
    print()

    # Show column widths distribution
    print("Column width statistics:")
    widths = [w for _, _, w in columns]
    if widths:
        print(f"  Narrowest column: {min(widths)} px")
        print(f"  Widest column: {max(widths)} px")
        print(f"  Average width: {sum(widths) / len(widths):.0f} px")
    print()

    # Save annotated image
    if output_path:
        cv2.imwrite(output_path, annotated)
        print(f"✅ Saved annotated image to: {output_path}")
    else:
        output_path = str(Path(image_path).parent / f"{Path(image_path).stem}_annotated.jpg")
        cv2.imwrite(output_path, annotated)
        print(f"✅ Saved annotated image to: {output_path}")

    print()
    print("=" * 70)
    print("NEXT STEPS:")
    print("=" * 70)
    print("1. Open the annotated image to see column/row detection")
    print("2. Verify the red lines match census column boundaries")
    print("3. Count columns from left to right")
    print("4. Match columns to census fields (Name, Age, etc.)")
    print("=" * 70)

    return {
        "vertical_positions": vertical_positions,
        "horizontal_positions": horizontal_positions,
        "columns": columns,
        "image_width": img.shape[1],
        "image_height": img.shape[0],
    }


if __name__ == "__main__":
    # Test image
    test_image = "/Users/miams/Genealogy/RootsMagic/Files/Records - Census/1940 Federal/1940, Wyoming, Fremont - Iiams, Clara.jpg"

    print("=" * 70)
    print("Census Image Layout Analyzer")
    print("=" * 70)
    print()

    result = analyze_census_image(test_image)

    print()
    print("Analysis complete!")
    print(f"Review the annotated image to see detected columns and rows.")
