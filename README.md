# RMAgent - AI-Powered Genealogy Agent for RootsMagic

AI-powered command-line tool for analyzing RootsMagic databases, generating biographies, and conducting genealogical research.

## Features

- 🔍 **Data Quality Analysis** - Run 24 validation rules to identify issues
- 📝 **Biography Generation** - AI-generated biographical narratives with proper sourcing
- 👪 **Family Insights** - Spouse, child, and sibling context (births, migrations, losses) injected into AI prompts
- 💬 **Interactive Q&A** - Ask questions about people and families in your database
- 📅 **Timeline Creation** - Generate interactive timelines (TimelineJS3 format)
- 📤 **Hugo Blog Export** - Export biographies as Hugo-compatible blog posts

## Requirements

- Python 3.11+
- RootsMagic 11 database (.rmtree file)
- SQLite ICU extension (included in `sqlite-extension/` for macOS)
- API key for at least one LLM provider:
  - Anthropic (Claude)
  - OpenAI (GPT-4)
  - Ollama (local models)

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for fast Python package management.

### Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Clone and Install

```bash
# Clone the repository
git clone git@github.com:miams/rmagent.git
cd rmagent

# Install dependencies
uv sync
```

**Note:** SSH access requires `ssh-add ~/.ssh/miams-github` for authentication.

This creates a virtual environment in `.venv/` and installs all dependencies.

### Install Development Dependencies

```bash
uv sync --extra dev
```

## Configuration

1. Copy the example environment file:

```bash
cp config/.env.example config/.env
```

2. Edit `config/.env` and add your API keys:

```bash
# Choose your LLM provider
DEFAULT_LLM_PROVIDER=anthropic  # or openai, ollama
LLM_TEMPERATURE=0.2
LLM_MAX_TOKENS=1024

# Add your API key
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Set database path
RM_DATABASE_PATH=data/Iiams.rmtree

# Logging options
LOG_LEVEL=INFO                # set DEBUG to capture JSON traces
LLM_DEBUG_LOG_FILE=logs/llm_debug.jsonl
```

### Programmatic access

Use the configuration helper when building integrations:

```python
from rmagent.config.config import load_app_config

config = load_app_config()
provider = config.build_provider()  # Anthropic/OpenAI/Ollama based on config/.env
db_path = config.database.database_path

from rmagent.agent.prompts import render_prompt
biography_prompt = render_prompt(
    "biography",
    {
        "person_summary": "...",
        "timeline_overview": "...",
        "relationship_notes": "...",
        "source_notes": "...",
    },
)

from rmagent.agent.genealogy_agent import GenealogyAgent
from rmagent.agent.tools import default_langchain_tools
from rmagent.rmlib.database import RMDatabase
from rmagent.rmlib.queries import QueryService
from rmagent.rmlib.quality import DataQualityValidator

with RMDatabase(db_path, extension_path=config.database.sqlite_extension_path) as db:
    query_service = QueryService(db)
    validator = DataQualityValidator(db)
    tools = default_langchain_tools(query_service, validator)

agent = GenealogyAgent(
    llm_provider=provider,
    db_path=db_path,
    extension_path=config.database.sqlite_extension_path,
)
biography = agent.generate_biography(person_id=1)
quality_summary = agent.analyze_data_quality()
```

### Debug logging and tracing

- Set `LOG_LEVEL=DEBUG` in `config/.env` to enable verbose logs.
- LLM prompts/responses (model, provider, tokens, latency, prompt text, completion text) are written as JSON lines to `LLM_DEBUG_LOG_FILE` (default `logs/llm_debug.jsonl`).
- Configure `LLM_MAX_TOKENS` to raise or lower the default response limit used by providers.

## Usage

### CLI Setup Options

**Option 1: Direct Access (Recommended)**
Run `./setup_cli.sh` to enable direct CLI access and tab completion. See [docs/CLI_SETUP.md](docs/CLI_SETUP.md) for details.

After setup, use commands directly:
```bash
rmagent person 1          # Direct access
rmagent <TAB>             # Tab completion works!
```

**Option 2: Using uv run**
All commands can use the `uv run rmagent` prefix:

### Query a Person

