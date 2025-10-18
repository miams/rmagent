# Census Row Detection Analysis Artifacts - October 18, 2025

## Overview

This directory preserves the complete analysis of the morphological row detection approach tested on 179 1940 Federal Census images. The analysis revealed critical systematic errors that must be addressed before production use.

## Key Finding

**The 86.6% "success rate" is misleading** - detailed examination of a successful image (Yavapai) revealed:
- First boundary line incorrectly placed in 3rd data row
- Non-deterministic behavior between runs (same image, different results)
- False success criteria (40 rows detected ≠ correct 40 rows)

## Files in This Directory

### Analysis Script
- `detailed_analysis_yavapai.py` - Complete step-by-step analysis framework showing every decision point

### Visual Analysis (9 images from Yavapai image processing)
1. `1_original.jpg` - Original census image (5854x4505px)
2. `2_regions.jpg` - Region boundaries (header, top_transition, main_table, bottom, supplemental)
3. `3_top_transition_region.jpg` - Extracted top_transition region (5854x451px)
4. `4_thresholded.jpg` - Adaptive thresholding result (binary image)
5. `5_morphological_lines.jpg` - Horizontal line segments after morphological opening
6. `6_segments.jpg` - Individual segments (77 contours) with bounding boxes
7. `7_grouped_lines.jpg` - Segments grouped into 13 lines by Y-coordinate
8. `8_column_boundaries.jpg` - Column reference lines (line numbers, blank column)
9. `9_final_detection.jpg` - Final first boundary detection result

### Test Results
- `full-test-results.txt` - Summary of 179-image test (155 success, 24 failed)

## Critical Issues Identified

See `../row-detection-analysis-2025-10-18.md` for complete details:

**Issue A**: Main table region extends too far (into supplemental questions)
**Issue B**: Single-segment false positives (handwriting mistaken for table lines)
**Issue C**: Inaccurate column boundary detection (blank column not correctly identified)
**Issue D**: **NON-DETERMINISTIC BEHAVIOR** - Same image produces different results ⚠️ CRITICAL
**Issue E**: False success criteria - detecting 40 rows doesn't mean they're the correct 40 rows

## Recommended Action Plan

1. **IMMEDIATE**: Fix non-determinism (blocking all other work)
2. **HIGH**: Implement honest validation metrics
3. **HIGH**: Fix column boundary detection (primary criterion for first boundary)
4. **MEDIUM**: Filter single-segment false positives
5. **MEDIUM**: Adjust region boundaries

Expected outcome: Success rate will drop to ~70-75% (honest metrics) before fixes, then improve to 95%+ with all fixes applied.

## Using These Artifacts

**For reference**: These images document the current state of detection as of Oct 18, 2025
**For regression testing**: After fixes, re-run analysis on Yavapai image and compare
**For documentation**: Illustrate each processing step in papers/presentations
**For ML training**: Can be used as examples when creating ground truth datasets

## Related Documentation

- Main analysis: `../row-detection-analysis-2025-10-18.md`
- Implementation plan: `../implementation-plan.md`
- Schema design: `../sidecar-schema-diagram.md`

---

**Preservation Note**: All files in this directory should be kept in version control as historical reference and for regression testing after detector improvements.
