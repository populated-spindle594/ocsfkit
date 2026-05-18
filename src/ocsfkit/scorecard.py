from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, Field

from ocsfkit.coverage import CoverageReport, enforce_coverage_thresholds, mapping_coverage
from ocsfkit.mapping import apply_mapping
from ocsfkit.models import LintIssue
from ocsfkit.registry import lint_event
from ocsfkit.strict import strict_mapping_failures


class ScorecardReport(BaseModel):
    grade: str
    passed: bool
    events: int
    average_confidence: float
    source_field_coverage: float
    mapped_target_count: int
    unmapped_source_field_count: int
    dropped_source_field_count: int
    missing_target_field_count: int
    lint_error_count: int
    lint_warning_count: int
    failures: list[str] = Field(default_factory=list)
    coverage: CoverageReport


def mapping_scorecard(
    events: Iterable[dict[str, Any]],
    mapping: dict[str, Any],
    custom_transforms: dict[str, Any] | None = None,
    *,
    min_confidence: float = 0.8,
    max_unmapped: int = 0,
    max_lint_errors: int = 0,
    strict: bool = False,
) -> ScorecardReport:
    event_list = list(events)
    coverage = mapping_coverage(event_list, mapping, custom_transforms)
    lint_issues: list[LintIssue] = []
    strict_failures: list[str] = []
    for event in event_list:
        result = apply_mapping(event, mapping, custom_transforms)
        lint_issues.extend(lint_event(result.event, result.explanation.schema_version))
        if strict:
            strict_failures.extend(strict_mapping_failures(result.explanation))
    lint_error_count = sum(1 for issue in lint_issues if issue.level == "error")
    lint_warning_count = sum(1 for issue in lint_issues if issue.level == "warning")
    failures = enforce_coverage_thresholds(coverage, min_confidence, max_unmapped)
    if lint_error_count > max_lint_errors:
        failures.append(f"Lint error count {lint_error_count} exceeds {max_lint_errors}")
    failures.extend(strict_failures)
    grade = _grade(coverage, lint_error_count, bool(failures))
    return ScorecardReport(
        grade=grade,
        passed=not failures,
        events=coverage.events,
        average_confidence=coverage.average_confidence,
        source_field_coverage=coverage.source_field_coverage,
        mapped_target_count=sum(coverage.mapped_targets.values()),
        unmapped_source_field_count=sum(coverage.unmapped_source_fields.values()),
        dropped_source_field_count=sum(coverage.dropped_source_fields.values()),
        missing_target_field_count=sum(coverage.missing_target_fields.values()),
        lint_error_count=lint_error_count,
        lint_warning_count=lint_warning_count,
        failures=failures,
        coverage=coverage,
    )


def scorecard_markdown(report: ScorecardReport) -> str:
    lines = [
        "## ocsfkit Scorecard",
        "",
        f"- Grade: **{report.grade}**",
        f"- Passed: **{'yes' if report.passed else 'no'}**",
        f"- Events: {report.events}",
        f"- Average confidence: {report.average_confidence:.3f}",
        f"- Source field coverage: {report.source_field_coverage:.3f}",
        f"- Mapped target values: {report.mapped_target_count}",
        f"- Unmapped source fields: {report.unmapped_source_field_count}",
        f"- Missing target fields: {report.missing_target_field_count}",
        f"- Lint errors: {report.lint_error_count}",
        f"- Lint warnings: {report.lint_warning_count}",
    ]
    if report.failures:
        lines.extend(["", "### Failures"])
        lines.extend(f"- {failure}" for failure in report.failures)
    return "\n".join(lines) + "\n"


def _grade(report: CoverageReport, lint_errors: int, failed: bool) -> str:
    if failed or lint_errors:
        return "F"
    if report.average_confidence >= 0.95 and report.source_field_coverage >= 0.95:
        return "A"
    if report.average_confidence >= 0.85 and report.source_field_coverage >= 0.85:
        return "B"
    if report.average_confidence >= 0.70 and report.source_field_coverage >= 0.70:
        return "C"
    return "D"
