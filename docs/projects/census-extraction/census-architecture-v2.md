# Census Extraction Architecture v2.0

**Date:** 2025-10-15
**Status:** Architecture Finalized - Ready for Implementation
**Scope:** All U.S. Federal Census 1790-1950

---

## Executive Summary

**Goal:** Extract census data from images and populate sidecar database with information not currently recorded in RootsMagic, linking via PersonID.

**Key Principle:** RootsMagic database is **READ ONLY**. All extracted data goes to PostgreSQL sidecar.

**Coverage:** All U.S. Federal Census years 1790-1950 (later: state census, special schedules)

---

## Core Architecture Decisions

### 1. Database Design

**Primary Table:** `census_entry` - One record per person (or per head of household for pre-1850)

**Supporting Tables:**
- `census_page` - Processing bookkeeping (optional reference)
- `census_field_provenance` - OCR metadata per field
- `census_review_log` - Audit trail

**Removed:** `census_household` table (not needed - dwelling/family numbers in census_entry)

### 2. Unified Schema (1790-1950)

**Two Census Formats:**

**Pre-1850 (1790-1840): Aggregate/Tally Format**
- One `census_entry` per head of household
- Tallies stored in JSONB fields
- Example: `"free_white_males_5_10": 2`

**Post-1850 (1850-1950): Individual Format**
- One `census_entry` per person
- Person attributes in columns + JSONB
- Example: name="John Smith", age=42

**Unified via:**
- Nullable columns (age, sex, race, birthplace, occupation)
- JSONB flexibility for year-specific fields
- `census_format` discriminator column

### 3. Implied Entries (Pre-1850 Innovation)

**Problem:** Pre-1850 census only names head of household. Known family members are in tallies.

**Solution:** `implied` flag

**Example:**
```
Head (from OCR):
  person_id: 123, name: "John Smith", implied: false
  fields: {"free_white_males_5_10": 2}

Family (genealogist assessment):
  person_id: 456, name: "William Smith", implied: true, age: 7
  fields: {"source_tally": "free_white_males_5_10"}

  person_id: 457, name: "Thomas Smith", implied: true, age: 9
  fields: {"source_tally": "free_white_males_5_10"}
```

**Use Case:** Allows linking known family members to aggregate census data, enables tally reconciliation.

---

## Schema Design

### census_entry (Primary Table)

```sql
CREATE TABLE census_entry (
    entry_id SERIAL PRIMARY KEY,

    -- Links to RootsMagic (core requirement)
    person_id INTEGER NOT NULL,    -- RootsMagic PersonID
    citation_id INTEGER,            -- RootsMagic CitationID
    event_id INTEGER,               -- RootsMagic EventID

    -- Census format handling
    census_format TEXT NOT NULL CHECK (census_format IN ('aggregate', 'individual')),
    implied BOOLEAN DEFAULT false,  -- True for pre-1850 inferred entries

    -- Sheet/Page Metadata (redundant per person - ACCEPTABLE)
    census_year INTEGER NOT NULL CHECK (census_year BETWEEN 1790 AND 1950),
    image_path TEXT,                -- Link to original image
    sheet_number TEXT,              -- Census sheet/page number
    enumeration_district TEXT,      -- ED number
    enumeration_date DATE,          -- When census was taken
    dwelling_number TEXT,
    family_number TEXT,
    line_number INTEGER,            -- Line number on census sheet

    -- Person Data (nullable for pre-1850)
    name TEXT,
    age INTEGER CHECK (age >= 0 AND age <= 150 OR age IS NULL),
    sex TEXT CHECK (sex IN ('M', 'F', 'Male', 'Female') OR sex IS NULL),
    race TEXT,
    birthplace TEXT,
    occupation TEXT,

    -- Year-specific fields (JSONB for flexibility)
    fields JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Review tracking
    review_status TEXT DEFAULT 'pending'
        CHECK (review_status IN ('pending', 'approved', 'corrected', 'flagged', 'skipped')),
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,

    -- Provenance
    match_confidence REAL CHECK (match_confidence >= 0 AND match_confidence <= 1),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_entry_person ON census_entry(person_id);
CREATE INDEX idx_entry_citation ON census_entry(citation_id);
CREATE INDEX idx_entry_event ON census_entry(event_id);
CREATE INDEX idx_entry_year ON census_entry(census_year);
CREATE INDEX idx_entry_format ON census_entry(census_format);
CREATE INDEX idx_entry_implied ON census_entry(implied);
CREATE INDEX idx_entry_status ON census_entry(review_status);
CREATE INDEX idx_entry_name ON census_entry(name);
CREATE INDEX idx_entry_fields_gin ON census_entry USING GIN (fields);
```

