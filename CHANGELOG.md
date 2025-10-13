# Changelog

All notable changes to RMAgent will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Phase 6 comprehensive documentation suite (INSTALL.md, USAGE.md, CONFIGURATION.md, FAQ.md, EXAMPLES.md)
- Developer documentation (CONTRIBUTING.md, TESTING.md, ARCHITECTURE.md, API.md)
- Biography enhancement: Primary portrait images with text wrapping in introduction section
- Biography enhancement: Additional images displayed in Photos section
- Biography enhancement: Death information (date, place, age) in introduction paragraph
- Biography enhancement: Updated title format to "# Biography of [Name] ([birth_year]-[death_year])"

### Changed
- **Major refactoring:** Biography generator modularized from single 1,400-line file to 5 focused modules:
  - `biography/models.py` - Data models & enums (195 lines)
  - `biography/generator.py` - Main generator class (635 lines)
  - `biography/rendering.py` - Markdown rendering (220 lines)
  - `biography/citations.py` - Citation processing (308 lines)
  - `biography/templates.py` - Template generation (231 lines)
- **Major refactoring:** Genealogy agent and query service modularized for better organization:
  - `rmlib/sql_queries.py` - SQL query constants extracted from queries.py (541 lines)
  - `rmlib/queries.py` - Query service class reduced from 1,076 to 581 lines (-46%)
  - `agent/formatters.py` - Formatting utilities extracted from genealogy_agent.py (505 lines)
  - `agent/genealogy_agent.py` - Agent orchestration reduced from 735 to 289 lines (-61%)
- Improved maintainability: Each module now has a single, clear responsibility
- Enhanced testability: Components can be tested independently
- Better extensibility: Easy to add new renderers or citation styles
- Updated DEVELOPER_GUIDE.md to reflect new modular biography structure

### Fixed
- Python syntax warning in docstring (added raw string prefix)

### Test Coverage
- All 418 tests passing after refactoring
- Biography modules: generator (88%), models (90%), rendering (71%), citations (68%), templates (63%)
- Refactored modules: genealogy_agent (84%), queries (91%), formatters (included in agent coverage)
- Overall: 82% coverage across codebase

## [0.2.0] - 2025-10-12 - Phase 5 Complete

### Added
- Integration tests for multi-provider LLM system (19 tests total)
  - 12 mock-based integration tests (fast, free)
  - 7 real API tests with auto-skip for missing credentials
- Persistent result caching for expensive quality validation tests (110x speedup)
- Pytest markers for selective test execution (`real_api`, `anthropic_api`, `openai_api`, `ollama_api`, `slow`)
- Test coverage analysis documentation (docs/Test_Coverage_Analysis.md)
- Integration testing summary documentation (docs/INTEGRATION_TESTING_SUMMARY.md)
- Real API verification documentation (docs/REAL_API_VERIFICATION.md)
- Optimization summary documentation (docs/OPTIMIZATION_SUMMARY.md)
- Phase 5 completion report (docs/PHASE_5_COMPLETION.md)

### Changed
- Optimized Rule 5.1 date validation using SQL SUBSTR() instead of Python parsing (200x speedup)
- Updated pyproject.toml with pytest markers configuration
- Quality test fixture now uses persistent caching (tests/unit/conftest.py)

### Fixed
- Timeline.py bug: empty event list handling
- All Black formatting issues (4 files)
- All Ruff linting errors (57 issues across 8 files)
- Test timeout issues (quality tests now complete in <30s with caching)

### Performance
- Quality test execution: 41s → 0.35s (cached runs, 110x speedup)
- Rule 5.1 validation: 8-10s → 0.04s (200x speedup)
- Eliminated 33,841 expensive parse_rm_date() Python calls

### Test Coverage
- Total tests: 279 (260 unit + 19 integration)
- llm_provider.py: 76% → 90% (+14%)
- quality.py: 91% (SQL-optimized, highly tested)
- database.py: 76%
- Overall: 27% (high coverage on critical modules)

## [0.1.0] - 2025-10-10 - MVP (Milestone 2)

### Added
- Phase 4: Complete CLI interface with 8 commands
  - `person` command with --events, --family, --ancestors, --descendants options
  - `bio` command with --length, --citation-style, --no-ai, --no-sources options
  - `quality` command with --category, --severity, --format filters
  - `ask` command with --interactive conversation mode
  - `timeline` command with --format, --group-by-phase, --include-family options
  - `export` command for Hugo blog export with --batch-ids and --all options
  - `search` command with --name, --place, --limit, --exact options
- Rich terminal formatting for all CLI commands
- Progress indicators for long operations
- Comprehensive CLI help text for all commands
- CLI integration tests (23 tests, 100% pass rate)

### Changed
- Fixed agent instantiation bugs in bio.py, ask.py, timeline.py
- Fixed CLIContext.load_config() parameter naming
- Updated all CLI commands to use correct config attribute names
- Improved error handling and user feedback across CLI

### Documentation
- docs/MVP_CHECKPOINT.md - Milestone 2 verification report
- docs/USER_GUIDE.md - Complete user documentation
- docs/RMAgent_User_Guide.pdf - PDF version of user guide

### Test Coverage
- CLI commands: 68-100% coverage (varies by command)
- Integration tests: 23 passing tests

## [0.0.5] - 2025-10-09 - Phase 3 Complete

### Added
- Phase 3: Output generators
  - Biography generator with 9-section structure (24 tests, 85% coverage)
  - Data quality report generator with Markdown/HTML/CSV formats (13 tests, 95% coverage)
  - Timeline generator with TimelineJS3 JSON/HTML output (29 tests, 90% coverage)
  - Hugo blog exporter with batch support (24 tests, 91% coverage)
- BiographyLength enum (SHORT, STANDARD, COMPREHENSIVE)
- CitationStyle enum (FOOTNOTE, PARENTHETICAL, NARRATIVE)
- LifePhase enum for timeline grouping (8 life phases)
- TimelineFormat enum (JSON, HTML)
- Privacy filtering (IsPrivate flags + 110-year rule)

### Test Coverage
- Biography generator: 24 tests, 85% coverage
- Quality report: 13 tests, 95% coverage
- Timeline generator: 29 tests, 90% coverage
- Hugo exporter: 24 tests, 91% coverage

## [0.0.4] - 2025-10-09 - Phase 2 Complete

### Added
- Phase 2: AI Integration
  - Multi-provider LLM abstraction (Anthropic, OpenAI, Ollama)
  - Configuration management with Pydantic settings
  - Prompt template registry with versioning
  - GenealogyAgent with biography/Q&A/quality workflows
  - LangChain-style tools for agent interactions
- Retry logic and rate limiting for LLM providers
- Token usage and cost tracking
- LLM debug logging to logs/llm_debug.jsonl
- Unit tests for LLM providers, config, prompts, agent, tools

### Test Coverage
- llm_provider.py: 76% coverage (before integration tests)
- config.py: Basic coverage
- prompts.py: 68% coverage
- agent.py: Minimal coverage (4 tests)

## [0.0.3] - 2025-10-09 - Phase 1 Complete (Milestone 1)

### Added
- Phase 1: Foundation (Core Library)
  - Database connection module with RMNOCASE collation support (17 tests, 97% coverage)
  - Pydantic data models for 8 RootsMagic tables (34 tests, 95% coverage)
  - Date parser for 24-char RM11 format (44 tests, 93% coverage)
  - BLOB parsers for XML source/citation/template fields (24 tests, 91% coverage)
  - Place parser for comma-delimited hierarchy (55 tests, 99% coverage)
  - Name parser with primary/alternate selection (34 tests, 96% coverage)
  - Query service with 15 optimized SQL patterns (16 tests, 91% coverage)
  - Data quality validator with 24 validation rules across 6 categories
- RMDatabase class with context manager protocol
- SQLite ICU extension integration (RMNOCASE collation)
- Prototype script: `uv run python -m rmagent.rmlib.prototype`

### Test Coverage
- Total: 229 unit tests
- Coverage: 91-99% across foundation modules
- All tests passing

### Milestone 1 - Working Prototype
- ✅ Query person with complete data
- ✅ Display events with dates, places, citations
- ✅ Generate basic biography (template-based)
- ✅ Run all 24 data quality validation rules
- ✅ Identify 49,057 issues across 6 categories in test database

## [0.0.2] - 2025-10-08 - Documentation Complete

### Added
- Comprehensive schema documentation (18 files in data_reference/)
  - RM11_Schema_Reference.md - Complete database schema
  - RM11_Date_Format.md - 24-character date encoding
  - RM11_BLOB_*.md - XML BLOB parsing specifications
  - RM11_Query_Patterns.md - 15 optimized SQL patterns
  - RM11_Biography_Best_Practices.md - 9-section structure
  - RM11_Data_Quality_Rules.md - 24 validation rules
  - ... and 12 more specification documents
- docs/VALIDATION_RESULTS.md - Validation of all specifications
- docs/DATA_PARSING_TODO.md - Parsing implementation checklist
- Sample database (data/Iiams.rmtree) - 11,571 persons, 29,543 events

## [0.0.1] - 2025-01-08 - Initial Setup

### Added
- Project structure with uv package manager
- pyproject.toml with dependencies
- .gitignore with database file exclusions
- README.md with project overview
- SQLite ICU extension (sqlite-extension/icu.dylib for macOS)
- Initial phase planning (docs/AI_AGENT_TODO.md)

### Dependencies
- Python 3.11+ requirement
- Core: pydantic, python-dotenv, click, rich, jinja2, pyyaml
- AI: anthropic, openai, ollama-python, langchain
- Testing: pytest, pytest-cov, pytest-mock
- Dev: black, ruff, mypy

---

## Version History Summary

- **v0.2.0** (2025-10-12): Phase 5 complete - Testing & Quality
- **v0.1.0** (2025-10-10): Milestone 2 (MVP) - All 8 CLI commands working
- **v0.0.5** (2025-10-09): Phase 3 complete - Output generators
- **v0.0.4** (2025-10-09): Phase 2 complete - AI integration
- **v0.0.3** (2025-10-09): Milestone 1 complete - Working prototype
- **v0.0.2** (2025-10-08): Documentation complete
- **v0.0.1** (2025-01-08): Initial project setup

---

## Semantic Versioning

Given a version number MAJOR.MINOR.PATCH:

- **MAJOR**: Incompatible API changes
- **MINOR**: Add functionality (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

## Release Schedule

- **Patch releases:** As needed for bug fixes
- **Minor releases:** Monthly (new features)
- **Major releases:** When breaking changes are necessary

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute changes.

## Links

- **Repository:** https://github.com/miams/rmagent
- **Issues:** https://github.com/miams/rmagent/issues
- **Discussions:** https://github.com/miams/rmagent/discussions
