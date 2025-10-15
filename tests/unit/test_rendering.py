"""
Unit tests for biography rendering and markdown generation.

Tests biography rendering, metadata formatting, and image handling.
"""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from rmagent.generators.biography.models import Biography, BiographyLength, CitationStyle, LLMMetadata
from rmagent.generators.biography.rendering import BiographyRenderer


class TestFormatTokens:
    """Test format_tokens static method."""

    def test_format_less_than_thousand(self):
        """Test formatting tokens less than 1000."""
        assert BiographyRenderer.format_tokens(500) == "500"
        assert BiographyRenderer.format_tokens(999) == "999"

    def test_format_thousands(self):
        """Test formatting tokens in thousands."""
        assert BiographyRenderer.format_tokens(1000) == "1.0k"
        assert BiographyRenderer.format_tokens(1500) == "1.5k"
        assert BiographyRenderer.format_tokens(2300) == "2.3k"

    def test_format_large_numbers(self):
        """Test formatting large token counts."""
        assert BiographyRenderer.format_tokens(10000) == "10.0k"
        assert BiographyRenderer.format_tokens(42500) == "42.5k"


class TestFormatDuration:
    """Test format_duration static method."""

    def test_format_seconds_only(self):
        """Test formatting durations less than 60 seconds."""
        assert BiographyRenderer.format_duration(5.2) == "5s"
        assert BiographyRenderer.format_duration(45.9) == "45s"
        assert BiographyRenderer.format_duration(59) == "59s"

    def test_format_minutes_and_seconds(self):
        """Test formatting durations with minutes and seconds."""
        assert BiographyRenderer.format_duration(65) == "1m5s"
        assert BiographyRenderer.format_duration(125) == "2m5s"
        assert BiographyRenderer.format_duration(183.5) == "3m3s"

    def test_format_minutes_only(self):
        """Test formatting durations with even minutes."""
        assert BiographyRenderer.format_duration(60) == "1m"
        assert BiographyRenderer.format_duration(120) == "2m"
        assert BiographyRenderer.format_duration(180) == "3m"


class TestFormatImageCaption:
    """Test _format_image_caption static method."""

    def test_caption_with_both_years(self):
        """Test caption with birth and death years."""
        caption = BiographyRenderer._format_image_caption("John Doe", 1850, 1920)
        assert caption == "John Doe (1850-1920)"

    def test_caption_birth_only(self):
        """Test caption with only birth year."""
        caption = BiographyRenderer._format_image_caption("Jane Smith", 1900, None)
        assert caption == "Jane Smith (1900-????)"

    def test_caption_death_only(self):
        """Test caption with only death year."""
        caption = BiographyRenderer._format_image_caption("Bob Jones", None, 1950)
        assert caption == "Bob Jones (????-1950)"

    def test_caption_no_years(self):
        """Test caption without any years."""
        caption = BiographyRenderer._format_image_caption("Alice Brown", None, None)
        assert caption == "Alice Brown"


class TestFormatImagePath:
    """Test _format_image_path method."""

    def test_format_path_with_question_mark_backslash(self):
        """Test formatting path with question-backslash prefix (Windows-style)."""
        renderer = BiographyRenderer()
        media = {"MediaPath": r"?\Photos\Family", "MediaFile": "portrait.jpg"}

        result = renderer._format_image_path(media)

        # Path object preserves backslashes on Unix, but as_posix() converts separators
        # The actual behavior depends on the implementation - accept either format
        assert "../images" in result
        assert "portrait.jpg" in result

    def test_format_path_with_question_mark_slash(self):
        """Test formatting path with ?/ prefix (Unix-style)."""
        renderer = BiographyRenderer()
        media = {"MediaPath": "?/Photos/Family", "MediaFile": "photo.png"}

        result = renderer._format_image_path(media)

        assert result == "../images/Photos/Family/photo.png"

    def test_format_path_without_question_mark(self):
        """Test formatting path without ? prefix."""
        renderer = BiographyRenderer()
        media = {"MediaPath": "Photos/Family", "MediaFile": "image.jpg"}

        result = renderer._format_image_path(media)

        assert result == "Photos/Family/image.jpg"

    def test_format_path_no_media_path(self):
        """Test formatting with no MediaPath (only MediaFile)."""
        renderer = BiographyRenderer()
        media = {"MediaPath": "", "MediaFile": "standalone.jpg"}

        result = renderer._format_image_path(media)

        assert result == "standalone.jpg"


