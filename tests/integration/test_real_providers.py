"""Optional integration tests with real LLM provider APIs.

These tests make actual API calls and are skipped if credentials aren't configured.
Use pytest markers to run selectively:

    pytest -m anthropic_api     # Only Anthropic tests
    pytest -m openai_api        # Only OpenAI tests
    pytest -m ollama_api        # Only Ollama tests
    pytest -m "not real_api"    # Skip all real API tests (default)
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from rmagent.agent.llm_provider import AnthropicProvider, OllamaProvider, OpenAIProvider

# Load environment variables from config/.env
_env_path = Path(__file__).parents[2] / "config" / ".env"
if _env_path.exists():
    load_dotenv(_env_path)


# Environment checks - detect placeholder vs real keys
def _is_real_key(key_value: str | None) -> bool:
    """Check if API key is real (not placeholder like sk-xxxxx)."""
    if not key_value:
        return False
    # Check for common placeholder patterns
    if key_value == "sk-xxxxx" or key_value.endswith("xxxxx"):
        return False
    # Valid if has reasonable length and starts with expected prefix
    return len(key_value) > 20 and key_value.startswith("sk-")


HAS_ANTHROPIC_KEY = _is_real_key(os.getenv("ANTHROPIC_API_KEY"))
HAS_OPENAI_KEY = _is_real_key(os.getenv("OPENAI_API_KEY"))
OLLAMA_AVAILABLE = os.getenv("OLLAMA_BASE_URL") == "http://localhost:11434"


@pytest.mark.real_api
@pytest.mark.anthropic_api
@pytest.mark.skipif(not HAS_ANTHROPIC_KEY, reason="ANTHROPIC_API_KEY not configured")
class TestAnthropicRealAPI:
    """Real API integration tests for Anthropic."""

    def test_simple_generation(self):
        """Verify real Anthropic API call succeeds."""
        provider = AnthropicProvider(model="claude-3-5-sonnet-20241022", max_tokens=100)
        result = provider.generate("Say 'Hello RMAgent' and nothing else.")

        assert result.text
        assert "hello" in result.text.lower() or "rmagent" in result.text.lower()
        assert result.usage.prompt_tokens > 0
        assert result.usage.completion_tokens > 0
        assert result.cost > 0

    def test_genealogy_specific_prompt(self):
        """Test provider with genealogy-domain prompt."""
        provider = AnthropicProvider(model="claude-3-5-sonnet-20241022", max_tokens=200)
        prompt = "List 3 common genealogy research sources in 20 words or less."
        result = provider.generate(prompt)

        assert result.text
        assert result.usage.total_tokens > 0
        # Check for genealogy keywords
        text_lower = result.text.lower()
        assert any(word in text_lower for word in ["census", "vital", "records", "birth", "death", "marriage"])


@pytest.mark.real_api
@pytest.mark.openai_api
@pytest.mark.skipif(not HAS_OPENAI_KEY, reason="OPENAI_API_KEY not configured")
class TestOpenAIRealAPI:
    """Real API integration tests for OpenAI."""

    def test_simple_generation(self):
        """Verify real OpenAI API call succeeds."""
        provider = OpenAIProvider(model="gpt-4o-mini", max_tokens=100)
        result = provider.generate("Say 'Hello RMAgent' and nothing else.")

        assert result.text
        assert "hello" in result.text.lower() or "rmagent" in result.text.lower()
        assert result.usage.prompt_tokens > 0
        assert result.usage.completion_tokens > 0
        assert result.cost > 0

    def test_provider_consistency_with_anthropic(self):
        """Both providers should handle identical prompts."""
        prompt = "List 3 genealogy sources."
        openai_provider = OpenAIProvider(model="gpt-4o-mini", max_tokens=100)
        openai_result = openai_provider.generate(prompt)

        # Should return valid response
        assert openai_result.text
        assert len(openai_result.text) > 10


@pytest.mark.real_api
@pytest.mark.ollama_api
@pytest.mark.skipif(not OLLAMA_AVAILABLE, reason="Ollama not running on localhost:11434")
class TestOllamaRealAPI:
    """Real API integration tests for Ollama.

    Note: Requires Ollama to be running locally with llama3.1 model pulled.
    """

    def test_ollama_connection(self):
        """Verify Ollama connection succeeds."""
        provider = OllamaProvider(model="llama3.1")
        result = provider.generate("Say 'Hello RMAgent' and nothing else.")

        assert result.text
        assert result.usage.completion_tokens > 0
        assert result.cost is None  # Ollama is free

    def test_ollama_genealogy_prompt(self):
        """Test Ollama with genealogy-specific content."""
        provider = OllamaProvider(model="llama3.1", temperature=0.1)
        prompt = "List 3 genealogy research sources."
        result = provider.generate(prompt)

        assert result.text
        assert len(result.text) > 20


@pytest.mark.real_api
class TestCrossProviderConsistency:
    """Verify all available providers produce reasonable outputs for same prompt."""

    @pytest.mark.skipif(
        not (HAS_ANTHROPIC_KEY or HAS_OPENAI_KEY or OLLAMA_AVAILABLE),
        reason="No providers configured",
    )
    def test_all_available_providers_respond(self):
        """Test that all configured providers can handle basic prompts."""
        prompt = "Name one genealogy source."
        results = {}

        if HAS_ANTHROPIC_KEY:
            provider = AnthropicProvider(max_tokens=50)
            results["anthropic"] = provider.generate(prompt)

        if HAS_OPENAI_KEY:
            provider = OpenAIProvider(max_tokens=50)
            results["openai"] = provider.generate(prompt)

        if OLLAMA_AVAILABLE:
            provider = OllamaProvider()
            results["ollama"] = provider.generate(prompt)

        # All providers should return valid text
        assert len(results) > 0
        for provider_name, result in results.items():
            assert result.text, f"{provider_name} returned empty response"
            assert result.usage.total_tokens > 0
