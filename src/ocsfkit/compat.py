from __future__ import annotations

import re
from typing import Any

from ocsfkit import __version__
from ocsfkit.models import LintIssue
from ocsfkit.registry import DEFAULT_SCHEMA_VERSION, SUPPORTED_SCHEMA_VERSIONS


def compatibility_issues(mapping: dict[str, Any]) -> list[LintIssue]:
    issues: list[LintIssue] = []
    required = mapping.get("requires_ocsfkit")
    if required is not None and isinstance(required, str):
        if not _satisfies(__version__, required):
            issues.append(
                LintIssue(
                    level="error",
                    path="requires_ocsfkit",
                    message=f"requires ocsfkit {required}, running {__version__}",
                )
            )
    elif required is not None:
        issues.append(
            LintIssue(level="error", path="requires_ocsfkit", message="must be a string")
        )
    ocsf_version = mapping.get("ocsf_version")
    schema_version = mapping.get("schema_version") or DEFAULT_SCHEMA_VERSION
    if ocsf_version is not None and ocsf_version != schema_version:
        issues.append(
            LintIssue(
                level="warning",
                path="ocsf_version",
                message=(
                    f"ocsf_version {ocsf_version!r} differs from "
                    f"schema_version {schema_version!r}"
                ),
            )
        )
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        issues.append(
            LintIssue(
                level="warning",
                path="schema_version",
                message=f"schema version {schema_version!r} is not bundled",
            )
        )
    return issues


def _satisfies(version: str, requirement: str) -> bool:
    parts = [part.strip() for part in requirement.split(",") if part.strip()]
    return all(_satisfies_part(version, part) for part in parts)


def _satisfies_part(version: str, part: str) -> bool:
    match = re.fullmatch(r"(>=|<=|==|>|<)?\s*([0-9]+(?:\.[0-9]+){0,2})", part)
    if not match:
        return False
    op = match.group(1) or "=="
    actual = _version_tuple(version)
    expected = _version_tuple(match.group(2))
    if op == "==":
        return actual == expected
    if op == ">=":
        return actual >= expected
    if op == "<=":
        return actual <= expected
    if op == ">":
        return actual > expected
    if op == "<":
        return actual < expected
    return False


def _version_tuple(version: str) -> tuple[int, int, int]:
    numbers = [int(part) for part in version.split(".")[:3]]
    while len(numbers) < 3:
        numbers.append(0)
    return tuple(numbers)  # type: ignore[return-value]
