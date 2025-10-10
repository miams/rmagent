# Repository Guidelines
This repository curates documentation and sample datasets for analyzing the RootsMagic 11 SQLite schema. Keep contributions focused on verifiable reference material and reproducible data work.

## Project Structure & Module Organization
- `data_reference/` holds canonical schema narratives, SQL definitions, and YAML mappings; extend these files instead of forking new formats.
- `data/` contains sanitized working databases such as `Iiams.rmtree`; treat it as the primary fixture for experiments.
- `docs/` tracks open research tasks; close the loop by updating the relevant checklist when you deliver.
- `archive/` preserves vendor-source artifacts for citation; never edit these files, but cite them when deriving new material.
- `reports/` is reserved for generated summaries or inventories like `template_sources_list.txt`.

## Build, Test, and Development Commands
- `sqlite3 data/Iiams.rmtree ".tables"` confirms table coverage when documenting schema updates.
- `sqlite3 data/Iiams.rmtree < scripts/query.sql` runs reproducible query suites; include the script you reference.
- `bash tools/export_schema.sh` (create if needed) should wrap any repeatable extraction so future agents can rerun it unchanged.
- Use [Astral's `uv`](https://github.com/astral-sh/uv) for Python dependency management, environment activation, and running Python/pytest commands (`uv run`, `uv pip`, etc.).
- Prefer invoking shared orchestration layers (`rmagent/agent/genealogy_agent.py`, `rmagent/agent/tools.py`, `rmagent/agent/prompts.py`) rather than duplicating bespoke prompt or database wiring.

## Coding Style & Naming Conventions
- Markdown: start documents with a single `#` heading, follow with sentence-case section titles, and include intra-doc tables of contents only when exceeding three sections.
- File names: use the `RM11_*` prefix and UpperCamel underscore pattern (`RM11_BLOB_SourceFields.md`) to align with existing references.
- SQL and YAML: indent continuation lines by two spaces, uppercase SQL keywords, and place one clause per line for readability.

## Testing Guidelines
Document every data claim with the query or script that produced it, either inline code blocks or linked `.sql` files. When defining new parsing logic, add a minimal reproducible example drawn from `Iiams.rmtree` and note any assumptions about collations or date encodings.

## Commit & Pull Request Guidelines
Adopt Conventional Commit prefixes (`docs:`, `data:`, `refactor:`) followed by concise imperatives. Each pull request should summarize the covered tables or BLOB structures, link to the motivating issue or TODO entry, and attach diffs or screenshots when inspecting generated reports. Mention any manual validation steps in the PR body so reviewers can replicate them quickly.

## Data Handling & Security Tips
Only commit sanitized genealogical data; scrub personal details before adding fixtures. Reference sensitive upstream files from `archive/` rather than copying content into editable areas. When ingesting new datasets, note provenance, anonymization steps, and storage location so downstream agents can audit compliance.

## Observability
- Set `LOG_LEVEL=DEBUG` in `config/.env` to stream verbose logs.
- LLM prompt/response JSON traces (prompt text, completion, provider, model, token totals, latency) write to `LLM_DEBUG_LOG_FILE` (default `logs/llm_debug.jsonl`) for reproducible debugging.

## Current Implementation Status (2025-10-10)

🎉 **MILESTONE 2: MVP (Minimum Viable Product) - ACHIEVED!**

All 26 foundation tasks complete. See [docs/MVP_CHECKPOINT.md](docs/MVP_CHECKPOINT.md) for verification report.

### Completed Phases
- **Phase 1: Foundation** (9/9 tasks) ✅ - Database access, parsers, queries, quality validation
- **Phase 2: AI Integration** (5/5 tasks) ✅ - Multi-LLM support, prompts, agent core, LangChain tools
- **Phase 3: Output Generators** (4/4 tasks) ✅ - Biography, quality reports, timelines, Hugo export
- **Phase 4: CLI Interface** (8/8 tasks) ✅ - Command-line interface (COMPLETE)

### Next Phase
- **Phase 5: Testing & Quality** (0/4 tasks) ⏭️ - Increase test coverage to 80%, integration tests, code quality

### Available CLI Commands
All commands use `uv run rmagent [command]` prefix:

- **`person <id>`** - Query person information with optional flags:
  - `--events` - Show all life events
  - `--family` - Show immediate family (parents, spouses, children)
  - `--ancestors` - Show ancestor tree (default 3 generations)
  - `--descendants` - Show descendant tree

- **`bio <id>`** - Generate biographies:
  - `--length` (short/standard/comprehensive)
  - `--citation-style` (footnote/parenthetical/narrative)
  - `--no-ai` - Template-based generation (no LLM required)
  - `--output` - Save to file

- **`quality`** - Run data quality validation (24 rules):
  - `--category` - Filter by category (required/logical/integrity/sources/dates/values)
  - `--severity` - Filter by severity (critical/high/medium/low)
  - `--format` - Output format (markdown/html/csv)
  - `--output` - Save to file

- **`ask <question>`** - Interactive Q&A (requires LLM):
  - `--interactive` - Conversation mode with memory

- **`timeline <id>`** - Generate interactive timelines:
  - `--format` (json/html) - JSON for embedding or HTML for standalone viewer
  - `--group-by-phase` - Group events by life phases
  - `--include-family` - Include spouse/children events
  - `--output` - Save to file

- **`export hugo <id>`** - Export to Hugo blog format:
  - `--output-dir` - Output directory for Hugo content
  - `--bio-length` (short/standard/comprehensive)
  - `--include-timeline` - Include timeline files (default: true)
  - `--batch-ids` - Export multiple persons (comma-separated IDs)
  - `--all` - Export all persons in batch mode

- **`search`** - Search database by name/place with phonetic matching (✅ COMPLETE)

### Testing Status
- **Total Unit Tests:** 245+ tests across 18 modules
- **Test Coverage:** 30-99% across components (85%+ for generators, 68-88% for CLI commands)
- **Test Framework:** pytest with coverage reporting (`uv run pytest --cov=rmagent`)

### Next Development Tasks
1. ✅ Complete `search` command implementation (Task 4.8) - COMPLETE
2. Comprehensive integration testing (Phase 5)
3. User documentation (Phase 6)
4. Production polish and enhancements (Phase 7)

See `docs/AI_AGENT_TODO.md` for detailed roadmap and progress tracking.
