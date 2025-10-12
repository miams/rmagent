"""Integration tests for LLM provider abstraction.

These tests verify provider interface compliance and error handling
using mocked clients (no real API calls required).
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from rmagent.agent.llm_provider import (
    AnthropicProvider,
    LLMError,
    LLMResult,
    OllamaProvider,
    OpenAIProvider,
    TokenUsage,
    get_provider,
)


class TestProviderFactory:
    """Test provider registry and factory."""

    def test_get_provider_anthropic(self):
        """Verify factory returns AnthropicProvider."""
        # Mock to avoid requiring API key
        mock_client = Mock()
        provider = get_provider("anthropic", client=mock_client)
        assert isinstance(provider, AnthropicProvider)

    def test_get_provider_openai(self):
        """Verify factory returns OpenAIProvider."""
        mock_client = Mock()
        provider = get_provider("openai", client=mock_client)
        assert isinstance(provider, OpenAIProvider)

    def test_get_provider_ollama(self):
        """Verify factory returns OllamaProvider."""
        mock_client = Mock()
        provider = get_provider("ollama", client=mock_client)
        assert isinstance(provider, OllamaProvider)

    def test_get_provider_unknown_raises(self):
        """Verify unknown provider raises LLMError."""
        with pytest.raises(LLMError, match="Unknown provider"):
            get_provider("invalid_provider")


class TestAnthropicProvider:
    """Test Anthropic provider with mocked client."""

    def test_generate_returns_llm_result(self):
        """Verify generate() returns structured LLMResult."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Test response")]
        mock_response.usage = Mock(input_tokens=10, output_tokens=20)
        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(client=mock_client, model="claude-3-5-sonnet-20241022")
        result = provider.generate("Test prompt")

        assert isinstance(result, LLMResult)
        assert result.text == "Test response"
        assert result.model == "claude-3-5-sonnet-20241022"
        assert result.usage.prompt_tokens == 10
        assert result.usage.completion_tokens == 20
        assert result.cost > 0  # Pricing calculated

    def test_generate_with_max_tokens_override(self):
        """Verify max_tokens can be overridden."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Response")]
        mock_response.usage = Mock(input_tokens=5, output_tokens=10)
        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(client=mock_client, max_tokens=1024)
        provider.generate("Prompt", max_tokens=2048)

        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 2048

    def test_generate_retries_on_failure(self):
        """Verify retry logic on provider failure."""
        mock_client = Mock()
        mock_client.messages.create.side_effect = [
            Exception("API Error"),
            Exception("API Error"),
            Mock(
                content=[Mock(text="Success")],
                usage=Mock(input_tokens=5, output_tokens=5),
            ),
        ]

        provider = AnthropicProvider(client=mock_client)
        result = provider.generate("Prompt")

        assert result.text == "Success"
        assert mock_client.messages.create.call_count == 3


class TestOpenAIProvider:
    """Test OpenAI provider with mocked client."""

    def test_generate_returns_llm_result(self):
        """Verify generate() returns structured LLMResult."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="GPT response"))]
        mock_response.usage = Mock(prompt_tokens=15, completion_tokens=25)
        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(client=mock_client, model="gpt-4o")
        result = provider.generate("Test prompt")

        assert isinstance(result, LLMResult)
        assert result.text == "GPT response"
        assert result.model == "gpt-4o"
        assert result.usage.prompt_tokens == 15
        assert result.usage.completion_tokens == 25


class TestOllamaProvider:
    """Test Ollama provider with mocked client."""

    def test_generate_returns_llm_result(self):
        """Verify generate() returns structured LLMResult."""
        mock_client = Mock()
        mock_client.generate.return_value = {
            "response": "Llama response",
            "eval_count": 100,
        }

        provider = OllamaProvider(client=mock_client, model="llama3.1")
        result = provider.generate("Test prompt")

        assert isinstance(result, LLMResult)
        assert result.text == "Llama response"
        assert result.model == "llama3.1"
        assert result.usage.completion_tokens == 100
        assert result.cost is None  # Ollama is free


class TestProviderInterfaceCompliance:
    """Verify all providers implement the LLMProvider interface consistently."""

    @pytest.mark.parametrize(
        "provider_class,mock_setup",
        [
            (
                AnthropicProvider,
                lambda m: setattr(
                    m.messages,
                    "create",
                    lambda **kw: Mock(
                        content=[Mock(text="Text")],
                        usage=Mock(input_tokens=5, output_tokens=5),
                    ),
                ),
            ),
            (
                OpenAIProvider,
                lambda m: setattr(
                    m.chat.completions,
                    "create",
                    lambda **kw: Mock(
                        choices=[Mock(message=Mock(content="Text"))],
                        usage=Mock(prompt_tokens=5, completion_tokens=5),
                    ),
                ),
            ),
            (
                OllamaProvider,
                lambda m: setattr(
                    m, "generate", lambda **kw: {"response": "Text", "eval_count": 10}
                ),
            ),
        ],
    )
    def test_all_providers_return_llm_result(self, provider_class, mock_setup):
        """All providers must return LLMResult with consistent fields."""
        mock_client = Mock()
        mock_setup(mock_client)

        provider = provider_class(client=mock_client)
        result = provider.generate("Test")

        assert isinstance(result, LLMResult)
        assert isinstance(result.text, str)
        assert isinstance(result.model, str)
        assert isinstance(result.usage, TokenUsage)
        assert result.usage.total_tokens >= 0
