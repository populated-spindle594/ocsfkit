from __future__ import annotations

from typing import Any


def aws_severity(value: Any) -> int:
    severities = {
        "unknown": 0,
        "informational": 1,
        "info": 1,
        "low": 2,
        "medium": 3,
        "high": 4,
        "critical": 5,
        "fatal": 6,
    }
    return severities[str(value).strip().lower()]


def azure_status_id(value: Any) -> int:
    return 1 if int(value) == 0 else 2


def azure_status(value: Any) -> str:
    return "Success" if int(value) == 0 else "Failure"


def okta_status_id(value: Any) -> int:
    return 1 if str(value).lower() == "success" else 2


def okta_status(value: Any) -> str:
    return "Success" if str(value).lower() == "success" else "Failure"


def network_activity_id(value: Any) -> int:
    text = str(value).lower()
    if text in {"open", "start"}:
        return 1
    if text in {"close", "end"}:
        return 2
    if text == "reset":
        return 3
    return 6


TRANSFORM_PACKS = {
    "aws.severity": aws_severity,
    "azure.status_id": azure_status_id,
    "azure.status": azure_status,
    "okta.status_id": okta_status_id,
    "okta.status": okta_status,
    "network.activity_id": network_activity_id,
}
