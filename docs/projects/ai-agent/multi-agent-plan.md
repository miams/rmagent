# Multi-Agent Biography Writer - Development Plan

## Executive Summary

**Business Problem**: Professional genealogists spend 4-8 hours and $200-1200 per comprehensive biography. Current single-agent AI generates drafts in 30 seconds for $0.20, but lacks depth and polish.

**Solution**: Multi-agent system with researcher, reporter, and editor agents that produces professional-grade biographies in 2-3 minutes for ~$1.50, saving 95%+ of cost and time while matching or exceeding human quality.

**LangChain 1.0 Showcase**: Demonstrates agent orchestration, LangGraph state management, tool ecosystem integration, LangSmith observability, and evaluation-driven development.

**Target Audience**: Hiring managers evaluating AI/ML engineering capabilities

**Timeline**: Flexible (4-6 weeks part-time recommended)

---

## Architecture Overview

### LangGraph State Machine

```
┌─────────────┐
│   START     │
└──────┬──────┘
       │
       v
┌─────────────────────┐
│  PLAN               │  ← Supervisor agent analyzes source data
│  - Assess data      │    and creates generation strategy
│  - Identify gaps    │
│  - Create strategy  │
└──────┬──────────────┘
       │
       ├─(needs research?)─Yes─→┌──────────────┐
       │                         │  RESEARCH    │ ← Researcher agent
       │                    ┌───→│  - Web search│   fills gaps with
       │                    │    │  - Historical│   historical context
       │                    │    │  - Context   │
       │                    │    └──────┬───────┘
       │                    │           │
       │                    │           v
       No                   │    ┌──────────────┐
       │                    └────│  ENRICH      │ ← Supervisor integrates
       │                         │  - Merge     │   research findings
       │                         └──────┬───────┘
       │                                │
       v                                │
┌──────────────────────┐◄──────────────┘
│  DRAFT               │
│  - Generate bio      │  ← Reporter agent writes narrative
│  - Apply citations   │
│  - Structure content │
└──────┬───────────────┘
       │
       v
┌──────────────────────┐
│  REVIEW              │  ← Editor agent evaluates draft
│  - Check accuracy    │
│  - Assess quality    │
│  - Identify issues   │
└──────┬───────────────┘
       │
       ├─(quality < threshold?)─Yes─→┌──────────────┐
       │                              │  REVISE      │ ← Editor agent
       │                         ┌───→│  - Fix errors│   improves draft
       │                         │    │  - Improve   │
       │                         │    │    flow      │
       │                         │    └──────┬───────┘
       │                         │           │
       No                        └───────────┘ (max 2 iterations)
       │
       v
┌──────────────────────┐
│  FINALIZE            │  ← Format, render, metrics
│  - Apply formatting  │
│  - Generate metrics  │
│  - Calculate cost    │
└──────┬───────────────┘
       │
       v
┌──────────────┐
│     END      │
└──────────────┘
```

### Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Supervisor Agent                        │
│  - Orchestrates workflow                                    │
│  - Makes routing decisions                                  │
│  - Monitors quality thresholds                              │
│  Tools: state_manager, quality_evaluator                    │
└────────┬─────────────────┬─────────────────┬────────────────┘
         │                 │                 │
    ┌────v─────┐     ┌────v─────┐     ┌────v─────┐
    │Researcher│     │ Reporter │     │  Editor  │
    │  Agent   │     │  Agent   │     │  Agent   │
    └────┬─────┘     └────┬─────┘     └────┬─────┘
         │                │                │
    ┌────v─────┐     ┌────v─────┐     ┌────v─────┐
    │ Tools:   │     │ Tools:   │     │ Tools:   │
    │ - Tavily │     │ - SQL DB │     │ - Grammar│
    │ - Wiki   │     │ - Prompt │     │ - Fact   │
    │ - Context│     │ - Cite   │     │   Check  │
    │   Cache  │     │ - Format │     │ - Polish │
    └──────────┘     └──────────┘     └──────────┘
