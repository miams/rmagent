# Census Sidecar Database Schema

## Entity-Relationship Diagram

```mermaid
erDiagram
    census_page ||--o{ census_household : contains
    census_household ||--o{ census_entry : contains
    census_entry ||--o{ census_field_value : "has fields"
    census_field_value }o--|| census_field_provenance : "links to"
    census_entry ||--o{ census_review_log : "has review log"
    census_field_value ||--o{ census_review_log : "has review log"

    census_page {
        int page_id PK
        int media_id UK "RootsMagic MediaID"
        int person_id FK "Primary person link"
        int census_year "1790-1950"
        text image_path "Original image path"
        text processed_path "Preprocessed image"
        text layout_metadata JSON "Cell coordinates"
        timestamp created_at
        timestamp updated_at
    }

    census_household {
        int household_id PK
        int page_id FK
        text dwelling_number
        text family_number
        text address
        text enumeration_district
        text sheet_number
        int line_number_start
        int line_number_end
        int prev_page_id FK "Cross-page tracking"
        int next_page_id FK "Cross-page tracking"
        timestamp created_at
    }

    census_entry {
        int entry_id PK
        int household_id FK
        int person_id FK "Matched RootsMagic PersonID"
        real match_confidence "0.0-1.0"
        int line_number
        text review_status "pending/approved/corrected/flagged"
        text reviewed_by
        timestamp reviewed_at
        timestamp created_at
        timestamp updated_at
    }

    census_field_value {
        int value_id PK
        int entry_id FK
        text field_name "e.g., name, age, occupation, income_1940"
        text field_value "String representation"
        text field_type "text/integer/date"
        int provenance_id FK "Link to OCR metadata"
        timestamp created_at
        timestamp updated_at
    }

    census_field_provenance {
        int provenance_id PK
        text ocr_model "tesseract/kraken/calamari/vision_llm"
        real ocr_confidence "0.0-1.0"
        text raw_ocr_text "Before normalization"
        text cell_coordinates JSON
        text cell_image_path
        timestamp created_at
    }

    census_review_log {
        int log_id PK
        int entry_id FK
        int value_id FK "Specific field edited"
        text reviewer_id
        text action "approve/correct/flag/skip"
        text field_name
        text old_value
        text new_value
        text notes
        timestamp created_at
    }
```

## Design Philosophy: Flexible Field Storage

**Problem**: Each census year has a completely different schema:
- 1850: 11 columns (no relationship to head)
- 1900: 30 columns (added relationship, nativity, citizenship)
- 1940: 31 columns (employment, income, education, migration)
- 1790-1840: Only household head counted

**Solution**: Use an Entity-Attribute-Value (EAV) pattern for census data:

1. **census_entry** stores only metadata (person_id, review_status, match_confidence)
2. **census_field_value** stores actual census data as field/value pairs
3. **census_field_provenance** tracks OCR metadata for each extracted value

**Benefits:**
- ✅ Handles any census year without schema changes
- ✅ Maintains full provenance (OCR model, confidence, raw text)
- ✅ Queryable with SQL (filter by field_name)
- ✅ Supports year-specific fields (e.g., "income_1940", "education_level_1940")
- ✅ Easy to add new census years without database migrations

**Trade-offs:**
- Queries require JOINs and pivot operations for multi-field queries
- Slightly more complex than fixed-column schema
- Storage overhead (field names repeated per entry)

**Example**: Storing a 1900 census entry with 30 fields creates:
- 1 row in `census_entry` (metadata)
- 30 rows in `census_field_value` (one per field)
- ~10-15 rows in `census_field_provenance` (OCR metadata per cell, shared across fields from same cell)

## Table Descriptions

### census_page
Represents a census page image and its metadata. Each page corresponds to one scanned census image from RootsMagic.

**Key Features:**
- Links to RootsMagic MediaID (unique constraint)
- Stores both original and preprocessed image paths
- Layout metadata (JSON) stores cell coordinates and row/column structure
- Can optionally link to primary person in RootsMagic

### census_household
Represents a household unit within a census page. Households may span multiple pages (prev_page_id/next_page_id).

**Key Features:**
- Dwelling and family numbers for household identification
- Address and enumeration district metadata
- Line number ranges for the household on the page
- Cross-page tracking for households split across images

### census_entry
Represents a single person entry in a census record. **Stores only metadata** - actual census data is in census_field_value.

**Key Features:**
- Links to RootsMagic PersonID when matched
- Match confidence score for fuzzy matching
- Review workflow tracking (status, reviewer, timestamp)
- Minimal schema - flexible for any census year structure

### census_field_value
Stores actual census field values for each entry. **This is the flexible schema that accommodates different census years.**

**Key Features:**
- One row per field per entry (EAV pattern)
- field_name identifies what the field is (e.g., "name", "age", "occupation", "income_1940")
- field_value stores the actual value as text
- field_type provides hint for parsing ("text", "integer", "date")
- Links to provenance for OCR metadata
- Queryable by field name for cross-year analysis

