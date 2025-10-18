# Census Row Detection Analysis - October 18, 2025

**Status**: Current state analysis and critical issues identified
**Test Dataset**: 179 1940 Federal Census images
**Success Rate**: 155/179 (86.6%) - but with fundamental flaws
**Reference Image**: `1940, Arizona, Yavapai - Ijams, Edward.jpg`

---

## Executive Summary

The current morphological row detection approach achieves 86.6% success rate on 179 images, but detailed analysis reveals **critical systematic errors** that undermine the reported success rate. The Yavapai image was marked as "success" despite having the first boundary line incorrectly placed in the 3rd data row, demonstrating that our success criteria are too lenient.

**Most Critical Issue**: Non-deterministic behavior between analysis runs indicates a fundamental algorithmic problem that must be resolved before production use.

---

## Detailed Analysis: Yavapai Image

### Test Setup

**Image**: `1940, Arizona, Yavapai - Ijams, Edward.jpg`
**Dimensions**: 5854 x 4505 pixels
**Analysis Location**: `docs/projects/census-extraction/analysis-artifacts-2025-10-18/`
**Test Result Location**: `data/census/images/full_179_annotated/success/` (local only, .gitignored)

### Analysis Process

Complete step-by-step analysis documented in 9 images showing:
1. Original image with region boundaries
2. Adaptive thresholding (binary conversion)
3. Morphological line detection
4. Segment grouping (77 segments → 13 lines)
5. Column boundary identification
6. Candidate evaluation
7. Multi-criteria detection decision
8. Final boundary placement

**Reference Files**:
- Analysis script: `docs/projects/census-extraction/analysis-artifacts-2025-10-18/detailed_analysis_yavapai.py`
- Output images: `docs/projects/census-extraction/analysis-artifacts-2025-10-18/1_original.jpg` through `9_final_detection.jpg`

---

## Critical Issues Identified

### Issue A: Main Table Region Extends Too Far ⚠️ HIGH PRIORITY

**Problem**:
The Main Table region (15%+150px to 80% of image height) extends into the Supplemental Questions table header.

**Current Boundaries** (for Yavapai image):
- Main table region: y=1276 to y=3604 (2,328 pixels tall)
- Bottom transition: y=3604 to y=3829 (225 pixels)
- Supplemental region: y=3829 to y=4505 (676 pixels)

**Issue**:
The main table should ONLY contain the 40 data rows (100% positive census table). Currently it includes part of the supplemental questions header, causing:
- False line detections in supplemental header
- Incorrect row height calculations
- Bottom boundary detection failures

**Recommended Fix**:
```python
# Current (WRONG)
'main_table': (int(img_height * 0.25) + 150, int(img_height * 0.80))

# Proposed (CORRECT)
'main_table': (int(img_height * 0.25) + 150, int(img_height * 0.80) - 250)
'bottom_transition': (int(img_height * 0.80) - 250, int(img_height * 0.85))
```

**Validation Required**: Test on all 179 images to confirm 250px adjustment is universal.

**Impact**: MEDIUM - Affects row 40 detection and grid uniformity calculations

**File to Update**: `rmagent/census/pipelines/preprocessing/region_guided_detector.py:184-186`

---

### Issue B: Single-Segment False Positives ⚠️ MEDIUM PRIORITY

**Problem**:
Lines detected from single segments (like Line 7 in `7_grouped_lines.jpg`) are false positives caused by horizontal handwriting strokes.

**Example** (Yavapai image):
- Line 7: Only 1 segment, width=2.6% (151 pixels)
- Caused by handwritten text with horizontal stroke
- Should not be considered a valid table boundary

**Current Logic**:
```python
# No minimum segment requirement
is_candidate = (has_line_numbers and span_pct > 50 and max_height > 3)
```

**Recommended Fix**:
```python
def _is_valid_line(self, segments, img_width):
    """Validate that segments represent a real table line, not handwriting."""

    # Require at minimum 2 segments
    if len(segments) < 2:
        return False

    # Segments must be separated by at least 500px horizontally
    sorted_segs = sorted(segments, key=lambda s: s['x'])
    if len(segments) >= 2:
        max_separation = max(
            sorted_segs[i+1]['x'] - sorted_segs[i]['x_end']
            for i in range(len(sorted_segs) - 1)
        )
        if max_separation < 500:
            return False

    return True
```

