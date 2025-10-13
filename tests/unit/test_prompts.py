"""
Tests for rmagent.agent.prompts module.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rmagent.agent import prompts


def test_list_prompts_contains_expected_keys():
    keys = set(prompts.list_prompts())
    assert {"biography", "quality", "qa", "timeline"}.issubset(keys)


def test_get_prompt_returns_template():
    tmpl = prompts.get_prompt("biography")
    assert tmpl.key == "biography"
    assert tmpl.version == "2025-01-08"  # Version from YAML file
    assert tmpl.few_shots


def test_render_prompt_substitutes_values():
    output = prompts.render_prompt(
        "qa",
        {
            "question": "Who is Donna's spouse?",
            "context_snippets": "- Marriage in 1985 (Citation 455)",
        },
    )
    assert "Donna's spouse" in output
    assert "Citation 455" in output


def test_render_prompt_leaves_unknown_placeholder_intact():
    rendered = prompts.render_prompt(
        "biography",
        {
            "person_summary": "Person summary",
            "timeline_overview": "Timeline data",
            "relationship_notes": "Relationships",
            # intentionally omit source_notes
        },
    )
    assert "{source_notes}" in rendered


def test_get_prompt_unknown_key_raises():
    with pytest.raises(KeyError):
        prompts.get_prompt("unknown-key")


# Provider-specific prompt tests
def test_get_prompt_with_anthropic_provider():
    """Test loading Anthropic-specific prompt variant."""
    tmpl = prompts.get_prompt("biography", provider="anthropic")
    assert tmpl.key == "biography"
    # Anthropic prompt should have more detailed instructions
    assert "professional genealogist with expertise" in tmpl.template
    assert "academic writing" in tmpl.template


def test_get_prompt_with_ollama_provider():
    """Test loading Ollama-specific prompt variant."""
    tmpl = prompts.get_prompt("biography", provider="ollama")
    assert tmpl.key == "biography"
    # Ollama prompt should be simpler
    assert "Create a biography" in tmpl.template
    assert "clear, direct language" in tmpl.template


def test_get_prompt_with_unsupported_provider_falls_back_to_default():
    """Test that unsupported provider falls back to default prompt."""
    tmpl_default = prompts.get_prompt("biography")
    tmpl_unsupported = prompts.get_prompt("biography", provider="unsupported")
    # Should use default template
    assert tmpl_default.template == tmpl_unsupported.template


def test_prompt_registry_caching():
    """Test that prompt registry caches loaded prompts."""
    registry = prompts.PromptRegistry()

    # First load
    tmpl1 = registry.get_prompt("biography")
    # Second load (should be cached)
    tmpl2 = registry.get_prompt("biography")

    # Should be the same object (cached)
    assert tmpl1 is tmpl2


def test_prompt_registry_provider_specific_caching():
    """Test that provider-specific prompts are cached separately."""
    registry = prompts.PromptRegistry()

    # Load default
    tmpl_default = registry.get_prompt("biography")
    # Load Anthropic variant
    tmpl_anthropic = registry.get_prompt("biography", provider="anthropic")

    # Should be different templates
    assert tmpl_default.template != tmpl_anthropic.template


def test_render_prompt_with_provider():
    """Test rendering prompt with provider-specific variant."""
    output = prompts.render_prompt(
        "biography",
        {
            "person_summary": "John Doe",
            "person_notes": "No notes",
            "timeline_overview": "Timeline",
            "early_life_overview": "Early life",
            "family_overview": "Family",
            "sibling_summary": "Siblings",
            "relationship_notes": "Relationships",
            "family_loss_notes": "Losses",
            "source_notes": "Sources",
            "available_citations": "No citations",
        },
        provider="anthropic",
    )
    assert "John Doe" in output
    assert "professional genealogist with expertise" in output
