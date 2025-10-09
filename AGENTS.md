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
