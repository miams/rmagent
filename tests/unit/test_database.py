"""
Unit tests for rmlib.database module.

Tests the RMDatabase class for:
- Connection management
- RMNOCASE collation loading
- Error handling
- Query methods
"""

import sqlite3
from pathlib import Path

import pytest

from rmagent.rmlib.database import (
    DatabaseError,
    DatabaseNotFoundError,
    ExtensionLoadError,
    RMDatabase,
)


class TestRMDatabase:
    """Test suite for RMDatabase class."""

    @pytest.fixture
    def db_path(self, tmp_path):
        """Create a temporary SQLite database for testing."""
        db_file = tmp_path / "test.rmtree"
        conn = sqlite3.connect(str(db_file))

        # Create a simple test table
        conn.execute(
            """
            CREATE TABLE PersonTable (
                PersonID INTEGER PRIMARY KEY,
                Sex INTEGER,
                Living INTEGER
            )
        """
        )

        # Insert test data
        conn.execute("INSERT INTO PersonTable VALUES (1, 0, 1)")
        conn.execute("INSERT INTO PersonTable VALUES (2, 1, 0)")
        conn.commit()
        conn.close()

        return db_file

    @pytest.fixture
    def extension_path(self):
        """Return path to ICU extension."""
        return Path("./sqlite-extension/icu.dylib")

    def test_database_not_found(self):
        """Test that DatabaseNotFoundError is raised for missing database."""
        with pytest.raises(DatabaseNotFoundError, match="Database file not found"):
            RMDatabase("nonexistent.rmtree")

    def test_extension_not_found(self, db_path):
        """Test that ExtensionLoadError is raised for missing extension."""
        with pytest.raises(ExtensionLoadError, match="ICU extension not found"):
            with RMDatabase(db_path, extension_path="nonexistent.dylib"):
                pass

    def test_connection_with_rmnocase(self, db_path, extension_path):
        """Test successful connection with RMNOCASE collation."""
        # Skip this test if extension doesn't exist
        if not extension_path.exists():
            pytest.skip("ICU extension not available")

        with RMDatabase(db_path, extension_path=extension_path) as db:
            assert db._conn is not None
            # Verify we can execute a simple query
            result = db.query_value("SELECT COUNT(*) FROM PersonTable")
            assert result == 2

    def test_context_manager(self, db_path, extension_path):
        """Test context manager protocol."""
        # Skip if extension doesn't exist
        if not extension_path.exists():
            pytest.skip("ICU extension not available")

        db = RMDatabase(db_path, extension_path=extension_path)
        assert db._conn is None

        with db:
            assert db._conn is not None

        assert db._conn is None

    def test_query_method(self, db_path, extension_path):
        """Test query method returns all results."""
        # Skip if extension doesn't exist
        if not extension_path.exists():
            pytest.skip("ICU extension not available")

        with RMDatabase(db_path, extension_path=extension_path) as db:
            results = db.query("SELECT * FROM PersonTable")
            assert len(results) == 2
            assert results[0]["PersonID"] == 1

    def test_query_one_method(self, db_path, extension_path):
        """Test query_one method returns single result."""
        # Skip if extension doesn't exist
        if not extension_path.exists():
            pytest.skip("ICU extension not available")

        with RMDatabase(db_path, extension_path=extension_path) as db:
            result = db.query_one("SELECT * FROM PersonTable WHERE PersonID = ?", (1,))
            assert result is not None
            assert result["PersonID"] == 1
            assert result["Sex"] == 0

    def test_query_one_no_results(self, db_path, extension_path):
        """Test query_one returns None when no results."""
        # Skip if extension doesn't exist
        if not extension_path.exists():
            pytest.skip("ICU extension not available")

        with RMDatabase(db_path, extension_path=extension_path) as db:
            result = db.query_one("SELECT * FROM PersonTable WHERE PersonID = ?", (999,))
            assert result is None

    def test_query_value_method(self, db_path, extension_path):
        """Test query_value method returns single value."""
        # Skip if extension doesn't exist
        if not extension_path.exists():
            pytest.skip("ICU extension not available")

        with RMDatabase(db_path, extension_path=extension_path) as db:
            count = db.query_value("SELECT COUNT(*) FROM PersonTable")
            assert count == 2

    def test_query_value_no_results(self, db_path, extension_path):
        """Test query_value returns None when no results."""
        # Skip if extension doesn't exist
        if not extension_path.exists():
            pytest.skip("ICU extension not available")

        with RMDatabase(db_path, extension_path=extension_path) as db:
            result = db.query_value("SELECT PersonID FROM PersonTable WHERE PersonID = ?", (999,))
            assert result is None

    def test_connection_property_no_connection(self):
        """Test connection property raises error when no connection."""
        db = RMDatabase.__new__(RMDatabase)
        db._conn = None

        with pytest.raises(DatabaseError, match="No active connection"):
            _ = db.connection

    def test_row_factory_dict_access(self, db_path, extension_path):
        """Test that results support dict-like access with default row factory."""
        # Skip if extension doesn't exist
        if not extension_path.exists():
            pytest.skip("ICU extension not available")

        with RMDatabase(db_path, extension_path=extension_path) as db:
            result = db.query_one("SELECT * FROM PersonTable WHERE PersonID = 1")
            # Dict-like access
            assert result["PersonID"] == 1
            assert result["Sex"] == 0
            # Index access
            assert result[0] == 1

    def test_close_multiple_times(self, db_path, extension_path):
        """Test that calling close multiple times is safe."""
        # Skip if extension doesn't exist
        if not extension_path.exists():
            pytest.skip("ICU extension not available")

        db = RMDatabase(db_path, extension_path=extension_path)
        db.connect()
        db.close()
        db.close()  # Should not raise error

    def test_commit_and_rollback(self, db_path, extension_path):
        """Test commit and rollback methods."""
        # Skip if extension doesn't exist
        if not extension_path.exists():
            pytest.skip("ICU extension not available")

        with RMDatabase(db_path, extension_path=extension_path) as db:
            # Insert and commit
            db.execute("INSERT INTO PersonTable VALUES (3, 0, 1)")
            db.commit()

            # Verify insert
            count = db.query_value("SELECT COUNT(*) FROM PersonTable")
            assert count == 3

            # Insert and rollback
            db.execute("INSERT INTO PersonTable VALUES (4, 1, 0)")
            db.rollback()

            # Verify rollback worked
            count = db.query_value("SELECT COUNT(*) FROM PersonTable")
            assert count == 3

    def test_parameterized_queries(self, db_path, extension_path):
        """Test queries with parameters."""
        # Skip if extension doesn't exist
        if not extension_path.exists():
            pytest.skip("ICU extension not available")

        with RMDatabase(db_path, extension_path=extension_path) as db:
            # Single parameter
            result = db.query_one("SELECT * FROM PersonTable WHERE PersonID = ?", (1,))
            assert result["PersonID"] == 1

            # Multiple parameters
            results = db.query("SELECT * FROM PersonTable WHERE Sex = ? AND Living = ?", (0, 1))
            assert len(results) == 1
            assert results[0]["PersonID"] == 1


