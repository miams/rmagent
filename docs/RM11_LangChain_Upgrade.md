# RM11 LangChain v1.0 Migration Plan

## Critical Context

**Current Status (2025-10-12):**
- RMAgent has **ZERO active LangChain imports** - no code currently uses LangChain APIs
- Custom "LangChain-style" tools in `rmagent/agent/tools.py` are standalone implementations
- LangChain packages (0.3.27) are installed but unused
- All 400 unit tests pass without any LangChain dependencies
- Python 3.11+ requirement exceeds v1.0 minimum (3.10+)

**Upgrade Timing:**
- **When:** After Phase 5 (Testing & Quality) and Phase 6 (Documentation) complete
- **Target:** LangChain 1.0 stable release (not currently available, currently 0.3.x is latest stable)
- **Risk:** Zero - no refactoring needed since LangChain is not currently used

## Goals

- Prepare for future LangChain integration when building new features (census extraction, timeline enrichment)
- Ensure all new LangChain code follows v1.0 best practices from day one
- Document architectural patterns for LangChain features to maintain clean separation
- Establish observability and testing standards for LangChain components

## Background

- **Current versions:** `langchain 0.3.27`, `langchain-openai 0.3.35`, `langchain-anthropic 0.3.21`
- **Current usage:** Custom tool wrappers (`rmagent/agent/tools.py`) provide LangChain-compatible interface but don't import LangChain
- **Future usage:** Census extraction (OCR + entity matching), timeline enrichment (RAG), FAN discovery (agentic research)
- **v1.0 status:** LangChain 1.0 is not yet released (currently at 0.3.x stable, 1.0.0a14 alpha)
- **Architecture:** 0.3.x series already includes "v1.0 architecture" (Runnables/LCEL, modular packages, modern tool calling)

## LangChain v1.0 Breaking Changes Reference

When v1.0 stable releases, all new LangChain code must use these patterns:

| **Feature** | **0.3.x (Deprecated)** | **v1.0 (Required)** |
|------------|------------------------|---------------------|
| Agent creation | `create_react_agent()` | `create_agent()` |
| Agent prompts | `prompt=ChatPromptTemplate(...)` | `system_prompt="string"` |
| Pre-bound tools | `llm.bind_tools(tools)` | ❌ Removed, pass tools to agent |
| Hooks | `pre_model_hook`, `post_model_hook` | Use middleware instead |
| State schema | Any dict-like or Pydantic | **Only `TypedDict`** |
| Context passing | `config["configurable"]["key"]` | `context={"key": value}` |
| Structured output | `method="json_mode"` option | Single strategy per model |

See: https://docs.langchain.com/oss/python/migrate/langchain-v1

## Phase Breakdown

### Phase 0 – Discovery & Decision (1 day)

**Goal:** Verify current state and confirm upgrade strategy.

#### Checklist
- [x] Confirmed: Zero active LangChain imports in codebase
- [x] Confirmed: All LangChain usage is planned for future features
- [x] Confirmed: Python 3.11+ meets v1.0 requirements
- [x] Confirmed: All 400 unit tests pass without LangChain dependencies
- [ ] Monitor LangChain releases for stable 1.0 announcement
- [ ] Review v1.0 migration guide when stable release is announced
- [ ] Inventory planned LangChain touchpoints (census extraction, timeline enrichment, agent tools)

#### Decision: Upgrade Timing

**✅ RECOMMENDED: Wait for stable 1.0 release, upgrade after Phase 5 & 6 complete**

**Rationale:**
- No current usage means no urgency
- Phase 5 focus is test coverage (80%+ target) - avoid introducing complexity
- Phase 6 focus is documentation - should document stable APIs
- Census extraction project (Phase 7+) is ideal time to adopt LangChain
- Stable 1.0 will have better docs, community testing, and no alpha bugs

**Timeline:**
1. Complete Phase 5 (Testing & Quality) - ~2-4 weeks
2. Complete Phase 6 (Documentation) - ~1-2 weeks
3. Monitor for LangChain 1.0 stable release
4. Upgrade when 1.0 stable + census extraction begins

