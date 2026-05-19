from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

import typer
import yaml

from ocsfkit.baseline import check_baseline, create_baseline
from ocsfkit.benchmark import benchmark_mapping
from ocsfkit.catalog import catalog_markdown, mapping_catalog
from ocsfkit.ci import (
    explanations_to_github_annotations,
    lint_issues_flat_to_sarif,
    lint_issues_to_github_annotations,
    lint_issues_to_sarif,
    privacy_findings_to_sarif,
)
from ocsfkit.coverage import enforce_coverage_thresholds, mapping_coverage
from ocsfkit.diff import diff_events
from ocsfkit.doctor import run_doctor
from ocsfkit.drift import mapping_schema_drift
from ocsfkit.errors import OCSFKitError, QueryError
from ocsfkit.io import iter_events, load_events, load_mapping_file
from ocsfkit.junit import mapping_results_to_junit
from ocsfkit.mapping import apply_mapping
from ocsfkit.mapping_test import run_mapping_tests
from ocsfkit.models import DiffChange
from ocsfkit.packs import list_packs, validate_pack
from ocsfkit.paths import flatten_paths, query_field
from ocsfkit.privacy import scan_events
from ocsfkit.redact import redact_value
from ocsfkit.registry import DEFAULT_SCHEMA_VERSION, lint_event
from ocsfkit.render import (
    console,
    print_events,
    print_json,
    render_diff,
    render_explanation,
    render_lint,
)
from ocsfkit.report import coverage_html, explanation_html
from ocsfkit.schema import bundled_schema
from ocsfkit.schema_import import import_schema
from ocsfkit.schema_sync import sync_schema
from ocsfkit.scorecard import mapping_scorecard, scorecard_markdown
from ocsfkit.strict import strict_mapping_failures
from ocsfkit.summary import coverage_markdown, explanation_markdown
from ocsfkit.targets import list_targets, search_targets, show_target
from ocsfkit.transform_test import run_transform_tests
from ocsfkit.validation import validate_mapping_doc

app = typer.Typer(
    no_args_is_help=True,
    help=(
        "OCSF workbench for normalizing, linting, explaining, diffing, "
        "and querying security events."
    ),
)
targets_app = typer.Typer(help="Search and inspect bundled OCSF target fields.")
packs_app = typer.Typer(help="List and validate built-in mapping packs.")
baseline_app = typer.Typer(help="Create and check approved mapping-quality baselines.")
app.add_typer(targets_app, name="targets")
app.add_typer(packs_app, name="pack")
app.add_typer(baseline_app, name="baseline")


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
    event_id_path: Annotated[
        str | None, typer.Option("--event-id-path", help="Source path used to label events")
    ] = None,
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
        if event_id_path and not json_output and not sarif and not github_annotations:
            _print_event_ids(events, event_id_path)
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
    strict: Annotated[
        bool, typer.Option("--strict", help="Fail on guessed, missing, or unmapped fields")
    ] = False,
    allow_unsafe_transforms: Annotated[
        bool,
        typer.Option(
            "--allow-unsafe-transforms",
            help="Allow Python custom_transforms files when strict mode is enabled",
        ),
    ] = False,
    format: OutputFormat = "json",  # noqa: A002
) -> None:
    """Apply a YAML mapping and emit OCSF JSON."""

    def command() -> None:
        _validate_format(format)
        mapping_doc = load_mapping_file(mapping)
        custom_transforms = _custom_transforms_for_mapping(
            mapping_doc, mapping, allow_unsafe_transforms or not strict
        )
        results = [
            apply_mapping(event, mapping_doc, custom_transforms) for event in iter_events(input)
        ]
        if strict:
            _raise_on_strict_failures([result.explanation for result in results])
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
    markdown: Annotated[bool, typer.Option("--markdown", help="Emit Markdown explanation")] = False,
    html_output: Annotated[bool, typer.Option("--html", help="Emit HTML explanation")] = False,
    output: Annotated[
        str | None,
        typer.Option("--output", "-o", help="Write report to a file"),
    ] = None,
    strict: Annotated[
        bool, typer.Option("--strict", help="Fail on guessed, missing, or unmapped fields")
    ] = False,
    allow_unsafe_transforms: Annotated[
        bool,
        typer.Option("--allow-unsafe-transforms", help="Allow Python custom_transforms files"),
    ] = False,
    event_id_path: Annotated[
        str | None, typer.Option("--event-id-path", help="Source path used to label events")
    ] = None,
) -> None:
    """Explain mapping decisions, data loss, missing targets, and confidence."""

    def command() -> None:
        mapping_doc = load_mapping_file(mapping)
        custom_transforms = _custom_transforms_for_mapping(
            mapping_doc, mapping, allow_unsafe_transforms or not strict
        )
        results = [
            apply_mapping(event, mapping_doc, custom_transforms) for event in iter_events(input)
        ]
        if strict:
            _raise_on_strict_failures([result.explanation for result in results])
        if github_annotations:
            explanations = [result.explanation for result in results]
            for annotation in explanations_to_github_annotations(explanations, input):
                console.print(annotation)
            return
        if json_output:
            print_json([result.explanation.model_dump() for result in results])
            return
        if markdown:
            text = "\n".join(explanation_markdown(result.explanation) for result in results)
            _write_or_print(text, output)
            return
        if html_output:
            if len(results) != 1:
                raise OCSFKitError("--html currently requires exactly one input event")
            _write_or_print(explanation_html(results[0].explanation), output)
            return
        event_ids = _event_ids(load_events(input), event_id_path) if event_id_path else []
        for index, result in enumerate(results, start=1):
            if len(results) > 1:
                label = event_ids[index - 1] if event_ids else index
                console.rule(f"Event {label}")
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