```bash
# Basic person info
uv run rmagent person 1

# With all events
uv run rmagent person 1 --events

# With family information (parents, spouses, children)
uv run rmagent person 1 --family

# With ancestors (default: 3 generations)
uv run rmagent person 1 --ancestors

# With descendants
uv run rmagent person 1 --descendants
```

### Generate a Biography

```bash
# Basic biography (template-based, no AI required)
uv run rmagent bio 1 --no-ai

# AI-powered biography with different lengths
uv run rmagent bio 1 --length short
uv run rmagent bio 1 --length standard
uv run rmagent bio 1 --length comprehensive

# With different citation styles
uv run rmagent bio 1 --citation-style footnote
uv run rmagent bio 1 --citation-style parenthetical
uv run rmagent bio 1 --citation-style narrative

# Save to file
uv run rmagent bio 1 --output bio.md

# Without sources section
uv run rmagent bio 1 --no-sources
```

### Run Data Quality Checks

```bash
# Run all quality checks
uv run rmagent quality

# Filter by severity
uv run rmagent quality --severity critical
uv run rmagent quality --severity high

# Filter by category
uv run rmagent quality --category logical
uv run rmagent quality --category sources

# Generate different formats
uv run rmagent quality --format markdown --output quality.md
uv run rmagent quality --format html --output quality.html
uv run rmagent quality --format csv --output quality.csv

# Combined filters
uv run rmagent quality --category logical --severity high --output issues.md
```

### Ask Questions (Requires LLM)

```bash
# Single question
uv run rmagent ask "Who were John Smith's parents?"

# Interactive conversation mode
uv run rmagent ask --interactive
```

### Create Timeline

```bash
# Generate JSON timeline (for embedding)
uv run rmagent timeline 1 --output timeline.json

# Generate standalone HTML viewer
uv run rmagent timeline 1 --format html --output timeline.html

# Group by life phases
uv run rmagent timeline 1 --group-by-phase

# Include family member events
uv run rmagent timeline 1 --include-family
```

### Export to Hugo

```bash
# Export single person to Hugo blog format
uv run rmagent export hugo 1 --output-dir content/people

# Export with timeline included (default)
uv run rmagent export hugo 1 --output-dir content/people --include-timeline

# Export with different biography lengths
uv run rmagent export hugo 1 --output-dir content/people --bio-length comprehensive

# Export multiple people with batch IDs
uv run rmagent export hugo --batch-ids 1,2,3 --output-dir content/people

# Export all persons (large database warning)
uv run rmagent export hugo --all --output-dir content/people
```

### Search Database

The search command uses intelligent multi-strategy matching with support for:
- **Alternate names** (automatically included)
- **Married names** (with `--married-name` flag for women)
- **Surname variations** (with `[variant]` bracket syntax)
- **Multi-word searches** across name fields
- **Phonetic matching** fallback

```bash
# Search by surname (finds all matches)
uv run rmagent search --name "Smith"

# Search by full name (e.g., "John Smith" or "Lucy Virginia Dorsey")
# Automatically matches across surname and given name fields
uv run rmagent search --name "John Smith"
uv run rmagent search --name "Lucy Virginia Dorsey"

# Search with surname variations (bracket syntax)
uv run rmagent search --name "John Iiams [Ijams]"         # Searches "John Iiams" and "John Ijams"
uv run rmagent search --name "John Iams [Ijams] [Imes]"   # Searches 3 variations
uv run rmagent search --name "John [ALL]"                 # Searches all configured variants

# Search by first and middle name
uv run rmagent search --name "Lucy Virginia"

# Search by alternate name (e.g., "Janet Bross" finds person with primary name "Janet Casey")
uv run rmagent search --name "Janet Bross"

# Search by married name (e.g., "Janet Iiams" finds women who married someone named Iiams)
uv run rmagent search --name "Janet Iiams" --married-name

# Search by place
uv run rmagent search --name "Maryland"

# Limit results
uv run rmagent search --name "Smith" --limit 10

# Exact match only (no phonetic matching)
uv run rmagent search --name "Smith" --exact
```

**Surname Variations:**
The `[ALL]` keyword expands to configured variants (default: Iams, Iames, Iiams, Iiames, Ijams, Ijames, Imes, Eimes).
Configure custom variants in `config/.env`:
```bash
SURNAME_VARIANTS_ALL=Iams,Iames,Iiams,Iiames,Ijams,Ijames,Imes,Eimes
```

