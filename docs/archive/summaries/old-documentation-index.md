# RootsMagic 11: Documentation Index

**Purpose:** Master index of all RootsMagic 11 database documentation
**Last Updated:** 2025-01-08
**Total Documents:** 18

---

## Quick Start Guide

**For AI Agent Development**, read documents in this order:

1. **RM11_Schema_Reference.md** - Understand database structure
2. **RM11_Date_Format.md** - Parse date fields
3. **RM11_FactTypes.md** - Categorize events
4. **RM11_Query_Patterns.md** - Write efficient queries
5. **RM11_BLOB_SourceFields.md** - Extract source data
6. **RM11_Data_Quality_Rules.md** - Validate data
7. **RM11_Biography_Best_Practices.md** - Generate narratives

---

## Document Categories

### 1. Core Schema (4 documents)

#### RM11_Schema_Reference.md
- **Purpose:** Comprehensive schema reference organized by functional category
- **Size:** ~50K
- **Key Content:**
  - 31 tables organized into 9 categories
  - Field descriptions with examples
  - OwnerType/OwnerID polymorphic pattern
  - Common query patterns
  - Index reference
- **When to Use:** Primary reference for understanding database structure

#### RM11_schema_annotated.sql
- **Purpose:** SQL schema with inline documentation
- **Size:** ~51K
- **Key Content:**
  - Complete CREATE TABLE statements
  - Field descriptions and constraints
  - FK/PK annotations
  - Typical values and enumerations
- **When to Use:** SQL work, schema analysis, database migrations

#### RM11_schema.json
- **Purpose:** Machine-readable JSON Schema
- **Size:** ~109K
- **Key Content:**
  - Type definitions for all tables/fields
  - Index information
  - Field metadata
- **When to Use:** Programmatic validation, code generation

#### RM11_DataDef.yaml
- **Purpose:** Detailed field definitions with enumerations
- **Size:** ~71K
- **Key Content:**
  - All 31 tables with 347 fields
  - Type information and typical values
  - Comments and descriptions
  - Key/Index specifications
- **When to Use:** Field-level reference, enumeration lookups

---

### 2. Date and Time (2 documents)

#### RM11_Date_Format.md ⭐ CRITICAL
- **Purpose:** 24-character date encoding specification
- **Size:** ~12K
- **Key Content:**
  - Position-by-position format specification
  - Date types: Standard, Quaker, Text, Unknown
  - Modifiers: Before, After, Between, From, To
  - Qualifiers: About, Estimated, Calculated
  - BC/AD, double dates, partial dates
  - SortDate integer representation
- **When to Use:** Parsing EventTable.Date, NameTable.Date
- **Critical For:** Timeline construction, date validation, chronological sorting

#### RM11_Date_Format.yaml
- **Purpose:** Structured date format data
- **Size:** ~10K
- **Key Content:**
  - Date type enumerations
  - Modifier codes
  - Qualifier codes
  - Parsing rules in structured format
- **When to Use:** Programmatic date parsing, validation

---

### 3. BLOB Structures (3 documents)

#### RM11_BLOB_SourceFields.md
- **Purpose:** SourceTable.Fields XML structure
- **Size:** ~11K
- **Key Content:**
  - XML schema for source metadata
  - Free-form (TemplateID=0) vs template-based sources
  - Field names by template type (Book, Census, Newspaper, etc.)
  - Python/SQL parsing examples
- **When to Use:** Extracting source-level field data
- **Relationships:** Used with RM11_BLOB_SourceTemplateFieldDefs.md

#### RM11_BLOB_SourceTemplateFieldDefs.md
- **Purpose:** SourceTemplateTable.FieldDefs XML structure
- **Size:** ~24K
- **Key Content:**
  - 433 built-in templates analyzed
  - 4,211 field definitions total
  - Field types: Text (74%), Place (10.7%), Date (10%), Name (5.8%)
  - CitationField flag (False=source-level, True=citation-level)
  - Double-bar notation for full/shortened versions
- **When to Use:** Understanding template structures, field definitions
- **Relationships:** Defines structure for RM11_BLOB_SourceFields.md and RM11_BLOB_CitationFields.md

