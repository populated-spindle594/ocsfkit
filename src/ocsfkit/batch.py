from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, Field

from ocsfkit.coverage import CoverageReport, mapping_coverage
from ocsfkit.mapping import apply_mapping
from ocsfkit.models import LintIssue, MappingExplanation
from ocsfkit.registry import lint_event


class BatchReport(BaseModel):
    events: int
    coverage: CoverageReport
    lint_errors: int
    lint_warnings: int
    unmapped_source_fields: dict[str, int] = Field(default_factory=dict)
    missing_target_fields: dict[str, int] = Field(default_factory=dict)


class BatchResult(BaseModel):
    events: list[dict[str, Any]]
    explanations: list[MappingExplanation]
    lint_issues: list[list[LintIssue]]
    report: BatchReport


def run_batch(
    events: Iterable[dict[str, Any]],
    mapping: dict[str, Any],
    custom_transforms: dict[str, Any] | None = None,
) -> BatchResult:
    event_list = list(events)
    mapped_events: list[dict[str, Any]] = []
    explanations: list[MappingExplanation] = []
    lint_issues: list[list[LintIssue]] = []
    unmapped: Counter[str] = Counter()
    missing: Counter[str] = Counter()

    for event in event_list:
        result = apply_mapping(event, mapping, custom_transforms)
        mapped_events.append(result.event)
        explanations.append(result.explanation)
        lint_issues.append(lint_event(result.event, result.explanation.schema_version))
        unmapped.update(result.explanation.unmapped_source_fields)
        missing.update(result.explanation.missing_target_fields)

    flat_issues = [issue for issues in lint_issues for issue in issues]
    report = BatchReport(
        events=len(mapped_events),
        coverage=mapping_coverage(event_list, mapping, custom_transforms),
        lint_errors=sum(1 for issue in flat_issues if issue.level == "error"),
        lint_warnings=sum(1 for issue in flat_issues if issue.level == "warning"),
        unmapped_source_fields=dict(sorted(unmapped.items())),
        missing_target_fields=dict(sorted(missing.items())),
    )
    return BatchResult(
        events=mapped_events,
        explanations=explanations,
        lint_issues=lint_issues,
        report=report,
    )