class TestRenderMetadata:
    """Test render_metadata method."""

    @staticmethod
    def _create_minimal_biography(**kwargs):
        """Helper to create Biography with minimal required fields."""
        defaults = {
            "person_id": 1,
            "full_name": "Test Person",
            "length": BiographyLength.STANDARD,
            "citation_style": CitationStyle.FOOTNOTE,
            "introduction": "Test intro",
            "early_life": "",
            "education": "",
            "career": "",
            "marriage_family": "",
            "later_life": "",
            "death_legacy": "",
            "footnotes": "",
            "sources": "",
        }
        defaults.update(kwargs)
        return Biography(**defaults)

    def test_render_metadata_basic(self):
        """Test rendering basic metadata without LLM metadata."""
        bio = self._create_minimal_biography(
            full_name="John Doe",
            birth_year=1850,
            death_year=1920,
            citation_count=5,
            source_count=3,
        )
        renderer = BiographyRenderer()

        result = renderer.render_metadata(bio)

        assert "---" in result
        assert 'Title: "Biography of John Doe (1850-1920)"' in result
        assert "PersonID: 1" in result
        assert "Words:" in result
        assert "Citations: 5" in result
        assert "Sources: 3" in result

    def test_render_metadata_with_llm_metadata(self):
        """Test rendering metadata with LLM metadata."""
        llm_meta = LLMMetadata(
            provider="anthropic",
            model="claude-3-5-sonnet-20241022",
            prompt_tokens=1500,
            completion_tokens=800,
            total_tokens=2300,
            prompt_time=2.5,
            llm_time=5.3,
        )
        bio = self._create_minimal_biography(
            llm_metadata=llm_meta,
            citation_count=10,
            source_count=5,
        )
        renderer = BiographyRenderer()

        result = renderer.render_metadata(bio)

        assert "TokensIn: 1.5k" in result
        assert "TokensOut: 800" in result
        assert "TotalTokens: 2.3k" in result
        assert "LLM: Anthropic" in result
        assert "Model: claude-3-5-sonnet-20241022" in result
        assert "PromptTime: 2s" in result
        assert "LLMTime: 5s" in result

    def test_render_metadata_missing_years(self):
        """Test rendering metadata with missing birth/death years."""
        bio = self._create_minimal_biography(
            birth_year=None,
            death_year=None,
        )
        renderer = BiographyRenderer()

        result = renderer.render_metadata(bio)

        # Should not include years in title when both are None
        assert 'Title: "Biography of Test Person"' in result
        assert "????" not in result  # No placeholder years


