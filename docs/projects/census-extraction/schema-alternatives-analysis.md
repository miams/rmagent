# Census Schema Alternatives Analysis

**Date**: 2025-10-15
**Status**: Recommendation
**Context**: Choosing between EAV, JSON, Hybrid, or other approaches

## Use Case Requirements

### Data Characteristics
- **17 census years**: 1790-1950 (excluding 1890)
- **Varying schemas**: 5-31 columns per year
- **Volume**: ~42,000 entries (1,400 images × ~30 people/image)
- **Read-heavy**: Extract once, review many times
- **Query patterns**:
  - Most common: Get all fields for ONE entry (review UI)
  - Common: Get specific field across years (occupation progression)
  - Less common: Complex analytics across entries

### Technical Constraints
- **SQLite** (not PostgreSQL with JSONB)
- **Embedded database** (no separate document DB)
- **Human-in-loop review** (UI loads one entry at a time)

## Option 1: Pure EAV (Current Implementation)

### Schema
```sql
CREATE TABLE census_entry (
    entry_id INTEGER PRIMARY KEY,
    household_id INTEGER,
    person_id INTEGER,
    match_confidence REAL,
    review_status TEXT
);

CREATE TABLE census_field_value (
    value_id INTEGER PRIMARY KEY,
    entry_id INTEGER,
    field_name TEXT,
    field_value TEXT,
    field_type TEXT
);
```

### Pros
- ✅ Handles ANY census year without schema changes
- ✅ Easy to add new census years (no migrations)
- ✅ Full provenance per field (links to OCR metadata)
- ✅ Cross-year queries by field_name

### Cons
- ❌ Query complexity (JOINs + pivoting for every query)
- ❌ Performance overhead (30 JOINs to get one entry)
- ❌ No data type safety (everything TEXT)
- ❌ Storage overhead (field names repeated)
- ❌ Harder to index specific fields

### Query Examples
```sql
-- Get all fields for review UI (30 rows → 1 result)
SELECT
    MAX(CASE WHEN field_name = 'name' THEN field_value END) as name,
    MAX(CASE WHEN field_name = 'age' THEN field_value END) as age,
    MAX(CASE WHEN field_name = 'occupation' THEN field_value END) as occupation
    -- ... repeat for 30 fields
FROM census_field_value
WHERE entry_id = 456
GROUP BY entry_id;

-- Occupation progression (fast - filters on field_name)
SELECT census_year, field_value as occupation
FROM census_entry ce
JOIN census_field_value fv ON ce.entry_id = fv.entry_id
WHERE ce.person_id = 123 AND fv.field_name = 'occupation'
ORDER BY census_year;
```

### Performance Analysis
- **42,000 entries × 30 fields = 1,260,000 rows** in census_field_value
- Review UI query: 30 JOINs per entry
- Estimated query time: 10-50ms (acceptable for interactive UI)
- Index on (entry_id, field_name) critical

## Option 2: JSON Column (SQLite JSON1)

### Schema
```sql
CREATE TABLE census_entry (
    entry_id INTEGER PRIMARY KEY,
    household_id INTEGER,
    person_id INTEGER,
    census_year INTEGER,
    fields TEXT  -- JSON: {"name": "John", "age": "42", "occupation": "Farmer"}
);
```

### Pros
- ✅ Simple schema (one row per entry)
- ✅ Flexible (handles any year)
- ✅ No JOINs for single entry queries
- ✅ Less storage overhead

