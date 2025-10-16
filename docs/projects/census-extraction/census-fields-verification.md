# Census Fields Verification (1790-1950)

**Purpose**: Verify all census year field definitions against actual census forms
**Source**: ~/Genealogy/RootsMagic/Files/Records - Census/
**Date**: 2025-01-15

---

## Instructions for Review

For each census year below:
1. ✅ = Field is in our current config (`census_years.py`)
2. ❌ = Field is MISSING from our current config
3. ⚠️ = Field may be incorrect or needs clarification

**Review Process:**
- Open the actual census image from your collection
- Compare the column headers against the list below
- Mark any discrepancies or add missing fields

---

## 1950 Census (15 fields)

**Status**: Not yet implemented (1950 folder is empty)
**Source**: Wikipedia

1. address
2. farm_residence
3. name *(common)*
4. relationship_to_head
5. sex *(common)*
6. race *(common)*
7. age *(common)*
8. marital_status
9. birthplace *(common)*
10. naturalization_status (if foreign born)
11. employment_status
12. hours_worked_week
13. occupation *(common)*
14. industry
15. class_of_worker

**Notes**:
- Sample questions about income, marital history, fertility not included (not on all forms)
- Need actual 1950 form to verify

---

## 1940 Census (31→38+ fields)

**Status**: ⚠️ Implemented but needs significant expansion
**Verification**: `/1940 Federal/1940, California, Los Angeles - Iiams, John Calvin.jpg`
**User Review Date**: 2025-10-15

### Current Implementation (31 columns):

1. ✅ street_address
2. ✅ house_number
3. ✅ dwelling_number
4. ✅ home_ownership (owned/rented)
5. ✅ home_value (if owned)
6. ✅ farm_residence
7. ✅ name *(common)*
8. ✅ relationship_to_head
9. ✅ sex *(common)*
10. ✅ race *(common)*
11. ✅ age *(common)*
12. ✅ marital_status
13. ✅ school_attendance
14. ✅ education_level
15. ✅ birthplace *(common)*
16. ✅ citizenship (for foreign born)
17. ✅ residence_1935_city
18. ✅ residence_1935_county
19. ✅ residence_1935_state
20. ✅ farm_residence_1935
21. ✅ employment_status
22. ✅ seeking_work
23. ✅ emergency_work
24. ✅ hours_worked
25. ✅ duration_unemployment
26. ✅ occupation *(common)*
27. ✅ industry
28. ✅ class_of_worker
29. ✅ weeks_worked (1939)
30. ✅ income_wages
31. ✅ income_self_employment

### Missing Critical Fields (User Review Findings):

**Sheet/Page Metadata** (HIGH VALUE - Essential for citations):
- ❌ line_number (Column 1, INTEGER, required) - First column, essential for record location
- ❌ sheet_number (TEXT) - e.g., "1A", "61A", "81A" - three-tier numbering system
- ❌ enumeration_district (TEXT) - e.g., "15-1" - for citation and navigation
- ❌ enumeration_date (DATE) - Date of enumeration (user specifically requested)

**Person Record Fields**:
- ❌ is_informant (BOOLEAN) - Circled X marker next to person interviewed (source reliability)
- ❌ monthly_rent (INTEGER) - Rental amount (we have home_value for owners but not rent)

**Supplementary Questions** (HIGH VALUE - Asked only on lines 14 & 29):
- ❌ father_birthplace_supp (TEXT) - Father's birthplace (supplementary question)
- ❌ mother_birthplace_supp (TEXT) - Mother's birthplace (supplementary question)
- ❌ mother_tongue_supp (TEXT) - Language spoken before immigration (supplementary)
- ❌ veteran_status_supp (TEXT) - Veteran status details (supplementary)
- ❌ social_security_supp (TEXT) - Social Security info (supplementary)

**Fields to SKIP** (LOW VALUE):
- ⛔ Lettered columns (A, B, C, etc.) - Post-enumeration administrative codes, no genealogical value

**Action**: Add 7 core fields + 5 supplementary question fields = 12 new fields total

---

## 1930 Census (31+ fields)

**Status**: Not yet implemented
**Verification**: `/1930 Federal/1930, California, Los Angeles - Iiams, John Calvin.jpg`

### Fields to Extract:

1. address (street, house number)
2. name *(common)*
3. relationship_to_head
4. home_ownership_status
5. home_value (if owned)
6. monthly_rent (if rented)
7. radio_set_ownership
8. farm_residence
9. sex *(common)*
10. race *(common)*
11. age *(common)*
12. marital_status
13. age_at_first_marriage
14. school_attendance
15. literacy
16. birthplace *(common)*
17. father_birthplace
18. mother_birthplace
19. language_spoken_before_immigration (if foreign-born)
20. immigration_year
21. naturalization_status
22. english_speaking_ability
23. occupation *(common)*
24. industry
25. worker_class
26. employment_status (worked previous day)
27. veteran_status
28. native_american_blood_status (if applicable)
29. tribal_affiliation (if applicable)

