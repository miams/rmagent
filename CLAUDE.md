# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Information

- **Name:** rmagent - AI-Powered Genealogy Agent for RootsMagic
- **GitHub:** https://github.com/miams/rmagent
- **Clone:** `git clone git@github.com:miams/rmagent.git`
- **SSH Authentication:** `ssh-add ~/.ssh/miams-github`

## Overview

This repository contains comprehensive documentation and analysis tools for RootsMagic 11 (RM11), a genealogy software application. The goal is to enable AI agents to read and analyze RootsMagic SQLite databases to identify data quality issues, generate biographies, family histories, and timelines.

## Repository Structure

```
rmagent/
├── rmtool/                    # Main Python package (AI agent implementation)
│   ├── __init__.py
│   ├── rmlib/                # Core library (database access, parsers, queries)
│   │   ├── __init__.py
│   │   ├── database.py       # Database connection with RMNOCASE support
│   │   ├── models.py         # Pydantic data models
│   │   ├── queries.py        # 15 optimized query patterns
│   │   ├── quality.py        # 24 data quality validation rules
│   │   └── parsers/          # Parsers for dates, BLOBs, places, names
│   │       ├── __init__.py
│   │       ├── date_parser.py
│   │       ├── blob_parser.py
│   │       ├── place_parser.py
│   │       └── name_parser.py
│   ├── agent/                # AI agent (LLM integration)
│   │   ├── __init__.py
│   │   ├── llm_provider.py   # Multi-provider abstraction (Anthropic/OpenAI/Ollama)
│   │   ├── genealogy_agent.py # Main agent class
│   │   ├── prompts.py        # Prompt templates
│   │   └── tools.py          # LangChain tools
│   ├── generators/           # Output generators
│   │   ├── __init__.py
│   │   ├── biography.py      # 9-section biography generation
│   │   ├── quality_report.py # Data quality reports
│   │   ├── timeline.py       # TimelineJS3 generation
│   │   └── hugo_exporter.py  # Hugo blog post export
│   ├── cli/                  # Command-line interface
│   │   ├── __init__.py
│   │   ├── main.py           # CLI entry point
│   │   └── commands/         # CLI commands (person, bio, quality, ask, etc.)
│   │       ├── __init__.py
│   │       ├── person.py
│   │       ├── bio.py
│   │       ├── quality.py
│   │       ├── ask.py
│   │       ├── timeline.py
│   │       ├── export.py
│   │       └── search.py
│   └── config/               # Configuration
│       ├── __init__.py
│       ├── config.py
│       └── prompts/          # Prompt template files
│
├── tests/                    # Test suite
│   ├── unit/                 # Unit tests
│   └── integration/          # Integration tests
│
├── data/                     # RootsMagic database files
│   └── Iiams.rmtree         # Sample RM11 database for testing
│
├── data_reference/           # Core schema and format documentation (18 files)
│   ├── RM11_Schema_Reference.md   # Comprehensive guide (50K)
│   ├── RM11_Query_Patterns.md     # Optimized query patterns (18K)
│   ├── RM11_Date_Format.md   # Date encoding specification (12K)
│   ├── RM11_FactTypes.md     # 65 built-in fact types (26K)
│   ├── RM11_Data_Quality_Rules.md  # 24 validation rules (28K)
│   ├── RM11_Biography_Best_Practices.md  # Biography writing (28K)
│   ├── RM11_Timeline_Construction.md  # TimelineJS3 generation (25K)
│   ├── RM11_BLOB_SourceFields.md  # BLOB structure (11K)
│   ├── RM11_BLOB_SourceTemplateFieldDefs.md  # Template defs (24K)
│   ├── RM11_BLOB_CitationFields.md  # Citation BLOB (20K)
│   ├── RM11_Place_Format.md  # Place hierarchy (21K)
│   ├── RM11_Name_Display_Logic.md  # Name selection (16K)
│   ├── RM11_EventTable_Details.md  # Details field (13K)
│   ├── RM11_Sentence_Templates.md  # Template language (18K)
│   ├── RM11_Relationships.md # Relationship calculation (11K)
│   ├── RM11_DataDef.yaml     # Field definitions (71K)
│   ├── RM11_Date_Format.yaml # Date format data (10K)
│   ├── RM11_schema.json      # JSON Schema (109K)
│   ├── RM11_schema_annotated.sql  # SQL with docs (51K)
│   └── RM11_Documentation_Index.md # Master index
│
├── docs/                     # Project documentation
│   ├── AI_AGENT_TODO.md      # Implementation roadmap (38 tasks)
│   ├── DATA_PARSING_TODO.md  # Documentation tasks (73 tasks, mostly complete)
│   ├── VALIDATION_RESULTS.md # Validation test results
│   └── SETUP_COMPLETE.md     # Task 1.1 completion summary
│
├── sqlite-extension/         # SQLite RMNOCASE collation support
│   ├── icu.dylib            # ICU extension for macOS
│   ├── how-to-use-extension.md  # Usage guide
│   └── python_example.py    # Working Python examples
│
├── templates/                # Output templates (Jinja2)
├── config/                   # Config files
│   ├── .env.example         # Configuration template
│   └── prompts/             # Prompt template files
│
├── archive/                  # Source files (archived)
│   ├── RM11_schema.txt
│   └── RM11DataDef-V11_0_0-20250914.xlsx
│
├── .venv/                    # Virtual environment (created by uv)
├── pyproject.toml           # Python project configuration (uv/pip)
├── uv.lock                  # Dependency lock file
├── .gitignore               # Git ignore rules
├── README.md                # User documentation
└── CLAUDE.md                # This file
```

## Primary Documentation Files

### Schema Documentation (data_reference/)

1. **RM11_Schema_Reference.md** - START HERE for schema understanding
   - Tables organized by functional category
   - Field descriptions and relationships
   - Common query patterns
   - Index reference

2. **RM11_schema_annotated.sql** - For SQL work
   - Complete schema with inline comments
   - Field descriptions, types, constraints
   - FK/PK annotations
   - Typical values and enumerations

3. **RM11_schema.json** - For programmatic validation
   - JSON Schema format
   - Type definitions
   - Index information
   - Field metadata

4. **RM11_DataDef.yaml** - Detailed field reference
   - All 31 tables with 347 fields
   - Type information
   - Typical values
   - Comments and descriptions
   - Key/Index specifications

### Core Format Documentation

5. **RM11_Date_Format.md** - CRITICAL for date handling
   - 24-character fixed-width date encoding
   - Position-by-position specification
   - Examples for all date types
   - Parsing logic and pseudocode

6. **RM11_Relationships.md** - For genealogical relationships
   - Relate1/Relate2/Flags calculation system
   - Direct line vs collateral relationships
   - Cousin degree and removal formulas
   - In-law and half-relationship encoding

### BLOB Structure Documentation

7. **RM11_BLOB_SourceFields.md** - SourceTable.Fields extraction
   - XML structure for source metadata
   - Free-form vs template-based sources
   - Field names by template type
   - Parsing examples in Python and SQL

8. **RM11_BLOB_SourceTemplateFieldDefs.md** - Template definitions
   - 433 built-in templates with field structures
   - Field types: Text, Name, Date, Place
   - CitationField distinction (source vs citation level)
   - Double-bar notation for full/short versions

9. **RM11_BLOB_CitationFields.md** - CitationTable.Fields extraction
   - XML structure identical to SourceFields
   - 95.8% of citations have single Page field
   - Find-a-Grave citations with 10-12 fields
   - Field name variations and patterns

### Event and Fact Documentation

10. **RM11_FactTypes.md** - Event type reference
    - All 65 built-in fact types enumerated
    - 11 functional categories (Vital, Religious, Military, etc.)
    - Person vs Family distinctions
    - GEDCOM tag mappings
    - Usage frequency statistics

11. **RM11_Sentence_Templates.md** - Template language (REFERENCE ONLY)
    - Variable substitution syntax ([person], [Date], [Place])
    - Modifiers for formatting (:first, :Age, :Plain)
    - Conditional logic (<?...>)
    - Choice expressions (<male|female>)
    - NOTE: AI agents generate text natively, don't need to execute templates

### Place and Geography

