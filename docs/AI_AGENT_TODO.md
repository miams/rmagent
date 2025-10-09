# RootsMagic AI Genealogy Agent - Implementation TODO

**Created:** 2025-01-08
**Target:** Python-based AI agent for RootsMagic database analysis, biography generation, and genealogical research
**Status:** Planning Phase → Ready to Build

---

## Project Overview

**Goal:** Build a Python CLI tool that leverages RootsMagic databases with AI (Anthropic/OpenAI/Ollama) to:
1. Analyze data quality and generate reports
2. Generate biographical narratives
3. Answer questions about people and families
4. Create interactive timelines
5. Export content for Hugo blog posts

**LLM Support:** Multi-provider (Anthropic Claude, OpenAI GPT-4, Ollama local models)
**Interface:** Command-line interface (CLI)
**Deployment:** Local machine only (for now)
**Testing:** Comprehensive test suite (>80% coverage target)

---

## Milestones

### 🎯 Milestone 1: Working Prototype
**Goal:** Demonstrate core functionality end-to-end
**Definition:** Query 1 person, generate basic biography, identify 1 data quality issue
**Target:** Foundation for all future features
**Deliverables:**
- Database connection with RMNOCASE support
- Basic person/event queries working
- Simple biography generation with AI
- 1-2 data quality checks running
- CLI commands: `person`, `bio`, `check`

### 🎯 Milestone 2: MVP (Minimum Viable Product)
**Goal:** All 5 core features working in basic form
**Definition:** Command-line tool handling common workflows end-to-end
**Deliverables:**
- Complete data quality analysis with all 24 rules
- Full biography generation (9-section structure)
- Interactive Q&A about database
- Timeline generation (TimelineJS3 format)
- Hugo blog post export
- CLI commands: `quality`, `bio`, `ask`, `timeline`, `export`
- Comprehensive test suite
- Documentation for end users

### 🎯 Milestone 3: Production Polish
**Goal:** Refinement, optimization, and user experience
**Deliverables:**
- Performance optimization
- Enhanced error handling
- Progress indicators for long operations
- Configuration management
- Batch processing capabilities
- Advanced features (relationship graphs, source analysis)

---

## Phase 1: Foundation (Working Prototype - Core Library)

**Goal:** Build the foundational Python library for database access and parsing

### Task 1.1: Project Setup ✅ COMPLETE
- [✓] Documentation complete (18 files, validated)
- [✓] Sample database available (data/Iiams.rmtree)
- [✓] SQLite extension verified (icu.dylib)
- [✓] Create project structure:
  ```
  rmlib/               # Core library
  agent/               # AI agent
  generators/          # Output generators
  cli/                 # Command-line interface
  tests/               # Test suite
  config/              # Configuration
  docs/                # User documentation
  ```
- [✓] Set up Python project with UV (pyproject.toml, uv.lock)
- [✓] Initialize git repository with .gitignore
- [✓] Set up virtual environment (.venv/ with UV)

**Dependencies:**
```
# Core
sqlite3 (built-in)
# AI
anthropic
openai
ollama-python
langchain
langchain-anthropic
langchain-openai
# Utilities
pydantic
python-dotenv
click (CLI)
rich (terminal formatting)
jinja2 (templates)
pyyaml
# Testing
pytest
pytest-cov
pytest-mock
# Dev
black
ruff
mypy
```

---

### Task 1.2: Database Connection Module ✅ COMPLETE
**File:** `rmtool/rmlib/database.py`
**Reference:** sqlite-extension/python_example.py, RM11_Query_Patterns.md
**Completed:** 2025-10-09

- [✓] Implement `RMDatabase` class with context manager
- [✓] RMNOCASE collation loader
- [✓] Error handling for missing database/extension
- [✓] Logging support
- [✓] Unit tests (test_database.py) - 17 tests, 97% coverage

**API:**
```python
with RMDatabase('data/Iiams.rmtree') as db:
    results = db.query("SELECT * FROM PersonTable")
    person = db.query_one("SELECT * FROM PersonTable WHERE PersonID = ?", (1,))
    count = db.query_value("SELECT COUNT(*) FROM PersonTable")
```

**Features:**
- Context manager protocol (`__enter__`/`__exit__`)
- Automatic RMNOCASE collation loading via ICU extension
- Query helper methods: `query()`, `query_one()`, `query_value()`
- Error handling with custom exceptions
- sqlite3.Row factory for dict-like access
- Transaction support (`commit()`, `rollback()`)
- Comprehensive logging

**Note:** Connection pooling deferred - not needed for single-threaded CLI tool

---

### Task 1.3: Data Models ✅ COMPLETE
**File:** `rmtool/rmlib/models.py`
**Reference:** RM11_Schema_Reference.md, RM11_DataDef.yaml
**Completed:** 2025-10-09

- [✓] Define Pydantic models for:
  - `Person` (PersonID, sex, living, etc.)
  - `Name` (surname, given, prefix, suffix, nickname, IsPrimary, NameType)
  - `Event` (EventID, EventType, date, place, details, proof)
  - `Place` (PlaceID, name, normalized, coordinates, PlaceType)
  - `Source` (SourceID, name, TemplateID, fields)
  - `Citation` (CitationID, CitationName, fields)
  - `Family` (FamilyID, FatherID, MotherID)
  - `FactType` (FactTypeID, name, UseValue, GEDCOM tag)
- [✓] Type hints throughout
- [✓] Validation rules (e.g., Sex in [0,1,2])
- [✓] Unit tests (test_models.py) - 34 tests, 95% coverage

**Features:**
- **Enumerations:** Sex, NameType, OwnerType, PlaceType, ProofLevel, ParentLabel, MotherLabel
- **Field aliases:** Support both Python names (snake_case) and database names (PascalCase)
- **Type validation:** Pydantic validators for all fields with constraints
- **Boolean conversion:** Automatic conversion of integer flags (0/1) to boolean
- **Custom validators:** Sex validation, boolean field conversion
- **Helper properties:** `Name.full_name`, `Place.latitude_decimal`, `Place.longitude_decimal`
- **BLOB support:** `bytes` fields for XML data in Source.fields and Citation.fields