```

---

## LangChain 1.0 Capabilities Demonstrated

This implementation showcases comprehensive LangChain 1.0 usage:

1. **Agent Orchestration**
   - Multiple specialized agents with distinct roles
   - ReAct-style reasoning and planning
   - Inter-agent communication through state

2. **LangGraph State Management**
   - TypedDict state schemas (v1.0 requirement)
   - Conditional routing based on agent decisions
   - State accumulation (research results, revisions)
   - Checkpointing for workflow resumption

3. **Tool Ecosystem**
   - Custom tools (database queries, quality evaluation)
   - Community tools (Tavily search, Wikipedia)
   - Tool composition and chaining
   - Result caching for cost optimization

4. **LangSmith Observability**
   - Full trace collection
   - Custom metrics (quality score, cost tracking)
   - Evaluation datasets
   - A/B testing in LangSmith UI

5. **LCEL Chains**
   - Structured output parsing (Pydantic)
   - Prompt composition
   - Error handling and fallbacks

6. **Evaluation Framework**
   - LLM-as-judge pattern
   - Statistical significance testing
   - Business value quantification

---

## Phase 1: Foundation (Week 1)

### Goals
- Set up LangChain 1.0 infrastructure
- Define state schemas
- Implement core tools
- Configure LangSmith

### 1.1 Dependencies

Add to `pyproject.toml`:

```toml
[project.dependencies]
langchain = "^1.0.0"          # Core LangChain
langgraph = "^1.0.0"          # State machine orchestration
langsmith = "^0.2.0"          # Observability
langchain-anthropic = "^1.0.0"  # Claude integration
langchain-openai = "^1.0.0"   # OpenAI integration (for comparison)
langchain-community = "^1.0.0"  # Community tools
tavily-python = "^0.5.0"      # Web search tool
```

### 1.2 Directory Structure

Create new directory:

```
rmagent/agent/lc/
├── __init__.py           # Package initialization
├── state.py              # LangGraph state schemas (TypedDict)
├── agents.py             # Agent definitions
├── tools.py              # Custom tool implementations
├── graph.py              # LangGraph workflow
├── prompts.py            # Agent system prompts
└── evaluator.py          # Quality evaluation (LLM-as-judge)
```

### 1.3 State Schema (`state.py`)

```python
from typing import TypedDict, Literal, Annotated
from operator import add

class BiographyState(TypedDict):
    """State for biography generation workflow."""

    # Input
    person_id: int
    length: Literal["short", "standard", "comprehensive"]

    # Source data (from RM database)
    person_data: dict
    events: list[dict]
    family_data: dict

    # Planning
    strategy: dict  # Generated by supervisor
    information_gaps: list[str]
    research_needed: bool

    # Research (optional)
    research_queries: list[str]
    research_results: Annotated[list[dict], add]  # Accumulate results
    historical_context: dict

    # Generation
    draft_biography: str
    draft_citations: list[str]
    draft_word_count: int

    # Review
    quality_score: float
    quality_assessment: dict
    revision_needed: bool
    revision_count: int

    # Final
    final_biography: str
    final_quality_score: float
    metadata: dict

    # Cost tracking
    total_cost: float
    token_usage: dict
```

**Key LangChain Features:**
- ✅ TypedDict state (v1.0 requirement, replaces Pydantic)
- ✅ Annotated types for state reduction (`operator.add`)
- ✅ Explicit input/output tracking for observability

### 1.4 Tool Implementations (`tools.py`)

```python
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from typing import Optional

@tool
def query_person_data(person_id: int) -> dict:
    """
    Retrieve person data from RootsMagic database.

    Returns person details, events, family relationships, and notes.
    """
    from rmagent.rmlib.database import RMDatabase
    from rmagent.rmlib.queries import QueryService
    from rmagent.config.config import load_app_config

    config = load_app_config()
    with RMDatabase(config.database.database_path) as db:
        query = QueryService(db)
        return {
            "person": query.get_person_with_primary_name(person_id),
            "events": query.get_person_events(person_id),
            "family": {
                "parents": query.get_parents(person_id),
                "spouses": query.get_spouses(person_id),
                "children": query.get_children(person_id),
            }
        }

