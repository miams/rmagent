"""Unit tests for quality report generator."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from rmtool.generators.quality_report import (
    QualityReportGenerator,
    ReportFormat,
)
from rmtool.rmlib.quality import (
    QualityIssue,
    QualityReport,
    QualitySeverity,
)


class TestReportFormat:
    """Test ReportFormat enum."""

    def test_format_values(self):
        """Test that all format values are defined."""
        assert ReportFormat.MARKDOWN.value == "markdown"
        assert ReportFormat.HTML.value == "html"
        assert ReportFormat.CSV.value == "csv"


class TestQualityReportGenerator:
    """Test QualityReportGenerator class."""

    @pytest.fixture
    def real_db_path(self):
        """Path to real test database."""
        return Path("data/Iiams.rmtree")

    @pytest.fixture
    def extension_path(self):
        """Path to ICU extension."""
        return Path("sqlite-extension/icu.dylib")

    @pytest.fixture
    def mock_quality_report(self):
        """Create a mock QualityReport for testing."""
        issues = [
            QualityIssue(
                rule_id="1.1",
                name="People without primary names",
                category="Required Fields",
                severity=QualitySeverity.CRITICAL,
                description="Every person must have a primary name.",
                count=5,
                samples=[
                    {"PersonID": 100, "Given": "", "Surname": ""},
                    {"PersonID": 200, "Given": "John", "Surname": ""},
                ],
            ),
            QualityIssue(
                rule_id="2.1",
                name="Death occurs before birth",
                category="Logical Consistency",
                severity=QualitySeverity.CRITICAL,
                description="Death date must be after birth date.",
                count=3,
                samples=[
                    {"PersonID": 300, "Given": "Jane", "Surname": "Doe"},
                ],
            ),
            QualityIssue(
                rule_id="4.1",
                name="Vital events without citations",
                category="Source Quality",
                severity=QualitySeverity.HIGH,
                description="Birth and death events should have citations.",
                count=150,
                samples=[
                    {"EventID": 1000, "EventType": "Birth"},
                    {"EventID": 2000, "EventType": "Death"},
                ],
            ),
            QualityIssue(
                rule_id="5.3",
                name="Unreasonable lifespan",
                category="Date Validity",
                severity=QualitySeverity.MEDIUM,
                description="Lifespan should be less than 120 years.",
                count=2,
                samples=[
                    {"PersonID": 400, "Given": "Old", "Surname": "Person"},
                ],
            ),
            QualityIssue(
                rule_id="4.2",
                name="Sources without citations",
                category="Source Quality",
                severity=QualitySeverity.LOW,
                description="Sources should have at least one citation.",
                count=25,
                samples=[
                    {"SourceID": 500, "Name": "Unused Source"},
                ],
            ),
        ]

        totals_by_severity = {
            QualitySeverity.CRITICAL: 8,
            QualitySeverity.HIGH: 150,
            QualitySeverity.MEDIUM: 2,
            QualitySeverity.LOW: 25,
        }

        totals_by_category = {
            "Required Fields": 5,
            "Logical Consistency": 3,
            "Source Quality": 175,
            "Date Validity": 2,
        }

        summary = {
            "total_people": 10000,
            "total_events": 25000,
            "total_sources": 500,
            "total_citations": 3000,
            "issue_total": 185,
        }

        return QualityReport(
            issues=issues,
            totals_by_severity=totals_by_severity,
            totals_by_category=totals_by_category,
            summary=summary,
        )

    def test_generator_init_with_path(self, real_db_path, extension_path):
        """Test initializing generator with database path."""
        if not real_db_path.exists():
            pytest.skip("Real database not available")

        generator = QualityReportGenerator(db=real_db_path, extension_path=extension_path)
        assert generator.db_path == real_db_path
        assert generator._db is None
        assert generator._owns_db

    def test_generator_init_without_db(self):
        """Test initializing generator without database."""
        generator = QualityReportGenerator()
        assert generator.db_path is None
        assert generator._db is None

    def test_severity_icon(self):
        """Test severity icon mapping."""
        generator = QualityReportGenerator()

        assert generator._severity_icon(QualitySeverity.CRITICAL) == "🔴"
        assert generator._severity_icon(QualitySeverity.HIGH) == "🟠"
        assert generator._severity_icon(QualitySeverity.MEDIUM) == "🟡"
        assert generator._severity_icon(QualitySeverity.LOW) == "🟢"

    def test_format_markdown(self, mock_quality_report):
        """Test markdown formatting."""
        generator = QualityReportGenerator()
        markdown = generator._format_markdown(mock_quality_report)

        # Verify header
        assert "# Data Quality Report" in markdown
        assert "## Summary Statistics" in markdown

        # Verify statistics
        assert "Total People:** 10,000" in markdown
        assert "Total Events:** 25,000" in markdown
        assert "Total Issues Found:** 185" in markdown

        # Verify severity sections
        assert "🔴 **Critical:** 8" in markdown
        assert "🟠 **High:** 150" in markdown
        assert "🟡 **Medium:** 2" in markdown
        assert "🟢 **Low:** 25" in markdown

        # Verify categories
        assert "Required Fields:** 5" in markdown
        assert "Logical Consistency:** 3" in markdown
        assert "Source Quality:** 175" in markdown

        # Verify issue details
        assert "### People without primary names" in markdown
        assert "Rule ID:** 1.1" in markdown
        assert "Count:** 5" in markdown

        # Verify samples
        assert "Sample Issues:" in markdown
        assert "PersonID: 100" in markdown

    def test_format_html(self, mock_quality_report):
        """Test HTML formatting."""
        generator = QualityReportGenerator()
        html = generator._format_html(mock_quality_report)

        # Verify HTML structure
        assert "<!DOCTYPE html>" in html
        assert "<html lang='en'>" in html
        assert "</html>" in html

        # Verify title
        assert "<h1>Data Quality Report</h1>" in html

        # Verify summary table
        assert "<table>" in html
        assert "Total People</td><td>10,000</td>" in html
        assert "Total Issues</strong></td><td><strong>185" in html

        # Verify severity sections
        assert "class='critical'" in html
        assert "class='high'" in html
        assert "class='medium'" in html
        assert "class='low'" in html

        # Verify issue details
        assert "People without primary names" in html
        assert "Rule ID: 1.1" in html

        # Verify samples
        assert "Sample Issues:" in html
        assert "PersonID: 100" in html

        # Verify CSS
        assert "<style>" in html
        assert "font-family:" in html

    def test_format_csv(self, mock_quality_report):
        """Test CSV formatting."""
        generator = QualityReportGenerator()
        csv_output = generator._format_csv(mock_quality_report)

        # Verify CSV structure
        lines = csv_output.strip().split("\n")

        # Verify header
        header = lines[0]
        assert "Rule ID" in header
        assert "Rule Name" in header
        assert "Category" in header
        assert "Severity" in header
        assert "Count" in header
        assert "Description" in header
        assert "Sample PersonID" in header

        # Verify data rows
        assert len(lines) > 1

        # Verify some data content
        csv_text = csv_output.lower()
        assert "1.1" in csv_text
        assert "people without primary names" in csv_text
        assert "required fields" in csv_text
        assert "critical" in csv_text

    def test_generate_raises_error_without_database(self):
        """Test that generate raises ValueError without database."""
        generator = QualityReportGenerator()

        with pytest.raises(ValueError, match="No database provided"):
            generator.generate(format=ReportFormat.MARKDOWN)

    def test_generate_markdown_with_mock_validation(self, real_db_path, extension_path, mock_quality_report):
        """Test generate with mocked validation."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = QualityReportGenerator(db=real_db_path, extension_path=extension_path)

        # Mock the _run_validation method
        with patch.object(generator, '_run_validation', return_value=mock_quality_report):
            report = generator.generate(format=ReportFormat.MARKDOWN)

            assert "# Data Quality Report" in report
            assert "Total People:** 10,000" in report
            assert "Total Issues Found:** 185" in report

    def test_generate_html_with_mock_validation(self, real_db_path, extension_path, mock_quality_report):
        """Test HTML generation with mocked validation."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = QualityReportGenerator(db=real_db_path, extension_path=extension_path)

        with patch.object(generator, '_run_validation', return_value=mock_quality_report):
            report = generator.generate(format=ReportFormat.HTML)

            assert "<!DOCTYPE html>" in report
            assert "<h1>Data Quality Report</h1>" in report

    def test_generate_csv_with_mock_validation(self, real_db_path, extension_path, mock_quality_report):
        """Test CSV generation with mocked validation."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = QualityReportGenerator(db=real_db_path, extension_path=extension_path)

        with patch.object(generator, '_run_validation', return_value=mock_quality_report):
            report = generator.generate(format=ReportFormat.CSV)

            assert "Rule ID" in report
            assert "Rule Name" in report
            assert "1.1" in report

    def test_generate_with_output_path(self, tmp_path, real_db_path, extension_path, mock_quality_report):
        """Test writing report to file."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = QualityReportGenerator(db=real_db_path, extension_path=extension_path)
        output_file = tmp_path / "quality_report.md"

        with patch.object(generator, '_run_validation', return_value=mock_quality_report):
            report = generator.generate(format=ReportFormat.MARKDOWN, output_path=output_file)

            # Verify file was created
            assert output_file.exists()

            # Verify content matches
            file_content = output_file.read_text(encoding="utf-8")
            assert file_content == report
            assert "# Data Quality Report" in file_content

    def test_generate_unsupported_format(self, real_db_path, extension_path):
        """Test that unsupported format raises ValueError."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = QualityReportGenerator(db=real_db_path, extension_path=extension_path)

        # Create mock report to avoid actual validation
        mock_report = Mock(spec=QualityReport)

        with patch.object(generator, '_run_validation', return_value=mock_report):
            with pytest.raises(ValueError, match="Unsupported format"):
                generator.generate(format="invalid_format")  # type: ignore


