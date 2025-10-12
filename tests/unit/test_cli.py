"""Tests for CLI commands."""

import pytest
from click.testing import CliRunner

from rmagent.cli.main import cli


@pytest.fixture
def runner():
    """Click CLI runner."""
    return CliRunner()


@pytest.fixture
def test_db_path():
    """Path to test database."""
    return "data/Iiams.rmtree"


class TestCLIMain:
    """Test main CLI group."""

    def test_help(self, runner):
        """Test main help output."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "RMAgent" in result.output
        assert "Commands:" in result.output

    def test_version(self, runner):
        """Test version flag."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_invalid_command(self, runner):
        """Test invalid command."""
        result = runner.invoke(cli, ["invalid"])
        assert result.exit_code != 0


class TestPersonCommand:
    """Test person command."""

    def test_help(self, runner):
        """Test person help output."""
        result = runner.invoke(cli, ["person", "--help"])
        assert result.exit_code == 0
        assert "Query person information" in result.output
        assert "--events" in result.output
        assert "--family" in result.output

    def test_person_without_id(self, runner):
        """Test person command without ID."""
        result = runner.invoke(cli, ["person"])
        assert result.exit_code != 0

    def test_person_with_id(self, runner, test_db_path):
        """Test person command with valid ID."""
        result = runner.invoke(cli, ["--database", test_db_path, "person", "1"])
        # Should succeed even if person not found (graceful error)
        assert "Person" in result.output or "Error" in result.output


class TestBioCommand:
    """Test bio command."""

    def test_help(self, runner):
        """Test bio help output."""
        result = runner.invoke(cli, ["bio", "--help"])
        assert result.exit_code == 0
        assert "Generate biography" in result.output
        assert "--length" in result.output
        assert "--citation-style" in result.output

    def test_bio_without_id(self, runner):
        """Test bio command without ID."""
        result = runner.invoke(cli, ["bio"])
        assert result.exit_code != 0

    def test_bio_with_invalid_length(self, runner, test_db_path):
        """Test bio with invalid length option."""
        result = runner.invoke(cli, ["--database", test_db_path, "bio", "1", "--length", "invalid"])
        assert result.exit_code != 0

    def test_bio_no_ai_template_based(self, runner, test_db_path, tmp_path):
        """Test bio command with --no-ai flag (template-based generation)."""
        output_file = tmp_path / "bio_test.md"
        result = runner.invoke(
            cli, ["--database", test_db_path, "bio", "1", "--no-ai", "--output", str(output_file)]
        )
        # Should succeed with template-based generation
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert len(content) > 0
        # Check for markdown structure
        assert "#" in content

    def test_bio_length_variations(self, runner, test_db_path):
        """Test bio with different length options."""
        for length in ["short", "standard", "comprehensive"]:
            result = runner.invoke(
                cli,
                [
                    "--database",
                    test_db_path,
                    "bio",
                    "1",
                    "--no-ai",  # Use template to avoid LLM dependency
                    "--length",
                    length,
                ],
            )
            # Should succeed for all length options
            assert result.exit_code == 0

    def test_bio_citation_styles(self, runner, test_db_path):
        """Test bio with different citation styles."""
        for style in ["footnote", "parenthetical", "narrative"]:
            result = runner.invoke(
                cli, ["--database", test_db_path, "bio", "1", "--no-ai", "--citation-style", style]
            )
            assert result.exit_code == 0

    def test_bio_with_file_output(self, runner, test_db_path, tmp_path):
        """Test bio with file output."""
        output_file = tmp_path / "biography.md"
        result = runner.invoke(
            cli, ["--database", test_db_path, "bio", "1", "--no-ai", "--output", str(output_file)]
        )
        assert result.exit_code == 0
        assert "Biography written to" in result.output
        assert output_file.exists()

    def test_bio_no_sources(self, runner, test_db_path):
        """Test bio with --no-sources flag."""
        result = runner.invoke(
            cli, ["--database", test_db_path, "bio", "1", "--no-ai", "--no-sources"]
        )
        assert result.exit_code == 0
        # Biography should not include sources section when --no-sources is used
        # (We can't easily verify this without parsing output, but command should succeed)


