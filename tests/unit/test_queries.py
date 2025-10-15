"""
Integration-style unit tests for rmagent.rmlib.queries.QueryService.

These tests exercise canonical query patterns against the sanitized
RootsMagic sample database (data/Iiams.rmtree). The ICU extension is
required so the RMNOCASE collation is available.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pytest

# Ensure repository root is importable for rmagent package
PROJECT_ROOT = Path(__file__).resolve().parents[2]
import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rmagent.rmlib.database import RMDatabase
from rmagent.rmlib.queries import VITAL_EVENT_TYPES, QueryService

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


def test_search_names_flexible(query_service: QueryService) -> None:
    """Test flexible name search that searches surname or given name."""
    rows = query_service.search_names_flexible("Michael", limit=10)
    assert rows
    # Should find people with "Michael" in given or surname
    for row in rows:
        name_text = f"{row['Given']} {row['Surname']}".lower()
        assert "michael" in name_text


def test_search_names_by_words(query_service: QueryService) -> None:
    """Test multi-word search where all words must appear."""
    rows = query_service.search_names_by_words("Michael Iams", limit=10)
    assert rows
    # All results should contain both "Michael" and "Iams"
    for row in rows:
        name_text = f"{row['Given']} {row['Surname']}".lower()
        assert "michael" in name_text and "iams" in name_text.lower()


def test_search_names_with_married(query_service: QueryService) -> None:
    """Test search for females by maiden or married name."""
    # This searches only females (Sex=1) and includes spouse surnames
    rows = query_service.search_names_with_married("Dorsey", limit=10)
    # Should return results if there are females with Dorsey as maiden or married name
    # Note: May be empty if no matches, so just verify it runs without error
    assert isinstance(rows, list)


def test_search_names_with_married_by_words(query_service: QueryService) -> None:
    """Test multi-word search for females by maiden or married name."""
    rows = query_service.search_names_with_married_by_words("Janet Iams", limit=10)
    # Should search for females where all words appear in name
    assert isinstance(rows, list)


def test_find_places_within_radius(query_service: QueryService) -> None:
    """Test finding places within a radius of a center point."""
    # First find a place with coordinates to use as center
    all_places = query_service.db.query(
        "SELECT PlaceID, Name, Latitude, Longitude FROM PlaceTable "
        "WHERE Latitude IS NOT NULL AND Latitude != 0 "
        "AND Longitude IS NOT NULL AND Longitude != 0 "
        "LIMIT 1"
    )
    if not all_places:
        pytest.skip("No places with GPS coordinates in database")

    center_place_id = all_places[0]["PlaceID"]

    # Search within 100km radius
    rows = query_service.find_places_within_radius(center_place_id, radius_km=100, limit=10)

    # Results should be sorted by distance
    if len(rows) > 1:
        distances = [r["DistanceKm"] for r in rows]
        assert distances == sorted(distances)

    # All results should have distance and be within radius
    for row in rows:
        assert "DistanceKm" in row
        assert row["DistanceKm"] <= 100


def test_find_places_within_radius_no_coordinates(query_service: QueryService) -> None:
    """Test that radius search fails gracefully for places without coordinates."""
    # Create or find a place without coordinates
    places_no_coords = query_service.db.query(
        "SELECT PlaceID FROM PlaceTable WHERE Latitude IS NULL OR Latitude = 0 LIMIT 1"
    )
    if places_no_coords:
        with pytest.raises(ValueError, match="has no GPS coordinates"):
            query_service.find_places_within_radius(places_no_coords[0]["PlaceID"], radius_km=100)


def test_get_person_count_by_place(query_service: QueryService) -> None:
    """Test counting unique people with events at a place."""
    # Find a place that has events
    places = query_service.find_places_by_name("Maryland", limit=1)
    if not places:
        pytest.skip("No places named Maryland in database")

    place_id = places[0]["PlaceID"]
    count = query_service.get_person_count_by_place(place_id)

    # Count should be non-negative integer
    assert isinstance(count, int)
    assert count >= 0


def test_find_places_exact_match(query_service: QueryService) -> None:
    """Test exact place name matching."""
    # First get a known place name
    all_places = query_service.find_places_by_name("Maryland", limit=1, exact=False)
    if not all_places:
        pytest.skip("No places with Maryland in name")

    exact_name = all_places[0]["Name"]

    # Now search for exact match
    exact_results = query_service.find_places_by_name(exact_name, limit=10, exact=True)

    # Should return only places with exact name match (case-insensitive)
    assert len(exact_results) > 0
    for place in exact_results:
        assert place["Name"].lower() == exact_name.lower()
