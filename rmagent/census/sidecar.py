"""
Census sidecar database management.

Provides functions to create, initialize, and interact with the census
sidecar SQLite database.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from rmagent.census.models.schema import SIDECAR_SCHEMA


class CensusSidecarDB:
    """Manages the census sidecar SQLite database."""

    def __init__(self, db_path: str | Path):
        """
        Initialize sidecar database connection.

        Args:
            db_path: Path to sidecar SQLite database file
        """
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """
        Connect to the sidecar database.

        Creates the database file if it doesn't exist.

        Returns:
            SQLite connection object
        """
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        return self.conn

    def initialize_schema(self) -> None:
        """Create all tables and indexes if they don't exist."""
        if not self.conn:
            self.connect()

        # Execute schema in a transaction
        with self.conn:
            self.conn.executescript(SIDECAR_SCHEMA)

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def create_sidecar_database(db_path: str | Path) -> CensusSidecarDB:
    """
    Create and initialize a new census sidecar database.

    Args:
        db_path: Path where database should be created

    Returns:
        CensusSidecarDB instance with initialized schema
    """
    sidecar = CensusSidecarDB(db_path)
    sidecar.connect()
    sidecar.initialize_schema()
    return sidecar
