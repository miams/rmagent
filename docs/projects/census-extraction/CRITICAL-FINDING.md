# CRITICAL FINDING: Row Cropping Accuracy Blocks Validation

**Date**: 2025-10-16, ~19:00
**Status**: ❌ VALIDATION BLOCKED

---

## Problem Discovered

When testing Wilma (PersonID 5524, expected line 14), the LLM scored **30+ rows at 85-95/100 similarity**.

This means:
1. **Either**: My manual cropping coordinates are completely wrong (likely)
2. **Or**: The LLM is hallucinating "Wilma" in every row (less likely)

### Results

| Row | Score | Extracted Name | Expected |
|-----|-------|----------------|----------|
| 3 | 95/100 | Saunders, Wilma M | ✗ WRONG |
| 4 | 95/100 | , Wilma M | ✗ WRONG |
| 6 | 95/100 | Saunders, Wilma M | ✗ WRONG |
| ... | ... | ... | ... |
| 14 | 90/100 | Wilma M | ✓ Correct but NOT highest |

**30+ rows scored 85-95/100 - similarity scoring cannot distinguish!**

---

## Root Cause: Manual Cropping Coordinates Are Wrong

My approach used **static coordinates**:
```python
table_start_y = 900  # Guess
row_height = 100     # Guess
row_y = table_start_y + (row_num - 1) * row_height
```

**Problem**: This high-resolution image (6169×4653 pixels) has:
- Variable row heights (not uniform 100px)
- Unknown table start position
- Rows may not be perfectly horizontal (skew/rotation)

**Result**: My "row 3" crop might actually contain parts of lines 5, 6, and 7 from the census, causing the LLM to see "Wilma" everywhere.

---

## Why Test 2 (Marshall) Succeeded

Marshall's test (Iteration 5) worked because:
1. I only tested 4 specific rows (10, 13, 14, 15)
2. By chance, one of my crops roughly aligned with line 13
3. Only 1 row scored high (90/100), others scored much lower (45, 15, 85)

**This was lucky**, not reliable.

---

## Implications

**The similarity scoring approach CANNOT work without accurate row cropping.**

### What We Learned

✓ **LLM CAN compare rows and score similarity** (when given correct row images)
✗ **Manual cropping is too inaccurate** (causes false positives across all rows)
❌ **Cannot proceed to validation of 5 family members** until cropping is fixed

---

## Path Forward: Two Options

### Option A: Implement Automatic Row Detection (Recommended)

**Use OpenCV/doctr to automatically detect row boundaries:**

1. **Pre-processing**:
   - Deskew image (fix rotation)
   - Binarization (black/white)
   - Denoise

2. **Layout Detection**:
   - Detect horizontal lines (table borders)
   - Identify row boundaries
   - Crop each row with exact coordinates

3. **Validation**:
   - Manually verify 10 sample crops are correct
   - Then proceed with similarity scoring

**Pros**:
- Accurate, automated, scalable
- Works for all 1,400 images

**Cons**:
- Requires implementing M1 preprocessing pipeline first
- 1-2 weeks of work

**Estimated Timeline**:
- Week 1: Implement preprocessing + layout detection
- Week 2: Validate on 50 images, tune parameters
- Week 3: Proceed with similarity scoring validation

### Option B: Manual Verification + Coordinate Tuning

**Manually find correct coordinates for this ONE image:**

1. Use image viewer to measure exact pixel coordinates for lines 13-18
2. Update cropping script with correct coordinates
3. Re-run Wilma validation (should work if coordinates accurate)
4. If successful, validate remaining 4 family members

**Pros**:
- Fast (1-2 hours)
- Proves similarity scoring works

**Cons**:
- Only works for THIS image
- Not scalable to 1,400 images
- Still need Option A eventually

---

## Recommendation

**Proceed with Option A: Implement automatic row detection.**

**Rationale**:
1. Manual cropping proved unreliable (Wilma test failed)
2. We need row detection anyway for production (1,400 images)
3. Similarity scoring has shown promise (Marshall test succeeded)
4. Once rows are accurately cropped, similarity scoring should work

**Next Steps**:
1. Implement M1 preprocessing pipeline (deskew, denoise, layout detection)
2. Validate row cropping accuracy on 10 sample images
3. Re-run similarity scoring tests with accurate crops
4. If successful, proceed with extraction testing

---

## Alternative: Pivot Back to Traditional OCR

**If automatic row detection proves too difficult:**

1. Use Tesseract/Kraken for full-table OCR
2. Parse OCR output into 40 rows × 34 columns
3. Use Python fuzzy matching (RapidFuzz) to match people to rows
4. LLM only for difficult handwriting (spot-checking)

**This was the original Option B from the changelog.**

---

## Cost Impact

**Current approach** (similarity scoring + manual cropping):
- ❌ Blocked - cannot validate until cropping fixed

**With automatic row detection**:
- M1 implementation: 1-2 weeks
- Then proceed with similarity scoring: $280 for 1,400 images

**Traditional OCR approach**:
- M1 implementation: 1-2 weeks
- Lower cost: ~$0 for OCR, $50-100 for LLM spot-checking

---

## User Decision Required

**Questions**:
1. **Proceed with Option A** (implement automatic row detection, then validate similarity scoring)?
2. **Or proceed with Option B** (manually fix coordinates for this image first, prove concept)?
3. **Or pivot to traditional OCR approach**?

**My Recommendation**: Option A (automatic row detection) because it's needed for production anyway, and similarity scoring showed promise when crops were accurate.