### Phase 1 – Dependency Upgrade (1 day)

**Goal:** Upgrade to latest stable LangChain without breaking existing code.

**Status:** Non-breaking upgrade (zero active usage)

#### When LangChain 1.0 stable releases:

```bash
# Update pyproject.toml with pinned 1.0 versions
[project]
dependencies = [
    # Core utilities (unchanged)
    "pydantic>=2.0",
    "python-dotenv>=1.0",
    "click>=8.0",
    "rich>=13.0",
    "jinja2>=3.0",
    "pyyaml>=6.0",

    # AI providers (unchanged)
    "anthropic>=0.18.0",
    "openai>=1.10.0",
    "ollama>=0.1.0",

    # LangChain v1.0 (UPDATED - use exact versions from 1.0 release)
    "langchain>=1.0.0,<1.1.0",
    "langchain-anthropic>=1.0.0,<1.1.0",
    "langchain-openai>=1.0.0,<1.1.0",
    "langchain-core>=1.0.0,<1.1.0",
]

# Regenerate lockfile
uv lock --upgrade-package langchain

# Verify no dependency conflicts
uv pip check

# Run full test suite (expect 400/400 pass - no changes to code)
uv run pytest tests/unit/ -v --tb=short

# Verify all CLI commands still work
uv run rmagent person 1
uv run rmagent bio 1 --no-ai
uv run rmagent quality --severity critical
uv run rmagent search --name "Smith"
```

#### Checklist
- [ ] Update `pyproject.toml` with pinned v1.0 versions
- [ ] Regenerate `uv.lock` with `uv lock --upgrade-package langchain`
- [ ] Run `uv pip check` to verify no dependency conflicts
- [ ] Run full test suite (all 400 tests must pass)
- [ ] Manual smoke test of all 8 CLI commands
- [ ] Create git tag: `pre-langchain-v1-upgrade` (rollback point)
- [ ] Document upgrade in CHANGELOG.md

**Success Criteria:**
- ✅ All 400 tests pass unchanged
- ✅ All CLI commands functional
- ✅ No dependency conflicts
- ✅ Test execution time within 10% of baseline

### Phase 2 – LangChain Integration Layer (3-5 days)

**Goal:** Create new LangChain v1.0 tools/chains WITHOUT modifying existing code.

**Strategy:** Build alongside existing code in new `lc/` subdirectory.

#### Architecture

```
rmagent/agent/
├── llm_provider.py           # Keep - used by non-LangChain features
├── genealogy_agent.py        # Keep - used by existing CLI commands
├── tools.py                  # Rename to legacy_tools.py
├── prompts.py               # Keep - used by both approaches
└── lc/                      # NEW: LangChain v1.0 integration
    ├── __init__.py
    ├── tools.py             # v1.0 BaseTool implementations
    ├── chains.py            # LCEL Runnable chains
    ├── agents.py            # v1.0 agent configurations
    └── callbacks.py         # Custom observability callbacks
```

#### 2.1 - Create LangChain v1.0 Tools

**File:** `rmagent/agent/lc/tools.py`

**Pattern:** Decorator-based tools (simplest) or class-based (structured I/O)

```python
from langchain_core.tools import tool, BaseTool
from pydantic import BaseModel, Field
from rmagent.rmlib.queries import QueryService

# Decorator-based (simple tools)
@tool
def query_person(person_id: int) -> dict:
    """Return person details (primary name, sex, birth/death years).

    Args:
        person_id: The PersonID from RootsMagic database
    """
    query_service = get_query_service()
    return query_service.get_person_with_primary_name(person_id)

# Class-based with structured I/O (complex tools)
class QueryPersonInput(BaseModel):
    person_id: int = Field(description="PersonID from RootsMagic database")

class QueryPersonOutput(BaseModel):
    person_id: int
    given: str
    surname: str
    birth_year: int | None
    death_year: int | None

class QueryPersonTool(BaseTool):
    name: str = "query_person"
    description: str = "Return person details from RootsMagic database"
    args_schema: type[BaseModel] = QueryPersonInput

    query_service: QueryService

    def _run(self, person_id: int) -> dict:
        """Synchronous implementation"""
        return self.query_service.get_person_with_primary_name(person_id)

    async def _arun(self, person_id: int) -> dict:
        """Async implementation (future-proof)"""
        return self._run(person_id)
```