### census_page (Processing Bookkeeping)

```sql
CREATE TABLE census_page (
    page_id SERIAL PRIMARY KEY,
    media_id INTEGER NOT NULL UNIQUE,  -- RootsMagic MediaID
    census_year INTEGER NOT NULL,
    image_path TEXT NOT NULL,
    processed_path TEXT,               -- Preprocessed image location
    layout_metadata JSONB,             -- Cell coordinates for review UI
    processing_status TEXT DEFAULT 'pending'
        CHECK (processing_status IN ('pending', 'processing', 'complete', 'failed')),
    ocr_completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_page_media ON census_page(media_id);
CREATE INDEX idx_page_year ON census_page(census_year);
CREATE INDEX idx_page_status ON census_page(processing_status);
```

### census_field_provenance (OCR Metadata)

```sql
CREATE TABLE census_field_provenance (
    provenance_id SERIAL PRIMARY KEY,
    entry_id INTEGER NOT NULL REFERENCES census_entry(entry_id),
    field_path TEXT NOT NULL,  -- e.g., "name", "age", "fields.income_wages"

    -- OCR metadata
    ocr_model TEXT NOT NULL CHECK (ocr_model IN ('tesseract', 'kraken', 'calamari', 'vision_llm')),
    ocr_confidence REAL CHECK (ocr_confidence >= 0 AND ocr_confidence <= 1),
    raw_ocr_text TEXT,  -- Before normalization

    -- Image region
    cell_coordinates JSONB,  -- {x, y, width, height}
    cell_image_path TEXT,    -- Path to cropped cell snippet

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_provenance_entry ON census_field_provenance(entry_id);
CREATE INDEX idx_provenance_field_path ON census_field_provenance(field_path);
```

### census_review_log (Audit Trail)

```sql
CREATE TABLE census_review_log (
    log_id SERIAL PRIMARY KEY,
    entry_id INTEGER NOT NULL REFERENCES census_entry(entry_id),
    reviewer_id TEXT NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('approve', 'correct', 'flag', 'skip', 'create_implied')),
    field_path TEXT,  -- e.g., "name", "fields.income_wages"
    old_value TEXT,
    new_value TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_review_entry ON census_review_log(entry_id);
CREATE INDEX idx_review_reviewer ON census_review_log(reviewer_id);
CREATE INDEX idx_review_created ON census_review_log(created_at);
```

---

## NULL vs Sentinel Values

**Question:** Use NULL or sentinel values (e.g., age=-1) for missing data?

**Decision: Use NULL**

**Rationale:**
- ✅ Semantically correct (NULL = unknown/not applicable)
- ✅ SQL standard, clear intent
- ✅ Easier queries: `WHERE age IS NULL` vs `WHERE age = -1`
- ✅ No confusion with real data (age=-1 is nonsensical)
- ❌ Sentinel values (like -1) require documentation and can be confused with data errors

**Sentinel values only beneficial when:**
- Programming language doesn't support NULL well
- Need default sort order (NULL sorts first/last unpredictably)

**For PostgreSQL:** NULL is the right choice. Indexes handle NULL efficiently.

