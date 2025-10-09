"""
Tests for rmtool.agent.genealogy_agent.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rmtool.agent.genealogy_agent import GenealogyAgent
from rmtool.agent.llm_provider import LLMProvider, LLMResult, RetryConfig, TokenUsage
from rmtool.rmlib.quality import QualityIssue, QualityReport, QualitySeverity


class StubLLMProvider(LLMProvider):
    def __init__(self):
        super().__init__("stub", retry_config=RetryConfig(max_attempts=1))
        self.prompts: List[str] = []

    def _invoke(self, prompt: str, **kwargs) -> LLMResult:
        self.prompts.append(prompt)
        return LLMResult(
            text="stub-response",
            model="stub",
            usage=TokenUsage(prompt_tokens=1, completion_tokens=1),
        )


class StubQueryService:
    def __init__(self):
        self.person = {"PersonID": 1, "Given": "Michael", "Surname": "Iams", "BirthYear": 1968, "DeathYear": None}
        self.events = [
            {"EventID": 1, "EventType": "Birth", "Date": "1968-04-30", "Place": "Arizona", "Details": ""},
            {"EventID": 2, "EventType": "Education", "Date": "1988", "Place": "University of Arizona", "Details": "Graduated"},
        ]
        self.ancestors = [
            {"PersonID": 1541, "Surname": "Iams", "Given": "Donald", "Relationship": "Father", "Generation": 1},
            {"PersonID": 1430, "Surname": "Shepherd", "Given": "Gail", "Relationship": "Mother", "Generation": 1},
        ]

    def get_person_with_primary_name(self, person_id: int):
        return dict(self.person) if person_id == self.person["PersonID"] else None

    def get_person_events(self, person_id: int):
        return list(self.events) if person_id == self.person["PersonID"] else []

    def get_direct_ancestors(self, person_id: int, generations: int = 3):
        return list(self.ancestors) if person_id == self.person["PersonID"] else []

    def search_primary_names(self, surname=None, given=None, limit=10):
        return [dict(self.person)]


class StubQualityValidator:
    def run_all_checks(self):
        return QualityReport(
            issues=[
                QualityIssue(
                    rule_id="1.1",
                    name="Missing primary name",
                    category="Required Fields",
                    severity=QualitySeverity.CRITICAL,
                    description="",
                    count=1,
                )
            ],
            totals_by_severity={QualitySeverity.CRITICAL: 1},
            totals_by_category={"Required Fields": 1},
            summary={"issue_total": 1},
        )


def stub_query_factory(_db: Any) -> StubQueryService:
    return StubQueryService()


def stub_validator_factory(_db: Any) -> StubQualityValidator:
    return StubQualityValidator()


def test_generate_biography_calls_provider():
    provider = StubLLMProvider()
    agent = GenealogyAgent(
        llm_provider=provider,
        db_path=None,
        query_service_factory=stub_query_factory,
        validator_factory=stub_validator_factory,
    )

    result = agent.generate_biography(1)
    assert result.text == "stub-response"
    assert provider.prompts
    assert "Michael Iams" in provider.prompts[0]


def test_analyze_data_quality_returns_report():
    agent = GenealogyAgent(
        llm_provider=StubLLMProvider(),
        db_path=None,
        query_service_factory=stub_query_factory,
        validator_factory=stub_validator_factory,
    )
    report = agent.analyze_data_quality()
    assert report.summary["issue_total"] == 1


def test_ask_adds_memory():
    provider = StubLLMProvider()
    agent = GenealogyAgent(
        llm_provider=provider,
        db_path=None,
        query_service_factory=stub_query_factory,
        validator_factory=stub_validator_factory,
    )
    agent.ask("Who are the parents?")
    assert len(agent.memory()) == 1
    assert "Who are the parents" in provider.prompts[0]


def test_generate_timeline_summary_uses_events():
    provider = StubLLMProvider()
    agent = GenealogyAgent(
        llm_provider=provider,
        db_path=None,
        query_service_factory=stub_query_factory,
        validator_factory=stub_validator_factory,
    )
    agent.generate_timeline_summary(1)
    prompt = provider.prompts[-1]
    assert "TimelineJS3" in prompt