#### 2.2 - Create v1.0 Agent Patterns

**File:** `rmagent/agent/lc/agents.py`

**Pattern:** Use v1.0 `create_agent()` with string system prompts

```python
from langchain import create_agent  # v1.0 API
from langchain.agents import AgentExecutor
from langchain_anthropic import ChatAnthropic
from rmagent.agent.lc.tools import query_person, get_events, search_database

def create_research_agent(model: str = "claude-3-5-sonnet-20241022") -> AgentExecutor:
    """Create genealogy research agent with v1.0 patterns."""

    llm = ChatAnthropic(model=model)
    tools = [query_person, get_events, search_database]

    # v1.0: Use system_prompt string (not ChatPromptTemplate)
    system_prompt = """You are a professional genealogist with access to a RootsMagic database.

Guidelines:
- Always cite sources (PersonID, EventID, census records)
- Flag uncertainties and conflicting data
- Suggest follow-up research when gaps exist
- Use tools systematically: search → query → analyze
"""

    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt  # v1.0 pattern
    )

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=10,
    )
```

#### 2.3 - Create LCEL Chains for Workflows

**File:** `rmagent/agent/lc/chains.py`

**Use case:** Census extraction, timeline enrichment

```python
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field

class CensusRecord(BaseModel):
    """Structured census record output."""
    name: str = Field(description="Full name from census")
    age: int = Field(description="Age at time of census")
    birthplace: str = Field(description="Place of birth")
    occupation: str = Field(description="Occupation listed")
    confidence: float = Field(description="Confidence score 0-1")

parser = PydanticOutputParser(pydantic_object=CensusRecord)

census_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a genealogy expert extracting information from census records.
    Extract structured data from the OCR text provided.

    {format_instructions}"""),
    ("human", """Census image OCR output:
    {ocr_text}

    Known person context:
    {person_context}

    Extract the census record.""")
])

# LCEL chain composition
census_extraction_chain = (
    {
        "ocr_text": RunnablePassthrough(),
        "person_context": lambda x: get_person_context(x["person_id"]),
        "format_instructions": lambda _: parser.get_format_instructions(),
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

#### Checklist
- [ ] Create `rmagent/agent/lc/` subdirectory
- [ ] Implement `lc/tools.py` with v1.0 tool patterns (6 tools)
- [ ] Add `tests/unit/test_lc_tools.py` (20+ tests)
- [ ] Implement `lc/agents.py` with v1.0 agent patterns
- [ ] Add `tests/integration/test_lc_agents.py` (10+ tests)
- [ ] Implement `lc/chains.py` with LCEL patterns (census, timeline)
- [ ] Add `tests/unit/test_lc_chains.py` (15+ tests)
- [ ] Rename `tools.py` → `legacy_tools.py` (non-breaking)
- [ ] Update imports in `genealogy_agent.py` (legacy_tools)
- [ ] Document: When to use legacy vs LangChain tools

**Success Criteria:**
- ✅ Old code unchanged and working (legacy_tools)
- ✅ New LangChain tools pass all tests
- ✅ Test coverage increases by 50+ tests
- ✅ All 8 CLI commands still functional

### Phase 3 – State Management & TypedDict (1-2 days)

**Goal:** Implement v1.0-compliant state schemas for stateful agents.

**v1.0 Requirement:** State MUST be `TypedDict`, not Pydantic models.

#### Pattern: TypedDict State

```python
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph

# ✅ v1.0 compliant: TypedDict
class ResearchState(TypedDict):
    messages: Sequence[BaseMessage]
    person_id: int
    research_notes: str
    census_records: list[dict]
    confidence: float

# ❌ v0.3 pattern (deprecated in v1.0)
class ResearchState(BaseModel):  # DON'T DO THIS
    messages: list[BaseMessage]
    person_id: int

# Define graph with TypedDict state
workflow = StateGraph(ResearchState)
```

#### Checklist
- [ ] Define TypedDict state schemas for research workflows
- [ ] Implement context passing via `context=` parameter (v1.0)
- [ ] Add tests for state management
- [ ] Document state patterns in `docs/AGENTS.md`

### Phase 4 – Observability & Callbacks (2 days)

**Goal:** Implement logging and tracing for LangChain operations.

#### Pattern: Custom Callbacks

**File:** `rmagent/agent/lc/callbacks.py`

```python
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
import json
from pathlib import Path

class RMAgentCallbackHandler(BaseCallbackHandler):
    """Custom callback for logging LLM interactions."""

    def __init__(self, log_path: Path = Path("logs/llm_debug.jsonl")):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def on_llm_start(self, serialized, prompts, **kwargs):
        """Log when LLM call starts."""
        self._log({
            "event": "llm_start",
            "prompts": prompts,
            "model": kwargs.get("invocation_params", {}).get("model_name"),
        })

    def on_llm_end(self, response: LLMResult, **kwargs):
        """Log when LLM call completes."""
        self._log({
            "event": "llm_end",
            "response": response.generations[0][0].text,
            "token_usage": response.llm_output.get("token_usage"),
        })

    def on_tool_start(self, serialized, input_str, **kwargs):
        """Log tool usage."""
        self._log({
            "event": "tool_start",
            "tool": serialized.get("name"),
            "input": input_str,
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

#### Optional: LangSmith Integration

```python
# config/.env additions
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=sk-ls-xxxxx  # Optional
LANGCHAIN_PROJECT=rmagent

# Privacy consideration: LangSmith sends data to cloud
# Document opt-in/opt-out in user guide
```

#### Checklist
- [ ] Implement `RMAgentCallbackHandler` in `lc/callbacks.py`
- [ ] Update `AppConfig` with LangChain settings
- [ ] Add LangSmith configuration (optional, opt-in)
- [ ] Document observability in user guide
- [ ] Add tests for callback logging
- [ ] Document privacy implications of LangSmith

**Success Criteria:**
- ✅ All LLM calls logged to `llm_debug.jsonl`
- ✅ Token usage tracked
- ✅ LangSmith integration optional (opt-in)

### Phase 5 – Documentation & Examples (2-3 days)

**Goal:** Comprehensive documentation of v1.0 patterns.

#### 5.1 - Update CLAUDE.md

Add section: **LangChain v1.0 Integration Patterns**
- v1.0 agent creation patterns
- Tool implementation examples
- LCEL chain patterns
- State management with TypedDict
- When to use LangChain vs legacy code

#### 5.2 - Update AGENTS.md

Add section: **LangChain v1.0 Best Practices**
- Agent architecture patterns
- Tool design guidelines
- State management patterns
- Observability setup

#### 5.3 - Update README.md

Add section: **LangChain Integration**
- Quick start for LangChain features
- Tool usage examples
- Agent configuration

#### 5.4 - Create Examples

Create `examples/langchain_v1/` directory:
- `simple_agent.py` - Basic agent example
- `census_extraction.py` - Census chain example
- `research_workflow.py` - Multi-step research agent

#### Checklist
- [ ] Add v1.0 patterns section to CLAUDE.md
- [ ] Add best practices section to AGENTS.md
- [ ] Add integration section to README.md
- [ ] Create example scripts in `examples/langchain_v1/`
- [ ] Update AI_AGENT_TODO.md with LangChain status
- [ ] Document migration strategy in CHANGELOG.md

## Future-Facing Enhancements (Phase 7+)

These features will use LangChain v1.0 from day one:

### Census Extraction (See: RM11_CensusExtraction_Plan.md)
- **Tool:** `find_census_records(person_id)` - Search 1,400 census images
- **Chain:** OCR → Entity Extraction → Person Matching (LCEL)
- **Agent:** Iterative refinement with human-in-the-loop review
- **Storage:** Census sidecar SQLite database

### Timeline Enrichment
- **Tool:** `enrich_timeline_event(event_id)` - Add context from multiple sources
- **Chain:** Event → Census → Biography → Enriched Narrative
- **RAG:** Vector search over census records and biographies

### FAN (Family, Associates, Neighbors) Research
- **Tool:** `discover_fan_connections(person_id)` - Find related persons
- **Agent:** Multi-step research workflow with source prioritization
- **Graph:** LangGraph for complex research paths

### Agentic Biography Generation
- **Current:** Template-based with single LLM call
- **Future:** Multi-step research agent gathering sources before writing
- **Workflow:** Search → Verify → Synthesize → Cite

## Validation Checklist

Before considering upgrade complete:

### Code Quality
- [ ] All 400+ unit tests pass
- [ ] New LangChain tests added (80+ tests)
- [ ] Test coverage maintained or improved (target 80%+)
- [ ] No mypy type errors
- [ ] No ruff linting errors
- [ ] Code formatted with black

### Functionality
- [ ] All 8 CLI commands work unchanged
- [ ] New LangChain tools integrate with sample agent
- [ ] Chains produce expected outputs (census, timeline)
- [ ] Callbacks log all LLM interactions
- [ ] No performance regressions (test execution time)

### Documentation
- [ ] CLAUDE.md updated with v1.0 patterns
- [ ] AGENTS.md updated with best practices
- [ ] README.md updated with integration examples
- [ ] Migration documented in CHANGELOG.md
- [ ] Examples directory created with working samples
- [ ] User guide updated (if LangSmith enabled)

### Architecture
- [ ] Clean separation: legacy vs LangChain code
- [ ] No breaking changes to existing APIs
- [ ] v1.0 patterns used throughout new code
- [ ] TypedDict state schemas defined
- [ ] Middleware/callbacks replace hooks

## Rollback Strategy

If issues arise during upgrade:

```bash
# Restore from git tag
git checkout pre-langchain-v1-upgrade

# Or restore lockfile
git checkout HEAD -- uv.lock
uv sync

# Run tests to verify restoration
uv run pytest tests/unit/ -v
```

## References

- **LangChain v1.0 Migration Guide:** https://docs.langchain.com/oss/python/migrate/langchain-v1
- **LangChain Documentation:** https://python.langchain.com/
- **LCEL (Runnables) Guide:** https://python.langchain.com/docs/expression_language/
- **LangGraph Documentation:** https://python.langchain.com/docs/langgraph
- **Tool Calling Guide:** https://python.langchain.com/docs/how_to/tool_calling/
- **Callbacks Guide:** https://python.langchain.com/docs/how_to/callbacks/

## Timeline Summary

| Phase | Duration | When | Dependencies |
|-------|----------|------|--------------|
| Phase 0 | 1 day | After Phase 5 & 6 | Testing & docs complete |
| Phase 1 | 1 day | When v1.0 stable | Phase 0 decision |
| Phase 2 | 3-5 days | After Phase 1 | v1.0 installed |
| Phase 3 | 1-2 days | After Phase 2 | Tools/agents working |
| Phase 4 | 2 days | After Phase 3 | State management done |
| Phase 5 | 2-3 days | After Phase 4 | Observability working |

**Total:** ~2 weeks (10-13 days)

**Start Date:** TBD (after Phase 5 & 6 complete, when v1.0 stable)

---

**Last Updated:** 2025-10-12
**Status:** Planning phase - awaiting completion of Phase 5 & 6 and LangChain v1.0 stable release
**Next Step:** Complete Phase 5 (Testing & Quality, 80%+ coverage target)
