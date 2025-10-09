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

All commands use the `uv run` prefix to run in the virtual environment:

### Query a Person

```bash
uv run rmagent person 1 --events
```

### Generate a Biography

```bash
uv run rmagent bio 1 --length standard --output bio.md
```

### Run Data Quality Checks

```bash
uv run rmagent quality --severity critical
```

### Ask Questions

```bash
uv run rmagent ask "Who were John Smith's parents?"
```

### Create Timeline

```bash
uv run rmagent timeline 1 --output timeline.json
```

### Export to Hugo

```bash
uv run rmagent export hugo 1 --output-dir content/people
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

Comprehensive documentation is available in the `data_reference/` directory:

- **RM11_Schema_Reference.md** - Complete database schema
- **RM11_Query_Patterns.md** - Optimized SQL query patterns
- **RM11_Biography_Best_Practices.md** - Biography writing guidelines
- **RM11_Data_Quality_Rules.md** - All 24 validation rules
- **RM11_Documentation_Index.md** - Master index of all 18 docs

See `docs/AI_AGENT_TODO.md` for the complete development roadmap.

## Status

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

**📍 Phase 4: CLI Interface - IN PROGRESS (2/8 tasks)**
- ✅ CLI Framework (Click + Rich, global options, 7 command modules, 23 tests)
- ✅ Person Command (query person with --events, --family, --ancestors, --descendants)
- ⏭️ Command implementations (bio, quality, ask, timeline, export, search)

**⏭️ Next Tasks:** Complete Phase 4 CLI command implementations (Tasks 4.3-4.8)

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
