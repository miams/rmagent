# 1940 Federal Census - Complete Column Reference

**Census Year**: 1940 (April 1, 1940 enumeration date)
**Total Columns**: 50 data columns + office codes (A-Z)
**Structure**: Main table (34 columns) + Supplemental schedule (16 columns)

---

## Main Table (Columns 1-34)

All households and individuals appear in the main table.

| Column # | JSON Field Name | Data Type | Description | Valid Values |
|----------|-----------------|-----------|-------------|--------------|
| 1 | street_name | text | Street, avenue, road, etc. | Often written vertically across multiple rows |
| 2 | house_number | text | House number (or farm name) | Alphanumeric |
| 3 | dwelling_number | integer | Sequential household number | Numeric |
| 4 | home_ownership | text | Home owned or rented | O=Owned, R=Rented |
| 5 | home_value | text | Dollar amount if owned | Blank if rented |
| 6 | farm_residence | text | Does household live on farm? | Yes, No, or blank |
| 7 | name | text | Full name | Format: "Surname, Given" (ditto marks for repeated surnames) |
| 8 | relationship | text | Relationship to head of household | Head, Wife, Son, Daughter, Father, Mother, etc. |
| 9 | sex | text | Sex | M=Male, F=Female |
| 10 | race | text | Color or race | W=White, B=Black, etc. |
| 11 | age | integer | Age at last birthday | Fractions for infants (e.g., 2/12 = 2 months) |
| 12 | marital_status | text | Marital status | S=Single, M=Married, Wd=Widowed, D=Divorced |
| 13 | school_attendance | text | Attended school or college this year | Yes, No, or blank |
| 14 | education_level | text | Highest grade of school completed | Grade number or blank |
| 15 | birthplace | text | Place of birth | State, territory, or foreign country |
| 16 | citizenship | text | Citizenship status | Na=Naturalized, Pa=First papers, Al=Alien, blank=Native |
| 17 | residence_1935_city | text | City/town of residence April 1, 1935 | "Same house", "Same place", or city name |
| 18 | residence_1935_county | text | County of residence April 1, 1935 | County name or blank if same |
| 19 | residence_1935_state | text | State of residence April 1, 1935 | State abbreviation or blank if same |
| 20 | farm_residence_1935 | text | On farm April 1, 1935? | Yes, No, or blank |
| 21 | worked_march_24_30 | text | At work in week of March 24-30, 1940 | Yes, No |
| 22 | emergency_work | text | If at work, was it public emergency work? | Yes, No, or blank |
| 23 | seeking_work | text | If not at work, was seeking work? | Yes, No, or blank |
| 24 | have_job | text | If not seeking work, did have a job/business? | Yes, No, or blank |
| 25 | other_activity | text | If none above, engaged in what activity? | H=Home housework, S=School, U=Unable to work, O=Other |
| 26 | hours_worked | text | Hours worked in week of March 24-30 | Numeric or blank |
| 27 | duration_unemployment | text | Duration of unemployment (weeks) | Numeric or blank |
| 28 | occupation | text | Trade, profession, or kind of work | Free text description |
| 29 | industry | text | Industry or business | Free text description |
| 30 | class_of_worker | text | Class of worker | W=Wage/salary, PW=Paid worker, OA=Own account, E=Employer, NP=Unpaid family |
| 31 | weeks_worked_1939 | text | Number of weeks worked in 1939 | Numeric (0-52) or blank |
| 32 | income_wages | text | Wage or salary income in 1939 | Dollar amount or blank |
| 33 | income_other | text | Other income (non-wage) in 1939 | Dollar amount or blank (if $50+) |
| 34 | number_farm_schedule | text | Farm schedule number | Reference number (e.g., 21, 007, 145) or blank |

---

## Supplemental Schedule (Columns 35-50)

Only selected individuals (usually 2 per page) have supplemental data collected at the bottom of the census page.

**Important**: Supplemental rows reference a line number from the main table (e.g., line 14, line 29).

| Column # | JSON Field Name | Data Type | Description | Valid Values |
|----------|-----------------|-----------|-------------|--------------|
| 35 | name | text | Name (should match main table) | Format: "Surname, Given" |
| 36 | father_birthplace | text | Place of birth of father | State, territory, or foreign country |
| 37 | mother_birthplace | text | Place of birth of mother | State, territory, or foreign country |
| **G** | code_g | — | **Office code (skip)** | — |
| 38 | mother_tongue | text | Language spoken in earliest childhood | Language name |
| **H** | code_h | — | **Office code (skip)** | — |
| 39 | veteran_status | text | Is person a U.S. veteran or wife/widow/child of veteran? | Yes, No |
| 40 | veteran_child_father_dead | text | If child of veteran—is father dead? | Yes, No, or blank |
| 41 | war_service | text | War or military service | W=WWI, S=Spanish-Am/Phil/Boxer, SW=Both, R=Regular/peacetime, Ot=Other |
| **I** | code_i | — | **Office code (skip)** | — |
| 42 | has_social_security_number | text | Has a Federal Social Security Number? | Yes, No |
| 43 | ss_deductions_1939 | text | Deductions for Federal Old-Age Insurance or Railroad Retirement in 1939? | Yes, No |
| 44 | ss_deductions_extent | text | If yes—deductions from what portion of wages? | 1=all, 2=half+, 3=part (<half), 0 or blank |
| 45 | usual_occupation | text | Usual occupation | Free text (may differ from column 28) |
| 46 | usual_industry | text | Usual industry | Free text (may differ from column 29) |
| 47 | usual_class_of_worker | text | Usual class of worker | W, OA, E, NP (same codes as column 30) |
| **J** | code_j | — | **Office code (skip - spans 3 columns)** | — |
| **J** | code_j | — | **Office code (skip)** | — |
| **J** | code_j | — | **Office code (skip)** | — |
| 48 | married_more_than_once | text | Has this woman been married more than once? | Yes, No, or blank (blank if male) |
| 49 | age_at_first_marriage | text | Age at first marriage | Numeric or blank (blank if male) |
| 50 | children_ever_born | text | Number of children ever born (exclude stillbirths) | Numeric or blank (blank if male or never had children) |
| **K-Z** | — | — | **Office codes (skip)** | — |

