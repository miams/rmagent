"""
Data quality report generator for RMAgent.

Generates formatted data quality reports from validation results. Supports
multiple output formats (Markdown, HTML, CSV) and provides comprehensive
statistics on data quality issues across all validation categories.
"""

from __future__ import annotations

import csv
from datetime import datetime
from enum import Enum
from pathlib import Path

from rmagent.rmlib.database import RMDatabase
from rmagent.rmlib.quality import (
    DataQualityValidator,
    QualityIssue,
    QualityReport,
    QualitySeverity,
)


class ReportFormat(str, Enum):
    """Report output formats."""

    MARKDOWN = "markdown"
    HTML = "html"
    CSV = "csv"


class QualityReportGenerator:
    """
    Generate formatted data quality reports from validation results.

    Takes a QualityReport from DataQualityValidator and formats it for different
    output types (Markdown, HTML, CSV). Includes summary statistics, issue
    grouping by severity and category, and detailed sample listings.

    Args:
        db: RMDatabase instance or path to database
        extension_path: Path to ICU extension (default: ./sqlite-extension/icu.dylib)
        sample_limit: Maximum number of sample issues to include (default: 25)

    Example:
        ```python
        from rmagent.generators.quality_report import QualityReportGenerator

        generator = QualityReportGenerator(db="data/Iiams.rmtree")
        report = generator.generate(format=ReportFormat.MARKDOWN)
        print(report)
        ```
    """

    def __init__(
        self,
        db: RMDatabase | Path | str | None = None,
        extension_path: Path | str = Path("./sqlite-extension/icu.dylib"),
        sample_limit: int = 25,
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
        self.sample_limit = sample_limit
        self._last_report: QualityReport | None = None

    def generate(
        self,
        format: ReportFormat = ReportFormat.MARKDOWN,
        output_path: Path | str | None = None,
        category_filter: str | None = None,
        severity_filter: QualitySeverity | None = None,
    ) -> str:
        """
        Generate a data quality report.

        Args:
            format: Output format (markdown, html, or csv)
            output_path: Optional path to write output file
            category_filter: Filter by category name
            severity_filter: Filter by severity level

        Returns:
            Formatted report as string (or CSV writes directly to file)

        Raises:
            ValueError: If no database provided
        """
        # Run validation
        quality_report = self._run_validation()

        # Store for summary display
        self._last_report = quality_report

        # Apply filters
        if category_filter or severity_filter:
            quality_report = self._apply_filters(quality_report, category_filter, severity_filter)

        # Format report based on requested type
        if format == ReportFormat.MARKDOWN:
            output = self._format_markdown(quality_report)
        elif format == ReportFormat.HTML:
            output = self._format_html(quality_report)
        elif format == ReportFormat.CSV:
            output = self._format_csv(quality_report)
        else:
            raise ValueError(f"Unsupported format: {format}")

        # Write to file if requested
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(output, encoding="utf-8")

        return output

    def _run_validation(self) -> QualityReport:
        """Run data quality validation."""

        def _validate(db: RMDatabase) -> QualityReport:
            validator = DataQualityValidator(db, sample_limit=self.sample_limit)
            return validator.run_all_checks()

        if self._db:
            return _validate(self._db)
        elif self.db_path:
            with RMDatabase(self.db_path, extension_path=self.extension_path) as db:
                return _validate(db)
        else:
            raise ValueError("No database provided")

    def _apply_filters(
        self,
        report: QualityReport,
        category_filter: str | None,
        severity_filter: QualitySeverity | None,
    ) -> QualityReport:
        """Apply category and severity filters to the report."""
        filtered_issues = report.issues

        # Apply category filter
        if category_filter:
            filtered_issues = [
                issue for issue in filtered_issues if issue.category == category_filter
            ]

        # Apply severity filter
        if severity_filter:
            filtered_issues = [
                issue for issue in filtered_issues if issue.severity == severity_filter
            ]

        # Recalculate totals for filtered issues
        totals_by_severity = {
            severity: sum(issue.count for issue in filtered_issues if issue.severity == severity)
            for severity in QualitySeverity
        }

        totals_by_category: dict[str, int] = {}
        for issue in filtered_issues:
            totals_by_category.setdefault(issue.category, 0)
            totals_by_category[issue.category] += issue.count

        # Update summary with filtered issue count
        summary = report.summary.copy()
        summary["issue_total"] = sum(issue.count for issue in filtered_issues)

        return QualityReport(
            issues=filtered_issues,
            totals_by_severity=totals_by_severity,
            totals_by_category=totals_by_category,
            summary=summary,
        )

    # ---- Markdown Formatting ----

    def _format_markdown(self, report: QualityReport) -> str:
        """Format report as Markdown."""
        lines = []

        # Header
        lines.append("# Data Quality Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Summary statistics
        lines.append("## Summary Statistics")
        lines.append("")
        lines.append(f"- **Total People:** {report.summary.get('total_people', 0):,}")
        lines.append(f"- **Total Events:** {report.summary.get('total_events', 0):,}")
        lines.append(f"- **Total Sources:** {report.summary.get('total_sources', 0):,}")
        lines.append(f"- **Total Citations:** {report.summary.get('total_citations', 0):,}")
        lines.append("")
        lines.append(f"- **Total Issues Found:** {report.summary.get('issue_total', 0):,}")
        lines.append("")

        # Issues by severity
        lines.append("### Issues by Severity")
        lines.append("")
        for severity in [
            QualitySeverity.CRITICAL,
            QualitySeverity.HIGH,
            QualitySeverity.MEDIUM,
            QualitySeverity.LOW,
        ]:
            count = report.totals_by_severity.get(severity, 0)
            icon = self._severity_icon(severity)
            lines.append(f"- {icon} **{severity.value.capitalize()}:** {count:,}")
        lines.append("")

        # Issues by category
        lines.append("### Issues by Category")
        lines.append("")
        for category in sorted(report.totals_by_category.keys()):
            count = report.totals_by_category[category]
            lines.append(f"- **{category}:** {count:,}")
        lines.append("")

        # Detailed issues by severity
        for severity in [
            QualitySeverity.CRITICAL,
            QualitySeverity.HIGH,
            QualitySeverity.MEDIUM,
            QualitySeverity.LOW,
        ]:
            severity_issues = [issue for issue in report.issues if issue.severity == severity]
            if severity_issues:
                icon = self._severity_icon(severity)
                lines.append(f"## {icon} {severity.value.capitalize()} Issues")
                lines.append("")

                for issue in severity_issues:
                    self._add_issue_markdown(lines, issue)

        return "\n".join(lines)

    def _add_issue_markdown(self, lines: list[str], issue: QualityIssue) -> None:
        """Add an issue section to markdown output."""
        lines.append(f"### {issue.name}")
        lines.append("")
        lines.append(f"- **Rule ID:** {issue.rule_id}")
        lines.append(f"- **Category:** {issue.category}")
        lines.append(f"- **Count:** {issue.count:,}")
        lines.append(f"- **Description:** {issue.description}")
        lines.append("")

        if issue.samples:
            lines.append("**Sample Issues:**")
            lines.append("")

            for i, sample in enumerate(issue.samples[: self.sample_limit], 1):
                self._add_sample_markdown(lines, i, sample)

        lines.append("---")
        lines.append("")

    def _add_sample_markdown(self, lines: list[str], index: int, sample: dict) -> None:
        """Add a sample issue to markdown output."""
        # Format sample based on available fields
        if "PersonID" in sample:
            person_id = sample["PersonID"]
            name_parts = []
            if "Given" in sample and sample["Given"]:
                name_parts.append(sample["Given"])
            if "Surname" in sample and sample["Surname"]:
                name_parts.append(sample["Surname"])
            name = " ".join(name_parts) if name_parts else f"Person {person_id}"
            lines.append(f"{index}. **{name}** (PersonID: {person_id})")
        elif "SourceID" in sample:
            source_id = sample["SourceID"]
            source_name = sample.get("Name", f"Source {source_id}")
            lines.append(f"{index}. **{source_name}** (SourceID: {source_id})")
        elif "EventID" in sample:
            event_id = sample["EventID"]
            event_type = sample.get("EventType", "Event")
            lines.append(f"{index}. **{event_type}** (EventID: {event_id})")
        else:
            # Generic sample
            lines.append(f"{index}. **Record:** {', '.join(f'{k}={v}' for k, v in sample.items())}")

    def _severity_icon(self, severity: QualitySeverity) -> str:
        """Get emoji icon for severity level."""
        icons = {
            QualitySeverity.CRITICAL: "🔴",
            QualitySeverity.HIGH: "🟠",
            QualitySeverity.MEDIUM: "🟡",
            QualitySeverity.LOW: "🟢",
        }
        return icons.get(severity, "⚪")

    # ---- HTML Formatting ----

    def _format_html(self, report: QualityReport) -> str:
        """Format report as HTML."""
        lines = []

        # HTML header
        lines.append("<!DOCTYPE html>")
        lines.append("<html lang='en'>")
        lines.append("<head>")
        lines.append("    <meta charset='UTF-8'>")
        lines.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        lines.append("    <title>Data Quality Report</title>")
        lines.append("    <style>")
        lines.append(
            "        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, "
            "sans-serif; margin: 40px; }"
        )
        lines.append(
            "        h1 { color: #333; border-bottom: 2px solid #4CAF50; "
            "padding-bottom: 10px; }"
        )
        lines.append("        h2 { color: #555; margin-top: 30px; }")
        lines.append("        h3 { color: #666; }")
        lines.append(
            "        .summary { background-color: #f9f9f9; padding: 15px; "
            "border-left: 4px solid #4CAF50; margin: 20px 0; }"
        )
        lines.append("        .critical { color: #d32f2f; }")
        lines.append("        .high { color: #f57c00; }")
        lines.append("        .medium { color: #fbc02d; }")
        lines.append("        .low { color: #388e3c; }")
        lines.append(
            "        .issue { background-color: #fff; border: 1px solid #ddd; padding: 15px; "
            "margin: 15px 0; border-radius: 4px; }"
        )
        lines.append(
            "        .issue-header { font-weight: bold; font-size: 1.1em; "
            "margin-bottom: 10px; }"
        )
        lines.append("        .metadata { color: #666; font-size: 0.9em; }")
        lines.append("        .samples { margin-top: 10px; }")
        lines.append("        .sample { margin: 5px 0; padding-left: 20px; }")
        lines.append("        table { border-collapse: collapse; width: 100%; margin: 20px 0; }")
        lines.append("        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        lines.append("        th { background-color: #4CAF50; color: white; }")
        lines.append("    </style>")
        lines.append("</head>")
        lines.append("<body>")

        # Content
        lines.append("    <h1>Data Quality Report</h1>")
        lines.append(
            f"    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
        )

        # Summary
        lines.append("    <div class='summary'>")
        lines.append("        <h2>Summary Statistics</h2>")
        lines.append("        <table>")
        lines.append("            <tr><th>Metric</th><th>Count</th></tr>")
        lines.append(
            f"            <tr><td>Total People</td><td>{report.summary.get('total_people', 0):,}</td></tr>"
        )
        lines.append(
            f"            <tr><td>Total Events</td><td>{report.summary.get('total_events', 0):,}</td></tr>"
        )
        lines.append(
            f"            <tr><td>Total Sources</td><td>{report.summary.get('total_sources', 0):,}</td></tr>"
        )
        lines.append(
            f"            <tr><td>Total Citations</td><td>{report.summary.get('total_citations', 0):,}</td></tr>"
        )
        lines.append(
            f"            <tr><td><strong>Total Issues</strong></td>"
            f"<td><strong>{report.summary.get('issue_total', 0):,}</strong></td></tr>"
        )
        lines.append("        </table>")
        lines.append("    </div>")

        # Issues by severity
        lines.append("    <h2>Issues by Severity</h2>")
        lines.append("    <table>")
        lines.append("        <tr><th>Severity</th><th>Count</th></tr>")
        for severity in [
            QualitySeverity.CRITICAL,
            QualitySeverity.HIGH,
            QualitySeverity.MEDIUM,
            QualitySeverity.LOW,
        ]:
            count = report.totals_by_severity.get(severity, 0)
            css_class = severity.value
            lines.append(
                f"        <tr><td class='{css_class}'>{severity.value.capitalize()}</td><td>{count:,}</td></tr>"
            )
        lines.append("    </table>")

        # Detailed issues
        for severity in [
            QualitySeverity.CRITICAL,
            QualitySeverity.HIGH,
            QualitySeverity.MEDIUM,
            QualitySeverity.LOW,
        ]:
            severity_issues = [issue for issue in report.issues if issue.severity == severity]
            if severity_issues:
                css_class = severity.value
                lines.append(
                    f"    <h2 class='{css_class}'>{severity.value.capitalize()} Issues</h2>"
                )

                for issue in severity_issues:
                    lines.append("    <div class='issue'>")
                    lines.append(f"        <div class='issue-header'>{issue.name}</div>")
                    lines.append(
                        f"        <div class='metadata'>Rule ID: {issue.rule_id} | "
                        f"Category: {issue.category} | Count: {issue.count:,}</div>"
                    )
                    lines.append(f"        <p>{issue.description}</p>")

                    if issue.samples:
                        lines.append(
                            "        <div class='samples'><strong>Sample Issues:</strong><ul>"
                        )
                        for sample in issue.samples[: self.sample_limit]:
                            sample_text = self._format_sample_html(sample)
                            lines.append(f"            <li>{sample_text}</li>")
                        lines.append("        </ul></div>")

                    lines.append("    </div>")

        # Footer
        lines.append("</body>")
        lines.append("</html>")

        return "\n".join(lines)

    def _format_sample_html(self, sample: dict) -> str:
        """Format a sample issue for HTML output."""
        if "PersonID" in sample:
            person_id = sample["PersonID"]
            name_parts = []
            if "Given" in sample and sample["Given"]:
                name_parts.append(sample["Given"])
            if "Surname" in sample and sample["Surname"]:
                name_parts.append(sample["Surname"])
            name = " ".join(name_parts) if name_parts else f"Person {person_id}"
            return f"<strong>{name}</strong> (PersonID: {person_id})"
        elif "SourceID" in sample:
            source_id = sample["SourceID"]
            source_name = sample.get("Name", f"Source {source_id}")
            return f"<strong>{source_name}</strong> (SourceID: {source_id})"
        elif "EventID" in sample:
            event_id = sample["EventID"]
            event_type = sample.get("EventType", "Event")
            return f"<strong>{event_type}</strong> (EventID: {event_id})"
        else:
            return ", ".join(f"{k}={v}" for k, v in sample.items())

    # ---- CSV Formatting ----

    def _format_csv(self, report: QualityReport) -> str:
        """Format report as CSV."""
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header row
        writer.writerow(
            [
                "Rule ID",
                "Rule Name",
                "Category",
                "Severity",
                "Count",
                "Description",
                "Sample PersonID",
                "Sample Name",
                "Sample SourceID",
                "Sample Source Name",
                "Sample EventID",
                "Sample Event Type",
            ]
        )

        # Data rows
        for issue in report.issues:
            base_row = [
                issue.rule_id,
                issue.name,
                issue.category,
                issue.severity.value,
                issue.count,
                issue.description,
            ]

            if issue.samples:
                # Write one row per sample
                for sample in issue.samples[: self.sample_limit]:
                    row = base_row + [
                        sample.get("PersonID", ""),
                        f"{sample.get('Given', '')} {sample.get('Surname', '')}".strip(),
                        sample.get("SourceID", ""),
                        sample.get("Name", ""),
                        sample.get("EventID", ""),
                        sample.get("EventType", ""),
                    ]
                    writer.writerow(row)
            else:
                # Write row without samples
                row = base_row + ["", "", "", "", "", ""]
                writer.writerow(row)

        return output.getvalue()