**Models created:**
1. `Person` - 17 fields with color coding, relationships, privacy
2. `Name` - 20 fields with Metaphone encodings, name types
3. `Event` - 16 fields with dates, places, proof levels
4. `Place` - 13 fields with coordinates, normalization
5. `Source` - 8 fields with template support, BLOB fields
6. `Citation` - 10 fields with footnotes, bibliography
7. `Family` - 15 fields with parent labels, proof levels
8. `FactType` - 11 fields with GEDCOM tags, sentence templates

---

### Task 1.4: Date Parser ✅ COMPLETE
**File:** `rmtool/rmlib/parsers/date_parser.py`
**Reference:** RM11_Date_Format.md
**Completed:** 2025-10-09

- [✓] Parse 24-character RM11 date format
- [✓] Extract components: type, modifier, era, year, month, day, qualifier
- [✓] Handle date ranges (between, from, to)
- [✓] Handle qualifiers (about, estimated, calculated, etc.)
- [✓] Handle partial dates (year only, month/year)
- [✓] Format dates for display
- [✓] Convert to Python datetime (where possible)
- [✓] Handle unknown dates (SortDate = 9223372036854775807)
- [✓] Unit tests with edge cases (test_date_parser.py) - 44 tests, 93% coverage

**API:**
```python
date = parse_rm_date("D.+18960302..+00000000..")
# Returns: RMDate(year=1896, month=3, day=2, ...)
date.format_display()  # "2 Mar 1896"
date.to_datetime()     # datetime(1896, 3, 2)
```

**Features:**
- **RMDate dataclass** with all date components
- **3 enumerations:** DateType, DateModifier, DateQualifier
- **Complete date parsing:** Standard, Quaker, text, null dates
- **Modifiers:** Before, after, between, from/to, or, range, etc.
- **Qualifiers:** About, circa, estimated, calculated, certainty levels
- **BC/AD support:** Proper handling of BC dates
- **Double dates:** Calendar transition dates (1583/84)
- **Range support:** Between...and, From...to, Or
- **Partial dates:** Year only, month/year, day/month
- **Display formatting:** Human-readable with proper qualifiers
- **Datetime conversion:** Complete dates → Python datetime
- **Helper methods:** is_null, is_range, is_partial properties
- **Unknown date detection:** is_unknown_date() function

**Test coverage:**
- 44 comprehensive tests across 10 test classes
- Basic dates (null, complete, partial)
- Modifiers (before, after, between, etc.)
- Ranges (between/and, from/to, or)
- Qualifiers (about, estimated, probably, etc.)
- BC dates and ranges
- Double dates (calendar transitions)
- Text and Quaker dates
- Datetime conversion
- Edge cases and error handling
- Real-world examples (births, deaths, marriages, census)

---

### Task 1.5: BLOB Parsers ✅ COMPLETE
**File:** `rmtool/rmlib/parsers/blob_parser.py`
**Reference:** RM11_BLOB_SourceFields.md, RM11_BLOB_CitationFields.md, RM11_BLOB_SourceTemplateFieldDefs.md
**Completed:** 2025-10-09

- [✓] Parse SourceTable.Fields (UTF-8 with BOM)
- [✓] Parse CitationTable.Fields (UTF-8 with/without BOM)
- [✓] Parse SourceTemplateTable.FieldDefs
- [✓] Handle malformed XML gracefully
- [✓] Extract field name/value pairs
- [✓] Extract template field definitions
- [✓] Unit tests (test_blob_parser.py) - 24 tests, 91% coverage

**API:**
```python
# Parse source fields
fields = parse_source_fields(blob_data)
# Returns: {'Author': 'Smith, John', 'Title': 'Census Records', ...}

# Parse citation fields
fields = parse_citation_fields(blob_data)
# Returns: {'Page': '123'}

# Parse template definitions
template_fields = parse_template_field_defs(blob_data)
# Returns: [TemplateField(name='Author', type='Name', ...), ...]
```

**Features:**
- **3 parsing functions:**
  - `parse_source_fields()` - SourceTable.Fields BLOB
  - `parse_citation_fields()` - CitationTable.Fields BLOB
  - `parse_template_field_defs()` - SourceTemplateTable.FieldDefs BLOB
- **TemplateField dataclass** for template definitions
- **BLOBParseError exception** for error handling
- **UTF-8 BOM handling** - Automatic detection and decoding
- **HTML entity decoding** - Automatic via XML parser
- **Malformed XML handling** - Graceful error messages
- **Helper functions:**
  - `has_blob_data()` - Check if BLOB exists
  - `is_freeform_source()` - Detect free-form sources
  - `get_citation_level_fields()` - Extract citation fields from template
  - `get_source_level_fields()` - Extract source fields from template

**Test coverage:**
- 24 comprehensive tests across 5 test classes
- Source fields parsing (free-form, template, BOM, entities, errors)
- Citation fields parsing (Page, Find-a-Grave, etc.)
- Template definitions (field types, hints, citation_field flag)
- Helper functions
- Real-world examples (books, census, online databases)

---

### Task 1.6: Place Parser ✅ COMPLETE
**File:** `rmlib/parsers/place_parser.py`
**Reference:** RM11_Place_Format.md

- [✓] Parse comma-delimited place hierarchy
- [✓] Extract levels (City, County, State, Country)
- [✓] Use Normalized when available
- [✓] Handle PlaceType (0=Place, 1=Temple, 2=Detail)
- [✓] Format for display (short, medium, full)
- [✓] Master/Detail relationship handling
- [✓] Unit tests (test_place_parser.py)

