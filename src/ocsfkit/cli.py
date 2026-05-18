from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer

from ocsfkit.ci import (
    explanations_to_github_annotations,
    lint_issues_to_github_annotations,
    lint_issues_to_sarif,
)
from ocsfkit.diff import diff_events
from ocsfkit.errors import OCSFKitError, QueryError
from ocsfkit.io import load_events, load_mapping_file
from ocsfkit.mapping import apply_mapping
from ocsfkit.paths import query_field
from ocsfkit.registry import DEFAULT_SCHEMA_VERSION, lint_event
from ocsfkit.render import (
    console,
    print_events,
    print_json,
    render_diff,
    render_explanation,
    render_lint,
)

app = typer.Typer(
    no_args_is_help=True,
    help=(
        "OCSF workbench for normalizing, linting, explaining, diffing, "
        "and querying security events."
    ),
)


OutputFormat = Annotated[str, typer.Option("--format", help="Output format: json or ndjson")]


@app.command()
def parse(
    input: Annotated[str, typer.Argument(help="JSON, YAML, NDJSON file, or - for stdin")],
    format: OutputFormat = "json",  # noqa: A002
) -> None:
    """Read JSON/YAML/NDJSON and emit normalized JSON."""
    _validate_format(format)
    _run(lambda: print_events(load_events(input), format))


@app.command()
def lint(
    input: Annotated[str, typer.Argument(help="OCSF JSON, YAML, NDJSON file, or - for stdin")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
    sarif: Annotated[bool, typer.Option("--sarif", help="Emit SARIF JSON for CI")] = False,
    github_annotations: Annotated[
        bool, typer.Option("--github-annotations", help="Emit GitHub workflow annotations")
    ] = False,
    schema_version: Annotated[
        str, typer.Option("--schema-version", help="Expected OCSF schema version")
    ] = DEFAULT_SCHEMA_VERSION,
    warn_only: Annotated[
        bool, typer.Option("--warn-only", help="Exit zero even when errors exist")
    ] = False,
) -> None:
    """Validate OCSF-looking events against the minimal local registry."""

    def command() -> None:
        events = load_events(input)
        issues_by_event = [lint_event(event, schema_version) for event in events]
        if sarif:
            print_json(lint_issues_to_sarif(issues_by_event, input))
        elif github_annotations:
            for annotation in lint_issues_to_github_annotations(issues_by_event, input):
                console.print(annotation)
        elif json_output:
            print_json([[issue.model_dump() for issue in issues] for issues in issues_by_event])
        else:
            render_lint(issues_by_event)
        has_error = any(issue.level == "error" for issues in issues_by_event for issue in issues)
        if has_error and not warn_only:
            raise typer.Exit(1)

    _run(command)


@app.command()
def map(  # noqa: A001
    input: Annotated[
        str, typer.Argument(help="Source event JSON, YAML, NDJSON file, or - for stdin")
    ],
    mapping: Annotated[str, typer.Option("--mapping", "-m", help="Mapping YAML path")],
    explain: Annotated[
        bool, typer.Option("--explain", help="Include explanation metadata")
    ] = False,
    format: OutputFormat = "json",  # noqa: A002
) -> None:
    """Apply a YAML mapping and emit OCSF JSON."""

    def command() -> None:
        _validate_format(format)
        mapping_doc = load_mapping_file(mapping)
        custom_transforms = _custom_transforms_for_mapping(mapping_doc, mapping)
        results = [
            apply_mapping(event, mapping_doc, custom_transforms) for event in load_events(input)
        ]
        if explain:
            payload = [
                {"event": result.event, "explanation": result.explanation.model_dump()}
                for result in results
            ]
            print_events(payload, format)
        else:
            print_events([result.event for result in results], format)

    _run(command)


@app.command()
def explain(
    input: Annotated[
        str, typer.Argument(help="Source event JSON, YAML, NDJSON file, or - for stdin")
    ],
    mapping: Annotated[str, typer.Option("--mapping", "-m", help="Mapping YAML path")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
    github_annotations: Annotated[
        bool, typer.Option("--github-annotations", help="Emit GitHub workflow annotations")
    ] = False,
) -> None:
    """Explain mapping decisions, data loss, missing targets, and confidence."""

    def command() -> None:
        mapping_doc = load_mapping_file(mapping)
        custom_transforms = _custom_transforms_for_mapping(mapping_doc, mapping)
        results = [
            apply_mapping(event, mapping_doc, custom_transforms) for event in load_events(input)
        ]
        if github_annotations:
            explanations = [result.explanation for result in results]
            for annotation in explanations_to_github_annotations(explanations, input):
                console.print(annotation)
            return
        if json_output:
            print_json([result.explanation.model_dump() for result in results])
            return
        for index, result in enumerate(results, start=1):
            if len(results) > 1:
                console.rule(f"Event {index}")
            render_explanation(result.explanation)

    _run(command)


@app.command()
def diff(
    before: Annotated[str, typer.Argument(help="Before OCSF event or stream")],
    after: Annotated[str, typer.Argument(help="After OCSF event or stream")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
) -> None:
    """Show semantic differences between two OCSF events or streams."""

    def command() -> None:
        before_events = load_events(before)
        after_events = load_events(after)
        if len(before_events) != len(after_events):
            message = (
                "Cannot diff streams with different lengths: "
                f"{len(before_events)} vs {len(after_events)}"
            )
            raise OCSFKitError(
                message
            )
        changes_by_event = [
            diff_events(before_event, after_event)
            for before_event, after_event in zip(before_events, after_events, strict=True)
        ]
        if json_output:
            payload = [[change.model_dump() for change in changes] for changes in changes_by_event]
            print_json(payload)
        else:
            render_diff(changes_by_event)

    _run(command)


@app.command()
def query(
    input: Annotated[
        str, typer.Argument(help="OCSF event JSON, YAML, NDJSON file, or - for stdin")
    ],
    expression: Annotated[str, typer.Argument(help="Dotted OCSF field path, e.g. actor.user.name")],
) -> None:
    """Extract common OCSF fields using a small dotted-path convenience layer."""

    def command() -> None:
        values = [query_field(event, expression) for event in load_events(input)]
        for value in values:
            if isinstance(value, dict | list):
                print_json(value)
            elif value is None:
                console.print("null")
            else:
                console.print(value)

    _run(command)


def _validate_format(format_name: str) -> None:
    if format_name not in {"json", "ndjson"}:
        raise OCSFKitError("--format must be one of: json, ndjson")


def _custom_transforms_for_mapping(mapping_doc: dict, mapping_path: str) -> dict[str, Callable]:
    from ocsfkit.transforms import load_custom_transforms

    paths = mapping_doc.get("custom_transforms") or []
    if not paths:
        return {}
    if not isinstance(paths, list) or not all(isinstance(item, str) for item in paths):
        raise OCSFKitError("custom_transforms must be a list of Python file paths")
    base_dir = Path(mapping_path).resolve().parent
    return load_custom_transforms(paths, base_dir)


def _run(callback: Callable[[], None]) -> None:
    try:
        callback()
    except QueryError as exc:
        console.print(f"[red]Query error:[/red] {exc}")
        raise typer.Exit(2) from exc
    except OCSFKitError as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(2) from exc


if __name__ == "__main__":
    app()
