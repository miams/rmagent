"""
RootsMagic query service implementing canonical query patterns.

These helpers wrap the SQL statements documented in
`data_reference/RM11_Query_Patterns.md` so downstream modules can
reuse optimized, parameterized statements consistently.
"""

from __future__ import annotations

from collections.abc import Sequence

from .database import RMDatabase
from .sql_queries import (
    _FIND_LOGICAL_INCONSISTENCIES_SQL,
    _FIND_MISSING_VITAL_EVENTS_SQL,
    _FIND_PLACES_SQL,
    _GET_ANCESTORS_SQL,
    _GET_ANCESTORS_WITH_SPOUSES_SQL,
    _GET_CHILDREN_SQL,
    _GET_DESCENDANTS_SQL,
    _GET_EVENT_CITATIONS_SQL,
    _GET_PARENTS_SQL,
    _GET_PERSON_EVENTS_SQL,
    _GET_PERSON_SQL,
    _GET_SPOUSES_SQL,
    _GET_UNSOURCED_EVENTS_SQL_TEMPLATE,
    _GET_VITAL_EVENTS_SQL,
    _SEARCH_NAMES_FLEXIBLE_SQL,
    _SEARCH_NAMES_WITH_MARRIED_SQL,
    _SEARCH_PERSON_PHONETIC_SQL,
    _SEARCH_PERSON_SQL,
)

VITAL_EVENT_TYPES: tuple[int, ...] = (1, 2, 3, 4, 300)
DEFAULT_GENERATION_LIMIT = 10
DEFAULT_RESULT_LIMIT = 10000  # High limit for genealogy searches