**Example API:**
```python
parsed = parse_place("Baltimore, Baltimore, Maryland, United States")
# Returns: {'city': 'Baltimore', 'county': 'Baltimore', 'state': 'Maryland', 'country': 'United States'}
```

---

### Task 1.7: Name Parser ✅ COMPLETE
**File:** `rmlib/parsers/name_parser.py`
**Reference:** RM11_Name_Display_Logic.md

- [✓] Select primary name (IsPrimary=1)
- [✓] Get all alternate names
- [✓] Context-aware name selection (maiden vs married)
- [✓] Format full name (Prefix + Given + Surname + Suffix)
- [✓] Handle nickname display
- [✓] Validate: exactly one primary name per person
- [✓] Unit tests (test_name_parser.py)

**Example API:**
```python
name = get_primary_name(person_id, db)
full = format_full_name(name, include_nickname=True)
# Returns: "Dr. John William Smith Jr. (\"Jack\")"
```

---

### Task 1.8: Query Service ✅ COMPLETE
**File:** `rmlib/queries.py`
**Reference:** RM11_Query_Patterns.md

- [✓] Implement `QueryService` façade with parameterized helpers
- [✓] Cover Patterns 1-15 (person, family, ancestor, place, quality queries)
- [✓] Recursive CTE helpers honor configurable generation limits
- [✓] Optional RMNOCASE-aware search helpers (exact + metaphone)
- [✓] Unit tests using `data/Iiams.rmtree` (`tests/unit/test_queries.py`)
- [✓] Vital event constants shared for downstream generators

**Example API:**
```python
with RMDatabase('data/Iiams.rmtree') as db:
    queries = QueryService(db)
    person = queries.get_person_with_primary_name(1)
    timeline = queries.get_person_events(1)
    ancestors = queries.get_direct_ancestors(1, generations=5)
```

---

### Task 1.9: Data Quality Validator ✅ COMPLETE
**File:** `rmlib/quality.py`
**Reference:** RM11_Data_Quality_Rules.md

Implement all 24 validation rules across 6 categories:

**Category 1: Required Field Combinations (5 rules)**
- [✓] Rule 1.1: Birth event must have date or place
- [✓] Rule 1.2: Death event must have date or place
- [✓] Rule 1.3: Marriage event must have date or place
- [✓] Rule 1.4: Every person must have primary name
- [✓] Rule 1.5: Every citation must have source reference

**Category 2: Logical Consistency (6 rules)**
- [✓] Rule 2.1: Death date after birth date
- [✓] Rule 2.2: Marriage date after birth dates of both spouses
- [✓] Rule 2.3: Parent birth before child birth (minimum 13 years)
- [✓] Rule 2.4: Parent death after child birth
- [✓] Rule 2.5: Child events between parent marriage and death
- [✓] Rule 2.6: Living flag consistency with death event

**Category 3: Referential Integrity (4 rules)**
- [✓] Rule 3.1: All PersonTable.ParentID → FamilyTable.FamilyID
- [✓] Rule 3.2: All EventTable.PlaceID → PlaceTable.PlaceID
- [✓] Rule 3.3: All CitationTable.SourceID → SourceTable.SourceID
- [✓] Rule 3.4: All MediaLinkTable.MediaID → MultimediaTable.MediaID

**Category 4: Source Documentation Quality (3 rules)**
- [✓] Rule 4.1: Birth events should have citations
- [✓] Rule 4.2: Death events should have citations
- [✓] Rule 4.3: Marriage events should have citations

**Category 5: Date Validity (3 rules)**
- [✓] Rule 5.1: Date format validation (24-character structure)
- [✓] Rule 5.2: Date component ranges (month 1-12, day 1-31)
- [✓] Rule 5.3: SortDate consistency with Date

**Category 6: Value Range Constraints (4 rules)**
- [✓] Rule 6.1: PersonTable.Sex in [0,1,2]
- [✓] Rule 6.2: EventTable.Proof in [0,1,2,3]
- [✓] Rule 6.3: NameTable.IsPrimary in [0,1]
- [✓] Rule 6.4: PlaceTable.PlaceType in [0,1,2]

**Additional:**
- [✓] Generate quality report with severity levels
- [✓] Summary statistics (total issues, by category, by severity)
- [✓] Unit tests (test_quality.py)

**Example API:**
```python
validator = DataQualityValidator(db)
report = validator.run_all_checks()
# Returns: QualityReport with issues categorized by severity
```

---

### 🎯 Milestone 1 Checkpoint: Working Prototype

**Definition:** Query 1 person, generate basic biography, identify 1 data quality issue

**Deliverables:**
- [ ] Database connection working with RMNOCASE
- [ ] Person query returns complete data (name, events, places)
- [ ] Date parsing works for all formats
- [ ] At least 1 data quality check runs
- [ ] Basic biography text generated (even if not AI-enhanced yet)
- [ ] All unit tests passing
- [ ] Code coverage >80%

**Test Command:**
```bash
# Should work at this checkpoint
python -m rmlib.prototype --person-id 1 --check-quality
```

**Acceptance Criteria:**
✓ Can query person by ID and display all events
✓ Dates display in human-readable format
✓ At least 1 quality issue detected (if exists)
✓ No crashes, graceful error handling
✓ Tests pass with >80% coverage

---

## Phase 2: AI Integration (Working Prototype - AI Layer)

**Goal:** Add AI capabilities for analysis and generation

### Task 2.1: LLM Provider Abstraction
**File:** `agent/llm_provider.py`

- [ ] Abstract base class `LLMProvider`
- [ ] `AnthropicProvider` (Claude 3.5 Sonnet/Opus)
- [ ] `OpenAIProvider` (GPT-4/GPT-4 Turbo)
- [ ] `OllamaProvider` (local models)
- [ ] Provider selection via configuration
- [ ] Rate limiting and retry logic
- [ ] Token counting and cost tracking
- [ ] Unit tests (test_llm_provider.py)

