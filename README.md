# RMTool - AI-Powered Genealogy Agent for RootsMagic

AI-powered command-line tool for analyzing RootsMagic databases, generating biographies, and conducting genealogical research.

## Features

- 🔍 **Data Quality Analysis** - Run 24 validation rules to identify issues
- 📝 **Biography Generation** - AI-generated biographical narratives with proper sourcing
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
cp .env.example .env
```

2. Edit `.env` and add your API keys:

```bash
# Choose your LLM provider
DEFAULT_LLM_PROVIDER=anthropic  # or openai, ollama

# Add your API key
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Set database path
RM_DATABASE_PATH=data/Iiams.rmtree
```

## Usage

All commands use the `uv run` prefix to run in the virtual environment:

### Query a Person

```bash
uv run rmtool person 1 --events
```

### Generate a Biography

```bash
uv run rmtool bio 1 --length standard --output bio.md
```

### Run Data Quality Checks

```bash
uv run rmtool quality --severity critical
```

### Ask Questions

```bash
uv run rmtool ask "Who were John Smith's parents?"
```

### Create Timeline

```bash
uv run rmtool timeline 1 --output timeline.json
```

### Export to Hugo

```bash
uv run rmtool export hugo 1 --output-dir content/people
```

## Project Structure

```
RM11/
├── rmtool/              # Main package
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
uv run mypy rmtool/
```

### Run with Coverage

```bash
uv run pytest --cov=rmtool --cov-report=html
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

🚧 **Currently in development** - Working Prototype phase

**Progress:** Phase 1 Foundation - Tasks 1.1-1.8 complete (8/9)
- ✅ Database connection with RMNOCASE support
- ✅ Pydantic data models
- ✅ Date parser (24-char RM11 format)
- ✅ BLOB parsers (XML source/citation/template fields)
- ✅ Place parser (comma-delimited hierarchy)
- ✅ Name parser (primary/alternate, context-aware)
- ✅ Query service (15 optimized patterns)
- 🚧 Data quality validator (in progress)

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