## Project Structure

```
RM11/
├── rmagent/              # Main package
│   ├── rmlib/          # Core library (database, parsers, queries)
│   ├── agent/          # AI agent (LLM providers, prompts)
│   ├── generators/     # Output generators (bio, timeline, hugo)
│   ├── cli/            # Command-line interface
│   └── config/         # Configuration
├── tests/              # Test suite
├── docs/               # Documentation
├── data/               # Database files
└── sqlite-extension/   # SQLite ICU extension for RMNOCASE
```

## LangChain Integration (Future Features)

**Status:** LangChain v1.0 upgrade planned after Phase 5 (Testing) & Phase 6 (Documentation) complete.

### Current LangChain Usage

RMAgent currently has **zero active LangChain imports**. Custom "LangChain-style" tool wrappers in `rmagent/agent/tools.py` provide a compatible interface but are standalone implementations.

### Future LangChain Features

When implementing new features using LangChain (census extraction, timeline enrichment, agentic research), follow **v1.0 patterns exclusively**:

#### Quick Start Example (v1.0 Pattern)

```python
from langchain import create_agent  # v1.0 API
from langchain.agents import AgentExecutor
from langchain_anthropic import ChatAnthropic
from rmagent.agent.lc.tools import query_person, get_events

def create_research_agent():
    """Create genealogy research agent (v1.0 pattern)."""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    tools = [query_person, get_events, search_database]

    # v1.0: String system prompt (not ChatPromptTemplate)
    system_prompt = """You are a professional genealogist.
    Always cite sources and flag uncertainties."""

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt  # v1.0 requirement
    )

    return AgentExecutor(agent=agent, tools=tools, verbose=True)

# Usage
agent = create_research_agent()
result = agent.invoke({
    "input": "Find census records for person 123"
})
```

### v1.0 Breaking Changes (Important!)

When LangChain v1.0 stable releases, use these patterns:

| **Feature** | **❌ 0.3.x (Don't Use)** | **✅ v1.0 (Required)** |
|------------|------------------------|---------------------|
| Agent creation | `create_react_agent()` | `create_agent()` |
| Agent prompts | `prompt=ChatPromptTemplate(...)` | `system_prompt="string"` |
| State schema | Pydantic models | **Only `TypedDict`** |
| Context passing | `config["configurable"]` | `context=` parameter |

**Reference:** https://docs.langchain.com/oss/python/migrate/langchain-v1

### Migration Plan

See `docs/RM11_LangChain_Upgrade.md` for complete upgrade strategy and timeline.

**Key Points:**
- New LangChain code goes in `rmagent/agent/lc/` directory
- Use v1.0 patterns from day one (no migration needed)
- Maintain 80%+ test coverage for all LangChain features
- See `AGENTS.md` for comprehensive best practices

## Development

### Run Tests

```bash
uv run pytest
```

### Check Code Quality

```bash
# Format code
uv run black .

# Lint code
uv run ruff check .

# Type checking
uv run mypy rmagent/
```

### Run with Coverage

```bash
uv run pytest --cov=rmagent --cov-report=html
```

## Documentation

**📚 Complete Documentation Index:** [docs/README.md](docs/README.md)

### For New Users

Start here to get up and running:

1. **[INSTALL.md](INSTALL.md)** - Installation guide (macOS, Linux, Windows/WSL2)
2. **[CONFIGURATION.md](CONFIGURATION.md)** - Configuration, LLM providers, prompt customization
3. **[USAGE.md](USAGE.md)** - Complete CLI reference with 50+ examples
4. **[FAQ.md](FAQ.md)** - Common questions and troubleshooting

**Comprehensive Guide:** [docs/USER_GUIDE.md](docs/USER_GUIDE.md) (31KB, all-in-one)

### For Developers

Start here to contribute or extend RMAgent:

1. **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Architecture, design patterns, API reference
2. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution workflow and coding standards
3. **[TESTING.md](TESTING.md)** - Testing guide (279 tests, coverage analysis)
4. **[CHANGELOG.md](CHANGELOG.md)** - Complete version history

### Additional Documentation

- **[AGENTS.md](AGENTS.md)** - Agent design patterns
- **[data_reference/](data_reference/)** - RootsMagic 11 schema (18 reference docs)
- **[docs/](docs/)** - Project documentation and completion reports

## Status

🎉 **Milestone 2: MVP (Minimum Viable Product) - ACHIEVED!**

**Date:** 2025-10-10
**Completion:** All 26 foundation tasks complete (Phases 1-4)
**Next Focus:** Testing & Quality improvements (Phase 5)

See [docs/MVP_CHECKPOINT.md](docs/MVP_CHECKPOINT.md) for complete verification report.

---

🎯 **Milestone 1: Working Prototype - COMPLETE!**

**✅ Phase 1: Foundation - COMPLETE (9/9 tasks)**
- ✅ Project setup (uv, dependencies, configuration)
- ✅ Database connection with RMNOCASE support
- ✅ Pydantic data models (Person, Name, Event, Place, Source, Citation, Family)
- ✅ Date parser (24-char RM11 format, 44 tests, 93% coverage)
- ✅ BLOB parsers (XML source/citation/template fields, 24 tests, 91% coverage)
- ✅ Place parser (comma-delimited hierarchy, 55 tests, 99% coverage)
- ✅ Name parser (primary/alternate/context-aware, 34 tests, 96% coverage)
- ✅ Query service (15 optimized patterns, 16 tests, 91% coverage)
- ✅ Data quality validator (24 validation rules across 6 categories)

**✅ Milestone 1: Working Prototype - COMPLETE (2025-10-09)**
- ✅ Query person with complete data (name, events, family)
- ✅ Display web links (Find a Grave, etc.)
- ✅ Display citations grouped by event with page numbers
- ✅ Display sources with formatted bibliographies (italics support)
- ✅ Generate basic biography (text-based, no AI yet)
- ✅ Run all 24 data quality validation rules
- ✅ Prototype script: `uv run python -m rmagent.rmlib.prototype --person-id 1 --check-quality`

**📊 Test Coverage:** 229 unit tests, 91-99% coverage across modules

**✅ Phase 2: AI Integration - COMPLETE (5/5 tasks)**
- ✅ LLM providers (Anthropic/OpenAI/Ollama) with retry/pricing
- ✅ Configuration management (`config/.env`, Pydantic settings)
- ✅ Prompt templates (biography, quality, Q&A, timeline)
- ✅ Agent core (GenealogyAgent with context builders)
- ✅ LangChain tools (query, events, validation, search)

**✅ Phase 3: Output Generators - COMPLETE (4/4 tasks)**
- ✅ Biography generator (9-section structure, AI-powered, 24 tests)
- ✅ Quality report generator (Markdown/HTML/CSV formats, 13 tests)
- ✅ Timeline generator (TimelineJS3 JSON/HTML, 29 tests)
- ✅ Hugo blog exporter (single/batch export, 24 tests)

**✅ Phase 4: CLI Interface - COMPLETE (8/8 tasks)**
- ✅ CLI Framework (Click + Rich, global options, 7 command modules)
- ✅ Person Command (query person with --events, --family, --ancestors, --descendants)
- ✅ Biography Command (all length/citation options, --no-ai mode, 8 tests, 88% coverage)
- ✅ Quality Command (category/severity filters, Rich tables, 8 tests)
- ✅ Ask Command (Q&A with conversation memory, 3 tests, 68% coverage, requires LLM)
- ✅ Timeline Command (JSON/HTML formats, --include-family, 7 tests, 78% coverage)
- ✅ Export Command (Hugo blog export with batch support, 8 tests, 74% coverage)
- ✅ Search Command (name/place search with phonetic matching, 8 tests, 88% coverage)

**⏭️ Next Tasks:** Phase 5 - Testing & Quality (comprehensive integration testing)

See `docs/AI_AGENT_TODO.md` for detailed progress and roadmap.

## Repository

- **GitHub:** https://github.com/miams/rmagent
- **Clone:** `git clone git@github.com:miams/rmagent.git`
- **SSH Key:** `ssh-add ~/.ssh/miams-github`

## License

MIT License - See LICENSE file for details

## Author

Michael Iams
- GitHub: https://github.com/miams
- Repository: https://github.com/miams/rmagent
