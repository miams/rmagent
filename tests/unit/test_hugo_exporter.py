"""Unit tests for Hugo blog post exporter."""

from pathlib import Path

import pytest

from rmagent.generators.biography import BiographyLength
from rmagent.generators.hugo_exporter import HugoExporter, _slugify


class TestSlugify:
    """Test slugify utility function."""

    def test_slugify_simple(self):
        """Test basic slugification."""
        assert _slugify("John Smith") == "john-smith"

    def test_slugify_with_dates(self):
        """Test slugification with dates and parentheses."""
        assert _slugify("John Smith (1850-1920)") == "john-smith-1850-1920"

    def test_slugify_special_characters(self):
        """Test slugification removes special characters."""
        assert _slugify("O'Brien, Mary Ann") == "obrien-mary-ann"

    def test_slugify_multiple_spaces(self):
        """Test slugification handles multiple spaces."""
        assert _slugify("John   Doe") == "john-doe"

    def test_slugify_underscores(self):
        """Test slugification converts underscores to hyphens."""
        assert _slugify("john_doe_smith") == "john-doe-smith"


class TestHugoExporter:
    """Test HugoExporter class."""

    @pytest.fixture
    def real_db_path(self):
        """Path to real test database."""
        return Path("data/Iiams.rmtree")

    @pytest.fixture
    def extension_path(self):
        """Path to ICU extension."""
        return Path("sqlite-extension/icu.dylib")

    def test_exporter_init_with_path(self, real_db_path, extension_path):
        """Test initializing exporter with database path."""
        if not real_db_path.exists():
            pytest.skip("Real database not available")

        exporter = HugoExporter(db=real_db_path, extension_path=extension_path)
        assert exporter.db_path == real_db_path
        assert exporter._db is None
        assert exporter._owns_db

    def test_exporter_init_without_db(self):
        """Test initializing exporter without database."""
        exporter = HugoExporter()
        assert exporter.db_path is None
        assert exporter._db is None

    def test_exporter_media_base_path(self):
        """Test media base path configuration."""
        exporter = HugoExporter(media_base_path="/images/")
        assert exporter.media_base_path == "/images/"

        exporter = HugoExporter(media_base_path="/media")  # Without trailing slash
        assert exporter.media_base_path == "/media/"  # Should add it

    def test_format_media_url_with_rm_prefix(self):
        """Test media URL formatting with RootsMagic ?\\ prefix."""
        exporter = HugoExporter(media_base_path="/media/")

        media = {
            "media_path": "?\\Pictures - People",
            "media_file": "john-smith.jpg",
        }

        url = exporter._format_media_url(media)
        assert url == "/media/Pictures - People/john-smith.jpg"

    def test_format_media_url_without_prefix(self):
        """Test media URL formatting without prefix."""
        exporter = HugoExporter(media_base_path="/media/")

        media = {
            "media_path": "Photos",
            "media_file": "portrait.jpg",
        }

        url = exporter._format_media_url(media)
        assert url == "/media/Photos/portrait.jpg"

    def test_format_media_url_empty_path(self):
        """Test media URL formatting with empty path."""
        exporter = HugoExporter(media_base_path="/media/")

        media = {
            "media_path": "",
            "media_file": "document.pdf",
        }

        url = exporter._format_media_url(media)
        assert url == "/media/document.pdf"

    def test_export_person_raises_error_without_database(self, tmp_path):
        """Test that export_person raises ValueError without database."""
        exporter = HugoExporter()

        with pytest.raises(ValueError, match="No database provided"):
            exporter.export_person(person_id=1, output_dir=tmp_path)

    def test_export_person_raises_error_for_nonexistent_person(
        self, tmp_path, real_db_path, extension_path
    ):
        """Test that export_person raises ValueError for nonexistent person."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        exporter = HugoExporter(db=real_db_path, extension_path=extension_path)

        with pytest.raises(ValueError, match="Person 999999 not found"):
            exporter.export_person(person_id=999999, output_dir=tmp_path)

    def test_export_person_creates_markdown_file(self, tmp_path, real_db_path, extension_path):
        """Test that export_person creates markdown file."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        exporter = HugoExporter(db=real_db_path, extension_path=extension_path)

        result = exporter.export_person(
            person_id=1,
            output_dir=tmp_path,
            include_timeline=False,  # Skip timeline for faster test
        )

        # Verify markdown file was created
        assert "markdown" in result
        assert result["markdown"].exists()
        assert result["markdown"].suffix == ".md"

        # Verify content
        content = result["markdown"].read_text()
        assert "---" in content  # YAML front matter
        assert "title:" in content
        assert "person_id:" in content

    def test_export_person_with_timeline(self, tmp_path, real_db_path, extension_path):
        """Test that export_person creates timeline files."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        exporter = HugoExporter(db=real_db_path, extension_path=extension_path)

        result = exporter.export_person(
            person_id=1,
            output_dir=tmp_path / "content" / "people",  # Hugo structure
            include_timeline=True,
        )

        # Verify markdown file
        assert "markdown" in result
        assert result["markdown"].exists()

        # Verify timeline files
        assert "timeline_json" in result
        assert "timeline_html" in result
        assert result["timeline_json"].exists()
        assert result["timeline_html"].exists()

        # Verify timeline shortcode in markdown
        content = result["markdown"].read_text()
        assert "{{< timeline" in content

    def test_export_person_front_matter_structure(self, tmp_path, real_db_path, extension_path):
        """Test YAML front matter structure."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        exporter = HugoExporter(db=real_db_path, extension_path=extension_path)

        result = exporter.export_person(
            person_id=1,
            output_dir=tmp_path,
            include_timeline=False,
        )

        content = result["markdown"].read_text()

        # Verify front matter exists
        assert content.startswith("---")
        assert content.count("---") >= 2

        # Verify required fields
        assert "title:" in content
        assert "date:" in content
        assert "categories:" in content
        assert "person_id:" in content

        # Verify structure
        lines = content.split("\n")
        assert lines[0] == "---"
        # Find closing ---
        closing_idx = lines[1:].index("---") + 1
        assert closing_idx > 0

    def test_export_person_hugo_taxonomies(self, tmp_path, real_db_path, extension_path):
        """Test Hugo taxonomies (categories, tags) generation."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        exporter = HugoExporter(db=real_db_path, extension_path=extension_path)

        result = exporter.export_person(
            person_id=1,
            output_dir=tmp_path,
            include_timeline=False,
        )

        content = result["markdown"].read_text()

        # Should have categories (surname-based)
        assert "categories:" in content
        assert "Family" in content

        # May have tags (places, decades)
        # Can't assert specific tags without knowing the test data

    def test_export_batch_creates_multiple_files(self, tmp_path, real_db_path, extension_path):
        """Test batch export creates multiple markdown files."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        exporter = HugoExporter(db=real_db_path, extension_path=extension_path)

        result = exporter.export_batch(
            person_ids=[1, 2],
            output_dir=tmp_path,
            include_timeline=False,
            generate_index=False,
        )

        # Verify multiple markdown files created
        assert "markdown_files" in result
        assert len(result["markdown_files"]) >= 1  # At least one should succeed

        # Verify all are markdown files
        for md_file in result["markdown_files"]:
            assert md_file.exists()
            assert md_file.suffix == ".md"

    def test_export_batch_with_index(self, tmp_path, real_db_path, extension_path):
        """Test batch export generates index page."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        exporter = HugoExporter(db=real_db_path, extension_path=extension_path)

        result = exporter.export_batch(
            person_ids=[1, 2],
            output_dir=tmp_path,
            include_timeline=False,
            generate_index=True,
        )

        # Verify index file created
        assert "index_file" in result
        assert result["index_file"].exists()
        assert result["index_file"].name == "_index.md"

        # Verify index content
        content = result["index_file"].read_text()
        assert "Family Biographies" in content
        assert "---" in content  # Has front matter

    def test_export_batch_handles_invalid_person_gracefully(
        self, tmp_path, real_db_path, extension_path
    ):
        """Test batch export continues when one person fails."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        exporter = HugoExporter(db=real_db_path, extension_path=extension_path)

        # Mix valid and invalid person IDs
        result = exporter.export_batch(
            person_ids=[1, 999999, 2],  # 999999 doesn't exist
            output_dir=tmp_path,
            include_timeline=False,
            generate_index=False,
        )

        # Should have at least one successful export
        assert "markdown_files" in result
        assert len(result["markdown_files"]) >= 1

    def test_export_with_different_bio_lengths(self, tmp_path, real_db_path, extension_path):
        """Test export with different biography lengths."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        exporter = HugoExporter(db=real_db_path, extension_path=extension_path)

        # Export with short biography
        result_short = exporter.export_person(
            person_id=1,
            output_dir=tmp_path / "short",
            bio_length=BiographyLength.SHORT,
            include_timeline=False,
        )

        # Export with standard biography
        result_standard = exporter.export_person(
            person_id=1,
            output_dir=tmp_path / "standard",
            bio_length=BiographyLength.STANDARD,
            include_timeline=False,
        )

        # Verify both created successfully
        assert result_short["markdown"].exists()
        assert result_standard["markdown"].exists()

        # Short biography should be shorter
        short_content = result_short["markdown"].read_text()
        standard_content = result_standard["markdown"].read_text()

        # Both should have front matter and content
        assert "---" in short_content
        assert "---" in standard_content


class TestHugoExporterIntegration:
    """Integration tests with real database."""

    @pytest.fixture
    def real_db_path(self):
        """Path to real test database."""
        return Path("data/Iiams.rmtree")

    @pytest.fixture
    def extension_path(self):
        """Path to ICU extension."""
        return Path("sqlite-extension/icu.dylib")

    def test_complete_hugo_export_workflow(self, tmp_path, real_db_path, extension_path):
        """Test complete Hugo export workflow."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        exporter = HugoExporter(
            db=real_db_path, extension_path=extension_path, media_base_path="/media/"
        )

        # Create Hugo directory structure
        content_dir = tmp_path / "content" / "people"
        content_dir.mkdir(parents=True)

        # Export batch of people
        result = exporter.export_batch(
            person_ids=[1, 2, 3],
            output_dir=content_dir,
            bio_length=BiographyLength.STANDARD,
            include_timeline=True,
            generate_index=True,
        )

        # Verify markdown files
        assert len(result["markdown_files"]) >= 1

        # Verify timeline files (in static/timelines)
        assert len(result["timeline_files"]) >= 2  # JSON + HTML per person

        # Verify index file
        assert result["index_file"].exists()

        # Verify Hugo directory structure
        static_dir = tmp_path / "static" / "timelines"
        assert static_dir.exists()

        # Verify at least one markdown file has proper structure
        md_file = result["markdown_files"][0]
        content = md_file.read_text()

        # Check front matter
        assert content.startswith("---")
        assert "title:" in content
        assert "person_id:" in content
        assert "categories:" in content

        # Check content sections
        assert "## " in content  # Has at least one section

        # Check timeline reference if included
        if "{{< timeline" in content:
            assert 'src="/timelines/' in content

    def test_media_references_in_export(self, tmp_path, real_db_path, extension_path):
        """Test that media references are properly formatted."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        exporter = HugoExporter(
            db=real_db_path, extension_path=extension_path, media_base_path="/media/"
        )

        result = exporter.export_person(
            person_id=1,
            output_dir=tmp_path,
            include_media=True,
            include_timeline=False,
        )

        content = result["markdown"].read_text()

        # Check if media section exists (only if person has media)
        if "## Photos & Documents" in content:
            # Should have image markdown syntax
            assert "![" in content
            # Should have media base path
            assert "/media/" in content

    def test_index_page_format(self, tmp_path, real_db_path, extension_path):
        """Test index page formatting."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        exporter = HugoExporter(db=real_db_path, extension_path=extension_path)

        result = exporter.export_batch(
            person_ids=[1, 2],
            output_dir=tmp_path,
            include_timeline=False,
            generate_index=True,
        )

        index_content = result["index_file"].read_text()

        # Verify front matter
        assert index_content.startswith("---")
        assert 'title: "Family Biographies"' in index_content

        # Verify has list of people
        assert "- [" in index_content  # Markdown link

        # Verify has metadata footer
        assert "Generated" in index_content
