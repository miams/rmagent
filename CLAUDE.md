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
├── docs/                     # **📚 START HERE: docs/INDEX.md** - Complete documentation
│   ├── INDEX.md             # Master table of contents
│   ├── getting-started/     # Installation, quickstart, configuration
│   ├── guides/              # User & developer guides
│   ├── reference/           # Schema, formats, query patterns
│   ├── projects/            # Active feature development
│   └── archive/             # Completed milestones & summaries
├── sqlite-extension/         # ICU extension for RMNOCASE collation
└── tests/unit/               # Test suite (490+ tests, pytest)
```

## 📚 Essential Documentation

**For complete documentation, see [`docs/INDEX.md`](docs/INDEX.md)**

### Quick Reference (Most Important Files)

**Schema & Database:**
- **[schema-reference.md](docs/reference/schema/schema-reference.md)** - START HERE: tables, fields, relationships
- **[annotated-schema.sql](docs/reference/schema/annotated-schema.sql)** - SQL with comments
- **[data-definitions.yaml](docs/reference/schema/data-definitions.yaml)** - Field enumerations

**Critical Data Formats:**
- **[date-format.md](docs/reference/data-formats/date-format.md)** - ⚠️ CRITICAL: 24-char date encoding
- **[place-format.md](docs/reference/data-formats/place-format.md)** - Comma-delimited hierarchy
- **[fact-types.md](docs/reference/data-formats/fact-types.md)** - 65 built-in event types

**BLOB Parsing (UTF-8 XML with BOM):**
- **[blob-source-fields.md](docs/reference/data-formats/blob-source-fields.md)** - SourceTable.Fields
- **[blob-citation-fields.md](docs/reference/data-formats/blob-citation-fields.md)** - CitationTable.Fields
- **[blob-template-field-defs.md](docs/reference/data-formats/blob-template-field-defs.md)** - Template definitions

**Query & Quality:**
- **[query-patterns.md](docs/reference/query-patterns/query-patterns.md)** - 15 optimized SQL patterns
- **[data-quality-rules.md](docs/reference/query-patterns/data-quality-rules.md)** - 24 validation rules

**Biography & Output:**
- **[biography-best-practices.md](docs/reference/biography/biography-best-practices.md)** - 9-section structure
- **[timeline-construction.md](docs/reference/biography/timeline-construction.md)** - TimelineJS3 format

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

### Claude Code Integration

RMAgent includes 12 custom slash commands and automated hooks for Claude Code:

**Quick Commands:**
- `/rm-bio <id>` - Generate biography with AI
- `/rm-person <id>` - Query person from database
- `/rm-quality` - Run data quality checks
- `/doc-review [brief|deep]` - Review documentation for accuracy with AI
- `/test` - Run pytest suite
- `/coverage` - Run tests with coverage
- `/check-db` - Verify database connection

**Automated Hooks:**
- Coverage reminders after pytest runs
- Commit preview before git push
- Documentation review reminder (pre-commit)

**See [`docs/guides/claude-code-setup.md`](docs/guides/claude-code-setup.md) for complete setup and usage guide.**

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

**Test Coverage:** 490 tests, 88% overall coverage (97% database, 96% parsers, 94% rendering)

**Next Phase:** Phase 7 - Production Polish (performance optimization, advanced features)

See [`docs/projects/ai-agent/roadmap.md`](docs/projects/ai-agent/roadmap.md) for complete roadmap.

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

**Status:** Zero active LangChain imports. v1.0 upgrade planned for Phase 7. See [`docs/projects/ai-agent/langchain-upgrade.md`](docs/projects/ai-agent/langchain-upgrade.md) for detailed plan.

**v1.0 Requirements:** `create_agent()`, `system_prompt="string"`, TypedDict state only. New code goes in `rmagent/agent/lc/` directory.

## Git Workflow

**RMAgent uses a gitflow workflow with automated testing on all PRs.**

### Branch Structure
- **main** - Production-ready code only (protected, PR-only)
- **develop** - Default integration branch (all work starts here)
- **feature/** - Individual features (branch from develop, PR back to develop)

### Quick Start
```bash
# Clone and setup
git clone git@github.com:miams/rmagent.git && ssh-add ~/.ssh/miams-github

# Start new feature
git checkout develop && git pull
git checkout -b feature/description
git push -u origin feature/description

# Make changes and commit
git add . && git commit -m "feat: description"
git push

# Create PR to develop (squash merge)
gh pr create --base develop

# Merge when tests pass
gh pr merge --squash --delete-branch
```

### Commit Convention
Use: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`

### Release Process
When milestone complete: Create PR from `develop` → `main` (merge commit, not squash)

### CI/CD
All PRs automatically run:
- Linting (black, ruff)
- Full test suite with coverage (must maintain 80%+)
- See `.github/workflows/pr-tests.yml`

**For detailed workflow instructions, see [`docs/guides/git-workflow.md`](docs/guides/git-workflow.md)**

**New to git collaboration?** See [`docs/guides/git-for-newbies.md`](docs/guides/git-for-newbies.md) for fundamentals:
- `git pull` vs `git fetch` explained
- Feature branch relationships
- Multi-developer sync strategies

### ⚠️ GitHub CLI: Common Mistakes to Avoid

**CRITICAL:** The `gh pr view` command does NOT have a `merged` field!

**❌ WRONG (This will error):**
```bash
gh pr view 7 --json merged,state  # Error: Unknown JSON field: "merged"
```

**✅ CORRECT:**
```bash
# Check if PR is merged
gh pr view 7 --json state,mergedAt --jq '{state: .state, mergedAt: .mergedAt}'

# Check merge status
gh pr view 7 --json state --jq .state  # Returns: "MERGED", "OPEN", or "CLOSED"
```

**Available PR fields:**
- `mergedAt` (timestamp when merged)
- `mergedBy` (who merged it)
- `state` (OPEN, MERGED, CLOSED)
- `mergeCommit` (merge commit SHA)

**Never use `--admin` flag unless absolutely necessary** - it bypasses branch protection and should only be used for genuine emergencies, not convenience.

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