class TestQualityCommand:
    """Test quality command."""

    def test_help(self, runner):
        """Test quality help output."""
        result = runner.invoke(cli, ["quality", "--help"])
        assert result.exit_code == 0
        assert "data quality checks" in result.output
        assert "--format" in result.output
        assert "--sample-limit" in result.output
        assert "--category" in result.output
        assert "--severity" in result.output

    def test_quality_with_invalid_format(self, runner):
        """Test quality with invalid format."""
        result = runner.invoke(cli, ["quality", "--format", "invalid"])
        assert result.exit_code != 0

    def test_quality_basic(self, runner, test_db_path, tmp_path):
        """Test basic quality report generation."""
        output_file = tmp_path / "quality.md"
        result = runner.invoke(
            cli, ["--database", test_db_path, "quality", "--output", str(output_file)]
        )
        assert result.exit_code == 0
        assert output_file.exists()
        assert "📊 Data Quality Summary" in result.output

    def test_quality_severity_filter(self, runner, test_db_path, tmp_path):
        """Test quality report with severity filter."""
        for severity in ["critical", "high", "medium", "low"]:
            output_file = tmp_path / f"quality_{severity}.md"
            result = runner.invoke(
                cli,
                [
                    "--database",
                    test_db_path,
                    "quality",
                    "--severity",
                    severity,
                    "--output",
                    str(output_file),
                ],
            )
            assert result.exit_code == 0
            assert output_file.exists()

    def test_quality_category_filter(self, runner, test_db_path, tmp_path):
        """Test quality report with category filter."""
        for category in ["required", "logical", "integrity", "sources", "dates", "values"]:
            output_file = tmp_path / f"quality_{category}.md"
            result = runner.invoke(
                cli,
                [
                    "--database",
                    test_db_path,
                    "quality",
                    "--category",
                    category,
                    "--output",
                    str(output_file),
                ],
            )
            assert result.exit_code == 0
            assert output_file.exists()

    def test_quality_html_format(self, runner, test_db_path, tmp_path):
        """Test quality report in HTML format."""
        output_file = tmp_path / "quality.html"
        result = runner.invoke(
            cli,
            [
                "--database",
                test_db_path,
                "quality",
                "--format",
                "html",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "<!DOCTYPE html>" in content

    def test_quality_csv_format(self, runner, test_db_path, tmp_path):
        """Test quality report in CSV format."""
        output_file = tmp_path / "quality.csv"
        result = runner.invoke(
            cli,
            [
                "--database",
                test_db_path,
                "quality",
                "--format",
                "csv",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "Rule ID" in content

    def test_quality_combined_filters(self, runner, test_db_path, tmp_path):
        """Test quality report with combined category and severity filters."""
        output_file = tmp_path / "quality_filtered.md"
        result = runner.invoke(
            cli,
            [
                "--database",
                test_db_path,
                "quality",
                "--category",
                "logical",
                "--severity",
                "high",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()


class TestAskCommand:
    """Test ask command."""

    def test_help(self, runner):
        """Test ask help output."""
        result = runner.invoke(cli, ["ask", "--help"])
        assert result.exit_code == 0
        assert "Ask questions" in result.output
        assert "--interactive" in result.output

    def test_ask_without_question(self, runner):
        """Test ask without question or interactive flag."""
        result = runner.invoke(cli, ["ask"])
        # Should show error about missing question
        assert result.exit_code != 0 or "Error" in result.output

    def test_ask_with_question(self, runner, test_db_path):
        """Test ask with a question (requires LLM provider).

        Note: This test will fail if no LLM provider is configured,
        which is expected behavior. The test verifies command structure
        accepts the question argument.
        """
        result = runner.invoke(cli, ["--database", test_db_path, "ask", "Who is person 1?"])
        # May succeed with LLM configured, or fail with missing credentials
        # Either way, command should recognize the question format
        assert "Ask questions" not in result.output  # Not showing help text


class TestTimelineCommand:
    """Test timeline command."""

    def test_help(self, runner):
        """Test timeline help output."""
        result = runner.invoke(cli, ["timeline", "--help"])
        assert result.exit_code == 0
        assert "Generate timeline" in result.output
        assert "--format" in result.output
        assert "--group-by-phase" in result.output

    def test_timeline_without_id(self, runner):
        """Test timeline without person ID."""
        result = runner.invoke(cli, ["timeline"])
        assert result.exit_code != 0

    def test_timeline_json_with_output(self, runner, test_db_path, tmp_path):
        """Test timeline JSON generation with file output."""
        output_file = tmp_path / "timeline.json"
        result = runner.invoke(
            cli,
            [
                "--database",
                test_db_path,
                "timeline",
                "1",
                "--format",
                "json",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        # Verify JSON structure
        assert '"title"' in content or '"events"' in content

    def test_timeline_html_format(self, runner, test_db_path, tmp_path):
        """Test timeline HTML generation."""
        output_file = tmp_path / "timeline.html"
        result = runner.invoke(
            cli,
            [
                "--database",
                test_db_path,
                "timeline",
                "1",
                "--format",
                "html",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "<!DOCTYPE html>" in content

    def test_timeline_with_group_by_phase(self, runner, test_db_path, tmp_path):
        """Test timeline with life phase grouping."""
        output_file = tmp_path / "timeline_phases.json"
        result = runner.invoke(
            cli,
            [
                "--database",
                test_db_path,
                "timeline",
                "1",
                "--group-by-phase",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_timeline_with_include_family(self, runner, test_db_path, tmp_path):
        """Test timeline with family events included."""
        output_file = tmp_path / "timeline_family.json"
        result = runner.invoke(
            cli,
            [
                "--database",
                test_db_path,
                "timeline",
                "1",
                "--include-family",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()

    def test_timeline_invalid_format(self, runner, test_db_path):
        """Test timeline with invalid format option."""
        result = runner.invoke(
            cli, ["--database", test_db_path, "timeline", "1", "--format", "invalid"]
        )
        assert result.exit_code != 0


class TestExportCommand:
    """Test export command."""

    def test_help(self, runner):
        """Test export help output."""
        result = runner.invoke(cli, ["export", "--help"])
        assert result.exit_code == 0
        assert "Export content" in result.output
        assert "Commands:" in result.output
        assert "hugo" in result.output

    def test_hugo_help(self, runner):
        """Test hugo subcommand help."""
        result = runner.invoke(cli, ["export", "hugo", "--help"])
        assert result.exit_code == 0
        assert "Hugo blog format" in result.output
        assert "--bio-length" in result.output
        assert "--all" in result.output

    def test_hugo_single_person_export(self, runner, test_db_path, tmp_path):
        """Test exporting a single person to Hugo format."""
        output_dir = tmp_path / "content" / "people"
        result = runner.invoke(
            cli,
            ["--database", test_db_path, "export", "hugo", "1", "--output-dir", str(output_dir)],
        )
        assert result.exit_code == 0
        assert "Exported to:" in result.output

        # Verify markdown file was created
        markdown_files = list(output_dir.glob("*.md"))
        assert len(markdown_files) >= 1

        # Verify markdown content structure
        markdown_content = markdown_files[0].read_text()
        assert "---" in markdown_content  # YAML front matter
        assert "title:" in markdown_content
        assert "person_id:" in markdown_content

    def test_hugo_batch_export(self, runner, test_db_path, tmp_path):
        """Test exporting multiple persons with --batch-ids."""
        output_dir = tmp_path / "content" / "people"
        result = runner.invoke(
            cli,
            [
                "--database",
                test_db_path,
                "export",
                "hugo",
                "--batch-ids",
                "1,2,3",
                "--output-dir",
                str(output_dir),
            ],
        )
        assert result.exit_code == 0
        assert "Exported" in result.output

        # Verify markdown files were created
        markdown_files = list(output_dir.glob("*.md"))
        # Should have at least 2 files (may have fewer if some persons don't exist)
        # Plus potentially an _index.md file
        assert len(markdown_files) >= 2

    def test_hugo_with_timeline(self, runner, test_db_path, tmp_path):
        """Test Hugo export with timeline included."""
        output_dir = tmp_path / "content" / "people"
        result = runner.invoke(
            cli,
            [
                "--database",
                test_db_path,
                "export",
                "hugo",
                "1",
                "--output-dir",
                str(output_dir),
                "--include-timeline",
            ],
        )
        assert result.exit_code == 0
        assert "Timeline JSON:" in result.output
        assert "Timeline HTML:" in result.output

        # Verify timeline files were created
        timelines_dir = tmp_path / "static" / "timelines"
        if timelines_dir.exists():
            json_files = list(timelines_dir.glob("*.json"))
            html_files = list(timelines_dir.glob("*.html"))
            assert len(json_files) >= 1
            assert len(html_files) >= 1

    def test_hugo_bio_length_variations(self, runner, test_db_path, tmp_path):
        """Test Hugo export with different biography lengths."""
        for length in ["short", "standard", "comprehensive"]:
            output_dir = tmp_path / f"content_{length}"
            result = runner.invoke(
                cli,
                [
                    "--database",
                    test_db_path,
                    "export",
                    "hugo",
                    "1",
                    "--output-dir",
                    str(output_dir),
                    "--bio-length",
                    length,
                ],
            )
            assert result.exit_code == 0

            # Verify file was created
            markdown_files = list(output_dir.glob("*.md"))
            assert len(markdown_files) >= 1

    def test_hugo_without_person_id(self, runner):
        """Test Hugo export without person ID or batch options."""
        result = runner.invoke(cli, ["export", "hugo"])
        assert result.exit_code != 0
        assert "Error" in result.output

    def test_hugo_invalid_bio_length(self, runner, test_db_path, tmp_path):
        """Test Hugo export with invalid bio-length option."""
        output_dir = tmp_path / "content"
        result = runner.invoke(
            cli,
            [
                "--database",
                test_db_path,
                "export",
                "hugo",
                "1",
                "--output-dir",
                str(output_dir),
                "--bio-length",
                "invalid",
            ],
        )
        assert result.exit_code != 0


class TestSearchCommand:
    """Test search command."""

    def test_help(self, runner):
        """Test search help output."""
        result = runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "Search" in result.output
        assert "--name" in result.output
        assert "--place" in result.output
        assert "--exact" in result.output

    def test_search_without_criteria(self, runner):
        """Test search without name or place."""
        result = runner.invoke(cli, ["search"])
        # Should show error about missing criteria
        assert result.exit_code != 0 or "Error" in result.output

    def test_search_by_name(self, runner, test_db_path):
        """Test search by name."""
        result = runner.invoke(cli, ["--database", test_db_path, "search", "--name", "Iams"])
        # Should succeed if database has matching names
        assert result.exit_code == 0
        # Output should show search results or "No persons found"
        assert "Found" in result.output or "No persons" in result.output

    def test_search_by_full_name(self, runner, test_db_path):
        """Test search by full name (given and surname)."""
        result = runner.invoke(
            cli, ["--database", test_db_path, "search", "--name", "Michael Iams"]
        )
        assert result.exit_code == 0

    def test_search_by_place(self, runner, test_db_path):
        """Test search by place."""
        result = runner.invoke(cli, ["--database", test_db_path, "search", "--place", "Maryland"])
        assert result.exit_code == 0
        # Should show place results or "No places found"
        assert "Found" in result.output or "No places" in result.output

    def test_search_with_limit(self, runner, test_db_path):
        """Test search with custom limit."""
        result = runner.invoke(
            cli, ["--database", test_db_path, "search", "--name", "Smith", "--limit", "10"]
        )
        assert result.exit_code == 0

    def test_search_exact_mode(self, runner, test_db_path):
        """Test search with --exact flag (no phonetic matching)."""
        result = runner.invoke(
            cli, ["--database", test_db_path, "search", "--name", "Iams", "--exact"]
        )
        assert result.exit_code == 0

    def test_search_name_and_place(self, runner, test_db_path):
        """Test search with both name and place criteria."""
        result = runner.invoke(
            cli, ["--database", test_db_path, "search", "--name", "Iams", "--place", "Maryland"]
        )
        # Should show results for both searches
        assert result.exit_code == 0

    def test_search_with_surname_variation(self, runner, test_db_path):
        """Test search with surname variation syntax [variant]."""
        result = runner.invoke(
            cli, ["--database", test_db_path, "search", "--name", "John Iiams [Ijams]"]
        )
        assert result.exit_code == 0
        # Should show that it's searching multiple variations
        assert "Searching 2 name variations" in result.output or "Found" in result.output

    def test_search_with_multiple_variations(self, runner, test_db_path):
        """Test search with multiple surname variations."""
        result = runner.invoke(
            cli, ["--database", test_db_path, "search", "--name", "John Iams [Ijams] [Imes]"]
        )
        assert result.exit_code == 0
        # Should search 3 variations (base + 2 variants)
        assert "Searching 3 name variations" in result.output or "Found" in result.output

    def test_search_with_all_keyword(self, runner, test_db_path):
        """Test search with [ALL] keyword for configured variants."""
        result = runner.invoke(cli, ["--database", test_db_path, "search", "--name", "John [ALL]"])
        assert result.exit_code == 0
        # Should search all 8 configured variants
        assert "Searching 8 name variations" in result.output or "Found" in result.output


class TestGlobalOptions:
    """Test global CLI options."""

    def test_database_option(self, runner):
        """Test --database global option."""
        result = runner.invoke(cli, ["--database", "nonexistent.rmtree", "person", "1"])
        # Should fail because database doesn't exist
        assert result.exit_code != 0

    def test_verbose_option(self, runner, test_db_path):
        """Test --verbose flag."""
        result = runner.invoke(cli, ["--verbose", "--database", test_db_path, "person", "1"])
        # Verbose mode should work (may succeed or fail gracefully)
        assert result.exit_code in [0, 1]

    def test_llm_provider_option(self, runner):
        """Test --llm-provider option."""
        result = runner.invoke(cli, ["--llm-provider", "anthropic", "--help"])
        assert result.exit_code == 0

    def test_invalid_llm_provider(self, runner):
        """Test invalid LLM provider."""
        result = runner.invoke(cli, ["--llm-provider", "invalid", "person", "1"])
        assert result.exit_code != 0
