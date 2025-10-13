# CLAUDE.md

Guidance for Claude Code when working with RMAgent - an AI-powered genealogy agent for RootsMagic 11 databases.

## Repository: miams/rmagent

- **GitHub:** https://github.com/miams/rmagent
- **Clone:** `git clone git@github.com:miams/rmagent.git`
- **SSH Key:** `ssh-add ~/.ssh/miams-github`

## Project Overview

Python tooling stack for RootsMagic 11 (RM11) SQLite databases. Provides AI agents for querying databases, diagnosing data quality, and generating biographies with family context (sibling order, parental ages, migrations, family losses). LLM prompts/responses logged to `logs/llm_debug.jsonl` for reproducibility.

## Key Directories

```
rmagent/
├── rmagent/                   # Main Python package
│   ├── agent/                # AI agent (LLM providers, prompts, tools)
│   ├── cli/                  # CLI commands (8 commands)
│   ├── config/               # Configuration (Pydantic settings)
│   ├── generators/           # Biography, timeline, Hugo export
│   └── rmlib/                # Core library (database, parsers, queries)
├── config/                   # Runtime config (config/.env)
├── data/                     # Database files (*.rmtree, NOT tracked in git)
├── data_reference/           # 18 schema/format docs (RM11_*.md)
├── docs/                     # Project docs (AI_AGENT_TODO.md, USER_GUIDE.md, MVP_CHECKPOINT.md)
├── sqlite-extension/         # ICU extension for RMNOCASE collation
└── tests/unit/               # Test suite (245+ tests, pytest)
```

## Essential Documentation (data_reference/)

**Schema & Structure:**
- **RM11_Schema_Reference.md** - START HERE: tables, fields, relationships, query patterns
- **RM11_schema_annotated.sql** - SQL with comments for query writing
- **RM11_DataDef.yaml** - Field enumerations and constraints

**Core Formats:**
- **RM11_Date_Format.md** - CRITICAL: 24-char date encoding (ranges, qualifiers, BC/AD)
- **RM11_Place_Format.md** - Comma-delimited hierarchy (City, County, State, Country)
- **RM11_FactTypes.md** - 65 built-in event types

**BLOB Structures (UTF-8 XML with BOM):**
- **RM11_BLOB_SourceFields.md** - SourceTable.Fields extraction
- **RM11_BLOB_SourceTemplateFieldDefs.md** - Template definitions (433 templates)
- **RM11_BLOB_CitationFields.md** - CitationTable.Fields extraction

**Data Quality & Output:**
- **RM11_Data_Quality_Rules.md** - 24 validation rules across 6 categories
- **RM11_Query_Patterns.md** - 15 optimized SQL patterns
- **RM11_Biography_Best_Practices.md** - 9-section structure, citation styles
- **RM11_Timeline_Construction.md** - TimelineJS3 JSON generation

**Additional References:**
- RM11_Relationships.md (Relate1/Relate2 calculations)
- RM11_Name_Display_Logic.md (context-aware name selection)
- RM11_EventTable_Details.md (Details field patterns)
- RM11_Sentence_Templates.md (reference only - AI generates text natively)

## Critical Schema Patterns

### OwnerType/OwnerID Polymorphism
Linking tables use `OwnerType` + `OwnerID` for polymorphic associations:
- 0=Person, 1=Family, 2=Event, 3=Source, 4=Citation, 5=Place, 6=Task, 7=Name, 14=Place Details, 19=FAN

### Date Handling
- **Date (TEXT)**: 24-char encoding (see RM11_Date_Format.md)
- **SortDate (BIGINT)**: Sortable integer (9223372036854775807 = unknown)

### BLOB Fields
UTF-8 XML with BOM (EFBBBF):
- SourceTable.Fields, CitationTable.Fields, SourceTemplateTable.FieldDefs
- Decode with `utf-8-sig`, parse with ElementTree

### Collation
**CRITICAL:** Text fields use `COLLATE RMNOCASE` - requires ICU extension:
```python
conn = sqlite3.connect('data/Iiams.rmtree')
conn.enable_load_extension(True)
conn.load_extension('./sqlite-extension/icu.dylib')
conn.execute("SELECT icu_load_collation('en_US@colStrength=primary;caseLevel=off;normalization=on','RMNOCASE')")
conn.enable_load_extension(False)
```

### Privacy & Proof
- **IsPrivate**: 0=public, 1=private
- **Proof**: 0=blank, 1=proven, 2=disproven, 3=disputed

## Development Setup

Uses **uv** for package management. Key commands:
```bash
uv sync --extra dev                  # Install dependencies
uv run pytest --cov=rmagent          # Run tests with coverage
uv run black . && uv run ruff check .  # Format and lint
uv run rmagent person 1 --events     # Run CLI commands
```

