# Row Detection Strategy: Scalable Approach

**Date:** 2025-10-16
**Context:** After manual column detection proved laborious and unscalable

## The Problem

Manual column detection required:
- 3 rounds of false positive removal (20 + 9 + 4 = 33 removals)
- Numbered visualizations and manual inspection for each round
- Not scalable to 1,400+ census images

**User's question:** "Do we use same approach for rows, or is there a better way?"

## Why Rows Are Different (and Easier)

### Column Detection Challenges:
- Highly variable column widths (from 36px to 298px)
- Many false positives (text edges, artifacts, noise)
- Two completely different table structures (main vs supplemental)
- Irregular spacing

### Row Detection Advantages:
- **Uniform row height:** ~42px for main table, ~36px for supplemental
- **Consistent spacing:** Rows are evenly distributed
- **Strong horizontal lines:** Printed lines separate each row
- **Predictable count:** ~40 rows in main table, ~13 in supplemental

## Proposed Approach: Horizontal Projection Profile

**Method:** Sum pixel intensities horizontally across each Y-coordinate to find gaps between rows.

### Algorithm:
```python
def detect_rows_by_projection(image_region, expected_row_height=42):
    """
    Detect rows using horizontal projection profile.

    1. Sum pixel intensities for each horizontal line (Y-axis)
    2. Find valleys (low pixel sums = gaps between rows)
    3. Cluster valleys that are ~expected_row_height apart
    4. Return Y-coordinates of row separators
    """

    # Invert image so lines are white on black
    inverted = cv2.bitwise_not(image_region)

    # Sum intensities horizontally (axis=1)
    projection = np.sum(inverted, axis=1)

    # Smooth with moving average to reduce noise
    smoothed = np.convolve(projection, np.ones(5)/5, mode='same')

    # Find local minima (valleys = row separators)
    valleys = find_local_minima(smoothed, min_distance=expected_row_height)

    return valleys
```

### Why This Works:
- **No manual intervention required**
- **Scales to all images** (same algorithm, different images)
- **Robust to noise** (averaging reduces false positives)
- **Self-adjusting** (adapts to actual row spacing in each image)

## Alternative Approaches Considered

### 1. Hough Line Transform (Used for columns)
**Pros:** Detects printed lines directly
**Cons:**
- Misses faint or broken lines
- Generates many false positives for horizontal lines (every text baseline detected)
- Requires extensive parameter tuning per image

### 2. Morphological Operations (Used for columns)
**Pros:** Good at detecting continuous vertical structures
**Cons:**
- Horizontal lines are often broken or faint
- Text creates many horizontal artifacts
- Would require same manual cleanup as columns

### 3. **Projection Profile (RECOMMENDED)**
**Pros:**
- Uses overall pixel density, not individual line detection
- Naturally filters out text (text rows have MORE pixels, we want FEWER)
- Works even with faint or broken lines
- No parameter tuning needed
- **Scales automatically**

**Cons:** None significant for this use case

## Template-Based Workflow

Once we have clean row/column detection from the template:

### For Template (1940_census_form_large.jpg):
1. ✅ Detect columns (DONE: 50 main, 43 supplemental)
2. Detect rows via projection profile
3. Save template grid to file

### For New Census Images:
1. **No detection needed!** Just use template grid
2. Apply template column ratios to new image width
3. Apply template row ratios to each table section
4. Fine-tune with small adjustments if needed (±5px)

### Validation:
- For each cell, check if it contains expected content (text, numbers, checkboxes)
- If validation fails, fall back to projection profile for that specific image

## Next Steps

1. Implement `detect_rows_by_projection()` function
2. Test on template to get clean row positions
3. Visualize results (horizontal lines in GREEN)
4. Save complete grid (rows + columns) to template data
5. Test applying template grid to actual census images

## Expected Outcome

Instead of manual iteration:
- **Template processing:** 5 minutes to get clean grid once
- **Each new image:** < 1 second to apply template grid
- **Total time for 1,400 images:** ~30 minutes (vs. weeks of manual work)

**Scalability achieved!**