**Impact**: MEDIUM - Prevents ~5-10% of false positive line detections

**File to Update**: `rmagent/census/pipelines/preprocessing/region_guided_detector.py:285-286`

---

### Issue C: Inaccurate Column Boundary Detection ⚠️ HIGH PRIORITY

**Problem**:
The blank column detection (11-12.3% of width) is fundamentally flawed. Visual inspection of `8_column_boundaries.jpg` shows:
- Vertical reference lines don't align with actual column boundaries
- Blank column area is too narrow or misaligned
- This causes the primary detection criterion (blank column segments) to fail

**Current Logic**:
```python
blank_column_start = img_width * 0.11   # 644px for Yavapai
blank_column_end = img_width * 0.123    # 720px for Yavapai
# Total width: 76 pixels
```

**Root Cause**:
The column positions were identified using a numbered grid on one test image (Pennsylvania), but:
1. May not generalize to all census sheets (different scanners, states, printers)
2. The actual blank column may be wider than 76 pixels
3. Line numbers column and blank column boundaries may vary by image

**Recommended Investigation**:
1. Manually measure blank column on 10 diverse images (different states)
2. Calculate statistics (mean, std dev) of column positions
3. Determine if positions are image-dependent (require detection) or universal (can hardcode)

**Proposed Adaptive Detection**:
```python
def _detect_blank_column_boundaries(self, gray, img_width):
    """Detect blank column boundaries by analyzing vertical whitespace."""

    # Sample vertical strips in expected column area (8-15% of width)
    search_start = int(img_width * 0.08)
    search_end = int(img_width * 0.15)

    # For each vertical position, count white pixels in middle rows
    vertical_profile = []
    for x in range(search_start, search_end):
        column = gray[img_height//3:img_height*2//3, x]
        white_ratio = np.sum(column > 200) / len(column)
        vertical_profile.append(white_ratio)

    # Find region with highest white ratio (blank column)
    # Return adaptive boundaries
    ...
```

**Impact**: HIGH - This is the primary detection criterion; fixing it could improve success rate from 86% to 95%+

**Status**: REQUIRES MANUAL DATA COLLECTION before implementing solution

---

### Issue D: Non-Deterministic Behavior ⚠️ CRITICAL PRIORITY

**Problem**:
The **SAME IMAGE** produces **DIFFERENT RESULTS** between the detailed analysis and the full test run.

**Evidence**:
1. **Detailed Analysis** (see `analysis-artifacts-2025-10-18/9_final_detection.jpg`):
   - First Boundary detected at y=965 (Line 4)
   - Method: spacing_ratio
   - Result: **CORRECT** - top of first data row

2. **Full 179 Test** (local test outputs, not in repository):
   - First Boundary placed in 3rd data row (visual inspection)
   - Many subsequent rows misaligned
   - Result: **INCORRECT** - yet marked as "success"

**Root Cause Analysis**:

This is **NOT acceptable** for production use. Possible causes:

1. **Random seed not set**: Data augmentation or random operations without fixed seed
2. **Floating-point instability**: np.mean() or similar operations with inconsistent rounding
3. **Dictionary iteration order**: Python dicts are ordered (3.7+), but set operations might not be
4. **Concurrency issues**: If using multiprocessing without proper synchronization
5. **File system race condition**: Reading files in non-deterministic order

**Investigation Steps**:

```python
# 1. Add seed fixing at top of detector
import random
import numpy as np

random.seed(42)
np.random.seed(42)

# 2. Add debug logging to track decision points
logger.debug(f"Segments found: {len(all_segments)}")
logger.debug(f"Grouped into: {len(segment_groups)} lines")
logger.debug(f"Candidates: {[(c['line_num'], c['full_y']) for c in candidates]}")
logger.debug(f"Blank column lines: {len(blank_column_lines)}")
logger.debug(f"First boundary: {first_boundary['full_y'] if first_boundary else None}")

# 3. Compare debug output between runs
```

**Recommended Fix Priority**: **IMMEDIATE** - Cannot proceed until determinism is guaranteed