---

## Column vs JSONB Decision Rules

### Columns (Traditional Fields)

**Use column when:**
- Present in 6+ census years (1850-1950)
- Frequently queried for filtering/joining
- Simple atomic type (text, integer, date)
- Used for matching/validation

**Current columns (justified):**
- `name` - All years, matching key
- `age` - 1850+, matching key, frequently queried
- `sex` - 1850+, matching support
- `race` - 1850+, research queries
- `birthplace` - 1850+, frequently queried
- `occupation` - 1850+, frequently queried

**Should add as columns:**
- `relationship_to_head` - 1880+, frequently queried, important for household structure
- Consider: Keep in JSONB for now, promote to column if queries become slow

### JSONB (Year-Specific Fields)

**Use JSONB when:**
- Year-specific (1940 income, 1900 immigration_year)
- Infrequently queried
- Complex/nested structure
- Varies by census format

**Examples:**
- `marital_status` - 1880+, varies by year (S/M/W/D vs codes)
- `immigration_year` - 1900-1930 only
- `income_wages` - 1940 only
- `education_level` - 1940 only
- Pre-1850 tallies - All year-specific buckets

---

## Processing Workflow

### Phase 1: Catalog (Identify What to Process)

**Input:** RootsMagic database (READ ONLY)

**Query:** Find all MediaIDs with census events and their linked persons

```sql
-- Get all census images with linked persons
SELECT
    m.MediaID,
    m.MediaPath,
    m.MediaFile,
    e.EventID,
    e.OwnerID as PersonID,
    c.CitationID,
    cp.census_year
FROM MultimediaTable m
JOIN MediaLinkTable ml ON ml.MediaID = m.MediaID AND ml.OwnerType = 2
JOIN EventTable e ON e.EventID = ml.OwnerID
JOIN FactTypeTable ft ON ft.FactTypeID = e.EventType AND ft.GedcomTag = 'CENS'
JOIN CitationLinkTable cl ON cl.OwnerID = e.EventID AND cl.OwnerType = 2
JOIN CitationTable c ON c.CitationID = cl.CitationID
-- Extract year from event date or other source
-- TODO: How to reliably get census_year? From event date? From media path?
WHERE m.MediaType = 1  -- Images only
ORDER BY census_year DESC, m.MediaPath  -- Process 1950s first, then 1940s, etc.
```

**Output:** List of MediaIDs grouped by decade, with all PersonIDs per image

**Priority:** Process 1950s first (same format, easier for Tesseract)

### Phase 2: Preprocess Image

**Input:** Image file from MediaPath

**Steps:**
1. Deskew (rotation correction)
2. Denoise (Gaussian blur)
3. Contrast enhancement (CLAHE)
4. Binarization (adaptive threshold)

**Output:** Preprocessed image saved to `data/census/images/processed/`

**Record:** Update `census_page.processed_path` and `processing_status='processing'`

### Phase 3: Layout Detection

**Input:** Preprocessed image

**Steps:**
1. Morphological operations (detect horizontal/vertical lines)
2. Contour extraction (find cells)
3. Grid organization (assign row/col indices)

**Output:** `TableLayout` object with cell coordinates

**Record:** Store layout in `census_page.layout_metadata` (JSONB)

### Phase 4: OCR Extraction

**Input:** Preprocessed image + TableLayout

**For each cell:**
1. Crop cell region
2. Run Tesseract OCR
3. Get text + confidence score

**Output:** List of `CellOCRResult` (cell → text + confidence)

### Phase 5: Person Matching (PersonID-Known)

**Key Insight:** We **know** which PersonIDs should be on this page (from catalog).

**For each PersonID from catalog:**