---

## Office Code Columns (Skip During Extraction)

The following columns are reserved for Census Bureau coding and should **NOT** be extracted:

**Main table**: Letters A-F (interspersed between numeric columns)
**Supplemental schedule**: Letters G-Z (G, H, I, J×3, K-Z)

These columns were filled in by census office staff during processing and are not genealogically relevant.

---

## Special Cases and Conventions

### Ditto Marks (Column 7 - Name)
When a surname repeats within a household, census takers used:
- Quotation marks: `", Given Name`
- Horizontal line: `_____, Given Name`
- Written: `do, Given Name`
- Blank: `, Given Name`

**Always resolve to full name**: `"Iames, Given Name"`

### Interviewee Designation (Column 7 - Name)
Census takers marked the household informant (interviewee) with a circled X after their name in column 7. This indicates who provided the information during the census interview.

**Extraction rule**:
- If circled X (or similar mark) is clearly visible after the name → `interviewee: "Yes"`
- If unclear or absent → `interviewee: ""`

**Note**: This field is not a numbered column but should be captured as metadata for each person.

### Infant Ages (Column 11)
Infants under 1 year shown as fractions:
- `2/12` = 2 months old
- `11/12` = 11 months old

### Same House/Same Place (Columns 17-19)
Common entries for 1935 residence:
- "Same house" = lived in same dwelling
- "Same place" = lived in same city/county

### Literal Transcription Philosophy

**Ground truth = literal transcription, no interpretation.**

Distinguish between:
- **Empty/blank**: Field left blank → `""`
- **Dash**: Literally written as dash → `"-"` (no spaces)
- **"No"**: Explicit text "No" written → `"No"`
- **"0"**: Zero literally written → `"0"`
- **Unusual values**: Transcribe exactly (e.g., `home_value="1"` for a rental)

**Key principles:**
1. Transcribe exactly what appears on the census form
2. Do NOT fill in blank fields with assumed values (e.g., `dwelling_number` only appears once per household)
3. Do NOT interpret or normalize unusual entries
4. Preserve number formatting (e.g., `"1,000"` not `"1000"`)
5. Business logic and interpretation happen in software, not during transcription

### Supplemental Schedule Reference
- Supplemental rows are physically located at the **bottom** of the census page (separate section)
- Each row references a line number from the main table
- Typically 2 people per page have supplemental data (lines 14 and 29 are common)

---

## JSON Field Mapping

When creating ground truth or LLM extraction outputs, use these exact field names for consistency.

**Main table fields (34)**:
```json
{
  "street_name": "",
  "house_number": "",
  "dwelling_number": null,
  "home_ownership": "",
  "home_value": "",
  "farm_residence": "",
  "name": "",
  "relationship": "",
  "sex": "",
  "race": "",
  "age": null,
  "marital_status": "",
  "school_attendance": "",
  "education_level": "",
  "birthplace": "",
  "citizenship": "",
  "residence_1935_city": "",
  "residence_1935_county": "",
  "residence_1935_state": "",
  "farm_residence_1935": "",
  "worked_march_24_30": "",
  "emergency_work": "",
  "seeking_work": "",
  "have_job": "",
  "other_activity": "",
  "hours_worked": "",
  "duration_unemployment": "",
  "occupation": "",
  "industry": "",
  "class_of_worker": "",
  "weeks_worked_1939": "",
  "income_wages": "",
  "income_other": "",
  "number_farm_schedule": ""
}
```

**Supplemental fields (16 additional)**:
```json
{
  "has_supplemental_data": true,
  "supplemental_references_line": 14,
  "father_birthplace": "",
  "mother_birthplace": "",
  "mother_tongue": "",
  "veteran_status": "",
  "veteran_child_father_dead": "",
  "war_service": "",
  "has_social_security_number": "",
  "ss_deductions_1939": "",
  "ss_deductions_extent": "",
  "usual_occupation": "",
  "usual_industry": "",
  "usual_class_of_worker": "",
  "married_more_than_once": "",
  "age_at_first_marriage": "",
  "children_ever_born": ""
}
```

**Note**: Column 35 (supplemental name) is captured but typically matches main table column 7.

---

## References

- 1940 U.S. Census Bureau instructions to enumerators
- [Ground Truth Data Standards](ground-truth-standards.md)
- [Census Extraction Implementation Plan](implementation-plan.md)

**Last Updated**: 2025-10-16
