from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ocsfkit.registry import BASE_FIELDS, CLASS_REGISTRY, DEFAULT_SCHEMA_VERSION


def bundled_schema(version: str = DEFAULT_SCHEMA_VERSION) -> dict[str, Any]:
    return {
        "schema_version": version,
        "fields": {
            path: {
                "type": _type_name(spec.py_type),
                "required": spec.required,
                "recommended": spec.recommended,
            }
            for path, spec in sorted(BASE_FIELDS.items())
        },
        "classes": {
            str(class_uid): _class_spec_dict(spec)
            for class_uid, spec in sorted(CLASS_REGISTRY.items())
        },
        "enums": {
            "severity_id": {
                0: "Unknown",
                1: "Informational",
                2: "Low",
                3: "Medium",
                4: "High",
                5: "Critical",
                6: "Fatal",
            },
            "status_id": {
                0: "Unknown",
                1: "Success",
                2: "Failure",
                3: "Other",
            },
        },
    }


def bundled_json_schema(version: str = DEFAULT_SCHEMA_VERSION) -> dict[str, Any]:
    registry = bundled_schema(version)
    schema: dict[str, Any] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"https://github.com/pfrederiksen/ocsfkit/schema/{version}",
        "title": f"ocsfkit minimal OCSF {version} event",
        "type": "object",
        "additionalProperties": True,
        "properties": {},
        "required": [],
    }
    for path, spec in registry["fields"].items():
        _set_json_schema_path(schema, path, spec)
    for required in sorted(registry["classes"]["2004"]["required"]):
        _add_required_path(schema, required)
    return schema


def _type_name(py_type: type | tuple[type, ...]) -> str:
    if isinstance(py_type, tuple):
        return " | ".join(item.__name__ for item in py_type)
    return py_type.__name__


def _class_spec_dict(spec: Any) -> dict[str, Any]:
    value = asdict(spec)
    value["required"] = sorted(value["required"])
    value["recommended"] = sorted(value["recommended"])
    return value


def _set_json_schema_path(schema: dict[str, Any], path: str, spec: dict[str, Any]) -> None:
    current = schema
    segments = _schema_segments(path)
    for segment, is_array in segments[:-1]:
        properties = current.setdefault("properties", {})
        if is_array:
            current = properties.setdefault(
                segment,
                {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": True,
                        "properties": {},
                    },
                },
            )["items"]
        else:
            current = properties.setdefault(
                segment,
                {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {},
                },
            )
    leaf, is_array = segments[-1]
    current.setdefault("properties", {})[leaf] = {
        "type": _json_schema_type(spec["type"]),
        "description": _field_description(spec),
    }
    if is_array:
        current["properties"][leaf] = {
            "type": "array",
            "items": current["properties"][leaf],
        }


def _add_required_path(schema: dict[str, Any], path: str) -> None:
    current = schema
    segments = _schema_segments(path)
    for segment, is_array in segments[:-1]:
        current.setdefault("required", [])
        if segment not in current["required"]:
            current["required"].append(segment)
        if is_array:
            current = current.setdefault("properties", {}).setdefault(
                segment,
                {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": True,
                        "properties": {},
                        "required": [],
                    },
                },
            )["items"]
        else:
            current = current.setdefault("properties", {}).setdefault(
                segment,
                {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {},
                    "required": [],
                },
            )
    current.setdefault("required", [])
    leaf = segments[-1][0]
    if leaf not in current["required"]:
        current["required"].append(leaf)


def _schema_segments(path: str) -> list[tuple[str, bool]]:
    return [(segment.removesuffix("[]"), segment.endswith("[]")) for segment in path.split(".")]


def _json_schema_type(type_name: str) -> str | list[str]:
    if "int" in type_name:
        return "integer"
    if "float" in type_name:
        return "number"
    if "bool" in type_name:
        return "boolean"
    if "dict" in type_name:
        return "object"
    if "list" in type_name:
        return "array"
    if "|" in type_name:
        return sorted({_json_schema_type(part.strip()) for part in type_name.split("|")})
    return "string"


def _field_description(spec: dict[str, Any]) -> str:
    markers = []
    if spec.get("required"):
        markers.append("required")
    if spec.get("recommended"):
        markers.append("recommended")
    return "ocsfkit minimal registry field" + (f" ({', '.join(markers)})" if markers else "")
