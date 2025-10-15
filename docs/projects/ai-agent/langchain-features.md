# RMAgent: Advanced Features Using LangChain

**Document Version**: 2025-10-13
**Status**: Planning / Research

## Overview

This document outlines potential advanced features for RMAgent leveraging LangChain v1.0 capabilities. Features are ranked by potential value delivery to genealogical researchers.

---

## Top 10 Advanced LangChain Features (Ranked by Value)

### 1. Source Document RAG Pipeline (Highest Value)

**LangChain Capabilities**: Document loaders + embeddings + vector store + reranking

**Value Proposition**: Index full-text OCR'd documents (census pages, obituaries, military records) and extract structured facts on-demand

**Use Case**:
- User asks: "What does the 1930 census say about John's occupation?"
- RAG retrieves relevant page section from indexed documents
- LLM extracts occupation + confidence score
- Returns answer with citation to original source

**Impact**:
- Eliminates manual re-reading of source documents
- Brings primary sources directly into Q&A workflow
- Reduces research time by 60-80% for document review

**Implementation Details**:
- Vector store: Chroma or FAISS per source type
- Metadata filtering: person_id, date_range, place, source_type
- Chunking strategy: Preserve paragraph/section boundaries
- Embedding model: text-embedding-3-small or sentence-transformers
- Reranking: Cohere reranker or cross-encoder for precision

**Technical Components**:
```python
from langchain_community.document_loaders import PyPDFLoader
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CohereRerank

# Index documents with metadata
vectorstore = Chroma(
    embedding_function=OpenAIEmbeddings(),
    collection_metadata={"source_type": "census", "year": "1930"}
)

# Retrieval with reranking
compressor = CohereRerank(model="rerank-english-v2.0", top_n=5)
retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=vectorstore.as_retriever(search_kwargs={"k": 20})
)
```

---

### 2. Multi-Source Conflict Resolution Agent (Very High Value)

**LangChain Capabilities**: LangGraph multi-step reasoning + structured output

**Value Proposition**: Automatically detect and reconcile contradictory facts across sources using Evidence Explained genealogical standards

**Use Case**:
- Birth date conflict: Census says 1872, tombstone says 1874
- Agent evaluates source quality (primary vs. derivative)
- Considers proximity to event (contemporaneous vs. retrospective)
- Suggests resolution with genealogical reasoning

**Impact**:
- Solves core genealogy challenge of conflicting sources
- Saves hours of manual source comparison
- Teaches best practices through AI-generated reasoning

**Implementation Details**:
- LangGraph workflow nodes:
  1. **Retrieve**: Gather all sources for disputed fact
  2. **Categorize**: Classify as primary/secondary/tertiary
  3. **Evaluate**: Score reliability (proximity to event, informant knowledge)
  4. **Analyze**: Compare temporal/contextual factors
  5. **Resolve**: Generate recommendation with Evidence Explained citation
  6. **Report**: Structured output with reasoning chain

**LangGraph State Machine**:
```python
from langgraph.graph import StateGraph
from typing import TypedDict, Annotated

class ConflictState(TypedDict):
    person_id: int
    fact_type: str  # birth, death, marriage
    conflicting_sources: list[dict]
    source_evaluations: list[dict]
    resolution: dict
    reasoning: list[str]

def retrieve_sources(state: ConflictState) -> ConflictState:
    """Gather all sources for disputed fact."""
    # Query database for all sources mentioning fact
    pass

def evaluate_reliability(state: ConflictState) -> ConflictState:
    """Score each source using genealogical standards."""
    # Apply Evidence Explained criteria
    pass

def resolve_conflict(state: ConflictState) -> ConflictState:
    """Generate recommended resolution."""
    # Use LLM to synthesize evaluation into recommendation
    pass

workflow = StateGraph(ConflictState)
workflow.add_node("retrieve", retrieve_sources)
workflow.add_node("evaluate", evaluate_reliability)
workflow.add_node("resolve", resolve_conflict)
workflow.add_edge("retrieve", "evaluate")
workflow.add_edge("evaluate", "resolve")
```

---

### 3. Research Gap Advisor with Vector Similarity (Very High Value)

**LangChain Capabilities**: Self-querying retriever + semantic search across family trees

**Value Proposition**: Analyze person's data completeness, find similar research paths from other families, suggest next steps

**Use Case**:
- Person X missing marriage record
- System finds 20 similar cases (same region, time period, ethnicity)
- Analyzes which record types successfully filled gaps
- Recommends: "Check county clerk marriage bonds 1870-1875"

