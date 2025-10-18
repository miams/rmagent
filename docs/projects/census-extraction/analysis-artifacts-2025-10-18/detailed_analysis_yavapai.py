"""Detailed step-by-step analysis of detection process for Yavapai image."""
import sys
from pathlib import Path
import cv2
import numpy as np

# Add rmagent to path
sys.path.insert(0, str(Path.home() / "Code/RM11"))

img_path = Path.home() / "Genealogy/RootsMagic/Files/Records - Census/1940 Federal/1940, Arizona, Yavapai - Ijams, Edward.jpg"
OUTPUT_DIR = Path("/tmp/yavapai_analysis")
OUTPUT_DIR.mkdir(exist_ok=True)

img = cv2.imread(str(img_path))
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
img_height, img_width = gray.shape

print("=" * 80)
print("DETAILED ANALYSIS: 1940, Arizona, Yavapai - Ijams, Edward.jpg")
print("=" * 80)
print()

print("STEP 1: IMAGE PROPERTIES")
print("-" * 80)
print(f"  Image dimensions: {img_width} x {img_height} pixels")
print(f"  Image saved: {OUTPUT_DIR / '1_original.jpg'}")
cv2.imwrite(str(OUTPUT_DIR / "1_original.jpg"), img)
print()

print("STEP 2: DEFINE REGIONS")
print("-" * 80)
header = (0, int(img_height * 0.15))
top_transition = (int(img_height * 0.15) + 150, int(img_height * 0.25) + 150)
main_table = (int(img_height * 0.25) + 150, int(img_height * 0.80))
bottom_transition = (int(img_height * 0.80), int(img_height * 0.85))

print(f"  Header region:          y={header[0]:4d} to y={header[1]:4d}")
print(f"  Top transition region:  y={top_transition[0]:4d} to y={top_transition[1]:4d}  ← FOCUS")
print(f"  Main table region:      y={main_table[0]:4d} to y={main_table[1]:4d}")
print(f"  Bottom transition:      y={bottom_transition[0]:4d} to y={bottom_transition[1]:4d}")
print()

# Visualize regions
vis = img.copy()
cv2.rectangle(vis, (0, header[0]), (img_width, header[1]), (128, 128, 128), 5)
cv2.putText(vis, "HEADER", (50, header[1] - 50), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (128, 128, 128), 5)

cv2.rectangle(vis, (0, top_transition[0]), (img_width, top_transition[1]), (0, 255, 255), 5)
cv2.putText(vis, "TOP TRANSITION (FIRST BOUNDARY)", (50, top_transition[0] + 100),
            cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 255, 255), 5)

cv2.rectangle(vis, (0, main_table[0]), (img_width, main_table[1]), (0, 255, 0), 5)
cv2.putText(vis, "MAIN TABLE", (50, main_table[0] + 100), cv2.FONT_HERSHEY_SIMPLEX, 2.0, (0, 255, 0), 5)

cv2.imwrite(str(OUTPUT_DIR / "2_regions.jpg"), vis)
print(f"  Regions visualized: {OUTPUT_DIR / '2_regions.jpg'}")
print()

print("STEP 3: EXTRACT TOP TRANSITION REGION")
print("-" * 80)
y_start, y_end = top_transition
region_img = gray[y_start:y_end, :]
print(f"  Extracted region: {region_img.shape[1]} x {region_img.shape[0]} pixels")
cv2.imwrite(str(OUTPUT_DIR / "3_top_transition_region.jpg"), region_img)
print(f"  Region saved: {OUTPUT_DIR / '3_top_transition_region.jpg'}")
print()

print("STEP 4: ADAPTIVE THRESHOLDING")
print("-" * 80)
print(f"  Method: ADAPTIVE_THRESH_MEAN_C, THRESH_BINARY_INV")
print(f"  Block size: 15, Constant: 2")
thresh = cv2.adaptiveThreshold(
    region_img, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
    cv2.THRESH_BINARY_INV, 15, 2
)
cv2.imwrite(str(OUTPUT_DIR / "4_thresholded.jpg"), thresh)
print(f"  Result: {OUTPUT_DIR / '4_thresholded.jpg'}")
print(f"  Effect: Converts grayscale to binary (black text/lines on white)")
print()

