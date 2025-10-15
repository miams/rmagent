# Census Sidecar Database Schema

## Entity-Relationship Diagram

```mermaid
erDiagram
    census_page ||--o{ census_household : contains
    census_household ||--o{ census_entry : contains
    census_entry ||--o{ census_field_provenance : "has provenance"
    census_entry ||--o{ census_review_log : "has review log"

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
        text name
        int age
        text sex
        text race
        text relationship_to_head
        text marital_status
        text birthplace
        text father_birthplace
        text mother_birthplace
        text occupation
        text extended_fields JSON "Year-specific fields"
        text review_status "pending/approved/corrected/flagged"
        text reviewed_by
        timestamp reviewed_at
        timestamp created_at
        timestamp updated_at
    }

    census_field_provenance {
        int provenance_id PK
        int entry_id FK
        text field_name
        text ocr_model "tesseract/kraken/calamari/vision_llm"
        real ocr_confidence "0.0-1.0"
        text raw_ocr_text
        text normalized_value
        text cell_coordinates JSON
        text cell_image_path
        timestamp created_at
    }

    census_review_log {
        int log_id PK
        int entry_id FK
        text reviewer_id
        text action "approve/correct/flag/skip"
        text field_name
        text old_value
        text new_value
        text notes
        timestamp created_at
    }
```

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
Represents a single person entry in a census record. Links to RootsMagic PersonID when matched.

**Key Features:**
- Standard fields common across census years (name, age, sex, etc.)
- Extended fields (JSON) for year-specific columns (e.g., income_1940)
- Match confidence score for fuzzy matching
- Review workflow tracking (status, reviewer, timestamp)

### census_field_provenance
Provenance tracking for individual census fields. Records OCR metadata and transformations.

**Key Features:**
- OCR model used and confidence score
- Raw OCR text before normalization
- Cell coordinates and cropped image path for review UI
- Links to specific field in parent entry

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
    ce.*,
    cp.census_year,
    cp.image_path
FROM census_entry ce
JOIN census_household ch ON ce.household_id = ch.household_id
JOIN census_page cp ON ch.page_id = cp.page_id
WHERE ce.person_id = 123
ORDER BY cp.census_year;
```

### Get pending review items by year
```sql
SELECT
    ce.entry_id,
    ce.name,
    ce.age,
    cp.census_year,
    cp.image_path
FROM census_entry ce
JOIN census_household ch ON ce.household_id = ch.household_id
JOIN census_page cp ON ch.page_id = cp.page_id
WHERE ce.review_status = 'pending'
  AND cp.census_year = 1900
ORDER BY ce.match_confidence ASC
LIMIT 50;
```

### Get OCR confidence metrics
```sql
SELECT
    cfp.ocr_model,
    AVG(cfp.ocr_confidence) as avg_confidence,
    COUNT(*) as field_count
FROM census_field_provenance cfp
JOIN census_entry ce ON cfp.entry_id = ce.entry_id
JOIN census_household ch ON ce.household_id = ch.household_id
JOIN census_page cp ON ch.page_id = cp.page_id
WHERE cp.census_year = 1940
GROUP BY cfp.ocr_model
ORDER BY avg_confidence DESC;
```
