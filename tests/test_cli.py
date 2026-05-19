from typer.testing import CliRunner

from ocsfkit.cli import app

runner = CliRunner()


def test_parse_smoke() -> None:
    result = runner.invoke(app, ["parse", "fixtures/aws_guardduty_finding.json"])
    assert result.exit_code == 0
    assert "111122223333" in result.stdout


def test_lint_smoke_failure() -> None:
    result = runner.invoke(app, ["lint", "fixtures/broken_ocsf_event.json"])
    assert result.exit_code == 1
    assert "Invalid severity_id" in result.stdout


def test_lint_sarif_smoke() -> None:
    result = runner.invoke(app, ["lint", "fixtures/broken_ocsf_event.json", "--sarif"])
    assert result.exit_code == 1
    assert '"version": "2.1.0"' in result.stdout


def test_map_smoke() -> None:
    result = runner.invoke(
        app,
        [
            "map",
            "fixtures/aws_guardduty_finding.json",
            "--mapping",
            "examples/guardduty-mapping.yaml",
        ],
    )
    assert result.exit_code == 0
    assert "Detection Finding" in result.stdout


def test_explain_json_smoke() -> None:
    result = runner.invoke(
        app,
        [
            "explain",
            "fixtures/aws_guardduty_finding.json",
            "--mapping",
            "examples/guardduty-mapping.yaml",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert "unmapped_source_fields" in result.stdout


def test_explain_github_annotations_smoke() -> None:
    result = runner.invoke(
        app,
        [
            "explain",
            "fixtures/aws_guardduty_finding.json",
            "--mapping",
            "examples/guardduty-mapping.yaml",
            "--github-annotations",
        ],
    )
    assert result.exit_code == 0
    assert "::warning file=fixtures/aws_guardduty_finding.json,line=1::" in result.stdout


def test_explain_markdown_and_html_smoke(tmp_path) -> None:
    markdown = runner.invoke(
        app,
        [
            "explain",
            "fixtures/aws_guardduty_finding.json",
            "--mapping",
            "examples/guardduty-mapping.yaml",
            "--markdown",
        ],
    )
    assert markdown.exit_code == 0
    assert "Mapping Explanation" in markdown.stdout

    output = tmp_path / "explain.html"
    html = runner.invoke(
        app,
        [
            "explain",
            "fixtures/aws_guardduty_finding.json",
            "--mapping",
            "examples/guardduty-mapping.yaml",
            "--html",
            "--output",
            str(output),
        ],
    )
    assert html.exit_code == 0
    assert "Mapping Explanation" in output.read_text()


def test_map_strict_blocks_unmapped_fields() -> None:
    result = runner.invoke(
        app,
        [
            "map",
            "fixtures/aws_guardduty_finding.json",
            "--mapping",
            "examples/guardduty-mapping.yaml",
            "--strict",
        ],
    )
    assert result.exit_code == 2
    assert "Strict mode failed" in result.stdout


def test_query_smoke() -> None:
    result = runner.invoke(app, ["query", "fixtures/ocsf_detection_finding.json", "severity_id"])
    assert result.exit_code == 0
    assert "4" in result.stdout


def test_diff_mapping_smoke(tmp_path) -> None:
    before = tmp_path / "before.yaml"
    after = tmp_path / "after.yaml"
    before.write_text(
        """
target_class:
  class_uid: 2004
  class_name: Detection Finding
fields:
  message:
    from: $.title
"""
    )
    after.write_text(
        """
target_class:
  class_uid: 2004
  class_name: Detection Finding
fields:
  message:
    from: $.detail
"""
    )
    result = runner.invoke(app, ["diff-mapping", str(before), str(after), "--json"])
    assert result.exit_code == 1
    assert "$.detail" in result.stdout


def test_coverage_smoke() -> None:
    result = runner.invoke(
        app,
        [
            "coverage",
            "fixtures/aws_guardduty_finding.json",
            "--mapping",
            "examples/guardduty-mapping.yaml",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert "source_field_coverage" in result.stdout


def test_coverage_markdown_smoke() -> None:
    result = runner.invoke(
        app,
        [
            "coverage",
            "fixtures/aws_guardduty_finding.json",
            "--mapping",
            "examples/guardduty-mapping.yaml",
            "--markdown",
        ],
    )
    assert result.exit_code == 0
    assert "ocsfkit Coverage" in result.stdout


def test_baseline_commands_smoke(tmp_path) -> None:
    baseline = tmp_path / "baseline.yaml"
    created = runner.invoke(
        app,
        [
            "baseline",
            "create",
            "fixtures/guardduty.ndjson",
            "--mapping",
            "examples/guardduty-mapping.yaml",
            "--output",
            str(baseline),
        ],
    )
    assert created.exit_code == 0
    checked = runner.invoke(
        app,
        [
            "baseline",
            "check",
            "fixtures/guardduty.ndjson",
            "--mapping",
            "examples/guardduty-mapping.yaml",
            "--baseline",
            str(baseline),
        ],
    )
    assert checked.exit_code == 0
    assert "passed" in checked.stdout


def test_scorecard_smoke() -> None:
    result = runner.invoke(
        app,
        [
            "scorecard",
            "fixtures/guardduty.ndjson",
            "--mapping",
            "examples/guardduty-mapping.yaml",
            "--min-confidence",
            "0.7",
            "--max-unmapped",
            "10",
            "--json",
        ],
    )
    assert result.exit_code == 0
    assert '"grade": "C"' in result.stdout


def test_validate_mapping_smoke() -> None:
    result = runner.invoke(app, ["validate-mapping", "examples/guardduty-mapping.yaml"])
    assert result.exit_code == 0


def test_init_mapping_smoke() -> None:
    result = runner.invoke(app, ["init-mapping", "fixtures/aws_guardduty_finding.json"])
    assert result.exit_code == 0
    assert "schema_version" in result.stdout


def test_schema_smoke() -> None:
    result = runner.invoke(app, ["schema"])
    assert result.exit_code == 0
    assert "Detection Finding" in result.stdout


def test_test_mapping_smoke() -> None:
    result = runner.invoke(app, ["test-mapping", "tests/fixtures/guardduty-test.yaml"])
    assert result.exit_code == 0
    assert "passed" in result.stdout


def test_test_mapping_directory_smoke() -> None:
    result = runner.invoke(app, ["test-mapping", "tests/fixtures"])
    assert result.exit_code == 0
    assert "guardduty-test.yaml" in result.stdout


def test_test_mapping_junit_smoke(tmp_path) -> None:
    output = tmp_path / "junit.xml"
    result = runner.invoke(
        app,
        ["test-mapping", "tests/fixtures", "--junit", str(output)],
    )
    assert result.exit_code == 0
    assert "<testsuite" in output.read_text()


def test_test_transform_smoke() -> None:
    result = runner.invoke(app, ["test-transform", "tests/fixtures/transform-test.yaml"])
    assert result.exit_code == 0
    assert "severity_text_to_id" in result.stdout


def test_schema_drift_smoke() -> None:
    result = runner.invoke(app, ["schema-drift", "examples/guardduty-mapping.yaml"])
    assert result.exit_code == 0


def test_schema_drift_sarif_smoke() -> None:
    result = runner.invoke(app, ["schema-drift", "examples/guardduty-mapping.yaml", "--sarif"])
    assert result.exit_code == 0
    assert '"version": "2.1.0"' in result.stdout


def test_scan_smoke() -> None:
    result = runner.invoke(app, ["scan", "fixtures/aws_guardduty_finding.json", "--warn-only"])
    assert result.exit_code == 0
    assert "account_id" in result.stdout


def test_scan_sarif_smoke() -> None:
    result = runner.invoke(
        app, ["scan", "fixtures/aws_guardduty_finding.json", "--sarif", "--warn-only"]
    )
    assert result.exit_code == 0
    assert "ocsfkit.privacy.account_id" in result.stdout


def test_redact_smoke() -> None:
    result = runner.invoke(app, ["redact", "fixtures/aws_guardduty_finding.json"])
    assert result.exit_code == 0
    assert "<redacted>" in result.stdout
    assert "111122223333" not in result.stdout


def test_catalog_smoke() -> None:
    result = runner.invoke(app, ["catalog", "--json"])
    assert result.exit_code == 0
    assert "guardduty-mapping" in result.stdout


def test_report_smoke(tmp_path) -> None:
    output = tmp_path / "report.html"
    result = runner.invoke(
        app,
        [
            "report",
            "fixtures/aws_guardduty_finding.json",
            "--mapping",
            "examples/guardduty-mapping.yaml",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0
    assert "Mapping Report" in output.read_text()


def test_import_schema_smoke(tmp_path) -> None:
    schema = tmp_path / "schema.json"
    schema.write_text('{"schema_version": "test", "classes": {"1": {"class_name": "X"}}}')
    result = runner.invoke(app, ["import-schema", str(schema)])
    assert result.exit_code == 0
    assert "schema_version" in result.stdout


def test_workshop_smoke() -> None:
    result = runner.invoke(app, ["workshop", "fixtures/okta_login_event.json"])
    assert result.exit_code == 0
    assert "$.published" in result.stdout


def test_targets_commands_smoke() -> None:
    search = runner.invoke(app, ["targets", "search", "user"])
    assert search.exit_code == 0
    assert "actor.user.name" in search.stdout

    show = runner.invoke(app, ["targets", "show", "severity_id"])
    assert show.exit_code == 0
    assert '"path": "severity_id"' in show.stdout

    complete = runner.invoke(app, ["targets", "complete", "actor.user"])
    assert complete.exit_code == 0
    assert "actor.user.name" in complete.stdout


def test_pack_commands_smoke() -> None:
    listed = runner.invoke(app, ["pack", "list"])
    assert listed.exit_code == 0
    assert "aws" in listed.stdout

    validated = runner.invoke(app, ["pack", "validate", "--json"])
    assert validated.exit_code == 0
    assert "guardduty-mapping.yaml" in validated.stdout


def test_doctor_and_benchmark_smoke() -> None:
    doctor = runner.invoke(app, ["doctor", "--json"])
    assert doctor.exit_code == 0
    assert '"passed": true' in doctor.stdout

    benchmark = runner.invoke(
        app,
        [
            "benchmark",
            "fixtures/aws_guardduty_finding.json",
            "--mapping",
            "examples/guardduty-mapping.yaml",
            "--iterations",
            "1",
            "--json",
        ],
    )
    assert benchmark.exit_code == 0
    assert "events_per_second" in benchmark.stdout


def test_golden_catalog_mapping_tests() -> None:
    result = runner.invoke(app, ["test-mapping", "tests/goldens"])
    assert result.exit_code == 0
    assert "guardduty-mapping.yaml" in result.stdout