**Impact**: CRITICAL - Undermines all testing and validation

---

### Issue E: False Success Criteria ⚠️ HIGH PRIORITY

**Problem**:
Yavapai image was marked as "success" (40 rows detected) despite having the first boundary line incorrectly placed in the 3rd data row.

**Current Success Criteria**:
```python
if len(rows) == 40:
    results['success'].append(img_path.name)
```

**Why This is Wrong**:
- Detecting 40 rows doesn't mean they're the CORRECT 40 rows
- If first boundary is off by 2 rows, all subsequent rows are misaligned
- OCR on misaligned rows will extract wrong data (row N data attributed to person in row N±2)

**Recommended Fix**:

Need **validation metrics** beyond just row count:

```python
def validate_detection_quality(rows, img_height):
    """Validate that detected rows are plausible."""

    if len(rows) != 40:
        return False, "Wrong row count"

    # 1. Check row height consistency
    heights = [row.height for row in rows]
    median_height = np.median(heights)
    outliers = sum(1 for h in heights if abs(h - median_height) > median_height * 0.3)
    if outliers > 5:
        return False, f"Too many height outliers ({outliers})"

    # 2. Check first row position (should be ~15-20% down the image)
    first_row_pct = rows[0].y_start / img_height
    if not (0.15 < first_row_pct < 0.25):
        return False, f"First row at {first_row_pct*100:.1f}% (expect 15-25%)"

    # 3. Check last row position (should be ~80-85% down)
    last_row_pct = rows[-1].y_end / img_height
    if not (0.75 < last_row_pct < 0.90):
        return False, f"Last row at {last_row_pct*100:.1f}% (expect 75-90%)"

    # 4. Check uniform spacing
    gaps = [rows[i+1].y_start - rows[i].y_end for i in range(len(rows)-1)]
    if max(gaps) > median_height * 2:
        return False, f"Excessive gap detected ({max(gaps)}px)"

    return True, "Valid"

# Usage
is_valid, reason = validate_detection_quality(rows, img_height)
if is_valid:
    results['success'].append(img_path.name)
else:
    results['failed'].append((img_path.name, reason))
```

**Expected Impact**:
- Success rate will DROP from 86.6% to ~70-75% (revealing hidden failures)
- But we'll have honest metrics
- Can then focus on fixing real issues

**File to Update**: Test validation logic (can be integrated into detector or test scripts)

---

## Additional Observations

### Line Consolidation Needed

In `7_grouped_lines.jpg`, the algorithm correctly detected the first 4 row boundaries, but:
- Some lines are doubled (within 5px of each other)
- These need to be consolidated to single representatives
- Current grouping tolerance (5px) works, but needs better selection of representative Y-coordinate

**Current Logic**:
```python
def _cluster_lines(self, y_positions: List[int], distance: int = 5) -> List[int]:
    # Takes mean of cluster - good approach
    return [int(np.mean(cluster)) for cluster in clusters]
```

**Recommendation**: This part is working correctly. Issue is upstream (filtering before clustering).

---

## Recommended Action Plan

### Immediate (Week 1)
1. **Fix Issue D (Non-determinism)** ← BLOCKING
   - Add debug logging to track decision variations
   - Set random seeds
   - Run same image 10 times, verify identical output
   - Document root cause

2. **Implement Issue E (Validation Metrics)**
   - Add quality validation function
   - Re-run 179 test with honest metrics
   - Document true success rate

### Short-term (Week 2)
3. **Fix Issue B (Single-segment filtering)**
   - Implement 2-segment minimum with 500px separation
   - Test on 179 images
   - Measure improvement

4. **Investigate Issue C (Column boundaries)**
   - Manually measure blank column on 10 diverse images
   - Calculate statistics
   - Determine if adaptive detection is needed

### Medium-term (Week 3-4)
5. **Fix Issue A (Region boundaries)**
   - Adjust main_table and bottom_transition regions
   - Test on 179 images
   - Validate row 40 detection improves

6. **Re-evaluate success rate with all fixes**
   - Target: 95%+ with honest validation metrics

---

## Files Preserved