class TestRMDatabaseIntegration:
    """Integration tests with actual RootsMagic database."""

    @pytest.fixture
    def real_db_path(self):
        """Path to real test database."""
        return Path("data/Iiams.rmtree")

    @pytest.fixture
    def extension_path(self):
        """Path to ICU extension."""
        return Path("./sqlite-extension/icu.dylib")

    def test_real_database_connection(self, real_db_path, extension_path):
        """Test connection to real RootsMagic database."""
        # Skip if database or extension doesn't exist
        if not real_db_path.exists():
            pytest.skip("Real database not available")
        if not extension_path.exists():
            pytest.skip("ICU extension not available")

        with RMDatabase(real_db_path, extension_path=extension_path) as db:
            # Verify connection works
            count = db.query_value("SELECT COUNT(*) FROM PersonTable")
            assert count > 0

    def test_rmnocase_collation_sorting(self, real_db_path, extension_path):
        """Test that RMNOCASE collation works for sorting."""
        # Skip if database or extension doesn't exist
        if not real_db_path.exists():
            pytest.skip("Real database not available")
        if not extension_path.exists():
            pytest.skip("ICU extension not available")

        with RMDatabase(real_db_path, extension_path=extension_path) as db:
            # Query with RMNOCASE collation
            results = db.query(
                """
                SELECT DISTINCT Surname
                FROM NameTable
                WHERE Surname IS NOT NULL AND Surname != ''
                ORDER BY Surname COLLATE RMNOCASE
                LIMIT 5
            """
            )

            assert len(results) > 0
            # Verify results are sorted (case-insensitive)
            surnames = [r["Surname"] for r in results]
            assert surnames == sorted(surnames, key=str.lower)

    def test_complex_query_with_joins(self, real_db_path, extension_path):
        """Test complex query with joins."""
        # Skip if database or extension doesn't exist
        if not real_db_path.exists():
            pytest.skip("Real database not available")
        if not extension_path.exists():
            pytest.skip("ICU extension not available")

        with RMDatabase(real_db_path, extension_path=extension_path) as db:
            result = db.query_one(
                """
                SELECT p.PersonID, n.Surname, n.Given
                FROM PersonTable p
                JOIN NameTable n ON p.PersonID = n.OwnerID
                WHERE n.IsPrimary = 1
                LIMIT 1
            """
            )

            assert result is not None
            assert "PersonID" in result.keys()
            assert "Surname" in result.keys()
            assert "Given" in result.keys()
