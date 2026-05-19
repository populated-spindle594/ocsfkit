from __future__ import annotations

from typing import Any

from ocsfkit.models import LintIssue, MappingExplanation
from ocsfkit.privacy import Finding
from ocsfkit.scorecard import ScorecardReport


def lint_issues_to_sarif(issues_by_event: list[list[LintIssue]], source_uri: str) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for index, issues in enumerate(issues_by_event, start=1):
        for issue in issues:
            results.append(
                {
                    "ruleId": f"ocsfkit.{issue.path}",
                    "level": "error" if issue.level == "error" else "warning",
                    "message": {"text": issue.message},
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": source_uri},
                                "region": {"startLine": index},
                            },
                            "logicalLocations": [{"fullyQualifiedName": issue.path}],
                        }
                    ],
                }
            )
    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "ocsfkit",
                        "informationUri": "https://github.com/pfrederiksen/ocsfkit",
                        "rules": [],
                    }
                },
                "results": results,
            }
        ],
    }


def lint_issues_flat_to_sarif(
    issues: list[LintIssue],
    source_uri: str,
    category: str = "ocsfkit",
) -> dict[str, Any]:
    return _sarif(
        [
            {
                "ruleId": f"{category}.{issue.path}",
                "level": "error" if issue.level == "error" else "warning",
                "message": {"text": issue.message},
                "locations": [_location(source_uri, 1, issue.path)],
            }
            for issue in issues
        ]
    )


def privacy_findings_to_sarif(findings: list[Finding], source_uri: str) -> dict[str, Any]:
    return _sarif(
        [
            {
                "ruleId": f"ocsfkit.privacy.{finding.kind}",
                "level": "warning",
                "message": {
                    "text": f"{finding.kind} at {finding.path}: {finding.value}",
                },
                "locations": [_location(source_uri, _event_line(finding.path), finding.path)],
            }
            for finding in findings
        ]
    )


def quality_failures_to_sarif(
    failures: list[str],
    source_uri: str,
    category: str = "ocsfkit.quality",
) -> dict[str, Any]:
    return _sarif(
        [
            {
                "ruleId": f"{category}.{index}",
                "level": "error",
                "message": {"text": failure},
                "locations": [_location(source_uri, 1, category)],
            }
            for index, failure in enumerate(failures, start=1)
        ]
    )


def scorecard_to_sarif(report: ScorecardReport, source_uri: str) -> dict[str, Any]:
    failures = report.failures or ([] if report.passed else [f"Scorecard grade {report.grade}"])
    return quality_failures_to_sarif(failures, source_uri, "ocsfkit.scorecard")


def lint_issues_to_github_annotations(
    issues_by_event: list[list[LintIssue]],
    source_uri: str,
) -> list[str]:
    annotations: list[str] = []
    for index, issues in enumerate(issues_by_event, start=1):
        for issue in issues:
            level = "error" if issue.level == "error" else "warning"
            message = _escape_annotation(f"{issue.path}: {issue.message}")
            annotations.append(f"::{level} file={source_uri},line={index}::{message}")
    return annotations


def explanations_to_github_annotations(
    explanations: list[MappingExplanation],
    source_uri: str,
) -> list[str]:
    annotations: list[str] = []
    for index, explanation in enumerate(explanations, start=1):
        for path in explanation.missing_target_fields:
            message = _escape_annotation(f"Missing target field: {path}")
            annotations.append(f"::error file={source_uri},line={index}::{message}")
        for path in explanation.unmapped_source_fields:
            message = _escape_annotation(f"Unmapped source field: {path}")
            annotations.append(f"::warning file={source_uri},line={index}::{message}")
    return annotations


def _escape_annotation(message: str) -> str:
    return message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def _sarif(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "ocsfkit",
                        "informationUri": "https://github.com/pfrederiksen/ocsfkit",
                        "rules": [],
                    }
                },
                "results": results,
            }
        ],
    }


def _location(source_uri: str, line: int, logical_name: str) -> dict[str, Any]:
    return {
        "physicalLocation": {
            "artifactLocation": {"uri": source_uri},
            "region": {"startLine": max(line, 1)},
        },
        "logicalLocations": [{"fullyQualifiedName": logical_name}],
    }


def _event_line(path: str) -> int:
    prefix = "event["
    if not path.startswith(prefix):
        return 1
    raw = path[len(prefix) :].split("]", 1)[0]
    try:
        return int(raw)
    except ValueError:
        return 1