12. **RM11_Place_Format.md** - Place name structure
    - Standard format: "City, County, State, Country"
    - 4-level hierarchy (65% of places)
    - Name vs Normalized vs Reverse fields
    - Master/Detail relationships (8% detail places)
    - Coordinate system (85% have lat/long)
    - Parsing and formatting examples

### Data Quality and Validation

13. **RM11_Data_Quality_Rules.md** - Validation rules
    - 24 specific validation rules across 6 categories
    - Required field combinations
    - Logical consistency checks (death after birth, etc.)
    - Referential integrity rules
    - Source documentation quality metrics
    - SQL queries for each validation check

### Output Generation

14. **RM11_Timeline_Construction.md** - Timeline generation
    - TimelineJS3 JSON format specification
    - Event extraction and filtering rules
    - Date parsing from RM11 to TimelineJS3
    - Date range handling (between, from, to)
    - Event grouping by life phases
    - Complete Python generation example

15. **RM11_Biography_Best_Practices.md** - Biography writing
    - 9-section standard structure (Introduction → Death & Legacy)
    - Fact inclusion priorities (Essential → Context)
    - Uncertainty handling (6 certainty levels)
    - Privacy rules (IsPrivate, 110-year rule)
    - Source citation styles (Footnote, Parenthetical, Narrative)
    - Tone guidelines and common pitfalls
    - Quality checklist

### Additional Reference Documentation

16. **RM11_EventTable_Details.md** - EventTable.Details field
    - Plain text field (no XML structure)
    - 21.4% of events have Details content
    - Usage patterns by event type (SSN, Occupation, Death cause)
    - Relationship to FactTypeTable.UseValue flag
    - Common content patterns and validation

17. **RM11_Name_Display_Logic.md** - Name selection rules
    - IsPrimary flag (one per person required)
    - NameType values (0=Standard, 5=Married, 7=Maiden)
    - Context-aware selection (maiden name pre-marriage)
    - Name component assembly (Prefix + Given + Surname + Suffix)
    - Multiple name scenarios and display recommendations

18. **RM11_Query_Patterns.md** - Optimized SQL queries
    - 15 common query patterns (person, event, family, ancestor, descendant)
    - Index usage optimization
    - Recursive CTEs for relationship traversal
    - Performance tips and EXPLAIN guidance
    - Python helper functions with RMNOCASE support

## Database Architecture

### Core Entity Tables

- **PersonTable** - Central table storing individuals with unique IDs, sex, privacy flags, colors for visual organization, and relationship pointers
- **FamilyTable** - Represents family units linking fathers, mothers, and children with proof standards and custom labels
- **ChildTable** - Many-to-many relationship between persons and families, including relationship types and proof standards
- **NameTable** - Stores multiple names per person (primary, alternate, married names) with Metaphone encoding (SurnameMP, GivenMP) for phonetic matching

### Events and Facts

- **EventTable** - Life events (births, deaths, marriages, etc.) linked to persons or families with encoded dates
- **FactTypeTable** - Defines custom fact/event types with sentence templates and GEDCOM mappings
- **WitnessTable** - Links persons as witnesses to events with roles
- **RoleTable** - Defines witness/participant roles in events

### Sources and Citations

- **SourceTable** - Source documents with template-based field definitions (BLOB storage)
- **SourceTemplateTable** - Reusable templates defining source types with formatted output patterns
- **CitationTable** - Specific citations of sources with formatted footnotes and bibliographies
- **CitationLinkTable** - Many-to-many linking citations to various owner types (persons, families, events)

### Places and Addresses

- **PlaceTable** - Hierarchical place names with normalization, coordinates, and reverse-order indexing for searching
- **AddressTable** - Physical addresses for repositories and contacts
- **AddressLinkTable** - Links addresses to various entities

### Multimedia

- **MultimediaTable** - Media files with paths, thumbnails (BLOB), captions, and dates
- **MediaLinkTable** - Associates media with persons, families, events, sources with cropping rectangles and ordering

### Research Management

- **TaskTable** - Research tasks and to-dos with status, priority, and dates
- **TaskLinkTable** - Associates tasks with persons, families, or other entities
- **GroupTable** - Named sets for reports and filtering
- **TagTable** - Custom tags for categorization

