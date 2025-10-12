# Testing Guide - RMAgent

Comprehensive guide to testing RMAgent.

## Table of Contents

- [Test Suite Overview](#test-suite-overview)
- [Running Tests](#running-tests)
- [Test Organization](#test-organization)
- [Writing Tests](#writing-tests)
- [Coverage Analysis](#coverage-analysis)
- [Integration Testing](#integration-testing)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting](#troubleshooting)

---

## Test Suite Overview

### Test Statistics (as of v0.2.0)

- **Total Tests:** 279 (260 unit + 19 integration)
- **Pass Rate:** 100%
- **Execution Time:** ~25s (with caching)
- **Overall Coverage:** 27% (90%+ on critical modules)

### Test Framework

- **pytest** - Test runner and fixtures
- **pytest-cov** - Coverage reporting
- **pytest-mock** - Mocking utilities

### Test Types

1. **Unit Tests** (`tests/unit/`) - 260 tests
   - Test individual functions and classes
   - Fast execution (<10s without database operations)
   - High coverage (65-99% per module)

2. **Integration Tests** (`tests/integration/`) - 19 tests
   - Test multi-provider LLM system
   - 12 mock-based tests (fast, free)
   - 7 real API tests (optional, skip by default)

---

## Running Tests

### Quick Start

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=rmagent --cov-report=html

# Open coverage report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Run Specific Test Files

```bash
# Run single test file
uv run pytest tests/unit/test_database.py

# Run multiple test files
uv run pytest tests/unit/test_database.py tests/unit/test_queries.py

# Run all unit tests
uv run pytest tests/unit/

# Run all integration tests (mock only)
uv run pytest tests/integration/
```

### Run Specific Tests

```bash
# Run specific test function
uv run pytest tests/unit/test_database.py::test_connection

# Run specific test class
uv run pytest tests/unit/test_date_parser.py::TestRMDateParsing

# Run tests matching pattern
uv run pytest -k "test_date"
```

### Verbose Output

```bash
# Verbose mode (-v)
uv run pytest -v

# Very verbose mode (-vv)
uv run pytest -vv

# Show print statements (-s)
uv run pytest -s

# Show test durations
uv run pytest --durations=10
```

### Parallel Execution

```bash
# Install pytest-xdist
uv pip install pytest-xdist

# Run tests in parallel
uv run pytest -n auto  # Use all CPU cores
uv run pytest -n 4     # Use 4 workers
```

---

## Test Organization

### Directory Structure

```
tests/
├── unit/                    # Unit tests
│   ├── conftest.py         # Shared fixtures (caching)
│   ├── test_database.py    # Database tests (17 tests)
│   ├── test_models.py      # Pydantic model tests (34 tests)
│   ├── test_date_parser.py # Date parsing tests (44 tests)
│   ├── test_blob_parser.py # BLOB parsing tests (24 tests)
│   ├── test_place_parser.py # Place parsing tests (55 tests)
│   ├── test_name_parser.py # Name parsing tests (34 tests)
│   ├── test_queries.py     # Query service tests (16 tests)
│   ├── test_quality.py     # Quality validation tests (5 tests)
│   ├── test_llm_provider.py # LLM provider tests
│   ├── test_agent.py       # Agent tests
│   ├── test_biography_generator.py # Biography tests (24 tests)
│   ├── test_quality_report.py # Quality report tests (13 tests)
│   ├── test_timeline_generator.py # Timeline tests (29 tests)
│   ├── test_hugo_exporter.py # Hugo export tests (24 tests)
│   └── test_cli.py         # CLI tests (23 tests)
│
└── integration/             # Integration tests
    ├── __init__.py
    ├── README.md           # Integration test documentation
    ├── test_llm_providers.py # Mock-based tests (12 tests)
    └── test_real_providers.py # Real API tests (7 tests)
```

### Test Coverage by Module

| Module | Tests | Coverage | Status |
|--------|-------|----------|--------|
| llm_provider.py | 18 | 90% | ✅ Excellent |
| quality.py | 5 | 91% | ✅ Excellent |
| database.py | 17 | 76% | ✅ Good |
| blob_parser.py | 24 | 65% | ✅ Good |
| date_parser.py | 44 | 59% | ⚠️ Adequate |
| prompts.py | 3 | 68% | ⚠️ Adequate |
| place_parser.py | 55 | 99% | ✅ Excellent |
| name_parser.py | 34 | 96% | ✅ Excellent |
| queries.py | 16 | 91% | ✅ Excellent |

---

## Writing Tests

### Basic Test Structure

```python
import pytest
from rmagent.rmlib.database import RMDatabase

def test_database_connection():
    """Test basic database connection."""
    with RMDatabase("data/Iiams.rmtree") as db:
        result = db.query_value("SELECT COUNT(*) FROM PersonTable")
        assert result > 0
        assert isinstance(result, int)
```

### Using Fixtures

```python
@pytest.fixture
def database():
    """Provide database connection for tests."""
    with RMDatabase("data/Iiams.rmtree") as db:
        yield db

def test_query_person(database):
    """Test person query."""
    person = database.query_one(
        "SELECT * FROM PersonTable WHERE PersonID = ?",
        (1,)
    )
    assert person is not None
    assert person["PersonID"] == 1
```

### Parametrized Tests

```python
@pytest.mark.parametrize("date_string,expected_year", [
    ("D.+18960302..+00000000..", 1896),
    ("D.+19210405..+00000000..", 1921),
    ("D.+20000615..+00000000..", 2000),
])
def test_date_parsing(date_string, expected_year):
    """Test date parsing with various formats."""
    parsed = parse_rm_date(date_string)
    assert parsed.year == expected_year
```

### Testing Exceptions

```python
def test_person_not_found():
    """Test PersonNotFoundError is raised."""
    with pytest.raises(PersonNotFoundError) as exc_info:
        query_service.get_person_with_primary_name(99999999)

    assert "not found" in str(exc_info.value)
```

### Mocking

```python
from unittest.mock import Mock, patch

def test_llm_provider_with_mock():
    """Test LLM provider with mocked client."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.content = [Mock(text="Test response")]
    mock_response.usage = Mock(input_tokens=10, output_tokens=20)
    mock_client.messages.create.return_value = mock_response

    provider = AnthropicProvider(client=mock_client)
    result = provider.generate("Test prompt")

    assert result.text == "Test response"
    assert result.usage.prompt_tokens == 10
```

### Test Naming Conventions

```python
# Good test names (descriptive)
def test_database_connection_with_invalid_path_raises_error():
    pass

def test_date_parser_handles_bc_dates_correctly():
    pass

def test_biography_generator_respects_privacy_flags():
    pass

# Bad test names (vague)
def test_database():
    pass

def test_dates():
    pass

def test_bio():
    pass
```

---

## Coverage Analysis

### Generate Coverage Report

```bash
# HTML report (recommended)
uv run pytest --cov=rmagent --cov-report=html

# Terminal report
uv run pytest --cov=rmagent --cov-report=term

# Both
uv run pytest --cov=rmagent --cov-report=html --cov-report=term
```

### View Coverage Report

```bash
# Open HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Coverage by Module

```bash
# Show coverage for specific module
uv run pytest --cov=rmagent.rmlib.database --cov-report=term

# Show missing lines
uv run pytest --cov=rmagent --cov-report=term-missing
```

### Coverage Configuration

**pyproject.toml:**
```toml
[tool.coverage.run]
source = ["rmagent"]
omit = [
    "*/tests/*",
    "*/conftest.py",
    "*/__init__.py",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
```

---

## Integration Testing

### Mock-Based Integration Tests

These tests are **always run by default** (fast, free):

```bash
# Run mock integration tests
uv run pytest tests/integration/

# Expected output:
# 12 passed, 7 deselected in 1.87s
```

**What they test:**
- Provider factory registration
- LLM provider interfaces
- Response handling
- Token usage tracking
- Cost calculation
- Error handling

### Real API Integration Tests

These tests are **skipped by default** (require API keys, cost money):

```bash
# Run ALL tests (mock + real API)
uv run pytest tests/integration/ -m ""

# Run specific provider
uv run pytest tests/integration/ -m anthropic_api
uv run pytest tests/integration/ -m openai_api
uv run pytest tests/integration/ -m ollama_api
```

**Prerequisites:**
1. Valid API keys in `config/.env`
2. Ollama running locally (for Ollama tests)
3. Billing enabled (Anthropic/OpenAI)

**Cost:**
- Full run: ~$0.002 per execution
- Per provider: ~$0.001 per execution
- Ollama: Free

### Test Markers

```python
# Mock test (always runs)
def test_anthropic_provider():
    pass

# Real API test (skipped by default)
@pytest.mark.real_api
@pytest.mark.anthropic_api
@pytest.mark.skipif(not HAS_ANTHROPIC_KEY, reason="API key not configured")
def test_anthropic_real_api():
    pass
```

### Configuration

**pyproject.toml:**
```toml
[tool.pytest.ini_options]
addopts = "-v --cov=rmagent --cov-report=html --cov-report=term -m 'not real_api'"
markers = [
    "real_api: tests that make real API calls (skipped by default)",
    "anthropic_api: tests that require Anthropic API key",
    "openai_api: tests that require OpenAI API key",
    "ollama_api: tests that require Ollama running locally",
    "slow: tests that take >5 seconds to run",
]
```

---

## Continuous Integration

### GitHub Actions Workflow

**.github/workflows/test.yml:**

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"

    - name: Install uv
      run: curl -LsSf https://astral.sh/uv/install.sh | sh

    - name: Install dependencies
      run: uv sync --extra dev

    - name: Run tests
      run: uv run pytest --cov=rmagent --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        fail_ci_if_error: true
```

### Pre-commit Hooks

**.pre-commit-config.yaml:**

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

**Install:**
```bash
pip install pre-commit
pre-commit install
```

---

## Troubleshooting

### Tests Timing Out

**Problem:** `test_quality.py` times out (>30s)

**Solution:** Caching is now automatic! First run builds cache, subsequent runs use cache.

```bash
# First run (slow, builds cache)
uv run pytest tests/unit/test_quality.py  # ~40s

# Subsequent runs (fast, uses cache)
uv run pytest tests/unit/test_quality.py  # ~0.3s
```

Cache is stored in `.pytest_cache/quality_cache/` and auto-invalidates when database changes.

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'rmagent'`

**Solution:**
```bash
# Reinstall in development mode
uv sync

# Or with pip
pip install -e .
```

### Database Not Found

**Problem:** `FileNotFoundError: data/Iiams.rmtree`

**Solution:**
```bash
# Check database exists
ls -l data/*.rmtree

# Update path in config/.env
RM_DATABASE_PATH=data/your-database.rmtree
```

### Integration Tests Skipped

**Problem:** "7 deselected" when running integration tests

**Solution:** This is expected! Real API tests are skipped by default.

To run them:
```bash
# Run all tests (including real API)
uv run pytest tests/integration/ -m ""

# Configure API keys in config/.env first
```

### Coverage Not Generated

**Problem:** No `htmlcov/` directory created

**Solution:**
```bash
# Ensure pytest-cov is installed
uv pip install pytest-cov

# Run with coverage flag
uv run pytest --cov=rmagent --cov-report=html

# Check for errors in output
```

### Slow Test Execution

**Problem:** Tests take >60 seconds

**Solution:**
```bash
# Use pytest-xdist for parallel execution
uv pip install pytest-xdist
uv run pytest -n auto

# Skip slow tests
uv run pytest -m "not slow"

# Run without coverage (faster)
uv run pytest
```

---

## Best Practices

### 1. Test-Driven Development (TDD)

Write tests before implementation:

```python
# 1. Write test first (it will fail)
def test_new_feature():
    result = new_feature(input_data)
    assert result == expected_output

# 2. Implement feature
def new_feature(data):
    return processed_data

# 3. Run test (it should pass)
uv run pytest tests/unit/test_new_feature.py
```

### 2. Test Isolation

Each test should be independent:

```python
# Good (isolated)
def test_create_person(database):
    person_id = create_person(database, name="John")
    cleanup(database, person_id)  # Clean up after test

# Bad (dependent on previous test)
def test_query_person():
    # Assumes person was created by previous test
    person = get_person(1)
```

### 3. Meaningful Assertions

```python
# Good (specific assertions)
def test_biography_length():
    bio = generate_biography(person_id=1, length=BiographyLength.SHORT)
    assert 200 <= len(bio.text) <= 500
    assert bio.sections is not None
    assert "birth" in bio.text.lower()

# Bad (vague assertion)
def test_biography():
    bio = generate_biography(person_id=1)
    assert bio  # Too vague
```

### 4. Test Documentation

```python
def test_date_parser_handles_bc_dates():
    """Test date parser correctly handles BC (Before Christ) dates.

    RM11 uses negative years for BC dates. This test verifies:
    1. BC dates are parsed correctly
    2. Year is negative
    3. Era flag is set to BC
    """
    date_string = "D.-00500101..+00000000.."  # 500 BC
    parsed = parse_rm_date(date_string)

    assert parsed.year == -500
    assert parsed.era == Era.BC
```

---

## Next Steps

- **Contributing:** See `CONTRIBUTING.md` for development workflow
- **CI/CD Setup:** Add GitHub Actions for automated testing
- **Coverage Goals:** Aim for 80%+ coverage on new code
- **Integration Tests:** Set up API keys for real provider testing

---

**Questions?** Check `FAQ.md` or open an issue on GitHub.