**Example API:**
```python
provider = get_provider('anthropic')  # or 'openai', 'ollama'
response = provider.generate(prompt, max_tokens=2000)
```

---

### Task 2.2: Configuration Management
**File:** `config/config.py`

- [ ] Load from `.env` file
- [ ] LLM provider settings (API keys, model names, temperature)
- [ ] Database path configuration
- [ ] Output directory settings
- [ ] Logging configuration
- [ ] User preferences (privacy rules, citation style)
- [ ] Validation of required settings
- [ ] Unit tests (test_config.py)

**Example `.env`:**
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_LLM_PROVIDER=anthropic
DEFAULT_MODEL=claude-3-5-sonnet-20250110
RM_DATABASE_PATH=data/Iiams.rmtree
```

---

### Task 2.3: Prompt Templates
**File:** `agent/prompts.py`
**Reference:** RM11_Biography_Best_Practices.md, RM11_Data_Quality_Rules.md

- [ ] System prompts for biography generation
- [ ] System prompts for data quality analysis
- [ ] System prompts for Q&A
- [ ] System prompts for timeline curation
- [ ] Few-shot examples for each task
- [ ] Variable substitution (person data, events, etc.)
- [ ] Prompt versioning
- [ ] Unit tests (test_prompts.py)

**Example Templates:**
```python
BIOGRAPHY_SYSTEM_PROMPT = """
You are a professional genealogist writing biographical narratives.
Follow the 9-section structure:
1. Introduction
2. Early Life & Family Background
...

Guidelines:
- Use 3rd person past tense
- Handle uncertainty with qualifiers: "likely", "probably", "about"
- Respect privacy rules (110-year rule, IsPrivate flags)
- Cite sources when available
"""

DATA_QUALITY_PROMPT = """
Analyze the following genealogical data for quality issues.
Check for:
- Logical inconsistencies (death before birth, etc.)
- Missing required information
- Referential integrity problems
...
"""
```

---

### Task 2.4: Agent Core
**File:** `agent/genealogy_agent.py`

- [ ] Main `GenealogyAgent` class
- [ ] Context building from database queries
- [ ] Prompt construction with person/event data
- [ ] LLM invocation with retry logic
- [ ] Response parsing and validation
- [ ] Conversation memory (for Q&A)
- [ ] Integration tests (test_agent.py)

**Example API:**
```python
agent = GenealogyAgent(db, llm_provider)
bio = agent.generate_biography(person_id, style='standard')
issues = agent.analyze_data_quality(person_id)
answer = agent.ask("Tell me about John Smith's occupation")
```

---

### Task 2.5: LangChain Tools
**File:** `agent/tools.py`

- [ ] `QueryPersonTool` - Get person information
- [ ] `GetEventsTool` - Get events for person
- [ ] `GetAncestorsTool` - Get ancestor tree
- [ ] `FindRelationshipTool` - Calculate relationship between two persons
- [ ] `ValidateDataTool` - Run quality checks
- [ ] `SearchDatabaseTool` - Search by name/place/date
- [ ] Tool descriptions for LangChain agent
- [ ] Unit tests (test_tools.py)

**Example:**
```python
tools = [
    QueryPersonTool(db),
    GetEventsTool(db),
    ValidateDataTool(db),
]
agent = create_langchain_agent(llm, tools)
```

---

## Phase 3: Output Generators (Working Prototype - Output)

**Goal:** Generate formatted output in various formats

### Task 3.1: Biography Generator
**File:** `generators/biography.py`
**Reference:** RM11_Biography_Best_Practices.md

- [ ] Extract person data (name, events, relationships)
- [ ] Build context for AI (facts, sources, uncertainty levels)
- [ ] Generate 9-section biography structure:
  1. Introduction
  2. Early Life & Family Background
  3. Education & Training
  4. Career & Accomplishments
  5. Marriage & Family
  6. Later Life & Activities
  7. Death & Burial
  8. Legacy & Significance
  9. Sources & Notes
- [ ] Handle length variations (short/standard/comprehensive)
- [ ] Apply privacy rules (IsPrivate flags, 110-year rule)
- [ ] Format citations (footnote/parenthetical/narrative)
- [ ] Include media references where appropriate
- [ ] Integration tests (test_biography_generator.py)

**Example API:**
```python
generator = BiographyGenerator(db, agent)
bio = generator.generate(
    person_id=1,
    length='standard',  # 500-1500 words
    citation_style='footnote',
    include_sources=True
)
```

---

### Task 3.2: Data Quality Report Generator
**File:** `generators/quality_report.py`
**Reference:** RM11_Data_Quality_Rules.md

- [ ] Run all 24 validation rules
- [ ] Categorize issues by severity (Critical/High/Medium/Low)
- [ ] Group by category (Required Fields, Logical Consistency, etc.)
- [ ] Generate summary statistics
- [ ] Format as Markdown report
- [ ] Format as HTML report (optional)
- [ ] Export to CSV for spreadsheet analysis
- [ ] Integration tests (test_quality_report.py)

**Example Output:**
```markdown
# Data Quality Report
Generated: 2025-01-08

## Summary
- Total Issues: 156
- Critical: 12
- High: 34
- Medium: 67
- Low: 43

## Critical Issues
### Death Before Birth (3 persons)
1. Anna Francis Iams (PersonID: 123)
   - Birth: 1896-03-02
   - Death: 1896-00-00
   ...
