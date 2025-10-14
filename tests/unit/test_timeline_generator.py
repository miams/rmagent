"""Unit tests for timeline generator."""

import json
from pathlib import Path

import pytest

from rmagent.generators.timeline import (
    PHASE_COLORS,
    PHASE_MAPPING,
    LifePhase,
    TimelineFormat,
    TimelineGenerator,
)


class TestTimelineFormat:
    """Test TimelineFormat enum."""

    def test_format_values(self):
        """Test that all format values are defined."""
        assert TimelineFormat.JSON.value == "json"
        assert TimelineFormat.HTML.value == "html"


class TestLifePhase:
    """Test LifePhase enum."""

    def test_phase_values(self):
        """Test that all phase values are defined."""
        assert LifePhase.EARLY_LIFE.value == "Early Life"
        assert LifePhase.EDUCATION_CAREER.value == "Education & Career"
        assert LifePhase.FAMILY_LIFE.value == "Family Life"
        assert LifePhase.MILITARY_SERVICE.value == "Military Service"
        assert LifePhase.MIGRATION.value == "Migration & Residence"
        assert LifePhase.FINAL_YEARS.value == "Final Years"


class TestPhaseMappings:
    """Test phase mapping constants."""

    def test_phase_mapping_has_birth(self):
        """Test that birth event maps to Early Life."""
        assert PHASE_MAPPING[1] == LifePhase.EARLY_LIFE

    def test_phase_mapping_has_death(self):
        """Test that death event maps to Final Years."""
        assert PHASE_MAPPING[2] == LifePhase.FINAL_YEARS

    def test_phase_colors_defined(self):
        """Test that all phases have colors."""
        assert LifePhase.EARLY_LIFE in PHASE_COLORS
        assert LifePhase.FINAL_YEARS in PHASE_COLORS


