from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ocsfkit.models import LintIssue
from ocsfkit.paths import get_dotted
from ocsfkit.transforms import SEVERITY_ID_TO_TEXT

STATUS_ID_TO_TEXT = {
    0: "Unknown",
    1: "Success",
    2: "Failure",
    3: "Other",
}

CLASS_ACTIVITY_IDS = {
    3002: {1: "Logon", 2: "Logoff", 3: "Authentication Ticket"},
    4001: {1: "Open", 2: "Close", 3: "Reset", 6: "Traffic"},
    1007: {1: "Launch", 2: "Terminate", 3: "Open"},
    2004: {},
}


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
    category_uid: int
    category_name: str
    required: set[str] = field(default_factory=set)
    recommended: set[str] = field(default_factory=set)


DEFAULT_SCHEMA_VERSION = "1.7.0"
SUPPORTED_SCHEMA_VERSIONS = {"1.6.0", "1.7.0"}

BASE_FIELDS = {
    "time": FieldSpec("time", int, required=True),
    "class_uid": FieldSpec("class_uid", int, required=True),
    "class_name": FieldSpec("class_name", str, required=True),
    "category_uid": FieldSpec("category_uid", int),
    "category_name": FieldSpec("category_name", str),
    "activity_id": FieldSpec("activity_id", int),
    "activity_name": FieldSpec("activity_name", str),
    "type_uid": FieldSpec("type_uid", int),
    "type_name": FieldSpec("type_name", str),
    "severity_id": FieldSpec("severity_id", int, required=True),
    "severity": FieldSpec("severity", str, recommended=True),
    "message": FieldSpec("message", str, recommended=True),
    "metadata.version": FieldSpec("metadata.version", str, required=True),
    "metadata.product.name": FieldSpec("metadata.product.name", str, recommended=True),
    "actor.user.name": FieldSpec("actor.user.name", str),
    "actor.user.uid": FieldSpec("actor.user.uid", str),
    "cloud.account_uid": FieldSpec("cloud.account_uid", str),
    "cloud.region": FieldSpec("cloud.region", str),
    "device.hostname": FieldSpec("device.hostname", str),
    "dst_endpoint.ip": FieldSpec("dst_endpoint.ip", str),
    "dst_endpoint.port": FieldSpec("dst_endpoint.port", int),
    "process.name": FieldSpec("process.name", str),
    "process.pid": FieldSpec("process.pid", int),
    "resources[].name": FieldSpec("resources[].name", str),
    "resources[].type": FieldSpec("resources[].type", str),
    "src_endpoint.ip": FieldSpec("src_endpoint.ip", str),
    "src_endpoint.port": FieldSpec("src_endpoint.port", int),
    "status": FieldSpec("status", str),
    "status_id": FieldSpec("status_id", int),
}

CLASS_REGISTRY = {
    2004: ClassSpec(
        class_uid=2004,
        class_name="Detection Finding",
        category_uid=2,
        category_name="Findings",
        required={"time", "class_uid", "class_name", "severity_id", "metadata.version"},
        recommended={"message", "metadata.product.name", "severity"},
    ),
    3002: ClassSpec(
        class_uid=3002,
        class_name="Authentication",
        category_uid=3,
        category_name="Identity & Access Management",
        required={"time", "class_uid", "class_name", "metadata.version"},
        recommended={"activity_id", "activity_name", "actor.user.name", "status_id", "status"},
    ),
    4001: ClassSpec(
        class_uid=4001,
        class_name="Network Activity",
        category_uid=4,
        category_name="Network Activity",
        required={"time", "class_uid", "class_name", "metadata.version"},
        recommended={"src_endpoint.ip", "dst_endpoint.ip", "activity_id", "activity_name"},
    ),
    1007: ClassSpec(
        class_uid=1007,
        class_name="Process Activity",
        category_uid=1,
        category_name="System Activity",
        required={"time", "class_uid", "class_name", "metadata.version"},
        recommended={"process.name", "actor.user.name", "device.hostname"},
    ),
}


