"""
RootsMagic query service implementing canonical query patterns.

These helpers wrap the SQL statements documented in
`data_reference/RM11_Query_Patterns.md` so downstream modules can
reuse optimized, parameterized statements consistently.
"""

from __future__ import annotations

from collections.abc import Sequence

from .database import RMDatabase

VITAL_EVENT_TYPES: tuple[int, ...] = (1, 2, 3, 4, 300)
DEFAULT_GENERATION_LIMIT = 10
DEFAULT_RESULT_LIMIT = 50


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
            filters.append("n.Surname = ?")
            params.append(surname)
        if given is not None:
            filters.append("n.Given = ?")
            params.append(given)

        where_clause = " AND ".join(filters)
        sql = f"{_SEARCH_PERSON_SQL} AND {where_clause} ORDER BY n.Surname, n.Given LIMIT ?"
        params.append(limit)
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
    def find_places_by_name(self, pattern: str, limit: int = DEFAULT_RESULT_LIMIT):
        if limit <= 0:
            raise ValueError("limit must be positive")
        like_pattern = f"%{pattern}%"
        params = (like_pattern, limit)
        return self.db.query(_FIND_PLACES_SQL, params)

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


_GET_PERSON_SQL = """
SELECT
  p.PersonID,
  n.Surname,
  n.Given,
  n.Prefix,
  n.Suffix,
  n.BirthYear,
  n.DeathYear,
  p.Sex
FROM PersonTable p
JOIN NameTable n
  ON p.PersonID = n.OwnerID
  AND n.IsPrimary = 1
WHERE p.PersonID = ?
"""

_SEARCH_PERSON_SQL = """
SELECT
  p.PersonID,
  n.Surname,
  n.Given,
  n.BirthYear,
  n.DeathYear
FROM PersonTable p
JOIN NameTable n
  ON p.PersonID = n.OwnerID
  AND n.IsPrimary = 1
WHERE 1 = 1
"""

_SEARCH_PERSON_PHONETIC_SQL = """
SELECT
  p.PersonID,
  n.Surname,
  n.Given,
  n.BirthYear,
  n.DeathYear
FROM PersonTable p
JOIN NameTable n
  ON p.PersonID = n.OwnerID
  AND n.IsPrimary = 1
WHERE n.SurnameMP = ?
ORDER BY n.Surname,
         n.Given
LIMIT ?
"""

_GET_PARENTS_SQL = """
SELECT
  father.PersonID AS FatherID,
  fn.Surname AS FatherSurname,
  fn.Given AS FatherGiven,
  fn.BirthYear AS FatherBirthYear,
  fn.DeathYear AS FatherDeathYear,
  mother.PersonID AS MotherID,
  mn.Surname AS MotherSurname,
  mn.Given AS MotherGiven,
  mn.BirthYear AS MotherBirthYear,
  mn.DeathYear AS MotherDeathYear
FROM PersonTable p
LEFT JOIN ChildTable ct
  ON p.PersonID = ct.ChildID
LEFT JOIN FamilyTable f
  ON ct.FamilyID = f.FamilyID
LEFT JOIN PersonTable father
  ON f.FatherID = father.PersonID
LEFT JOIN NameTable fn
  ON father.PersonID = fn.OwnerID
  AND fn.IsPrimary = 1
LEFT JOIN PersonTable mother
  ON f.MotherID = mother.PersonID
LEFT JOIN NameTable mn
  ON mother.PersonID = mn.OwnerID
  AND mn.IsPrimary = 1
WHERE p.PersonID = ?
LIMIT 1
"""

_GET_CHILDREN_SQL = """
SELECT
  child.PersonID,
  cn.Surname,
  cn.Given,
  cn.BirthYear,
  cn.DeathYear,
  child.Sex,
  f.FamilyID,
  birth.Date AS BirthDate,
  birth.SortDate AS BirthSortDate,
  birth_place.Name AS BirthPlace,
  death.Date AS DeathDate,
  death.SortDate AS DeathSortDate,
  death_place.Name AS DeathPlace
FROM FamilyTable f
JOIN ChildTable ct
  ON f.FamilyID = ct.FamilyID
JOIN PersonTable child
  ON ct.ChildID = child.PersonID
JOIN NameTable cn
  ON child.PersonID = cn.OwnerID
  AND cn.IsPrimary = 1
LEFT JOIN EventTable birth
  ON birth.OwnerType = 0
  AND birth.OwnerID = child.PersonID
  AND birth.EventType = 1
LEFT JOIN PlaceTable birth_place
  ON birth.PlaceID = birth_place.PlaceID
LEFT JOIN EventTable death
  ON death.OwnerType = 0
  AND death.OwnerID = child.PersonID
  AND death.EventType = 2
LEFT JOIN PlaceTable death_place
  ON death.PlaceID = death_place.PlaceID
WHERE f.FatherID = ?
   OR f.MotherID = ?
ORDER BY COALESCE(birth.SortDate, 9223372036854775807),
         cn.BirthYear,
         cn.Surname,
         cn.Given
"""

_GET_PERSON_EVENTS_SQL = """
SELECT
  e.EventID,
  ft.Name AS EventType,
  ft.FactTypeID,
  e.Date,
  e.SortDate,
  e.Details,
  pl.Name AS Place,
  e.IsPrivate,
  e.Proof
FROM EventTable e
JOIN FactTypeTable ft
  ON e.EventType = ft.FactTypeID
LEFT JOIN PlaceTable pl
  ON e.PlaceID = pl.PlaceID
WHERE e.OwnerType = 0
  AND e.OwnerID = ?
ORDER BY e.SortDate,
         ft.FactTypeID
"""

_GET_VITAL_EVENTS_SQL = """
SELECT
  e.EventID,
  ft.Name AS EventType,
  ft.FactTypeID,
  e.Date,
  e.Details,
  pl.Name AS Place
FROM EventTable e
JOIN FactTypeTable ft
  ON e.EventType = ft.FactTypeID
LEFT JOIN PlaceTable pl
  ON e.PlaceID = pl.PlaceID
WHERE e.OwnerType = 0
  AND e.OwnerID = ?
  AND e.EventType IN {placeholder}
ORDER BY e.SortDate
""".replace(
    "{placeholder}", "(" + ",".join("?" for _ in VITAL_EVENT_TYPES) + ")"
)

_GET_SPOUSES_SQL = """
SELECT DISTINCT
  spouse.PersonID,
  sn.Surname,
  sn.Given,
  sn.BirthYear,
  sn.DeathYear,
  f.FamilyID,
  marriage.Date AS MarriageDate,
  marriage.SortDate AS MarriageSortDate,
  marriage_place.Name AS MarriagePlace,
  death.Date AS DeathDate,
  death.SortDate AS DeathSortDate,
  death_place.Name AS DeathPlace
FROM FamilyTable f
JOIN PersonTable spouse
  ON spouse.PersonID = f.FatherID
  OR spouse.PersonID = f.MotherID
JOIN NameTable sn
  ON spouse.PersonID = sn.OwnerID
  AND sn.IsPrimary = 1
LEFT JOIN EventTable marriage
  ON marriage.OwnerType = 1
  AND marriage.OwnerID = f.FamilyID
  AND marriage.EventType = 300
LEFT JOIN PlaceTable marriage_place
  ON marriage.PlaceID = marriage_place.PlaceID
LEFT JOIN EventTable death
  ON death.OwnerType = 0
  AND death.OwnerID = spouse.PersonID
  AND death.EventType = 2
LEFT JOIN PlaceTable death_place
  ON death.PlaceID = death_place.PlaceID
WHERE (f.FatherID = ? OR f.MotherID = ?)
  AND spouse.PersonID != ?
ORDER BY COALESCE(marriage.SortDate, 9223372036854775807),
         sn.Surname,
         sn.Given
"""

_GET_ANCESTORS_SQL = """
WITH RECURSIVE ancestors(PersonID, Generation, Relationship) AS (
  SELECT
    p.PersonID,
    0,
    'Self'
  FROM PersonTable p
  WHERE p.PersonID = ?
  UNION ALL
  SELECT
    f.FatherID,
    ancestors.Generation + 1,
    'Father'
  FROM ancestors
  JOIN ChildTable ct
    ON ancestors.PersonID = ct.ChildID
  JOIN FamilyTable f
    ON ct.FamilyID = f.FamilyID
  WHERE f.FatherID IS NOT NULL
    AND ancestors.Generation < ?
  UNION ALL
  SELECT
    f.MotherID,
    ancestors.Generation + 1,
    'Mother'
  FROM ancestors
  JOIN ChildTable ct
    ON ancestors.PersonID = ct.ChildID
  JOIN FamilyTable f
    ON ct.FamilyID = f.FamilyID
  WHERE f.MotherID IS NOT NULL
    AND ancestors.Generation < ?
)
SELECT
  a.PersonID,
  n.Surname,
  n.Given,
  n.BirthYear,
  n.DeathYear,
  a.Generation,
  a.Relationship
FROM ancestors a
JOIN NameTable n
  ON a.PersonID = n.OwnerID
  AND n.IsPrimary = 1
WHERE a.Generation > 0
ORDER BY a.Generation,
         n.Surname,
         n.Given
"""

_GET_ANCESTORS_WITH_SPOUSES_SQL = """
SELECT
  parent.PersonID,
  n.Surname,
  n.Given,
  'Parent' AS Relationship
FROM PersonTable root
JOIN ChildTable ct
  ON root.PersonID = ct.ChildID
JOIN FamilyTable f
  ON ct.FamilyID = f.FamilyID
JOIN PersonTable parent
  ON parent.PersonID = f.FatherID
   OR parent.PersonID = f.MotherID
JOIN NameTable n
  ON parent.PersonID = n.OwnerID
  AND n.IsPrimary = 1
WHERE root.PersonID = ?
UNION
SELECT
  grandparent.PersonID,
  gn.Surname,
  gn.Given,
  'Grandparent' AS Relationship
FROM PersonTable root
JOIN ChildTable ct1
  ON root.PersonID = ct1.ChildID
JOIN FamilyTable f1
  ON ct1.FamilyID = f1.FamilyID
JOIN PersonTable parent
  ON parent.PersonID = f1.FatherID
   OR parent.PersonID = f1.MotherID
JOIN ChildTable ct2
  ON parent.PersonID = ct2.ChildID
JOIN FamilyTable f2
  ON ct2.FamilyID = f2.FamilyID
JOIN PersonTable grandparent
  ON grandparent.PersonID = f2.FatherID
   OR grandparent.PersonID = f2.MotherID
JOIN NameTable gn
  ON grandparent.PersonID = gn.OwnerID
  AND gn.IsPrimary = 1
WHERE root.PersonID = ?
ORDER BY Relationship,
         Surname,
         Given
"""

_GET_DESCENDANTS_SQL = """
WITH RECURSIVE descendants(PersonID, Generation) AS (
  SELECT
    p.PersonID,
    0
  FROM PersonTable p
  WHERE p.PersonID = ?
  UNION ALL
  SELECT
    ct.ChildID,
    descendants.Generation + 1
  FROM descendants
  JOIN FamilyTable f
    ON descendants.PersonID = f.FatherID
     OR descendants.PersonID = f.MotherID
  JOIN ChildTable ct
    ON f.FamilyID = ct.FamilyID
  WHERE descendants.Generation < ?
)
SELECT
  d.PersonID,
  n.Surname,
  n.Given,
  n.BirthYear,
  n.DeathYear,
  d.Generation
FROM descendants d
JOIN NameTable n
  ON d.PersonID = n.OwnerID
  AND n.IsPrimary = 1
WHERE d.Generation > 0
ORDER BY d.Generation,
         n.Surname,
         n.Given
"""

_GET_EVENT_CITATIONS_SQL = """
SELECT
  c.CitationID,
  c.CitationName,
  s.SourceID,
  s.Name AS SourceName,
  s.TemplateID
FROM CitationLinkTable cl
JOIN CitationTable c
  ON cl.CitationID = c.CitationID
JOIN SourceTable s
  ON c.SourceID = s.SourceID
WHERE cl.OwnerType = 2
  AND cl.OwnerID = ?
ORDER BY cl.SortOrder,
         c.CitationID
"""

_GET_UNSOURCED_EVENTS_SQL_TEMPLATE = """
SELECT
  e.EventID,
  ft.Name AS EventType,
  p.PersonID,
  n.Surname,
  n.Given,
  e.Date,
  pl.Name AS Place
FROM EventTable e
JOIN FactTypeTable ft
  ON e.EventType = ft.FactTypeID
JOIN PersonTable p
  ON e.OwnerID = p.PersonID
JOIN NameTable n
  ON p.PersonID = n.OwnerID
  AND n.IsPrimary = 1
LEFT JOIN PlaceTable pl
  ON e.PlaceID = pl.PlaceID
LEFT JOIN CitationLinkTable cl
  ON e.EventID = cl.OwnerID
  AND cl.OwnerType = 2
WHERE e.OwnerType = 0
  AND e.EventType IN ({event_type_list})
  AND cl.LinkID IS NULL
"""

_FIND_PLACES_SQL = """
SELECT
  PlaceID,
  Name
FROM PlaceTable
WHERE Name LIKE ?
ORDER BY Name
LIMIT ?
"""

_FIND_MISSING_VITAL_EVENTS_SQL = """
SELECT
  p.PersonID,
  n.Surname,
  n.Given,
  n.BirthYear
FROM PersonTable p
JOIN NameTable n
  ON p.PersonID = n.OwnerID
  AND n.IsPrimary = 1
LEFT JOIN EventTable evt
  ON p.PersonID = evt.OwnerID
  AND evt.OwnerType = 0
  AND evt.EventType = ?
WHERE evt.EventID IS NULL
ORDER BY n.Surname,
         n.Given
LIMIT ?
"""

_FIND_LOGICAL_INCONSISTENCIES_SQL = """
SELECT
  p.PersonID,
  n.Surname,
  n.Given,
  birth.Date AS BirthDate,
  birth.SortDate AS BirthSort,
  death.Date AS DeathDate,
  death.SortDate AS DeathSort
FROM PersonTable p
JOIN NameTable n
  ON p.PersonID = n.OwnerID
  AND n.IsPrimary = 1
JOIN EventTable birth
  ON p.PersonID = birth.OwnerID
  AND birth.OwnerType = 0
  AND birth.EventType = 1
JOIN EventTable death
  ON p.PersonID = death.OwnerID
  AND death.OwnerType = 0
  AND death.EventType = 2
WHERE birth.SortDate != 9223372036854775807
  AND death.SortDate != 9223372036854775807
  AND death.SortDate < birth.SortDate
ORDER BY death.SortDate,
         birth.SortDate
LIMIT ?
"""
