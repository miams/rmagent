# Ground Truth Data Standards - Census Extraction

**Purpose**: Define standards for creating ground truth datasets used to validate and iterate on LLM-based census extraction prompts.

**Created**: 2025-10-16
**Status**: Active Standard

---

## Overview

Ground truth files contain manually verified census data used to:
1. Measure LLM extraction accuracy
2. Iterate on prompt design until achieving 95%+ accuracy
3. Regression testing when modifying prompts
4. Document edge cases and ambiguous handwriting

## File Naming Convention

**Format**: `YYYY, State, County - Surname, Given (ground).json`

**Examples**:
- `1940, West Virginia, Mineral - Iames, Marshall M. (ground).json`
- `1900, Pennsylvania, Allegheny - Smith, John (ground).json`

**Location**: `data/census/images/processed/`

## JSON Structure

```json
{
  "census_image": "1940, West Virginia, Mineral - Iames, Marshall M..jpg",
  "ground_truth_metadata": {
    "enumeration_district": "7",
    "sheet_number": "13A",
    "county": "Mineral",
    "state": "West Virginia",
    "city_or_town": "",
    "township_or_district": "Frankfort District",
    "supervisor_district": "6",
    "enumeration_date": "April 13, 1940",
    "enumerator_name": "Ida Ward Warner",
    "metadata_warnings": ""
  },
  "ground_truth_people": [
    {
      "person_id": 5519,
      "status": "found",
      "census_line": 13,
      "name": "Iames, McKinley M.",
      "relationship": "Head",
      "sex": "M",
      "race": "W",
      "age": 36,
      ...
      "notes": ""
    }
  ]
}
```

## Critical Standards

### 1. Ditto Marks (Surname Repetition)

**Rule**: Always record the **RESOLVED** full name in the `name` field. Document what actually appears on the census in the `notes` field.

**Why**: The LLM's job is to resolve ditto marks. Ground truth represents the correct answer after resolution.

#### Type 1: Quotation Marks (`"`)

**Census shows**: `", Wilma M.`

**Ground truth**:
```json
{
  "name": "Iames, Wilma M.",
  "notes": "Ditto marks for surname (shown as \" on census)"
}
```

#### Type 2: Horizontal Line/Underscore (`_____`)

**Census shows**: `______, Richard T.`

**Ground truth**:
```json
{
  "name": "Iames, Richard T.",
  "notes": "Ditto marks for surname (shown as _____ on census)"
}
```

#### Type 3: Written "do" or "ditto"

**Census shows**: `do, Allan F.`

**Ground truth**:
```json
{
  "name": "Iames, Allan F.",
  "notes": "Ditto marks for surname (shown as 'do' on census)"
}
```

#### Type 4: Blank/Implicit

**Census shows**: `, Harold E.` (just comma and given name)

**Ground truth**:
```json
{
  "name": "Iames, Harold E.",
  "notes": "Surname implied by household context (blank on census)"
}
```

### 2. String vs. Numeric Fields

**String fields** (pre-quoted in template):
- `street_address`, `house_number`, `name`, `relationship`, `sex`, `race`
- `marital_status`, `school_attendance`, `education_level`, `birthplace`
- `occupation`, `industry`, `class_of_worker`, etc.

**Numeric fields** (no quotes):
- `census_line`, `dwelling_number`, `age`, `home_value`
- `hours_worked`, `weeks_worked_1939`, `income_wages`, `income_self_employment`

**Empty fields**: Use `""` for empty strings, omit or use `null` for missing numbers

### 3. Ambiguous Handwriting

When handwriting is unclear, record your best interpretation and document uncertainty:

```json
{
  "occupation": "Coal miner",
  "notes": "Occupation could be 'Coal miner' or 'Coal mine laborer' - handwriting unclear"
}
```

```json
{
  "age": 42,
  "notes": "Age could be 42 or 47 - digit unclear"
}
```

### 4. Partial/Illegible Fields

When a field is completely illegible:

```json
{
  "birthplace": "[ILLEGIBLE]",
  "notes": "Birthplace column damaged/illegible on census image"
}
```

### 5. Empty vs. Dash vs. "No"

