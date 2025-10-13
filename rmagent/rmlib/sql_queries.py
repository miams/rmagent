"""
SQL query constants for RootsMagic query service.

Contains all parameterized SQL statements used by QueryService.
These queries are documented in `data_reference/RM11_Query_Patterns.md`.
"""

# Import constants needed for query construction
VITAL_EVENT_TYPES: tuple[int, ...] = (1, 2, 3, 4, 300)

# Pattern 1: Get person with primary name
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

# Pattern 2: Search person by name (base query)
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

# Pattern 2: Search by phonetic surname
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

# Pattern 2: Flexible name search
_SEARCH_NAMES_FLEXIBLE_SQL = """
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
WHERE n.Surname LIKE ? COLLATE RMNOCASE
   OR n.Given LIKE ? COLLATE RMNOCASE
ORDER BY
  n.IsPrimary DESC,
  CASE
    WHEN n.Surname LIKE ? COLLATE RMNOCASE THEN 1
    WHEN n.Given LIKE ? COLLATE RMNOCASE THEN 2
    ELSE 3
  END,
  n.Surname,
  n.Given
LIMIT ?
"""

# Pattern 2: Search females by maiden or married surname
_SEARCH_NAMES_WITH_MARRIED_SQL = """
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
  AND (pn.Surname LIKE ? COLLATE RMNOCASE
    OR pn.Given LIKE ? COLLATE RMNOCASE)
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
  AND spouse_name.Surname LIKE ? COLLATE RMNOCASE
ORDER BY 2, 3
LIMIT ?
"""

# Pattern 3: Get parents
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

# Pattern 4: Get children
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

# Pattern 5: Get person events
_GET_PERSON_EVENTS_SQL = """
SELECT
  e.EventID,
  ft.Name AS EventType,
  ft.FactTypeID,
  e.Date,
  e.SortDate,
  e.Details,
  e.Note,
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

# Pattern 6: Get vital events
_GET_VITAL_EVENTS_SQL = """
SELECT
  e.EventID,
  ft.Name AS EventType,
  ft.FactTypeID,
  e.Date,
  e.Details,
  e.Note,
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

# Pattern 7: Get spouses
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

# Pattern 8: Get direct ancestors
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

# Pattern 9: Get ancestors with spouses
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

# Pattern 10: Get descendants
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

# Pattern 11: Get event citations
_GET_EVENT_CITATIONS_SQL = """
SELECT
  c.CitationID,
  c.CitationName,
  c.Footnote,
  c.ShortFootnote,
  c.Bibliography AS CitationBibliography,
  c.Fields AS CitationFields,
  s.SourceID,
  s.Name AS SourceName,
  s.TemplateID,
  s.ActualText AS SourceBibliography,
  s.Fields AS SourceFields,
  st.Name AS TemplateName
FROM CitationLinkTable cl
JOIN CitationTable c
  ON cl.CitationID = c.CitationID
JOIN SourceTable s
  ON c.SourceID = s.SourceID
LEFT JOIN SourceTemplateTable st
  ON s.TemplateID = st.TemplateID
WHERE cl.OwnerType = 2
  AND cl.OwnerID = ?
ORDER BY cl.SortOrder,
         c.CitationID
"""

# Pattern 12: Get unsourced vital events
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

# Pattern 13: Find places
_FIND_PLACES_SQL = """
SELECT
  PlaceID,
  Name,
  Latitude,
  Longitude
FROM PlaceTable
WHERE Name LIKE ?
ORDER BY Name
LIMIT ?
"""

# Pattern 14: Find people missing vital events
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

# Pattern 15: Find logical inconsistencies
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