**Action**: Extract exact column headers and order from actual form

---

## 1920 Census (29 fields)

**Status**: Not yet implemented
**Verification**: `/1920 Federal/1920, Arizona, Cochise - Ijams, Sheldon.jpg`

### Fields to Extract:

1. address
2. dwelling_number
3. family_number
4. name *(common)*
5. relationship_to_head
6. home_ownership_status
7. home_mortgage_status (if owned)
8. sex *(common)*
9. race *(common)*
10. age *(common)*
11. marital_status
12. immigration_year (if foreign-born)
13. naturalization_status
14. naturalization_year
15. school_attendance
16. literacy
17. birthplace *(common)*
18. mother_tongue (if foreign-born)
19. father_birthplace
20. mother_birthplace
21. english_speaking_ability
22. occupation *(common)*
23. industry
24. class_of_worker

**Action**: Extract exact column headers and order from actual form

---

## 1910 Census (32 fields)

**Status**: Not yet implemented
**Verification**: `/1910 Federal/1910, Arizona, Graham - Ijams, Edward T.jpg`

### Fields to Extract:

1. address
2. dwelling_number
3. family_number
4. name *(common)*
5. relationship_to_head
6. sex *(common)*
7. race *(common)*
8. age *(common)*
9. marital_status
10. years_married
11. children_born (for women)
12. children_living (for women)
13. birthplace *(common)*
14. father_birthplace
15. mother_birthplace
16. mother_tongue
17. immigration_year (if foreign-born)
18. naturalization_status
19. english_language_ability
20. occupation *(common)*
21. industry
22. worker_class
23. employment_status (out of work)
24. literacy (read/write)
25. school_attendance
26. home_ownership_status
27. home_mortgage_status (if owned)
28. farm_or_house
29. veteran_status (Union/Confederate)
30. disabilities (blind, deaf, dumb)

**Action**: Extract exact column headers and order from actual form

---

## 1900 Census (30 fields)

**Status**: ✅ Already implemented in census_years.py
**Verification**: `/1900 Federal/1900, California, Los Angeles - Iiams, James Calvin.jpg`

### Current Implementation (30 columns):

1. ✅ sheet_number
2. ✅ line_number
3. ✅ dwelling_number
4. ✅ family_number
5. ✅ name *(common)*
6. ✅ relationship_to_head
7. ✅ race
8. ✅ sex *(common)*
9. ✅ birth_month
10. ✅ birth_year
11. ✅ age *(common)*
12. ✅ marital_status
13. ✅ years_married
14. ✅ mother_children_born
15. ✅ mother_children_living
16. ✅ birthplace *(common)*
17. ✅ father_birthplace
18. ✅ mother_birthplace
19. ✅ immigration_year
20. ✅ years_in_us
21. ✅ naturalization
22. ✅ occupation *(common)*
23. ✅ months_unemployed
24. ✅ school_attendance
25. ✅ literacy_read
26. ✅ literacy_write
27. ✅ english_speaking
28. ✅ home_ownership
29. ✅ home_mortgage
30. ✅ farm_or_house

**Status**: Appears complete - verify against actual form

---

## 1880 Census (23+ fields)

**Status**: Not yet implemented
**Verification**: `/1880 Federal/1880, Alabama, Lauderdale - Ijams, Joseph.jpg`

### Fields to Extract:

1. dwelling_number
2. family_number
3. name *(common)*
4. relationship_to_head
5. sex *(common)*
6. race *(common)*
7. age *(common)*
8. marital_status
9. birth_month (if born within year)
10. marriage_month (if married within year)
11. occupation *(common)*
12. months_unemployed
13. sickness_or_disability
14. school_attendance
15. literacy_read
16. literacy_write
17. birthplace *(common)*
18. father_birthplace
19. mother_birthplace

**Note**: Similar to 1870 but dropped real estate and personal estate values

**Action**: Extract exact column headers and order from actual form

---

## 1870 Census (20 fields)

**Status**: Not yet implemented
**Verification**: `/1870 Federal/1870, Alabama, Lauderdale - Ijams, Joseph.jpg`

### Fields to Extract:

1. dwelling_number
2. family_number
3. name *(common)*
4. age *(common)*
5. sex *(common)*
6. race (color)
7. occupation (profession) *(common)*
8. real_estate_value
9. personal_estate_value
10. birthplace *(common)*
11. father_birthplace (if foreign-born)
12. mother_birthplace (if foreign-born)
13. birth_month (if born within year)
14. marriage_month (if married within year)
15. school_attendance
16. literacy_cannot_read
17. literacy_cannot_write
18. disability_status
19. male_citizen_21_plus (voting eligibility)

**Action**: Extract exact column headers and order from actual form

---

## 1860 Census (14 fields)

**Status**: Not yet implemented
**Verification**: `/1860 Federal/1860, Alabama, Lauderdale - Ijams, Joseph.jpg`

### Fields to Extract:

1. dwelling_number
2. family_number
3. name *(common)*
4. age *(common)*
5. sex *(common)*
6. race (color)
7. occupation (for persons over 15) *(common)*
8. real_estate_value
9. personal_estate_value
10. birthplace *(common)*
11. married_within_year
12. school_attendance
13. literacy_status (persons over 20 who cannot read/write)
14. disability_status

**Note**: First census after 1850 to record individual names

**Action**: Extract exact column headers and order from actual form

---

## 1850 Census (11 fields)

**Status**: ✅ Already implemented in census_years.py
**Verification**: `/1850 Federal/1850, Illinois, Boone - Iams, Francis Marion.jpg`

### Current Implementation (11 columns):

1. ✅ dwelling_number
2. ✅ family_number
3. ✅ name *(common)*
4. ✅ age *(common)*
5. ✅ sex *(common)*
6. ✅ race (color)
7. ✅ occupation *(common)*
8. ✅ birthplace *(common)*
9. ✅ married_within_year
10. ✅ school_attendance
11. ✅ literacy

**Missing Fields from Wikipedia**:
- ❌ disability_status ("deaf and dumb, blind, psychologically ill or idiotic")
- ❌ real_estate_value
- ❌ social_status ("whether a pauper or convict")

**Action**: Verify against actual form and add missing fields if present

---

## 1840 Census and Earlier (Aggregate Data)

**Status**: Not yet implemented
**Type**: Household aggregates (no individual names except head of household)

### 1840 Census (Aggregate counts)
- head_of_household_name
- address
- age group counts (free white males/females, slaves, free colored)
- disability counts (deaf/dumb, blind, insane/idiotic by race)
- employment by occupation class
- schools and scholars
- illiteracy count
- revolutionary pensioners

### 1830 Census (Aggregate counts)
- head_of_household_name
- address
- age group counts (free white males/females, slaves, free colored)
- disability counts (deaf/dumb by age, blind)
- foreigners not naturalized

### 1820, 1810, 1800, 1790 Census
- Similar aggregate household counts
- No individual person records

**Decision Needed**: Should we implement these? Most genealogy work focuses on 1850+.

---

## Summary of Actions

### Immediate (Fix existing configs):
1. ❌ **1940**: Add 12 new fields (user review complete 2025-10-15)
   - Sheet metadata: `line_number`, `sheet_number`, `enumeration_district`, `enumeration_date`
   - Person fields: `is_informant`, `monthly_rent`
   - Supplementary questions: 5 fields for lines 14 & 29 only
   - Skip: Lettered columns (post-enumeration codes)
2. ❌ **1850**: Add `disability_status`, `real_estate_value`, `social_status` fields (needs user verification)

### To Implement (14 new years):
1. **1930** - 31+ fields
2. **1920** - 29 fields
3. **1910** - 32 fields
4. **1880** - 23+ fields
5. **1870** - 20 fields
6. **1860** - 14 fields

### Low Priority (aggregate data):
7. **1840** - Household aggregates
8. **1830** - Household aggregates
9. **1820** - Household aggregates
10. **1810** - Household aggregates
11. **1800** - Household aggregates
12. **1790** - Household aggregates

---

## Next Steps

1. **Review**: Check each verified year against actual census images
2. **Extract**: Get exact column headers from forms for unimplemented years
3. **Update**: Modify `census_years.py` with verified/new configurations
4. **Test**: Validate schema can handle all field types

---

## Common Fields (Present in 10+ years: 1850-1950)

These 6 fields are stored as typed columns in our Hybrid PostgreSQL schema:

1. **name** (TEXT) - All years 1850-1950
2. **age** (INTEGER) - All years 1850-1950
3. **sex** (TEXT) - All years 1850-1950
4. **race** (TEXT) - All years 1850-1950 (called "Color" in earlier years)
5. **birthplace** (TEXT) - All years 1850-1950
6. **occupation** (TEXT) - All years 1850-1950

All other fields stored in JSONB `fields` column for flexibility.