@tool
def search_historical_context(
    query: str,
    location: Optional[str] = None,
    time_period: Optional[str] = None
) -> dict:
    """
    Search web for historical context about a location and time period.

    Args:
        query: Main search query (e.g., "Pittsburgh steel industry")
        location: Geographic location to focus on
        time_period: Time period (e.g., "1890s", "late 19th century")

    Returns:
        Search results with historical context information.
    """
    # Build enhanced query
    enhanced_query = f"{query} historical context genealogy"
    if location:
        enhanced_query += f" {location}"
    if time_period:
        enhanced_query += f" {time_period}"

    # Use Tavily for high-quality search
    search = TavilySearchResults(
        max_results=3,
        search_depth="advanced",
        include_answer=True
    )

    results = search.invoke({"query": enhanced_query})

    # Cache results to avoid redundant searches
    _cache_research_result(query, location, time_period, results)

    return {
        "query": enhanced_query,
        "results": results,
        "cached": False
    }

@tool
def evaluate_biography_quality(
    biography_text: str,
    source_data: dict,
    criteria: list[str]
) -> dict:
    """
    Evaluate biography quality using LLM-as-judge.

    Args:
        biography_text: The biography to evaluate
        source_data: Original source data for fact checking
        criteria: List of evaluation criteria

    Returns:
        Quality scores and detailed assessment.
    """
    from rmagent.agent.lc.evaluator import BiographyEvaluator

    evaluator = BiographyEvaluator()
    return evaluator.evaluate(biography_text, source_data, criteria)
```

**Key LangChain Features:**
- ✅ `@tool` decorator for automatic tool registration
- ✅ Integration with existing codebase (RMDatabase)
- ✅ Community tools (Tavily search)
- ✅ Structured inputs/outputs

### 1.5 LangSmith Configuration

Add to `config/.env`:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls-...
LANGCHAIN_PROJECT=rmagent-biography
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

### Deliverables
- [ ] `rmagent/agent/lc/` directory created
- [ ] `state.py` with TypedDict schemas
- [ ] `tools.py` with 5+ custom tools
- [ ] LangSmith account configured
- [ ] Basic tracing verified

---

## Phase 2: Agent Implementation (Week 2)

### Goals
- Implement 4 specialized agents
- Create LangGraph workflow
- Add conditional routing logic
- Test basic flow

### 2.1 Agent Definitions (`agents.py`)

```python
from langchain import create_agent
from langchain_anthropic import ChatAnthropic

def create_supervisor_agent():
    """
    Supervisor agent orchestrates the workflow.

    Responsibilities:
    - Analyze source data completeness
    - Decide if research is needed
    - Evaluate quality and decide if revision needed
    - Monitor cost and quality thresholds
    """

    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)

    tools = [
        query_person_data,
        evaluate_biography_quality,
        check_chronological_consistency
    ]

    system_prompt = """You are a biography generation supervisor.

Your role is to:
1. Analyze source data to identify information gaps
2. Decide if historical research is needed
3. Evaluate biography drafts for quality
4. Determine if revisions are necessary

Key decision criteria:
- Research needed if: Missing historical context, unclear migration patterns,
  insufficient career details, or gaps in 10+ year periods
- Revision needed if: Quality score < 7.5/10, chronological errors present,
  or missing required biography sections
- Maximum 2 revision iterations to control cost

Be decisive but cost-conscious. Not every biography needs research."""

    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt
    )

def create_researcher_agent():
    """Researcher agent fills information gaps."""

    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0.3)

    tools = [
        search_historical_context,
        # Wikipedia tool from langchain-community
    ]

    system_prompt = """You are a genealogical researcher specializing in historical context.

Your goal: Enrich biographies with relevant historical background.

Research priorities:
1. Economic conditions (what was happening in their location/era?)
2. Migration patterns (why did families move?)
3. Occupational context (what did their job entail in that era?)
4. Major events (wars, panics, epidemics affecting their life)

Best practices:
- Focus on location + time period specific context
- Keep summaries concise (2-3 sentences per topic)
- Cite sources for all claims
- Check cache before new searches (cost control)

Quality over quantity: 2-3 highly relevant facts > 10 generic facts."""

    return create_agent(model=llm, tools=tools, system_prompt=system_prompt)

def create_reporter_agent():
    """Reporter agent writes the biography narrative."""

    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        temperature=0.7  # Higher temp for creative writing
    )

    # Reuse existing biography prompts from config/prompts/biography.yaml
    from rmagent.agent.prompts import load_prompt_template
    system_prompt = load_prompt_template("biography")

    return create_agent(model=llm, tools=[], system_prompt=system_prompt)

