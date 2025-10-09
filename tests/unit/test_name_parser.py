"""
Unit tests for rmlib.parsers.name_parser module.

Tests name selection and formatting for:
- Primary name selection
- Multiple name handling
- Context-aware name selection (maiden vs married)
- Full name construction
- Validation
"""

import pytest
import sqlite3
from pathlib import Path

from rmagent.rmlib.parsers.name_parser import (
    get_primary_name,
    get_all_names,
    get_name_at_date,
    format_full_name,
    validate_name_requirements,
    NameType,
    Name,
)


@pytest.fixture
def test_db(tmp_path):
    """Create a test database with name records."""
    db_path = tmp_path / "test_names.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create NameTable
    cursor.execute("""
        CREATE TABLE NameTable (
            NameID INTEGER PRIMARY KEY,
            OwnerID INTEGER,
            IsPrimary INTEGER,
            NameType INTEGER,
            Surname TEXT,
            Given TEXT,
            Prefix TEXT,
            Suffix TEXT,
            Nickname TEXT,
            SurnameMP TEXT,
            GivenMP TEXT,
            BirthYear INTEGER,
            DeathYear INTEGER
        )
    """)

    # Person 1: Standard name
    cursor.execute("""
        INSERT INTO NameTable VALUES
        (1, 1, 1, 0, 'Smith', 'John William', 'Dr.', 'Jr.', 'Jack', 'SM0', 'JNW', 1850, 1920)
    """)

    # Person 2: Multiple names (primary + maiden)
    cursor.execute("""
        INSERT INTO NameTable VALUES
        (2, 2, 1, 0, 'Smith', 'Mary Elizabeth', NULL, NULL, NULL, 'SM0', 'MRL', 1855, 1925),
        (3, 2, 0, 7, 'Jones', 'Mary Elizabeth', NULL, NULL, NULL, 'JNS', 'MRL', 1855, 1925)
    """)

    # Person 3: Multiple alternate names (spelling variations)
    cursor.execute("""
        INSERT INTO NameTable VALUES
        (4, 3, 1, 0, 'Tittsworth', 'James Fredrick', NULL, NULL, 'Fred', 'TTS0', 'JMSFR', 1880, 1960),
        (5, 3, 0, 0, 'Titsworth', 'James F.', NULL, NULL, NULL, 'TTS0', 'JMSF', 1880, 1960),
        (6, 3, 0, 1, 'Tittsworth', 'Fred', NULL, NULL, NULL, 'TTS0', 'FRT', 1880, 1960)
    """)

    # Person 4: No primary name (data quality issue)
    cursor.execute("""
        INSERT INTO NameTable VALUES
        (7, 4, 0, 0, 'Johnson', 'Robert', NULL, NULL, NULL, 'JNS', 'RBR', 1900, 1970)
    """)

    # Person 5: Multiple primary names (data quality issue)
    cursor.execute("""
        INSERT INTO NameTable VALUES
        (8, 5, 1, 0, 'Williams', 'Sarah', NULL, NULL, NULL, 'WLM', 'SR', 1910, 1980),
        (9, 5, 1, 0, 'Williams', 'Sara', NULL, NULL, NULL, 'WLM', 'SR', 1910, 1980)
    """)

    # Person 6: Name with no surname or given (data quality issue)
    cursor.execute("""
        INSERT INTO NameTable VALUES
        (10, 6, 1, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 0, 0)
    """)

    # Create FamilyTable for marriage date testing
    cursor.execute("""
        CREATE TABLE FamilyTable (
            FamilyID INTEGER PRIMARY KEY,
            FatherID INTEGER,
            MotherID INTEGER
        )
    """)

    # Create EventTable for marriage date testing
    cursor.execute("""
        CREATE TABLE EventTable (
            EventID INTEGER PRIMARY KEY,
            EventType INTEGER,
            OwnerType INTEGER,
            OwnerID INTEGER,
            SortDate INTEGER
        )
    """)

    # Person 2 marriage (EventType=300, SortDate for 1875-06-15)
    cursor.execute("""
        INSERT INTO FamilyTable VALUES (1, 10, 2)
    """)
    cursor.execute("""
        INSERT INTO EventTable VALUES (1, 300, 1, 1, 18750615000000)
    """)

    conn.commit()
    return db_path


class TestName:
    """Test Name dataclass methods."""

    def test_full_name_all_components(self):
        """Test full name with all components."""
        name = Name(
            name_id=1,
            person_id=1,
            is_primary=True,
            name_type=NameType.BIRTH,
            surname="Smith",
            given="John William",
            prefix="Dr.",
            suffix="Jr.",
            nickname="Jack"
        )

        assert name.full_name() == "Dr. John William Smith Jr."
        assert name.full_name(include_nickname=True) == 'Dr. John William Smith Jr. ("Jack")'

    def test_full_name_minimal(self):
        """Test full name with just surname and given."""
        name = Name(
            name_id=1,
            person_id=1,
            is_primary=True,
            name_type=NameType.BIRTH,
            surname="Smith",
            given="John"
        )

        assert name.full_name() == "John Smith"

    def test_full_name_surname_only(self):
        """Test full name with surname only."""
        name = Name(
            name_id=1,
            person_id=1,
            is_primary=True,
            name_type=NameType.BIRTH,
            surname="Smith"
        )

        assert name.full_name() == "Smith"

    def test_short_name(self):
        """Test short name format."""
        name = Name(
            name_id=1,
            person_id=1,
            is_primary=True,
            name_type=NameType.BIRTH,
            surname="Smith",
            given="John William",
            prefix="Dr.",
            suffix="Jr."
        )

        assert name.short_name() == "John William Smith"

    def test_surname_first(self):
        """Test surname-first format."""
        name = Name(
            name_id=1,
            person_id=1,
            is_primary=True,
            name_type=NameType.BIRTH,
            surname="Smith",
            given="John William"
        )

        assert name.surname_first() == "Smith, John William"

    def test_lifespan_both_dates(self):
        """Test lifespan with birth and death."""
        name = Name(
            name_id=1,
            person_id=1,
            is_primary=True,
            name_type=NameType.BIRTH,
            surname="Smith",
            given="John",
            birth_year=1850,
            death_year=1920
        )

        assert name.lifespan() == "(1850-1920)"

    def test_lifespan_living(self):
        """Test lifespan for living person."""
        name = Name(
            name_id=1,
            person_id=1,
            is_primary=True,
            name_type=NameType.BIRTH,
            surname="Smith",
            given="John",
            birth_year=1968
        )

        assert name.lifespan() == "(1968-)"

    def test_lifespan_no_birth(self):
        """Test lifespan with no birth year."""
        name = Name(
            name_id=1,
            person_id=1,
            is_primary=True,
            name_type=NameType.BIRTH,
            surname="Smith",
            given="John"
        )

        assert name.lifespan() == ""


class TestGetPrimaryName:
    """Test get_primary_name function."""

    def test_get_primary_name_found(self, test_db):
        """Test getting primary name."""
        conn = sqlite3.connect(str(test_db))

        name = get_primary_name(1, conn)

        assert name is not None
        assert name.person_id == 1
        assert name.is_primary is True
        assert name.surname == "Smith"
        assert name.given == "John William"
        assert name.prefix == "Dr."
        assert name.suffix == "Jr."
        assert name.nickname == "Jack"
        assert name.birth_year == 1850
        assert name.death_year == 1920

        conn.close()

    def test_get_primary_name_not_found(self, test_db):
        """Test getting primary name for person without one."""
        conn = sqlite3.connect(str(test_db))

        name = get_primary_name(4, conn)

        assert name is None

        conn.close()

    def test_get_primary_name_nonexistent_person(self, test_db):
        """Test getting primary name for non-existent person."""
        conn = sqlite3.connect(str(test_db))

        name = get_primary_name(999, conn)

        assert name is None

        conn.close()