#### RM11_BLOB_CitationFields.md
- **Purpose:** CitationTable.Fields XML structure
- **Size:** ~20K
- **Key Content:**
  - XML structure identical to SourceFields
  - 95.8% of citations have single Page field
  - Find-a-Grave citations with 10-12 fields
  - 41 unique field names documented
  - Field patterns by source type
- **When to Use:** Extracting citation-specific field values
- **Relationships:** Complements RM11_BLOB_SourceFields.md

---

### 4. Events and Facts (3 documents)

#### RM11_FactTypes.md ⭐ ESSENTIAL
- **Purpose:** Complete fact type reference
- **Size:** ~26K
- **Key Content:**
  - All 65 built-in fact types enumerated (FactTypeID < 1000)
  - 11 functional categories:
    - Vital (Birth, Death, Burial, etc.)
    - Religious (Baptism, Confirmation, etc.)
    - Military (War Veteran, War Branch, etc.)
    - Life Events (Education, Occupation, etc.)
    - Legal (Probate, Will, etc.)
    - Migration (Immigration, Emigration, etc.)
    - Family (Marriage, Divorce, etc.)
    - Census (Census)
    - Attributes (Physical Description, SSN, etc.)
    - Associations (Resided, Associated)
    - Miscellaneous
  - Person vs Family fact distinctions
  - GEDCOM tag mappings
  - Usage frequency statistics
- **When to Use:** Event categorization, event type validation, narrative generation
- **Relationships:** References EventTable.EventType

#### RM11_Sentence_Templates.md
- **Purpose:** Sentence template language reference
- **Size:** ~18K
- **Key Content:**
  - Variable substitution syntax ([person], [Date], [Place])
  - Modifiers for formatting (:first, :Age, :Plain)
  - Conditional logic (<?...>)
  - Choice expressions (&lt;male|female&gt;)
  - Template examples from FactTypeTable
- **When to Use:** Understanding RootsMagic's text generation approach
- **Note:** AI agents generate text natively - this is for reference only

#### RM11_EventTable_Details.md
- **Purpose:** EventTable.Details field specification
- **Size:** ~13K
- **Key Content:**
  - Plain text field (no XML structure)
  - 21.4% of events have Details content
  - Usage patterns by event type:
    - War events (100%): War name, military unit
    - SSN (99.6%): Social Security numbers
    - Occupation (96.8%): Job titles
    - Death (5.2%): Cause of death
  - Relationship to FactTypeTable.UseValue flag
  - Common content patterns and validation
- **When to Use:** Extracting event descriptions, enriching narratives
- **Relationships:** UseValue in FactTypeTable indicates when Details is used

---

### 5. Places and Geography (1 document)

#### RM11_Place_Format.md
- **Purpose:** Place name hierarchy and parsing specification
- **Size:** ~21K
- **Key Content:**
  - Standard format: "City, County, State, Country"
  - 4-level hierarchy (65% of places use 4+ levels)
  - Name vs Normalized vs Reverse fields
  - Master/Detail relationships (8% detail places like cemeteries)
  - Coordinate system (85% have lat/long, only 1.4% exact)
  - PlaceType values: 0=Standard, 1=LDS Temple, 2=Detail
  - Parsing and formatting examples in Python
- **When to Use:** Place name parsing, validation, geographic queries
- **Relationships:** Used by EventTable.PlaceID, EventTable.SiteID

---

### 6. Names and Relationships (2 documents)

#### RM11_Name_Display_Logic.md
- **Purpose:** Name selection and display rules
- **Size:** ~16K
- **Key Content:**
  - IsPrimary flag (one per person required)
  - NameType values: 0=Standard (99.6%), 5=Married, 7=Maiden, 1=AKA, 6=Immigrant
  - Average 1.04 names per person, 4.5% have multiples
  - Context-aware selection (maiden name pre-marriage, married name after)
  - Name component assembly: Prefix + Given + Surname + Suffix + Nickname
  - Display field currently unused (all values "0")
  - Python functions for name selection
- **When to Use:** Selecting appropriate name for display, biographical context
- **Relationships:** References NameTable fields

#### RM11_Relationships.md
- **Purpose:** Genealogical relationship calculation
- **Size:** ~11K
- **Key Content:**
  - Relate1/Relate2/Flags calculation system
  - Direct line vs collateral relationships
  - Cousin degree and removal formulas
  - In-law and half-relationship encoding
  - Calculation examples