def create_editor_agent():
    """Editor agent reviews and polishes the draft."""

    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0.3)

    tools = [
        evaluate_biography_quality,
        check_chronological_consistency
    ]

    system_prompt = """You are an expert genealogical editor.

Your role: Polish biography drafts to professional standards.

Review checklist:
1. ACCURACY: All facts match source data exactly
2. COMPLETENESS: All major life events covered
3. FLOW: Smooth transitions, logical progression
4. CITATIONS: Properly placed, not over-cited
5. STYLE: Clear, engaging, appropriate tone

When revising:
- Make minimal changes (preserve good sections)
- Fix errors but don't add unsourced information
- Improve flow without changing facts
- Balance comprehensiveness with readability

Output: Revised biography + explanation of changes made."""

    return create_agent(model=llm, tools=tools, system_prompt=system_prompt)
```

**Key LangChain Features:**
- ✅ v1.0 `create_agent()` API (not `create_react_agent()`)
- ✅ System prompt strings (not ChatPromptTemplate)
- ✅ Per-agent tool assignment
- ✅ Temperature tuning by role

### 2.2 LangGraph Workflow (`graph.py`)

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from rmagent.agent.lc.state import BiographyState

def create_biography_graph():
    """Create LangGraph workflow for multi-agent biography generation."""

    workflow = StateGraph(BiographyState)

    # Add nodes for each stage
    workflow.add_node("plan", plan_node)
    workflow.add_node("research", research_node)
    workflow.add_node("draft", draft_node)
    workflow.add_node("review", review_node)
    workflow.add_node("revise", revise_node)
    workflow.add_node("finalize", finalize_node)

    # Define edges (routing logic)
    workflow.set_entry_point("plan")

    # After planning, conditionally go to research or draft
    workflow.add_conditional_edges(
        "plan",
        should_research,  # Decision function
        {
            "research": "research",
            "draft": "draft"
        }
    )

    workflow.add_edge("research", "draft")
    workflow.add_edge("draft", "review")

    # After review, conditionally revise or finalize
    workflow.add_conditional_edges(
        "review",
        should_revise,
        {
            "revise": "revise",
            "finalize": "finalize"
        }
    )

    workflow.add_edge("revise", "review")  # Loop back
    workflow.add_edge("finalize", END)

    # Add memory for checkpointing
    memory = MemorySaver()

    return workflow.compile(checkpointer=memory)

# Conditional routing functions
def should_research(state: BiographyState) -> Literal["research", "draft"]:
    """Decide if research is needed."""
    return "research" if state["research_needed"] else "draft"

def should_revise(state: BiographyState) -> Literal["revise", "finalize"]:
    """Decide if revision is needed."""
    return "revise" if state["revision_needed"] else "finalize"
```

**Key LangChain Features:**
- ✅ LangGraph state machine
- ✅ Conditional routing
- ✅ Checkpointing (workflow can resume)
- ✅ Loop detection (max iterations)

### Deliverables
- [ ] `agents.py` with 4 agent definitions
- [ ] `graph.py` with LangGraph workflow
- [ ] Node implementations (plan, research, draft, review, revise, finalize)
- [ ] Basic workflow test (single person)

---

## Phase 3: Evaluation Framework (Week 3)

### Goals
- Implement LLM-as-judge evaluator
- Create human labor equivalency calculator
- Build A/B testing framework
- Generate evaluation datasets

### 3.1 LLM-as-Judge Evaluator (`evaluator.py`)

