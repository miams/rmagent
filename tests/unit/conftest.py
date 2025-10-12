"""Shared pytest fixtures for unit tests."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path

import pytest

from rmagent.rmlib.database import RMDatabase
from rmagent.rmlib.quality import DataQualityValidator, QualityReport

DATA_PATH = Path("data/Iiams.rmtree")
ICU_PATH = Path("sqlite-extension/icu.dylib")
CACHE_DIR = Path(".pytest_cache/quality_cache")


@pytest.fixture(scope="session")
def quality_validator() -> Iterable[DataQualityValidator]:
    """Create a shared DataQualityValidator for tests."""
    if not (DATA_PATH.exists() and ICU_PATH.exists()):
        pytest.skip("Sample database or ICU extension missing")

    db = RMDatabase(DATA_PATH, extension_path=ICU_PATH)
    db.connect()
    validator = DataQualityValidator(db)
    try:
        yield validator
    finally:
        db.close()


@pytest.fixture(scope="session")
def quality_results_cached(quality_validator: DataQualityValidator):
    """Quality check results with persistent disk caching.

    Caches results to .pytest_cache/quality_cache/ and invalidates
    when the database file modification time changes.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "quality_report.json"
    db_mtime = DATA_PATH.stat().st_mtime

    # Try to load from cache
    if cache_file.exists():
        try:
            cached_data = json.loads(cache_file.read_text())
            if cached_data.get("db_mtime") == db_mtime:
                # Cache hit - deserialize
                report = _deserialize_report(cached_data["report"])
                grouped = {}
                for issue in report.issues:
                    grouped.setdefault(issue.rule_id, []).append(issue)
                return report, grouped
        except (json.JSONDecodeError, KeyError, TypeError):
            # Cache corrupted - will regenerate
            pass

    # Cache miss - run expensive check
    report = quality_validator.run_all_checks()
    grouped = {}
    for issue in report.issues:
        grouped.setdefault(issue.rule_id, []).append(issue)

    # Serialize and save to cache
    cache_data = {
        "db_mtime": db_mtime,
        "report": _serialize_report(report),
    }
    cache_file.write_text(json.dumps(cache_data, indent=2))

    return report, grouped


def _serialize_report(report: QualityReport) -> dict:
    """Convert QualityReport to JSON-serializable dict."""
    return {
        "issues": [asdict(issue) for issue in report.issues],
        "totals_by_severity": {k.value: v for k, v in report.totals_by_severity.items()},
        "totals_by_category": report.totals_by_category,
        "summary": report.summary,
    }


def _deserialize_report(data: dict) -> QualityReport:
    """Reconstruct QualityReport from cached dict."""
    from rmagent.rmlib.quality import QualityIssue, QualitySeverity

    issues = [QualityIssue(**issue) for issue in data["issues"]]
    totals_by_severity = {QualitySeverity(k): v for k, v in data["totals_by_severity"].items()}

    return QualityReport(
        issues=issues,
        totals_by_severity=totals_by_severity,
        totals_by_category=data["totals_by_category"],
        summary=data["summary"],
    )