### External Synchronization

- **AncestryTable** - Links to Ancestry.com records with sync status
- **FamilySearchTable** - Links to FamilySearch records with sync status

### DNA and Health

- **DNATable** - DNA match data including shared centimorgans, segments, and relationship predictions
- **HealthTable** - Medical conditions and health information for persons

### Supporting Tables

- **FANTable/FANTypeTable** - Friends, Associates, and Neighbors relationships
- **URLTable** - Web links associated with various entities
- **ExclusionTable** - Records to exclude from specific operations
- **ConfigTable** - Application configuration (BLOB storage)
- **PayloadTable** - Generic BLOB storage for various data types (saved searches, groups)

## Key Schema Patterns

### OwnerType/OwnerID Pattern
Many linking tables use `OwnerType` (integer enum) and `OwnerID` to create polymorphic associations with different entity types.

**Common OwnerType values:**
- `0` = Person
- `1` = Family
- `2` = Event
- `3` = Source
- `4` = Citation
- `5` = Place
- `6` = Task
- `7` = Name
- `14` = Place Details
- `19` = Association (FAN)

### BLOB Fields
Several tables use BLOB columns for structured XML data:
- **SourceTable.Fields** - Template field values (see RM11_BLOB_SourceFields.md)
- **SourceTemplateTable.FieldDefs** - Field definitions (see RM11_BLOB_SourceTemplateFieldDefs.md)
- **CitationTable.Fields** - Citation field values (see RM11_BLOB_CitationFields.md)
- **ConfigTable.DataRec** - Application configuration (not genealogical - skipped)
- **PayloadTable.DataRec** - UI metadata: saved searches, groups, prompts (not genealogical - skipped)

All BLOBs are UTF-8 encoded XML with BOM (EFBBBF).

### Collation
Text fields used for searching/sorting use `COLLATE RMNOCASE` for case-insensitive comparisons.

### Date Handling
Dates use a two-part system:
- **Date (TEXT)** - 24-character encoded format supporting ranges, qualifiers, BC/AD (see RM11_Date_Format.md)
- **SortDate (BIGINT)** - Sortable integer representation for queries (18-19 digits)

Date encoding supports:
- Complete and partial dates
- Date ranges (between, from/to)
- Directional modifiers (before, after, etc.)
- Qualifiers (about, estimated, calculated)
- Certainty levels (probably, possibly, etc.)
- BC/AD dates, double dates, Quaker dates

### Modification Tracking
All tables include `UTCModDate FLOAT` (Julian day format) for sync and change tracking.

### Privacy and Proof
Many tables include:
- **IsPrivate INTEGER** - Boolean flag for privacy (0=public, 1=private)
- **Proof INTEGER** - Evidence quality rating (0=blank, 1=proven, 2=disproven, 3=disputed)

## Index Strategy

The schema includes extensive indexes for:
- **Name searching** - Exact (idxSurname, idxGiven) and Metaphone phonetic (idxSurnameMP, idxGivenMP)
- **Ownership relationships** - OwnerID indexes on all linking tables
- **Date-based queries** - idxOwnerDate for chronological sorting
- **Cross-references** - Foreign key indexes throughout

## Working with This Repository

### For AI Agent Development

**Essential Reading:**
1. **RM11_Schema_Reference.md** - Understand database structure
2. **RM11_Date_Format.md** - Parse and format dates
3. **RM11_FactTypes.md** - Categorize events
4. **RM11_Place_Format.md** - Parse place hierarchies
5. **RM11_Query_Patterns.md** - Optimized SQL patterns

**Data Extraction:**
6. **RM11_BLOB_SourceFields.md** - Extract source metadata
7. **RM11_BLOB_SourceTemplateFieldDefs.md** - Understand template structures
8. **RM11_BLOB_CitationFields.md** - Extract citation details
9. **RM11_EventTable_Details.md** - Extract event details (SSN, occupation, etc.)
10. **RM11_Name_Display_Logic.md** - Select appropriate names by context

**Data Quality:**
11. **RM11_Data_Quality_Rules.md** - Validate data integrity (24 rules)
12. **RM11_Relationships.md** - Calculate genealogical relationships

**Output Generation:**
13. **RM11_Timeline_Construction.md** - Generate TimelineJS3 timelines
14. **RM11_Biography_Best_Practices.md** - Write quality biographies

**Reference:**
15. **RM11_DataDef.yaml** - Field enumerations and constraints
16. **data/Iiams.rmtree** - Real-world example database
17. **sqlite-extension/python_example.py** - RMNOCASE collation support

### For Query Writing

1. **Schema**: Use `RM11_schema_annotated.sql` as reference
2. **Patterns**: See "Common Query Patterns" section in `RM11_Schema_Reference.md`
3. **Validation**: Use `RM11_schema.json` for type checking

## AI Agent Implementation (rmtool/)

**Status:** 🚧 In Development - Working Prototype Phase

### Project Setup

The `rmtool/` package uses **[uv](https://github.com/astral-sh/uv)** for fast Python package management:

```bash
# Install dependencies (first time setup)
uv sync

# Install with dev dependencies
uv sync --extra dev

# Run any command in the virtual environment
uv run <command>

# Example: Run CLI
uv run rmtool --help
```

### Development Workflow

```bash
# Format code
uv run black .

# Lint code
uv run ruff check .

# Type check
uv run mypy rmtool/

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=rmtool --cov-report=html
```

### Implementation Roadmap

See `docs/AI_AGENT_TODO.md` for complete task list (38 tasks across 7 phases):

**Phase 1: Foundation** (Tasks 1.1-1.9) ✅ COMPLETE
- ✅ Task 1.1: Project Setup (uv, dependencies, configuration)
- ✅ Task 1.2: Database Connection Module (RMDatabase with RMNOCASE)
- ✅ Task 1.3-1.9: Data models, parsers, queries, quality validation

**Phase 2: AI Integration** (Tasks 2.1-2.5) ✅ COMPLETE
- ✅ Multi-LLM support (Anthropic Claude, OpenAI GPT-4, Ollama)
- ✅ Configuration management (`config/.env`, Pydantic settings)
- ✅ Prompt templates (biography, quality, Q&A, timeline)
- ✅ Agent core (GenealogyAgent with context builders)
- ✅ LangChain tools (query, events, validation, search)

**Phase 3: Output Generators** (Tasks 3.1-3.4)
- Biography generation (9-section structure)
- Data quality reports
- Timeline generation (TimelineJS3)
- Hugo blog post export

**Phase 4: CLI Interface** (Tasks 4.1-4.8)
- 8 CLI commands: person, bio, quality, ask, timeline, export, search

**Milestones:**
- ✅ **Milestone 1: Working Prototype** - COMPLETE (2025-10-09)
- 🎯 **Milestone 2: MVP** - In Progress (quality analysis, bio, Q&A, timeline, Hugo)
- 🎯 **Milestone 3: Production Polish** - Performance, advanced features, enhancements

### Current Project Status

**Implementation Progress (as of 2025-10-09):**

**✅ Phase 1: Foundation - COMPLETE (9/9 tasks)**
- ✅ Task 1.1: Project Setup (uv, dependencies, configuration)
- ✅ Task 1.2: Database Connection Module (RMDatabase with RMNOCASE)
- ✅ Task 1.3: Data Models (Pydantic models for all core entities)
- ✅ Task 1.4: Date Parser (24-character RM11 format, 44 tests, 93% coverage)
- ✅ Task 1.5: BLOB Parsers (XML parsing for sources/citations/templates, 24 tests, 91% coverage)
- ✅ Task 1.6: Place Parser (hierarchy parsing/formatting, 55 tests, 99% coverage)
- ✅ Task 1.7: Name Parser (primary/alternate/context-aware, 34 tests, 96% coverage)
- ✅ Task 1.8: Query Service (15 optimized patterns, 16 tests, 91% coverage)
- ✅ Task 1.9: Data Quality Validator (24 validation rules across 6 categories)

**✅ Phase 2: AI Integration - COMPLETE (5/5 tasks)**
- ✅ Task 2.1: LLM Provider Abstraction (Anthropic/OpenAI/Ollama with retry/pricing)
- ✅ Task 2.2: Configuration Management (`config/.env`, Pydantic settings, provider builder)
- ✅ Task 2.3: Prompt Templates (biography, quality, Q&A, timeline with versioning)
- ✅ Task 2.4: Agent Core (GenealogyAgent with context builders)
- ✅ Task 2.5: LangChain Tools (query, events, validation, search)

**📊 Test Coverage:**
- Total: 229 unit tests
- Parsers: 157 tests (date, BLOB, place, name)
- Query service: 16 tests
- Agent/Config: 56 tests
- Coverage: 91-99% across modules

**⏭️ Next Phase:**
- Phase 3: Output Generators (biography, quality report, timeline, Hugo export)

**Completed Documentation (as of 2025-01-08):**

**Schema & Structure:**
- ✓ Core schema documentation (SQL, JSON, Markdown, YAML)
- ✓ Date format specification (24-character encoding)
- ✓ Relationship calculation documentation
- ✓ Place name format and hierarchy

**BLOB Field Structures:**
- ✓ SourceTable.Fields - Source metadata (Task 1.1)
- ✓ SourceTemplateTable.FieldDefs - Template definitions (Task 1.2)
- ✓ CitationTable.Fields - Citation details (Task 1.3)
- ⊗ ConfigTable.DataRec - SKIPPED (application settings only)
- ⊗ PayloadTable.DataRec - SKIPPED (UI metadata only)

**Event & Fact Documentation:**
- ✓ FactType enumeration - All 65 built-in types (Tasks 4.1-4.5)
- ✓ Sentence template language - Reference only (Task 2.1)

**Data Quality:**
- ✓ Validation rules - 24 rules across 6 categories (Tasks 3.1-3.7)

**Output Generation:**
- ✓ Timeline construction - TimelineJS3 format (Tasks 6.1-6.5)
- ✓ Biography best practices - Writing guidelines (Tasks 7.1-7.6)

**Additional Documentation:**
- ✓ EventTable.Details - Plain text field patterns (Task 8)
- ✓ Name display logic - Context-aware name selection (Task 9)
- ✓ Query patterns - 15 optimized query templates (Task 10)

**Remaining Work:**
See `docs/DATA_PARSING_TODO.md` for status. Documentation consolidation tasks:
- Task 11: Update documentation cross-references (in progress)
- Task 12: Validation and testing of all examples

### Sample Database

The `data/Iiams.rmtree` database contains:
- Real genealogical data (11,571 persons, 29,543 events)
- 114 template-based sources using 32 different templates
- Examples of all major table types
- 10,838 citations (95.8% with single Page field)
- 5,082 places (65% using 4-level hierarchy)
- Use for BLOB analysis, query testing, and validation

### SQLite Extension (RMNOCASE Collation)

**Critical for database access:**
- RootsMagic uses proprietary RMNOCASE collation
- ICU extension provides compatibility
- `sqlite-extension/icu.dylib` - macOS extension
- `sqlite-extension/python_example.py` - Working Python examples
- `sqlite-extension/how-to-use-extension.md` - Usage guide

**Python Usage:**
```python
import sqlite3

conn = sqlite3.connect('data/Iiams.rmtree')
conn.enable_load_extension(True)
conn.load_extension('./sqlite-extension/icu.dylib')
conn.execute("SELECT icu_load_collation('en_US@colStrength=primary;caseLevel=off;normalization=on','RMNOCASE')")
conn.enable_load_extension(False)

# Now you can query the database without collation errors
```

## Common Tasks

### Extract Person Information
```sql
SELECT p.PersonID, n.Surname, n.Given, n.BirthYear, n.DeathYear
FROM PersonTable p
JOIN NameTable n ON p.PersonID = n.OwnerID
WHERE n.IsPrimary = 1;
```

### Get Events for Person
```sql
SELECT ft.Name, e.Date, e.Details
FROM EventTable e
JOIN FactTypeTable ft ON e.EventType = ft.FactTypeID
WHERE e.OwnerType = 0 AND e.OwnerID = ?
ORDER BY e.SortDate;
```

### Extract Citation from BLOB
```python
import xml.etree.ElementTree as ET

def parse_source_fields(blob_data):
    xml_text = blob_data.decode('utf-8-sig')
    root = ET.fromstring(xml_text)
    fields = {}
    for field in root.findall('.//Field'):
        name = field.find('Name').text
        value = field.find('Value').text or ''
        fields[name] = value
    return fields
```

### Parse Date Field
See RM11_Date_Format.md for complete specification. Basic structure:
- Position 1: Date type (D=standard, Q=Quaker, T=text, .=null)
- Position 2: Modifier (B=before, A=after, R=between, etc.)
- Position 3: Era (+/-)
- Positions 4-7: Year (yyyy)
- Positions 8-9: Month (mm)
- Positions 10-11: Day (dd)
- Position 13: Qualifier (A=about, E=estimated, etc.)

## Related Documentation

- **RootsMagic Official Documentation**: https://www.rootsmagic.com/
- **SQLite Documentation**: https://www.sqlite.org/docs.html
- **GEDCOM Standard**: For understanding FactTypeTable.GedcomTag mappings

## Notes for AI Agents

**Database Access:**
- **RMNOCASE collation required** - Use ICU extension (see sqlite-extension/)
- **Connection template** in `sqlite-extension/python_example.py`

**Data Extraction:**
- **Always decode BLOBs** with `utf-8-sig` to handle BOM (EF BB BF)
- **Date fields** - Parse with RM11_Date_Format.md (24-character encoding)
- **SortDate = 9223372036854775807** - Unknown/missing date marker
- **Place names** - Parse comma-delimited hierarchy, use Normalized when available
- **Templates** - TemplateID=0 is free-form, >0 uses template structure

**Relationships:**
- **OwnerType/OwnerID** is polymorphic - check OwnerType before joining
  - 0=Person, 1=Family, 2=Event, 3=Source, 4=Citation, 5=Place, etc.
- **Relate1/Relate2/Flags** - See RM11_Relationships.md for calculations

**Data Quality:**
- **IsPrivate flags** - Respect privacy (0=public, 1=private)
- **Proof levels** - 0=Blank, 1=Proven, 2=Disproven, 3=Disputed
- **Validation rules** - 24 rules in RM11_Data_Quality_Rules.md

**Content Generation:**
- **Sentence templates** - AI generates text natively, templates for reference only
- **Timeline format** - TimelineJS3 JSON (see RM11_Timeline_Construction.md)
- **Biography structure** - 9 sections (see RM11_Biography_Best_Practices.md)
- **Uncertainty qualifiers** - "likely", "probably", "about", "circa", etc.

## Git Workflow

### Repository Setup

The project is hosted on GitHub at **miams/rmagent**:

```bash
# Clone repository (requires SSH key)
git clone git@github.com:miams/rmagent.git
cd rmagent

# Configure SSH authentication
ssh-add ~/.ssh/miams-github

# Verify connection
ssh -T git@github.com
```

### Branch Strategy

- **main** - Stable, production-ready code
- **develop** - Integration branch for completed features
- **feature/** - Feature branches for new development

### Common Git Operations

```bash
# Check status
git status

# Add changes
git add .

# Commit with descriptive message
git commit -m "feat: implement place parser with 55 tests"

# Push to remote
git push origin main

# Pull latest changes
git pull origin main

# Create feature branch
git checkout -b feature/data-quality-validator

# Merge feature to main
git checkout main
git merge feature/data-quality-validator
```

### Commit Message Conventions

Use conventional commit format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

## Future Development

See `docs/AI_AGENT_TODO.md` for implementation roadmap:
- **Phase 1:** Foundation (Tasks 1.1-1.9) ✅ COMPLETE
- **Phase 2:** AI Integration (Tasks 2.1-2.5) ✅ COMPLETE
- **Phase 3:** Output Generators (Tasks 3.1-3.4) ⏭️ NEXT
- **Phase 4:** CLI Interface (Tasks 4.1-4.8)
- **Phase 5:** Testing & Quality (Tasks 5.1-5.4)
- **Phase 6:** Documentation (Tasks 6.1-6.3)
- **Phase 7:** Production Polish (Tasks 7.1-7.5)

See `docs/DATA_PARSING_TODO.md` for documentation tasks (mostly complete)