**Impact**:
- Guides researchers to most promising next steps
- Learns from collective research patterns
- Reduces trial-and-error research time

**Implementation Details**:
- Person profile embedding: Encode facts + gaps as semantic vectors
- Similarity search: Find successful research paths
- Recommendation engine: Rank suggestions by success rate
- Metadata: Region, time period, ethnicity, religion, social class

**Technical Approach**:
```python
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# Embed person profiles
def create_person_profile(person_id: int) -> dict:
    return {
        "facts": [...],  # Known facts
        "gaps": [...],   # Missing vital records
        "context": {
            "region": "Pennsylvania",
            "period": "1850-1900",
            "ethnicity": "German",
        }
    }

# Store successful research paths
vectorstore.add_documents([
    Document(
        page_content="Missing marriage record found via county clerk bonds",
        metadata={"gap_type": "marriage", "region": "PA", "success": True}
    )
])

# Query for similar gaps
similar_cases = vectorstore.similarity_search(
    query="Pennsylvania German missing marriage 1870s",
    filter={"success": True},
    k=10
)
```

---

### 4. Conversational Research Assistant (High Value)

**LangChain Capabilities**: Agent with memory (conversation history + entity memory) + custom tools

**Value Proposition**: Multi-turn dialogue that remembers context, asks clarifying questions, uses tools for database queries and analysis

**Use Case**:
```
User: "Tell me about the Iams migration"
Agent: "Which branch of the Iams family? I see three main lines in the database."
User: "Donald's line"
Agent: [Uses QueryService tool] "Donald Richard Iams (1932-2014) was born in Tulsa,
       Oklahoma and later moved to Arizona. His father Jesse Dorsey Iams came from..."
User: "Show me a timeline"
Agent: [Uses TimelineGenerator tool] [Generates timeline visualization]
```

**Impact**:
- Natural research workflow vs. CLI commands
- Reduces learning curve for new users
- Enables exploratory research conversations

**Implementation Details**:
```python
from langchain.agents import create_tool_calling_agent
from langchain.memory import ConversationBufferMemory, EntityMemory
from langchain_core.tools import tool

@tool
def query_person(person_id: int) -> dict:
    """Get detailed information about a person."""
    query = QueryService(db)
    return query.get_person_with_primary_name(person_id)

@tool
def generate_timeline(person_id: int) -> str:
    """Generate timeline for a person's life events."""
    generator = TimelineGenerator(db)
    return generator.generate(person_id, format="json")

@tool
def search_by_name(name: str, limit: int = 10) -> list[dict]:
    """Search for persons by name."""
    # Implementation
    pass

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
entity_memory = EntityMemory()  # Track mentioned people/places

agent = create_tool_calling_agent(
    llm=llm,
    tools=[query_person, generate_timeline, search_by_name],
    prompt=prompt
)
```

---

### 5. Historical Context Augmentation (High Value)

**LangChain Capabilities**: RAG over external historical knowledge base + reranking

**Value Proposition**: Automatically enrich biographies with relevant historical context (wars, economic conditions, migration waves)

**Use Case**:
- Biography of 1890s immigrant from Germany
- RAG retrieves: Ellis Island processing info, steamship routes, German political conditions (1848 revolution aftermath), NYC settlement patterns
- LLM integrates context naturally into narrative

**Impact**:
- Adds professional-quality depth to biographies
- Eliminates manual historical research
- Educational for readers

**Implementation Details**:
- Knowledge base: Wikipedia dumps, historical databases, genealogy guides
- Indexing: By time period, geographic region, event type
- Retrieval: Query expansion for temporal/geographic relevance
- Reranking: Cohere or cross-encoder for precision

**Data Sources**:
- Wikipedia historical events (structured)
- Immigration databases (Ellis Island, Castle Garden)
- Economic data (census, labor statistics)
- Military records (war rosters, pension files)

---

### 6. Cross-Record Entity Resolution (Medium-High Value)

**LangChain Capabilities**: Embedding-based similarity + structured output validation

**Value Proposition**: Identify potential duplicate persons or same individual across disconnected family trees

**Use Case**:
- Find all variants of "John Smith b.~1850 Maryland"
- Calculate embedding similarity (name + birth + parents + places)
- Flag likely duplicates with confidence scores
- Suggest merge operations

**Impact**:
- Critical for data quality
- Prevents duplicate entries
- Merges fragmented research from multiple sources

