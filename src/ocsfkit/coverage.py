from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, Field

from ocsfkit.mapping import apply_mapping


class CoverageReport(BaseModel):
    events: int
    mapped_targets: dict[str, int] = Field(default_factory=dict)
    unmapped_source_fields: dict[str, int] = Field(default_factory=dict)
    dropped_source_fields: dict[str, int] = Field(default_factory=dict)
    missing_target_fields: dict[str, int] = Field(default_factory=dict)
    average_confidence: float
    source_field_coverage: float


def mapping_coverage(
    events: Iterable[dict[str, Any]],
    mapping: dict[str, Any],
    custom_transforms: dict[str, Any] | None = None,
) -> CoverageReport:
    mapped_targets: dict[str, int] = {}
    unmapped_source_fields: dict[str, int] = {}
    dropped_source_fields: dict[str, int] = {}
    missing_target_fields: dict[str, int] = {}
    confidence_total = 0.0
    event_count = 0
    for event in events:
        event_count += 1
        result = apply_mapping(event, mapping, custom_transforms)
        explanation = result.explanation
        confidence_total += explanation.confidence
        decisions = [
            *explanation.mapped_fields,
            *explanation.defaulted_fields,
            *explanation.guessed_fields,
        ]
        for decision in decisions:
            _increment(mapped_targets, decision.target)
        for path in explanation.unmapped_source_fields:
            _increment(unmapped_source_fields, path)
        for path in explanation.dropped_fields:
            _increment(dropped_source_fields, path)
        for path in explanation.missing_target_fields:
            _increment(missing_target_fields, path)
    reviewed = sum(mapped_targets.values()) + sum(dropped_source_fields.values())
    unmapped = sum(unmapped_source_fields.values())
    denominator = reviewed + unmapped
    return CoverageReport(
        events=event_count,
        mapped_targets=dict(sorted(mapped_targets.items())),
        unmapped_source_fields=dict(sorted(unmapped_source_fields.items())),
        dropped_source_fields=dict(sorted(dropped_source_fields.items())),
        missing_target_fields=dict(sorted(missing_target_fields.items())),
        average_confidence=round(confidence_total / event_count, 3) if event_count else 0.0,
        source_field_coverage=round(reviewed / denominator, 3) if denominator else 1.0,
    )


def enforce_coverage_thresholds(
    report: CoverageReport,
    min_confidence: float | None = None,
    max_unmapped: int | None = None,
) -> list[str]:
    failures: list[str] = []
    if min_confidence is not None and report.average_confidence < min_confidence:
        failures.append(
            f"Average confidence {report.average_confidence:.3f} is below {min_confidence:.3f}"
        )
    unmapped_total = sum(report.unmapped_source_fields.values())
    if max_unmapped is not None and unmapped_total > max_unmapped:
        failures.append(f"Unmapped source field count {unmapped_total} exceeds {max_unmapped}")
    return failures


def _increment(counts: dict[str, int], key: str) -> None:
    counts[key] = counts.get(key, 0) + 1