Census forms distinguish between:
- **Empty/blank**: Field intentionally left blank → `""`
- **Dash** (`-`): Not applicable → `"-"`
- **"No"**: Explicit negative response → `"No"`

Preserve the distinction exactly as shown.

### 6. Supplemental Schedule Data

**Rule**: When a person has supplemental data at the bottom of the census page:

```json
{
  "person_id": 5524,
  "census_line": 14,
  "name": "Iames, Wilma M.",
  "has_supplemental_data": true,
  "supplemental_references_line": 14,
  "usual_occupation": "Housewife",
  "usual_industry": "",
  "usual_class_of_worker": "",
  "for_women_children_born": "4",
  "notes": "Has supplemental schedule entry referencing line 14"
}
```

**Important**: The supplemental schedule is physically separate (2 rows at bottom of page), but data should be merged into the person's record.

### 7. Interviewee Designation

Census takers marked the household informant with a circled X (or similar mark) after their name in column 7.

**Extraction rule:**
- If circled X is clearly visible → `"interviewee": "Yes"`
- If unclear or absent → `"interviewee": ""`

```json
{
  "name": "Iames, Wilma M.",
  "interviewee": "",
  "notes": "Circled X present but too faint to mark as definite"
}
```

### 8. Confidence Scoring

**Note**: Confidence scores are for LLM output only, NOT ground truth documents. Ground truth files should leave `confidence` blank.

For LLM extraction, include confidence level based on handwriting clarity:

- **high**: All critical fields (name, age, relationship) clearly legible
- **medium**: Some fields unclear but name identifiable
- **low**: Significant uncertainty, difficult handwriting

```json
{
  "confidence": "high",
  "notes": "Clear handwriting throughout"
}
```

## Quality Guidelines

1. **Transcribe exactly**: Don't correct spelling errors or standardize abbreviations
2. **Preserve formatting**: If census shows "W.Va." don't expand to "West Virginia"
3. **Context is key**: Use household structure to resolve ambiguities
4. **Document everything**: When in doubt, explain your interpretation in notes
5. **Cross-check**: Verify ages, relationships make sense within household

## Usage Workflow

### Step 1: Create Template
Ground truth templates were generated during development using temporary test scripts (not in repository).

### Step 2: Manual Transcription
Fill in ground truth by viewing census image side-by-side with JSON file.

### Step 3: Validation Test
Validation was performed during development using temporary test scripts (not in repository).

### Step 4: Iterate Prompt
- Identify fields where LLM output != ground truth
- Adjust prompt instructions
- Re-run validation
- Repeat until 95%+ accuracy achieved

## Accuracy Metrics

**Target**: 95%+ field-level accuracy

**Critical fields** (must be 100% on clear handwriting):
- `census_line` (row number)
- `name` (with ditto marks resolved)
- `age`
- `relationship`

**High priority fields** (target 95%+):
- `occupation`, `industry`, `income_wages`
- `birthplace`, `residence_1935_city`

**Lower priority fields** (target 90%+):
- `education_level`, `hours_worked`
- `weeks_worked_1939`, `class_of_worker`

## Edge Cases

### Case 1: Person Not Found
If expected person is genuinely not on this census page:

```json
{
  "person_id": 9999,
  "status": "not_found",
  "name": "Iames, Robert L.",
  "notes": "Expected person not found on this census page - may be on different sheet or enumeration district"
}
```

### Case 2: Split Households
When family spans two sheets:

```json
{
  "metadata_warnings": "Household continues on next sheet (14A)",
  "notes": "Only 3 of 6 family members appear on this page"
}
```

### Case 3: Name Variations
When census name differs significantly from database:

```json
{
  "person_id": 5519,
  "name": "Iames, McKinley M.",
  "notes": "Database shows 'Marshall McKinley Iames' but census shows 'McKinley M.' - same person, goes by middle name"
}
```

## Version History

- **2025-10-16**: Initial standard created (ditto marks, field types, confidence)
- Future updates will be documented here

## Related Documents

- [`implementation-plan.md`](implementation-plan.md) - Overall M0-M2 roadmap
- [`census-fields-verification.md`](census-fields-verification.md) - Column definitions per year
- [`sidecar-schema-diagram.md`](sidecar-schema-diagram.md) - Database schema for storing extracted data
