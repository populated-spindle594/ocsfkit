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


def _type_name(py_type: type | tuple[type, ...]) -> str:
    if isinstance(py_type, tuple):
        return " | ".join(item.__name__ for item in py_type)
    return py_type.__name__


def _class_spec_dict(spec: Any) -> dict[str, Any]:
    value = asdict(spec)
    value["required"] = sorted(value["required"])
    value["recommended"] = sorted(value["recommended"])
    return value