**Implementation Details**:
```python
from langchain_openai import OpenAIEmbeddings
from sklearn.metrics.pairwise import cosine_similarity

def create_person_signature(person: dict) -> str:
    """Generate text signature for embedding."""
    return f"""
    Name: {person['Given']} {person['Surname']}
    Birth: {person['BirthYear']} in {person['BirthPlace']}
    Parents: {person['FatherName']}, {person['MotherName']}
    """

# Embed all persons
embeddings = OpenAIEmbeddings()
person_vectors = embeddings.embed_documents([
    create_person_signature(p) for p in all_persons
])

# Find similar pairs
similarity_matrix = cosine_similarity(person_vectors)
duplicates = np.where(
    (similarity_matrix > 0.85) & (similarity_matrix < 1.0)
)
```

---

### 7. Agentic Census Extraction Workflow (Medium-High Value)

**LangChain Capabilities**: LangGraph with conditional routing + vision models (GPT-4V, Claude)

**Value Proposition**: Structured extraction from census images with validation and error correction

**Use Case**:
1. Upload 1920 census page image
2. Agent extracts household members (names, ages, occupations, relationships)
3. Validates against known family data
4. Flags discrepancies (age conflicts, spelling variations)
5. Suggests corrections with confidence scores

**Impact**:
- Dramatically reduces manual transcription time (5 min → 30 sec per page)
- Improves accuracy through validation
- Catches transcription errors automatically

**LangGraph Workflow**:
```python
from langgraph.graph import StateGraph

class CensusExtractionState(TypedDict):
    image_path: str
    ocr_text: str
    extracted_household: list[dict]
    validation_results: list[dict]
    conflicts: list[dict]
    final_data: list[dict]

workflow = StateGraph(CensusExtractionState)
workflow.add_node("ocr", perform_ocr)
workflow.add_node("extract", extract_structured_data)
workflow.add_node("validate", validate_against_known_data)
workflow.add_node("resolve_conflicts", human_in_loop_resolution)
workflow.add_node("save", save_to_database)

# Conditional routing
def should_resolve_conflicts(state):
    return "resolve_conflicts" if state["conflicts"] else "save"

workflow.add_conditional_edges("validate", should_resolve_conflicts)
```

---

### 8. Citation Format Assistant (Medium Value)

**LangChain Capabilities**: Few-shot learning + structured output (Pydantic)

**Value Proposition**: Auto-generate Evidence Explained citations from source metadata or raw text

**Use Case**:
- User pastes obituary text or provides source metadata
- Agent generates proper footnote, short footnote, bibliography entries
- Follows Evidence Explained standards automatically

**Impact**:
- Eliminates citation formatting headaches
- Ensures consistency across all sources
- Teaches proper citation format

**Implementation**:
```python
from langchain_core.prompts import FewShotPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

class Citation(BaseModel):
    footnote: str
    short_footnote: str
    bibliography: str

parser = PydanticOutputParser(pydantic_object=Citation)

examples = [
    {
        "input": "1930 US Census, Pennsylvania, Philadelphia County, enumeration district 51-627",
        "output": Citation(
            footnote='1930 U.S. census, Philadelphia County, Pennsylvania, enumeration district 51-627...',
            short_footnote='1930 U.S. census, Philadelphia County, ED 51-627.',
            bibliography='U.S. Census Bureau. 1930 U.S. Census, Population Schedule...'
        )
    }
]

few_shot_prompt = FewShotPromptTemplate(
    examples=examples,
    example_prompt=...,
    prefix="Generate Evidence Explained citations for genealogical sources.",
    suffix="Source: {input}\n{format_instructions}",
)
```

---

### 9. Relationship Path Finder (Medium Value)

**LangChain Capabilities**: LangGraph graph traversal + explanation chains

**Value Proposition**: Calculate complex multi-generational relationships with human-readable explanations

**Use Case**:
```
User: "How am I related to John Dorsey Iams (1921-2008)?"
Agent: [Traverses family tree graph]
Output: "John Dorsey Iams is your great-uncle (your grandfather's brother).
         The connection path is: You → Father (Michael) → Grandfather (Donald)
         → Donald's brother (John Dorsey)."
```

**Impact**:
- Clarifies confusing distant relationships
- Educational for family researchers
- Useful for reunion planning

**Implementation**:
```python
from langgraph.graph import StateGraph

class RelationshipState(TypedDict):
    person_a_id: int
    person_b_id: int
    path: list[tuple[int, str]]  # (person_id, relationship_type)
    relationship_name: str
    explanation: str

def find_common_ancestor(state: RelationshipState):
    """BFS to find shortest path through family tree."""
    # Graph traversal implementation
    pass

def calculate_relationship(state: RelationshipState):
    """Convert path to relationship name (cousin, uncle, etc.)."""
    # Apply relationship calculation rules
    pass

def generate_explanation(state: RelationshipState):
    """Create human-readable explanation."""
    # Use LLM to format path as natural language
    pass
```

