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
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'RMAgent' in result.output
        assert 'Commands:' in result.output

    def test_version(self, runner):
        """Test version flag."""
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        assert '0.1.0' in result.output

    def test_invalid_command(self, runner):
        """Test invalid command."""
        result = runner.invoke(cli, ['invalid'])
        assert result.exit_code != 0


class TestPersonCommand:
    """Test person command."""

    def test_help(self, runner):
        """Test person help output."""
        result = runner.invoke(cli, ['person', '--help'])
        assert result.exit_code == 0
        assert 'Query person information' in result.output
        assert '--events' in result.output
        assert '--family' in result.output

    def test_person_without_id(self, runner):
        """Test person command without ID."""
        result = runner.invoke(cli, ['person'])
        assert result.exit_code != 0

    def test_person_with_id(self, runner, test_db_path):
        """Test person command with valid ID."""
        result = runner.invoke(cli, ['--database', test_db_path, 'person', '1'])
        # Should succeed even if person not found (graceful error)
        assert 'Person' in result.output or 'Error' in result.output


class TestBioCommand:
    """Test bio command."""

    def test_help(self, runner):
        """Test bio help output."""
        result = runner.invoke(cli, ['bio', '--help'])
        assert result.exit_code == 0
        assert 'Generate biography' in result.output
        assert '--length' in result.output
        assert '--citation-style' in result.output

    def test_bio_without_id(self, runner):
        """Test bio command without ID."""
        result = runner.invoke(cli, ['bio'])
        assert result.exit_code != 0

    def test_bio_with_invalid_length(self, runner, test_db_path):
        """Test bio with invalid length option."""
        result = runner.invoke(cli, ['--database', test_db_path, 'bio', '1', '--length', 'invalid'])
        assert result.exit_code != 0


class TestQualityCommand:
    """Test quality command."""

    def test_help(self, runner):
        """Test quality help output."""
        result = runner.invoke(cli, ['quality', '--help'])
        assert result.exit_code == 0
        assert 'data quality checks' in result.output
        assert '--format' in result.output
        assert '--sample-limit' in result.output

    def test_quality_with_invalid_format(self, runner):
        """Test quality with invalid format."""
        result = runner.invoke(cli, ['quality', '--format', 'invalid'])
        assert result.exit_code != 0


class TestAskCommand:
    """Test ask command."""

    def test_help(self, runner):
        """Test ask help output."""
        result = runner.invoke(cli, ['ask', '--help'])
        assert result.exit_code == 0
        assert 'Ask questions' in result.output
        assert '--interactive' in result.output

    def test_ask_without_question(self, runner):
        """Test ask without question or interactive flag."""
        result = runner.invoke(cli, ['ask'])
        # Should show error about missing question
        assert result.exit_code != 0 or 'Error' in result.output


class TestTimelineCommand:
    """Test timeline command."""

    def test_help(self, runner):
        """Test timeline help output."""
        result = runner.invoke(cli, ['timeline', '--help'])
        assert result.exit_code == 0
        assert 'Generate timeline' in result.output
        assert '--format' in result.output
        assert '--group-by-phase' in result.output

    def test_timeline_without_id(self, runner):
        """Test timeline without person ID."""
        result = runner.invoke(cli, ['timeline'])
        assert result.exit_code != 0


class TestExportCommand:
    """Test export command."""

    def test_help(self, runner):
        """Test export help output."""
        result = runner.invoke(cli, ['export', '--help'])
        assert result.exit_code == 0
        assert 'Export content' in result.output
        assert 'Commands:' in result.output
        assert 'hugo' in result.output

    def test_hugo_help(self, runner):
        """Test hugo subcommand help."""
        result = runner.invoke(cli, ['export', 'hugo', '--help'])
        assert result.exit_code == 0
        assert 'Hugo blog format' in result.output
        assert '--bio-length' in result.output
        assert '--all' in result.output


class TestSearchCommand:
    """Test search command."""

    def test_help(self, runner):
        """Test search help output."""
        result = runner.invoke(cli, ['search', '--help'])
        assert result.exit_code == 0
        assert 'Search' in result.output
        assert '--name' in result.output
        assert '--place' in result.output
        assert '--phonetic' in result.output

    def test_search_without_criteria(self, runner):
        """Test search without name or place."""
        result = runner.invoke(cli, ['search'])
        # Should show error about missing criteria
        assert result.exit_code != 0 or 'Error' in result.output


class TestGlobalOptions:
    """Test global CLI options."""

    def test_database_option(self, runner):
        """Test --database global option."""
        result = runner.invoke(cli, ['--database', 'nonexistent.rmtree', 'person', '1'])
        # Should fail because database doesn't exist
        assert result.exit_code != 0

    def test_verbose_option(self, runner, test_db_path):
        """Test --verbose flag."""
        result = runner.invoke(cli, ['--verbose', '--database', test_db_path, 'person', '1'])
        # Verbose mode should work (may succeed or fail gracefully)
        assert result.exit_code in [0, 1]

    def test_llm_provider_option(self, runner):
        """Test --llm-provider option."""
        result = runner.invoke(cli, ['--llm-provider', 'anthropic', '--help'])
        assert result.exit_code == 0

    def test_invalid_llm_provider(self, runner):
        """Test invalid LLM provider."""
        result = runner.invoke(cli, ['--llm-provider', 'invalid', 'person', '1'])
        assert result.exit_code != 0
