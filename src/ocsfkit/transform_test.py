from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ocsfkit.diff import diff_events
from ocsfkit.models import DiffChange
from ocsfkit.transforms import apply_transform, load_custom_transforms


def run_transform_tests(spec_path: str) -> list[dict[str, Any]]:
    spec_file = Path(spec_path)
    spec = yaml.safe_load(spec_file.read_text())
    if not isinstance(spec, dict):
        raise ValueError("Transform test spec must be a YAML mapping")
    custom = load_custom_transforms(spec.get("custom_transforms") or [], spec_file.parent)
    results: list[dict[str, Any]] = []
    for index, case in enumerate(spec.get("cases") or [], start=1):
        name = case["transform"]
        actual = apply_transform(name, case.get("input"), custom)
        expected = case.get("expected")
        changes: list[DiffChange]
        if isinstance(actual, dict) and isinstance(expected, dict):
            changes = diff_events(expected, actual)
        elif actual == expected:
            changes = []
        else:
            changes = [DiffChange(path="$", before=expected, after=actual, kind="changed")]
        results.append(
            {
                "index": index,
                "name": case.get("name") or f"case {index}",
                "transform": name,
                "passed": not changes,
                "actual": actual,
                "expected": expected,
                "changes": [change.model_dump() for change in changes],
            }
        )
    return results
