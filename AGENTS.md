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

### ⚠️ CRITICAL: Database File Policy

**NEVER commit database files to git!**

- `.gitignore` correctly excludes `*.rmtree` files - DO NOT override this
- **NEVER add exceptions** like `!data/Iiams.rmtree` to `.gitignore`
- Database files contain sensitive personal information (names, dates, relationships)
- Database files are large binary files unsuitable for version control
- Users maintain their own local database files in `data/` directory
- Document database structure in markdown/SQL, not by committing the actual database

## Observability
- Set `LOG_LEVEL=DEBUG` in `config/.env` to stream verbose logs.
- LLM prompt/response JSON traces (prompt text, completion, provider, model, token totals, latency) write to `LLM_DEBUG_LOG_FILE` (default `logs/llm_debug.jsonl`) for reproducible debugging.

## LangChain v1.0 Best Practices

**CRITICAL:** When adding LangChain features, use v1.0 patterns exclusively. RMAgent currently has zero active LangChain usage.

### Upgrade Status
- **Current:** LangChain 0.3.27 installed but unused
- **Target:** Upgrade to v1.0 after Phase 5 (Testing) & Phase 6 (Documentation)
- **Plan:** See `docs/RM11_LangChain_Upgrade.md` for complete strategy

### Agent Architecture Patterns

#### ✅ v1.0 Pattern: create_agent()
```python
from langchain import create_agent  # v1.0 API
from langchain.agents import AgentExecutor
from langchain_anthropic import ChatAnthropic
from rmagent.agent.lc.tools import query_person, get_events

def create_research_agent(model: str = "claude-3-5-sonnet-20241022"):
    """Create genealogy research agent (v1.0 pattern)."""
    llm = ChatAnthropic(model=model)
    tools = [query_person, get_events, search_database]

    # v1.0: String system prompt (not ChatPromptTemplate)
    system_prompt = """You are a professional genealogist.

    Guidelines:
    - Always cite sources (PersonID, EventID, census records)
    - Flag uncertainties and conflicting data
    - Suggest follow-up research when gaps exist
    """

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt  # v1.0 requirement
    )

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10
    )
```

#### ❌ 0.3.x Pattern (Don't Use)
```python
# DON'T USE THIS - Deprecated in v1.0
from langchain.agents import create_react_agent, initialize_agent

agent = create_react_agent(  # Renamed to create_agent() in v1.0
    llm=llm,
    tools=tools,
    prompt=ChatPromptTemplate(...)  # Changed to system_prompt string
)
```

### Tool Design Guidelines

#### Place Tools in `rmagent/agent/lc/tools.py`

**Decorator Pattern (Simple Tools):**
```python
from langchain_core.tools import tool

@tool
def query_person(person_id: int) -> dict:
    """Return person details from RootsMagic database.

    Args:
        person_id: PersonID from RootsMagic database
    """
    from rmagent.rmlib.database import RMDatabase
    from rmagent.rmlib.queries import QueryService

    with RMDatabase('data/Iiams.rmtree') as db:
        queries = QueryService(db)
        return queries.get_person_with_primary_name(person_id)
```

**Class Pattern (Structured I/O):**
```python
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

class QueryPersonInput(BaseModel):
    person_id: int = Field(description="PersonID from RootsMagic database")

class QueryPersonTool(BaseTool):
    name: str = "query_person"
    description: str = "Return person details from RootsMagic database"
    args_schema: type[BaseModel] = QueryPersonInput

    query_service: QueryService  # Inject dependency

    def _run(self, person_id: int) -> dict:
        """Synchronous implementation"""
        return self.query_service.get_person_with_primary_name(person_id)

    async def _arun(self, person_id: int) -> dict:
        """Async implementation (future-proof)"""
        return self._run(person_id)
```

**Tool Testing Requirements:**
```python
# tests/unit/test_lc_tools.py
def test_query_person_tool_langchain():
    """Test LangChain v1.0 tool wrapper."""
    from rmagent.agent.lc.tools import query_person

    result = query_person.invoke({"person_id": 1})

    assert result["PersonID"] == 1
    assert "Given" in result
    assert "Surname" in result
```

### State Management Patterns

**v1.0 Requirement: TypedDict ONLY**

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
    sources_checked: list[int]
    confidence: float

# Define workflow with TypedDict state
workflow = StateGraph(ResearchState)

def research_node(state: ResearchState) -> ResearchState:
    """Process research step."""
    # Access state fields
    person_id = state["person_id"]
    messages = state["messages"]

    # Return updated state
    return {
        **state,
        "research_notes": "...",
        "confidence": 0.85
    }

workflow.add_node("research", research_node)
```

**❌ Don't Use Pydantic Models (Deprecated in v1.0):**
```python
# DON'T DO THIS - v1.0 rejects Pydantic state
class ResearchState(BaseModel):
    messages: list[BaseMessage]
    person_id: int
```

### Context Passing Pattern (v1.0)

```python
# ✅ v1.0: Use context parameter
agent = create_research_agent()
result = agent.invoke(
    {"input": "Find census records for person 123"},
    context={  # v1.0 pattern
        "database_path": "data/Iiams.rmtree",
        "sqlite_extension": "./sqlite-extension/icu.dylib"
    }
)

# ❌ 0.3.x: config["configurable"] (deprecated)
result = agent.invoke(
    {"input": "..."},
    config={"configurable": {"database_path": "..."}}  # DON'T USE
)
```

### Observability Setup

**Custom Callbacks (Preferred):**
```python
# rmagent/agent/lc/callbacks.py
from langchain_core.callbacks import BaseCallbackHandler
import json
from pathlib import Path

class RMAgentCallbackHandler(BaseCallbackHandler):
    """Log all LLM interactions to llm_debug.jsonl."""

    def __init__(self, log_path: Path = Path("logs/llm_debug.jsonl")):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def on_llm_start(self, serialized, prompts, **kwargs):
        self._log({
            "event": "llm_start",
            "timestamp": datetime.now().isoformat(),
            "prompts": prompts,
            "model": kwargs.get("invocation_params", {}).get("model_name")
        })

    def on_llm_end(self, response, **kwargs):
        self._log({
            "event": "llm_end",
            "timestamp": datetime.now().isoformat(),
            "response": response.generations[0][0].text,
            "token_usage": response.llm_output.get("token_usage")
        })

    def on_tool_start(self, serialized, input_str, **kwargs):
        self._log({
            "event": "tool_start",
            "tool": serialized.get("name"),
            "input": input_str
        })

    def _log(self, data: dict):
        with self.log_path.open("a") as f:
            json.dump(data, f)
            f.write("\n")

# Usage
from rmagent.agent.lc.callbacks import RMAgentCallbackHandler

agent = create_research_agent()
result = agent.invoke(
    {"input": "Find census records for person 123"},
    callbacks=[RMAgentCallbackHandler()]
)
```

**LangSmith Integration (Optional, Opt-In):**
```python
# config/.env additions
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=sk-ls-xxxxx  # Optional
LANGCHAIN_PROJECT=rmagent

# ⚠️ Privacy Warning: LangSmith sends data to Anthropic's cloud
# Users must explicitly enable this in config
```

### LCEL Chain Patterns

**Census Extraction Chain:**
```python
# rmagent/agent/lc/chains.py
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

class CensusRecord(BaseModel):
    name: str = Field(description="Full name from census")
    age: int = Field(description="Age at time of census")
    birthplace: str = Field(description="Place of birth")
    occupation: str = Field(description="Occupation listed")
    confidence: float = Field(description="Confidence 0-1")

parser = PydanticOutputParser(pydantic_object=CensusRecord)

census_prompt = ChatPromptTemplate.from_messages([
    ("system", """Extract structured census data.
    {format_instructions}"""),
    ("human", "OCR: {ocr_text}\nContext: {person_context}")
])

# LCEL composition
census_extraction_chain = (
    {
        "ocr_text": RunnablePassthrough(),
        "person_context": lambda x: get_person_context(x["person_id"]),
        "format_instructions": lambda _: parser.get_format_instructions()
    }
    | census_prompt
    | ChatAnthropic(model="claude-3-5-sonnet-20241022")
    | parser
)

# Usage
result = census_extraction_chain.invoke({
    "ocr_text": "John Smith 45 Pennsylvania Farmer...",
    "person_id": 123
})
```

### Testing Strategy

**Unit Tests for Tools:**
```python
# tests/unit/test_lc_tools.py
def test_query_person_returns_dict():
    result = query_person.invoke({"person_id": 1})
    assert isinstance(result, dict)
    assert "PersonID" in result

def test_query_person_invalid_id_raises():
    with pytest.raises(ToolExecutionError):
        query_person.invoke({"person_id": 999999})
```

**Integration Tests for Agents:**
```python
# tests/integration/test_lc_agents.py
def test_research_agent_answers_question():
    agent = create_research_agent()
    result = agent.invoke({
        "input": "Who are the parents of person 1?"
    })
    assert "parent" in result["output"].lower()
    assert result["intermediate_steps"]  # Verify tool usage
```

**Chain Tests:**
```python
# tests/unit/test_lc_chains.py
def test_census_extraction_chain_parses_ocr():
    result = census_extraction_chain.invoke({
        "ocr_text": "John Smith 45 Pennsylvania Farmer",
        "person_id": 1
    })
    assert result.name == "John Smith"
    assert result.age == 45
    assert result.occupation == "Farmer"
```

### Migration Checklist

Before implementing LangChain features:
- [ ] Read `docs/RM11_LangChain_Upgrade.md` migration plan
- [ ] Verify v1.0 stable release is available (not alpha)
- [ ] Create new code in `rmagent/agent/lc/` directory
- [ ] Use v1.0 patterns exclusively (create_agent, system_prompt, TypedDict)
- [ ] Add unit tests for all tools (80%+ coverage)
- [ ] Add integration tests for agents
- [ ] Document in CLAUDE.md when to use LangChain vs legacy code

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
