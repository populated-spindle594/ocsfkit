from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ocsfkit.validation import validate_mapping_doc


def mapping_catalog(root: str = "examples") -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in sorted(Path(root).glob("*.yaml")):
        mapping = yaml.safe_load(path.read_text())
        if not isinstance(mapping, dict):
            continue
        fields = mapping.get("fields") or {}
        target_class = mapping.get("target_class") or {}
        transforms = sorted(
            {
                transform
                for spec in fields.values()
                if isinstance(spec, dict)
                for transform in _as_list(spec.get("transform"))
            }
        )
        issues = validate_mapping_doc(mapping)
        items.append(
            {
                "file": str(path),
                "name": path.stem,
                "schema_version": mapping.get("schema_version"),
                "class_uid": target_class.get("class_uid"),
                "class_name": target_class.get("class_name"),
                "category_uid": target_class.get("category_uid"),
                "category_name": target_class.get("category_name"),
                "field_count": len(fields),
                "mapped_targets": sorted(str(target) for target in fields),
                "transforms": transforms,
                "drop_count": len(mapping.get("drop") or []),
                "custom_transforms": mapping.get("custom_transforms") or [],
                "issue_count": len(issues),
                "error_count": sum(1 for issue in issues if issue.level == "error"),
                "warning_count": sum(1 for issue in issues if issue.level == "warning"),
            }
        )
    return items


def catalog_markdown(items: list[dict[str, Any]]) -> str:
    lines = [
        "# ocsfkit Mapping Catalog",
        "",
        "Generated from `examples/*.yaml`.",
        "",
        "| Mapping | Target class | Fields | Transforms | Drops | Validation |",
        "| --- | --- | ---: | --- | ---: | --- |",
    ]
    for item in items:
        transforms = ", ".join(f"`{value}`" for value in item["transforms"]) or "-"
        validation = (
            "ok"
            if item["issue_count"] == 0
            else f"{item['error_count']} errors, {item['warning_count']} warnings"
        )
        lines.append(
            "| "
            f"`{item['file']}` | "
            f"{item.get('class_name') or 'Unknown'} ({item.get('class_uid') or '-'}) | "
            f"{item['field_count']} | "
            f"{transforms} | "
            f"{item['drop_count']} | "
            f"{validation} |"
        )
    lines.append("")
    for item in items:
        lines.extend(
            [
                f"## {item['name']}",
                "",
                f"- File: `{item['file']}`",
                f"- Target class: {item.get('class_name') or 'Unknown'} "
                f"(`{item.get('class_uid') or '-'}`)",
                f"- Schema version: `{item.get('schema_version') or 'unspecified'}`",
                "- Mapped targets:",
            ]
        )
        lines.extend(f"  - `{target}`" for target in item["mapped_targets"])
        lines.append("")
    return "\n".join(lines)


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []
