"""
Census sidecar database management.

Provides functions to create, initialize, and interact with the census
sidecar PostgreSQL database with JSONB storage.

Hybrid Schema Architecture:
- Common fields (name, age, sex, race, birthplace, occupation) as typed columns
- Year-specific fields in JSONB for flexibility
- GIN indexes for fast JSONB queries
"""

from __future__ import annotations

import json
from typing import Any, Optional

import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection as Connection

from rmagent.census.models.schema import SIDECAR_SCHEMA


class CensusSidecarDB:
    """Manages the census sidecar PostgreSQL database."""

    def __init__(self, connection_string: str):
        """
        Initialize sidecar database connection.

        Args:
            connection_string: PostgreSQL connection string
                Format: postgresql://user:password@host:port/database
                Example: postgresql://rmagent:password@localhost:5432/census_sidecar
        """
        self.connection_string = connection_string
        self.conn: Optional[Connection] = None

    def connect(self) -> Connection:
        """
        Connect to the sidecar database.

        Returns:
            psycopg2 connection object with JSON support

        Raises:
            psycopg2.Error: If connection fails
        """
        self.conn = psycopg2.connect(
            self.connection_string,
            cursor_factory=psycopg2.extras.RealDictCursor,  # Return dicts instead of tuples
        )
        # Register JSON adapter for JSONB fields
        psycopg2.extras.register_json(self.conn, globally=False, loads=json.loads)
        return self.conn

    def initialize_schema(self) -> None:
        """
        Create all tables and indexes if they don't exist.

        Executes the schema definition with proper PostgreSQL syntax including:
        - SERIAL primary keys
        - JSONB columns for flexible data
        - GIN indexes for fast JSONB queries
        - CHECK constraints for data validation
        """
        if not self.conn:
            self.connect()

        # Execute schema in a transaction
        with self.conn.cursor() as cur:
            cur.execute(SIDECAR_SCHEMA)
        self.conn.commit()

    def execute(
        self, query: str, params: Optional[tuple | dict] = None
    ) -> list[dict[str, Any]]:
        """
        Execute a query and return results.

        Args:
            query: SQL query to execute
            params: Query parameters (tuple for %s placeholders, dict for %(name)s)

        Returns:
            List of result rows as dictionaries

        Raises:
            psycopg2.Error: If query fails
        """
        if not self.conn:
            self.connect()

        with self.conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:  # SELECT query
                return cur.fetchall()
            else:  # INSERT/UPDATE/DELETE
                self.conn.commit()
                return []

    def execute_one(
        self, query: str, params: Optional[tuple | dict] = None
    ) -> Optional[dict[str, Any]]:
        """
        Execute a query and return a single result.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            Single result row as dictionary, or None if no results
        """
        if not self.conn:
            self.connect()

        with self.conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                return cur.fetchone()
            else:
                self.conn.commit()
                return None

    def get_stats(self) -> dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dictionary with counts for pages, households, entries by year and status
        """
        if not self.conn:
            self.connect()

        with self.conn.cursor() as cur:
            # Total counts
            cur.execute("SELECT COUNT(*) as count FROM census_page")
            total_pages = cur.fetchone()["count"]

            cur.execute("SELECT COUNT(*) as count FROM census_household")
            total_households = cur.fetchone()["count"]

            cur.execute("SELECT COUNT(*) as count FROM census_entry")
            total_entries = cur.fetchone()["count"]

            # By census year
            cur.execute(
                """
                SELECT census_year, COUNT(*) as count
                FROM census_page
                GROUP BY census_year
                ORDER BY census_year
                """
            )
            by_year = {row["census_year"]: row["count"] for row in cur.fetchall()}

            # By review status
            cur.execute(
                """
                SELECT review_status, COUNT(*) as count
                FROM census_entry
                GROUP BY review_status
                """
            )
            by_status = {row["review_status"]: row["count"] for row in cur.fetchall()}

        return {
            "total_pages": total_pages,
            "total_households": total_households,
            "total_entries": total_entries,
            "by_year": by_year,
            "by_status": by_status,
        }

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


def create_sidecar_database(connection_string: str) -> CensusSidecarDB:
    """
    Create and initialize a new census sidecar database.

    Args:
        connection_string: PostgreSQL connection string
            Format: postgresql://user:password@host:port/database

    Returns:
        CensusSidecarDB instance with initialized schema

    Example:
        >>> sidecar = create_sidecar_database(
        ...     "postgresql://rmagent:password@localhost:5432/census_sidecar"
        ... )
        >>> sidecar.get_stats()
        {'total_pages': 0, 'total_entries': 0, ...}
    """
    sidecar = CensusSidecarDB(connection_string)
    sidecar.connect()
    sidecar.initialize_schema()
    return sidecar
