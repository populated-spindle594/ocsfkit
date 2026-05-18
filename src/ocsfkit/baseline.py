from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from ocsfkit.coverage import mapping_coverage


class BaselineDiff(BaseModel):
    passed: bool
    new_unmapped_source_fields: list[str] = Field(default_factory=list)
    new_missing_target_fields: list[str] = Field(default_factory=list)
    baseline_unmapped_source_fields: list[str] = Field(default_factory=list)
    current_unmapped_source_fields: list[str] = Field(default_factory=list)


def create_baseline(
    events: list[dict[str, Any]],
    mapping: dict[str, Any],
    custom_transforms: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report = mapping_coverage(events, mapping, custom_transforms)
    return {
        "version": 1,
        "events": report.events,
        "average_confidence": report.average_confidence,
        "source_field_coverage": report.source_field_coverage,
        "unmapped_source_fields": sorted(report.unmapped_source_fields),
        "missing_target_fields": sorted(report.missing_target_fields),
    }


def check_baseline(
    baseline_path: str,
    events: list[dict[str, Any]],
    mapping: dict[str, Any],
    custom_transforms: dict[str, Any] | None = None,
) -> BaselineDiff:
    baseline = yaml.safe_load(Path(baseline_path).read_text())
    if not isinstance(baseline, dict):
        baseline = {}
    current = create_baseline(events, mapping, custom_transforms)
    baseline_unmapped = set(baseline.get("unmapped_source_fields") or [])
    current_unmapped = set(current.get("unmapped_source_fields") or [])
    baseline_missing = set(baseline.get("missing_target_fields") or [])
    current_missing = set(current.get("missing_target_fields") or [])
    new_unmapped = sorted(current_unmapped - baseline_unmapped)
    new_missing = sorted(current_missing - baseline_missing)
    return BaselineDiff(
        passed=not new_unmapped and not new_missing,
        new_unmapped_source_fields=new_unmapped,
        new_missing_target_fields=new_missing,
        baseline_unmapped_source_fields=sorted(baseline_unmapped),
        current_unmapped_source_fields=sorted(current_unmapped),
    )