class TestGetAllNames:
    """Test get_all_names function."""

    def test_get_all_names_single(self, test_db):
        """Test getting all names for person with one name."""
        conn = sqlite3.connect(str(test_db))

        names = get_all_names(1, conn)

        assert len(names) == 1
        assert names[0].surname == "Smith"
        assert names[0].is_primary is True

        conn.close()

    def test_get_all_names_multiple(self, test_db):
        """Test getting all names for person with multiple names."""
        conn = sqlite3.connect(str(test_db))

        names = get_all_names(2, conn)

        assert len(names) == 2
        # Primary name first
        assert names[0].is_primary is True
        assert names[0].surname == "Smith"
        assert names[0].name_type == NameType.BIRTH
        # Maiden name second
        assert names[1].is_primary is False
        assert names[1].surname == "Jones"
        assert names[1].name_type == NameType.MAIDEN

        conn.close()

    def test_get_all_names_spelling_variations(self, test_db):
        """Test getting all names with spelling variations."""
        conn = sqlite3.connect(str(test_db))

        names = get_all_names(3, conn)

        assert len(names) == 3
        # Primary name first
        assert names[0].surname == "Tittsworth"
        assert names[0].given == "James Fredrick"
        # Alternates follow
        assert names[1].surname == "Titsworth"
        assert names[2].given == "Fred"
        assert names[2].name_type == NameType.AKA

        conn.close()

    def test_get_all_names_empty(self, test_db):
        """Test getting all names for non-existent person."""
        conn = sqlite3.connect(str(test_db))

        names = get_all_names(999, conn)

        assert len(names) == 0

        conn.close()


class TestGetNameAtDate:
    """Test get_name_at_date function (context-aware)."""

    def test_get_name_before_marriage(self, test_db):
        """Test getting name for event before marriage (maiden name)."""
        conn = sqlite3.connect(str(test_db))

        # Birth date (1855) before marriage (1875) - should return maiden name
        birth_date = 18550101000000

        name = get_name_at_date(2, birth_date, conn)

        assert name is not None
        assert name.surname == "Jones"  # Maiden name
        assert name.name_type == NameType.MAIDEN

        conn.close()

    def test_get_name_after_marriage(self, test_db):
        """Test getting name for event after marriage (married name)."""
        conn = sqlite3.connect(str(test_db))

        # Death date (1925) after marriage (1875) - should return primary (married) name
        death_date = 19250101000000

        name = get_name_at_date(2, death_date, conn)

        assert name is not None
        assert name.surname == "Smith"  # Married name (primary)
        assert name.is_primary is True

        conn.close()

    def test_get_name_no_date(self, test_db):
        """Test getting name with no event date (current name)."""
        conn = sqlite3.connect(str(test_db))

        name = get_name_at_date(2, None, conn)

        assert name is not None
        assert name.surname == "Smith"  # Primary name
        assert name.is_primary is True

        conn.close()

    def test_get_name_no_marriage(self, test_db):
        """Test getting name for person with no marriage."""
        conn = sqlite3.connect(str(test_db))

        name = get_name_at_date(1, 18600101000000, conn)

        assert name is not None
        assert name.surname == "Smith"  # Primary name
        assert name.is_primary is True

        conn.close()

    def test_get_name_no_maiden_name(self, test_db):
        """Test getting name before marriage when no maiden name exists."""
        conn = sqlite3.connect(str(test_db))

        # Person 1 has no maiden name, should return primary even for early date
        early_date = 18400101000000

        name = get_name_at_date(1, early_date, conn)

        assert name is not None
        assert name.surname == "Smith"
        assert name.is_primary is True

        conn.close()


