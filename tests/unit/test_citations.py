"""
Unit tests for biography citation processing and formatting.

Tests citation formatting, footnote generation, and bibliography creation.
"""

from rmagent.generators.biography.citations import CitationProcessor
from rmagent.generators.biography.models import CitationInfo, CitationStyle, CitationTracker


class TestStripSourceTypePrefix:
    """Test strip_source_type_prefix static method."""

    def test_strip_book_prefix(self):
        """Test removing 'Book: ' prefix."""
        result = CitationProcessor.strip_source_type_prefix("Book: Smith Family History")
        assert result == "Smith Family History"

    def test_strip_newspaper_prefix(self):
        """Test removing 'Newspaper: ' prefix."""
        result = CitationProcessor.strip_source_type_prefix("Newspaper: Baltimore Sun")
        assert result == "Baltimore Sun"

    def test_strip_newspapers_plural_prefix(self):
        """Test removing 'Newspapers: ' prefix."""
        result = CitationProcessor.strip_source_type_prefix("Newspapers: New York Times")
        assert result == "New York Times"

    def test_no_prefix_to_strip(self):
        """Test source name without prefix remains unchanged."""
        result = CitationProcessor.strip_source_type_prefix("US Census Records")
        assert result == "US Census Records"

    def test_strip_cemetery_prefix(self):
        """Test removing 'Cemetery: ' prefix."""
        result = CitationProcessor.strip_source_type_prefix("Cemetery: Oak Hill")
        assert result == "Oak Hill"

    def test_strip_website_prefix(self):
        """Test removing 'Website: ' prefix."""
        result = CitationProcessor.strip_source_type_prefix("Website: Ancestry.com")
        assert result == "Ancestry.com"


class TestFormatCitationInfo:
    """Test format_citation_info method."""

    def test_format_freeform_citation_with_all_fields(self):
        """Test formatting free-form citation with all fields populated."""
        processor = CitationProcessor()
        citation = {
            "CitationID": 123,
            "SourceID": 456,
            "TemplateID": 0,  # Free-form
            "Footnote": "Smith, *Family History*, p. 42",
            "ShortFootnote": "Smith, p. 42",
            "CitationBibliography": "Smith, John. *Family History*. Publisher, 2000.",
        }

        result = processor.format_citation_info(citation)

        assert isinstance(result, CitationInfo)
        assert result.citation_id == 123
        assert result.source_id == 456
        assert result.footnote == "Smith, *Family History*, p. 42"
        assert result.short_footnote == "Smith, p. 42"
        assert result.bibliography == "Smith, John. *Family History*. Publisher, 2000."
        assert result.is_freeform is True
        assert result.template_name is None

    def test_format_template_citation(self):
        """Test formatting template-based citation shows placeholders."""
        processor = CitationProcessor()
        citation = {
            "CitationID": 789,
            "SourceID": 101,
            "TemplateID": 5,  # Template-based
            "TemplateName": "US Census",
            "Footnote": None,
            "ShortFootnote": None,
            "CitationBibliography": None,
        }

        result = processor.format_citation_info(citation)

        assert result.citation_id == 789
        assert result.source_id == 101
        assert result.is_freeform is False
        assert result.template_name == "US Census"
        assert "[Citation 789, Template: US Census]" in result.footnote
        assert "[Source 101, Template: US Census]" in result.bibliography


