"""
Tests for rmtool.agent.prompts module.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rmtool.agent import prompts


def test_list_prompts_contains_expected_keys():
    keys = set(prompts.list_prompts())
    assert {"biography", "quality", "qa", "timeline"}.issubset(keys)


def test_get_prompt_returns_template():
    tmpl = prompts.get_prompt("biography")
    assert tmpl.key == "biography"
    assert tmpl.version == prompts.PROMPT_VERSION
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
