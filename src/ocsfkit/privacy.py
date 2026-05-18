from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from ocsfkit.paths import leaf_paths


class Finding(BaseModel):
    path: str
    kind: str
    value: str


PATTERNS = {
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "generic_secret": re.compile(r"(?i)(api[_-]?key|secret|token|password)"),
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "ipv4": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "account_id": re.compile(r"\b\d{12}\b"),
}


def scan_value(value: Any, path: str = "$") -> list[Finding]:
    findings: list[Finding] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if PATTERNS["generic_secret"].search(str(key)):
                findings.append(Finding(path=child_path, kind="sensitive_key", value=str(key)))
            findings.extend(scan_value(child, child_path))
    elif isinstance(value, list):
        for child in value:
            findings.extend(scan_value(child, f"{path}[]"))
    else:
        text = str(value)
        for kind, pattern in PATTERNS.items():
            if kind == "generic_secret":
                continue
            for match in pattern.finditer(text):
                findings.append(Finding(path=path, kind=kind, value=_redact(match.group(0))))
    return findings


def scan_events(events: list[dict[str, Any]]) -> list[Finding]:
    findings: list[Finding] = []
    for index, event in enumerate(events, start=1):
        event_findings = scan_value(event)
        for finding in event_findings:
            finding.path = f"event[{index}].{finding.path}"
        findings.extend(event_findings)
    return findings


def fixture_paths(value: Any) -> list[str]:
    return sorted(leaf_paths(value))


def _redact(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"
