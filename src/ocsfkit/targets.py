from __future__ import annotations

from typing import Any

from ocsfkit.registry import BASE_FIELDS, CLASS_REGISTRY, FieldSpec


def search_targets(term: str) -> list[dict[str, Any]]:
    lowered = term.lower()
    return [
        _field_payload(path, spec)
        for path, spec in sorted(BASE_FIELDS.items())
        if lowered in path.lower()
    ]


def show_target(path: str) -> dict[str, Any] | None:
    spec = BASE_FIELDS.get(path)
    if spec is None:
        return None
    payload = _field_payload(path, spec)
    payload["classes_required"] = [
        class_spec.class_uid
        for class_spec in CLASS_REGISTRY.values()
        if path in class_spec.required
    ]
    payload["classes_recommended"] = [
        class_spec.class_uid
        for class_spec in CLASS_REGISTRY.values()
        if path in class_spec.recommended
    ]
    return payload


def list_targets() -> list[dict[str, Any]]:
    return [_field_payload(path, spec) for path, spec in sorted(BASE_FIELDS.items())]


def _field_payload(path: str, spec: FieldSpec) -> dict[str, Any]:
    return {
        "path": path,
        "type": _type_name(spec.py_type),
        "required": spec.required,
        "recommended": spec.recommended,
    }


def _type_name(py_type: type | tuple[type, ...]) -> str:
    if isinstance(py_type, tuple):
        return " or ".join(item.__name__ for item in py_type)
    return py_type.__name__