class TestQualityReportIntegration:
    """Integration tests with real database."""

    @pytest.fixture
    def real_db_path(self):
        """Path to real test database."""
        return Path("data/Iiams.rmtree")

    @pytest.fixture
    def extension_path(self):
        """Path to ICU extension."""
        return Path("sqlite-extension/icu.dylib")

    def test_generate_real_markdown_report(self, real_db_path, extension_path):
        """Test generating real markdown report from database."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = QualityReportGenerator(db=real_db_path, extension_path=extension_path, sample_limit=5)

        report = generator.generate(format=ReportFormat.MARKDOWN)

        # Verify structure
        assert "# Data Quality Report" in report
        assert "## Summary Statistics" in report
        assert "### Issues by Severity" in report
        assert "### Issues by Category" in report

        # Verify has actual data
        assert "Total People:" in report
        assert "Total Issues Found:" in report

        # Verify severity sections exist
        severity_headers = ["🔴 Critical Issues", "🟠 High Issues", "🟡 Medium Issues", "🟢 Low Issues"]
        # At least some severity sections should exist
        assert any(header in report for header in severity_headers)

    def test_generate_real_html_report(self, real_db_path, extension_path):
        """Test generating real HTML report from database."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = QualityReportGenerator(db=real_db_path, extension_path=extension_path, sample_limit=5)

        report = generator.generate(format=ReportFormat.HTML)

        # Verify HTML structure
        assert "<!DOCTYPE html>" in report
        assert "<html lang='en'>" in report
        assert "</html>" in report
        assert "<title>Data Quality Report</title>" in report

        # Verify has content
        assert "Total People" in report
        assert "Total Issues" in report

        # Verify CSS
        assert "<style>" in report
        assert "</style>" in report

    def test_generate_real_csv_report(self, real_db_path, extension_path):
        """Test generating real CSV report from database."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = QualityReportGenerator(db=real_db_path, extension_path=extension_path, sample_limit=5)

        report = generator.generate(format=ReportFormat.CSV)

        # Verify CSV structure
        lines = report.strip().split("\n")
        assert len(lines) > 1  # Header + at least one data row

        # Verify header
        header = lines[0]
        assert "Rule ID" in header
        assert "Rule Name" in header
        assert "Category" in header
        assert "Severity" in header

    def test_generate_all_formats(self, real_db_path, extension_path):
        """Test that all three formats can be generated successfully."""
        if not real_db_path.exists() or not extension_path.exists():
            pytest.skip("Real database or ICU extension not available")

        generator = QualityReportGenerator(db=real_db_path, extension_path=extension_path, sample_limit=3)

        # Generate all three formats
        markdown_report = generator.generate(format=ReportFormat.MARKDOWN)
        html_report = generator.generate(format=ReportFormat.HTML)
        csv_report = generator.generate(format=ReportFormat.CSV)

        # Verify all succeeded
        assert len(markdown_report) > 0
        assert len(html_report) > 0
        assert len(csv_report) > 0

        # Verify they're different
        assert markdown_report != html_report
        assert markdown_report != csv_report
        assert html_report != csv_report