```

---

### Task 3.3: Timeline Generator
**File:** `generators/timeline.py`
**Reference:** RM11_Timeline_Construction.md

- [ ] Extract events for person (or family)
- [ ] Parse dates to TimelineJS3 format
- [ ] Handle date ranges (between, from, to)
- [ ] Order events chronologically
- [ ] Same-date event prioritization (Birth, Death, Marriage first)
- [ ] Handle undated events (exclude or estimate)
- [ ] Group events by life phases (Early Life, Career, Family, etc.)
- [ ] Format places (short form: "City, State")
- [ ] Attach media from MultimediaTable
- [ ] Include citation credits
- [ ] Generate TimelineJS3 JSON
- [ ] Integration tests (test_timeline_generator.py)

**Example API:**
```python
generator = TimelineGenerator(db)
timeline = generator.generate(person_id=1, format='timelinejs3')
# Outputs: timeline.json for TimelineJS viewer
```

---

### Task 3.4: Hugo Blog Post Exporter
**File:** `generators/hugo_exporter.py`

- [ ] Generate Hugo-compatible Markdown
- [ ] Front matter (YAML) with metadata
- [ ] Embed biography content
- [ ] Embed timeline (via shortcode or iframe)
- [ ] Link to source images/documents
- [ ] Generate person index page
- [ ] Generate family tree visualization (optional)
- [ ] Handle Hugo taxonomies (surnames, places, time periods)
- [ ] Integration tests (test_hugo_exporter.py)

**Example Output:**
```markdown
---
title: "Biography of John William Smith"
date: 2025-01-08
categories: ["Biographies", "Smith Family"]
tags: ["Maryland", "Civil War", "1800s"]
person_id: 123
birth_year: 1845
death_year: 1923
---

## Introduction
John William Smith was born on March 15, 1845, in Baltimore, Maryland...

{{< timeline person_id="123" >}}

## Sources
1. U.S. Census 1850, Maryland, Baltimore County...
```

---

## Phase 4: CLI Interface (Working Prototype - Complete)

**Goal:** Command-line interface for all features

### Task 4.1: CLI Framework
**File:** `cli/main.py`

- [ ] Use `click` for command structure
- [ ] Use `rich` for formatted output
- [ ] Global options: `--database`, `--verbose`, `--llm-provider`
- [ ] Progress indicators for long operations
- [ ] Error handling and user-friendly messages
- [ ] Help text for all commands
- [ ] Integration tests (test_cli.py)

**Command Structure:**
```bash
rmtool [OPTIONS] COMMAND [ARGS]

Options:
  --database PATH      Path to RootsMagic database
  --llm-provider TEXT  LLM provider (anthropic/openai/ollama)
  --verbose           Enable verbose logging
  --help              Show this message and exit

Commands:
  person     Query person information
  bio        Generate biography
  quality    Run data quality checks
  ask        Ask questions about the database
  timeline   Generate timeline
  export     Export to Hugo blog
  search     Search database
```

---

### Task 4.2: Person Command
**File:** `cli/commands/person.py`

- [ ] `rmtool person <id>` - Show person details
- [ ] `rmtool person <id> --events` - Show all events
- [ ] `rmtool person <id> --ancestors` - Show ancestor tree
- [ ] `rmtool person <id> --descendants` - Show descendant tree
- [ ] `rmtool person <id> --family` - Show immediate family
- [ ] Rich table formatting
- [ ] Integration tests

**Example:**
```bash
$ rmtool person 1 --events

📋 Person: Michael Dorsey Iams (1968-)
─────────────────────────────────────

Events:
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Date      ┃ Type         ┃ Place                  ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 30 Apr 68 │ Birth        │ Palo Alto, California  │
│ 1988      │ Education    │ Tucson, Arizona        │
│ 29 May 17 │ DNA test     │                        │
└───────────┴──────────────┴────────────────────────┘
```

---

### Task 4.3: Biography Command
**File:** `cli/commands/bio.py`

- [ ] `rmtool bio <id>` - Generate biography
- [ ] `--length` option (short/standard/comprehensive)
- [ ] `--style` option (narrative/academic/casual)
- [ ] `--output` option (stdout/file)
- [ ] `--format` option (markdown/html/text)
- [ ] `--citations` flag (include source citations)
- [ ] Progress indicator during generation
- [ ] Integration tests

**Example:**
```bash
$ rmtool bio 1 --length standard --output bio.md

⏳ Generating biography for Michael Dorsey Iams...
✓ Querying database (12 events found)
✓ Building context
✓ Generating narrative with Claude 3.5 Sonnet
✓ Formatting citations
✓ Writing to bio.md

📄 Biography complete: bio.md (1,247 words)
```

---

### Task 4.4: Quality Command
**File:** `cli/commands/quality.py`

- [ ] `rmtool quality` - Run all checks on entire database
- [ ] `rmtool quality --person <id>` - Check specific person
- [ ] `--category` filter (required/logical/integrity/sources/dates/values)
- [ ] `--severity` filter (critical/high/medium/low)
- [ ] `--output` option (stdout/file)
- [ ] `--format` option (markdown/html/csv/json)
- [ ] Summary statistics display
- [ ] Integration tests

**Example:**
```bash
$ rmtool quality --severity critical

🔍 Running data quality checks...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Data Quality Report
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Summary:
  Total Issues: 156
  Critical: 12
  High: 34
  Medium: 67
  Low: 43

🚨 Critical Issues (12)

Death Before Birth (3)
├─ Anna Francis Iams (PersonID: 456)
│  Birth: 1896-03-02, Death: 1896-00-00
├─ Frances Keller (PersonID: 789)
│  Birth: 1859-10-19, Death: 1928-00-00
└─ Jesse Imes (PersonID: 234)
   Birth: 1919-05-26, Death: 1919-00-00
```

---

### Task 4.5: Ask Command (Q&A)
**File:** `cli/commands/ask.py`

- [ ] `rmtool ask "question"` - Interactive Q&A
- [ ] `rmtool ask --interactive` - Conversation mode
- [ ] Context preservation across questions
- [ ] Source attribution in answers
- [ ] Rich markdown formatting
- [ ] Integration tests

**Example:**
```bash
$ rmtool ask "Who were Michael Iams' parents?"

🤔 Searching database...