class TestProcessCitationsInText:
    """Test process_citations_in_text method."""

    def test_process_single_citation(self):
        """Test processing single citation marker in text."""
        processor = CitationProcessor()
        text = "He was born in 1850.{{cite:123}}"
        citations = [
            {
                "CitationID": 123,
                "SourceID": 456,
                "TemplateID": 0,
                "Footnote": "Birth Record, p. 10",
                "ShortFootnote": "Birth Record",
                "CitationBibliography": "Vital Records Office.",
            }
        ]

        modified_text, footnotes, tracker = processor.process_citations_in_text(text, citations)

        assert modified_text == "He was born in 1850.[^1]"
        assert len(footnotes) == 1
        assert footnotes[0][0] == 1  # Footnote number
        assert footnotes[0][1].citation_id == 123
        assert len(tracker.citation_order) == 1

    def test_process_multiple_citations(self):
        """Test processing multiple citation markers in text."""
        processor = CitationProcessor()
        text = "He was born{{cite:123}} and died{{cite:456}}."
        citations = [
            {
                "CitationID": 123,
                "SourceID": 1,
                "TemplateID": 0,
                "Footnote": "Birth Record",
                "ShortFootnote": "Birth Record",
                "CitationBibliography": "Vital Records.",
            },
            {
                "CitationID": 456,
                "SourceID": 2,
                "TemplateID": 0,
                "Footnote": "Death Record",
                "ShortFootnote": "Death Record",
                "CitationBibliography": "Death Index.",
            },
        ]

        modified_text, footnotes, tracker = processor.process_citations_in_text(text, citations)

        assert modified_text == "He was born[^1] and died[^2]."
        assert len(footnotes) == 2
        assert footnotes[0][0] == 1
        assert footnotes[1][0] == 2

    def test_process_duplicate_citation(self):
        """Test that duplicate citations get same footnote number."""
        processor = CitationProcessor()
        text = "First mention{{cite:123}} and second mention{{cite:123}}."
        citations = [
            {
                "CitationID": 123,
                "SourceID": 456,
                "TemplateID": 0,
                "Footnote": "Source A",
                "ShortFootnote": "Source A",
                "CitationBibliography": "Bibliography A.",
            }
        ]

        modified_text, footnotes, tracker = processor.process_citations_in_text(text, citations)

        assert modified_text == "First mention[^1] and second mention[^1]."
        assert len(footnotes) == 1  # Only one unique citation

    def test_process_missing_citation(self):
        """Test processing citation marker with missing citation."""
        processor = CitationProcessor()
        text = "Reference to missing citation{{cite:999}}."
        citations = []  # No citations available

        modified_text, footnotes, tracker = processor.process_citations_in_text(text, citations)

        assert "[^999?]" in modified_text  # Should show placeholder with ?
        assert len(footnotes) == 0

    def test_process_no_citations(self):
        """Test text with no citation markers."""
        processor = CitationProcessor()
        text = "Plain text with no citations."
        citations = []

        modified_text, footnotes, tracker = processor.process_citations_in_text(text, citations)

        assert modified_text == text
        assert len(footnotes) == 0
        assert len(tracker.citation_order) == 0


class TestGenerateFootnotesSection:
    """Test generate_footnotes_section method."""

    def test_generate_single_footnote(self):
        """Test generating footnotes section with single entry."""
        processor = CitationProcessor()
        tracker = CitationTracker()
        tracker.add_citation(123, 456)

        citation_info = CitationInfo(
            citation_id=123,
            source_id=456,
            footnote="Full footnote text",
            short_footnote="Short footnote",
            bibliography="Bibliography entry",
            is_freeform=True,
            template_name=None,
        )
        footnotes = [(1, citation_info)]

        result = processor.generate_footnotes_section(footnotes, tracker)

        assert result == "   [^1]: Full footnote text"

    def test_generate_multiple_footnotes_first_and_subsequent(self):
        """Test first citation uses full footnote, subsequent use short."""
        processor = CitationProcessor()
        tracker = CitationTracker()

        # Same source cited twice
        tracker.add_citation(123, 456)  # First citation for source 456
        tracker.add_citation(124, 456)  # Second citation for same source

        citation1 = CitationInfo(
            citation_id=123,
            source_id=456,
            footnote="Full footnote for source 456",
            short_footnote="Short for 456",
            bibliography="Bibliography",
            is_freeform=True,
            template_name=None,
        )
        citation2 = CitationInfo(
            citation_id=124,
            source_id=456,
            footnote="Full footnote for source 456",
            short_footnote="Short for 456",
            bibliography="Bibliography",
            is_freeform=True,
            template_name=None,
        )

        footnotes = [(1, citation1), (2, citation2)]
        result = processor.generate_footnotes_section(footnotes, tracker)

        lines = result.split("\n")
        assert "Full footnote for source 456" in lines[0]  # First uses full
        assert "Short for 456" in lines[1]  # Second uses short