Configuration in `config/.env`:
```bash
DEFAULT_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx
RM_DATABASE_PATH=data/Iiams.rmtree
LOG_LEVEL=DEBUG                      # Enable LLM logging
```

## Project Status (2025-10-12)

🎉 **Milestone 2: MVP ACHIEVED** - All foundation phases complete (33/33 tasks)

**Completed Phases:**
- ✅ Phase 1: Foundation (9/9) - Database, parsers, queries, validation
- ✅ Phase 2: AI Integration (5/5) - Multi-LLM, prompts, agent, tools
- ✅ Phase 3: Generators (4/4) - Biography, timeline, quality reports, Hugo export
- ✅ Phase 4: CLI (8/8) - All commands working (person, bio, quality, ask, timeline, export, search)
- ✅ Phase 5: Testing & Quality (4/4) - 418 tests, 82% coverage, optimized performance
- ✅ Phase 6: Documentation (2/3) - User & developer docs complete

**Recent Enhancements:**
- **Major refactoring:** Modularized genealogy_agent.py and queries.py for better maintainability
  - `agent/formatters.py` - Extracted formatting utilities (505 lines)
  - `agent/genealogy_agent.py` - Focused on orchestration (735→289 lines, -61%)
  - `rmlib/sql_queries.py` - Extracted SQL constants (541 lines)
  - `rmlib/queries.py` - Focused on query service (1,076→581 lines, -46%)
- Biography notes integration (PersonTable.Note + EventTable.Note in AI context)
- Structured biography file output (`./reports/biographies/Surname, Given (bbbb-dddd).md`)
- Source formatting improvements (italic rendering, type prefix removal)
- Biography collision handling with sequential numbering

**Test Coverage:** 418 tests, 82% overall coverage (97% database, 96% parsers, 91% quality)

**Next Phase:** Phase 7 - Production Polish (performance optimization, advanced features)

See `docs/AI_AGENT_TODO.md` for complete roadmap.

## CLI Commands

All commands use `uv run rmagent [command]`:

- **person** `<id>` - Query person (--events, --family, --ancestors, --descendants)
- **bio** `<id>` - Generate biography (--length, --citation-style, --no-ai, --output)
- **quality** - Data validation (--category, --severity, --format, --output)
- **ask** `<question>` - Q&A with LLM (--interactive for conversation mode)
- **timeline** `<id>` - Generate timeline (--format json/html, --group-by-phase, --include-family)
- **export hugo** `<id>` - Hugo blog export (--output-dir, --batch-ids, --all, --include-timeline)
- **search** - Search by name/place (--name, --place, --limit, --exact)

## ⚠️ Database File Policy

**NEVER commit database files to git!**

- `.gitignore` correctly excludes `*.rmtree` files
- **NEVER add exceptions** like `!data/Iiams.rmtree`
- Database files contain sensitive personal information
- Users maintain local database files in `data/` directory
- Document structure in markdown/SQL, not by committing the database

## LangChain v1.0 Integration (Future)

**Status:** Zero active LangChain imports. v1.0 upgrade planned for Phase 7. See `docs/RM11_LangChain_Upgrade.md` and `AGENTS.md` for patterns.

**v1.0 Requirements:** `create_agent()`, `system_prompt="string"`, TypedDict state only. New code goes in `rmagent/agent/lc/` directory.

## Git Workflow

```bash
git clone git@github.com:miams/rmagent.git && ssh-add ~/.ssh/miams-github
git commit -m "feat: description"  # Use: feat|fix|docs|test|refactor
```

**Branches:** main (production), develop (integration), feature/* (new work)

## Quick Reference

**Sample Database:** `data/Iiams.rmtree` (11,571 persons, 29,543 events, 114 sources, 10,838 citations)

**Key Files:**
- `rmagent/agent/genealogy_agent.py` - Agent orchestration (289 lines)
- `rmagent/agent/formatters.py` - Formatting utilities for genealogical data (505 lines)
- `rmagent/agent/llm_provider.py` - Multi-provider abstraction (Anthropic/OpenAI/Ollama)
- `rmagent/config/config.py` - Configuration with `load_app_config()`
- `rmagent/rmlib/database.py` - Database connection with RMNOCASE
- `rmagent/rmlib/queries.py` - Query service class (581 lines)
- `rmagent/rmlib/sql_queries.py` - SQL query constants (541 lines)
- `sqlite-extension/python_example.py` - RMNOCASE collation examples

**External Resources:**
- RootsMagic: https://www.rootsmagic.com/
- SQLite Docs: https://www.sqlite.org/docs.html
- GEDCOM Standard (for FactTypeTable.GedcomTag mappings)
