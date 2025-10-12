"""
RootsMagic Database Connection Module

Provides a context-managed database connection with RMNOCASE collation support
for querying RootsMagic 11 .rmtree databases.

Example:
    with RMDatabase('data/Iiams.rmtree') as db:
        person = db.query_one("SELECT * FROM PersonTable WHERE PersonID = ?", (1,))
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Base exception for database-related errors."""

    pass


class DatabaseNotFoundError(DatabaseError):
    """Raised when database file does not exist."""

    pass


class ExtensionLoadError(DatabaseError):
    """Raised when SQLite extension cannot be loaded."""

    pass


class RMDatabase:
    """
    Context manager for RootsMagic database connections with RMNOCASE support.

    This class handles:
    - Loading the ICU extension for RMNOCASE collation
    - Connection lifecycle management
    - Error handling for missing database/extension
    - Query helper methods

    Args:
        db_path: Path to .rmtree database file
        extension_path: Path to ICU extension library (default: ./sqlite-extension/icu.dylib)
        row_factory: Optional row factory (default: sqlite3.Row for dict-like access)

    Raises:
        DatabaseNotFoundError: If database file does not exist
        ExtensionLoadError: If ICU extension cannot be loaded

    Example:
        with RMDatabase('data/Iiams.rmtree') as db:
            person = db.query_one("SELECT * FROM PersonTable WHERE PersonID = ?", (1,))
            print(person['PersonID'], person['Sex'])
    """

    def __init__(
        self,
        db_path: str | Path,
        extension_path: str | Path = "./sqlite-extension/icu.dylib",
        row_factory: Any | None = sqlite3.Row,
    ):
        self.db_path = Path(db_path)
        self.extension_path = Path(extension_path)
        self.row_factory = row_factory
        self._conn: sqlite3.Connection | None = None

        # Validate database exists
        if not self.db_path.exists():
            raise DatabaseNotFoundError(f"Database file not found: {self.db_path}")

        logger.debug(f"Initialized RMDatabase for {self.db_path}")

    def __enter__(self) -> "RMDatabase":
        """Enter context manager - establish database connection."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager - close database connection."""
        self.close()

    def connect(self) -> None:
        """
        Establish connection to database and load RMNOCASE collation.

        Raises:
            ExtensionLoadError: If ICU extension cannot be loaded
        """
        if self._conn is not None:
            logger.warning("Connection already exists - closing existing connection")
            self.close()

        logger.info(f"Connecting to database: {self.db_path}")

        # Connect to database
        self._conn = sqlite3.connect(str(self.db_path))

        # Set row factory for dict-like access
        if self.row_factory:
            self._conn.row_factory = self.row_factory

        # Load RMNOCASE collation
        try:
            self._load_rmnocase_collation()
        except Exception as e:
            self._conn.close()
            self._conn = None
            raise ExtensionLoadError(f"Failed to load RMNOCASE collation: {e}") from e

        logger.info("Database connection established with RMNOCASE support")

    def _load_rmnocase_collation(self) -> None:
        """
        Load ICU extension and register RMNOCASE collation.

        Raises:
            sqlite3.OperationalError: If extension cannot be loaded
        """
        if self._conn is None:
            raise DatabaseError("No active connection")

        # Check if extension file exists
        if not self.extension_path.exists():
            raise ExtensionLoadError(f"ICU extension not found: {self.extension_path}")

        # Enable extension loading
        self._conn.enable_load_extension(True)

        try:
            # Load ICU extension
            logger.debug(f"Loading ICU extension from {self.extension_path}")
            self._conn.load_extension(str(self.extension_path))

            # Register RMNOCASE collation using ICU
            # Parameters:
            #   - en_US: English locale
            #   - colStrength=primary: Case-insensitive comparison
            #   - caseLevel=off: Ignore case differences
            #   - normalization=on: Normalize Unicode characters
            self._conn.execute(
                "SELECT icu_load_collation("
                "'en_US@colStrength=primary;caseLevel=off;normalization=on',"
                "'RMNOCASE')"
            )
            logger.debug("RMNOCASE collation registered successfully")
        finally:
            # Disable extension loading (security best practice)
            self._conn.enable_load_extension(False)

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            logger.debug("Closing database connection")
            self._conn.close()
            self._conn = None

    @property
    def connection(self) -> sqlite3.Connection:
        """
        Get the underlying sqlite3 Connection object.

        Returns:
            sqlite3.Connection object

        Raises:
            DatabaseError: If no active connection
        """
        if self._conn is None:
            raise DatabaseError(
                "No active connection - use 'with RMDatabase(...)' or call connect()"
            )
        return self._conn

    def execute(self, query: str, params: tuple | None = None) -> sqlite3.Cursor:
        """
        Execute a SQL query.

        Args:
            query: SQL query string
            params: Optional query parameters

        Returns:
            sqlite3.Cursor object

        Raises:
            DatabaseError: If no active connection
        """
        cursor = self.connection.cursor()
        if params:
            logger.debug(f"Executing query: {query[:100]}... with params: {params}")
            cursor.execute(query, params)
        else:
            logger.debug(f"Executing query: {query[:100]}...")
            cursor.execute(query)
        return cursor

    def query(self, query: str, params: tuple | None = None) -> list[sqlite3.Row]:
        """
        Execute query and return all results.

        Args:
            query: SQL query string
            params: Optional query parameters

        Returns:
            List of rows (sqlite3.Row objects if row_factory set)
        """
        cursor = self.execute(query, params)
        results = cursor.fetchall()
        logger.debug(f"Query returned {len(results)} rows")
        return results

    def query_one(self, query: str, params: tuple | None = None) -> sqlite3.Row | None:
        """
        Execute query and return single result.

        Args:
            query: SQL query string
            params: Optional query parameters

        Returns:
            Single row or None if no results
        """
        cursor = self.execute(query, params)
        result = cursor.fetchone()
        logger.debug(f"Query returned {'1 row' if result else 'no results'}")
        return result

    def query_value(self, query: str, params: tuple | None = None) -> Any:
        """
        Execute query and return single value from first column of first row.

        Args:
            query: SQL query string
            params: Optional query parameters

        Returns:
            Single value or None if no results
        """
        cursor = self.execute(query, params)
        result = cursor.fetchone()
        if result:
            return result[0]
        return None

    def commit(self) -> None:
        """Commit current transaction."""
        self.connection.commit()
        logger.debug("Transaction committed")

    def rollback(self) -> None:
        """Rollback current transaction."""
        self.connection.rollback()
        logger.debug("Transaction rolled back")