class TestFormatFullName:
    """Test format_full_name function."""

    def test_format_all_components(self):
        """Test formatting with all components."""
        full = format_full_name(
            surname="Smith",
            given="John William",
            prefix="Dr.",
            suffix="Jr.",
            nickname="Jack",
            include_nickname=True
        )

        assert full == 'Dr. John William Smith Jr. ("Jack")'

    def test_format_minimal(self):
        """Test formatting with just surname and given."""
        full = format_full_name(surname="Smith", given="John")

        assert full == "John Smith"

    def test_format_no_nickname(self):
        """Test formatting without nickname."""
        full = format_full_name(
            surname="Smith",
            given="John",
            nickname="Jack",
            include_nickname=False
        )

        assert full == "John Smith"

    def test_format_surname_only(self):
        """Test formatting with surname only."""
        full = format_full_name(surname="Smith")

        assert full == "Smith"

    def test_format_given_only(self):
        """Test formatting with given only."""
        full = format_full_name(given="John")

        assert full == "John"

    def test_format_empty(self):
        """Test formatting with no components."""
        full = format_full_name()

        assert full == ""


class TestValidateNameRequirements:
    """Test validate_name_requirements function."""

    def test_validate_valid_person(self, test_db):
        """Test validation for person with valid name."""
        conn = sqlite3.connect(str(test_db))

        issues = validate_name_requirements(1, conn)

        assert len(issues) == 0

        conn.close()

    def test_validate_no_primary_name(self, test_db):
        """Test validation for person without primary name."""
        conn = sqlite3.connect(str(test_db))

        issues = validate_name_requirements(4, conn)

        assert len(issues) == 1
        assert "No primary name" in issues[0]

        conn.close()

    def test_validate_multiple_primary_names(self, test_db):
        """Test validation for person with multiple primary names."""
        conn = sqlite3.connect(str(test_db))

        issues = validate_name_requirements(5, conn)

        assert len(issues) == 1
        assert "Multiple primary names" in issues[0]

        conn.close()

    def test_validate_missing_surname_and_given(self, test_db):
        """Test validation for name missing both surname and given."""
        conn = sqlite3.connect(str(test_db))

        issues = validate_name_requirements(6, conn)

        assert len(issues) == 1
        assert "missing both surname and given" in issues[0]

        conn.close()


class TestNameTypeEnum:
    """Test NameType enumeration."""

    def test_name_type_values(self):
        """Test NameType enum values."""
        assert NameType.BIRTH == 0
        assert NameType.AKA == 1
        assert NameType.MARRIED == 5
        assert NameType.IMMIGRANT == 6
        assert NameType.MAIDEN == 7

    def test_name_type_names(self):
        """Test NameType enum names."""
        assert NameType.BIRTH.name == "BIRTH"
        assert NameType.AKA.name == "AKA"
        assert NameType.MARRIED.name == "MARRIED"
        assert NameType.IMMIGRANT.name == "IMMIGRANT"
        assert NameType.MAIDEN.name == "MAIDEN"


class TestRealWorldScenarios:
    """Test real-world name scenarios."""

    def test_married_woman_name_timeline(self, test_db):
        """Test name selection for married woman across timeline."""
        conn = sqlite3.connect(str(test_db))

        # Birth: before marriage (1855)
        birth_name = get_name_at_date(2, 18550814000000, conn)
        assert birth_name.surname == "Jones"  # Maiden name

        # Marriage: on marriage date (1875-06-15)
        marriage_name = get_name_at_date(2, 18750615000000, conn)
        # At marriage date itself, use primary (married) name
        assert marriage_name.surname == "Smith"

        # Death: after marriage (1925)
        death_name = get_name_at_date(2, 19250101000000, conn)
        assert death_name.surname == "Smith"  # Married name

        conn.close()

    def test_person_with_spelling_variations(self, test_db):
        """Test handling person with multiple spelling variations."""
        conn = sqlite3.connect(str(test_db))

        # Primary name
        primary = get_primary_name(3, conn)
        assert primary.surname == "Tittsworth"
        assert primary.full_name() == 'James Fredrick Tittsworth'
        assert primary.full_name(include_nickname=True) == 'James Fredrick Tittsworth ("Fred")'

        # All names
        all_names = get_all_names(3, conn)
        assert len(all_names) == 3

        # Primary first
        assert all_names[0].surname == "Tittsworth"
        assert all_names[0].is_primary is True

        # Alternates
        assert all_names[1].surname == "Titsworth"
        assert all_names[2].given == "Fred"

        conn.close()