**Analysis Scripts** (in repository):
- `docs/projects/census-extraction/analysis-artifacts-2025-10-18/detailed_analysis_yavapai.py` - Complete step-by-step analysis framework

**Analysis Output** (in repository):
- `docs/projects/census-extraction/analysis-artifacts-2025-10-18/` - 9 processing step images and test results

**Local Test Outputs** (.gitignored, not in repository):
- `data/census/images/yavapai_analysis/` - Yavapai reference outputs
- `data/census/images/full_179_annotated/success/` - 155 "successful" detections
- `data/census/images/full_179_annotated/failed/` - 24 failed detections

**Documentation** (in repository):
- This file: `docs/projects/census-extraction/row-detection-analysis-2025-10-18.md`
- Summary: `docs/projects/census-extraction/morphological-segmentation-summary.md`

---

## Response to Feedback

### On Issue A (Region boundaries)
**Agreed**. The 250px adjustment makes sense. The main table region should be 100% data rows with no contamination from supplemental questions. This will improve:
- Row height uniformity calculations
- Bottom boundary detection
- Median spacing accuracy

**Risk**: Some census sheets may have varying amounts of whitespace. Need to validate 250px works across all 179 images, not just Yavapai.

### On Issue B (Single-segment false positives)
**Excellent catch**. The 2-segment minimum with 500px separation is a simple, effective filter. This addresses ~10% of false positives with minimal computational cost.

**Implementation note**: Should apply this filter BEFORE grouping, not after:
```python
# In _detect_lines_in_region, after finding contours
valid_segments = []
for contour in contours:
    x, y, w, h = cv2.boundingRect(contour)
    if w > img_width * 0.15:  # Existing width check
        valid_segments.append({'x': x, 'y': y, ...})

# Then validate multi-segment requirement during grouping
```

### On Issue C (Column boundaries)
**This is the crux of the problem**. You're right - we need a better way to communicate/visualize this. Options:

1. **Interactive annotation tool**: Load census image, click to mark column boundaries, save coordinates
2. **Automated detection**: Analyze vertical whitespace profiles to find blank column
3. **Manual measurement study**: Measure 20 images by hand, find patterns

I recommend approach #2 (automated detection) since column positions likely vary by scanner/printer. The blank column should have higher whitespace density than adjacent columns - this is detectable.

### On Issue D (Non-determinism)
**This is the most concerning issue**. A few hypotheses:

1. **Set operations**: The `set(top_lines + main_lines + bottom_lines)` in line 142 of region_guided_detector.py doesn't guarantee order
2. **Floating-point rounding**: np.mean() might round differently based on input order
3. **File iteration order**: glob() doesn't guarantee order across runs

**Fix**: Add deterministic sorting at every step:
```python
# Line 142 - ensure deterministic ordering
all_lines = sorted(set(top_lines + main_lines + bottom_lines))
```

But the detailed analysis ran the SAME detector code path as the full test. Need to diff the exact execution to find divergence.

### On Issue E (False success criteria)
**Absolutely correct**. 86.6% "success" rate is misleading if many successes have misaligned rows. The validation metrics I proposed will reveal the true quality.

**Expected outcome**: Success rate drops to 70-75%, but we'll know which images are truly usable for OCR.

---

## Conclusion

The Yavapai detailed analysis was invaluable for exposing these systematic issues. The current 86.6% success rate is **not production-ready** due to:

1. Non-deterministic behavior (CRITICAL)
2. False success criteria hiding misaligned rows (HIGH)
3. Inaccurate column boundary detection (HIGH)

**Next immediate step**: Fix non-determinism and implement honest validation metrics to establish true baseline performance.

**Estimated timeline to production-ready (95%+ with validated quality)**:
- 3-4 weeks with focused effort on Issues A-E
- Alternative: 2-3 weeks to collect 50 annotated images and train ML model

---

## Preservation Note

This analysis represents the state of census row detection as of October 18, 2025. It documents both the achievements (multi-criteria first boundary detection working in isolated testing) and critical flaws (non-determinism, validation gaps) that must be addressed before production deployment.

**All analysis scripts and output images should be preserved** for:
- Historical reference
- Regression testing after fixes
- Training data for future ML approaches
- Documentation of decision-making process
