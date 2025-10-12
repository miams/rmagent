"""
Prompt templates for the RMAgent AI agent layer.

Provides reusable system prompts with version metadata and helper utilities
for formatting canonical genealogy workflows (biography, quality analysis,
timeline planning, and Q&A).

Prompts are loaded from YAML files in config/prompts/ with support for:
- Provider-specific variants (anthropic, openai, ollama)
- User overrides in config/prompts/custom/
- Backward-compatible API
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FewShotExample:
    """Minimal representation of a few-shot example."""

    user: str
    assistant: str


@dataclass(frozen=True)
class PromptTemplate:
    """Prompt text with metadata."""

    key: str
    version: str
    description: str
    template: str
    few_shots: list[FewShotExample]

    def render(self, substitutions: Mapping[str, str]) -> str:
        """Render the prompt template with safe substitution."""

        class _SafeDict(dict):
            def __missing__(self, key):
                return "{" + key + "}"

        safe_values = _SafeDict(**substitutions)
        return self.template.format_map(safe_values)


class PromptRegistry:
    """Load and manage prompts from YAML configuration files.

    Supports:
    - Default prompts from config/prompts/
    - User overrides from config/prompts/custom/
    - Provider-specific variants (anthropic, openai, ollama)
    - Fallback to default if provider variant not found
    """

    def __init__(
        self,
        default_dir: Path | None = None,
        custom_dir: Path | None = None,
        provider: str | None = None,
    ):
        """Initialize prompt registry.

        Args:
            default_dir: Default prompt directory (defaults to config/prompts/)
            custom_dir: Custom prompt directory (defaults to config/prompts/custom/)
            provider: LLM provider for provider-specific variants (anthropic, openai, ollama)
        """
        if default_dir is None:
            # Default to config/prompts/ relative to this file
            default_dir = Path(__file__).parent.parent.parent / "config" / "prompts"

        if custom_dir is None:
            custom_dir = default_dir / "custom"

        self.default_dir = default_dir
        self.custom_dir = custom_dir
        self.provider = provider
        self._cache: dict[str, PromptTemplate] = {}

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        """Load and parse YAML file."""
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _yaml_to_template(self, data: dict[str, Any], provider: str | None = None) -> PromptTemplate:
        """Convert YAML data to PromptTemplate.

        Args:
            data: YAML data dictionary
            provider: LLM provider for provider-specific variants
        """
        # Check for provider-specific override
        template_text = data["template"]
        if provider and "provider_overrides" in data:
            overrides = data["provider_overrides"]
            if provider in overrides and "template" in overrides[provider]:
                template_text = overrides[provider]["template"]
                logger.debug(f"Using {provider}-specific prompt for '{data['key']}'")

        # Parse few-shot examples
        few_shots = []
        if "few_shots" in data:
            for example in data["few_shots"]:
                few_shots.append(FewShotExample(user=example["user"], assistant=example["assistant"]))

        return PromptTemplate(
            key=data["key"],
            version=data["version"],
            description=data["description"],
            template=template_text,
            few_shots=few_shots,
        )

    def get_prompt(self, key: str, provider: str | None = None) -> PromptTemplate:
        """Get prompt by key, checking custom dir first.

        Args:
            key: Prompt key (biography, quality, qa, timeline)
            provider: LLM provider for provider-specific variants (overrides registry default)

        Returns:
            PromptTemplate instance

        Raises:
            KeyError: If prompt not found
        """
        # Use provided provider or fall back to registry default
        provider = provider or self.provider

        # Check cache (with provider-specific key)
        cache_key = f"{key}:{provider}" if provider else key
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Check custom directory first (user overrides)
        custom_path = self.custom_dir / f"{key}.yaml"
        if custom_path.exists():
            logger.info(f"Loading custom prompt: {key} from {custom_path}")
            data = self._load_yaml(custom_path)
            template = self._yaml_to_template(data, provider)
            self._cache[cache_key] = template
            return template

        # Fall back to default
        default_path = self.default_dir / f"{key}.yaml"
        if default_path.exists():
            logger.debug(f"Loading default prompt: {key} from {default_path}")
            data = self._load_yaml(default_path)
            template = self._yaml_to_template(data, provider)
            self._cache[cache_key] = template
            return template

        # Prompt not found
        available = list(self._list_available_prompts())
        raise KeyError(f"Unknown prompt key '{key}'. Available: {sorted(available)}")

    def _list_available_prompts(self) -> Iterable[str]:
        """List all available prompt keys."""
        prompts = set()

        # Scan default directory
        if self.default_dir.exists():
            for path in self.default_dir.glob("*.yaml"):
                if path.stem != "custom":  # Skip custom directory
                    prompts.add(path.stem)

        # Scan custom directory
        if self.custom_dir.exists():
            for path in self.custom_dir.glob("*.yaml"):
                prompts.add(path.stem)

        return prompts

    def list_prompts(self) -> Iterable[str]:
        """Return available prompt keys."""
        return self._list_available_prompts()


# Global registry instance
_registry: PromptRegistry | None = None


def _get_registry() -> PromptRegistry:
    """Get or create global prompt registry."""
    global _registry
    if _registry is None:
        # Try to get provider from config
        try:
            from rmagent.config.config import load_app_config

            config = load_app_config()
            provider = config.default_llm_provider
        except Exception:
            # If config loading fails, use no provider
            provider = None

        _registry = PromptRegistry(provider=provider)

    return _registry


# Maintain backward-compatible API
PROMPTS: dict[str, PromptTemplate] = {}


def list_prompts() -> Iterable[str]:
    """Return available prompt keys.

    Backward-compatible API that delegates to PromptRegistry.
    """
    registry = _get_registry()
    return registry.list_prompts()


def get_prompt(key: str, provider: str | None = None) -> PromptTemplate:
    """Retrieve a prompt template by key.

    Backward-compatible API that delegates to PromptRegistry.

    Args:
        key: Prompt key (biography, quality, qa, timeline)
        provider: LLM provider for provider-specific variants (optional)

    Returns:
        PromptTemplate instance

    Raises:
        KeyError: If prompt not found
    """
    registry = _get_registry()
    return registry.get_prompt(key, provider=provider)


def render_prompt(key: str, substitutions: Mapping[str, str] | None = None, provider: str | None = None) -> str:
    """Render a prompt by key with optional substitutions.

    Backward-compatible API that delegates to PromptRegistry.

    Args:
        key: Prompt key (biography, quality, qa, timeline)
        substitutions: Variable substitutions for template
        provider: LLM provider for provider-specific variants (optional)

    Returns:
        Rendered prompt text
    """
    template = get_prompt(key, provider=provider)
    if not substitutions:
        substitutions = {}
    return template.render(substitutions)


__all__ = [
    "PromptTemplate",
    "FewShotExample",
    "PromptRegistry",
    "render_prompt",
    "get_prompt",
    "list_prompts",
    "PROMPTS",
]
