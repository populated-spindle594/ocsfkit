from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ocsfkit.diff import diff_events
from ocsfkit.io import load_events, load_mapping_file
from ocsfkit.mapping import apply_mapping
from ocsfkit.models import DiffChange
from ocsfkit.transforms import load_custom_transforms


def run_mapping_tests(path: str) -> list[dict[str, Any]]:
    root = Path(path)
    specs = _mapping_specs(root) if root.is_dir() else [root]
    results: list[dict[str, Any]] = []
    for spec in specs:
        changes = run_mapping_test(str(spec))
        results.append(
            {
                "spec": str(spec),
                "passed": not changes,
                "changes": [change.model_dump() for change in changes],
            }
        )
    return results


def run_mapping_test(spec_path: str) -> list[DiffChange]:
    spec = yaml.safe_load(Path(spec_path).read_text())
    mapping_path = Path(spec_path).parent / spec["mapping"]
    mapping = load_mapping_file(str(mapping_path))
    custom_transforms = load_custom_transforms(
        mapping.get("custom_transforms") or [],
        mapping_path.parent,
    )
    source = load_events(str(Path(spec_path).parent / spec["input"]))[0]
    expected = load_events(str(Path(spec_path).parent / spec["expected"]))[0]
    actual = apply_mapping(source, mapping, custom_transforms).event
    return diff_events(expected, actual)


def _mapping_specs(root: Path) -> list[Path]:
    specs: list[Path] = []
    for path in sorted(root.glob("*.yaml")):
        spec = yaml.safe_load(path.read_text())
        if isinstance(spec, dict) and {"input", "mapping", "expected"} <= set(spec):
            specs.append(path)
    return specs


def write_mapping_test(
    spec_path: str,
    input_path: str,
    mapping_path: str,
    expected_path: str,
) -> None:
    spec: dict[str, Any] = {
        "input": input_path,
        "mapping": mapping_path,
        "expected": expected_path,
    }
    Path(spec_path).write_text(yaml.safe_dump(spec, sort_keys=False))
