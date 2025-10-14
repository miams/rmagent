"""
Unit tests for DataQualityValidator.

These are integration-flavored unit checks that exercise the validator
against the sanitized sample RootsMagic database bundled with the repo.
"""

from __future__ import annotations

from pathlib import Path

# Ensure repository root is available on sys.path when running with pytest -o addopts=''
PROJECT_ROOT = Path(__file__).resolve().parents[2]
import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rmagent.rmlib.quality import QualitySeverity


def test_report_summary_contains_entity_totals(quality_results_cached) -> None:
    quality_results = quality_results_cached
    report, _ = quality_results
    assert report.summary["total_people"] > 0
    assert report.summary["total_events"] > 0
    assert sum(report.totals_by_severity.values()) == report.summary["issue_total"]


def test_rule_2_1_detects_death_before_birth(quality_results_cached) -> None:
    _, issues = quality_results_cached
    rule_issues = issues.get("2.1")
    assert rule_issues is not None
    total = sum(item.count for item in rule_issues)
    assert total >= 1
    assert all(item.severity == QualitySeverity.CRITICAL for item in rule_issues)


def test_rule_4_1_counts_unsourced_vital_events(quality_results_cached) -> None:
    _, issues = quality_results_cached
    rule_issues = issues.get("4.1")
    assert rule_issues
    high_issue = rule_issues[0]
    assert high_issue.severity == QualitySeverity.HIGH
    assert high_issue.count > 100  # sample database has many unsourced events


def test_rule_2_3_returns_both_high_and_medium_when_applicable(quality_results_cached) -> None:
    _, issues = quality_results_cached
    rule_issues = issues.get("2.3")
    assert rule_issues
    severities = {issue.severity for issue in rule_issues}
    assert QualitySeverity.HIGH in severities


def test_sortdate_rule_identifies_mismatches(quality_results_cached) -> None:
    _, issues = quality_results_cached
    rule_issues = issues.get("5.1")
    assert rule_issues
    assert rule_issues[0].count > 0
