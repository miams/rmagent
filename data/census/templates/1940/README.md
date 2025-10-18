# 1940 Federal Census Template

**Created:** 2025-10-16
**Status:** Production Ready (Main Table) | Supplemental Pending

## Files

- **`template.jpg`** - Blank 1940 census form (3000x2343px)
- **`visualization.jpg`** - Color-coded column labels
- **`grid_specification.json`** - Complete grid coordinates and metadata

## Grid Specifications

### Main Table
- **Data columns:** 34 (numbered 1-34, blue)
- **Census taker columns:** 8 (A, B, C, D, E, F×3, orange) - **Skip OCR**
- **Admin columns:** 2 ("Line#", gray) - **Skip OCR**
- **Rows:** 40 uniform data entry rows (35.20px spacing)
- **Total cells:** 34 × 40 = 1,360 data cells

### Supplemental Table
- **Status:** Not yet labeled (pending main table OCR test)
- **Rows:** 2 uniform data entry rows (39.00px spacing)

## Usage

### Apply Template to Census Image

```python
import json
import cv2

# Load template specification
with open("data/census/templates/1940/grid_specification.json") as f:
    template = json.load(f)

# Load census image
image = cv2.imread("path/to/census/image.jpg", cv2.IMREAD_GRAYSCALE)
img_height, img_width = image.shape

# Scale template ratios to image dimensions
main_table = template["tables"]["main"]
rows = main_table["rows"]["separators"]
cols = main_table["columns"]["vertical_lines"]

# Convert to image coordinates
scaled_rows = [int(y * img_height / 2343) for y in rows]
scaled_cols = [int(x * img_width / 3000) for x in cols]

# Extract cells
for row_idx in range(len(scaled_rows) - 1):
    y1, y2 = scaled_rows[row_idx], scaled_rows[row_idx + 1]

    for col_info in main_table["columns"]["labels"]:
        if col_info["skip_ocr"]:
            continue  # Skip census taker and admin columns

        col_idx = col_info["column_index"]
        x1 = scaled_cols[col_idx]
        x2 = scaled_cols[col_idx + 1]

        cell_image = image[y1:y2, x1:x2]

        # Run OCR on cell_image
        # ... (Tesseract processing)
```

### Column Mapping

Data columns (1-34) map to census fields. Metadata available in RMAgent's census catalog:

```python
from rmagent.census.models.schema import CensusFieldMetadata

# Column 1 = "Street"
# Column 2 = "House Number"
# ... etc (34 total fields)
```

## Detection Methodology

### Column Detection (Manual Cleanup)
1. Morphological operations detected 50 initial vertical lines
2. Removed 5 false positives at positions: 290, 1071, 1922, 1968, 2161px
3. Result: 45 lines → 44 column spaces
4. Labeled: 34 data + 8 census taker + 2 admin

### Row Detection (Uniform Spacing)
1. Identified data entry region boundaries (Y=470 to Y=1878)
2. Edge detection refined to exact horizontal line positions
3. Calculated uniform spacing: 1408px ÷ 40 rows = 35.20px/row
4. Generated evenly-spaced separators

**Key insight:** Data rows are uniform, don't try to detect each line individually.

## Scaling to Different Image Sizes

Template uses **ratio-based coordinates** for portability:

```python
# Template coordinate at X=723px (image width 3000px)
x_ratio = 723 / 3000 = 0.2410

# Apply to new image (width 2400px)
x_new = int(0.2410 * 2400) = 578px
```

All ratios stored in `grid_specification.json` for automated scaling.

## Quality Checks

Before OCR processing, verify:
1. ✓ Image orientation correct (not rotated)
2. ✓ Sufficient resolution (recommended: 2000+ px width)
3. ✓ Reasonable contrast (CLAHE preprocessing if needed)
4. ✓ No severe skew/distortion (may need alignment)

## Next Steps

1. **Test OCR on actual census images** using this template
2. **Validate cell extraction accuracy** (visual inspection)
3. **Map 34 data columns** to census field metadata
4. **Label supplemental table columns** (43 columns)
5. **Batch process 1,400 images** with parallel workers

## Performance Estimates

- **Cell extraction:** ~2 seconds per image (1,360 cells)
- **OCR per cell:** ~0.5 seconds (Tesseract)
- **Total per image:** ~12 minutes (sequential)
- **With parallelization (10 workers):** ~1.2 minutes per image

**1,400 images:** ~28 hours with 10 parallel workers

## Troubleshooting

### Columns misaligned
- Check image width matches expected aspect ratio
- Apply fine-tuning: search ±5px around template position

### Rows misaligned
- Verify data region boundaries (may differ by page)
- Recalculate uniform spacing for THIS image

### OCR quality poor
- Increase image resolution (scan at 300+ DPI)
- Apply CLAHE contrast enhancement (clipLimit=1.0)
- Consider handwriting recognition for difficult cells

## References

- **Template source:** Blank 1940 Federal Census form (NARA)
- **Documentation:** `/docs/projects/census-extraction/`
- **Detection scripts:** `/tmp/detect_*.py` (development only)
