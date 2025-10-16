"""
Census media catalog management.

Queries RootsMagic database for census-related media files and populates
the census sidecar database with page metadata.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from rmagent.census.models.schema import CensusPage
from rmagent.census.sidecar import CensusSidecarDB


class CensusMediaCatalog:
    """Manages census media cataloging from RootsMagic database."""

    def __init__(self, rm_db_path: str | Path, sidecar_db: CensusSidecarDB):
        """
        Initialize catalog manager.

        Args:
            rm_db_path: Path to RootsMagic database
            sidecar_db: Census sidecar database instance
        """
        self.rm_db_path = Path(rm_db_path)
        self.sidecar_db = sidecar_db

    def catalog_census_media(self) -> dict:
        """
        Scan RootsMagic database for census media and populate sidecar.

        Returns:
            Dictionary with cataloging statistics
        """
        stats = {
            "total_media": 0,
            "census_events": 0,
            "media_with_year": 0,
            "media_without_year": 0,
            "errors": [],
        }

        # Connect to RootsMagic database
        rm_conn = self._connect_rm_database()

        try:
            # Query 1: Get census events with media
            census_events = self._get_census_events_with_media(rm_conn)
            stats["census_events"] = len(census_events)

            # Query 2: Get all media that might be census-related
            all_census_media = self._get_all_census_media(rm_conn)
            stats["total_media"] = len(all_census_media)

            # Process and insert into sidecar
            for media in all_census_media:
                try:
                    census_year = self._extract_census_year(media, census_events)

                    if census_year:
                        stats["media_with_year"] += 1
                        self._insert_census_page(media, census_year)
                    else:
                        stats["media_without_year"] += 1
                        print(
                            f"Warning: Could not determine census year for MediaID {media['MediaID']}: "
                            f"{media['MediaFile']}"
                        )

                except Exception as e:
                    error_msg = f"Error processing MediaID {media['MediaID']}: {str(e)}"
                    stats["errors"].append(error_msg)
                    print(f"ERROR: {error_msg}")

        finally:
            rm_conn.close()

        return stats

    def _connect_rm_database(self) -> sqlite3.Connection:
        """Connect to RootsMagic database with ICU extension."""
        conn = sqlite3.connect(str(self.rm_db_path))
        conn.row_factory = sqlite3.Row

        # Load ICU extension for RMNOCASE collation
        try:
            conn.enable_load_extension(True)
            conn.load_extension("./sqlite-extension/icu.dylib")
            conn.execute(
                "SELECT icu_load_collation('en_US@colStrength=primary;"
                "caseLevel=off;normalization=on','RMNOCASE')"
            )
            conn.enable_load_extension(False)
        except Exception as e:
            print(f"Warning: Could not load ICU extension: {e}")
            print("RMNOCASE collation may not work correctly")

        return conn

    def _get_census_events_with_media(self, conn: sqlite3.Connection) -> list[dict]:
        """
        Get all census person-media-event links via all pathways.

        Includes 4 pathways to handle both pre-1850 and post-1850 data:
        1. Media → Event (post-1850 primary person)
        2. Media → Event + WitnessTable (post-1850 household members)
        3. Media → Citation → Event (pre-1850)
        4. Media → Source → Citation → Event (pre-1850)

        Returns:
            List of dicts with person-media-event information
        """
        query = """
        -- Pathway 1: Media → Event (Post-1850 typical) - Primary person
        SELECT
            m.MediaID,
            m.MediaPath,
            m.MediaFile,
            e.EventID,
            e.OwnerID as PersonID,
            e.Date as EventDate,
            c.CitationID,
            c.CitationName,
            n.Surname,
            n.Given,
            p.Sex,
            'Head' as Role,
            NULL as RoleID,
            'Media→Event' as LinkPath
        FROM MultimediaTable m
        JOIN MediaLinkTable ml ON ml.MediaID = m.MediaID AND ml.OwnerType = 2
        JOIN EventTable e ON e.EventID = ml.OwnerID
        JOIN FactTypeTable ft ON ft.FactTypeID = e.EventType AND ft.GedcomTag = 'CENS'
        LEFT JOIN CitationLinkTable cl ON cl.OwnerID = e.EventID AND cl.OwnerType = 2
        LEFT JOIN CitationTable c ON c.CitationID = cl.CitationID
        LEFT JOIN PersonTable p ON p.PersonID = e.OwnerID
        LEFT JOIN NameTable n ON n.OwnerID = e.OwnerID AND n.IsPrimary = 1
        WHERE m.MediaType = 1

        UNION ALL

        -- Pathway 2: Media → Event (Post-1850 typical) - Witnesses/household members
        SELECT
            m.MediaID,
            m.MediaPath,
            m.MediaFile,
            e.EventID,
            w.PersonID,
            e.Date as EventDate,
            c.CitationID,
            c.CitationName,
            n.Surname,
            n.Given,
            p.Sex,
            r.RoleName as Role,
            w.Role as RoleID,
            'Media→Event+Witness' as LinkPath
        FROM MultimediaTable m
        JOIN MediaLinkTable ml ON ml.MediaID = m.MediaID AND ml.OwnerType = 2
        JOIN EventTable e ON e.EventID = ml.OwnerID
        JOIN FactTypeTable ft ON ft.FactTypeID = e.EventType AND ft.GedcomTag = 'CENS'
        JOIN WitnessTable w ON w.EventID = e.EventID
        LEFT JOIN RoleTable r ON r.RoleID = w.Role
        LEFT JOIN CitationLinkTable cl ON cl.OwnerID = e.EventID AND cl.OwnerType = 2
        LEFT JOIN CitationTable c ON c.CitationID = cl.CitationID
        LEFT JOIN PersonTable p ON p.PersonID = w.PersonID
        LEFT JOIN NameTable n ON n.OwnerID = w.PersonID AND n.IsPrimary = 1
        WHERE m.MediaType = 1

        UNION ALL

        -- Pathway 3: Media → Citation → Event (Pre-1850 typical)
        SELECT
            m.MediaID,
            m.MediaPath,
            m.MediaFile,
            e.EventID,
            e.OwnerID as PersonID,
            e.Date as EventDate,
            c.CitationID,
            c.CitationName,
            n.Surname,
            n.Given,
            p.Sex,
            'Head' as Role,
            NULL as RoleID,
            'Media→Citation→Event' as LinkPath
        FROM MultimediaTable m
        JOIN MediaLinkTable ml ON ml.MediaID = m.MediaID AND ml.OwnerType = 4
        JOIN CitationTable c ON c.CitationID = ml.OwnerID
        JOIN CitationLinkTable cl ON cl.CitationID = c.CitationID AND cl.OwnerType = 2
        JOIN EventTable e ON e.EventID = cl.OwnerID
        JOIN FactTypeTable ft ON ft.FactTypeID = e.EventType AND ft.GedcomTag = 'CENS'
        LEFT JOIN PersonTable p ON p.PersonID = e.OwnerID
        LEFT JOIN NameTable n ON n.OwnerID = e.OwnerID AND n.IsPrimary = 1
        WHERE m.MediaType = 1

        UNION ALL

        -- Pathway 4: Media → Source → Citation → Event (Pre-1850 typical)
        SELECT
            m.MediaID,
            m.MediaPath,
            m.MediaFile,
            e.EventID,
            e.OwnerID as PersonID,
            e.Date as EventDate,
            c.CitationID,
            c.CitationName,
            n.Surname,
            n.Given,
            p.Sex,
            'Head' as Role,
            NULL as RoleID,
            'Media→Source→Citation→Event' as LinkPath
        FROM MultimediaTable m
        JOIN MediaLinkTable ml ON ml.MediaID = m.MediaID AND ml.OwnerType = 3
        JOIN SourceTable s ON s.SourceID = ml.OwnerID
        JOIN CitationTable c ON c.SourceID = s.SourceID
        JOIN CitationLinkTable cl ON cl.CitationID = c.CitationID AND cl.OwnerType = 2
        JOIN EventTable e ON e.EventID = cl.OwnerID
        JOIN FactTypeTable ft ON ft.FactTypeID = e.EventType AND ft.GedcomTag = 'CENS'
        LEFT JOIN PersonTable p ON p.PersonID = e.OwnerID
        LEFT JOIN NameTable n ON n.OwnerID = e.OwnerID AND n.IsPrimary = 1
        WHERE m.MediaType = 1

        ORDER BY MediaPath, EventID, PersonID
        """

        results = conn.execute(query).fetchall()
        return [dict(row) for row in results]

    def _get_all_census_media(self, conn: sqlite3.Connection) -> list[dict]:
        """
        Get all media files that appear to be census-related.

        Looks for:
        1. Media linked to census events
        2. Media with "census" in caption/description
        3. Media linked to persons (potential manual links)

        Returns:
            List of dicts with media information
        """
        query = """
        SELECT DISTINCT
            m.MediaID,
            m.MediaFile,
            m.MediaPath,
            m.Caption,
            m.Description,
            m.Date,
            ml.OwnerType,
            ml.OwnerID,
            ml.IsPrimary,
            CASE
                WHEN ml.OwnerType = 2 THEN (
                    SELECT ft.GedcomTag
                    FROM EventTable e
                    JOIN FactTypeTable ft ON e.EventType = ft.FactTypeID
                    WHERE e.EventID = ml.OwnerID
                )
                ELSE NULL
            END as EventType
        FROM MultimediaTable m
        JOIN MediaLinkTable ml ON m.MediaID = ml.MediaID
        WHERE m.MediaType = 1  -- Images only
          AND (
            -- Linked to census events
            (ml.OwnerType = 2 AND EXISTS (
                SELECT 1 FROM EventTable e
                JOIN FactTypeTable ft ON e.EventType = ft.FactTypeID
                WHERE e.EventID = ml.OwnerID AND ft.GedcomTag = 'CENS'
            ))
            -- OR has "census" in caption/description
            OR LOWER(m.Caption) LIKE '%census%'
            OR LOWER(m.Description) LIKE '%census%'
            OR LOWER(m.MediaFile) LIKE '%census%'
          )
        ORDER BY m.MediaID
        """

        results = conn.execute(query).fetchall()
        return [dict(row) for row in results]

    def _extract_census_year(
        self, media: dict, census_events: list[dict]
    ) -> Optional[int]:
        """
        Determine census year from media metadata.

        Tries multiple strategies (in priority order):
        1. MediaPath (most reliable - contains year in path structure)
        2. MediaFile (filename may contain year)
        3. Linked census event date
        4. Media caption/description

        Args:
            media: Media record dict
            census_events: List of census events with media

        Returns:
            Census year (e.g., 1900) or None if not determinable
        """
        import re

        # Strategy 1: Parse MediaPath for year (most reliable)
        # Example: "?\Records - Census\1790 Federal" → 1790
        media_path = media.get("MediaPath", "")
        if media_path:
            match = re.search(r'\b(1[78]\d{2}|19[0-5]\d)\b', media_path)
            if match:
                year = int(match.group(1))
                if self._is_valid_census_year(year):
                    return year

        # Strategy 2: Parse filename for year patterns
        filename = media.get("MediaFile", "")
        if filename:
            match = re.search(r'\b(1[78]\d{2}|19[0-5]\d)\b', filename)
            if match:
                year = int(match.group(1))
                if self._is_valid_census_year(year):
                    return year

        # Strategy 3: Check linked census event date
        linked_event = next(
            (e for e in census_events if e["MediaID"] == media["MediaID"]), None
        )
        if linked_event and linked_event.get("EventDate"):
            year = self._extract_year_from_rm_date(linked_event["EventDate"])
            if self._is_valid_census_year(year):
                return year

        # Strategy 4: Parse caption/description for year
        for text in [media.get("Caption"), media.get("Description")]:
            if text:
                match = re.search(r'\b(1[78]\d{2}|19[0-5]\d)\b', text)
                if match:
                    year = int(match.group(1))
                    if self._is_valid_census_year(year):
                        return year

        return None

    def _extract_year_from_rm_date(self, rm_date: str) -> Optional[int]:
        """
        Extract year from RootsMagic date string.

        RootsMagic dates are 24-character encoded strings.
        For simple dates, characters 10-13 contain the year.

        Args:
            rm_date: RootsMagic date string

        Returns:
            Year as integer or None
        """
        if not rm_date or len(rm_date) < 14:
            return None

        try:
            year_str = rm_date[10:14]
            year = int(year_str)
            return year if year > 0 else None
        except (ValueError, IndexError):
            return None

    def _extract_year_from_text(self, text: str) -> Optional[int]:
        """Extract 4-digit year from text."""
        import re

        # Look for 4-digit years (1790-1950)
        matches = re.findall(r"\b(1[78]\d{2}|19[0-5]\d)\b", text)
        return int(matches[0]) if matches else None

    def _extract_year_from_filename(self, filename: str) -> Optional[int]:
        """Extract census year from filename patterns."""
        import re

        # Common patterns: "1900_census", "census_1900", "1900-01-census"
        matches = re.findall(r"\b(1[78]\d{2}|19[0-5]\d)\b", filename)
        return int(matches[0]) if matches else None

    def _is_valid_census_year(self, year: Optional[int]) -> bool:
        """
        Check if year is a valid census year (federal or state).

        Args:
            year: Year to validate

        Returns:
            True if valid census year
            - Federal census: 1790-1950, every 10 years (excluding 1890)
            - State census: 1855, 1865, 1875, 1885, 1895, 1905, 1915, 1925, 1935, 1945
        """
        if not year:
            return False

        # Federal census years: 1790, 1800, ..., 1950 (excluding 1890)
        if 1790 <= year <= 1950 and year % 10 == 0 and year != 1890:
            return True

        # State census years (5-year intervals between federal census)
        # Common in: New York, Iowa, Kansas, Wisconsin, Florida, etc.
        state_census_years = {1855, 1865, 1875, 1885, 1895, 1905, 1915, 1925, 1935, 1945}
        return year in state_census_years

    def _insert_census_page(self, media: dict, census_year: int) -> None:
        """
        Insert census page record into sidecar database.

        Args:
            media: Media record dict
            census_year: Determined census year
        """
        if not self.sidecar_db.conn:
            raise RuntimeError("Sidecar database not connected")

        # Construct image path
        media_path = media.get("MediaPath", "")
        media_file = media.get("MediaFile", "")

        # Handle RootsMagic path prefix (?/)
        if media_path.startswith("?/") or media_path.startswith("?\\"):
            # Relative to database root
            image_path = str(Path("images") / media_path[2:] / media_file)
        elif media_path:
            image_path = str(Path(media_path) / media_file)
        else:
            image_path = media_file

        # Insert or update census page (PostgreSQL upsert syntax)
        query = """
        INSERT INTO census_page (
            media_id, person_id, census_year, image_path
        ) VALUES (%s, %s, %s, %s)
        ON CONFLICT (media_id) DO UPDATE SET
            person_id = EXCLUDED.person_id,
            census_year = EXCLUDED.census_year,
            image_path = EXCLUDED.image_path,
            updated_at = CURRENT_TIMESTAMP
        """

        person_id = media.get("OwnerID") if media.get("OwnerType") == 0 else None

        with self.sidecar_db.conn.cursor() as cur:
            cur.execute(
                query, (media["MediaID"], person_id, census_year, image_path)
            )
        self.sidecar_db.conn.commit()


def catalog_census_media(
    rm_db_path: str | Path, sidecar_connection_string: str
) -> dict:
    """
    Convenience function to catalog census media.

    Args:
        rm_db_path: Path to RootsMagic database
        sidecar_connection_string: PostgreSQL connection string
            Format: postgresql://user:password@host:port/database

    Returns:
        Cataloging statistics dict

    Example:
        >>> stats = catalog_census_media(
        ...     "data/Iiams.rmtree",
        ...     "postgresql://rmagent:password@localhost:5432/census_sidecar"
        ... )
        >>> print(stats["total_media"])
        1400
    """
    with CensusSidecarDB(sidecar_connection_string) as sidecar:
        sidecar.initialize_schema()
        catalog = CensusMediaCatalog(rm_db_path, sidecar)
        return catalog.catalog_census_media()
