"""
Integration-style unit tests for rmtool.rmlib.queries.QueryService.

These tests exercise canonical query patterns against the sanitized
RootsMagic sample database (data/Iiams.rmtree). The ICU extension is
required so the RMNOCASE collation is available.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pytest

# Ensure repository root is importable for rmtool package
PROJECT_ROOT = Path(__file__).resolve().parents[2]
import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rmtool.rmlib.database import RMDatabase
from rmtool.rmlib.queries import QueryService, VITAL_EVENT_TYPES

DATA_PATH = Path("data/Iiams.rmtree")
ICU_EXTENSION_PATH = Path("sqlite-extension/icu.dylib")


def _requires_sample_data() -> None:
    if not DATA_PATH.exists():
        pytest.skip("Sample RootsMagic database not available")
    if not ICU_EXTENSION_PATH.exists():
        pytest.skip("ICU extension not available for RMNOCASE")


@pytest.fixture(scope="module")
def query_service() -> Iterable[QueryService]:
    _requires_sample_data()
    db = RMDatabase(DATA_PATH, extension_path=ICU_EXTENSION_PATH)
    db.connect()
    service = QueryService(db)
    yield service
    db.close()


def test_get_person_with_primary_name(query_service: QueryService) -> None:
    row = query_service.get_person_with_primary_name(1)
    assert row is not None
    assert row["Surname"] == "Iams"
    assert row["Given"] == "Michael Dorsey"


def test_search_primary_names_exact(query_service: QueryService) -> None:
    rows = query_service.search_primary_names(
        surname="Iams",
        given="Michael Dorsey",
        limit=5,
    )
    ids = {row["PersonID"] for row in rows}
    assert 1 in ids
    assert len(rows) <= 5


def test_search_primary_names_phonetic(query_service: QueryService) -> None:
    rows = query_service.search_primary_names_phonetic("Iams", limit=50)
    assert rows
    assert all(row["Surname"] == "Iams" for row in rows)


def test_get_parents(query_service: QueryService) -> None:
    row = query_service.get_parents(1)
    assert row["FatherID"] == 1541
    assert row["MotherID"] == 1430


def test_get_children(query_service: QueryService) -> None:
    rows = query_service.get_children(1541)
    child_ids = {row["PersonID"] for row in rows}
    assert 1 in child_ids
    assert len(rows) >= 1


def test_get_person_events_sorted(query_service: QueryService) -> None:
    rows = query_service.get_person_events(1)
    sort_dates = [row["SortDate"] for row in rows]
    assert sort_dates == sorted(sort_dates)


def test_get_vital_events_subset(query_service: QueryService) -> None:
    rows = query_service.get_vital_events(1)
    assert rows
    fact_ids = {row["FactTypeID"] for row in rows}
    assert fact_ids.issubset(set(VITAL_EVENT_TYPES))


def test_get_spouses(query_service: QueryService) -> None:
    rows = query_service.get_spouses(1541)
    spouse_ids = {row["PersonID"] for row in rows}
    assert 1430 in spouse_ids or 247 in spouse_ids


def test_get_direct_ancestors(query_service: QueryService) -> None:
    rows = query_service.get_direct_ancestors(1, generations=3)
    assert any(row["PersonID"] == 1541 for row in rows)
    assert max(row["Generation"] for row in rows) <= 3


def test_get_ancestors_with_spouses(query_service: QueryService) -> None:
    rows = query_service.get_ancestors_with_spouses(1)
    relationships = {row["Relationship"] for row in rows}
    assert relationships.issubset({"Parent", "Grandparent"})


def test_get_descendants(query_service: QueryService) -> None:
    rows = query_service.get_descendants(1541, generations=3)
    assert any(row["PersonID"] == 1 for row in rows)
    assert max(row["Generation"] for row in rows) <= 3


def test_get_event_citations(query_service: QueryService) -> None:
    rows = query_service.get_event_citations(12306)
    assert rows
    source_names = {row["SourceName"] for row in rows}
    assert source_names


def test_get_unsourced_vital_events(query_service: QueryService) -> None:
    rows = query_service.get_unsourced_vital_events(owner_id=1, limit=5)
    assert rows
    assert all(row["PersonID"] == 1 for row in rows)


def test_find_places_by_name(query_service: QueryService) -> None:
    rows = query_service.find_places_by_name("Maryland", limit=10)
    assert rows
    assert any("Maryland" in row["Name"] for row in rows)


def test_find_people_missing_vital_events(query_service: QueryService) -> None:
    rows = query_service.find_people_missing_vital_events(event_type=1, limit=5)
    assert rows
    assert rows[0]["PersonID"] is not None


def test_find_logical_inconsistencies(query_service: QueryService) -> None:
    rows = query_service.find_logical_inconsistencies(limit=5)
    assert rows
    for row in rows:
        assert row["DeathSort"] < row["BirthSort"]
