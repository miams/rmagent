"""
Tests for rmagent.agent.llm_provider.

Uses dummy providers to avoid calling external APIs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rmagent.agent.llm_provider import (
    LLMError,
    LLMProvider,
    LLMResult,
    RetryConfig,
    TokenUsage,
    get_provider,
    register_provider,
)


class DummyProvider(LLMProvider):
    """Simple provider that returns deterministic responses."""

    def __init__(self, responses, **kwargs):
        super().__init__(model="dummy", **kwargs)
        self._responses = list(responses)

    def _invoke(self, prompt: str, **kwargs):
        if not self._responses:
            raise LLMError("No responses configured")
        text = self._responses.pop(0)
        return LLMResult(
            text=text,
            model=self.model,
            usage=TokenUsage(
                prompt_tokens=len(prompt.split()), completion_tokens=len(text.split())
            ),
        )


def test_generate_returns_result():
    provider = DummyProvider(["hello world"])
    result = provider.generate("hi there")
    assert result.text == "hello world"
    assert result.usage.total_tokens > 0


def test_retry_logic_retries_then_succeeds():
    class FlakyProvider(LLMProvider):
        def __init__(self):
            super().__init__("flaky", retry_config=RetryConfig(max_attempts=3, backoff_seconds=0))
            self.invocations = 0

        def _invoke(self, prompt: str, **kwargs):
            self.invocations += 1
            if self.invocations < 2:
                raise LLMError("temporary failure")
            return LLMResult(
                text="ok", model=self.model, usage=TokenUsage(prompt_tokens=1, completion_tokens=1)
            )

    provider = FlakyProvider()
    result = provider.generate("prompt")
    assert result.text == "ok"
    assert provider.invocations == 2


def test_retry_exhaustion_raises():
    class AlwaysFailProvider(LLMProvider):
        def __init__(self):
            super().__init__("fail", retry_config=RetryConfig(max_attempts=2, backoff_seconds=0))
            self.invocations = 0

        def _invoke(self, prompt: str, **kwargs):
            self.invocations += 1
            raise LLMError("nope")

    provider = AlwaysFailProvider()
    with pytest.raises(LLMError):
        provider.generate("prompt")
    assert provider.invocations == 2


def test_cost_calculation_applies_pricing():
    provider = DummyProvider(["response"], pricing_per_1k=(0.002, 0.004))
    result = provider.generate("one two three")
    assert result.cost is not None
    assert result.cost > 0


def test_registry_register_and_get():
    register_provider("dummy", DummyProvider)
    provider = get_provider("dummy", responses=["hi"])
    assert isinstance(provider, DummyProvider)
    assert provider.generate("prompt").text == "hi"


def test_unknown_provider_raises():
    with pytest.raises(LLMError):
        get_provider("does-not-exist")
