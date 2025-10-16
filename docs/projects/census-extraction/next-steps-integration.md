# Census Extraction: Next Steps - Integration & Testing

**Date:** 2025-10-15
**Status:** M0 Complete ✅, M1 Core Complete ✅, Catalog Working ✅
**Ready For:** Integration Testing & Pilot Run

---

## Session Accomplishments ✅

### Pre-1850 Census Discovery & Resolution
- **Problem:** Original catalog query missed all pre-1850 data (1790-1840)
- **Solution:** Enhanced 4-pathway query now finds all census years
- **Result:** 3,684 person-media links (vs 2,652 previously, +39%)
- **Coverage:** Complete 1790-1945 (all federal + state census)

### Database Population
- **Census sidecar database initialized** with PostgreSQL
- **1,334 census_page records** inserted
- **State census support added** (1855, 1865, 1875, 1885, 1895, 1925, 1945)
- **No census entries** yet - requires OCR pipeline

### Files Modified
1. **`rmagent/census/catalog.py`**
   - Enhanced `_get_census_events_with_media()` with 4-pathway query
   - Updated `_extract_census_year()` to prioritize MediaPath
   - Added state census year validation

2. **`rmagent/census/models/schema.py`**
   - Added `event_id`, `citation_id`, `census_format`, `implied`, `enumeration_date`
   - Updated indexes for new fields

3. **`scripts/test_census_catalog.py`**
   - Updated with 4-pathway query
   - Added linkage pathway and pre-1850 statistics

### Documentation Created
1. **`census-catalog-query-solution.md`** - Pre-1850 discovery documentation
2. **`session-2025-10-15-summary.md`** - Complete session summary (~1,000 lines)
3. **`next-steps-integration.md`** - This file

---

## Current System Status

### ✅ Working Components

**M0 Foundation:**
- PostgreSQL sidecar database with hybrid schema (columns + JSONB)
- Census year configurations (1850, 1900, 1940 implemented)
- Docker Compose setup for PostgreSQL
- GIN indexes for fast JSONB queries

**M1 Core:**
- Image preprocessing pipeline (deskew, denoise, CLAHE, binarization)
- Layout detection (OpenCV morphological operations)
- OCR engine (Tesseract with confidence scoring)
- Person matching (RapidFuzz - needs refactoring for PersonID-known workflow)
- Review UI (FastAPI + HTMX with keyboard shortcuts)

**Catalog:**
- 4-pathway query finds all census years (1790-1945)
- MediaPath year extraction (100% success rate)
- State census support (1855-1945 in 5-year intervals)
- 1,334 census_page records populated

**Dependencies:**
- ✅ PostgreSQL running and healthy
- ✅ Tesseract 5.5.1 installed
- ✅ psycopg2-binary installed
- ✅ All M1 dependencies installed (pillow, opencv-python, pytesseract, rapidfuzz, fastapi, uvicorn)

### ❌ Pending Components

**Integration:**
- Pipeline orchestrator (`rmagent/census/pipeline.py`) - not created yet
- CLI commands for processing (`process`, `process-batch`) - not implemented
- End-to-end testing - not done

**Census Year Configurations:**
- Pre-1850 configs (1790-1840) - not created yet
- State census configs (1855-1945) - not created yet
- Only 1850, 1900, 1940 configs exist

**Review UI:**
- Not tested with real census data
- May need adjustments

---

## Next Steps: Priority Order

### Priority 1: Integration Testing (HIGH) 🔴

**Goal:** Verify full pipeline works end-to-end on a single image

**Tasks:**
1. Create pipeline orchestrator (`rmagent/census/pipeline.py`)
   - Load image from census_page table
   - Preprocess image (deskew, denoise, enhance)
   - Detect layout (extract cell regions)
   - Extract OCR (with confidence and provenance)
   - Create household record
   - Create entry records for known PersonIDs
   - Insert to sidecar DB
   - Generate provenance records

2. Add CLI command `rmagent census process <page_id>`
   - Process single census page by page_id
   - Display results (households, entries, confidence scores)
   - Show errors and warnings

3. Test on single 1900 census page
   - Select page with good quality and known household
   - Run through full pipeline
   - Verify household and entry records created
   - Check OCR accuracy against known data
   - Review provenance tracking

**Time Estimate:** 4-6 hours

---

### Priority 2: Pilot Run (MEDIUM) 🟡

**Goal:** Process 10 diverse images and collect metrics

**Tasks:**
1. Select 10 test images:
   - 2× Pre-1850 (1790, 1820) - aggregate format
   - 2× 1850-1900 - early individual format
   - 3× 1900-1920 - peak quality
   - 2× 1930-1940 - modern format
   - 1× State census (1885 or 1925)

