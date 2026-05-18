from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ocsfkit.models import LintIssue
from ocsfkit.paths import get_dotted
from ocsfkit.transforms import SEVERITY_ID_TO_TEXT


@dataclass(frozen=True)
class FieldSpec:
    path: str
    py_type: type | tuple[type, ...]
    required: bool = False
    recommended: bool = False


@dataclass(frozen=True)
class ClassSpec:
    class_uid: int
    class_name: str
    required: set[str] = field(default_factory=set)
    recommended: set[str] = field(default_factory=set)


BASE_FIELDS = {
    "time": FieldSpec("time", int, required=True),
    "class_uid": FieldSpec("class_uid", int, required=True),
    "class_name": FieldSpec("class_name", str, required=True),
    "category_uid": FieldSpec("category_uid", int),
    "severity_id": FieldSpec("severity_id", int, required=True),
    "severity": FieldSpec("severity", str, recommended=True),
    "message": FieldSpec("message", str, recommended=True),
    "metadata.product.name": FieldSpec("metadata.product.name", str, recommended=True),
    "actor.user.name": FieldSpec("actor.user.name", str),
    "actor.user.uid": FieldSpec("actor.user.uid", str),
    "cloud.account_uid": FieldSpec("cloud.account_uid", str),
    "cloud.region": FieldSpec("cloud.region", str),
    "resources[].name": FieldSpec("resources[].name", str),
    "resources[].type": FieldSpec("resources[].type", str),
}

CLASS_REGISTRY = {
    2004: ClassSpec(
        class_uid=2004,
        class_name="Detection Finding",
        required={"time", "class_uid", "class_name", "severity_id"},
        recommended={"message", "metadata.product.name", "severity"},
    )
}


def required_fields_for(event: dict[str, Any]) -> set[str]:
    class_uid = event.get("class_uid")
    if isinstance(class_uid, int) and class_uid in CLASS_REGISTRY:
        return set(CLASS_REGISTRY[class_uid].required)
    return {spec.path for spec in BASE_FIELDS.values() if spec.required}


def recommended_fields_for(event: dict[str, Any]) -> set[str]:
    class_uid = event.get("class_uid")
    if isinstance(class_uid, int) and class_uid in CLASS_REGISTRY:
        return set(CLASS_REGISTRY[class_uid].recommended)
    return {spec.path for spec in BASE_FIELDS.values() if spec.recommended}


def lint_event(event: dict[str, Any]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    for path in sorted(required_fields_for(event)):
        if get_dotted(event, path) is None:
            issues.append(LintIssue(level="error", path=path, message="Missing required field"))
    for path in sorted(recommended_fields_for(event)):
        if get_dotted(event, path) is None:
            issues.append(
                LintIssue(level="warning", path=path, message="Missing recommended field")
            )
    for path, spec in BASE_FIELDS.items():
        value = get_dotted(event, path)
        if value is None:
            continue
        values = value if isinstance(value, list) and "[]" in path else [value]
        for item in values:
            if item is not None and not isinstance(item, spec.py_type):
                expected = _type_name(spec.py_type)
                issues.append(
                    LintIssue(
                        level="error",
                        path=path,
                        message=f"Expected {expected}, got {type(item).__name__}",
                    )
                )
    class_uid = event.get("class_uid")
    if class_uid is not None and class_uid not in CLASS_REGISTRY:
        issues.append(
            LintIssue(level="warning", path="class_uid", message="Unknown OCSF class_uid")
        )
    elif (
        class_uid in CLASS_REGISTRY
        and event.get("class_name") != CLASS_REGISTRY[class_uid].class_name
    ):
        message = f"Expected {CLASS_REGISTRY[class_uid].class_name!r} for class_uid {class_uid}"
        issues.append(
            LintIssue(
                level="error",
                path="class_name",
                message=message,
            )
        )
    severity_id = event.get("severity_id")
    if isinstance(severity_id, int) and severity_id not in SEVERITY_ID_TO_TEXT:
        issues.append(LintIssue(level="error", path="severity_id", message="Invalid severity_id"))
    if "time" in event and isinstance(event["time"], int) and event["time"] <= 0:
        issues.append(
            LintIssue(level="error", path="time", message="Timestamp must be positive epoch ms")
        )
    return issues


def _type_name(py_type: type | tuple[type, ...]) -> str:
    if isinstance(py_type, tuple):
        return " or ".join(item.__name__ for item in py_type)
    return py_type.__name__