---

### 10. Migration Pattern Analyzer (Medium Value)

**LangChain Capabilities**: RAG over combined family data + LLM summarization

**Value Proposition**: Detect geographic/temporal patterns across multiple families (chain migration, settlement clusters)

**Use Case**:
```
Query: "Show migration patterns for Pennsylvania Germans 1850-1900"
Output:
- Identified 47 families in dataset
- Primary origin: Rhineland-Palatinate (65%), Bavaria (20%), Württemberg (15%)
- Common route: Bremen → Baltimore → Philadelphia → Lancaster County
- Peak years: 1852-1854 (post-1848 revolution), 1880-1885 (economic migration)
- Settlement clusters: Lancaster (35%), Lebanon (25%), York (20%)
- Occupations: Farmer (60%), craftsman (25%), laborer (15%)
```

**Impact**:
- Reveals broader historical patterns
- Contextualizes individual family moves
- Identifies research opportunities (others in migration chain)

**Implementation**:
```python
from langchain.chains import MapReduceDocumentsChain

# 1. Aggregate residence events for cohort
residence_events = db.execute("""
    SELECT p.PersonID, e.Date, e.Place, e.Details
    FROM PersonTable p
    JOIN EventTable e ON e.OwnerID = p.PersonID
    WHERE e.EventType = 13  -- Residence
      AND e.Date BETWEEN ? AND ?
      AND p.Ethnicity = ?
""", (start_year, end_year, ethnicity))

# 2. Embed events for clustering
embeddings = embed_locations(residence_events)
clusters = DBSCAN().fit(embeddings)

# 3. LLM summarization
summary_chain = MapReduceDocumentsChain(
    llm_chain=...,
    reduce_chain=...,
)
pattern_summary = summary_chain.run(residence_events)
```

---

## Implementation Priority

### Phase 1: Quick Wins (Foundation)
**Timeline**: 2-4 weeks

