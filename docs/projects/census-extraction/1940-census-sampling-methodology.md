# 1940 Census Sampling Methodology

**Date:** 2025-10-15
**Status:** ✅ Documented and Implemented in Metadata
**Feature:** Sample-only field tracking for 1940 census supplemental questions

---

## Overview

The 1940 US Federal Census was the **first census to use sampling methodology**. Supplemental questions (columns 35-50) were only asked for persons enumerated on **lines 14 and 29** of each page, representing approximately **5% of the population**.

This design decision was made to:
1. Reduce burden on enumerators and respondents
2. Gather more detailed information from a representative sample
3. Test statistical sampling for future censuses

---

## Which Lines Were Sampled?

**Sample Lines:** 14 and 29 on each page

**Page Structure:**
- Each enumeration sheet had 2 sides (A and B)
- Each side had 40 lines
- Total of 80 lines per sheet
- Sample lines: 14A, 29A, 14B, 29B
- **2 sample lines per 40 lines = 5% sample**

---

## Supplemental Questions (Columns 35-50)

The following 10 fields were **only asked for sample lines**:

### 1. Occupation and Industry Codes
- `fields.occupation_code` - Numerical occupation code
- `fields.industry_code` - Numerical industry code

### 2. Veteran Status
- `fields.veteran_status` - Whether veteran of U.S. military or naval forces
- `fields.veteran_war` - Which war or military service

### 3. Income and Social Security
- `fields.social_security` - Income of $50+ from non-wage sources
- `fields.deductions` - Federal Old-Age Insurance deductions

### 4. Marital History
- `fields.marital_events` - Whether married, widowed, or divorced in 1939
- `fields.num_marriages` - Number of times married
- `fields.age_first_marriage` - Age at first marriage

### 5. Fertility (Women Only)
- `fields.children_born` - Number of children ever born

---

## Implementation in Census Metadata

### Schema Fields

Added to `census_field_metadata` table:

```sql
sample_only BOOLEAN DEFAULT FALSE,  -- TRUE if only for sample lines
sample_lines JSONB,                  -- Which lines: [14, 29] for 1940
```

### Querying Sample-Only Fields

```sql
-- Get all sample-only fields for 1940
SELECT field_path, display_name, sample_lines
FROM census_field_metadata
WHERE census_year = 1940 AND sample_only = TRUE;
```

**Result:** 10 fields with `sample_lines = [14, 29]`

### Validating Census Entries

When processing census data, the system can now:

1. **Check if person was on sample line:**
   ```python
   is_sample_line = entry.line_number in [14, 29]
   ```

2. **Warn if sample-only field has value for non-sample line:**
   ```python
   if not is_sample_line and entry.fields.get('veteran_status'):
       warn("veteran_status should only exist for sample lines 14, 29")
   ```

3. **Guide biography generation:**
   ```python
   # Only include sample fields if person was on sample line
   if is_sample_line:
       include_supplemental_questions(entry.fields)
   ```

---

## Example: Jesse Dorsey Iams (1940)

From integration test (`PersonID=1651`):

**Household members:**
1. Jesse Dorsey Iams - Line 25 → **NOT a sample line**
2. Margaret Shannon Iams - Line 26 → **NOT a sample line**
3. Donald Richard Iams - Line 27 → **NOT a sample line**
4. John Dorsey Iams - Line 28 → **NOT a sample line**
5. Kathrine Virginia Iams - Line 29 → **✓ SAMPLE LINE!**
6. Sarah Kathrine Shannon - Line 30 → **NOT a sample line**
7. Mary Johnson (servant) - Line 31 → **NOT a sample line**

**Expected behavior:**
- Only Kathrine (line 29) should have values for supplemental questions
- Other household members should have NULL for sample-only fields
- Biography generator should only mention supplemental data for Kathrine

---

## Historical Context

### Why Sample Lines 14 and 29?

The Bureau of Census chose lines 14 and 29 because:
1. **Systematic sampling** - Every 15th person after line 14 (14, 29, 44, 59...)
2. **Representative** - Distributed evenly across page
3. **Easy for enumerators** - Simple rule to remember
4. **Quality control** - Could verify sample selection

### Impact on Genealogy

**Advantages:**
- Richer data for sample persons (veteran status, marital history, fertility)
- More detailed occupational coding
- Income and employment data

**Limitations:**
- Only 5% of population has supplemental data
- May miss important details for non-sample persons
- Requires understanding of sampling to interpret correctly

**Common Mistakes:**
- Assuming missing supplemental data means "unknown" (it means "not asked")
- Comparing sample-only fields across all persons (only 5% have valid data)
- Not documenting which household members were on sample lines

---

## Metadata Statistics

From `census_field_metadata` table for 1940:

```
Total fields: 34
├── Common fields (all persons): 24
├── Sample-only fields (lines 14 & 29): 10
├── With narrative templates: 14
└── Enum/categorical fields: 8
```

**Sample-only fields distribution:**
- Priority 4: veteran_status, veteran_war
- Priority 5: children_born
- Priority 6: social_security, marital_events
- Priority 7: deductions, num_marriages, age_first_marriage
- Priority 10: occupation_code, industry_code

---

## Bibliography Generation Implications

### Template-Based Generation

```python
def generate_census_narrative(entry, metadata):
    # Check if person was on sample line
    is_sample_line = entry.line_number in [14, 29]

    for field_meta in metadata:
        # Skip sample-only fields for non-sample persons
        if field_meta['sample_only'] and not is_sample_line:
            continue

        value = entry.fields.get(field_meta['field_path'])
        if value:
            # Generate narrative from template
            ...
```

### LLM-Enhanced Generation

```python
def generate_llm_narrative(entry, metadata):
    # Build context
    context = {
        "is_sample_line": entry.line_number in [14, 29],
        "available_fields": get_available_fields(entry, metadata),
        "sample_methodology": "1940 census used sampling for supplemental questions..."
    }

    prompt = f"""
    Generate biography paragraph. Note: This person was{'not ' if not context['is_sample_line'] else ' '}
    on a sample line, so supplemental questions {' are NOT available' if not context['is_sample_line'] else 'ARE available'}.

    Available data: {context['available_fields']}
    """
```

---

## Data Quality Checks

### Validation Rules

1. **Sample-only fields should be NULL for non-sample lines**
   ```sql
   -- Flag suspicious entries
   SELECT entry_id, line_number, name
   FROM census_entry
   WHERE census_year = 1940
     AND line_number NOT IN (14, 29)
     AND (fields->>'veteran_status') IS NOT NULL;
   ```

2. **Sample lines should have supplemental data**
   ```sql
   -- Warn about missing supplemental data for sample lines
   SELECT entry_id, line_number, name
   FROM census_entry
   WHERE census_year = 1940
     AND line_number IN (14, 29)
     AND (fields->>'veteran_status') IS NULL
     AND (fields->>'num_marriages') IS NULL;
   ```

3. **Cross-check with enumeration district totals**
   - Expected: ~5% of persons have supplemental data
   - Actual: Count persons with veteran_status or num_marriages

---

## Future Census Years

**Other censuses with sampling:**

- **1950 Census** - 20% sample (lines ending in 0 or 5)
- **1960 Census** - 25% sample (every 4th housing unit)
- **1970-2000** - Long form (~16-20% sample)
- **2010+** - American Community Survey (continuous sampling)

Each will need similar `sample_only` and `sample_lines` tracking in metadata.

---

## Files Modified

1. **`rmagent/census/models/schema.py`**
   - Added `sample_only` and `sample_lines` to `CensusFieldMetadata` model
   - Added columns to SQL CREATE TABLE
   - Added index on `sample_only`

2. **`scripts/populate_1940_census_metadata_v2.py`**
   - Updated to include sample_only flags
   - Set `sample_lines = [14, 29]` for supplemental fields
   - Helper function `create_field()` for cleaner syntax

3. **`scripts/migrate_metadata_add_sample_fields.py`**
   - Migration script to add columns to existing table

4. **`docs/projects/census-extraction/1940-census-sampling-methodology.md`**
   - This document

---

## References

1. **National Archives:** https://www.archives.gov/research/census/1940
2. **1940 Census Instructions to Enumerators** (Bureau of Census, 1940)
3. **FamilySearch Wiki:** https://www.familysearch.org/wiki/en/1940_United_States_Federal_Census
4. **IPUMS Documentation:** https://usa.ipums.org/usa/sampdesc.shtml#us1940a

---

**Status:** Sample methodology fully documented and implemented in metadata system ✅