class TestTimelineGenerator:
    """Test TimelineGenerator class."""

    @pytest.fixture
    def real_db_path(self):
        """Path to real test database."""
        return Path("data/Iiams.rmtree")

    @pytest.fixture
    def extension_path(self):
        """Path to ICU extension."""
        return Path("sqlite-extension/icu.dylib")

    def test_generator_init_with_path(self, real_db_path, extension_path):
        """Test initializing generator with database path."""
        if not real_db_path.exists():
            pytest.skip("Real database not available")

        generator = TimelineGenerator(db=real_db_path, extension_path=extension_path)
        assert generator.db_path == real_db_path
        assert generator._db is None
        assert generator._owns_db

    def test_generator_init_without_db(self):
        """Test initializing generator without database."""
        generator = TimelineGenerator()
        assert generator.db_path is None
        assert generator._db is None

    def test_parse_date_to_timelinejs_simple(self):
        """Test parsing simple date to TimelineJS format."""
        generator = TimelineGenerator()

        # Date: December 30, 1921
        start, end, display = generator._parse_date_to_timelinejs("D.+192112300000000000000000")

        assert start is not None
        assert start["year"] == 1921
        assert start["month"] == 12
        assert start["day"] == 30
        assert end is None
        assert "1921" in display

    def test_parse_date_to_timelinejs_year_only(self):
        """Test parsing year-only date."""
        generator = TimelineGenerator()

        # Date: 1850 (year only)
        start, end, display = generator._parse_date_to_timelinejs("D.+185000000000000000000000")

        assert start is not None
        assert start["year"] == 1850
        assert "month" not in start
        assert "day" not in start

    def test_parse_date_to_timelinejs_unknown(self):
        """Test parsing unknown date."""
        generator = TimelineGenerator()

        start, end, display = generator._parse_date_to_timelinejs(".")

        assert start is None
        assert end is None
        # Empty string or None is acceptable for unknown dates
        assert display is None or display == ""

    def test_format_place_for_timeline(self):
        """Test place formatting for timeline display."""
        generator = TimelineGenerator()

        # Full US place: City, County, State, Country
        place = generator._format_place_for_timeline("Tulsa, Tulsa County, Oklahoma, United States")
        assert place == "Tulsa, Oklahoma"

        # International place
        place = generator._format_place_for_timeline("London, Greater London, England, United Kingdom")
        assert place == "London, England"

        # Simple place
        place = generator._format_place_for_timeline("Tulsa")
        assert place == "Tulsa"

        # Empty place
        place = generator._format_place_for_timeline("")
        assert place is None

    def test_build_event_narrative(self):
        """Test building event narrative."""
        generator = TimelineGenerator()

        narrative = generator._build_event_narrative(
            event_type="Birth",
            date="December 30, 1921",
            place="Tulsa, Oklahoma",
            details="Born at home",
        )

        assert "<p><strong>December 30, 1921</strong> in Tulsa, Oklahoma</p>" in narrative
        assert "<p>Born at home</p>" in narrative

    def test_build_event_narrative_no_date(self):
        """Test building narrative without date."""
        generator = TimelineGenerator()

        narrative = generator._build_event_narrative(
            event_type="Event", date=None, place="Tulsa, Oklahoma", details=None
        )

        assert "<p><strong>Date Unknown</strong> in Tulsa, Oklahoma</p>" in narrative

    def test_determine_life_phase_by_event_type(self):
        """Test life phase determination by event type."""
        generator = TimelineGenerator()

        # Birth -> Early Life
        phase = generator._determine_life_phase(1, None, None)
        assert phase == LifePhase.EARLY_LIFE

        # Death -> Final Years
        phase = generator._determine_life_phase(2, None, None)
        assert phase == LifePhase.FINAL_YEARS

        # Marriage -> Family Life
        phase = generator._determine_life_phase(9, None, None)
        assert phase == LifePhase.FAMILY_LIFE

    def test_determine_life_phase_by_age(self):
        """Test life phase determination by age."""
        generator = TimelineGenerator()

        # Age 10 -> Early Life
        phase = generator._determine_life_phase(999, 1921, {"year": 1931})
        assert phase == LifePhase.EARLY_LIFE

        # Age 65 -> Later Life
        phase = generator._determine_life_phase(999, 1921, {"year": 1986})
        assert phase == LifePhase.LATER_LIFE

        # Age 35 -> Life Events
        phase = generator._determine_life_phase(999, 1921, {"year": 1956})
        assert phase == LifePhase.LIFE_EVENTS

    def test_sort_events(self):
        """Test event sorting."""
        generator = TimelineGenerator()

        events = [
            {
                "unique_id": "event_3",
                "_sort_date": 19500000,
                "_event_type_id": 12,
            },
            {
                "unique_id": "event_1",
                "_sort_date": 19210000,
                "_event_type_id": 1,  # Birth
            },
            {
                "unique_id": "event_2",
                "_sort_date": 19210000,
                "_event_type_id": 2,  # Death (should come after birth on same date)
            },
        ]

        sorted_events = generator._sort_events(events)

        # Check order: birth (1921), death (1921), other (1950)
        assert sorted_events[0]["unique_id"] == "event_1"  # Birth first
        assert sorted_events[1]["unique_id"] == "event_2"  # Death second (same date)
        assert sorted_events[2]["unique_id"] == "event_3"  # Later event

        # Check internal fields removed
        assert "_sort_date" not in sorted_events[0]
        assert "_event_type_id" not in sorted_events[0]

    def test_format_json(self):
        """Test JSON formatting."""
        generator = TimelineGenerator()

        timeline_data = {
            "person_name": "John Doe",
            "lifespan": "(1920 - 2000)",
            "person_id": 1,
            "events": [
                {
                    "unique_id": "event_1",
                    "start_date": {"year": 1920, "month": 1, "day": 1},
                    "text": {"headline": "Birth", "text": "<p>Born in 1920</p>"},
                }
            ],
            "title_media": None,
        }

        json_output = generator._format_json(timeline_data)
        parsed = json.loads(json_output)

        assert parsed["title"]["text"]["headline"] == "John Doe"
        assert parsed["title"]["text"]["text"] == "(1920 - 2000)"
        assert len(parsed["events"]) == 1
        assert parsed["events"][0]["unique_id"] == "event_1"
        assert parsed["scale"] == "human"

    def test_format_html(self):
        """Test HTML formatting."""
        generator = TimelineGenerator()

        timeline_data = {
            "person_name": "John Doe",
            "lifespan": "(1920 - 2000)",
            "person_id": 1,
            "events": [],
            "title_media": None,
        }

        html_output = generator._format_html(timeline_data)

        # Verify HTML structure
        assert "<!DOCTYPE html>" in html_output
        assert '<html lang="en">' in html_output
        assert "<title>Timeline: John Doe</title>" in html_output

        # Verify TimelineJS3 includes
        assert "timeline3/latest/css/timeline.css" in html_output
        assert "timeline3/latest/js/timeline.js" in html_output

        # Verify header
        assert "<h1>John Doe</h1>" in html_output
        assert "<p>(1920 - 2000)</p>" in html_output

        # Verify timeline initialization
        assert "new TL.Timeline" in html_output
        assert "timeline-embed" in html_output

    def test_generate_raises_error_without_database(self):
        """Test that generate raises ValueError without database."""
        generator = TimelineGenerator()

        with pytest.raises(ValueError, match="No database provided"):
            generator.generate(person_id=1, format=TimelineFormat.JSON)

    def test_generate_raises_error_for_nonexistent_person(self, real_db_path, extension_path):
        """Test that generate raises ValueError for nonexistent person."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = TimelineGenerator(db=real_db_path, extension_path=extension_path)

        with pytest.raises(ValueError, match="Person 999999 not found"):
            generator.generate(person_id=999999, format=TimelineFormat.JSON)

    def test_generate_json_format(self, real_db_path, extension_path):
        """Test generating JSON timeline."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = TimelineGenerator(db=real_db_path, extension_path=extension_path)

        json_output = generator.generate(person_id=1, format=TimelineFormat.JSON)

        # Verify it's valid JSON
        parsed = json.loads(json_output)

        # Verify structure
        assert "title" in parsed
        assert "text" in parsed["title"]
        assert "headline" in parsed["title"]["text"]
        assert "events" in parsed
        assert isinstance(parsed["events"], list)
        assert parsed["scale"] == "human"

    def test_generate_html_format(self, real_db_path, extension_path):
        """Test generating HTML timeline."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = TimelineGenerator(db=real_db_path, extension_path=extension_path)

        html_output = generator.generate(person_id=1, format=TimelineFormat.HTML)

        # Verify HTML structure
        assert "<!DOCTYPE html>" in html_output
        assert "timeline3/latest" in html_output
        assert "new TL.Timeline" in html_output

    def test_generate_with_output_path(self, tmp_path, real_db_path, extension_path):
        """Test writing timeline to file."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = TimelineGenerator(db=real_db_path, extension_path=extension_path)
        output_file = tmp_path / "timeline.json"

        json_output = generator.generate(person_id=1, format=TimelineFormat.JSON, output_path=output_file)

        # Verify file was created
        assert output_file.exists()

        # Verify content matches
        file_content = output_file.read_text(encoding="utf-8")
        assert file_content == json_output

        # Verify it's valid JSON
        parsed = json.loads(file_content)
        assert "title" in parsed
        assert "events" in parsed

    def test_generate_unsupported_format(self, real_db_path, extension_path):
        """Test that unsupported format raises ValueError."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = TimelineGenerator(db=real_db_path, extension_path=extension_path)

        with pytest.raises(ValueError, match="Unsupported format"):
            generator.generate(person_id=1, format="invalid_format")  # type: ignore


class TestTimelineIntegration:
    """Integration tests with real database."""

    @pytest.fixture
    def real_db_path(self):
        """Path to real test database."""
        return Path("data/Iiams.rmtree")

    @pytest.fixture
    def extension_path(self):
        """Path to ICU extension."""
        return Path("sqlite-extension/icu.dylib")

    def test_generate_complete_timeline(self, real_db_path, extension_path):
        """Test generating complete timeline with all features."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = TimelineGenerator(db=real_db_path, extension_path=extension_path)

        # Generate JSON
        json_output = generator.generate(person_id=1, format=TimelineFormat.JSON, group_by_phase=True)

        # Parse and verify
        timeline = json.loads(json_output)

        # Verify title
        assert timeline["title"]["text"]["headline"]
        assert timeline["title"]["text"]["text"]  # Lifespan

        # Verify has events
        assert len(timeline["events"]) > 0

        # Verify events have required fields
        for event in timeline["events"]:
            assert "unique_id" in event
            assert "text" in event
            assert "headline" in event["text"]

            # At least some events should have dates
            if "start_date" in event:
                assert "year" in event["start_date"]

            # At least some events should have groups
            if "group" in event:
                assert event["group"] in [phase.value for phase in LifePhase]

    def test_generate_both_formats(self, real_db_path, extension_path):
        """Test that both JSON and HTML formats can be generated."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = TimelineGenerator(db=real_db_path, extension_path=extension_path)

        # Generate both formats
        json_output = generator.generate(person_id=1, format=TimelineFormat.JSON)
        html_output = generator.generate(person_id=1, format=TimelineFormat.HTML)

        # Verify both succeeded
        assert len(json_output) > 0
        assert len(html_output) > 0

        # Verify they're different
        assert json_output != html_output

        # Verify JSON is valid
        timeline = json.loads(json_output)
        assert "title" in timeline
        assert "events" in timeline

        # Verify HTML contains JSON data
        assert "var timelineData =" in html_output
        # HTML should contain the timeline data
        assert timeline["title"]["text"]["headline"] in html_output

    def test_timeline_event_ordering(self, real_db_path, extension_path):
        """Test that events are properly ordered chronologically."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = TimelineGenerator(db=real_db_path, extension_path=extension_path)

        json_output = generator.generate(person_id=1, format=TimelineFormat.JSON)
        timeline = json.loads(json_output)

        # Check that events are in chronological order
        previous_year = None
        for event in timeline["events"]:
            if "start_date" in event and "year" in event["start_date"]:
                current_year = event["start_date"]["year"]
                if previous_year is not None:
                    # Current year should be >= previous year
                    assert current_year >= previous_year
                previous_year = current_year

    def test_timeline_with_private_events_excluded(self, real_db_path, extension_path):
        """Test that private events are excluded by default."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = TimelineGenerator(db=real_db_path, extension_path=extension_path, include_private=False)

        json_output = generator.generate(person_id=1, format=TimelineFormat.JSON)
        timeline = json.loads(json_output)

        # Just verify it works - we can't easily test if private events are excluded
        # without knowing which events are private in the test database
        assert "events" in timeline
        assert isinstance(timeline["events"], list)

    def test_timeline_html_is_self_contained(self, real_db_path, extension_path):
        """Test that HTML output is self-contained."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = TimelineGenerator(db=real_db_path, extension_path=extension_path)

        html_output = generator.generate(person_id=1, format=TimelineFormat.HTML)

        # Verify it has all necessary components
        assert "<!DOCTYPE html>" in html_output
        assert "<html" in html_output
        assert "</html>" in html_output
        assert "<head>" in html_output
        assert "<body>" in html_output

        # Verify it includes TimelineJS library via CDN
        assert "cdn.knightlab.com" in html_output

        # Verify it has embedded data
        assert "var timelineData =" in html_output

        # Verify it has timeline initialization
        assert "new TL.Timeline" in html_output
