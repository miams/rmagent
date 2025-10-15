"""
LangChain-style tool wrappers for RMAgent.

These small adapters expose commonly used query patterns and quality checks
so they can be plugged into LangChain (or similar) agents. Tools are designed
to be dependency-injected for ease of testing.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from rmagent.rmlib.quality import DataQualityValidator
from rmagent.rmlib.queries import QueryService


class ToolExecutionError(RuntimeError):
    """Raised when a tool cannot complete its work."""


@dataclass
class BaseTool:
    """Minimal interface compatible with LangChain-like tooling."""

    name: str
    description: str

    def run(self, *args, **kwargs):
        raise NotImplementedError

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)


@dataclass
class QueryPersonTool(BaseTool):
    query_service: QueryService

    def __init__(self, query_service: QueryService):
        super().__init__(
            name="query_person",
            description="Return person details (primary name, sex, birth/death years).",
        )
        self.query_service = query_service

    def run(self, person_id: int) -> dict[str, str | None]:
        row = self.query_service.get_person_with_primary_name(person_id)
        if row is None:
            raise ToolExecutionError(f"Person {person_id} not found.")
        return dict(row)


@dataclass
class GetEventsTool(BaseTool):
    query_service: QueryService

    def __init__(self, query_service: QueryService):
        super().__init__(
            name="get_events",
            description="Return event rows for a person ordered by sort date.",
        )
        self.query_service = query_service

    def run(self, person_id: int):
        return [dict(row) for row in self.query_service.get_person_events(person_id)]


@dataclass
class GetAncestorsTool(BaseTool):
    query_service: QueryService

    def __init__(self, query_service: QueryService):
        super().__init__(
            name="get_ancestors",
            description="Return ancestor rows for a person up to N generations.",
        )
        self.query_service = query_service

    def run(self, person_id: int, generations: int = 3):
        return [dict(row) for row in self.query_service.get_direct_ancestors(person_id, generations=generations)]


@dataclass
class FindRelationshipTool(BaseTool):
    query_service: QueryService

    def __init__(self, query_service: QueryService):
        super().__init__(
            name="find_relationship",
            description="Estimate relationship context between two people using parents and ancestor lookups.",
        )
        self.query_service = query_service

    def run(self, person_a: int, person_b: int) -> dict[str, str | None]:
        if person_a == person_b:
            return {"relationship": "Same person"}

        ancestors_a = {row["PersonID"]: row for row in self.query_service.get_direct_ancestors(person_a, generations=5)}
        ancestors_b = {row["PersonID"]: row for row in self.query_service.get_direct_ancestors(person_b, generations=5)}

        shared = set(ancestors_a).intersection(ancestors_b)
        if not shared:
            return {"relationship": "No common ancestor within five generations"}

        ancestor = shared.pop()
        rel_a = ancestors_a[ancestor]["Relationship"]
        rel_b = ancestors_b[ancestor]["Relationship"]
        return {
            "relationship": f"Common ancestor via {rel_a} / {rel_b}",
            "ancestor_id": ancestor,
        }


@dataclass
class ValidateDataTool(BaseTool):
    validator_factory: Callable[[], DataQualityValidator]

    def __init__(self, validator_factory: Callable[[], DataQualityValidator]):
        super().__init__(
            name="validate_data",
            description="Run the RootsMagic data-quality validator and summarize issues.",
        )
        self.validator_factory = validator_factory

    def run(self):
        validator = self.validator_factory()
        report = validator.run_all_checks()
        return {
            "totals_by_severity": {
                k.value if hasattr(k, "value") else str(k): v for k, v in report.totals_by_severity.items()
            },
            "totals_by_category": report.totals_by_category,
            "issue_count": report.summary.get("issue_total", 0),
        }


@dataclass
class SearchDatabaseTool(BaseTool):
    query_service: QueryService

    def __init__(self, query_service: QueryService):
        super().__init__(
            name="search_database",
            description="Search for primary names by exact surname/given name.",
        )
        self.query_service = query_service

    def run(self, surname: str | None = None, given: str | None = None, limit: int = 10):
        if surname is None and given is None:
            raise ToolExecutionError("Provide at least a surname or given name.")
        rows = self.query_service.search_primary_names(surname=surname, given=given, limit=limit)
        return [dict(row) for row in rows]


def default_langchain_tools(query_service: QueryService, validator: DataQualityValidator):
    """Return a canonical set of tools wired to the supplied dependencies."""

    return [
        QueryPersonTool(query_service),
        GetEventsTool(query_service),
        GetAncestorsTool(query_service),
        FindRelationshipTool(query_service),
        SearchDatabaseTool(query_service),
        ValidateDataTool(lambda: validator),
    ]