2. Document image characteristics:
   - Census year and format (aggregate vs individual)
   - Image quality (clear, faded, damaged)
   - Table structure (ruled, unruled, handwritten)
   - Number of expected persons

3. Run pilot:
   - Process all 10 images
   - Collect success/failure rates
   - Measure OCR accuracy on sample fields
   - Document failure modes

4. Analyze results:
   - OCR accuracy by field type (name, age, occupation)
   - Layout detection success rate
   - Person matching accuracy
   - Time per image

**Success Metrics:**
- [ ] Process 10 images without crashes
- [ ] OCR accuracy > 85% on printed text
- [ ] Layout detection identifies > 90% of cells
- [ ] Person matching verifies correct PersonID > 95%
- [ ] Provenance tracking captures all OCR metadata

**Time Estimate:** 6-8 hours

---

### Priority 3: Review UI Testing (MEDIUM) 🟡

**Goal:** Verify review UI works with real census data

**Tasks:**
1. Process 5-10 images to generate census entries
2. Launch review UI: `rmagent census review`
3. Test all features:
   - Entry navigation (keyboard shortcuts A/F/S/N)
   - Field editing
   - Approval/flagging/skipping
   - Statistics dashboard
   - HTMX dynamic updates

4. Document UX issues:
   - Missing features
   - UI bugs
   - Performance issues
   - Usability improvements

**Time Estimate:** 2-3 hours

---

### Priority 4: Person Matching Refactoring (LOW) 🟢

**Goal:** Simplify matching for PersonID-known workflow

**Current Implementation:**
- Fuzzy matching with RapidFuzz
- Age/birthplace scoring
- Designed for discovering unknown people

**New Understanding:**
- We KNOW PersonIDs beforehand from catalog query
- Goal: Verify OCR name matches expected PersonID's name
- Goal: Assign line numbers to household members
- Goal: Flag mismatches for human review

**Refactoring Tasks:**
1. Create `PersonVerifier` class (vs `PersonMatcher`)
   - `verify_person(person_id, ocr_name, expected_name)` → confidence score
   - `assign_line_numbers(household_persons, ocr_lines)` → person-line mapping
   - Flag low-confidence matches for review

2. Update pipeline to use verification instead of matching
3. Update review UI to show expected vs OCR name
4. Add unit tests for verification logic

**Time Estimate:** 3-4 hours

---

### Priority 5: Pre-1850 Census Configurations (LOW) 🟢

**Goal:** Add census year configs for 1790-1840

**Tasks:**
1. Research pre-1850 census formats:
   - 1790-1840: Aggregate/tally format
   - Different column structures per year
   - Free white males/females by age buckets
   - Enslaved persons counts
   - Other categories

2. Create `census_years.py` configs for each decade:
   - 1790, 1800, 1810, 1820, 1830, 1840
   - Define JSONB field names for tally buckets
   - Example: `free_white_males_under_10`, `free_white_females_16_to_25`

3. Document pre-1850 workflow:
   - OCR extracts tally counts (not names)
   - Genealogist creates `implied` entries linking PersonIDs to tallies
   - Review UI shows tally buckets vs individual records

**Time Estimate:** 2-3 hours

---

### Priority 6: Batch Processing Infrastructure (LOW) 🟢

**Goal:** Enable processing large batches of images

**Tasks:**
1. Add CLI command `rmagent census process-batch`
   - Options: `--census-year`, `--limit`, `--parallel`
   - Progress bar with rich/tqdm
   - Error recovery and resume capability

2. Implement parallel processing:
   - Process N images concurrently (default: 4)
   - Queue-based architecture
   - Graceful shutdown on errors

3. Add logging and reporting:
   - Per-image success/failure log
   - Summary statistics (total, success, failed, skipped)
   - Export to CSV/JSON

**Time Estimate:** 4-5 hours

---

## Known Issues & Blockers

### Issues ⚠️

1. **Pre-1850 OCR Not Implemented**
   - Current pipeline assumes individual records
   - No logic for extracting tally bucket counts
   - May require manual entry or different OCR approach

2. **Person Matching May Be Obsolete**
   - Designed for fuzzy matching unknown people
   - Now we KNOW PersonIDs beforehand
   - Should refactor to verification-focused approach

3. **No Unit Tests**
   - All M1 code untested
   - High risk of regressions
   - Should add tests before expanding features

4. **OpenCV Layout Detection Limitations**
   - Assumes ruled tables with visible lines
   - May fail on unruled schedules
   - Need pilot data to assess prevalence

5. **State Census Configurations Missing**
   - Only federal census configs exist (1850, 1900, 1940)
   - State census years (1855-1945) have no configs yet
   - May have different column structures