1. **Citation Format Assistant** (#8)
   - Immediate utility
   - Low complexity
   - Teaches Evidence Explained standards

2. **Conversational Research Assistant** (#4)
   - Core UX improvement
   - Builds on existing tools
   - Enables exploratory research

**Dependencies**: LangChain v1.0 agent framework, existing QueryService tools

---

### Phase 2: High-Impact Features (Transformation)
**Timeline**: 6-8 weeks

1. **Source Document RAG Pipeline** (#1)
   - Transformative capability
   - Requires document ingestion infrastructure
   - Biggest time savings (60-80% reduction in document review)

2. **Multi-Source Conflict Resolution Agent** (#2)
   - Solves core genealogy pain point
   - Complex but high educational value
   - Builds on Evidence Explained principles

**Dependencies**: Vector database setup, document loaders, LangGraph workflows

---

### Phase 3: Advanced Features (Automation)
**Timeline**: 8-12 weeks

1. **Research Gap Advisor** (#3)
   - Requires training data (successful research paths)
   - High value once trained
   - Network effects (learns from all users)

2. **Agentic Census Extraction** (#7)
   - Requires vision models (GPT-4V)
   - High automation potential
   - Reduces transcription time by 90%

**Dependencies**: Historical success data, vision model API access, validation workflows

---

### Phase 4: Contextual Enhancements (Polish)
**Timeline**: Ongoing

1. **Historical Context Augmentation** (#5)
2. **Relationship Path Finder** (#9)
3. **Migration Pattern Analyzer** (#10)
4. **Cross-Record Entity Resolution** (#6)

**Dependencies**: External knowledge bases, graph algorithms, clustering tools

---

## Technical Architecture

### Core Components

```
rmagent/
├── agent/
│   ├── lc/                          # LangChain v1.0 integration
│   │   ├── tools.py                # Custom tools (QueryService, BiographyGenerator)
│   │   ├── chains.py               # LCEL chains (citation, extraction)
│   │   ├── agents.py               # Agent orchestration
│   │   └── workflows/              # LangGraph workflows
│   │       ├── conflict_resolution.py
│   │       ├── census_extraction.py
│   │       └── research_advisor.py
│   ├── llm_provider.py             # Multi-provider abstraction (existing)
│   └── genealogy_agent.py          # Simple agent (existing)
├── rag/                            # RAG infrastructure (NEW)
│   ├── vectorstore.py              # Chroma/FAISS wrapper
│   ├── embeddings.py               # Embedding utilities
│   ├── document_loaders.py         # PDF, OCR, structured data
│   └── retrievers.py               # Custom retrievers with metadata
├── knowledge/                       # External knowledge (NEW)
│   ├── historical_context/         # Wikipedia, historical DBs
│   ├── citation_examples/          # Evidence Explained templates
│   └── research_patterns/          # Successful research paths
└── cli/
    └── commands/
        ├── chat.py                 # NEW: Conversational interface
        └── rag_admin.py            # NEW: Index management
```

---

## Data Requirements

### Vector Stores
- **Source documents**: ~10GB per 1000 documents (census, obituaries, etc.)
- **Person profiles**: ~100MB per 10,000 persons
- **Historical context**: ~5GB (Wikipedia historical events)

### APIs
- OpenAI embeddings: $0.13 per 1M tokens (~$1/month for typical use)
- Anthropic Claude: $3 per MTok input, $15 per MTok output
- Cohere reranking: $1 per 1000 searches

---

## Evaluation Metrics

### Success Criteria by Feature

1. **Source Document RAG**
   - Retrieval precision: >90% (correct document in top-3)
   - Answer accuracy: >85% (verified against ground truth)
   - Time savings: >60% vs manual review

2. **Conflict Resolution**
   - Expert agreement: >80% (genealogists agree with AI recommendation)
   - Reasoning quality: >4/5 (expert rating)
   - Time savings: >70% vs manual resolution

3. **Research Gap Advisor**
   - Recommendation success rate: >50% (suggested record found)
   - User satisfaction: >4/5 stars
   - Adoption: >30% of users try recommended sources

4. **Conversational Assistant**
   - Task completion: >80% (user achieves research goal)
   - User satisfaction: >4/5 stars
   - Engagement: >5 turns per session (indicates useful conversation)

---

## Risks and Mitigations

### Technical Risks
1. **Hallucination**: LLMs generating false genealogical facts
   - *Mitigation*: Structured output, citation requirements, confidence scores
   - *Validation*: Cross-reference with source documents

2. **Vector store scaling**: Performance degradation with >100K documents
   - *Mitigation*: Partitioning by source type, date range, geographic region
   - *Optimization*: FAISS with IVF indexing, query caching

3. **API costs**: $100-500/month for heavy users
   - *Mitigation*: Local embeddings (sentence-transformers), caching, rate limiting
   - *Alternative*: Ollama for non-critical tasks

### Genealogical Risks
1. **Privacy concerns**: Living persons in public models
   - *Mitigation*: 110-year rule enforcement, PII filtering, local-only mode
   - *Compliance*: GDPR-style data handling

2. **Source misattribution**: Wrong citation attached to fact
   - *Mitigation*: Strict metadata tracking, citation validation
   - *Audit trail*: All AI-generated claims linked to source

---

## References

### LangChain Documentation
- LangChain v1.0 Migration Guide: https://docs.langchain.com/oss/python/migrate/langchain-v1
- LangGraph Documentation: https://langchain-ai.github.io/langgraph/
- RAG Best Practices: https://python.langchain.com/docs/use_cases/question_answering/

### Genealogical Standards
- Evidence Explained: https://www.evidenceexplained.com/
- BCG Standards: https://bcgcertification.org/resources/standard.html
- FamilySearch Research Wiki: https://www.familysearch.org/en/wiki/Main_Page

### Related Projects
- Gramps AI Plugin: https://github.com/gramps-project/addons
- FamilySearch Discovery: https://www.familysearch.org/discovery/
- Ancestry Hints: https://www.ancestry.com/cs/hints

---

## Next Steps

1. **Technical Spike** (1 week)
   - Prototype Source Document RAG with 10 sample documents
   - Benchmark retrieval precision and latency
   - Estimate API costs

2. **User Research** (2 weeks)
   - Interview 5-10 genealogists about pain points
   - Validate feature prioritization
   - Identify must-have vs. nice-to-have capabilities

3. **MVP Scope** (Phase 1)
   - Implement Citation Format Assistant
   - Add conversational interface to existing CLI
   - Gather user feedback

4. **Iteration**
   - Monitor usage metrics (engagement, satisfaction)
   - Iterate based on user feedback
   - Expand to Phase 2 features

---

## Changelog

- **2025-10-13**: Initial document creation
  - Ranked 10 LangChain features by value
  - Defined implementation phases
  - Outlined technical architecture
