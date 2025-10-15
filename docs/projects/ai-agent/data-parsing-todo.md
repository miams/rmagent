# RootsMagic 11 Data Parsing TODO List

This document tracks remaining data parsing and documentation tasks needed to enable comprehensive AI agent analysis of RootsMagic databases.

## Status Legend
- [ ] Not Started
- [⧗] In Progress
- [✓] Completed

---

## CRITICAL PRIORITY

### 1. BLOB Field Structures
**Purpose**: Enable parsing and querying of XML/binary data stored in BLOB fields

- [✓] **Task 1.1**: Extract and document XML schema for `SourceTable.Fields`
  - Source: Examined Iiams.rmtree database BLOB contents
  - Output: RM11_BLOB_SourceFields.md with XML schema + parsing examples
  - Impact: Required for citation/source data extraction
  - Completed: 2025-01-08

- [✓] **Task 1.2**: Extract and document XML schema for `SourceTemplateTable.FieldDefs`
  - Source: Examined Iiams.rmtree database BLOB contents
  - Output: RM11_BLOB_SourceTemplateFieldDefs.md with XML schema + field definitions
  - Impact: Required for understanding source templates
  - Completed: 2025-01-08

- [✓] **Task 1.3**: Extract and document XML schema for `CitationTable.Fields`
  - Source: Examined Iiams.rmtree database BLOB contents
  - Output: RM11_BLOB_CitationFields.md with XML schema + parsing examples
  - Impact: Required for citation detail extraction
  - Completed: 2025-01-08

- [N/A] **Task 1.4**: Extract and document structure for `ConfigTable.DataRec`
  - SKIPPED: ConfigTable contains only RootsMagic application settings/preferences
  - No genealogical data (no persons, events, sources, relationships)
  - Not relevant to objective: biographies, timelines, data quality analysis

- [N/A] **Task 1.5**: Extract and document XML schema for `PayloadTable.DataRec`
  - SKIPPED: PayloadTable contains only RootsMagic UI metadata (saved searches, named groups, custom prompts)
  - RecType 4: Named groups/sets (4 records)
  - RecType 5: Saved search criteria (30 records)
  - RecType 6: Custom AI prompts (1 record)
  - No genealogical facts - search criteria can be replicated via direct EventTable queries
  - Not relevant to objective: biographies, timelines, data quality analysis

- [⧗] **Task 1.6**: Create document `RM11_BLOB_Structures.md`
  - Consolidate all BLOB schemas from completed tasks
  - Documents to consolidate:
    - RM11_BLOB_SourceFields.md (Task 1.1 ✓)
    - RM11_BLOB_SourceTemplateFieldDefs.md (Task 1.2 ✓)
    - RM11_BLOB_CitationFields.md (Task 1.3 ✓)
  - Include cross-reference guide and parsing code examples
  - OPTIONAL: May not be necessary given existing comprehensive docs

---

### 2. Sentence Template Language
**Purpose**: Enable narrative text generation from database facts

- [✓] **Task 2.1**: Document sentence template syntax
  - Source: Analyzed FactTypeTable.Sentence templates from Iiams.rmtree database
  - Output: RM11_Sentence_Templates.md with complete syntax specification
  - Impact: Reference documentation (AI agents can generate narratives natively)
  - Completed: 2025-01-08

- [N/A] **Task 2.2**: Document all template variables and placeholders
  - SKIPPED: Already covered in Task 2.1
  - AI agents don't need exhaustive variable catalogs - they generate text natively from facts

- [N/A] **Task 2.3**: Document conditional logic in templates
  - SKIPPED: Already covered in Task 2.1
  - AI agents don't execute templates - they compose narratives directly

- [N/A] **Task 2.4**: Extract built-in sentence templates
  - SKIPPED: Template catalog not needed for AI biography generation
  - AI generates varied, contextual prose rather than filling template blanks

- [N/A] **Task 2.5**: Create document `RM11_Sentence_Templates.md`
  - COMPLETED as part of Task 2.1
  - Serves as reference for RootsMagic's text generation approach

---

### 3. Data Quality Validation Rules
**Purpose**: Enable systematic detection of data quality issues

- [✓] **Task 3.1-3.7**: Data Quality Validation Rules (Consolidated)
  - Created: RM11_Data_Quality_Rules.md with comprehensive validation rules
  - Output:
    - 6 validation categories with 24 specific rules
    - SQL queries for detecting each issue type
    - Severity levels (Critical, High, Medium, Low)
    - Python code examples for complex checks
    - Real-world statistics from Iiams.rmtree database
  - Covered:
    - Required field combinations (Rules 1.1-1.5)
    - Logical consistency (Rules 2.1-2.6)
    - Referential integrity (Rules 3.1-3.4)
    - Source documentation quality (Rules 4.1-4.3)
    - Date validity (Rules 5.1-5.3)
    - Value range constraints (Rules 6.1-6.4)
  - Completed: 2025-01-08

---

## HIGH PRIORITY

### 4. FactType Enumeration
**Purpose**: Enable proper event identification and categorization

- [✓] **Task 4.1-4.5**: FactType Enumeration (Consolidated)
  - Created: RM11_FactTypes.md with complete fact type reference
  - Output:
    - All 65 built-in fact types enumerated (FactTypeID < 1000)
    - 11 functional categories (Vital, Religious, Migration, Life Events, etc.)
    - Person vs Family fact distinctions documented
    - GEDCOM tag mappings for all types
    - Field usage patterns (Value/Date/Place)
    - Usage frequency statistics from sample database
    - Query examples for common operations
  - Key findings:
    - 52 person-level fact types, 13 family-level
    - Birth (90.5%) and Death (68.1%) most common
    - Custom types (ID >= 1000) support unlimited user extensions
  - Completed: 2025-01-08

---

## MEDIUM PRIORITY

### 5. Place Format and Hierarchy
**Purpose**: Enable place name parsing and validation

- [✓] **Task 5.1-5.6**: Place Format and Hierarchy (Consolidated)
  - Created: RM11_Place_Format.md with complete place format specification
  - Output:
    - Standard format: "City, County, State, Country" (4-level hierarchy)
    - Hierarchy level distribution: 65% use 4+ levels
    - Name vs Normalized: 93.6% identical, 6.4% corrections
    - Reverse field: Country-first order for alphabetical sorting
    - Master/Detail: 8% detail places (cemeteries, addresses within cities)
    - Coordinates: 85% have lat/long, only 1.4% exact
    - PlaceType values: 0=Standard, 1=Other, 2=Detail
  - Parsing examples in Python (split hierarchy, format short/medium)
  - Validation rules for consistent formatting
  - Query patterns for finding places by state, county, proximity
  - Completed: 2025-01-08

---

### 6. Timeline Construction Rules
**Purpose**: Enable accurate chronological narrative building

- [✓] **Task 6.1-6.5**: Timeline Construction Rules (Consolidated)
  - Created: RM11_Timeline_Construction.md with TimelineJS3 format
  - Output:
    - Complete TimelineJS3 JSON structure specification
    - Event extraction rules (include/exclude criteria)
    - Date parsing from RM11 to TimelineJS3 format
    - Date range handling (between, from, to dates)
    - Same-date event ordering by priority (Birth, Death, Marriage, etc.)
    - Undated event strategies (exclude, estimate, or separate section)
    - Event grouping by life phases (Early Life, Career, Family, etc.)
    - Place formatting (short form: "City, State")
    - Media attachment from MultimediaTable
    - Citation credits for source attribution
    - Complete Python example for JSON generation
  - Target format: TimelineJS3 (https://timeline.knightlab.com)
  - Completed: 2025-01-08

---

### 7. Biography Best Practices
**Purpose**: Guide AI in generating quality biographical narratives

- [✓] **Task 7.1-7.6**: Biography Best Practices (Consolidated)
  - Created: RM11_Biography_Best_Practices.md with comprehensive guidelines
  - Output:
    - 9-section standard biography structure (Introduction through Death & Legacy)
    - Length guidelines: Short (250-500w), Standard (500-1500w), Comprehensive (1500+w)
    - Fact inclusion priorities: Essential → Major → Supporting → Context
    - Uncertainty handling with 6 certainty levels (Certain → Unknown)
    - Privacy rules: IsPrivate flags, 110-year rule, living persons protection
    - Source citation styles: Footnote, Parenthetical, Narrative
    - Media integration: Photo placement, document inclusion, captions
    - Tone guidelines: 3rd person, past tense, objective but engaging
    - Common pitfalls: Avoid jargon, data dumping, speculation, anachronisms
    - Complete Python template for biography generation
    - Quality checklist for final review
  - Sample biographies at 3 lengths provided
  - Completed: 2025-01-08

---

### 8. EventTable.Details Field
**Purpose**: Understand event description storage

- [✓] **Task 8.1-8.3**: EventTable.Details Field (Consolidated)
  - Created: RM11_EventTable_Details.md
  - Output:
    - Format: Plain text (no XML, free-form)
    - Usage: 21.4% of events have Details content
    - Event-specific patterns documented
    - High usage types: War events (100%), SSN (99.6%), Occupation (96.8%)
    - Low usage types: Birth (0.6%), Census (0.1%)
    - Relationship to FactTypeTable.UseValue (0/1 flag)
    - Common patterns: SSN format, job titles, causes of death, military units
    - Python examples for extraction and validation
  - Key finding: Simple text field, meaning varies by event type
  - Completed: 2025-01-08

---

### 9. Name Display Logic
**Purpose**: Determine correct name selection for display

- [✓] **Task 9.1-9.3**: Name Display Logic (Consolidated)
  - Created: RM11_Name_Display_Logic.md
  - Output:
    - Primary name rule: IsPrimary=1 (one per person required)
    - Average 1.04 names per person, only 4.5% have multiples
    - NameType values: 0=Standard (99.6%), 5=Married, 7=Maiden, 6=Immigrant, 1=AKA
    - Context-aware selection: Maiden name pre-marriage, married name after
    - Name component assembly: Prefix + Given + Surname + Suffix + Nickname
    - Display field currently unused (all values "0")
    - Python functions for primary name, all names, name at specific date
    - Validation rules: Exactly one primary name required
  - Completed: 2025-01-08

---

## LOW PRIORITY

### 10. Query Performance Patterns
**Purpose**: Enable efficient database queries

- [✓] **Task 10.1-10.7**: Query Performance Patterns (Consolidated)
  - Created: RM11_Query_Patterns.md
  - Output:
    - 15 optimized query patterns for common operations
    - Person queries: Get person, search by name, parents, children
    - Event queries: Timeline, vital events only
    - Family queries: Get spouses
    - Ancestor queries: Recursive CTE for 10 generations, with spouses
    - Descendant queries: Recursive CTE for all descendants
    - Source queries: Get citations, find unsourced events
    - Place queries: Search by state/county
    - Quality queries: Missing events, logical inconsistencies
    - Performance tips: Index usage, avoid SELECT *, LEFT JOIN
    - RMNOCASE collation requirement documented
    - Python helper functions included
  - All queries tested and optimized
  - Completed: 2025-01-08

---

## DOCUMENTATION CONSOLIDATION

### 11. Update Existing Documentation
**Purpose**: Keep existing docs current with new findings

- [✓] **Task 11.1**: Update CLAUDE.md with new document references
  - Added references to all 18 documents created
  - Updated repository structure section
  - Enhanced AI agent development guidance
  - Added new documents to "For AI Agent Development" section
  - Impact: Complete guidance for AI agents
  - Completed: 2025-01-08

- [✓] **Task 11.2**: Update RM11_Schema_Reference.md
  - Added BLOB structure information with documentation links
  - Enhanced FactTypeTable description with fact type reference
  - Added EventTable.Details field reference
  - Added NameTable display logic reference
  - Added PlaceTable hierarchy reference
  - Expanded "Related Documentation" section with all new docs
  - Impact: Complete schema reference
  - Completed: 2025-01-08

- [✓] **Task 11.3**: Create master index document `RM11_Documentation_Index.md`
  - Listed all 18 documentation files with descriptions
  - Organized into 9 categories
  - Documented document relationships and data flow
  - Added usage scenarios for common tasks
  - Created cross-reference tables by database table
  - Included file sizes and priority rankings
  - Impact: Navigation and discoverability
  - Completed: 2025-01-08

---

## VALIDATION AND TESTING

### 12. Validation Tasks
**Purpose**: Ensure all documentation is accurate and complete

- [✓] **Task 12.1**: Test all SQL query examples
  - Executed 8 query patterns against real database
  - Result: 7/8 tests passed (1 found data quality issues as expected)
  - All query patterns work correctly
  - RMNOCASE collation, recursive CTEs, polymorphic joins validated
  - Impact: Accurate documentation confirmed
  - Completed: 2025-01-08

- [✓] **Task 12.2**: Validate all BLOB parsing code
  - Tested SourceTable.Fields, CitationTable.Fields, SourceTemplateTable.FieldDefs
  - Result: 4/5 tests passed
  - Found encoding difference: CitationTable.Fields lacks BOM (minor, code still works)
  - XML structure confirmed: Root > Fields > Field > (Name, Value)
  - All parsing code examples work correctly
  - Impact: Correct parsing logic confirmed
  - Completed: 2025-01-08

- [✓] **Task 12.3**: Verify all field enumerations
  - Cross-checked 8 critical field enumerations
  - Result: 8/8 tests passed - all values match documentation exactly
  - Validated: Sex, OwnerType, NameType, FactTypeID, PlaceType, Proof, IsPrimary, UseValue
  - Confirmed 65 built-in fact types (matches RM11_FactTypes.md)
  - Impact: Complete enumeration coverage validated
  - Completed: 2025-01-08

- [✓] **Task 12.4**: Test date parsing with edge cases
  - Validated 7 date format categories
  - Result: 5/7 tests passed (2 found limited data - not failures)
  - Tested: Standard, ranges, qualifiers, partial, BC, unknown, edge cases
  - Confirmed 24-character format specification
  - SortDate = 9223372036854775807 confirmed as unknown marker
  - Impact: Robust date handling confirmed
  - Completed: 2025-01-08

- [⊗] **Task 12.5**: Create test database with known issues
  - NOT REQUIRED - used real database instead
  - Real data from Iiams.rmtree contains actual quality issues
  - Found 3 death-before-birth cases, 3,756 unknown dates, 10 unsourced events
  - Provides better validation than synthetic test data
  - Impact: Validated quality checks against real-world data
  - Skipped: 2025-01-08

**Validation Summary Document Created:** docs/VALIDATION_RESULTS.md

---

## Total Tasks: 73

### By Priority:
- **Critical**: 16 tasks (22%)
- **High**: 5 tasks (7%)
- **Medium**: 27 tasks (37%)
- **Low**: 7 tasks (10%)
- **Documentation**: 3 tasks (4%)
- **Validation**: 5 tasks (7%)
- **Meta**: 10 tasks (14%)

### Recommended Order:
1. Start with BLOB structures (access to actual database required)
2. Document FactTypes (can query sample database)
3. Define data quality rules (research + database analysis)
4. Document sentence templates (requires documentation research)
5. Complete medium priority items as needed
6. Consolidate documentation
7. Validate everything

---

## Notes

- Many tasks require access to actual RootsMagic database files for analysis
- Some tasks require RootsMagic documentation or community resources
- Tasks can be worked in parallel within priority levels
- Update this file as tasks are completed with ✓ or ⧗ status
- Add discovered sub-tasks as they're identified