1. **Query RM for matching data:**
   ```sql
   -- Get person's names (primary + married + alt)
   SELECT Given, Surname, IsPrimary
   FROM NameTable
   WHERE OwnerID = :PersonID AND OwnerType = 0

   -- Get spouses (for married names)
   SELECT FatherID, MotherID
   FROM FamilyTable
   WHERE FatherID = :PersonID OR MotherID = :PersonID

   -- Get birth year
   SELECT BirthYear FROM PersonTable WHERE PersonID = :PersonID

   -- Get sex
   SELECT Sex FROM PersonTable WHERE PersonID = :PersonID

   -- Get Alt Name events
   SELECT Details FROM EventTable
   WHERE OwnerID = :PersonID AND EventType = [AltNameFactTypeID]
   ```

2. **Build candidate names:**
   - Given name (required)
   - All surname variants (primary + married + alt)
   - Birth year → expected age in census_year
   - Sex

3. **Fuzzy match against OCR lines:**
   - **Priority:** Given name match (strongest signal)
   - **Support:** Age within ±2 years
   - **Support:** Sex matches
   - **Hard:** Surname (use all variants)

4. **Select best match:**
   - Highest fuzzy score
   - Confidence adjustment based on uniqueness

**Output:** PersonID → OCR line mapping with confidence score

### Phase 6: Store to Sidecar

**For each matched PersonID:**

1. **Create census_entry:**
   ```sql
   INSERT INTO census_entry (
       person_id, citation_id, event_id,
       census_format, implied,
       census_year, image_path, sheet_number, line_number, enumeration_date,
       name, age, sex, race, birthplace, occupation,
       fields,
       match_confidence
   ) VALUES (...)
   ```

2. **Store field provenance:**
   ```sql
   INSERT INTO census_field_provenance (
       entry_id, field_path,
       ocr_model, ocr_confidence, raw_ocr_text,
       cell_coordinates
   ) VALUES (...)
   ```

3. **Update processing status:**
   ```sql
   UPDATE census_page
   SET processing_status = 'complete',
       ocr_completed_at = CURRENT_TIMESTAMP
   WHERE page_id = :page_id
   ```

### Phase 7: Human Review

**Review UI workflow:**
1. Load next pending entry
2. Display OCR data + matched person info
3. Show original image with highlighted cell
4. Genealogist actions:
   - Approve (confirm correct)
   - Correct (edit field values)
   - Flag (needs further research)
   - Skip (defer decision)
   - Create implied entry (pre-1850 only)

**Output:** Updated review_status, logged in census_review_log

---

## Pre-1850 Specific Workflow

### Differences from Post-1850:

**1. OCR Extraction:**
- Focus on head name (first column)
- Extract tally numbers (remaining columns)
- Simpler layout, always integers

**2. Matching:**
- Only match head of household name
- No age/sex matching (not recorded)
- Result: One census_entry per head

**3. Implied Entry Creation (Manual):**

**Review UI shows:**
- Head's entry with tallies
- List of known family members alive in census_year (from RM)
- Side-by-side: family members sorted by age vs tally buckets

**Genealogist creates implied entry:**
1. Select PersonID from family list
2. System pre-fills:
   - name (from RM)
   - age (calculated from birth year)
   - sex (from RM)
   - person_id, citation_id, event_id (from RM event)
3. Genealogist selects source_tally bucket
4. Genealogist adds notes (deductive reasoning)
5. System sets implied=true

**Result:** census_entry with implied=true

### Tally Reconciliation:

**Query to check completeness:**
```sql
-- Compare tally counts to implied entries
SELECT
    head.entry_id,
    head.name,
    head.fields->>'free_white_males_5_10' as tally_count,
    COUNT(implied.entry_id) as implied_count
FROM census_entry head
LEFT JOIN census_entry implied ON
    implied.census_year = head.census_year AND
    implied.sheet_number = head.sheet_number AND
    implied.dwelling_number = head.dwelling_number AND
    implied.fields->>'source_tally' = 'free_white_males_5_10' AND
    implied.implied = true
WHERE head.census_year = 1840 AND head.implied = false
GROUP BY head.entry_id, head.name, tally_count
HAVING (head.fields->>'free_white_males_5_10')::int != COUNT(implied.entry_id)
```