print("STEP 5: MORPHOLOGICAL DETECTION (HORIZONTAL KERNEL)")
print("-" * 80)
kernel_width = img_width // 120
print(f"  Kernel width ratio: 120")
print(f"  Kernel width: {img_width} / 120 = {kernel_width} pixels")
print(f"  Kernel shape: ({kernel_width}, 1) - detects horizontal features")
print(f"  Operation: MORPH_OPEN with 2 iterations")
horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_width, 1))
detected_lines_img = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
cv2.imwrite(str(OUTPUT_DIR / "5_morphological_lines.jpg"), detected_lines_img)
print(f"  Result: {OUTPUT_DIR / '5_morphological_lines.jpg'}")
print(f"  Effect: Isolates horizontal line segments, removes noise")
print()

print("STEP 6: FIND CONTOURS (LINE SEGMENTS)")
print("-" * 80)
contours, _ = cv2.findContours(detected_lines_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print(f"  Found {len(contours)} contours (line segments)")

all_segments = []
for contour in contours:
    x, y, w, h = cv2.boundingRect(contour)
    line_y = y + h // 2
    all_segments.append({'x': x, 'y': line_y, 'x_end': x + w, 'width': w, 'height': h})

print(f"  Extracted {len(all_segments)} segment properties")

# Visualize segments
vis_segments = cv2.cvtColor(region_img, cv2.COLOR_GRAY2BGR)
for seg in all_segments:
    cv2.rectangle(vis_segments, (seg['x'], seg['y'] - seg['height']//2),
                  (seg['x_end'], seg['y'] + seg['height']//2), (0, 255, 0), 2)
cv2.imwrite(str(OUTPUT_DIR / "6_segments.jpg"), vis_segments)
print(f"  Segments visualized: {OUTPUT_DIR / '6_segments.jpg'} (green boxes)")
print()

print("STEP 7: GROUP SEGMENTS BY Y-COORDINATE")
print("-" * 80)
print(f"  Tolerance: 5 pixels")

def group_segments_by_y(segments, tolerance=5):
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

segment_groups = group_segments_by_y(all_segments)
print(f"  Grouped {len(all_segments)} segments into {len(segment_groups)} lines")

# Visualize groups
vis_groups = cv2.cvtColor(region_img, cv2.COLOR_GRAY2BGR)
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255),
          (0, 255, 255), (128, 0, 0), (0, 128, 0), (0, 0, 128)]
for i, group in enumerate(segment_groups):
    color = colors[i % len(colors)]
    avg_y = int(np.mean([s['y'] for s in group]))
    cv2.line(vis_groups, (0, avg_y), (region_img.shape[1], avg_y), color, 3)
    cv2.putText(vis_groups, f"Line {i+1} ({len(group)} segs)", (10, avg_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
cv2.imwrite(str(OUTPUT_DIR / "7_grouped_lines.jpg"), vis_groups)
print(f"  Groups visualized: {OUTPUT_DIR / '7_grouped_lines.jpg'}")
print()

print("STEP 8: DEFINE COLUMN BOUNDARIES")
print("-" * 80)
line_numbers_start = img_width * 0.08
line_numbers_end = img_width * 0.12
blank_column_start = img_width * 0.11
blank_column_end = img_width * 0.123

print(f"  Line numbers column:  {line_numbers_start:6.1f} to {line_numbers_end:6.1f} pixels ({line_numbers_start/img_width*100:.1f}% to {line_numbers_end/img_width*100:.1f}%)")
print(f"  Blank column (Col 1): {blank_column_start:6.1f} to {blank_column_end:6.1f} pixels ({blank_column_start/img_width*100:.1f}% to {blank_column_end/img_width*100:.1f}%)")

# Visualize columns
vis_columns = cv2.cvtColor(region_img, cv2.COLOR_GRAY2BGR)
cv2.line(vis_columns, (int(line_numbers_start), 0), (int(line_numbers_start), region_img.shape[0]), (255, 0, 255), 3)
cv2.putText(vis_columns, "8%", (int(line_numbers_start) + 10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 255), 3)

cv2.line(vis_columns, (int(line_numbers_end), 0), (int(line_numbers_end), region_img.shape[0]), (255, 0, 255), 3)
cv2.putText(vis_columns, "12%", (int(line_numbers_end) + 10, 200), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 255), 3)

cv2.line(vis_columns, (int(blank_column_start), 0), (int(blank_column_start), region_img.shape[0]), (0, 255, 255), 3)
cv2.putText(vis_columns, "11%", (int(blank_column_start) + 10, 300), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)

cv2.line(vis_columns, (int(blank_column_end), 0), (int(blank_column_end), region_img.shape[0]), (0, 255, 255), 3)
cv2.putText(vis_columns, "12.3%", (int(blank_column_end) + 10, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 255), 3)

cv2.imwrite(str(OUTPUT_DIR / "8_column_boundaries.jpg"), vis_columns)
print(f"  Columns visualized: {OUTPUT_DIR / '8_column_boundaries.jpg'}")
print()

print("STEP 9: ANALYZE EACH LINE GROUP (CANDIDATE DETECTION)")
print("-" * 80)
print(f"  Criteria for candidates:")
print(f"    - Has segment in line numbers area (8-12%)")
print(f"    - Span > 50% of image width")
print(f"    - Max height > 3 pixels")
print()

candidates = []
for i, group in enumerate(segment_groups):
    avg_y = int(np.mean([s['y'] for s in group]))
    full_y = y_start + avg_y
    max_height = max(s['height'] for s in group)

    has_line_numbers = any(line_numbers_start < s['x'] < line_numbers_end for s in group)
    has_blank_column = any(blank_column_start < s['x'] < blank_column_end for s in group)

    min_x = min(s['x'] for s in group)
    max_x_end = max(s['x_end'] for s in group)
    span = max_x_end - min_x
    span_pct = span / img_width * 100

    is_candidate = (has_line_numbers and span_pct > 50 and max_height > 3)

    print(f"  Line {i+1}:")
    print(f"    Y (region): {avg_y:4d}, Y (full): {full_y:4d}")
    print(f"    Segments: {len(group)}, Max height: {max_height}px")
    print(f"    Span: {span_pct:.1f}% of width")
    print(f"    Has line numbers: {has_line_numbers}")
    print(f"    Has blank column: {has_blank_column}")
    print(f"    → Candidate: {is_candidate}")

    if is_candidate:
        candidates.append({
            'line_num': i + 1,
            'y': avg_y,
            'full_y': full_y,
            'max_height': max_height,
            'has_line_numbers': has_line_numbers,
            'has_blank_column': has_blank_column,
            'num_segments': len(group)
        })
    print()

print(f"RESULT: {len(candidates)} candidates found")
print()

print("STEP 10: CALCULATE GAPS BETWEEN CANDIDATES")
print("-" * 80)
for i in range(len(candidates)):
    if i < len(candidates) - 1:
        gap_after = candidates[i+1]['full_y'] - candidates[i]['full_y']
        candidates[i]['gap_after'] = gap_after

        if i > 0:
            gap_before = candidates[i]['full_y'] - candidates[i-1]['full_y']
            candidates[i]['gap_ratio'] = gap_after / gap_before if gap_before > 0 else 0
        else:
            candidates[i]['gap_ratio'] = 0

        print(f"  Candidate {i+1}: Gap after = {gap_after}px")
        if i > 0:
            print(f"             Gap ratio = {candidates[i]['gap_ratio']:.2f}x")
    else:
        candidates[i]['gap_after'] = 0
        candidates[i]['gap_ratio'] = 0

print()

print("STEP 11: MULTI-CRITERIA DETECTION")
print("-" * 80)
print("  Criterion 1: BLANK COLUMN (most reliable)")
blank_column_lines = [c for c in candidates if c['has_blank_column']]
print(f"    Candidates with blank column: {len(blank_column_lines)}")
if blank_column_lines:
    for c in blank_column_lines:
        print(f"      - Line {c['line_num']}: y={c['full_y']}")

first_boundary = None
method = None

if blank_column_lines:
    first_boundary = min(blank_column_lines, key=lambda c: c['y'])
    method = "blank_column"
    print(f"    ✓ DETECTED via blank_column: Line {first_boundary['line_num']}, y={first_boundary['full_y']}")
else:
    print(f"    ✗ No blank column candidates")

print()

if not first_boundary and len(candidates) >= 2:
    print("  Criterion 2: SPACING RATIO (fallback)")
    spacing_candidates = [c for c in candidates if c['gap_ratio'] > 1.5]
    print(f"    Candidates with gap_ratio > 1.5x: {len(spacing_candidates)}")
    if spacing_candidates:
        for c in spacing_candidates:
            print(f"      - Line {c['line_num']}: gap_ratio={c['gap_ratio']:.2f}x")
        first_boundary = spacing_candidates[0]
        method = "spacing_ratio"
        print(f"    ✓ DETECTED via spacing_ratio: Line {first_boundary['line_num']}, y={first_boundary['full_y']}")
    else:
        print(f"    ✗ No spacing ratio candidates")
    print()

if not first_boundary:
    print("  Criterion 3: THICKNESS FALLBACK")
    if len(candidates) >= 2:
        sorted_by_height = sorted(candidates, key=lambda c: c['max_height'], reverse=True)
        first_boundary = sorted_by_height[1]
        method = "thickness_fallback"
        print(f"    ✓ DETECTED via thickness_fallback: Line {first_boundary['line_num']}, y={first_boundary['full_y']}")
    elif len(candidates) == 1:
        first_boundary = candidates[0]
        method = "single_candidate"
        print(f"    ✓ DETECTED via single_candidate: Line {first_boundary['line_num']}, y={first_boundary['full_y']}")
    print()

print("=" * 80)
print("FINAL DECISION")
print("=" * 80)
if first_boundary:
    print(f"  ✓ FIRST TABLE BOUNDARY DETECTED")
    print(f"    Method: {method}")
    print(f"    Line number: {first_boundary['line_num']}")
    print(f"    Y position (full image): {first_boundary['full_y']}")
    print(f"    Height: {first_boundary['max_height']}px")
    print(f"    Has blank column: {first_boundary['has_blank_column']}")
else:
    print(f"  ✗ NO FIRST TABLE BOUNDARY DETECTED")
print()

# Create final visualization
vis_final = img.copy()

# Draw all regions
cv2.line(vis_final, (0, top_transition[0]), (img_width, top_transition[0]), (255, 255, 0), 3)
cv2.line(vis_final, (0, top_transition[1]), (img_width, top_transition[1]), (255, 255, 0), 3)

# Draw column boundaries
cv2.line(vis_final, (int(line_numbers_start), 0), (int(line_numbers_start), img_height), (255, 0, 255), 2)
cv2.line(vis_final, (int(blank_column_start), 0), (int(blank_column_start), img_height), (0, 255, 255), 2)
cv2.line(vis_final, (int(blank_column_end), 0), (int(blank_column_end), img_height), (0, 255, 255), 2)

# Draw all candidates
for i, cand in enumerate(candidates):
    if cand == first_boundary:
        color = (0, 0, 255)  # RED
        thickness = 8
        label = f"FIRST BOUNDARY (Line {cand['line_num']}, {method})"
    elif cand.get('has_blank_column'):
        color = (255, 128, 0)  # Orange
        thickness = 4
        label = f"Cand {i+1} (has blank col)"
    else:
        color = (0, 255, 0)  # Green
        thickness = 3
        label = f"Cand {i+1}"

    cv2.line(vis_final, (0, cand['full_y']), (img_width, cand['full_y']), color, thickness)
    cv2.putText(vis_final, label, (50, cand['full_y'] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 2.0, color, 4)

# Zoom to region of interest
zoom_start = max(0, top_transition[0] - 200)
zoom_end = min(img_height, top_transition[1] + 400)
zoom = vis_final[zoom_start:zoom_end, :].copy()

cv2.imwrite(str(OUTPUT_DIR / "9_final_detection.jpg"), zoom)
print(f"Final detection saved: {OUTPUT_DIR / '9_final_detection.jpg'}")
print()

print(f"All analysis images saved to: {OUTPUT_DIR}")
