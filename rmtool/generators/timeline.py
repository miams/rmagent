"""
Timeline generator for RMAgent.

Generates interactive timelines from RootsMagic data in TimelineJS3 format.
Supports both JSON output (for embedding) and standalone HTML viewer.
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

from rmtool.rmlib.database import RMDatabase
from rmtool.rmlib.models import OwnerType
from rmtool.rmlib.parsers.date_parser import parse_rm_date, is_unknown_date, UNKNOWN_SORT_DATE
from rmtool.rmlib.parsers.place_parser import parse_place_name
from rmtool.rmlib.parsers.name_parser import format_full_name
from rmtool.rmlib.queries import QueryService


class TimelineFormat(str, Enum):
    """Timeline output formats."""

    JSON = "json"
    HTML = "html"


class LifePhase(str, Enum):
    """Life phase groupings for events."""

    EARLY_LIFE = "Early Life"
    EDUCATION_CAREER = "Education & Career"
    FAMILY_LIFE = "Family Life"
    MILITARY_SERVICE = "Military Service"
    MIGRATION = "Migration & Residence"
    LATER_LIFE = "Later Life"
    FINAL_YEARS = "Final Years"
    LIFE_EVENTS = "Life Events"


# Event type to life phase mapping (FactTypeID)
PHASE_MAPPING = {
    1: LifePhase.EARLY_LIFE,      # Birth
    3: LifePhase.EARLY_LIFE,      # Baptism
    4: LifePhase.EARLY_LIFE,      # Christening
    6: LifePhase.EARLY_LIFE,      # Blessing
    7: LifePhase.EARLY_LIFE,      # Bar Mitzvah

    17: LifePhase.EDUCATION_CAREER,  # Education
    18: LifePhase.EDUCATION_CAREER,  # Graduation
    12: LifePhase.EDUCATION_CAREER,  # Occupation
    27: LifePhase.EDUCATION_CAREER,  # Retirement

    9: LifePhase.FAMILY_LIFE,      # Marriage
    11: LifePhase.FAMILY_LIFE,     # Divorce

    10: LifePhase.MILITARY_SERVICE,  # Military Service

    13: LifePhase.MIGRATION,       # Residence
    14: LifePhase.MIGRATION,       # Immigration
    15: LifePhase.MIGRATION,       # Emigration

    2: LifePhase.FINAL_YEARS,      # Death
    5: LifePhase.FINAL_YEARS,      # Burial
    8: LifePhase.FINAL_YEARS,      # Probate
}

# Phase colors for visual distinction
PHASE_COLORS = {
    LifePhase.EARLY_LIFE: "#e3f2fd",
    LifePhase.EDUCATION_CAREER: "#e8f5e9",
    LifePhase.FAMILY_LIFE: "#fff9c4",
    LifePhase.MILITARY_SERVICE: "#ffebee",
    LifePhase.MIGRATION: "#f3e5f5",
    LifePhase.LATER_LIFE: "#e0f2f1",
    LifePhase.FINAL_YEARS: "#f5f5f5",
    LifePhase.LIFE_EVENTS: "#fafafa",
}

# Event type priority for same-date sorting
EVENT_PRIORITY = {
    1: 1,    # Birth (highest priority)
    2: 2,    # Death
    9: 3,    # Marriage
}


def _get_row_value(row, key: str, default=None):
    """Get value from sqlite3.Row object with default."""
    try:
        return row[key] if key in row.keys() else default
    except (KeyError, TypeError):
        return default


class TimelineGenerator:
    """
    Generate interactive timelines from RootsMagic data.

    Creates TimelineJS3-compatible timelines showing a person's life events
    in chronological order with dates, places, media, and citations.

    Args:
        db: RMDatabase instance or path to database
        extension_path: Path to ICU extension (default: ./sqlite-extension/icu.dylib)
        include_private: Include events marked as private (default: False)

    Example:
        ```python
        from rmtool.generators.timeline import TimelineGenerator, TimelineFormat

        generator = TimelineGenerator(db="data/Iiams.rmtree")

        # Generate JSON
        json_output = generator.generate(person_id=1, format=TimelineFormat.JSON)

        # Generate standalone HTML viewer
        html_output = generator.generate(person_id=1, format=TimelineFormat.HTML)
        ```
    """

    def __init__(
        self,
        db: Optional[RMDatabase | Path | str] = None,
        extension_path: Path | str = Path("./sqlite-extension/icu.dylib"),
        include_private: bool = False,
    ):
        # Handle db parameter
        if isinstance(db, (Path, str)):
            self.db_path = Path(db)
            self._db = None
            self._owns_db = True
        elif isinstance(db, RMDatabase):
            self.db_path = None
            self._db = db
            self._owns_db = False
        else:
            self.db_path = None
            self._db = None
            self._owns_db = False

        self.extension_path = Path(extension_path)
        self.include_private = include_private

    def generate(
        self,
        person_id: int,
        format: TimelineFormat = TimelineFormat.JSON,
        output_path: Optional[Path | str] = None,
        include_family: bool = False,
        group_by_phase: bool = True,
    ) -> str:
        """
        Generate a timeline for the specified person.

        Args:
            person_id: PersonID from PersonTable
            format: Output format (json or html)
            output_path: Optional path to write output file
            include_family: Include spouse and children events (not yet implemented)
            group_by_phase: Group events by life phase

        Returns:
            Timeline as JSON string or HTML string

        Raises:
            ValueError: If person not found or no database provided
        """
        # Extract timeline data
        timeline_data = self._extract_timeline_data(person_id, include_family, group_by_phase)

        # Format based on requested type
        if format == TimelineFormat.JSON:
            output = self._format_json(timeline_data)
        elif format == TimelineFormat.HTML:
            output = self._format_html(timeline_data)
        else:
            raise ValueError(f"Unsupported format: {format}")

        # Write to file if requested
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(output, encoding="utf-8")

        return output

    def _extract_timeline_data(
        self,
        person_id: int,
        include_family: bool,
        group_by_phase: bool,
    ) -> Dict:
        """Extract timeline data from database."""

        def _extract(db: RMDatabase) -> Dict:
            query = QueryService(db)

            # Get person
            person = query.get_person_with_primary_name(person_id)
            if not person:
                raise ValueError(f"Person {person_id} not found")

            # Get person name
            full_name = format_full_name(
                given=_get_row_value(person, "Given"),
                surname=_get_row_value(person, "Surname"),
                prefix=_get_row_value(person, "Prefix"),
                suffix=_get_row_value(person, "Suffix"),
            )

            birth_year = _get_row_value(person, "BirthYear")
            death_year = _get_row_value(person, "DeathYear")
            lifespan = ""
            if birth_year or death_year:
                lifespan = f"({birth_year or '?'} - {death_year or '?'})"

            # Get all events
            all_events = query.get_person_events(person_id)

            # Filter and convert events
            timeline_events = []
            for event in all_events:
                # Skip private events unless requested
                if not self.include_private and _get_row_value(event, "IsPrivate", 0):
                    continue

                # Skip technical events
                event_type_id = _get_row_value(event, "EventType", 0)
                if event_type_id in (30, 34, 35):  # SSN, AFN, Ref#
                    continue

                # Skip events without dates AND without meaningful details
                date_str = _get_row_value(event, "Date", "")
                details = _get_row_value(event, "Details", "")
                if (not date_str or is_unknown_date(date_str)) and not details:
                    continue

                # Build timeline event
                timeline_event = self._build_timeline_event(db, event, person_id, birth_year, group_by_phase)
                if timeline_event:
                    timeline_events.append(timeline_event)

            # Sort events chronologically
            timeline_events = self._sort_events(timeline_events)

            # Get primary media for title slide
            title_media = self._get_title_media(db, person_id)

            return {
                "person_name": full_name,
                "lifespan": lifespan,
                "person_id": person_id,
                "events": timeline_events,
                "title_media": title_media,
            }

        if self._db:
            return _extract(self._db)
        elif self.db_path:
            with RMDatabase(self.db_path, extension_path=self.extension_path) as db:
                return _extract(db)
        else:
            raise ValueError("No database provided")

    def _build_timeline_event(
        self,
        db: RMDatabase,
        event,
        person_id: int,
        birth_year: Optional[int],
        group_by_phase: bool,
    ) -> Optional[Dict]:
        """Build a TimelineJS3 event object from an RM event."""
        event_id = _get_row_value(event, "EventID", 0)
        event_type_id = _get_row_value(event, "EventType", 0)
        event_type_name = self._get_event_type_name(db, event_type_id)
        date_str = _get_row_value(event, "Date", "")
        sort_date = _get_row_value(event, "SortDate", UNKNOWN_SORT_DATE)
        details = _get_row_value(event, "Details", "")
        place_str = _get_row_value(event, "Place", "")

        # Parse date
        start_date, end_date, display_date = self._parse_date_to_timelinejs(date_str)

        # Format place
        place_formatted = self._format_place_for_timeline(place_str)

        # Build narrative text
        narrative = self._build_event_narrative(
            event_type_name,
            display_date,
            place_formatted,
            details
        )

        # Get media
        media = self._get_event_media(db, event_id)

        # Get citations for credit
        citations = self._get_event_citations(db, event_id)
        credit = self._format_citations_credit(citations)

        # Determine life phase
        phase = None
        if group_by_phase:
            phase = self._determine_life_phase(event_type_id, birth_year, start_date)

        # Build timeline event
        timeline_event = {
            "unique_id": f"event_{event_id}",
            "text": {
                "headline": event_type_name,
                "text": narrative,
            },
            "_sort_date": sort_date,  # Internal field for sorting
            "_event_type_id": event_type_id,  # Internal field for priority
        }

        # Add dates if available
        if start_date:
            timeline_event["start_date"] = start_date
        if end_date:
            timeline_event["end_date"] = end_date

        # Add media if available
        if media:
            timeline_event["media"] = media

        # Add phase grouping
        if phase:
            timeline_event["group"] = phase.value
            timeline_event["background"] = {"color": PHASE_COLORS.get(phase, "#fafafa")}

        return timeline_event

    def _parse_date_to_timelinejs(self, rm_date: str) -> Tuple[Optional[Dict], Optional[Dict], Optional[str]]:
        """Parse RM11 date to TimelineJS3 format."""
        if not rm_date or is_unknown_date(rm_date):
            return None, None, None

        try:
            parsed = parse_rm_date(rm_date)

            # Build start_date
            start_date = {}
            if parsed.year is not None:
                start_date["year"] = parsed.year
            if parsed.month is not None:
                start_date["month"] = parsed.month
            if parsed.day is not None:
                start_date["day"] = parsed.day

            # Build end_date if range
            end_date = None
            if parsed.is_range and parsed.year2 is not None:
                end_date = {"year": parsed.year2}
                if parsed.month2 is not None:
                    end_date["month"] = parsed.month2
                if parsed.day2 is not None:
                    end_date["day"] = parsed.day2

            # Get display date
            display_date = parsed.format_display()

            return start_date or None, end_date, display_date

        except Exception:
            # If parsing fails, return None
            return None, None, rm_date

    def _format_place_for_timeline(self, place_str: str) -> Optional[str]:
        """Format place for timeline display (short form)."""
        if not place_str:
            return None

        try:
            parsed = parse_place_name(place_str)
            levels = parsed.levels

            # Remove country if United States
            if len(levels) >= 4 and levels[3] == "United States":
                levels = levels[:3]

            # Return City, State or City, Country
            if len(levels) >= 3:
                return f"{levels[0]}, {levels[2]}"  # City, State
            elif len(levels) == 2:
                return f"{levels[0]}, {levels[1]}"  # City, Country
            else:
                return levels[0] if levels else None

        except Exception:
            # If parsing fails, return as-is
            return place_str

    def _build_event_narrative(
        self,
        event_type: str,
        date: Optional[str],
        place: Optional[str],
        details: Optional[str],
    ) -> str:
        """Build narrative text for event."""
        parts = []

        # Start with date if available
        if date:
            parts.append(f"<p><strong>{date}</strong>")
        else:
            parts.append("<p><strong>Date Unknown</strong>")

        # Add place if available
        if place:
            parts.append(f" in {place}")

        parts.append("</p>")

        # Add details if available
        if details:
            parts.append(f"<p>{details}</p>")

        return "".join(parts)

    def _get_event_type_name(self, db: RMDatabase, event_type_id: int) -> str:
        """Get event type name from FactTypeTable."""
        cursor = db.execute(
            "SELECT Name FROM FactTypeTable WHERE FactTypeID = ?",
            (event_type_id,)
        )
        row = cursor.fetchone()
        return _get_row_value(row, "Name", f"Event {event_type_id}") if row else f"Event {event_type_id}"

    def _get_event_media(self, db: RMDatabase, event_id: int) -> Optional[Dict]:
        """Get primary media for an event."""
        cursor = db.execute(
            """
            SELECT m.MediaFile, m.Caption, m.Description
            FROM MediaLinkTable ml
            JOIN MultimediaTable m ON ml.MediaID = m.MediaID
            WHERE ml.OwnerType = ? AND ml.OwnerID = ?
            ORDER BY ml.SortOrder
            LIMIT 1
            """,
            (OwnerType.EVENT.value, event_id),
        )
        row = cursor.fetchone()
        if not row:
            return None

        media_file = _get_row_value(row, "MediaFile")
        if not media_file:
            return None

        return {
            "url": media_file,
            "caption": _get_row_value(row, "Caption", ""),
        }

    def _get_event_citations(self, db: RMDatabase, event_id: int) -> List[Dict]:
        """Get citations for an event."""
        cursor = db.execute(
            """
            SELECT c.CitationName, s.Name AS SourceName
            FROM CitationLinkTable cl
            JOIN CitationTable c ON cl.CitationID = c.CitationID
            JOIN SourceTable s ON c.SourceID = s.SourceID
            WHERE cl.OwnerType = ? AND cl.OwnerID = ?
            ORDER BY cl.SortOrder
            """,
            (OwnerType.EVENT.value, event_id),
        )
        return cursor.fetchall()

    def _format_citations_credit(self, citations: List) -> Optional[str]:
        """Format citations as credit string."""
        if not citations:
            return None

        sources = []
        for citation in citations[:3]:  # Limit to 3 sources
            source_name = _get_row_value(citation, "SourceName")
            if source_name:
                sources.append(source_name)

        if sources:
            return "Sources: " + "; ".join(sources)
        return None

    def _get_title_media(self, db: RMDatabase, person_id: int) -> Optional[Dict]:
        """Get primary media for title slide."""
        cursor = db.execute(
            """
            SELECT m.MediaFile, m.Caption, m.Description
            FROM MediaLinkTable ml
            JOIN MultimediaTable m ON ml.MediaID = m.MediaID
            WHERE ml.OwnerType = ? AND ml.OwnerID = ?
            ORDER BY ml.IsPrimary DESC, ml.SortOrder
            LIMIT 1
            """,
            (OwnerType.PERSON.value, person_id),
        )
        row = cursor.fetchone()
        if not row:
            return None

        media_file = _get_row_value(row, "MediaFile")
        if not media_file:
            return None

        return {
            "url": media_file,
            "caption": _get_row_value(row, "Caption", ""),
            "credit": _get_row_value(row, "Description", ""),
        }

    def _determine_life_phase(
        self,
        event_type_id: int,
        birth_year: Optional[int],
        start_date: Optional[Dict],
    ) -> LifePhase:
        """Determine life phase for an event."""
        # Check predefined mapping first
        if event_type_id in PHASE_MAPPING:
            return PHASE_MAPPING[event_type_id]

        # Calculate age if possible
        if birth_year and start_date and "year" in start_date:
            age = start_date["year"] - birth_year

            if age < 18:
                return LifePhase.EARLY_LIFE
            elif age >= 60:
                return LifePhase.LATER_LIFE
            else:
                return LifePhase.LIFE_EVENTS

        return LifePhase.LIFE_EVENTS

    def _sort_events(self, events: List[Dict]) -> List[Dict]:
        """Sort events chronologically with priority for same-date events."""
        def sort_key(event):
            sort_date = event.get("_sort_date", UNKNOWN_SORT_DATE)
            event_type_id = event.get("_event_type_id", 999)
            priority = EVENT_PRIORITY.get(event_type_id, 999)
            event_id = int(event.get("unique_id", "event_0").split("_")[1])
            return (sort_date, priority, event_id)

        sorted_events = sorted(events, key=sort_key)

        # Remove internal sorting fields
        for event in sorted_events:
            event.pop("_sort_date", None)
            event.pop("_event_type_id", None)

        return sorted_events

    # ---- JSON Format ----

    def _format_json(self, timeline_data: Dict) -> str:
        """Format timeline as TimelineJS3 JSON."""
        timelinejs = {
            "title": {
                "text": {
                    "headline": timeline_data["person_name"],
                    "text": timeline_data["lifespan"],
                }
            },
            "events": timeline_data["events"],
            "scale": "human",
        }

        # Add title media if available
        if timeline_data.get("title_media"):
            timelinejs["title"]["media"] = timeline_data["title_media"]

        return json.dumps(timelinejs, indent=2, ensure_ascii=False)

    # ---- HTML Format ----

    def _format_html(self, timeline_data: Dict) -> str:
        """Format timeline as standalone HTML viewer."""
        # Get JSON data
        json_data = self._format_json(timeline_data)

        # Build HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Timeline: {timeline_data['person_name']}</title>

    <!-- TimelineJS3 CSS -->
    <link title="timeline-styles" rel="stylesheet" href="https://cdn.knightlab.com/libs/timeline3/latest/css/timeline.css">

    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
        }}
        #timeline-embed {{
            width: 100%;
            height: 100vh;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 15px 20px;
            font-size: 14px;
        }}
        .header h1 {{
            margin: 0 0 5px 0;
            font-size: 24px;
        }}
        .header p {{
            margin: 0;
            opacity: 0.9;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{timeline_data['person_name']}</h1>
        <p>{timeline_data['lifespan']}</p>
    </div>

    <div id="timeline-embed"></div>

    <!-- TimelineJS3 JavaScript -->
    <script src="https://cdn.knightlab.com/libs/timeline3/latest/js/timeline.js"></script>

    <script>
        // Timeline data embedded directly
        var timelineData = {json_data};

        // Create timeline
        window.timeline = new TL.Timeline('timeline-embed', timelineData, {{
            start_at_end: false,
            initial_zoom: 2,
            hash_bookmark: true,
            timenav_height: 250,
        }});
    </script>
</body>
</html>"""

        return html
