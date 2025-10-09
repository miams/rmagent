"""
Tests for rmtool.config.config module.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rmtool.agent.llm_provider import LLMError
from rmtool.config.config import load_app_config


def test_load_app_config_from_env_file(tmp_path, monkeypatch):
    env_path = tmp_path / "test.env"
    output_dir = tmp_path / "out"
    export_dir = tmp_path / "exports"
    env_path.write_text(
        "\n".join(
            [
                "DEFAULT_LLM_PROVIDER=openai",
                "OPENAI_API_KEY=sk-test",
                "OPENAI_MODEL=gpt-4o-mini",
                f"OUTPUT_DIR={output_dir}",
                f"EXPORT_DIR={export_dir}",
                "RM_DATABASE_PATH=data/Iiams.rmtree",
            ]
        )
    )

    monkeypatch.delenv("DEFAULT_LLM_PROVIDER", raising=False)
    config = load_app_config(env_path=env_path, auto_create_dirs=True)

    assert config.llm.default_provider == "openai"
    assert config.output.output_dir == output_dir.resolve()
    assert output_dir.exists()
    assert export_dir.exists()


def test_missing_required_api_key_raises(tmp_path, monkeypatch):
    env_path = tmp_path / "missing.env"
    env_path.write_text("DEFAULT_LLM_PROVIDER=anthropic\n")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "")

    with pytest.raises(LLMError):
        load_app_config(env_path=env_path, auto_create_dirs=False)


def test_invalid_citation_style(tmp_path):
    env_path = tmp_path / "style.env"
    env_path.write_text(
        "\n".join(
            [
                "DEFAULT_CITATION_STYLE=invalid",
                "DEFAULT_LLM_PROVIDER=ollama",
                "OLLAMA_BASE_URL=http://localhost:11434",
            ]
        )
    )
    with pytest.raises(LLMError):
        load_app_config(env_path=env_path, auto_create_dirs=False)