@app.command("scorecard")
def scorecard_command(
    input: Annotated[str, typer.Argument(help="Source event JSON, YAML, NDJSON file, or -")],
    mapping: Annotated[str, typer.Option("--mapping", "-m", help="Mapping YAML path")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
    markdown: Annotated[bool, typer.Option("--markdown", help="Emit Markdown")] = False,
    github_summary: Annotated[
        bool, typer.Option("--github-summary", help="Append Markdown to GITHUB_STEP_SUMMARY")
    ] = False,
    min_confidence: Annotated[
        float, typer.Option("--min-confidence", help="Fail below this average confidence")
    ] = 0.8,
    max_unmapped: Annotated[
        int, typer.Option("--max-unmapped", help="Fail above this unmapped source field count")
    ] = 0,
    max_lint_errors: Annotated[
        int, typer.Option("--max-lint-errors", help="Fail above this mapped-event lint error count")
    ] = 0,
    strict: Annotated[
        bool, typer.Option("--strict", help="Fail on guessed, missing, or unmapped fields")
    ] = False,
    allow_unsafe_transforms: Annotated[
        bool, typer.Option("--allow-unsafe-transforms", help="Allow Python custom_transforms files")
    ] = False,
    event_id_path: Annotated[
        str | None, typer.Option("--event-id-path", help="Source path included in human output")
    ] = None,
) -> None:
    """Grade mapping production readiness with coverage, lint, and strict checks."""

    def command() -> None:
        mapping_doc = load_mapping_file(mapping)
        custom_transforms = _custom_transforms_for_mapping(
            mapping_doc, mapping, allow_unsafe_transforms or not strict
        )
        report = mapping_scorecard(
            iter_events(input),
            mapping_doc,
            custom_transforms,
            min_confidence=min_confidence,
            max_unmapped=max_unmapped,
            max_lint_errors=max_lint_errors,
            strict=strict,
        )
        if json_output:
            print_json(report.model_dump())
        elif markdown or github_summary:
            text = scorecard_markdown(report)
            if github_summary:
                _append_github_summary(text)
            if markdown:
                console.print(text)
        else:
            if event_id_path:
                console.print(f"[bold]Event ID path:[/bold] {event_id_path}")
            console.print(f"[bold]Grade:[/bold] {report.grade}")
            console.print(f"[bold]Passed:[/bold] {'yes' if report.passed else 'no'}")
            console.print(f"[bold]Events:[/bold] {report.events}")
            console.print(f"[bold]Average confidence:[/bold] {report.average_confidence:.3f}")
            console.print(f"[bold]Source field coverage:[/bold] {report.source_field_coverage:.3f}")
            console.print(
                f"[bold]Unmapped source fields:[/bold] {report.unmapped_source_field_count}"
            )
            console.print(
                f"[bold]Missing target fields:[/bold] {report.missing_target_field_count}"
            )
            console.print(f"[bold]Lint errors:[/bold] {report.lint_error_count}")
            for failure in report.failures:
                console.print(f"[red]{failure}[/red]")
        if not report.passed:
            raise typer.Exit(1)

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
    markdown: Annotated[
        bool, typer.Option("--markdown", help="Emit a Markdown coverage summary")
    ] = False,
    github_summary: Annotated[
        bool,
        typer.Option("--github-summary", help="Append a Markdown summary to GITHUB_STEP_SUMMARY"),
    ] = False,
    strict: Annotated[
        bool, typer.Option("--strict", help="Fail on guessed, missing, or unmapped fields")
    ] = False,
    allow_unsafe_transforms: Annotated[
        bool,
        typer.Option("--allow-unsafe-transforms", help="Allow Python custom_transforms files"),
    ] = False,
    event_id_path: Annotated[
        str | None, typer.Option("--event-id-path", help="Source path included in human output")
    ] = None,
) -> None:
    """Report mapping coverage across an event stream."""

    def command() -> None:
        mapping_doc = load_mapping_file(mapping)
        custom_transforms = _custom_transforms_for_mapping(
            mapping_doc, mapping, allow_unsafe_transforms or not strict
        )
        events = list(iter_events(input))
        report = mapping_coverage(events, mapping_doc, custom_transforms)
        failures = enforce_coverage_thresholds(report, min_confidence, max_unmapped)
        if strict:
            strict_failures: list[str] = []
            for event in events:
                strict_failures.extend(
                    strict_mapping_failures(
                        apply_mapping(event, mapping_doc, custom_transforms).explanation
                    )
                )
            failures.extend(strict_failures)
        if markdown or github_summary:
            text = coverage_markdown(report, failures)
            if github_summary:
                _append_github_summary(text)
            if markdown:
                console.print(text)
            if failures:
                raise typer.Exit(1)
            return
        if json_output:
            payload = report.model_dump()
            payload["threshold_failures"] = failures
            print_json(payload)
            if failures:
                raise typer.Exit(1)
            return
        console.print(f"[bold]Events:[/bold] {report.events}")
        if event_id_path:
            console.print(f"[bold]Event ID path:[/bold] {event_id_path}")
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
    strict: Annotated[
        bool, typer.Option("--strict", help="Treat warnings as errors")
    ] = False,
) -> None:
    """Validate a mapping file before applying it to events."""

    def command() -> None:
        issues = validate_mapping_doc(load_mapping_file(mapping))
        if json_output:
            print_json([issue.model_dump() for issue in issues])
        else:
            render_lint([issues])
        has_failure = any(issue.level == "error" or strict for issue in issues)
        if has_failure and not warn_only:
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


