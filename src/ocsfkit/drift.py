from __future__ import annotations

from typing import Any

from ocsfkit.models import LintIssue
from ocsfkit.registry import BASE_FIELDS, CLASS_REGISTRY


def mapping_schema_drift(
    mapping: dict[str, Any],
    schema: dict[str, Any] | None = None,
) -> list[LintIssue]:
    fields = _schema_fields(schema)
    classes = _schema_classes(schema)
    issues: list[LintIssue] = []
    target_class = mapping.get("target_class") or {}
    if isinstance(target_class, dict):
        class_uid = target_class.get("class_uid")
        if class_uid is not None and str(class_uid) not in classes:
            issues.append(
                LintIssue(
                    level="warning",
                    path="target_class.class_uid",
                    message=f"class_uid {class_uid!r} is not present in schema",
                )
            )
    for target in (mapping.get("fields") or {}):
        target_path = str(target)
        if target_path not in fields:
            issues.append(
                LintIssue(
                    level="warning",
                    path=f"fields.{target_path}",
                    message="Target field is not present in schema",
                )
            )
    required = set()
    if isinstance(target_class, dict):
        class_spec = classes.get(str(target_class.get("class_uid")))
        if isinstance(class_spec, dict):
            required = set(class_spec.get("required") or [])
    mapped = set(mapping.get("fields") or {}) | set(target_class)
    for path in sorted(required - mapped):
        issues.append(
            LintIssue(
                level="warning",
                path=path,
                message="Required schema field is not mapped or defaulted",
            )
        )
    return issues


def _schema_fields(schema: dict[str, Any] | None) -> set[str]:
    if schema and isinstance(schema.get("fields"), dict):
        return set(schema["fields"])
    return set(BASE_FIELDS)


def _schema_classes(schema: dict[str, Any] | None) -> dict[str, Any]:
    if schema and isinstance(schema.get("classes"), dict):
        return schema["classes"]
    return {str(class_uid): spec for class_uid, spec in CLASS_REGISTRY.items()}
