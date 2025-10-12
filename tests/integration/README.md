# Integration Tests

Integration tests for RMAgent that verify end-to-end functionality including LLM provider integration, agent workflows, and database operations.

## Test Categories

### 1. Mock-Based Integration Tests (Always Run)

**File:** `test_llm_providers.py`

Tests provider abstraction, interface compliance, and error handling using **mocked clients** (no real API calls). These tests:
- Run by default with `pytest`
- Require no API credentials
- Execute quickly (<1s)
- Verify provider interface consistency

### 2. Real API Integration Tests (Optional)

**File:** `test_real_providers.py`

Tests actual API calls to verify provider integration. These tests:
- **Skip by default** (marked with `@pytest.mark.real_api`)
- Require valid API credentials
- Cost money (API usage fees)
- May be slow (network latency)

## Running Tests

### Default: Skip Real API Tests
```bash
# Run all tests EXCEPT real API calls (default behavior)
pytest tests/integration/

# Equivalent explicit command
pytest tests/integration/ -m "not real_api"
```

### Run Specific Provider Tests
```bash
# Only Anthropic real API tests
pytest tests/integration/ -m anthropic_api

# Only OpenAI real API tests
pytest tests/integration/ -m openai_api

# Only Ollama real API tests
pytest tests/integration/ -m ollama_api
```

### Run ALL Tests (Including Real APIs)
```bash
# Run everything, including real API calls
pytest tests/integration/ -m ""

# Or explicitly run real API tests only
pytest tests/integration/ -m real_api
```

### Combine Markers
```bash
# Run mock tests + Anthropic real API tests
pytest tests/integration/ -m "not (openai_api or ollama_api)"
```

## Prerequisites

### For Mock Tests (test_llm_providers.py)
- ✅ No prerequisites - always ready to run

### For Real API Tests (test_real_providers.py)

#### Anthropic
```bash
# Set API key in config/.env
ANTHROPIC_API_KEY=sk-ant-xxxxx
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

#### OpenAI
```bash
# Set API key in config/.env
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4o-mini
```

#### Ollama
```bash
# Install Ollama: https://ollama.com/download
ollama pull llama3.1
ollama serve  # Start server on http://localhost:11434

# Configure in config/.env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

## Test Status Indicators

When running real API tests, pytest will automatically skip unavailable providers:

```
tests/integration/test_real_providers.py::TestAnthropicRealAPI::test_simple_generation PASSED
tests/integration/test_real_providers.py::TestOpenAIRealAPI::test_simple_generation SKIPPED (OPENAI_API_KEY not configured)
tests/integration/test_real_providers.py::TestOllamaRealAPI::test_ollama_connection SKIPPED (Ollama not running on localhost:11434)
```

## Cost Considerations

Real API tests make actual provider calls:

| Provider | Estimated Cost per Test Run |
|----------|----------------------------|
| Anthropic Claude | ~$0.001-0.01 per test |
| OpenAI GPT-4o-mini | ~$0.0001-0.001 per test |
| Ollama (local) | Free |

**Recommendation:** Use mock tests during development, run real API tests before major releases.

## CI/CD Integration

For GitHub Actions or similar CI:

```yaml
# .github/workflows/test.yml
- name: Run tests (skip real API)
  run: pytest tests/integration/

- name: Run Anthropic integration tests
  if: secrets.ANTHROPIC_API_KEY
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: pytest tests/integration/ -m anthropic_api
```

## Writing New Integration Tests

### Mock-Based Test Pattern
```python
def test_new_feature():
    """Test feature with mocked provider."""
    mock_client = Mock()
    mock_client.messages.create.return_value = Mock(
        content=[Mock(text="Response")],
        usage=Mock(input_tokens=10, output_tokens=20)
    )

    provider = AnthropicProvider(client=mock_client)
    result = provider.generate("Test")

    assert result.text == "Response"
```

### Real API Test Pattern
```python
@pytest.mark.real_api
@pytest.mark.anthropic_api
@pytest.mark.skipif(not HAS_ANTHROPIC_KEY, reason="No API key")
def test_new_feature_real():
    """Test feature with real API (costs money)."""
    provider = AnthropicProvider()
    result = provider.generate("Test prompt")

    assert result.text
    assert result.cost > 0
```

## Troubleshooting

### "No module named 'anthropic'"
```bash
uv sync --extra dev
```

### "OPENAI_API_KEY not configured" (but you set it)
Check for placeholder value:
```bash
grep OPENAI_API_KEY config/.env
# Should NOT show: sk-xxxxx (placeholder)
```

### Ollama tests fail
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Pull required model
ollama pull llama3.1
```

## See Also

- Unit Tests: `tests/unit/`
- Provider Implementation: `rmagent/agent/llm_provider.py`
- Configuration: `config/.env`