def required_fields_for(event: dict[str, Any], schema_version: str | None = None) -> set[str]:
    _ = schema_version
    class_uid = event.get("class_uid")
    if isinstance(class_uid, int) and class_uid in CLASS_REGISTRY:
        return set(CLASS_REGISTRY[class_uid].required)
    return {spec.path for spec in BASE_FIELDS.values() if spec.required}


def recommended_fields_for(event: dict[str, Any], schema_version: str | None = None) -> set[str]:
    _ = schema_version
    class_uid = event.get("class_uid")
    if isinstance(class_uid, int) and class_uid in CLASS_REGISTRY:
        return set(CLASS_REGISTRY[class_uid].recommended)
    return {spec.path for spec in BASE_FIELDS.values() if spec.recommended}


def lint_event(event: dict[str, Any], schema_version: str | None = None) -> list[LintIssue]:
    issues: list[LintIssue] = []
    expected_version = schema_version or DEFAULT_SCHEMA_VERSION
    event_version = get_dotted(event, "metadata.version")
    if event_version is not None and event_version not in SUPPORTED_SCHEMA_VERSIONS:
        issues.append(
            LintIssue(
                level="warning",
                path="metadata.version",
                message=f"Unsupported schema version {event_version!r}",
            )
        )
    if event_version is not None and schema_version is not None and event_version != schema_version:
        issues.append(
            LintIssue(
                level="error",
                path="metadata.version",
                message=f"Expected schema version {expected_version!r}, got {event_version!r}",
            )
        )
    for path in sorted(required_fields_for(event, expected_version)):
        if get_dotted(event, path) is None:
            issues.append(LintIssue(level="error", path=path, message="Missing required field"))
    for path in sorted(recommended_fields_for(event, expected_version)):
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
    if class_uid in CLASS_REGISTRY:
        spec = CLASS_REGISTRY[class_uid]
        if event.get("category_uid") is not None and event.get("category_uid") != spec.category_uid:
            issues.append(
                LintIssue(
                    level="error",
                    path="category_uid",
                    message=f"Expected {spec.category_uid} for class_uid {class_uid}",
                )
            )
        if (
            event.get("category_name") is not None
            and event.get("category_name") != spec.category_name
        ):
            issues.append(
                LintIssue(
                    level="error",
                    path="category_name",
                    message=f"Expected {spec.category_name!r} for class_uid {class_uid}",
                )
            )
    severity_id = event.get("severity_id")
    if isinstance(severity_id, int) and severity_id not in SEVERITY_ID_TO_TEXT:
        issues.append(LintIssue(level="error", path="severity_id", message="Invalid severity_id"))
    status_id = event.get("status_id")
    if isinstance(status_id, int) and status_id not in STATUS_ID_TO_TEXT:
        issues.append(LintIssue(level="error", path="status_id", message="Invalid status_id"))
    activity_id = event.get("activity_id")
    if isinstance(class_uid, int) and isinstance(activity_id, int):
        activity_ids = CLASS_ACTIVITY_IDS.get(class_uid, {})
        if activity_ids and activity_id not in activity_ids:
            issues.append(
                LintIssue(
                    level="error",
                    path="activity_id",
                    message=f"Invalid activity_id for class_uid {class_uid}",
                )
            )
        elif activity_id in activity_ids and event.get("activity_name") not in {
            None,
            activity_ids[activity_id],
        }:
            issues.append(
                LintIssue(
                    level="error",
                    path="activity_name",
                    message=f"Expected {activity_ids[activity_id]!r} for activity_id {activity_id}",
                )
            )
    if "time" in event and isinstance(event["time"], int) and event["time"] <= 0:
        issues.append(
            LintIssue(level="error", path="time", message="Timestamp must be positive epoch ms")
        )
    return issues


def _type_name(py_type: type | tuple[type, ...]) -> str:
    if isinstance(py_type, tuple):
        return " or ".join(item.__name__ for item in py_type)
    return py_type.__name__
