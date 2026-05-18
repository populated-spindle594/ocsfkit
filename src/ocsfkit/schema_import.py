from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from ocsfkit.errors import InputLoadError


def import_schema(path: str) -> dict[str, Any]:
    root = Path(path)
    if root.is_file():
        return _load_schema_file(root)
    if not root.is_dir():
        raise InputLoadError(f"Schema path does not exist: {path}")
    schema: dict[str, Any] = {"schema_version": "imported", "classes": {}, "fields": {}}
    for candidate in sorted(root.rglob("*.json")):
        value = _load_schema_file(candidate)
        _merge_schema(schema, value)
    for candidate in sorted(root.rglob("*.yml")) + sorted(root.rglob("*.yaml")):
        value = _load_schema_file(candidate)
        _merge_schema(schema, value)
    return schema


def _load_schema_file(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text()
        value = yaml.safe_load(raw) if path.suffix in {".yml", ".yaml"} else json.loads(raw)
    except (OSError, json.JSONDecodeError, yaml.YAMLError) as exc:
        raise InputLoadError(f"Could not load schema file {path}: {exc}") from exc
    if not isinstance(value, dict):
        return {}
    if "classes" in value or "fields" in value:
        return value
    class_uid = value.get("uid") or value.get("class_uid")
    caption = value.get("caption") or value.get("name") or value.get("class_name")
    if class_uid and caption:
        numeric_class_uid = _optional_int(class_uid)
        if numeric_class_uid is None:
            return {}
        attributes = value.get("attributes") or value.get("fields") or {}
        fields = _fields_from_attributes(attributes)
        enum_map = _enums_from_attributes(attributes)
        return {
            "classes": {
                str(class_uid): {
                    "class_uid": numeric_class_uid,
                    "class_name": str(caption),
                    "category_uid": _optional_int(value.get("category_uid")) or 0,
                    "category_name": str(value.get("category_name") or ""),
                    "required": sorted(value.get("required") or []),
                    "recommended": sorted(value.get("recommended") or []),
                    "attributes": sorted(fields),
                }
            },
            "fields": fields,
            "enums": enum_map,
        }
    return {}


def _merge_schema(target: dict[str, Any], source: dict[str, Any]) -> None:
    for key in ("classes", "fields", "enums"):
        if isinstance(source.get(key), dict):
            target.setdefault(key, {}).update(source[key])
    if source.get("schema_version"):
        target["schema_version"] = source["schema_version"]


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _fields_from_attributes(attributes: Any) -> dict[str, Any]:
    if not isinstance(attributes, dict):
        return {}
    fields: dict[str, Any] = {}
    for name, spec in attributes.items():
        if not isinstance(name, str) or not isinstance(spec, dict):
            continue
        fields[name] = {
            "type": str(spec.get("type") or spec.get("object_type") or "unknown"),
            "required": str(spec.get("requirement", "")).lower() == "required"
            or bool(spec.get("required", False)),
            "recommended": str(spec.get("requirement", "")).lower() == "recommended"
            or bool(spec.get("recommended", False)),
            "caption": spec.get("caption") or spec.get("description"),
            "deprecated": bool(spec.get("deprecated", False)),
        }
    return fields


def _enums_from_attributes(attributes: Any) -> dict[str, Any]:
    if not isinstance(attributes, dict):
        return {}
    enums: dict[str, Any] = {}
    for name, spec in attributes.items():
        if isinstance(spec, dict) and isinstance(spec.get("enum"), dict):
            enums[name] = spec["enum"]
    return enums