### Blockers 🔴

**None currently** - all dependencies installed and working

---

## Testing Checklist

### Integration Testing
- [ ] Create pipeline orchestrator
- [ ] Add `process` CLI command
- [ ] Test on single 1900 census page
- [ ] Verify household record created
- [ ] Verify entry records created with correct PersonIDs
- [ ] Check OCR confidence scores
- [ ] Verify provenance tracking
- [ ] Test error handling (missing file, bad image, OCR failure)

### Pilot Run (10 Images)
- [ ] Select 10 diverse test images
- [ ] Document image characteristics
- [ ] Process all 10 images
- [ ] Measure OCR accuracy on sample fields
- [ ] Calculate layout detection success rate
- [ ] Verify person matching accuracy
- [ ] Collect timing metrics
- [ ] Document failure modes
- [ ] Compare results against success metrics

### Review UI Testing
- [ ] Process 5-10 images to generate entries
- [ ] Launch review UI
- [ ] Test navigation (keyboard shortcuts)
- [ ] Test field editing
- [ ] Test approve/flag/skip actions
- [ ] Verify statistics dashboard
- [ ] Test HTMX updates (no page reload)
- [ ] Document UX issues

### Person Matching Refactoring
- [ ] Design verification API
- [ ] Implement `PersonVerifier` class
- [ ] Add line number assignment logic
- [ ] Update pipeline to use verification
- [ ] Update review UI for expected vs OCR display
- [ ] Add unit tests
- [ ] Document verification algorithm

### Pre-1850 Configuration
- [ ] Research 1790 census format
- [ ] Research 1800 census format
- [ ] Research 1810 census format
- [ ] Research 1820 census format
- [ ] Research 1830 census format
- [ ] Research 1840 census format
- [ ] Create configs for all 6 decades
- [ ] Document pre-1850 workflow
- [ ] Add examples to docs

---

## Recommendations

### Start With (Next Session)

**1. Pipeline Orchestrator (4-6 hours)**
- Create `rmagent/census/pipeline.py`
- Implement end-to-end workflow
- Add basic error handling
- Test on single 1900 image

**2. CLI Integration (2-3 hours)**
- Add `process` command
- Add `process-batch` command stub (parallel processing later)
- Test with `rmagent census process 1` (page_id=1)

**3. Pilot Run (6-8 hours)**
- Select 10 diverse images
- Run pilot
- Collect metrics
- Document results

**Total Time Estimate:** 12-17 hours (1.5-2 days of focused work)

### Defer Until M2

**1. Advanced Features:**
- AI-assisted validation (LLM for difficult handwriting)
- Vision LLM for cell extraction verification
- Bulk operations in review UI
- Export to CSV/Excel

**2. Performance Optimization:**
- Caching preprocessed images
- Batch inserts for provenance
- Database query optimization

**3. Pre-1850 Full Support:**
- Tally extraction OCR
- Implied entry workflow
- Pre-1850 review UI

**4. Production Polish:**
- Comprehensive unit tests
- Type safety (mypy validation)
- User documentation
- Troubleshooting guide

---

## Success Criteria for M1

- [ ] Successfully process 10 diverse images end-to-end
- [ ] OCR accuracy > 85% on printed text
- [ ] Layout detection identifies > 90% of cells correctly
- [ ] Person matching verifies correct PersonID > 95% of time
- [ ] Review UI functional for approving/flagging entries
- [ ] Documentation sufficient for running pilot

**Status:** Ready to begin integration testing! All foundation work complete.

---

## File References

**Documentation:**
- Session summary: `docs/projects/census-extraction/session-2025-10-15-summary.md`
- Catalog solution: `docs/projects/census-extraction/census-catalog-query-solution.md`
- M1 summary: `docs/projects/census-extraction/M1-implementation-summary.md`
- Architecture: `docs/projects/census-extraction/census-architecture-v2.md`

**Code:**
- Catalog: `rmagent/census/catalog.py`
- Schema: `rmagent/census/models/schema.py`
- Sidecar: `rmagent/census/sidecar.py`
- CLI: `rmagent/cli/census.py`
- Test script: `scripts/test_census_catalog.py`

**M1 Components:**
- Preprocessing: `rmagent/census/pipelines/preprocessing/`
- Layout detection: `rmagent/census/pipelines/preprocessing/layout_detector.py`
- OCR: `rmagent/census/pipelines/ocr/tesseract_engine.py`
- Matching: `rmagent/census/pipelines/matching/person_matcher.py`
- Review UI: `rmagent/census/review/app.py`

---

**End of Integration Roadmap**
