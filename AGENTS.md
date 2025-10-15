# Agent Design Patterns

Guidelines for building LangChain-based agents in RMAgent.

## Critical Rules

### Database File Policy
**NEVER commit database files to git!**
- `.gitignore` excludes `*.rmtree` files - never override this
- Database files contain sensitive personal information
- Users maintain local database files in `data/` directory

### LangChain v1.0 Migration
**Status:** RMAgent has zero active LangChain imports. v1.0 upgrade planned for Phase 7.
**Plan:** See `docs/RM11_LangChain_Upgrade.md` for complete migration strategy.

**When implementing new LangChain features, use v1.0 patterns exclusively:**

| Feature | ❌ 0.3.x (Don't Use) | ✅ v1.0 (Required) |
|---------|---------------------|-------------------|
| Agent creation | `create_react_agent()` | `create_agent()` |
| Agent prompts | `prompt=ChatPromptTemplate(...)` | `system_prompt="string"` |
| State schema | Pydantic models | **Only `TypedDict`** |
| Context passing | `config["configurable"]` | `context=` parameter |

**Reference:** https://docs.langchain.com/oss/python/migrate/langchain-v1

## Agent Creation (v1.0)

```python
from langchain import create_agent
from langchain.agents import AgentExecutor
from langchain_anthropic import ChatAnthropic
from rmagent.agent.lc.tools import query_person, get_events

def create_research_agent():
    """Create genealogy research agent."""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    tools = [query_person, get_events, search_database]

    # v1.0: String system prompt (not ChatPromptTemplate)
    system_prompt = """You are a professional genealogist.
    Always cite sources and flag uncertainties."""

    agent = create_agent(model=llm, tools=tools, system_prompt=system_prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
```

## Tool Design

Place tools in `rmagent/agent/lc/tools.py`.

**Simple Tools (Decorator Pattern):**
```python
from langchain_core.tools import tool

@tool
def query_person(person_id: int) -> dict:
    """Return person details from RootsMagic database."""
    from rmagent.rmlib.database import RMDatabase
    from rmagent.rmlib.queries import QueryService

    with RMDatabase('data/Iiams.rmtree') as db:
        return QueryService(db).get_person_with_primary_name(person_id)
```

**Structured Tools (Class Pattern):**
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
        return self.query_service.get_person_with_primary_name(person_id)

    async def _arun(self, person_id: int) -> dict:
        return self._run(person_id)
```

## State Management (v1.0)

**Use TypedDict ONLY (Pydantic models deprecated):**

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
    confidence: float

workflow = StateGraph(ResearchState)

def research_node(state: ResearchState) -> ResearchState:
    return {**state, "research_notes": "...", "confidence": 0.85}

workflow.add_node("research", research_node)
```

## Observability

**Custom Callbacks (Preferred):**
```python
# rmagent/agent/lc/callbacks.py
from langchain_core.callbacks import BaseCallbackHandler
import json

class RMAgentCallbackHandler(BaseCallbackHandler):
    """Log LLM interactions to llm_debug.jsonl."""

    def on_llm_start(self, serialized, prompts, **kwargs):
        self._log({"event": "llm_start", "prompts": prompts})

    def on_llm_end(self, response, **kwargs):
        self._log({"event": "llm_end", "response": response.text})

    def _log(self, data: dict):
        with Path("logs/llm_debug.jsonl").open("a") as f:
            json.dump(data, f); f.write("\n")

# Usage
agent.invoke({"input": "..."}, callbacks=[RMAgentCallbackHandler()])
```

**LangSmith (Optional, Opt-In):**
```bash
# config/.env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=sk-ls-xxxxx
LANGCHAIN_PROJECT=rmagent
```

## LCEL Chain Patterns

```python
# rmagent/agent/lc/chains.py
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

census_prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract census data. {format_instructions}"),
    ("human", "OCR: {ocr_text}")
])

census_chain = (
    {"ocr_text": RunnablePassthrough(), "format_instructions": lambda _: parser.get_format_instructions()}
    | census_prompt
    | ChatAnthropic(model="claude-3-5-sonnet-20241022")
    | PydanticOutputParser(pydantic_object=CensusRecord)
)
```

## Testing Requirements

**80%+ coverage required for all LangChain features.**

```python
# tests/unit/test_lc_tools.py
def test_query_person_returns_dict():
    result = query_person.invoke({"person_id": 1})
    assert isinstance(result, dict)
    assert "PersonID" in result

# tests/integration/test_lc_agents.py
def test_research_agent_answers_question():
    agent = create_research_agent()
    result = agent.invoke({"input": "Who are the parents of person 1?"})
    assert "parent" in result["output"].lower()
    assert result["intermediate_steps"]  # Verify tool usage
```

## Directory Structure

```
rmagent/agent/
├── llm_provider.py      # Current: Multi-provider abstraction
├── genealogy_agent.py   # Current: Simple agent for CLI
├── formatters.py        # Current: Formatting utilities
├── prompts.py           # Current: YAML-based prompts
└── lc/                  # Future: LangChain v1.0 integration
    ├── tools.py         # v1.0 BaseTool implementations
    ├── chains.py        # LCEL chains for census extraction
    ├── agents.py        # v1.0 agentic workflows
    └── callbacks.py     # Custom callback handlers
```

## Migration Checklist

Before implementing LangChain features:
- [ ] Read `docs/RM11_LangChain_Upgrade.md`
- [ ] Verify v1.0 stable release available (not alpha)
- [ ] Create code in `rmagent/agent/lc/` directory
- [ ] Use v1.0 patterns exclusively
- [ ] Add unit tests (80%+ coverage)
- [ ] Add integration tests
- [ ] Document in CLAUDE.md

## Development Setup

```bash
# Install dependencies with uv
uv sync --extra dev

# Run tests
uv run pytest --cov=rmagent

# Format and lint
uv run black .
uv run ruff check .

# Enable debug logging
# config/.env: LOG_LEVEL=DEBUG
```

## References

- **Project Status:** See `docs/AI_AGENT_TODO.md` for roadmap
- **CLI Commands:** See `README.md` or `USAGE.md` for complete reference
- **Database Schema:** See `data_reference/RM11_Schema_Reference.md`
- **LangChain Migration:** See `docs/RM11_LangChain_Upgrade.md`
