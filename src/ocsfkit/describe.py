from __future__ import annotations

from typing import Any

from ocsfkit.registry import (
    CLASS_REGISTRY,
    SEVERITY_ID_TO_TEXT,
    STATUS_ID_TO_TEXT,
    SUPPORTED_SCHEMA_VERSIONS,
)
from ocsfkit.targets import show_target


def describe(subject: str, value: str | None = None) -> dict[str, Any]:
    """Return a human-readable description payload for a field, enum, or class."""
    normalized = subject.strip()
    if normalized == "schema_version":
        return {
            "kind": "schema_version",
            "default": "1.7.0",
            "supported": sorted(SUPPORTED_SCHEMA_VERSIONS),
        }
    if normalized in {"class_uid", "class"} and value is not None:
        return describe_class(value)
    if normalized.isdigit():
        return describe_class(normalized)
    if normalized == "severity_id":
        return _enum_payload("severity_id", SEVERITY_ID_TO_TEXT, value)
    if normalized == "status_id":
        return _enum_payload("status_id", STATUS_ID_TO_TEXT, value)
    target = show_target(normalized)
    if target is not None:
        return {"kind": "field", **target}
    return {
        "kind": "unknown",
        "subject": normalized,
        "message": "No bundled description is available for this subject.",
    }


def describe_class(raw_uid: str) -> dict[str, Any]:
    try:
        class_uid = int(raw_uid)
    except ValueError:
        return {"kind": "unknown", "subject": raw_uid, "message": "class_uid must be an integer."}
    spec = CLASS_REGISTRY.get(class_uid)
    if spec is None:
        return {
            "kind": "unknown",
            "subject": raw_uid,
            "message": "Unknown OCSF class_uid in the bundled registry.",
        }
    return {
        "kind": "class",
        "class_uid": spec.class_uid,
        "class_name": spec.class_name,
        "category_uid": spec.category_uid,
        "category_name": spec.category_name,
        "required": sorted(spec.required),
        "recommended": sorted(spec.recommended),
    }


def _enum_payload(name: str, values: dict[int, str], raw_value: str | None) -> dict[str, Any]:
    if raw_value is None:
        return {"kind": "enum", "name": name, "values": values}
    try:
        enum_value = int(raw_value)
    except ValueError:
        return {"kind": "unknown", "subject": raw_value, "message": f"{name} must be an integer."}
    if enum_value not in values:
        return {"kind": "unknown", "subject": raw_value, "message": f"Unknown {name} value."}
    return {"kind": "enum_value", "name": name, "value": enum_value, "label": values[enum_value]}
