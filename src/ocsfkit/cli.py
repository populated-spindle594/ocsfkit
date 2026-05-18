from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer
import yaml

from ocsfkit.ci import (
    explanations_to_github_annotations,
    lint_issues_to_github_annotations,
    lint_issues_to_sarif,
)
from ocsfkit.coverage import enforce_coverage_thresholds, mapping_coverage
from ocsfkit.diff import diff_events
from ocsfkit.errors import OCSFKitError, QueryError
from ocsfkit.io import load_events, load_mapping_file
from ocsfkit.mapping import apply_mapping
from ocsfkit.mapping_test import run_mapping_test
from ocsfkit.paths import flatten_paths, query_field
from ocsfkit.registry import DEFAULT_SCHEMA_VERSION, lint_event
from ocsfkit.render import (
    console,
    print_events,
    print_json,
    render_diff,
    render_explanation,
    render_lint,
)
from ocsfkit.report import coverage_html
from ocsfkit.schema import bundled_schema
from ocsfkit.schema_import import import_schema
from ocsfkit.validation import validate_mapping_doc

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


@app.command("coverage")
def coverage_command(
    input: Annotated[
        str, typer.Argument(help="Source event JSON, YAML, NDJSON file, or - for stdin")
    ],
    mapping: Annotated[str, typer.Option("--mapping", "-m", help="Mapping YAML path")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
    min_confidence: Annotated[
        float | None, typer.Option("--min-confidence", help="Fail below this average confidence")
    ] = None,
    max_unmapped: Annotated[
        int | None, typer.Option("--max-unmapped", help="Fail above this unmapped field count")
    ] = None,
) -> None:
    """Report mapping coverage across an event stream."""

    def command() -> None:
        mapping_doc = load_mapping_file(mapping)
        custom_transforms = _custom_transforms_for_mapping(mapping_doc, mapping)
        report = mapping_coverage(load_events(input), mapping_doc, custom_transforms)
        failures = enforce_coverage_thresholds(report, min_confidence, max_unmapped)
        if json_output:
            payload = report.model_dump()
            payload["threshold_failures"] = failures
            print_json(payload)
            if failures:
                raise typer.Exit(1)
            return
        console.print(f"[bold]Events:[/bold] {report.events}")
        console.print(f"[bold]Average confidence:[/bold] {report.average_confidence:.3f}")
        console.print(f"[bold]Source field coverage:[/bold] {report.source_field_coverage:.3f}")
        if report.unmapped_source_fields:
            console.print("[bold]Top unmapped source fields:[/bold]")
            for path, count in sorted(
                report.unmapped_source_fields.items(), key=lambda item: item[1], reverse=True
            )[:20]:
                console.print(f"  {path}: {count}")
        for failure in failures:
            console.print(f"[red]{failure}[/red]")
        if failures:
            raise typer.Exit(1)

    _run(command)


@app.command("validate-mapping")
def validate_mapping(
    mapping: Annotated[str, typer.Argument(help="Mapping YAML path")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
    warn_only: Annotated[
        bool, typer.Option("--warn-only", help="Exit zero even when errors exist")
    ] = False,
) -> None:
    """Validate a mapping file before applying it to events."""

    def command() -> None:
        issues = validate_mapping_doc(load_mapping_file(mapping))
        if json_output:
            print_json([issue.model_dump() for issue in issues])
        else:
            render_lint([issues])
        if any(issue.level == "error" for issue in issues) and not warn_only:
            raise typer.Exit(1)

    _run(command)


@app.command("init-mapping")
def init_mapping(
    input: Annotated[str, typer.Argument(help="Sample source event file")],
    class_uid: Annotated[int, typer.Option("--class-uid", help="Target OCSF class UID")] = 2004,
    class_name: Annotated[
        str, typer.Option("--class-name", help="Target OCSF class name")
    ] = "Detection Finding",
    product_name: Annotated[
        str, typer.Option("--product-name", help="metadata.product.name default")
    ] = "Unknown Product",
) -> None:
    """Scaffold a starter mapping from a sample source event."""

    def command() -> None:
        event = load_events(input)[0]
        source_paths = sorted(path for path in flatten_paths(event) if "[]" not in path)
        mapping = {
            "schema_version": DEFAULT_SCHEMA_VERSION,
            "target_class": {
                "class_uid": class_uid,
                "class_name": class_name,
                "metadata.product.name": product_name,
            },
            "fields": _starter_fields(source_paths, product_name),
            "drop": [],
        }
        console.print(yaml.safe_dump(mapping, sort_keys=False))

    _run(command)


@app.command("schema")
def schema_command(
    version: Annotated[
        str, typer.Option("--schema-version", help="Bundled schema version")
    ] = DEFAULT_SCHEMA_VERSION,
) -> None:
    """Emit the bundled minimal OCSF schema registry as JSON."""
    _run(lambda: print_json(bundled_schema(version)))


@app.command("import-schema")
def import_schema_command(
    path: Annotated[str, typer.Argument(help="OCSF schema JSON/YAML file or directory")],
) -> None:
    """Import an upstream-style OCSF schema export into ocsfkit JSON."""
    _run(lambda: print_json(import_schema(path)))


@app.command("test-mapping")
def test_mapping_command(
    spec: Annotated[str, typer.Argument(help="Mapping test YAML path")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
) -> None:
    """Run a mapping fixture test against expected OCSF output."""

    def command() -> None:
        changes = run_mapping_test(spec)
        if json_output:
            print_json([change.model_dump() for change in changes])
        elif changes:
            render_diff([changes])
        else:
            console.print("[green]Mapping test passed[/green]")
        if changes:
            raise typer.Exit(1)

    _run(command)


@app.command("report")
def report_command(
    input: Annotated[str, typer.Argument(help="Source event JSON, YAML, NDJSON file, or -")],
    mapping: Annotated[str, typer.Option("--mapping", "-m", help="Mapping YAML path")],
    output: Annotated[str, typer.Option("--output", "-o", help="HTML output path")],
) -> None:
    """Generate an HTML mapping coverage report."""

    def command() -> None:
        mapping_doc = load_mapping_file(mapping)
        custom_transforms = _custom_transforms_for_mapping(mapping_doc, mapping)
        report = mapping_coverage(load_events(input), mapping_doc, custom_transforms)
        Path(output).write_text(coverage_html(report))
        console.print(f"Wrote {output}")

    _run(command)


@app.command("workshop")
def workshop_command(
    input: Annotated[str, typer.Argument(help="Sample source event file")],
    mapping: Annotated[
        str | None, typer.Option("--mapping", "-m", help="Existing mapping YAML path")
    ] = None,
) -> None:
    """Print a guided mapping review worksheet for a sample event."""

    def command() -> None:
        event = load_events(input)[0]
        source_paths = sorted(flatten_paths(event))
        console.print("[bold]Source fields[/bold]")
        for path in source_paths:
            console.print(f"  {path}")
        if mapping:
            mapping_doc = load_mapping_file(mapping)
            custom_transforms = _custom_transforms_for_mapping(mapping_doc, mapping)
            explanation = apply_mapping(event, mapping_doc, custom_transforms).explanation
            render_explanation(explanation)
        else:
            console.print("\nRun init-mapping to generate a starter YAML.")

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


def _starter_fields(source_paths: list[str], product_name: str) -> dict[str, dict[str, str | bool]]:
    candidates = {
        "time": ("time", "eventTime", "timestamp", "created_at", "createdAt", "published"),
        "message": ("message", "title", "description", "eventName", "name"),
        "severity": ("severity", "Severity.Label", "risk", "risk_label"),
        "cloud.account_uid": ("accountId", "AwsAccountId", "tenantId"),
        "cloud.region": ("region", "awsRegion", "Region"),
        "actor.user.name": ("user", "userName", "actor.name", "target.user"),
        "src_endpoint.ip": ("src_ip", "sourceIPAddress", "source.ip", "client.ip"),
        "dst_endpoint.ip": ("dst_ip", "destination.ip", "server.ip"),
    }
    fields: dict[str, dict[str, str | bool]] = {
        "metadata.product.name": {"default": product_name}
    }
    for target, names in candidates.items():
        match = _find_source_path(source_paths, names)
        if match:
            spec: dict[str, str | bool] = {"from": match}
            if target == "time":
                spec["transform"] = "parse_timestamp"
                spec["required"] = True
            fields[target] = spec
    if "severity" in fields:
        fields["severity_id"] = {
            "from": fields["severity"]["from"],
            "transform": "severity_text_to_id",
            "default": 1,
            "required": True,
        }
    return fields


def _find_source_path(source_paths: list[str], names: tuple[str, ...]) -> str | None:
    lowered = {path.lower(): path for path in source_paths}
    for name in names:
        suffix = f".{name}".lower()
        for lowered_path, path in lowered.items():
            if lowered_path.endswith(suffix) or lowered_path == f"${suffix}":
                return path
    return None


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