@app.command("sync-schema")
def sync_schema_command(
    output: Annotated[str, typer.Option("--output", "-o", help="Output registry JSON path")],
    url: Annotated[
        str,
        typer.Option("--url", help="OCSF schema zip archive URL"),
    ] = "https://github.com/ocsf/ocsf-schema/archive/refs/heads/main.zip",
) -> None:
    """Download and import the upstream OCSF schema archive."""

    def command() -> None:
        imported = sync_schema(output, url)
        console.print(f"Wrote {output} ({len(imported.get('classes', {}))} classes)")

    _run(command)


@app.command("schema-drift")
def schema_drift_command(
    mapping: Annotated[str, typer.Argument(help="Mapping YAML path")],
    schema: Annotated[
        str | None, typer.Option("--schema", help="Optional compact schema JSON/YAML path")
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
    sarif: Annotated[bool, typer.Option("--sarif", help="Emit SARIF JSON for CI")] = False,
    warn_only: Annotated[
        bool, typer.Option("--warn-only", help="Exit zero even when drift is found")
    ] = False,
) -> None:
    """Compare a mapping against bundled or synced schema data."""

    def command() -> None:
        schema_doc = yaml.safe_load(Path(schema).read_text()) if schema else None
        issues = mapping_schema_drift(load_mapping_file(mapping), schema_doc)
        if sarif:
            print_json(lint_issues_flat_to_sarif(issues, mapping, "ocsfkit.schema_drift"))
        elif json_output:
            print_json([issue.model_dump() for issue in issues])
        else:
            render_lint([issues])
        if issues and not warn_only:
            raise typer.Exit(1)

    _run(command)


@app.command("scan")
def scan_command(
    input: Annotated[str, typer.Argument(help="JSON, YAML, or NDJSON file to scan")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
    sarif: Annotated[bool, typer.Option("--sarif", help="Emit SARIF JSON for CI")] = False,
    warn_only: Annotated[
        bool, typer.Option("--warn-only", help="Exit zero even when findings exist")
    ] = False,
) -> None:
    """Scan fixtures or reports for likely secrets and sensitive identifiers."""

    def command() -> None:
        findings = scan_events(_load_scan_events(input))
        if sarif:
            print_json(privacy_findings_to_sarif(findings, input))
        elif json_output:
            print_json([finding.model_dump() for finding in findings])
        else:
            if not findings:
                console.print("[green]No likely secrets or sensitive identifiers found[/green]")
            for finding in findings:
                console.print(f"[yellow]{finding.kind}[/] {finding.path}: {finding.value}")
        if findings and not warn_only:
            raise typer.Exit(1)

    _run(command)


@app.command("redact")
def redact_command(
    input: Annotated[str, typer.Argument(help="JSON, YAML, NDJSON file, or - for stdin")],
    output: Annotated[
        str | None, typer.Option("--output", "-o", help="Write redacted output to a file")
    ] = None,
    replacement: Annotated[
        str, typer.Option("--replacement", help="Replacement text for sensitive values")
    ] = "<redacted>",
    format: OutputFormat = "json",  # noqa: A002
) -> None:
    """Redact likely secrets and identifiers while preserving event structure."""

    def command() -> None:
        _validate_format(format)
        redacted = [redact_value(event, replacement) for event in load_events(input)]
        if output:
            if format == "ndjson":
                import json

                Path(output).write_text("\n".join(json.dumps(event) for event in redacted) + "\n")
            else:
                import json

                payload = redacted[0] if len(redacted) == 1 else redacted
                Path(output).write_text(json.dumps(payload, indent=2) + "\n")
            console.print(f"Wrote {output}")
        else:
            print_events(redacted, format)

    _run(command)


@app.command("catalog")
def catalog_command(
    root: Annotated[
        str, typer.Option("--root", help="Directory containing mapping YAML files")
    ] = "examples",
    output: Annotated[
        str | None, typer.Option("--output", "-o", help="Write Markdown catalog to a file")
    ] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
) -> None:
    """Generate a catalog from mapping YAML files."""

    def command() -> None:
        items = mapping_catalog(root)
        if json_output:
            print_json(items)
            return
        _write_or_print(catalog_markdown(items), output)

    _run(command)


@app.command("test-mapping")
def test_mapping_command(
    spec: Annotated[str, typer.Argument(help="Mapping test YAML path or directory")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
    junit: Annotated[
        str | None, typer.Option("--junit", help="Write JUnit XML results to a file")
    ] = None,
) -> None:
    """Run one or more mapping fixture tests against expected OCSF output."""

    def command() -> None:
        results = run_mapping_tests(spec)
        if junit:
            Path(junit).write_text(mapping_results_to_junit(results))
            console.print(f"Wrote {junit}")
        if json_output:
            print_json(results)
        else:
            for result in results:
                if result["passed"]:
                    console.print(f"[green]{result['spec']}: passed[/green]")
                else:
                    console.print(f"[red]{result['spec']}: failed[/red]")
                    changes = [DiffChange(**change) for change in result["changes"]]
                    render_diff([changes])
        if any(not result["passed"] for result in results):
            raise typer.Exit(1)

    _run(command)


@app.command("doctor")
def doctor_command(
    root: Annotated[str, typer.Option("--root", help="Repository root to inspect")] = ".",
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
) -> None:
    """Check local install, schema, mapping packs, and common release tooling."""

    def command() -> None:
        report = run_doctor(root)
        if json_output:
            print_json(report)
            return
        for check in report["checks"]:
            color = "green" if check["passed"] else "red"
            console.print(f"[{color}]{check['name']}[/]: {check['detail']}")
        if not report["passed"]:
            raise typer.Exit(1)

    _run(command)


@app.command("benchmark")
def benchmark_command(
    input: Annotated[str, typer.Argument(help="Source event JSON, YAML, NDJSON file, or -")],
    mapping: Annotated[str, typer.Option("--mapping", "-m", help="Mapping YAML path")],
    iterations: Annotated[int, typer.Option("--iterations", help="Benchmark iterations")] = 5,
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
    allow_unsafe_transforms: Annotated[
        bool, typer.Option("--allow-unsafe-transforms", help="Allow Python custom_transforms files")
    ] = False,
) -> None:
    """Benchmark mapping throughput for a sample corpus."""

    def command() -> None:
        mapping_doc = load_mapping_file(mapping)
        custom_transforms = _custom_transforms_for_mapping(
            mapping_doc, mapping, allow_unsafe_transforms
        )
        report = benchmark_mapping(load_events(input), mapping_doc, custom_transforms, iterations)
        if json_output:
            print_json(report)
            return
        console.print(f"[bold]Events:[/bold] {report['events']}")
        console.print(f"[bold]Iterations:[/bold] {report['iterations']}")
        console.print(f"[bold]Best seconds:[/bold] {report['best_seconds']}")
        console.print(f"[bold]Median seconds:[/bold] {report['median_seconds']}")
        console.print(f"[bold]Events/sec:[/bold] {report['events_per_second']}")

    _run(command)


@app.command("test-transform")
def test_transform_command(
    spec: Annotated[str, typer.Argument(help="Transform test YAML path")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
) -> None:
    """Run YAML-defined tests for built-in or custom transforms."""

    def command() -> None:
        results = run_transform_tests(spec)
        if json_output:
            print_json(results)
        else:
            for result in results:
                color = "green" if result["passed"] else "red"
                console.print(f"[{color}]{result['name']}: {result['transform']}[/]")
                if not result["passed"]:
                    console.print(f"  expected: {result['expected']!r}")
                    console.print(f"  actual:   {result['actual']!r}")
        if any(not result["passed"] for result in results):
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
    interactive: Annotated[
        bool, typer.Option("--interactive", help="Prompt through source fields and write a mapping")
    ] = False,
    output: Annotated[
        str | None, typer.Option("--output", "-o", help="Mapping YAML path for interactive mode")
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
        if interactive:
            _interactive_mapping_review(source_paths, output)
        elif not mapping:
            console.print("\nRun init-mapping to generate a starter YAML.")

    _run(command)


@targets_app.command("list")
def targets_list(
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
) -> None:
    """List bundled OCSF target fields."""
    _run(lambda: print_json(list_targets()) if json_output else _print_targets(list_targets()))


@targets_app.command("search")
def targets_search(
    term: Annotated[str, typer.Argument(help="Search term")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
) -> None:
    """Search bundled OCSF target fields."""

    def command() -> None:
        targets = search_targets(term)
        print_json(targets) if json_output else _print_targets(targets)

    _run(command)


@targets_app.command("complete")
def targets_complete(
    prefix: Annotated[str, typer.Argument(help="Target path prefix")],
) -> None:
    """Print target paths matching a prefix for shell/editor completion."""

    def command() -> None:
        matches = [
            target["path"]
            for target in list_targets()
            if str(target["path"]).startswith(prefix)
        ]
        for match in matches:
            console.print(match)

    _run(command)


@targets_app.command("show")
def targets_show(
    path: Annotated[str, typer.Argument(help="Target field path")],
) -> None:
    """Show details for a bundled OCSF target field."""

    def command() -> None:
        target = show_target(path)
        if target is None:
            raise OCSFKitError(f"Unknown target field: {path}")
        print_json(target)

    _run(command)


@packs_app.command("list")
def pack_list(
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
) -> None:
    """List built-in mapping packs."""

    def command() -> None:
        packs = list_packs()
        if json_output:
            print_json(packs)
            return
        for pack in packs:
            console.print(f"[bold]{pack['name']}[/bold] ({pack['mapping_count']} mappings)")
            for mapping in pack["mappings"]:
                console.print(f"  {mapping}")

    _run(command)


@packs_app.command("validate")
def pack_validate(
    root: Annotated[str, typer.Option("--root", help="Repository root containing examples/")] = ".",
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
) -> None:
    """Validate all built-in mapping packs."""

    def command() -> None:
        results = validate_pack(root)
        if json_output:
            print_json(results)
        else:
            for result in results:
                issue_count = len(result["issues"])
                color = "green" if issue_count == 0 else "yellow"
                console.print(
                    f"[{color}]{result['pack']}[/] {result['mapping']}: {issue_count} issues"
                )
        if any(issue["level"] == "error" for result in results for issue in result["issues"]):
            raise typer.Exit(1)

    _run(command)


@baseline_app.command("create")
def baseline_create(
    input: Annotated[str, typer.Argument(help="Source event JSON, YAML, NDJSON file, or -")],
    mapping: Annotated[str, typer.Option("--mapping", "-m", help="Mapping YAML path")],
    output: Annotated[str, typer.Option("--output", "-o", help="Baseline YAML output path")],
    allow_unsafe_transforms: Annotated[
        bool, typer.Option("--allow-unsafe-transforms", help="Allow Python custom_transforms files")
    ] = False,
) -> None:
    """Create an approved baseline of current mapping gaps."""

    def command() -> None:
        mapping_doc = load_mapping_file(mapping)
        custom_transforms = _custom_transforms_for_mapping(
            mapping_doc, mapping, allow_unsafe_transforms
        )
        baseline = create_baseline(list(iter_events(input)), mapping_doc, custom_transforms)
        Path(output).write_text(yaml.safe_dump(baseline, sort_keys=False))
        console.print(f"Wrote {output}")

    _run(command)


@baseline_app.command("check")
def baseline_check(
    input: Annotated[str, typer.Argument(help="Source event JSON, YAML, NDJSON file, or -")],
    baseline: Annotated[str, typer.Option("--baseline", "-b", help="Baseline YAML path")],
    mapping: Annotated[str, typer.Option("--mapping", "-m", help="Mapping YAML path")],
    json_output: Annotated[bool, typer.Option("--json", help="Emit machine-readable JSON")] = False,
    warn_only: Annotated[
        bool, typer.Option("--warn-only", help="Exit zero even when new gaps exist")
    ] = False,
    allow_unsafe_transforms: Annotated[
        bool, typer.Option("--allow-unsafe-transforms", help="Allow Python custom_transforms files")
    ] = False,
) -> None:
    """Fail only when mapping gaps appear beyond the approved baseline."""

    def command() -> None:
        mapping_doc = load_mapping_file(mapping)
        custom_transforms = _custom_transforms_for_mapping(
            mapping_doc, mapping, allow_unsafe_transforms
        )
        result = check_baseline(baseline, list(iter_events(input)), mapping_doc, custom_transforms)
        if json_output:
            print_json(result.model_dump())
        else:
            if result.passed:
                console.print("[green]Baseline check passed[/green]")
            for path in result.new_unmapped_source_fields:
                console.print(f"[red]New unmapped source field:[/red] {path}")
            for path in result.new_missing_target_fields:
                console.print(f"[red]New missing target field:[/red] {path}")
        if not result.passed and not warn_only:
            raise typer.Exit(1)

    _run(command)


def _validate_format(format_name: str) -> None:
    if format_name not in {"json", "ndjson"}:
        raise OCSFKitError("--format must be one of: json, ndjson")


def _custom_transforms_for_mapping(
    mapping_doc: dict,
    mapping_path: str,
    allow_unsafe: bool = True,
) -> dict[str, Callable]:
    from ocsfkit.transforms import load_custom_transforms

    paths = mapping_doc.get("custom_transforms") or []
    if not paths:
        return {}
    if not allow_unsafe:
        raise OCSFKitError(
            "custom_transforms execute Python code; rerun with --allow-unsafe-transforms"
        )
    if not isinstance(paths, list) or not all(isinstance(item, str) for item in paths):
        raise OCSFKitError("custom_transforms must be a list of Python file paths")
    base_dir = Path(mapping_path).resolve().parent
    return load_custom_transforms(paths, base_dir)


def _raise_on_strict_failures(explanations: list) -> None:
    failures: list[str] = []
    for index, explanation in enumerate(explanations, start=1):
        failures.extend(
            f"event {index}: {failure}" for failure in strict_mapping_failures(explanation)
        )
    if failures:
        raise OCSFKitError("Strict mode failed:\n" + "\n".join(failures))


def _write_or_print(text: str, output: str | None) -> None:
    if output:
        Path(output).write_text(text)
        console.print(f"Wrote {output}")
    else:
        console.print(text)


def _load_scan_events(input_path: str) -> list[dict]:
    path = Path(input_path)
    if not path.is_dir():
        return load_events(input_path)
    events: list[dict] = []
    for candidate in sorted(path.rglob("*")):
        if candidate.suffix.lower() not in {".json", ".yaml", ".yml", ".ndjson"}:
            continue
        events.extend(load_events(str(candidate)))
    return events


def _append_github_summary(text: str) -> None:
    import os

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        raise OCSFKitError("GITHUB_STEP_SUMMARY is not set")
    with Path(summary_path).open("a") as handle:
        handle.write(text)


def _print_targets(targets: list[dict]) -> None:
    for target in targets:
        markers = []
        if target["required"]:
            markers.append("required")
        if target["recommended"]:
            markers.append("recommended")
        suffix = f" ({', '.join(markers)})" if markers else ""
        console.print(f"{target['path']} [{target['type']}]{suffix}")


def _event_ids(events: list[dict], event_id_path: str | None) -> list[object]:
    if not event_id_path:
        return []
    return [query_field(event, event_id_path) for event in events]


def _print_event_ids(events: list[dict], event_id_path: str) -> None:
    console.print(f"[bold]Event IDs from {event_id_path}[/bold]")
    for index, event_id in enumerate(_event_ids(events, event_id_path), start=1):
        console.print(f"  event {index}: {event_id}")


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


def _interactive_mapping_review(source_paths: list[str], output: str | None) -> None:
    if not output:
        raise OCSFKitError("--interactive requires --output")
    mapping: dict[str, object] = {
        "schema_version": DEFAULT_SCHEMA_VERSION,
        "target_class": {
            "class_uid": 2004,
            "class_name": "Detection Finding",
            "category_uid": 2,
            "category_name": "Findings",
        },
        "fields": {},
        "drop": [],
    }
    fields: dict[str, dict[str, str]] = {}
    drops: list[str] = []
    console.print("\n[bold]Interactive review[/bold]")
    console.print("For each source path, enter an OCSF target path, 'drop', or blank to skip.")
    for source_path in source_paths:
        if "[]" in source_path:
            continue
        answer = typer.prompt(source_path, default="", show_default=False).strip()
        if not answer:
            continue
        if answer.lower() == "drop":
            drops.append(source_path)
            continue
        fields[answer] = {"from": source_path}
    mapping["fields"] = fields
    mapping["drop"] = drops
    Path(output).write_text(yaml.safe_dump(mapping, sort_keys=False))
    console.print(f"Wrote {output}")


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