```python
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

class BiographyQualityScore(BaseModel):
    """Quality assessment scores."""
    factual_accuracy: int = Field(ge=1, le=10)
    narrative_flow: int = Field(ge=1, le=10)
    citation_quality: int = Field(ge=1, le=10)
    completeness: int = Field(ge=1, le=10)
    readability: int = Field(ge=1, le=10)
    strengths: list[str]
    weaknesses: list[str]
    explanation: str

class BiographyEvaluator:
    """LLM-as-judge evaluator for biography quality."""

    def __init__(self):
        self.llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0)
        self.parser = JsonOutputParser(pydantic_object=BiographyQualityScore)

    def evaluate(self, biography_text: str, source_data: dict) -> dict:
        """Evaluate using LLM-as-judge pattern."""

        prompt = f"""Evaluate this biography against source data.

SOURCE DATA (Ground Truth):
{self._format_source(source_data)}

BIOGRAPHY:
{biography_text}

Rate 1-10 on:
1. Factual accuracy (matches source exactly)
2. Narrative flow (smooth, engaging)
3. Citation quality (proper coverage)
4. Completeness (covers all major events)
5. Readability (clear, concise)

{self.parser.get_format_instructions()}"""

        result = self.llm.invoke(prompt)
        scores = self.parser.parse(result.content)

        # Weighted overall score
        overall = (
            scores.factual_accuracy * 0.35 +
            scores.completeness * 0.25 +
            scores.narrative_flow * 0.20 +
            scores.citation_quality * 0.15 +
            scores.readability * 0.05
        )

        return {**scores.dict(), "overall_score": overall}
```

**Key LangChain Features:**
- ✅ Structured output parsing (Pydantic)
- ✅ LLM-as-judge pattern
- ✅ Consistent evaluation (temp=0)

### 3.2 Labor Equivalency Calculator

Create `rmagent/evaluation/labor_equivalency.py`:

```python
from dataclasses import dataclass
from typing import Literal

@dataclass
class CostComparison:
    """Cost/time comparison between human and AI."""

    human_hours_min: float
    human_hours_max: float
    human_cost_min: float
    human_cost_max: float
    ai_seconds: float
    ai_cost: float
    time_savings_pct: float
    cost_savings_pct: float
    human_hour_equivalent: float
    roi_multiplier: float

def calculate_labor_equivalency(
    biography_length: Literal["short", "standard", "comprehensive"],
    ai_quality_score: float,
    ai_generation_time: float,
    ai_cost: float
) -> CostComparison:
    """
    Calculate human labor equivalency and ROI.

    Maps AI quality score to equivalent human work hours:
    - 9.0-10.0: Expert genealogist (100% equivalent)
    - 7.5-9.0: Experienced genealogist (80% equivalent)
    - 6.0-7.5: Junior genealogist (60% equivalent)
    """

    # Human time estimates (hours)
    time_ranges = {
        "short": (2, 4),
        "standard": (4, 8),
        "comprehensive": (8, 16)
    }

    # Quality multiplier
    if ai_quality_score >= 9.0:
        quality_mult = 1.0
    elif ai_quality_score >= 7.5:
        quality_mult = 0.8
    elif ai_quality_score >= 6.0:
        quality_mult = 0.6
    else:
        quality_mult = 0.4

    time_range = time_ranges[biography_length]
    human_hour_equivalent = sum(time_range) / 2 * quality_mult

    # Cost calculations (genealogist rates: $50-150/hr, avg $85)
    hourly_rate_min = 50.0
    hourly_rate_max = 150.0
    human_cost_min = time_range[0] * hourly_rate_min
    human_cost_max = time_range[1] * hourly_rate_max
    human_cost_avg = (human_cost_min + human_cost_max) / 2

    time_savings_pct = (1 - ai_generation_time / (time_range[0] * 3600)) * 100
    cost_savings_pct = (1 - ai_cost / human_cost_avg) * 100
    roi_multiplier = human_cost_avg / ai_cost if ai_cost > 0 else float('inf')

    return CostComparison(
        human_hours_min=time_range[0],
        human_hours_max=time_range[1],
        human_cost_min=human_cost_min,
        human_cost_max=human_cost_max,
        ai_seconds=ai_generation_time,
        ai_cost=ai_cost,
        time_savings_pct=time_savings_pct,
        cost_savings_pct=cost_savings_pct,
        human_hour_equivalent=human_hour_equivalent,
        roi_multiplier=roi_multiplier
    )
```

### 3.3 A/B Testing CLI

Add to `rmagent/cli/commands/evaluate.py`:

```python
@click.command()
@click.option("--sample-size", type=int, default=10)
def ab_test(sample_size: int):
    """
    Compare single-agent vs multi-agent approaches.

    Runs statistical analysis and displays:
    - Quality score comparison
    - Cost comparison
    - Labor equivalency
    - ROI analysis
    """

    # Select representative sample
    person_ids = select_representative_sample(sample_size)

    results = []
    for person_id in person_ids:
        # Generate with both approaches
        single = generate_single_agent(person_id)
        multi = generate_multi_agent(person_id)

        # Evaluate both
        score_single = evaluate_biography(single)
        score_multi = evaluate_biography(multi)

        results.append({
            "person_id": person_id,
            "single_score": score_single["overall_score"],
            "multi_score": score_multi["overall_score"],
            "single_cost": single.cost,
            "multi_cost": multi.cost
        })

    # Statistical analysis (paired t-test)
    from scipy import stats
    single_scores = [r["single_score"] for r in results]
    multi_scores = [r["multi_score"] for r in results]
    t_stat, p_value = stats.ttest_rel(multi_scores, single_scores)

    # Display results table
    display_ab_results(results, p_value)
```

### Deliverables
- [ ] `evaluator.py` with LLM-as-judge
- [ ] `labor_equivalency.py` with ROI calculator
- [ ] `evaluate.py` CLI command for A/B testing
- [ ] Evaluation dataset (10-20 persons)
- [ ] Statistical analysis verified

---

## Phase 4: LangSmith Integration (Week 3-4)

### Goals
- Configure comprehensive tracing
- Create evaluation datasets
- Set up custom metrics
- Enable production debugging

### 4.1 Tracing Configuration

```python
# rmagent/agent/lc/observability.py
from langsmith import Client
from langsmith.run_helpers import traceable

client = Client()

@traceable(run_type="chain", name="multi_agent_biography")
def generate_biography_with_tracing(person_id: int, **kwargs):
    """Generate biography with full LangSmith tracing."""

    graph = create_biography_graph()
    result = graph.invoke({"person_id": person_id, **kwargs})

    # Log custom metrics
    client.create_feedback(
        run_id=result["run_id"],
        key="quality_score",
        score=result["final_quality_score"]
    )

    client.create_feedback(
        run_id=result["run_id"],
        key="cost",
        value=result["metadata"]["total_cost"]
    )

    return result
```

### 4.2 Evaluation Datasets

```python
# rmagent/evaluation/datasets.py

def create_evaluation_dataset(name: str, person_ids: list[int]):
    """Create LangSmith evaluation dataset."""

    client = Client()
    dataset = client.create_dataset(
        dataset_name=name,
        description="Biography quality evaluation"
    )

    for person_id in person_ids:
        source_data = query_person_data(person_id)
        reference_bio = get_expert_biography(person_id)  # If available

        client.create_example(
            dataset_id=dataset.id,
            inputs={"person_id": person_id},
            outputs={"biography": reference_bio},
            metadata={
                "complexity": assess_complexity(source_data),
                "expected_quality": "7.5-9.0"
            }
        )
```

### Deliverables
- [ ] LangSmith tracing enabled
- [ ] Custom metrics (quality, cost)
- [ ] Evaluation dataset created
- [ ] Example traces published

---

## Phase 5: CLI Integration & Demo (Week 4)

### Goals
- Add `--multi-agent` flag to bio command
- Implement rich terminal output
- Create demo script
- Write GitHub documentation

### 5.1 CLI Enhancement

Update `rmagent/cli/commands/bio.py`:

```python
@click.option("--multi-agent", is_flag=True, help="Use multi-agent workflow")
@click.option("--show-reasoning", is_flag=True, help="Display agent reasoning")
def bio(person_id: int, multi_agent: bool, show_reasoning: bool, **kwargs):
    """Generate biography with optional multi-agent workflow."""

    if multi_agent:
        graph = create_biography_graph()

        if show_reasoning:
            for step in graph.stream({"person_id": person_id, **kwargs}):
                display_agent_step(step)
        else:
            result = graph.invoke({"person_id": person_id, **kwargs})

        # Show cost comparison
        labor_equiv = calculate_labor_equivalency(
            biography_length=kwargs["length"],
            ai_quality_score=result["final_quality_score"],
            ai_generation_time=result["metadata"]["generation_time"],
            ai_cost=result["metadata"]["total_cost"]
        )

        console.print(labor_equiv.summary())
    else:
        # Existing single-agent approach
        pass
```

### 5.2 Demo Documentation

Create `docs/MULTI_AGENT_DEMO.md`:

```markdown
# Multi-Agent Biography Generation Demo

## Quick Start

```bash
# Single-agent (fast, baseline)
rmagent bio 2

