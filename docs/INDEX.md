# RMAgent Documentation Index

**Version**: 1.0
**Last Updated**: 2025-10-15

This is the master table of contents for all RMAgent documentation. All paths are relative to the `docs/` directory.

---

## Quick Links

- [Installation Guide](getting-started/installation.md) - Get RMAgent installed
- [Quick Start](getting-started/quickstart.md) - 5-minute getting started guide
- [User Guide](guides/user-guide.md) - Complete CLI reference
- [Developer Guide](guides/developer-guide.md) - Contributing and development setup
- [FAQ](faq.md) - Frequently asked questions

---

## 📚 Documentation Structure

### Getting Started

New users start here:

- **[installation.md](getting-started/installation.md)** - Installation instructions (uv, dependencies, database setup)
- **[quickstart.md](getting-started/quickstart.md)** - 5-minute tutorial with first commands
- **[configuration.md](getting-started/configuration.md)** - Environment configuration and API keys

### User Guides

Complete guides for using RMAgent:

- **[user-guide.md](guides/user-guide.md)** - Complete CLI command reference and usage patterns
- **[faq.md](faq.md)** - Frequently asked questions and troubleshooting

### Developer Guides

For contributors and developers:

- **[developer-guide.md](guides/developer-guide.md)** - Architecture, coding standards, development setup
- **[testing-guide.md](guides/testing-guide.md)** - Running tests, writing tests, coverage
- **[git-workflow.md](guides/git-workflow.md)** - Branching strategy, commit conventions, PR process
- **[claude-code-setup.md](guides/claude-code-setup.md)** - Claude Code slash commands and hooks configuration

### Reference Documentation

Technical reference materials:

#### Schema & Database
- **[reference/schema/](reference/schema/)** - RootsMagic 11 database schema documentation
  - `schema-reference.md` - Complete table and field reference
  - `annotated-schema.sql` - Annotated SQL schema
  - `data-definitions.yaml` - Field enumerations and constraints
  - `relationships.md` - Parent-child and family relationships

#### Data Formats
- **[reference/data-formats/](reference/data-formats/)** - RootsMagic data format specifications
  - `date-format.md` - 24-character date encoding (CRITICAL)
  - `place-format.md` - Comma-delimited place hierarchy
  - `blob-fields.md` - UTF-8 XML BLOB parsing (sources, citations, templates)
  - `fact-types.md` - 65 built-in event types

#### Query Patterns
- **[reference/query-patterns/](reference/query-patterns/)** - SQL query patterns and best practices
  - `query-patterns.md` - 15 optimized query patterns
  - `rmnocase-collation.md` - ICU extension for case-insensitive text matching
  - `data-quality-rules.md` - 24 validation rules across 6 categories

#### Biography
- **[reference/biography/](reference/biography/)** - Biography generation reference
  - `biography-best-practices.md` - 9-section structure, citation styles
  - `timeline-construction.md` - TimelineJS3 JSON generation

### Active Projects

Point-in-time feature work and planning documents:

#### AI Agent Development
- **[projects/ai-agent/](projects/ai-agent/)**
  - `roadmap.md` - AI agent development roadmap (phases 1-7)
  - `langchain-upgrade.md` - LangChain 1.0 migration plan
  - `multi-agent-plan.md` - Multi-agent architecture design

#### Census Extraction
- **[projects/census-extraction/](projects/census-extraction/)**
  - `architecture.md` - Census extraction system architecture
  - `implementation-plan.md` - Step-by-step implementation plan

#### Biography & Citations
- **[projects/biography-citations/](projects/biography-citations/)**
  - `citation-implementation.md` - Citation processing implementation
  - `married-name-search.md` - Married name search optimization

### Archive

Completed milestones and historical documentation:

- **[archive/checkpoints/](archive/checkpoints/)** - Milestone completion documents
  - `mvp-checkpoint.md` - MVP milestone (Phases 1-6 complete)
  - `phase-5-completion.md` - Testing & quality phase
  - `phase-6-completion.md` - Documentation phase

- **[archive/summaries/](archive/summaries/)** - Implementation summaries
  - `integration-testing-summary.md` - Integration test implementation
  - `optimization-summary.md` - Performance optimization work
  - `test-coverage-analysis.md` - Coverage improvement analysis

### Root Documentation

Key files in the repository root (not in docs/):

- **[CLAUDE.md](../CLAUDE.md)** - AI assistant context and project guide
- **[AGENTS.md](../AGENTS.md)** - LangChain patterns and multi-agent architecture
- **[README.md](../README.md)** - Repository entry point and quick start
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Contribution guidelines
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history and release notes

---

## 🎯 For Claude Code and AI Assistants

When working on this codebase:

1. **Start with**: `CLAUDE.md` (root) for project context and guidelines
2. **Schema questions**: `reference/schema/schema-reference.md`
3. **Data parsing**: `reference/data-formats/` (especially `date-format.md`)
4. **Query patterns**: `reference/query-patterns/query-patterns.md`
5. **Active work**: `projects/` subdirectories for current feature development
6. **Testing**: `guides/testing-guide.md`

---

## 📝 Documentation Maintenance

### Keeping Docs Current

- **Active work** → `projects/` (move to `archive/` when complete)
- **Completed milestones** → `archive/checkpoints/`
- **Implementation notes** → `archive/summaries/`
- **Update INDEX.md** when adding/moving documentation

### Naming Conventions

- **Directories**: `lowercase-with-hyphens/`
- **Files**: `lowercase-with-hyphens.md`
- **Be descriptive**: `installation.md` not `install.md`
- **No abbreviations** unless universally known (e.g., `faq.md` is OK)

### Where Does It Go?

| Content Type | Location | Example |
|--------------|----------|---------|
| User-facing guides | `guides/` | CLI reference, tutorials |
| Installation/setup | `getting-started/` | Installation, configuration |
| Technical reference | `reference/` | Schema, formats, patterns |
| Active feature work | `projects/{feature}/` | Planning, architecture docs |
| Completed work | `archive/` | Checkpoints, summaries |
| General questions | `faq.md` | Common issues, how-tos |

---

## 🔗 External Resources

- **Repository**: https://github.com/miams/rmagent
- **RootsMagic**: https://www.rootsmagic.com/
- **SQLite**: https://www.sqlite.org/docs.html
- **LangChain**: https://python.langchain.com/

---

**Need help?** Check [faq.md](faq.md) or open an issue on GitHub.