class TestGenerateSourcesSection:
    """Test generate_sources_section method."""

    def test_generate_single_source(self):
        """Test generating bibliography with single source."""
        processor = CitationProcessor()
        citations = [
            {
                "CitationID": 123,
                "SourceID": 456,
                "TemplateID": 0,
                "Footnote": "Footnote",
                "ShortFootnote": "Short",
                "CitationBibliography": "Smith, John. *Family History*. 2000.",
            }
        ]

        result = processor.generate_sources_section(citations)

        assert "   Smith, John. *Family History*. 2000." in result

    def test_generate_multiple_sources_sorted(self):
        """Test bibliography is alphabetically sorted."""
        processor = CitationProcessor()
        citations = [
            {
                "CitationID": 1,
                "SourceID": 1,
                "TemplateID": 0,
                "Footnote": "F",
                "ShortFootnote": "S",
                "CitationBibliography": "Zimmerman, Alice. Book Z.",
            },
            {
                "CitationID": 2,
                "SourceID": 2,
                "TemplateID": 0,
                "Footnote": "F",
                "ShortFootnote": "S",
                "CitationBibliography": "Adams, Bob. Book A.",
            },
        ]

        result = processor.generate_sources_section(citations)

        lines = result.split("\n")
        assert "Adams" in lines[0]  # Adams should be first alphabetically
        assert "Zimmerman" in lines[1]  # Zimmerman should be second

    def test_deduplicate_sources_by_id(self):
        """Test that sources are deduplicated by SourceID."""
        processor = CitationProcessor()
        citations = [
            {
                "CitationID": 1,
                "SourceID": 100,
                "TemplateID": 0,
                "Footnote": "F",
                "ShortFootnote": "S",
                "CitationBibliography": "Same Source.",
            },
            {
                "CitationID": 2,
                "SourceID": 100,  # Same SourceID
                "TemplateID": 0,
                "Footnote": "F",
                "ShortFootnote": "S",
                "CitationBibliography": "Same Source.",
            },
        ]

        result = processor.generate_sources_section(citations)

        # Should only appear once
        assert result.count("Same Source.") == 1


class TestFormatSourcesSection:
    """Test format_sources_section method for legacy formatting."""

    @staticmethod
    def _create_minimal_context(**kwargs):
        """Helper to create PersonContext with minimal required fields."""
        from rmagent.generators.biography.models import PersonContext

        defaults = {
            "person_id": 1,
            "full_name": "Test Person",
            "given_name": "Test",
            "surname": "Person",
            "prefix": None,
            "suffix": None,
            "nickname": None,
            "birth_year": None,
            "birth_date": None,
            "birth_place": None,
            "death_year": None,
            "death_date": None,
            "death_place": None,
            "sex": 2,  # Unknown
            "is_private": False,
            "is_living": False,
        }
        defaults.update(kwargs)
        return PersonContext(**defaults)

    def test_format_footnote_style(self):
        """Test formatting sources in footnote style."""
        processor = CitationProcessor()
        context = self._create_minimal_context(
            all_citations=[
                {"SourceName": "Book: Family History", "CitationName": "Page 42"},
            ]
        )

        result = processor.format_sources_section(context, CitationStyle.FOOTNOTE)

        assert "1. *Family History*" in result  # Prefix stripped
        assert "   Page 42" in result

    def test_format_parenthetical_style(self):
        """Test formatting sources in parenthetical style."""
        processor = CitationProcessor()
        context = self._create_minimal_context(
            all_citations=[
                {"SourceName": "Newspaper: Daily News", "CitationName": "1950-01-01"},
            ]
        )

        result = processor.format_sources_section(context, CitationStyle.PARENTHETICAL)

        assert "- *Daily News*" in result  # Prefix stripped
        assert "  (1950-01-01)" in result

    def test_format_narrative_style(self):
        """Test formatting sources in narrative style."""
        processor = CitationProcessor()
        context = self._create_minimal_context(
            all_citations=[
                {"SourceName": "Census Records", "CitationName": ""},
            ]
        )

        result = processor.format_sources_section(context, CitationStyle.NARRATIVE)

        assert "- *Census Records*" in result

    def test_format_no_citations(self):
        """Test formatting with no citations returns empty string."""
        processor = CitationProcessor()
        context = self._create_minimal_context(all_citations=[])

        result = processor.format_sources_section(context, CitationStyle.FOOTNOTE)

        assert result == ""