# Multi-agent (comprehensive)
rmagent bio 2 --multi-agent --show-reasoning

# Compare approaches
rmagent ab-test --sample-size 10
```

## Example Output

[Include example with agent reasoning, quality scores, cost comparison]

## Architecture

[Include state machine diagram]

## LangSmith Traces

[Link to example traces]
```

### Deliverables
- [ ] `--multi-agent` CLI flag working
- [ ] Rich terminal output with reasoning display
- [ ] Demo documentation
- [ ] Example traces published
- [ ] README updated with multi-agent section

---

## Success Metrics

### Technical Metrics
- [ ] All 4 agents functional
- [ ] LangGraph workflow with conditional routing working
- [ ] LangSmith tracing 100% coverage
- [ ] Test coverage >80% for new code
- [ ] A/B test shows statistical significance (p<0.05)

### Business Metrics
- [ ] Quality improvement: 15-25% better scores
- [ ] Cost: $1-2 per comprehensive biography
- [ ] Time: 2-3 minutes (vs 4-8 hours human)
- [ ] ROI: 400-800x demonstrated
- [ ] Human labor equivalent: 5-6 hours of work delivered

### Portfolio Metrics
- [ ] GitHub README with clear demo
- [ ] Architecture diagrams
- [ ] Published LangSmith traces
- [ ] A/B test results documented
- [ ] Business value quantified (ROI, labor savings)

---

## Portfolio Narrative for Hiring Managers

**Problem Statement:**
"Professional genealogists spend 4-8 hours and charge $200-1200 for comprehensive biographies. This creates a bottleneck for family historians working with hundreds or thousands of ancestors."

**Solution:**
"I built a multi-agent system using LangChain 1.0 that orchestrates researcher, reporter, and editor agents to produce professional-grade biographies in 2-3 minutes for ~$1.50—a 99%+ reduction in cost and time."

**Technical Implementation:**
- LangGraph state machine with conditional routing
- 4 specialized agents with distinct tool ecosystems
- LLM-as-judge evaluation framework
- LangSmith observability for production debugging
- Statistical A/B testing with human labor equivalency

**Business Impact:**
- 400-800x ROI validated with real cost/time data
- Quality scores map to human work hours (5-6 hours equivalent)
- Cost-conscious engineering (max 2 revisions, research caching)

**Why LangChain:**
"The use case naturally maps to LangChain's strengths: complex agent orchestration, conditional workflow routing, diverse tool integration, and production observability. Alternative approaches would require building these capabilities from scratch."

---

## Implementation Checklist

### Week 1: Foundation
- [ ] Install LangChain 1.0 dependencies
- [ ] Create `rmagent/agent/lc/` directory
- [ ] Implement state schema (TypedDict)
- [ ] Build 5+ custom tools
- [ ] Configure LangSmith
- [ ] Verify basic tracing

### Week 2: Agents
- [ ] Implement supervisor agent
- [ ] Implement researcher agent (Tavily)
- [ ] Implement reporter agent
- [ ] Implement editor agent
- [ ] Build LangGraph workflow
- [ ] Add conditional routing
- [ ] Test basic flow (1 person)

### Week 3: Evaluation
- [ ] Build LLM-as-judge evaluator
- [ ] Create labor equivalency calculator
- [ ] Implement A/B testing CLI
- [ ] Generate evaluation dataset (10-20 persons)
- [ ] Run statistical analysis
- [ ] Create LangSmith evaluation datasets

### Week 4: Polish
- [ ] Add `--multi-agent` CLI flag
- [ ] Implement rich terminal output
- [ ] Add `--show-reasoning` display
- [ ] Create demo documentation
- [ ] Write architecture docs
- [ ] Publish example LangSmith traces
- [ ] Update README with demo section
- [ ] Create architecture diagram

---

## Questions & Next Steps

**Ready to start?**

I can help with:
1. Implementing any phase in detail
2. Creating architecture diagrams
3. Writing specific agent prompts
4. Building evaluation datasets
5. Drafting GitHub documentation

**Which phase should we tackle first?**

Recommended start: **Phase 1 (Foundation)** - Sets up infrastructure for everything else.

Alternative: **Phase 5 first** to validate the CLI/UX before heavy implementation.

Let me know your preference!
