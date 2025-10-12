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

## LangChain v1.0 Integration Patterns

**IMPORTANT:** When building new features that use LangChain, follow v1.0 patterns exclusively.

### Current Status (2025-10-12)
- RMAgent has **ZERO active LangChain imports** - custom tool wrappers are standalone
- LangChain v1.0 upgrade planned after Phase 5 (Testing) & Phase 6 (Documentation)
- See `docs/RM11_LangChain_Upgrade.md` for complete migration plan

### v1.0 Breaking Changes Reference

All new LangChain code MUST use v1.0 patterns:

| **Feature** | **❌ 0.3.x (Don't Use)** | **✅ v1.0 (Required)** |
|------------|------------------------|---------------------|
| Agent creation | `create_react_agent()` | `create_agent()` |
| Agent prompts | `prompt=ChatPromptTemplate(...)` | `system_prompt="string"` |
| Pre-bound tools | `llm.bind_tools(tools)` | Pass tools to agent directly |
| Hooks | `pre_model_hook`, `post_model_hook` | Use middleware/callbacks |
| State schema | Any dict-like or Pydantic | **Only `TypedDict`** |
| Context passing | `config["configurable"]` | `context=` parameter |

**Reference:** https://docs.langchain.com/oss/python/migrate/langchain-v1

### Tool Implementation Pattern (v1.0)

Place new LangChain tools in `rmagent/agent/lc/tools.py`:

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# Simple decorator-based tool
@tool
def query_person(person_id: int) -> dict:
    """Return person details from RootsMagic database.

    Args:
        person_id: PersonID from RootsMagic database
    """
    query_service = get_query_service()
    return query_service.get_person_with_primary_name(person_id)

# Class-based tool with structured I/O
class QueryPersonInput(BaseModel):
    person_id: int = Field(description="PersonID from RootsMagic")

class QueryPersonTool(BaseTool):
    name: str = "query_person"
    description: str = "Return person details"
    args_schema: type[BaseModel] = QueryPersonInput
    query_service: QueryService

    def _run(self, person_id: int) -> dict:
        return self.query_service.get_person_with_primary_name(person_id)
```

### Agent Creation Pattern (v1.0)

Place new agents in `rmagent/agent/lc/agents.py`:

```python
from langchain import create_agent  # v1.0 API
from langchain.agents import AgentExecutor
from langchain_anthropic import ChatAnthropic

def create_research_agent(model: str = "claude-3-5-sonnet-20241022"):
    """Create genealogy research agent with v1.0 patterns."""

    llm = ChatAnthropic(model=model)
    tools = [query_person, get_events, search_database]

    # v1.0: String system prompt (not ChatPromptTemplate)
    system_prompt = """You are a professional genealogist.

    Guidelines:
    - Always cite sources (PersonID, EventID)
    - Flag uncertainties and conflicts
    - Suggest follow-up research when needed
    """

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt  # v1.0 pattern
    )

    return AgentExecutor(agent=agent, tools=tools, verbose=True)
```

### LCEL Chain Pattern (v1.0)

Place chains in `rmagent/agent/lc/chains.py`:

```python
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_anthropic import ChatAnthropic

# Chain composition
census_extraction_chain = (
    {
        "ocr_text": RunnablePassthrough(),
        "person_context": lambda x: get_person_context(x["person_id"]),
    }
    | census_prompt
    | ChatAnthropic(model="claude-3-5-sonnet-20241022")
    | PydanticOutputParser(pydantic_object=CensusRecord)
)

# Usage
result = census_extraction_chain.invoke({
    "ocr_text": "John Smith 45 Pennsylvania...",
    "person_id": 123
})
```

### State Management Pattern (v1.0)

**Critical:** State MUST be `TypedDict`, not Pydantic models:

```python
from typing import TypedDict, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph

# ✅ Correct: TypedDict state
class ResearchState(TypedDict):
    messages: Sequence[BaseMessage]
    person_id: int
    research_notes: str
    census_records: list[dict]

# ❌ Wrong: Pydantic model (deprecated in v1.0)
class ResearchState(BaseModel):  # DON'T USE THIS
    messages: list[BaseMessage]
    person_id: int

# Define workflow
workflow = StateGraph(ResearchState)
```

### Observability Pattern (v1.0)

Place callbacks in `rmagent/agent/lc/callbacks.py`:

```python
from langchain_core.callbacks import BaseCallbackHandler
import json
from pathlib import Path

class RMAgentCallbackHandler(BaseCallbackHandler):
    """Log LLM interactions to llm_debug.jsonl."""

    def __init__(self, log_path: Path = Path("logs/llm_debug.jsonl")):
        self.log_path = log_path

    def on_llm_start(self, serialized, prompts, **kwargs):
        self._log({"event": "llm_start", "prompts": prompts})

    def on_llm_end(self, response, **kwargs):
        self._log({"event": "llm_end", "response": response.text})

    def _log(self, data: dict):
        with self.log_path.open("a") as f:
            json.dump(data, f)
            f.write("\n")

# Usage
agent = create_research_agent()
result = agent.invoke(
    {"input": "Find census records..."},
    callbacks=[RMAgentCallbackHandler()]
)
```

### Architecture Guidelines

**Directory Structure:**
```
rmagent/agent/
├── llm_provider.py      # Keep - used by non-LangChain features
├── genealogy_agent.py   # Keep - used by existing CLI
├── legacy_tools.py      # Renamed from tools.py (non-breaking)
├── prompts.py           # Keep - used by both approaches
└── lc/                  # NEW: LangChain v1.0 integration
    ├── tools.py         # v1.0 BaseTool implementations
    ├── chains.py        # LCEL Runnable chains
    ├── agents.py        # v1.0 agent configurations
    └── callbacks.py     # Custom observability
```

**When to Use LangChain vs Legacy:**
- **Use legacy code:** Existing CLI commands, simple workflows, non-agentic tasks
- **Use LangChain v1.0:** Census extraction, multi-step research, RAG, agentic workflows

**Testing Requirements:**
- All LangChain tools must have unit tests in `tests/unit/test_lc_*.py`
- Integration tests for agents in `tests/integration/test_lc_agents.py`
- Maintain 80%+ coverage for all new LangChain code

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
