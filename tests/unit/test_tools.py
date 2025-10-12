"""
Tests for rmagent.agent.tools.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rmagent.agent.tools import (
    FindRelationshipTool,
    GetAncestorsTool,
    GetEventsTool,
    QueryPersonTool,
    SearchDatabaseTool,
    ToolExecutionError,
    ValidateDataTool,
)
from rmagent.rmlib.quality import QualityReport, QualitySeverity


class StubQueryService:
    def __init__(self):
        self.person = {"PersonID": 1, "Given": "Michael", "Surname": "Iams"}
        self.events = [
            {
                "EventID": 1,
                "EventType": "Birth",
                "Date": "1968-04-30",
                "Place": "Arizona",
                "Details": "",
            },
        ]
        self.ancestors = [
            {
                "PersonID": 100,
                "Given": "Donald",
                "Surname": "Iams",
                "Relationship": "Father",
                "Generation": 1,
            },
        ]

    def get_person_with_primary_name(self, person_id: int):
        return dict(self.person) if person_id == 1 else None

    def get_person_events(self, person_id: int):
        return list(self.events)

    def get_direct_ancestors(self, person_id: int, generations: int = 3):
        return list(self.ancestors)

    def search_primary_names(self, surname=None, given=None, limit=10):
        return [dict(self.person)]


class StubValidator:
    def run_all_checks(self):
        return QualityReport(
            issues=[],
            totals_by_severity={QualitySeverity.CRITICAL: 0},
            totals_by_category={},
            summary={"issue_total": 0},
        )


def test_query_person_tool_returns_person():
    tool = QueryPersonTool(StubQueryService())
    data = tool.run(1)
    assert data["PersonID"] == 1


def test_get_events_tool_returns_events():
    tool = GetEventsTool(StubQueryService())
    events = tool.run(1)
    assert len(events) == 1


def test_get_ancestors_tool_returns_list():
    tool = GetAncestorsTool(StubQueryService())
    ancestors = tool.run(1)
    assert ancestors[0]["Relationship"] == "Father"


def test_find_relationship_tool_shared_ancestor():
    tool = FindRelationshipTool(StubQueryService())
    result = tool.run(1, 1)
    assert "Same person" in result["relationship"]


def test_search_database_tool_requires_name():
    tool = SearchDatabaseTool(StubQueryService())
    with pytest.raises(ToolExecutionError):
        tool.run()
    matches = tool.run(surname="Iams")
    assert matches


def test_validate_data_tool_returns_summary():
    tool = ValidateDataTool(lambda: StubValidator())
    report = tool.run()
    assert report["issue_count"] == 0
