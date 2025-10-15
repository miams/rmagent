"""
RootsMagic Name Parser

Handles name selection and formatting from RootsMagic NameTable.

Implements logic for:
- Primary name selection (IsPrimary=1)
- Context-aware name selection (maiden vs married)
- Full name construction from components
- Multiple name handling

Reference: RM11_Name_Display_Logic.md
"""

import sqlite3
from dataclasses import dataclass
from enum import IntEnum


class NameType(IntEnum):
    """NameType values from NameTable."""

    BIRTH = 0  # Birth/Standard name (99.6%)
    AKA = 1  # Also Known As
    MARRIED = 5  # Married name
    IMMIGRANT = 6  # Immigrant name (pre-immigration)
    MAIDEN = 7  # Maiden name (pre-marriage surname)


@dataclass
class Name:
    """Represents a person's name with all components."""

    name_id: int
    person_id: int
    is_primary: bool
    name_type: NameType

    # Name components
    surname: str | None = None
    given: str | None = None
    prefix: str | None = None
    suffix: str | None = None
    nickname: str | None = None

    # Metaphone encodings (for phonetic searching)
    surname_mp: str | None = None
    given_mp: str | None = None

    # Birth/death years (for display)
    birth_year: int | None = None
    death_year: int | None = None

    def full_name(self, include_nickname: bool = False) -> str:
        """
        Construct full name from components.

        Args:
            include_nickname: Include nickname in parentheses

        Returns:
            Formatted full name

        Example:
            >>> name.full_name()
            'Dr. John William Smith Jr.'
            >>> name.full_name(include_nickname=True)
            'Dr. John William Smith Jr. ("Jack")'
        """
        parts = []

        # Prefix (Dr., Rev., Sir)
        if self.prefix:
            parts.append(self.prefix)

        # Given name(s)
        if self.given:
            parts.append(self.given)

        # Surname
        if self.surname:
            parts.append(self.surname)

        # Suffix (Jr., III, Esq.)
        if self.suffix:
            parts.append(self.suffix)

        full = " ".join(parts)

        # Nickname in parentheses
        if include_nickname and self.nickname:
            full += f' ("{self.nickname}")'

        return full

    def short_name(self) -> str:
        """
        Get short name (Given Surname).

        Returns:
            Short formatted name

        Example:
            >>> name.short_name()
            'John Smith'
        """
        parts = []

        if self.given:
            parts.append(self.given)

        if self.surname:
            parts.append(self.surname)

        return " ".join(parts)

    def surname_first(self) -> str:
        """
        Get name in surname-first format (Surname, Given).

        Returns:
            Surname-first formatted name

        Example:
            >>> name.surname_first()
            'Smith, John William'
        """
        if self.surname and self.given:
            return f"{self.surname}, {self.given}"
        elif self.surname:
            return self.surname
        elif self.given:
            return self.given
        else:
            return ""

    def lifespan(self) -> str:
        """
        Get lifespan string (birth_year-death_year).

        Returns:
            Lifespan string

        Example:
            >>> name.lifespan()
            '(1850-1920)'
            >>> name.lifespan()  # Still living
            '(1968-)'
        """
        if not self.birth_year:
            return ""

        if self.death_year:
            return f"({self.birth_year}-{self.death_year})"
        else:
            return f"({self.birth_year}-)"


def get_primary_name(person_id: int, db_connection: sqlite3.Connection) -> Name | None:
    """
    Get primary name for a person (IsPrimary=1).

    Args:
        person_id: PersonID to look up
        db_connection: Database connection

    Returns:
        Name object or None if not found

    Example:
        >>> name = get_primary_name(1, db)
        >>> name.full_name()
        'John William Smith'
    """
    cursor = db_connection.cursor()

    cursor.execute(
        """
        SELECT
            n.NameID,
            n.OwnerID,
            n.IsPrimary,
            n.NameType,
            n.Surname,
            n.Given,
            n.Prefix,
            n.Suffix,
            n.Nickname,
            n.SurnameMP,
            n.GivenMP,
            n.BirthYear,
            n.DeathYear
        FROM NameTable n
        WHERE n.OwnerID = ? AND n.IsPrimary = 1
    """,
        (person_id,),
    )

    row = cursor.fetchone()

    if not row:
        return None

    return Name(
        name_id=row[0],
        person_id=row[1],
        is_primary=row[2] == 1,
        name_type=NameType(row[3]),
        surname=row[4],
        given=row[5],
        prefix=row[6],
        suffix=row[7],
        nickname=row[8],
        surname_mp=row[9],
        given_mp=row[10],
        birth_year=row[11] if row[11] and row[11] > 0 else None,
        death_year=row[12] if row[12] and row[12] > 0 else None,
    )


def get_all_names(person_id: int, db_connection: sqlite3.Connection) -> list[Name]:
    """
    Get all names for a person (primary and alternates).

    Args:
        person_id: PersonID to look up
        db_connection: Database connection

    Returns:
        List of Name objects, ordered by IsPrimary DESC, NameType

    Example:
        >>> names = get_all_names(1, db)
        >>> names[0].is_primary
        True
        >>> names[1].name_type
        NameType.MAIDEN
    """
    cursor = db_connection.cursor()

    cursor.execute(
        """
        SELECT
            n.NameID,
            n.OwnerID,
            n.IsPrimary,
            n.NameType,
            n.Surname,
            n.Given,
            n.Prefix,
            n.Suffix,
            n.Nickname,
            n.SurnameMP,
            n.GivenMP,
            n.BirthYear,
            n.DeathYear
        FROM NameTable n
        WHERE n.OwnerID = ?
        ORDER BY n.IsPrimary DESC, n.NameType
    """,
        (person_id,),
    )

    names = []
    for row in cursor.fetchall():
        names.append(
            Name(
                name_id=row[0],
                person_id=row[1],
                is_primary=row[2] == 1,
                name_type=NameType(row[3]),
                surname=row[4],
                given=row[5],
                prefix=row[6],
                suffix=row[7],
                nickname=row[8],
                surname_mp=row[9],
                given_mp=row[10],
                birth_year=row[11] if row[11] and row[11] > 0 else None,
                death_year=row[12] if row[12] and row[12] > 0 else None,
            )
        )

    return names


def get_name_at_date(person_id: int, event_sort_date: int | None, db_connection: sqlite3.Connection) -> Name | None:
    """
    Get appropriate name for a specific date (context-aware).

    For events before marriage: prefer maiden name if available
    For events after marriage: use primary (usually married) name

    Args:
        person_id: PersonID to look up
        event_sort_date: SortDate of event (or None for current name)
        db_connection: Database connection

    Returns:
        Name object appropriate for the date

    Example:
        >>> # Birth event (before marriage) - returns maiden name
        >>> name = get_name_at_date(123, birth_date, db)
        >>> name.surname
        'Jones'
        >>> # Death event (after marriage) - returns married name
        >>> name = get_name_at_date(123, death_date, db)
        >>> name.surname
        'Smith'
    """
    cursor = db_connection.cursor()

    # Get marriage date if exists
    cursor.execute(
        """
        SELECT MIN(e.SortDate)
        FROM FamilyTable f
        JOIN EventTable e ON f.FamilyID = e.OwnerID AND e.EventType = 300
        WHERE (f.FatherID = ? OR f.MotherID = ?)
          AND e.SortDate IS NOT NULL
          AND e.SortDate > 0
          AND e.SortDate < 9223372036854775807
    """,
        (person_id, person_id),
    )

    marriage_result = cursor.fetchone()

    # If event is before marriage, try to get maiden name
    if marriage_result and marriage_result[0]:
        marriage_date = marriage_result[0]

        if event_sort_date and event_sort_date < marriage_date:
            # Try to get maiden name (NameType=7)
            cursor.execute(
                """
                SELECT
                    n.NameID,
                    n.OwnerID,
                    n.IsPrimary,
                    n.NameType,
                    n.Surname,
                    n.Given,
                    n.Prefix,
                    n.Suffix,
                    n.Nickname,
                    n.SurnameMP,
                    n.GivenMP,
                    n.BirthYear,
                    n.DeathYear
                FROM NameTable n
                WHERE n.OwnerID = ? AND n.NameType = 7
            """,
                (person_id,),
            )

            maiden_row = cursor.fetchone()

            if maiden_row:
                return Name(
                    name_id=maiden_row[0],
                    person_id=maiden_row[1],
                    is_primary=maiden_row[2] == 1,
                    name_type=NameType(maiden_row[3]),
                    surname=maiden_row[4],
                    given=maiden_row[5],
                    prefix=maiden_row[6],
                    suffix=maiden_row[7],
                    nickname=maiden_row[8],
                    surname_mp=maiden_row[9],
                    given_mp=maiden_row[10],
                    birth_year=maiden_row[11] if maiden_row[11] and maiden_row[11] > 0 else None,
                    death_year=maiden_row[12] if maiden_row[12] and maiden_row[12] > 0 else None,
                )

    # Default to primary name
    return get_primary_name(person_id, db_connection)


def format_full_name(
    surname: str | None = None,
    given: str | None = None,
    prefix: str | None = None,
    suffix: str | None = None,
    nickname: str | None = None,
    include_nickname: bool = False,
) -> str:
    """
    Construct full name from individual components.

    Args:
        surname: Last name
        given: First and middle names
        prefix: Title (Dr., Rev., Sir)
        suffix: Designation (Jr., III, Esq.)
        nickname: Informal name
        include_nickname: Include nickname in parentheses

    Returns:
        Formatted full name

    Example:
        >>> format_full_name(
        ...     surname="Smith",
        ...     given="John William",
        ...     prefix="Dr.",
        ...     suffix="Jr.",
        ...     nickname="Jack",
        ...     include_nickname=True
        ... )
        'Dr. John William Smith Jr. ("Jack")'
    """
    parts = []

    if prefix:
        parts.append(prefix)

    if given:
        parts.append(given)

    if surname:
        parts.append(surname)

    if suffix:
        parts.append(suffix)

    full = " ".join(parts)

    if include_nickname and nickname:
        full += f' ("{nickname}")'

    return full


def validate_name_requirements(person_id: int, db_connection: sqlite3.Connection) -> list[str]:
    """
    Validate name requirements for a person.

    Checks:
    - Exactly one primary name exists
    - At least surname or given name is populated

    Args:
        person_id: PersonID to validate
        db_connection: Database connection

    Returns:
        List of validation issues (empty if valid)

    Example:
        >>> issues = validate_name_requirements(1, db)
        >>> if issues:
        ...     print("Issues found:", issues)
    """
    issues = []
    cursor = db_connection.cursor()

    # Check for exactly one primary name
    cursor.execute(
        """
        SELECT COUNT(*)
        FROM NameTable
        WHERE OwnerID = ? AND IsPrimary = 1
    """,
        (person_id,),
    )

    primary_count = cursor.fetchone()[0]

    if primary_count == 0:
        issues.append("No primary name (IsPrimary=1) found")
    elif primary_count > 1:
        issues.append(f"Multiple primary names found ({primary_count})")

    # Check that primary name has surname or given
    cursor.execute(
        """
        SELECT Surname, Given
        FROM NameTable
        WHERE OwnerID = ? AND IsPrimary = 1
    """,
        (person_id,),
    )

    result = cursor.fetchone()

    if result:
        surname, given = result
        if (not surname or surname.strip() == "") and (not given or given.strip() == ""):
            issues.append("Primary name missing both surname and given name")

    return issues