- **When to Use:** Calculating relationships between persons
- **Relationships:** Uses PersonTable.Relate1, PersonTable.Relate2, PersonTable.Flags

---

### 7. Data Quality (1 document)

#### RM11_Data_Quality_Rules.md ⭐ IMPORTANT
- **Purpose:** Comprehensive validation rules
- **Size:** ~28K
- **Key Content:**
  - 24 specific validation rules across 6 categories:
    1. Required field combinations (5 rules)
    2. Logical consistency (6 rules) - death after birth, etc.
    3. Referential integrity (4 rules)
    4. Source documentation quality (3 rules)
    5. Date validity (3 rules)
    6. Value range constraints (4 rules)
  - SQL queries for detecting each issue type
  - Severity levels: Critical, High, Medium, Low
  - Python code examples for complex checks
  - Real-world statistics from sample database
- **When to Use:** Data quality analysis, validation, cleanup
- **Relationships:** Cross-references all major tables

---

### 8. Query Optimization (1 document)

#### RM11_Query_Patterns.md ⭐ ESSENTIAL
- **Purpose:** Optimized SQL query patterns
- **Size:** ~18K
- **Key Content:**
  - 15 common query patterns:
    - Person queries (get person, search by name, parents, children)
    - Event queries (timeline, vital events)
    - Family queries (get spouses)
    - Ancestor queries (recursive CTE, 10 generations, with spouses)
    - Descendant queries (recursive CTE)
    - Source queries (get citations, find unsourced events)
    - Place queries (search by state/county)
    - Quality queries (missing events, logical inconsistencies)
  - Performance tips: Index usage, avoid SELECT *, LEFT JOIN
  - RMNOCASE collation requirement
  - Python helper functions
- **When to Use:** Writing efficient database queries
- **Relationships:** Uses indexes from RM11_Schema_Reference.md

---

### 9. Output Generation (2 documents)

#### RM11_Timeline_Construction.md
- **Purpose:** TimelineJS3 timeline generation
- **Size:** ~25K
- **Key Content:**
  - Complete TimelineJS3 JSON structure specification
  - Event extraction rules (include/exclude criteria)
  - Date parsing from RM11 to TimelineJS3 format
  - Date range handling (between, from, to dates)
  - Same-date event ordering by priority
  - Undated event strategies (exclude, estimate, or separate section)
  - Event grouping by life phases (Early Life, Career, Family, etc.)
  - Place formatting (short form: "City, State")
  - Media attachment from MultimediaTable
  - Citation credits for source attribution
  - Complete Python example for JSON generation
