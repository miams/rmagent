# Developer Guide - RMAgent

Comprehensive guide for developers working on RMAgent internals, adding features, and contributing code.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Core Components](#core-components)
- [Key Design Patterns](#key-design-patterns)
- [Development Setup](#development-setup)
- [Adding New Features](#adding-new-features)
- [Extension Points](#extension-points)
- [API Reference](#api-reference)
- [Testing Guide](#testing-guide)
- [Code Quality](#code-quality)
- [Contributing](#contributing)

---

## Architecture Overview

RMAgent follows a layered architecture:

```
┌─────────────────────────────────────┐
│         CLI Layer (cli/)            │  ← User interaction
├─────────────────────────────────────┤
│    Generators (generators/)         │  ← Output generation
├─────────────────────────────────────┤
│      AI Agent (agent/)              │  ← LLM integration
├─────────────────────────────────────┤
│    Core Library (rmlib/)            │  ← Database access
└─────────────────────────────────────┘
       ↓
┌─────────────────────────────────────┐
│   RootsMagic SQLite Database        │
└─────────────────────────────────────┘
```

### Design Principles

1. **Separation of Concerns** - Each module has a single, well-defined responsibility
2. **Provider Pattern** - Abstract LLM providers for flexibility
3. **Data-Driven** - Use configuration files (YAML, .env) over hardcoded values
4. **Type Safety** - Pydantic models for all data structures
5. **Testability** - Design for unit and integration testing

---

## Project Structure

```
rmagent/
├── rmagent/                   # Main Python package
│   ├── __init__.py
│   ├── agent/                # AI agent layer
│   │   ├── __init__.py
│   │   ├── llm_provider.py  # LLM abstraction
│   │   ├── prompts.py       # Prompt loading (YAML)
│   │   ├── genealogy_agent.py # Main agent
│   │   └── tools.py         # Agent tools
│   │
│   ├── cli/                  # Command-line interface
│   │   ├── __init__.py
│   │   ├── main.py          # CLI entry point
│   │   └── commands/        # Command implementations
│   │       ├── person.py
│   │       ├── bio.py
│   │       ├── quality.py
│   │       ├── ask.py
│   │       ├── timeline.py
│   │       ├── export.py
│   │       └── search.py
│   │
│   ├── config/              # Configuration management
│   │   ├── __init__.py
│   │   └── config.py        # Pydantic settings
│   │
│   ├── generators/          # Output generators
│   │   ├── __init__.py
│   │   ├── biography.py     # Biography generator
│   │   ├── timeline.py      # Timeline generator
│   │   ├── quality_report.py # Quality report generator
│   │   └── hugo_exporter.py # Hugo export
│   │
│   └── rmlib/               # Core library (no external dependencies)
│       ├── __init__.py
│       ├── database.py      # Database connection
│       ├── models.py        # Pydantic data models
│       ├── queries.py       # SQL query service
│       ├── quality.py       # Data quality validation
│       └── parsers/         # Format parsers
│           ├── date_parser.py
│           ├── place_parser.py
│           ├── name_parser.py
│           └── blob_parser.py
│
├── config/                  # Runtime configuration
│   ├── .env.example        # Configuration template
│   └── prompts/            # Prompt YAML files
│       ├── biography.yaml
│       ├── quality.yaml
│       ├── qa.yaml
│       └── timeline.yaml
│
├── tests/                   # Test suite
│   ├── unit/               # Unit tests (245+ tests)
│   └── integration/        # Integration tests (19 tests)
│
├── data_reference/          # Schema documentation
│   └── RM11_*.md           # 18 reference documents
│
└── docs/                    # Project documentation
    └── *.md
```

### Module Dependencies

**Dependency Flow (top to bottom):**
```
cli/
 ↓
generators/
 ↓
agent/
 ↓
rmlib/  (no dependencies on other rmagent modules)
```

**Key Rule:** `rmlib/` is the foundation and must not depend on higher layers.

---

## Core Components

### 1. rmlib/ - Core Library

**Purpose:** Database access, data parsing, data quality validation

**Key Classes:**

**RMDatabase** (`database.py`)
```python
class RMDatabase:
    """Context manager for RootsMagic database connections.

    Handles:
    - SQLite connection with ICU extension (RMNOCASE collation)
    - Row factory for dict-like results
    - Automatic connection cleanup
    """

    def __init__(self, db_path: str, icu_extension_path: str | None = None)
    def query_all(self, sql: str, params: tuple = ()) -> list[dict]
    def query_one(self, sql: str, params: tuple = ()) -> dict | None
    def query_value(self, sql: str, params: tuple = ()) -> Any
```

**QueryService** (`queries.py`)
```python
class QueryService:
    """High-level query interface for RootsMagic data.

    Provides 15 optimized query patterns:
    - Person with primary name
    - All events for person
    - Family relationships (parents, spouses, children)
    - Ancestor/descendant queries
    - Source/citation queries
    """

    def get_person_with_primary_name(self, person_id: int) -> dict
    def get_events_for_person(self, person_id: int) -> list[dict]
    def get_parents(self, person_id: int) -> dict
    def get_spouses(self, person_id: int) -> list[dict]
    def get_children(self, person_id: int) -> list[dict]
```

**Data Parsers** (`parsers/`)
- `date_parser.py` - Parse 24-char RM11 date format
- `place_parser.py` - Parse comma-delimited place hierarchy
- `name_parser.py` - Handle primary/alternate names
- `blob_parser.py` - Parse XML BLOB fields

**DataQualityValidator** (`quality.py`)
```python
class DataQualityValidator:
    """Run 24 validation rules across 6 categories.

    Categories:
    1. Required - Essential field combinations
    2. Logical - Date and relationship consistency
    3. Integrity - Foreign key references
    4. Sources - Citation quality
    5. Dates - Date format validity
    6. Values - Value range constraints
    """

    def validate_all(self) -> QualityReport
    def validate_category(self, category: str) -> QualityReport
```

### 2. agent/ - AI Agent Layer

**Purpose:** LLM integration, prompt management, agentic workflows

**Key Classes:**

**LLMProvider** (`llm_provider.py`)
```python
@dataclass
class LLMResponse:
    """Standardized LLM response."""
    text: str
    usage: UsageInfo
    model: str
    provider: str

class BaseLLMProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse

    @abstractmethod
    def stream_generate(self, prompt: str, system_prompt: str | None = None) -> Iterator[str]

class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider."""

class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider."""

class OllamaProvider(BaseLLMProvider):
    """Ollama local model provider."""
```

**PromptRegistry** (`prompts.py`)
```python
class PromptRegistry:
    """Load prompts from YAML files.

    Features:
    - Default prompts from config/prompts/
    - User overrides from config/prompts/custom/
    - Provider-specific variants (anthropic, openai, ollama)
    - Caching for performance
    """

    def get_prompt(self, key: str, provider: str | None = None) -> PromptTemplate
    def list_prompts(self) -> Iterable[str]
```

**GenealogyAgent** (`genealogy_agent.py`)
```python
class GenealogyAgent:
    """Orchestrate AI-powered genealogy workflows.

    Workflows:
    - Biography generation
    - Data quality analysis
    - Interactive Q&A
    - Timeline synthesis
    """

    def generate_biography(self, person_id: int, length: BiographyLength) -> str
    def analyze_quality(self, quality_report: QualityReport) -> str
    def ask(self, question: str, context: str | None = None) -> str
    def generate_timeline_summary(self, events: list[dict]) -> str
```

### 3. generators/ - Output Generators

**Purpose:** Generate structured output formats

**BiographyGenerator** (`biography.py`)
```python
class BiographyGenerator:
    """Generate biographical narratives.

    Modes:
    - Template-based (no AI, fast)
    - AI-powered (requires LLM provider)

    Lengths: SHORT, STANDARD, COMPREHENSIVE
    Citation Styles: FOOTNOTE, PARENTHETICAL, NARRATIVE
    """

    def generate(
        self,
        person_id: int,
        length: BiographyLength = BiographyLength.STANDARD,
        citation_style: CitationStyle = CitationStyle.FOOTNOTE,
        use_ai: bool = True
    ) -> Biography
```

**TimelineGenerator** (`timeline.py`)
```python
class TimelineGenerator:
    """Generate TimelineJS3 timelines.

    Formats:
    - JSON (for embedding)
    - HTML (standalone viewer)

    Features:
    - Life phase grouping
    - Family event inclusion
    - Historical context
    """

    def generate(
        self,
        person_id: int,
        format: TimelineFormat = TimelineFormat.JSON,
        group_by_phase: bool = False,
        include_family: bool = False
    ) -> str
```

**QualityReportGenerator** (`quality_report.py`)
```python
class QualityReportGenerator:
    """Generate data quality reports.

    Formats: MARKDOWN, HTML, CSV

    Features:
    - Severity filtering
    - Category filtering
    - Sample limiting
    - Statistics summary
    """

    def generate(
        self,
        quality_report: QualityReport,
        format: ReportFormat = ReportFormat.MARKDOWN
    ) -> str
```

**HugoExporter** (`hugo_exporter.py`)
```python
class HugoExporter:
    """Export biographies to Hugo static site format.

    Features:
    - YAML front matter
    - Batch export
    - Timeline integration
    - Media path configuration
    """

    def export_person(
        self,
        person_id: int,
        output_dir: Path,
        include_timeline: bool = True
    ) -> Path
```

### 4. cli/ - Command-Line Interface

**Purpose:** User-facing command-line interface

**Structure:**
```python
# cli/main.py - Entry point
@click.group()
def cli():
    """RMAgent CLI entry point."""
    pass

# cli/commands/*.py - Command implementations
@cli.command()
@click.argument("person_id", type=int)
@click.option("--events", is_flag=True)
def person(person_id: int, events: bool):
    """Query person information."""
    pass
```

**Command Pattern:**
1. Parse arguments (Click decorators)
2. Load configuration
3. Instantiate services (database, agent, generator)
4. Execute workflow
5. Format and display output (Rich library)

### 5. config/ - Configuration Management

**Purpose:** Centralized configuration with Pydantic

**AppConfig** (`config.py`)
```python
class DatabaseConfig(BaseSettings):
    database_path: str
    icu_extension_path: str

class LLMConfig(BaseSettings):
    default_provider: str
    temperature: float = 0.2
    max_tokens: int = 3000
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    ollama_model: str = "llama3.1"

class AppConfig(BaseSettings):
    database: DatabaseConfig
    llm: LLMConfig
    output: OutputConfig
    privacy: PrivacyConfig
    logging: LoggingConfig

    def build_provider(self) -> BaseLLMProvider:
        """Factory method for LLM providers."""
        pass
```

---

## Key Design Patterns

### 1. Provider Pattern (LLM Abstraction)

**Problem:** Support multiple LLM providers with different APIs

**Solution:** Abstract base class with concrete implementations

```python
# Abstract interface
class BaseLLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        pass

# Concrete implementations
class AnthropicProvider(BaseLLMProvider):
    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        # Anthropic-specific implementation
        response = self.client.messages.create(...)
        return LLMResponse(...)

class OpenAIProvider(BaseLLMProvider):
    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        # OpenAI-specific implementation
        response = self.client.chat.completions.create(...)
        return LLMResponse(...)
```

**Benefits:**
- Easy to add new providers
- Consistent interface for all LLMs
- Testable with mock providers

### 2. Context Manager Pattern (Database)

**Problem:** Ensure database connections are properly closed

**Solution:** Implement `__enter__` and `__exit__`

```python
class RMDatabase:
    def __enter__(self) -> "RMDatabase":
        self.conn = sqlite3.connect(self.db_path)
        self._load_icu_extension()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()

# Usage
with RMDatabase("data/family.rmtree") as db:
    result = db.query_one("SELECT * FROM PersonTable WHERE PersonID = ?", (1,))
    # Connection automatically closed on exit
```

### 3. Registry Pattern (Prompts)

**Problem:** Manage multiple prompts with variants

**Solution:** Registry with lazy loading and caching

```python
class PromptRegistry:
    def __init__(self):
        self._cache: dict[str, PromptTemplate] = {}

    def get_prompt(self, key: str, provider: str | None = None) -> PromptTemplate:
        cache_key = f"{key}:{provider}" if provider else key

        if cache_key not in self._cache:
            # Load from YAML
            prompt_data = self._load_yaml(f"config/prompts/{key}.yaml")
            # Check for provider-specific variant
            if provider and "provider_overrides" in prompt_data:
                # Use provider-specific template
                pass
            self._cache[cache_key] = self._yaml_to_template(prompt_data)

        return self._cache[cache_key]
```

### 4. Pydantic Models (Data Validation)

**Problem:** Validate data from SQLite database

**Solution:** Use Pydantic for runtime type checking

```python
from pydantic import BaseModel, Field

class Person(BaseModel):
    PersonID: int
    Surname: str
    Given: str
    BirthYear: int | None = Field(None, ge=-10000, le=3000)
    DeathYear: int | None = Field(None, ge=-10000, le=3000)
    IsPrivate: bool = False

# Usage
person_data = db.query_one("SELECT * FROM PersonTable WHERE PersonID = ?", (1,))
person = Person(**person_data)  # Validates automatically
```

---

## Development Setup

### Prerequisites

- Python 3.11+
- uv package manager
- Git
- RootsMagic 11 database for testing

### Installation

```bash
# Clone repository
git clone git@github.com:miams/rmagent.git
cd rmagent

# Install with development dependencies
uv sync --extra dev

# Verify installation
uv run pytest
```

### Development Tools

**Code Formatting:**
```bash
# Format code with black
uv run black rmagent/ tests/

# Check formatting
uv run black --check rmagent/ tests/
```

**Linting:**
```bash
# Run ruff linter
uv run ruff check rmagent/ tests/

# Auto-fix issues
uv run ruff check --fix rmagent/ tests/
```

**Type Checking:**
```bash
# Run mypy
uv run mypy rmagent/

# Type check specific file
uv run mypy rmagent/rmlib/database.py
```

### Running Tests

See [TESTING.md](TESTING.md) for comprehensive testing guide.

```bash
# Run all unit tests
uv run pytest tests/unit/

# Run with coverage
uv run pytest --cov=rmagent --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_database.py

# Run integration tests (requires API keys)
uv run pytest tests/integration/ -m ""
```

---

## Adding New Features

### Add a New CLI Command

**1. Create command file:**

```python
# cli/commands/analyze.py

import click
from rmagent.config.config import load_app_config
from rmagent.rmlib.database import RMDatabase

@click.command()
@click.argument("person_id", type=int)
@click.option("--detailed", is_flag=True, help="Show detailed analysis")
def analyze(person_id: int, detailed: bool):
    """Analyze person's genealogical data."""

    # Load configuration
    config = load_app_config()

    # Connect to database
    with RMDatabase(config.database.database_path) as db:
        # Query data
        person = db.query_one("SELECT * FROM PersonTable WHERE PersonID = ?", (person_id,))

        # Process and display
        click.echo(f"Analyzing person {person_id}...")

        if detailed:
            # Show detailed analysis
            pass
```

**2. Register command:**

```python
# cli/main.py

from rmagent.cli.commands.analyze import analyze

@click.group()
def cli():
    pass

cli.add_command(analyze)
```

**3. Add tests:**

```python
# tests/unit/test_cli_analyze.py

from click.testing import CliRunner
from rmagent.cli.main import cli

def test_analyze_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["analyze", "1"])
    assert result.exit_code == 0
    assert "Analyzing person 1" in result.output
```

### Add a New Generator

**1. Create generator class:**

```python
# generators/relationship_graph.py

from pathlib import Path
from rmagent.rmlib.database import RMDatabase
from rmagent.rmlib.queries import QueryService

class RelationshipGraphGenerator:
    """Generate relationship graphs in GraphViz format."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def generate(
        self,
        person_id: int,
        max_generations: int = 3,
        include_spouses: bool = True
    ) -> str:
        """Generate DOT format graph."""

        with RMDatabase(self.db_path) as db:
            query_service = QueryService(db)

            # Build graph
            graph = self._build_graph(query_service, person_id, max_generations)

            # Convert to DOT format
            return self._to_dot(graph)

    def _build_graph(self, query_service, person_id, max_generations):
        # Recursive graph building logic
        pass

    def _to_dot(self, graph):
        # Convert to GraphViz DOT format
        pass

    def export(self, person_id: int, output_path: Path):
        """Export graph to file."""
        graph = self.generate(person_id)
        output_path.write_text(graph)
```

**2. Add CLI command:**

```python
# cli/commands/graph.py

@click.command()
@click.argument("person_id", type=int)
@click.option("--output", "-o", type=click.Path(), help="Output file")
def graph(person_id: int, output: str):
    """Generate relationship graph."""

    config = load_app_config()
    generator = RelationshipGraphGenerator(config.database.database_path)

    if output:
        generator.export(person_id, Path(output))
        click.echo(f"Graph exported to {output}")
    else:
        graph = generator.generate(person_id)
        click.echo(graph)
```

**3. Add tests:**

```python
# tests/unit/test_relationship_graph.py

def test_graph_generation():
    generator = RelationshipGraphGenerator("data/test.rmtree")
    graph = generator.generate(person_id=1, max_generations=2)

    assert "digraph" in graph
    assert "person_1" in graph
```

### Add a New LLM Provider

**1. Implement provider class:**

```python
# agent/llm_provider.py

class GoogleGeminiProvider(BaseLLMProvider):
    """Google Gemini provider."""

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-pro",
        temperature: float = 0.2,
        max_tokens: int = 3000
    ):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = genai.GenerativeModel(model_name=model)

    def generate(self, prompt: str, system_prompt: str | None = None) -> LLMResponse:
        # Combine system and user prompts
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        # Call Gemini API
        response = self.client.generate_content(
            full_prompt,
            generation_config={
                "temperature": self.temperature,
                "max_output_tokens": self.max_tokens,
            }
        )

        # Return standardized response
        return LLMResponse(
            text=response.text,
            usage=UsageInfo(
                prompt_tokens=response.usage_metadata.prompt_token_count,
                completion_tokens=response.usage_metadata.candidates_token_count,
                total_tokens=response.usage_metadata.total_token_count,
                cost=self._calculate_cost(response.usage_metadata)
            ),
            model=self.model,
            provider="gemini"
        )

    def _calculate_cost(self, usage):
        # Gemini pricing
        input_cost = usage.prompt_token_count * 0.00000035  # $0.35/1M tokens
        output_cost = usage.candidates_token_count * 0.00000105  # $1.05/1M tokens
        return input_cost + output_cost
```

**2. Add to configuration:**

```python
# config/config.py

class LLMConfig(BaseSettings):
    # ... existing fields ...
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-pro"

class AppConfig(BaseSettings):
    def build_provider(self) -> BaseLLMProvider:
        provider = self.llm.default_provider

        if provider == "gemini":
            return GoogleGeminiProvider(
                api_key=self.llm.gemini_api_key,
                model=self.llm.gemini_model,
                temperature=self.llm.temperature,
                max_tokens=self.llm.max_tokens
            )
        # ... other providers ...
```

**3. Add tests:**

```python
# tests/unit/test_llm_provider.py

def test_gemini_provider():
    provider = GoogleGeminiProvider(
        api_key="test-key",
        model="gemini-pro"
    )

    # Test with mock
    with patch.object(provider.client, 'generate_content') as mock_generate:
        mock_response = Mock()
        mock_response.text = "Test response"
        mock_response.usage_metadata.prompt_token_count = 10
        mock_generate.return_value = mock_response

        response = provider.generate("Test prompt")

        assert response.text == "Test response"
        assert response.provider == "gemini"
```

### Add a New Prompt

**1. Create YAML file:**

```yaml
# config/prompts/census_extraction.yaml

key: census_extraction
version: "2025-01-08"
description: "Extract structured data from census records"

# Required variables
required_variables:
  - ocr_text
  - person_context

# Default prompt
template: |
  Extract census information from the following OCR text.

  Person Context:
  {person_context}

  OCR Text:
  {ocr_text}

  Extract:
  - Name (as recorded)
  - Age
  - Birth year (calculated)
  - Birth place
  - Occupation
  - Residence
  - Household members

  Format as JSON.

# Provider-specific variants
provider_overrides:
  anthropic:
    template: |
      You are an expert in genealogical census research.
      Analyze the following census record OCR output and extract structured data.

      [More detailed instructions for Claude]

      {ocr_text}

# Few-shot examples
few_shots:
  - user: "Extract census data for John Smith..."
    assistant: '{"name": "John Smith", "age": 45, ...}'
```

**2. Use in code:**

```python
# generators/census_extractor.py

from rmagent.agent.prompts import get_prompt, render_prompt

class CensusExtractor:
    def extract(self, ocr_text: str, person_context: str) -> dict:
        # Get provider-specific prompt
        provider = self.config.llm.default_provider
        prompt = render_prompt(
            "census_extraction",
            {
                "ocr_text": ocr_text,
                "person_context": person_context
            },
            provider=provider
        )

        # Generate with LLM
        response = self.agent.generate(prompt)

        # Parse JSON response
        return json.loads(response)
```

---

## Extension Points

### Custom Data Quality Rules

Add new validation rules to `rmlib/quality.py`:

```python
class DataQualityValidator:
    def rule_7_1_census_consistency(self) -> list[dict]:
        """Check census record consistency across years."""

        issues = []

        # Query census events
        census_events = self.db.query_all("""
            SELECT PersonID, Date, Details
            FROM EventTable
            WHERE EventType = 15  -- Census FactType
            ORDER BY PersonID, SortDate
        """)

        # Check for inconsistencies
        for person_id, events in groupby(census_events, key=lambda e: e["PersonID"]):
            events = list(events)

            # Check age progression
            for i in range(len(events) - 1):
                current = events[i]
                next_event = events[i + 1]

                age_current = self._extract_age(current["Details"])
                age_next = self._extract_age(next_event["Details"])

                if age_next < age_current:
                    issues.append({
                        "person_id": person_id,
                        "message": f"Census age decreased: {age_current} → {age_next}",
                        "severity": "high"
                    })

        return issues
```

### Custom Exporters

Create new export formats by subclassing or following the generator pattern:

```python
# generators/gedcom_exporter.py

class GEDCOMExporter:
    """Export to GEDCOM format."""

    def export(self, person_ids: list[int], output_path: Path):
        """Export people to GEDCOM."""

        with RMDatabase(self.db_path) as db:
            gedcom_data = self._build_gedcom(db, person_ids)
            output_path.write_text(gedcom_data)

    def _build_gedcom(self, db, person_ids):
        lines = ["0 HEAD", "1 GEDC", "2 VERS 5.5.1"]

        for person_id in person_ids:
            person = db.query_one("SELECT * FROM PersonTable WHERE PersonID = ?", (person_id,))
            lines.extend(self._person_to_gedcom(person))

        lines.append("0 TRLR")
        return "\n".join(lines)

    def _person_to_gedcom(self, person):
        # Convert person to GEDCOM INDI record
        return [
            f"0 @I{person['PersonID']}@ INDI",
            f"1 NAME {person['Given']} /{person['Surname']}/",
            # ... more GEDCOM fields
        ]
```

---

## API Reference

### Core API Usage Examples

**Query Database:**

```python
from rmagent.rmlib.database import RMDatabase
from rmagent.rmlib.queries import QueryService

with RMDatabase("data/family.rmtree") as db:
    query_service = QueryService(db)

    # Get person with primary name
    person = query_service.get_person_with_primary_name(1)
    print(f"{person['Given']} {person['Surname']}")

    # Get all events
    events = query_service.get_events_for_person(1)
    for event in events:
        print(f"{event['Date']} - {event['EventType']}")

    # Get family
    parents = query_service.get_parents(1)
    spouses = query_service.get_spouses(1)
    children = query_service.get_children(1)
```

**Use LLM Provider:**

```python
from rmagent.config.config import load_app_config

config = load_app_config()
provider = config.build_provider()

response = provider.generate(
    prompt="Generate a biography for John Smith born 1850.",
    system_prompt="You are a professional genealogist."
)

print(response.text)
print(f"Tokens: {response.usage.total_tokens}")
print(f"Cost: ${response.usage.cost:.4f}")
```

**Generate Biography:**

```python
from rmagent.generators.biography import BiographyGenerator, BiographyLength, CitationStyle

generator = BiographyGenerator(
    db_path="data/family.rmtree",
    agent=None  # None for template-based
)

bio = generator.generate(
    person_id=1,
    length=BiographyLength.STANDARD,
    citation_style=CitationStyle.FOOTNOTE
)

print(bio.render_markdown())
```

**Validate Data Quality:**

```python
from rmagent.rmlib.quality import DataQualityValidator

with RMDatabase("data/family.rmtree") as db:
    validator = DataQualityValidator(db)

    # Run all rules
    report = validator.validate_all()

    print(f"Total issues: {report.total_issues}")
    print(f"Critical: {report.critical_count}")

    # Run specific category
    logical_report = validator.validate_category("logical")
    for issue in logical_report.issues[:10]:
        print(f"Rule {issue.rule_id}: {issue.message}")
```

---

## Testing Guide

See [TESTING.md](TESTING.md) for comprehensive testing documentation.

### Test Structure

```
tests/
├── unit/
│   ├── conftest.py           # Shared fixtures
│   ├── test_database.py     # Database tests (17 tests)
│   ├── test_models.py       # Pydantic tests (34 tests)
│   ├── test_date_parser.py  # Date parsing (44 tests)
│   └── ...
└── integration/
    ├── test_llm_providers.py # Mock tests (12 tests)
    └── test_real_providers.py # Real API tests (7 tests)
```

### Writing Tests

**Unit Test Example:**

```python
import pytest
from rmagent.rmlib.database import RMDatabase

@pytest.fixture
def database():
    """Provide test database connection."""
    with RMDatabase("data/test.rmtree") as db:
        yield db

def test_query_person(database):
    """Test person query."""
    person = database.query_one(
        "SELECT * FROM PersonTable WHERE PersonID = ?",
        (1,)
    )

    assert person is not None
    assert person["PersonID"] == 1
    assert "Surname" in person
```

**Mock LLM Test:**

```python
from unittest.mock import Mock, patch
from rmagent.agent.llm_provider import AnthropicProvider

def test_generate_biography_with_mock():
    """Test biography generation with mocked LLM."""

    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(text="John Smith was born...")]
    mock_response.usage = Mock(input_tokens=100, output_tokens=200)
    mock_client.messages.create.return_value = mock_response

    provider = AnthropicProvider(client=mock_client)
    response = provider.generate("Generate biography")

    assert "John Smith" in response.text
    assert response.usage.total_tokens == 300
```

---

## Code Quality

### Pre-commit Checklist

Before committing code:

```bash
# 1. Format code
uv run black rmagent/ tests/

# 2. Lint code
uv run ruff check --fix rmagent/ tests/

# 3. Type check
uv run mypy rmagent/

# 4. Run tests
uv run pytest

# 5. Check coverage
uv run pytest --cov=rmagent --cov-report=term
```

### Code Style Guidelines

**Imports:**
```python
# Standard library first
import json
import logging
from pathlib import Path

# Third-party packages
import click
from pydantic import BaseModel

# Local imports
from rmagent.rmlib.database import RMDatabase
from rmagent.rmlib.queries import QueryService
```

**Type Hints:**
```python
# Always use type hints
def get_person(person_id: int) -> dict | None:
    pass

# Use Union for older Python versions if needed
from typing import Union
def get_person(person_id: int) -> Union[dict, None]:
    pass
```

**Docstrings:**
```python
def generate_biography(
    person_id: int,
    length: BiographyLength = BiographyLength.STANDARD
) -> Biography:
    """Generate biographical narrative for a person.

    Args:
        person_id: PersonID from RootsMagic database
        length: Biography length (SHORT, STANDARD, COMPREHENSIVE)

    Returns:
        Biography object with text, sources, and metadata

    Raises:
        PersonNotFoundError: If person_id doesn't exist
        DatabaseError: If database query fails

    Example:
        >>> generator = BiographyGenerator("data/family.rmtree")
        >>> bio = generator.generate(person_id=1, length=BiographyLength.STANDARD)
        >>> print(bio.text)
    """
    pass
```

### Performance Guidelines

**Database Queries:**
- Use indexes (PersonID, EventID)
- Limit results when appropriate
- Avoid N+1 queries (use JOINs)
- Close connections promptly (use context managers)

**LLM Calls:**
- Cache results when possible
- Use appropriate token limits
- Implement retry logic
- Track usage and costs

**Memory Management:**
- Stream large results
- Use generators for iteration
- Clear caches periodically
- Profile memory usage for large databases

---

## Contributing

### Contribution Workflow

See [CONTRIBUTING.md](CONTRIBUTING.md) for complete guidelines.

**Quick Start:**

```bash
# 1. Fork and clone
git clone git@github.com:YOUR_USERNAME/rmagent.git
cd rmagent

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Make changes
# ... edit code ...

# 4. Run quality checks
uv run pytest
uv run black .
uv run ruff check .
uv run mypy rmagent/

# 5. Commit
git add .
git commit -m "feat: add your feature"

# 6. Push and create PR
git push origin feature/your-feature-name
```

### Pull Request Guidelines

**PR Checklist:**
- [ ] All tests passing
- [ ] Code formatted with black
- [ ] No ruff linting errors
- [ ] Type checking passes
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Tests added for new features

**Commit Message Format:**

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add census extraction feature
fix: resolve database connection timeout
docs: update API reference
test: add integration tests for export
refactor: simplify prompt loading logic
perf: optimize query service
```

### Code Review Process

1. Automated checks run (CI/CD)
2. Maintainer reviews code
3. Feedback addressed
4. PR approved and merged
5. Changelog updated

---

## Additional Resources

### Documentation

- [README.md](README.md) - Project overview
- [INSTALL.md](INSTALL.md) - Installation guide
- [USAGE.md](USAGE.md) - CLI reference
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration guide
- [TESTING.md](TESTING.md) - Testing guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [FAQ.md](FAQ.md) - Common questions

### Schema Reference

- `data_reference/RM11_Schema_Reference.md` - Complete database schema
- `data_reference/RM11_Date_Format.md` - Date encoding specification
- `data_reference/RM11_BLOB_*.md` - XML BLOB parsing
- `data_reference/RM11_Query_Patterns.md` - SQL patterns

### External Resources

- [RootsMagic](https://www.rootsmagic.com/) - Official software
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Anthropic Claude API](https://docs.anthropic.com/)
- [OpenAI API](https://platform.openai.com/docs/)
- [Ollama](https://ollama.com/library) - Local models

---

**Questions?** Open an issue on [GitHub](https://github.com/miams/rmagent/issues)