### census_field_provenance
Provenance tracking for OCR extraction. **One provenance record can be shared by multiple field values** (e.g., a single OCR cell might contain "John, 42").

**Key Features:**
- OCR model used and confidence score
- Raw OCR text before normalization/parsing
- Cell coordinates and cropped image path for review UI
- Reusable across multiple field values from same OCR cell

### census_review_log
Audit log for all reviewer actions. Immutable record of changes.

**Key Features:**
- Before/after values for corrections
- Action type (approve, correct, flag, skip)
- Reviewer ID and timestamp
- Optional notes for complex decisions

## Indexes

Performance indexes on common query patterns:

```sql
-- Page lookups
CREATE INDEX idx_page_media ON census_page(media_id);
CREATE INDEX idx_page_year ON census_page(census_year);

-- Entry lookups
CREATE INDEX idx_entry_person ON census_entry(person_id);
CREATE INDEX idx_entry_status ON census_entry(review_status);
CREATE INDEX idx_entry_household ON census_entry(household_id);

-- Household lookups
CREATE INDEX idx_household_page ON census_household(page_id);

-- Provenance and review logs
CREATE INDEX idx_provenance_entry ON census_field_provenance(entry_id);
CREATE INDEX idx_review_entry ON census_review_log(entry_id);
```

## Integration with RootsMagic

The sidecar database integrates with RootsMagic through two key foreign keys:

1. **census_page.media_id** → RootsMagic MultimediaTable.MediaID
2. **census_entry.person_id** → RootsMagic PersonTable.PersonID

This allows:
- Census entries to be queried alongside RootsMagic person data
- Media files to be located using RootsMagic's media management
- Biographies to incorporate census information
- Timeline enrichment with census events

## Example Queries

### Get all census entries for a person
```sql
SELECT
    ce.entry_id,
    cp.census_year,
    cp.image_path,
    ce.line_number,
    ce.match_confidence
FROM census_entry ce
JOIN census_household ch ON ce.household_id = ch.household_id
JOIN census_page cp ON ch.page_id = cp.page_id
WHERE ce.person_id = 123
ORDER BY cp.census_year;
```

### Get specific field values for an entry
```sql
-- Get name and age for an entry
SELECT
    field_name,
    field_value,
    field_type
FROM census_field_value
WHERE entry_id = 456
  AND field_name IN ('name', 'age', 'occupation')
ORDER BY field_name;
```

### Get all fields for an entry (pivot-style query)
```sql
-- Get all fields as columns (requires knowing field names)
SELECT
    e.entry_id,
    MAX(CASE WHEN fv.field_name = 'name' THEN fv.field_value END) as name,
    MAX(CASE WHEN fv.field_name = 'age' THEN fv.field_value END) as age,
    MAX(CASE WHEN fv.field_name = 'occupation' THEN fv.field_value END) as occupation
FROM census_entry e
LEFT JOIN census_field_value fv ON e.entry_id = fv.entry_id
WHERE e.entry_id = 456
GROUP BY e.entry_id;
```

### Get pending review items by year with key fields
```sql
SELECT
    ce.entry_id,
    cp.census_year,
    cp.image_path,
    ce.match_confidence,
    MAX(CASE WHEN fv.field_name = 'name' THEN fv.field_value END) as name,
    MAX(CASE WHEN fv.field_name = 'age' THEN fv.field_value END) as age
FROM census_entry ce
JOIN census_household ch ON ce.household_id = ch.household_id
JOIN census_page cp ON ch.page_id = cp.page_id
LEFT JOIN census_field_value fv ON ce.entry_id = fv.entry_id
WHERE ce.review_status = 'pending'
  AND cp.census_year = 1900
GROUP BY ce.entry_id, cp.census_year, cp.image_path, ce.match_confidence
ORDER BY ce.match_confidence ASC
LIMIT 50;
```

### Get OCR confidence metrics
```sql
SELECT
    cfp.ocr_model,
    AVG(cfp.ocr_confidence) as avg_confidence,
    COUNT(DISTINCT fv.value_id) as field_count
FROM census_field_provenance cfp
JOIN census_field_value fv ON cfp.provenance_id = fv.provenance_id
JOIN census_entry ce ON fv.entry_id = ce.entry_id
JOIN census_household ch ON ce.household_id = ch.household_id
JOIN census_page cp ON ch.page_id = cp.page_id
WHERE cp.census_year = 1940
GROUP BY cfp.ocr_model
ORDER BY avg_confidence DESC;
```

### Cross-census analysis (find all occupations across years)
```sql
-- Find occupation progression for a person across census years
SELECT
    cp.census_year,
    fv.field_value as occupation
FROM census_entry ce
JOIN census_household ch ON ce.household_id = ch.household_id
JOIN census_page cp ON ch.page_id = cp.page_id
JOIN census_field_value fv ON ce.entry_id = fv.entry_id
WHERE ce.person_id = 123
  AND fv.field_name = 'occupation'
ORDER BY cp.census_year;
```