### Cons
- ❌ SQLite JSON1 less powerful than PostgreSQL JSONB
- ❌ Limited indexing (can't index specific JSON keys efficiently)
- ❌ All values stored as strings (no type safety)
- ❌ Provenance tracking harder (need separate table)

### Query Examples
```sql
-- Get all fields (simple!)
SELECT JSON_EXTRACT(fields, '$.name') as name,
       JSON_EXTRACT(fields, '$.age') as age,
       JSON_EXTRACT(fields, '$.occupation') as occupation
FROM census_entry
WHERE entry_id = 456;

-- Occupation progression (requires JSON_EXTRACT)
SELECT census_year, JSON_EXTRACT(fields, '$.occupation') as occupation
FROM census_entry
WHERE person_id = 123
ORDER BY census_year;
```

### Performance Analysis
- **42,000 rows** (one per entry)
- Review UI query: O(1) - single row lookup
- JSON parsing overhead minimal
- Can't efficiently filter "all farmers" without full table scan

## Option 3: Hybrid (Common Fields + JSON)

### Schema
```sql
CREATE TABLE census_entry (
    entry_id INTEGER PRIMARY KEY,
    household_id INTEGER,
    person_id INTEGER,
    census_year INTEGER,

    -- Common fields (present in most/all census years)
    name TEXT,
    age INTEGER,
    sex TEXT,
    birthplace TEXT,
    occupation TEXT,

    -- Year-specific fields
    extended_fields TEXT  -- JSON for income_1940, education_1940, etc.
);
```

### Pros
- ✅ Fast queries for common fields (80% of use cases)
- ✅ Proper data types for common fields
- ✅ Simple queries (no JOINs for basic review)
- ✅ Still flexible for year-specific fields

### Cons
- ❌ Have to decide what's "common" (subjective)
- ❌ 1790-1840 censuses don't have individual names
- ❌ Mixing paradigms (columns + JSON)
- ❌ Schema changes if "common" definition changes

### Common Fields Analysis

**Fields present in 10+ census years:**
- name (1850-1950) - 11 years
- age (1850-1950) - 11 years
- sex (1850-1950) - 11 years
- race/color (1850-1950) - 11 years
- birthplace (1850-1950) - 11 years
- occupation (1850-1950) - 11 years

**Fields present in 5-9 years:**
- relationship_to_head (1880-1950) - 8 years
- marital_status (1880-1950) - 8 years
- father_birthplace (1880-1950) - 8 years
- mother_birthplace (1880-1950) - 8 years

**Recommendation for "common":**
- name, age, sex, race, birthplace, occupation (6 fields)

### Query Examples
```sql
-- Get common fields (fast, no JOINs)
SELECT name, age, sex, occupation
FROM census_entry
WHERE entry_id = 456;

-- Get extended fields
SELECT JSON_EXTRACT(extended_fields, '$.income_1940') as income
FROM census_entry
WHERE entry_id = 456 AND census_year = 1940;

-- Occupation progression (simple!)
SELECT census_year, occupation
FROM census_entry
WHERE person_id = 123
ORDER BY census_year;
```

### Performance Analysis
- **42,000 rows** (one per entry)
- Review UI query: O(1) for common fields + JSON parse for extended
- Common field queries: Fast with standard indexes
- Best of both worlds for typical queries

## Option 4: Year-Specific Tables

### Schema
```sql
CREATE TABLE census_entry_1850 (
    entry_id INTEGER PRIMARY KEY,
    household_id INTEGER,
    name TEXT,
    age INTEGER,
    sex TEXT
    -- ... 11 columns for 1850
);

CREATE TABLE census_entry_1900 (
    entry_id INTEGER PRIMARY KEY,
    household_id INTEGER,
    name TEXT,
    age INTEGER,
    relationship_to_head TEXT
    -- ... 30 columns for 1900
);
-- ... 17 tables total
```

### Pros
- ✅ Proper data types per year
- ✅ Schema matches historical forms exactly
- ✅ Fast within-year queries

### Cons
- ❌ Can't query across years easily
- ❌ 17 separate tables
- ❌ Code duplication (insert/update logic per table)
- ❌ Refactoring nightmare

**Verdict: Not recommended for this use case**

## Option 5: Wide Table (All Fields, Mostly NULL)

### Schema
```sql
CREATE TABLE census_entry (
    entry_id INTEGER PRIMARY KEY,
    -- Common fields
    name TEXT,
    age INTEGER,
    -- 1900-specific
    relationship_to_head TEXT,
    nativity TEXT,
    -- 1940-specific
    income INTEGER,
    education_level TEXT,
    -- ... ~100 columns total
);
```

### Pros
- ✅ Simple queries
- ✅ Proper data types

### Cons
- ❌ 90%+ NULL values (massive waste)
- ❌ Confusing schema
- ❌ Hard to maintain

**Verdict: Not recommended**

## Recommendation: Hybrid Approach

### Why Hybrid Wins

1. **Review UI Performance** (Primary use case)
   - Common fields: Fast column access
   - Extended fields: Fast JSON extraction
   - No complex pivoting or 30 JOINs

2. **Cross-Year Analytics**
   - Common fields: Standard SQL
   - Extended fields: JSON_EXTRACT filters

3. **Storage Efficiency**
   - 6 common columns vs 1,260,000 EAV rows
   - JSON for remaining ~24 fields per entry

4. **Maintainability**
   - Clear separation: common vs year-specific
   - No 17 separate tables to manage

5. **Query Complexity**
   - 80% of queries are simple column access
   - 20% need JSON_EXTRACT (acceptable)

### Recommended Schema

```sql
CREATE TABLE census_entry (
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
    household_id INTEGER NOT NULL,
    person_id INTEGER,
    match_confidence REAL,
    line_number INTEGER,

    -- Common fields (present in 10+ census years)
    name TEXT,
    age INTEGER,
    sex TEXT,
    race TEXT,
    birthplace TEXT,
    occupation TEXT,

    -- Year-specific fields (JSON)
    extended_fields TEXT,  -- JSON for relationship_to_head, income_1940, etc.

    -- Review tracking
    review_status TEXT DEFAULT 'pending',
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (household_id) REFERENCES census_household(household_id)
);

-- Provenance stays separate (links to OCR metadata)
CREATE TABLE census_field_provenance (
    provenance_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    field_path TEXT NOT NULL,  -- e.g., "name", "extended.income_1940"
    ocr_model TEXT NOT NULL,
    ocr_confidence REAL,
    raw_ocr_text TEXT,
    cell_coordinates TEXT,
    cell_image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (entry_id) REFERENCES census_entry(entry_id)
);

-- Indexes
CREATE INDEX idx_entry_person ON census_entry(person_id);
CREATE INDEX idx_entry_name ON census_entry(name);
CREATE INDEX idx_entry_occupation ON census_entry(occupation);
CREATE INDEX idx_provenance_entry ON census_field_provenance(entry_id);
```

### Migration Path from Current EAV

If we decide to switch:

1. **Keep current EAV implementation for M0/M1** (already working)
2. **Evaluate performance during M1 OCR pilot** (10 images)
3. **Switch to hybrid before M2** if EAV proves slow
4. **Migration script**: Pivot census_field_value into columns + JSON

Migration is straightforward:
```sql
INSERT INTO census_entry_new (entry_id, name, age, occupation, extended_fields)
SELECT
    entry_id,
    MAX(CASE WHEN field_name = 'name' THEN field_value END) as name,
    MAX(CASE WHEN field_name = 'age' THEN field_value END) as age,
    MAX(CASE WHEN field_name = 'occupation' THEN field_value END) as occupation,
    JSON_GROUP_OBJECT(
        CASE WHEN field_name NOT IN ('name', 'age', 'occupation')
             THEN field_name END,
        CASE WHEN field_name NOT IN ('name', 'age', 'occupation')
             THEN field_value END
    ) as extended_fields
FROM census_field_value
GROUP BY entry_id;
```

## Decision Matrix

| Criteria | EAV | JSON | Hybrid | Year Tables | Wide Table |
|----------|-----|------|--------|-------------|------------|
| Query simplicity | ❌ | ✅ | ✅ | ✅ | ✅ |
| Performance (review UI) | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| Performance (analytics) | ✅ | ⚠️ | ✅ | ❌ | ✅ |
| Flexibility (new years) | ✅ | ✅ | ✅ | ❌ | ⚠️ |
| Data type safety | ❌ | ❌ | ✅ | ✅ | ✅ |
| Storage efficiency | ⚠️ | ✅ | ✅ | ✅ | ❌ |
| Maintainability | ⚠️ | ✅ | ✅ | ❌ | ⚠️ |
| Provenance tracking | ✅ | ⚠️ | ✅ | ✅ | ✅ |
| **TOTAL SCORE** | 3/8 | 5/8 | **7/8** | 4/8 | 4/8 |

## Final Recommendation

**Start with current EAV** (already implemented), **benchmark during M1 pilot**, **switch to Hybrid if needed**.

### Why This Approach?

1. **EAV works for pilot** (10 images, ~300 entries)
2. **Real performance data** before committing
3. **Easy migration** if hybrid proves better
4. **No wasted effort** (EAV → Hybrid migration is one SQL query)

### Decision Points

- **After M1 (10 images)**: Measure query times
  - If review UI < 100ms: Keep EAV
  - If review UI > 100ms: Switch to Hybrid

- **After M2 (1,400 images)**: Reassess at scale
  - 42,000 entries: If slow, switch to Hybrid
  - If fast enough: Keep EAV

## References

- SQLite JSON1 Extension: https://www.sqlite.org/json1.html
- EAV Pattern: https://en.wikipedia.org/wiki/Entity%E2%80%93attribute%E2%80%93value_model
- PostgreSQL JSONB: https://www.postgresql.org/docs/current/datatype-json.html (for comparison)
