from __future__ import annotations

from typing import Any

from ocsfkit.models import LintIssue, MappingExplanation


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

