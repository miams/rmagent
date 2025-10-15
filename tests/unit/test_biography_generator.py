"""Unit tests for biography generator."""

from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from rmagent.agent.genealogy_agent import GenealogyAgent
from rmagent.agent.llm_provider import LLMResult
from rmagent.generators.biography import (
    Biography,
    BiographyGenerator,
    BiographyLength,
    CitationStyle,
    EventContext,
    PersonContext,
)


class TestBiographyLength:
    """Test BiographyLength enum."""

    def test_length_values(self):
        """Test that all length values are defined."""
        assert BiographyLength.SHORT.value == "short"
        assert BiographyLength.STANDARD.value == "standard"
        assert BiographyLength.COMPREHENSIVE.value == "comprehensive"


class TestCitationStyle:
    """Test CitationStyle enum."""

    def test_citation_style_values(self):
        """Test that all citation style values are defined."""
        assert CitationStyle.FOOTNOTE.value == "footnote"
        assert CitationStyle.PARENTHETICAL.value == "parenthetical"
        assert CitationStyle.NARRATIVE.value == "narrative"


class TestEventContext:
    """Test EventContext dataclass."""

    def test_event_context_creation(self):
        """Test creating EventContext."""
        event = EventContext(
            event_id=1,
            event_type="Birth",
            date="30 Apr 1968",
            place="Palo Alto, California",
            details="",
            note="",
            is_private=False,
            proof=1,
            citations=[],
            sort_date=19680430,
        )

        assert event.event_id == 1
        assert event.event_type == "Birth"
        assert event.date == "30 Apr 1968"
        assert event.place == "Palo Alto, California"
        assert not event.is_private


class TestPersonContext:
    """Test PersonContext dataclass."""

    def test_person_context_creation(self):
        """Test creating PersonContext with minimal data."""
        person = PersonContext(
            person_id=1,
            full_name="John Smith",
            given_name="John",
            surname="Smith",
            prefix=None,
            suffix=None,
            nickname=None,
            birth_year=1850,
            birth_date="1850",
            birth_place="Maryland",
            death_year=1920,
            death_date="1920",
            death_place="Pennsylvania",
            sex=0,
            is_private=False,
            is_living=False,
        )

        assert person.person_id == 1
        assert person.full_name == "John Smith"
        assert person.birth_year == 1850
        assert person.death_year == 1920
        assert person.sex == 0
        assert not person.is_private
        assert not person.is_living

    def test_person_context_with_relationships(self):
        """Test PersonContext with family relationships."""
        person = PersonContext(
            person_id=1,
            full_name="John Smith",
            given_name="John",
            surname="Smith",
            prefix=None,
            suffix=None,
            nickname=None,
            birth_year=1850,
            birth_date=None,
            birth_place=None,
            death_year=None,
            death_date=None,
            death_place=None,
            sex=0,
            is_private=False,
            is_living=False,
            father_id=2,
            father_name="James Smith",
            mother_id=3,
            mother_name="Mary Smith",
            spouses=[{"PersonID": 4, "Given": "Jane", "Surname": "Doe"}],
            children=[{"PersonID": 5, "Given": "Tom", "Surname": "Smith"}],
        )

        assert person.father_name == "James Smith"
        assert person.mother_name == "Mary Smith"
        assert len(person.spouses) == 1
        assert len(person.children) == 1


class TestBiography:
    """Test Biography dataclass."""

    def test_biography_creation(self):
        """Test creating Biography."""
        bio = Biography(
            person_id=1,
            full_name="John Smith",
            length=BiographyLength.STANDARD,
            citation_style=CitationStyle.FOOTNOTE,
            introduction="John Smith was born in 1850.",
            early_life="He grew up in Maryland.",
            education="He attended local schools.",
            career="He worked as a farmer.",
            marriage_family="He married Jane Doe.",
            later_life="He lived in Pennsylvania.",
            death_legacy="He died in 1920.",
            footnotes="",
            sources="1. Census records",
        )

        assert bio.person_id == 1
        assert bio.full_name == "John Smith"
        assert bio.length == BiographyLength.STANDARD
        assert bio.citation_style == CitationStyle.FOOTNOTE

    def test_biography_render_markdown(self):
        """Test rendering biography as markdown."""
        bio = Biography(
            person_id=1,
            full_name="John Smith",
            length=BiographyLength.SHORT,
            citation_style=CitationStyle.FOOTNOTE,
            introduction="John Smith was born in 1850.",
            early_life="He grew up in Maryland.",
            education="",
            career="",
            marriage_family="",
            later_life="",
            death_legacy="He died in 1920.",
            footnotes="",
            sources="",
        )

        markdown = bio.render_markdown()
        assert "# Biography of John Smith" in markdown
        assert "## Introduction" in markdown
        assert "## Early Life & Family Background" in markdown
        assert "John Smith was born in 1850." in markdown
        assert bio.word_count > 0

    def test_biography_str(self):
        """Test Biography.__str__ returns markdown."""
        bio = Biography(
            person_id=1,
            full_name="John Smith",
            length=BiographyLength.SHORT,
            citation_style=CitationStyle.FOOTNOTE,
            introduction="Test",
            early_life="",
            education="",
            career="",
            marriage_family="",
            later_life="",
            death_legacy="",
            footnotes="",
            sources="",
        )

        str_output = str(bio)
        assert "# Biography of John Smith" in str_output


class TestBiographyGenerator:
    """Test BiographyGenerator class."""

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

        generator = BiographyGenerator(db=real_db_path, extension_path=extension_path)
        assert generator.db_path == real_db_path
        assert generator._db is None
        assert generator._owns_db

    def test_generator_init_without_db(self):
        """Test initializing generator without database."""
        generator = BiographyGenerator()
        assert generator.db_path is None
        assert generator._db is None

    def test_apply_privacy_rules_for_private_person(self):
        """Test that privacy rules filter private events."""
        generator = BiographyGenerator()

        # Create person context with private events
        context = PersonContext(
            person_id=1,
            full_name="John Smith",
            given_name="John",
            surname="Smith",
            prefix=None,
            suffix=None,
            nickname=None,
            birth_year=1850,
            birth_date=None,
            birth_place=None,
            death_year=None,
            death_date=None,
            death_place=None,
            sex=0,
            is_private=True,
            is_living=False,
            occupation_events=[
                EventContext(
                    event_id=1,
                    event_type="Occupation",
                    date="1870",
                    place="Maryland",
                    details="Farmer",
                    note="",
                    is_private=True,
                    proof=0,
                    citations=[],
                    sort_date=18700000,
                )
            ],
        )

        # Apply privacy rules
        generator._apply_privacy_rules(context)

        # Verify private events were filtered
        assert len(context.occupation_events) == 0
        assert hasattr(context, "privacy_applied")

    def test_apply_privacy_rules_for_living_person(self):
        """Test that living persons have sensitive events filtered."""
        generator = BiographyGenerator(current_year=2025)

        # Create person context for living person (born 1990, age 35)
        context = PersonContext(
            person_id=1,
            full_name="Jane Doe",
            given_name="Jane",
            surname="Doe",
            prefix=None,
            suffix=None,
            nickname=None,
            birth_year=1990,
            birth_date=None,
            birth_place=None,
            death_year=None,
            death_date=None,
            death_place=None,
            sex=1,
            is_private=False,
            is_living=True,
            occupation_events=[
                EventContext(
                    event_id=1,
                    event_type="Occupation",
                    date="2010",
                    place="California",
                    details="Engineer",
                    note="",
                    is_private=False,
                    proof=0,
                    citations=[],
                    sort_date=20100000,
                )
            ],
            residence_events=[
                EventContext(
                    event_id=2,
                    event_type="Residence",
                    date="2020",
                    place="San Francisco",
                    details="",
                    note="",
                    is_private=False,
                    proof=0,
                    citations=[],
                    sort_date=20200000,
                )
            ],
        )

        # Apply privacy rules
        generator._apply_privacy_rules(context)

        # Verify sensitive events were filtered for living person
        assert len(context.occupation_events) == 0
        assert len(context.residence_events) == 0

    def test_generate_introduction(self):
        """Test generating introduction section."""
        from rmagent.generators.biography import BiographyTemplates

        templates = BiographyTemplates()

        context = PersonContext(
            person_id=1,
            full_name="John Dorsey Iams",
            given_name="John",
            surname="Iams",
            prefix=None,
            suffix=None,
            nickname=None,
            birth_year=1921,
            birth_date="30 Dec 1921",
            birth_place="Tulsa, Oklahoma",
            death_year=None,
            death_date=None,
            death_place=None,
            sex=0,
            is_private=False,
            is_living=False,
            father_name="William Leonard Iams",
            mother_name="Lucy Virginia Dorsey",
        )

        intro = templates.generate_introduction(context)

        assert "John Dorsey Iams" in intro
        assert "30 Dec 1921" in intro
        assert "Tulsa, Oklahoma" in intro
        assert "William Leonard Iams" in intro
        assert "Lucy Virginia Dorsey" in intro

    def test_generate_early_life(self):
        """Test generating early life section."""
        from rmagent.generators.biography import BiographyTemplates

        templates = BiographyTemplates()

        # Test with siblings
        context = PersonContext(
            person_id=1,
            full_name="John Smith",
            given_name="John",
            surname="Smith",
            prefix=None,
            suffix=None,
            nickname=None,
            birth_year=1850,
            birth_date=None,
            birth_place=None,
            death_year=None,
            death_date=None,
            death_place=None,
            sex=0,
            is_private=False,
            is_living=False,
            siblings=[{"PersonID": 2}, {"PersonID": 3}],
        )

        early_life = templates.generate_early_life(context)
        assert "2 siblings" in early_life

    def test_format_sources_footnote_style(self):
        """Test formatting sources in footnote style."""
        from rmagent.generators.biography import CitationProcessor

        citation_processor = CitationProcessor()

        context = PersonContext(
            person_id=1,
            full_name="John Smith",
            given_name="John",
            surname="Smith",
            prefix=None,
            suffix=None,
            nickname=None,
            birth_year=1850,
            birth_date=None,
            birth_place=None,
            death_year=None,
            death_date=None,
            death_place=None,
            sex=0,
            is_private=False,
            is_living=False,
            all_citations=[
                {"CitationID": 1, "SourceName": "U.S. Census 1850", "CitationName": "Page 123"},
                {
                    "CitationID": 2,
                    "SourceName": "Birth Certificate",
                    "CitationName": "Certificate No. 456",
                },
            ],
        )

        sources = citation_processor.format_sources_section(context, CitationStyle.FOOTNOTE)

        assert "1. *U.S. Census 1850*" in sources
        assert "2. *Birth Certificate*" in sources
        assert "Page 123" in sources
        assert "Certificate No. 456" in sources

    def test_format_sources_parenthetical_style(self):
        """Test formatting sources in parenthetical style."""
        from rmagent.generators.biography import CitationProcessor

        citation_processor = CitationProcessor()

        context = PersonContext(
            person_id=1,
            full_name="John Smith",
            given_name="John",
            surname="Smith",
            prefix=None,
            suffix=None,
            nickname=None,
            birth_year=1850,
            birth_date=None,
            birth_place=None,
            death_year=None,
            death_date=None,
            death_place=None,
            sex=0,
            is_private=False,
            is_living=False,
            all_citations=[
                {"CitationID": 1, "SourceName": "U.S. Census 1850", "CitationName": "Page 123"},
            ],
        )

        sources = citation_processor.format_sources_section(context, CitationStyle.PARENTHETICAL)

        assert "- *U.S. Census 1850*" in sources
        assert "(Page 123)" in sources

    def test_parse_ai_response(self):
        """Test parsing AI-generated biography."""
        from rmagent.generators.biography import BiographyTemplates

        templates = BiographyTemplates()

        ai_response = """
## Introduction

John Smith was born in 1850 in Maryland.

## Early Life & Family Background

John grew up on a farm with three siblings.

## Career & Occupation

John worked as a blacksmith for thirty years.

## Death & Legacy

John died in 1920 in Pennsylvania.
"""

        sections = templates.parse_ai_response(ai_response)

        assert "John Smith was born" in sections["introduction"]
        assert "grew up on a farm" in sections["early_life"]
        assert "blacksmith" in sections["career"]
        assert "died in 1920" in sections["death_legacy"]

    def test_generate_template_based_without_agent(self, real_db_path, extension_path):
        """Test generating biography without AI agent (template-based)."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = BiographyGenerator(db=real_db_path, extension_path=extension_path)

        bio = generator.generate(
            person_id=1,
            length=BiographyLength.SHORT,
            citation_style=CitationStyle.FOOTNOTE,
            use_ai=False,
        )

        assert bio.person_id == 1
        assert bio.length == BiographyLength.SHORT
        assert bio.citation_style == CitationStyle.FOOTNOTE
        assert bio.introduction  # Should have introduction
        assert isinstance(bio, Biography)

    def test_generate_raises_error_for_nonexistent_person(self, real_db_path, extension_path):
        """Test that generate raises ValueError for nonexistent person."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = BiographyGenerator(db=real_db_path, extension_path=extension_path)

        with pytest.raises(ValueError, match="Person 999999 not found"):
            generator.generate(person_id=999999, use_ai=False)

    def test_generate_with_ai_requires_agent(self, real_db_path, extension_path):
        """Test that AI generation requires agent parameter."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = BiographyGenerator(db=real_db_path, extension_path=extension_path)

        with pytest.raises(ValueError, match="AI generation requested but no agent provided"):
            generator.generate(person_id=1, use_ai=True)

    def test_generate_with_mock_agent(self, real_db_path, extension_path):
        """Test biography generation with mocked AI agent."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        # Create mock agent
        mock_agent = Mock(spec=GenealogyAgent)
        mock_result = MagicMock(spec=LLMResult)
        mock_result.text = """
## Introduction

Michael Dorsey Iams was born on 30 April 1968 in Palo Alto, California.

## Early Life & Family Background

Michael grew up in California and Arizona.

## Career & Accomplishments

Michael became a genealogist and researcher.
"""
        mock_agent.generate_biography.return_value = mock_result

        generator = BiographyGenerator(
            db=real_db_path,
            agent=mock_agent,
            extension_path=extension_path,
        )

        bio = generator.generate(
            person_id=1,
            length=BiographyLength.STANDARD,
            citation_style=CitationStyle.FOOTNOTE,
            use_ai=True,
        )

        assert bio.person_id == 1
        assert "Michael Dorsey Iams" in bio.introduction
        assert mock_agent.generate_biography.called

    def test_categorize_events(self, real_db_path, extension_path):
        """Test event categorization."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        from rmagent.rmlib.database import RMDatabase

        generator = BiographyGenerator(db=real_db_path, extension_path=extension_path)

        with RMDatabase(real_db_path, extension_path=extension_path) as db:
            # Create sample events with different types
            events = [
                {
                    "EventID": 1,
                    "EventType": 1,
                    "Date": "",
                    "Place": "",
                    "Details": "",
                    "IsPrivate": 0,
                    "Proof": 0,
                    "SortDate": 0,
                },  # Birth
                {
                    "EventID": 2,
                    "EventType": 17,
                    "Date": "",
                    "Place": "",
                    "Details": "",
                    "IsPrivate": 0,
                    "Proof": 0,
                    "SortDate": 0,
                },  # Education
                {
                    "EventID": 3,
                    "EventType": 12,
                    "Date": "",
                    "Place": "",
                    "Details": "",
                    "IsPrivate": 0,
                    "Proof": 0,
                    "SortDate": 0,
                },  # Occupation
                {
                    "EventID": 4,
                    "EventType": 10,
                    "Date": "",
                    "Place": "",
                    "Details": "",
                    "IsPrivate": 0,
                    "Proof": 0,
                    "SortDate": 0,
                },  # Military
                {
                    "EventID": 5,
                    "EventType": 13,
                    "Date": "",
                    "Place": "",
                    "Details": "",
                    "IsPrivate": 0,
                    "Proof": 0,
                    "SortDate": 0,
                },  # Residence
            ]

            vital, education, occupation, military, residence, other = generator._categorize_events(db, events)

            assert len(vital) == 1
            assert len(education) == 1
            assert len(occupation) == 1
            assert len(military) == 1
            assert len(residence) == 1


class TestBiographyIntegration:
    """Integration tests with real database."""

    @pytest.fixture
    def real_db_path(self):
        """Path to real test database."""
        return Path("data/Iiams.rmtree")

    @pytest.fixture
    def extension_path(self):
        """Path to ICU extension."""
        return Path("sqlite-extension/icu.dylib")

    def test_full_biography_generation_template_based(self, real_db_path, extension_path):
        """Test complete biography generation (template-based) with real database."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = BiographyGenerator(db=real_db_path, extension_path=extension_path)

        bio = generator.generate(
            person_id=1,
            length=BiographyLength.STANDARD,
            citation_style=CitationStyle.FOOTNOTE,
            include_sources=True,
            use_ai=False,
        )

        # Verify biography structure
        assert bio.person_id == 1
        assert bio.full_name
        assert bio.introduction
        assert bio.length == BiographyLength.STANDARD
        assert bio.citation_style == CitationStyle.FOOTNOTE

        # Verify markdown rendering
        markdown = bio.render_markdown()
        assert "# " in markdown  # Title
        assert "## " in markdown  # Section headers
        assert bio.word_count > 0

    def test_biography_with_different_citation_styles(self, real_db_path, extension_path):
        """Test biography generation with different citation styles."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = BiographyGenerator(db=real_db_path, extension_path=extension_path)

        # Test each citation style
        for style in [CitationStyle.FOOTNOTE, CitationStyle.PARENTHETICAL, CitationStyle.NARRATIVE]:
            bio = generator.generate(
                person_id=1,
                citation_style=style,
                include_sources=True,
                use_ai=False,
            )

            assert bio.citation_style == style
            if bio.sources:  # Only if sources exist
                assert len(bio.sources) > 0