**Identifies:**
- Extra people (implied > tally): Possible error or duplicate
- Missing people (implied < tally): Known family members not linked yet

---

## Year-Specific Field Configurations

### Structure:

File: `rmagent/census/config/census_years.py`

**Each year has:**
- List of expected columns/fields
- Data types
- Display names
- OCR hints

### Coverage Needed:

**Pre-1850 (Aggregate):**
- 1790, 1800, 1810, 1820, 1830, 1840
- Tally bucket definitions per year

**Post-1850 (Individual):**
- Already have: 1850, 1900, 1940
- Need: 1860, 1870, 1880, 1890*, 1910, 1920, 1930

*1890 mostly destroyed by fire, minimal coverage

---

## Data Flow Summary

```
RootsMagic (READ ONLY)
    ↓
Catalog: MediaID → [PersonIDs]
    ↓
For each image (prioritize 1950s):
    ↓
Preprocess → Layout Detection → OCR
    ↓
Fuzzy Match: PersonID → OCR Line
    ↓
Sidecar DB: census_entry + provenance
    ↓
Review UI: Approve/Correct/Flag
    ↓
(Pre-1850 only) Create Implied Entries
    ↓
Tally Reconciliation Reports
```

---

## Open Questions & Future Work

### Immediate (Before M1 Pilot):

1. **Census year extraction:** How to reliably get census_year from RootsMagic?
   - Event.Date field? (24-char encoded)
   - Media path parsing? (e.g., "1950/..." → 1950)
   - Citation text parsing?

2. **Catalog query refinement:** Test query on actual database, verify PersonID retrieval works for entire households

3. **Married name logic:** Confirm FamilyTable query correctly identifies all spouse surnames

4. **Alt Name events:** Verify FactTypeID for Alt Name fact type

### Future (M2+):

5. **State census:** Different years, different formats (1855 NY, 1865 NY, etc.)

6. **Special schedules:**
   - Agricultural schedules (farm production)
   - Mortality schedules (deaths in year)
   - Manufacturing schedules

7. **Citation enhancement:** Generate reports for updating RM citations with line numbers (manual process)

8. **Unmatched OCR lines:** What to do with boarders/servants not in RM database?
   - Store with person_id=NULL?
   - Link to RM "relationships without PersonID" feature?

9. **Ditto marks:** OCR logic to handle vertical ditto marks (same as above)

10. **Multi-page households:** Handle families split across consecutive sheets

---

## Success Metrics

### M1 (Working Prototype):

- [ ] Successfully catalog 100+ 1950 census images from RM database
- [ ] Process 10 pilot images end-to-end
- [ ] OCR accuracy > 85% on printed text (1950s)
- [ ] Person matching finds correct line > 90% (known PersonIDs)
- [ ] Review UI functional for approve/flag/correct
- [ ] Store complete census_entry records with provenance

### M2 (MVP Release):

- [ ] Process all 1950 census images (~500?)
- [ ] Extend to 1940, 1930 census images
- [ ] Pre-1850 pilot: 10 images with implied entry creation
- [ ] Tally reconciliation reports working
- [ ] Export/reporting tools functional

---

## Next Steps

1. **Update schema:** Add census_format, implied, citation_id, event_id, enumeration_date columns
2. **Revise catalog.py:** Query for all household PersonIDs per MediaID
3. **Update matching logic:** PersonID-known workflow instead of fuzzy-first
4. **Add year configs:** Create 1790-1840 tally definitions
5. **Enhance review UI:** Add implied entry creation interface
6. **Test on real data:** Run catalog query on actual RM database, verify results

---

**Document Version:** 2.0
**Last Updated:** 2025-10-15
**Status:** Architecture Finalized - Ready for Implementation