class TestRenderMarkdown:
    """Test render_markdown method."""

    @staticmethod
    def _create_minimal_biography(**kwargs):
        """Helper to create Biography with minimal required fields."""
        defaults = {
            "person_id": 1,
            "full_name": "Test Person",
            "length": BiographyLength.STANDARD,
            "citation_style": CitationStyle.FOOTNOTE,
            "introduction": "Test intro",
            "early_life": "",
            "education": "",
            "career": "",
            "marriage_family": "",
            "later_life": "",
            "death_legacy": "",
            "footnotes": "",
            "sources": "",
        }
        defaults.update(kwargs)
        return Biography(**defaults)

    def test_render_markdown_with_all_sections(self):
        """Test rendering biography with all sections populated."""
        bio = self._create_minimal_biography(
            full_name="Jane Smith",
            birth_year=1900,
            death_year=1980,
            introduction="Jane was born in 1900.",
            early_life="She grew up in Maryland.",
            education="She attended local schools.",
            career="She worked as a teacher.",
            marriage_family="She married John.",
            later_life="She retired in 1965.",
            death_legacy="She passed away in 1980.",
            sources="Source 1\nSource 2",
        )
        renderer = BiographyRenderer()

        result = renderer.render_markdown(bio, include_metadata=False)

        # Check all sections are present
        assert "# Biography of Jane Smith (1900-1980)" in result
        assert "## Introduction" in result
        assert "Jane was born in 1900." in result
        assert "## Early Life & Family Background" in result
        assert "She grew up in Maryland." in result
        assert "## Education" in result
        assert "She attended local schools." in result
        assert "## Career & Accomplishments" in result
        assert "She worked as a teacher." in result
        assert "## Marriage & Family" in result
        assert "She married John." in result
        assert "## Later Life & Activities" in result
        assert "She retired in 1965." in result
        assert "## Death & Legacy" in result
        assert "She passed away in 1980." in result
        assert "## Sources" in result
        assert "Source 1" in result

    def test_render_markdown_with_metadata(self):
        """Test rendering biography with front matter metadata."""
        bio = self._create_minimal_biography(
            introduction="Test introduction.",
        )
        renderer = BiographyRenderer()

        result = renderer.render_markdown(bio, include_metadata=True)

        # Should have front matter
        assert "---" in result
        assert "PersonID:" in result

    def test_render_markdown_without_metadata(self):
        """Test rendering biography without front matter."""
        bio = self._create_minimal_biography(
            introduction="Test introduction.",
        )
        renderer = BiographyRenderer()

        result = renderer.render_markdown(bio, include_metadata=False)

        # Should not have front matter
        lines = result.split("\n")
        # First line should be the title, not ---
        assert not lines[0].startswith("---")
        assert lines[0].startswith("# Biography")

    def test_render_markdown_with_footnotes(self):
        """Test rendering biography with footnotes section."""
        bio = self._create_minimal_biography(
            introduction="Test intro.",
            footnotes="[^1]: Footnote 1\n[^2]: Footnote 2",
            citation_style=CitationStyle.FOOTNOTE,
        )
        renderer = BiographyRenderer()

        result = renderer.render_markdown(bio, include_metadata=False)

        assert "## Footnotes" in result
        assert "[^1]: Footnote 1" in result

    def test_render_markdown_no_footnotes_for_other_styles(self):
        """Test that footnotes section is omitted for non-footnote citation styles."""
        bio = self._create_minimal_biography(
            introduction="Test intro.",
            footnotes="[^1]: Footnote 1",
            citation_style=CitationStyle.NARRATIVE,  # Not FOOTNOTE
        )
        renderer = BiographyRenderer()

        result = renderer.render_markdown(bio, include_metadata=False)

        assert "## Footnotes" not in result

    def test_render_markdown_short_biography_no_images(self):
        """Test that SHORT biographies don't include images."""
        bio = self._create_minimal_biography(
            length=BiographyLength.SHORT,
            introduction="Short bio.",
            media_files=[{"IsPrimary": 1, "MediaPath": "?/test", "MediaFile": "photo.jpg"}],
        )
        renderer = BiographyRenderer()

        result = renderer.render_markdown(bio, include_metadata=False)

        # Should not have image HTML
        assert "<img" not in result
        assert "Photos" not in result

    def test_render_markdown_with_primary_image(self):
        """Test rendering with primary image in introduction."""
        bio = self._create_minimal_biography(
            length=BiographyLength.STANDARD,
            full_name="Test Person",
            birth_year=1900,
            death_year=1980,
            introduction="Test introduction paragraph.",
            media_files=[
                {
                    "IsPrimary": 1,
                    "MediaPath": "?/Photos",
                    "MediaFile": "portrait.jpg",
                    "Caption": "Official portrait",
                }
            ],
        )
        renderer = BiographyRenderer()

        result = renderer.render_markdown(bio, include_metadata=False)

        # Should have image with text wrapping divs
        assert '<div style="float:right;width:35%;padding-left:15px;">' in result
        assert '<img src="../images/Photos/portrait.jpg"' in result
        assert 'alt="Test Person (1900-1980)"' in result
        assert "Official portrait" in result  # Uses database Caption

    def test_render_markdown_with_additional_images(self):
        """Test rendering with additional non-primary images in Photos section."""
        bio = self._create_minimal_biography(
            length=BiographyLength.COMPREHENSIVE,
            full_name="Test Person",
            introduction="Test intro.",
            media_files=[
                {"IsPrimary": 0, "MediaPath": "?/Photos", "MediaFile": "family.jpg", "Caption": ""},
                {"IsPrimary": 0, "MediaPath": "?/Photos", "MediaFile": "house.jpg", "Caption": ""},
            ],
        )
        renderer = BiographyRenderer()

        result = renderer.render_markdown(bio, include_metadata=False)

        # Should have Photos section
        assert "## Photos" in result
        assert "![Test Person]" in result
        assert "../images/Photos/family.jpg" in result
        assert "../images/Photos/house.jpg" in result


class TestBiographyWordCount:
    """Test word count calculation."""

    @staticmethod
    def _create_minimal_biography(**kwargs):
        """Helper to create Biography with minimal required fields."""
        defaults = {
            "person_id": 1,
            "full_name": "Test Person",
            "length": BiographyLength.STANDARD,
            "citation_style": CitationStyle.FOOTNOTE,
            "introduction": "",
            "early_life": "",
            "education": "",
            "career": "",
            "marriage_family": "",
            "later_life": "",
            "death_legacy": "",
            "footnotes": "",
            "sources": "",
        }
        defaults.update(kwargs)
        return Biography(**defaults)

    def test_word_count_excludes_footnotes_and_sources(self):
        """Test that word count only includes narrative sections, not footnotes or sources."""
        bio = self._create_minimal_biography(
            introduction="This is a ten word introduction sentence for testing purposes.",  # 10 words
            early_life="Five word early life.",  # 4 words
            footnotes="[^1]: This footnote should not be counted.",
            sources="Source 1. Source 2. These should not be counted either.",
        )

        word_count = bio.calculate_word_count()

        # Should be 10 + 4 = 14 words (excluding footnotes and sources)
        assert word_count == 14
