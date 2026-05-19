from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.table import Table

from ocsfkit.models import DiffChange, LintIssue, MappingExplanation

console = Console()


def print_json(value: Any) -> None:
    console.file.write(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n")


def print_events(events: list[dict[str, Any]], output_format: str) -> None:
    if output_format == "ndjson":
        for event in events:
            console.file.write(json.dumps(event, sort_keys=True, default=str) + "\n")
    else:
        print_json(events[0] if len(events) == 1 else events)


def render_explanation(explanation: MappingExplanation) -> None:
    console.print(f"[bold]Confidence:[/bold] {explanation.confidence:.3f}")
    if explanation.target_class:
        console.print(f"[bold]Target class:[/bold] {explanation.target_class}")
    _decision_table("Mapped fields", explanation.mapped_fields)
    _decision_table("Defaulted fields", explanation.defaulted_fields)
    _decision_table("Guessed fields", explanation.guessed_fields)
    _path_table("Dropped fields", explanation.dropped_fields)
    _path_table("Unmapped source fields", explanation.unmapped_source_fields)
    _path_table("Missing target fields", explanation.missing_target_fields)


def _decision_table(title: str, rows: list[Any]) -> None:
    table = Table(title=title)
    table.add_column("Target")
    table.add_column("Source")
    table.add_column("Transform")
    table.add_column("Provenance")
    table.add_column("Value")
    for row in rows:
        table.add_row(
            row.target,
            row.source or "",
            row.transform or "",
            row.provenance,
            json.dumps(row.value, default=str),
        )
    console.print(table)


def _path_table(title: str, rows: list[str]) -> None:
    table = Table(title=title)
    table.add_column("Path")
    for row in rows:
        table.add_row(row)
    console.print(table)


def render_lint(issues_by_event: list[list[LintIssue]]) -> None:
    for index, issues in enumerate(issues_by_event, start=1):
        if not issues:
            console.print(f"[green]Event {index}: OK[/green]")
            continue
        table = Table(title=f"Event {index} lint")
        table.add_column("Level")
        table.add_column("Path")
        table.add_column("Message")
        for issue in issues:
            style = "red" if issue.level == "error" else "yellow"
            table.add_row(f"[{style}]{issue.level}[/{style}]", issue.path, issue.message)
        console.print(table)


def render_diff(changes_by_event: list[list[DiffChange]]) -> None:
    for index, changes in enumerate(changes_by_event, start=1):
        if not changes:
            console.print(f"[green]Event {index}: no semantic changes[/green]")
            continue
        table = Table(title=f"Event {index} semantic diff")
        table.add_column("Kind")
        table.add_column("Path")
        table.add_column("Before")
        table.add_column("After")
        for change in changes:
            style = _diff_style(change.path, change.kind)
            table.add_row(
                f"[{style}]{change.kind}[/{style}]",
                change.path,
                json.dumps(change.before, default=str),
                json.dumps(change.after, default=str),
            )
        console.print(table)


def _diff_style(path: str, kind: str) -> str:
    if path in {"class_uid", "class_name", "severity_id", "severity"}:
        return "bold red"
    if kind == "added":
        return "green"
    if kind == "removed":
        return "red"
    return "yellow"