Michael Dorsey Iams' parents were:

👨 Father: Dorsey Preston Iams (1929-2017)
  - Born: 30 May 1929 in Baltimore, Maryland
  - Died: 30 May 2017 in Tucson, Arizona

👩 Mother: Patricia Anne Hughes (1937-)
  - Born: 14 August 1937 in Baltimore, Maryland
  - Still living

Source: FamilyTable (FamilyID: 42), PersonTable
```

---

### Task 4.6: Timeline Command
**File:** `cli/commands/timeline.py`

- [ ] `rmtool timeline <id>` - Generate timeline JSON
- [ ] `--format` option (timelinejs3/json/markdown)
- [ ] `--output` option (stdout/file)
- [ ] `--group-by` option (phase/year/decade)
- [ ] `--include-family` flag (add spouse/children events)
- [ ] Integration tests

**Example:**
```bash
$ rmtool timeline 1 --output timeline.json

⏳ Generating timeline for Michael Dorsey Iams...
✓ Extracted 12 events
✓ Parsed dates
✓ Grouped by life phases
✓ Writing TimelineJS3 JSON

📅 Timeline complete: timeline.json
   View at: https://timeline.knightlab.com
```

---

### Task 4.7: Export Command (Hugo)
**File:** `cli/commands/export.py`

- [ ] `rmtool export hugo <id>` - Export person to Hugo post
- [ ] `rmtool export hugo --all` - Export all persons
- [ ] `--output-dir` option
- [ ] `--template` option (custom Hugo template)
- [ ] `--include-timeline` flag
- [ ] `--include-media` flag (copy media files)
- [ ] Generate index pages
- [ ] Integration tests

**Example:**
```bash
$ rmtool export hugo 1 --output-dir content/people

⏳ Exporting Michael Dorsey Iams to Hugo...
✓ Generated biography
✓ Generated timeline
✓ Copied 3 media files
✓ Created content/people/michael-dorsey-iams.md

📝 Hugo post ready: content/people/michael-dorsey-iams.md
```

---

### Task 4.8: Search Command
**File:** `cli/commands/search.py`

- [ ] `rmtool search --name "John Smith"` - Search by name
- [ ] `rmtool search --place "Maryland"` - Search by place
- [ ] `rmtool search --date "1850"` - Search by date
- [ ] `--limit` option
- [ ] Phonetic search support (Metaphone)
- [ ] Rich table formatting
- [ ] Integration tests

**Example:**
```bash
$ rmtool search --name "Smith" --limit 5

🔍 Searching for: Smith

Found 5 matches:

┏━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┓
┃ ID   ┃ Name                  ┃ Birth    ┃ Death    ┃
┡━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ 234  │ Adelaide Smith        │ 1841     │ 1906     │
│ 567  │ Albert Henry Smith    │ 1911     │ 1977     │
│ 890  │ Ann Smith             │          │          │
└──────┴───────────────────────┴──────────┴──────────┘
```

---

### 🎯 Milestone 2 Checkpoint: MVP (Minimum Viable Product)

**Definition:** All 5 core features working in basic form

**Deliverables:**
- [ ] Complete CLI with all 8 commands working
- [ ] Data quality analysis (all 24 rules)
- [ ] Biography generation (9-section structure)
- [ ] Interactive Q&A with conversation memory
- [ ] Timeline generation (TimelineJS3 format)
- [ ] Hugo blog post export
- [ ] Multi-LLM support (Anthropic, OpenAI, Ollama)
- [ ] Comprehensive test suite (>80% coverage)
- [ ] User documentation (README, CLI help)
- [ ] Configuration management (.env)

**Test Commands:**
```bash
# All should work at MVP
rmtool person 1
rmtool bio 1 --length standard
rmtool quality --severity critical
rmtool ask "Tell me about the Smith family"
rmtool timeline 1
rmtool export hugo 1
rmtool search --name "Smith"
```

**Acceptance Criteria:**
✓ All CLI commands execute without errors
✓ All 24 data quality rules detect issues correctly
✓ Biographies follow 9-section structure and read naturally
✓ Q&A provides accurate answers with source attribution
✓ Timelines display correctly in TimelineJS viewer
✓ Hugo posts render correctly in Hugo site
✓ All 3 LLM providers work (Claude, GPT-4, Ollama)
✓ Test coverage >80%
✓ No crashes, graceful error handling throughout
✓ Documentation complete and accurate

---

## Phase 5: Testing & Quality (MVP - Polish)

**Goal:** Comprehensive test coverage and code quality

### Task 5.1: Unit Tests
**Target:** >80% code coverage

- [ ] test_database.py (connection, RMNOCASE)
- [ ] test_models.py (Pydantic validation)
- [ ] test_date_parser.py (all date formats)
- [ ] test_blob_parser.py (all BLOB types)
- [ ] test_place_parser.py (hierarchy parsing)
- [ ] test_name_parser.py (name selection logic)
- [ ] test_queries.py (all 15 patterns)
- [ ] test_quality.py (all 24 rules)
- [ ] test_llm_provider.py (all 3 providers)
- [ ] test_prompts.py (template rendering)
- [ ] test_agent.py (biography/Q&A generation)
- [ ] test_tools.py (LangChain tools)
- [ ] test_biography_generator.py
- [ ] test_quality_report.py
- [ ] test_timeline_generator.py
- [ ] test_hugo_exporter.py
- [ ] All CLI command tests

**Run with:**
```bash
pytest tests/ --cov=rmlib --cov=agent --cov=generators --cov=cli --cov-report=html
```

---

### Task 5.2: Integration Tests

- [ ] End-to-end biography generation
- [ ] End-to-end data quality report
- [ ] End-to-end Q&A session
- [ ] End-to-end timeline generation
- [ ] End-to-end Hugo export
- [ ] Multi-person batch processing
- [ ] All LLM providers tested
- [ ] Edge cases (missing data, malformed input)

---

### Task 5.3: Code Quality

- [ ] Type hints throughout (mypy validation)
- [ ] Code formatting with Black
- [ ] Linting with Ruff
- [ ] Docstrings for all public functions
- [ ] Error handling comprehensive
- [ ] Logging properly configured
- [ ] No hardcoded values (use config)
- [ ] Security review (API key handling)

**Run with:**
```bash
black .
ruff check .
mypy rmlib/ agent/ generators/ cli/
```

---

### Task 5.4: Performance Testing

- [ ] Profile database queries
- [ ] Optimize slow queries
- [ ] Profile LLM token usage
- [ ] Optimize prompt lengths
- [ ] Test with large database (>50K persons)
- [ ] Memory usage profiling
- [ ] Batch processing optimization

---

## Phase 6: Documentation (MVP - Complete)

**Goal:** Complete user and developer documentation

### Task 6.1: User Documentation

- [ ] **README.md** - Project overview, installation, quick start
- [ ] **INSTALL.md** - Detailed installation instructions
- [ ] **USAGE.md** - All CLI commands with examples
- [ ] **CONFIGURATION.md** - .env settings, LLM provider setup
- [ ] **FAQ.md** - Common questions and troubleshooting
- [ ] **EXAMPLES.md** - Real-world usage scenarios

---

### Task 6.2: Developer Documentation

- [ ] **ARCHITECTURE.md** - System design, module structure
- [ ] **API.md** - Python API reference
- [ ] **CONTRIBUTING.md** - How to contribute
- [ ] **TESTING.md** - How to run tests
- [ ] **CHANGELOG.md** - Version history
- [ ] Code docstrings (Sphinx-compatible)

---

### Task 6.3: Tutorial

- [ ] Getting started tutorial
- [ ] Biography generation walkthrough
- [ ] Data quality analysis tutorial
- [ ] Q&A session examples
- [ ] Hugo integration guide
- [ ] Custom LLM provider guide

---

## Phase 7: Production Polish (Post-MVP)

**Goal:** Refinement, optimization, advanced features

### Task 7.1: Performance Optimization

- [ ] Query result caching
- [ ] LLM response caching
- [ ] Batch processing for multiple persons
- [ ] Parallel processing where possible
- [ ] Database indexing optimization
- [ ] Memory profiling and optimization

---

### Task 7.2: Enhanced Error Handling

- [ ] Graceful degradation (work without LLM if needed)
- [ ] Detailed error messages with suggestions
- [ ] Automatic retry for transient failures
- [ ] Validation of user inputs
- [ ] Database corruption detection
- [ ] Missing extension detection and guidance

---

### Task 7.3: User Experience Enhancements

- [ ] Progress bars for long operations
- [ ] Colorized output (rich terminal)
- [ ] Interactive prompts (confirm before expensive operations)
- [ ] Auto-complete for CLI commands
- [ ] Command history
- [ ] Export to PDF (biographies, reports)

---

### Task 7.4: Advanced Features

- [ ] Relationship graph visualization (GraphViz)
- [ ] Source analysis (most-used sources, source quality)
- [ ] Place analysis (geographic distribution)
- [ ] DNA integration (if DNATable has data)
- [ ] Photo gallery generation
- [ ] Custom report templates
- [ ] Batch biography generation (entire database)
- [ ] Multi-database support (compare databases)

---

### Task 7.5: Hugo Integration Enhancements

- [ ] Custom Hugo shortcodes for timelines
- [ ] Custom Hugo shortcodes for family trees
- [ ] Automatic taxonomy generation (surnames, places)
- [ ] Photo gallery integration
- [ ] Search index generation
- [ ] Related persons suggestions
- [ ] Dynamic family tree widgets

---

## Testing Strategy

### Unit Tests (>80% coverage target)
- Test all parsers with edge cases
- Test all query patterns
- Test all validation rules
- Mock LLM responses for predictable tests
- Mock database for isolated tests

### Integration Tests
- Test full workflows end-to-end
- Test with real Iiams.rmtree database
- Test all LLM providers
- Test error conditions

### Validation Tests
- Use validation scripts from docs/VALIDATION_RESULTS.md
- Run against real database regularly
- Verify documentation accuracy

---

## Dependency Management

### Core Dependencies
```
python >= 3.11
sqlite3 (built-in)
pydantic >= 2.0
python-dotenv >= 1.0
click >= 8.0
rich >= 13.0
jinja2 >= 3.0
pyyaml >= 6.0
```

### AI Dependencies
```
anthropic >= 0.18.0
openai >= 1.10.0
ollama >= 0.1.0
langchain >= 0.1.0
langchain-anthropic >= 0.1.0
langchain-openai >= 0.0.5
```

### Testing Dependencies
```
pytest >= 7.0
pytest-cov >= 4.0
pytest-mock >= 3.0
pytest-asyncio >= 0.21.0
```

### Development Dependencies
```
black >= 23.0
ruff >= 0.1.0
mypy >= 1.0
```

---

## Project Structure

```
RM11/
├── rmlib/                      # Core library
│   ├── __init__.py
│   ├── database.py            # Database connection
│   ├── models.py              # Pydantic data models
│   ├── queries.py             # 15 query patterns
│   ├── quality.py             # 24 validation rules
│   └── parsers/
│       ├── __init__.py
│       ├── date_parser.py     # 24-char date format
│       ├── blob_parser.py     # XML BLOB parsing
│       ├── place_parser.py    # Place hierarchy
│       └── name_parser.py     # Name selection
│
├── agent/                      # AI agent
│   ├── __init__.py
│   ├── llm_provider.py        # LLM abstraction
│   ├── genealogy_agent.py     # Main agent
│   ├── prompts.py             # Prompt templates
│   └── tools.py               # LangChain tools
│
├── generators/                 # Output generators
│   ├── __init__.py
│   ├── biography.py           # 9-section bios
│   ├── quality_report.py      # Quality reports
│   ├── timeline.py            # TimelineJS3
│   └── hugo_exporter.py       # Hugo blog posts
│
├── cli/                        # CLI interface
│   ├── __init__.py
│   ├── main.py                # CLI entry point
│   └── commands/
│       ├── __init__.py
│       ├── person.py
│       ├── bio.py
│       ├── quality.py
│       ├── ask.py
│       ├── timeline.py
│       ├── export.py
│       └── search.py
│
├── tests/                      # Test suite
│   ├── unit/
│   │   ├── test_database.py
│   │   ├── test_models.py
│   │   ├── test_parsers.py
│   │   ├── test_queries.py
│   │   └── ...
│   └── integration/
│       ├── test_biography.py
│       ├── test_quality.py
│       └── ...
│
├── config/                     # Configuration
│   ├── __init__.py
│   ├── config.py
│   └── prompts/
│       ├── biography.txt
│       ├── quality.txt
│       └── qna.txt
│
├── templates/                  # Output templates
│   ├── biography.md.j2
│   ├── quality_report.md.j2
│   ├── hugo_post.md.j2
│   └── timeline.json.j2
│
├── data/                       # Data (not in git)
│   └── Iiams.rmtree           # Sample database
│
├── sqlite-extension/           # SQLite extension
│   ├── icu.dylib
│   └── python_example.py
│
├── docs/                       # Documentation
│   ├── VALIDATION_RESULTS.md
│   ├── AI_AGENT_TODO.md       # This file
│   └── data_reference/        # Schema docs
│
├── .env.example               # Example configuration
├── .gitignore
├── pyproject.toml             # Project metadata
├── requirements.txt           # Dependencies
├── README.md                  # User docs
└── LICENSE
```

---

## Progress Tracking

### Phase 1: Foundation (Working Prototype - Core Library)
- [ ] 1.1: Project Setup
- [ ] 1.2: Database Connection Module
- [ ] 1.3: Data Models
- [ ] 1.4: Date Parser
- [ ] 1.5: BLOB Parsers
- [x] 1.6: Place Parser
- [x] 1.7: Name Parser
- [x] 1.8: Query Service
- [x] 1.9: Data Quality Validator

**Progress:** 4/9 tasks

### Phase 2: AI Integration (Working Prototype - AI Layer)
- [ ] 2.1: LLM Provider Abstraction
- [ ] 2.2: Configuration Management
- [ ] 2.3: Prompt Templates
- [ ] 2.4: Agent Core
- [ ] 2.5: LangChain Tools

**Progress:** 0/5 tasks

### Phase 3: Output Generators (Working Prototype - Output)
- [ ] 3.1: Biography Generator
- [ ] 3.2: Data Quality Report Generator
- [ ] 3.3: Timeline Generator
- [ ] 3.4: Hugo Blog Post Exporter

**Progress:** 0/4 tasks

### Phase 4: CLI Interface (Working Prototype - Complete)
- [ ] 4.1: CLI Framework
- [ ] 4.2: Person Command
- [ ] 4.3: Biography Command
- [ ] 4.4: Quality Command
- [ ] 4.5: Ask Command (Q&A)
- [ ] 4.6: Timeline Command
- [ ] 4.7: Export Command (Hugo)
- [ ] 4.8: Search Command

**Progress:** 0/8 tasks

### 🎯 Milestone 1: Working Prototype
**Status:** Not Started
**Progress:** 0% (0/26 tasks in Phases 1-4)

### Phase 5: Testing & Quality (MVP - Polish)
- [ ] 5.1: Unit Tests
- [ ] 5.2: Integration Tests
- [ ] 5.3: Code Quality
- [ ] 5.4: Performance Testing

**Progress:** 0/4 tasks

### Phase 6: Documentation (MVP - Complete)
- [ ] 6.1: User Documentation
- [ ] 6.2: Developer Documentation
- [ ] 6.3: Tutorial

**Progress:** 0/3 tasks

### 🎯 Milestone 2: MVP
**Status:** Not Started
**Progress:** 0% (0/33 tasks total)

### Phase 7: Production Polish (Post-MVP)
- [ ] 7.1: Performance Optimization
- [ ] 7.2: Enhanced Error Handling
- [ ] 7.3: User Experience Enhancements
- [ ] 7.4: Advanced Features
- [ ] 7.5: Hugo Integration Enhancements

**Progress:** 0/5 tasks

### 🎯 Milestone 3: Production Polish
**Status:** Not Started
**Progress:** 0% (0/38 tasks total)

---

## Total Task Count

- **Phase 1 (Foundation):** 9 tasks
- **Phase 2 (AI Integration):** 5 tasks
- **Phase 3 (Output Generators):** 4 tasks
- **Phase 4 (CLI Interface):** 8 tasks
- **Phase 5 (Testing):** 4 tasks
- **Phase 6 (Documentation):** 3 tasks
- **Phase 7 (Polish):** 5 tasks

**Total:** 38 tasks

**Milestone Distribution:**
- **Working Prototype:** 26 tasks (Phases 1-4)
- **MVP:** 33 tasks (Phases 1-6)
- **Production Polish:** 38 tasks (All phases)

---

## Notes

- All documentation references are in `/Users/miams/Code/RM11/data_reference/`
- Sample database at `/Users/miams/Code/RM11/data/Iiams.rmtree`
- SQLite extension at `/Users/miams/Code/RM11/sqlite-extension/icu.dylib`
- All specifications validated (see docs/VALIDATION_RESULTS.md)
- Test scripts available in `/tmp/` (test_query_patterns.py, etc.)
- 18 comprehensive documentation files ready for reference
- No reverse-engineering needed - all formats documented

---

**Last Updated:** 2025-01-08
**Status:** Ready to begin implementation
**Next Step:** Start Phase 1, Task 1.1 (Project Setup)