- **When to Use:** Generating interactive timelines
- **Target Format:** TimelineJS3 (https://timeline.knightlab.com)
- **Relationships:** Uses EventTable, PlaceTable, MultimediaTable, CitationTable

#### RM11_Biography_Best_Practices.md ⭐ IMPORTANT
- **Purpose:** Biography writing guidelines
- **Size:** ~28K
- **Key Content:**
  - 9-section standard biography structure:
    1. Introduction (birth, context, significance)
    2. Early Life & Family Background
    3. Education & Training
    4. Career & Accomplishments
    5. Marriage & Family
    6. Later Life & Activities
    7. Death & Burial
    8. Legacy & Significance
    9. Sources & Notes
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
- **When to Use:** Generating biographical narratives
- **Relationships:** Uses PersonTable, EventTable, NameTable, PlaceTable, SourceTable, CitationTable

---

## Document Relationships

### Primary Data Flow

```
Database Schema
    ↓
RM11_Schema_Reference.md (understand structure)
    ↓
RM11_Date_Format.md (parse dates)
RM11_FactTypes.md (categorize events)
RM11_Place_Format.md (parse places)
RM11_Name_Display_Logic.md (select names)
    ↓
RM11_BLOB_SourceFields.md (extract source data)
RM11_BLOB_CitationFields.md (extract citation data)
RM11_EventTable_Details.md (extract event details)
    ↓
RM11_Data_Quality_Rules.md (validate data)
    ↓
RM11_Query_Patterns.md (write efficient queries)
    ↓
RM11_Timeline_Construction.md (generate timelines)
RM11_Biography_Best_Practices.md (generate biographies)
```

### Cross-References by Table

**PersonTable:**
- RM11_Schema_Reference.md (structure)
- RM11_Name_Display_Logic.md (name selection)
- RM11_Relationships.md (Relate1/Relate2/Flags)
- RM11_Query_Patterns.md (person queries)

**EventTable:**
- RM11_Schema_Reference.md (structure)
- RM11_Date_Format.md (Date field)
- RM11_FactTypes.md (EventType field)
- RM11_EventTable_Details.md (Details field)
- RM11_Query_Patterns.md (event queries)
- RM11_Timeline_Construction.md (timeline generation)

**NameTable:**
- RM11_Schema_Reference.md (structure)
- RM11_Name_Display_Logic.md (IsPrimary, NameType)
- RM11_Query_Patterns.md (name searches)

**PlaceTable:**
- RM11_Schema_Reference.md (structure)
- RM11_Place_Format.md (hierarchy, parsing)
- RM11_Query_Patterns.md (place queries)

**SourceTable:**
- RM11_Schema_Reference.md (structure)
- RM11_BLOB_SourceFields.md (Fields BLOB)
- RM11_BLOB_SourceTemplateFieldDefs.md (template structures)

**CitationTable:**
- RM11_Schema_Reference.md (structure)
- RM11_BLOB_CitationFields.md (Fields BLOB)
- RM11_Query_Patterns.md (citation queries)

**FactTypeTable:**
- RM11_Schema_Reference.md (structure)
- RM11_FactTypes.md (all 65 built-in types)
- RM11_Sentence_Templates.md (Sentence field)
- RM11_EventTable_Details.md (UseValue field)

---

## Documentation Status

### Completed (18 documents) ✓

**Core Schema:**
- RM11_Schema_Reference.md
- RM11_schema_annotated.sql
- RM11_schema.json
- RM11_DataDef.yaml

**Dates:**
- RM11_Date_Format.md
- RM11_Date_Format.yaml

**BLOB Structures:**
- RM11_BLOB_SourceFields.md
- RM11_BLOB_SourceTemplateFieldDefs.md
- RM11_BLOB_CitationFields.md

**Events & Facts:**
- RM11_FactTypes.md
- RM11_Sentence_Templates.md
- RM11_EventTable_Details.md

**Places & Names:**
- RM11_Place_Format.md
- RM11_Name_Display_Logic.md
- RM11_Relationships.md

**Data Quality:**
- RM11_Data_Quality_Rules.md

**Queries & Output:**
- RM11_Query_Patterns.md
- RM11_Timeline_Construction.md
- RM11_Biography_Best_Practices.md

### Skipped (Not Genealogical)

- ConfigTable.DataRec - Application settings only
- PayloadTable.DataRec - UI metadata (saved searches, groups, prompts)

---

## Usage Scenarios

### Scenario 1: Build Data Quality Checker

**Documents Needed:**
1. RM11_Schema_Reference.md - Understand table structure
2. RM11_Data_Quality_Rules.md - Implement 24 validation rules
3. RM11_Query_Patterns.md - Write efficient validation queries
4. RM11_Date_Format.md - Validate date fields
5. RM11_Place_Format.md - Validate place hierarchies

### Scenario 2: Generate Person Biography

**Documents Needed:**
1. RM11_Query_Patterns.md - Query person, events, names, places
2. RM11_Date_Format.md - Parse event dates
3. RM11_FactTypes.md - Categorize events
4. RM11_Name_Display_Logic.md - Select appropriate names
5. RM11_EventTable_Details.md - Extract event details (occupation, death cause)
6. RM11_Place_Format.md - Format place names
7. RM11_BLOB_CitationFields.md - Extract citation page numbers
8. RM11_Biography_Best_Practices.md - Structure and write biography

### Scenario 3: Create Interactive Timeline

**Documents Needed:**
1. RM11_Query_Patterns.md - Query events for person
2. RM11_Date_Format.md - Parse dates to TimelineJS3 format
3. RM11_FactTypes.md - Categorize events for grouping
4. RM11_Place_Format.md - Format place names (short form)
5. RM11_Timeline_Construction.md - Generate TimelineJS3 JSON

### Scenario 4: Extract All Source Citations

**Documents Needed:**
1. RM11_BLOB_SourceFields.md - Parse source-level fields
2. RM11_BLOB_SourceTemplateFieldDefs.md - Understand template structures
3. RM11_BLOB_CitationFields.md - Parse citation-level fields (Page, etc.)
4. RM11_Query_Patterns.md - Query citations efficiently

### Scenario 5: Find Data Quality Issues

**Documents Needed:**
1. RM11_Data_Quality_Rules.md - Run 24 validation checks
2. RM11_Query_Patterns.md - Write efficient quality queries
3. RM11_Date_Format.md - Check date logic (death before birth, etc.)
4. RM11_FactTypes.md - Validate required events (birth, death)

---

## File Sizes Summary

| Document | Size | Priority |
|----------|------|----------|
| RM11_schema.json | ~109K | Reference |
| RM11_DataDef.yaml | ~71K | Reference |
| RM11_Schema_Reference.md | ~50K | ⭐ Essential |
| RM11_schema_annotated.sql | ~51K | Reference |
| RM11_Data_Quality_Rules.md | ~28K | ⭐ Important |
| RM11_Biography_Best_Practices.md | ~28K | ⭐ Important |
| RM11_FactTypes.md | ~26K | ⭐ Essential |
| RM11_Timeline_Construction.md | ~25K | Important |
| RM11_BLOB_SourceTemplateFieldDefs.md | ~24K | Important |
| RM11_Place_Format.md | ~21K | Important |
| RM11_BLOB_CitationFields.md | ~20K | Important |
| RM11_Sentence_Templates.md | ~18K | Reference |
| RM11_Query_Patterns.md | ~18K | ⭐ Essential |
| RM11_Name_Display_Logic.md | ~16K | Important |
| RM11_EventTable_Details.md | ~13K | Important |
| RM11_Date_Format.md | ~12K | ⭐ Critical |
| RM11_BLOB_SourceFields.md | ~11K | Important |
| RM11_Relationships.md | ~11K | Reference |
| RM11_Date_Format.yaml | ~10K | Reference |

**Total Documentation Size:** ~570K

---

## Additional Resources

### Sample Database
- **Location:** `data/Iiams.rmtree`
- **Contents:**
  - 11,571 persons
  - 29,543 events
  - 10,838 citations (95.8% with single Page field)
  - 5,082 places (65% using 4-level hierarchy)
  - 114 template-based sources using 32 different templates
- **Use For:** BLOB analysis, query testing, validation

### SQLite Extension (RMNOCASE Collation)
- **Location:** `sqlite-extension/`
- **Files:**
  - `icu.dylib` - ICU extension for macOS
  - `python_example.py` - Working Python examples
  - `how-to-use-extension.md` - Usage guide
- **Critical For:** Querying tables with COLLATE RMNOCASE fields
- **See:** RM11_Query_Patterns.md for connection examples

### Project Documentation
- **Location:** `docs/`
- **Files:**
  - `DATA_PARSING_TODO.md` - Task tracker (73 tasks)
- **Status:** Most tasks completed, documentation consolidation in progress

---

## Changelog

### 2025-01-08
- Created master index document
- Updated CLAUDE.md with all new document references
- Updated RM11_Schema_Reference.md with BLOB structures and fact type references
- All 18 documentation files completed and cross-referenced

### 2025-01-08 (Earlier)
- Completed RM11_EventTable_Details.md (Task 8)
- Completed RM11_Name_Display_Logic.md (Task 9)
- Completed RM11_Query_Patterns.md (Task 10)

### 2025-01-08 (Previous)
- Completed RM11_BLOB_SourceFields.md (Task 1.1)
- Completed RM11_BLOB_SourceTemplateFieldDefs.md (Task 1.2)
- Completed RM11_BLOB_CitationFields.md (Task 1.3)
- Completed RM11_Data_Quality_Rules.md (Tasks 3.1-3.7)
- Completed RM11_FactTypes.md (Tasks 4.1-4.5)
- Completed RM11_Place_Format.md (Tasks 5.1-5.6)
- Completed RM11_Timeline_Construction.md (Tasks 6.1-6.5)
- Completed RM11_Biography_Best_Practices.md (Tasks 7.1-7.6)

---

**End of Index**
