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
        metadata = mapping.get("metadata") or {}
        if not isinstance(metadata, dict):
            metadata = {}
        items.append(
            {
                "file": str(path),
                "name": path.stem,
                "source_product": metadata.get("source_product")
                or _product_name(target_class),
                "source_version": metadata.get("source_version"),
                "owner": metadata.get("owner"),
                "maturity": metadata.get("maturity", "draft"),
                "last_reviewed": metadata.get("last_reviewed"),
                "fixture": metadata.get("fixture"),
                "expected": metadata.get("expected"),
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
                f"- Source product: {item.get('source_product') or 'Unknown'}",
                f"- Maturity: `{item.get('maturity') or 'draft'}`",
                f"- Owner: `{item.get('owner') or 'unassigned'}`",
                f"- Last reviewed: `{item.get('last_reviewed') or 'unknown'}`",
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


def _product_name(target_class: dict[str, Any]) -> str | None:
    metadata = target_class.get("metadata")
    if isinstance(metadata, dict):
        product = metadata.get("product")
        if isinstance(product, dict) and product.get("name"):
            return str(product["name"])
    value = target_class.get("metadata.product.name")
    return str(value) if value else None
