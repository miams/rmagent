"""
LLM provider abstraction with multi-provider support.

Implements Anthropic, OpenAI, and Ollama adapters with retry handling,
token usage metrics, structured debug logging, and a minimal factory for
provider lookup.
"""

from __future__ import annotations

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Tuple, Type

try:  # Optional dependency
    import anthropic
except ImportError:  # pragma: no cover - handled at runtime
    anthropic = None  # type: ignore

try:  # Optional dependency
    import openai
except ImportError:  # pragma: no cover - handled at runtime
    openai = None  # type: ignore

try:  # Optional dependency
    import ollama
except ImportError:  # pragma: no cover - handled at runtime
    ollama = None  # type: ignore


class LLMError(RuntimeError):
    """Raised when a provider call fails."""


@dataclass
class TokenUsage:
    """Tracks token usage for a generation."""

    prompt_tokens: int = 0
    completion_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class LLMResult:
    """Standard response envelope for provider calls."""

    text: str
    model: str
    usage: TokenUsage
    cost: Optional[float] = None
    raw_response: Any = None


@dataclass
class RetryConfig:
    """Simple retry configuration."""

    max_attempts: int = 3
    backoff_seconds: float = 0.5


class LLMProvider(ABC):
    """
    Base provider interface with retry handling.

    Subclasses should override `_invoke` and return an `LLMResult`.
    """

    def __init__(
        self,
        model: str,
        default_max_tokens: Optional[int] = None,
        retry_config: Optional[RetryConfig] = None,
        pricing_per_1k: Optional[Tuple[float, float]] = None,
    ) -> None:
        self.model = model
        self.default_max_tokens = default_max_tokens
        self.retry_config = retry_config or RetryConfig()
        self.prompt_cost_per_1k, self.completion_cost_per_1k = (
            pricing_per_1k if pricing_per_1k else (0.0, 0.0)
        )

    def generate(self, prompt: str, **kwargs: Any) -> LLMResult:
        """Invoke provider with retry semantics."""
        attempts = 0
        last_error: Optional[Exception] = None
        invoke_kwargs = dict(kwargs)
        if "max_tokens" not in invoke_kwargs and self.default_max_tokens is not None:
            invoke_kwargs["max_tokens"] = self.default_max_tokens
        while attempts < self.retry_config.max_attempts:
            try:
                start = time.perf_counter()
                result = self._invoke(prompt, **invoke_kwargs)
                elapsed = time.perf_counter() - start
                result = self._with_cost(result)
                self._log_debug(prompt, result, elapsed, invoke_kwargs)
                return result
            except Exception as exc:  # pragma: no cover - retry path
                last_error = exc
                attempts += 1
                if attempts >= self.retry_config.max_attempts:
                    break
                time.sleep(self.retry_config.backoff_seconds)
        raise LLMError(str(last_error)) from last_error

    def _with_cost(self, result: LLMResult) -> LLMResult:
        if result.cost is not None:
            return result
        cost = 0.0
        if self.prompt_cost_per_1k:
            cost += (result.usage.prompt_tokens / 1000.0) * self.prompt_cost_per_1k
        if self.completion_cost_per_1k:
            cost += (result.usage.completion_tokens / 1000.0) * self.completion_cost_per_1k
        if cost == 0.0:
            return result
        return LLMResult(
            text=result.text,
            model=result.model,
            usage=result.usage,
            cost=cost,
            raw_response=result.raw_response,
        )

    @abstractmethod
    def _invoke(self, prompt: str, **kwargs: Any) -> LLMResult:
        """Concrete providers implement this call."""

    def _log_debug(self, prompt: str, result: LLMResult, elapsed: float, kwargs: Dict[str, Any]) -> None:
        debug_logger = logging.getLogger("rmtool.llm_debug")
        if not debug_logger.isEnabledFor(logging.DEBUG):
            return
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": self.__class__.__name__,
            "model": result.model,
            "max_tokens": kwargs.get("max_tokens"),
            "temperature": kwargs.get("temperature"),
            "prompt_tokens": result.usage.prompt_tokens,
            "completion_tokens": result.usage.completion_tokens,
            "total_tokens": result.usage.total_tokens,
            "duration_ms": round(elapsed * 1000, 3),
            "prompt": prompt,
            "response": result.text,
        }
        debug_logger.debug(json.dumps(log_entry))


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 1024,
        temperature: float = 0.2,
        client: Optional[Any] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> None:
        if anthropic is None and client is None:
            raise LLMError("anthropic package is required but not installed")
        super().__init__(
            model=model,
            default_max_tokens=max_tokens,
            retry_config=retry_config,
            pricing_per_1k=(0.003, 0.015),
        )
        self.temperature = temperature
        api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if client is not None:
            self.client = client
        else:
            self.client = anthropic.Anthropic(api_key=api_key)  # type: ignore[arg-type]

    def _invoke(self, prompt: str, **kwargs: Any) -> LLMResult:
        max_tokens = kwargs.get("max_tokens") or self.default_max_tokens
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=kwargs.get("temperature", self.temperature),
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        content_blocks = getattr(response, "content", [])
        text_parts = []
        for block in content_blocks:
            block_text = getattr(block, "text", None)
            if block_text:
                text_parts.append(block_text)
        text = "\n".join(text_parts).strip()
        usage = getattr(response, "usage", None)
        prompt_tokens = getattr(usage, "input_tokens", 0)
        completion_tokens = getattr(usage, "output_tokens", 0)
        return LLMResult(
            text=text,
            model=self.model,
            usage=TokenUsage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens),
            raw_response=response,
        )


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        max_tokens: Optional[int] = None,
        temperature: float = 0.2,
        client: Optional[Any] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> None:
        if openai is None and client is None:
            raise LLMError("openai package is required but not installed")
        super().__init__(
            model=model,
            default_max_tokens=max_tokens,
            retry_config=retry_config,
            pricing_per_1k=(0.005, 0.015),
        )
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if client is not None:
            self.client = client
        else:
            self.client = openai.OpenAI(api_key=api_key)  # type: ignore[arg-type]

        self.temperature = temperature

    def _invoke(self, prompt: str, **kwargs: Any) -> LLMResult:
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", self.default_max_tokens),
            messages=[{"role": "user", "content": prompt}],
        )
        choice = response.choices[0]
        text = choice.message.content or ""
        usage = response.usage or {}
        return LLMResult(
            text=text.strip(),
            model=self.model,
            usage=TokenUsage(
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
            ),
            raw_response=response,
        )


class OllamaProvider(LLMProvider):
    """Ollama local model provider."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: str = "llama3.1",
        temperature: float = 0.2,
        client: Optional[Any] = None,
        retry_config: Optional[RetryConfig] = None,
    ) -> None:
        if ollama is None and client is None:
            raise LLMError("ollama package is required but not installed")
        super().__init__(
            model=model,
            default_max_tokens=None,
            retry_config=retry_config,
            pricing_per_1k=None,
        )
        self.temperature = temperature
        if client is not None:
            self.client = client
        else:
            kwargs: Dict[str, Any] = {}
            if base_url or os.getenv("OLLAMA_BASE_URL"):
                kwargs["host"] = base_url or os.getenv("OLLAMA_BASE_URL")
            self.client = ollama.Client(**kwargs)  # type: ignore[operator]

    def _invoke(self, prompt: str, **kwargs: Any) -> LLMResult:
        options = kwargs.get("options", {})
        options.setdefault("temperature", kwargs.get("temperature", self.temperature))
        response = self.client.generate(model=self.model, prompt=prompt, options=options)
        text = response.get("response", "").strip()
        usage = response.get("eval_count", 0)
        return LLMResult(
            text=text,
            model=self.model,
            usage=TokenUsage(prompt_tokens=0, completion_tokens=usage),
            raw_response=response,
        )


ProviderFactory = Callable[..., LLMProvider]
PROVIDER_REGISTRY: Dict[str, ProviderFactory] = {
    "anthropic": AnthropicProvider,
    "openai": OpenAIProvider,
    "ollama": OllamaProvider,
}


def register_provider(name: str, factory: ProviderFactory) -> None:
    """Register a provider factory."""
    PROVIDER_REGISTRY[name.lower()] = factory


def get_provider(name: str, **kwargs: Any) -> LLMProvider:
    """Instantiate a provider by registry name."""
    factory = PROVIDER_REGISTRY.get(name.lower())
    if factory is None:
        raise LLMError(f"Unknown provider '{name}'")
    return factory(**kwargs)


__all__ = [
    "LLMProvider",
    "LLMResult",
    "LLMError",
    "TokenUsage",
    "RetryConfig",
    "AnthropicProvider",
    "OpenAIProvider",
    "OllamaProvider",
    "register_provider",
    "get_provider",
]
