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

Uses **uv** for Python package management:

```bash
# Install dependencies
uv sync                              # Production
uv sync --extra dev                  # With dev tools

# Development workflow
uv run pytest                        # Run tests
uv run pytest --cov=rmagent          # With coverage
uv run black .                       # Format
uv run ruff check .                  # Lint
uv run mypy rmagent/                 # Type check

# Run CLI commands
uv run rmagent person 1 --events --family
uv run rmagent bio 1 --length comprehensive
uv run rmagent quality --category logical
uv run rmagent search --name "Smith"
```

Configuration in `config/.env`:
```bash
DEFAULT_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx
RM_DATABASE_PATH=data/Iiams.rmtree
LOG_LEVEL=DEBUG                      # Enable LLM logging to logs/llm_debug.jsonl
```

## Project Status (2025-10-10)

🎉 **Milestone 2: MVP ACHIEVED** - All 26 foundation tasks complete

**Completed Phases:**
- ✅ Phase 1: Foundation (9/9) - Database, parsers, queries, validation
- ✅ Phase 2: AI Integration (5/5) - Multi-LLM, prompts, agent, tools
- ✅ Phase 3: Generators (4/4) - Biography, timeline, quality reports, Hugo export
- ✅ Phase 4: CLI (8/8) - person, bio, quality, ask, timeline, export, search commands

**Test Coverage:** 245+ tests, 68-99% coverage across modules

**Next Phase:** Phase 5 - Testing & Quality (integration tests, 80%+ coverage)

See `docs/AI_AGENT_TODO.md` for complete roadmap (38 tasks across 7 phases).

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

## Git Workflow

```bash
# Repository setup
git clone git@github.com:miams/rmagent.git
ssh-add ~/.ssh/miams-github

# Commit conventions (Conventional Commits)
git commit -m "feat: add new feature"
git commit -m "fix: resolve bug"
git commit -m "docs: update documentation"
git commit -m "test: add tests"
git commit -m "refactor: restructure code"
```

**Branches:**
- **main** - Production-ready code
- **develop** - Integration branch
- **feature/** - Feature branches

## Quick Reference

**Sample Database:** `data/Iiams.rmtree` (11,571 persons, 29,543 events, 114 sources, 10,838 citations)

**Key Files:**
- `rmagent/agent/genealogy_agent.py` - Agent orchestration
- `rmagent/agent/llm_provider.py` - Multi-provider abstraction (Anthropic/OpenAI/Ollama)
- `rmagent/config/config.py` - Configuration with `load_app_config()`
- `rmagent/rmlib/database.py` - Database connection with RMNOCASE
- `rmagent/rmlib/queries.py` - 15 optimized query patterns
- `sqlite-extension/python_example.py` - RMNOCASE collation examples

**External Resources:**
- RootsMagic: https://www.rootsmagic.com/
- SQLite Docs: https://www.sqlite.org/docs.html
- GEDCOM Standard (for FactTypeTable.GedcomTag mappings)