class QueryService:
    """Lightweight façade for the canonical RootsMagic query suite."""

    def __init__(self, db: RMDatabase):
        self.db = db

    # Pattern 1
    def get_person_with_primary_name(self, person_id: int):
        return self.db.query_one(_GET_PERSON_SQL, (person_id,))

    # Pattern 2
    def search_primary_names(
        self,
        surname: str | None = None,
        given: str | None = None,
        limit: int = DEFAULT_RESULT_LIMIT,
    ):
        if surname is None and given is None:
            raise ValueError("Provide at least one of surname or given")
        if limit <= 0:
            raise ValueError("limit must be positive")

        filters = []
        params: list[object] = []
        if surname is not None:
            filters.append("n.Surname LIKE ? COLLATE RMNOCASE")
            params.append(f"%{surname}%")
        if given is not None:
            filters.append("n.Given LIKE ? COLLATE RMNOCASE")
            params.append(f"%{given}%")

        where_clause = " AND ".join(filters)
        sql = f"{_SEARCH_PERSON_SQL} AND {where_clause} ORDER BY n.Surname, n.Given LIMIT ?"
        params.append(limit)
        return self.db.query(sql, tuple(params))

    def search_names_flexible(
        self,
        search_text: str,
        limit: int = DEFAULT_RESULT_LIMIT,
    ):
        """
        Flexible name search that tries multiple strategies:
        1. Full text in surname or given name
        2. Individual words in surname or given name
        3. Returns ranked results with surname matches first
        """
        if limit <= 0:
            raise ValueError("limit must be positive")

        search_pattern = f"%{search_text}%"
        # Parameters: WHERE surname, WHERE given, ORDER BY surname, ORDER BY given, LIMIT
        params = (search_pattern, search_pattern, search_pattern, search_pattern, limit)
        return self.db.query(_SEARCH_NAMES_FLEXIBLE_SQL, params)

    def search_names_by_words(
        self,
        search_text: str,
        limit: int = DEFAULT_RESULT_LIMIT,
        include_alternate: bool = True,
    ):
        """
        Search for persons where ALL words appear in name (surname + given combined).
        This handles cases like "Lucy Virginia Dorsey" where words span both fields.
        Includes alternate names by default.
        """
        if limit <= 0:
            raise ValueError("limit must be positive")

        words = search_text.strip().split()
        if not words:
            return []

        # Build WHERE clause: each word must appear in CONCAT(Given, ' ', Surname)
        where_conditions = []
        params: list[object] = []
        for word in words:
            where_conditions.append(
                "(n.Given || ' ' || n.Surname LIKE ? COLLATE RMNOCASE "
                "OR n.Surname || ' ' || n.Given LIKE ? COLLATE RMNOCASE)"
            )
            pattern = f"%{word}%"
            params.append(pattern)
            params.append(pattern)

        where_clause = " AND ".join(where_conditions)
        primary_filter = "" if include_alternate else "AND n.IsPrimary = 1"

        sql = f"""
SELECT DISTINCT
  p.PersonID,
  n.Surname,
  n.Given,
  n.BirthYear,
  n.DeathYear,
  n.IsPrimary
FROM PersonTable p
JOIN NameTable n
  ON p.PersonID = n.OwnerID
  {primary_filter}
WHERE {where_clause}
ORDER BY n.IsPrimary DESC, n.Surname, n.Given
LIMIT ?
"""
        params.append(limit)
        return self.db.query(sql, tuple(params))

    def search_names_with_married(
        self,
        search_text: str,
        limit: int = DEFAULT_RESULT_LIMIT,
    ):
        """
        Search for female persons by maiden name OR married surname.
        Only searches females (Sex = 1) and includes spouse surnames.
        """
        if limit <= 0:
            raise ValueError("limit must be positive")

        search_pattern = f"%{search_text}%"
        params = (search_pattern, search_pattern, search_pattern, limit)
        return self.db.query(_SEARCH_NAMES_WITH_MARRIED_SQL, params)

    def search_names_with_married_by_words(
        self,
        search_text: str,
        limit: int = DEFAULT_RESULT_LIMIT,
    ):
        """
        Search for female persons where ALL words appear in:
        - Given name + Maiden surname OR
        - Given name + Married surname
        Handles multi-word queries like "Janet Iiams".

        Uses UNION approach for better performance:
        1. Search maiden names (no joins through family)
        2. Search married names (inner joins only for matches)
        """
        if limit <= 0:
            raise ValueError("limit must be positive")

        words = search_text.strip().split()
        if not words:
            return []

        # Build WHERE clause for each word appearing in maiden name
        maiden_conditions = []
        maiden_params: list[object] = []
        for word in words:
            maiden_conditions.append(
                "(pn.Given || ' ' || pn.Surname LIKE ? COLLATE RMNOCASE "
                "OR pn.Surname || ' ' || pn.Given LIKE ? COLLATE RMNOCASE)"
            )
            pattern = f"%{word}%"
            maiden_params.append(pattern)
            maiden_params.append(pattern)

        # Build WHERE clause for each word appearing in married name
        married_conditions = []
        married_params: list[object] = []
        for word in words:
            married_conditions.append(
                "(pn.Given || ' ' || spouse_name.Surname LIKE ? COLLATE RMNOCASE "
                "OR spouse_name.Surname || ' ' || pn.Given LIKE ? COLLATE RMNOCASE)"
            )
            pattern = f"%{word}%"
            married_params.append(pattern)
            married_params.append(pattern)

        maiden_where = " AND ".join(maiden_conditions)
        married_where = " AND ".join(married_conditions)

        sql = f"""
SELECT DISTINCT
  p.PersonID,
  pn.Surname,
  pn.Given,
  pn.BirthYear,
  pn.DeathYear,
  1 AS IsPrimary
FROM PersonTable p
JOIN NameTable pn ON p.PersonID = pn.OwnerID AND pn.IsPrimary = 1
WHERE p.Sex = 1
  AND ({maiden_where})
UNION
SELECT DISTINCT
  p.PersonID,
  pn.Surname,
  pn.Given,
  pn.BirthYear,
  pn.DeathYear,
  1 AS IsPrimary
FROM PersonTable p
JOIN NameTable pn ON p.PersonID = pn.OwnerID AND pn.IsPrimary = 1
JOIN FamilyTable f ON p.PersonID = f.MotherID
JOIN PersonTable spouse ON spouse.PersonID = f.FatherID
JOIN NameTable spouse_name ON spouse.PersonID = spouse_name.OwnerID AND spouse_name.IsPrimary = 1
WHERE p.Sex = 1
  AND ({married_where})
ORDER BY 2, 3
LIMIT ?
"""
        params = maiden_params + married_params + [limit]
        return self.db.query(sql, tuple(params))

    def search_primary_names_phonetic(
        self,
        surname_phonetic: str,
        limit: int = DEFAULT_RESULT_LIMIT,
    ):
        if limit <= 0:
            raise ValueError("limit must be positive")
        params = (surname_phonetic, limit)
        return self.db.query(_SEARCH_PERSON_PHONETIC_SQL, params)

    # Pattern 3
    def get_parents(self, person_id: int):
        return self.db.query_one(_GET_PARENTS_SQL, (person_id,))

    # Pattern 4
    def get_children(self, person_id: int):
        params = (person_id, person_id)
        return self.db.query(_GET_CHILDREN_SQL, params)

    # Pattern 5
    def get_person_events(self, person_id: int):
        return self.db.query(_GET_PERSON_EVENTS_SQL, (person_id,))

    # Pattern 6
    def get_vital_events(self, person_id: int):
        params = (person_id,) + VITAL_EVENT_TYPES
        return self.db.query(_GET_VITAL_EVENTS_SQL, params)

    # Pattern 7
    def get_spouses(self, person_id: int):
        params = (person_id, person_id, person_id)
        return self.db.query(_GET_SPOUSES_SQL, params)

    # Pattern 8
    def get_direct_ancestors(
        self,
        person_id: int,
        generations: int = DEFAULT_GENERATION_LIMIT,
    ):
        if generations <= 0:
            raise ValueError("generations must be positive")
        params = (person_id, generations, generations)
        return self.db.query(_GET_ANCESTORS_SQL, params)

    # Pattern 9
    def get_ancestors_with_spouses(self, person_id: int):
        params = (person_id, person_id)
        return self.db.query(_GET_ANCESTORS_WITH_SPOUSES_SQL, params)

    # Pattern 10
    def get_descendants(
        self,
        person_id: int,
        generations: int = DEFAULT_GENERATION_LIMIT,
    ):
        if generations <= 0:
            raise ValueError("generations must be positive")
        params = (person_id, generations)
        return self.db.query(_GET_DESCENDANTS_SQL, params)

    # Pattern 11
    def get_event_citations(self, event_id: int):
        return self.db.query(_GET_EVENT_CITATIONS_SQL, (event_id,))

    # Pattern 12
    def get_unsourced_vital_events(
        self,
        owner_id: int | None = None,
        event_types: Sequence[int] = VITAL_EVENT_TYPES,
        limit: int | None = None,
    ):
        if not event_types:
            raise ValueError("event_types must contain at least one value")
        if limit is not None and limit <= 0:
            raise ValueError("limit must be positive")

        placeholders = ",".join("?" for _ in event_types)
        sql = _GET_UNSOURCED_EVENTS_SQL_TEMPLATE.format(event_type_list=placeholders)

        params: list[object] = list(event_types)
        if owner_id is not None:
            sql += "\n  AND e.OwnerID = ?"
            params.append(owner_id)

        sql += """
ORDER BY n.Surname,
         n.Given,
         e.SortDate
"""
        if limit is not None:
            sql += "\nLIMIT ?"
            params.append(limit)
        return self.db.query(sql, tuple(params))

    # Pattern 13
    def find_places_by_name(
        self, pattern: str, limit: int = DEFAULT_RESULT_LIMIT, exact: bool = False
    ):
        """
        Find places by name with flexible or exact matching.

        Args:
            pattern: Place name to search for
            limit: Maximum number of results
            exact: If True, requires exact match (case-insensitive).
                   If False (default), uses flexible comma-separated matching.

        Flexible matching (exact=False):
            Supports hierarchy matching where comma-separated parts can be
            non-consecutive. For example:
            - "Scottsdale, Maricopa" matches "Scottsdale, Maricopa, Arizona, United States"
            - "Scottsdale, Arizona" matches "Scottsdale, Maricopa, Arizona, United States"
            All parts must appear in the place name (case-insensitive).

        Exact matching (exact=True):
            Requires the full place name to match exactly (case-insensitive).
            - "Phoenix, Maricopa, Arizona, United States" matches only that exact place
            - Will not match "Phoenix, Maricopa, Arizona Territory, United States"
        """
        if limit <= 0:
            raise ValueError("limit must be positive")

        if exact:
            # Exact match: use = with COLLATE RMNOCASE
            sql = """
SELECT
  PlaceID,
  Name,
  Latitude,
  Longitude
FROM PlaceTable
WHERE Name = ? COLLATE RMNOCASE
ORDER BY Name
LIMIT ?
"""
            params = (pattern, limit)
            return self.db.query(sql, params)
        else:
            # Flexible matching (original behavior)
            # Split pattern by comma-space to get hierarchy parts
            parts = [p.strip() for p in pattern.split(',') if p.strip()]

            if len(parts) == 1:
                # Simple case: single search term
                like_pattern = f"%{pattern}%"
                params = (like_pattern, limit)
                return self.db.query(_FIND_PLACES_SQL, params)
            else:
                # Multiple parts: all must appear in the place name
                conditions = []
                params_list: list[object] = []
                for part in parts:
                    conditions.append("Name LIKE ? COLLATE RMNOCASE")
                    params_list.append(f"%{part}%")

                where_clause = " AND ".join(conditions)
                sql = f"""
SELECT
  PlaceID,
  Name,
  Latitude,
  Longitude
FROM PlaceTable
WHERE {where_clause}
ORDER BY Name
LIMIT ?
"""
                params_list.append(limit)
                return self.db.query(sql, tuple(params_list))

    def find_places_within_radius(
        self,
        center_place_id: int,
        radius_km: float,
        limit: int = DEFAULT_RESULT_LIMIT,
    ):
        """
        Find all places within a given radius of a center place.

        Uses Haversine formula to calculate distances on Earth's surface.
        Only returns places that have GPS coordinates.

        Args:
            center_place_id: PlaceID of the center location
            radius_km: Search radius in kilometers
            limit: Maximum number of results

        Returns:
            List of places within radius, including distance in km

        Raises:
            ValueError: If center place not found or has no coordinates
        """
        if limit <= 0:
            raise ValueError("limit must be positive")
        if radius_km <= 0:
            raise ValueError("radius must be positive")

        # Get center place coordinates
        center = self.db.query_one(
            "SELECT PlaceID, Name, Latitude, Longitude FROM PlaceTable WHERE PlaceID = ?",
            (center_place_id,),
        )

        if not center:
            raise ValueError(f"Place ID {center_place_id} not found")

        center_lat = center["Latitude"] if center["Latitude"] is not None else 0
        center_lon = center["Longitude"] if center["Longitude"] is not None else 0

        if not center_lat or not center_lon or center_lat == 0 or center_lon == 0:
            raise ValueError(
                f"Place '{center['Name']}' (ID {center_place_id}) has no GPS coordinates"
            )

        # Convert integer coordinates to degrees
        center_lat_deg = center_lat / 10_000_000.0
        center_lon_deg = center_lon / 10_000_000.0

        # Get all places with coordinates
        all_places = self.db.query(
            """
SELECT PlaceID, Name, Latitude, Longitude
FROM PlaceTable
WHERE Latitude IS NOT NULL
  AND Latitude != 0
  AND Longitude IS NOT NULL
  AND Longitude != 0
  AND PlaceID != ?
""",
            (center_place_id,),
        )

        # Calculate distances and filter by radius
        results = []
        for place in all_places:
            place_lat_deg = place["Latitude"] / 10_000_000.0
            place_lon_deg = place["Longitude"] / 10_000_000.0

            distance_km = _haversine_distance(
                center_lat_deg, center_lon_deg, place_lat_deg, place_lon_deg
            )

            if distance_km <= radius_km:
                results.append(
                    {
                        "PlaceID": place["PlaceID"],
                        "Name": place["Name"],
                        "Latitude": place["Latitude"],
                        "Longitude": place["Longitude"],
                        "DistanceKm": round(distance_km, 2),
                    }
                )

        # Sort by distance and apply limit
        results.sort(key=lambda x: x["DistanceKm"])
        return results[:limit]

    def get_person_count_by_place(self, place_id: int) -> int:
        """
        Get count of unique people who had events at a specific place.

        Args:
            place_id: PlaceID to count people for

        Returns:
            Count of distinct PersonIDs with events at this place
        """
        result = self.db.query_one(
            """
SELECT COUNT(DISTINCT e.OwnerID) as PersonCount
FROM EventTable e
WHERE e.OwnerType = 0
  AND e.PlaceID = ?
""",
            (place_id,),
        )
        return result["PersonCount"] if result else 0

    # Pattern 14
    def find_people_missing_vital_events(
        self,
        event_type: int = 1,
        limit: int = DEFAULT_RESULT_LIMIT,
    ):
        if limit <= 0:
            raise ValueError("limit must be positive")
        params = (event_type, limit)
        return self.db.query(_FIND_MISSING_VITAL_EVENTS_SQL, params)

    # Pattern 15
    def find_logical_inconsistencies(self, limit: int = DEFAULT_RESULT_LIMIT):
        if limit <= 0:
            raise ValueError("limit must be positive")
        return self.db.query(_FIND_LOGICAL_INCONSISTENCIES_SQL, (limit,))


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two GPS coordinates using Haversine formula.

    Args:
        lat1: Latitude of first point in decimal degrees
        lon1: Longitude of first point in decimal degrees
        lat2: Latitude of second point in decimal degrees
        lon2: Longitude of second point in decimal degrees

    Returns:
        Distance in kilometers

    Formula:
        a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
        c = 2 * atan2(√a, √(1-a))
        distance = R * c

    where R = Earth's radius (6371 km)
    """
    import math

    # Earth radius in kilometers
    R = 6371.0

    # Convert degrees to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    # Haversine formula
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance
